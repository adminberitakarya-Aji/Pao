"""Relationship Service - Main orchestrator for relationship operations."""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from relationship_engine.config import settings
from relationship_engine.models.relationship import (
    Phase,
    RelationshipState,
    RelationshipCreate,
    RelationshipUpdate,
    RelationshipResponse,
)
from relationship_engine.models.requests import (
    CreateRelationshipRequest,
    UpdateDimensionsRequest,
    AddMilestoneRequest,
    AddDiaryEntryRequest,
    StateTransitionRequest,
    BulkDimensionUpdateRequest,
    RecalculatePhaseRequest,
)
from relationship_engine.models.responses import (
    GetStateResponse,
    UpdateDimensionsResponse,
    AddMilestoneResponse,
    AddDiaryEntryResponse,
    CreateRelationshipResponse,
    StateTransitionResponse,
    RelationshipStateResponse,
)
from relationship_engine.repositories.base import (
    RelationshipRepository,
    MilestoneRepository,
    DiaryRepository,
    StateTransitionRepository,
)
from relationship_engine.services.dimensions import DimensionsService
from relationship_engine.services.milestones import MilestonesService
from relationship_engine.services.diary import DiaryService
from relationship_engine.services.state_machine import StateMachineService


class RelationshipService:
    """Main orchestrator service for relationship operations."""

    def __init__(
        self,
        relationship_repo: RelationshipRepository,
        milestone_repo: MilestoneRepository,
        diary_repo: DiaryRepository,
        transition_repo: StateTransitionRepository,
    ):
        self.relationship_repo = relationship_repo
        self.dimensions_service = DimensionsService()
        self.milestones_service = MilestonesService(milestone_repo)
        self.diary_service = DiaryService(diary_repo)
        self.state_machine_service = StateMachineService(transition_repo)

    async def create_relationship(
        self,
        request: CreateRelationshipRequest,
    ) -> CreateRelationshipResponse:
        """Create a new relationship."""
        # Check if relationship already exists
        existing = await self.relationship_repo.get(request.user_id, request.companion_id)
        if existing:
            raise ValueError("Relationship already exists")

        # Initialize dimensions
        dimensions = self.dimensions_service.initialize_dimensions(request.initial_dimensions)

        # Create relationship state
        state = RelationshipState(
            user_id=request.user_id,
            companion_id=request.companion_id,
            dimensions=dimensions,
            metadata=request.metadata or {},
        )

        # Initialize default milestones
        milestones = await self.milestones_service.initialize_milestones(
            request.user_id, request.companion_id
        )
        state.milestones = milestones

        # Save relationship
        saved_state = await self.relationship_repo.create(state)

        # Convert to response
        response_state = RelationshipStateResponse.from_state(saved_state)
        return CreateRelationshipResponse(relationship=response_state)

    async def get_relationship_state(
        self,
        user_id: UUID,
        companion_id: UUID,
        include_milestones: bool = True,
        include_diary: bool = True,
        diary_limit: int = 10,
    ) -> GetStateResponse | None:
        """Get current relationship state."""
        state = await self.relationship_repo.get(user_id, companion_id)
        if not state:
            return None

        # Optionally limit diary entries
        if include_diary and len(state.diary_entries) > diary_limit:
            state.diary_entries = state.diary_entries[-diary_limit:]

        if not include_milestones:
            state.milestones = []

        response_state = RelationshipStateResponse.from_state(state)
        return GetStateResponse(relationship=response_state)

    async def update_dimensions(
        self,
        request: UpdateDimensionsRequest,
    ) -> UpdateDimensionsResponse:
        """Update relationship dimensions."""
        state = await self.relationship_repo.get(request.user_id, request.companion_id)
        if not state:
            raise ValueError("Relationship not found")

        # Apply dimension updates
        updated_dimensions = self.dimensions_service.apply_bulk_updates(state, request.dimension_updates)

        # Apply counter deltas
        state.message_count += request.message_count_delta
        state.voice_calls += request.voice_calls_delta
        state.memories_shared += request.memories_shared_delta
        state.days_known += request.days_known_delta
        state.last_interaction_at = datetime.utcnow()

        if request.metadata:
            state.metadata.update(request.metadata)

        # Check milestones
        new_milestones = await self.milestones_service.check_and_update_milestones(state)

        # Evaluate phase transition
        should_transition, new_phase, reason = await self.state_machine_service.evaluate_transition(state)
        phase_changed = False
        old_phase = None

        if should_transition and new_phase:
            old_phase = state.phase
            phase_changed = True
            await self.state_machine_service.execute_transition(
                state=state,
                new_phase=new_phase,
                reason=reason,
                triggered_by="auto",
            )
            state.metadata["new_milestones"] = [m.name for m in new_milestones]

        # Save updated state
        saved_state = await self.relationship_repo.update(state)

        # Build response
        response_state = RelationshipStateResponse.from_state(saved_state)
        return UpdateDimensionsResponse(
            relationship=response_state,
            phase_changed=phase_changed,
            old_phase=old_phase,
            new_milestones=[
                {
                    "id": str(m.id),
                    "name": m.name,
                    "trigger": m.trigger.value,
                    "threshold": m.threshold,
                    "celebration_message": m.celebration_message,
                }
                for m in new_milestones
            ],
            updated_dimensions=[
                {
                    "name": d.name,
                    "score": d.score,
                    "trend": d.trend,
                    "last_updated": d.last_updated.isoformat(),
                    "interaction_count": d.interaction_count,
                }
                for d in updated_dimensions
            ],
        )

    async def process_interaction(
        self,
        user_id: UUID,
        companion_id: UUID,
        interaction_type: str,
        intensity: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> UpdateDimensionsResponse:
        """Process a single interaction (message, voice call, etc.) and update dimensions."""
        request = UpdateDimensionsRequest(
            user_id=user_id,
            companion_id=companion_id,
            dimension_updates=[],  # Will be filled by interaction impacts
            message_count_delta=1 if interaction_type == "message" else 0,
            voice_calls_delta=1 if interaction_type == "voice_call" else 0,
            memories_shared_delta=1 if interaction_type == "memory_share" else 0,
            metadata=metadata or {},
        )

        # Get current state
        state = await self.relationship_repo.get(user_id, companion_id)
        if not state:
            raise ValueError("Relationship not found")

        # Apply interaction impacts
        updated_dims = self.dimensions_service.apply_interaction_impact(
            state, interaction_type, intensity, metadata
        )

        # Convert to dimension updates for the request
        for dim in updated_dims:
            request.dimension_updates.append({
                "name": dim.name,
                "delta": dim.score - (dim.score - dim.trend),  # Approximate delta
                "reason": f"Interaction: {interaction_type}",
                "interaction_type": interaction_type,
            })

        return await self.update_dimensions(request)

    async def add_milestone(self, request: AddMilestoneRequest) -> AddMilestoneResponse:
        """Add a custom milestone."""
        state = await self.relationship_repo.get(request.user_id, request.companion_id)
        if not state:
            raise ValueError("Relationship not found")

        milestone = await self.milestones_service.add_custom_milestone(
            user_id=request.user_id,
            companion_id=request.companion_id,
            name=request.name,
            trigger=request.trigger,
            threshold=request.threshold,
            celebration_message=request.celebration_message,
            metadata=request.metadata,
        )

        return AddMilestoneResponse(
            milestone={
                "id": str(milestone.id),
                "name": milestone.name,
                "trigger": milestone.trigger.value,
                "threshold": milestone.threshold,
                "achieved": milestone.achieved,
                "celebration_message": milestone.celebration_message,
            }
        )

    async def add_diary_entry(self, request: AddDiaryEntryRequest) -> AddDiaryEntryResponse:
        """Add a diary entry."""
        state = await self.relationship_repo.get(request.user_id, request.companion_id)
        if not state:
            raise ValueError("Relationship not found")

        entry = await self.diary_service.add_entry(
            user_id=request.user_id,
            companion_id=request.companion_id,
            title=request.title,
            content=request.content,
            author=request.author,
            tags=request.tags,
            sentiment=request.sentiment,
            importance=request.importance,
            metadata=request.metadata,
        )

        return AddDiaryEntryResponse(
            entry={
                "id": str(entry.id),
                "date": entry.date.isoformat(),
                "title": entry.title,
                "content": entry.content,
                "author": entry.author,
                "tags": entry.tags,
                "sentiment": entry.sentiment,
                "importance": entry.importance,
            }
        )

    async def trigger_state_transition(
        self,
        request: StateTransitionRequest,
    ) -> StateTransitionResponse:
        """Manually trigger a state transition."""
        state = await self.relationship_repo.get(request.user_id, request.companion_id)
        if not state:
            raise ValueError("Relationship not found")

        if request.target_phase:
            # Force specific transition
            success, transition, message = await self.state_machine_service.force_transition(
                state=state,
                target_phase=request.target_phase,
                reason=request.reason,
                metadata=request.metadata,
            )
            if not success:
                raise ValueError(message)

            # Save state
            await self.relationship_repo.update(state)

            response_state = RelationshipStateResponse.from_state(state)
            return StateTransitionResponse(
                transition={
                    "id": str(transition.id),
                    "from_phase": transition.from_phase.value if transition.from_phase else None,
                    "to_phase": transition.to_phase.value,
                    "reason": transition.reason,
                    "triggered_by": transition.triggered_by,
                    "created_at": transition.created_at.isoformat(),
                },
                relationship=response_state,
            )
        else:
            # Evaluate natural transition
            should_transition, new_phase, reason = await self.state_machine_service.evaluate_transition(
                state, force=request.force
            )

            if should_transition and new_phase:
                transition = await self.state_machine_service.execute_transition(
                    state=state,
                    new_phase=new_phase,
                    reason=reason,
                    triggered_by="manual",
                    metadata=request.metadata,
                )
                await self.relationship_repo.update(state)

                response_state = RelationshipStateResponse.from_state(state)
                return StateTransitionResponse(
                    transition={
                        "id": str(transition.id),
                        "from_phase": transition.from_phase.value if transition.from_phase else None,
                        "to_phase": transition.to_phase.value,
                        "reason": transition.reason,
                        "triggered_by": transition.triggered_by,
                        "created_at": transition.created_at.isoformat(),
                    },
                    relationship=response_state,
                )
            else:
                raise ValueError(reason)

    async def bulk_update_dimensions(
        self,
        request: BulkDimensionUpdateRequest,
    ) -> UpdateDimensionsResponse:
        """Process bulk dimension updates from multiple interactions."""
        # Convert interactions to dimension updates
        dimension_updates = []
        message_delta = 0
        voice_delta = 0
        memory_delta = 0

        for interaction in request.interactions:
            interaction_type = interaction.get("type", "message")
            deltas = interaction.get("dimension_deltas", {})

            if interaction_type == "message":
                message_delta += 1
            elif interaction_type == "voice_call":
                voice_delta += 1
            elif interaction_type == "memory_share":
                memory_delta += 1

            for dim_name, delta in deltas.items():
                dimension_updates.append({
                    "name": dim_name,
                    "delta": delta,
                    "reason": f"Bulk: {interaction_type}",
                    "interaction_type": interaction_type,
                    "metadata": interaction.get("metadata", {}),
                })

        update_request = UpdateDimensionsRequest(
            user_id=request.user_id,
            companion_id=request.companion_id,
            dimension_updates=[
                # Will be converted by the model
            ],
            message_count_delta=message_delta,
            voice_calls_delta=voice_delta,
            memories_shared_delta=memory_delta,
        )

        # We need to convert the dict updates to proper model instances
        # For simplicity, let the update_dimensions handle the conversion
        return await self.update_dimensions(update_request)

    async def recalculate_phase(self, request: RecalculatePhaseRequest) -> GetStateResponse:
        """Recalculate phase from current dimensions."""
        state = await self.relationship_repo.get(request.user_id, request.companion_id)
        if not state:
            raise ValueError("Relationship not found")

        old_phase = state.phase
        new_phase = state.update_phase()

        if new_phase != old_phase or request.force:
            if new_phase != old_phase:
                await self.state_machine_service.execute_transition(
                    state=state,
                    new_phase=new_phase,
                    reason="Phase recalculated from dimensions",
                    triggered_by="recalculation",
                )

            await self.relationship_repo.update(state)

        response_state = RelationshipStateResponse.from_state(state)
        return GetStateResponse(
            relationship=response_state,
            phase_changed=new_phase != old_phase,
            old_phase=old_phase if new_phase != old_phase else None,
        )

    async def get_milestone_progress(
        self,
        user_id: UUID,
        companion_id: UUID,
    ) -> list[dict[str, Any]]:
        """Get progress towards all milestones."""
        state = await self.relationship_repo.get(user_id, companion_id)
        if not state:
            raise ValueError("Relationship not found")

        return await self.milestones_service.get_achievement_progress(state)

    async def get_next_milestones(
        self,
        user_id: UUID,
        companion_id: UUID,
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        """Get the closest upcoming milestones."""
        state = await self.relationship_repo.get(user_id, companion_id)
        if not state:
            raise ValueError("Relationship not found")

        return await self.milestones_service.get_next_milestones(state, limit)

    async def generate_diary_entry(
        self,
        user_id: UUID,
        companion_id: UUID,
        period_start: datetime,
        period_end: datetime,
    ) -> AddDiaryEntryResponse | None:
        """Auto-generate a diary entry for a period."""
        state = await self.relationship_repo.get(user_id, companion_id)
        if not state:
            raise ValueError("Relationship not found")

        entry = await self.diary_service.auto_generate_entry(state, period_start, period_end)
        if entry:
            return AddDiaryEntryResponse(
                entry={
                    "id": str(entry.id),
                    "date": entry.date.isoformat(),
                    "title": entry.title,
                    "content": entry.content,
                    "author": entry.author,
                    "tags": entry.tags,
                    "sentiment": entry.sentiment,
                    "importance": entry.importance,
                }
            )
        return None

    async def get_relationship_summary(
        self,
        user_id: UUID,
        companion_id: UUID,
    ) -> dict[str, Any]:
        """Get a comprehensive relationship summary."""
        state = await self.relationship_repo.get(user_id, companion_id)
        if not state:
            raise ValueError("Relationship not found")

        # Dimension summary
        dim_summary = self.dimensions_service.get_dimension_summary(state)

        # Phase prediction
        prediction = self.dimensions_service.predict_phase_progression(state, 30)

        # Milestone progress
        milestones_progress = await self.milestones_service.get_achievement_progress(state)
        next_milestones = await self.milestones_service.get_next_milestones(state, 3)

        # Recent diary entries
        recent_diary = await self.diary_service.get_recent_entries(user_id, companion_id, days=7, limit=5)

        # Time in current phase
        time_in_phase = await self.state_machine_service.get_time_in_current_phase(user_id, companion_id)

        return {
            "relationship_id": f"{user_id}:{companion_id}",
            "phase": state.phase.value,
            "phase_score": state.phase_score,
            "days_known": state.days_known,
            "message_count": state.message_count,
            "voice_calls": state.voice_calls,
            "memories_shared": state.memories_shared,
            "dimensions": dim_summary,
            "strongest_dimensions": self.dimensions_service.get_strongest_dimensions(state, 3),
            "weakest_dimensions": self.dimensions_service.get_weakest_dimensions(state, 3),
            "phase_prediction": prediction,
            "milestones": {
                "total": len(state.milestones),
                "achieved": sum(1 for m in state.milestones if m.achieved),
                "progress": milestones_progress,
                "next": next_milestones,
            },
            "diary": {
                "total_entries": len(state.diary_entries),
                "recent_entries": len(recent_diary),
            },
            "time_in_current_phase_hours": time_in_phase.total_seconds() / 3600,
            "created_at": state.created_at.isoformat(),
            "last_interaction_at": state.last_interaction_at.isoformat() if state.last_interaction_at else None,
        }

    async def list_relationships_by_user(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[RelationshipStateResponse]:
        """List all relationships for a user."""
        states = await self.relationship_repo.list_by_user(user_id, limit, offset)
        return [RelationshipStateResponse.from_state(s) for s in states]

    async def delete_relationship(self, user_id: UUID, companion_id: UUID) -> bool:
        """Delete a relationship."""
        return await self.relationship_repo.delete(user_id, companion_id)