"""Cache service abstraction layer.

Supports diskcache (dev) and Redis (prod) with a unified interface.
"""

import json
import time
from typing import Any

from config.settings import settings
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class CacheService:
    """Abstract cache service with automatic backend selection."""

    def __init__(self):
        self._backend = self._create_backend()
        self._default_ttl = settings.CACHE_DEFAULT_TTL_SECONDS

    def _create_backend(self):
        """Create the appropriate cache backend based on settings."""
        if settings.REDIS_URL:
            try:
                import redis

                client = redis.from_url(settings.REDIS_URL, decode_responses=True)
                client.ping()
                logger.info("cache_backend", backend="redis")
                return RedisBackend(client)
            except Exception as e:
                logger.warning("redis_unavailable_falling_back_to_diskcache", error=str(e))

        # Fallback to diskcache
        import diskcache

        cache_dir = "cache_data"
        client = diskcache.Cache(cache_dir)
        logger.info("cache_backend", backend="diskcache", directory=cache_dir)
        return DiskCacheBackend(client)

    def get(self, key: str) -> Any | None:
        """Retrieve a cached value by key."""
        try:
            return self._backend.get(key)
        except Exception as e:
            logger.warning("cache_get_failed", key=key, error=str(e))
            return None

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        """Store a value in cache with TTL.

        Args:
            key: Cache key.
            value: Value to store (must be JSON-serializable).
            ttl_seconds: Time-to-live in seconds. Uses default if None.
        """
        if ttl_seconds is None:
            ttl_seconds = self._default_ttl

        try:
            self._backend.set(key, value, ttl_seconds)
        except Exception as e:
            logger.warning("cache_set_failed", key=key, error=str(e))

    def delete(self, key: str) -> None:
        """Remove a key from cache."""
        try:
            self._backend.delete(key)
        except Exception as e:
            logger.warning("cache_delete_failed", key=key, error=str(e))

    def has(self, key: str) -> bool:
        """Check if a key exists in cache."""
        return self.get(key) is not None


class DiskCacheBackend:
    """diskcache-based backend for development."""

    def __init__(self, cache):
        self.cache = cache

    def get(self, key: str) -> Any | None:
        entry = self.cache.get(key)
        if entry is None:
            return None
        # Check expiry
        if isinstance(entry, dict) and "expires_at" in entry:
            if time.time() > entry["expires_at"]:
                self.cache.delete(key)
                return None
            return entry["value"]
        return entry

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        entry = {
            "value": value,
            "expires_at": time.time() + ttl_seconds,
        }
        self.cache.set(key, entry, expire=ttl_seconds)

    def delete(self, key: str) -> None:
        self.cache.delete(key)


class RedisBackend:
    """Redis-based backend for production."""

    def __init__(self, client):
        self.client = client

    def get(self, key: str) -> Any | None:
        value = self.client.get(key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        serialized = json.dumps(value, default=str)
        self.client.setex(key, ttl_seconds, serialized)

    def delete(self, key: str) -> None:
        self.client.delete(key)


# Global cache service instance
cache_service = CacheService()
