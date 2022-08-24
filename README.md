# 1. Device drivers for VS1053b

The VS1053b is an audio player capable of handling MP3 files. Development was
done with this [Adafruit breakout](https://www.adafruit.com/product/1381). This
includes an SD card adaptor which may be used to store MP3 files. MP3 bit rates
up to 256Kbps and VBR (variable bit rate) files are supported. Adafruit "Music
Maker" Arduino shields have also been used with a MicroPython host running
these drivers.

It should be noted that these drivers run the adaptor board's SD card at a
higher clock rate than the official SD card driver. If this slot is used, good
quality SD cards should be used.

The interface uses seven I/O pins. However the Adafruit card provides 8 GPIO
pins which are supported by the driver. You gain a pin :).

There are two versions of the driver: synchronous and asynchronous. The
asynchronous version uses `uasyncio` to enable tasks (such as a GUI interface)
to run concurrently while playing audio files. Sadly the overhead of `uasyncio`
prevents audio playback on ESP8266 and ESP32.

### [Asynchronous driver docs](./ASYNC.md)

The synchronous driver has been tested on ESP8266 and ESP32. On Pyboards and
te Pio CD quality audio may be achieved using FLAC files.

### [Synchronous driver docs](./SYNCHRONOUS.md)

Compatibility matrix:

| Platform     | Synchronous    | Asynchronous   |
|:-------------|:---------------|:---------------|
| Pyboard      | FLAC           |                |
| (1.x and D)  | VBR MP3        | VBR MP3        |
|              | MP3 <= 256Kbps | MP3 <= 256Kbps |
| Pyboard Lite | Not yet tested | MP3 <= 128Kbps |
| Pico         | FLAC, VBR MP3, | FLAC, VBR MP3, |
|              | MP3 <= 256Kbps | MP3 <= 256Kbps |
| ESP32        | MP3 <= 256Kbps | Unsupported    |
| ESP8266      | MP3 <= 256Kbps | Unsupported    |

Where a platform supports VBR MP3 it will also support 256Kbps MP3.

The synchronous driver also supports recording audio to an IMA ADPCM `wav` file
which can be played by the VS1053b or by other applications.
