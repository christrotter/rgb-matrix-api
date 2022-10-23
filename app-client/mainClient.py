#!/usr/bin/python
import asyncio
import time
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
board_json = {}
white = 100,100,100

loop = asyncio.get_event_loop() # sets our infinite loop; not a great choice according to docs...

async def drawIdle(network_colour):
    colour = white
    time_font = large_font
    idle_image = Image.new("RGB", (96, 32), 0)
    draw = ImageDraw.Draw(idle_image)
    date_month = time.strftime("%b")
    date_month_short = date_month[0:2]
    date_str = time.strftime(date_month_short + "%d %H:%M")
    date_xoffset, date_height = time_font.getsize(date_str)
    date_xoffset = 0
    upper_offset = -1
    draw.text((date_xoffset, upper_offset), date_str, colour, font=time_font)
    draw.line([-1,31,96,31], fill=network_colour, width=0, joint=None)
    matrix.SetImage(idle_image, 1, 0)

async def drawFullBoardImage(image_name):
    image = Image.open(os.path.dirname(os.path.realpath(__file__)) + "/icons/"+ image_name +".png")
    resized_image = image.resize((96,32))
    matrix.SetImage(resized_image.convert('RGB'))

"""
    paint_matrix: This async function acts on other state pulled from redis keys and modifies the rgb matrix accordingly.

    This is where we define the business logic (cases).
"""
async def paint_matrix():
    global board_json, interrupted
    while running:
        try:
            async with async_timeout.timeout(5):
                last_state = board_json
                # why this text jankiness?  because of redis.pubsub(message=json) -> redis.kv(data=json) -> here
                # i'm sure there are better ways - and chief might be 'y u have pubsub at all?!'
                value = (await get_board_state()).strip('\"')
                fixed_value = value.replace('\'', '"')
                board_json = json.loads(fixed_value)
                if last_state != board_json:
                    # state has changed, let's clear the matrix to remove any ghosting; this helped!
                    print("State has changed, clearing matrix!")
                    matrix.Clear()

                if board_json['board'] == "network":
                    await drawIdle(board_json['state'])
                if board_json['board'] == "zoom":
                    if board_json['state'] == "muted":
                        await drawFullBoardImage("muted")
                    if board_json['state'] == "unmuted":
                        await drawFullBoardImage("unmuted")
                interrupted = True
        except asyncio.TimeoutError:
            pass
        await asyncio.sleep(.1)

"""
    get_zoom_state: This async function calls redis and checks the zoom_state key, and returns it.
    Why are we using a redis key get?
    Because I didn't know how to share variable value changes between async threads.
    So redis keys become our shared memory.
    ¯\_(ツ)_/¯
    Now that I've gotten it working, I have thoughts on ways of not having two redis calls, but, it works atm, so...
"""
async def get_board_state():
    redis = aioredis.Redis.from_url(config.redis_url, password=config.redis_pass, decode_responses=True)
    async with redis.client() as conn:
        #board = await conn.get("board")
        #state = await conn.get("state")
        #type = await conn.get("type")
        #await redis.close()
        #board_state = {}
        #board_state['board'] = board
        #board_state['state'] = state
        #board_state['type'] = type
        #board_json = json.dumps(board_state)
        board_json = json.dumps(await conn.get("json"))

        return board_json

#async def get_zoom_state():
#    redis = aioredis.Redis.from_url(config.redis_url, password=config.redis_pass, decode_responses=True)
#    async with redis.client() as conn:
#        zoom_state = await conn.get("zoom_state")
#        await redis.close()
#        return zoom_state

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
                            await conn.set("board-"+message["channel"], messageData['board'])
                            await conn.set("active-board", messageData['board'])
                            await conn.set("state", messageData['state'])
                            await conn.set("type", messageData['type'])
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
