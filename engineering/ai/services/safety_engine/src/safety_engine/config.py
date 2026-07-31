"""
Safety Engine Configuration.

Manages all configuration settings for the Safety Engine including
model paths, thresholds, database connections, and external service endpoints.
"""

from functools import lru_cache
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Service
    service_name: str = "safety-engine"
    service_port: int = 8005
    log_level: str = "INFO"
    environment: str = "development"
    
    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/pao_safety",
        description="PostgreSQL connection URL"
    )
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/1",
        description="Redis connection URL for caching"
    )
    redis_max_connections: int = 50
    
    # Model Configuration
    crisis_model_path: str = Field(
        default="models/crisis_detector",
        description="Path to crisis detection model"
    )
    content_filter_model_path: str = Field(
        default="models/content_filter",
        description="Path to content filter model"
    )
    behavioral_guard_model_path: str = Field(
        default="models/behavioral_guard",
        description="Path to behavioral guard model"
    )
    use_local_models: bool = True
    model_device: str = "cpu"  # cpu, cuda, mps
    model_precision: str = "float16"  # float32, float16, int8
    
    # Crisis Detection Thresholds
    crisis_threshold_high: float = 0.95
    crisis_threshold_medium: float = 0.80
    crisis_threshold_low: float = 0.60
    crisis_keywords: List[str] = Field(
        default=[
            "suicide", "kill myself", "end my life", "want to die",
            "self-harm", "hurt myself", "cutting", "overdose",
            "no reason to live", "better off dead"
        ],
        description="Keywords that trigger immediate crisis response"
    )
    
    # Content Filter Thresholds
    content_filter_thresholds: dict = Field(
        default={
            "hate": 0.85,
            "harassment": 0.80,
            "sexual": 0.90,
            "violence": 0.85,
            "illegal": 0.90,
            "medical": 0.80,
            "financial": 0.85,
            "pii": 0.95,
        },
        description="Thresholds for each content category"
    )
    pii_patterns: List[str] = Field(
        default=[
            r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
            r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",  # Credit card
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
            r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",  # Phone
        ],
        description="Regex patterns for PII detection"
    )
    
    # Behavioral Guards
    behavioral_check_enabled: bool = True
    manipulation_threshold: float = 0.75
    dependency_threshold: float = 0.70
    enmeshment_threshold: float = 0.65
    gaslighting_threshold: float = 0.70
    authority_threshold: float = 0.75
    
    # Reality Anchor
    reality_anchor_enabled: bool = True
    reality_anchor_triggers: List[str] = Field(
        default=[
            "delusion", "hallucination", "paranoid", "conspiracy",
            "not real", "fake reality", "simulation", "matrix",
            "voices telling me", "god told me", "aliens"
        ],
        description="Triggers for reality anchor injection"
    )
    reality_anchor_templates: List[str] = Field(
        default=[
            "I'm here to support you. What you're experiencing sounds difficult. "
            "Would you like to talk about what's on your mind?",
            "I care about your wellbeing. Sometimes our minds can play tricks on us. "
            "You're not alone in this.",
            "That sounds really challenging. Remember, I'm an AI companion here to help. "
            "If you're feeling overwhelmed, consider reaching out to a trusted person or professional."
        ],
        description="Templates for reality anchor responses"
    )
    
    # Intervention Levels
    intervention_levels: dict = Field(
        default={
            0: "allow",           # No intervention needed
            1: "gentle_redirect", # Soft topic change
            2: "firm_boundary",   # Clear boundary setting
            3: "resource_provide", # Provide help resources
            4: "crisis_escalate", # Immediate crisis response
        },
        description="Intervention level definitions"
    )
    
    # Crisis Resources
    crisis_resources: dict = Field(
        default={
            "US": {
                "phone": "988",
                "text": "HOME to 741741",
                "name": "988 Suicide & Crisis Lifeline"
            },
            "UK": {
                "phone": "116 123",
                "name": "Samaritans"
            },
            "CA": {
                "phone": "988",
                "name": "Canada Suicide Prevention Service"
            },
            "AU": {
                "phone": "13 11 14",
                "name": "Lifeline Australia"
            },
            "international": {
                "url": "https://findahelpline.com/",
                "name": "Find A Helpline"
            }
        },
        description="Crisis resources by country"
    )
    
    # Inference Gateway
    inference_gateway_url: str = "http://inference-gateway:8000"
    inference_timeout: float = 30.0
    
    # Embedding Service
    embedding_service_url: str = "http://embedding-service:8001"
    embedding_timeout: float = 10.0
    
    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_safety_topic: str = "safety.alerts"
    kafka_consumer_group: str = "safety-engine"
    
    # Temporal
    temporal_address: str = "localhost:7233"
    temporal_namespace: str = "default"
    
    # Monitoring
    metrics_enabled: bool = True
    metrics_port: int = 9090
    tracing_enabled: bool = True
    tracing_sample_rate: float = 0.1
    otlp_endpoint: str = "http://otel-collector:4317"
    
    # Security
    api_key: Optional[str] = None
    jwt_secret: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        valid_envs = ["development", "staging", "production", "test"]
        if v.lower() not in valid_envs:
            raise ValueError(f"environment must be one of {valid_envs}")
        return v.lower()
    
    @field_validator("model_precision")
    @classmethod
    def validate_model_precision(cls, v: str) -> str:
        valid_precision = ["float32", "float16", "int8", "bfloat16"]
        if v.lower() not in valid_precision:
            raise ValueError(f"model_precision must be one of {valid_precision}")
        return v.lower()


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()