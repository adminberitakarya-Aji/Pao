"""Configuration for Emotion Engine."""

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
    app_name: str = "emotion-engine"
    version: str = "0.1.0"
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    port: int = Field(default=8007, alias="PORT")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/pao_emotion",
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
    
    # Emotion Classification Model
    emotion_model_name: str = Field(default="j-hartmann/emotion-english-distilroberta-base", alias="EMOTION_MODEL_NAME")
    emotion_model_path: Optional[str] = Field(default=None, alias="EMOTION_MODEL_PATH")
    emotion_labels: List[str] = Field(
        default=[
            "joy", "sadness", "anger", "fear", "surprise", "disgust", "neutral",
            "love", "optimism", "pessimism", "trust", "anticipation", "confusion"
        ],
        alias="EMOTION_LABELS",
    )
    
    # Valence-Arousal Model
    va_model_name: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", alias="VA_MODEL_NAME")
    va_model_path: Optional[str] = Field(default=None, alias="VA_MODEL_PATH")
    
    # Sentiment Analysis
    sentiment_model: str = Field(default="vader", alias="SENTIMENT_MODEL")  # vader, textblob, transformer
    sentiment_threshold: float = Field(default=0.05, alias="SENTIMENT_THRESHOLD")
    
    # Appraisal Model
    appraisal_model_name: str = Field(default="facebook/bart-large-mnli", alias="APPRAISAL_MODEL_NAME")
    appraisal_model_path: Optional[str] = Field(default=None, alias="APPRAISAL_MODEL_PATH")
    appraisal_candidates: List[str] = Field(
        default=[
            "goal_conduciveness", "goal_obstructiveness", "control", "lack_of_control",
            "agency_self", "agency_other", "certainty", "uncertainty",
            "expectedness", "unexpectedness", "effort_required", "no_effort",
            "pleasantness", "unpleasantness", "fairness", "unfairness",
            "self_responsibility", "other_responsibility", "situational_responsibility"
        ],
        alias="APPRAISAL_CANDIDATES",
    )
    
    # Expression Model
    expression_model_name: str = Field(default="gpt2", alias="EXPRESSION_MODEL_NAME")
    expression_model_path: Optional[str] = Field(default=None, alias="EXPRESSION_MODEL_PATH")
    expression_temperature: float = Field(default=0.7, alias="EXPRESSION_TEMPERATURE")
    expression_max_tokens: int = Field(default=100, alias="EXPRESSION_MAX_TOKENS")
    
    # Calibration
    calibration_enabled: bool = Field(default=True, alias="CALIBRATION_ENABLED")
    calibration_window: int = Field(default=100, alias="CALIBRATION_WINDOW")
    calibration_decay: float = Field(default=0.95, alias="CALIBRATION_DECAY")
    
    # Service URLs
    identity_engine_url: str = Field(default="http://localhost:8003", alias="IDENTITY_ENGINE_URL")
    memory_engine_url: str = Field(default="http://localhost:8004", alias="MEMORY_ENGINE_URL")
    safety_engine_url: str = Field(default="http://localhost:8005", alias="SAFETY_ENGINE_URL")
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
    
    # NLTK Data
    nltk_data_path: str = Field(default="/app/nltk_data", alias="NLTK_DATA_PATH")
    
    # Performance
    max_batch_size: int = Field(default=32, alias="MAX_BATCH_SIZE")
    inference_timeout: float = Field(default=5.0, alias="INFERENCE_TIMEOUT")
    
    # Feature Flags
    enable_appraisal: bool = Field(default=True, alias="ENABLE_APPRAISAL")
    enable_expression: bool = Field(default=True, alias="ENABLE_EXPRESSION")
    enable_calibration: bool = Field(default=True, alias="ENABLE_CALIBRATION")
    enable_real_time: bool = Field(default=True, alias="ENABLE_REAL_TIME")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()