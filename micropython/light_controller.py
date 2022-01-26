import time
from machine import Pin
import neopixel

OPEN_CLOSE_TIME = 0.2


class LightController:

    def __init__(self, pin, pixels, cc) -> None:
        self.pin = Pin(pin, Pin.OUT)
        self.pixel_count = pixels
        self.np = neopixel.NeoPixel(self.pin, self.pixel_count)
        self.cc = cc

        self.open_time = OPEN_CLOSE_TIME  # time to open or close
        # time per pixel on open or close
        self.pixel_delay = int(self.open_time/self.pixel_count*1000)

        self.white_color = (255, 255, 255)

    def open(self):
        self.np.write()
        for i in range(self.pixel_count):
            self.np[i] = self.cc.current_font.color
            self.np.write()
            time.sleep_ms(self.pixel_delay)

    def close(self):
        for i in range(self.pixel_count-1, -1, -1):
            self.np[i] = (0, 0, 0)
            self.np.write()
            time.sleep_ms(self.pixel_delay)

    def fill_color(self, color):
        for i in range(self.pixel_count):
            self.np[i] = color
        self.np.write()

    def flash_white(self):
        self.fill_color(self.white_color)
        time.sleep_ms(self.pixel_delay)
        self.fill_color(self.cc.current_font.color)
        pass

    def idle(self):
        pass

    def hit(self):
        self.flash_white()
        pass

    def lock(self):
        self.fill_color(self.white_color)
        pass

    def unlock(self):
        self.fill_color(self.cc.current_font.color)
        pass

    def move(self):
        self.flash_white()
        pass
