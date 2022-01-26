from light_controller import LightStripController

LED2_PIN = 14
NUM_PIXELS = 10


class LightStrip2:
    def __init__(self) -> None:
        self.lc = LightStripController(LED2_PIN, NUM_PIXELS)
        pass
