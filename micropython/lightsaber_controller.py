from button_controller import *


class LightsaberState:
    SELECT = 0
    CLOSE = 1
    OPEN = 2
    IDLE = 3
    HIT = 4
    MOVE = 5
    LOCK = 6


class LightsaberController:

    state = LightsaberState.SELECT

    def __init__(self, lc, mc, cc, sc, bc):
        self.lc = lc
        self.lc.set_color(cc.current_font.color)  # TODO Fix
        self.mc = mc
        self.cc = cc
        self.sc = sc
        self.bc = bc
        self.__init_button_controller()
        # register button callbacks

    def __init_button_controller(self):
        self.bc.register_button(
            ButtonType.UP, ButtonState.Pressed, self.up_button_pressed
        )
        self.bc.register_button(
            ButtonType.CENTER, ButtonState.Pressed, self.center_button_pressed
        )
        self.bc.register_button(
            ButtonType.DOWN, ButtonState.Pressed, self.down_button_pressed
        )
        self.bc.register_button(
            ButtonType.DOWN, ButtonState.Released, self.down_button_released
        )

    def up_button_pressed(self):
        if self.state == LightsaberState.IDLE or self.state == LightsaberState.MOVE:
            # hit
            self.hit()
            pass
        elif self.state == LightsaberState.SELECT:
            # select next
            self.next()
            pass
        pass

    def center_button_pressed(self):
        if self.state == LightsaberState.IDLE or self.state == LightsaberState.MOVE:
            self.close()
        elif self.state == LightsaberState.SELECT:
            self.open()
        pass

    def down_button_pressed(self):
        if self.state == LightsaberState.IDLE or self.state == LightsaberState.MOVE:
            # lock
            self.lock()
            pass
        elif self.state == LightsaberState.SELECT:
            # select prev
            self.previous()
            pass

        pass

    def down_button_released(self):
        if self.state == LightsaberState.LOCK:
            self.unlock()

    def open(self):
        print("Opening")
        self.state = LightsaberState.OPEN
        self.lc.open()
        # open sound
        # self.sc.play(self.cc.get_filename(self.cc.open_filename))
        self.idle()

    def close(self):
        print("Closing")
        self.mc.unregister_callback()
        self.state = LightsaberState.CLOSE
        self.lc.close()
        # close sound
        # self.sc.play(self.cc.get_filename(self.cc.close_filename))
        self.select()

    def next(self):
        print("Setting Next")
        self.cc.set_next_font()
        self.lc.set_color(self.cc.current_font.color)
        # get color sound and animation
        # set color sound and animation
        pass

    def previous(self):
        print("Setting Previous")
        self.cc.set_previous_font()
        self.lc.set_color(self.cc.current_font.color)
        # get color sound and animation
        # set color sound and animation
        pass

    def idle(self):
        print("Idling")
        self.state = LightsaberState.IDLE
        self.lc.idle()
        # idle sound
        # begin move detection
        self.mc.register_callback(self.receive_move_event)

    def select(self):
        print("Selecting")
        self.state = LightsaberState.SELECT

    def hit(self):
        print("Hitting")
        self.mc.unregister_callback()
        self.state = LightsaberState.HIT
        self.lc.hit()
        # hit sound
        self.idle()

    def lock(self):
        print("Locking")
        self.mc.unregister_callback()
        self.state = LightsaberState.LOCK
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
        self.state = LightsaberState.MOVE
        self.lc.move()
        # move sound

    def unmove(self):
        print("Stoping Move")
        self.idle()
