"""Tests for State Machine Service."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock

from relationship_engine.models.relationship import (
    Phase,
    RelationshipState,
    StateTransition,
)
from relationship_engine.services.state_machine import StateMachineService


@pytest.fixture
def mock_repo():
    """Create a mock state transition repository."""
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.list = AsyncMock(return_value=[])
    repo.get_latest = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def state_machine_service(mock_repo):
    """Create a state machine service instance with mock repo."""
    return StateMachineService(mock_repo)


@pytest.fixture
def sample_state():
    """Create a sample relationship state."""
    state = RelationshipState(
        user_id=uuid4(),
        companion_id=uuid4(),
        created_at=datetime.utcnow() - timedelta(days=30),
    )
    return state


class TestStateMachineService:
    """Test cases for StateMachineService."""

    def test_valid_transitions(self, state_machine_service):
        """Test valid phase transitions."""
        assert state_machine_service._is_valid_transition(Phase.STRANGER, Phase.ACQUAINTANCE) is True
        assert state_machine_service._is_valid_transition(Phase.ACQUAINTANCE, Phase.FRIEND) is True
        assert state_machine_service._is_valid_transition(Phase.ACQUAINTANCE, Phase.STRANGER) is True
        assert state_machine_service._is_valid_transition(Phase.FRIEND, Phase.CLOSE_FRIEND) is True
        assert state_machine_service._is_valid_transition(Phase.CLOSE_FRIEND, Phase.PARTNER) is True
        assert state_machine_service._is_valid_transition(Phase.PARTNER, Phase.SOULMATE) is True
        assert state_machine_service._is_valid_transition(Phase.SOULMATE, Phase.PARTNER) is True

    def test_invalid_transitions(self, state_machine_service):
        """Test invalid phase transitions."""
        assert state_machine_service._is_valid_transition(Phase.STRANGER, Phase.FRIEND) is False
        assert state_machine_service._is_valid_transition(Phase.ACQUAINTANCE, Phase.CLOSE_FRIEND) is False
        assert state_machine_service._is_valid_transition(Phase.FRIEND, Phase.PARTNER) is False
        assert state_machine_service._is_valid_transition(Phase.CLOSE_FRIEND, Phase.SOULMATE) is False
        assert state_machine_service._is_valid_transition(Phase.PARTNER, Phase.FRIEND) is False

    def test_get_possible_transitions(self, state_machine_service):
        """Test getting possible transitions from each phase."""
        assert state_machine_service.get_possible_transitions(Phase.STRANGER) == [Phase.ACQUAINTANCE]
        assert set(state_machine_service.get_possible_transitions(Phase.ACQUAINTANCE)) == {Phase.FRIEND, Phase.STRANGER}
        assert set(state_machine_service.get_possible_transitions(Phase.FRIEND)) == {Phase.CLOSE_FRIEND, Phase.ACQUAINTANCE}
        assert set(state_machine_service.get_possible_transitions(Phase.CLOSE_FRIEND)) == {Phase.PARTNER, Phase.FRIEND}
        assert set(state_machine_service.get_possible_transitions(Phase.PARTNER)) == {Phase.SOULMATE, Phase.CLOSE_FRIEND}
        assert state_machine_service.get_possible_transitions(Phase.SOULMATE) == [Phase.PARTNER]

    def test_get_phase_info(self, state_machine_service):
        """Test getting phase information."""
        info = state_machine_service.get_phase_info(Phase.FRIEND)
        assert info["phase"] == "friend"
        assert info["min_duration_hours"] == 168
        assert "close_friend" in info["can_transition_to"]
        assert "acquaintance" in info["can_transition_to"]

    @pytest.mark.asyncio
    async def test_evaluate_transition_no_change(self, state_machine_service, sample_state):
        """Test evaluation when no phase change needed."""
        sample_state.phase = Phase.FRIEND
        sample_state.phase_score = 4.0
        
        # Mock dimensions to return same phase
        for name in sample_state.dimensions:
            sample_state.dimensions[name].score = 4.0
        
        should_transition, new_phase, reason = await state_machine_service.evaluate_transition(sample_state)
        assert should_transition is False
        assert new_phase is None

    @pytest.mark.asyncio
    async def test_evaluate_transition_valid(self, state_machine_service, sample_state):
        """Test evaluation with valid phase change."""
        sample_state.phase = Phase.ACQUAINTANCE
        sample_state.phase_score = 2.5
        
        # Mock dimensions to push to friend phase
        for name in sample_state.dimensions:
            sample_state.dimensions[name].score = 4.0
        
        # Mock repo for cooldown and min duration checks
        state_machine_service.repository.get_latest = AsyncMock(return_value=None)
        state_machine_service.repository.list = AsyncMock(return_value=[])
        
        should_transition, new_phase, reason = await state_machine_service.evaluate_transition(sample_state)
        assert should_transition is True
        assert new_phase == Phase.FRIEND

    @pytest.mark.asyncio
    async def test_evaluate_transition_cooldown(self, state_machine_service, sample_state):
        """Test evaluation respects cooldown."""
        sample_state.phase = Phase.ACQUAINTANCE
        for name in sample_state.dimensions:
            sample_state.dimensions[name].score = 4.0
        
        # Mock recent transition (within cooldown)
        recent_transition = StateTransition(
            user_id=sample_state.user_id,
            companion_id=sample_state.companion_id,
            from_phase=Phase.STRANGER,
            to_phase=Phase.ACQUAINTANCE,
            reason="Test",
            triggered_by="auto",
            created_at=datetime.utcnow() - timedelta(minutes=30),
        )
        state_machine_service.repository.get_latest = AsyncMock(return_value=recent_transition)
        
        should_transition, new_phase, reason = await state_machine_service.evaluate_transition(sample_state)
        assert should_transition is False
        assert "Cooldown" in reason

    @pytest.mark.asyncio
    async def test_evaluate_transition_min_duration(self, state_machine_service, sample_state):
        """Test evaluation respects minimum phase duration."""
        sample_state.phase = Phase.FRIEND
        for name in sample_state.dimensions:
            sample_state.dimensions[name].score = 6.0  # Should trigger close_friend
        
        # Mock transition to friend phase that happened recently
        recent_transition = StateTransition(
            user_id=sample_state.user_id,
            companion_id=sample_state.companion_id,
            from_phase=Phase.ACQUAINTANCE,
            to_phase=Phase.FRIEND,
            reason="Test",
            triggered_by="auto",
            created_at=datetime.utcnow() - timedelta(hours=24),  # Less than 168 hours
        )
        state_machine_service.repository.get_latest = AsyncMock(return_value=recent_transition)
        state_machine_service.repository.list = AsyncMock(return_value=[recent_transition])
        
        should_transition, new_phase, reason = await state_machine_service.evaluate_transition(sample_state)
        assert should_transition is False
        assert "Minimum duration" in reason

    @pytest.mark.asyncio
    async def test_execute_transition(self, state_machine_service, sample_state):
        """Test executing a transition."""
        sample_state.phase = Phase.ACQUAINTANCE
        old_phase = sample_state.phase
        
        # Mock repo create
        new_transition = StateTransition(
            user_id=sample_state.user_id,
            companion_id=sample_state.companion_id,
            from_phase=Phase.ACQUAINTANCE,
            to_phase=Phase.FRIEND,
            reason="Test transition",
            triggered_by="auto",
        )
        state_machine_service.repository.create = AsyncMock(return_value=new_transition)
        
        transition = await state_machine_service.execute_transition(
            state=sample_state,
            new_phase=Phase.FRIEND,
            reason="Test transition",
            triggered_by="auto",
        )
        
        assert transition.from_phase == Phase.ACQUAINTANCE
        assert transition.to_phase == Phase.FRIEND
        assert sample_state.phase == Phase.FRIEND
        assert sample_state.metadata["phase_changed"] is True
        assert sample_state.metadata["old_phase"] == "acquaintance"

    @pytest.mark.asyncio
    async def test_force_transition_valid(self, state_machine_service, sample_state):
        """Test forcing a valid transition."""
        sample_state.phase = Phase.FRIEND
        
        new_transition = StateTransition(
            user_id=sample_state.user_id,
            companion_id=sample_state.companion_id,
            from_phase=Phase.FRIEND,
            to_phase=Phase.CLOSE_FRIEND,
            reason="Forced",
            triggered_by="forced",
        )
        state_machine_service.repository.create = AsyncMock(return_value=new_transition)
        
        success, transition, message = await state_machine_service.force_transition(
            state=sample_state,
            target_phase=Phase.CLOSE_FRIEND,
            reason="Forced by admin",
        )
        
        assert success is True
        assert transition.to_phase == Phase.CLOSE_FRIEND
        assert sample_state.phase == Phase.CLOSE_FRIEND

    @pytest.mark.asyncio
    async def test_force_transition_invalid(self, state_machine_service, sample_state):
        """Test forcing an invalid transition."""
        sample_state.phase = Phase.STRANGER
        
        success, transition, message = await state_machine_service.force_transition(
            state=sample_state,
            target_phase=Phase.SOULMATE,
            reason="Invalid jump",
        )
        
        assert success is False
        assert transition is None
        assert "Invalid transition" in message

    @pytest.mark.asyncio
    async def test_can_transition_to(self, state_machine_service, sample_state):
        """Test checking if transition is possible."""
        sample_state.phase = Phase.FRIEND
        for name in sample_state.dimensions:
            sample_state.dimensions[name].score = 6.0
        
        state_machine_service.repository.get_latest = AsyncMock(return_value=None)
        state_machine_service.repository.list = AsyncMock(return_value=[])
        
        can_transition, message = await state_machine_service.can_transition_to(
            sample_state, Phase.CLOSE_FRIEND
        )
        assert can_transition is True
        assert message == "Transition allowed"

    @pytest.mark.asyncio
    async def test_can_transition_to_invalid(self, state_machine_service, sample_state):
        """Test checking invalid transition."""
        sample_state.phase = Phase.FRIEND
        
        can_transition, message = await state_machine_service.can_transition_to(
            sample_state, Phase.SOULMATE
        )
        assert can_transition is False
        assert "Invalid transition" in message