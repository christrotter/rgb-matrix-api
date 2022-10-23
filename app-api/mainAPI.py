import os
from fastapi import FastAPI, APIRouter
from enum import Enum
from pydantic import BaseModel
from pydantic import BaseSettings
import json
import asyncio
import async_timeout
import aioredis

REDIS_HOST = os.environ.get('REDIS_HOST', '127.0.0.1')

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

config = Config()
app = FastAPI()
api_router = APIRouter()
STOPWORD = "STOP"

# new replacement for rgb_toggle
"""
    board: theme? e.g. zoom
    state: e.g. idle, override, momentary
    type: this is useless...
"""
async def toggle_state(board, state, override):
    redis = aioredis.from_url(config.redis_url, password=config.redis_pass, decode_responses=True)
    channel = "ch-" + board
    stateDict = {
        'board': board,
        'state': state,
        'type': override
    }
    jsonBlob = json.dumps(stateDict)
    print(jsonBlob)
    await redis.publish(channel,jsonBlob)

async def fetch_zoom_state():
    redis = aioredis.from_url(config.redis_url, password=config.redis_pass, decode_responses=True)
    value = await redis.get("zoom_state")
    return value

@api_router.on_event('startup')
async def startup_event():
    redis = aioredis.from_url(config.redis_url, password=config.redis_pass, decode_responses=True)
    await redis.set("state", "green")
    await redis.set("full_board_state", "zoom_indicator")
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
    await toggle_state("zoom", zoom_state, "no-override")

@api_router.put("/network/{network_state}", status_code=200)
async def get_model(network_state: NetworkState):
    await toggle_state("network", network_state, "colour")

app.include_router(api_router)
