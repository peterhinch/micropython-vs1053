# 1. Device drivers for VS1053b

The VS1053b is an audio player capable of handling MP3 files. Development was
done with this [Adafruit breakout](https://www.adafruit.com/product/1381). This
includes an SD card adaptor which may be used to store MP3 files. MP3 bit rates
up to 256Kbps and VBR (variable bit rate) files are supported.

It should be noted that these drivers run the adaptor board's SD card at a
higher clock rate than the official SD card driver. If this slot is used, good
quality SD cards should be used.

The interface uses seven I/O pins. However the Adafruit card provides 8 GPIO
pins which are supported by the driver. You gain a pin :).

There are two versions of the driver: synchronous and asynchronous. The
asynchronous version uses `uasyncio` to enable tasks (such as a GUI interface)
to run concurrently while playing audio files. Sadly the overhead of
`uasyncio` prevents it from working properly on ESP8266 and ESP32.

### [Asynchronous driver docs](./ASYNC.md)

The synchronous driver has been tested on ESP8266 and ESP32. On Pyboards CD
quality audio may be achieved using FLAC files.

### [Synchronous driver docs](./SYNCHRONOUS.md)
