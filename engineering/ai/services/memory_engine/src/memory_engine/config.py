"""Memory Engine Configuration."""

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
    environment: str = Field(default="development", description="Environment: development, staging, production")
    log_level: str = Field(default="INFO", description="Logging level")
    service_name: str = Field(default="memory-engine", description="Service name for observability")
    port: int = Field(default=8004, description="Port to run the service on")
    
    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080", "*"],
        description="Allowed CORS origins"
    )
    
    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/pao_memory",
        description="PostgreSQL connection URL with pgvector"
    )
    database_pool_size: int = Field(default=20, description="Connection pool size")
    database_max_overflow: int = Field(default=10, description="Max overflow connections")
    
    # Qdrant (Vector Database)
    qdrant_url: str = Field(default="http://localhost:6333", description="Qdrant HTTP URL")
    qdrant_api_key: Optional[str] = Field(default=None, description="Qdrant API key (if auth enabled)")
    qdrant_grpc_port: int = Field(default=6334, description="Qdrant gRPC port")
    qdrant_prefer_grpc: bool = Field(default=False, description="Prefer gRPC over HTTP")
    qdrant_collection_prefix: str = Field(default="pao_memory", description="Collection name prefix")
    
    # Kuzu (Graph Database)
    kuzu_path: str = Field(default="/var/lib/kuzu/memory_engine", description="Kuzu database path")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    redis_max_connections: int = Field(default=50, description="Max Redis connections")
    redis_socket_timeout: float = Field(default=5.0, description="Socket timeout in seconds")
    redis_socket_connect_timeout: float = Field(default=5.0, description="Socket connect timeout in seconds")
    
    # Kafka
    kafka_bootstrap_servers: str = Field(default="localhost:9092", description="Kafka bootstrap servers")
    kafka_topics: dict = Field(
        default_factory=lambda: {
            "memory_consolidation": "memory.consolidation",
            "memory_events": "memory.events",
            "safety_alerts": "safety.alerts",
        },
        description="Kafka topics"
    )
    
    # Temporal
    temporal_address: str = Field(default="localhost:7233", description="Temporal server address")
    temporal_namespace: str = Field(default="default", description="Temporal namespace")
    
    # Embedding Service (for generating embeddings)
    embedding_service_url: str = Field(default="http://localhost:8001", description="Embedding service URL")
    embedding_dimension: int = Field(default=768, description="Embedding dimension")
    embedding_model: str = Field(default="bge-large-en-v1.5", description="Embedding model name")
    
    # Inference Gateway (for LLM calls)
    inference_gateway_url: str = Field(default="http://localhost:8000", description="Inference gateway URL")
    
    # Safety Engine
    safety_engine_url: str = Field(default="http://localhost:8005", description="Safety engine URL")
    
    # Identity Engine
    identity_engine_url: str = Field(default="http://localhost:8003", description="Identity engine URL")
    
    # Memory Engine Settings
    default_recall_limit: int = Field(default=10, description="Default recall limit")
    max_recall_limit: int = Field(default=100, description="Maximum recall limit")
    consolidation_batch_size: int = Field(default=50, description="Batch size for consolidation")
    consolidation_interval_hours: int = Field(default=24, description="Hours between consolidation runs")
    memory_ttl_days: dict = Field(
        default_factory=lambda: {
            "episodic": 730,      # 2 years
            "semantic": 1825,     # 5 years
            "emotional": 365,     # 1 year
            "relationship": 1825, # 5 years
            "timeline": 1825,     # 5 years
            "preference": 1825,   # 5 years
        },
        description="Default TTL in days per memory type"
    )
    importance_threshold: float = Field(default=0.3, description="Minimum importance for consolidation")
    contradiction_threshold: float = Field(default=0.8, description="Cosine similarity threshold for contradiction detection")
    
    # Caching
    redis_cache_ttl: int = Field(default=300, description="Redis cache TTL in seconds")
    recall_cache_ttl: int = Field(default=60, description="Recall result cache TTL")
    
    # Export
    export_max_memories: int = Field(default=10000, description="Max memories per export")
    export_formats: List[str] = Field(
        default=["json", "json-ld", "timeline", "audit_log"],
        description="Supported export formats"
    )
    
    # Metrics
    metrics_port: int = Field(default=9090, description="Prometheus metrics port")
    tracing_sample_rate: float = Field(default=0.1, description="Trace sampling rate (0-1)")
    
    # Security
    api_key: Optional[str] = Field(default=None, description="API key for service-to-service auth")
    internal_api_key: Optional[str] = Field(default=None, description="Internal API key")
    jwt_secret: Optional[str] = Field(default=None, description="JWT secret for token validation")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_audience: Optional[str] = Field(default=None, description="JWT audience")
    jwt_issuer: Optional[str] = Field(default=None, description="JWT issuer")
    
    # Feature Flags
    enable_consolidation: bool = Field(default=True, description="Enable automatic consolidation")
    enable_graph_queries: bool = Field(default=True, description="Enable Kuzu graph queries")
    enable_emotional_memory: bool = Field(default=True, description="Enable emotional memory type")
    enable_voice_memory: bool = Field(default=False, description="Enable voice memory storage (Phase 3)")
    

settings = Settings()