# General
import time
from machine import Pin
# sd card
import os
from sdcard import SDCard

# light
import neopixel
# imu
from machine import Timer
from mpu9250 import MPU9250
# Sound
from wavplayer import WavPlayer

# Button
from button import Debounce

from i2c import I2CController
from spi import SPIController
# SD Card VSPI
# # https://randomnerdtutorials.com/esp32-microsd-card-arduino/
SPI_CS = 5  # SD card

# NEO Pixel

LED1_PIN = 13
LED2_PIN = 14
LED3_PIN = 33
LED4_PIN = 32
NUM_PIXELS = 10

# Buttons
BTN_LEFT_PIN = 4
BTN_CENTER_PIN = 0
BTN_RIGHT_PIN = 15

# IMU MPU9250 I2C address 0x68
# # https://randomnerdtutorials.com/esp32-i2c-communication-arduino-ide/

# Audio MAX98357A I2S
I2S_DOUT = 25
I2S_BCLK = 27
I2S_LRC = 26

# LED Status
LED_STATUS_PIN = 16

# SD Card

# Hyper Params
MOVE_THRESHOLD = 5
MOVE_REFRESH_TIME = 500  # ms
OPEN_CLOSE_TIME = 0.2


class SDCardController:

    def __init__(self, spi_controller) -> None:
        # # sd = SDCard(slot=2)  # sck=18, mosi=23, miso=19, cs=5
        self.sd = SDCard(spi_controller.spi, Pin(SPI_CS))
        os.mount(self.sd, "/sd")

        # print('Root directory:{}'.format(os.listdir()))
        # vfs = os.VfsFat(self.sd)
        # os.mount(vfs, '/sd')

        print('Root directory:{}'.format(os.listdir()))
        os.chdir('sd')
        print('SD Card contains:{}'.format(os.listdir()))

        pass


class SoundController:

    def __init__(self) -> None:

        # ======= I2S CONFIGURATION =======
        SCK_PIN = I2S_BCLK
        WS_PIN = I2S_LRC
        SD_PIN = I2S_DOUT
        I2S_ID = 0
        BUFFER_LENGTH_IN_BYTES = 40000
        # ======= I2S CONFIGURATION =======

        self.wp = WavPlayer(id=I2S_ID,
                            sck_pin=Pin(SCK_PIN),
                            ws_pin=Pin(WS_PIN),
                            sd_pin=Pin(SD_PIN),
                            ibuf=BUFFER_LENGTH_IN_BYTES)

    def play(self, filename):
        self.wp.play(filename, loop=False)
        # wait until the entire WAV file has been played
        # while self.wp.isplaying() == True:
        #     # other actions can be done inside this loop during playback
        #     pass
        # wp.play("blst01.wav", loop=False)
        # time.sleep(10)  # play for 10 seconds
        # wp.pause()
        # time.sleep(5)  # pause playback for 5 seconds
        # wp.resume()  # continue playing to the end of the WAV file

    def pause(self):
        self.wp.pause()

    def resume(self):
        self.wp.resume()


class Font:
    name = ""
    color = (0, 0, 0)
    index = None

    def __init__(self, name, color, index) -> None:
        self.name = name
        self.color = color
        self.index = index


class ConfigController:

    def __init__(self) -> None:
        self.read_all_profiles_into_memory()
        self.read_current_font()
        pass

    def read_all_profiles_into_memory(self):
        print('SD Card contains:{}'.format(os.listdir()))
        os.chdir("fonts")
        self.fonts = []
        for i, font in enumerate(os.listdir()):
            os.chdir(font)
            with open(self.color_filename, "r") as color_file:
                color_bytes = eval(color_file.read())
                self.fonts.append(Font(font, color_bytes, i))
            os.chdir("..")
        print(self.fonts)

    def get_filename(self, filename):
        return self.base_dir + "/" + self.current_font.name + "/" + filename

    base_dir = "/fonts"
    color_filename = "color.txt"
    font_filename = "font.wav"
    open_filename = "open.wav"
    idle_filename = "idle.wav"
    close_filename = "close.wav"
    hit_filename = "hit.wav"
    lock_filename = "lock.wav"
    unlock_filename = "unlock.wav"
    move_filename = "move.wav"

    current_font_index = 0
    current_font = None
    fonts = []

    def set_next_font(self):
        self.current_font_index = (
            self.current_font_index+1
        ) % len(self.fonts)
        self.current_font = self.fonts[self.current_font_index]
        pass

    def set_previous_font(self):
        color_count = len(self.fonts)
        self.current_font_index = (
            self.current_font_index+color_count-1
        ) % color_count
        self.current_font = self.fonts[self.current_font_index]
        pass

    def read_current_font(self):
        self.current_font = self.fonts[self.current_font_index]
        pass


