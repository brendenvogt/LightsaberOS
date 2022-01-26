import time
from machine import Pin
from button import Debounce

from light_controller import LightController
from sound_controller import SoundController
from config_controller import ConfigController
from sdcard_controller import SDCardController
from movement_controller import MovementController
from lightsaber_controller import LightSaberController
from i2c import I2CController
from spi import SPIController

# SD Card VSPI
# # https://randomnerdtutorials.com/esp32-microsd-card-arduino/

# NEO Pixel

LED1_PIN = 13
LED2_PIN = 14
LED3_PIN = 33
LED4_PIN = 32
NUM_PIXELS = 10

# Buttons
BTN_LEFT_PIN = 4
BTN_CENTER_PIN = 0
BTN_RIGHT_PIN = 15

# IMU MPU9250 I2C address 0x68
# # https://randomnerdtutorials.com/esp32-i2c-communication-arduino-ide/
# Audio MAX98357A I2S
# LED Status
LED_STATUS_PIN = 16
# SD Card
# Light
# # TODO: Have all light strips on a single write cycle, that way any timing and waiting are synchronized
# # TODO: Alternatively Have timers and interrupts for each strip


i2c_controller = I2CController()
spi_controller = SPIController()

sd = SDCardController(spi_controller)
sc = SoundController()
cc = ConfigController()

mc = MovementController(i2c_controller)

ls1 = LightSaberController(
    LightController(LED1_PIN, NUM_PIXELS, cc), mc, cc, sc
)
ls2 = LightSaberController(
    LightController(LED2_PIN, NUM_PIXELS, cc), mc, cc, sc
)
ls3 = LightSaberController(
    LightController(LED3_PIN, NUM_PIXELS, cc), mc, cc, sc
)
ls4 = LightSaberController(
    LightController(LED4_PIN, NUM_PIXELS, cc), mc, cc, sc
)


# Buttons

def btn_left_down(pin):
    print("Left Button Pressed")
    ls1.up_button_pressed()
    ls2.up_button_pressed()
    ls3.up_button_pressed()
    ls4.up_button_pressed()


def btn_center_down(pin):
    print("Center Button Pressed")
    ls1.center_button_pressed()
    ls2.center_button_pressed()
    ls3.center_button_pressed()
    ls4.center_button_pressed()


def btn_right_down(pin):
    print("Right Button Pressed")
    ls1.down_button_pressed()
    ls2.down_button_pressed()
    ls3.down_button_pressed()
    ls4.down_button_pressed()


def btn_right_up(pin):
    print("Right Button Released")
    ls1.down_button_released()
    ls2.down_button_released()
    ls3.down_button_released()
    ls4.down_button_released()


def call_button_callback_down(pin):
    # print(f"Button Pressed {pin}")
    pass


def call_button_callback_up(pin):
    # print(f"Button Released {pin}")
    pass


button_left = Pin(BTN_LEFT_PIN, Pin.IN, Pin.PULL_UP)
Debounce(
    button_left,
    Pin.PULL_UP,
    btn_left_down,
    call_button_callback_up
)


button_center = Pin(BTN_CENTER_PIN, Pin.IN, Pin.PULL_UP)
Debounce(
    button_center,
    Pin.PULL_UP,
    btn_center_down,
    call_button_callback_up
)


button_right = Pin(BTN_RIGHT_PIN, Pin.IN, Pin.PULL_UP)
Debounce(
    button_right,
    Pin.PULL_UP,
    btn_right_down,
    btn_right_up
)

led_status = Pin(LED_STATUS_PIN, Pin.OUT)

# Main
while True:
    led_status.value(
        button_left.value() and
        button_center.value() and
        button_right.value()
    )

    time.sleep_ms(50)
