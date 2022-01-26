from machine import Pin
from wavplayer import WavPlayer

I2S_DOUT = 25
I2S_BCLK = 27
I2S_LRC = 26


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
