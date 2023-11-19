import os
from fastapi import FastAPI, APIRouter
from enum import Enum
from pydantic import BaseModel
from pydantic import BaseSettings
import json
import time
import asyncio
import async_timeout
import aioredis

"""
    ############# CONFIG SECTION #############
"""
REDIS_HOST = os.environ.get('REDIS_HOST', '127.0.0.1')
STOPWORD = "STOP"

"""
    ############# CLASSES SECTION #############
"""
class Config(BaseSettings):
    redis_url: str = "redis://{}:{}/0".format(REDIS_HOST, 6379)
    redis_pass: str = 'eYVX7EwVmmxKPCDmwMtyKVge8oLd2t81'

class ZoomState(str, Enum):
    muted       = "muted"
    unmuted     = "unmuted"
    inactive    = "inactive"

class NetworkState(str, Enum):
    green       = "green"
    yellow      = "yellow"
    red         = "red"

"""
    ############# WHATEVER THESE ARE SECTION #############
"""
config = Config()
app = FastAPI()
api_router = APIRouter()

"""
    ############# FUNCTIONS SECTION #############
"""
"""
    send_client_json: how we send the json blob over to the client, c/o Redis pubsub

    function: e.g. zoom
    state: e.g. idle, override, momentary
    type: this is useless...
    time: timestamp used for expiry calculations
"""
async def send_client_json(function, jsonDict):
    redis = aioredis.from_url(config.redis_url, password=config.redis_pass, decode_responses=True)
    channel = "ch-" + function
    jsonBlob = json.dumps(jsonDict)
    print(jsonBlob)
    await redis.publish(channel,jsonBlob)

"""
    the swiftbar plugin needs this; queries state and acts
"""
async def fetch_zoom_state():
    redis = aioredis.from_url(config.redis_url, password=config.redis_pass, decode_responses=True)
    value = await redis.get("zoom_state")
    return value

"""
    ############# API SECTION #############
"""

@api_router.on_event('startup')
async def startup_event():
    redis = aioredis.from_url(config.redis_url, password=config.redis_pass, decode_responses=True)
    await redis.set("function", "idle")
    value = await redis.get("zoom_state")
    print("startup: redis value is:",value)

@api_router.get("/", status_code=200)
async def root():
    return {"message": "Welcome to the rgb-matrix-api. /docs has more info."}

@api_router.get("/zoom/state", status_code=200)
async def get_zoom_state():
    state = await fetch_zoom_state()
    return state

@api_router.put("/zoom/{zoom_state}", status_code=200)
async def get_model(zoom_state: ZoomState):
    configDict = {
        'function': 'zoom',
        'zoom_state': zoom_state,
        'type': 'override',
        'time': time.time()
    }
    await send_client_json("zoom",configDict)

"""
    so a big problem here is that a network call is associated with an entire board state...
    we want this to only touch the indicator
    this requires a shift in how we process the board...
    put /network/state should be its own thing; so we need to start looking at channel sources on the client end
"""
@api_router.put("/network/{network_state}", status_code=200)
async def get_model(network_state: NetworkState):
    # todo: make the model be a json input
    configDict = {
        'function': 'network',
        'local_indicator_colour': network_state,
        'isp_indicator_colour': network_state,
        'dns_indicator_colour': network_state,
        'type': 'override',
        'time': time.time()
    }
    await send_client_json("network",configDict)

"""
    ############# APP STARTUP SECTION #############
"""
app.include_router(api_router)
