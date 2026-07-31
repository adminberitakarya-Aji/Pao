"""Evaluation Engine Request Models."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class ComputeRHIRequest(BaseModel):
    """Request to compute Relationship Health Index."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID = Field(..., description="User ID")
    companion_id: UUID = Field(..., description="Companion ID")
    dimensions: Optional[Dict[str, float]] = Field(
        None,
        description="Pre-computed dimension scores (trust, intimacy, satisfaction, safety, growth)",
    )
    include_breakdown: bool = Field(
        True,
        description="Include dimension-level breakdown in response",
    )
    period_days: int = Field(
        30,
        ge=1,
        le=365,
        description="Period for calculation in days",
    )
    request_id: Optional[str] = Field(None, description="Request ID for tracing")


class DriftCheckRequest(BaseModel):
    """Request to check for dimension drift."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID = Field(..., description="User ID")
    companion_id: UUID = Field(..., description="Companion ID")
    dimensions: Optional[List[str]] = Field(
        None,
        description="Specific dimensions to check (default: all)",
    )
    threshold: float = Field(
        0.15,
        ge=0.0,
        le=1.0,
        description="Drift threshold (0-1)",
    )
    window_days: int = Field(
        30,
        ge=1,
        le=365,
        description="Analysis window in days",
    )
    request_id: Optional[str] = Field(None, description="Request ID for tracing")


class ABTestRequest(BaseModel):
    """Request for A/B test operations."""
    
    model_config = ConfigDict(extra="forbid")
    
    test_id: Optional[str] = Field(None, description="Test ID (for get/update)")
    name: str = Field(..., description="Test name")
    description: Optional[str] = Field(None, description="Test description")
    variant_a: Dict[str, Any] = Field(..., description="Variant A configuration")
    variant_b: Dict[str, Any] = Field(..., description="Variant B configuration")
    allocation_ratio: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Traffic allocation to variant A",
    )
    min_sample_size: int = Field(
        100,
        ge=10,
        description="Minimum sample size per variant",
    )
    max_duration_days: int = Field(
        14,
        ge=1,
        le=90,
        description="Maximum test duration in days",
    )
    metrics: List[str] = Field(
        ...,
        description="Metrics to track (rhi, engagement, retention, satisfaction)",
    )
    status: str = Field(
        "draft",
        description="Test status: draft, running, paused, completed",
    )
    request_id: Optional[str] = Field(None, description="Request ID for tracing")


class SurveySubmitRequest(BaseModel):
    """Request to submit survey response."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID = Field(..., description="User ID")
    companion_id: UUID = Field(..., description="Companion ID")
    survey_type: str = Field(
        ...,
        description="Survey type: nps, satisfaction, relationship, safety",
    )
    responses: Dict[str, Any] = Field(
        ...,
        description="Survey responses (question_id -> answer)",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata (device, platform, version)",
    )
    request_id: Optional[str] = Field(None, description="Request ID for tracing")


class ReportRequest(BaseModel):
    """Request for evaluation report."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: Optional[UUID] = Field(None, description="User ID (optional for global report)")
    companion_id: Optional[UUID] = Field(None, description="Companion ID (optional)")
    report_type: str = Field(
        "comprehensive",
        description="Report type: comprehensive, rhi, drift, ab_test, survey",
    )
    period_days: int = Field(
        30,
        ge=1,
        le=365,
        description="Report period in days",
    )
    include_recommendations: bool = Field(
        True,
        description="Include actionable recommendations",
    )
    format: str = Field(
        "json",
        description="Output format: json, pdf, html",
    )
    request_id: Optional[str] = Field(None, description="Request ID for tracing")