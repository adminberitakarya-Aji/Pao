"""Configuration settings for Relationship Engine."""

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

    # Service
    service_name: str = "relationship_engine"
    port: int = 8006
    environment: str = "development"
    log_level: str = "INFO"

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/pao",
        description="PostgreSQL connection URL",
    )
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Kuzu Graph Database
    kuzu_path: str = "/var/lib/kuzu/relationship"
    kuzu_read_only: bool = False

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )
    redis_max_connections: int = 50

    # Auth
    jwt_secret_key: str = Field(
        default="dev-secret-change-in-production",
        description="JWT secret key for token signing",
    )
    jwt_algorithm: str = "RS256"
    jwt_audience: str = "pao-ai-services"
    jwt_issuer: str = "pao-auth"
    service_tokens: dict[str, str] = Field(
        default_factory=dict,
        description="Service-to-service authentication tokens",
    )

    # Relationship dimensions
    dimensions: list[str] = Field(
        default=[
            "trust",
            "intimacy",
            "affection",
            "respect",
            "commitment",
            "communication",
            "shared_values",
            "support",
            "playfulness",
            "growth",
        ],
        description="Relationship dimensions to track",
    )

    # Phase thresholds (dimension score ranges 0-10)
    phase_thresholds: dict[str, dict[str, float]] = Field(
        default={
            "stranger": {"min": 0.0, "max": 1.5},
            "acquaintance": {"min": 1.5, "max": 3.0},
            "friend": {"min": 3.0, "max": 5.0},
            "close_friend": {"min": 5.0, "max": 7.0},
            "partner": {"min": 7.0, "max": 8.5},
            "soulmate": {"min": 8.5, "max": 10.0},
        },
        description="Relationship phase thresholds by dimension score",
    )

    # Milestone configuration
    milestones_config: dict[str, dict] = Field(
        default={
            "first_conversation": {"trigger": "message_count", "threshold": 1},
            "first_day": {"trigger": "days_known", "threshold": 1},
            "first_week": {"trigger": "days_known", "threshold": 7},
            "first_month": {"trigger": "days_known", "threshold": 30},
            "hundred_messages": {"trigger": "message_count", "threshold": 100},
            "thousand_messages": {"trigger": "message_count", "threshold": 1000},
            "first_voice_call": {"trigger": "voice_calls", "threshold": 1},
            "first_memory_shared": {"trigger": "memories_shared", "threshold": 1},
            "trust_5": {"trigger": "dimension_trust", "threshold": 5.0},
            "intimacy_5": {"trigger": "dimension_intimacy", "threshold": 5.0},
            "phase_friend": {"trigger": "phase", "threshold": "friend"},
            "phase_close_friend": {"trigger": "phase", "threshold": "close_friend"},
            "phase_partner": {"trigger": "phase", "threshold": "partner"},
            "phase_soulmate": {"trigger": "phase", "threshold": "soulmate"},
        },
        description="Milestone definitions with triggers and thresholds",
    )

    # Diary configuration
    diary_enabled: bool = True
    diary_max_entries_per_day: int = 10
    diary_auto_generate: bool = True
    diary_generation_interval_hours: int = 24

    # State machine
    state_machine_enabled: bool = True
    state_transition_cooldown_hours: int = 1

    # External services
    identity_engine_url: str = "http://identity-engine:8003"
    memory_engine_url: str = "http://memory-engine:8004"
    safety_engine_url: str = "http://safety-engine:8005"
    emotion_engine_url: str = "http://emotion-engine:8007"

    # HTTP client settings
    http_timeout_seconds: float = 30.0
    http_max_connections: int = 100
    http_max_keepalive: int = 20

    # Observability
    otel_exporter_otlp_endpoint: str = "http://otel-collector:4317"
    otel_service_name: str = "relationship-engine"
    metrics_enabled: bool = True
    tracing_enabled: bool = True

    # Feature flags
    dimensions_tracking_enabled: bool = True
    milestones_enabled: bool = True
    diary_enabled: bool = True
    state_machine_enabled: bool = True


settings = Settings()