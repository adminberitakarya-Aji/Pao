"""Relationship Engine Models Package."""

from relationship_engine.models.relationship import (
    Dimension,
    DimensionUpdate,
    Phase,
    Milestone,
    MilestoneTrigger,
    DiaryEntry,
    RelationshipState,
    RelationshipCreate,
    RelationshipUpdate,
    RelationshipResponse,
    StateTransition,
)

from relationship_engine.models.requests import (
    GetStateRequest,
    UpdateDimensionsRequest,
    AddMilestoneRequest,
    AddDiaryEntryRequest,
    StateTransitionRequest,
)

from relationship_engine.models.responses import (
    GetStateResponse,
    UpdateDimensionsResponse,
    MilestoneResponse,
    DiaryEntryResponse,
    StateTransitionResponse,
    ListMilestonesResponse,
    ListDiaryEntriesResponse,
    HealthResponse,
)

__all__ = [
    # Core models
    "Dimension",
    "DimensionUpdate",
    "Phase",
    "Milestone",
    "MilestoneTrigger",
    "DiaryEntry",
    "RelationshipState",
    "RelationshipCreate",
    "RelationshipUpdate",
    "RelationshipResponse",
    "StateTransition",
    # Request models
    "GetStateRequest",
    "UpdateDimensionsRequest",
    "AddMilestoneRequest",
    "AddDiaryEntryRequest",
    "StateTransitionRequest",
    # Response models
    "GetStateResponse",
    "UpdateDimensionsResponse",
    "MilestoneResponse",
    "DiaryEntryResponse",
    "StateTransitionResponse",
    "ListMilestonesResponse",
    "ListDiaryEntriesResponse",
    "HealthResponse",
]