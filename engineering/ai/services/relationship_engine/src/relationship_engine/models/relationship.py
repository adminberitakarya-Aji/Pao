"""Core Relationship Models."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class Phase(str, Enum):
    """Relationship phase/stage."""

    STRANGER = "stranger"
    ACQUAINTANCE = "acquaintance"
    FRIEND = "friend"
    CLOSE_FRIEND = "close_friend"
    PARTNER = "partner"
    SOULMATE = "soulmate"

    @classmethod
    def from_score(cls, score: float) -> "Phase":
        """Determine phase from average dimension score (0-10)."""
        if score >= 8.5:
            return cls.SOULMATE
        elif score >= 7.0:
            return cls.PARTNER
        elif score >= 5.0:
            return cls.CLOSE_FRIEND
        elif score >= 3.0:
            return cls.FRIEND
        elif score >= 1.5:
            return cls.ACQUAINTANCE
        return cls.STRANGER

    def next_phase(self) -> "Phase | None":
        """Get the next phase in progression."""
        phases = list(Phase)
        idx = phases.index(self)
        if idx < len(phases) - 1:
            return phases[idx + 1]
        return None

    def prev_phase(self) -> "Phase | None":
        """Get the previous phase."""
        phases = list(Phase)
        idx = phases.index(self)
        if idx > 0:
            return phases[idx - 1]
        return None


class Dimension(BaseModel):
    """A single relationship dimension."""

    name: str
    score: float = Field(ge=0.0, le=10.0, default=0.0)
    trend: float = Field(ge=-1.0, le=1.0, default=0.0)  # -1 declining, 0 stable, 1 improving
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    interaction_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("score")
    @classmethod
    def validate_score(cls, v: float) -> float:
        return round(max(0.0, min(10.0, v)), 2)

    @field_validator("trend")
    @classmethod
    def validate_trend(cls, v: float) -> float:
        return round(max(-1.0, min(1.0, v)), 2)


class DimensionUpdate(BaseModel):
    """Request to update a dimension."""

    name: str
    delta: float = Field(ge=-2.0, le=2.0)  # Change amount
    reason: str | None = None
    interaction_type: str | None = None  # message, voice_call, memory_share, etc.
    metadata: dict[str, Any] = Field(default_factory=dict)


class MilestoneTrigger(str, Enum):
    """Types of milestone triggers."""

    MESSAGE_COUNT = "message_count"
    DAYS_KNOWN = "days_known"
    VOICE_CALLS = "voice_calls"
    MEMORIES_SHARED = "memories_shared"
    DIMENSION_TRUST = "dimension_trust"
    DIMENSION_INTIMACY = "dimension_intimacy"
    PHASE = "phase"


class Milestone(BaseModel):
    """A relationship milestone."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    trigger: MilestoneTrigger
    threshold: float | str  # numeric threshold or phase name
    achieved: bool = False
    achieved_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    celebration_message: str | None = None


class DiaryEntry(BaseModel):
    """A diary entry for the relationship."""

    id: UUID = Field(default_factory=uuid4)
    date: datetime = Field(default_factory=datetime.utcnow)
    title: str
    content: str
    author: str = "system"  # "system", "user", "companion"
    tags: list[str] = Field(default_factory=list)
    sentiment: float = Field(ge=-1.0, le=1.0, default=0.0)
    importance: int = Field(ge=1, le=5, default=3)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RelationshipState(BaseModel):
    """Complete relationship state."""

    user_id: UUID
    companion_id: UUID
    dimensions: dict[str, Dimension] = Field(default_factory=dict)
    phase: Phase = Phase.STRANGER
    phase_score: float = 0.0
    milestones: list[Milestone] = Field(default_factory=list)
    diary_entries: list[DiaryEntry] = Field(default_factory=list)
    message_count: int = 0
    voice_calls: int = 0
    memories_shared: int = 0
    days_known: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_interaction_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def get_dimension(self, name: str) -> Dimension:
        """Get or create a dimension."""
        if name not in self.dimensions:
            self.dimensions[name] = Dimension(name=name)
        return self.dimensions[name]

    def calculate_phase_score(self) -> float:
        """Calculate average dimension score for phase determination."""
        if not self.dimensions:
            return 0.0
        return sum(d.score for d in self.dimensions.values()) / len(self.dimensions)

    def update_phase(self) -> Phase:
        """Recalculate and update phase based on dimensions."""
        self.phase_score = self.calculate_phase_score()
        new_phase = Phase.from_score(self.phase_score)
        if new_phase != self.phase:
            old_phase = self.phase
            self.phase = new_phase
            return old_phase
        return self.phase

    def check_milestones(self) -> list[Milestone]:
        """Check and return newly achieved milestones."""
        newly_achieved = []
        for milestone in self.milestones:
            if not milestone.achieved:
                achieved = self._check_milestone_condition(milestone)
                if achieved:
                    milestone.achieved = True
                    milestone.achieved_at = datetime.utcnow()
                    newly_achieved.append(milestone)
        return newly_achieved

    def _check_milestone_condition(self, milestone: Milestone) -> bool:
        """Check if a milestone condition is met."""
        trigger = milestone.trigger
        threshold = milestone.threshold

        if trigger == MilestoneTrigger.MESSAGE_COUNT:
            return self.message_count >= threshold
        elif trigger == MilestoneTrigger.DAYS_KNOWN:
            return self.days_known >= threshold
        elif trigger == MilestoneTrigger.VOICE_CALLS:
            return self.voice_calls >= threshold
        elif trigger == MilestoneTrigger.MEMORIES_SHARED:
            return self.memories_shared >= threshold
        elif trigger == MilestoneTrigger.DIMENSION_TRUST:
            trust = self.dimensions.get("trust")
            return trust is not None and trust.score >= threshold
        elif trigger == MilestoneTrigger.DIMENSION_INTIMACY:
            intimacy = self.dimensions.get("intimacy")
            return intimacy is not None and intimacy.score >= threshold
        elif trigger == MilestoneTrigger.PHASE:
            return self.phase == Phase(threshold)
        return False


class RelationshipCreate(BaseModel):
    """Request to create a new relationship."""

    user_id: UUID
    companion_id: UUID
    initial_dimensions: dict[str, float] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RelationshipUpdate(BaseModel):
    """Request to update relationship."""

    dimension_updates: list[DimensionUpdate] = Field(default_factory=list)
    message_count_delta: int = 0
    voice_calls_delta: int = 0
    memories_shared_delta: int = 0
    days_known_delta: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class RelationshipResponse(BaseModel):
    """Response with relationship state."""

    relationship: RelationshipState
    phase_changed: bool = False
    old_phase: Phase | None = None
    new_milestones: list[Milestone] = Field(default_factory=list)


class StateTransition(BaseModel):
    """A phase transition record."""

    id: UUID = Field(default_factory=uuid4)
    from_phase: Phase
    to_phase: Phase
    trigger: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    dimension_scores: dict[str, float] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)