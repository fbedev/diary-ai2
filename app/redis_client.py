import os
import redis

redis_url = "redis://default:pfyZcHRDaTaJiRpqlTgbWRKZVSjhasqY@shuttle.proxy.rlwy.net:10674"

redis_client = redis.from_url(redis_url, decode_responses=True)