from machine import SPI, Pin, freq
import uasyncio as asyncio
import monitor
monitor.set_device(UART(0, 1_000_000))

reset = Pin(15, Pin.OUT, value=1)  # Active low hardware reset
sdcs = Pin(5, Pin.OUT, value=1)  # SD card CS
xcs = Pin(14, Pin.OUT, value=1)  # Labelled CS on PCB, xcs on chip datasheet
xdcs = Pin(2, Pin.OUT, value=1)  # Data chip select xdcs in datasheet
dreq = Pin(3, Pin.IN)  # Active high data request
player = VS1053(SPI(0), reset, dreq, xdcs, xcs, sdcs, '/fc')

async def heartbeat():
    led = Pin(25, Pin.OUT)
    while(True):
        led(not(led()))
        await asyncio.sleep_ms(500)

async def main():
    monitor.init()
    player.volume(-10, -10)  # -10dB (0dB is loudest)
    locn = '/fc/192kbps/'
    asyncio.create_task(heartbeat())
    with open(locn + '01.mp3', 'rb') as f:
        await player.play(f)
    # player.mode_set(SM_EARSPEAKER_LO | SM_EARSPEAKER_HI)  # You decide.
    # player.response(bass_freq=150, bass_amp=15)  # This is extreme.
    with open(locn + '02.mp3', 'rb') as f:
        await player.play(f)
    with open(locn + '03.mp3', 'rb') as f:
        await player.play(f)
    print('All done.')

asyncio.run(main())
