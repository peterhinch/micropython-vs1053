# VS1053_syn Synchronous driver for MicroPython
# (C) Peter Hinch 2020
# Released under the MIT licence

# Driver is based on the following sources
# Adafruit https://github.com/adafruit/Adafruit_CircuitPython_VS1053
# Uri Shaked https://github.com/urish/vs1053-circuitpython
# https://bois083.wordpress.com/2014/11/11/playing-flac-files-using-vs1053-audio-decoder-chip/
# http://www.vlsi.fi/fileadmin/software/VS10XX/vs1053b-peq.pdf

import time
import os

# V0.1.2 Add patch facility
__version__ = (0, 1, 2)

# Before setting, the internal clock runs at 12.288MHz. Data P7: "the
# maximum speed for SCI reads is CLKI/7" hence max initial baudrate is
# 12.288/7 = 1.75MHz
_INITIAL_BAUDRATE = const(1_000_000)
# 12.288*3.5/4 = 10.752MHz for data read (using _SCI_CLOCKF,0x8800)
_DATA_BAUDRATE = const(10_752_000)  # Speed for data transfers. On Pyboard D
# actual rate is 9MHz shared with SD card - sdcard.py uses 1.32MHz.
_SCI_BAUDRATE = const(5_000_000)

# SCI Registers
_SCI_MODE = const(0x0)
_SCI_STATUS = const(0x1)
_SCI_BASS = const(0x2)
_SCI_CLOCKF = const(0x3)
_SCI_DECODE_TIME = const(0x4)
# _SCI_AUDATA = const(0x5)
_SCI_WRAM = const(0x6)
_SCI_WRAMADDR = const(0x7)
_SCI_HDAT0 = const(0x8)
_SCI_HDAT1 = const(0x9)
# _SCI_AIADDR = const(0xa)
_SCI_VOL = const(0xb)
# _SCI_AICTRL0 = const(0xc)
# _SCI_AICTRL1 = const(0xd)
# _SCI_AICTRL2 = const(0xe)
# _SCI_AICTRL3 = const(0xf)

# Mode register bits: Public
SM_DIFF = const(0x01)  # Invert left channel (why?)
SM_LAYER12 = const(0x02)  # Enable MPEG
SM_EARSPEAKER_LO = const(0x10)  # EarSpeaker spatial processing
SM_EARSPEAKER_HI = const(0x80)
SM_LINE_IN = const(0x4000)  # Line/Mic in
# Private bits
_SM_RESET = const(0x04)
_SM_CANCEL = const(0x08)
_SM_TESTS = const(0x20)
_SM_SDINEW = const(0x800)
# Unused and private
# _SM_STREAM = const(0x40)
# _SM_DACT = const(0x100)
# _SM_SDIORD = const(0x200)
# _SM_SDISHARE = const(0x400)
# _SM_ADPCM = const(0x1000)
# _SM_ADPCM_HP = const(0x2000)
# _SM_CLK_RANGE = const(0x8000)

# Common parameters section 10.11.1 (RAM locations)
_END_FILL_BYTE = const(0x1e06)
_BYTE_RATE = const(0x1e05)
_POS_MS_LS = const(0x1e27)
_POS_MS_MS = const(0x1e28)
_IO_DIRECTION = const(0xc017)  # Datasheet 11.10
_IO_READ = const(0xc018)
_IO_WRITE = const(0xc019)


