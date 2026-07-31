"""Configuration for Proactive Engine."""

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

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
    app_name: str = "proactive-engine"
    version: str = "0.1.0"
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    port: int = Field(default=8009, alias="PORT")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/pao_proactive",
        alias="DATABASE_URL",
    )
    database_pool_size: int = Field(default=10, alias="DB_POOL_SIZE")
    database_max_overflow: int = Field(default=20, alias="DB_MAX_OVERFLOW")
    database_pool_timeout: int = Field(default=30, alias="DB_POOL_TIMEOUT")

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        alias="REDIS_URL",
    )
    redis_max_connections: int = Field(default=50, alias="REDIS_MAX_CONNECTIONS")
    redis_socket_timeout: int = Field(default=5, alias="REDIS_SOCKET_TIMEOUT")
    redis_socket_connect_timeout: int = Field(default=5, alias="REDIS_SOCKET_CONNECT_TIMEOUT")

    # Model Configuration
    model_cache_dir: str = Field(default="/app/models", alias="MODEL_CACHE_DIR")
    device: str = Field(default="cpu", alias="DEVICE")  # cpu, cuda, mps
    
    # Proactivity Models
    initiative_model_name: str = Field(default="microsoft/DialoGPT-medium", alias="INITIATIVE_MODEL_NAME")
    initiative_model_path: Optional[str] = Field(default=None, alias="INITIATIVE_MODEL_PATH")
    anticipation_model_name: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", alias="ANTICIPATION_MODEL_NAME")
    anticipation_model_path: Optional[str] = Field(default=None, alias="ANTICIPATION_MODEL_PATH")
    suggestion_model_name: str = Field(default="google/flan-t5-base", alias="SUGGESTION_MODEL_NAME")
    suggestion_model_path: Optional[str] = Field(default=None, alias="SUGGESTION_MODEL_PATH")
    
    # Scheduling
    scheduler_enabled: bool = Field(default=True, alias="SCHEDULER_ENABLED")
    scheduler_timezone: str = Field(default="UTC", alias="SCHEDULER_TIMEZONE")
    check_interval_seconds: int = Field(default=60, alias="CHECK_INTERVAL_SECONDS")
    
    # Proactivity Triggers
    trigger_threshold: float = Field(default=0.7, alias="TRIGGER_THRESHOLD")
    max_proactive_actions_per_hour: int = Field(default=10, alias="MAX_PROACTIVE_ACTIONS_PER_HOUR")
    cooldown_minutes: int = Field(default=30, alias="COOLDOWN_MINUTES")
    
    # Context Awareness
    context_window_size: int = Field(default=10, alias="CONTEXT_WINDOW_SIZE")
    relevance_threshold: float = Field(default=0.6, alias="RELEVANCE_THRESHOLD")
    max_context_age_hours: int = Field(default=24, alias="MAX_CONTEXT_AGE_HOURS")
    
    # Personality & Style
    proactivity_level: float = Field(default=0.5, alias="PROACTIVITY_LEVEL")  # 0-1
    initiative_style: str = Field(default="balanced", alias="INITIATIVE_STYLE")  # subtle, balanced, bold
    user_preference_weight: float = Field(default=0.8, alias="USER_PREFERENCE_WEIGHT")
    
    # Service URLs
    identity_engine_url: str = Field(default="http://localhost:8003", alias="IDENTITY_ENGINE_URL")
    memory_engine_url: str = Field(default="http://localhost:8004", alias="MEMORY_ENGINE_URL")
    emotion_engine_url: str = Field(default="http://localhost:8007", alias="EMOTION_ENGINE_URL")
    relationship_engine_url: str = Field(default="http://localhost:8006", alias="RELATIONSHIP_ENGINE_URL")
    voice_engine_url: str = Field(default="http://localhost:8008", alias="VOICE_ENGINE_URL")
    
    # HTTP Client
    http_timeout: float = Field(default=30.0, alias="HTTP_TIMEOUT")
    http_max_retries: int = Field(default=3, alias="HTTP_MAX_RETRIES")
    http_backoff_factor: float = Field(default=0.5, alias="HTTP_BACKOFF_FACTOR")
    
    # Caching
    cache_ttl_seconds: int = Field(default=300, alias="CACHE_TTL_SECONDS")
    cache_max_size: int = Field(default=10000, alias="CACHE_MAX_SIZE")
    
    # Metrics
    metrics_enabled: bool = Field(default=True, alias="METRICS_ENABLED")
    metrics_port: int = Field(default=9090, alias="METRICS_PORT")
    metrics_path: str = Field(default="/metrics", alias="METRICS_PATH")
    
    # Tracing
    tracing_enabled: bool = Field(default=True, alias="TRACING_ENABLED")
    jaeger_agent_host: str = Field(default="localhost", alias="JAEGER_AGENT_HOST")
    jaeger_agent_port: int = Field(default=6831, alias="JAEGER_AGENT_PORT")
    otlp_endpoint: Optional[str] = Field(default=None, alias="OTLP_ENDPOINT")
    
    # Performance
    max_batch_size: int = Field(default=32, alias="MAX_BATCH_SIZE")
    inference_timeout: float = Field(default=5.0, alias="INFERENCE_TIMEOUT")
    
    # Feature Flags
    enable_suggestions: bool = Field(default=True, alias="ENABLE_SUGGESTIONS")
    enable_reminders: bool = Field(default=True, alias="ENABLE_REMINDERS")
    enable_check_ins: bool = Field(default=True, alias="ENABLE_CHECK_INS")
    enable_anticipation: bool = Field(default=True, alias="ENABLE_ANTICIPATION")
    enable_scheduling: bool = Field(default=True, alias="ENABLE_SCHEDULING")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()