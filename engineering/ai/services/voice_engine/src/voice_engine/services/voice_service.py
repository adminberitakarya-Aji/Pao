"""Main Voice Service orchestrating all voice capabilities."""

import asyncio
import logging
import uuid
from typing import Optional, Dict, Any, AsyncGenerator
from pathlib import Path

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
)
from voice_engine.services.stt_service import get_stt_service, close_stt_service
from voice_engine.services.tts_service import get_tts_service, close_tts_service
from voice_engine.services.streaming_service import get_streaming_service, close_streaming_service
from voice_engine.services.livekit_service import get_livekit_service, close_livekit_service

logger = logging.getLogger(__name__)


class VoiceService:
    """Main orchestrator service for all voice capabilities."""
    
    def __init__(self):
        self.stt_service = None
        self.tts_service = None
        self.streaming_service = None
        self.livekit_service = None
        self._voice_configs: Dict[str, Dict[str, Any]] = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize all voice sub-services."""
        logger.info("Initializing Voice Engine services")
        
        try:
            # Initialize sub-services
            self.stt_service = await get_stt_service()
            self.tts_service = await get_tts_service()
            self.streaming_service = await get_streaming_service()
            self.livekit_service = await get_livekit_service()
            
            self._initialized = True
            logger.info("Voice Engine services initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Voice Engine services", error=str(e))
            raise
    
    # ==================== STT ====================
    
    async def transcribe(self, request: TranscribeRequest) -> TranscribeResponse:
        """Transcribe audio to text."""
        return await self.stt_service.transcribe(request)
    
    # ==================== TTS ====================
    
    async def synthesize(self, request: SynthesizeRequest) -> SynthesizeResponse:
        """Synthesize text to speech."""
        return await self.tts_service.synthesize(request)
    
    async def stream_synthesize(
        self,
        request: SynthesizeRequest,
        chunk_size: int = 1024
    ) -> AsyncGenerator[bytes, None]:
        """Stream synthesized audio."""
        async for chunk in self.tts_service.stream_synthesize(request, chunk_size):
            yield chunk
    
    # ==================== Streaming ====================
    
    async def start_stream(self, request: StreamStartRequest) -> StreamStartResponse:
        """Start a streaming transcription session."""
        return await self.streaming_service.start_stream(request)
    
    async def process_stream_chunk(self, request: StreamChunkRequest) -> StreamChunkResponse:
        """Process a streaming audio chunk."""
        return await self.streaming_service.process_chunk(request)
    
    async def end_stream(self, request: StreamEndRequest) -> StreamEndResponse:
        """End a streaming session."""
        return await self.streaming_service.end_stream(request.session_id, request.reason)
    
    # ==================== Interruption Handling ====================
    
    async def handle_interruption(self, request: InterruptionRequest) -> InterruptionResponse:
        """Handle user interruption during TTS playback."""
        return await self.streaming_service.handle_interruption(
            session_id=request.session_id,
            interruption_point=request.interruption_point_ms,
            user_audio_data=request.user_audio_data,
        )
    
    # ==================== LiveKit Calls ====================
    
    async def setup_call(self, request: CallSetupRequest) -> CallSetupResponse:
        """Set up a LiveKit voice call."""
        return await self.livekit_service.setup_call(request)
    
    async def end_call(self, request: CallEndRequest) -> CallEndResponse:
        """End a LiveKit voice call."""
        return await self.livekit_service.end_call(request)
    
    # ==================== Recording ====================
    
    async def start_recording(self, request: RecordingRequest) -> RecordingResponse:
        """Start recording a call."""
        egress_id = await self.livekit_service.start_recording(request)
        return RecordingResponse(
            room_name=request.room_name,
            action="started",
            egress_id=egress_id,
        )
    
    async def stop_recording(self, request: RecordingRequest) -> RecordingResponse:
        """Stop recording a call."""
        return await self.livekit_service.stop_recording(request)
    
    # ==================== Voice Configuration ====================
    
    async def set_voice_config(self, request: VoiceConfigRequest) -> VoiceConfigResponse:
        """Configure voice settings for a companion."""
        config = {
            "tts_engine": request.tts_engine,
            "voice_id": request.voice_id,
            "default_speed": request.default_speed,
            "default_pitch": request.default_pitch,
            "default_volume": request.default_volume,
            "default_language": request.default_language,
            "emotion_mapping": request.emotion_mapping,
            "interruption_sensitivity": request.interruption_sensitivity,
            "vad_sensitivity": request.vad_sensitivity,
        }
        
        self._voice_configs[str(request.companion_id)] = config
        
        return VoiceConfigResponse(
            companion_id=request.companion_id,
            tts_engine=request.tts_engine,
            voice_id=request.voice_id,
            default_speed=request.default_speed,
            default_pitch=request.default_pitch,
            default_volume=request.default_volume,
            default_language=request.default_language,
            emotion_mapping=request.emotion_mapping,
            interruption_sensitivity=request.interruption_sensitivity,
            vad_sensitivity=request.vad_sensitivity,
            updated_at=asyncio.get_event_loop().time(),
        )
    
    async def get_voice_config(self, companion_id: uuid.UUID) -> VoiceConfigResponse:
        """Get voice configuration for a companion."""
        config = self._voice_configs.get(str(companion_id), {})
        
        return VoiceConfigResponse(
            companion_id=companion_id,
            tts_engine=config.get("tts_engine", "kokoro"),
            voice_id=config.get("voice_id"),
            default_speed=config.get("default_speed", 1.0),
            default_pitch=config.get("default_pitch", 1.0),
            default_volume=config.get("default_volume", 1.0),
            default_language=config.get("default_language"),
            emotion_mapping=config.get("emotion_mapping"),
            interruption_sensitivity=config.get("interruption_sensitivity", 0.5),
            vad_sensitivity=config.get("vad_sensitivity", 0.5),
            updated_at=asyncio.get_event_loop().time(),
        )
    
    # ==================== Health & Monitoring ====================
    
    async def health_check(self) -> HealthResponse:
        """Comprehensive health check."""
        stt_health = await self.stt_service.health_check() if self.stt_service else {}
        tts_health = await self.tts_service.health_check() if self.tts_service else {}
        streaming_health = await self.streaming_service.health_check() if self.streaming_service else {}
        livekit_health = await self.livekit_service.health_check() if self.livekit_service else {}
        
        # Determine overall status
        status = "healthy"
        if not all([stt_health.get("model_loaded"), tts_health.get("initialized")]):
            status = "degraded"
        if not stt_health.get("model_loaded") or not tts_health.get("initialized"):
            status = "unhealthy"
        
        return HealthResponse(
            service="voice-engine",
            version="0.1.0",
            status=status,
            checks={
                "stt_model_loaded": stt_health.get("model_loaded", False),
                "tts_initialized": tts_health.get("initialized", False),
                "streaming_active": streaming_health.get("active_sessions", 0) > 0,
                "livekit_connected": livekit_health.get("connected", False),
            },
            stt_model_loaded=stt_health.get("model_loaded", False),
            tts_model_loaded=tts_health.get("initialized", False),
            livekit_connected=livekit_health.get("connected", False),
        )
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics."""
        return {
            "stt": await self.stt_service.health_check() if self.stt_service else {},
            "tts": await self.tts_service.health_check() if self.tts_service else {},
            "streaming": await self.streaming_service.health_check() if self.streaming_service else {},
            "livekit": await self.livekit_service.health_check() if self.livekit_service else {},
            "voice_configs": len(self._voice_configs),
        }
    
    # ==================== Cleanup ====================
    
    async def close(self) -> None:
        """Cleanup all services."""
        logger.info("Closing Voice Engine services")
        
        if self.streaming_service:
            await close_streaming_service()
        
        if self.tts_service:
            await close_tts_service()
        
        if self.stt_service:
            await close_stt_service()
        
        if self.livekit_service:
            await close_livekit_service()
        
        self._voice_configs.clear()
        self._initialized = False
        logger.info("Voice Engine services closed")


# Singleton instance
_voice_service: Optional[VoiceService] = None


async def get_voice_service() -> VoiceService:
    """Get or create Voice service singleton."""
    global _voice_service
    if _voice_service is None:
        _voice_service = VoiceService()
        await _voice_service.initialize()
    return _voice_service


async def close_voice_service() -> None:
    """Close Voice service."""
    global _voice_service
    if _voice_service:
        await _voice_service.close()
        _voice_service = None