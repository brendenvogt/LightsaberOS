import os
from sdcard import SDCard
from machine import Pin

SPI_CS = 5  # SD card


class SDCardController:

    def __init__(self, spi_controller) -> None:

        self.sd = SDCard(spi_controller.spi, Pin(SPI_CS))
        os.mount(self.sd, "/sd")

        # print('Root directory:{}'.format(os.listdir()))
        # vfs = os.VfsFat(self.sd)
        # os.mount(vfs, '/sd')

        print('Root directory:{}'.format(os.listdir()))
        os.chdir('sd')
        print('SD Card contains:{}'.format(os.listdir()))

        pass
