import machine
import time
import sys

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import trickLED
from trickLED import animations
from trickLED import generators


async def play(animation, n_frames, **kwargs):
    await animation.play(n_frames, **kwargs)


async def demo_animations(leds, n_frames=200):
    print('Demonstrating animations press CTRL+C to cancel... or wait about 2 minutes.')
    # store repeat_n so we can set it back if we change it
    leds_repeat_n = leds.repeat_n
    # LitBits
    ani = animations.LitBits(leds)
    print('LitBits settings: default')
    await play(ani, n_frames)
    print('LitBits settings: lit_percent=50')
    await play(ani, n_frames, lit_percent=50)

    # NextGen
    ani = animations.NextGen(leds)
    print('NextGen settings: default')
    await play(ani, n_frames)
    print('NextGen settings: blanks=2, interval=150')
    await play(ani, n_frames, blanks=2, interval=150)

    # Jitter
    ani = animations.Jitter(leds)
    print('Jitter settings: default')
    await play(ani, n_frames)
    print('Jitter settings: background=0x020212, fill_mode=FILL_MODE_SOLID')
    ani.generator = generators.random_vivid()
    await play(ani, n_frames, background=0x020212,
               fill_mode=trickLED.FILL_MODE_SOLID)

    # SideSwipe
    ani = animations.SideSwipe(leds)
    print('SideSwipe settings: default')
    await play(ani, n_frames)

    # Divergent
    ani = animations.Divergent(leds)
    print('Divergent settings: default')
    await play(ani, n_frames)
    print('Divergent settings: fill_mode=FILL_MODE_MULTI')
    await play(ani, n_frames, fill_mode=trickLED.FILL_MODE_MULTI)

    # Convergent
    ani = animations.Convergent(leds)
    print('Convergent settings: default')
    await play(ani, n_frames)
    print('Convergent settings: fill_mode=FILL_MODE_MULTI')
    await play(ani, n_frames, fill_mode=trickLED.FILL_MODE_MULTI)

    if leds.n > 60 and leds.repeat_n is None:
        print('Setting leds.repeat_n = 40, set it back to {} if you cancel the demo'.format(
            leds_repeat_n))
        leds.repeat_n = 40

    if 'trickLED.animations32' in sys.modules:
        # Fire
        ani = animations32.Fire(leds)
        print('Fire settings: default')
        await play(ani, n_frames)

        # Conjuction
        ani = animations32.Conjunction(leds)
        print('Conjuction settings: default')
        await play(ani, n_frames)

    if leds.repeat_n != leds_repeat_n:
        leds.repeat_n = leds_repeat_n


def demo_generators(leds, n_frames=200):
    print('Demonstrating generators:')
    # stepped_color_wheel
    print('stepped_color_wheel')
    ani = animations.NextGen(leds, generator=generators.stepped_color_wheel())
    play(ani, n_frames)

    # striped_color_wheel
    print('stepped_color_wheel')
    ani.generator = generators.striped_color_wheel()
    play(ani, n_frames)
    print('stepped_color_wheel(stripe_size=1)')
    ani.generator = generators.striped_color_wheel(stripe_size=1)
    play(ani, n_frames)

    # fading_color_wheel
    print('fading_color_wheel(mode=FADE_OUT) (default)')
    ani.generator = generators.fading_color_wheel()
    play(ani, n_frames)
    print('fading_color_wheel(mode=FADE_IN)')
    ani.generator = generators.fading_color_wheel(mode=trickLED.FADE_IN)
    play(ani, n_frames)
    print('fading_color_wheel(mode=FADE_IN_OUT)')
    ani.generator = generators.fading_color_wheel(mode=trickLED.FADE_IN_OUT)
    play(ani, n_frames)

    # color_compliment
    print('color_compliment()')
    ani.generator = generators.color_compliment(stripe_size=10)
    play(ani, n_frames)

    # random_vivid
    print('random_vivid()')
    ani.generator = generators.random_vivid()
    play(ani, n_frames)

    # random_pastel
    print('random_pastel()')
    ani.generator = generators.random_pastel()
    play(ani, n_frames)
    print('random_pastel(mask=(127, 0, 31))')
    ani.generator = generators.random_pastel(mask=(127, 0, 31))
    play(ani, n_frames)
    print('random_pastel(mask=(0, 63, 63))')
    ani.generator = generators.random_pastel(mask=(0, 63, 63))
    play(ani, n_frames)


async def main():
    await asyncio.gather(
        asyncio.create_task(demo_animations(tl1, 100)),
        asyncio.create_task(demo_animations(tl2, 100)),
        asyncio.create_task(demo_animations(tl3, 100)),
        asyncio.create_task(demo_animations(tl4, 100))
    )


if __name__ == '__main__':

    from trickLED import animations32

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

    led1_pin = machine.Pin(LED1_PIN)
    led2_pin = machine.Pin(LED2_PIN)
    led3_pin = machine.Pin(LED3_PIN)
    led4_pin = machine.Pin(LED4_PIN)

    tl1 = trickLED.TrickLED(led1_pin, LED1_NUM_PIXELS, timing=1)
    tl2 = trickLED.TrickLED(led2_pin, LED2_NUM_PIXELS, timing=1)
    tl3 = trickLED.TrickLED(led3_pin, LED3_NUM_PIXELS, timing=1)
    tl4 = trickLED.TrickLED(led4_pin, LED4_NUM_PIXELS, timing=1)

    asyncio.run(main())
