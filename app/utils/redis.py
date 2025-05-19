import os
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

_redis = redis.from_url(
    os.getenv("REDIS_URL"),
    decode_responses=True,
    max_connections=50
)

def get_redis_client():
    return _redis