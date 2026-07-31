"""Companion Runtime Request Models."""

from typing import Optional, List, Dict, Any, Literal
from uuid import UUID
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request for a chat completion (non-streaming)."""

    user_id: UUID = Field(..., description="User ID")
    companion_id: UUID = Field(..., description="Companion ID")
    conversation_id: UUID = Field(..., description="Conversation ID")
    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    message_id: Optional[UUID] = Field(default=None, description="Client-generated message ID")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracing")


class ChatStreamRequest(BaseModel):
    """Request for a streaming chat completion."""

    user_id: UUID = Field(..., description="User ID")
    companion_id: UUID = Field(..., description="Companion ID")
    conversation_id: UUID = Field(..., description="Conversation ID")
    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    message_id: Optional[UUID] = Field(default=None, description="Client-generated message ID")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracing")
    include_state: bool = Field(default=False, description="Include companion state in response")


class CompanionContextRequest(BaseModel):
    """Request to get companion context for a conversation."""

    user_id: UUID = Field(..., description="User ID")
    companion_id: UUID = Field(..., description="Companion ID")
    conversation_id: Optional[UUID] = Field(default=None, description="Conversation ID (optional)")
    include_memory: bool = Field(default=True, description="Include memory context")
    include_relationship: bool = Field(default=True, description="Include relationship state")
    include_emotion: bool = Field(default=True, description="Include emotional state")
    include_identity: bool = Field(default=True, description="Include identity context")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracing")


class EngineCallRequest(BaseModel):
    """Generic request for calling an engine."""

    engine: Literal[
        "identity",
        "memory",
        "safety",
        "relationship",
        "emotion",
        "voice",
        "proactive",
        "evaluation",
        "inference",
    ] = Field(..., description="Engine to call")
    method: str = Field(..., description="Method/endpoint to call")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Request payload")
    timeout: Optional[float] = Field(default=None, description="Override default timeout")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracing")


class SafetyCheckRequest(BaseModel):
    """Request for safety check (pre or post)."""

    content: str = Field(..., description="Content to check")
    content_type: Literal["user_input", "model_output"] = Field(..., description="Type of content")
    user_id: UUID = Field(..., description="User ID")
    companion_id: UUID = Field(..., description="Companion ID")
    conversation_id: UUID = Field(..., description="Conversation ID")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracing")


class MemoryConsolidationRequest(BaseModel):
    """Request to trigger memory consolidation."""

    user_id: UUID = Field(..., description="User ID")
    companion_id: UUID = Field(..., description="Companion ID")
    conversation_id: Optional[UUID] = Field(default=None, description="Specific conversation (optional)")
    force: bool = Field(default=False, description="Force consolidation even if recently done")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracing")


class ProactiveCheckRequest(BaseModel):
    """Request to check if proactive nudge should be generated."""

    user_id: UUID = Field(..., description="User ID")
    companion_id: UUID = Field(..., description="Companion ID")
    conversation_id: UUID = Field(..., description="Conversation ID")
    last_message: str = Field(..., description="Last user message")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracing")