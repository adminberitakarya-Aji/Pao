"""PostgreSQL repository for Memory Engine - handles relational data, preferences, relationship time-series."""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import uuid

from sqlalchemy import (
    create_engine, Column, String, Text, DateTime, Float, Integer, 
    Boolean, JSON, ForeignKey, Index, select, and_, or_, func, delete, update
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ARRAY

from pao_shared.config import get_settings

from ..models import (
    MemoryType,
    EpisodicMemory,
    SemanticMemory,
    EmotionalMemory,
    RelationshipMemory,
    TimelineMemory,
    PreferenceMemory,
    MemoryFilter,
    RecallQuery,
    RecallResponse,
    RecallContext,
)
from .base import MemoryRepository

settings = get_settings()
Base = declarative_base()


class EpisodicMemoryModel(Base):
    __tablename__ = "episodic_memories"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    companion_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    event = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    participants = Column(ARRAY(String), default=[])
    modality = Column(String(20), default="text")
    emotional_tone = Column(Float, default=0.0)
    emotional_intensity = Column(Float, default=0.0)
    topics = Column(ARRAY(String), default=[])
    entities = Column(JSON, default=[])
    source_message_ids = Column(ARRAY(String), default=[])
    version = Column(Integer, default=1)
    consolidated = Column(Boolean, default=False, index=True)
    consolidation_parent_id = Column(PG_UUID(as_uuid=True), nullable=True)
    importance = Column(Float, default=0.5)
    metadata = Column(JSON, default={})
    tags = Column(ARRAY(String), default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_episodic_companion_timestamp", "companion_id", "timestamp"),
        Index("ix_episodic_companion_consolidated", "companion_id", "consolidated"),
    )


class SemanticMemoryModel(Base):
    __tablename__ = "semantic_memories"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    companion_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    fact = Column(Text, nullable=False)
    confidence = Column(Float, default=0.8)
    source = Column(String(20), default="episodic")
    source_episodic_ids = Column(ARRAY(PG_UUID(as_uuid=True)), default=[])
    entities = Column(JSON, default=[])
    category = Column(String(50), default="general", index=True)
    contradicted_by = Column(PG_UUID(as_uuid=True), nullable=True)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    access_count = Column(Integer, default=0)
    importance = Column(Float, default=0.5)
    metadata = Column(JSON, default={})
    tags = Column(ARRAY(String), default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_semantic_companion_category", "companion_id", "category"),
        Index("ix_semantic_companion_confidence", "companion_id", "confidence"),
    )


class EmotionalMemoryModel(Base):
    __tablename__ = "emotional_memories"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    companion_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    trigger = Column(Text, nullable=False)
    emotion = Column(JSON, nullable=False)
    intensity = Column(Float, default=0.5)
    context = Column(Text, default="")
    associated_memories = Column(ARRAY(PG_UUID(as_uuid=True)), default=[])
    pattern_strength = Column(Float, default=0.5)
    last_activated = Column(DateTime, default=datetime.utcnow)
    user_validated = Column(Boolean, default=False)
    importance = Column(Float, default=0.5)
    metadata = Column(JSON, default={})
    tags = Column(ARRAY(String), default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RelationshipMemoryModel(Base):
    __tablename__ = "relationship_memories"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    companion_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    dimension_changes = Column(JSON, nullable=False)
    trigger_event = Column(Text, nullable=False)
    trigger_type = Column(String(20), nullable=False)
    relationship_type = Column(String(50), default="companion")
    milestone = Column(String(100), nullable=True)
    user_perception = Column(Float, nullable=True)
    importance = Column(Float, default=0.5)
    metadata = Column(JSON, default={})
    tags = Column(ARRAY(String), default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_relationship_companion_created", "companion_id", "created_at"),
    )


class TimelineMemoryModel(Base):
    __tablename__ = "timeline_memories"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    companion_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    narrative_arc = Column(Text, nullable=False)
    events = Column(JSON, nullable=False)
    themes = Column(ARRAY(String), default=[])
    status = Column(String(20), default="active", index=True)
    significance = Column(Float, default=0.5)
    user_curated = Column(Boolean, default=False)
    importance = Column(Float, default=0.5)
    metadata = Column(JSON, default={})
    tags = Column(ARRAY(String), default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PreferenceMemoryModel(Base):
    __tablename__ = "preference_memories"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    companion_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    key = Column(String(200), nullable=False, index=True)
    value = Column(JSON, nullable=False)
    confidence = Column(Float, default=1.0)
    source = Column(String(20), default="explicit")
    category = Column(String(50), default="general", index=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    importance = Column(Float, default=0.5)
    metadata = Column(JSON, default={})
    tags = Column(ARRAY(String), default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_preference_companion_key", "companion_id", "key", unique=True),
        Index("ix_preference_companion_category", "companion_id", "category"),
    )


class MemoryVersionModel(Base):
    """Version history for memories."""
    __tablename__ = "memory_versions"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    memory_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    memory_type = Column(String(20), nullable=False)
    version = Column(Integer, nullable=False)
    content_snapshot = Column(JSON, nullable=False)
    change_reason = Column(Text)
    changed_by = Column(String(100))
    source_message_id = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_version_memory_version", "memory_id", "version"),
    )


class PostgresRepository(MemoryRepository):
    """PostgreSQL repository for relational memory data."""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.database_url
        self.engine = None
        self.session_factory = None
    
    async def initialize(self) -> None:
        """Initialize database connection and create tables."""
        # Convert to async URL
        async_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://")
        self.engine = create_async_engine(
            async_url,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            echo=settings.environment == "development",
        )
        self.session_factory = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def close(self) -> None:
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()
    
    async def _get_session(self) -> AsyncSession:
        """Get a database session."""
        if not self.session_factory:
            await self.initialize()
        return self.session_factory()
    
    # Write operations
    async def write_episodic(self, memory: EpisodicMemory) -> str:
        async with await self._get_session() as session:
            model = EpisodicMemoryModel(
                id=uuid.UUID(memory.id) if isinstance(memory.id, str) else memory.id,
                companion_id=uuid.UUID(memory.companion_id),
                user_id=uuid.UUID(memory.user_id),
                event=memory.event,
                timestamp=datetime.fromisoformat(memory.timestamp.replace('Z', '+00:00')),
                participants=memory.participants,
                modality=memory.modality,
                emotional_tone=memory.emotional_tone,
                emotional_intensity=memory.emotional_intensity,
                topics=memory.topics,
                entities=memory.entities,
                source_message_ids=memory.source_message_ids,
                version=memory.version,
                consolidated=memory.consolidated,
                consolidation_parent_id=uuid.UUID(memory.consolidation_parent_id) if memory.consolidation_parent_id else None,
                importance=memory.importance,
                metadata=memory.metadata,
                tags=memory.tags,
            )
            session.add(model)
            await session.commit()
            return str(model.id)
    
    async def write_semantic(self, memory: SemanticMemory) -> str:
        async with await self._get_session() as session:
            model = SemanticMemoryModel(
                id=uuid.UUID(memory.id) if isinstance(memory.id, str) else memory.id,
                companion_id=uuid.UUID(memory.companion_id),
                user_id=uuid.UUID(memory.user_id),
                fact=memory.fact,
                confidence=memory.confidence,
                source=memory.source,
                source_episodic_ids=[uuid.UUID(eid) for eid in memory.source_episodic_ids],
                entities=memory.entities,
                category=memory.category,
                contradicted_by=uuid.UUID(memory.contradicted_by) if memory.contradicted_by else None,
                last_accessed=datetime.fromisoformat(memory.last_accessed.replace('Z', '+00:00')),
                access_count=memory.access_count,
                importance=memory.importance,
                metadata=memory.metadata,
                tags=memory.tags,
            )
            session.add(model)
            await session.commit()
            return str(model.id)
    
    async def write_emotional(self, memory: EmotionalMemory) -> str:
        async with await self._get_session() as session:
            model = EmotionalMemoryModel(
                id=uuid.UUID(memory.id) if isinstance(memory.id, str) else memory.id,
                companion_id=uuid.UUID(memory.companion_id),
                user_id=uuid.UUID(memory.user_id),
                trigger=memory.trigger,
                emotion=memory.emotion,
                intensity=memory.intensity,
                context=memory.context,
                associated_memories=[uuid.UUID(mid) for mid in memory.associated_memories],
                pattern_strength=memory.pattern_strength,
                last_activated=datetime.fromisoformat(memory.last_activated.replace('Z', '+00:00')),
                user_validated=memory.user_validated,
                importance=memory.importance,
                metadata=memory.metadata,
                tags=memory.tags,
            )
            session.add(model)
            await session.commit()
            return str(model.id)
    
    async def write_relationship(self, memory: RelationshipMemory) -> str:
        async with await self._get_session() as session:
            model = RelationshipMemoryModel(
                id=uuid.UUID(memory.id) if isinstance(memory.id, str) else memory.id,
                companion_id=uuid.UUID(memory.companion_id),
                user_id=uuid.UUID(memory.user_id),
                dimension_changes=memory.dimension_changes,
                trigger_event=memory.trigger_event,
                trigger_type=memory.trigger_type,
                relationship_type=memory.relationship_type,
                milestone=memory.milestone,
                user_perception=memory.user_perception,
                importance=memory.importance,
                metadata=memory.metadata,
                tags=memory.tags,
            )
            session.add(model)
            await session.commit()
            return str(model.id)
    
    async def write_timeline(self, memory: TimelineMemory) -> str:
        async with await self._get_session() as session:
            model = TimelineMemoryModel(
                id=uuid.UUID(memory.id) if isinstance(memory.id, str) else memory.id,
                companion_id=uuid.UUID(memory.companion_id),
                user_id=uuid.UUID(memory.user_id),
                narrative_arc=memory.narrative_arc,
                events=memory.events,
                themes=memory.themes,
                status=memory.status,
                significance=memory.significance,
                user_curated=memory.user_curated,
                importance=memory.importance,
                metadata=memory.metadata,
                tags=memory.tags,
            )
            session.add(model)
            await session.commit()
            return str(model.id)
    
    async def write_preference(self, memory: PreferenceMemory) -> str:
        async with await self._get_session() as session:
            # Upsert preference
            stmt = select(PreferenceMemoryModel).where(
                and_(
                    PreferenceMemoryModel.companion_id == uuid.UUID(memory.companion_id),
                    PreferenceMemoryModel.key == memory.key,
                )
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                existing.value = memory.value
                existing.confidence = memory.confidence
                existing.source = memory.source
                existing.category = memory.category
                existing.last_updated = datetime.utcnow()
                existing.expires_at = datetime.fromisoformat(memory.expires_at.replace('Z', '+00:00')) if memory.expires_at else None
                existing.importance = memory.importance
                existing.metadata = memory.metadata
                existing.tags = memory.tags
                await session.commit()
                return str(existing.id)
            else:
                model = PreferenceMemoryModel(
                    id=uuid.UUID(memory.id) if isinstance(memory.id, str) else memory.id,
                    companion_id=uuid.UUID(memory.companion_id),
                    user_id=uuid.UUID(memory.user_id),
                    key=memory.key,
                    value=memory.value,
                    confidence=memory.confidence,
                    source=memory.source,
                    category=memory.category,
                    last_updated=datetime.fromisoformat(memory.last_updated.replace('Z', '+00:00')),
                    expires_at=datetime.fromisoformat(memory.expires_at.replace('Z', '+00:00')) if memory.expires_at else None,
                    importance=memory.importance,
                    metadata=memory.metadata,
                    tags=memory.tags,
                )
                session.add(model)
                await session.commit()
                return str(model.id)
    
    async def bulk_write(self, memories: List[Any]) -> List[str]:
        ids = []
        for memory in memories:
            if isinstance(memory, EpisodicMemory):
                ids.append(await self.write_episodic(memory))
            elif isinstance(memory, SemanticMemory):
                ids.append(await self.write_semantic(memory))
            elif isinstance(memory, EmotionalMemory):
                ids.append(await self.write_emotional(memory))
            elif isinstance(memory, RelationshipMemory):
                ids.append(await self.write_relationship(memory))
            elif isinstance(memory, TimelineMemory):
                ids.append(await self.write_timeline(memory))
            elif isinstance(memory, PreferenceMemory):
                ids.append(await self.write_preference(memory))
        return ids
    
    # Read operations
    async def get_by_id(self, memory_id: str, memory_type: MemoryType) -> Optional[Any]:
        async with await self._get_session() as session:
            model_class = self._get_model_class(memory_type)
            if not model_class:
                return None
            
            stmt = select(model_class).where(model_class.id == uuid.UUID(memory_id))
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._model_to_memory(model, memory_type) if model else None
    
    async def get_by_ids(self, memory_ids: List[str], memory_type: MemoryType) -> List[Any]:
        async with await self._get_session() as session:
            model_class = self._get_model_class(memory_type)
            if not model_class:
                return []
            
            uuid_ids = [uuid.UUID(mid) for mid in memory_ids]
            stmt = select(model_class).where(model_class.id.in_(uuid_ids))
            result = await session.execute(stmt)
            models = result.scalars().all()
            return [self._model_to_memory(m, memory_type) for m in models]
    
    # Query operations
    async def query(self, filter: MemoryFilter) -> List[Any]:
        async with await self._get_session() as session:
            model_class = self._get_model_class(filter.type) if filter.type else None
            
            if model_class:
                stmt = select(model_class).where(model_class.companion_id == uuid.UUID(filter.companion_id))
                
                if filter.user_id:
                    stmt = stmt.where(model_class.user_id == uuid.UUID(filter.user_id))
                
                if filter.date_range:
                    if filter.date_range.get("start"):
                        stmt = stmt.where(model_class.created_at >= datetime.fromisoformat(filter.date_range["start"].replace('Z', '+00:00')))
                    if filter.date_range.get("end"):
                        stmt = stmt.where(model_class.created_at <= datetime.fromisoformat(filter.date_range["end"].replace('Z', '+00:00')))
                
                if filter.tags:
                    stmt = stmt.where(model_class.tags.op('&&')(filter.tags))
                
                if filter.importance_min is not None:
                    stmt = stmt.where(model_class.importance >= filter.importance_min)
                
                stmt = stmt.order_by(model_class.created_at.desc()).limit(filter.limit or 100)
                
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [self._model_to_memory(m, filter.type) for m in models]
            
            return []
    
    async def recall(self, query: RecallQuery, context: RecallContext) -> RecallResponse:
        """PostgreSQL doesn't handle vector recall - delegate to Qdrant."""
        # This is a stub - actual recall is handled by QdrantRepository
        return RecallResponse(
            memories=[],
            total_candidates=0,
            latency_ms=0,
        )
    
    # Update operations
    async def update(self, memory_id: str, memory_type: MemoryType, updates: Dict[str, Any], 
                     new_version: int, reason: str) -> bool:
        async with await self._get_session() as session:
            model_class = self._get_model_class(memory_type)
            if not model_class:
                return False
            
            stmt = select(model_class).where(model_class.id == uuid.UUID(memory_id))
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                return False
            
            # Save version history
            version_entry = MemoryVersionModel(
                memory_id=uuid.UUID(memory_id),
                memory_type=memory_type.value,
                version=model.version,
                content_snapshot=self._model_to_dict(model),
                change_reason=reason,
                changed_by=updates.get("changed_by", "system"),
                source_message_id=updates.get("source_message_id"),
            )
            session.add(version_entry)
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(model, key) and key not in ["id", "companion_id", "user_id", "created_at"]:
                    setattr(model, key, value)
            
            model.version = new_version
            model.updated_at = datetime.utcnow()
            
            await session.commit()
            return True
    
    # Delete operations
    async def delete(self, memory_id: str, memory_type: MemoryType, 
                     verification: bool = True) -> Dict[str, Any]:
        async with await self._get_session() as session:
            model_class = self._get_model_class(memory_type)
            if not model_class:
                return {"success": False, "error": "Invalid memory type"}
            
            stmt = select(model_class).where(model_class.id == uuid.UUID(memory_id))
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                return {"success": False, "error": "Memory not found"}
            
            if verification:
                # In real implementation, verify with user confirmation
                pass
            
            await session.delete(model)
            await session.commit()
            
            return {
                "memory_id": memory_id,
                "deleted_at": datetime.utcnow().isoformat(),
                "verification": {"relational_deleted": True}
            }
    
    async def bulk_delete(self, filter: MemoryFilter, confirm: bool = False) -> Dict[str, Any]:
        if not confirm:
            return {"success": False, "error": "Confirmation required"}
        
        async with await self._get_session() as session:
            model_class = self._get_model_class(filter.type)
            if not model_class:
                return {"success": False, "error": "Invalid memory type"}
            
            stmt = delete(model_class).where(model_class.companion_id == uuid.UUID(filter.companion_id))
            
            if filter.user_id:
                stmt = stmt.where(model_class.user_id == uuid.UUID(filter.user_id))
            
            if filter.date_range:
                if filter.date_range.get("start"):
                    stmt = stmt.where(model_class.created_at >= datetime.fromisoformat(filter.date_range["start"].replace('Z', '+00:00')))
                if filter.date_range.get("end"):
                    stmt = stmt.where(model_class.created_at <= datetime.fromisoformat(filter.date_range["end"].replace('Z', '+00:00')))
            
            if filter.tags:
                stmt = stmt.where(model_class.tags.op('&&')(filter.tags))
            
            result = await session.execute(stmt)
            await session.commit()
            
            return {
                "deleted_count": result.rowcount,
                "types": {filter.type.value: result.rowcount},
                "verification": {"relational_deleted": True}
            }
    
    # Export operations
    async def export_all(self, companion_id: str, user_id: str, 
                         formats: List[str]) -> Dict[str, str]:
        """Export all memories - placeholder for full implementation."""
        return {"json": "export_job_id", "status": "processing"}
    
    # Consolidation support
    async def get_consolidation_candidates(self, companion_id: str, 
                                           older_than_days: int = 30,
                                           max_access_count: int = 3) -> List[Any]:
        async with await self._get_session() as session:
            cutoff = datetime.utcnow() - timedelta(days=older_than_days)
            
            stmt = select(EpisodicMemoryModel).where(
                and_(
                    EpisodicMemoryModel.companion_id == uuid.UUID(companion_id),
                    EpisodicMemoryModel.consolidated == False,
                    EpisodicMemoryModel.created_at < cutoff,
                    EpisodicMemoryModel.access_count < max_access_count,
                    EpisodicMemoryModel.importance < 0.7,  # Not user-protected
                )
            ).order_by(EpisodicMemoryModel.created_at).limit(1000)
            
            result = await session.execute(stmt)
            models = result.scalars().all()
            return [self._model_to_memory(m, MemoryType.EPISODIC) for m in models]
    
    async def mark_consolidated(self, memory_ids: List[str], 
                                semantic_memory_ids: List[str]) -> None:
        async with await self._get_session() as session:
            uuid_ids = [uuid.UUID(mid) for mid in memory_ids]
            stmt = update(EpisodicMemoryModel).where(
                EpisodicMemoryModel.id.in_(uuid_ids)
            ).values(
                consolidated=True,
                consolidation_parent_id=uuid.UUID(semantic_memory_ids[0]) if semantic_memory_ids else None,
                updated_at=datetime.utcnow(),
            )
            await session.execute(stmt)
            await session.commit()
    
    # Consistency validation
    async def get_memories_for_validation(self, companion_id: str, 
                                           memory_types: List[MemoryType]) -> List[Any]:
        memories = []
        for mem_type in memory_types:
            filter = MemoryFilter(companion_id=companion_id, type=mem_type, limit=10000)
            memories.extend(await self.query(filter))
        return memories
    
    async def resolve_contradiction(self, issue_id: str, resolution: str,
                                     resolved_by: str) -> bool:
        # Placeholder - would update the consistency tracking table
        return True
    
    # Helper methods
    def _get_model_class(self, memory_type: MemoryType):
        mapping = {
            MemoryType.EPISODIC: EpisodicMemoryModel,
            MemoryType.SEMANTIC: SemanticMemoryModel,
            MemoryType.EMOTIONAL: EmotionalMemoryModel,
            MemoryType.RELATIONSHIP: RelationshipMemoryModel,
            MemoryType.TIMELINE: TimelineMemoryModel,
            MemoryType.PREFERENCE: PreferenceMemoryModel,
        }
        return mapping.get(memory_type)
    
    def _model_to_memory(self, model: Any, memory_type: MemoryType) -> Any:
        """Convert SQLAlchemy model to Pydantic memory model."""
        if memory_type == MemoryType.EPISODIC:
            return EpisodicMemory(
                id=str(model.id),
                companion_id=str(model.companion_id),
                user_id=str(model.user_id),
                event=model.event,
                timestamp=model.timestamp.isoformat(),
                participants=model.participants,
                modality=model.modality,
                emotional_tone=model.emotional_tone,
                emotional_intensity=model.emotional_intensity,
                topics=model.topics,
                entities=model.entities,
                source_message_ids=model.source_message_ids,
                version=model.version,
                consolidated=model.consolidated,
                consolidation_parent_id=str(model.consolidation_parent_id) if model.consolidation_parent_id else None,
                importance=model.importance,
                metadata=model.metadata,
                tags=model.tags,
                created_at=model.created_at.isoformat(),
                updated_at=model.updated_at.isoformat(),
            )
        elif memory_type == MemoryType.SEMANTIC:
            return SemanticMemory(
                id=str(model.id),
                companion_id=str(model.companion_id),
                user_id=str(model.user_id),
                fact=model.fact,
                confidence=model.confidence,
                source=model.source,
                source_episodic_ids=[str(eid) for eid in model.source_episodic_ids],
                entities=model.entities,
                category=model.category,
                contradicted_by=str(model.contradicted_by) if model.contradicted_by else None,
                last_accessed=model.last_accessed.isoformat(),
                access_count=model.access_count,
                importance=model.importance,
                metadata=model.metadata,
                tags=model.tags,
                created_at=model.created_at.isoformat(),
                updated_at=model.updated_at.isoformat(),
            )
        elif memory_type == MemoryType.EMOTIONAL:
            return EmotionalMemory(
                id=str(model.id),
                companion_id=str(model.companion_id),
                user_id=str(model.user_id),
                trigger=model.trigger,
                emotion=model.emotion,
                intensity=model.intensity,
                context=model.context,
                associated_memories=[str(mid) for mid in model.associated_memories],
                pattern_strength=model.pattern_strength,
                last_activated=model.last_activated.isoformat(),
                user_validated=model.user_validated,
                importance=model.importance,
                metadata=model.metadata,
                tags=model.tags,
                created_at=model.created_at.isoformat(),
                updated_at=model.updated_at.isoformat(),
            )
        elif memory_type == MemoryType.RELATIONSHIP:
            return RelationshipMemory(
                id=str(model.id),
                companion_id=str(model.companion_id),
                user_id=str(model.user_id),
                dimension_changes=model.dimension_changes,
                trigger_event=model.trigger_event,
                trigger_type=model.trigger_type,
                relationship_type=model.relationship_type,
                milestone=model.milestone,
                user_perception=model.user_perception,
                importance=model.importance,
                metadata=model.metadata,
                tags=model.tags,
                created_at=model.created_at.isoformat(),
                updated_at=model.updated_at.isoformat(),
            )
        elif memory_type == MemoryType.TIMELINE:
            return TimelineMemory(
                id=str(model.id),
                companion_id=str(model.companion_id),
                user_id=str(model.user_id),
                narrative_arc=model.narrative_arc,
                events=model.events,
                themes=model.themes,
                status=model.status,
                significance=model.significance,
                user_curated=model.user_curated,
                importance=model.importance,
                metadata=model.metadata,
                tags=model.tags,
                created_at=model.created_at.isoformat(),
                updated_at=model.updated_at.isoformat(),
            )
        elif memory_type == MemoryType.PREFERENCE:
            return PreferenceMemory(
                id=str(model.id),
                companion_id=str(model.companion_id),
                user_id=str(model.user_id),
                key=model.key,
                value=model.value,
                confidence=model.confidence,
                source=model.source,
                category=model.category,
                last_updated=model.last_updated.isoformat(),
                expires_at=model.expires_at.isoformat() if model.expires_at else None,
                importance=model.importance,
                metadata=model.metadata,
                tags=model.tags,
                created_at=model.created_at.isoformat(),
                updated_at=model.updated_at.isoformat(),
            )
        return None
    
    def _model_to_dict(self, model: Any) -> Dict[str, Any]:
        """Convert model to dictionary for versioning."""
        return {c.name: getattr(model, c.name) for c in model.__table__.columns}