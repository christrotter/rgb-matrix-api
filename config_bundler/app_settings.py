import os
from pydantic import BaseSettings

REDIS_HOST = os.environ.get('REDIS_HOST', '127.0.0.1')

# Redis config
class Config(BaseSettings):
    redis_url: str = "redis://{}:{}/0".format(REDIS_HOST, 6379)
    redis_pass: str = 'eYVX7EwVmmxKPCDmwMtyKVge8oLd2t81'
