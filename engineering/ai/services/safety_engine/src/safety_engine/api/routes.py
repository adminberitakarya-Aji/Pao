"""
Safety Engine API Routes.

FastAPI endpoints for safety checking:
- POST /safety/check - Full safety check
- POST /safety/check/streaming - Streaming safety check
- GET /safety/health - Health check
- GET /safety/metrics - Safety metrics
- GET /safety/alerts - Safety alerts
"""

import time
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from safety_engine.config import get_settings
from safety_engine.models.safety import (
    SafetyCheckRequest,
    SafetyCheckResponse,
    SafetyAlert,
    SafetyMetrics,
    SafetyCategory,
    InterventionLevel,
    CheckType,
)
from safety_engine.services.safety_service import SafetyService
from safety_engine.repositories.postgres import PostgresRepository
from safety_engine.repositories.redis import RedisRepository


router = APIRouter(prefix="/safety", tags=["safety"])

# Global service instances (initialized on startup)
_safety_service: Optional[SafetyService] = None
_postgres_repo: Optional[PostgresRepository] = None
_redis_repo: Optional[RedisRepository] = None


async def get_safety_service() -> SafetyService:
    """Dependency to get safety service instance."""
    global _safety_service
    if _safety_service is None:
        raise HTTPException(status_code=503, detail="Safety service not initialized")
    return _safety_service


async def get_postgres_repo() -> PostgresRepository:
    """Dependency to get PostgreSQL repository."""
    global _postgres_repo
    if _postgres_repo is None:
        raise HTTPException(status_code=503, detail="PostgreSQL repository not initialized")
    return _postgres_repo


async def get_redis_repo() -> RedisRepository:
    """Dependency to get Redis repository."""
    global _redis_repo
    if _redis_repo is None:
        raise HTTPException(status_code=503, detail="Redis repository not initialized")
    return _redis_repo


# Request/Response models for API
class SafetyCheckRequestModel(BaseModel):
    """API model for safety check request."""
    text: str = Field(..., min_length=1, max_length=100000, description="Text to check")
    check_type: CheckType = Field(default=CheckType.INPUT, description="Type of check")
    companion_id: Optional[str] = Field(default=None, description="Companion ID")
    user_id: Optional[str] = Field(default=None, description="User ID")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID")
    relationship_context: Optional[dict] = Field(default=None, description="Relationship context")
    enable_crisis_detection: bool = Field(default=True, description="Enable crisis detection")
    enable_content_filter: bool = Field(default=True, description="Enable content filtering")
    enable_behavioral_guards: bool = Field(default=True, description="Enable behavioral guards")
    enable_reality_anchor: bool = Field(default=True, description="Enable reality anchoring")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class SafetyCheckResponseModel(BaseModel):
    """API model for safety check response."""
    request_id: str
    timestamp: datetime
    passed: bool
    intervention_level: int
    crisis: Optional[dict] = None
    content_filter: Optional[dict] = None
    behavioral_guards: Optional[dict] = None
    reality_anchor: Optional[dict] = None
    safe_response: Optional[str] = None
    refusal_message: Optional[str] = None
    processing_time_ms: float
    metadata: dict = Field(default_factory=dict)


class StreamingCheckRequest(BaseModel):
    """API model for streaming safety check."""
    text_chunk: str = Field(..., min_length=1, max_length=10000, description="Text chunk to check")


class HealthResponse(BaseModel):
    """API model for health check response."""
    status: str
    timestamp: datetime
    components: dict
    version: str = "1.0.0"


class MetricsResponse(BaseModel):
    """API model for metrics response."""
    total_checks: int
    crisis_detected: int
    content_violations: int
    behavioral_violations: int
    reality_anchors_triggered: int
    interventions_by_level: dict
    avg_processing_time_ms: float
    false_positive_rate: float
    false_negative_rate: float
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class AlertsResponse(BaseModel):
    """API model for alerts response."""
    alerts: List[dict]
    total: int
    page: int
    page_size: int


@router.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global _safety_service, _postgres_repo, _redis_repo
    
    settings = get_settings()
    
    # Initialize repositories
    _postgres_repo = PostgresRepository()
    await _postgres_repo.initialize()
    
    _redis_repo = RedisRepository()
    await _redis_repo.initialize()
    
    # Initialize safety service
    _safety_service = SafetyService(_postgres_repo, _redis_repo)
    await _safety_service.initialize()


