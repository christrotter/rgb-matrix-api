#!/usr/bin/python
import asyncio
from enum import Enum
import time
import os

import async_timeout
from redis import asyncio as aioredis

from rgbmatrix import RGBMatrix, RGBMatrixOptions
from rgbmatrix import graphics
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


"""
    We want a way of overriding 'idle'.
    New redis key: FullBoardState:(zoom_indicator|weather|network)
    The display logic will start with that as 'what path do i go down here',
    and then the matrix will get drawn accordingly.
    Maybe one day this is selectable like channels on an old tv? knob wired into rpi gpio.
"""
class FullBoardState(str, Enum):
    zoom_indicator       = "zoom_indicator"
    #weather              = "weather"
    #network              = "network" # TODO: add a network layout for displaying gping or local network hop health; client to router, router to isp, isp to net

#class IdleState(str, Enum):
#    top_half = "date-time"
#    bottom_half = "blank"

async def FullBoardLayout(FullBoardState):
    """
        How we define a 'fullscreen matrix' layout.
        so pseudo-code...
        import BoardClass
        zoom_board = async def FullBoard(zoom)
        async def zoom_board_idle
            await zoom_board.LayoutIdle() # this knows to put draw_time from a lookup
        async def zoom_override_muted
            async def zoom_board.LayoutOverride("muted") # this knows how to draw the muted image
        async def zoom_override_unmuted
            async def zoom_board.LayoutOverride("unmuted") # this knows how to draw the unmuted image
        (if muted):
            await zoom_override_muted()
        (elif unmuted):
            await zoom_override_unmuted()
        (else):
            await
    """
    full_board_state = FullBoardState
    async def IdleLayout(full_board_state):
        #drawLayoutIdle(full_board_state)        # this has logic for all idles
        print("idle layout for: " + full_board_state)
    async def LayoutOverride():
        #drawLayoutOverride(full_board_state)    # this has logic for all overrides
        print("override layout or: " + full_board_state)
    async def MomentaryOverride():
        #drawLayoutMomentary(full_board_state)   # this has logic for all momentaries
        print("momentary layout for: " + full_board_state)
    print("running idle layout function")
    await IdleLayout(full_board_state)