# xcs is chip XSS/
# xdcs is chipXDCS/BSYNC/
# sdcs is SD card CS/
class VS1053:

    def __init__(self, spi, reset, dreq, xdcs, xcs, sdcs=None, mp=None, cancb=lambda : False):
        self._reset = reset
        self._dreq = dreq  # Data request
        self._xdcs = xdcs  # Data CS
        self._xcs = xcs  # Register CS
        self._mp = mp
        self._spi = spi
        self._cbuf = bytearray(4)  # Command buffer
        self._cancb = cancb  # Cancellation callback
        self._slow_spi = True
        self.reset()
        if ((sdcs is not None) and (mp is not None)):
            import sdcard
            import os
            sd = sdcard.SDCard(spi, sdcs)
            vfs = os.VfsFat(sd)
            os.mount(vfs, mp)
        self._spi.init(baudrate=_DATA_BAUDRATE)

    def _wait_ready(self):
        self._xdcs(1)
        self._xcs(1)
        while not self._dreq():
            pass

    def _write_reg(self, addr, value):  # Datasheet 7.4
        self._wait_ready()
        self._spi.init(baudrate = _INITIAL_BAUDRATE if self._slow_spi else _SCI_BAUDRATE)
        b = self._cbuf
        b[0] = 2  # WRITE
        b[1] = addr & 0xff
        b[2] = (value >> 8) & 0xff
        b[3] = value & 0xff
        self._xcs(0)
        self._spi.write(b)
        self._xcs(1)
        self._spi.init(baudrate=_DATA_BAUDRATE)

    def _read_reg(self, addr):  # Datasheet 7.4
        self._wait_ready()
        self._spi.init(baudrate = _INITIAL_BAUDRATE if self._slow_spi else _SCI_BAUDRATE)
        b = self._cbuf
        b[0] = 3  # READ
        b[1] = addr & 0xff
        b[2] = 0xff
        b[3] = 0xff
        self._xcs(0)
        self._spi.write_readinto(b, b)
        self._xcs(1)
        self._spi.init(baudrate=_DATA_BAUDRATE)
        return (b[2] << 8) | b[3]

    def _read_ram(self, addr):
        self._write_reg(_SCI_WRAMADDR, addr)
        return self._read_reg(_SCI_WRAM)

    def _write_ram(self, addr, data):
        self._write_reg(_SCI_WRAMADDR, addr)
        return self._write_reg(_SCI_WRAM, data)

    # Datasheet section 10.5.1: procedure for normal end of play
    def _end_play(self, buf):
        efb = self._read_ram(_END_FILL_BYTE) & 0xff
        for n in range(len(buf)):
            buf[n] = efb
        for n in range(65):  # send 2080 bytes of end fill byte
            self.write(buf)
        self.mode_set(_SM_CANCEL)
        for n in range(64):  # send up to 2048 bytes
            self.write(buf)
            if not self.mode() & _SM_CANCEL:
                break
        else:  # Cancel has not been acknowledged
            self.soft_reset()
            return
        if self._read_reg(_SCI_HDAT0) or self._read_reg(_SCI_HDAT1):
            raise RuntimeError('Invalid HDAT value.')

    def write(self, buf):
        while not self._dreq():  # minimise for speed
            pass
        self._xdcs(0)
        self._spi.write(buf)
        self._xdcs(1)
        return len(buf)

    def _patch_stream(self, s):
        def read_word(s, buf=bytearray(2)):
            if s.readinto(buf) != 2:
                raise RuntimeError('Invalid file')
            return (buf[1] << 8) + buf[0]

        while True:
            try:
                addr = read_word(s)
            except RuntimeError:  # Normal EOF
                break
            count = read_word(s)
            if (count & 0x8000):  # RLE run, replicate n samples
                count &= 0x7fff
                val = read_word(s)
                for _ in range(count):
                    self._write_reg(addr, val)
            else:  # Copy run, copy n samples
                for _ in range(count):
                    val = read_word(s)
                    self._write_reg(addr, val)

