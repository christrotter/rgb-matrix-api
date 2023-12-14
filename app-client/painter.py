#!/usr/bin/python
import asyncio
import time
import datetime
import os
import async_timeout
from redis import asyncio as aioredis
import json

# does not compile on a mac :(
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from rgbmatrix import graphics

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import MatrixSettings

"""
    Classes provide a means of bundling data and functionality together.
    Creating a new class creates a new type of object, allowing new
    instances of that type to be made. Each class instance can have
    attributes attached to it for maintaining its state. Class instances
    can also have methods (defined by its class) for modifying its state.

    Or, a class is a blueprint for constructing an object.

    a class helps you describe a standard format for an object you need

    we need a canvas object
"""

class MatrixCanvas:
    def __init__(self, xy_dimensions:list=(96,32), xy_image_offsets:list=(0,0), matrix_settings:object=MatrixSettings.Config ) -> None:
        """An rgb matrix canvas constructor with predefined canvas slots.

        Args:
            xy_dimensions (list): LED counts across x and y.  e.g.(96,32)
        """
        self.xy_dimensions = (96,32)
        self.xy_image_offsets = (0,0)
        #self.matrix_settings = None
        self.matrix = RGBMatrix(options=self.matrix_settings.options)
    def __repr__(self):
        return "xy_dimensions: {}\nxy_image_offsets: {}".format(self.xy_dimensions,self.xy_image_offsets)

    def create_canvas(self):
        matrix_canvas = Image.new("RGB", self.xy_dimensions, 0) # not sure what the zero does...
        draw = ImageDraw.Draw(matrix_canvas)


canvas = MatrixCanvas(matrix_settings=config)
print(canvas)
