"""Diary Service - Manages relationship diary entries."""

from datetime import datetime
from typing import Any
from uuid import UUID

from relationship_engine.config import settings
from relationship_engine.models.relationship import (
    DiaryEntry,
    RelationshipState,
)
from relationship_engine.repositories.base import DiaryRepository


class DiaryService:
    """Service for managing relationship diary."""

    def __init__(self, repository: DiaryRepository):
        self.repository = repository

    async def add_entry(
        self,
        user_id: UUID,
        companion_id: UUID,
        title: str,
        content: str,
        author: str = "system",
        tags: list[str] | None = None,
        sentiment: float = 0.0,
        importance: int = 3,
        metadata: dict[str, Any] | None = None,
    ) -> DiaryEntry:
        """Add a diary entry."""
        entry = DiaryEntry(
            title=title,
            content=content,
            author=author,
            tags=tags or [],
            sentiment=sentiment,
            importance=importance,
            metadata=metadata or {},
        )

        # The repository expects user_id and companion_id on the model
        entry.user_id = user_id
        entry.companion_id = companion_id

        return await self.repository.create(entry)

    async def get_entry(self, entry_id: UUID) -> DiaryEntry | None:
        """Get a diary entry by ID."""
        return await self.repository.get(entry_id)

    async def list_entries(
        self,
        user_id: UUID,
        companion_id: UUID,
        author: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        tags: list[str] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[DiaryEntry]:
        """List diary entries with filters."""
        return await self.repository.list(
            user_id=user_id,
            companion_id=companion_id,
            author=author,
            start_date=start_date,
            end_date=end_date,
            tags=tags,
            limit=limit,
            offset=offset,
        )

    async def update_entry(self, entry: DiaryEntry) -> DiaryEntry:
        """Update a diary entry."""
        return await self.repository.update(entry)

    async def delete_entry(self, entry_id: UUID) -> bool:
        """Delete a diary entry."""
        return await self.repository.delete(entry_id)

    async def count_entries(
        self,
        user_id: UUID,
        companion_id: UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> int:
        """Count diary entries."""
        return await self.repository.count(
            user_id=user_id,
            companion_id=companion_id,
            start_date=start_date,
            end_date=end_date,
        )

    async def auto_generate_entry(
        self,
        state: RelationshipState,
        period_start: datetime,
        period_end: datetime,
    ) -> DiaryEntry | None:
        """Auto-generate a diary entry based on relationship activity."""
        if not settings.diary_auto_generate:
            return None

        # Check if we already have an entry for this period
        existing = await self.list_entries(
            user_id=state.user_id,
            companion_id=state.companion_id,
            author="system",
            start_date=period_start,
            end_date=period_end,
            limit=1,
        )
        if existing:
            return None  # Already generated

        # Build content based on relationship activity
        title, content = self._generate_diary_content(state, period_start, period_end)

        if not content.strip():
            return None  # Nothing noteworthy

        entry = DiaryEntry(
            title=title,
            content=content,
            author="system",
            tags=["auto-generated", "summary"],
            sentiment=self._calculate_period_sentiment(state),
            importance=3,
            metadata={
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "auto_generated": True,
                "phase": state.phase.value,
                "phase_score": state.phase_score,
            },
        )

        entry.user_id = state.user_id
        entry.companion_id = state.companion_id

        return await self.repository.create(entry)

    def _generate_diary_content(
        self,
        state: RelationshipState,
        period_start: datetime,
        period_end: datetime,
    ) -> tuple[str, str]:
        """Generate diary content from relationship state."""
        lines = []

        # Phase change
        if state.metadata.get("phase_changed"):
            old_phase = state.metadata.get("old_phase", "unknown")
            lines.append(f"🌟 Our relationship evolved from **{old_phase}** to **{state.phase.value}**!")

        # Milestones achieved
        new_milestones = state.metadata.get("new_milestones", [])
        for milestone in new_milestones:
            lines.append(f"🎉 {milestone}")

        # Dimension highlights
        strongest = self._get_strongest_dimensions(state, 2)
        if strongest:
            dims_str = ", ".join([f"**{name}** ({state.dimensions[name].score:.1f}/10)" for name in strongest])
            lines.append(f"💪 Strongest bonds: {dims_str}")

        # Areas for growth
        weakest = self._get_weakest_dimensions(state, 2)
        if weakest:
            dims_str = ", ".join([f"**{name}** ({state.dimensions[name].score:.1f}/10)" for name in weakest])
            lines.append(f"🌱 Room to grow: {dims_str}")

        # Activity summary
        if state.message_count > 0:
            lines.append(f"💬 {state.message_count} messages exchanged this period")

        if state.voice_calls > 0:
            lines.append(f"📞 {state.voice_calls} voice calls")

        if state.memories_shared > 0:
            lines.append(f"🧠 {state.memories_shared} memories shared")

        # Trend summary
        improving = [name for name, dim in state.dimensions.items() if dim.trend > 0.2]
        declining = [name for name, dim in state.dimensions.items() if dim.trend < -0.2]

        if improving:
            lines.append(f"📈 Improving: {', '.join(improving)}")
        if declining:
            lines.append(f"📉 Needs attention: {', '.join(declining)}")

        content = "\n".join(lines) if lines else "A quiet period in our relationship."
        title = f"Weekly Summary: {state.phase.value.title()} Phase"

        return title, content

    def _calculate_period_sentiment(self, state: RelationshipState) -> float:
        """Calculate overall sentiment for the period."""
        if not state.dimensions:
            return 0.0

        # Weighted average of dimension scores, normalized to -1 to 1
        total = sum(dim.score for dim in state.dimensions.values())
        avg = total / len(state.dimensions)

        # Convert 0-10 to -1 to 1
        return round((avg / 10.0) * 2 - 1, 2)

    def _get_strongest_dimensions(self, state: RelationshipState, n: int) -> list[str]:
        """Get top N strongest dimensions."""
        sorted_dims = sorted(
            state.dimensions.items(),
            key=lambda x: x[1].score,
            reverse=True,
        )
        return [name for name, _ in sorted_dims[:n]]

    def _get_weakest_dimensions(self, state: RelationshipState, n: int) -> list[str]:
        """Get bottom N weakest dimensions."""
        sorted_dims = sorted(
            state.dimensions.items(),
            key=lambda x: x[1].score,
        )
        return [name for name, _ in sorted_dims[:n]]

    async def get_recent_entries(
        self,
        user_id: UUID,
        companion_id: UUID,
        days: int = 7,
        limit: int = 10,
    ) -> list[DiaryEntry]:
        """Get recent diary entries."""
        from datetime import timedelta
        start_date = datetime.utcnow() - timedelta(days=days)
        return await self.list_entries(
            user_id=user_id,
            companion_id=companion_id,
            start_date=start_date,
            limit=limit,
        )

    async def get_entries_by_importance(
        self,
        user_id: UUID,
        companion_id: UUID,
        min_importance: int = 4,
        limit: int = 20,
    ) -> list[DiaryEntry]:
        """Get high-importance diary entries."""
        entries = await self.list_entries(
            user_id=user_id,
            companion_id=companion_id,
            limit=limit * 2,  # Fetch more to filter
        )
        # Filter by importance (since we can't easily filter in DB without adding column)
        filtered = [e for e in entries if e.importance >= min_importance]
        return filtered[:limit]

    async def search_entries(
        self,
        user_id: UUID,
        companion_id: UUID,
        query: str,
        limit: int = 20,
    ) -> list[DiaryEntry]:
        """Search diary entries by content (basic implementation)."""
        entries = await self.list_entries(
            user_id=user_id,
            companion_id=companion_id,
            limit=limit * 3,
        )
        query_lower = query.lower()
        results = [
            e for e in entries
            if query_lower in e.content.lower() or query_lower in e.title.lower()
        ]
        return results[:limit]