"""Redis repository for Memory Engine - handles caching, session data, and real-time features."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import asyncio

import redis.asyncio as redis
from redis.asyncio import Redis

from pao_shared.config import get_settings

from ..models import (
    MemoryType,
    MemoryFilter,
)
from .base import MemoryRepository

settings = get_settings()


class RedisRepository(MemoryRepository):
    """Redis repository for caching and real-time memory operations."""
    
    # Key prefixes
    PREFIXES = {
        "memory_cache": "mem:cache",
        "recall_cache": "mem:recall",
        "consolidation_lock": "mem:consol:lock",
        "consolidation_progress": "mem:consol:progress",
        "session": "mem:session",
        "rate_limit": "mem:ratelimit",
        "embedding_cache": "mem:embedding",
        "recent_memories": "mem:recent",
    }
    
    # TTL settings (seconds)
    CACHE_TTL = 3600  # 1 hour
    RECALL_CACHE_TTL = 300  # 5 minutes
    LOCK_TTL = 300  # 5 minutes
    SESSION_TTL = 86400  # 24 hours
    RECENT_MEMORIES_TTL = 604800  # 7 days
    
    def __init__(self, url: Optional[str] = None):
        self.url = url or settings.redis_url
        self.client: Optional[Redis] = None
    
    async def initialize(self) -> None:
        """Initialize Redis client."""
        self.client = redis.from_url(
            self.url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,
        )
        # Test connection
        await self.client.ping()
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self.client:
            await self.client.close()
    
    def _key(self, prefix: str, *parts: str) -> str:
        """Build a Redis key."""
        return f"{self.PREFIXES[prefix]}:{':'.join(parts)}"
    
    # Memory caching
    async def cache_memory(self, memory_id: str, memory_type: MemoryType, 
                           data: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Cache a memory object."""
        key = self._key("memory_cache", memory_type.value, memory_id)
        await self.client.setex(
            key,
            ttl or self.CACHE_TTL,
            json.dumps(data, default=str),
        )
    
    async def get_cached_memory(self, memory_id: str, memory_type: MemoryType) -> Optional[Dict[str, Any]]:
        """Get a cached memory object."""
        key = self._key("memory_cache", memory_type.value, memory_id)
        data = await self.client.get(key)
        if data:
            return json.loads(data)
        return None
    
    async def invalidate_memory_cache(self, memory_id: str, memory_type: MemoryType) -> None:
        """Invalidate a memory cache entry."""
        key = self._key("memory_cache", memory_type.value, memory_id)
        await self.client.delete(key)
    
    # Recall caching
    async def cache_recall(self, query_hash: str, companion_id: str, 
                           results: List[Dict[str, Any]], ttl: Optional[int] = None) -> None:
        """Cache recall results."""
        key = self._key("recall_cache", companion_id, query_hash)
        await self.client.setex(
            key,
            ttl or self.RECALL_CACHE_TTL,
            json.dumps(results, default=str),
        )
    
    async def get_cached_recall(self, query_hash: str, companion_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached recall results."""
        key = self._key("recall_cache", companion_id, query_hash)
        data = await self.client.get(key)
        if data:
            return json.loads(data)
        return None
    
    async def invalidate_recall_cache(self, companion_id: str, pattern: str = "*") -> None:
        """Invalidate recall cache for a companion."""
        pattern_key = self._key("recall_cache", companion_id, pattern)
        keys = []
        async for key in self.client.scan_iter(match=pattern_key):
            keys.append(key)
        if keys:
            await self.client.delete(*keys)
    
    # Consolidation locking
    async def acquire_consolidation_lock(self, companion_id: str, 
                                          ttl: Optional[int] = None) -> bool:
        """Acquire a lock for consolidation (prevents concurrent runs)."""
        key = self._key("consolidation_lock", companion_id)
        return await self.client.set(
            key, "locked", nx=True, ex=ttl or self.LOCK_TTL
        )
    
    async def release_consolidation_lock(self, companion_id: str) -> None:
        """Release consolidation lock."""
        key = self._key("consolidation_lock", companion_id)
        await self.client.delete(key)
    
    async def is_consolidation_locked(self, companion_id: str) -> bool:
        """Check if consolidation is locked."""
        key = self._key("consolidation_lock", companion_id)
        return await self.client.exists(key) > 0
    
    async def set_consolidation_progress(self, companion_id: str, 
                                          progress: Dict[str, Any]) -> None:
        """Set consolidation progress."""
        key = self._key("consolidation_progress", companion_id)
        await self.client.setex(
            key,
            self.LOCK_TTL,
            json.dumps(progress, default=str),
        )
    
    async def get_consolidation_progress(self, companion_id: str) -> Optional[Dict[str, Any]]:
        """Get consolidation progress."""
        key = self._key("consolidation_progress", companion_id)
        data = await self.client.get(key)
        if data:
            return json.loads(data)
        return None
    
    # Recent memories tracking (for quick access)
    async def add_recent_memory(self, companion_id: str, memory_id: str, 
                                 memory_type: MemoryType, timestamp: Optional[str] = None) -> None:
        """Add a memory to recent memories sorted set."""
        key = self._key("recent_memories", companion_id)
        score = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).timestamp() if timestamp else datetime.utcnow().timestamp()
        member = f"{memory_type.value}:{memory_id}"
        await self.client.zadd(key, {member: score})
        # Trim to last 1000 memories
        await self.client.zremrangebyrank(key, 0, -1001)
        # Set TTL
        await self.client.expire(key, self.RECENT_MEMORIES_TTL)
    
    async def get_recent_memories(self, companion_id: str, 
                                   limit: int = 50,
                                   memory_types: Optional[List[MemoryType]] = None) -> List[Dict[str, Any]]:
        """Get recent memories for a companion."""
        key = self._key("recent_memories", companion_id)
        # Get most recent first
        members = await self.client.zrevrange(key, 0, limit - 1, withscores=True)
        
        results = []
        for member, score in members:
            mem_type_str, mem_id = member.split(":", 1)
            mem_type = MemoryType(mem_type_str)
            
            if memory_types and mem_type not in memory_types:
                continue
            
            results.append({
                "memory_id": mem_id,
                "type": mem_type,
                "timestamp": datetime.utcfromtimestamp(score).isoformat(),
            })
        
        return results
    
    # Embedding cache
    async def cache_embedding(self, text_hash: str, embedding: List[float]) -> None:
        """Cache an embedding vector."""
        key = self._key("embedding_cache", text_hash)
        await self.client.setex(
            key,
            self.CACHE_TTL * 24,  # Longer TTL for embeddings
            json.dumps(embedding),
        )
    
    async def get_cached_embedding(self, text_hash: str) -> Optional[List[float]]:
        """Get a cached embedding vector."""
        key = self._key("embedding_cache", text_hash)
        data = await self.client.get(key)
        if data:
            return json.loads(data)
        return None
    
    # Session management
    async def set_session(self, session_id: str, data: Dict[str, Any], 
                           ttl: Optional[int] = None) -> None:
        """Set session data."""
        key = self._key("session", session_id)
        await self.client.setex(
            key,
            ttl or self.SESSION_TTL,
            json.dumps(data, default=str),
        )
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        key = self._key("session", session_id)
        data = await self.client.get(key)
        if data:
            return json.loads(data)
        return None
    
    async def delete_session(self, session_id: str) -> None:
        """Delete session data."""
        key = self._key("session", session_id)
        await self.client.delete(key)
    
    # Rate limiting
    async def check_rate_limit(self, identifier: str, limit: int, 
                                window_seconds: int) -> tuple[bool, int]:
        """Check rate limit using sliding window."""
        key = self._key("rate_limit", identifier)
        now = datetime.utcnow().timestamp()
        window_start = now - window_seconds
        
        # Remove old entries
        await self.client.zremrangebyscore(key, 0, window_start)
        
        # Count current requests
        count = await self.client.zcard(key)
        
        if count >= limit:
            # Get oldest entry to calculate retry-after
            oldest = await self.client.zrange(key, 0, 0, withscores=True)
            if oldest:
                retry_after = int(oldest[0][1] + window_seconds - now) + 1
            else:
                retry_after = window_seconds
            return False, retry_after
        
        # Add current request
        await self.client.zadd(key, {f"{now}": now})
        await self.client.expire(key, window_seconds + 1)
        
        return True, 0
    
    # Pub/Sub for real-time updates
    async def publish_memory_event(self, companion_id: str, event_type: str, 
                                    data: Dict[str, Any]) -> None:
        """Publish a memory event for real-time subscribers."""
        channel = self._key("events", companion_id)
        message = json.dumps({
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }, default=str)
        await self.client.publish(channel, message)
    
    async def subscribe_to_events(self, companion_id: str):
        """Subscribe to memory events for a companion."""
        channel = self._key("events", companion_id)
        pubsub = self.client.pubsub()
        await pubsub.subscribe(channel)
        return pubsub
    
    # Write operations (stubs - not primary storage)
    async def write_episodic(self, memory: Any) -> str:
        # Cache the memory
        await self.cache_memory(memory.id, MemoryType.EPISODIC, memory.model_dump())
        await self.add_recent_memory(memory.companion_id, memory.id, MemoryType.EPISODIC, memory.created_at)
        return memory.id
    
    async def write_semantic(self, memory: Any) -> str:
        await self.cache_memory(memory.id, MemoryType.SEMANTIC, memory.model_dump())
        await self.add_recent_memory(memory.companion_id, memory.id, MemoryType.SEMANTIC, memory.created_at)
        return memory.id
    
    async def write_emotional(self, memory: Any) -> str:
        await self.cache_memory(memory.id, MemoryType.EMOTIONAL, memory.model_dump())
        await self.add_recent_memory(memory.companion_id, memory.id, MemoryType.EMOTIONAL, memory.created_at)
        return memory.id
    
    async def write_relationship(self, memory: Any) -> str:
        return memory.id
    
    async def write_timeline(self, memory: Any) -> str:
        return memory.id
    
    async def write_preference(self, memory: Any) -> str:
        # Preferences are frequently accessed - cache them
        await self.cache_memory(memory.id, MemoryType.PREFERENCE, memory.model_dump(), ttl=86400)
        return memory.id
    
    async def bulk_write(self, memories: List[Any]) -> List[str]:
        ids = []
        for memory in memories:
            if hasattr(memory, 'type'):
                if memory.type == MemoryType.EPISODIC:
                    ids.append(await self.write_episodic(memory))
                elif memory.type == MemoryType.SEMANTIC:
                    ids.append(await self.write_semantic(memory))
                elif memory.type == MemoryType.EMOTIONAL:
                    ids.append(await self.write_emotional(memory))
                elif memory.type == MemoryType.PREFERENCE:
                    ids.append(await self.write_preference(memory))
        return ids
    
    # Read operations
    async def get_by_id(self, memory_id: str, memory_type: MemoryType) -> Optional[Any]:
        cached = await self.get_cached_memory(memory_id, memory_type)
        if cached:
            # Return dict - caller will convert to proper model
            return cached
        return None
    
    async def get_by_ids(self, memory_ids: List[str], memory_type: MemoryType) -> List[Any]:
        # Batch get from cache
        results = []
        for mid in memory_ids:
            cached = await self.get_cached_memory(mid, memory_type)
            if cached:
                results.append(cached)
        return results
    
    # Query operations
    async def query(self, filter: MemoryFilter) -> List[Any]:
        # Redis doesn't support complex queries - fallback to get recent
        return await self.get_recent_memories(
            filter.companion_id,
            limit=filter.limit or 50,
            memory_types=[filter.type] if filter.type else None
        )
    
    async def recall(self, query: Any, context: Any) -> Any:
        # Redis doesn't handle vector recall
        return None
    
    # Update operations
    async def update(self, memory_id: str, memory_type: MemoryType, updates: Dict[str, Any], 
                     new_version: int, reason: str) -> bool:
        # Invalidate cache on update
        await self.invalidate_memory_cache(memory_id, memory_type)
        return True
    
    # Delete operations
    async def delete(self, memory_id: str, memory_type: MemoryType, 
                     verification: bool = True) -> Dict[str, Any]:
        await self.invalidate_memory_cache(memory_id, memory_type)
        return {"memory_id": memory_id, "verification": {"cache_invalidated": True}}
    
    async def bulk_delete(self, filter: MemoryFilter, confirm: bool = False) -> Dict[str, Any]:
        if filter.type:
            # Invalidate all caches for this companion and type
            pattern = self._key("memory_cache", filter.type.value, f"{filter.companion_id}:*")
            keys = []
            async for key in self.client.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                await self.client.delete(*keys)
        return {"deleted_count": len(keys), "verification": {"cache_invalidated": True}}
    
    # Export operations
    async def export_all(self, companion_id: str, user_id: str, 
                         formats: List[str]) -> Dict[str, str]:
        return {"cache": "export_job_id", "status": "processing"}
    
    # Consolidation support
    async def get_consolidation_candidates(self, companion_id: str, 
                                           older_than_days: int = 30,
                                           max_access_count: int = 3) -> List[Any]:
        return []
    
    async def mark_consolidated(self, memory_ids: List[str], 
                                semantic_memory_ids: List[str]) -> None:
        # Invalidate caches for consolidated memories
        for mem_id in memory_ids:
            await self.invalidate_memory_cache(mem_id, MemoryType.EPISODIC)
    
    # Consistency validation
    async def get_memories_for_validation(self, companion_id: str, 
                                           memory_types: List[MemoryType]) -> List[Any]:
        return []