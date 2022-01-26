from light_controller import LightStripController

LED1_PIN = 13
NUM_PIXELS = 10


class LightStrip1:
    def __init__(self) -> None:
        self.lc = LightStripController(LED1_PIN, NUM_PIXELS)
        pass
