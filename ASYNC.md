# 1. Asynchronous device driver for VS1053b

The driver is asynchronous enabling other tasks (such as a GUI interface) to
run concurrently while playing audio files.

While the driver is cross-platform, testing on ESP8266 and ESP32 failed. It
works on Pyboard D, Pyboard 1.x and Pyboard Lite (the latter restricted to
128Kbps MP3 files). The synchronous driver works on ESP8266.

# 2. Wiring

Pin numbers and the SPI bus ID may be changed to suit different platforms. The
test script assumes a Pyboard host with the following wiring. Note `cs` denotes
an active low chip select, `nc` denotes no connection.

| VS1053 | Pyboard | Signal       |
|:------:|:-------:|:------------:|
| xdcs   | Y2      | Data cs      |
| sdcs   | Y3      | SD card cs (see below) |
| cs     | Y4      | Control cs (chip datasheet xcs) |
| rst    | Y5      | VS1053 hardware reset |
| sclk   | Y6      | SCK SPI bus 2 |
| mosi   | Y8      | MOSI         |
| miso   | Y7      | MISO         |
| gnd    | gnd     |              |
| 3v3    | nc      | 3.3V o/p     |
| vcc    | vcc     | 5V           |
| dreq   | Y1 I/P  | Data request |

If the board's SD card slot is not used the `sdcs` pin may be unconnected.

Headphones or an audio amplifier may be connected as follows:

| VS1053 | Audio |
|:------:|:-----:|
| agnd   | gnd   |
| lout   | left  |
| rout   | right |

The Adafruit adaptor may be powered from 5V or 3.3V.

# 3. Installation

Copy the following files to the target filesystem:
 * `vs1053.py` The driver
 * `sdcard.py` SD card driver. See below.
Optional test script:
 * `pbaudio.py` For Pyboards.

The test script will need to be adapted to reflect your MP3 files. It assumes
files stored on an SD card in the board's socket. Adapt the script for files
stored elsewhere - this has been tested with MP3's on the Pyboard SD card.

