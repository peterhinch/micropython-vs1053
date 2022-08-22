# pico_syn.py VS1053b driver demo/test for RP2 Pico

# (C) Peter Hinch 2022
# Released under the MIT licence

from vs1053_mon_syn import *
from machine import SPI, Pin, UART
import time
import os
import monitor
monitor.set_device(UART(0, 1_000_000))

# 128K conversion
# ffmpeg -i yellow.flac -acodec libmp3lame -ab 128k yellow.mp3
# VBR conversion
# ffmpeg -i yellow.flac -acodec libmp3lame -qscale:a 0 yellow.mp3
# Yeah, I know. I like Coldplay...
can = Pin(16, Pin.IN, Pin.PULL_UP)
def cancb():
    return not can()

xcs = Pin(14, Pin.OUT, value=1)  # Labelled CS on PCB, xcs on chip datasheet
reset = Pin(15, Pin.OUT, value=1)  # Active low hardware reset
xdcs = Pin(2, Pin.OUT, value=1)  # Data chip select xdcs in datasheet
dreq = Pin(3, Pin.IN)  # Active high data request
sdcs = Pin(5, Pin.OUT, value=1)  # SD card CS
spi = SPI(0, sck=Pin(6), mosi=Pin(7), miso=Pin(4))
player = VS1053(spi, reset, dreq, xdcs, xcs, sdcs, '/fc', cancb)
#player.patch()  # Optional. From /fc/plugins

def main(locn):
    monitor.init()
    player.volume(-10, -10)  # -10dB (0dB is loudest)
    # player.mode_set(SM_EARSPEAKER_LO | SM_EARSPEAKER_HI)  # You decide.
    # player.response(bass_freq=150, bass_amp=15)  # This is extreme.
    songs = sorted([x[0] for x in os.ilistdir(locn) if x[1] != 0x4000])
    for song in songs:
        print(song)
        fn = '/'.join((locn, song))
        with open(fn, 'rb') as f:
            player.play(f)
            time.sleep(1)

main('/fc/192kbps')
