from light_controller import LightStripController

LED3_PIN = 33
NUM_PIXELS = 10


class LightStrip3:
    def __init__(self) -> None:
        self.lc = LightStripController(LED3_PIN, NUM_PIXELS)
        pass
