"""Evaluation Engine API routes."""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from evaluation_engine.config import settings
from evaluation_engine.services import (
    get_evaluation_service,
    close_evaluation_service,
    get_rhi_service,
    get_drift_service,
    get_ab_test_service,
    get_survey_service,
    get_report_service,
)
from evaluation_engine.models.requests import (
    ComputeRHIRequest,
    DriftCheckRequest,
    ABTestRequest,
    SurveySubmitRequest,
    ReportRequest,
)
from evaluation_engine.models.responses import (
    RHIResponse,
    DriftResponse,
    ABTestResponse,
    SurveyResponse,
    ReportResponse,
    HealthResponse,
    ABTestVariantResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["evaluation-engine"])


# Health endpoints
@router.get("/health/live", response_model=HealthResponse)
async def liveness_check() -> HealthResponse:
    """Liveness probe."""
    return HealthResponse(
        status="healthy",
        processing_time_ms=0.0,
    )


@router.get("/health/ready", response_model=HealthResponse)
async def readiness_check() -> HealthResponse:
    """Readiness probe with full health check."""
    service = await get_evaluation_service()
    return await service.health_check()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Full health check."""
    service = await get_evaluation_service()
    return await service.health_check()


# RHI endpoints
@router.post("/rhi/compute", response_model=RHIResponse)
async def compute_rhi(request: ComputeRHIRequest) -> RHIResponse:
    """Compute Relationship Health Index."""
    service = await get_evaluation_service()
    return await service.compute_rhi(request)


@router.get("/rhi/history", response_model=List[Dict[str, Any]])
async def get_rhi_history(
    user_id: UUID = Query(...),
    companion_id: UUID = Query(...),
    days: int = Query(90, ge=1, le=365),
) -> List[Dict[str, Any]]:
    """Get RHI history for trend analysis."""
    service = await get_evaluation_service()
    return await service.get_rhi_history(user_id, companion_id, days)


# Drift endpoints
@router.post("/drift/check", response_model=DriftResponse)
async def check_drift(request: DriftCheckRequest) -> DriftResponse:
    """Check for dimension drift."""
    service = await get_evaluation_service()
    return await service.check_drift(request)


@router.post("/drift/record", response_model=Dict[str, bool])
async def record_dimension_score(
    user_id: UUID = Query(...),
    companion_id: UUID = Query(...),
    dimension: str = Query(...),
    score: float = Query(..., ge=1.0, le=10.0),
) -> Dict[str, bool]:
    """Record a dimension score for drift tracking."""
    service = await get_evaluation_service()
    await service.record_dimension_score(user_id, companion_id, dimension, score)
    return {"success": True}


@router.get("/drift/history", response_model=Dict[str, Any])
async def get_drift_history(
    user_id: UUID = Query(...),
    companion_id: UUID = Query(...),
    dimension: str = Query(...),
    days: int = Query(90, ge=1, le=365),
) -> Dict[str, Any]:
    """Get drift history for a dimension."""
    service = await get_evaluation_service()
    return await service.get_drift_history(user_id, companion_id, dimension, days)


# A/B Test endpoints
@router.post("/ab-tests", response_model=ABTestResponse)
async def create_ab_test(request: ABTestRequest) -> ABTestResponse:
    """Create a new A/B test."""
    service = await get_evaluation_service()
    return await service.create_ab_test(request)


@router.get("/ab-tests", response_model=List[ABTestResponse])
async def list_ab_tests(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
) -> List[ABTestResponse]:
    """List A/B tests."""
    service = await get_evaluation_service()
    return await service.list_ab_tests(status, limit)


@router.get("/ab-tests/{test_id}", response_model=ABTestResponse)
async def get_ab_test(test_id: str) -> ABTestResponse:
    """Get an A/B test by ID."""
    service = await get_evaluation_service()
    test = await service.get_ab_test(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="A/B test not found")
    return test


@router.post("/ab-tests/{test_id}/start", response_model=ABTestResponse)
async def start_ab_test(test_id: str) -> ABTestResponse:
    """Start an A/B test."""
    service = await get_evaluation_service()
    test = await service.start_ab_test(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="A/B test not found")
    return test


@router.post("/ab-tests/{test_id}/pause", response_model=ABTestResponse)
async def pause_ab_test(test_id: str) -> ABTestResponse:
    """Pause an A/B test."""
    service = await get_evaluation_service()
    test = await service.pause_ab_test(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="A/B test not found")
    return test


@router.post("/ab-tests/{test_id}/complete", response_model=ABTestResponse)
async def complete_ab_test(test_id: str) -> ABTestResponse:
    """Complete an A/B test."""
    service = await get_evaluation_service()
    test = await service.complete_ab_test(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="A/B test not found")
    return test


@router.post("/ab-tests/{test_id}/results", response_model=Dict[str, bool])
async def record_ab_test_result(
    test_id: str,
    variant: str = Query(..., description="Variant: A or B"),
    user_id: UUID = Query(...),
    metrics: Dict[str, float] = Query(..., description="Metrics as JSON"),
    metadata: Optional[Dict[str, Any]] = Query(None),
) -> Dict[str, bool]:
    """Record an A/B test result."""
    service = await get_evaluation_service()
    success = await service.record_ab_test_result(test_id, variant, metrics, user_id, metadata)
    if not success:
        raise HTTPException(status_code=404, detail="A/B test not found or not running")
    return {"success": True}


# Survey endpoints
@router.post("/surveys", response_model=SurveyResponse)
async def submit_survey(request: SurveySubmitRequest) -> SurveyResponse:
    """Submit a survey response."""
    service = await get_evaluation_service()
    return await service.submit_survey(request)


@router.get("/surveys/templates", response_model=List[Dict[str, Any]])
async def list_survey_templates() -> List[Dict[str, Any]]:
    """List all available survey templates."""
    service = await get_evaluation_service()
    return await service.list_survey_templates()


@router.get("/surveys/templates/{survey_type}", response_model=Dict[str, Any])
async def get_survey_template(survey_type: str) -> Dict[str, Any]:
    """Get survey template by type."""
    service = await get_evaluation_service()
    template = await service.get_survey_template(survey_type)
    if not template:
        raise HTTPException(status_code=404, detail="Survey template not found")
    return template


@router.get("/surveys/user", response_model=List[Dict[str, Any]])
async def get_user_surveys(
    user_id: UUID = Query(...),
    companion_id: Optional[UUID] = Query(None),
    survey_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
) -> List[Dict[str, Any]]:
    """Get survey responses for a user."""
    service = await get_evaluation_service()
    return await service.get_user_surveys(user_id, companion_id, survey_type, limit)


@router.get("/surveys/nps", response_model=List[Dict[str, Any]])
async def get_nps_history(
    user_id: UUID = Query(...),
    companion_id: Optional[UUID] = Query(None),
    days: int = Query(90, ge=1, le=365),
) -> List[Dict[str, Any]]:
    """Get NPS score history."""
    service = await get_evaluation_service()
    return await service.get_nps_history(user_id, companion_id, days)


@router.get("/surveys/satisfaction", response_model=List[Dict[str, Any]])
async def get_satisfaction_trends(
    user_id: UUID = Query(...),
    companion_id: Optional[UUID] = Query(None),
    days: int = Query(90, ge=1, le=365),
) -> List[Dict[str, Any]]:
    """Get satisfaction score trends."""
    service = await get_evaluation_service()
    return await service.get_satisfaction_trends(user_id, companion_id, days)


# Report endpoints
@router.post("/reports", response_model=ReportResponse)
async def generate_report(request: ReportRequest) -> ReportResponse:
    """Generate an evaluation report."""
    service = await get_evaluation_service()
    return await service.generate_report(request)


# Metrics endpoint
@router.get("/metrics")
async def metrics() -> str:
    """Prometheus metrics endpoint."""
    # In production, this would return actual Prometheus metrics
    return "# Evaluation Engine metrics placeholder\n"


# Service lifecycle
@router.on_event("startup")
async def startup_event() -> None:
    """Initialize services on startup."""
    logger.info("Starting Evaluation Engine API")
    await get_evaluation_service()


@router.on_event("shutdown")
async def shutdown_event() -> None:
    """Clean up services on shutdown."""
    logger.info("Shutting down Evaluation Engine API")
    await close_evaluation_service()