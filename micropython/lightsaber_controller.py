
class LightSaberState:
    SELECT = 0
    CLOSE = 1
    OPEN = 2
    IDLE = 3
    HIT = 4
    MOVE = 5
    LOCK = 6


class LightSaberController:

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
