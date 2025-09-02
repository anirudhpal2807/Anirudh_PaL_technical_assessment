import os
import redis.asyncio as redis
import asyncio
from typing import Dict, Any
import time

# In-memory storage for testing (fallback when Redis is not available)
_memory_storage: Dict[str, Any] = {}
_memory_expiry: Dict[str, float] = {}

redis_host = os.environ.get('REDIS_HOST', 'localhost')

try:
    redis_client = redis.Redis(host=redis_host, port=6379, db=0)
    # Test connection
    asyncio.run(redis_client.ping())
    USE_REDIS = True
except Exception as e:
    print(f"Redis server not available, using in-memory storage: {e}")
    USE_REDIS = False

async def add_key_value_redis(key, value, expire=None):
    if USE_REDIS:
        await redis_client.set(key, value)
        if expire:
            await redis_client.expire(key, expire)
    else:
        _memory_storage[key] = value
        if expire:
            _memory_expiry[key] = time.time() + expire

async def get_value_redis(key):
    if USE_REDIS:
        return await redis_client.get(key)
    else:
        # Check if key has expired
        if key in _memory_expiry and time.time() > _memory_expiry[key]:
            del _memory_storage[key]
            del _memory_expiry[key]
            return None
        return _memory_storage.get(key)

async def delete_key_redis(key):
    if USE_REDIS:
        await redis_client.delete(key)
    else:
        if key in _memory_storage:
            del _memory_storage[key]
        if key in _memory_expiry:
            del _memory_expiry[key]
