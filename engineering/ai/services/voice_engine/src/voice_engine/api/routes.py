"""API routes for Voice Engine."""

import time
import uuid
from typing import Optional, List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from voice_engine.config import settings
from voice_engine.models.requests import (
    TranscribeRequest,
    SynthesizeRequest,
    StreamStartRequest,
    StreamChunkRequest,
    StreamEndRequest,
    InterruptionRequest,
    CallSetupRequest,
    CallEndRequest,
    RecordingRequest,
    VoiceConfigRequest,
)
from voice_engine.models.responses import (
    TranscribeResponse,
    SynthesizeResponse,
    StreamStartResponse,
    StreamChunkResponse,
    StreamEndResponse,
    InterruptionResponse,
    CallSetupResponse,
    CallEndResponse,
    RecordingResponse,
    VoiceConfigResponse,
    HealthResponse,
    ErrorResponse,
)
from voice_engine.services.voice_service import VoiceService, get_voice_service, close_voice_service

router = APIRouter(prefix="/api/v1", tags=["voice"])


# Dependency injection
async def get_service() -> VoiceService:
    return await get_voice_service()


# Rate limiting dependency
async def rate_limit(request: Request, service: VoiceService = Depends(get_service)):
    if service.streaming_service and service.streaming_service.redis_cache:
        identifier = request.client.host if request.client else "unknown"
        allowed, remaining = await service.streaming_service.redis_cache.check_rate_limit(
            identifier, limit=100, window_seconds=60
        )
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"X-RateLimit-Remaining": str(remaining)},
            )
        request.state.rate_limit_remaining = remaining


# Exception handlers
@router.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail if isinstance(exc.detail, str) else "HTTP Error",
            message=str(exc.detail),
        ).model_dump(),
    )


@router.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal Server Error",
            message=str(exc),
        ).model_dump(),
    )


# ==================== Health Checks ====================

@router.get("/health/live", response_model=HealthResponse, tags=["health"])
async def liveness_check(service: VoiceService = Depends(get_service)):
    """Liveness probe - service is running."""
    return await service.health_check()


@router.get("/health/ready", response_model=HealthResponse, tags=["health"])
async def readiness_check(service: VoiceService = Depends(get_service)):
    """Readiness probe - service can handle requests."""
    health = await service.health_check()
    if health.status == "unhealthy":
        raise HTTPException(status_code=503, detail="Service not ready")
    return health


@router.get("/metrics", tags=["monitoring"])
async def metrics(service: VoiceService = Depends(get_service)):
    """Prometheus metrics endpoint."""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ==================== Speech-to-Text ====================

@router.post("/stt/transcribe", response_model=TranscribeResponse, dependencies=[Depends(rate_limit)])
async def transcribe_audio(
    request: TranscribeRequest,
    service: VoiceService = Depends(get_service),
):
    """
    Transcribe audio to text using Whisper.
    
    Supports multiple audio formats and languages.
    """
    return await service.transcribe(request)


# ==================== Text-to-Speech ====================

@router.post("/tts/synthesize", response_model=SynthesizeResponse, dependencies=[Depends(rate_limit)])
async def synthesize_speech(
    request: SynthesizeRequest,
    service: VoiceService = Depends(get_service),
):
    """
    Synthesize text to speech using Kokoro or XTTS.
    
    Returns base64 encoded audio data.
    """
    return await service.synthesize(request)


# ==================== Streaming Transcription ====================

@router.post("/stream/start", response_model=StreamStartResponse, dependencies=[Depends(rate_limit)])
async def start_stream(
    request: StreamStartRequest,
    service: VoiceService = Depends(get_service),
):
    """Start a new streaming transcription session."""
    return await service.start_stream(request)


@router.post("/stream/chunk", response_model=StreamChunkResponse, dependencies=[Depends(rate_limit)])
async def process_stream_chunk(
    request: StreamChunkRequest,
    service: VoiceService = Depends(get_service),
):
    """Process an audio chunk in a streaming session."""
    return await service.process_stream_chunk(request)


@router.post("/stream/end", response_model=StreamEndResponse, dependencies=[Depends(rate_limit)])
async def end_stream(
    request: StreamEndRequest,
    service: VoiceService = Depends(get_service),
):
    """End a streaming transcription session and get final transcript."""
    return await service.end_stream(request)


# ==================== Interruption Handling ====================

@router.post("/interrupt", response_model=InterruptionResponse, dependencies=[Depends(rate_limit)])
async def handle_interruption(
    request: InterruptionRequest,
    service: VoiceService = Depends(get_service),
):
    """
    Handle user interruption during TTS playback.
    
    Stops current TTS and processes user's interrupting speech.
    """
    return await service.handle_interruption(request)


