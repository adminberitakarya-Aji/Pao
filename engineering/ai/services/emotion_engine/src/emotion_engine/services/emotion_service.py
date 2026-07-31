"""Main Emotion Service orchestrating all emotion capabilities."""

import asyncio
import logging
import uuid
from typing import Optional, Dict, Any, List
from uuid import UUID

from emotion_engine.config import settings
from emotion_engine.models.requests import (
    EmotionAnalysisRequest,
    ValenceArousalRequest,
    AppraisalRequest,
    ExpressionRequest,
    CalibrationRequest,
    BatchEmotionRequest,
    StreamEmotionRequest,
)
from emotion_engine.models.responses import (
    EmotionAnalysisResponse,
    ValenceArousalResponse,
    AppraisalResponse,
    ExpressionResponse,
    CalibrationResponse,
    BatchEmotionResponse,
    StreamEmotionResponse,
    HealthResponse,
)
from emotion_engine.services.valence_arousal_service import get_valence_arousal_service, close_valence_arousal_service
from emotion_engine.services.discrete_emotion_service import get_discrete_emotion_service, close_discrete_emotion_service
from emotion_engine.services.appraisal_service import get_appraisal_service, close_appraisal_service
from emotion_engine.services.expression_service import get_expression_service, close_expression_service
from emotion_engine.services.calibration_service import get_calibration_service, close_calibration_service

logger = logging.getLogger(__name__)


