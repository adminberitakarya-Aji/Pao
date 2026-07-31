"""Base Repository Interfaces for Relationship Engine."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from uuid import UUID

from relationship_engine.models.relationship import (
    DiaryEntry,
    Milestone,
    Phase,
    RelationshipState,
    StateTransition,
)


class RelationshipRepository(ABC):
    """Interface for relationship state persistence."""

    @abstractmethod
    async def create(self, relationship: RelationshipState) -> RelationshipState:
        """Create a new relationship."""
        pass

    @abstractmethod
    async def get(self, user_id: UUID, companion_id: UUID) -> RelationshipState | None:
        """Get relationship by user and companion IDs."""
        pass

    @abstractmethod
    async def update(self, relationship: RelationshipState) -> RelationshipState:
        """Update relationship state."""
        pass

    @abstractmethod
    async def delete(self, user_id: UUID, companion_id: UUID) -> bool:
        """Delete relationship."""
        pass

    @abstractmethod
    async def list_by_user(self, user_id: UUID, limit: int = 50, offset: int = 0) -> list[RelationshipState]:
        """List relationships for a user."""
        pass

    @abstractmethod
    async def list_by_companion(self, companion_id: UUID, limit: int = 50, offset: int = 0) -> list[RelationshipState]:
        """List relationships for a companion."""
        pass


class MilestoneRepository(ABC):
    """Interface for milestone persistence."""

    @abstractmethod
    async def create(self, milestone: Milestone) -> Milestone:
        """Create a new milestone."""
        pass

    @abstractmethod
    async def get(self, milestone_id: UUID) -> Milestone | None:
        """Get milestone by ID."""
        pass

    @abstractmethod
    async def list(
        self,
        user_id: UUID,
        companion_id: UUID,
        achieved_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Milestone]:
        """List milestones for a relationship."""
        pass

    @abstractmethod
    async def update(self, milestone: Milestone) -> Milestone:
        """Update milestone."""
        pass

    @abstractmethod
    async def delete(self, milestone_id: UUID) -> bool:
        """Delete milestone."""
        pass

    @abstractmethod
    async def get_unachieved(self, user_id: UUID, companion_id: UUID) -> list[Milestone]:
        """Get all unachieved milestones for a relationship."""
        pass


class DiaryRepository(ABC):
    """Interface for diary entry persistence."""

    @abstractmethod
    async def create(self, entry: DiaryEntry) -> DiaryEntry:
        """Create a new diary entry."""
        pass

    @abstractmethod
    async def get(self, entry_id: UUID) -> DiaryEntry | None:
        """Get diary entry by ID."""
        pass

    @abstractmethod
    async def list(
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
        pass

    @abstractmethod
    async def update(self, entry: DiaryEntry) -> DiaryEntry:
        """Update diary entry."""
        pass

    @abstractmethod
    async def delete(self, entry_id: UUID) -> bool:
        """Delete diary entry."""
        pass

    @abstractmethod
    async def count(
        self,
        user_id: UUID,
        companion_id: UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> int:
        """Count diary entries."""
        pass


class StateTransitionRepository(ABC):
    """Interface for state transition history."""

    @abstractmethod
    async def create(self, transition: StateTransition) -> StateTransition:
        """Record a state transition."""
        pass

    @abstractmethod
    async def list(
        self,
        user_id: UUID,
        companion_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[StateTransition]:
        """List state transitions for a relationship."""
        pass

    @abstractmethod
    async def get_latest(self, user_id: UUID, companion_id: UUID) -> StateTransition | None:
        """Get the most recent state transition."""
        pass

    @abstractmethod
    async def count_since(
        self,
        user_id: UUID,
        companion_id: UUID,
        since: datetime,
    ) -> int:
        """Count transitions since a timestamp."""
        pass