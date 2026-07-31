"""Main Evaluation Service orchestrating all evaluation capabilities."""

import logging
import time
from typing import Optional, Dict, Any, List
from uuid import UUID

from evaluation_engine.config import settings
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
)

from evaluation_engine.services.rhi_service import RHIService
from evaluation_engine.services.drift_service import DriftService
from evaluation_engine.services.ab_test_service import ABTestService
from evaluation_engine.services.survey_service import SurveyService
from evaluation_engine.services.report_service import ReportService

logger = logging.getLogger(__name__)


class EvaluationService:
    """Main service orchestrating all evaluation capabilities."""
    
    def __init__(self):
        self._initialized = False
        self.rhi_service: Optional[RHIService] = None
        self.drift_service: Optional[DriftService] = None
        self.ab_test_service: Optional[ABTestService] = None
        self.survey_service: Optional[SurveyService] = None
        self.report_service: Optional[ReportService] = None
    
    async def initialize(self) -> None:
        """Initialize all sub-services."""
        logger.info("Initializing Evaluation Engine")
        
        # Initialize sub-services
        self.rhi_service = RHIService()
        await self.rhi_service.initialize()
        
        self.drift_service = DriftService()
        await self.drift_service.initialize()
        
        self.ab_test_service = ABTestService()
        await self.ab_test_service.initialize()
        
        self.survey_service = SurveyService()
        await self.survey_service.initialize()
        
        self.report_service = ReportService()
        await self.report_service.initialize()
        
        self._initialized = True
        logger.info("Evaluation Engine initialized")
    
    # RHI operations
    async def compute_rhi(self, request: ComputeRHIRequest) -> RHIResponse:
        """Compute Relationship Health Index."""
        if not self.rhi_service:
            raise RuntimeError("RHI service not initialized")
        return await self.rhi_service.compute_rhi(request)
    
    async def get_rhi_history(
        self,
        user_id: UUID,
        companion_id: UUID,
        days: int = 90,
    ) -> List[Dict[str, Any]]:
        """Get historical RHI values."""
        if not self.rhi_service:
            raise RuntimeError("RHI service not initialized")
        return await self.rhi_service.get_rhi_history(user_id, companion_id, days)
    
    # Drift operations
    async def check_drift(self, request: DriftCheckRequest) -> DriftResponse:
        """Check for dimension drift."""
        if not self.drift_service:
            raise RuntimeError("Drift service not initialized")
        return await self.drift_service.check_drift(request)
    
    async def record_dimension_score(
        self,
        user_id: UUID,
        companion_id: UUID,
        dimension: str,
        score: float,
    ) -> None:
        """Record a dimension score for drift tracking."""
        if not self.drift_service:
            raise RuntimeError("Drift service not initialized")
        return await self.drift_service.record_dimension_score(user_id, companion_id, dimension, score)
    
    async def get_drift_history(
        self,
        user_id: UUID,
        companion_id: UUID,
        dimension: str,
        days: int = 90,
    ) -> Dict[str, Any]:
        """Get drift history for a dimension."""
        if not self.drift_service:
            raise RuntimeError("Drift service not initialized")
        return await self.drift_service.get_drift_history(user_id, companion_id, dimension, days)
    
    # A/B Test operations
    async def create_ab_test(self, request: ABTestRequest) -> ABTestResponse:
        """Create a new A/B test."""
        if not self.ab_test_service:
            raise RuntimeError("A/B Test service not initialized")
        return await self.ab_test_service.create_test(request)
    
    async def get_ab_test(self, test_id: str) -> Optional[ABTestResponse]:
        """Get an A/B test by ID."""
        if not self.ab_test_service:
            raise RuntimeError("A/B Test service not initialized")
        return await self.ab_test_service.get_test(test_id)
    
    async def list_ab_tests(
        self,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[ABTestResponse]:
        """List A/B tests."""
        if not self.ab_test_service:
            raise RuntimeError("A/B Test service not initialized")
        return await self.ab_test_service.list_tests(status, limit)
    
    async def start_ab_test(self, test_id: str) -> Optional[ABTestResponse]:
        """Start an A/B test."""
        if not self.ab_test_service:
            raise RuntimeError("A/B Test service not initialized")
        return await self.ab_test_service.start_test(test_id)
    
    async def pause_ab_test(self, test_id: str) -> Optional[ABTestResponse]:
        """Pause an A/B test."""
        if not self.ab_test_service:
            raise RuntimeError("A/B Test service not initialized")
        return await self.ab_test_service.pause_test(test_id)
    
    async def complete_ab_test(self, test_id: str) -> Optional[ABTestResponse]:
        """Complete an A/B test."""
        if not self.ab_test_service:
            raise RuntimeError("A/B Test service not initialized")
        return await self.ab_test_service.complete_test(test_id)
    
    async def record_ab_test_result(
        self,
        test_id: str,
        variant: str,
        metrics: Dict[str, float],
        user_id: UUID,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Record an A/B test result."""
        if not self.ab_test_service:
            raise RuntimeError("A/B Test service not initialized")
        return await self.ab_test_service.record_result(test_id, variant, metrics, user_id, metadata)
    
    # Survey operations
    async def submit_survey(self, request: SurveySubmitRequest) -> SurveyResponse:
        """Submit a survey response."""
        if not self.survey_service:
            raise RuntimeError("Survey service not initialized")
        return await self.survey_service.submit_survey(request)
    
    async def get_survey_template(self, survey_type: str) -> Optional[Dict[str, Any]]:
        """Get survey template by type."""
        if not self.survey_service:
            raise RuntimeError("Survey service not initialized")
        return await self.survey_service.get_survey_template(survey_type)
    
    async def list_survey_templates(self) -> List[Dict[str, Any]]:
        """List all available survey templates."""
        if not self.survey_service:
            raise RuntimeError("Survey service not initialized")
        return await self.survey_service.list_survey_templates()
    
    async def get_user_surveys(
        self,
        user_id: UUID,
        companion_id: Optional[UUID] = None,
        survey_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get survey responses for a user."""
        if not self.survey_service:
            raise RuntimeError("Survey service not initialized")
        return await self.survey_service.get_user_surveys(user_id, companion_id, survey_type, limit)
    
    async def get_nps_history(
        self,
        user_id: UUID,
        companion_id: Optional[UUID] = None,
        days: int = 90,
    ) -> List[Dict[str, Any]]:
        """Get NPS score history."""
        if not self.survey_service:
            raise RuntimeError("Survey service not initialized")
        return await self.survey_service.get_nps_history(user_id, companion_id, days)
    
    async def get_satisfaction_trends(
        self,
        user_id: UUID,
        companion_id: Optional[UUID] = None,
        days: int = 90,
    ) -> List[Dict[str, Any]]:
        """Get satisfaction score trends."""
        if not self.survey_service:
            raise RuntimeError("Survey service not initialized")
        return await self.survey_service.get_satisfaction_trends(user_id, companion_id, days)
    
    # Report operations
    async def generate_report(self, request: ReportRequest) -> ReportResponse:
        """Generate an evaluation report."""
        if not self.report_service:
            raise RuntimeError("Report service not initialized")
        return await self.report_service.generate_report(request)
    
    # Health check
    async def health_check(self) -> HealthResponse:
        """Comprehensive health check."""
        start_time = time.time()
        
        checks = {
            "rhi_service": False,
            "drift_service": False,
            "ab_test_service": False,
            "survey_service": False,
            "report_service": False,
        }
        
        models_loaded = {}
        
        # Check each service
        if self.rhi_service:
            health = await self.rhi_service.health_check()
            checks["rhi_service"] = health.get("initialized", False)
        
        if self.drift_service:
            health = await self.drift_service.health_check()
            checks["drift_service"] = health.get("initialized", False)
        
        if self.ab_test_service:
            health = await self.ab_test_service.health_check()
            checks["ab_test_service"] = health.get("initialized", False)
            models_loaded["total_tests"] = health.get("total_tests", 0)
            models_loaded["running_tests"] = health.get("running_tests", 0)
        
        if self.survey_service:
            health = await self.survey_service.health_check()
            checks["survey_service"] = health.get("initialized", False)
            models_loaded["total_survey_responses"] = health.get("total_responses", 0)
        
        if self.report_service:
            health = await self.report_service.health_check()
            checks["report_service"] = health.get("initialized", False)
        
        # Determine overall status
        all_healthy = all(checks.values())
        any_healthy = any(checks.values())
        
        if all_healthy:
            status = "healthy"
        elif any_healthy:
            status = "degraded"
        else:
            status = "unhealthy"
        
        processing_time = (time.time() - start_time) * 1000
        
        return HealthResponse(
            service="evaluation-engine",
            version="0.1.0",
            status=status,
            checks=checks,
            models_loaded=models_loaded,
            processing_time_ms=processing_time,
        )
    
    async def close(self) -> None:
        """Close all services."""
        logger.info("Closing Evaluation Engine")
        
        services = [
            ("rhi", self.rhi_service),
            ("drift", self.drift_service),
            ("ab_test", self.ab_test_service),
            ("survey", self.survey_service),
            ("report", self.report_service),
        ]
        
        for name, service in services:
            if service:
                try:
                    await service.close()
                    logger.info(f"Closed {name} service")
                except Exception as e:
                    logger.error(f"Error closing {name} service", error=str(e))
        
        self._initialized = False
        logger.info("Evaluation Engine closed")


# Singleton instance
_evaluation_service: Optional[EvaluationService] = None


async def get_evaluation_service() -> EvaluationService:
    """Get or create Evaluation service singleton."""
    global _evaluation_service
    if _evaluation_service is None:
        _evaluation_service = EvaluationService()
        await _evaluation_service.initialize()
    return _evaluation_service


async def close_evaluation_service() -> None:
    """Close Evaluation service."""
    global _evaluation_service
    if _evaluation_service:
        await _evaluation_service.close()
        _evaluation_service = None