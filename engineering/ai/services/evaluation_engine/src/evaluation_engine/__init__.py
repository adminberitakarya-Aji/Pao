"""Evaluation Engine - Relationship Health Index, Drift Detection, A/B Testing, Surveys, and Reports."""

from evaluation_engine.config import settings
from evaluation_engine.models import (
    ComputeRHIRequest,
    DriftCheckRequest,
    ABTestRequest,
    SurveySubmitRequest,
    ReportRequest,
    RHIResponse,
    DriftResponse,
    ABTestResponse,
    SurveyResponse,
    ReportResponse,
    HealthResponse,
)
from evaluation_engine.services import (
    RHIService,
    DriftService,
    ABTestService,
    SurveyService,
    ReportService,
    EvaluationService,
)
from evaluation_engine.api import router
from evaluation_engine.main import app

__version__ = "0.1.0"

__all__ = [
    # Config
    "settings",
    # Models
    "ComputeRHIRequest",
    "DriftCheckRequest",
    "ABTestRequest",
    "SurveySubmitRequest",
    "ReportRequest",
    "RHIResponse",
    "DriftResponse",
    "ABTestResponse",
    "SurveyResponse",
    "ReportResponse",
    "HealthResponse",
    # Services
    "RHIService",
    "DriftService",
    "ABTestService",
    "SurveyService",
    "ReportService",
    "EvaluationService",
    # API
    "router",
    "app",
]