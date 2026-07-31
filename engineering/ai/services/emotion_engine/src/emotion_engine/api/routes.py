"""API routes for Emotion Engine."""

import logging
from typing import Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse

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
    ErrorResponse,
)
from emotion_engine.services.emotion_service import get_emotion_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["emotion-engine"])


# ==================== Dependency ====================

async def get_service():
    """Get Emotion Service instance."""
    return await get_emotion_service()


# ==================== Health ====================

@router.get(
    "/health/live",
    response_model=HealthResponse,
    summary="Liveness probe",
)
async def liveness_probe():
    """Kubernetes liveness probe endpoint."""
    service = await get_service()
    return await service.health_check()


@router.get(
    "/health/ready",
    response_model=HealthResponse,
    summary="Readiness probe",
)
async def readiness_probe():
    """Kubernetes readiness probe endpoint."""
    service = await get_service()
    health = await service.health_check()
    
    if health.status == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )
    
    return health


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
)
async def health_check():
    """Comprehensive health check."""
    service = await get_service()
    return await service.health_check()


# ==================== Comprehensive Analysis ====================

@router.post(
    "/emotion/analyze",
    response_model=EmotionAnalysisResponse,
    summary="Comprehensive emotion analysis",
    description="Analyze text for valence-arousal, discrete emotions, and cognitive appraisals",
)
async def analyze_emotion(
    request: EmotionAnalysisRequest,
    service = Depends(get_service),
) -> EmotionAnalysisResponse:
    """Perform comprehensive emotion analysis."""
    try:
        return await service.analyze_emotion(request)
    except Exception as e:
        logger.error("Emotion analysis failed", error=str(e), request_id=request.request_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


# ==================== Valence-Arousal ====================

@router.post(
    "/emotion/valence-arousal",
    response_model=ValenceArousalResponse,
    summary="Predict valence and arousal",
)
async def predict_valence_arousal(
    request: ValenceArousalRequest,
    service = Depends(get_service),
) -> ValenceArousalResponse:
    """Predict valence-arousal coordinates for text."""
    try:
        return await service.predict_valence_arousal(request)
    except Exception as e:
        logger.error("VA prediction failed", error=str(e), request_id=request.request_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


# ==================== Discrete Emotions ====================

@router.post(
    "/emotion/discrete",
    response_model=EmotionAnalysisResponse,
    summary="Predict discrete emotions",
)
async def predict_discrete_emotions(
    request: EmotionAnalysisRequest,
    service = Depends(get_service),
) -> EmotionAnalysisResponse:
    """Predict discrete emotion categories."""
    try:
        return await service.predict_discrete_emotions(request)
    except Exception as e:
        logger.error("Discrete emotion prediction failed", error=str(e), request_id=request.request_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@router.post(
    "/emotion/batch",
    response_model=BatchEmotionResponse,
    summary="Batch emotion analysis",
)
async def batch_emotion_analysis(
    request: BatchEmotionRequest,
    service = Depends(get_service),
) -> BatchEmotionResponse:
    """Analyze multiple texts in batch."""
    try:
        return await service.predict_batch(request)
    except Exception as e:
        logger.error("Batch emotion analysis failed", error=str(e), request_id=request.request_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch analysis failed: {str(e)}"
        )


# ==================== Appraisal ====================

@router.post(
    "/emotion/appraisal",
    response_model=AppraisalResponse,
    summary="Cognitive appraisal analysis",
)
async def analyze_appraisal(
    request: AppraisalRequest,
    service = Depends(get_service),
) -> AppraisalResponse:
    """Analyze cognitive appraisals (Scherer's model)."""
    try:
        return await service.analyze_appraisal(request)
    except Exception as e:
        logger.error("Appraisal analysis failed", error=str(e), request_id=request.request_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Appraisal failed: {str(e)}"
        )


# ==================== Expression ====================

@router.post(
    "/emotion/express",
    response_model=ExpressionResponse,
    summary="Generate emotional expression",
)
async def generate_expression(
    request: ExpressionRequest,
    service = Depends(get_service),
) -> ExpressionResponse:
    """Generate emotional expression in text, voice, facial, or multimodal format."""
    try:
        return await service.generate_expression(request)
    except Exception as e:
        logger.error("Expression generation failed", error=str(e), request_id=request.request_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Expression failed: {str(e)}"
        )


# ==================== Calibration ====================

@router.post(
    "/emotion/calibrate",
    response_model=CalibrationResponse,
    summary="Emotion regulation calibration",
)
async def calibrate_emotion(
    request: CalibrationRequest,
    service = Depends(get_service),
) -> CalibrationResponse:
    """Get emotion regulation strategy recommendations."""
    try:
        return await service.calibrate(request)
    except Exception as e:
        logger.error("Calibration failed", error=str(e), request_id=request.request_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Calibration failed: {str(e)}"
        )


@router.get(
    "/emotion/calibration/history",
    summary="Get calibration history",
)
async def get_calibration_history(
    user_id: UUID,
    companion_id: UUID,
    limit: int = 50,
    service = Depends(get_service),
) -> Dict[str, Any]:
    """Get user's emotion calibration history."""
    try:
        history = await service.get_calibration_history(user_id, companion_id, limit)
        return {"history": history, "count": len(history)}
    except Exception as e:
        logger.error("Failed to get calibration history", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"History retrieval failed: {str(e)}"
        )


# ==================== Streaming ====================

@router.post(
    "/emotion/stream",
    response_model=StreamEmotionResponse,
    summary="Streaming emotion analysis",
)
async def stream_emotion_analysis(
    request: StreamEmotionRequest,
    service = Depends(get_service),
) -> StreamEmotionResponse:
    """Real-time streaming emotion analysis."""
    try:
        return await service.stream_analyze(request)
    except Exception as e:
        logger.error("Streaming analysis failed", error=str(e), session_id=str(request.session_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Streaming failed: {str(e)}"
        )


@router.post(
    "/emotion/stream/websocket",
    summary="WebSocket streaming emotion analysis",
)
async def websocket_stream_emotion(
    request: Request,
    service = Depends(get_service),
):
    """WebSocket endpoint for continuous streaming emotion analysis."""
    # This would be implemented with WebSocket support
    # For now, return info about WebSocket endpoint
    return {
        "message": "WebSocket endpoint available at /ws/emotion/stream",
        "protocol": "WebSocket",
        "format": "JSON messages with StreamEmotionRequest/Response",
    }


# ==================== Metrics ====================

@router.get(
    "/metrics",
    summary="Prometheus metrics",
)
async def metrics():
    """Prometheus metrics endpoint."""
    # Metrics are exposed via prometheus-client at /metrics
    # This is handled by the middleware
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response
    
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ==================== Error Handlers ====================

async def validation_exception_handler(request: Request, exc: Exception):
    """Handle validation errors."""
    return ErrorResponse(
        error="validation_error",
        message=str(exc),
        details={"path": str(request.url.path)},
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error("Unhandled exception", path=str(request.url.path), error=str(exc))
    return ErrorResponse(
        error="internal_error",
        message="An internal server error occurred",
        details={"path": str(request.url.path)},
    )