# IMU


class MovementController:

    registered_callback = None
    move_state = 0

    def read_sensor(self, timer):
        x = self.sensor.gyro[0]
        y = self.sensor.gyro[1]
        z = self.sensor.gyro[2]

        if (self.is_move(x, y, z) and self.move_state == 0):
            self.move_state = 1
            self.detected_move()
        elif not self.is_move(x, y, z) and self.move_state > 0:
            self.move_state = 0
            self.detected_still()

    def is_move(self, x, y, z):
        magnitude = pow(x, 2)+pow(y, 2)+pow(z, 2)
        if self.registered_callback is not None:
            print(f"movement magnitude {magnitude}")
        return magnitude > MOVE_THRESHOLD

    def __init__(self, i2c) -> None:
        self.sensor = MPU9250(i2c.i2c)

        timer_0 = Timer(0)
        timer_0.init(period=MOVE_REFRESH_TIME,
                     mode=Timer.PERIODIC,
                     callback=self.read_sensor)
        print("MPU9250 id: " + hex(self.sensor.whoami))

        pass

    # possibly add move severity and pass that down
    # subscribe callback methods
    def register_callback(self, callback):
        self.registered_callback = callback
        pass

    def unregister_callback(self):
        self.registered_callback = None
        pass

    def detected_move(self):
        if (self.registered_callback is None):
            return
        self.registered_callback(self.move_state)
        pass

    def detected_still(self):
        if (self.registered_callback is None):
            return
        self.registered_callback(self.move_state)
        pass


# Light
# TODO: Have all light strips on a single write cycle, that way any timing and waiting are synchronized
# TODO: Alternatively Have timers and interrupts for each strip

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


class LightSaberState:
    SELECT = 0
    CLOSE = 1
    OPEN = 2
    IDLE = 3
    HIT = 4
    MOVE = 5
    LOCK = 6


