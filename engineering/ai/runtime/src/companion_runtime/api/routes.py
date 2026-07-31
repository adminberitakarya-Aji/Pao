"""Companion Runtime API Routes."""

import logging
from typing import AsyncGenerator
from uuid import UUID
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from companion_runtime.models.requests import (
    ChatRequest,
    ChatStreamRequest,
    CompanionContextRequest,
)
from companion_runtime.models.responses import (
    ChatResponse,
    ChatStreamChunk,
    HealthResponse,
    CompanionStateResponse,
    GraphExecutionResponse,
)
from companion_runtime.services.runtime_service import get_runtime_service
from companion_runtime.services.state_manager import get_state_manager
from companion_runtime.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["companion-runtime"])


@router.get("/health/live", response_model=HealthResponse)
async def health_live():
    """Liveness probe - service is running."""
    return HealthResponse(
        service="companion-runtime",
        version=settings.version,
        status="healthy",
        checks={"service": True},
    )


@router.get("/health/ready", response_model=HealthResponse)
async def health_ready():
    """Readiness probe - service can handle requests."""
    # Check engine connectivity
    engines = {
        "inference-gateway": settings.inference_gateway_url,
        "identity-engine": settings.identity_engine_url,
        "memory-engine": settings.memory_engine_url,
        "safety-engine": settings.safety_engine_url,
        "relationship-engine": settings.relationship_engine_url,
        "emotion-engine": settings.emotion_engine_url,
        "voice-engine": settings.voice_engine_url,
        "proactive-engine": settings.proactive_engine_url,
        "evaluation-engine": settings.evaluation_engine_url,
    }
    
    # In production, actually check each engine
    engine_status = {name: True for name in engines}
    
    # Check database
    try:
        state_manager = await get_state_manager()
        db_health = await state_manager.health_check()
        db_healthy = db_health.get("database") == "healthy"
    except Exception:
        db_healthy = False
    
    all_healthy = all(engine_status.values()) and db_healthy
    
    return HealthResponse(
        service="companion-runtime",
        version=settings.version,
        status="healthy" if all_healthy else "degraded",
        checks={
            "service": True,
            "database": db_healthy,
            **engine_status,
        },
        engines=engine_status,
    )


@router.post("/chat", response_model=GraphExecutionResponse)
async def chat(request: ChatRequest):
    """Process a chat request (non-streaming)."""
    runtime_service = await get_runtime_service()
    return await runtime_service.chat(request)


@router.post("/chat/stream")
async def chat_stream(request: ChatStreamRequest):
    """Process a streaming chat request."""
    runtime_service = await get_runtime_service()
    
    async def generate():
        async for chunk in runtime_service.chat_stream(request):
            yield chunk.model_dump_json() + "\n"
    
    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/context", response_model=CompanionStateResponse)
async def get_companion_context(request: CompanionContextRequest):
    """Get aggregated companion context from all engines."""
    runtime_service = await get_runtime_service()
    return await runtime_service.get_companion_context(request)


@router.get("/companions/{companion_id}/state")
async def get_companion_state(
    companion_id: UUID,
    user_id: UUID,
    conversation_id: UUID,
):
    """Get full companion state for a conversation."""
    # This would aggregate from all engines
    # Simplified for now
    return {
        "companion_id": str(companion_id),
        "user_id": str(user_id),
        "conversation_id": str(conversation_id),
        "message": "State aggregation endpoint - to be implemented",
    }


@router.get("/conversations/{conversation_id}/history")
async def get_conversation_history(
    conversation_id: UUID,
    user_id: UUID,
    companion_id: UUID,
    limit: int = 50,
):
    """Get conversation history from checkpoints."""
    try:
        state_manager = await get_state_manager()
        history = await state_manager.get_thread_history(
            user_id=user_id,
            companion_id=companion_id,
            conversation_id=conversation_id,
            limit=limit,
        )
        return {"conversation_id": str(conversation_id), "history": history}
    except Exception as e:
        logger.error(f"Failed to get conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversations/{conversation_id}/checkpoints")
async def delete_conversation_checkpoints(
    conversation_id: UUID,
    user_id: UUID,
    companion_id: UUID,
):
    """Delete all checkpoints for a conversation."""
    try:
        state_manager = await get_state_manager()
        thread_id = f"{user_id}:{companion_id}:{conversation_id}"
        await state_manager.delete_checkpoints(thread_id)
        return {"message": "Checkpoints deleted", "conversation_id": str(conversation_id)}
    except Exception as e:
        logger.error(f"Failed to delete checkpoints: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/engines/{engine_name}/health")
async def check_engine_health(engine_name: str):
    """Check health of a specific engine."""
    # Map engine names to clients
    engines = {
        "identity": "identity-engine",
        "memory": "memory-engine",
        "safety": "safety-engine",
        "relationship": "relationship-engine",
        "emotion": "emotion-engine",
        "voice": "voice-engine",
        "proactive": "proactive-engine",
        "evaluation": "evaluation-engine",
        "inference": "inference-gateway",
    }
    
    if engine_name not in engines:
        raise HTTPException(status_code=404, detail=f"Unknown engine: {engine_name}")
    
    # In production, actually check the engine
    return {
        "engine": engine_name,
        "healthy": True,
        "message": "Health check endpoint - implement actual checks",
    }


@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    # In production, expose Prometheus metrics
    return Response(
        content="# Metrics endpoint - implement prometheus_client exposition\n",
        media_type="text/plain",
    )


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    message: str
    request_id: str | None = None


@router.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return Response(
        content=ErrorResponse(
            error="internal_error",
            message="An internal error occurred",
        ).model_dump_json(),
        status_code=500,
        media_type="application/json",
    )