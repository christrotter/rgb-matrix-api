#!/usr/bin/python
import asyncio
import time
import datetime
import os
import async_timeout
from redis import asyncio as aioredis
import json

from rgbmatrix import RGBMatrix, RGBMatrixOptions
from rgbmatrix import graphics
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import MatrixSettings
config = MatrixSettings.Config() # redis config
matrix = RGBMatrix(options=MatrixSettings.options)
large_font = ImageFont.load(os.path.dirname(os.path.realpath(__file__)) + "/fonts/9x15B.pil")
small_font = ImageFont.load(os.path.dirname(os.path.realpath(__file__)) + "/fonts/8x13B.pil")
#buffer = matrix.CreateFrameCanvas() # note for later...cuz i suspect we'll have to move to images vs. 'fill' or 'text'

STOPWORD = "STOP" # not sure this is ever really functionally used...is it some kinda redis thing?
# not sure how to declare this any less jankily
running = True
zoom_state = ''
board_json = {"board": "idle", "state": "green", "type": "colour", "time": 1666557636.784309}
board_reset_json = board_json
loop = asyncio.get_event_loop() # sets our infinite loop; not a great choice according to docs...

"""
    ############   FUNCTIONS SECTION   ############
"""
async def drawIdle(text_colour="white", indicator1_colour="white", indicator2_colour="white", indicator3_colour="white"):
    time_font = large_font
    idle_image = Image.new("RGB", (96, 32), 0) # set our canvas size
    draw = ImageDraw.Draw(idle_image)

    # set the date and time
    date_month = time.strftime("%b")
    date_month_short = date_month[0:2]
    date_str = time.strftime(date_month_short + "%d %H:%M")
    date_xoffset, date_height = time_font.getsize(date_str)
    date_xoffset = 0
    upper_offset = -1
    draw.text((date_xoffset, upper_offset), date_str, text_colour, font=time_font)

    # indicators, bottom two pixel rows of each board
    # need to pull this out into drawIndicators, so we can composite canvas things up here...zoom full screen is only a part
    draw.rectangle([-1,30,31,31], fill=indicator1_colour, width=2)
    draw.rectangle([31,30,63,31], fill=indicator2_colour, width=2)
    draw.rectangle([63,30,96,31], fill=indicator3_colour, width=2)
    matrix.SetImage(idle_image, 1, 0)

async def drawFullBoardImage(image_name):
    image = Image.open(os.path.dirname(os.path.realpath(__file__)) + "/icons/"+ image_name +".png")
    resized_image = image.resize((96,30))
    matrix.SetImage(resized_image.convert('RGB'))

"""
    paint_matrix: This async function acts on other state pulled from redis keys and modifies the rgb matrix accordingly.

    This is where we define the business logic (cases).
"""
async def paint_matrix():
    global board_json, board_reset_json, interrupted
    redis = aioredis.Redis.from_url(config.redis_url, password=config.redis_pass, decode_responses=True)

    while running:
        try:
            async with async_timeout.timeout(5):
                last_board = board_json['board']
                # why this text jankiness?  because of redis.pubsub(message=json) -> redis.kv(data=json) -> here
                # i'm sure there are problems here - and chief might be 'y u have pubsub at all?!'
                value = (await get_board_state()).strip('\"')
                fixed_value = value.replace('\'', '"')
                board_json = json.loads(fixed_value)
                current_time = time.time()
                message_time = board_json['time']
                time_delta = current_time - message_time

                async def resetBoard():
                    print(f"Resetting board to: {board_reset_json}")
                    async with redis.client() as conn:
                        await conn.set("json", str(board_reset_json))

                if last_board != board_json['board']:
                    # state has changed, let's clear the matrix to remove any ghosting; this helped!
                    # worth calling out that we are only looking at board state here...
                    print("State has changed, clearing matrix!")
                    matrix.Clear()

                # counters - where we reset to idle
                if last_board == "zoom" and time_delta > 2:
                    print(f"Resetting board after zoom usage and time_delta: {time_delta}")
                    await resetBoard()

                # board logic tree
                if board_json['board'] == "idle":
                    text_colour         = "white"
                    indicator1_colour   = "white"
                    indicator2_colour   = "white"
                    indicator3_colour   = board_json['state']
                    await drawIdle(text_colour, indicator1_colour, indicator2_colour, indicator3_colour)

                if board_json['board'] == "zoom":
                    # we got a zoom call, reset the zoom expiry timer
                    if board_json['state'] == "muted":
                        await drawFullBoardImage("muted")
                    if board_json['state'] == "unmuted":
                        await drawFullBoardImage("unmuted")

                interrupted = True
        except asyncio.TimeoutError:
            pass
        await asyncio.sleep(.1)

