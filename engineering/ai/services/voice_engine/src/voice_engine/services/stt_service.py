"""Speech-to-Text Service using Faster-Whisper."""

import asyncio
import base64
import io
import logging
import time
import uuid
from typing import Optional, List, Dict, Any, AsyncGenerator
from pathlib import Path

import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel

from voice_engine.config import settings
from voice_engine.models.requests import TranscribeRequest, StreamStartRequest, StreamChunkRequest
from voice_engine.models.responses import TranscribeResponse, StreamStartResponse, StreamChunkResponse, StreamEndResponse

logger = logging.getLogger(__name__)


class STTService:
    """Speech-to-Text service using Faster-Whisper."""
    
    def __init__(self):
        self.model: Optional[WhisperModel] = None
        self.model_name = settings.stt_model_name
        self.device = settings.stt_device
        self.compute_type = settings.stt_compute_type
        self._streaming_sessions: Dict[uuid.UUID, Dict[str, Any]] = {}
        self._vad_threshold = 0.5
    
    async def initialize(self) -> None:
        """Initialize the Whisper model."""
        logger.info("Loading STT model", model=self.model_name, device=self.device)
        
        try:
            self.model = WhisperModel(
                self.model_name,
                device=self.device,
                compute_type=self.compute_type,
                download_root=settings.stt_model_cache_dir,
            )
            logger.info("STT model loaded successfully")
        except Exception as e:
            logger.error("Failed to load STT model", error=str(e))
            raise
    
    async def transcribe(self, request: TranscribeRequest) -> TranscribeResponse:
        """Transcribe audio file to text."""
        start_time = time.time()
        
        # Decode base64 audio
        audio_data = base64.b64decode(request.audio_data)
        
        # Load audio using soundfile
        audio_io = io.BytesIO(audio_data)
        audio_array, sample_rate = sf.read(audio_io)
        
        # Convert to mono if stereo
        if len(audio_array.shape) > 1:
            audio_array = np.mean(audio_array, axis=1)
        
        # Resample to 16kHz if needed
        if sample_rate != 16000:
            audio_array = self._resample(audio_array, sample_rate, 16000)
            sample_rate = 16000
        
        # Transcribe
        segments, info = self.model.transcribe(
            audio_array,
            language=request.language,
            task="transcribe",
            beam_size=5,
            word_timestamps=request.word_timestamps,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )
        
        # Collect results
        segments_list = []
        full_text = []
        word_timestamps = []
        
        for segment in segments:
            segments_list.append({
                "id": segment.id,
                "start": segment.start,
                "end": segment.end,
                "text": segment.text,
                "tokens": segment.tokens,
                "temperature": segment.temperature,
                "avg_logprob": segment.avg_logprob,
                "compression_ratio": segment.compression_ratio,
                "no_speech_prob": segment.no_speech_prob,
            })
            full_text.append(segment.text)
            
            if request.word_timestamps and segment.words:
                for word in segment.words:
                    word_timestamps.append({
                        "word": word.word,
                        "start": word.start,
                        "end": word.end,
                        "probability": word.probability,
                    })
        
        full_text_str = " ".join(full_text).strip()
        duration = time.time() - start_time
        
        return TranscribeResponse(
            user_id=request.user_id,
            companion_id=request.companion_id,
            text=full_text_str,
            language=info.language,
            language_probability=info.language_probability,
            duration_seconds=info.duration,
            segments=segments_list,
            word_timestamps=word_timestamps,
            confidence=info.language_probability,
            processing_time_ms=duration * 1000,
            request_id=request.request_id,
        )
    
    async def start_streaming(self, request: StreamStartRequest) -> StreamStartResponse:
        """Start a streaming transcription session."""
        session_id = uuid.uuid4()
        
        # Initialize streaming session state
        self._streaming_sessions[session_id] = {
            "user_id": request.user_id,
            "companion_id": request.companion_id,
            "language": request.language,
            "sample_rate": request.sample_rate,
            "buffer": np.array([], dtype=np.float32),
            "chunk_count": 0,
            "start_time": time.time(),
            "vad_state": "silence",
            "silence_duration": 0.0,
            "speech_started": False,
        }
        
        return StreamStartResponse(
            session_id=session_id,
            status="started",
            message="Streaming session started",
            config={
                "sample_rate": request.sample_rate,
                "language": request.language,
                "vad_threshold": self._vad_threshold,
            },
        )
    
    async def process_stream_chunk(self, request: StreamChunkRequest) -> StreamChunkResponse:
        """Process a streaming audio chunk."""
        session = self._streaming_sessions.get(request.session_id)
        if not session:
            return StreamChunkResponse(
                session_id=request.session_id,
                chunk_index=request.chunk_index,
                is_final=True,
                interruption_detected=False,
            )
        
        # Decode audio chunk
        audio_data = base64.b64decode(request.audio_data)
        audio_io = io.BytesIO(audio_data)
        chunk_array, _ = sf.read(audio_io)
        
        if len(chunk_array.shape) > 1:
            chunk_array = np.mean(chunk_array, axis=1)
        
        # Resample if needed
        if session["sample_rate"] != 16000:
            chunk_array = self._resample(chunk_array, session["sample_rate"], 16000)
        
        # Add to buffer
        session["buffer"] = np.concatenate([session["buffer"], chunk_array.astype(np.float32)])
        session["chunk_count"] += 1
        
        # Simple VAD - check if speech is present
        energy = np.mean(chunk_array ** 2)
        is_speech = energy > self._vad_threshold * 0.01  # Simplified threshold
        
        transcript = None
        is_final = request.is_final
        confidence = None
        vad_prob = float(is_speech)
        interruption = False
        
        # Process if we have enough audio or it's the final chunk
        buffer_duration = len(session["buffer"]) / 16000
        
        if buffer_duration >= 2.0 or request.is_final:
            # Transcribe buffer
            segments, info = self.model.transcribe(
                session["buffer"],
                language=session["language"],
                task="transcribe",
                beam_size=1,  # Faster for streaming
                vad_filter=True,
            )
            
            segment_texts = []
            for segment in segments:
                segment_texts.append(segment.text)
            
            transcript = " ".join(segment_texts).strip()
            confidence = info.language_probability if transcript else 0.0
            
            # Clear buffer if not final (keep last 0.5s for context)
            if not request.is_final:
                keep_samples = int(0.5 * 16000)
                if len(session["buffer"]) > keep_samples:
                    session["buffer"] = session["buffer"][-keep_samples:]
            else:
                session["buffer"] = np.array([], dtype=np.float32)
        
        if request.is_final:
            # Clean up session
            del self._streaming_sessions[request.session_id]
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
    
    async def end_streaming(self, session_id: uuid.UUID, reason: str = "completed") -> StreamEndResponse:
        """End a streaming session and return final transcript."""
        session = self._streaming_sessions.get(session_id)
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
        final_transcript = ""
        avg_confidence = 0.0
        
        if len(session["buffer"]) > 0:
            segments, info = self.model.transcribe(
                session["buffer"],
                language=session["language"],
                task="transcribe",
            )
            segment_texts = [s.text for s in segments]
            final_transcript = " ".join(segment_texts).strip()
            avg_confidence = info.language_probability
        
        duration = time.time() - session["start_time"]
        total_chunks = session["chunk_count"]
        
        del self._streaming_sessions[session_id]
        
        return StreamEndResponse(
            session_id=session_id,
            status=reason,
            full_transcript=final_transcript,
            total_duration_seconds=duration,
            total_chunks=total_chunks,
            average_confidence=avg_confidence,
        )
    
    def _resample(self, audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """Resample audio to target sample rate."""
        if orig_sr == target_sr:
            return audio
        
        # Simple linear interpolation resampling
        ratio = target_sr / orig_sr
        new_length = int(len(audio) * ratio)
        indices = np.linspace(0, len(audio) - 1, new_length)
        return np.interp(indices, np.arange(len(audio)), audio).astype(np.float32)
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for STT service."""
        return {
            "model_loaded": self.model is not None,
            "model_name": self.model_name,
            "device": self.device,
            "active_sessions": len(self._streaming_sessions),
        }
    
    async def close(self) -> None:
        """Cleanup resources."""
        self._streaming_sessions.clear()
        self.model = None
        logger.info("STT service closed")


# Singleton instance
_stt_service: Optional[STTService] = None


async def get_stt_service() -> STTService:
    """Get or create STT service singleton."""
    global _stt_service
    if _stt_service is None:
        _stt_service = STTService()
        await _stt_service.initialize()
    return _stt_service


async def close_stt_service() -> None:
    """Close STT service."""
    global _stt_service
    if _stt_service:
        await _stt_service.close()
        _stt_service = None