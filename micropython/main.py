from machine import Pin

from light_strip import LightStrip1, LightStrip2, LightStrip3, LightStrip4
from light_controller import LightStripController
from sound_controller import SoundController
from config_controller import ConfigController
from sdcard_controller import SDCardController
from movement_controller import MovementController
from lightsaber_controller import LightSaberController
from i2c import I2CController
from spi import SPIController
from button_controller import ButtonController

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

# LightStripController relies on LightStrip


lsc1 = LightStripController(LightStrip1)
lsc2 = LightStripController(LightStrip2)
lsc3 = LightStripController(LightStrip3)
lsc4 = LightStripController(LightStrip4)

ls1 = LightSaberController(lsc1, mc, cc, sc)
ls2 = LightSaberController(lsc2, mc, cc, sc)
ls3 = LightSaberController(lsc3, mc, cc, sc)
ls4 = LightSaberController(lsc4, mc, cc, sc)

LED_STATUS_PIN = 16
led_status = Pin(LED_STATUS_PIN, Pin.OUT)

bc = ButtonController(ls1, led_status)
