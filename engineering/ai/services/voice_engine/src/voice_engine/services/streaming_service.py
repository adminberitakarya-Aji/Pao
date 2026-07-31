"""Streaming Audio Service for real-time voice processing."""

import asyncio
import base64
import io
import logging
import time
import uuid
from typing import Optional, Dict, Any, AsyncGenerator
from dataclasses import dataclass, field

import numpy as np
import soundfile as sf

from voice_engine.config import settings
from voice_engine.models.requests import (
    StreamStartRequest,
    StreamChunkRequest,
    StreamEndRequest,
    InterruptionRequest,
)
from voice_engine.models.responses import (
    StreamStartResponse,
    StreamChunkResponse,
    StreamEndResponse,
    InterruptionResponse,
)
from voice_engine.services.stt_service import get_stt_service
from voice_engine.services.tts_service import get_tts_service

logger = logging.getLogger(__name__)


@dataclass
class StreamingSession:
    """State for a streaming audio session."""
    session_id: uuid.UUID
    user_id: uuid.UUID
    companion_id: uuid.UUID
    sample_rate: int
    language: Optional[str]
    buffer: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.float32))
    chunk_count: int = 0
    start_time: float = field(default_factory=time.time)
    vad_state: str = "silence"
    silence_duration: float = 0.0
    speech_started: bool = False
    last_activity: float = field(default_factory=time.time)
    is_final: bool = False
    transcript_parts: list = field(default_factory=list)
    interruption_pending: bool = False


