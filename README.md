# 1. Device drivers for VS1053b

The VS1053b is an audio player capable of handling MP3 files. Development was
done with this [Adafruit breakout](https://www.adafruit.com/product/1381). This
includes an SD card adaptor which may be used to store MP3 files. MP3 bit rates
up to 256Kbps and VBR (variable bit rate) files are supported. Adafruit "Music
Maker" Arduino shields [e.g. this one](https://www.adafruit.com/product/1790)
have also been used with a MicroPython host running these drivers.

It should be noted that these drivers run the adaptor board's SD card at a
higher clock rate than the official SD card driver. If this slot is used, good
quality SD cards should be used.

The interface uses seven I/O pins. However the Adafruit card provides 8 GPIO
pins which are supported by the driver. You gain a pin :).

There are two versions of the driver: synchronous and asynchronous. The
asynchronous version uses `uasyncio` to enable tasks (such as a GUI interface)
to run concurrently while playing audio files. Sadly the overhead of `uasyncio`
prevents audio playback on ESP8266.

## 1.1 Version log

V0.1.5 Aug 2022 Asynchronous version has an optional buffered mode. This may
improve performance. It overcomes an apparent firmware bug which prevents the
normal version from working on ESP32.

V0.1.4 Aug 2022 The performance of the asynchronous driver is substantially
improved, with some improvement to the synchronous driver. Both drivers have
the means to enable I2S output from the VS1053b chip.

### [Asynchronous driver docs](./ASYNC.md)

The synchronous driver has been tested on ESP8266 and ESP32. On Pyboards and
the Pio CD quality audio may be achieved using FLAC files.

### [Synchronous driver docs](./SYNCHRONOUS.md)

# 2. Compatibility matrix

Music formats (lower MP3 rates exist but aren't considered music quality).

| Format   | Bits/s   | Bytes/s | Notes            |
|:---------|:---------|:--------|:-----------------|
| CD       | 1.4M     | 176.4K  |                  |
| FLAC     | 700K     | 88.2K   | CD quality       |
| MP3 320K | 320K     | 40K     | Maximum MP3 rate |
| MP3 VBR  | 220-260K | <= 33K  | V0 Variable rate |
| MP3 250K | 250K     | 31.25K  |                  |
| MP3 192K | 192K     | 24K     |                  |
| MP3 128K | 128K     | 16K     |                  |

The capability of the platform and driver combination is defined by the maximum
rate that can be sustained. All lower rates can be assumed to work. In testing
the following were the highest usable rates:

| Platform     | Synchronous    | Asynchronous   |
|:-------------|:---------------|:---------------|
| Pyboard 1.x  | FLAC           | FLAC           |
| Pyboard D    | FLAC           | FLAC           |
| Pyboard Lite | Not yet tested | MP3 <= 128Kbps |
| Pico         | FLAC           | FLAC           |
| ESP32        | FLAC           | VBR            |
| ESP8266      | MP3 <= 256Kbps | Unsupported    |

The synchronous driver also supports recording audio to an IMA ADPCM `wav` file
which can be played by the VS1053b or by other applications.

[Converting FLAC to MP3](https://wiki.archlinux.org/title/Convert_FLAC_to_MP3)

# 3. Troubleshooting

Timeout messages, e.g. "timeout waiting for response", are indicative of an SD
card which cannot handle the required data rate. High quality cards are
essential.

Dropouts when using the asynchronous driver indicate that the driver can't
supply data at the required rate. This can result from user tasks which demand
too much processor time. Solutions are to reduce blocking, to use a lower MP3
bit rate or to use the synchronous driver.

# 4. Plugins

These are available from
[VLSI solutions](http://www.vlsi.fi/en/support/software/vs10xxpatches.html).
They have a `.plg` extension but are C source files, intended for linking with
user C applications. For use with Python these need to be converted to binary
files. The supplied `patch.bin` file provides FLAC decoding and possibly bug
fixes. It is current as of August 2022.

The following describes the simple hack I used to convert from
`vs1053b-patches-flac.plg` to `patch.bin`: this can be amended for other `.plg`
files.

Append the following code to the end of the `plg` file:
```C
#include <stdio.h>
void main(){
    FILE *file;
    file = fopen("patch.bin", "w");
    char c;
    int n;
    unsigned short v;
    n = 0;
    while (n < PLUGIN_SIZE){
        v = plugin[n++];
        c = v & 0xFF;
        putc(c, file);
        c = v >> 8;
        putc(c, file);
    }
    fclose(file);
}
```
Rename the file to have a `.c` extension, compile and run with:
```bash
$ mv vs1053b-patches-flac.plg vs1053b-patches-flac.c
$ gcc -o rats vs1053b-patches-flac.c
$ chmod a+x rats
$ ./rats
```
