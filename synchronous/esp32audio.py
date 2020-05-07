# esp32audio.py VS1053b driver demo/test for ESP32
# Uses synchronous driver.

# (C) Peter Hinch 2020
# Released under the MIT licence

from vs1053_syn import *
from machine import SPI, Pin, freq
import uasyncio as asyncio
# Works at stock speed
# freq(240_000_000)

# 128K conversion
# ffmpeg -i yellow.flac -acodec libmp3lame -ab 128k yellow.mp3
# VBR conversion
# ffmpeg -i yellow.flac -acodec libmp3lame -qscale:a 0 yellow_v.mp3
# Yeah, I know. I like Coldplay...

spi = SPI(2, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
reset = Pin(32, Pin.OUT, value=1)  # Active low hardware reset
xcs = Pin(33, Pin.OUT, value=1)  # Labelled CS on PCB, xcs on chip datasheet
sdcs = Pin(25, Pin.OUT, value=1)  # SD card CS
xdcs = Pin(26, Pin.OUT, value=1)  # Data chip select xdcs in datasheet
dreq = Pin(27, Pin.IN)  # Active high data request
player = VS1053(spi, reset, dreq, xdcs, xcs, sdcs, '/fc')
# player.patch()  # Optional. From /fc/plugins/

def main():
    player.volume(-10, -10)  # -10dB (0dB is loudest)
    locn = '/fc/'
    # locn = '/sd/music/'
    # player.sine_test()  # Cattles volume
    # player.volume(-10, -10)  # -10dB (0dB is loudest)
    # player.mode_set(SM_EARSPEAKER_LO | SM_EARSPEAKER_HI)  # You decide.
    # player.response(bass_freq=150, bass_amp=15)  # This is extreme.
    with open(locn + 'panic.mp3', 'rb') as f:
        player.play(f)
    with open(locn + 'yellow_v.mp3', 'rb') as f:  # A VBR file
        player.play(f)

main()
