from trickLED import animations32
import machine

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import trickLED
from trickLED import animations


async def play(animation, n_frames, **kwargs):
    await animation.play(n_frames, **kwargs)


async def demo_animations(leds, n_frames=200):
    animation = animations.NextGen(leds)
    print('NextGen settings: default')
    await animation.play(n_frames)
    print('NextGen settings: blanks=2, interval=150')
    await animation.play(n_frames, blanks=2, interval=150)


async def main():
    demos = [
        asyncio.create_task(demo_animations(tl1, 100)),
        asyncio.create_task(demo_animations(tl2, 100)),
        asyncio.create_task(demo_animations(tl3, 100)),
        asyncio.create_task(demo_animations(tl4, 100))
    ]
    await asyncio.gather(*demos)

# LED_PIN
LED1_PIN = 13
LED2_PIN = 14
LED3_PIN = 33
LED4_PIN = 32

# LED_NUM_PIXELS
LED1_NUM_PIXELS = 10
LED2_NUM_PIXELS = 10
LED3_NUM_PIXELS = 10
LED4_NUM_PIXELS = 10


if __name__ == '__main__':

    led1_pin = machine.Pin(LED1_PIN)
    led2_pin = machine.Pin(LED2_PIN)
    led3_pin = machine.Pin(LED3_PIN)
    led4_pin = machine.Pin(LED4_PIN)

    tl1 = trickLED.TrickLED(led1_pin, LED1_NUM_PIXELS, timing=1)
    tl2 = trickLED.TrickLED(led2_pin, LED2_NUM_PIXELS, timing=1)
    tl3 = trickLED.TrickLED(led3_pin, LED3_NUM_PIXELS, timing=1)
    tl4 = trickLED.TrickLED(led4_pin, LED4_NUM_PIXELS, timing=1)

    asyncio.run(main())
