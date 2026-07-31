"""Configuration for Voice Engine."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    environment: str = "development"
    log_level: str = "INFO"
    port: int = 8008

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/voice_engine"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_timeout: int = 30

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 50

    # STT (Speech-to-Text) - Whisper
    stt_model_name: str = "large-v3"
    stt_model_path: Optional[str] = None
    stt_device: str = "cuda"
    stt_compute_type: str = "float16"
    stt_beam_size: int = 5
    stt_language: Optional[str] = None
    stt_vad_filter: bool = True
    stt_vad_threshold: float = 0.5

    # TTS (Text-to-Speech) - Kokoro/XTTS
    tts_default_engine: str = "kokoro"  # or "xtts"
    tts_kokoro_model_path: Optional[str] = None
    tts_xtts_model_path: Optional[str] = None
    tts_xtts_speaker_wav: Optional[str] = None
    tts_sample_rate: int = 24000
    tts_device: str = "cuda"

    # Streaming
    streaming_chunk_size: int = 1024
    streaming_sample_rate: int = 16000
    streaming_channels: int = 1
    streaming_format: str = "pcm_s16le"
    max_stream_duration_seconds: int = 300

    # Interruption handling
    interruption_enabled: bool = True
    interruption_threshold: float = 0.3
    interruption_min_speech_duration: float = 0.5

    # Voice Activity Detection
    vad_model: str = "silero"
    vad_threshold: float = 0.5
    vad_min_speech_duration: float = 0.25
    vad_max_speech_duration: float = 30.0
    vad_min_silence_duration: float = 0.5

    # LiveKit Integration
    livekit_url: str = "ws://localhost:7880"
    livekit_api_key: str = "devkey"
    livekit_api_secret: str = "secret"
    livekit_egress_bucket: str = "pao-voice-recordings"

    # Audio processing
    audio_normalize: bool = True
    audio_target_lufs: float = -23.0
    audio_noise_reduction: bool = True

    # Metrics
    metrics_enabled: bool = True
    metrics_port: int = 9090

    # Tracing
    tracing_enabled: bool = False
    tracing_endpoint: str = "http://localhost:4317"
    tracing_sample_rate: float = 0.1

    # API
    api_timeout_seconds: float = 30.0
    api_max_retries: int = 3

    # Worker
    worker_concurrency: int = 2
    worker_poll_interval_seconds: float = 1.0


settings = Settings()