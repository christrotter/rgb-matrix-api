"""
    the config bundler is responsible for bundling config :D
    1. redis get all config-* values; bundler doesn't care if anything has changed
    2. place into bundled data model (json)
    3. redis set into config-bundled json value for downstream consumption
"""

import enum
import aioredis
import asyncio
from enum import Enum
from pydantic import BaseModel, Field, schema_json_of
import json

import app_logging
import app_settings
import config_classes

logger = app_logging.logger
config = app_settings.Config() # redis config
redis = aioredis.from_url(config.redis_url, password=config.redis_pass, decode_responses=True)

"""
    Functions

                value = (await get_function_json()).strip('\"')
                fixed_value = value.replace('\'', '"')
                input_config_json = json.loads(fixed_value)

                function_json = json.dumps(await conn.get("json"))
"""
async def get_config_from_redis(key_name):
    async with redis.client() as conn:
        config_value  = json.dumps(await conn.get(key_name)).strip('\"')
        fixed_value = config_value.replace('\'', '"')
        return fixed_value

async def bundle_all_configs(config_dict):
    bundle_config = {}
    for config in config_dict:
        bundle_config += {config}
    return bundle_config

async def set_bundle_config_to_redis(bundle_config):
    async with redis.client() as conn:
        await conn.set("bundle_config",bundle_config)

#print(schema_json_of(config_classes.BundledConfigModel, indent=2))

"""
    here is our sample json object...



"""


async def run_config_bundler():
    # not sure what i'm doing is sensical; need to create an example data output...
    # yeah, need to fix the logic-there should be one big json object, not multiple..so each field needs to have dedicated naming
    config_dict = {}
    network_config = json.loads(await get_config_from_redis("network_config"))
    config_dict.update([network_config])
    logger.info(f"network dict: {config_dict}")
    zoom_config = json.loads(await get_config_from_redis("zoom_config"))
    config_dict.update([zoom_config])
    logger.info(f"network and zoom dict: {config_dict}")
    #config_dict.update(await get_config_from_redis("zoom_config"))
    #bundle_config = await bundle_all_configs(config_dict)
    #await set_bundle_config_to_redis(bundle_config)

"""
    try/except/finally: This is the only model that worked to allow me to have...
    - a thread constantly polling for messages
    - a thread constantly applying rgb matrix calls
    ...all the other ways I tried allowed one to work but not the other.
"""
try:
    logger.info("Starting config bundler microservice...")
    loop = asyncio.new_event_loop() # sets our infinite loop; not a great choice according to docs...
    asyncio.set_event_loop(loop)

    asyncio.Task(run_config_bundler())

    logger.info("Entering infinite loop.")
    loop.run_forever()
except KeyboardInterrupt:
    pass
finally:
    logger.info("Closing infinite loop.")
    loop.close()
