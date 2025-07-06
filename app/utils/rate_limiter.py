"""
Rate limiting utilities for the API.

This module provides rate limiting functionality to prevent abuse of the API.
It uses Redis for distributed rate limiting in production and an in-memory
cache for development.
"""
import asyncio
import time
from datetime import timedelta
from typing import Optional, Callable, Awaitable, Any, Dict

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import RequestResponseEndpoint

from app.core.config import settings
from app.core.redis import get_redis

# In-memory rate limit storage for development
_rate_limit_store = {}
_rate_limit_locks = {}

class RateLimitExceeded(HTTPException):
    """Exception raised when a rate limit is exceeded."""
    def __init__(self, detail: str, headers: Optional[Dict[str, str]] = None):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers=headers or {}
        )

class RateLimiter:
    """
    Rate limiter for API endpoints.
    
    This class provides both in-memory and Redis-based rate limiting.
    """
    
    def __init__(
        self,
        key_prefix: str,
        limit: int,
        window: int = 60,
        scope: Optional[str] = None,
        by_ip: bool = False,
        by_user: bool = False,
        by_endpoint: bool = True
    ):
        """
        Initialize the rate limiter.
        
        Args:
            key_prefix: Prefix for the rate limit key
            limit: Maximum number of requests allowed in the time window
            window: Time window in seconds
            scope: Optional scope for the rate limit
            by_ip: Whether to rate limit by IP address
            by_user: Whether to rate limit by user ID
            by_endpoint: Whether to include the endpoint in the rate limit key
        """
        self.key_prefix = key_prefix
        self.limit = limit
        self.window = window
        self.scope = scope
        self.by_ip = by_ip
        self.by_user = by_user
        self.by_endpoint = by_endpoint
    
    async def _get_redis_key(self, request: Request) -> str:
        """Generate a Redis key for rate limiting."""
        parts = [self.key_prefix]
        
        if self.scope:
            parts.append(self.scope)
            
        if self.by_ip:
            # Get the client's IP address
            if request.client is None:
                ip = "unknown"
            else:
                # Handle X-Forwarded-For if behind a proxy
                if "x-forwarded-for" in request.headers:
                    ip = request.headers["x-forwarded-for"].split(",")[0].strip()
                else:
                    ip = request.client.host or "unknown"
            parts.append(f"ip:{ip}")
        
        if self.by_user and hasattr(request, "user") and request.user:
            parts.append(f"user:{request.user.id}")
        
        if self.by_endpoint:
            parts.append(f"endpoint:{request.url.path}")
        
        return ":".join(parts)
    
    async def _in_memory_rate_limit(self, key: str) -> Dict[str, Any]:
        """
        In-memory rate limiting implementation.
        
        This is used when Redis is not available (e.g., in development).
        """
        current_time = time.time()
        
        # Ensure thread safety
        if key not in _rate_limit_locks:
            _rate_limit_locks[key] = asyncio.Lock()
        
        async with _rate_limit_locks[key]:
            if key in _rate_limit_store:
                count, reset_time = _rate_limit_store[key]
                if current_time > reset_time:
                    # Reset the counter if the window has passed
                    count = 1
                    reset_time = current_time + self.window
                else:
                    count += 1
            else:
                # First request in the window
                count = 1
                reset_time = current_time + self.window
            
            _rate_limit_store[key] = (count, reset_time)
            
            remaining = max(0, self.limit - count)
            return {
                "limit": self.limit,
                "remaining": remaining,
                "reset": int(reset_time - current_time),
                "count": count
            }
    
    async def _redis_rate_limit(self, key: str) -> Dict[str, Any]:
        """
        Redis-based rate limiting implementation.
        
        This is the production implementation that uses Redis for distributed
        rate limiting.
        """
        redis = await get_redis()
        
        # Use a Lua script for atomic operations
        lua_script = """
        local key = KEYS[1]
        local limit = tonumber(ARGV[1])
        local window = tonumber(ARGV[2])
        
        local current = redis.call('INCR', key)
        
        if current == 1 then
            redis.call('EXPIRE', key, window)
        end
        
        local ttl = redis.call('TTL', key)
        local remaining = math.max(0, limit - current)
        
        return {current, remaining, ttl}
        """
        
        result = await redis.eval(
            lua_script,
            keys=[key],
            args=[self.limit, self.window]
        )
        
        count, remaining, reset = result
        
        return {
            "limit": self.limit,
            "remaining": remaining,
            "reset": reset,
            "count": count
        }
    
    async def check_rate_limit(self, request: Request) -> Dict[str, Any]:
        """
        Check if the request is within the rate limit.
        
        Args:
            request: The incoming request
            
        Returns:
            Dict[str, Any]: Rate limit information
            
        Raises:
            RateLimitExceeded: If the rate limit is exceeded
        """
        key = await self._get_redis_key(request)
        
        if settings.USE_REDIS:
            rate_info = await self._redis_rate_limit(key)
        else:
            rate_info = await self._in_memory_rate_limit(key)
        
        # Add rate limit headers
        request.state.rate_limit = {
            "limit": rate_info["limit"],
            "remaining": rate_info["remaining"],
            "reset": rate_info["reset"]
        }
        
        if rate_info["remaining"] < 0:
            raise RateLimitExceeded(
                "Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(rate_info["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(rate_info["reset"]),
                    "Retry-After": str(rate_info["reset"])
                }
            )
        
        return rate_info
    
    async def __call__(
        self,
        request: Request,
        call_next: RequestResponseEndpoint
    ) -> JSONResponse:
        """
        Middleware implementation for rate limiting.
        
        This can be used as a FastAPI middleware.
        """
        try:
            await self.check_rate_limit(request)
            response = await call_next(request)
            
            # Add rate limit headers to the response
            if hasattr(request.state, "rate_limit"):
                rate_limit = request.state.rate_limit
                response.headers["X-RateLimit-Limit"] = str(rate_limit["limit"])
                response.headers["X-RateLimit-Remaining"] = str(rate_limit["remaining"])
                response.headers["X-RateLimit-Reset"] = str(rate_limit["reset"])
            
            return response
            
        except RateLimitExceeded as e:
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": str(e.detail)}
            )
            
            # Add rate limit headers to the error response
            for key, value in e.headers.items():
                if key.lower().startswith("x-ratelimit-"):
                    response.headers[key] = value
            
            return response

# Common rate limiters
api_rate_limiter = RateLimiter(
    key_prefix="rl:api",
    limit=100,  # 100 requests
    window=60,  # per minute
    by_ip=True
)

auth_rate_limiter = RateLimiter(
    key_prefix="rl:auth",
    limit=5,  # 5 requests
    window=60,  # per minute
    by_ip=True
)

def get_rate_limiter(
    key_prefix: str,
    limit: int,
    window: int = 60,
    scope: Optional[str] = None,
    by_ip: bool = False,
    by_user: bool = False,
    by_endpoint: bool = True
) -> RateLimiter:
    """
    Get a rate limiter instance.
    
    This is a convenience function for creating rate limiters with common configurations.
    """
    return RateLimiter(
        key_prefix=key_prefix,
        limit=limit,
        window=window,
        scope=scope,
        by_ip=by_ip,
        by_user=by_user,
        by_endpoint=by_endpoint
    )
