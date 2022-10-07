#!/usr/bin/python
import asyncio
import async_timeout

from redis import asyncio as aioredis

from rgbmatrix import RGBMatrix, RGBMatrixOptions
from rgbmatrix import graphics
from PIL import Image
from PIL import ImageDraw

import MatrixSettings
config = MatrixSettings.Config()
matrix = RGBMatrix(options=MatrixSettings.options)
#buffer = matrix.CreateFrameCanvas() # note for later...cuz i suspect we'll have to move to images vs. 'fill' or 'text'

STOPWORD = "STOP" # not sure this is ever really functionally used...is it some kinda redis thing?
# not sure how to declare this any less jankily
running = True
zoom_state = ''

loop = asyncio.get_event_loop() # sets our infinite loop; not a great choice according to docs...

"""
    paint_matrix: This async function acts on other state pulled from redis keys and modifies the rgb matrix accordingly.
"""
async def paint_matrix():
    global zoom_state, interrupted
    while running:
        try:
            zoom_state = await get_zoom_state()
            if zoom_state == "muted":
                #matrix.Fill(255,0,0)
                image = Image.open("icons/muted.png")
                resized_image = image.resize((96,32))
                matrix.SetImage(resized_image.convert('RGB'))
            if zoom_state == "unmuted":
                #matrix.Fill(0,255,0)
                image = Image.open("icons/unmuted.png")
                resized_image = image.resize((96,32))
                matrix.SetImage(resized_image.convert('RGB'))
            if zoom_state == "inactive":
                # working fill
                #matrix.Fill(100,100,100)

                # working image display, sort of...it's 11 pixels short...the resize function fixed that.  weird.
                # i'm exporting them at the right size...?
                image = Image.open("icons/inactive.png")
                resized_image = image.resize((96,32))
                matrix.SetImage(resized_image.convert('RGB'))

                # draw primitive...not working
                #image = Image.new("RGB", (96, 32))
                #draw = ImageDraw.Draw(image,0,0)
                #matrix.Clear()
                #matrix.draw.rectangle((0, 0, 95, 31), fill=(100, 100, 100), outline=(0, 0, 255))
                #matrix.SetImage(image)

                # working draw text
                #font = graphics.Font()
                #font.LoadFont("fonts/10x20.bdf")
                #colour = graphics.Color(100, 100, 100)
                #graphics.DrawText(matrix, font, 8, 22, colour, "INACTIVE")

            interrupted = True
        except:
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
async def get_zoom_state():
    redis = aioredis.Redis.from_url(config.redis_url, password=config.redis_pass, decode_responses=True)
    async with redis.client() as conn:
        zoom_state = await conn.get("zoom_state")
        #print("image file is: " + image_file)
        return zoom_state

"""
    pubsub: This async function subscribes to the redis pubsub channel(s) and updates the redis state keys.
"""
async def pubsub():
    print("(pubsub) Starting pubsub reader...")
    redis = aioredis.Redis.from_url(config.redis_url, password=config.redis_pass, decode_responses=True)
    psub = redis.pubsub()

    async def reader(channel: aioredis.client.PubSub):
        while True:
            try:
                async with async_timeout.timeout(5):
                    message = await channel.get_message(ignore_subscribe_messages=True)
                    if message is not None:
                        # too many print statements here causes the code to blow up
                        print(f"(Reader) Message Received: {message}")
                        if message["data"] == STOPWORD:
                            #print("(Reader) STOP")
                            break
                        if message["data"] == "muted":
                            #print("(Reader) We got a muted message.")
                            async with redis.client() as conn:
                                await conn.set("zoom_state", "muted")
                                #val = await conn.get("zoom_state")
                            #print("(Reader) zoom_state: " + val)
                        if message["data"] == "unmuted":
                            #print("(Reader) We got an unmuted message.")
                            async with redis.client() as conn:
                                await conn.set("zoom_state", "unmuted")
                                #val = await conn.get("zoom_state")
                            #print("(Reader) zoom_state: " + val)
                        if message["data"] == "inactive":
                            #print("(Reader) We got an inactive message.")
                            async with redis.client() as conn:
                                await conn.set("zoom_state", "inactive")
                                #val = await conn.get("zoom_state")
                            #print("(Reader) zoom_state: " + val)
                    await asyncio.sleep(0.01)
            except asyncio.TimeoutError:
                pass

    async with psub as p:
        await p.subscribe("ch-zoom")
        await reader(p)
        await p.unsubscribe("ch-zoom")

    await psub.close()

"""
    subscriber: This async function creates the long-running task to pull messages.
"""
async def subscriber():
    print("(async-subscriber) Redis pubsub subscriber async startup...")
    tsk = asyncio.create_task(pubsub())
    async def pull_messages():
        redis = aioredis.Redis.from_url(config.redis_url, password=config.redis_pass, decode_responses=True)
        while not tsk.done():
            subs = dict(await redis.pubsub_numsub("ch-zoom"))
            if subs["ch-zoom"] == 1:
                break
            await asyncio.sleep(0) # why is this here...and why zero
        await redis.close()
    await pull_messages()

"""
    init:   this is/was necessary to ensure first runs would not crash due to null key returns;
            it's outside of the try statement due to async getting angry at me not awaiting this call
"""
if __name__ == '__init__':
    redis = aioredis.Redis.from_url(config.redis_url, password=config.redis_pass, decode_responses=True)
    redis.client().set("zoom_state", "inactive") # ensuring key is there to start with

"""
    try/except/finally: This is the only model that worked to allow me to have...
    - a thread constantly polling for messages
    - a thread constantly applying rgb matrix calls
    ...all the other ways I tried allowed one to work but not the other.
"""
try:
    print("(main) RGB client startup...")
    print("(main) Starting subscriber async task...")
    asyncio.ensure_future(subscriber())
    print("(main) Starting matrix painter...")
    asyncio.ensure_future(paint_matrix())
    print("(main) Entering infinite loop.")
    loop.run_forever()
except KeyboardInterrupt:
    pass
finally:
    print("(main) Closing infinite loop.")
    loop.close()
