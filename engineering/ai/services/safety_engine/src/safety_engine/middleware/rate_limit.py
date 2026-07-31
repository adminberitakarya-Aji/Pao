"""
Rate Limiting Middleware.

Token bucket rate limiting with Redis backend.
"""

import time
import logging
from typing import Callable, Awaitable, Optional, Dict, Tuple

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from safety_engine.config import get_settings
from safety_engine.repositories.redis import RedisRepository

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Token bucket rate limiting middleware."""
    
    def __init__(
        self,
        app,
        redis_repo: RedisRepository,
        exclude_paths: list = None,
        default_limit: int = 100,
        default_window: int = 60,
    ):
        super().__init__(app)
        self.settings = get_settings()
        self.redis_repo = redis_repo
        self.exclude_paths = exclude_paths or [
            "/health",
            "/health/live",
            "/health/ready",
            "/metrics",
        ]
        self.default_limit = default_limit
        self.default_window = default_window
        
        # Rate limit configurations per endpoint
        self.endpoint_limits = {
            "/api/v1/safety/validate-input": (50, 60),  # 50 req/min
            "/api/v1/safety/filter-output": (100, 60),  # 100 req/min
            "/api/v1/safety/status": (200, 60),  # 200 req/min
        }
    
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Skip rate limiting for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Get rate limit for this endpoint
        limit, window = self._get_endpoint_limit(request.url.path)
        
        # Check rate limit
        allowed, remaining, reset_time = await self._check_rate_limit(
            client_id,
            request.url.path,
            limit,
            window,
        )
        
        if not allowed:
            # Rate limited
            response = Response(
                content=f'{{"detail": "Rate limit exceeded. Try again in {reset_time - int(time.time())} seconds."}}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
            )
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["X-RateLimit-Reset"] = str(reset_time)
            response.headers["Retry-After"] = str(reset_time - int(time.time()))
            return response
        
        # Continue with request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier for rate limiting."""
        # Try to get user ID from auth
        token_data = getattr(request.state, "token_data", None)
        if token_data and token_data.user_id:
            return f"user:{token_data.user_id}"
        
        # Try service name
        if token_data and token_data.service_name:
            return f"service:{token_data.service_name}"
        
        # Fall back to IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        
        return f"ip:{ip}"
    
    def _get_endpoint_limit(self, path: str) -> Tuple[int, int]:
        """Get rate limit for endpoint (limit, window_seconds)."""
        # Check exact match first
        if path in self.endpoint_limits:
            return self.endpoint_limits[path]
        
        # Check prefix matches
        for pattern, (limit, window) in self.endpoint_limits.items():
            if path.startswith(pattern.rstrip("*")):
                return (limit, window)
        
        return (self.default_limit, self.default_window)
    
    async def _check_rate_limit(
        self,
        client_id: str,
        endpoint: str,
        limit: int,
        window: int,
    ) -> Tuple[bool, int, int]:
        """
        Check rate limit using token bucket algorithm.
        
        Returns:
            (allowed, remaining, reset_time)
        """
        key = f"ratelimit:{client_id}:{endpoint}"
        now = time.time()
        window_start = now - window
        
        # Use Redis sorted set for sliding window
        # Score = timestamp, Member = unique request ID
        request_id = f"{now}:{time.perf_counter()}"
        
        # Add current request
        await self.redis_repo.client.zadd(key, {request_id: now})
        
        # Remove old entries outside window
        await self.redis_repo.client.zremrangebyscore(key, 0, window_start)
        
        # Set expiry on key
        await self.redis_repo.client.expire(key, window + 1)
        
        # Count requests in window
        current_count = await self.redis_repo.client.zcard(key)
        
        if current_count > limit:
            # Rate limited - remove the request we just added
            await self.redis_repo.client.zrem(key, request_id)
            
            # Calculate when oldest request expires
            oldest = await self.redis_repo.client.zrange(key, 0, 0, withscores=True)
            if oldest:
                reset_time = int(oldest[0][1]) + window
            else:
                reset_time = int(now) + window
            
            return (False, 0, reset_time)
        
        remaining = limit - current_count
        reset_time = int(now) + window
        
        return (True, remaining, reset_time)


class AdaptiveRateLimiter:
    """Adaptive rate limiter that adjusts limits based on system load."""
    
    def __init__(self, redis_repo: RedisRepository):
        self.redis_repo = redis_repo
        self.settings = get_settings()
    
    async def get_adaptive_limit(
        self,
        base_limit: int,
        service_name: str = "safety-engine",
    ) -> int:
        """Calculate adaptive limit based on current system load."""
        # Get current CPU/memory usage from metrics
        # This is a simplified version - in production, use actual metrics
        
        try:
            # Try to get load from Redis (set by metrics worker)
            load_key = f"system:load:{service_name}"
            load_data = await self.redis_repo.client.get(load_key)
            
            if load_data:
                import json
                load = json.loads(load_data)
                cpu_percent = load.get("cpu_percent", 50)
                memory_percent = load.get("memory_percent", 50)
                
                # Reduce limit if system is under high load
                if cpu_percent > 80 or memory_percent > 85:
                    return max(int(base_limit * 0.5), 10)
                elif cpu_percent > 60 or memory_percent > 70:
                    return max(int(base_limit * 0.75), 20)
        except Exception as e:
            logger.warning(f"Failed to get adaptive limit: {e}")
        
        return base_limit
    
    async def record_request_latency(self, endpoint: str, latency_ms: float) -> None:
        """Record request latency for adaptive limiting."""
        key = f"ratelimit:latency:{endpoint}"
        now = time.time()
        
        # Store latency with timestamp
        await self.redis_repo.client.zadd(key, {f"{now}:{latency_ms}": now})
        await self.redis_repo.client.expire(key, 60)  # Keep 1 minute
    
    async def get_avg_latency(self, endpoint: str, window: int = 60) -> float:
        """Get average latency for endpoint."""
        key = f"ratelimit:latency:{endpoint}"
        window_start = time.time() - window
        
        # Remove old entries
        await self.redis_repo.client.zremrangebyscore(key, 0, window_start)
        
        # Get all latencies
        entries = await self.redis_repo.client.zrange(key, 0, -1, withscores=True)
        
        if not entries:
            return 0.0
        
        latencies = [float(member.split(":")[-1]) for member, _ in entries]
        return sum(latencies) / len(latencies)