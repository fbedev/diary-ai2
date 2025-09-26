"""Utility helpers for working with Redis.

This module centralises the creation of the Redis client so that the rest of
our codebase can import a single shared connection.  The URL is resolved from
an environment variable which keeps the credentials out of the source code and
allows the app to run in different environments without code changes.
"""

from __future__ import annotations

import os
from functools import lru_cache

import redis
from dotenv import load_dotenv

# Load environment variables defined in a local .env file when developing.
load_dotenv()

DEFAULT_REDIS_URL = "redis://localhost:6379/0"


class RedisConfigurationError(RuntimeError):
    """Raised when a Redis client cannot be initialised."""


@lru_cache(maxsize=1)
def _create_client() -> redis.Redis:
    """Create and cache a configured Redis client instance.

    Returns
    -------
    redis.Redis
        The configured Redis client.

    Raises
    ------
    RedisConfigurationError
        If the REDIS_URL cannot be resolved or the connection fails.
    """

    redis_url = os.getenv("REDIS_URL", DEFAULT_REDIS_URL)
    if not redis_url:
        raise RedisConfigurationError("REDIS_URL environment variable is not set.")

    try:
        client = redis.from_url(redis_url, decode_responses=True)
        # Perform a lightweight ping so we fail fast when credentials are wrong.
        client.ping()
    except redis.RedisError as exc:  # pragma: no cover - defensive programming
        raise RedisConfigurationError("Unable to connect to Redis") from exc

    return client


# Export a module-level client that can be imported by the rest of the app.
redis_client: redis.Redis = _create_client()


__all__ = ["redis_client", "RedisConfigurationError"]
