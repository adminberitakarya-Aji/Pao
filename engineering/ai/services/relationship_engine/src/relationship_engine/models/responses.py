"""API Response Models."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from relationship_engine.models.relationship import (
    DiaryEntry,
    Dimension,
    Milestone,
    Phase,
    RelationshipState,
    StateTransition,
)


class DimensionResponse(BaseModel):
    """Response for a single dimension."""

    name: str
    score: float = Field(ge=0.0, le=10.0)
    trend: float = Field(ge=-1.0, le=1.0)
    last_updated: datetime
    interaction_count: int
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_dimension(cls, dimension: Dimension) -> "DimensionResponse":
        return cls(
            name=dimension.name,
            score=dimension.score,
            trend=dimension.trend,
            last_updated=dimension.last_updated,
            interaction_count=dimension.interaction_count,
            metadata=dimension.metadata,
        )


class MilestoneResponse(BaseModel):
    """Response for a milestone."""

    id: UUID
    name: str
    trigger: str
    threshold: float | str
    achieved: bool
    achieved_at: datetime | None
    celebration_message: str | None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_milestone(cls, milestone: Milestone) -> "MilestoneResponse":
        return cls(
            id=milestone.id,
            name=milestone.name,
            trigger=milestone.trigger.value if hasattr(milestone.trigger, "value") else str(milestone.trigger),
            threshold=milestone.threshold,
            achieved=milestone.achieved,
            achieved_at=milestone.achieved_at,
            celebration_message=milestone.celebration_message,
            metadata=milestone.metadata,
        )


class DiaryEntryResponse(BaseModel):
    """Response for a diary entry."""

    id: UUID
    date: datetime
    title: str
    content: str
    author: str
    tags: list[str]
    sentiment: float
    importance: int
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_entry(cls, entry: DiaryEntry) -> "DiaryEntryResponse":
        return cls(
            id=entry.id,
            date=entry.date,
            title=entry.title,
            content=entry.content,
            author=entry.author,
            tags=entry.tags,
            sentiment=entry.sentiment,
            importance=entry.importance,
            metadata=entry.metadata,
        )


class RelationshipStateResponse(BaseModel):
    """Response for relationship state."""

    user_id: UUID
    companion_id: UUID
    dimensions: dict[str, DimensionResponse] = Field(default_factory=dict)
    phase: Phase
    phase_score: float = Field(ge=0.0, le=10.0)
    milestones: list[MilestoneResponse] = Field(default_factory=list)
    diary_entries: list[DiaryEntryResponse] = Field(default_factory=list)
    message_count: int
    voice_calls: int
    memories_shared: int
    days_known: int
    created_at: datetime
    updated_at: datetime
    last_interaction_at: datetime | None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_state(cls, state: RelationshipState) -> "RelationshipStateResponse":
        return cls(
            user_id=state.user_id,
            companion_id=state.companion_id,
            dimensions={name: DimensionResponse.from_dimension(d) for name, d in state.dimensions.items()},
            phase=state.phase,
            phase_score=state.phase_score,
            milestones=[MilestoneResponse.from_milestone(m) for m in state.milestones],
            diary_entries=[DiaryEntryResponse.from_entry(e) for e in state.diary_entries],
            message_count=state.message_count,
            voice_calls=state.voice_calls,
            memories_shared=state.memories_shared,
            days_known=state.days_known,
            created_at=state.created_at,
            updated_at=state.updated_at,
            last_interaction_at=state.last_interaction_at,
            metadata=state.metadata,
        )


class GetStateResponse(BaseModel):
    """Response for GET /state endpoint."""

    relationship: RelationshipStateResponse
    phase_changed: bool = False
    old_phase: Phase | None = None
    new_milestones: list[MilestoneResponse] = Field(default_factory=list)


class UpdateDimensionsResponse(BaseModel):
    """Response for dimension updates."""

    relationship: RelationshipStateResponse
    phase_changed: bool = False
    old_phase: Phase | None = None
    new_milestones: list[MilestoneResponse] = Field(default_factory=list)
    updated_dimensions: list[DimensionResponse] = Field(default_factory=list)


class AddMilestoneResponse(BaseModel):
    """Response for adding a milestone."""

    milestone: MilestoneResponse


class AddDiaryEntryResponse(BaseModel):
    """Response for adding a diary entry."""

    entry: DiaryEntryResponse


class ListMilestonesResponse(BaseModel):
    """Response for listing milestones."""

    milestones: list[MilestoneResponse]
    total: int
    limit: int
    offset: int


class ListDiaryEntriesResponse(BaseModel):
    """Response for listing diary entries."""

    entries: list[DiaryEntryResponse]
    total: int
    limit: int
    offset: int


class StateTransitionResponse(BaseModel):
    """Response for state transition."""

    transition: StateTransition
    relationship: RelationshipStateResponse


class CreateRelationshipResponse(BaseModel):
    """Response for creating a relationship."""

    relationship: RelationshipStateResponse


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str = "relationship-engine"
    version: str = "0.1.0"
    checks: dict[str, str] = Field(default_factory=dict)


class MetricsResponse(BaseModel):
    """Metrics summary response."""

    total_relationships: int
    active_relationships_24h: int
    average_phase_score: float
    phase_distribution: dict[str, int]
    milestone_achievement_rate: float
    diary_entries_per_relationship: float