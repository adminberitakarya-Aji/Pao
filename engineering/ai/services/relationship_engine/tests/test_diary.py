"""Tests for Diary Service."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock

from relationship_engine.models.relationship import (
    DiaryEntry,
    RelationshipState,
    Dimension,
)
from relationship_engine.services.diary import DiaryService


@pytest.fixture
def mock_repo():
    """Create a mock diary repository."""
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.get = AsyncMock()
    repo.list = AsyncMock(return_value=[])
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.count = AsyncMock(return_value=0)
    return repo


@pytest.fixture
def diary_service(mock_repo):
    """Create a diary service instance with mock repo."""
    return DiaryService(mock_repo)


@pytest.fixture
def sample_state():
    """Create a sample relationship state."""
    state = RelationshipState(
        user_id=uuid4(),
        companion_id=uuid4(),
        phase="friend",
        phase_score=4.5,
        message_count=100,
        voice_calls=5,
        memories_shared=3,
        days_known=30,
        created_at=datetime.utcnow() - timedelta(days=30),
    )
    # Add some dimensions
    state.dimensions["trust"] = Dimension(name="trust", score=7.0, trend=0.1)
    state.dimensions["intimacy"] = Dimension(name="intimacy", score=5.0, trend=0.05)
    state.dimensions["affection"] = Dimension(name="affection", score=6.0, trend=-0.1)
    state.dimensions["communication"] = Dimension(name="communication", score=5.5, trend=0.2)
    state.dimensions["respect"] = Dimension(name="respect", score=8.0, trend=0.0)
    return state


class TestDiaryService:
    """Test cases for DiaryService."""

    @pytest.mark.asyncio
    async def test_add_entry(self, diary_service, sample_state):
        """Test adding a diary entry."""
        entry = DiaryEntry(
            title="Test Entry",
            content="Test content",
            author="user",
            tags=["test"],
            sentiment=0.5,
            importance=4,
        )
        entry.user_id = sample_state.user_id
        entry.companion_id = sample_state.companion_id
        
        diary_service.repository.create = AsyncMock(return_value=entry)
        
        created = await diary_service.add_entry(
            user_id=sample_state.user_id,
            companion_id=sample_state.companion_id,
            title="Test Entry",
            content="Test content",
            author="user",
            tags=["test"],
            sentiment=0.5,
            importance=4,
        )
        
        assert created.title == "Test Entry"
        assert created.author == "user"
        assert created.sentiment == 0.5
        assert created.importance == 4

    @pytest.mark.asyncio
    async def test_add_entry_defaults(self, diary_service, sample_state):
        """Test adding entry with default values."""
        entry = DiaryEntry(
            title="Default Entry",
            content="Default content",
        )
        entry.user_id = sample_state.user_id
        entry.companion_id = sample_state.companion_id
        
        diary_service.repository.create = AsyncMock(return_value=entry)
        
        created = await diary_service.add_entry(
            user_id=sample_state.user_id,
            companion_id=sample_state.companion_id,
            title="Default Entry",
            content="Default content",
        )
        
        assert created.author == "system"
        assert created.tags == []
        assert created.sentiment == 0.0
        assert created.importance == 3

    @pytest.mark.asyncio
    async def test_list_entries(self, diary_service, sample_state):
        """Test listing diary entries."""
        entries = [
            DiaryEntry(title="Entry 1", content="Content 1", author="user"),
            DiaryEntry(title="Entry 2", content="Content 2", author="system"),
        ]
        for e in entries:
            e.user_id = sample_state.user_id
            e.companion_id = sample_state.companion_id
        
        diary_service.repository.list = AsyncMock(return_value=entries)
        
        result = await diary_service.list_entries(
            user_id=sample_state.user_id,
            companion_id=sample_state.companion_id,
            limit=10,
        )
        
        assert len(result) == 2
        assert result[0].title == "Entry 1"
        assert result[1].author == "system"

    @pytest.mark.asyncio
    async def test_list_entries_with_filters(self, diary_service, sample_state):
        """Test listing entries with filters."""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        await diary_service.list_entries(
            user_id=sample_state.user_id,
            companion_id=sample_state.companion_id,
            author="user",
            start_date=start_date,
            end_date=end_date,
            tags=["important"],
            limit=5,
            offset=2,
        )
        
        # Verify filters were passed to repo
        call_args = diary_service.repository.list.call_args
        assert call_args.kwargs["author"] == "user"
        assert call_args.kwargs["start_date"] == start_date
        assert call_args.kwargs["end_date"] == end_date
        assert call_args.kwargs["tags"] == ["important"]
        assert call_args.kwargs["limit"] == 5
        assert call_args.kwargs["offset"] == 2

    def test_generate_diary_content(self, diary_service, sample_state):
        """Test generating diary content from state."""
        period_start = datetime.utcnow() - timedelta(days=7)
        period_end = datetime.utcnow()
        
        # Add metadata for phase change
        sample_state.metadata["phase_changed"] = True
        sample_state.metadata["old_phase"] = "acquaintance"
        sample_state.metadata["new_milestones"] = ["first_week", "trust_5"]
        
        title, content = diary_service._generate_diary_content(sample_state, period_start, period_end)
        
        assert "friend" in title.lower()
        assert "acquaintance" in content
        assert "friend" in content
        assert "first_week" in content
        assert "trust_5" in content
        assert "Strongest bonds" in content
        assert "100 messages" in content

    def test_generate_diary_content_empty(self, diary_service, sample_state):
        """Test generating content for empty period."""
        # Reset state
        sample_state.message_count = 0
        sample_state.voice_calls = 0
        sample_state.memories_shared = 0
        sample_state.metadata = {}
        
        title, content = diary_service._generate_diary_content(
            sample_state,
            datetime.utcnow() - timedelta(days=7),
            datetime.utcnow()
        )
        
        assert "quiet period" in content.lower()

    def test_calculate_period_sentiment(self, diary_service, sample_state):
        """Test calculating period sentiment."""
        sentiment = diary_service._calculate_period_sentiment(sample_state)
        
        # Average of dimension scores: (7+5+6+5.5+8+0+0+0+0+0)/10 = 3.15
        # Normalized: (3.15/10)*2 - 1 = -0.37
        assert -1.0 <= sentiment <= 1.0

    def test_get_strongest_dimensions(self, diary_service, sample_state):
        """Test getting strongest dimensions."""
        strongest = diary_service._get_strongest_dimensions(sample_state, 3)
        assert len(strongest) == 3
        assert strongest[0] == "respect"  # 8.0
        assert strongest[1] == "trust"    # 7.0

    def test_get_weakest_dimensions(self, diary_service, sample_state):
        """Test getting weakest dimensions."""
        # Add some low dimensions
        sample_state.dimensions["playfulness"] = Dimension(name="playfulness", score=1.0)
        sample_state.dimensions["growth"] = Dimension(name="growth", score=2.0)
        
        weakest = diary_service._get_weakest_dimensions(sample_state, 2)
        assert len(weakest) == 2
        assert "playfulness" in weakest
        assert "growth" in weakest

    @pytest.mark.asyncio
    async def test_auto_generate_entry(self, diary_service, sample_state):
        """Test auto-generating a diary entry."""
        period_start = datetime.utcnow() - timedelta(days=7)
        period_end = datetime.utcnow()
        
        # Mock no existing entry
        diary_service.repository.list = AsyncMock(return_value=[])
        
        # Mock create
        new_entry = DiaryEntry(
            title="Weekly Summary",
            content="Test summary",
            author="system",
            tags=["auto-generated"],
        )
        new_entry.user_id = sample_state.user_id
        new_entry.companion_id = sample_state.companion_id
        diary_service.repository.create = AsyncMock(return_value=new_entry)
        
        entry = await diary_service.auto_generate_entry(sample_state, period_start, period_end)
        
        assert entry is not None
        assert entry.author == "system"
        assert "auto-generated" in entry.tags

    @pytest.mark.asyncio
    async def test_auto_generate_entry_duplicate(self, diary_service, sample_state):
        """Test auto-generate doesn't create duplicate."""
        period_start = datetime.utcnow() - timedelta(days=7)
        period_end = datetime.utcnow()
        
        # Mock existing entry
        existing = DiaryEntry(
            title="Existing",
            content="Existing",
            author="system",
        )
        existing.user_id = sample_state.user_id
        existing.companion_id = sample_state.companion_id
        diary_service.repository.list = AsyncMock(return_value=[existing])
        
        entry = await diary_service.auto_generate_entry(sample_state, period_start, period_end)
        
        assert entry is None

    @pytest.mark.asyncio
    async def test_get_recent_entries(self, diary_service, sample_state):
        """Test getting recent entries."""
        entries = [DiaryEntry(title=f"Entry {i}", content="Content") for i in range(5)]
        for e in entries:
            e.user_id = sample_state.user_id
            e.companion_id = sample_state.companion_id
        
        diary_service.repository.list = AsyncMock(return_value=entries)
        
        result = await diary_service.get_recent_entries(
            sample_state.user_id,
            sample_state.companion_id,
            days=7,
            limit=10,
        )
        
        assert len(result) == 5
        # Verify start_date was calculated
        call_args = diary_service.repository.list.call_args
        assert call_args.kwargs["start_date"] is not None

    @pytest.mark.asyncio
    async def test_search_entries(self, diary_service, sample_state):
        """Test searching diary entries."""
        entries = [
            DiaryEntry(title="Happy day", content="We had a great time", author="user"),
            DiaryEntry(title="Sad day", content="Feeling down today", author="user"),
            DiaryEntry(title="Normal day", content="Just a regular day", author="system"),
        ]
        for e in entries:
            e.user_id = sample_state.user_id
            e.companion_id = sample_state.companion_id
        
        diary_service.repository.list = AsyncMock(return_value=entries)
        
        result = await diary_service.search_entries(
            sample_state.user_id,
            sample_state.companion_id,
            "great",
            limit=10,
        )
        
        assert len(result) == 1
        assert "great" in result[0].content.lower()

    @pytest.mark.asyncio
    async def test_get_entries_by_importance(self, diary_service, sample_state):
        """Test getting high-importance entries."""
        entries = [
            DiaryEntry(title="Low", content="Low", importance=1),
            DiaryEntry(title="Medium", content="Medium", importance=3),
            DiaryEntry(title="High", content="High", importance=5),
            DiaryEntry(title="Very High", content="Very High", importance=4),
        ]
        for e in entries:
            e.user_id = sample_state.user_id
            e.companion_id = sample_state.companion_id
        
        diary_service.repository.list = AsyncMock(return_value=entries)
        
        result = await diary_service.get_entries_by_importance(
            sample_state.user_id,
            sample_state.companion_id,
            min_importance=4,
            limit=10,
        )
        
        assert len(result) == 2
        assert all(e.importance >= 4 for e in result)