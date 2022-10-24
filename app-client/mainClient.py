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
config_json = {"function": "network", "network_indicator_colour": "green", "type": "colour", "time": 1666557636.784309}
config_reset_json = config_json
indicator1_colour="white"
indicator2_colour="white"
indicator3_colour="white"

loop = asyncio.get_event_loop() # sets our infinite loop; not a great choice according to docs...

"""
    ############   FUNCTIONS SECTION   ############
"""
async def drawIndicators(draw, indicator1_colour="white", indicator2_colour="white", indicator3_colour="white"):
    # indicators, bottom two pixel rows of each matrix board
    # how can we get a 1px space between each?
    draw.rectangle([-1,30,31,31], fill=indicator1_colour, width=2)
    draw.rectangle([31,30,63,31], fill=indicator2_colour, width=2)
    draw.rectangle([63,30,96,31], fill=indicator3_colour, width=2)
    return draw

async def drawBorderLine(draw, colour):
    # border to separate png from indicators
    draw.line([-1,29,96,29], fill=colour)
    return draw

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
    draw = await drawIndicators(draw, indicator1_colour, indicator2_colour, indicator3_colour)
    matrix.SetImage(idle_image, 1, 0)

async def drawFullImage(image_name, indicator1_colour="white", indicator2_colour="white", indicator3_colour="white"):
    image = ((Image.open(os.path.dirname(os.path.realpath(__file__)) + "/icons/"+ image_name +".png")).resize((96,32))).convert('RGB')
    draw = ImageDraw.Draw(image)
    draw = await drawBorderLine(draw, "black")
    draw = await drawIndicators(draw, indicator1_colour, indicator2_colour, indicator3_colour)

    matrix.SetImage(image, 1, 0)


"""
    paint_matrix: This async function acts on other state pulled from redis keys and modifies the rgb matrix accordingly.

    This is where we define the business logic (cases).
"""
async def paint_matrix():
    global config_json, config_reset_json, interrupted
    redis = aioredis.Redis.from_url(config.redis_url, password=config.redis_pass, decode_responses=True)

    while running:
        try:
            async with async_timeout.timeout(5):
                last_function = config_json['function']
                # why this text jankiness?  because of redis.pubsub(message=json) -> redis.kv(data=json) -> here
                # i'm sure there are problems here - and chief might be 'y u have pubsub at all?!'
                value = (await get_function_json()).strip('\"')
                fixed_value = value.replace('\'', '"')
                config_json = json.loads(fixed_value)
                current_time = time.time()
                message_time = config_json['time']
                time_delta = current_time - message_time
                async def resetConfig():
                    print(f"Resetting config to: {config_reset_json}")
                    async with redis.client() as conn:
                        await conn.set("json", str(config_reset_json))
                async def getLastNetworkIndicatorColour():
                    async with redis.client() as conn:
                        network_indicator_colour = await conn.get("network_indicator_colour")
                    return network_indicator_colour
                if 'network_indicator_colour' in config_json:
                    async with redis.client() as conn:
                        await conn.set("network_indicator_colour",config_json['network_indicator_colour'])
                    network_indicator_colour = config_json['network_indicator_colour']
                else:
                    network_indicator_colour = await getLastNetworkIndicatorColour()

                # global variables, i.e. indicators are globally important
                indicator1_colour   = "white"
                indicator2_colour   = "white"
                indicator3_colour   = network_indicator_colour

                if last_function != config_json['function']:
                    # state has changed, let's clear the matrix to remove any ghosting; this helped!
                    # worth calling out that we are only looking at 'function' here...
                    print("State has changed, clearing matrix!")
                    matrix.Clear()

                # counters - where we reset to idle
                if last_function == "zoom" and time_delta > 2:
                    print(f"Resetting config after zoom usage and time_delta: {time_delta}")
                    await resetConfig()

                # config logic tree
                # here, idle == network, is the next fix
                if config_json['function'] == "network":
                    text_colour         = "white"

                    await drawIdle(text_colour, indicator1_colour, indicator2_colour, indicator3_colour)

                if config_json['function'] == "zoom":
                    # we got a zoom call, reset the zoom expiry timer
                    if config_json['state'] == "muted":
                        await drawFullImage("muted", indicator1_colour, indicator2_colour, indicator3_colour)
                    if config_json['state'] == "unmuted":
                        await drawFullImage("unmuted", indicator1_colour, indicator2_colour, indicator3_colour)

                interrupted = True
        except asyncio.TimeoutError:
            pass
        await asyncio.sleep(.1)

"""
    get_function_json: This async function calls redis and checks the json key, and returns it.
    Why are we using a redis key get?
    Because I didn't know how to share variable value changes between async threads.
    So redis keys become our shared memory.
    ¯\_(ツ)_/¯
    Now that I've gotten it working, I have thoughts on ways of not having two redis calls, but, it works atm, so...
"""
async def get_function_json():
    redis = aioredis.Redis.from_url(config.redis_url, password=config.redis_pass, decode_responses=True)
    async with redis.client() as conn:
        function_json = json.dumps(await conn.get("json"))

        return function_json


"""
    ############   LOOPS SECTION   ############
"""
"""
    pubsub: This async function subscribes to the redis pubsub channel(s) and updates the redis json (config) key.
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
