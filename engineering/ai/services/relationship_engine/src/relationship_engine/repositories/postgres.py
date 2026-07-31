"""PostgreSQL Repository Implementations for Relationship Engine."""

import json
from datetime import datetime
from typing import Any
from uuid import UUID

import asyncpg
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    select,
    func,
    and_,
    or_,
    delete,
    update,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship

from relationship_engine.config import settings
from relationship_engine.models.relationship import (
    DiaryEntry,
    Milestone,
    MilestoneTrigger,
    Phase,
    RelationshipState,
    StateTransition,
    Dimension,
)
from relationship_engine.repositories.base import (
    RelationshipRepository,
    MilestoneRepository,
    DiaryRepository,
    StateTransitionRepository,
)

Base = declarative_base()


class RelationshipModel(Base):
    """SQLAlchemy model for relationship state."""

    __tablename__ = "relationships"

    user_id = Column(PG_UUID(as_uuid=True), primary_key=True)
    companion_id = Column(PG_UUID(as_uuid=True), primary_key=True)
    dimensions = Column(JSONB, default={}, nullable=False)
    phase = Column(String(50), default=Phase.STRANGER.value, nullable=False)
    phase_score = Column(Float, default=0.0, nullable=False)
    message_count = Column(Integer, default=0, nullable=False)
    voice_calls = Column(Integer, default=0, nullable=False)
    memories_shared = Column(Integer, default=0, nullable=False)
    days_known = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_interaction_at = Column(DateTime, nullable=True)
    metadata = Column(JSONB, default={}, nullable=False)

    # Relationships
    milestones = relationship("MilestoneModel", back_populates="relationship", cascade="all, delete-orphan")
    diary_entries = relationship("DiaryEntryModel", back_populates="relationship", cascade="all, delete-orphan")
    state_transitions = relationship("StateTransitionModel", back_populates="relationship", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_relationships_user_id", "user_id"),
        Index("ix_relationships_companion_id", "companion_id"),
        Index("ix_relationships_updated_at", "updated_at"),
    )


class MilestoneModel(Base):
    """SQLAlchemy model for milestones."""

    __tablename__ = "milestones"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("relationships.user_id"), nullable=False)
    companion_id = Column(PG_UUID(as_uuid=True), ForeignKey("relationships.companion_id"), nullable=False)
    name = Column(String(200), nullable=False)
    trigger = Column(String(50), nullable=False)
    threshold = Column(Text, nullable=False)  # Store as string to support both float and phase names
    achieved = Column(Integer, default=0, nullable=False)  # 0 or 1
    achieved_at = Column(DateTime, nullable=True)
    celebration_message = Column(Text, nullable=True)
    metadata = Column(JSONB, default={}, nullable=False)

    # Relationship
    relationship = relationship("RelationshipModel", back_populates="milestones")

    __table_args__ = (
        Index("ix_milestones_user_companion", "user_id", "companion_id"),
        Index("ix_milestones_achieved", "achieved"),
    )