@router.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global _safety_service, _postgres_repo, _redis_repo
    
    if _postgres_repo:
        await _postgres_repo.close()
    if _redis_repo:
        await _redis_repo.close()


@router.post("/check", response_model=SafetyCheckResponseModel)
async def check_safety(
    request: SafetyCheckRequestModel,
    safety_service: SafetyService = Depends(get_safety_service),
):
    """
    Perform complete safety check on text.
    
    Runs all enabled safety checks:
    - Crisis detection (self-harm, suicide ideation)
    - Content filtering (hate, harassment, sexual, violence, illegal, medical, financial, PII)
    - Behavioral guards (manipulation, dependency, enmeshment, gaslighting, authority)
    - Reality anchoring (delusions, hallucinations, paranoia, conspiracy)
    """
    start_time = time.perf_counter()
    
    # Convert to internal model
    safety_request = SafetyCheckRequest(
        text=request.text,
        check_type=request.check_type,
        companion_id=request.companion_id,
        user_id=request.user_id,
        conversation_id=request.conversation_id,
        relationship_context=request.relationship_context,
        enable_crisis_detection=request.enable_crisis_detection,
        enable_content_filter=request.enable_content_filter,
        enable_behavioral_guards=request.enable_behavioral_guards,
        enable_reality_anchor=request.enable_reality_anchor,
        metadata=request.metadata,
    )
    
    # Run safety check
    response = await safety_service.check_safety(safety_request)
    
    # Update processing time
    response.processing_time_ms = (time.perf_counter() - start_time) * 1000
    
    # Convert to API response model
    return SafetyCheckResponseModel(
        request_id=str(response.request_id),
        timestamp=response.timestamp,
        passed=response.passed,
        intervention_level=response.intervention_level.value,
        crisis=response.crisis.model_dump() if response.crisis else None,
        content_filter=response.content_filter.model_dump() if response.content_filter else None,
        behavioral_guards=response.behavioral_guards.model_dump() if response.behavioral_guards else None,
        reality_anchor=response.reality_anchor.model_dump() if response.reality_anchor else None,
        safe_response=response.safe_response,
        refusal_message=response.refusal_message,
        processing_time_ms=response.processing_time_ms,
        metadata=response.metadata,
    )


@router.post("/check/streaming", response_model=SafetyCheckResponseModel)
async def check_safety_streaming(
    request: StreamingCheckRequest,
    safety_service: SafetyService = Depends(get_safety_service),
):
    """
    Perform streaming safety check on text chunk.
    
    Lightweight check for real-time intervention during generation.
    Only runs pattern-based checks (no ML inference).
    """
    response = await safety_service.check_streaming(request.text_chunk)
    
    return SafetyCheckResponseModel(
        request_id=str(response.request_id),
        timestamp=response.timestamp,
        passed=response.passed,
        intervention_level=response.intervention_level.value,
        crisis=response.crisis.model_dump() if response.crisis else None,
        content_filter=response.content_filter.model_dump() if response.content_filter else None,
        behavioral_guards=response.behavioral_guards.model_dump() if response.behavioral_guards else None,
        reality_anchor=response.reality_anchor.model_dump() if response.reality_anchor else None,
        safe_response=response.safe_response,
        refusal_message=response.refusal_message,
        processing_time_ms=response.processing_time_ms,
        metadata=response.metadata,
    )


