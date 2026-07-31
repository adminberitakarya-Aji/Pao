"""Text-to-Speech Service using Kokoro and XTTS."""

import asyncio
import base64
import io
import logging
import time
import uuid
from typing import Optional, Dict, Any, AsyncGenerator
from pathlib import Path

import numpy as np
import soundfile as sf

from voice_engine.config import settings
from voice_engine.models.requests import SynthesizeRequest
from voice_engine.models.responses import SynthesizeResponse

logger = logging.getLogger(__name__)


class TTSService:
    """Text-to-Speech service supporting Kokoro and XTTS engines."""
    
    def __init__(self):
        self.kokoro_model = None
        self.xtts_model = None
        self.kokoro_voice_map = {}
        self.xtts_speakers = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize TTS models."""
        logger.info("Initializing TTS services")
        
        try:
            # Initialize Kokoro
            if settings.tts_kokoro_model_path:
                await self._init_kokoro()
            
            # Initialize XTTS
            if settings.tts_xtts_model_path:
                await self._init_xtts()
            
            self._initialized = True
            logger.info("TTS services initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize TTS services", error=str(e))
            raise
    
    async def _init_kokoro(self) -> None:
        """Initialize Kokoro TTS model."""
        try:
            from kokoro_onnx import Kokoro
            
            model_path = settings.tts_kokoro_model_path
            voices_path = settings.tts_kokoro_voices_path
            
            self.kokoro_model = Kokoro(
                model_path=str(model_path),
                voices_path=str(voices_path) if voices_path else None
            )
            
            # Load available voices
            self.kokoro_voice_map = self.kokoro_model.get_voices()
            logger.info("Kokoro model loaded", voices=list(self.kokoro_voice_map.keys()))
            
        except ImportError:
            logger.warning("kokoro-onnx not installed, Kokoro TTS unavailable")
        except Exception as e:
            logger.error("Failed to initialize Kokoro", error=str(e))
            raise
    
    async def _init_xtts(self) -> None:
        """Initialize XTTS v2 model."""
        try:
            from TTS.api import TTS
            
            self.xtts_model = TTS(
                model_name=settings.tts_xtts_model_path,
                progress_bar=False,
                gpu=settings.tts_device == "cuda"
            )
            
            # Get available speakers
            self.xtts_speakers = self.xtts_model.speakers or {}
            logger.info("XTTS model loaded", speakers=list(self.xtts_speakers.keys()))
            
        except ImportError:
            logger.warning("TTS (Coqui) not installed, XTTS unavailable")
        except Exception as e:
            logger.error("Failed to initialize XTTS", error=str(e))
            raise
    
    async def synthesize(self, request: SynthesizeRequest) -> SynthesizeResponse:
        """Synthesize text to speech."""
        start_time = time.time()
        
        if request.engine == "kokoro":
            return await self._synthesize_kokoro(request, start_time)
        elif request.engine == "xtts":
            return await self._synthesize_xtts(request, start_time)
        else:
            raise ValueError(f"Unknown TTS engine: {request.engine}")
    
    async def _synthesize_kokoro(self, request: SynthesizeRequest, start_time: float) -> SynthesizeResponse:
        """Synthesize using Kokoro."""
        if not self.kokoro_model:
            raise RuntimeError("Kokoro model not initialized")
        
        voice_id = request.voice_id or "af_heart"  # Default voice
        
        if voice_id not in self.kokoro_voice_map:
            logger.warning("Voice not found, using default", voice=voice_id)
            voice_id = "af_heart"
        
        # Generate audio
        samples, sample_rate = self.kokoro_model.create(
            text=request.text,
            voice=voice_id,
            speed=request.speed,
        )
        
        # Apply pitch and volume adjustments
        if request.pitch != 1.0:
            samples = self._adjust_pitch(samples, request.pitch, sample_rate)
        
        if request.volume != 1.0:
            samples = samples * request.volume
        
        # Normalize if enabled
        if settings.audio_normalize:
            samples = self._normalize_audio(samples, settings.audio_target_lufs)
        
        # Convert to bytes
        audio_bytes = self._samples_to_bytes(samples, sample_rate)
        audio_base64 = base64.b64encode(audio_bytes).decode()
        
        duration = len(samples) / sample_rate
        processing_time = (time.time() - start_time) * 1000
        
        return SynthesizeResponse(
            user_id=request.user_id,
            companion_id=request.companion_id,
            audio_data=audio_base64,
            audio_format="wav",
            sample_rate=sample_rate,
            duration_seconds=duration,
            engine="kokoro",
            voice_id=voice_id,
            processing_time_ms=processing_time,
            request_id=request.request_id,
        )
    
    async def _synthesize_xtts(self, request: SynthesizeRequest, start_time: float) -> SynthesizeResponse:
        """Synthesize using XTTS v2."""
        if not self.xtts_model:
            raise RuntimeError("XTTS model not initialized")
        
        speaker_wav = request.voice_id or settings.tts_xtts_speaker_wav
        
        # Generate audio
        samples = self.xtts_model.tts(
            text=request.text,
            speaker_wav=speaker_wav,
            language=request.language or "en",
            speed=request.speed,
        )
        
        sample_rate = settings.tts_sample_rate
        samples = np.array(samples, dtype=np.float32)
        
        # Apply pitch and volume adjustments
        if request.pitch != 1.0:
            samples = self._adjust_pitch_xtts(samples, request.pitch)
        
        if request.volume != 1.0:
            samples = samples * request.volume
        
        # Normalize
        if settings.audio_normalize:
            samples = self._normalize_audio(samples, settings.audio_target_lufs)
        
        # Convert to bytes
        audio_bytes = self._samples_to_bytes(samples, sample_rate)
        audio_base64 = base64.b64encode(audio_bytes).decode()
        
        duration = len(samples) / sample_rate
        processing_time = (time.time() - start_time) * 1000
        
        return SynthesizeResponse(
            user_id=request.user_id,
            companion_id=request.companion_id,
            audio_data=audio_base64,
            audio_format="wav",
            sample_rate=sample_rate,
            duration_seconds=duration,
            engine="xtts",
            voice_id=speaker_wav,
            processing_time_ms=processing_time,
            request_id=request.request_id,
        )
    
    async def stream_synthesize(
        self,
        request: SynthesizeRequest,
        chunk_size: int = 1024
    ) -> AsyncGenerator[bytes, None]:
        """Stream synthesized audio in chunks."""
        # For streaming, we synthesize in chunks
        # This is a simplified implementation - real streaming would use
        # incremental generation from the TTS model
        
        response = await self.synthesize(request)
        audio_data = base64.b64decode(response.audio_data)
        
        # Stream in chunks
        for i in range(0, len(audio_data), chunk_size):
            yield audio_data[i:i + chunk_size]
            await asyncio.sleep(0.01)  # Small delay to simulate streaming
    
    def _samples_to_bytes(self, samples: np.ndarray, sample_rate: int) -> bytes:
        """Convert numpy samples to WAV bytes."""
        buffer = io.BytesIO()
        sf.write(buffer, samples, sample_rate, format='WAV', subtype='PCM_16')
        return buffer.getvalue()
    
    def _adjust_pitch(self, samples: np.ndarray, pitch_factor: float, sample_rate: int) -> np.ndarray:
        """Adjust pitch using simple resampling."""
        if pitch_factor == 1.0:
            return samples
        
        # Resample to change pitch
        original_length = len(samples)
        new_length = int(original_length / pitch_factor)
        
        # Simple approach - just stretch/compress
        indices = np.linspace(0, original_length - 1, new_length)
        return np.interp(indices, np.arange(original_length), samples).astype(np.float32)
    
    def _adjust_pitch_xtts(self, samples: np.ndarray, pitch_factor: float) -> np.ndarray:
        """Adjust pitch for XTTS output."""
        return self._adjust_pitch(samples, pitch_factor, settings.tts_sample_rate)
    
    def _normalize_audio(self, samples: np.ndarray, target_lufs: float = -23.0) -> np.ndarray:
        """Normalize audio to target LUFS."""
        # Simple RMS normalization (approximation of LUFS)
        rms = np.sqrt(np.mean(samples ** 2))
        if rms > 0:
            target_rms = 10 ** (target_lufs / 20)
            gain = target_rms / rms
            # Limit gain to avoid clipping
            gain = min(gain, 3.0)
            samples = samples * gain
        
        # Hard limit
        samples = np.clip(samples, -1.0, 1.0)
        return samples
    
    async def get_voices(self, engine: str = "kokoro") -> Dict[str, Any]:
        """Get available voices for an engine."""
        if engine == "kokoro":
            return {
                "engine": "kokoro",
                "voices": [
                    {"id": vid, "name": vid, "language": "en", "gender": "neutral"}
                    for vid in self.kokoro_voice_map.keys()
                ]
            }
        elif engine == "xtts":
            return {
                "engine": "xtts",
                "speakers": list(self.xtts_speakers.keys())
            }
        return {"engine": engine, "voices": []}
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for TTS service."""
        return {
            "initialized": self._initialized,
            "kokoro_available": self.kokoro_model is not None,
            "xtts_available": self.xtts_model is not None,
            "kokoro_voices": len(self.kokoro_voice_map),
            "xtts_speakers": len(self.xtts_speakers),
        }
    
    async def close(self) -> None:
        """Cleanup resources."""
        self.kokoro_model = None
        self.xtts_model = None
        self.kokoro_voice_map.clear()
        self.xtts_speakers.clear()
        self._initialized = False
        logger.info("TTS service closed")


# Singleton instance
_tts_service: Optional[TTSService] = None


async def get_tts_service() -> TTSService:
    """Get or create TTS service singleton."""
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
        await _tts_service.initialize()
    return _tts_service


async def close_tts_service() -> None:
    """Close TTS service."""
    global _tts_service
    if _tts_service:
        await _tts_service.close()
        _tts_service = None