# Review of adafruit_vs1053.py

I studied this as the initial source of my asynchronous MicroPython solution. I
made significant changes and enhancements some of which which you may wish to
backport.

These were my objectives:  
 * Use asynchronous methods where appropriate.
 * Code in a cross-platform manner aiming for efficiency.
 * Check all code against the device data.
 * Remove CircuitPython dependencies.
 * Rename constants to match the datasheet.
 * Access SPI bus and pins directly rather than via CircuitPython arbitration.
 * Replace properties with methods in accordance with MicroPython practice.
 * Add functionality and make some methods more user friendly.

In the following, `CP` refers to `adafruit_vs1053.py`.

# Timing

Timing and SPI bus rate are crucial. An asynchronous solution is at an inherent
disadvantage owing to scheduling overheads: you may well achieve better results
with a synchronous design. But be aware that mine does not deliver acceptable
audio on ESPx platforms.

# Baudrate and clock rate

CP accesses command registers
[at 250Kbps](https://github.com/adafruit/Adafruit_CircuitPython_VS1053/blob/0676a052d65a169ca15f42006c1f5f129634b0be/adafruit_vs1053.py#L69)
with the comment "(MUST be slow)". I found nothing in the datasheet to justify
this. I use 1Mbps initially, increasing it for all transfers once the
`SCI_CLOCKF` register has been set.

After reset the internal clock runs at 12.288MHz. Datasheet section 7.4.4
states "the maximum speed for SCI reads is CLKI/7". I can't see from the timing
diagram how this figure of 7 is calculated. But they are the designers. Reading
from registers is not performance critical so I use this figure to determine
the rate for all register accesses.

Hence the maximum initial baudrate is 12.288/7 = 1.75MHz.  

I set the `SCI_CLOCKF` to 0x8800 (a multiplier of 3.5) as this corresponds to a
datasheet recommendation (section 4.2 footnote 4).
[CP uses 0x6000](https://github.com/adafruit/Adafruit_CircuitPython_VS1053/blob/0676a052d65a169ca15f42006c1f5f129634b0be/adafruit_vs1053.py#L171).

After setting the multiplier to 3.5 the maximum SCI (register) read speed is  
12.288*3.5/7=6.144MHz  

The maximum SDI (data) write speed is  
12.288*3.5/4=10.752MHz (data section 7.3.2).

I specify 10.752MHz for data, 5MHz for commands. The way I do this causes the
SD card to be clocked at up to 10.752MHz. This is much higher than the rate of
1.32MHz set by the official SD card driver. My reading suggests that modern SD
cards can be clocked at 25MHz. I would welcome comments on this.

## SPI bus

The actual clock rate is typically less than the specified one. A Pyboard Lite
runs at 6MHz, a Pyboard D at 9MHz, a Pyboard 1.x at 10.5MHz. There is a
difference in the behaviour of hard SPI interfaces between Pyboards and the
ESP8266. All Pyboards clock a buffer out at a constant rate. By contrast the
ESP8266 issues a byte at the specified rate, interposing a 7μs gap between each
byte. This (and probably other latencies) prevents successful operation.

# sdcard.py

The official version doesn't work if the bus is shared. This
[PR](https://github.com/micropython/micropython/pull/6007) is under review to
fix this. Comments welcome.

# Code review

 * This
 [comment](https://github.com/adafruit/Adafruit_CircuitPython_VS1053/blob/0676a052d65a169ca15f42006c1f5f129634b0be/adafruit_vs1053.py#L147)
 seems spurious.
 * `.reset` At 200ms total the sleep time is conservative.
 * `.reset` The setting of `_VS1053_REG_CLOCKF` on
 [line 171](https://github.com/adafruit/Adafruit_CircuitPython_VS1053/blob/0676a052d65a169ca15f42006c1f5f129634b0be/adafruit_vs1053.py#L171)
 is not optimal (see above).
 * `.set_volume` You might like to backport my solution which uses dB values.
 *`.ready_for_data` Given that this is performance critical it might be worth
 reviewing whether a property is the best approach. Should it be inlined?
 * `.decode_time` The code doesn't match the (correct) comment (data 9.6.5).
 * `.sine_test` I simplified this without obvious ill-effects. It uses maximum
 volume and a fixed frequency, and leaves the volume at max. My view is that
 this is OK if documented but you may wish to vary this. It also seemed wise to
 clear the `_SM_TESTS` mode bit on exit.

## Mode handling

The use of the `_VS1053_REG_MODE` register should be reviewed. The
`_VS1053_MODE_SM_SDINEW` bit should be set on reset and never cleared. I have
methods to set and clear bits which ensure this.

## Playback

This doesn't match the datasheet and (in my opinion) needs thorough review.
Here is my take on the requirements.

The device's FIFO control is crude. There is no way to check its state other
than the DREQ pin; when asserted the buffer can accept at least 32 bytes. Not
ideal for high performance.

The algorithm is therefore to wait on DREQ and send 32 bytes (or fewer, if at
the end of a track) repeating until at the end of data. This suggests that
checking DREQ should be fast and efficient, and the splitting of the datastream
should be fast and non-allocating. In my view these processes should be done in
the driver rather than by the caller, especially in code aimed at being
beginner friendly.

The end of a track, and cancellation of playback, require rather involved
sequences which I have attempted to implement (data 10.5.1 and 10.5.2). Playing
consecutive tracks and playing a track after cancelling a prior one occur with
no audible problems. But I'd welcome any comments as I may well have missed
something.

## Backport options

You may be interested in checking out other features which I have implemented
including support for the I/O pins. Also the bass and treble control with
meaningful Hz and (relative) dB values.
