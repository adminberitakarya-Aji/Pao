"""Response models for Proactive Engine API."""

from typing import Optional, List, Dict, Any, Literal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class InitiativeResponse(BaseModel):
    """Response for proactive initiative detection."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    initiative_detected: bool
    initiative_type: Optional[Literal[
        "conversation_start", 
        "activity_suggestion", 
        "check_in", 
        "reminder", 
        "content_share",
        "learning_prompt",
        "support_offer"
    ]] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    suggested_action: Optional[Dict[str, Any]] = None
    timing: Literal["immediate", "soon", "later", "scheduled"] = "soon"
    processing_time_ms: float
    request_id: Optional[str] = None


class AnticipationResponse(BaseModel):
    """Response for need anticipation."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    anticipated_needs: List[Dict[str, Any]] = Field(default_factory=list)
    top_need: Optional[Dict[str, Any]] = None
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
    time_horizon_hours: int
    reasoning: str
    processing_time_ms: float
    request_id: Optional[str] = None


class SuggestionResponse(BaseModel):
    """Response for proactive suggestions."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    suggestions: List[Dict[str, Any]] = Field(default_factory=list)
    suggestion_type: str
    context_used: Dict[str, Any] = Field(default_factory=dict)
    personalization_score: float = Field(default=0.0, ge=0.0, le=1.0)
    processing_time_ms: float
    request_id: Optional[str] = None


class ReminderResponse(BaseModel):
    """Response for proactive reminders."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    reminder_id: str
    title: str
    description: Optional[str] = None
    scheduled_time: datetime
    recurrence: Optional[str] = None
    priority: Literal["low", "medium", "high", "urgent"]
    status: Literal["created", "scheduled", "active", "completed", "cancelled"] = "created"
    processing_time_ms: float
    request_id: Optional[str] = None


class CheckInResponse(BaseModel):
    """Response for proactive check-in."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    check_in_id: str
    check_in_type: str
    message: str
    suggested_questions: List[str] = Field(default_factory=list)
    follow_up_actions: List[Dict[str, Any]] = Field(default_factory=list)
    timing_rationale: str
    processing_time_ms: float
    request_id: Optional[str] = None


class ScheduleResponse(BaseModel):
    """Response for proactive scheduling."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    schedule_id: str
    action_type: str
    schedule: Dict[str, Any]
    content_template: str
    conditions: List[Dict[str, Any]] = Field(default_factory=list)
    active: bool
    next_execution: Optional[datetime] = None
    processing_time_ms: float
    request_id: Optional[str] = None


class ProactiveActionResponse(BaseModel):
    """Response for proactive action execution."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    action_id: str
    action_type: str
    status: Literal["executed", "pending_confirmation", "scheduled", "failed", "cancelled"]
    result: Optional[Dict[str, Any]] = None
    confirmation_required: bool = False
    message: Optional[str] = None
    processing_time_ms: float
    request_id: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    
    model_config = ConfigDict(extra="forbid")
    
    service: str = "proactive-engine"
    version: str = "0.1.0"
    status: Literal["healthy", "degraded", "unhealthy"] = "healthy"
    checks: Dict[str, bool] = Field(default_factory=dict)
    models_loaded: Dict[str, bool] = Field(default_factory=dict)
    scheduler_status: Literal["running", "stopped", "error"] = "running"
    processing_time_ms: float = 0.0


class ErrorResponse(BaseModel):
    """Error response."""
    
    model_config = ConfigDict(extra="forbid")
    
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None