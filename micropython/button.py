
from machine import Pin


class Debounce:

    def __init__(self, pin, pull=Pin.PULL_UP, down_callback=None, up_callback=None) -> None:
        self.pull = pull
        pin.irq(handler=self.master_callback)
        self.down_callback = down_callback
        self.up_callback = up_callback

    def master_callback(self, pin):
        debounced = Debounce.debounce(pin)
        if debounced == None:
            return
        elif self.pull == Pin.PULL_UP and not debounced or self.pull == Pin.PULL_DOWN and debounced:
            print(f"{pin} {pin.value()} pressed")
            self.down_callback(pin)
        elif self.pull == Pin.PULL_UP and debounced or self.pull == Pin.PULL_DOWN and not debounced:
            print(f"{pin} {pin.value()} released")
            self.up_callback(pin)

    def debounce(pin):
        prev = None
        for _ in range(32):
            current_value = pin.value()
            if prev != None and prev != current_value:
                return None
            prev = current_value
        return prev
