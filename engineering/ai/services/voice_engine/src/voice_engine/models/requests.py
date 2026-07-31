"""Request models for Voice Engine API."""

from typing import Optional, List, Dict, Any, Literal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class TranscribeRequest(BaseModel):
    """Request to transcribe audio to text."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    audio_data: str = Field(..., description="Base64 encoded audio data")
    audio_format: Literal["wav", "mp3", "ogg", "webm", "pcm"] = "wav"
    sample_rate: int = Field(default=16000, ge=8000, le=48000)
    language: Optional[str] = None
    task: Literal["transcribe", "translate"] = "transcribe"
    vad_filter: bool = True
    word_timestamps: bool = False
    request_id: Optional[str] = None


class SynthesizeRequest(BaseModel):
    """Request to synthesize text to speech."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    text: str = Field(..., min_length=1, max_length=5000)
    engine: Literal["kokoro", "xtts"] = "kokoro"
    voice_id: Optional[str] = None
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=1.0, ge=0.5, le=2.0)
    volume: float = Field(default=1.0, ge=0.0, le=2.0)
    language: Optional[str] = None
    emotion: Optional[str] = None
    stream: bool = False
    request_id: Optional[str] = None


class StreamStartRequest(BaseModel):
    """Request to start a streaming audio session."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    session_id: UUID
    sample_rate: int = Field(default=16000, ge=8000, le=48000)
    channels: int = Field(default=1, ge=1, le=2)
    format: Literal["pcm_s16le", "pcm_f32le", "opus"] = "pcm_s16le"
    vad_enabled: bool = True
    interruption_enabled: bool = True


class StreamChunkRequest(BaseModel):
    """Request to send an audio chunk in a streaming session."""
    
    model_config = ConfigDict(extra="forbid")
    
    session_id: UUID
    chunk_index: int = Field(..., ge=0)
    audio_data: str = Field(..., description="Base64 encoded audio chunk")
    is_final: bool = False
    timestamp_ms: int = Field(..., ge=0)


class StreamEndRequest(BaseModel):
    """Request to end a streaming audio session."""
    
    model_config = ConfigDict(extra="forbid")
    
    session_id: UUID
    reason: Literal["completed", "interrupted", "error", "timeout"] = "completed"
    final_transcript: Optional[str] = None


class InterruptionRequest(BaseModel):
    """Request to handle user interruption during TTS playback."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    session_id: UUID
    interruption_point_ms: int = Field(..., ge=0)
    user_audio_data: Optional[str] = Field(None, description="Base64 encoded user audio that caused interruption")


class CallSetupRequest(BaseModel):
    """Request to set up a LiveKit voice call."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    room_name: str
    participant_identity: str
    participant_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    recording_enabled: bool = False
    egress_config: Optional[Dict[str, Any]] = None


class CallEndRequest(BaseModel):
    """Request to end a LiveKit voice call."""
    
    model_config = ConfigDict(extra="forbid")
    
    room_name: str
    reason: Literal["completed", "user_left", "error", "timeout"] = "completed"


class RecordingRequest(BaseModel):
    """Request to start/stop recording."""
    
    model_config = ConfigDict(extra="forbid")
    
    room_name: str
    action: Literal["start", "stop"]
    output_format: Literal["mp4", "webm", "ogg"] = "mp4"
    audio_only: bool = True


class VoiceConfigRequest(BaseModel):
    """Request to configure voice settings for a companion."""
    
    model_config = ConfigDict(extra="forbid")
    
    companion_id: UUID
    tts_engine: Literal["kokoro", "xtts"] = "kokoro"
    voice_id: Optional[str] = None
    default_speed: float = Field(default=1.0, ge=0.5, le=2.0)
    default_pitch: float = Field(default=1.0, ge=0.5, le=2.0)
    default_volume: float = Field(default=1.0, ge=0.0, le=2.0)
    default_language: Optional[str] = None
    emotion_mapping: Optional[Dict[str, Dict[str, float]]] = None
    interruption_sensitivity: float = Field(default=0.5, ge=0.0, le=1.0)
    vad_sensitivity: float = Field(default=0.5, ge=0.0, le=1.0)