from machine import Pin

from light_controller import LightStripController
from sound_controller import SoundController
from config_controller import ConfigController
from sdcard_controller import SDCardController
from movement_controller import MovementController
from lightsaber_controller import LightSaberController
from i2c import I2CController
from spi import SPIController
from button_controller import ButtonController
from light_strip_1 import LightStrip1
from light_strip_2 import LightStrip2
from light_strip_3 import LightStrip3
from light_strip_4 import LightStrip4

# NEO Pixel
# SD Card VSPI
# # https://randomnerdtutorials.com/esp32-microsd-card-arduino/
# IMU MPU9250 I2C address 0x68
# # https://randomnerdtutorials.com/esp32-i2c-communication-arduino-ide/
# Audio MAX98357A I2S
# LED Status
# SD Card
# Light
# # TODO: Have all light strips on a single write cycle, that way any timing and waiting are synchronized
# # TODO: Alternatively Have timers and interrupts for each strip


spi_controller = SPIController()
sd = SDCardController(spi_controller)

i2c_controller = I2CController()
mc = MovementController(i2c_controller)

sc = SoundController()
cc = ConfigController()

# TODO: Write animations for each strip
# TODO: Read animations for each strip
# TODO: Have animations run simultaneously across all strips (May need timer to keep in sync and have regular write intervals)
# TODO: Get sound to work in sync with lights with volume control
# TODO: Get movements working better


lstrip1 = LightStrip1()
lstrip2 = LightStrip2()
lstrip3 = LightStrip3()
lstrip4 = LightStrip4()

ls1 = LightSaberController(lstrip1.lc, mc, cc, sc)
ls2 = LightSaberController(lstrip2.lc, mc, cc, sc)
ls3 = LightSaberController(lstrip3.lc, mc, cc, sc)
ls4 = LightSaberController(lstrip4.lc, mc, cc, sc)

LED_STATUS_PIN = 16
led_status = Pin(LED_STATUS_PIN, Pin.OUT)

bc = ButtonController(ls1, led_status)
