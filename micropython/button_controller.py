from machine import Pin
from button import Debounce

BTN_UP_PIN = 4
BTN_CENTER_PIN = 0
BTN_DOWN_PIN = 15


class ButtonType:
    UP = 0
    CENTER = 1
    DOWN = 2


class ButtonState:
    Pressed = 0
    Released = 1


class ButtonController:

    def __init__(self) -> None:
        self.button_callback_map = {}
        self.button_callback_map[ButtonType.UP] = {
            ButtonState.Pressed: None, ButtonState.Released: None}
        self.button_callback_map[ButtonType.CENTER] = {
            ButtonState.Pressed: None, ButtonState.Released: None}
        self.button_callback_map[ButtonType.DOWN] = {
            ButtonState.Pressed: None, ButtonState.Released: None}

        # Up Button
        button_up = Pin(BTN_UP_PIN, Pin.IN, Pin.PULL_UP)
        Debounce(
            button_up,
            Pin.PULL_UP,
            self.btn_up_pressed,
            self.btn_up_released
        )

        # Center Button
        button_center = Pin(BTN_CENTER_PIN, Pin.IN, Pin.PULL_UP)
        Debounce(
            button_center,
            Pin.PULL_UP,
            self.btn_center_pressed,
            self.btn_center_released
        )

        # Down Button
        button_down = Pin(BTN_DOWN_PIN, Pin.IN, Pin.PULL_UP)
        Debounce(
            button_down,
            Pin.PULL_UP,
            self.btn_down_pressed,
            self.btn_down_released
        )

    def register_button(self, btn_type, btn_state, callback):
        self.button_callback_map.setdefault(btn_type, {})[btn_state] = callback

    def __safe_call(self, function):
        if function is not None:
            function()

    def btn_up_pressed(self, pin):
        print(f"Up Button Pressed {pin}")
        self.__safe_call(
            self.button_callback_map[ButtonType.UP][ButtonState.Pressed])

    def btn_up_released(self, pin):
        print(f"Up Button Released {pin}")
        self.__safe_call(
            self.button_callback_map[ButtonType.UP][ButtonState.Released])

    # center
    def btn_center_pressed(self, pin):
        print(f"Center Button Pressed {pin}")
        self.__safe_call(
            self.button_callback_map[ButtonType.CENTER][ButtonState.Pressed])

    def btn_center_released(self, pin):
        print(f"Center Button Released {pin}")
        self.__safe_call(
            self.button_callback_map[ButtonType.CENTER][ButtonState.Released])

    # down
    def btn_down_pressed(self, pin):
        print(f"Down Button Pressed {pin}")
        self.__safe_call(
            self.button_callback_map[ButtonType.DOWN][ButtonState.Pressed])

    def btn_down_released(self, pin):
        print(f"Down Button Released {pin}")
        self.__safe_call(
            self.button_callback_map[ButtonType.DOWN][ButtonState.Released])
