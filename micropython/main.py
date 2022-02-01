from machine import Pin

from light_strip import LightStrip1, LightStrip2, LightStrip3, LightStrip4
from light_strip_controller import LightStripController
from sound_controller import SoundController
from config_controller import ConfigController
from sdcard_controller import SDCardController
from movement_controller import MovementController
from lightsaber_controller import LightsaberController
from i2c import I2CController
from spi import SPIController
from button_controller import ButtonController

# TODO: Write animations for each strip
# TODO: Read animations for each strip
# TODO: Have animations run simultaneously across all strips (May need timer to keep in sync and have regular write intervals)
# TODO: Get sound to work in sync with lights with volume control
# TODO: Get movements working better

# Debugging
LED_STATUS_PIN = 16
led_status = Pin(LED_STATUS_PIN, Pin.OUT)

# Light Strip - Defines a light strip
light_strip1 = LightStrip1
light_strip2 = LightStrip2
light_strip3 = LightStrip3
light_strip4 = LightStrip4

# Light Strip Controller - Tells a light strip what to do
light_strip_controller1 = LightStripController(light_strip1)
light_strip_controller2 = LightStripController(light_strip2)
light_strip_controller3 = LightStripController(light_strip3)
light_strip_controller4 = LightStripController(light_strip4)

# Accessory Controllers - Controls sound, movement, config, sd card
# # SPI Specific
spi_controller = SPIController()
sd_card_controller = SDCardController(spi_controller)
# # I2C Specific
i2c_controller = I2CController()
movement_controller = MovementController(i2c_controller)
# # Other
sound_controller = SoundController()
config_controller = ConfigController()

# Lightsaber Controller - Tells light saber controllers and sound controllers what to do
# light_strip_controllers = [
#     light_strip_controller1,
#     light_strip_controller2,
#     light_strip_controller3,
#     light_strip_controller4
# ]

button_controller = ButtonController()

lightsaber_controller = LightsaberController(
    light_strip_controller1,
    movement_controller,
    config_controller,
    sound_controller,
    button_controller
)


# Ideally you would have 1 controller that takes in everything
# # That controller would
# # - load resources (from SD Card Controller),
# # - then listen for button events via ButtonController (with ButtonCallbacks)
# # - or movement events via MovementController (with MovementCallbacks)
# # - and then output light via LightController and or sound via SoundController accordingly.

# Likely scenario
# # We have multiple light animations to play with 1 or more sounds
# # In other words, we have possibly 4 light outputs, and 1 sound output.
# # A naive animation format is
# group(
#   light(1, ani1),
#   light(2, ani2),
#   light(3, ani3),
#   light(4, ani4),
#   sound(1, sound)
# )
