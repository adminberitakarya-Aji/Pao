"""Survey Service for collecting and processing user surveys."""

import logging
import time
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from evaluation_engine.config import settings
from evaluation_engine.models.requests import SurveySubmitRequest
from evaluation_engine.models.responses import SurveyResponse

logger = logging.getLogger(__name__)


class SurveyService:
    """Service for managing surveys and responses."""
    
    # Survey templates
    SURVEY_TEMPLATES = {
        "nps": {
            "name": "Net Promoter Score",
            "questions": [
                {
                    "id": "nps_score",
                    "type": "scale",
                    "text": "How likely are you to recommend your AI companion to a friend?",
                    "scale_min": 0,
                    "scale_max": 10,
                },
                {
                    "id": "nps_reason",
                    "type": "text",
                    "text": "What's the primary reason for your score?",
                    "required": False,
                },
            ],
        },
        "satisfaction": {
            "name": "Satisfaction Survey",
            "questions": [
                {
                    "id": "overall_satisfaction",
                    "type": "scale",
                    "text": "How satisfied are you with your AI companion overall?",
                    "scale_min": 1,
                    "scale_max": 10,
                },
                {
                    "id": "conversation_quality",
                    "type": "scale",
                    "text": "How would you rate the quality of conversations?",
                    "scale_min": 1,
                    "scale_max": 10,
                },
                {
                    "id": "helpfulness",
                    "type": "scale",
                    "text": "How helpful is your companion?",
                    "scale_min": 1,
                    "scale_max": 10,
                },
            ],
        },
        "relationship": {
            "name": "Relationship Health Survey",
            "questions": [
                {
                    "id": "trust",
                    "type": "scale",
                    "text": "How much do you trust your companion?",
                    "scale_min": 1,
                    "scale_max": 10,
                },
                {
                    "id": "intimacy",
                    "type": "scale",
                    "text": "How emotionally close do you feel to your companion?",
                    "scale_min": 1,
                    "scale_max": 10,
                },
                {
                    "id": "satisfaction",
                    "type": "scale",
                    "text": "How satisfied are you with the relationship?",
                    "scale_min": 1,
                    "scale_max": 10,
                },
                {
                    "id": "safety",
                    "type": "scale",
                    "text": "How safe do you feel sharing with your companion?",
                    "scale_min": 1,
                    "scale_max": 10,
                },
                {
                    "id": "growth",
                    "type": "scale",
                    "text": "Has your companion helped you grow?",
                    "scale_min": 1,
                    "scale_max": 10,
                },
            ],
        },
        "safety": {
            "name": "Safety & Wellbeing Survey",
            "questions": [
                {
                    "id": "feeling_safe",
                    "type": "scale",
                    "text": "Do you feel safe interacting with your companion?",
                    "scale_min": 1,
                    "scale_max": 10,
                },
                {
                    "id": "boundaries_respected",
                    "type": "scale",
                    "text": "Does your companion respect your boundaries?",
                    "scale_min": 1,
                    "scale_max": 10,
                },
                {
                    "id": "concerns",
                    "type": "text",
                    "text": "Any safety concerns you'd like to share?",
                    "required": False,
                },
            ],
        },
    }
    
    def __init__(self):
        self.http_client = None
        self._initialized = False
        # In-memory storage for survey responses
        self.responses: List[Dict[str, Any]] = []
    
    async def initialize(self) -> None:
        """Initialize the survey service."""
        logger.info("Initializing Survey service")
        self._initialized = True
        logger.info("Survey service initialized")
    
    async def submit_survey(self, request: SurveySubmitRequest) -> SurveyResponse:
        """Submit a survey response."""
        start_time = time.time()
        
        survey_id = f"survey_{uuid.uuid4().hex[:12]}"
        
        # Validate survey type
        if request.survey_type not in self.SURVEY_TEMPLATES:
            raise ValueError(f"Unknown survey type: {request.survey_type}")
        
        template = self.SURVEY_TEMPLATES[request.survey_type]
        
        # Calculate scores
        nps_score = None
        satisfaction_score = None
        
        if request.survey_type == "nps":
            nps_score = request.responses.get("nps_score")
        elif request.survey_type in ["satisfaction", "relationship"]:
            # Average of scale questions
            scale_values = [
                v for k, v in request.responses.items()
                if isinstance(v, (int, float))
            ]
            if scale_values:
                satisfaction_score = sum(scale_values) / len(scale_values)
        
        # Store response
        response_record = {
            "survey_id": survey_id,
            "user_id": str(request.user_id),
            "companion_id": str(request.companion_id),
            "survey_type": request.survey_type,
            "responses": request.responses,
            "metadata": request.metadata or {},
            "nps_score": nps_score,
            "satisfaction_score": satisfaction_score,
            "submitted_at": datetime.now().isoformat(),
        }
        
        self.responses.append(response_record)
        
        processing_time = (time.time() - start_time) * 1000
        
        return SurveyResponse(
            survey_id=survey_id,
            user_id=request.user_id,
            companion_id=request.companion_id,
            survey_type=request.survey_type,
            received_at=datetime.now(),
            processed=True,
            nps_score=nps_score,
            satisfaction_score=satisfaction_score,
            processing_time_ms=processing_time,
            request_id=request.request_id,
        )
    
    async def get_survey_template(self, survey_type: str) -> Optional[Dict[str, Any]]:
        """Get survey template by type."""
        return self.SURVEY_TEMPLATES.get(survey_type)
    
    async def list_survey_templates(self) -> List[Dict[str, Any]]:
        """List all available survey templates."""
        return [
            {
                "type": k,
                "name": v["name"],
                "question_count": len(v["questions"]),
            }
            for k, v in self.SURVEY_TEMPLATES.items()
        ]
    
    async def get_user_surveys(
        self,
        user_id: UUID,
        companion_id: Optional[UUID] = None,
        survey_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get survey responses for a user."""
        filtered = [
            r for r in self.responses
            if r["user_id"] == str(user_id)
        ]
        
        if companion_id:
            filtered = [r for r in filtered if r["companion_id"] == str(companion_id)]
        
        if survey_type:
            filtered = [r for r in filtered if r["survey_type"] == survey_type]
        
        # Sort by submission date (newest first)
        filtered.sort(key=lambda x: x["submitted_at"], reverse=True)
        
        return filtered[:limit]
    
    async def get_nps_history(
        self,
        user_id: UUID,
        companion_id: Optional[UUID] = None,
        days: int = 90,
    ) -> List[Dict[str, Any]]:
        """Get NPS score history for trend analysis."""
        cutoff = datetime.now() - timedelta(days=days)
        
        filtered = [
            r for r in self.responses
            if r["user_id"] == str(user_id)
            and r["survey_type"] == "nps"
            and r.get("nps_score") is not None
        ]
        
        if companion_id:
            filtered = [r for r in filtered if r["companion_id"] == str(companion_id)]
        
        # Filter by date
        filtered = [
            r for r in filtered
            if datetime.fromisoformat(r["submitted_at"]) >= cutoff
        ]
        
        # Sort by date
        filtered.sort(key=lambda x: x["submitted_at"])
        
        return [
            {
                "date": r["submitted_at"],
                "nps_score": r["nps_score"],
                "companion_id": r["companion_id"],
            }
            for r in filtered
        ]
    
    async def get_satisfaction_trends(
        self,
        user_id: UUID,
        companion_id: Optional[UUID] = None,
        days: int = 90,
    ) -> List[Dict[str, Any]]:
        """Get satisfaction score trends."""
        cutoff = datetime.now() - timedelta(days=days)
        
        filtered = [
            r for r in self.responses
            if r["user_id"] == str(user_id)
            and r["survey_type"] in ["satisfaction", "relationship"]
            and r.get("satisfaction_score") is not None
        ]
        
        if companion_id:
            filtered = [r for r in filtered if r["companion_id"] == str(companion_id)]
        
        filtered = [
            r for r in filtered
            if datetime.fromisoformat(r["submitted_at"]) >= cutoff
        ]
        
        filtered.sort(key=lambda x: x["submitted_at"])
        
        return [
            {
                "date": r["submitted_at"],
                "satisfaction_score": r["satisfaction_score"],
                "survey_type": r["survey_type"],
                "companion_id": r["companion_id"],
            }
            for r in filtered
        ]
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the service."""
        survey_types = {}
        for r in self.responses:
            st = r["survey_type"]
            survey_types[st] = survey_types.get(st, 0) + 1
        
        return {
            "initialized": self._initialized,
            "total_responses": len(self.responses),
            "responses_by_type": survey_types,
        }
    
    async def close(self) -> None:
        """Cleanup resources."""
        self._initialized = False
        self.responses.clear()
        logger.info("Survey service closed")


# Singleton instance
_survey_service: Optional[SurveyService] = None


async def get_survey_service() -> SurveyService:
    """Get or create Survey service singleton."""
    global _survey_service
    if _survey_service is None:
        _survey_service = SurveyService()
        await _survey_service.initialize()
    return _survey_service


async def close_survey_service() -> None:
    """Close Survey service."""
    global _survey_service
    if _survey_service:
        await _survey_service.close()
        _survey_service = None