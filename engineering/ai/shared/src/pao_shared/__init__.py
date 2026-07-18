"""
PAO Shared Python Library
Common utilities, config, models, and observability for PAO AI services.
"""

from .config import get_settings, Settings
from .models import (
    TaskType,
    ModelProvider,
    ModelConfig,
    InferenceRequest,
    InferenceResponse,
    StreamChunk,
    EmbeddingRequest,
    EmbeddingResponse,
    HealthResponse,
    ErrorResponse,
)
from .observability import (
    setup_tracing,
    setup_metrics,
    setup_logging,
    REQUEST_COUNT,
    REQUEST_LATENCY,
    ACTIVE_REQUESTS,
    MODEL_INFERENCE_COUNT,
    MODEL_INFERENCE_LATENCY,
    MODEL_TOKENS_USED,
    MODEL_COST_ESTIMATE,
    ERROR_COUNT,
)

__version__ = "1.0.0"

__all__ = [
    # Config
    "get_settings",
    "Settings",
    # Models
    "TaskType",
    "ModelProvider",
    "ModelConfig",
    "InferenceRequest",
    "InferenceResponse",
    "StreamChunk",
    "EmbeddingRequest",
    "EmbeddingResponse",
    "HealthResponse",
    "ErrorResponse",
    # Observability
    "setup_tracing",
    "setup_metrics",
    "setup_logging",
    "REQUEST_COUNT",
    "REQUEST_LATENCY",
    "ACTIVE_REQUESTS",
    "MODEL_INFERENCE_COUNT",
    "MODEL_INFERENCE_LATENCY",
    "MODEL_TOKENS_USED",
    "MODEL_COST_ESTIMATE",
    "ERROR_COUNT",
]