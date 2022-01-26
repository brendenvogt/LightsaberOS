from machine import Pin
from button import Debounce

# Buttons
BTN_LEFT_PIN = 4
BTN_CENTER_PIN = 0
BTN_RIGHT_PIN = 15


class ButtonController:

    def __init__(self, ls, status) -> None:
        self.ls = ls
        self.status = status

        button_left = Pin(BTN_LEFT_PIN, Pin.IN, Pin.PULL_UP)
        Debounce(
            button_left,
            Pin.PULL_UP,
            self.btn_left_down,
            self.call_button_callback_up
        )

        button_center = Pin(BTN_CENTER_PIN, Pin.IN, Pin.PULL_UP)
        Debounce(
            button_center,
            Pin.PULL_UP,
            self.btn_center_down,
            self.call_button_callback_up
        )

        button_right = Pin(BTN_RIGHT_PIN, Pin.IN, Pin.PULL_UP)
        Debounce(
            button_right,
            Pin.PULL_UP,
            self.btn_right_down,
            self.btn_right_up
        )

    def btn_left_down(self, pin):
        print("Left Button Pressed")
        self.ls.up_button_pressed()
        # ls1.up_button_pressed()
        # ls2.up_button_pressed()
        # ls3.up_button_pressed()
        # ls4.up_button_pressed()

    def btn_center_down(self, pin):
        print("Center Button Pressed")
        self.status.value(1)
        self.ls.center_button_pressed()
        # ls1.center_button_pressed()
        # ls2.center_button_pressed()
        # ls3.center_button_pressed()
        # ls4.center_button_pressed()

    def btn_right_down(self, pin):
        print("Right Button Pressed")
        self.ls.down_button_pressed()
        # ls1.down_button_pressed()
        # ls2.down_button_pressed()
        # ls3.down_button_pressed()
        # ls4.down_button_pressed()

    def btn_right_up(self, pin):
        print("Right Button Released")
        self.ls.down_button_released()
        # ls1.down_button_released()
        # ls2.down_button_released()
        # ls3.down_button_released()
        # ls4.down_button_released()

    def call_button_callback_down(self, pin):
        # print(f"Button Pressed {pin}")
        pass

    def call_button_callback_up(self, pin):
        self.status.value(0)
        # print(f"Button Released {pin}")
        pass
