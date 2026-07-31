"""
PostgreSQL Repository Implementation.

Provides persistent storage for safety events, alerts, logs, and metrics
using PostgreSQL with asyncpg/SQLAlchemy.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import asyncpg
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    select,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from safety_engine.config import get_settings
from safety_engine.models.safety import (
    SafetyAlert,
    SafetyCategory,
    SafetyMetrics,
)
from safety_engine.repositories.base import BaseRepository


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass


class CrisisEvent(Base):
    """Crisis detection event storage."""
    __tablename__ = "crisis_events"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    companion_id: Mapped[str] = mapped_column(String(255), index=True)
    conversation_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    crisis_type: Mapped[str] = mapped_column(String(50))
    confidence: Mapped[float] = mapped_column(Float)
    risk_level: Mapped[str] = mapped_column(String(20))
    urgency_score: Mapped[float] = mapped_column(Float)
    detected_keywords: Mapped[List[str]] = mapped_column(JSONB, default=list)
    detected_patterns: Mapped[List[str]] = mapped_column(JSONB, default=list)
    sentiment_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    intervention_level: Mapped[int] = mapped_column(Integer)
    crisis_resources: Mapped[List[Dict[str, str]]] = mapped_column(JSONB, default=list)
    requires_human_review: Mapped[bool] = mapped_column(default=False)
    check_response: Mapped[Dict[str, Any]] = mapped_column(JSONB)
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index("ix_crisis_events_user_created", "user_id", "created_at"),
        Index("ix_crisis_events_companion_created", "companion_id", "created_at"),
    )


class SafetyAlertModel(Base):
    """Safety alert storage."""
    __tablename__ = "safety_alerts"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    companion_id: Mapped[str] = mapped_column(String(255), index=True)
    conversation_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    alert_type: Mapped[str] = mapped_column(String(50), index=True)
    severity: Mapped[str] = mapped_column(String(20), index=True)
    intervention_level: Mapped[int] = mapped_column(Integer)
    details: Mapped[Dict[str, Any]] = mapped_column(JSONB)
    requires_human_review: Mapped[bool] = mapped_column(default=False)
    acknowledged: Mapped[bool] = mapped_column(default=False)
    acknowledged_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    resolved: Mapped[bool] = mapped_column(default=False)
    resolved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index("ix_safety_alerts_user_created", "user_id", "created_at"),
        Index("ix_safety_alerts_status", "acknowledged", "resolved", "created_at"),
    )


class ContentFilterLog(Base):
    """Content filter check logs."""
    __tablename__ = "content_filter_logs"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    companion_id: Mapped[str] = mapped_column(String(255), index=True)
    conversation_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    text_hash: Mapped[str] = mapped_column(String(64), index=True)  # SHA256 hash of text
    check_type: Mapped[str] = mapped_column(String(20))
    passed: Mapped[bool] = mapped_column(index=True)
    overall_risk: Mapped[float] = mapped_column(Float)
    intervention_level: Mapped[int] = mapped_column(Integer)
    violations: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=list)
    pii_detected: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=list)
    categories_checked: Mapped[List[str]] = mapped_column(JSONB, default=list)
    processing_time_ms: Mapped[float] = mapped_column(Float)
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index("ix_content_filter_logs_user_created", "user_id", "created_at"),
        Index("ix_content_filter_logs_passed_created", "passed", "created_at"),
    )


class BehavioralGuardLog(Base):
    """Behavioral guard check logs."""
    __tablename__ = "behavioral_guard_logs"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    companion_id: Mapped[str] = mapped_column(String(255), index=True)
    conversation_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    text_hash: Mapped[str] = mapped_column(String(64), index=True)
    manipulation_score: Mapped[float] = mapped_column(Float)
    dependency_score: Mapped[float] = mapped_column(Float)
    enmeshment_score: Mapped[float] = mapped_column(Float)
    gaslighting_score: Mapped[float] = mapped_column(Float)
    authority_score: Mapped[float] = mapped_column(Float)
    overall_risk: Mapped[float] = mapped_column(Float)
    intervention_level: Mapped[int] = mapped_column(Integer)
    violations: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=list)
    relationship_context: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    conversation_history_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processing_time_ms: Mapped[float] = mapped_column(Float)
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index("ix_behavioral_guard_logs_user_created", "user_id", "created_at"),
        Index("ix_behavioral_guard_logs_risk_created", "overall_risk", "created_at"),
    )


class RealityAnchorLog(Base):
    """Reality anchor check logs."""
    __tablename__ = "reality_anchor_logs"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    companion_id: Mapped[str] = mapped_column(String(255), index=True)
    conversation_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    text_hash: Mapped[str] = mapped_column(String(64), index=True)
    triggered: Mapped[bool] = mapped_column(default=False, index=True)
    trigger_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    detected_triggers: Mapped[List[str]] = mapped_column(JSONB, default=list)
    confidence: Mapped[float] = mapped_column(Float)
    intervention_level: Mapped[int] = mapped_column(Integer)
    anchor_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index("ix_reality_anchor_logs_user_created", "user_id", "created_at"),
        Index("ix_reality_anchor_logs_triggered_created", "triggered", "created_at"),
    )


class SafetyMetricsModel(Base):
    """Aggregated safety metrics storage."""
    __tablename__ = "safety_metrics"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    period_start: Mapped[datetime] = mapped_column(DateTime, index=True)
    period_end: Mapped[datetime] = mapped_column(DateTime, index=True)
    total_checks: Mapped[int] = mapped_column(Integer, default=0)
    crisis_detected: Mapped[int] = mapped_column(Integer, default=0)
    content_violations: Mapped[int] = mapped_column(Integer, default=0)
    behavioral_violations: Mapped[int] = mapped_column(Integer, default=0)
    reality_anchors_triggered: Mapped[int] = mapped_column(Integer, default=0)
    interventions_by_level: Mapped[Dict[int, int]] = mapped_column(JSONB, default=dict)
    avg_processing_time_ms: Mapped[float] = mapped_column(Float, default=0.0)
    false_positive_rate: Mapped[float] = mapped_column(Float, default=0.0)
    false_negative_rate: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_safety_metrics_period", "period_start", "period_end"),
    )


class AuditEntry(Base):
    """Audit trail entry."""
    __tablename__ = "audit_trail"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    companion_id: Mapped[str] = mapped_column(String(255), index=True)
    conversation_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    details: Mapped[Dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index("ix_audit_trail_user_created", "user_id", "created_at"),
        Index("ix_audit_trail_type_created", "event_type", "created_at"),
    )


class PostgresRepository(BaseRepository):
    """PostgreSQL implementation of safety repository."""
    
    def __init__(self, database_url: Optional[str] = None):
        self.settings = get_settings()
        self.database_url = database_url or self.settings.database_url
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        self._pool: Optional[asyncpg.Pool] = None
    
    async def initialize(self) -> None:
        """Initialize database connections."""
        self.engine = create_async_engine(
            self.database_url,
            pool_size=self.settings.database_pool_size,
            max_overflow=self.settings.database_max_overflow,
            echo=self.settings.log_level == "DEBUG",
        )
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        # Also create asyncpg pool for raw queries
        self._pool = await asyncpg.create_pool(
            self.database_url.replace("postgresql+asyncpg://", "postgresql://"),
            min_size=5,
            max_size=self.settings.database_pool_size,
        )
        
        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def close(self) -> None:
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()
        if self._pool:
            await self._pool.close()
    
    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            async with self.session_factory() as session:
                await session.execute(select(1))
            return True
        except Exception:
            return False
    
    def _hash_text(self, text: str) -> str:
        """Generate SHA256 hash of text for deduplication."""
        import hashlib
        return hashlib.sha256(text.encode()).hexdigest()
    
    # Crisis Events
    async def store_crisis_event(
        self,
        user_id: str,
        companion_id: str,
        conversation_id: Optional[str],
        crisis_result: Any,
        check_response: Any,
    ) -> UUID:
        """Store a crisis detection event."""
        event_id = uuid4()
        
        async with self.session_factory() as session:
            event = CrisisEvent(
                id=event_id,
                user_id=user_id,
                companion_id=companion_id,
                conversation_id=conversation_id,
                crisis_type=crisis_result.crisis_type.value if crisis_result.crisis_type else "unknown",
                confidence=crisis_result.confidence,
                risk_level=crisis_result.risk_level,
                urgency_score=crisis_result.urgency_score,
                detected_keywords=crisis_result.detected_keywords,
                detected_patterns=crisis_result.detected_patterns,
                sentiment_score=crisis_result.sentiment_score,
                intervention_level=crisis_result.recommended_intervention.value,
                crisis_resources=crisis_result.crisis_resources,
                requires_human_review=crisis_result.requires_human_review,
                check_response=check_response.model_dump() if hasattr(check_response, 'model_dump') else check_response,
                metadata=crisis_result.metadata,
            )
            session.add(event)
            await session.commit()
        
        return event_id
    
    async def get_crisis_events(
        self,
        user_id: Optional[str] = None,
        companion_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve crisis events with filtering."""
        async with self.session_factory() as session:
            query = select(CrisisEvent).order_by(CrisisEvent.created_at.desc()).limit(limit)
            
            if user_id:
                query = query.where(CrisisEvent.user_id == user_id)
            if companion_id:
                query = query.where(CrisisEvent.companion_id == companion_id)
            if start_time:
                query = query.where(CrisisEvent.created_at >= start_time)
            if end_time:
                query = query.where(CrisisEvent.created_at <= end_time)
            
            result = await session.execute(query)
            events = result.scalars().all()
            
            return [
                {
                    "id": str(e.id),
                    "user_id": e.user_id,
                    "companion_id": e.companion_id,
                    "conversation_id": e.conversation_id,
                    "crisis_type": e.crisis_type,
                    "confidence": e.confidence,
                    "risk_level": e.risk_level,
                    "urgency_score": e.urgency_score,
                    "detected_keywords": e.detected_keywords,
                    "detected_patterns": e.detected_patterns,
                    "sentiment_score": e.sentiment_score,
                    "intervention_level": e.intervention_level,
                    "crisis_resources": e.crisis_resources,
                    "requires_human_review": e.requires_human_review,
                    "check_response": e.check_response,
                    "metadata": e.metadata,
                    "created_at": e.created_at.isoformat(),
                }
                for e in events
            ]
    
    # Safety Alerts
    async def store_safety_alert(self, alert: SafetyAlert) -> UUID:
        """Store a safety alert."""
        async with self.session_factory() as session:
            alert_model = SafetyAlertModel(
                id=alert.alert_id,
                user_id=alert.user_id,
                companion_id=alert.companion_id,
                conversation_id=alert.conversation_id,
                alert_type=alert.alert_type.value,
                severity=alert.severity,
                intervention_level=alert.intervention_level.value,
                details=alert.details,
                requires_human_review=alert.requires_human_review,
                acknowledged=alert.acknowledged,
                resolved=alert.resolved,
            )
            session.add(alert_model)
            await session.commit()
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
        """Retrieve safety alerts with filtering."""
        async with self.session_factory() as session:
            query = select(SafetyAlertModel).order_by(SafetyAlertModel.created_at.desc()).limit(limit)
            
            if user_id:
                query = query.where(SafetyAlertModel.user_id == user_id)
            if companion_id:
                query = query.where(SafetyAlertModel.companion_id == companion_id)
            if acknowledged is not None:
                query = query.where(SafetyAlertModel.acknowledged == acknowledged)
            if resolved is not None:
                query = query.where(SafetyAlertModel.resolved == resolved)
            if severity:
                query = query.where(SafetyAlertModel.severity == severity)
            
            result = await session.execute(query)
            alerts = result.scalars().all()
            
            return [
                SafetyAlert(
                    alert_id=a.id,
                    timestamp=a.created_at,
                    user_id=a.user_id,
                    companion_id=a.companion_id,
                    conversation_id=a.conversation_id,
                    alert_type=SafetyCategory(a.alert_type),
                    severity=a.severity,
                    intervention_level=InterventionLevel(a.intervention_level),
                    details=a.details,
                    requires_human_review=a.requires_human_review,
                    acknowledged=a.acknowledged,
                    resolved=a.resolved,
                )
                for a in alerts
            ]
    
    async def acknowledge_alert(self, alert_id: UUID, reviewer_id: str) -> bool:
        """Mark alert as acknowledged."""
        async with self.session_factory() as session:
            alert = await session.get(SafetyAlertModel, alert_id)
            if alert:
                alert.acknowledged = True
                alert.acknowledged_by = reviewer_id
                alert.acknowledged_at = datetime.utcnow()
                await session.commit()
                return True
        return False
    
    async def resolve_alert(self, alert_id: UUID, resolver_id: str, resolution: str) -> bool:
        """Mark alert as resolved."""
        async with self.session_factory() as session:
            alert = await session.get(SafetyAlertModel, alert_id)
            if alert:
                alert.resolved = True
                alert.resolved_by = resolver_id
                alert.resolved_at = datetime.utcnow()
                alert.resolution = resolution
                await session.commit()
                return True
        return False
    
    # Content Filter Logs
    async def store_content_filter_log(
        self,
        user_id: str,
        companion_id: str,
        conversation_id: Optional[str],
        text: str,
        result: Any,
        check_type: str,
    ) -> UUID:
        """Store content filter check log."""
        log_id = uuid4()
        text_hash = self._hash_text(text)
        
        async with self.session_factory() as session:
            log = ContentFilterLog(
                id=log_id,
                user_id=user_id,
                companion_id=companion_id,
                conversation_id=conversation_id,
                text_hash=text_hash,
                check_type=check_type,
                passed=result.passed,
                overall_risk=result.overall_risk,
                intervention_level=result.intervention_level.value,
                violations=[v.model_dump() if hasattr(v, 'model_dump') else v for v in result.violations],
                pii_detected=[v.model_dump() if hasattr(v, 'model_dump') else v for v in result.pii_detected],
                categories_checked=[c.value for c in result.categories_checked],
                processing_time_ms=result.processing_time_ms,
                metadata=result.metadata,
            )
            session.add(log)
            await session.commit()
        
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
        """Retrieve content filter logs."""
        async with self.session_factory() as session:
            query = select(ContentFilterLog).order_by(ContentFilterLog.created_at.desc()).limit(limit)
            
            if user_id:
                query = query.where(ContentFilterLog.user_id == user_id)
            if companion_id:
                query = query.where(ContentFilterLog.companion_id == companion_id)
            if passed is not None:
                query = query.where(ContentFilterLog.passed == passed)
            if start_time:
                query = query.where(ContentFilterLog.created_at >= start_time)
            if end_time:
                query = query.where(ContentFilterLog.created_at <= end_time)
            
            result = await session.execute(query)
            logs = result.scalars().all()
            
            filtered_logs = []
            for log in logs:
                if violation_category:
                    # Filter by violation category in JSONB
                    has_category = any(
                        v.get("category") == violation_category.value 
                        for v in log.violations
                    )
                    if not has_category:
                        continue
                filtered_logs.append({
                    "id": str(log.id),
                    "user_id": log.user_id,
                    "companion_id": log.companion_id,
                    "conversation_id": log.conversation_id,
                    "check_type": log.check_type,
                    "passed": log.passed,
                    "overall_risk": log.overall_risk,
                    "intervention_level": log.intervention_level,
                    "violations": log.violations,
                    "pii_detected": log.pii_detected,
                    "categories_checked": log.categories_checked,
                    "processing_time_ms": log.processing_time_ms,
                    "metadata": log.metadata,
                    "created_at": log.created_at.isoformat(),
                })
            
            return filtered_logs
    
    # Behavioral Guard Logs
    async def store_behavioral_guard_log(
        self,
        user_id: str,
        companion_id: str,
        conversation_id: Optional[str],
        text: str,
        result: Any,
        relationship_context: Optional[Dict[str, Any]],
    ) -> UUID:
        """Store behavioral guard check log."""
        log_id = uuid4()
        text_hash = self._hash_text(text)
        
        async with self.session_factory() as session:
            log = BehavioralGuardLog(
                id=log_id,
                user_id=user_id,
                companion_id=companion_id,
                conversation_id=conversation_id,
                text_hash=text_hash,
                manipulation_score=result.manipulation_score,
                dependency_score=result.dependency_score,
                enmeshment_score=result.enmeshment_score,
                gaslighting_score=result.gaslighting_score,
                authority_score=result.authority_score,
                overall_risk=result.overall_risk,
                intervention_level=result.intervention_level.value,
                violations=[v.model_dump() if hasattr(v, 'model_dump') else v for v in result.violations],
                relationship_context=relationship_context,
                conversation_history_summary=result.conversation_history_summary,
                processing_time_ms=result.processing_time_ms,
                metadata=result.metadata,
            )
            session.add(log)
            await session.commit()
        
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
        """Retrieve behavioral guard logs."""
        async with self.session_factory() as session:
            query = select(BehavioralGuardLog).order_by(BehavioralGuardLog.created_at.desc()).limit(limit)
            
            if user_id:
                query = query.where(BehavioralGuardLog.user_id == user_id)
            if companion_id:
                query = query.where(BehavioralGuardLog.companion_id == companion_id)
            if start_time:
                query = query.where(BehavioralGuardLog.created_at >= start_time)
            if end_time:
                query = query.where(BehavioralGuardLog.created_at <= end_time)
            
            result = await session.execute(query)
            logs = result.scalars().all()
            
            filtered_logs = []
            for log in logs:
                if violation_type:
                    has_type = any(
                        v.get("category") == violation_type.value 
                        for v in log.violations
                    )
                    if not has_type:
                        continue
                filtered_logs.append({
                    "id": str(log.id),
                    "user_id": log.user_id,
                    "companion_id": log.companion_id,
                    "conversation_id": log.conversation_id,
                    "manipulation_score": log.manipulation_score,
                    "dependency_score": log.dependency_score,
                    "enmeshment_score": log.enmeshment_score,
                    "gaslighting_score": log.gaslighting_score,
                    "authority_score": log.authority_score,
                    "overall_risk": log.overall_risk,
                    "intervention_level": log.intervention_level,
                    "violations": log.violations,
                    "relationship_context": log.relationship_context,
                    "conversation_history_summary": log.conversation_history_summary,
                    "processing_time_ms": log.processing_time_ms,
                    "metadata": log.metadata,
                    "created_at": log.created_at.isoformat(),
                })
            
            return filtered_logs
    
    # Reality Anchor Logs
    async def store_reality_anchor_log(
        self,
        user_id: str,
        companion_id: str,
        conversation_id: Optional[str],
        text: str,
        result: Any,
    ) -> UUID:
        """Store reality anchor check log."""
        log_id = uuid4()
        text_hash = self._hash_text(text)
        
        async with self.session_factory() as session:
            log = RealityAnchorLog(
                id=log_id,
                user_id=user_id,
                companion_id=companion_id,
                conversation_id=conversation_id,
                text_hash=text_hash,
                triggered=result.triggered,
                trigger_category=result.trigger_category.value if result.trigger_category else None,
                detected_triggers=result.detected_triggers,
                confidence=result.confidence,
                intervention_level=result.intervention_level.value,
                anchor_response=result.anchor_response,
                metadata=result.metadata,
            )
            session.add(log)
            await session.commit()
        
        return log_id
    
    # Metrics
    async def store_metrics(self, metrics: SafetyMetrics) -> None:
        """Store aggregated safety metrics."""
        async with self.session_factory() as session:
            metrics_model = SafetyMetricsModel(
                period_start=datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
                period_end=datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=999999),
                total_checks=metrics.total_checks,
                crisis_detected=metrics.crisis_detected,
                content_violations=metrics.content_violations,
                behavioral_violations=metrics.behavioral_violations,
                reality_anchors_triggered=metrics.reality_anchors_triggered,
                interventions_by_level=metrics.interventions_by_level,
                avg_processing_time_ms=metrics.avg_processing_time_ms,
                false_positive_rate=metrics.false_positive_rate,
                false_negative_rate=metrics.false_negative_rate,
            )
            session.add(metrics_model)
            await session.commit()
    
    async def get_metrics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> SafetyMetrics:
        """Retrieve aggregated safety metrics."""
        async with self.session_factory() as session:
            query = select(SafetyMetricsModel)
            
            if start_time:
                query = query.where(SafetyMetricsModel.period_start >= start_time)
            if end_time:
                query = query.where(SafetyMetricsModel.period_end <= end_time)
            
            query = query.order_by(SafetyMetricsModel.period_start.desc()).limit(1)
            result = await session.execute(query)
            metrics = result.scalar_one_or_none()
            
            if metrics:
                return SafetyMetrics(
                    total_checks=metrics.total_checks,
                    crisis_detected=metrics.crisis_detected,
                    content_violations=metrics.content_violations,
                    behavioral_violations=metrics.behavioral_violations,
                    reality_anchors_triggered=metrics.reality_anchors_triggered,
                    interventions_by_level=metrics.interventions_by_level,
                    avg_processing_time_ms=metrics.avg_processing_time_ms,
                    false_positive_rate=metrics.false_positive_rate,
                    false_negative_rate=metrics.false_negative_rate,
                )
            
            return SafetyMetrics()
    
    # Audit Trail
    async def store_audit_entry(
        self,
        event_type: str,
        user_id: str,
        companion_id: str,
        conversation_id: Optional[str],
        details: Dict[str, Any],
    ) -> UUID:
        """Store audit trail entry."""
        entry_id = uuid4()
        
        async with self.session_factory() as session:
            entry = AuditEntry(
                id=entry_id,
                event_type=event_type,
                user_id=user_id,
                companion_id=companion_id,
                conversation_id=conversation_id,
                details=details,
            )
            session.add(entry)
            await session.commit()
        
        return entry_id
    
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
        async with self.session_factory() as session:
            query = select(AuditEntry).order_by(AuditEntry.created_at.desc()).limit(limit)
            
            if user_id:
                query = query.where(AuditEntry.user_id == user_id)
            if companion_id:
                query = query.where(AuditEntry.companion_id == companion_id)
            if event_type:
                query = query.where(AuditEntry.event_type == event_type)
            if start_time:
                query = query.where(AuditEntry.created_at >= start_time)
            if end_time:
                query = query.where(AuditEntry.created_at <= end_time)
            
            result = await session.execute(query)
            entries = result.scalars().all()
            
            return [
                {
                    "id": str(e.id),
                    "event_type": e.event_type,
                    "user_id": e.user_id,
                    "companion_id": e.companion_id,
                    "conversation_id": e.conversation_id,
                    "details": e.details,
                    "created_at": e.created_at.isoformat(),
                }
                for e in entries
            ]