"""Response models for Voice Engine API."""

from typing import Optional, List, Dict, Any, Literal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class TranscribeResponse(BaseModel):
    """Response from transcription."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    text: str
    language: str
    language_probability: float
    duration_seconds: float
    segments: List[Dict[str, Any]] = []
    word_timestamps: List[Dict[str, Any]] = []
    confidence: float
    processing_time_ms: float
    request_id: Optional[str] = None


class SynthesizeResponse(BaseModel):
    """Response from speech synthesis."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    audio_data: str = Field(..., description="Base64 encoded audio data")
    audio_format: str = "wav"
    sample_rate: int
    duration_seconds: float
    engine_used: str
    voice_id: Optional[str] = None
    processing_time_ms: float
    request_id: Optional[str] = None


class StreamStartResponse(BaseModel):
    """Response when starting a streaming session."""
    
    model_config = ConfigDict(extra="forbid")
    
    session_id: UUID
    status: Literal["started", "failed"] = "started"
    message: str = "Streaming session started"
    config: Dict[str, Any] = {}


class StreamChunkResponse(BaseModel):
    """Response for a streaming chunk."""
    
    model_config = ConfigDict(extra="forbid")
    
    session_id: UUID
    chunk_index: int
    transcript: Optional[str] = None
    is_final: bool = False
    confidence: Optional[float] = None
    vad_speech_probability: Optional[float] = None
    interruption_detected: bool = False


class StreamEndResponse(BaseModel):
    """Response when ending a streaming session."""
    
    model_config = ConfigDict(extra="forbid")
    
    session_id: UUID
    status: Literal["completed", "interrupted", "error", "timeout"]
    full_transcript: str
    total_duration_seconds: float
    total_chunks: int
    average_confidence: float


class InterruptionResponse(BaseModel):
    """Response to interruption handling."""
    
    model_config = ConfigDict(extra="forbid")
    
    session_id: UUID
    interruption_handled: bool
    interruption_point_ms: int
    tts_stopped: bool
    user_transcript: Optional[str] = None
    message: str = "Interruption processed"


class CallSetupResponse(BaseModel):
    """Response from call setup."""
    
    model_config = ConfigDict(extra="forbid")
    
    room_name: str
    token: str
    url: str
    participant_identity: str
    recording_started: bool = False
    egress_id: Optional[str] = None


class CallEndResponse(BaseModel):
    """Response from call end."""
    
    model_config = ConfigDict(extra="forbid")
    
    room_name: str
    status: Literal["completed", "user_left", "error", "timeout"]
    duration_seconds: float
    recording_url: Optional[str] = None
    message: str = "Call ended"


class RecordingResponse(BaseModel):
    """Response from recording action."""
    
    model_config = ConfigDict(extra="forbid")
    
    room_name: str
    action: Literal["started", "stopped", "failed"]
    egress_id: Optional[str] = None
    output_url: Optional[str] = None
    duration_seconds: Optional[float] = None
    file_size_bytes: Optional[int] = None


class VoiceConfigResponse(BaseModel):
    """Response with voice configuration."""
    
    model_config = ConfigDict(extra="forbid")
    
    companion_id: UUID
    tts_engine: str
    voice_id: Optional[str] = None
    default_speed: float
    default_pitch: float
    default_volume: float
    default_language: Optional[str] = None
    emotion_mapping: Optional[Dict[str, Dict[str, float]]] = None
    interruption_sensitivity: float
    vad_sensitivity: float
    updated_at: str


class HealthResponse(BaseModel):
    """Health check response."""
    
    model_config = ConfigDict(extra="forbid")
    
    service: str = "voice-engine"
    version: str = "0.1.0"
    status: Literal["healthy", "degraded", "unhealthy"] = "healthy"
    checks: Dict[str, bool] = {}
    stt_model_loaded: bool = False
    tts_model_loaded: bool = False
    livekit_connected: bool = False


class ErrorResponse(BaseModel):
    """Error response."""
    
    model_config = ConfigDict(extra="forbid")
    
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None