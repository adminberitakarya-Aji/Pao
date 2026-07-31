"""Request models for Proactive Engine API."""

from typing import Optional, List, Dict, Any, Literal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class InitiativeRequest(BaseModel):
    """Request for proactive initiative detection."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    context: Optional[Dict[str, Any]] = None
    current_activity: Optional[str] = None
    time_of_day: Optional[str] = None
    user_state: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


class AnticipationRequest(BaseModel):
    """Request for need anticipation."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    recent_interactions: List[Dict[str, Any]] = Field(default_factory=list)
    user_preferences: Optional[Dict[str, Any]] = None
    current_context: Optional[Dict[str, Any]] = None
    time_horizon_hours: int = Field(default=24, ge=1, le=168)
    request_id: Optional[str] = None


class SuggestionRequest(BaseModel):
    """Request for proactive suggestions."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    suggestion_type: Literal["activity", "conversation", "content", "action", "learning"] = "activity"
    context: Optional[Dict[str, Any]] = None
    user_interests: Optional[List[str]] = None
    exclude_recent: bool = True
    max_suggestions: int = Field(default=5, ge=1, le=20)
    request_id: Optional[str] = None


class ReminderRequest(BaseModel):
    """Request for proactive reminders."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    reminder_type: Literal["task", "event", "habit", "medication", "custom"] = "task"
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    recurrence: Optional[str] = None  # cron expression
    priority: Literal["low", "medium", "high", "urgent"] = "medium"
    context: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


class CheckInRequest(BaseModel):
    """Request for proactive check-in."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    check_in_type: Literal["wellbeing", "progress", "mood", "engagement", "general"] = "general"
    context: Optional[Dict[str, Any]] = None
    trigger_reason: Optional[str] = None
    request_id: Optional[str] = None


class ScheduleRequest(BaseModel):
    """Request for proactive scheduling."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    action_type: Literal["message", "call", "notification", "activity_suggestion"] = "message"
    schedule: Dict[str, Any]  # cron or interval
    content_template: str
    conditions: Optional[List[Dict[str, Any]]] = None
    active: bool = True
    request_id: Optional[str] = None


class ProactiveActionRequest(BaseModel):
    """Request to execute a proactive action."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    action_type: Literal[
        "send_message", 
        "suggest_activity", 
        "check_in", 
        "remind", 
        "share_content",
        "initiate_conversation",
        "adjust_behavior"
    ]
    parameters: Dict[str, Any]
    priority: Literal["low", "medium", "high"] = "medium"
    requires_confirmation: bool = False
    request_id: Optional[str] = None