from light_controller import LightStripController
from machine import Pin
import neopixel

# LED_PIN
LED1_PIN = 13
LED2_PIN = 14
LED3_PIN = 33
LED4_PIN = 32

# LED_NUM_PIXELS
LED1_NUM_PIXELS = 10
LED2_NUM_PIXELS = 10
LED3_NUM_PIXELS = 10
LED4_NUM_PIXELS = 10


class LightStrip:
    def __init__(self, led_pin, led_num_pixels) -> None:
        self.pin = Pin(led_pin, Pin.OUT)
        self.pixel_count = led_num_pixels
        self.np = neopixel.NeoPixel(self.pin, self.pixel_count)


LightStrip1 = LightStrip(LED1_PIN, LED1_NUM_PIXELS)
LightStrip2 = LightStrip(LED2_PIN, LED2_NUM_PIXELS)
LightStrip3 = LightStrip(LED3_PIN, LED3_NUM_PIXELS)
LightStrip4 = LightStrip(LED4_PIN, LED4_NUM_PIXELS)
