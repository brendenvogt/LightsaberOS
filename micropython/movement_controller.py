from machine import Timer
from mpu9250 import MPU9250

# Hyper Params
MOVE_THRESHOLD = 5
MOVE_REFRESH_TIME = 500  # ms


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
