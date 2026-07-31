"""Evaluation Engine Configuration."""

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
    app_name: str = "evaluation-engine"
    version: str = "0.1.0"
    environment: str = Field(default="development", description="Environment: development, staging, production")
    debug: bool = Field(default=True, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8010, description="Server port")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://pao:pao@localhost:5432/evaluation",
        description="PostgreSQL connection URL",
    )
    database_pool_size: int = Field(default=10, description="Database connection pool size")
    database_max_overflow: int = Field(default=20, description="Database max overflow connections")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    redis_max_connections: int = Field(default=50, description="Redis max connections")

    # Qdrant
    qdrant_url: str = Field(default="http://localhost:6333", description="Qdrant connection URL")
    qdrant_api_key: Optional[str] = Field(default=None, description="Qdrant API key")
    qdrant_collection_prefix: str = Field(default="evaluation", description="Qdrant collection prefix")

    # HTTP Client
    http_timeout: float = Field(default=30.0, description="HTTP client timeout in seconds")
    http_max_connections: int = Field(default=100, description="HTTP client max connections")

    # RHI (Relationship Health Index) Configuration
    rhi_dimensions: list[str] = Field(
        default=["trust", "intimacy", "satisfaction", "safety", "growth"],
        description="RHI dimension names",
    )
    rhi_weights: dict[str, float] = Field(
        default={"trust": 0.25, "intimacy": 0.2, "satisfaction": 0.2, "safety": 0.2, "growth": 0.15},
        description="RHI dimension weights (must sum to 1.0)",
    )
    rhi_survey_correlation_threshold: float = Field(
        default=0.85,
        description="Minimum correlation with survey for validation",
    )

    # Drift Detection
    drift_detection_enabled: bool = Field(default=True, description="Enable drift detection")
    drift_check_interval_hours: int = Field(default=24, description="Drift check interval in hours")
    drift_threshold_zscore: float = Field(default=2.5, description="Z-score threshold for drift alerts")
    drift_min_samples: int = Field(default=30, description="Minimum samples for drift detection")

    # A/B Testing
    ab_test_enabled: bool = Field(default=True, description="Enable A/B testing")
    ab_test_min_sample_size: int = Field(default=100, description="Minimum sample size per variant")
    ab_test_significance_level: float = Field(default=0.05, description="Statistical significance level")
    ab_test_min_effect_size: float = Field(default=0.1, description="Minimum detectable effect size")

    # Survey Integration
    survey_integration_enabled: bool = Field(default=True, description="Enable survey integration")
    survey_schedule_cron: str = Field(default="0 9 * * 1", description="Survey schedule (cron expression)")
    survey_lookback_days: int = Field(default=30, description="Lookback period for survey correlation")

    # Metrics & Monitoring
    metrics_enabled: bool = Field(default=True, description="Enable Prometheus metrics")
    metrics_port: int = Field(default=9090, description="Metrics port")

    # Tracing
    tracing_enabled: bool = Field(default=True, description="Enable distributed tracing")
    tracing_sample_rate: float = Field(default=0.1, description="Tracing sample rate")
    otlp_endpoint: Optional[str] = Field(default=None, description="OTLP endpoint for tracing")

    # External Services
    inference_gateway_url: str = Field(
        default="http://localhost:8000",
        description="Inference Gateway URL",
    )
    memory_engine_url: str = Field(
        default="http://localhost:8004",
        description="Memory Engine URL",
    )
    relationship_engine_url: str = Field(
        default="http://localhost:8006",
        description="Relationship Engine URL",
    )
    proactive_engine_url: str = Field(
        default="http://localhost:8009",
        description="Proactive Engine URL",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()