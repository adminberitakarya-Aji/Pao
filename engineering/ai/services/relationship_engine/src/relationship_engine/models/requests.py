"""API Request Models."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from relationship_engine.models.relationship import (
    DimensionUpdate,
    MilestoneTrigger,
    Phase,
)


class GetStateRequest(BaseModel):
    """Request to get relationship state."""

    user_id: UUID
    companion_id: UUID
    include_milestones: bool = True
    include_diary: bool = True
    diary_limit: int = Field(default=10, ge=1, le=100)
    diary_offset: int = Field(default=0, ge=0)


class UpdateDimensionsRequest(BaseModel):
    """Request to update relationship dimensions."""

    user_id: UUID
    companion_id: UUID
    dimension_updates: list[DimensionUpdate] = Field(min_length=1)
    message_count_delta: int = Field(default=0, ge=0)
    voice_calls_delta: int = Field(default=0, ge=0)
    memories_shared_delta: int = Field(default=0, ge=0)
    days_known_delta: int = Field(default=0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AddMilestoneRequest(BaseModel):
    """Request to add a custom milestone."""

    user_id: UUID
    companion_id: UUID
    name: str = Field(min_length=1, max_length=100)
    trigger: MilestoneTrigger
    threshold: float | str
    celebration_message: str | None = Field(default=None, max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AddDiaryEntryRequest(BaseModel):
    """Request to add a diary entry."""

    user_id: UUID
    companion_id: UUID
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=10000)
    author: str = Field(default="system", pattern="^(system|user|companion)$")
    tags: list[str] = Field(default_factory=list, max_length=10)
    sentiment: float = Field(default=0.0, ge=-1.0, le=1.0)
    importance: int = Field(default=3, ge=1, le=5)
    metadata: dict[str, Any] = Field(default_factory=dict)


class StateTransitionRequest(BaseModel):
    """Request to trigger a state transition."""

    user_id: UUID
    companion_id: UUID
    target_phase: Phase | None = None
    reason: str = Field(min_length=1, max_length=500)
    force: bool = False  # Bypass cooldown
    metadata: dict[str, Any] = Field(default_factory=dict)


class CreateRelationshipRequest(BaseModel):
    """Request to create a new relationship."""

    user_id: UUID
    companion_id: UUID
    initial_dimensions: dict[str, float] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ListMilestonesRequest(BaseModel):
    """Request to list milestones."""

    user_id: UUID
    companion_id: UUID
    achieved_only: bool = False
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class ListDiaryEntriesRequest(BaseModel):
    """Request to list diary entries."""

    user_id: UUID
    companion_id: UUID
    author: str | None = Field(default=None, pattern="^(system|user|companion)$")
    start_date: datetime | None = None
    end_date: datetime | None = None
    tags: list[str] = Field(default_factory=list)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class GenerateDiaryRequest(BaseModel):
    """Request to auto-generate a diary entry."""

    user_id: UUID
    companion_id: UUID
    period_start: datetime
    period_end: datetime
    force: bool = False


class BulkDimensionUpdateRequest(BaseModel):
    """Request for bulk dimension updates (from message processing)."""

    user_id: UUID
    companion_id: UUID
    interactions: list[dict[str, Any]] = Field(min_length=1)
    # Each interaction: {
    #   "type": "message|voice_call|memory_share|proactive_nudge",
    #   "dimension_deltas": {"trust": 0.1, "intimacy": 0.05, ...},
    #   "metadata": {...}
    # }


class RecalculatePhaseRequest(BaseModel):
    """Request to recalculate phase from dimensions."""

    user_id: UUID
    companion_id: UUID
    force: bool = False