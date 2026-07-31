"""Companion Runtime Configuration."""

from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "companion-runtime"
    version: str = "0.1.0"
    environment: str = Field(default="development", description="Environment: development, staging, production")
    debug: bool = Field(default=True, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")

    # Database (PostgreSQL for checkpointing)
    database_url: str = Field(
        default="postgresql+asyncpg://pao:pao@localhost:5432/companion_runtime",
        description="PostgreSQL connection URL for checkpointing",
    )
    database_pool_size: int = Field(default=10, description="Database connection pool size")
    database_max_overflow: int = Field(default=20, description="Database max overflow connections")

    # Redis (for session management, caching)
    redis_url: str = Field(default="redis://localhost:6379/1", description="Redis connection URL")
    redis_max_connections: int = Field(default=50, description="Redis max connections")

    # Engine URLs
    inference_gateway_url: str = Field(
        default="http://localhost:8000",
        description="Inference Gateway URL",
    )
    identity_engine_url: str = Field(
        default="http://localhost:8003",
        description="Identity Engine URL",
    )
    memory_engine_url: str = Field(
        default="http://localhost:8004",
        description="Memory Engine URL",
    )
    safety_engine_url: str = Field(
        default="http://localhost:8005",
        description="Safety Engine URL",
    )
    relationship_engine_url: str = Field(
        default="http://localhost:8006",
        description="Relationship Engine URL",
    )
    emotion_engine_url: str = Field(
        default="http://localhost:8007",
        description="Emotion Engine URL",
    )
    voice_engine_url: str = Field(
        default="http://localhost:8008",
        description="Voice Engine URL",
    )
    proactive_engine_url: str = Field(
        default="http://localhost:8009",
        description="Proactive Engine URL",
    )
    evaluation_engine_url: str = Field(
        default="http://localhost:8010",
        description="Evaluation Engine URL",
    )

    # HTTP Client
    http_timeout: float = Field(default=30.0, description="HTTP client timeout in seconds")
    http_max_connections: int = Field(default=100, description="HTTP client max connections")
    http_max_keepalive: int = Field(default=20, description="HTTP client max keepalive connections")

    # LangGraph
    langgraph_checkpoint_interval: int = Field(
        default=10,
        description="Checkpoint every N messages",
    )
    langgraph_recursion_limit: int = Field(
        default=50,
        description="Maximum recursion depth for graph execution",
    )

    # Circuit Breaker
    circuit_breaker_failure_threshold: int = Field(default=5, description="Circuit breaker failure threshold")
    circuit_breaker_recovery_timeout: int = Field(default=30, description="Circuit breaker recovery timeout in seconds")

    # Tracing
    tracing_enabled: bool = Field(default=True, description="Enable distributed tracing")
    tracing_sample_rate: float = Field(default=0.1, description="Tracing sample rate")
    otlp_endpoint: Optional[str] = Field(default=None, description="OTLP endpoint for tracing")

    # Metrics
    metrics_enabled: bool = Field(default=True, description="Enable Prometheus metrics")
    metrics_port: int = Field(default=9090, description="Metrics port")

    # Safety (cross-cutting)
    safety_strict_mode: bool = Field(default=True, description="Strict safety mode - block on any violation")
    safety_pre_check_enabled: bool = Field(default=True, description="Enable pre-check on user input")
    safety_post_check_enabled: bool = Field(default=True, description="Enable post-check on model output")

    # Streaming
    streaming_enabled: bool = Field(default=True, description="Enable streaming responses")
    streaming_chunk_size: int = Field(default=100, description="Streaming chunk size in tokens")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()