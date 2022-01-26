from machine import SoftI2C, Pin

I2C_SCL = 22
I2C_SDA = 21


class I2CController:
    def __init__(self) -> None:
        self.i2c = SoftI2C(scl=Pin(I2C_SCL), sda=Pin(I2C_SDA))
