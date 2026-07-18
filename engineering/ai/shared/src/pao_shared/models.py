"""
PAO Shared Models
Common Pydantic models used across AI services.
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from enum import Enum


class TaskType(str, Enum):
    """Supported task types for model routing."""
    REASONING = "reasoning"
    CREATIVE = "creative"
    CODING = "coding"
    BALANCED = "balanced"
    EMBEDDING = "embedding"


class ModelProvider(str, Enum):
    """Model provider enumeration."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    AZURE = "azure"
    BEDROCK = "bedrock"
    VERTEX = "vertex"


class ModelConfig(BaseModel):
    """Model configuration for routing."""
    id: str = Field(..., description="Unique model identifier")
    name: str = Field(..., description="Human-readable model name")
    provider: ModelProvider = Field(..., description="Model provider")
    category: TaskType = Field(..., description="Model category/task type")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Quality score (0-1)")
    cost_per_token: float = Field(..., ge=0.0, description="Cost per token in USD")
    max_tokens: int = Field(..., gt=0, description="Maximum context tokens")
    supports_streaming: bool = Field(default=True, description="Supports streaming responses")
    supports_functions: bool = Field(default=False, description="Supports function calling")
    supports_vision: bool = Field(default=False, description="Supports vision/multimodal")
    endpoint: Optional[str] = Field(default=None, description="Custom endpoint URL")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class InferenceRequest(BaseModel):
    """Internal inference request model."""
    prompt: str = Field(..., min_length=1, max_length=100000)
    task_type: TaskType = Field(default=TaskType.BALANCED)
    max_tokens: int = Field(default=2048, ge=1, le=128000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    max_cost_per_token: Optional[float] = Field(default=None, ge=0.0)
    stop_sequences: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InferenceResponse(BaseModel):
    """Inference response model."""
    text: str = Field(..., description="Generated text")
    model_used: str = Field(..., description="Model ID used")
    provider: ModelProvider = Field(..., description="Model provider")
    tokens_used: int = Field(..., ge=0, description="Approximate tokens used")
    cost_estimate: float = Field(..., ge=0.0, description="Estimated cost in USD")
    latency_ms: int = Field(..., ge=0, description="Latency in milliseconds")
    finish_reason: Optional[str] = Field(default=None, description="Finish reason")


class StreamChunk(BaseModel):
    """Streaming response chunk."""
    delta: str = Field(..., description="Text delta")
    finish_reason: Optional[str] = Field(default=None)
    model_used: Optional[str] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EmbeddingRequest(BaseModel):
    """Embedding generation request."""
    texts: List[str] = Field(..., min_length=1, max_length=100)
    model: Optional[str] = Field(default=None)
    dimensions: Optional[int] = Field(default=None, ge=1, le=4096)


class EmbeddingResponse(BaseModel):
    """Embedding generation response."""
    embeddings: List[List[float]] = Field(..., description="List of embeddings")
    model_used: str = Field(..., description="Model used")
    tokens_used: int = Field(..., ge=0)
    cost_estimate: float = Field(..., ge=0.0)


class HealthResponse(BaseModel):
    """Health check response."""
    status: Literal["healthy", "degraded", "unhealthy"]
    service: str
    version: str
    checks: Dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    code: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None