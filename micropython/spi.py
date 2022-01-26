from machine import Pin, SoftSPI

SPI_MOSI = 23
SPI_CLK = 18
SPI_MISO = 19


class SPIController:
    def __init__(self) -> None:
        self.spi = SoftSPI(
            -1,
            sck=Pin(SPI_CLK),
            mosi=Pin(SPI_MOSI),
            miso=Pin(SPI_MISO)
        )
