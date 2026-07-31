"""Evaluation Engine Response Models."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class HealthStatus(str, Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class RHIResponse(BaseModel):
    """Response for RHI computation."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    rhi_score: float = Field(..., ge=0.0, le=10.0, description="Overall RHI score (0-10)")
    dimensions: Dict[str, float] = Field(
        ...,
        description="Dimension scores: trust, intimacy, satisfaction, safety, growth",
    )
    breakdown: Optional[Dict[str, Any]] = Field(
        None,
        description="Detailed breakdown per dimension",
    )
    period_days: int
    computed_at: datetime
    trend: Optional[str] = Field(None, description="Trend: improving, stable, declining")
    correlation_with_survey: Optional[float] = Field(
        None,
        ge=-1.0,
        le=1.0,
        description="Correlation with latest survey",
    )
    processing_time_ms: float
    request_id: Optional[str] = None


class DriftAlert(BaseModel):
    """Individual drift alert."""
    
    dimension: str
    current_score: float
    baseline_score: float
    drift_magnitude: float
    direction: str = Field(..., description="increasing or decreasing")
    severity: str = Field(..., description="low, medium, high, critical")
    detected_at: datetime


class DriftResponse(BaseModel):
    """Response for drift check."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    has_drift: bool
    alerts: List[DriftAlert] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)
    window_days: int
    threshold: float
    checked_at: datetime
    processing_time_ms: float
    request_id: Optional[str] = None


class ABTestVariantResult(BaseModel):
    """A/B test variant result."""
    
    variant: str = Field(..., description="Variant identifier (A or B)")
    sample_size: int
    metrics: Dict[str, float]
    confidence_intervals: Dict[str, List[float]] = Field(default_factory=dict)


class ABTestResponse(BaseModel):
    """Response for A/B test operations."""
    
    model_config = ConfigDict(extra="forbid")
    
    test_id: str
    name: str
    status: str
    variant_a: ABTestVariantResult
    variant_b: ABTestVariantResult
    significance: Optional[Dict[str, Any]] = Field(
        None,
        description="Statistical significance results",
    )
    recommendation: Optional[str] = Field(
        None,
        description="Recommended variant or 'inconclusive'",
    )
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time_ms: float
    request_id: Optional[str] = None


class SurveyResponse(BaseModel):
    """Response for survey submission."""
    
    model_config = ConfigDict(extra="forbid")
    
    survey_id: str
    user_id: UUID
    companion_id: UUID
    survey_type: str
    received_at: datetime
    processed: bool
    nps_score: Optional[int] = Field(None, ge=-100, le=100)
    satisfaction_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    processing_time_ms: float
    request_id: Optional[str] = None


class ReportSection(BaseModel):
    """Report section."""
    
    title: str
    content: Dict[str, Any]
    visualizations: List[Dict[str, Any]] = Field(default_factory=list)


class ReportResponse(BaseModel):
    """Response for evaluation report."""
    
    model_config = ConfigDict(extra="forbid")
    
    report_id: str
    report_type: str
    user_id: Optional[UUID] = None
    companion_id: Optional[UUID] = None
    period_days: int
    generated_at: datetime
    sections: List[ReportSection]
    recommendations: List[str] = Field(default_factory=list)
    format: str
    processing_time_ms: float
    request_id: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    
    model_config = ConfigDict(extra="forbid")
    
    service: str = "evaluation-engine"
    version: str = "0.1.0"
    status: HealthStatus = HealthStatus.HEALTHY
    checks: Dict[str, bool] = Field(default_factory=dict)
    models_loaded: Dict[str, bool] = Field(default_factory=dict)
    processing_time_ms: float = 0.0