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
large_font = ImageFont.load(os.path.dirname(os.path.realpath(__file__)) + config.large_font)
small_font = ImageFont.load(os.path.dirname(os.path.realpath(__file__)) + config.small_font)
loop = asyncio.get_event_loop() # sets our infinite loop; not a great choice according to docs...

# todo: figure out how to put config in a config file
STOPWORD = "STOP" # not sure this is ever really functionally used...is it some kinda redis thing?
# not sure how to declare this any less jankily
running = True
zoom_state = ''

unset_colour = 'cyan'
indicator1_colour = unset_colour
indicator2_colour = unset_colour
indicator3_colour = unset_colour

input_config_json = {"function": "network", "network_indicator_colour": unset_colour, "type": "colour", "time": 1666557636.784309}
config_reset_json = input_config_json



"""
    ############   FUNCTIONS SECTION   ############
"""
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

async def drawImageBottomHalfCanvas(image_name, indicator1_colour="white", indicator2_colour="white", indicator3_colour="white"):
    canvas_size = '(96,16)'
    setimage_xy_offsets = '1, 0'
    image = ((Image.open(os.path.dirname(os.path.realpath(__file__)) + "/icons/"+ image_name +".png")).resize(canvas_size)).convert('RGB')
    draw = ImageDraw.Draw(image)
    draw = await drawBorderLine(draw, "black")
    draw = await drawIndicators(draw, indicator1_colour, indicator2_colour, indicator3_colour)

    matrix.SetImage(image, 1, 0)

async def drawImageTopHalfCanvas(image_name, indicator1_colour="white", indicator2_colour="white", indicator3_colour="white"):
    canvas_size = '(96,16)'
    setimage_xy_offsets = '1, 0'
    image = ((Image.open(os.path.dirname(os.path.realpath(__file__)) + "/icons/"+ image_name +".png")).resize(canvas_size)).convert('RGB')
    draw = ImageDraw.Draw(image)
    draw = await drawBorderLine(draw, "black")
    draw = await drawIndicators(draw, indicator1_colour, indicator2_colour, indicator3_colour)

    matrix.SetImage(image, setimage_xy_offsets)

async def drawImageFullCanvas(image_name, indicator1_colour="white", indicator2_colour="white", indicator3_colour="white"):
    canvas_size = '(96,32)'
    setimage_xy_offsets = '1, 0'
    image = ((Image.open(os.path.dirname(os.path.realpath(__file__)) + "/icons/"+ image_name +".png")).resize(canvas_size)).convert('RGB')
    draw = ImageDraw.Draw(image)
    draw = await drawBorderLine(draw, "black")
    draw = await drawIndicators(draw, indicator1_colour, indicator2_colour, indicator3_colour)

    matrix.SetImage(image, setimage_xy_offsets)

"""
    new matrix canvas functions below
"""

example_matrix_config_json = {
  "options": [
    { "indicator_options": [
      {
        "indicator1_colour":"white",
        "indicator2_colour":"white",
        "indicator3_colour":"white"
      }
    ]},
    { "top_half_options": [
      {
        "indicator1_colour":"white",
        "indicator2_colour":"white",
        "indicator3_colour":"white"
      }
    ]},
    { "bottom_half_options": [
      {
        "indicator1_colour":"white",
        "indicator2_colour":"white",
        "indicator3_colour":"white"
      }
    ]},
    { "datetime_options": [
      {
        "indicator1_colour":"white",
        "indicator2_colour":"white",
        "indicator3_colour":"white"
      }
    ]},
  ]
}

async def drawFullOverlay(draw, config_json):
    config = json.loads(config_json)
    canvas_size = '(96,29)'
    if 'image_name' in config:
        image_name = config['image_name']
        image = ((Image.open(os.path.dirname(os.path.realpath(__file__)) + "/icons/"+ image_name +".png")).resize(canvas_size)).convert('RGB')
        draw = ImageDraw.Draw(image)
    elif 'image_name' not in config:
        draw.rectangle([0,0,96,29], fill='cyan', width=2)
    return draw

async def drawDateTime(draw, config_json):
    config = json.loads(config_json)
    text_colour="white"
    time_font = large_font
    canvas_location = '(0, -1)'
    date_month = time.strftime("%b")
    date_month_short = date_month[0:2] # only first two chars, to save matrix space
    date_str = time.strftime(date_month_short + "%d %H:%M") # 24h time, to save matrix space
    draw.text(canvas_location, date_str, text_colour, font=time_font)
    return draw

async def drawIndicators(draw, config_json):
    # indicators, bottom two pixel rows of each matrix board
    config = json.loads(config_json)
    # todo: how can we get a 1px space between each?...trying...
    # these imply canvas locations...indicators can never change canvas locations
    draw.rectangle([0,30,30,31], fill=config['indicator1_colour'], width=2)
    draw.rectangle([32,30,62,31], fill=config['indicator2_colour'], width=2)
    draw.rectangle([64,30,96,31], fill=config['indicator3_colour'], width=2)
    return draw

