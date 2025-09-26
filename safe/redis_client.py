import os
import redis

redis_url = "redis://localhost:6379"

redis_client = redis.from_url(redis_url, decode_responses=True)