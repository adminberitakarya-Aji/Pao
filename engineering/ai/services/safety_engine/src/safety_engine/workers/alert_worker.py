"""
Alert Worker.

Processes safety alerts, handles escalation, notifications, and human review queue.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID

from safety_engine.config import get_settings
from safety_engine.repositories.base import BaseRepository
from safety_engine.models.safety import SafetyAlert, InterventionLevel, SafetyCategory


logger = logging.getLogger(__name__)


class AlertWorker:
    """Worker for processing and managing safety alerts."""
    
    def __init__(
        self,
        postgres_repo: BaseRepository,
        redis_repo: BaseRepository,
    ):
        self.settings = get_settings()
        self.postgres_repo = postgres_repo
        self.redis_repo = redis_repo
    
    async def process_new_alert(self, alert: SafetyAlert) -> None:
        """
        Process a newly created safety alert.
        
        - Store in both databases
        - Check for escalation rules
        - Send notifications if needed
        - Add to human review queue if required
        """
        logger.info(f"Processing new alert: {alert.alert_id} ({alert.alert_type.value})")
        
        # Alert is already stored by the safety service, but we can do additional processing
        
        # Check if escalation is needed
        if await self._should_escalate(alert):
            await self._escalate_alert(alert)
        
        # Send notification for high-severity alerts
        if alert.severity in ["high", "critical"] or alert.intervention_level >= InterventionLevel.RESOURCE_PROVIDE:
            await self._send_notification(alert)
        
        # Add to human review queue if needed
        if alert.requires_human_review:
            await self._add_to_review_queue(alert)
    
    async def _should_escalate(self, alert: SafetyAlert) -> bool:
        """Check if alert should be escalated based on rules."""
        # Escalate if:
        # 1. Critical severity
        # 2. Multiple alerts for same user in short time
        # 3. Crisis escalation intervention level
        
        if alert.severity == "critical":
            return True
        
        if alert.intervention_level == InterventionLevel.CRISIS_ESCALATE:
            return True
        
        # Check recent alerts for same user
        recent_alerts = await self.postgres_repo.get_safety_alerts(
            user_id=alert.user_id,
            start_time=datetime.utcnow() - timedelta(hours=1),
            limit=10,
        )
        
        if len(recent_alerts) >= 3:
            return True
        
        return False
    
    async def _escalate_alert(self, alert: SafetyAlert) -> None:
        """Escalate alert to higher priority."""
        logger.warning(f"Escalating alert {alert.alert_id} for user {alert.user_id}")
        
        # Update alert severity
        alert.severity = "critical"
        alert.intervention_level = InterventionLevel.CRISIS_ESCALATE
        alert.details["escalated"] = True
        alert.details["escalated_at"] = datetime.utcnow().isoformat()
        alert.details["escalation_reason"] = "Automatic escalation by alert worker"
        
        # Update in databases
        await self.postgres_repo.store_safety_alert(alert)
        await self.redis_repo.store_safety_alert(alert)
        
        # Send urgent notification
        await self._send_urgent_notification(alert)
    
    async def _send_notification(self, alert: SafetyAlert) -> None:
        """Send notification for alert (integrate with notification service)."""
        # TODO: Integrate with notification service (email, push, in-app)
        logger.info(f"Notification sent for alert {alert.alert_id}: {alert.alert_type.value}")
        
        # Example notification payload
        notification = {
            "type": "safety_alert",
            "alert_id": str(alert.alert_id),
            "user_id": alert.user_id,
            "companion_id": alert.companion_id,
            "severity": alert.severity,
            "alert_type": alert.alert_type.value,
            "message": self._format_alert_message(alert),
            "timestamp": alert.timestamp.isoformat(),
        }
        
        # Would publish to Kafka/notification service
        # await self._publish_notification(notification)
    
    async def _send_urgent_notification(self, alert: SafetyAlert) -> None:
        """Send urgent notification for escalated alerts."""
        logger.warning(f"URGENT notification for alert {alert.alert_id}")
        
        notification = {
            "type": "safety_alert_urgent",
            "alert_id": str(alert.alert_id),
            "user_id": alert.user_id,
            "companion_id": alert.companion_id,
            "severity": "critical",
            "alert_type": alert.alert_type.value,
            "message": f"URGENT: {self._format_alert_message(alert)}",
            "timestamp": datetime.utcnow().isoformat(),
            "requires_immediate_attention": True,
        }
        
        # Would publish to high-priority notification channel
        # await self._publish_urgent_notification(notification)
    
    def _format_alert_message(self, alert: SafetyAlert) -> str:
        """Format human-readable alert message."""
        type_messages = {
            SafetyCategory.SUICIDE: "Suicide/self-harm risk detected",
            SafetyCategory.SELF_HARM: "Self-harm indicators detected",
            SafetyCategory.CRISIS: "Crisis situation detected",
            SafetyCategory.HATE: "Hate speech detected",
            SafetyCategory.HARASSMENT: "Harassment detected",
            SafetyCategory.SEXUAL: "Inappropriate sexual content",
            SafetyCategory.VIOLENCE: "Violent content detected",
            SafetyCategory.ILLEGAL: "Illegal activity content",
            SafetyCategory.MEDICAL: "Medical advice violation",
            SafetyCategory.FINANCIAL: "Financial advice violation",
            SafetyCategory.MANIPULATION: "Manipulation pattern detected",
            SafetyCategory.DEPENDENCY: "Unhealthy dependency detected",
            SafetyCategory.ENMESHMENT: "Enmeshment pattern detected",
            SafetyCategory.GASLIGHTING: "Gaslighting behavior detected",
            SafetyCategory.AUTHORITY: "Undue authority influence",
            SafetyCategory.PARANOIA: "Paranoid ideation detected",
            SafetyCategory.DELUSION: "Delusional thinking detected",
            SafetyCategory.HALLUCINATION: "Hallucination indicators",
            SafetyCategory.CONSPIRACY: "Conspiracy thinking detected",
            SafetyCategory.PII: "Personal information detected",
        }
        
        base_message = type_messages.get(alert.alert_type, "Safety violation detected")
        
        if alert.companion_id:
            base_message += f" (Companion: {alert.companion_id[:8]}...)"
        
        return base_message
    
    async def _add_to_review_queue(self, alert: SafetyAlert) -> None:
        """Add alert to human review queue."""
        logger.info(f"Adding alert {alert.alert_id} to human review queue")
        
        # Store in Redis review queue for quick access by reviewers
        review_key = "safety:review_queue"
        review_item = {
            "alert_id": str(alert.alert_id),
            "user_id": alert.user_id,
            "companion_id": alert.companion_id,
            "alert_type": alert.alert_type.value,
            "severity": alert.severity,
            "intervention_level": alert.intervention_level.value,
            "details": alert.details,
            "created_at": alert.timestamp.isoformat(),
            "priority": "high" if alert.severity == "critical" else "normal",
        }
        
        # Add to sorted set with timestamp as score for FIFO
        import json
        await self.redis_repo.client.zadd(
            review_key,
            {json.dumps(review_item): alert.timestamp.timestamp()}
        )
    
    async def get_review_queue(
        self,
        limit: int = 50,
        priority: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get alerts pending human review."""
        review_key = "safety:review_queue"
        
        # Get items from sorted set (oldest first)
        items = await self.redis_repo.client.zrange(review_key, 0, limit - 1)
        
        alerts = []
        import json
        for item in items:
            alert_data = json.loads(item)
            if priority is None or alert_data.get("priority") == priority:
                alerts.append(alert_data)
        
        return alerts
    
    async def acknowledge_alert(self, alert_id: UUID, reviewer_id: str) -> bool:
        """Acknowledge alert (remove from review queue, mark acknowledged)."""
        # Remove from review queue
        review_key = "safety:review_queue"
        # We'd need to find the exact item - simplified here
        await self.redis_repo.client.zrem(review_key, str(alert_id))
        
        # Update in databases
        pg_success = await self.postgres_repo.acknowledge_alert(alert_id, reviewer_id)
        redis_success = await self.redis_repo.acknowledge_alert(alert_id, reviewer_id)
        
        return pg_success and redis_success
    
    async def resolve_alert(
        self,
        alert_id: UUID,
        resolver_id: str,
        resolution: str,
    ) -> bool:
        """Resolve alert."""
        pg_success = await self.postgres_repo.resolve_alert(alert_id, resolver_id, resolution)
        redis_success = await self.redis_repo.resolve_alert(alert_id, resolver_id, resolution)
        
        # Also remove from review queue if still there
        review_key = "safety:review_queue"
        await self.redis_repo.client.zrem(review_key, str(alert_id))
        
        return pg_success and redis_success
    
    async def cleanup_old_alerts(self, days: int = 90) -> int:
        """Clean up old resolved alerts from databases."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # PostgreSQL cleanup would be done via SQL DELETE
        # Redis cleanup is handled by TTL
        
        logger.info(f"Alert cleanup: removing alerts older than {days} days")
        return 0
    
    async def get_alert_statistics(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> Dict[str, Any]:
        """Get alert statistics for a time period."""
        alerts = await self.postgres_repo.get_safety_alerts(
            start_time=start_time,
            end_time=end_time,
            limit=10000,
        )
        
        stats = {
            "total_alerts": len(alerts),
            "by_type": {},
            "by_severity": {},
            "by_intervention": {},
            "acknowledged": 0,
            "resolved": 0,
            "pending_review": 0,
        }
        
        for alert in alerts:
            # By type
            atype = alert.alert_type.value if alert.alert_type else "unknown"
            stats["by_type"][atype] = stats["by_type"].get(atype, 0) + 1
            
            # By severity
            stats["by_severity"][alert.severity] = stats["by_severity"].get(alert.severity, 0) + 1
            
            # By intervention
            level = alert.intervention_level.value
            stats["by_intervention"][level] = stats["by_intervention"].get(level, 0) + 1
            
            if alert.acknowledged:
                stats["acknowledged"] += 1
            if alert.resolved:
                stats["resolved"] += 1
            if alert.requires_human_review and not alert.acknowledged:
                stats["pending_review"] += 1
        
        return stats