import time

OPEN_CLOSE_TIME = 0.2


class LightStripController:

    def __init__(self, light_strip) -> None:
        self.light_strip = light_strip
        self.pixel_count = self.light_strip.pixel_count
        self.open_time = OPEN_CLOSE_TIME  # time to open or close
        # time per pixel on open or close
        self.pixel_delay = int(self.open_time/self.pixel_count*1000)
        self.white_color = (255, 255, 255)
        self.current_color = self.white_color

    def open(self):
        self.light_strip.np.write()
        for i in range(self.pixel_count):
            self.light_strip.np[i] = self.current_color
            self.light_strip.np.write()
            time.sleep_ms(self.pixel_delay)

    def close(self):
        for i in range(self.pixel_count-1, -1, -1):
            self.light_strip.np[i] = (0, 0, 0)
            self.light_strip.np.write()
            time.sleep_ms(self.pixel_delay)

    def set_color(self, color):
        self.current_color = color

    def fill_color(self, color):
        for i in range(self.pixel_count):
            self.light_strip.np[i] = color
        self.light_strip.np.write()

    def flash_white(self):
        self.fill_color(self.white_color)
        time.sleep_ms(self.pixel_delay)
        self.fill_color(self.current_color)
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
        self.fill_color(self.current_color)
        pass

    def move(self):
        self.flash_white()
        pass
