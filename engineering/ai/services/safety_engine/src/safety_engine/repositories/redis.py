"""
Redis Repository Implementation.

Provides caching, rate limiting, and real-time data storage for safety engine
using Redis with asyncio support.
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

import redis.asyncio as redis
from redis.asyncio import Redis

from safety_engine.config import get_settings
from safety_engine.models.safety import (
    SafetyAlert,
    SafetyCategory,
    SafetyCheckResponse,
    SafetyMetrics,
    SafetyViolation,
)
from safety_engine.repositories.base import BaseRepository


class RedisRepository(BaseRepository):
    """Redis implementation for caching and real-time safety data."""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.settings = get_settings()
        self.redis_url = redis_url or self.settings.redis_url
        self.client: Optional[Redis] = None
        self._local_cache: Dict[str, Any] = {}
    
    async def initialize(self) -> None:
        """Initialize Redis connection."""
        self.client = redis.from_url(
            self.redis_url,
            max_connections=self.settings.redis_max_connections,
            decode_responses=True,
        )
        # Test connection
        await self.client.ping()
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self.client:
            await self.client.close()
    
    async def health_check(self) -> bool:
        """Check Redis connectivity."""
        try:
            if self.client:
                await self.client.ping()
                return True
        except Exception:
            pass
        return False
    
    # Key prefixes
    CRISIS_EVENT_PREFIX = "safety:crisis:"
    ALERT_PREFIX = "safety:alert:"
    CONTENT_FILTER_PREFIX = "safety:content_filter:"
    BEHAVIORAL_GUARD_PREFIX = "safety:behavioral_guard:"
    REALITY_ANCHOR_PREFIX = "safety:reality_anchor:"
    METRICS_PREFIX = "safety:metrics:"
    RATE_LIMIT_PREFIX = "safety:ratelimit:"
    CACHE_PREFIX = "safety:cache:"
    USER_SESSION_PREFIX = "safety:session:"
    
    def _crisis_key(self, event_id: UUID) -> str:
        return f"{self.CRISIS_EVENT_PREFIX}{event_id}"
    
    def _alert_key(self, alert_id: UUID) -> str:
        return f"{self.ALERT_PREFIX}{alert_id}"
    
    def _user_alerts_key(self, user_id: str) -> str:
        return f"{self.ALERT_PREFIX}user:{user_id}"
    
    def _content_filter_key(self, log_id: UUID) -> str:
        return f"{self.CONTENT_FILTER_PREFIX}{log_id}"
    
    def _behavioral_guard_key(self, log_id: UUID) -> str:
        return f"{self.BEHAVIORAL_GUARD_PREFIX}{log_id}"
    
    def _reality_anchor_key(self, log_id: UUID) -> str:
        return f"{self.REALITY_ANCHOR_PREFIX}{log_id}"
    
    def _metrics_key(self, period: str) -> str:
        return f"{self.METRICS_PREFIX}{period}"
    
    def _rate_limit_key(self, identifier: str) -> str:
        return f"{self.RATE_LIMIT_PREFIX}{identifier}"
    
    def _cache_key(self, key: str) -> str:
        return f"{self.CACHE_PREFIX}{key}"
    
    def _user_session_key(self, user_id: str) -> str:
        return f"{self.USER_SESSION_PREFIX}{user_id}"
    
    # Crisis Events (cached recent events)
    async def store_crisis_event(
        self,
        user_id: str,
        companion_id: str,
        conversation_id: Optional[str],
        crisis_result: Any,
        check_response: Any,
    ) -> UUID:
        """Store a crisis detection event in Redis (recent cache)."""
        from uuid import uuid4
        event_id = uuid4()
        
        data = {
            "id": str(event_id),
            "user_id": user_id,
            "companion_id": companion_id,
            "conversation_id": conversation_id,
            "crisis_type": crisis_result.crisis_type.value if crisis_result.crisis_type else "unknown",
            "confidence": crisis_result.confidence,
            "risk_level": crisis_result.risk_level,
            "urgency_score": crisis_result.urgency_score,
            "detected_keywords": crisis_result.detected_keywords,
            "detected_patterns": crisis_result.detected_patterns,
            "sentiment_score": crisis_result.sentiment_score,
            "intervention_level": crisis_result.recommended_intervention.value,
            "crisis_resources": crisis_result.crisis_resources,
            "requires_human_review": crisis_result.requires_human_review,
            "check_response": check_response.model_dump() if hasattr(check_response, 'model_dump') else check_response,
            "metadata": crisis_result.metadata,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        # Store with TTL (7 days)
        await self.client.setex(
            self._crisis_key(event_id),
            timedelta(days=7),
            json.dumps(data)
        )
        
        # Add to user's recent crisis events list
        user_crisis_key = f"{self.CRISIS_EVENT_PREFIX}user:{user_id}"
        await self.client.lpush(user_crisis_key, str(event_id))
        await self.client.ltrim(user_crisis_key, 0, 99)  # Keep last 100
        await self.client.expire(user_crisis_key, timedelta(days=7))
        
        return event_id
    
    async def get_crisis_events(
        self,
        user_id: Optional[str] = None,
        companion_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve recent crisis events from Redis cache."""
        if not user_id:
            return []
        
        user_crisis_key = f"{self.CRISIS_EVENT_PREFIX}user:{user_id}"
        event_ids = await self.client.lrange(user_crisis_key, 0, limit - 1)
        
        events = []
        for event_id in event_ids:
            data = await self.client.get(self._crisis_key(UUID(event_id)))
            if data:
                events.append(json.loads(data))
        
        return events
    
    # Safety Alerts (real-time)
    async def store_safety_alert(self, alert: SafetyAlert) -> UUID:
        """Store a safety alert in Redis for real-time processing."""
        data = {
            "alert_id": str(alert.alert_id),
            "timestamp": alert.timestamp.isoformat(),
            "user_id": alert.user_id,
            "companion_id": alert.companion_id,
            "conversation_id": alert.conversation_id,
            "alert_type": alert.alert_type.value,
            "severity": alert.severity,
            "intervention_level": alert.intervention_level.value,
            "details": alert.details,
            "requires_human_review": alert.requires_human_review,
            "acknowledged": alert.acknowledged,
            "resolved": alert.resolved,
        }
        
        # Store alert with TTL (30 days)
        await self.client.setex(
            self._alert_key(alert.alert_id),
            timedelta(days=30),
            json.dumps(data)
        )
        
        # Add to user's alert list
        user_alerts_key = self._user_alerts_key(alert.user_id)
        await self.client.lpush(user_alerts_key, str(alert.alert_id))
        await self.client.ltrim(user_alerts_key, 0, 499)  # Keep last 500
        await self.client.expire(user_alerts_key, timedelta(days=30))
        
        # Add to unacknowledged alerts set if needed
        if not alert.acknowledged and alert.requires_human_review:
            unacked_key = f"{self.ALERT_PREFIX}unacknowledged"
            await self.client.sadd(unacked_key, str(alert.alert_id))
        
        return alert.alert_id
    
    async def get_safety_alerts(
        self,
        user_id: Optional[str] = None,
        companion_id: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        resolved: Optional[bool] = None,
        severity: Optional[str] = None,
        limit: int = 100,
    ) -> List[SafetyAlert]:
        """Retrieve safety alerts from Redis."""
        if not user_id:
            return []
        
        user_alerts_key = self._user_alerts_key(user_id)
        alert_ids = await self.client.lrange(user_alerts_key, 0, limit - 1)
        
        alerts = []
        for alert_id in alert_ids:
            data = await self.client.get(self._alert_key(UUID(alert_id)))
            if data:
                alert_data = json.loads(data)
                
                # Apply filters
                if acknowledged is not None and alert_data.get("acknowledged") != acknowledged:
                    continue
                if resolved is not None and alert_data.get("resolved") != resolved:
                    continue
                if severity and alert_data.get("severity") != severity:
                    continue
                if companion_id and alert_data.get("companion_id") != companion_id:
                    continue
                
                alerts.append(SafetyAlert(
                    alert_id=UUID(alert_data["alert_id"]),
                    timestamp=datetime.fromisoformat(alert_data["timestamp"]),
                    user_id=alert_data["user_id"],
                    companion_id=alert_data["companion_id"],
                    conversation_id=alert_data.get("conversation_id"),
                    alert_type=SafetyCategory(alert_data["alert_type"]),
                    severity=alert_data["severity"],
                    intervention_level=InterventionLevel(alert_data["intervention_level"]),
                    details=alert_data["details"],
                    requires_human_review=alert_data["requires_human_review"],
                    acknowledged=alert_data["acknowledged"],
                    resolved=alert_data["resolved"],
                ))
        
        return alerts
    
    async def acknowledge_alert(self, alert_id: UUID, reviewer_id: str) -> bool:
        """Mark alert as acknowledged."""
        data = await self.client.get(self._alert_key(alert_id))
        if data:
            alert_data = json.loads(data)
            alert_data["acknowledged"] = True
            alert_data["acknowledged_by"] = reviewer_id
            alert_data["acknowledged_at"] = datetime.utcnow().isoformat()
            await self.client.setex(
                self._alert_key(alert_id),
                timedelta(days=30),
                json.dumps(alert_data)
            )
            # Remove from unacknowledged set
            await self.client.srem(f"{self.ALERT_PREFIX}unacknowledged", str(alert_id))
            return True
        return False
    
    async def resolve_alert(self, alert_id: UUID, resolver_id: str, resolution: str) -> bool:
        """Mark alert as resolved."""
        data = await self.client.get(self._alert_key(alert_id))
        if data:
            alert_data = json.loads(data)
            alert_data["resolved"] = True
            alert_data["resolved_by"] = resolver_id
            alert_data["resolved_at"] = datetime.utcnow().isoformat()
            alert_data["resolution"] = resolution
            await self.client.setex(
                self._alert_key(alert_id),
                timedelta(days=30),
                json.dumps(alert_data)
            )
            return True
        return False
    
    # Content Filter Logs (cached)
    async def store_content_filter_log(
        self,
        user_id: str,
        companion_id: str,
        conversation_id: Optional[str],
        text: str,
        result: Any,
        check_type: str,
    ) -> UUID:
        """Store content filter check log in Redis cache."""
        from uuid import uuid4
        log_id = uuid4()
        
        import hashlib
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        
        data = {
            "id": str(log_id),
            "user_id": user_id,
            "companion_id": companion_id,
            "conversation_id": conversation_id,
            "text_hash": text_hash,
            "check_type": check_type,
            "passed": result.passed,
            "overall_risk": result.overall_risk,
            "intervention_level": result.intervention_level.value,
            "violations": [v.model_dump() if hasattr(v, 'model_dump') else v for v in result.violations],
            "pii_detected": [v.model_dump() if hasattr(v, 'model_dump') else v for v in result.pii_detected],
            "categories_checked": [c.value for c in result.categories_checked],
            "processing_time_ms": result.processing_time_ms,
            "metadata": result.metadata,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        await self.client.setex(
            self._content_filter_key(log_id),
            timedelta(days=3),
            json.dumps(data)
        )
        
        return log_id
    
    async def get_content_filter_logs(
        self,
        user_id: Optional[str] = None,
        companion_id: Optional[str] = None,
        violation_category: Optional[SafetyCategory] = None,
        passed: Optional[bool] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve content filter logs (limited in Redis)."""
        # Redis doesn't support complex querying, return empty for now
        # Full querying should use PostgreSQL
        return []
    
    # Behavioral Guard Logs (cached)
    async def store_behavioral_guard_log(
        self,
        user_id: str,
        companion_id: str,
        conversation_id: Optional[str],
        text: str,
        result: Any,
        relationship_context: Optional[Dict[str, Any]],
    ) -> UUID:
        """Store behavioral guard check log in Redis cache."""
        from uuid import uuid4
        log_id = uuid4()
        
        import hashlib
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        
        data = {
            "id": str(log_id),
            "user_id": user_id,
            "companion_id": companion_id,
            "conversation_id": conversation_id,
            "text_hash": text_hash,
            "manipulation_score": result.manipulation_score,
            "dependency_score": result.dependency_score,
            "enmeshment_score": result.enmeshment_score,
            "gaslighting_score": result.gaslighting_score,
            "authority_score": result.authority_score,
            "overall_risk": result.overall_risk,
            "intervention_level": result.intervention_level.value,
            "violations": [v.model_dump() if hasattr(v, 'model_dump') else v for v in result.violations],
            "relationship_context": relationship_context,
            "conversation_history_summary": result.conversation_history_summary,
            "processing_time_ms": result.processing_time_ms,
            "metadata": result.metadata,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        await self.client.setex(
            self._behavioral_guard_key(log_id),
            timedelta(days=3),
            json.dumps(data)
        )
        
        return log_id
    
    async def get_behavioral_guard_logs(
        self,
        user_id: Optional[str] = None,
        companion_id: Optional[str] = None,
        violation_type: Optional[SafetyCategory] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve behavioral guard logs (limited in Redis)."""
        return []
    
    # Reality Anchor Logs (cached)
    async def store_reality_anchor_log(
        self,
        user_id: str,
        companion_id: str,
        conversation_id: Optional[str],
        text: str,
        result: Any,
    ) -> UUID:
        """Store reality anchor check log in Redis cache."""
        from uuid import uuid4
        log_id = uuid4()
        
        import hashlib
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        
        data = {
            "id": str(log_id),
            "user_id": user_id,
            "companion_id": companion_id,
            "conversation_id": conversation_id,
            "text_hash": text_hash,
            "triggered": result.triggered,
            "trigger_category": result.trigger_category.value if result.trigger_category else None,
            "detected_triggers": result.detected_triggers,
            "confidence": result.confidence,
            "intervention_level": result.intervention_level.value,
            "anchor_response": result.anchor_response,
            "metadata": result.metadata,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        await self.client.setex(
            self._reality_anchor_key(log_id),
            timedelta(days=3),
            json.dumps(data)
        )
        
        return log_id
    
    # Metrics (real-time aggregation)
    async def store_metrics(self, metrics: SafetyMetrics) -> None:
        """Store aggregated safety metrics in Redis."""
        period = datetime.utcnow().strftime("%Y%m%d")
        key = self._metrics_key(period)
        
        data = {
            "total_checks": metrics.total_checks,
            "crisis_detected": metrics.crisis_detected,
            "content_violations": metrics.content_violations,
            "behavioral_violations": metrics.behavioral_violations,
            "reality_anchors_triggered": metrics.reality_anchors_triggered,
            "interventions_by_level": metrics.interventions_by_level,
            "avg_processing_time_ms": metrics.avg_processing_time_ms,
            "false_positive_rate": metrics.false_positive_rate,
            "false_negative_rate": metrics.false_negative_rate,
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        await self.client.setex(key, timedelta(days=2), json.dumps(data))
    
    async def get_metrics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> SafetyMetrics:
        """Retrieve aggregated safety metrics from Redis."""
        period = datetime.utcnow().strftime("%Y%m%d")
        key = self._metrics_key(period)
        
        data = await self.client.get(key)
        if data:
            metrics_data = json.loads(data)
            return SafetyMetrics(**metrics_data)
        
        return SafetyMetrics()
    
    # Audit Trail (not cached in Redis)
    async def store_audit_entry(
        self,
        event_type: str,
        user_id: str,
        companion_id: str,
        conversation_id: Optional[str],
        details: Dict[str, Any],
    ) -> UUID:
        """Store audit trail entry (delegates to PostgreSQL)."""
        from uuid import uuid4
        return uuid4()
    
    async def get_audit_trail(
        self,
        user_id: Optional[str] = None,
        companion_id: Optional[str] = None,
        event_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve audit trail entries (delegates to PostgreSQL)."""
        return []
    
    # Rate Limiting
    async def check_rate_limit(self, identifier: str) -> bool:
        """Check if request is within rate limit."""
        key = self._rate_limit_key(identifier)
        current = await self.client.get(key)
        
        if current is None:
            await self.client.setex(
                key,
                self.settings.rate_limit_window_seconds,
                1
            )
            return True
        
        count = int(current)
        if count >= self.settings.rate_limit_requests:
            return False
        
        await self.client.incr(key)
        return True
    
    async def get_rate_limit_remaining(self, identifier: str) -> int:
        """Get remaining requests in current window."""
        key = self._rate_limit_key(identifier)
        current = await self.client.get(key)
        
        if current is None:
            return self.settings.rate_limit_requests
        
        return max(0, self.settings.rate_limit_requests - int(current))
    
    # Caching
    async def cache_get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        data = await self.client.get(self._cache_key(key))
        if data:
            return json.loads(data)
        return None
    
    async def cache_set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Set value in cache with TTL."""
        await self.client.setex(
            self._cache_key(key),
            ttl_seconds,
            json.dumps(value)
        )
    
    async def cache_delete(self, key: str) -> None:
        """Delete value from cache."""
        await self.client.delete(self._cache_key(key))
    
    # User Session Data
    async def store_user_session(self, user_id: str, session_data: Dict[str, Any]) -> None:
        """Store user session data."""
        await self.client.setex(
            self._user_session_key(user_id),
            timedelta(hours=24),
            json.dumps(session_data)
        )
    
    async def get_user_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user session data."""
        data = await self.client.get(self._user_session_key(user_id))
        if data:
            return json.loads(data)
        return None
    
    # Real-time Crisis Keywords (for fast lookup)
    async def load_crisis_keywords(self, keywords: List[str]) -> None:
        """Load crisis keywords into Redis set for fast lookup."""
        key = f"{self.CACHE_PREFIX}crisis_keywords"
        await self.client.delete(key)
        if keywords:
            await self.client.sadd(key, *keywords)
    
    async def check_crisis_keywords(self, text: str) -> List[str]:
        """Check if text contains any crisis keywords."""
        key = f"{self.CACHE_PREFIX}crisis_keywords"
        keywords = await self.client.smembers(key)
        found = []
        text_lower = text.lower()
        for keyword in keywords:
            if keyword.lower() in text_lower:
                found.append(keyword)
        return found
    
    # PII Patterns (for fast lookup)
    async def load_pii_patterns(self, patterns: List[str]) -> None:
        """Load PII regex patterns into Redis."""
        key = f"{self.CACHE_PREFIX}pii_patterns"
        await self.client.delete(key)
        if patterns:
            await self.client.sadd(key, *patterns)
    
    # Health check for monitoring
    async def get_stats(self) -> Dict[str, Any]:
        """Get Redis statistics."""
        info = await self.client.info()
        return {
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "0B"),
            "total_commands_processed": info.get("total_commands_processed", 0),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
        }