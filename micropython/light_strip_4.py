from light_controller import LightStripController

LED4_PIN = 32
NUM_PIXELS = 10


class LightStrip4:
    def __init__(self) -> None:
        self.lc = LightStripController(LED4_PIN, NUM_PIXELS)
        pass
