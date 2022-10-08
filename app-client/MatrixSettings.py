import os
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from pydantic import BaseSettings
from redis import asyncio as aioredis

REDIS_HOST = os.environ.get('REDIS_HOST', '127.0.0.1')

# Redis config
class Config(BaseSettings):
    redis_url: str = "redis://{}:{}/1".format(REDIS_HOST, 6379)
    redis_pass: str = 'eYVX7EwVmmxKPCDmwMtyKVge8oLd2t81'

# Configuration for the matrix
options = RGBMatrixOptions()
options.rows = 32
options.cols = 32
options.chain_length = 3
options.brightness = 15
options.parallel = 1
options.hardware_mapping = 'adafruit-hat-pwm'  # adafruit-hat-pwm is for the 4/18 gpio connection fix
options.limit_refresh_rate_hz = 100

"""
    Some notes on panel flickering, specifically in my use case:
    - rpi2
    - 3 panels chained on adafruit-hat-pwm
    - 4/18 gpio connection

    Test params:
    - fill canvas to red (255,0,0)
    - fill canvas to green (0,255,0)
    - fill canvas to white (100,100,100)

    What I was experiencing:
    - white was visibly flickering
    - green was slightly visibly flickering and definitely peripherally flickering
    - red was peripherally flickering
    - very random brightness flickers, like lines would light up at different brightness levels for like 100ms

    First thing I did was the 4/18 gpio connection, and this immediately removed the rando-flickers.

    Then I played with the other suggestions in order, but ended up on...

    The key success factor seems to be...
    - limiting refresh to 100hz
    - brightness at 15%

    Other options I tried...as per the troubleshooting docs here: https://github.com/hzeller/rpi-rgb-led-matrix#troubleshooting
    - pwm_dither_bits: doubles refresh rate, did not fix peripheral vision flickering
    - pwm_lsb_nanoseconds @400: red or green was fine; white was visibly flickering; playing with this value, only 400 was even close to acceptable, and white...was not
    - pwm_bits: did nothing useful
    - limiting refresh WITHOUT the 4/18 gpio connection fix did nothing!

"""

conf = {
	# check arguments
	"font": "9x15B.pil"
}