@router.get("/health", response_model=HealthResponse)
async def health_check(
    safety_service: SafetyService = Depends(get_safety_service),
):
    """Check health of safety engine and its dependencies."""
    health = await safety_service.health_check()
    
    all_healthy = all(health.values())
    
    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        timestamp=datetime.utcnow(),
        components=health,
    )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    postgres_repo: PostgresRepository = Depends(get_postgres_repo),
    redis_repo: RedisRepository = Depends(get_redis_repo),
):
    """Get aggregated safety metrics."""
    # Try Redis first (real-time), fallback to PostgreSQL
    metrics = await redis_repo.get_metrics(start_time, end_time)
    
    if metrics.total_checks == 0:
        metrics = await postgres_repo.get_metrics(start_time, end_time)
    
    return MetricsResponse(
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


@router.get("/alerts", response_model=AlertsResponse)
async def get_alerts(
    user_id: Optional[str] = None,
    companion_id: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    resolved: Optional[bool] = None,
    severity: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    postgres_repo: PostgresRepository = Depends(get_postgres_repo),
):
    """Get safety alerts with filtering."""
    alerts = await postgres_repo.get_safety_alerts(
        user_id=user_id,
        companion_id=companion_id,
        acknowledged=acknowledged,
        resolved=resolved,
        severity=severity,
        limit=limit + offset,
    )
    
    # Apply pagination
    paginated = alerts[offset:offset + limit]
    
    return AlertsResponse(
        alerts=[alert.model_dump() for alert in paginated],
        total=len(alerts),
        page=offset // limit + 1 if limit > 0 else 1,
        page_size=limit,
    )


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: UUID,
    reviewer_id: str,
    postgres_repo: PostgresRepository = Depends(get_postgres_repo),
    redis_repo: RedisRepository = Depends(get_redis_repo),
):
    """Acknowledge a safety alert."""
    success = await postgres_repo.acknowledge_alert(alert_id, reviewer_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Also update Redis
    await redis_repo.acknowledge_alert(alert_id, reviewer_id)
    
    return {"success": True, "alert_id": str(alert_id)}


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: UUID,
    resolver_id: str,
    resolution: str,
    postgres_repo: PostgresRepository = Depends(get_postgres_repo),
    redis_repo: RedisRepository = Depends(get_redis_repo),
):
    """Resolve a safety alert."""
    success = await postgres_repo.resolve_alert(alert_id, resolver_id, resolution)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Also update Redis
    await redis_repo.resolve_alert(alert_id, resolver_id, resolution)
    
    return {"success": True, "alert_id": str(alert_id)}


@router.get("/crisis-events")
async def get_crisis_events(
    user_id: Optional[str] = None,
    companion_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
    postgres_repo: PostgresRepository = Depends(get_postgres_repo),
):
    """Get crisis detection events."""
    events = await postgres_repo.get_crisis_events(
        user_id=user_id,
        companion_id=companion_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )
    return {"events": events, "total": len(events)}


@router.get("/content-filter-logs")
async def get_content_filter_logs(
    user_id: Optional[str] = None,
    companion_id: Optional[str] = None,
    violation_category: Optional[SafetyCategory] = None,
    passed: Optional[bool] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
    postgres_repo: PostgresRepository = Depends(get_postgres_repo),
):
    """Get content filter logs."""
    logs = await postgres_repo.get_content_filter_logs(
        user_id=user_id,
        companion_id=companion_id,
        violation_category=violation_category,
        passed=passed,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )
    return {"logs": logs, "total": len(logs)}


@router.get("/behavioral-guard-logs")
async def get_behavioral_guard_logs(
    user_id: Optional[str] = None,
    companion_id: Optional[str] = None,
    violation_type: Optional[SafetyCategory] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
    postgres_repo: PostgresRepository = Depends(get_postgres_repo),
):
    """Get behavioral guard logs."""
    logs = await postgres_repo.get_behavioral_guard_logs(
        user_id=user_id,
        companion_id=companion_id,
        violation_type=violation_type,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )
    return {"logs": logs, "total": len(logs)}


@router.get("/audit-trail")
async def get_audit_trail(
    user_id: Optional[str] = None,
    companion_id: Optional[str] = None,
    event_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
    postgres_repo: PostgresRepository = Depends(get_postgres_repo),
):
    """Get audit trail entries."""
    entries = await postgres_repo.get_audit_trail(
        user_id=user_id,
        companion_id=companion_id,
        event_type=event_type,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )
    return {"entries": entries, "total": len(entries)}


# Rate limit info endpoint
@router.get("/rate-limit/{identifier}")
async def get_rate_limit(
    identifier: str,
    redis_repo: RedisRepository = Depends(get_redis_repo),
):
    """Get rate limit status for an identifier."""
    remaining = await redis_repo.get_rate_limit_remaining(identifier)
    settings = get_settings()
    
    return {
        "identifier": identifier,
        "limit": settings.rate_limit_requests,
        "remaining": remaining,
        "window_seconds": settings.rate_limit_window_seconds,
    }