The SD card driver is provided because the official version currently has
[a bug](https://github.com/micropython/micropython/pull/6007).

# 4. Typical usage

This assumes an SD card fitted to the board with a file `music.mp3`:
```python
from vs1053 import *
from machine import SPI, Pin
import uasyncio as asyncio

reset = Pin('Y5', Pin.OUT, value=1)  # Active low hardware reset
sdcs = Pin('Y4', Pin.OUT, value=1)  # SD card CS
xcs = Pin('Y3', Pin.OUT, value=1)  # Labelled CS on PCB, xcs on chip datasheet
xdcs = Pin('Y2', Pin.OUT, value=1)  # Data chip select xdcs in datasheet
dreq = Pin('Y1', Pin.IN)  # Active high data request
player = VS1053(SPI(2), reset, dreq, xdcs, xcs, sdcs, '/fc')

async def main():
    player.volume(-10, -10)  # Volume -10dB (0,0 is loudest)
    with open('/fc/music.mp3', 'rb') as f:
        await player.play(f)

asyncio.run(main())
```

# 5. VS1053 class

## 5.1 Constructor

This takes the following mandatory args:
 * `spi` An SPI bus instance.
 * `reset` A `Pin` instance defined as `Pin.OUT` with `value=1`.
 * `dreq` A `Pin` instance defined as `Pin.IN`.
 * `xdcs` A `Pin` instance defined as `Pin.OUT` with `value=1`.
 * `xcs` A `Pin` instance defined as `Pin.OUT` with `value=1`.

Optional args - supply only if an SD card is fitted:
 * `sdcs` A `Pin` instance defined as `Pin.OUT` with `value=1`.
 * `mp` A string defining the mount point (e.g. `/fc`).

## 5.2 Asynchronous methods

 * `play` Arg `s` a stream providing MP3 data. Plays the stream with the task
 pausing until the stream is complete or cancellation occurs.
 * `cancel` No args. Cancels the currently playing track.
 * `sine_test` Arg `seconds=10` Plays a 517Hz sine wave for the specified time.
 The task pauses until complete. This test seems to set the volume to maximum,
 leaving it at that level after exit.

## 5.3 Synchronous methods

##### Audio

 * `volume` Args `left`, `right`, `powerdown=False` The `left` and `right`
 values are in dB with 0dB being the maximum and -63.5dB or below being silent.
 Out of range values are constrained to those limits. The `powerdown` arg puts
 the chip into a low power mode, cleared when `volume` is called with
 `powerdown` omitted.
 * `response` Sets bass boost and/or treble boost/cut. See
 [below](./ASYNC.md#531-setting-the-frequency-response).

##### I/O Pins

 * `pins_direction` Arg `bits`. The 8-bit mask defines the I/O pin direction, 1
 being output and 0 input.
 * `pins` Arg `data=None` If `data` is provided it issues the 8-bit value to
 the pins (if they are set to output). Returns the state of the pins.

##### Reporting

 * `version` No args. Returns version no. (currently 4).
 * `decode_time` No args. Returns the no. of seconds into the stream.
 * `byte_rate` No args. Returns the data rate in bytes/sec.

##### Special purpose

 * `mode` No args. Return the current mode (a 16 bit integer). See
 [below](./ASYNC.md#54-mode).
 * `mode_set` Arg `bits` Set specific mode bits.
 * `mode_clear` Arg `bits` Clear specific mode bits.
 * `reset` No arg. Issues a hardware reset to the VS1053 then `soft_reset`.
 * `soft_reset` No arg. Software reset of the VS1053.
 * `patch` Optional arg `loc` a directory containing patch files for the chip.
 The default directory is `/plugins` on the mounted flash card. Patch files are
 installed in alphabetical order. Note this process can take many seconds on
 some platforms.
 Plugins may be found on the
 [VLSI solutions](http://www.vlsi.fi/en/products/vs1053.html) site.

### 5.3.1 Setting the frequency response

The `response` synchronous method takes the following optional keyword only
args. If no args are supplied, response will be set to flat.
 * `treble_amp` range -12dB to +10.5db. If zero, treble response will be flat.
 * `treble_freq` range 1000Hz to 15000Hz: lowest frequency of treble filter.
 * `bass_amp` range 0dB to +15dB. If zero, bass response will be flat.
 * `bass_freq` range 20Hz to 150Hz. Sets lower limit frequency. The datasheet
 section 9.6.3 suggests setting this to 1.5 times the lowest frequency  the
 audio system can reproduce.
Out of range args will be constrained to in-range values.

The datasheet states "The Bass Enhancer ... is a powerful bass boosting DSP
algorithm, which tries to take the most out of the users earphones without
causing clipping".

## 5.4 Mode

The VS1053b provides various configuration options in the form of a 16 bit mode
value. Certain bits are reserved by the driver for its correct operation, but
some are user configurable. The driver exports these as constants which may be
set or cleared as follows. Note the combination of multiple settings using the
logical or `|`.

```python
from vs1053 import *
player = VS1053(...)  # Args omitted
player.mode_set(SM_EARSPEAKER_LO | SM_EARSPEAKER_HI)  # Constants from driver
# code omitted
player.mode_clear(SM_EARSPEAKER_LO | SM_EARSPEAKER_HI)  # Turn off EarSpeaker
```
Do not set or clear arbitrary bits: only use the provided constants. These
comprise:
 * `SM_EARSPEAKER_LO` EarSpeaker mode bits: see below.
 * `SM_EARSPEAKER_HI`
 * `SM_LAYER12` Enable MPEG layer 1 and 2 decode. Untested. Probably useless.
 See [section 6](./ASYNC.md#6-data-rates).
 * `SM_DIFF` Inverts the left channel. Used for differential mono output.
 * `SM_LINE_IN` Line/microphone input. Input is currently unsupported.

`EarSpeaker` processing claims to move the sound stage in front of the listener
when using headphones. Clearing both bits (the default) disables this.
Increasing values of this 2-bit field denote higher levels of processing, so
setting both bits invokes the maximum degree.

Users should note the warning in section 9.6.1 of the datasheet:  
"If you enable Layer I and Layer II decoding, you are liable for any patent
issues that may arise."

# 6. Data rates

The task of reading data and writing it to the VS1053 makes high demands on the
host hardware to support the necssary throughput. While the code is cross
platform it only produces good audio on high performing hosts.

## 6.1 Theory

MP3 files may be created with various data rates. Testing was done with files
having a 128Kbps rate. Note that this is the total rate for a stereo file. The
driver, after initialisation, sets the SPI bus baudrate to 10.752MHz. In
practice the rate may be less than that. Issuing `print(spi_instance)` will
show the actual rate on an individual platform. The Pyboard D runs it at 9MHz,
i.e. 111ns/bit (Pyboard 1.x is slightly faster). The following calculations are
based on 9MHz transfers.

For an Nbps data stream the time used by the bus in one second is 111N ns,
which is 14.2ms for a 128Kbps stream. However the stream is handled twice: once
in reading it from the SD card and again in writing it to the VS1053 giving an
overhead of 222N ns/s. Consequently the overhead is 28.4ms/s or 2.8%. I have
successfully tested MP3's having a 256Kbps rate and VBR files which have a
slightly higher rate.

The VS1053 can support lossles FLAC files with a plugin. However the data rate
for FLAC files is about 1Mbps which would give an overhead of 222ms/s or 22.5%.
This is the irreducibile overhead caused by bus transfers, and takes no account
of the Python code. FLAC playback from the SD card may be impossible. The twice
as bad WAV format is even more suspect.

## 6.2 Test results

Testing was done using the onboard SD card adaptor on the Adafruit board. Stock
CPU frequency was used except where stated.

On a Pyboard D or Pyboard 1.x the demo script worked with MP3 files including
256Kbps and VBR (variable bit rate) files.

The Pyboard Lite worked with 128Kbps files; 256Kbps and VBR (variable bit rate)
files exhibited distortion.

The ESP32, even at 240MHz, failed properly to decode any file. I suspect this
is a consequence of the underlying OS stealing processor timeslices.

The ESP8266 also failed at 160MHz. Hard SPI transfers one byte at a time, at a
bit rate of 8Mbps, but with a 7μs gap between each byte. The mean data rate is
about 1Mbps which needs to be divided by two as there are two devices on the
bus: the data source and the data sink. There are also periods of bus
inactivity lasting 3ms. Evidently the net rate is insufficient, even with a
128Kbps file, to leave time for the Python code.

## 6.3 Application design and blocking

In testing file reads from SD card sometimes block for over 4ms: this occurs
when a 512 byte sector is retrieved. This may vary with the quality of the SD
card.

Other tasks must limit the length of time for which they monopolise the
MicroPython VM. The VS1053 has a 2KiB buffer. A 128Kbps MP3 has a data rate of
16KiB/s so the buffer holds 125ms of data. If 256Kbps is used, this drops to
65ms. Given that `uasyncio` performs round-robin scheduling, this time is the
maximum allowable sum of the blocking time of all running tasks. If this is
exceeded the buffer will empty and distorted sound will result.

The driver uses the `uasyncio` IOStream mechanism. Currently this supports only
round-robin scheduling. I am [lobbying](https://github.com/micropython/micropython/issues/5857)
for an option to prioritise I/O, testing for readiness on every yield to the
scheduler. If this is implemented it will reduce the constraints on vs1053
application design.