# *** API ***

    def reset(self):  # Issue hardware reset to VS1053
        self._xcs(1)
        self._xdcs(1)
        self._reset(0)
        time.sleep_ms(20)
        self._reset(1)
        time.sleep_ms(20)
        self.soft_reset()

    def soft_reset(self):
        self._slow_spi = True  # Use _INITIAL_BAUDRATE
        self.mode_set(_SM_RESET)
        # This has many interesting settings data P39
        time.sleep_ms(20)  # Adafruit have a total of 200ms
        while not self._dreq():
            pass
        # Data P42. P7 footnote 4 recommends xtal * 3.5 + 1: using that.
        self._write_reg(_SCI_CLOCKF, 0x8800)
        if self._read_reg(_SCI_CLOCKF) != 0x8800:
            raise OSError('No VS1053 device found.')
        time.sleep_ms(1)  # Clock setting can take 100us
        # Datasheet suggests writing to SPI_BASS. 
        self._write_reg(_SCI_BASS, 0)  # 0 is flat response
        self.volume(0, 0)
        while not self._dreq():
            pass
        self._slow_spi = False

    # Range is 0 to -63.5 dB
    def volume(self, left, right, powerdown=False):
        bits = [0, 0]
        obits = 0xffff  # powerdown
        if not powerdown:
            for n, l in enumerate((left, right)):
                bits[n] = round(min(max(2 * -l, 0), 127))
            obits = bits[0] << 8 | bits[1]
        self._write_reg(_SCI_VOL, obits)

    def response(self, *, bass_freq=10, treble_freq=1000, bass_amp=0, treble_amp=0):
        bits = 0
        # Treble amplitude in dB range -12..10.5
        ta = round(min(max(treble_amp, -12.0), 10.5) / 1.5) & 0x0f
        bits |= ta << 12
        # Treble freq 1000-15000
        tf = round(min(max(treble_freq, 1000), 15000) / 1000) if ta else 0
        bits |= tf << 8
        # Bass amplitude in dB range 0..15
        ba = round(min(max(bass_amp, 0), 15))
        bits |= ba << 4
        # Bass freq 20Hz-150Hz
        bf = round(min(max(bass_freq, 20), 150) / 10) if ba else 0
        bits |= bf
        self._write_reg(_SCI_BASS, bits)

    def pins_direction(self, bits):
        self._write_ram(_IO_DIRECTION, bits & 0xff)

    def pins(self, data=None):
        if data is not None:
            self._write_ram(_IO_WRITE, data & 0xff)
        return self._read_ram(_IO_READ) & 0x3ff

    def version(self):
        return (self._read_reg(_SCI_STATUS) >> 4) & 0x0F

    def decode_time(self):  # Number of seconds into the stream
        return self._read_reg(_SCI_DECODE_TIME)

    def byte_rate(self):  # Data rate in bytes/sec
        return self._read_ram(_BYTE_RATE)

    def mode(self):
        return self._read_reg(_SCI_MODE)

    def mode_set(self, bits):
        bits |= self.mode() | _SM_SDINEW
        self._write_reg(_SCI_MODE, bits)

    def mode_clear(self, bits):
        bits ^= 0xffff
        bits &= self.mode()
        self._write_reg(_SCI_MODE, _SM_SDINEW | bits)  # Ensure new bit always set

# Doesn't return anything useful for MP3
#    def pos_ms(self):  # Position into stream in ms
#        return self._read_ram(_POS_MS_LS) | (self._read_ram(_POS_MS_MS) << 16)


    # Should check for short reads at EOF. Loop is time critical so I skip
    # this check. Sending a few bytes of old data has no obvious consequence.
    def play(self, s, buf = bytearray(32)):
        cancb = self._cancb
        cancnt = 0
        cnt = 0
        while s.readinto(buf):  # Read <=32 bytes
            cnt += 1
            self.write(buf)
            if cancnt == 0:  # Not cancelling. Check callback at ~8Hz (@128Kbps)
                if (not cnt & 0x7ff) and cancb():
                    self.mode_set(_SM_CANCEL)
                    cancnt = 1  # Send at least one more buffer
                continue

            # cancnt > 0: Cancelling
            if not self.mode() & _SM_CANCEL:  # Cancel done
                efb = self._read_ram(_END_FILL_BYTE) & 0xff
                for n in range(len(buf)):
                    buf[n] = efb
                for n in range(64):  # send 2048 bytes of end fill byte
                    self.write(buf)
                self.write(buf[:4])  # Take to 2052 bytes
                if self._read_reg(_SCI_HDAT0) or self._read_reg(_SCI_HDAT1):
                    raise RuntimeError('Invalid HDAT value.')
                break
            if cancnt > 64:  # Cancel has failed
                self.soft_reset()
                break
            cancnt += 1  # keep feeding data from stream
        else:
            self._end_play(buf)

    # Produce a 517Hz sine wave
    def sine_test(self, seconds=10):
        self.soft_reset()
        self.mode_set(_SM_TESTS)
        # 0x66-> Sample rate 22050 * 6/128 = 1034Hz 0x63->517Hz
        self.write(b'\x53\xef\x6e\x66\0\0\0\0')
        time.sleep(seconds)
        self.write(b'\x45\x78\x69\x74\0\0\0\0')
        self.mode_clear(_SM_TESTS)

    # Given a directory apply any patch files found. Applied in alphabetical
    # order.
    def patch(self, loc=None):
        if loc is None:
            mp = self._mp
            if mp is None:
                raise ValueError('No patch location')
            loc = ''.join((mp, 'plugins')) if mp.endswith('/') else ''.join((mp, '/plugins'))
        elif loc.endswith('/'):
            loc = loc[:-1]
        for f in sorted(os.listdir(loc)):
            f = ''.join((loc, '/', f))
            print('Patching', f)
            with open(f, 'rb') as s:
                self._patch_stream(s)
        print('Patching complete.')
