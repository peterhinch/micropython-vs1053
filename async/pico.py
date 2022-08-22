# pico.py VS1053 demo of asynchronous driver running on a RP2 Pico.
# Play all MP3 tracks found in a directory in the breakout board's SD card.

from machine import SPI, Pin
from vs1053 import *
import uasyncio as asyncio

xcs = Pin(14, Pin.OUT, value=1)  # Labelled CS on PCB, xcs on chip datasheet
reset = Pin(15, Pin.OUT, value=1)  # Active low hardware reset
xdcs = Pin(2, Pin.OUT, value=1)  # Data chip select xdcs in datasheet
dreq = Pin(3, Pin.IN)  # Active high data request
sdcs = Pin(5, Pin.OUT, value=1)  # SD card CS
spi = SPI(0, sck=Pin(6), mosi=Pin(7), miso=Pin(4))
player = VS1053(spi, reset, dreq, xdcs, xcs, None, '/fc')  #sdcs, '/fc')

import sdcard
import os
sd = sdcard.SDCard(spi1:=SPI(1,sck=Pin(10), mosi=Pin(11), miso=Pin(8)), Pin(9, Pin.OUT, value=1))
vfs = os.VfsFat(sd)
os.mount(vfs, '/fc')
spi1.init(baudrate=10_000_000)

player.patch()  # Optional. From /fc/plugins

async def heartbeat():
    led = Pin(25, Pin.OUT)
    while(True):
        led(not(led()))
        await asyncio.sleep_ms(500)

async def can_it():  # Cancel 1st song after 10 secs
    await asyncio.sleep(10)
    print('Cancelling playback')
    await player.cancel()
    print('Cancelled')

async def main(locn, cancel):
    asyncio.create_task(heartbeat())
    if cancel:
        asyncio.create_task(can_it())
    player.volume(-10, -10)  # -10dB (0dB is loudest)
    # player.mode_set(SM_EARSPEAKER_LO | SM_EARSPEAKER_HI)  # You decide.
    # player.response(bass_freq=150, bass_amp=15)  # This is extreme.
#    songs = sorted([x[0] for x in os.ilistdir(locn) if x[1] != 0x4000])
    songs = ['07 - Stainsby Girls.flac', "04 - Fool (If You Think It's Over).flac"]
    while True:
        for song in songs:
            print(song)
            with open('/'.join((locn, song)), 'rb') as f:
                await player.play(f)  # Ends or is cancelled
                await asyncio.sleep(1)  # Gap between tracks
    print('All done.')

#asyncio.run(main('/fc/192kbps', True))
asyncio.run(main('/fc', False))
