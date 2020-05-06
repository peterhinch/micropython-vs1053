# esp8266audio_syn.py VS1053b driver demo/test for ESP8266
# Uses synchronous driver.

# (C) Peter Hinch 2020
# Released under the MIT licence

from vs1053_syn import *
from machine import SPI, Pin, freq

# It works at stock speed, even with VBR files.
# freq(160_000_000)

# Available pins 0, 2, 4, 5, 12, 13, 14, 15, 16
# 128K conversion
# ffmpeg -i yellow.flac -acodec libmp3lame -ab 128k yellow.mp3
# VBR conversion
# ffmpeg -i yellow.flac -acodec libmp3lame -qscale:a 0 yellow_v.mp3
# Yeah, I know. I like Coldplay...

spi = SPI(1) # sck=Pin(14), mosi=Pin(13), miso=Pin(12))
reset = Pin(5, Pin.OUT, value=1)  # Active low hardware reset
xcs = Pin(4, Pin.OUT, value=1)  # Labelled CS on PCB, xcs on chip datasheet
sdcs = Pin(2, Pin.OUT, value=1)  # SD card CS
xdcs = Pin(0, Pin.OUT, value=1)  # Data chip select xdcs in datasheet
dreq = Pin(15, Pin.IN)  # Active high data request
player = VS1053(spi, reset, dreq, xdcs, xcs, sdcs=sdcs, mp='/fc')

def main():
    player.volume(-10, -10)  # -10dB (0dB is loudest)
    locn = '/fc/'
    # locn = '/sd/music/'
    # player.sine_test()  # Cattles volume
    # player.volume(-10, -10)  # -10dB (0dB is loudest)
    # player.mode_set(SM_EARSPEAKER_LO | SM_EARSPEAKER_HI)  # You decide.
    # player.response(bass_freq=150, bass_amp=15)  # This is extreme.
    with open(locn + 'yellow_v.mp3', 'rb') as f:  # A VBR file
        player.play(f)
    with open(locn + 'panic.mp3', 'rb') as f:
        player.play(f)

main()
