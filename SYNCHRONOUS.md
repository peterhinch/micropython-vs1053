# 1. Synchronous device driver for VS1053b

This driver is preferred for slow platforms such as ESP8266. It is a blocking
driver: the `play` command will block for the duration of an MP3 file. It has
been tested on an ESP8266 and ESP32. It will play 128Kbps and VBR MP3 files
with the CPU running at stock frequency.

Playback of CD quality audio may be achieved using FLAC files. Owing to the
data rates a Pyboard host is required. The supplied plugin is necessary.

Recording to a file is also supported.

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

Copy the following files from the `synchronous` directory to the target
filesystem:
 * `vs1053_syn.py` The driver
 * `sdcard.py` SD card driver (in root directory). See below.
Optional test scripts (these differ in pin numbering):
 * `pbaudio_syn.py` For Pyboards. Plays back FLAC files.
 * `esp8266_audio.py` For ESP8266. MP3 playback.
 * `esp32_audio.py` ESP32. MP3 playback.
 * `rectest.py` Recording test script.

Playback scripts will need to be adapted for your MP3 files. They assume
files stored on an SD card in the board's socket. Adapt scripts for files
stored elsewhere - this has been tested with MP3's on the Pyboard SD card.

The SD card driver is provided because the official version currently has
[a bug](https://github.com/micropython/micropython/pull/6007).

# 4. Typical usage

This assumes an SD card fitted to the board with a file `music.mp3`:
```python
from vs1053_syn import *
from machine import SPI, Pin
import uasyncio as asyncio

reset = Pin('Y5', Pin.OUT, value=1)  # Active low hardware reset
sdcs = Pin('Y4', Pin.OUT, value=1)  # SD card CS
xcs = Pin('Y3', Pin.OUT, value=1)  # Labelled CS on PCB, xcs on chip datasheet
xdcs = Pin('Y2', Pin.OUT, value=1)  # Data chip select xdcs in datasheet
dreq = Pin('Y1', Pin.IN)  # Active high data request
player = VS1053(SPI(2), reset, dreq, xdcs, xcs, sdcs, '/fc')

def main():
    player.volume(-10, -10)  # Volume -10dB (0,0 is loudest)
    with open('/fc/music.mp3', 'rb') as f:
        player.play(f)

main()
```
## 4.1 FLAC files

To play CD quality FLAC files, the supplied plugin must be installed. The
simplest way is to copy the `plugins` directory and its contents to the compact
flash card installed on the Adafruit board. Installation is then done by
issuing `.patch()` after instantiation:
```python
player = VS1053(SPI(2), reset, dreq, xdcs, xcs, sdcs, '/fc')
player.patch()
```
Because of performance limitations this requires a Pyboard host.

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
 * `cancb` A callback normally returning `True`. If it returns `False` while an
 MP3 is playing, playback will be cancelled. The callback should return as fast
 as possible: any delay is likely to affect playback.

## 5.2 Methods

##### Audio

 * `play` Arg `s` a stream providing MP3 data. Plays the stream. Blocks until
 the stream is complete or cancellation occurs.
 * `cancel` No args. Cancels the currently playing track.
 * `record` Record audio. See [Section 8](./SYNCHRONOUS.md#8-recording).
 * `sine_test` Arg `seconds=10` Plays a 517Hz sine wave for the specified time.
 Blocks until complete. This test sets the volume to maximum, leaving it at
 that level after exit.
 * `volume` Args `left`, `right`, `powerdown=False` The `left` and `right`
 values are in dB with 0dB being the maximum and -63.5dB or below being silent.
 Out of range values are constrained to those limits. The `powerdown` arg puts
 the chip into a low power mode, cleared when `volume` is called with
 `powerdown` omitted.
 * `response` Sets bass boost and/or treble boost/cut. See
 [below](./SYNCHRONOUS.md#521-setting-the-frequency-response).

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
 [below](./SYNCHRONOUS.md#53-mode).
 * `mode_set` Arg `bits` Set specific mode bits.
 * `mode_clear` Arg `bits` Clear specific mode bits.
 * `reset` No arg. Issues a hardware reset to the VS1053 then `soft_reset`.
 * `soft_reset` No arg. Software reset of the VS1053.
 * `patch` Optional arg `loc` a directory containing plugin files for the chip.
 The default directory is `/plugins` on the mounted flash card. Plugins are
 installed in alphabetical order.  See [Plugins](./SYNCHRONOUS.md#7-plugins).

### 5.2.1 Setting the frequency response

The `response` synchronous method takes the following optional keyword only
args. If no args are supplied, response will be set to flat.
 * `treble_amp` range -12dB to +10.5db. If zero, treble response will be flat.
 * `treble_freq` range 1000Hz to 15000Hz: lowest frequency of treble filter.
 * `bass_amp` range 0dB to +15dB. If zero, bass response will be flat.
 * `bass_freq` range 20Hz to 150Hz. Sets lower limit frequency. The datasheet
 section 9.6.3 suggests setting this to 1.5 times the lowest frequency the
 audio system can reproduce.

Out of range args will be constrained to in-range values.

The datasheet states "The Bass Enhancer ... is a powerful bass boosting DSP
algorithm, which tries to take the most out of the users earphones without
causing clipping".

## 5.3 Mode

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
 * `SM_LAYER12` Enable MPEG layer 1 and 2 decode. Untested.
 See [section 6](./SYNCHRONOUS.md#6-data-rates).
 * `SM_DIFF` Inverts the left channel. Used for differential mono output.

`EarSpeaker` processing claims to move the sound stage in front of the listener
when using headphones. Clearing both bits (the default) disables this.
Increasing values of this 2-bit field denote higher levels of processing, so
setting both bits invokes the maximum degree.

Users should note the warning in section 9.6.1 of the datasheet:  
"If you enable Layer I and Layer II decoding, you are liable for any patent
issues that may arise."

# 6. Data rates

The task of reading data and writing it to the VS1053 makes high demands on the
host hardware to support the necessary throughput.

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

The VS1053 can support lossless FLAC files with a plugin. However the data rate
for FLAC files is about 1Mbps which would give an overhead of 222ms/s or 22.5%.
This is the irreducible overhead caused by bus transfers, and takes no account
of the Python code. WAV files are typically twice as bad. In testing neither
played on an ESP32.

FLAC files played correctly on a Pyboard. WAV files were not tested. There is
no reason to use them as they may be converted to FLAC without loss of quality.

## 6.2 Test results

Testing was done using the onboard SD card adaptor on the Adafruit board. Stock
CPU frequency was used.

Pyboards, ESP8266 and ESP32 work with this driver with MP3 files recorded at up
to 256Kbps and VBR. Pyboards also work with FLAC files (using the plugin).

# 7. Plugins

These binary files provide a means of installing enhancements and bug fixes on
the VS1053. These are stored in RAM so need to be loaded after a power cycle.
The only plugin I have tested is the FLAC plugin.

The current FLAC driver `vs1053b-patches-flac.plg` does not work. An older
version `flac_plugin.bin` is included which does.

For some reason installing the FLAC plugin takes some 17s on ESP32 while being
almost instant on a Pyboard. Plugins may be found on the
[VLSI solutions](http://www.vlsi.fi/en/support/software/vs10xxpatches.html) site.

# 8. Recording

Mono sound from a microphone or stereo sound from a line input may be recorded.
The only file format supported by this driver is
[IMA ADPCM](https://wiki.multimedia.cx/index.php?title=IMA_ADPCM): the chip
compresses the data, reducing the data rate which must be handled by the host.
Depending on host performance sample rates ranging from 8000sps up to around
25Ksps may be employed.

Subjectively 8000sps provides very clear speech, albeit with some loss of high
frequencies. A rate of 25Ksps yields good quality audio with good high
frequency response. However the Nyquist theorem implies that it cannot be
audiophile quality.

The files produced can be played back on the VS1053; they have also been tested
on Linux audio players with one anomaly. See
[section 8.3](./SYNCHRONOUS.md#83-test-results).

A 10s mono speech recording from the line input may be done as follows:
```python
from vs1053_syn import *
from machine import SPI, Pin

spi = SPI(2)  # 2 MOSI Y8 MISO Y7 SCK Y6
reset = Pin('Y5', Pin.OUT, value=1)  # Active low hardware reset
xcs = Pin('Y4', Pin.OUT, value=1)  # Labelled CS on PCB, xcs on chip datasheet
sdcs = Pin('Y3', Pin.OUT, value=1)  # SD card CS
xdcs = Pin('Y2', Pin.OUT, value=1)  # Data chip select xdcs in datasheet
dreq = Pin('Y1', Pin.IN)  # Active high data request
player = VS1053(spi, reset, dreq, xdcs, xcs, sdcs=sdcs, mp='/fc')

fn = '/fc/test_rec.wav'

def main(t=10):
    print('Recording for {}s'.format(t))
    overrun = player.record(fn, True, t * 1000, 8000, stereo=False)
    print('Record complete')
    if overrun > 768:
        print('High data rate: loss may have occurred. Value = {}'.format(overrun))
    player.reset()  # Necessary before playback
    print('Playback')
    player.volume(-10, -10)  # -10dB (0dB is loudest)
    with open(fn, 'rb') as f:
        player.play(f)

main()
```

## 8.1 Wiring

This is as per [section 2](./SYNCHRONOUS.md#2-wiring) with the addition of the
microphone or line connection. The mic is connected between Adafruit JP3 pins
2 and 3. For line input the two channels are connected to Adafruit JP3 pins 1
and 2 as below. n/c indicates no connection.

| Chip pin/label | Adafruit     | Microphone | Line |
|:--------------:|:------------:|:----------:|:----:|
| 48 LINE 2      | JP3/1 LINE 2 |            |  L   |
| 1 MICP/Linein  | JP3/2 MIC+   |  +         |  R   |
| 2 MICN         | JP3/3 MIC-   |  -         | n/c  |
| Various        | JP3/4 AGND   | Gnd        | Gnd  |

The Adafruit pins connect directly to the chip. The chip data section 6
recommends circuitry between these audio signals and the chip for capacitive
coupling and filtering.

Line input signals should be restricted to 2.5Vp-p (data section 4.3) and mic
amplitude should be limited to 48mV p-p to avoid distortion.

Note microphone inputs are sensitive; precautions should be taken to minimise
noise and hum pickup.

## 8.2 The record method

This takes the following args:
 * `fn` Path and name of file for recording.
 * `line` `True` for line input, `False` for microphone.
 * `stop=10_000` If an integer is passed, recording will continue for that
 duration in ms. If a function is passed, recording will stop if the function
 returns `True`. The function should execute fast, otherwise the maximum
 recording speed will be reduced.
 * `sf=8000` Sample rate in samples/sec.
 * `agc_gain=None` See **gain** below.
 * `gain=None` See **gain** below.
 * `stereo=True` Set `False` for mono recording (halves file size).

Return value: `overrun`. An integer indicating the likelihood of data loss due
to excessive sample rate. Values < 768 indicate success. The closer the value
to 1024 the greater the likelihood of loss.

After recording, to return to playback mode the `.reset` method should be run.

#### Gain

The chip defines unity gain as a value of 1024. The gain range is linear, from
1 to 65535, with 0 having a special meaning. Hence a value of 1 corresponds to
a gain of 1/1024 and a value of 65535 is a gain of 64. The driver uses values
in dB which it converts to linear. The range is -60dB to +36dB; out of range
values are constrained to in-range figures. A value of `None` produces the 0
value whose meaning is discussed below.

Recording may be done at fixed gain or using AGC (automatic gain control). The
latter is usually preferred for speech: it adjusts the gain to compensate for
variations in the speaker's volume.

To use AGC, `gain` should be set to `None`. Then `agc_gain` sets the maximum
gain that may be employed by the AGC. An `agc_gain` value of `None` allows the
full range. For example an `agc_gain` value of 6 would allow the AGC to vary
gain to a maximum of +6dB.

To use a fixed gain (e.g. for music) `agc_gain` should be set to `None`, with
a numeric value of `gain` specifying the required gain. Thus a value of 10 will
provide a fixed gain of 10dB.

## 8.3 Test results

To date testing has only be done on Pyboards. It is likely that ESP32 and
ESP8266 will only work at low data rates.

On a Pyboard 1.1 recording worked without loss at rates of up to and including
25K samples/s stereo. A sample rate of 32Ksps resulted in `record` returning
`overrun` values over 768 and audio with clear artifacts.

Recording at 8000sps produces about 4KiB/s for mono files, 8KiB/s for stereo.
Both mono and stereo files play back correctly on the VS1053b. Stereo files
also played back on the Linux players tested. Mono files played on VLC but not
on rhythmbox. It is likely that the file header is incorrect but despite some
effort I have failed to identify the problem.