class DiaryEntryModel(Base):
    """SQLAlchemy model for diary entries."""

    __tablename__ = "diary_entries"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("relationships.user_id"), nullable=False)
    companion_id = Column(PG_UUID(as_uuid=True), ForeignKey("relationships.companion_id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String(20), default="system", nullable=False)
    tags = Column(JSONB, default=[], nullable=False)
    sentiment = Column(Float, default=0.0, nullable=False)
    importance = Column(Integer, default=3, nullable=False)
    metadata = Column(JSONB, default={}, nullable=False)

    # Relationship
    relationship = relationship("RelationshipModel", back_populates="diary_entries")

    __table_args__ = (
        Index("ix_diary_user_companion", "user_id", "companion_id"),
        Index("ix_diary_date", "date"),
        Index("ix_diary_author", "author"),
    )


class StateTransitionModel(Base):
    """SQLAlchemy model for state transitions."""

    __tablename__ = "state_transitions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("relationships.user_id"), nullable=False)
    companion_id = Column(PG_UUID(as_uuid=True), ForeignKey("relationships.companion_id"), nullable=False)
    from_phase = Column(String(50), nullable=True)
    to_phase = Column(String(50), nullable=False)
    reason = Column(Text, nullable=False)
    triggered_by = Column(String(50), nullable=False)  # system, user, companion, auto
    metadata = Column(JSONB, default={}, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    relationship = relationship("RelationshipModel", back_populates="state_transitions")

    __table_args__ = (
        Index("ix_transitions_user_companion", "user_id", "companion_id"),
        Index("ix_transitions_created_at", "created_at"),
    )


class PostgresRelationshipRepository(RelationshipRepository):
    """PostgreSQL implementation of RelationshipRepository."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def create(self, relationship: RelationshipState) -> RelationshipState:
        async with self.session_factory() as session:
            # Convert dimensions to JSON-serializable format
            dimensions_data = {
                name: {
                    "name": dim.name,
                    "score": dim.score,
                    "trend": dim.trend,
                    "last_updated": dim.last_updated.isoformat(),
                    "interaction_count": dim.interaction_count,
                    "metadata": dim.metadata,
                }
                for name, dim in relationship.dimensions.items()
            }

            model = RelationshipModel(
                user_id=relationship.user_id,
                companion_id=relationship.companion_id,
                dimensions=dimensions_data,
                phase=relationship.phase.value,
                phase_score=relationship.phase_score,
                message_count=relationship.message_count,
                voice_calls=relationship.voice_calls,
                memories_shared=relationship.memories_shared,
                days_known=relationship.days_known,
                created_at=relationship.created_at,
                updated_at=relationship.updated_at,
                last_interaction_at=relationship.last_interaction_at,
                metadata=relationship.metadata,
            )
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return self._model_to_state(model)

    async def get(self, user_id: UUID, companion_id: UUID) -> RelationshipState | None:
        async with self.session_factory() as session:
            result = await session.execute(
                select(RelationshipModel).where(
                    and_(
                        RelationshipModel.user_id == user_id,
                        RelationshipModel.companion_id == companion_id,
                    )
                )
            )
            model = result.scalar_one_or_none()
            if model:
                return self._model_to_state(model)
            return None

    async def update(self, relationship: RelationshipState) -> RelationshipState:
        async with self.session_factory() as session:
            # Convert dimensions to JSON-serializable format
            dimensions_data = {
                name: {
                    "name": dim.name,
                    "score": dim.score,
                    "trend": dim.trend,
                    "last_updated": dim.last_updated.isoformat(),
                    "interaction_count": dim.interaction_count,
                    "metadata": dim.metadata,
                }
                for name, dim in relationship.dimensions.items()
            }

            await session.execute(
                update(RelationshipModel)
                .where(
                    and_(
                        RelationshipModel.user_id == relationship.user_id,
                        RelationshipModel.companion_id == relationship.companion_id,
                    )
                )
                .values(
                    dimensions=dimensions_data,
                    phase=relationship.phase.value,
                    phase_score=relationship.phase_score,
                    message_count=relationship.message_count,
                    voice_calls=relationship.voice_calls,
                    memories_shared=relationship.memories_shared,
                    days_known=relationship.days_known,
                    updated_at=datetime.utcnow(),
                    last_interaction_at=relationship.last_interaction_at,
                    metadata=relationship.metadata,
                )
            )
            await session.commit()

            # Reload and return
            return await self.get(relationship.user_id, relationship.companion_id) or relationship

    async def delete(self, user_id: UUID, companion_id: UUID) -> bool:
        async with self.session_factory() as session:
            result = await session.execute(
                delete(RelationshipModel).where(
                    and_(
                        RelationshipModel.user_id == user_id,
                        RelationshipModel.companion_id == companion_id,
                    )
                )
            )
            await session.commit()
            return result.rowcount > 0

    async def list_by_user(self, user_id: UUID, limit: int = 50, offset: int = 0) -> list[RelationshipState]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(RelationshipModel)
                .where(RelationshipModel.user_id == user_id)
                .order_by(RelationshipModel.updated_at.desc())
                .limit(limit)
                .offset(offset)
            )
            models = result.scalars().all()
            return [self._model_to_state(m) for m in models]

    async def list_by_companion(self, companion_id: UUID, limit: int = 50, offset: int = 0) -> list[RelationshipState]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(RelationshipModel)
                .where(RelationshipModel.companion_id == companion_id)
                .order_by(RelationshipModel.updated_at.desc())
                .limit(limit)
                .offset(offset)
            )
            models = result.scalars().all()
            return [self._model_to_state(m) for m in models]

    def _model_to_state(self, model: RelationshipModel) -> RelationshipState:
        """Convert SQLAlchemy model to RelationshipState."""
        dimensions = {}
        for name, dim_data in model.dimensions.items():
            dimensions[name] = Dimension(
                name=dim_data["name"],
                score=dim_data["score"],
                trend=dim_data["trend"],
                last_updated=datetime.fromisoformat(dim_data["last_updated"]),
                interaction_count=dim_data["interaction_count"],
                metadata=dim_data.get("metadata", {}),
            )

        return RelationshipState(
            user_id=model.user_id,
            companion_id=model.companion_id,
            dimensions=dimensions,
            phase=Phase(model.phase),
            phase_score=model.phase_score,
            message_count=model.message_count,
            voice_calls=model.voice_calls,
            memories_shared=model.memories_shared,
            days_known=model.days_known,
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_interaction_at=model.last_interaction_at,
            metadata=model.metadata,
        )


class PostgresMilestoneRepository(MilestoneRepository):
    """PostgreSQL implementation of MilestoneRepository."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def create(self, milestone: Milestone) -> Milestone:
        async with self.session_factory() as session:
            model = MilestoneModel(
                id=milestone.id,
                user_id=milestone.user_id if hasattr(milestone, "user_id") else None,
                companion_id=milestone.companion_id if hasattr(milestone, "companion_id") else None,
                name=milestone.name,
                trigger=milestone.trigger.value,
                threshold=str(milestone.threshold),
                achieved=1 if milestone.achieved else 0,
                achieved_at=milestone.achieved_at,
                celebration_message=milestone.celebration_message,
                metadata=milestone.metadata,
            )
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return self._model_to_milestone(model)

    async def get(self, milestone_id: UUID) -> Milestone | None:
        async with self.session_factory() as session:
            result = await session.execute(
                select(MilestoneModel).where(MilestoneModel.id == milestone_id)
            )
            model = result.scalar_one_or_none()
            if model:
                return self._model_to_milestone(model)
            return None

    async def list(
        self,
        user_id: UUID,
        companion_id: UUID,
        achieved_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Milestone]:
        async with self.session_factory() as session:
            query = select(MilestoneModel).where(
                and_(
                    MilestoneModel.user_id == user_id,
                    MilestoneModel.companion_id == companion_id,
                )
            )
            if achieved_only:
                query = query.where(MilestoneModel.achieved == 1)
            query = query.order_by(MilestoneModel.achieved.asc(), MilestoneModel.id).limit(limit).offset(offset)
            result = await session.execute(query)
            models = result.scalars().all()
            return [self._model_to_milestone(m) for m in models]

    async def update(self, milestone: Milestone) -> Milestone:
        async with self.session_factory() as session:
            await session.execute(
                update(MilestoneModel)
                .where(MilestoneModel.id == milestone.id)
                .values(
                    achieved=1 if milestone.achieved else 0,
                    achieved_at=milestone.achieved_at,
                    celebration_message=milestone.celebration_message,
                    metadata=milestone.metadata,
                )
            )
            await session.commit()
            return await self.get(milestone.id) or milestone

    async def delete(self, milestone_id: UUID) -> bool:
        async with self.session_factory() as session:
            result = await session.execute(
                delete(MilestoneModel).where(MilestoneModel.id == milestone_id)
            )
            await session.commit()
            return result.rowcount > 0

    async def get_unachieved(self, user_id: UUID, companion_id: UUID) -> list[Milestone]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(MilestoneModel).where(
                    and_(
                        MilestoneModel.user_id == user_id,
                        MilestoneModel.companion_id == companion_id,
                        MilestoneModel.achieved == 0,
                    )
                )
            )
            models = result.scalars().all()
            return [self._model_to_milestone(m) for m in models]

    def _model_to_milestone(self, model: MilestoneModel) -> Milestone:
        """Convert SQLAlchemy model to Milestone."""
        # Parse threshold - could be float or phase name
        try:
            threshold = float(model.threshold)
        except ValueError:
            threshold = model.threshold

        return Milestone(
            id=model.id,
            name=model.name,
            trigger=MilestoneTrigger(model.trigger),
            threshold=threshold,
            achieved=bool(model.achieved),
            achieved_at=model.achieved_at,
            celebration_message=model.celebration_message,
            metadata=model.metadata,
        )


class PostgresDiaryRepository(DiaryRepository):
    """PostgreSQL implementation of DiaryRepository."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def create(self, entry: DiaryEntry) -> DiaryEntry:
        async with self.session_factory() as session:
            model = DiaryEntryModel(
                id=entry.id,
                user_id=entry.user_id if hasattr(entry, "user_id") else None,
                companion_id=entry.companion_id if hasattr(entry, "companion_id") else None,
                date=entry.date,
                title=entry.title,
                content=entry.content,
                author=entry.author,
                tags=entry.tags,
                sentiment=entry.sentiment,
                importance=entry.importance,
                metadata=entry.metadata,
            )
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return self._model_to_entry(model)

    async def get(self, entry_id: UUID) -> DiaryEntry | None:
        async with self.session_factory() as session:
            result = await session.execute(
                select(DiaryEntryModel).where(DiaryEntryModel.id == entry_id)
            )
            model = result.scalar_one_or_none()
            if model:
                return self._model_to_entry(model)
            return None

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
        async with self.session_factory() as session:
            query = select(DiaryEntryModel).where(
                and_(
                    DiaryEntryModel.user_id == user_id,
                    DiaryEntryModel.companion_id == companion_id,
                )
            )
            if author:
                query = query.where(DiaryEntryModel.author == author)
            if start_date:
                query = query.where(DiaryEntryModel.date >= start_date)
            if end_date:
                query = query.where(DiaryEntryModel.date <= end_date)
            if tags:
                # JSONB contains check for tags
                for tag in tags:
                    query = query.where(DiaryEntryModel.tags.contains([tag]))

            query = query.order_by(DiaryEntryModel.date.desc()).limit(limit).offset(offset)
            result = await session.execute(query)
            models = result.scalars().all()
            return [self._model_to_entry(m) for m in models]

    async def update(self, entry: DiaryEntry) -> DiaryEntry:
        async with self.session_factory() as session:
            await session.execute(
                update(DiaryEntryModel)
                .where(DiaryEntryModel.id == entry.id)
                .values(
                    title=entry.title,
                    content=entry.content,
                    author=entry.author,
                    tags=entry.tags,
                    sentiment=entry.sentiment,
                    importance=entry.importance,
                    metadata=entry.metadata,
                )
            )
            await session.commit()
            return await self.get(entry.id) or entry

    async def delete(self, entry_id: UUID) -> bool:
        async with self.session_factory() as session:
            result = await session.execute(
                delete(DiaryEntryModel).where(DiaryEntryModel.id == entry_id)
            )
            await session.commit()
            return result.rowcount > 0

    async def count(
        self,
        user_id: UUID,
        companion_id: UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> int:
        async with self.session_factory() as session:
            query = select(func.count(DiaryEntryModel.id)).where(
                and_(
                    DiaryEntryModel.user_id == user_id,
                    DiaryEntryModel.companion_id == companion_id,
                )
            )
            if start_date:
                query = query.where(DiaryEntryModel.date >= start_date)
            if end_date:
                query = query.where(DiaryEntryModel.date <= end_date)
            result = await session.execute(query)
            return result.scalar() or 0

    def _model_to_entry(self, model: DiaryEntryModel) -> DiaryEntry:
        """Convert SQLAlchemy model to DiaryEntry."""
        return DiaryEntry(
            id=model.id,
            date=model.date,
            title=model.title,
            content=model.content,
            author=model.author,
            tags=model.tags,
            sentiment=model.sentiment,
            importance=model.importance,
            metadata=model.metadata,
        )


class PostgresStateTransitionRepository(StateTransitionRepository):
    """PostgreSQL implementation of StateTransitionRepository."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def create(self, transition: StateTransition) -> StateTransition:
        async with self.session_factory() as session:
            model = StateTransitionModel(
                id=transition.id,
                user_id=transition.user_id if hasattr(transition, "user_id") else None,
                companion_id=transition.companion_id if hasattr(transition, "companion_id") else None,
                from_phase=transition.from_phase.value if transition.from_phase else None,
                to_phase=transition.to_phase.value,
                reason=transition.reason,
                triggered_by=transition.triggered_by,
                metadata=transition.metadata,
                created_at=transition.created_at,
            )
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return self._model_to_transition(model)

    async def list(
        self,
        user_id: UUID,
        companion_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[StateTransition]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(StateTransitionModel)
                .where(
                    and_(
                        StateTransitionModel.user_id == user_id,
                        StateTransitionModel.companion_id == companion_id,
                    )
                )
                .order_by(StateTransitionModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            models = result.scalars().all()
            return [self._model_to_transition(m) for m in models]

    async def get_latest(self, user_id: UUID, companion_id: UUID) -> StateTransition | None:
        async with self.session_factory() as session:
            result = await session.execute(
                select(StateTransitionModel)
                .where(
                    and_(
                        StateTransitionModel.user_id == user_id,
                        StateTransitionModel.companion_id == companion_id,
                    )
                )
                .order_by(StateTransitionModel.created_at.desc())
                .limit(1)
            )
            model = result.scalar_one_or_none()
            if model:
                return self._model_to_transition(model)
            return None

    async def count_since(
        self,
        user_id: UUID,
        companion_id: UUID,
        since: datetime,
    ) -> int:
        async with self.session_factory() as session:
            result = await session.execute(
                select(func.count(StateTransitionModel.id)).where(
                    and_(
                        StateTransitionModel.user_id == user_id,
                        StateTransitionModel.companion_id == companion_id,
                        StateTransitionModel.created_at >= since,
                    )
                )
            )
            return result.scalar() or 0

    def _model_to_transition(self, model: StateTransitionModel) -> StateTransition:
        """Convert SQLAlchemy model to StateTransition."""
        return StateTransition(
            id=model.id,
            from_phase=Phase(model.from_phase) if model.from_phase else None,
            to_phase=Phase(model.to_phase),
            reason=model.reason,
            triggered_by=model.triggered_by,
            metadata=model.metadata,
            created_at=model.created_at,
        )


async def create_engine_and_session():
    """Create database engine and session factory."""
    engine = create_async_engine(
        settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        echo=settings.environment == "development",
    )
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return engine, session_factory


async def init_db():
    """Initialize database tables."""
    engine, _ = await create_engine_and_session()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()