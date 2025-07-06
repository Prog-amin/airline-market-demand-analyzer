"""
Redis client and connection management.

This module provides a Redis client and connection management utilities.
"""
import aioredis
from typing import AsyncGenerator, Optional

from app.core.config import settings

# Global Redis connection pool
_redis_pool = None

async def get_redis() -> aioredis.Redis:
    """
    Get a Redis connection from the pool.
    
    Returns:
        aioredis.Redis: A Redis client instance
    """
    global _redis_pool
    
    if _redis_pool is None:
        await init_redis_pool()
    
    return _redis_pool

async def init_redis_pool() -> None:
    """
    Initialize the Redis connection pool.
    
    This should be called during application startup.
    """
    global _redis_pool
    
    if _redis_pool is not None:
        return
    
    # Create a Redis connection pool
    _redis_pool = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        max_connections=settings.REDIS_MAX_CONNECTIONS,
    )

async def close_redis_pool() -> None:
    """
    Close the Redis connection pool.
    
    This should be called during application shutdown.
    """
    global _redis_pool
    
    if _redis_pool is not None:
        await _redis_pool.close()
        await _redis_pool.wait_closed()
        _redis_pool = None

async def get_redis_connection() -> AsyncGenerator[aioredis.Redis, None]:
    """
    Get a Redis connection for use in dependency injection.
    
    Yields:
        aioredis.Redis: A Redis client instance
    """
    redis = await get_redis()
    try:
        yield redis
    finally:
        # The connection is returned to the pool automatically
        pass

class RedisCache:
    """
    A simple Redis-based cache.
    
    This class provides a simple interface for caching data in Redis.
    """
    
    def __init__(self, redis: aioredis.Redis, prefix: str = "cache:"):
        """
        Initialize the cache.
        
        Args:
            redis: A Redis client instance
            prefix: Prefix for all cache keys
        """
        self.redis = redis
        self.prefix = prefix
    
    def _get_key(self, key: str) -> str:
        """Get the full cache key with prefix."""
        return f"{self.prefix}{key}"
    
    async def get(self, key: str) -> Optional[str]:
        """
        Get a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            Optional[str]: The cached value, or None if not found
        """
        return await self.redis.get(self._get_key(key))
    
    async def set(
        self, 
        key: str, 
        value: str, 
        expire: Optional[int] = None
    ) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: The cache key
            value: The value to cache
            expire: Time to live in seconds (None for no expiration)
            
        Returns:
            bool: True if the operation was successful
        """
        if expire is not None:
            return await self.redis.setex(
                self._get_key(key), 
                expire, 
                value
            )
        else:
            return await self.redis.set(
                self._get_key(key), 
                value
            )
    
    async def delete(self, *keys: str) -> int:
        """
        Delete one or more keys from the cache.
        
        Args:
            *keys: The keys to delete
            
        Returns:
            int: The number of keys that were deleted
        """
        prefixed_keys = [self._get_key(key) for key in keys]
        return await self.redis.delete(*prefixed_keys)
    
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: The key to check
            
        Returns:
            bool: True if the key exists, False otherwise
        """
        return await self.redis.exists(self._get_key(key)) > 0
    
    async def expire(self, key: str, time: int) -> bool:
        """
        Set a key's time to live in seconds.
        
        Args:
            key: The key to set the TTL for
            time: Time to live in seconds
            
        Returns:
            bool: True if the timeout was set, False if key does not exist
        """
        return await self.redis.expire(self._get_key(key), time)
    
    async def ttl(self, key: str) -> int:
        """
        Get the time to live for a key.
        
        Args:
            key: The key to check
            
        Returns:
            int: TTL in seconds, -2 if the key does not exist, -1 if the key exists but has no TTL
        """
        return await self.redis.ttl(self._get_key(key))
    
    async def clear(self) -> bool:
        """
        Clear all keys with the current prefix.
        
        Returns:
            bool: True if the operation was successful
        """
        # This is a potentially expensive operation and should be used with caution
        keys = await self.redis.keys(f"{self.prefix}*")
        if keys:
            await self.redis.delete(*keys)
        return True

# Global cache instance
cache: Optional[RedisCache] = None

async def get_cache() -> RedisCache:
    """
    Get the global cache instance.
    
    Returns:
        RedisCache: The global cache instance
    """
    global cache
    
    if cache is None:
        redis = await get_redis()
        cache = RedisCache(redis)
    
    return cache