class StreamingService:
    """Service for handling real-time streaming audio transcription and synthesis."""
    
    def __init__(self):
        self.sessions: Dict[uuid.UUID, StreamingSession] = {}
        self.stt_service = None
        self.tts_service = None
        self._vad_threshold = settings.vad_threshold
        self._min_speech_duration = settings.vad_min_speech_duration
        self._max_speech_duration = settings.vad_max_speech_duration
        self._min_silence_duration = settings.vad_min_silence_duration
    
    async def initialize(self) -> None:
        """Initialize the streaming service with dependencies."""
        self.stt_service = await get_stt_service()
        self.tts_service = await get_tts_service()
        logger.info("Streaming service initialized")
    
    async def start_stream(self, request: StreamStartRequest) -> StreamStartResponse:
        """Start a new streaming session."""
        session_id = uuid.uuid4()
        
        session = StreamingSession(
            session_id=session_id,
            user_id=request.user_id,
            companion_id=request.companion_id,
            sample_rate=request.sample_rate,
            language=None,
        )
        
        self.sessions[session_id] = session
        
        logger.info(
            "Streaming session started",
            session_id=str(session_id),
            user_id=str(request.user_id),
            companion_id=str(request.companion_id),
        )
        
        return StreamStartResponse(
            session_id=session_id,
            status="started",
            message="Streaming session started",
            config={
                "sample_rate": request.sample_rate,
                "channels": request.channels,
                "format": request.format,
                "vad_enabled": request.vad_enabled,
                "interruption_enabled": request.interruption_enabled,
                "vad_threshold": self._vad_threshold,
            },
        )
    
    async def process_chunk(self, request: StreamChunkRequest) -> StreamChunkResponse:
        """Process an incoming audio chunk."""
        session = self.sessions.get(request.session_id)
        if not session:
            return StreamChunkResponse(
                session_id=request.session_id,
                chunk_index=request.chunk_index,
                is_final=True,
                interruption_detected=False,
            )
        
        session.last_activity = time.time()
        
        # Decode audio chunk
        try:
            audio_data = base64.b64decode(request.audio_data)
            audio_io = io.BytesIO(audio_data)
            chunk_array, sr = sf.read(audio_io, dtype=np.float32)
        except Exception as e:
            logger.error("Failed to decode audio chunk", error=str(e))
            return StreamChunkResponse(
                session_id=request.session_id,
                chunk_index=request.chunk_index,
                is_final=request.is_final,
                interruption_detected=False,
            )
        
        # Convert to mono if stereo
        if len(chunk_array.shape) > 1:
            chunk_array = np.mean(chunk_array, axis=1)
        
        # Resample if needed
        if session.sample_rate != 16000:
            chunk_array = self._resample(chunk_array, session.sample_rate, 16000)
        
        # Add to buffer
        session.buffer = np.concatenate([session.buffer, chunk_array.astype(np.float32)])
        session.chunk_count += 1
        
        # Simple energy-based VAD
        energy = np.mean(chunk_array ** 2)
        is_speech = energy > (self._vad_threshold * 0.01)
        
        transcript = None
        is_final = request.is_final
        confidence = None
        vad_prob = float(energy)
        interruption = False
        
        # Process if we have enough audio or it's the final chunk
        buffer_duration = len(session.buffer) / 16000
        
        if buffer_duration >= 2.0 or request.is_final:
            # Transcribe buffer
            try:
                transcript_result = await self.stt_service.transcribe_audio(
                    audio_data=session.buffer,
                    sample_rate=16000,
                    language=session.language,
                )
                transcript = transcript_result.get("text", "").strip()
                confidence = transcript_result.get("confidence", 0.0)
                
                if transcript:
                    session.transcript_parts.append(transcript)
                    
                    # Check for interruption (user speaking while TTS playing)
                    if session.interruption_pending and is_speech:
                        interruption = True
                        session.interruption_pending = False
                
            except Exception as e:
                logger.error("Transcription failed", error=str(e))
            
            # Clear buffer if not final (keep last 0.5s for context)
            if not request.is_final:
                keep_samples = int(0.5 * 16000)
                if len(session.buffer) > keep_samples:
                    session.buffer = session.buffer[-keep_samples:]
            else:
                session.buffer = np.array([], dtype=np.float32)
        
        if request.is_final:
            await self.end_stream(request.session_id, "completed")
            is_final = True
        
        return StreamChunkResponse(
            session_id=request.session_id,
            chunk_index=request.chunk_index,
            transcript=transcript,
            is_final=is_final,
            confidence=confidence,
            vad_speech_probability=vad_prob,
            interruption_detected=interruption,
        )
    
    async def handle_interruption(self, request: InterruptionRequest) -> InterruptionResponse:
        """Handle user interruption during TTS playback."""
        # Find active streaming session
        session = None
        for s in self.sessions.values():
            if s.user_id == request.user_id and s.companion_id == request.companion_id:
                session = s
                break
        
        if session:
            session.interruption_pending = True
            # The next chunk processing will detect the interruption
        
        interruption_point = request.interruption_point_ms
        user_transcript = None
        
        if request.user_audio_data:
            try:
                audio_data = base64.b64decode(request.user_audio_data)
                audio_io = io.BytesIO(audio_data)
                audio_array, sr = sf.read(audio_io, dtype=np.float32)
                
                if len(audio_array.shape) > 1:
                    audio_array = np.mean(audio_array, axis=1)
                
                if sr != 16000:
                    audio_array = self._resample(audio_array, sr, 16000)
                
                result = await self.stt_service.transcribe_audio(
                    audio_data=audio_array,
                    sample_rate=16000,
                )
                user_transcript = result.get("text", "").strip()
                
            except Exception as e:
                logger.error("Interruption transcription failed", error=str(e))
        
        logger.info(
            "Interruption handled",
            user_id=str(request.user_id),
            companion_id=str(request.companion_id),
            point_ms=interruption_point,
            transcript=user_transcript,
        )
        
        return InterruptionResponse(
            session_id=request.session_id,
            interruption_handled=True,
            interruption_point_ms=interruption_point,
            tts_stopped=True,
            user_transcript=user_transcript,
            message="Interruption processed",
        )
    
    async def end_stream(self, session_id: uuid.UUID, reason: str = "completed") -> StreamEndResponse:
        """End a streaming session and return final transcript."""
        session = self.sessions.get(session_id)
        if not session:
            return StreamEndResponse(
                session_id=session_id,
                status="error",
                full_transcript="",
                total_duration_seconds=0,
                total_chunks=0,
                average_confidence=0.0,
            )
        
        # Process any remaining buffer
        final_transcript = " ".join(session.transcript_parts).strip()
        avg_confidence = 0.0  # Would need to track this
        
        duration = time.time() - session.start_time
        total_chunks = session.chunk_count
        
        del self.sessions[session_id]
        
        logger.info(
            "Streaming session ended",
            session_id=str(session_id),
            reason=reason,
            duration=duration,
            chunks=total_chunks,
        )
        
        return StreamEndResponse(
            session_id=session_id,
            status=reason,
            full_transcript=final_transcript,
            total_duration_seconds=duration,
            total_chunks=total_chunks,
            average_confidence=avg_confidence,
        )
    
    async def synthesize_streaming(
        self,
        text: str,
        user_id: uuid.UUID,
        companion_id: uuid.UUID,
        voice_id: Optional[str] = None,
        speed: float = 1.0,
        pitch: float = 1.0,
        volume: float = 1.0,
        engine: str = "kokoro",
        chunk_size: int = 1024,
    ) -> AsyncGenerator[bytes, None]:
        """Stream synthesized audio for real-time playback."""
        # This would integrate with TTS service for streaming
        # For now, synthesize full and chunk
        from voice_engine.models.requests import SynthesizeRequest
        
        request = SynthesizeRequest(
            user_id=user_id,
            companion_id=companion_id,
            text=text,
            engine=engine,
            voice_id=voice_id,
            speed=speed,
            pitch=pitch,
            volume=volume,
            stream=True,
        )
        
        async for chunk in self.tts_service.stream_synthesize(request, chunk_size):
            yield chunk
    
    def _resample(self, audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """Resample audio to target sample rate."""
        if orig_sr == target_sr:
            return audio
        
        ratio = target_sr / orig_sr
        new_length = int(len(audio) * ratio)
        indices = np.linspace(0, len(audio) - 1, new_length)
        return np.interp(indices, np.arange(len(audio)), audio).astype(np.float32)
    
    async def cleanup_expired_sessions(self, max_age_seconds: int = 300) -> int:
        """Clean up expired streaming sessions."""
        now = time.time()
        expired = [
            sid for sid, session in self.sessions.items()
            if now - session.last_activity > max_age_seconds
        ]
        
        for sid in expired:
            del self.sessions[sid]
            logger.warning("Cleaned up expired session", session_id=str(sid))
        
        return len(expired)
    
    async def get_session(self, session_id: uuid.UUID) -> Optional[StreamingSession]:
        """Get session by ID."""
        return self.sessions.get(session_id)
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for streaming service."""
        stt_health = await self.stt_service.health_check() if self.stt_service else {}
        tts_health = await self.tts_service.health_check() if self.tts_service else {}
        
        return {
            "active_sessions": len(self.sessions),
            "stt": stt_health,
            "tts": tts_health,
        }
    
    async def close(self) -> None:
        """Cleanup all sessions and resources."""
        self.sessions.clear()
        logger.info("Streaming service closed")


# Singleton instance
_streaming_service: Optional[StreamingService] = None


async def get_streaming_service() -> StreamingService:
    """Get or create streaming service singleton."""
    global _streaming_service
    if _streaming_service is None:
        _streaming_service = StreamingService()
        await _streaming_service.initialize()
    return _streaming_service


async def close_streaming_service() -> None:
    """Close streaming service."""
    global _streaming_service
    if _streaming_service:
        await _streaming_service.close()
        _streaming_service = None