async def drawMatrixCanvas(config_json):
    canvas_size = '(96,32)'
    setimage_xy_offsets = '0, 0'
    matrix_canvas = Image.new("RGB", canvas_size, 0) # set our canvas size
    draw_on_canvas = ImageDraw.Draw(matrix_canvas)

    # here we append stuff to the canvas; assumption is that you are always drawing every part of the canvas
    # if the options are present, draw them
    # this will require clearly defined draw spaces...
    #if 'top_half_options' in config_json:
    #    draw_on_canvas = await drawTopHalf(draw_on_canvas, config_json['top_half_options'])
    #if 'bottom_half_options' in config_json:
    #    draw_on_canvas = await drawBottomHalf(draw_on_canvas, config_json['bottom_half_options'])

    if 'full_overlay_options' in config_json:
        draw_on_canvas = await drawFullOverlay(draw_on_canvas, config_json['full_overlay_options']) # e.g. zoom
    if 'datetime_options' in config_json:
        draw_on_canvas = await drawDateTime(draw_on_canvas, config_json['datetime_options'])
    if 'indicator_options' in config_json:
        draw_on_canvas = await drawIndicators(draw_on_canvas, config_json['indicator_options']) # contains explicit canvas location xy

    matrix.SetImage(matrix_canvas, setimage_xy_offsets)


"""
    paint_matrix: This async function acts on other state pulled from redis keys and modifies the rgb matrix accordingly.

    This is where we define the business logic (cases).
"""
async def paint_matrix():
    global input_config_json, config_reset_json, interrupted
    redis = aioredis.Redis.from_url(config.redis_url, password=config.redis_pass, decode_responses=True)

    while running:
        try:
            async with async_timeout.timeout(5):
                last_function = input_config_json['function'] # i think this blows up on first run...
                # why this text jankiness?  because of redis.pubsub(message=json) -> redis.kv(data=json) -> here
                # i'm sure there are problems here - and chief might be 'y u have pubsub at all?!'
                value = (await get_function_json()).strip('\"')
                fixed_value = value.replace('\'', '"')
                input_config_json = json.loads(fixed_value)
                current_time = time.time()
                message_time = input_config_json['time']
                time_delta = current_time - message_time
                matrix_config_json = {} # reset on each run
                matrix_config = {} # reset on each run
                function = 'main'

                async def resetConfig():
                    print(f"Resetting config to: {config_reset_json}")
                    # todo: this really just needs to be 'back to what we had on before zoom interrupted us'...
                    async with redis.client() as conn:
                        await conn.set("json", str(config_reset_json))
                async def getLastNetworkIndicatorColour(type): # persist network indicator colours across changes
                    async with redis.client() as conn:
                        key = f"{type}_indicator_colour"
                        network_indicator_colour = await conn.get(key)
                    return network_indicator_colour

                if 'network_indicator_colours' in input_config_json:
                    async with redis.client() as conn:
                        await conn.set("local_indicator_colour",input_config_json['network_indicator_colours']['local'])
                        await conn.set("isp_indicator_colour",input_config_json['network_indicator_colours']['local'])
                        await conn.set("dns_indicator_colour",input_config_json['network_indicator_colours']['local'])
                    local_indicator_colour  = input_config_json['network_indicator_colours']['local']
                    isp_indicator_colour    = input_config_json['network_indicator_colours']['local']
                    dns_indicator_colour    = input_config_json['network_indicator_colours']['local']
                else: # if we are not actively changing it, pull from Redis
                    local_indicator_colour  = await getLastNetworkIndicatorColour('local')
                    isp_indicator_colour    = await getLastNetworkIndicatorColour('local')
                    dns_indicator_colour    = await getLastNetworkIndicatorColour('local')
                # todo: inject this right into the if?
                matrix_config['indicators'] = {}
                matrix_config['indicators']['indicator1_colour'] = local_indicator_colour
                matrix_config['indicators']['indicator2_colour'] = isp_indicator_colour
                matrix_config['indicators']['indicator3_colour'] = dns_indicator_colour

                if last_function != input_config_json['function']:
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
                #if input_config_json['function'] == "network":
                #    text_colour         = "white"

                    #await drawIdle(text_colour, indicator1_colour, indicator2_colour, indicator3_colour)

                #if input_config_json['function'] == "zoom":
                #    # we got a zoom call, reset the zoom expiry timer
                #    if input_config_json['zoom_state'] == "muted":
                #        # change to 'populate json'
                #        #await drawFullImage("muted", indicator1_colour, indicator2_colour, indicator3_colour)
                #    if input_config_json['zoom_state'] == "unmuted":
                #        #change to 'populate json'
                #        #await drawFullImage("unmuted", indicator1_colour, indicator2_colour, indicator3_colour)
                matrix_config['function'] = input_config_json['function']
                # finally, after having set all the variables into our matrix_config_json
                matrix_config_json = json.dumps(matrix_config) # do we need to do the whole json encode/decode dance now?
                # we can create the canvas
                await drawMatrixCanvas(matrix_config_json)

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
