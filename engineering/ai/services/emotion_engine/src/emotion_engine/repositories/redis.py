"""Redis repositories for Emotion Engine - caching and real-time state."""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

import redis.asyncio as redis
from redis.asyncio import Redis

from emotion_engine.config import settings
from emotion_engine.models.emotion import (
    EmotionState,
    ValenceArousal,
    Appraisal,
    CalibrationData,
    Expression,
    EmotionEvent,
    EmotionCategory,
    ExpressionModality,
)


class RedisEmotionCache:
    """Redis cache for emotion state and real-time updates."""

    def __init__(self, redis_client: Optional[Redis] = None):
        self.redis = redis_client or redis.from_url(
            settings.redis_url,
            max_connections=settings.redis_max_connections,
            decode_responses=True,
        )
        self.state_ttl = settings.state_ttl_seconds
        self.cleanup_interval = settings.state_cleanup_interval_seconds

    async def close(self):
        """Close Redis connection."""
        await self.redis.close()

    # State caching
    async def get_state(self, user_id: UUID, companion_id: UUID) -> Optional[EmotionState]:
        """Get cached emotion state."""
        key = f"emotion:state:{user_id}:{companion_id}"
        data = await self.redis.get(key)
        if not data:
            return None
        return EmotionState.model_validate_json(data)

    async def set_state(self, state: EmotionState) -> None:
        """Cache emotion state."""
        key = f"emotion:state:{state.user_id}:{state.companion_id}"
        await self.redis.setex(key, self.state_ttl, state.model_dump_json())

    async def delete_state(self, user_id: UUID, companion_id: UUID) -> None:
        """Delete cached state."""
        key = f"emotion:state:{user_id}:{companion_id}"
        await self.redis.delete(key)

    async def update_valence_arousal(
        self,
        user_id: UUID,
        companion_id: UUID,
        valence: float,
        arousal: float,
        confidence: float = 0.8,
    ) -> None:
        """Quick update of valence/arousal in cache."""
        key = f"emotion:state:{user_id}:{companion_id}"
        pipe = self.redis.pipeline()
        pipe.hset(
            key,
            mapping={
                "valence": valence,
                "arousal": arousal,
                "va_confidence": confidence,
                "va_timestamp": datetime.utcnow().isoformat(),
            },
        )
        pipe.expire(key, self.state_ttl)
        await pipe.execute()

    # Real-time pub/sub for emotion updates
    async def publish_emotion_update(
        self,
        user_id: UUID,
        companion_id: UUID,
        event_type: str,
        data: Dict[str, Any],
    ) -> None:
        """Publish emotion update to subscribers."""
        channel = f"emotion:updates:{user_id}:{companion_id}"
        message = {
            "user_id": str(user_id),
            "companion_id": str(companion_id),
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.redis.publish(channel, json.dumps(message))

    async def subscribe_emotion_updates(
        self,
        user_id: UUID,
        companion_id: UUID,
    ):
        """Subscribe to emotion updates for a user-companion pair."""
        channel = f"emotion:updates:{user_id}:{companion_id}"
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel)
        return pubsub

    # Appraisal caching
    async def cache_appraisal(
        self,
        user_id: UUID,
        companion_id: UUID,
        appraisal: Appraisal,
    ) -> None:
        """Cache latest appraisal."""
        key = f"emotion:appraisal:{user_id}:{companion_id}"
        await self.redis.setex(key, self.state_ttl, appraisal.model_dump_json())

    async def get_cached_appraisal(
        self,
        user_id: UUID,
        companion_id: UUID,
    ) -> Optional[Appraisal]:
        """Get cached appraisal."""
        key = f"emotion:appraisal:{user_id}:{companion_id}"
        data = await self.redis.get(key)
        if not data:
            return None
        return Appraisal.model_validate_json(data)

    # Expression template caching
    async def cache_expression(
        self,
        modality: ExpressionModality,
        emotion_category: EmotionCategory,
        expression: Expression,
    ) -> None:
        """Cache expression template."""
        key = f"emotion:expression:{modality.value}:{emotion_category.value}"
        await self.redis.set(key, expression.model_dump_json())

    async def get_cached_expression(
        self,
        modality: ExpressionModality,
        emotion_category: EmotionCategory,
    ) -> Optional[Expression]:
        """Get cached expression template."""
        key = f"emotion:expression:{modality.value}:{emotion_category.value}"
        data = await self.redis.get(key)
        if not data:
            return None
        return Expression.model_validate_json(data)

    # Calibration caching
    async def cache_calibration(
        self,
        user_id: UUID,
        companion_id: UUID,
        calibration: CalibrationData,
    ) -> None:
        """Cache calibration data."""
        key = f"emotion:calibration:{user_id}:{companion_id}"
        await self.redis.setex(key, self.state_ttl * 2, calibration.model_dump_json())

    async def get_cached_calibration(
        self,
        user_id: UUID,
        companion_id: UUID,
    ) -> Optional[CalibrationData]:
        """Get cached calibration."""
        key = f"emotion:calibration:{user_id}:{companion_id}"
        data = await self.redis.get(key)
        if not data:
            return None
        return CalibrationData.model_validate_json(data)

    # Rate limiting for API
    async def check_rate_limit(
        self,
        identifier: str,
        limit: int,
        window_seconds: int,
    ) -> tuple[bool, int]:
        """
        Check rate limit using sliding window.
        Returns (allowed, remaining).
        """
        key = f"ratelimit:{identifier}"
        now = datetime.utcnow().timestamp()
        window_start = now - window_seconds

        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, window_seconds)
        results = await pipe.execute()

        current_count = results[1]
        allowed = current_count < limit
        remaining = max(0, limit - current_count - 1)
        return allowed, remaining

    # Session/lock management
    async def acquire_lock(
        self,
        lock_name: str,
        timeout: float = 10.0,
        ttl: float = 30.0,
    ) -> bool:
        """Acquire distributed lock."""
        lock_key = f"lock:{lock_name}"
        return await self.redis.set(lock_key, "1", nx=True, ex=int(ttl))

    async def release_lock(self, lock_name: str) -> None:
        """Release distributed lock."""
        lock_key = f"lock:{lock_name}"
        await self.redis.delete(lock_key)

    # Metrics counters
    async def increment_counter(self, name: str, value: int = 1) -> int:
        """Increment a counter."""
        key = f"metrics:counter:{name}"
        return await self.redis.incrby(key, value)

    async def get_counter(self, name: str) -> int:
        """Get counter value."""
        key = f"metrics:counter:{name}"
        val = await self.redis.get(key)
        return int(val) if val else 0

    async def set_gauge(self, name: str, value: float) -> None:
        """Set a gauge value."""
        key = f"metrics:gauge:{name}"
        await self.redis.set(key, value)

    async def get_gauge(self, name: str) -> Optional[float]:
        """Get gauge value."""
        key = f"metrics:gauge:{name}"
        val = await self.redis.get(key)
        return float(val) if val else None

    # Cleanup
    async def cleanup_expired_states(self) -> int:
        """Clean up expired emotion states (run periodically)."""
        pattern = "emotion:state:*"
        count = 0
        async for key in self.redis.scan_iter(match=pattern):
            ttl = await self.redis.ttl(key)
            if ttl == -1:  # No expiry set
                await self.redis.delete(key)
                count += 1
        return count


# Singleton instance
_redis_cache: Optional[RedisEmotionCache] = None


async def get_redis_cache() -> RedisEmotionCache:
    """Get or create Redis cache singleton."""
    global _redis_cache
    if _redis_cache is None:
        _redis_cache = RedisEmotionCache()
    return _redis_cache


# Alias classes for backward compatibility with __init__.py imports
class RedisEmotionStateCache(RedisEmotionCache):
    """Alias for RedisEmotionCache for backward compatibility."""
    pass


class RedisAppraisalCache(RedisEmotionCache):
    """Alias for RedisEmotionCache for backward compatibility."""
    pass


class RedisCalibrationCache(RedisEmotionCache):
    """Alias for RedisEmotionCache for backward compatibility."""
    pass
