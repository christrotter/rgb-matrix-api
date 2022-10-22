import os
from fastapi import FastAPI, APIRouter
from enum import Enum
from pydantic import BaseModel
from pydantic import BaseSettings
import asyncio
import async_timeout
import aioredis

REDIS_HOST = os.environ.get('REDIS_HOST', '127.0.0.1')

class Config(BaseSettings):
    redis_url: str = "redis://{}:{}/1".format(REDIS_HOST, 6379)
    redis_pass: str = 'eYVX7EwVmmxKPCDmwMtyKVge8oLd2t81'

class ZoomState(str, Enum):
    muted       = "muted"
    unmuted     = "unmuted"
    inactive    = "inactive"

config = Config()
app = FastAPI()
api_router = APIRouter()
STOPWORD = "STOP"

# rgb toggle function
# this is where we act on the rgb matrix
# pubsub might be the wrong tech here...but should work for now
# actually, we want the other end to react accordingly...so maybe it is?
async def toggle_rgb(zoom_state):
    redis = aioredis.from_url(config.redis_url, password=config.redis_pass, decode_responses=True)
    # if state mute, publish muted message
    if (zoom_state == "muted"):
        await redis.publish("ch-zoom","muted")
    # if state unmute, rgb green
    if (zoom_state == "unmuted"):
        await redis.publish("ch-zoom","unmuted")
    # if state inactive, rgb off
    if (zoom_state == "inactive"):
        await redis.publish("ch-zoom","inactive")
    #TODO there is no real way of clearing out old messages...which is kinda why i suspect pubsub is not what we want...

async def fetch_zoom_state():
    redis = aioredis.from_url(config.redis_url, password=config.redis_pass, decode_responses=True)
    value = await redis.get("zoom_state")
    return value

@api_router.on_event('startup')
async def startup_event():
    redis = aioredis.from_url(config.redis_url, password=config.redis_pass, decode_responses=True)
    await redis.set("zoom_state", "inactive")
    await redis.set("full_board_state", "zoom_indicator")
    value = await redis.get("zoom_state")
    print("startup: redis value is:",value)
    await redis.publish("ch-zoom", "Hello from FastAPI!")

@api_router.get("/", status_code=200)
async def root():
    return {"message": "Welcome to the rgb-matrix-api."}

@api_router.get("/zoom/state", status_code=200)
async def get_zoom_state():
    state = await fetch_zoom_state()
    return state

@api_router.put("/zoom/{zoom_state}", status_code=200)
async def get_model(zoom_state: ZoomState):
    await toggle_rgb(zoom_state)

app.include_router(api_router)