class LightSaber:

    state = LightSaberState.SELECT

    def __init__(self, lc, mc, cc, sc):
        self.lc = lc
        self.mc = mc
        self.cc = cc
        self.sc = sc

    def up_button_pressed(self):
        if self.state == LightSaberState.IDLE or self.state == LightSaberState.MOVE:
            # hit
            self.hit()
            pass
        elif self.state == LightSaberState.SELECT:
            # select next
            self.next()
            pass
        pass

    def center_button_pressed(self):
        if self.state == LightSaberState.IDLE or self.state == LightSaberState.MOVE:
            self.close()
        elif self.state == LightSaberState.SELECT:
            self.open()
        pass

    def down_button_pressed(self):
        if self.state == LightSaberState.IDLE or self.state == LightSaberState.MOVE:
            # lock
            self.lock()
            pass
        elif self.state == LightSaberState.SELECT:
            # select prev
            self.previous()
            pass

        pass

    def down_button_released(self):
        if self.state == LightSaberState.LOCK:
            self.unlock()

    def open(self):
        print("Opening")
        self.state = LightSaberState.OPEN
        self.lc.open()
        # open sound
        # self.sc.play(self.cc.get_filename(self.cc.open_filename))
        self.idle()

    def close(self):
        print("Closing")
        self.mc.unregister_callback()
        self.state = LightSaberState.CLOSE
        self.lc.close()
        # close sound
        # self.sc.play(self.cc.get_filename(self.cc.close_filename))
        self.select()

    def next(self):
        print("Setting Next")
        self.cc.set_next_font()
        # get color sound and animation
        # set color sound and animation
        pass

    def previous(self):
        print("Setting Previous")
        self.cc.set_previous_font()
        # get color sound and animation
        # set color sound and animation
        pass

    def idle(self):
        print("Idling")
        self.state = LightSaberState.IDLE
        self.lc.idle()
        # idle sound
        # begin move detection
        self.mc.register_callback(self.receive_move_event)

    def select(self):
        print("Selecting")
        self.state = LightSaberState.SELECT

    def hit(self):
        print("Hitting")
        self.mc.unregister_callback()
        self.state = LightSaberState.HIT
        self.lc.hit()
        # hit sound
        self.idle()

    def lock(self):
        print("Locking")
        self.mc.unregister_callback()
        self.state = LightSaberState.LOCK
        self.lc.lock()
        # lock sound

    def unlock(self):
        print("Unlocking")
        self.lc.unlock()
        # unlock sound
        self.idle()

    def receive_move_event(self, severity):
        print(f"Receiving move event {severity}")
        if severity == 0:
            self.unmove()
        elif severity == 1:
            self.move()

    def move(self):
        print("Moving")
        self.state = LightSaberState.MOVE
        self.lc.move()
        # move sound

    def unmove(self):
        print("Stoping Move")
        self.idle()


i2c_controller = I2CController()
spi_controller = SPIController()

sd = SDCardController(spi_controller)
sc = SoundController()
cc = ConfigController()

mc = MovementController(i2c_controller)

ls1 = LightSaber(LightController(LED1_PIN, NUM_PIXELS, cc), mc, cc, sc)
ls2 = LightSaber(LightController(LED2_PIN, NUM_PIXELS, cc), mc, cc, sc)
ls3 = LightSaber(LightController(LED3_PIN, NUM_PIXELS, cc), mc, cc, sc)
ls4 = LightSaber(LightController(LED4_PIN, NUM_PIXELS, cc), mc, cc, sc)


# Buttons

def btn_left_down(pin):
    print("Left Button Pressed")
    ls1.up_button_pressed()
    ls2.up_button_pressed()
    ls3.up_button_pressed()
    ls4.up_button_pressed()


def btn_center_down(pin):
    print("Center Button Pressed")
    ls1.center_button_pressed()
    ls2.center_button_pressed()
    ls3.center_button_pressed()
    ls4.center_button_pressed()


def btn_right_down(pin):
    print("Right Button Pressed")
    ls1.down_button_pressed()
    ls2.down_button_pressed()
    ls3.down_button_pressed()
    ls4.down_button_pressed()


def btn_right_up(pin):
    print("Right Button Released")
    ls1.down_button_released()
    ls2.down_button_released()
    ls3.down_button_released()
    ls4.down_button_released()


def call_button_callback_down(pin):
    # print(f"Button Pressed {pin}")
    pass


def call_button_callback_up(pin):
    # print(f"Button Released {pin}")
    pass


button_left = Pin(BTN_LEFT_PIN, Pin.IN, Pin.PULL_UP)
Debounce(
    button_left,
    Pin.PULL_UP,
    btn_left_down,
    call_button_callback_up
)


button_center = Pin(BTN_CENTER_PIN, Pin.IN, Pin.PULL_UP)
Debounce(
    button_center,
    Pin.PULL_UP,
    btn_center_down,
    call_button_callback_up
)


button_right = Pin(BTN_RIGHT_PIN, Pin.IN, Pin.PULL_UP)
Debounce(
    button_right,
    Pin.PULL_UP,
    btn_right_down,
    btn_right_up
)

led_status = Pin(LED_STATUS_PIN, Pin.OUT)

# Main
while True:
    led_status.value(
        button_left.value() and
        button_center.value() and
        button_right.value()
    )

    time.sleep_ms(50)
