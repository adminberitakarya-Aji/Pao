"""Report Service for generating evaluation reports."""

import logging
import time
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from uuid import UUID

from evaluation_engine.config import settings
from evaluation_engine.models.requests import ReportRequest
from evaluation_engine.models.responses import ReportResponse, ReportSection
from evaluation_engine.services.rhi_service import get_rhi_service
from evaluation_engine.services.drift_service import get_drift_service
from evaluation_engine.services.ab_test_service import get_ab_test_service
from evaluation_engine.services.survey_service import get_survey_service

logger = logging.getLogger(__name__)


class ReportService:
    """Service for generating comprehensive evaluation reports."""
    
    def __init__(self):
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the report service."""
        logger.info("Initializing Report service")
        self._initialized = True
        logger.info("Report service initialized")
    
    async def generate_report(self, request: ReportRequest) -> ReportResponse:
        """Generate an evaluation report."""
        start_time = time.time()
        
        report_id = f"rpt_{uuid.uuid4().hex[:12]}"
        
        sections = []
        recommendations = []
        
        # Generate sections based on report type
        if request.report_type in ["comprehensive", "rhi"]:
            rhi_section = await self._generate_rhi_section(request)
            if rhi_section:
                sections.append(rhi_section)
        
        if request.report_type in ["comprehensive", "drift"]:
            drift_section = await self._generate_drift_section(request)
            if drift_section:
                sections.append(drift_section)
        
        if request.report_type in ["comprehensive", "ab_test"]:
            ab_section = await self._generate_ab_test_section(request)
            if ab_section:
                sections.append(ab_section)
        
        if request.report_type in ["comprehensive", "survey"]:
            survey_section = await self._generate_survey_section(request)
            if survey_section:
                sections.append(survey_section)
        
        # Generate recommendations if requested
        if request.include_recommendations:
            recommendations = await self._generate_recommendations(sections, request)
        
        processing_time = (time.time() - start_time) * 1000
        
        return ReportResponse(
            report_id=report_id,
            report_type=request.report_type,
            user_id=request.user_id,
            companion_id=request.companion_id,
            period_days=request.period_days,
            generated_at=datetime.now(),
            sections=sections,
            recommendations=recommendations,
            format=request.format,
            processing_time_ms=processing_time,
            request_id=request.request_id,
        )
    
    async def _generate_rhi_section(self, request: ReportRequest) -> Optional[ReportSection]:
        """Generate RHI section."""
        if not request.user_id or not request.companion_id:
            return None
        
        try:
            rhi_service = await get_rhi_service()
            rhi_response = await rhi_service.compute_rhi(
                type('obj', (object,), {
                    'user_id': request.user_id,
                    'companion_id': request.companion_id,
                    'dimensions': None,
                    'include_breakdown': True,
                    'period_days': request.period_days,
                    'request_id': None,
                })()
            )
            
            # Get history
            history = await rhi_service.get_rhi_history(
                request.user_id,
                request.companion_id,
                request.period_days,
            )
            
            content = {
                "rhi_score": rhi_response.rhi_score,
                "dimensions": rhi_response.dimensions,
                "trend": rhi_response.trend,
                "correlation_with_survey": rhi_response.correlation_with_survey,
                "history": history,
            }
            
            if rhi_response.breakdown:
                content["breakdown"] = rhi_response.breakdown
            
            visualizations = [
                {
                    "type": "radar_chart",
                    "title": "RHI Dimensions",
                    "data": rhi_response.dimensions,
                },
                {
                    "type": "line_chart",
                    "title": "RHI Trend",
                    "data": history,
                    "x": "date",
                    "y": "rhi_score",
                },
            ]
            
            return ReportSection(
                title="Relationship Health Index (RHI)",
                content=content,
                visualizations=visualizations,
            )
        except Exception as e:
            logger.error(f"Error generating RHI section: {e}")
            return None
    
    async def _generate_drift_section(self, request: ReportRequest) -> Optional[ReportSection]:
        """Generate drift detection section."""
        if not request.user_id or not request.companion_id:
            return None
        
        try:
            drift_service = await get_drift_service()
            drift_response = await drift_service.check_drift(
                type('obj', (object,), {
                    'user_id': request.user_id,
                    'companion_id': request.companion_id,
                    'dimensions': None,
                    'threshold': 0.15,
                    'window_days': request.period_days,
                    'request_id': None,
                })()
            )
            
            content = {
                "has_drift": drift_response.has_drift,
                "alerts": [
                    {
                        "dimension": a.dimension,
                        "current": a.current_score,
                        "baseline": a.baseline_score,
                        "drift": a.drift_magnitude,
                        "direction": a.direction,
                        "severity": a.severity,
                    }
                    for a in drift_response.alerts
                ],
                "summary": drift_response.summary,
            }
            
            visualizations = []
            if drift_response.alerts:
                visualizations.append({
                    "type": "bar_chart",
                    "title": "Drift Magnitude by Dimension",
                    "data": {
                        a.dimension: a.drift_magnitude
                        for a in drift_response.alerts
                    },
                })
            
            return ReportSection(
                title="Dimension Drift Analysis",
                content=content,
                visualizations=visualizations,
            )
        except Exception as e:
            logger.error(f"Error generating drift section: {e}")
            return None
    
    async def _generate_ab_test_section(self, request: ReportRequest) -> Optional[ReportSection]:
        """Generate A/B test section."""
        try:
            ab_service = await get_ab_test_service()
            tests = await ab_service.list_tests(limit=10)
            
            if not tests:
                return None
            
            content = {
                "total_tests": len(tests),
                "tests": [
                    {
                        "test_id": t.test_id,
                        "name": t.name,
                        "status": t.status,
                        "recommendation": t.recommendation,
                        "started_at": t.started_at.isoformat() if t.started_at else None,
                        "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                    }
                    for t in tests
                ],
            }
            
            running_tests = [t for t in tests if t.status == "running"]
            if running_tests:
                content["running_tests"] = len(running_tests)
            
            visualizations = [
                {
                    "type": "status_chart",
                    "title": "A/B Test Status",
                    "data": {
                        "draft": len([t for t in tests if t.status == "draft"]),
                        "running": len([t for t in tests if t.status == "running"]),
                        "paused": len([t for t in tests if t.status == "paused"]),
                        "completed": len([t for t in tests if t.status == "completed"]),
                    },
                },
            ]
            
            return ReportSection(
                title="A/B Testing Overview",
                content=content,
                visualizations=visualizations,
            )
        except Exception as e:
            logger.error(f"Error generating A/B test section: {e}")
            return None
    
    async def _generate_survey_section(self, request: ReportRequest) -> Optional[ReportSection]:
        """Generate survey section."""
        if not request.user_id:
            return None
        
        try:
            survey_service = await get_survey_service()
            
            nps_history = await survey_service.get_nps_history(
                request.user_id,
                request.companion_id,
                request.period_days,
            )
            
            satisfaction_trends = await survey_service.get_satisfaction_trends(
                request.user_id,
                request.companion_id,
                request.period_days,
            )
            
            content = {
                "nps_history": nps_history,
                "satisfaction_trends": satisfaction_trends,
            }
            
            visualizations = []
            if nps_history:
                visualizations.append({
                    "type": "line_chart",
                    "title": "NPS Score Trend",
                    "data": nps_history,
                    "x": "date",
                    "y": "nps_score",
                })
            
            if satisfaction_trends:
                visualizations.append({
                    "type": "line_chart",
                    "title": "Satisfaction Trends",
                    "data": satisfaction_trends,
                    "x": "date",
                    "y": "satisfaction_score",
                    "series": "survey_type",
                })
            
            return ReportSection(
                title="Survey Feedback Analysis",
                content=content,
                visualizations=visualizations,
            )
        except Exception as e:
            logger.error(f"Error generating survey section: {e}")
            return None
    
    async def _generate_recommendations(
        self,
        sections: List[ReportSection],
        request: ReportRequest,
    ) -> List[str]:
        """Generate actionable recommendations based on report sections."""
        recommendations = []
        
        for section in sections:
            if section.title == "Relationship Health Index (RHI)":
                rhi_score = section.content.get("rhi_score", 5.0)
                if rhi_score < 4.0:
                    recommendations.append(
                        "RHI is critically low. Consider companion reset or re-onboarding."
                    )
                elif rhi_score < 6.0:
                    recommendations.append(
                        "RHI below average. Schedule proactive check-ins and review conversation quality."
                    )
                
                # Dimension-specific recommendations
                dimensions = section.content.get("dimensions", {})
                for dim, score in dimensions.items():
                    if score < 4.0:
                        if dim == "trust":
                            recommendations.append("Low trust: Increase transparency and consistency in responses.")
                        elif dim == "safety":
                            recommendations.append("Low safety: Review safety engine configuration and boundaries.")
                        elif dim == "intimacy":
                            recommendations.append("Low intimacy: Encourage deeper, more personal conversations.")
                        elif dim == "growth":
                            recommendations.append("Low growth: Introduce goal-setting and learning activities.")
            
            elif section.title == "Dimension Drift Analysis":
                if section.content.get("has_drift"):
                    alerts = section.content.get("alerts", [])
                    for alert in alerts:
                        if alert["severity"] in ["high", "critical"]:
                            recommendations.append(
                                f"Critical drift in {alert['dimension']} ({alert['direction']}). "
                                f"Investigate recent interactions and consider intervention."
                            )
            
            elif section.title == "A/B Testing Overview":
                tests = section.content.get("tests", [])
                completed = [t for t in tests if t["status"] == "completed" and t["recommendation"] != "inconclusive"]
                for test in completed:
                    recommendations.append(
                        f"A/B test '{test['name']}' recommends variant {test['recommendation']}. "
                        f"Consider rolling out to all users."
                    )
            
            elif section.title == "Survey Feedback Analysis":
                nps_history = section.content.get("nps_history", [])
                if nps_history:
                    latest_nps = nps_history[-1]["nps_score"]
                    if latest_nps < 0:
                        recommendations.append("Negative NPS. Urgent review of companion experience needed.")
                    elif latest_nps < 30:
                        recommendations.append("Low NPS. Implement feedback-driven improvements.")
        
        # Add general recommendations if none specific
        if not recommendations:
            recommendations.append(
                "All metrics within healthy ranges. Continue monitoring and maintain current engagement strategies."
            )
        
        return recommendations
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the service."""
        return {
            "initialized": self._initialized,
        }
    
    async def close(self) -> None:
        """Cleanup resources."""
        self._initialized = False
        logger.info("Report service closed")


# Singleton instance
_report_service: Optional[ReportService] = None


async def get_report_service() -> ReportService:
    """Get or create Report service singleton."""
    global _report_service
    if _report_service is None:
        _report_service = ReportService()
        await _report_service.initialize()
    return _report_service


async def close_report_service() -> None:
    """Close Report service."""
    global _report_service
    if _report_service:
        await _report_service.close()
        _report_service = None