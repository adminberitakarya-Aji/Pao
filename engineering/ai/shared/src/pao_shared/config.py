"""
PAO Shared Configuration
Centralized settings management using pydantic-settings.
"""

from functools import lru_cache
from typing import Optional, List
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
    environment: str = Field(default="development", description="Environment name")
    service_name: str = Field(default="pao-service", description="Service name for observability")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=1, description="Number of workers")
    
    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins"
    )
    
    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/pao",
        description="PostgreSQL connection URL"
    )
    database_pool_size: int = Field(default=10, description="Connection pool size")
    database_max_overflow: int = Field(default=20, description="Max overflow connections")
    
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    
    # Kafka
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        description="Kafka bootstrap servers"
    )
    
    # Observability
    otel_endpoint: str = Field(
        default="http://localhost:4317",
        description="OTEL collector endpoint"
    )
    otel_service_name: Optional[str] = Field(
        default=None,
        description="OTEL service name (defaults to service_name)"
    )
    enable_tracing: bool = Field(default=True, description="Enable distributed tracing")
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    
    # External APIs
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    
    # Vector DB
    qdrant_url: str = Field(default="http://localhost:6333", description="Qdrant URL")
    qdrant_api_key: Optional[str] = Field(default=None, description="Qdrant API key")
    
    # Auth
    jwt_secret: str = Field(
        default="change-me-in-production",
        description="JWT signing secret"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiry_minutes: int = Field(default=60, description="JWT token expiry in minutes")
    jwt_refresh_expiry_days: int = Field(default=30, description="JWT refresh token expiry in days")
    
    # Rate limiting
    rate_limit_requests: int = Field(default=100, description="Requests per window")
    rate_limit_window_seconds: int = Field(default=60, description="Rate limit window in seconds")
    
    # Feature flags
    enable_experimental_features: bool = Field(default=False, description="Enable experimental features")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()