# ==================== LiveKit Voice Calls ====================

@router.post("/calls/setup", response_model=CallSetupResponse, dependencies=[Depends(rate_limit)])
async def setup_call(
    request: CallSetupRequest,
    service: VoiceService = Depends(get_service),
):
    """Set up a LiveKit voice call room."""
    return await service.setup_call(request)


@router.post("/calls/end", response_model=CallEndResponse, dependencies=[Depends(rate_limit)])
async def end_call(
    request: CallEndRequest,
    service: VoiceService = Depends(get_service),
):
    """End a LiveKit voice call."""
    return await service.end_call(request)


# ==================== Recording ====================

@router.post("/recordings/start", response_model=RecordingResponse, dependencies=[Depends(rate_limit)])
async def start_recording(
    request: RecordingRequest,
    service: VoiceService = Depends(get_service),
):
    """Start recording a LiveKit room."""
    return await service.start_recording(request)


@router.post("/recordings/stop", response_model=RecordingResponse, dependencies=[Depends(rate_limit)])
async def stop_recording(
    request: RecordingRequest,
    service: VoiceService = Depends(get_service),
):
    """Stop recording a LiveKit room."""
    return await service.stop_recording(request)


# ==================== Voice Configuration ====================

@router.post("/voice/config", response_model=VoiceConfigResponse, dependencies=[Depends(rate_limit)])
async def set_voice_config(
    request: VoiceConfigRequest,
    service: VoiceService = Depends(get_service),
):
    """Configure voice settings for a companion."""
    return await service.set_voice_config(request)


@router.get("/voice/config/{companion_id}", response_model=VoiceConfigResponse, dependencies=[Depends(rate_limit)])
async def get_voice_config(
    companion_id: UUID,
    service: VoiceService = Depends(get_service),
):
    """Get voice configuration for a companion."""
    return await service.get_voice_config(companion_id)


# ==================== WebSocket for Real-time Streaming ====================

@router.websocket("/ws/{user_id}/{companion_id}")
async def websocket_voice(
    websocket: WebSocket,
    user_id: UUID,
    companion_id: UUID,
    service: VoiceService = Depends(get_service),
):
    """WebSocket endpoint for real-time voice streaming."""
    await websocket.accept()
    
    try:
        # Start streaming session
        start_request = StreamStartRequest(
            user_id=user_id,
            companion_id=companion_id,
            session_id=uuid.uuid4(),
        )
        start_response = await service.start_stream(start_request)
        await websocket.send_json(start_response.model_dump())
        
        # Process incoming audio chunks
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "audio_chunk":
                chunk_request = StreamChunkRequest(
                    session_id=start_response.session_id,
                    chunk_index=data["chunk_index"],
                    audio_data=data["audio_data"],
                    is_final=data.get("is_final", False),
                    timestamp_ms=data["timestamp_ms"],
                )
                chunk_response = await service.process_stream_chunk(chunk_request)
                await websocket.send_json(chunk_response.model_dump())
                
                if chunk_response.is_final:
                    break
            
            elif data.get("type") == "interruption":
                interrupt_request = InterruptionRequest(
                    user_id=user_id,
                    companion_id=companion_id,
                    session_id=start_response.session_id,
                    interruption_point_ms=data["interruption_point_ms"],
                    user_audio_data=data.get("user_audio_data"),
                )
                interrupt_response = await service.handle_interruption(interrupt_request)
                await websocket.send_json(interrupt_response.model_dump())
            
            elif data.get("type") == "end":
                end_request = StreamEndRequest(
                    session_id=start_response.session_id,
                    reason=data.get("reason", "completed"),
                )
                end_response = await service.end_stream(end_request)
                await websocket.send_json(end_response.model_dump())
                break
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json(ErrorResponse(
            error="WebSocket Error",
            message=str(e),
        ).model_dump())
    finally:
        await websocket.close()


# ==================== Service Management ====================

@router.get("/status", dependencies=[Depends(rate_limit)])
async def service_status(service: VoiceService = Depends(get_service)):
    """Get detailed service status and metrics."""
    return await service.get_metrics()


@router.post("/cleanup/sessions", dependencies=[Depends(rate_limit)])
async def cleanup_sessions(
    max_age_seconds: int = 300,
    service: VoiceService = Depends(get_service),
):
    """Clean up expired streaming sessions."""
    cleaned = await service.streaming_service.cleanup_expired_sessions(max_age_seconds)
    return {"cleaned_sessions": cleaned}