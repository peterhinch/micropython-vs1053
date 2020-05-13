# rectest.py VS1053b driver demo/test for Pyboard
# Records 10s of audio at 8000sps then replays it
# (C) Peter Hinch 2020
# Released under the MIT licence

from vs1053_syn import *
from machine import SPI, Pin

spi = SPI(2)  # 2 MOSI Y8 MISO Y7 SCK Y6
reset = Pin('Y5', Pin.OUT, value=1)  # Active low hardware reset
xcs = Pin('Y4', Pin.OUT, value=1)  # Labelled CS on PCB, xcs on chip datasheet
sdcs = Pin('Y3', Pin.OUT, value=1)  # SD card CS
xdcs = Pin('Y2', Pin.OUT, value=1)  # Data chip select xdcs in datasheet
dreq = Pin('Y1', Pin.IN)  # Active high data request
player = VS1053(spi, reset, dreq, xdcs, xcs, sdcs=sdcs, mp='/fc')

fn = '/fc/stereo_8k.wav'

def main(t=10):
    print('Recording for {}s'.format(t))
    overrun = player.record(fn, True, t * 1000, 8000)  #, stereo=False)
    print('Record complete')
    if overrun > 768:
        print('High data rate: loss may have occurred. Value = {}'.format(overrun))
    player.reset()  # Necessary before playback
    print('Playback')
    with open(fn, 'rb') as f:
        player.play(f)

main()
