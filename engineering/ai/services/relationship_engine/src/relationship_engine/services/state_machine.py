"""State Machine Service - Manages relationship phase transitions."""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from relationship_engine.config import settings
from relationship_engine.models.relationship import (
    Phase,
    RelationshipState,
    StateTransition,
)
from relationship_engine.repositories.base import StateTransitionRepository


class StateMachineService:
    """Service for managing relationship state transitions."""

    # Valid phase transitions (from -> allowed to)
    VALID_TRANSITIONS: dict[Phase, list[Phase]] = {
        Phase.STRANGER: [Phase.ACQUAINTANCE],
        Phase.ACQUAINTANCE: [Phase.FRIEND, Phase.STRANGER],
        Phase.FRIEND: [Phase.CLOSE_FRIEND, Phase.ACQUAINTANCE],
        Phase.CLOSE_FRIEND: [Phase.PARTNER, Phase.FRIEND],
        Phase.PARTNER: [Phase.SOULMATE, Phase.CLOSE_FRIEND],
        Phase.SOULMATE: [Phase.PARTNER],  # Can only go back
    }

    # Minimum time in phase before transition (hours)
    MIN_PHASE_DURATION_HOURS: dict[Phase, int] = {
        Phase.STRANGER: 0,
        Phase.ACQUAINTANCE: 24,
        Phase.FRIEND: 168,  # 1 week
        Phase.CLOSE_FRIEND: 720,  # 30 days
        Phase.PARTNER: 720,  # 30 days
        Phase.SOULMATE: 0,
    }

    def __init__(self, repository: StateTransitionRepository):
        self.repository = repository

    async def evaluate_transition(
        self,
        state: RelationshipState,
        force: bool = False,
    ) -> tuple[bool, Phase | None, str]:
        """
        Evaluate if a phase transition should occur.
        Returns: (should_transition, new_phase, reason)
        """
        if not settings.state_machine_enabled:
            return False, None, "State machine disabled"

        old_phase = state.phase
        new_phase = state.update_phase()

        if new_phase == old_phase:
            return False, None, "No phase change needed"

        # Check if transition is valid
        if not self._is_valid_transition(old_phase, new_phase):
            # Revert to old phase
            state.phase = old_phase
            state.phase_score = state.calculate_phase_score()
            return False, None, f"Invalid transition: {old_phase.value} -> {new_phase.value}"

        # Check cooldown unless forced
        if not force and not await self._check_cooldown(state, old_phase):
            state.phase = old_phase
            state.phase_score = state.calculate_phase_score()
            return False, None, "Cooldown period not elapsed"

        # Check minimum phase duration
        if not force and not await self._check_min_duration(state, old_phase):
            state.phase = old_phase
            state.phase_score = state.calculate_phase_score()
            return False, None, f"Minimum duration in {old_phase.value} not met"

        return True, new_phase, f"Phase transition: {old_phase.value} -> {new_phase.value}"

    def _is_valid_transition(self, from_phase: Phase, to_phase: Phase) -> bool:
        """Check if a transition is valid."""
        allowed = self.VALID_TRANSITIONS.get(from_phase, [])
        return to_phase in allowed

    async def _check_cooldown(self, state: RelationshipState, current_phase: Phase) -> bool:
        """Check if enough time has passed since last transition."""
        cooldown_hours = settings.state_transition_cooldown_hours
        if cooldown_hours <= 0:
            return True

        latest = await self.repository.get_latest(state.user_id, state.companion_id)
        if not latest:
            return True

        elapsed = datetime.utcnow() - latest.created_at
        return elapsed >= timedelta(hours=cooldown_hours)

    async def _check_min_duration(self, state: RelationshipState, current_phase: Phase) -> bool:
        """Check if minimum time in current phase has elapsed."""
        min_hours = self.MIN_PHASE_DURATION_HOURS.get(current_phase, 0)
        if min_hours <= 0:
            return True

        # Get when we entered this phase (latest transition TO this phase)
        transitions = await self.repository.list(state.user_id, state.companion_id, limit=100)
        for transition in transitions:
            if transition.to_phase == current_phase:
                elapsed = datetime.utcnow() - transition.created_at
                return elapsed >= timedelta(hours=min_hours)

        # No transition found to this phase - check created_at
        elapsed = datetime.utcnow() - state.created_at
        return elapsed >= timedelta(hours=min_hours)

    async def execute_transition(
        self,
        state: RelationshipState,
        new_phase: Phase,
        reason: str,
        triggered_by: str = "auto",
        metadata: dict[str, Any] | None = None,
    ) -> StateTransition:
        """Execute a phase transition and record it."""
        old_phase = state.phase

        # Create transition record
        transition = StateTransition(
            user_id=state.user_id,
            companion_id=state.companion_id,
            from_phase=old_phase,
            to_phase=new_phase,
            reason=reason,
            triggered_by=triggered_by,
            metadata=metadata or {},
            dimension_scores={name: dim.score for name, dim in state.dimensions.items()},
        )

        # Update state
        state.phase = new_phase
        state.phase_score = state.calculate_phase_score()
        state.metadata["phase_changed"] = True
        state.metadata["old_phase"] = old_phase.value
        state.metadata["phase_changed_at"] = datetime.utcnow().isoformat()
        state.updated_at = datetime.utcnow()

        # Persist transition
        created_transition = await self.repository.create(transition)

        return created_transition

    async def force_transition(
        self,
        state: RelationshipState,
        target_phase: Phase,
        reason: str,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[bool, StateTransition | None, str]:
        """Force a transition (admin/user override)."""
        if not self._is_valid_transition(state.phase, target_phase):
            return False, None, f"Invalid transition: {state.phase.value} -> {target_phase.value}"

        transition = await self.execute_transition(
            state=state,
            new_phase=target_phase,
            reason=reason,
            triggered_by="forced",
            metadata=metadata,
        )

        return True, transition, f"Forced transition: {state.phase.value} -> {target_phase.value}"

    async def get_transition_history(
        self,
        user_id: UUID,
        companion_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[StateTransition]:
        """Get transition history for a relationship."""
        return await self.repository.list(
            user_id=user_id,
            companion_id=companion_id,
            limit=limit,
            offset=offset,
        )

    async def get_time_in_current_phase(
        self,
        user_id: UUID,
        companion_id: UUID,
    ) -> timedelta:
        """Get time spent in current phase."""
        latest = await self.repository.get_latest(user_id, companion_id)
        if latest:
            return datetime.utcnow() - latest.created_at
        # Fall back to relationship creation
        return timedelta(0)

    async def can_transition_to(
        self,
        state: RelationshipState,
        target_phase: Phase,
    ) -> tuple[bool, str]:
        """Check if a transition to target phase is possible."""
        if not self._is_valid_transition(state.phase, target_phase):
            return False, f"Invalid transition from {state.phase.value}"

        if target_phase == state.phase:
            return False, "Already in target phase"

        # Check cooldown
        if not await self._check_cooldown(state, state.phase):
            return False, "Cooldown period active"

        # Check min duration
        if not await self._check_min_duration(state, state.phase):
            return False, f"Minimum duration in {state.phase.value} not met"

        return True, "Transition allowed"

    def get_possible_transitions(self, current_phase: Phase) -> list[Phase]:
        """Get all valid transitions from current phase."""
        return self.VALID_TRANSITIONS.get(current_phase, [])

    def get_phase_info(self, phase: Phase) -> dict[str, Any]:
        """Get information about a phase."""
        return {
            "phase": phase.value,
            "min_duration_hours": self.MIN_PHASE_DURATION_HOURS.get(phase, 0),
            "can_transition_to": [p.value for p in self.get_possible_transitions(phase)],
        }