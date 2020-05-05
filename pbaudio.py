# pbaudio.py VS1053b driver demo/test for Pyboard

# (C) Peter Hinch 2020
# Released under the MIT licence

from vs1053 import *
from machine import SPI, Pin
import uasyncio as asyncio

# 128K conversion
# ffmpeg -i yellow.flac -acodec libmp3lame -ab 128k yellow.mp3
# VBR conversion
# ffmpeg -i yellow.flac -acodec libmp3lame -qscale:a 0 yellow.mp3
# Yeah, I know. I like Coldplay...

spi = SPI(2)  # 2 MOSI Y8 MISO Y7 SCK Y6
reset = Pin('Y5', Pin.OUT, value=1)  # Active low hardware reset
xcs = Pin('Y4', Pin.OUT, value=1)  # Labelled CS on PCB, xcs on chip datasheet
sdcs = Pin('Y3', Pin.OUT, value=1)  # SD card CS
xdcs = Pin('Y2', Pin.OUT, value=1)  # Data chip select xdcs in datasheet
dreq = Pin('Y1', Pin.IN)  # Active high data request
player = VS1053(spi, reset, dreq, xdcs, xcs, sdcs, '/fc')

async def main():
    player.volume(-10, -10)  # -10dB (0dB is loudest)
    locn = '/fc/'
    fmt = 'pins {} byte rate {} decode time {}s'
    # locn = '/sd/music/'
    #await player.sine_test()  # Cattles volume
    #player.volume(-10, -10)  # -10dB (0dB is loudest)
    with open(locn + 'panic.mp3', 'rb') as f:
        # Demo concurrency and cancellation
        asyncio.create_task(player.play(f))
        for _ in range(20):
            await asyncio.sleep(1)
            print(fmt.format(player.pins(), player.byte_rate(), player.decode_time()))
        await player.cancel()
        print('Cancelled')
    # player.mode_set(SM_EARSPEAKER_LO | SM_EARSPEAKER_HI)  # You decide.
    # player.response(bass_freq=150, bass_amp=15)  # This is extreme.
    with open(locn + 'yellow_v.mp3', 'rb') as f:
        await player.play(f)
    with open(locn + 'panic.mp3', 'rb') as f:
        await player.play(f)

asyncio.run(main())
