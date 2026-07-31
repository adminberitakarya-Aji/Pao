"""Companion Runtime Response Models."""

from typing import Optional, List, Dict, Any, Literal
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class ChatResponse(BaseModel):
    """Response for a chat completion (non-streaming)."""

    message_id: UUID = Field(..., description="Generated message ID")
    conversation_id: UUID = Field(..., description="Conversation ID")
    content: str = Field(..., description="Companion response content")
    model_used: str = Field(..., description="Model used for generation")
    tokens_used: int = Field(..., description="Total tokens used")
    latency_ms: int = Field(..., description="Total latency in milliseconds")
    safety_filtered: bool = Field(default=False, description="Whether content was filtered by safety")
    safety_flags: Optional[List[str]] = Field(default=None, description="Safety flags if any")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracing")
    created_at: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class ChatStreamChunk(BaseModel):
    """Single chunk in a streaming chat response."""

    chunk_id: UUID = Field(..., description="Chunk ID")
    conversation_id: UUID = Field(..., description="Conversation ID")
    content: str = Field(..., description="Content chunk")
    is_final: bool = Field(default=False, description="Whether this is the final chunk")
    model_used: Optional[str] = Field(default=None, description="Model used (final chunk only)")
    tokens_used: Optional[int] = Field(default=None, description="Tokens used (final chunk only)")
    latency_ms: Optional[int] = Field(default=None, description="Total latency (final chunk only)")
    safety_filtered: bool = Field(default=False, description="Whether content was filtered")
    safety_flags: Optional[List[str]] = Field(default=None, description="Safety flags if any")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracing")


class HealthResponse(BaseModel):
    """Health check response."""

    service: str = Field(default="companion-runtime", description="Service name")
    version: str = Field(default="0.1.0", description="Service version")
    status: Literal["healthy", "degraded", "unhealthy"] = Field(default="healthy", description="Health status")
    checks: Dict[str, bool] = Field(default_factory=dict, description="Individual health checks")
    engines: Dict[str, bool] = Field(default_factory=dict, description="Engine connectivity status")
    uptime_seconds: float = Field(default=0.0, description="Uptime in seconds")
    processing_time_ms: float = Field(default=0.0, description="Health check processing time")


class EngineStatus(BaseModel):
    """Status of an individual engine."""

    name: str = Field(..., description="Engine name")
    url: str = Field(..., description="Engine URL")
    healthy: bool = Field(..., description="Whether engine is healthy")
    latency_ms: Optional[float] = Field(default=None, description="Last request latency")
    last_check: datetime = Field(default_factory=datetime.now, description="Last health check time")
    error: Optional[str] = Field(default=None, description="Error message if unhealthy")


class CompanionStateResponse(BaseModel):
    """Companion state response for context."""

    user_id: UUID = Field(..., description="User ID")
    companion_id: UUID = Field(..., description="Companion ID")
    conversation_id: Optional[UUID] = Field(default=None, description="Conversation ID")
    identity: Optional[Dict[str, Any]] = Field(default=None, description="Identity context")
    memory: Optional[Dict[str, Any]] = Field(default=None, description="Memory context")
    relationship: Optional[Dict[str, Any]] = Field(default=None, description="Relationship state")
    emotion: Optional[Dict[str, Any]] = Field(default=None, description="Emotional state")
    proactive_pending: Optional[List[Dict[str, Any]]] = Field(default=None, description="Pending proactive nudges")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracing")
    retrieved_at: datetime = Field(default_factory=datetime.now, description="Retrieval timestamp")


class SafetyCheckResponse(BaseModel):
    """Response from safety check."""

    allowed: bool = Field(..., description="Whether content is allowed")
    action: Literal["allow", "rewrite", "block"] = Field(..., description="Action taken")
    filtered_content: Optional[str] = Field(default=None, description="Filtered/rewritten content")
    violations: List[Dict[str, Any]] = Field(default_factory=list, description="Violations found")
    severity: Literal["none", "low", "medium", "high", "critical"] = Field(default="none", description="Highest severity")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracing")


class EngineCallResponse(BaseModel):
    """Generic response from an engine call."""

    engine: str = Field(..., description="Engine name")
    success: bool = Field(..., description="Whether call succeeded")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Response data")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    latency_ms: float = Field(..., description="Call latency in milliseconds")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracing")


class GraphExecutionResponse(BaseModel):
    """Response from LangGraph execution."""

    success: bool = Field(..., description="Whether execution succeeded")
    final_state: Optional[Dict[str, Any]] = Field(default=None, description="Final graph state")
    output: Optional[str] = Field(default=None, description="Final output message")
    steps: List[Dict[str, Any]] = Field(default_factory=list, description="Execution steps")
    errors: List[str] = Field(default_factory=list, description="Errors encountered")
    total_latency_ms: int = Field(..., description="Total execution latency")
    checkpoints_created: int = Field(default=0, description="Number of checkpoints created")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracing")


class MemoryConsolidationResponse(BaseModel):
    """Response from memory consolidation trigger."""

    success: bool = Field(..., description="Whether consolidation was triggered")
    consolidation_id: Optional[str] = Field(default=None, description="Consolidation job ID")
    message: str = Field(..., description="Status message")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracing")


class ProactiveCheckResponse(BaseModel):
    """Response from proactive check."""

    should_generate: bool = Field(..., description="Whether to generate a nudge")
    nudge: Optional[Dict[str, Any]] = Field(default=None, description="Generated nudge if any")
    reason: str = Field(..., description="Reason for decision")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracing")