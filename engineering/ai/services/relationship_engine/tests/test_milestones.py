"""Tests for Milestones Service."""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from relationship_engine.models.relationship import (
    Milestone,
    MilestoneTrigger,
    Phase,
    RelationshipState,
)
from relationship_engine.services.milestones import MilestonesService


@pytest.fixture
def mock_repo():
    """Create a mock milestone repository."""
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.list = AsyncMock(return_value=[])
    repo.get_unachieved = AsyncMock(return_value=[])
    repo.get = AsyncMock()
    return repo


@pytest.fixture
def milestones_service(mock_repo):
    """Create a milestones service instance with mock repo."""
    return MilestonesService(mock_repo)


@pytest.fixture
def sample_state():
    """Create a sample relationship state."""
    state = RelationshipState(
        user_id=uuid4(),
        companion_id=uuid4(),
        message_count=5,
        voice_calls=1,
        memories_shared=0,
        days_known=10,
    )
    # Add some dimensions
    from relationship_engine.models.relationship import Dimension
    state.dimensions["trust"] = Dimension(name="trust", score=6.0)
    state.dimensions["intimacy"] = Dimension(name="intimacy", score=4.0)
    return state


class TestMilestonesService:
    """Test cases for MilestonesService."""

    def test_initialize_milestones(self, milestones_service, sample_state):
        """Test initializing default milestones."""
        milestones = milestones_service.initialize_milestones(sample_state)
        assert len(milestones) > 0
        
        # Check that all default milestones are present
        names = [m.name for m in milestones]
        assert "first_conversation" in names
        assert "first_day" in names
        assert "first_week" in names
        assert "first_month" in names
        assert "trust_5" in names
        assert "intimacy_5" in names
        assert "phase_friend" in names

    def test_generate_celebration_message(self, milestones_service):
        """Test celebration message generation."""
        msg = milestones_service._generate_celebration_message(
            "first_conversation", MilestoneTrigger.MESSAGE_COUNT, 1
        )
        assert "journey begins" in msg or "First conversation" in msg

        msg = milestones_service._generate_celebration_message(
            "phase_soulmate", MilestoneTrigger.PHASE, "soulmate"
        )
        assert "Soulmates" in msg or "soulmate" in msg.lower()

    def test_check_milestone_condition_message_count(self, milestones_service, sample_state):
        """Test checking message count milestone."""
        milestone = Milestone(
            name="test",
            trigger=MilestoneTrigger.MESSAGE_COUNT,
            threshold=5,
        )
        assert milestones_service._check_milestone_condition(sample_state, milestone) is True

        milestone.threshold = 10
        assert milestones_service._check_milestone_condition(sample_state, milestone) is False

    def test_check_milestone_condition_days_known(self, milestones_service, sample_state):
        """Test checking days known milestone."""
        milestone = Milestone(
            name="test",
            trigger=MilestoneTrigger.DAYS_KNOWN,
            threshold=10,
        )
        assert milestones_service._check_milestone_condition(sample_state, milestone) is True

        milestone.threshold = 15
        assert milestones_service._check_milestone_condition(sample_state, milestone) is False

    def test_check_milestone_condition_trust(self, milestones_service, sample_state):
        """Test checking trust dimension milestone."""
        milestone = Milestone(
            name="test",
            trigger=MilestoneTrigger.DIMENSION_TRUST,
            threshold=5.0,
        )
        assert milestones_service._check_milestone_condition(sample_state, milestone) is True

        milestone.threshold = 7.0
        assert milestones_service._check_milestone_condition(sample_state, milestone) is False

    def test_check_milestone_condition_phase(self, milestones_service, sample_state):
        """Test checking phase milestone."""
        sample_state.phase = Phase.FRIEND
        milestone = Milestone(
            name="test",
            trigger=MilestoneTrigger.PHASE,
            threshold="friend",
        )
        assert milestones_service._check_milestone_condition(sample_state, milestone) is True

        milestone.threshold = "close_friend"
        assert milestones_service._check_milestone_condition(sample_state, milestone) is False

    def test_get_current_value(self, milestones_service, sample_state):
        """Test getting current values for different triggers."""
        assert milestones_service._get_current_value(sample_state, Milestone(
            name="", trigger=MilestoneTrigger.MESSAGE_COUNT, threshold=0
        )) == 5.0

        assert milestones_service._get_current_value(sample_state, Milestone(
            name="", trigger=MilestoneTrigger.DAYS_KNOWN, threshold=0
        )) == 10.0

        assert milestones_service._get_current_value(sample_state, Milestone(
            name="", trigger=MilestoneTrigger.DIMENSION_TRUST, threshold=0
        )) == 6.0

    @pytest.mark.asyncio
    async def test_check_milestones_new_achievements(self, milestones_service, sample_state):
        """Test checking milestones returns newly achieved ones."""
        # Add an unachieved milestone that should be achieved
        milestone = Milestone(
            name="test_milestone",
            trigger=MilestoneTrigger.MESSAGE_COUNT,
            threshold=5,
            achieved=False,
        )
        sample_state.milestones = [milestone]

        # Mock repo update
        milestones_service.repository.update = AsyncMock(return_value=milestone)

        newly_achieved = await milestones_service.check_milestones(sample_state)
        assert len(newly_achieved) == 1
        assert newly_achieved[0].name == "test_milestone"
        assert newly_achieved[0].achieved is True
        assert newly_achieved[0].achieved_at is not None

    @pytest.mark.asyncio
    async def test_check_milestones_already_achieved(self, milestones_service, sample_state):
        """Test checking milestones doesn't re-achieve."""
        milestone = Milestone(
            name="test_milestone",
            trigger=MilestoneTrigger.MESSAGE_COUNT,
            threshold=5,
            achieved=True,
            achieved_at=datetime.utcnow(),
        )
        sample_state.milestones = [milestone]

        newly_achieved = await milestones_service.check_milestones(sample_state)
        assert len(newly_achieved) == 0

    def test_get_achievement_progress(self, milestones_service, sample_state):
        """Test getting achievement progress."""
        milestone1 = Milestone(
            name="first_conversation",
            trigger=MilestoneTrigger.MESSAGE_COUNT,
            threshold=1,
            achieved=True,
        )
        milestone2 = Milestone(
            name="hundred_messages",
            trigger=MilestoneTrigger.MESSAGE_COUNT,
            threshold=100,
            achieved=False,
        )
        sample_state.milestones = [milestone1, milestone2]

        progress = milestones_service.get_achievement_progress(sample_state)
        assert len(progress) == 2
        
        # First milestone achieved
        p1 = next(p for p in progress if p["name"] == "first_conversation")
        assert p1["achieved"] is True
        assert p1["progress_percentage"] == 100.0

        # Second milestone in progress
        p2 = next(p for p in progress if p["name"] == "hundred_messages")
        assert p2["achieved"] is False
        assert p2["progress_percentage"] == 5.0  # 5/100 * 100

    def test_get_next_milestones(self, milestones_service, sample_state):
        """Test getting next upcoming milestones."""
        milestone1 = Milestone(
            name="first_conversation",
            trigger=MilestoneTrigger.MESSAGE_COUNT,
            threshold=1,
            achieved=True,
        )
        milestone2 = Milestone(
            name="first_week",
            trigger=MilestoneTrigger.DAYS_KNOWN,
            threshold=7,
            achieved=True,
        )
        milestone3 = Milestone(
            name="first_month",
            trigger=MilestoneTrigger.DAYS_KNOWN,
            threshold=30,
            achieved=False,
        )
        milestone4 = Milestone(
            name="trust_5",
            trigger=MilestoneTrigger.DIMENSION_TRUST,
            threshold=5.0,
            achieved=True,
        )
        sample_state.milestones = [milestone1, milestone2, milestone3, milestone4]

        next_milestones = milestones_service.get_next_milestones(sample_state, limit=2)
        # Should return unachieved ones sorted by progress
        assert len(next_milestones) <= 2
        assert all(not m["achieved"] for m in next_milestones)