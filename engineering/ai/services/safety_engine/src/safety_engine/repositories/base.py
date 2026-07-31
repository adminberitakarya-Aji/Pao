"""
Base Repository Interface.

Defines the abstract interface for all safety engine repositories.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from safety_engine.models.safety import (
    SafetyAlert,
    SafetyCategory,
    SafetyCheckResponse,
    SafetyMetrics,
    SafetyViolation,
)


class BaseRepository(ABC):
    """Abstract base class for safety data repositories."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize repository connections."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close repository connections."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check repository health."""
        pass
    
    # Crisis Events
    @abstractmethod
    async def store_crisis_event(
        self,
        user_id: str,
        companion_id: str,
        conversation_id: Optional[str],
        crisis_result: Any,  # CrisisDetectionResult
        check_response: SafetyCheckResponse,
    ) -> UUID:
        """Store a crisis detection event."""
        pass
    
    @abstractmethod
    async def get_crisis_events(
        self,
        user_id: Optional[str] = None,
        companion_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve crisis events with filtering."""
        pass
    
    # Safety Alerts
    @abstractmethod
    async def store_safety_alert(self, alert: SafetyAlert) -> UUID:
        """Store a safety alert."""
        pass
    
    @abstractmethod
    async def get_safety_alerts(
        self,
        user_id: Optional[str] = None,
        companion_id: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        resolved: Optional[bool] = None,
        severity: Optional[str] = None,
        limit: int = 100,
    ) -> List[SafetyAlert]:
        """Retrieve safety alerts with filtering."""
        pass
    
    @abstractmethod
    async def acknowledge_alert(self, alert_id: UUID, reviewer_id: str) -> bool:
        """Mark alert as acknowledged."""
        pass
    
    @abstractmethod
    async def resolve_alert(self, alert_id: UUID, resolver_id: str, resolution: str) -> bool:
        """Mark alert as resolved."""
        pass
    
    # Content Filter Logs
    @abstractmethod
    async def store_content_filter_log(
        self,
        user_id: str,
        companion_id: str,
        conversation_id: Optional[str],
        text: str,
        result: Any,  # ContentFilterResult
        check_type: str,
    ) -> UUID:
        """Store content filter check log."""
        pass
    
    @abstractmethod
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
        """Retrieve content filter logs."""
        pass
    
    # Behavioral Guard Logs
    @abstractmethod
    async def store_behavioral_guard_log(
        self,
        user_id: str,
        companion_id: str,
        conversation_id: Optional[str],
        text: str,
        result: Any,  # BehavioralGuardResult
        relationship_context: Optional[Dict[str, Any]],
    ) -> UUID:
        """Store behavioral guard check log."""
        pass
    
    @abstractmethod
    async def get_behavioral_guard_logs(
        self,
        user_id: Optional[str] = None,
        companion_id: Optional[str] = None,
        violation_type: Optional[SafetyCategory] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve behavioral guard logs."""
        pass
    
    # Reality Anchor Logs
    @abstractmethod
    async def store_reality_anchor_log(
        self,
        user_id: str,
        companion_id: str,
        conversation_id: Optional[str],
        text: str,
        result: Any,  # RealityAnchorResult
    ) -> UUID:
        """Store reality anchor check log."""
        pass
    
    # Metrics
    @abstractmethod
    async def store_metrics(self, metrics: SafetyMetrics) -> None:
        """Store aggregated safety metrics."""
        pass
    
    @abstractmethod
    async def get_metrics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> SafetyMetrics:
        """Retrieve aggregated safety metrics."""
        pass
    
    # Audit Trail
    @abstractmethod
    async def store_audit_entry(
        self,
        event_type: str,
        user_id: str,
        companion_id: str,
        conversation_id: Optional[str],
        details: Dict[str, Any],
    ) -> UUID:
        """Store audit trail entry."""
        pass
    
    @abstractmethod
    async def get_audit_trail(
        self,
        user_id: Optional[str] = None,
        companion_id: Optional[str] = None,
        event_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve audit trail entries."""
        pass