"""
    get_board_state: This async function calls redis and checks the json key, and returns it.
    Why are we using a redis key get?
    Because I didn't know how to share variable value changes between async threads.
    So redis keys become our shared memory.
    ¯\_(ツ)_/¯
    Now that I've gotten it working, I have thoughts on ways of not having two redis calls, but, it works atm, so...
"""
async def get_board_state():
    redis = aioredis.Redis.from_url(config.redis_url, password=config.redis_pass, decode_responses=True)
    async with redis.client() as conn:
        board_json = json.dumps(await conn.get("json"))

        return board_json

"""
    ############   END FUNCTIONS SECTION   ############
"""

"""
    ############   LOOPS SECTION   ############
"""
"""
    pubsub: This async function subscribes to the redis pubsub channel(s) and updates the redis state keys.
        board: main board type (zoom, idle, other...)
        state: per-board set of values (e.g. for zoom: muted, unmuted)
        type: override, idle, momentary (e.g. for zoom: override)
"""
async def readPubsubLoop():
    print("(pubsub) Starting pubsub reader...")
    redis = aioredis.Redis.from_url(config.redis_url, password=config.redis_pass, decode_responses=True)
    psub = redis.pubsub()

    async def reader(channel: aioredis.client.PubSub):
        while True:
            try:
                async with async_timeout.timeout(5):
                    message = await channel.get_message(ignore_subscribe_messages=True)
                    if message is not None:
                        print(f"(Reader) Message Received: {message}")
                        messageData = json.loads(message["data"]) # maybe we don't even need to convert to json...
                        async with redis.client() as conn:
                            await conn.set("json", str(messageData))
                await asyncio.sleep(0.01)
            except asyncio.TimeoutError:
                pass

    async with psub as p:
        await p.psubscribe("ch-*")
        await reader(p)
        await p.punsubscribe("ch-*")
    await psub.close()

"""
    subscriber: This async function creates the long-running task to pull messages.
"""
async def getStateLoop():
    print("(async-subscriber) Redis pubsub async startup, constantly polling for new state...")
    task = asyncio.create_task(readPubsubLoop())
    async def pubsub():
        redis = aioredis.Redis.from_url(config.redis_url, password=config.redis_pass, decode_responses=True)
        while not task.done():
            subs = dict(await redis.pubsub_numsub("ch-*")) # not quite sure what this block is doing
            if subs["ch-*"] == 1:
                break
            await asyncio.sleep(0) # this is your throttle for the loop
        await redis.close()
    await pubsub()
"""
    ############   END LOOPS SECTION   ############
"""


"""
    init:   this is/was necessary to ensure first runs would not crash due to null key returns;
            it's outside of the try statement due to async getting angry at me not awaiting this call
"""
if __name__ == '__init__':
    redis = aioredis.Redis.from_url(config.redis_url, password=config.redis_pass, decode_responses=True)
    # for some reason, can only set one thing here...
    redis.client().set("zoom_state", "inactive") # ensuring key is there to start with
    redis.close()

"""
    try/except/finally: This is the only model that worked to allow me to have...
    - a thread constantly polling for messages
    - a thread constantly applying rgb matrix calls
    ...all the other ways I tried allowed one to work but not the other.
"""
try:
    print("(main) RGB client startup...")

    print("(main) Starting subscriber async task...")
    asyncio.ensure_future(getStateLoop())

    print("(main) Starting matrix painter...")
    asyncio.ensure_future(paint_matrix())

    print("(main) Entering infinite loop.")
    loop.run_forever()
except KeyboardInterrupt:
    pass
finally:
    print("(main) Closing infinite loop.")
    loop.close()