class EmotionService:
    """Main orchestrator service for all emotion capabilities."""
    
    def __init__(self):
        self.valence_arousal_service = None
        self.discrete_emotion_service = None
        self.appraisal_service = None
        self.expression_service = None
        self.calibration_service = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize all emotion sub-services."""
        logger.info("Initializing Emotion Engine services")
        
        try:
            # Initialize sub-services
            self.valence_arousal_service = await get_valence_arousal_service()
            self.discrete_emotion_service = await get_discrete_emotion_service()
            self.appraisal_service = await get_appraisal_service()
            self.expression_service = await get_expression_service()
            self.calibration_service = await get_calibration_service()
            
            self._initialized = True
            logger.info("Emotion Engine services initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Emotion Engine services", error=str(e))
            raise
    
    # ==================== Comprehensive Emotion Analysis ====================
    
    async def analyze_emotion(self, request: EmotionAnalysisRequest) -> EmotionAnalysisResponse:
        """Perform comprehensive emotion analysis combining all models."""
        start_time = asyncio.get_event_loop().time()
        
        # Run predictions in parallel
        va_task = self.valence_arousal_service.predict_valence_arousal(
            ValenceArousalRequest(
                user_id=request.user_id,
                companion_id=request.companion_id,
                text=request.text,
                context=request.context,
                language=request.language,
            )
        )
        
        discrete_task = self.discrete_emotion_service.predict_emotions(request)
        appraisal_task = None
        
        if request.include_appraisal and settings.enable_appraisal:
            appraisal_task = self.appraisal_service.analyze_appraisal(
                AppraisalRequest(
                    user_id=request.user_id,
                    companion_id=request.companion_id,
                    text=request.text,
                    context=request.context,
                    language=request.language,
                )
            )
        
        # Wait for results
        va_result = await va_task
        discrete_result = await discrete_task
        appraisal_result = await appraisal_task if appraisal_task else None
        
        # Combine results
        dominant_emotion = discrete_result.top_emotion
        emotional_complexity = len(discrete_result.emotion_probabilities) / 10.0  # Normalized
        
        processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        return EmotionAnalysisResponse(
            user_id=request.user_id,
            companion_id=request.companion_id,
            valence_arousal=va_result,
            discrete_emotions=discrete_result.emotion_probabilities,
            appraisal=appraisal_result,
            dominant_emotion=dominant_emotion,
            emotional_complexity=min(1.0, emotional_complexity),
            processing_time_ms=processing_time,
            request_id=request.request_id,
        )
    
    # ==================== Valence-Arousal ====================
    
    async def predict_valence_arousal(self, request: ValenceArousalRequest) -> ValenceArousalResponse:
        """Predict valence and arousal."""
        return await self.valence_arousal_service.predict_valence_arousal(request)
    
    # ==================== Discrete Emotions ====================
    
    async def predict_discrete_emotions(self, request: EmotionAnalysisRequest) -> EmotionAnalysisResponse:
        """Predict discrete emotions."""
        return await self.discrete_emotion_service.predict_emotions(request)
    
    async def predict_batch(self, request: BatchEmotionRequest) -> BatchEmotionResponse:
        """Batch emotion prediction."""
        return await self.discrete_emotion_service.predict_batch(request)
    
    # ==================== Appraisal ====================
    
    async def analyze_appraisal(self, request: AppraisalRequest) -> AppraisalResponse:
        """Analyze cognitive appraisals."""
        return await self.appraisal_service.analyze_appraisal(request)
    
    # ==================== Expression ====================
    
    async def generate_expression(self, request: ExpressionRequest) -> ExpressionResponse:
        """Generate emotional expression."""
        return await self.expression_service.generate_expression(request)
    
    # ==================== Calibration ====================
    
    async def calibrate(self, request: CalibrationRequest) -> CalibrationResponse:
        """Generate emotion regulation recommendations."""
        return await self.calibration_service.calibrate(request)
    
    async def get_calibration_history(
        self,
        user_id: UUID,
        companion_id: UUID,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get user's emotion calibration history."""
        return await self.calibration_service.get_user_history(user_id, companion_id, limit)
    
    # ==================== Streaming ====================
    
    async def stream_analyze(self, request: StreamEmotionRequest) -> StreamEmotionResponse:
        """Streaming emotion analysis for real-time processing."""
        start_time = asyncio.get_event_loop().time()
        
        # Predict valence-arousal for chunk
        va_result = await self.valence_arousal_service.predict_valence_arousal(
            ValenceArousalRequest(
                user_id=request.user_id,
                companion_id=request.companion_id,
                text=request.text_chunk,
                context=request.context,
                language=request.language,
            )
        )
        
        # Get discrete emotions
        discrete_result = await self.discrete_emotion_service.predict_from_text(request.text_chunk)
        
        # Convert to list format
        discrete_emotions = [
            {"emotion": k, "intensity": v, "confidence": v}
            for k, v in discrete_result.items()
        ]
        
        processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        return StreamEmotionResponse(
            session_id=request.session_id,
            chunk_index=request.chunk_index,
            valence=va_result.valence,
            arousal=va_result.arousal,
            dominant_emotion=va_result.dominant_emotion,
            discrete_emotions=discrete_emotions,
            is_final=request.is_final,
            confidence=va_result.confidence,
            processing_time_ms=processing_time,
        )
    
    # ==================== Health & Monitoring ====================
    
    async def health_check(self) -> HealthResponse:
        """Comprehensive health check."""
        va_health = await self.valence_arousal_service.health_check()
        discrete_health = await self.discrete_emotion_service.health_check()
        appraisal_health = await self.appraisal_service.health_check()
        expression_health = await self.expression_service.health_check()
        calibration_health = await self.calibration_service.health_check()
        
        # Determine overall status
        all_healthy = all([
            va_health.get("initialized"),
            discrete_health.get("initialized"),
            appraisal_health.get("initialized"),
            expression_health.get("initialized"),
            calibration_health.get("initialized"),
        ])
        
        status = "healthy" if all_healthy else "degraded"
        if not any([va_health.get("model_loaded"), discrete_health.get("model_loaded")]):
            status = "unhealthy"
        
        return HealthResponse(
            service="emotion-engine",
            version="0.1.0",
            status=status,
            checks={
                "valence_arousal": va_health.get("initialized", False),
                "discrete_emotion": discrete_health.get("initialized", False),
                "appraisal": appraisal_health.get("initialized", False),
                "expression": expression_health.get("initialized", False),
                "calibration": calibration_health.get("initialized", False),
            },
            models_loaded={
                "valence_arousal": va_health.get("model_loaded", False),
                "discrete_emotion": discrete_health.get("model_loaded", False),
                "appraisal": appraisal_health.get("model_loaded", False),
                "expression": expression_health.get("model_loaded", False),
            },
            processing_time_ms=0.0,
        )
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics."""
        return {
            "valence_arousal": await self.valence_arousal_service.health_check(),
            "discrete_emotion": await self.discrete_emotion_service.health_check(),
            "appraisal": await self.appraisal_service.health_check(),
            "expression": await self.expression_service.health_check(),
            "calibration": await self.calibration_service.health_check(),
        }
    
    # ==================== Cleanup ====================
    
    async def close(self) -> None:
        """Cleanup all services."""
        logger.info("Closing Emotion Engine services")
        
        await close_expression_service()
        await close_calibration_service()
        await close_appraisal_service()
        await close_discrete_emotion_service()
        await close_valence_arousal_service()
        
        self._initialized = False
        logger.info("Emotion Engine services closed")


# Singleton instance
_emotion_service: Optional[EmotionService] = None


async def get_emotion_service() -> EmotionService:
    """Get or create Emotion service singleton."""
    global _emotion_service
    if _emotion_service is None:
        _emotion_service = EmotionService()
        await _emotion_service.initialize()
    return _emotion_service


async def close_emotion_service() -> None:
    """Close Emotion service."""
    global _emotion_service
    if _emotion_service:
        await _emotion_service.close()
        _emotion_service = None