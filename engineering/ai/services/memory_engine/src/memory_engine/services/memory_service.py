"""Memory Service - Core service coordinating all memory operations across repositories."""

from typing import Optional, List, Dict, Any
from datetime import datetime
import structlog
import hashlib

from pao_shared.observability import get_tracer, get_meter

from ..models import (
    MemoryType,
    MemoryWrite,
    MemoryRead,
    MemoryUpdate,
    MemoryDelete,
    MemoryResponse,
    MemoryFilter,
    RecallQuery,
    RecallResponse,
    RecallContext,
    EpisodicMemory,
    SemanticMemory,
    EmotionalMemory,
    RelationshipMemory,
    TimelineMemory,
    PreferenceMemory,
    ConsolidationCandidate,
    ConsolidationReport,
)
from ..repositories import (
    MemoryRepository,
    PostgresRepository,
    QdrantRepository,
    KuzuRepository,
    RedisRepository,
)

logger = structlog.get_logger(__name__)


class MemoryService:
    """
    Main Memory Service coordinating all memory operations.
    
    Uses a hybrid storage architecture:
    - PostgreSQL: Relational data, preferences, relationship time-series, audit logs
    - Qdrant: Vector embeddings for semantic similarity search
    - Kuzu: Graph database for entities, relationships, timelines
    - Redis: Caching, session data, rate limiting, real-time events
    """
    
    def __init__(
        self,
        postgres_repo: Optional[PostgresRepository] = None,
        qdrant_repo: Optional[QdrantRepository] = None,
        kuzu_repo: Optional[KuzuRepository] = None,
        redis_repo: Optional[RedisRepository] = None,
    ):
        self.postgres = postgres_repo
        self.qdrant = qdrant_repo
        self.kuzu = kuzu_repo
        self.redis = redis_repo
        
        self._tracer = get_tracer()
        self._meter = get_meter()
        
        # Metrics
        self._write_counter = self._meter.create_counter(
            "memory_write_total", "Total memory writes", {"type"}
        )
        self._read_counter = self._meter.create_counter(
            "memory_read_total", "Total memory reads", {"type"}
        )
        self._recall_counter = self._meter.create_counter(
            "memory_recall_total", "Total recall requests"
        )
        self._write_latency = self._meter.create_histogram(
            "memory_write_duration_seconds", "Memory write latency"
        )
        self._recall_latency = self._meter.create_histogram(
            "memory_recall_duration_seconds", "Memory recall latency"
        )
        self._delete_counter = self._meter.create_counter(
            "memory_delete_total", "Total memory deletions", {"type"}
        )
    
    async def initialize(self) -> None:
        """Initialize all repositories."""
        repos = [
            ("PostgreSQL", self.postgres),
            ("Qdrant", self.qdrant),
            ("Kuzu", self.kuzu),
            ("Redis", self.redis),
        ]
        
        for name, repo in repos:
            if repo:
                try:
                    await repo.initialize()
                    logger.info(f"{name} repository initialized")
                except Exception as e:
                    logger.error(f"Failed to initialize {name} repository", error=str(e))
                    raise
    
    async def close(self) -> None:
        """Close all repositories."""
        repos = [
            ("PostgreSQL", self.postgres),
            ("Qdrant", self.qdrant),
            ("Kuzu", self.kuzu),
            ("Redis", self.redis),
        ]
        
        for name, repo in repos:
            if repo:
                try:
                    await repo.close()
                    logger.info(f"{name} repository closed")
                except Exception as e:
                    logger.error(f"Error closing {name} repository", error=str(e))
    
    def _get_repo_for_type(self, memory_type: MemoryType) -> List[MemoryRepository]:
        """Get appropriate repositories for a memory type."""
        repos = []
        
        if memory_type in [MemoryType.EPISODIC, MemoryType.SEMANTIC, MemoryType.EMOTIONAL]:
            # These use all three: PG (metadata), Qdrant (vectors), Kuzu (entities for semantic)
            if self.postgres:
                repos.append(self.postgres)
            if self.qdrant:
                repos.append(self.qdrant)
            if memory_type == MemoryType.SEMANTIC and self.kuzu:
                repos.append(self.kuzu)
        
        elif memory_type == MemoryType.RELATIONSHIP:
            # Time-series in PostgreSQL
            if self.postgres:
                repos.append(self.postgres)
        
        elif memory_type == MemoryType.TIMELINE:
            # Graph in Kuzu, metadata in PostgreSQL
            if self.kuzu:
                repos.append(self.kuzu)
            if self.postgres:
                repos.append(self.postgres)
        
        elif memory_type == MemoryType.PREFERENCE:
            # PostgreSQL with Redis caching
            if self.postgres:
                repos.append(self.postgres)
            if self.redis:
                repos.append(self.redis)
        
        return repos
    
    async def write(self, request: MemoryWrite) -> MemoryResponse:
        """Write a memory to appropriate storage backends."""
        start_time = datetime.utcnow()
        
        with self._tracer.start_as_current_span("memory_write") as span:
            span.set_attribute("memory_type", request.type.value)
            span.set_attribute("companion_id", request.companion_id)
            
            # Create memory object based on type
            memory = self._create_memory_object(request)
            
            # Write to all appropriate repositories
            repos = self._get_repo_for_type(request.type)
            vector_id = None
            graph_nodes_created = 0
            
            for repo in repos:
                try:
                    if isinstance(repo, PostgresRepository):
                        await self._write_to_postgres(repo, memory, request.type)
                    elif isinstance(repo, QdrantRepository):
                        vector_id = await self._write_to_qdrant(repo, memory, request.type)
                    elif isinstance(repo, KuzuRepository):
                        graph_nodes_created = await self._write_to_kuzu(repo, memory, request.type)
                    elif isinstance(repo, RedisRepository):
                        await self._write_to_redis(repo, memory, request.type)
                except Exception as e:
                    logger.error(f"Failed to write to {type(repo).__name__}", error=str(e))
                    # Continue with other repos
            
            # Track metrics
            latency = (datetime.utcnow() - start_time).total_seconds()
            self._write_counter.add(1, {"type": request.type.value})
            self._write_latency.record(latency)
            
            logger.info(
                "Memory written",
                memory_id=memory.id,
                type=request.type.value,
                companion_id=request.companion_id,
                latency_ms=latency * 1000,
            )
            
            return MemoryResponse(
                memory_id=memory.id,
                type=request.type,
                content=memory.model_dump(),
                version=memory.version,
                created_at=memory.created_at,
                updated_at=memory.updated_at,
                vector_id=vector_id,
                graph_nodes_created=graph_nodes_created,
            )
    
    def _create_memory_object(self, request: MemoryWrite) -> Any:
        """Create memory object from request."""
        base_kwargs = {
            "companion_id": request.companion_id,
            "user_id": request.user_id,
            "source_message_ids": request.source_message_ids,
            "metadata": request.metadata,
            "tags": request.tags,
            "importance": request.importance,
        }
        
        content = request.content
        
        if request.type == MemoryType.EPISODIC:
            return EpisodicMemory(
                **base_kwargs,
                event=content.get("event", ""),
                timestamp=content.get("timestamp", datetime.utcnow().isoformat()),
                participants=content.get("participants", ["user", "companion"]),
                modality=content.get("modality", "text"),
                emotional_tone=content.get("emotional_tone", 0.0),
                emotional_intensity=content.get("emotional_intensity", 0.0),
                topics=content.get("topics", []),
                entities=content.get("entities", []),
            )
        
        elif request.type == MemoryType.SEMANTIC:
            return SemanticMemory(
                **base_kwargs,
                fact=content.get("fact", ""),
                confidence=content.get("confidence", 0.8),
                source=content.get("source", "episodic"),
                source_episodic_ids=content.get("source_episodic_ids", []),
                entities=content.get("entities", []),
                category=content.get("category", "general"),
            )
        
        elif request.type == MemoryType.EMOTIONAL:
            return EmotionalMemory(
                **base_kwargs,
                trigger=content.get("trigger", ""),
                emotion=content.get("emotion", {}),
                intensity=content.get("intensity", 0.5),
                context=content.get("context", ""),
                associated_memories=content.get("associated_memories", []),
                pattern_strength=content.get("pattern_strength", 0.5),
            )
        
        elif request.type == MemoryType.RELATIONSHIP:
            return RelationshipMemory(
                **base_kwargs,
                timestamp=content.get("timestamp", datetime.utcnow().isoformat()),
                dimension_changes=content.get("dimension_changes", {}),
                trigger_event=content.get("trigger_event", ""),
                trigger_type=content.get("trigger_type", "conversation"),
                relationship_type=content.get("relationship_type", "companion"),
                milestone=content.get("milestone"),
                user_perception=content.get("user_perception"),
            )
        
        elif request.type == MemoryType.TIMELINE:
            return TimelineMemory(
                **base_kwargs,
                narrative_arc=content.get("narrative_arc", ""),
                events=content.get("events", []),
                themes=content.get("themes", []),
                status=content.get("status", "active"),
                significance=content.get("significance", 0.5),
                user_curated=content.get("user_curated", False),
            )
        
        elif request.type == MemoryType.PREFERENCE:
            return PreferenceMemory(
                **base_kwargs,
                key=content.get("key", ""),
                value=content.get("value"),
                confidence=content.get("confidence", 0.9),
                source=content.get("source", "explicit"),
                category=content.get("category", "general"),
                expires_at=content.get("expires_at"),
            )
        
        raise ValueError(f"Unknown memory type: {request.type}")
    
    async def _write_to_postgres(self, repo: PostgresRepository, memory: Any, memory_type: MemoryType) -> None:
        """Write memory to PostgreSQL."""
        method_map = {
            MemoryType.EPISODIC: repo.write_episodic,
            MemoryType.SEMANTIC: repo.write_semantic,
            MemoryType.EMOTIONAL: repo.write_emotional,
            MemoryType.RELATIONSHIP: repo.write_relationship,
            MemoryType.TIMELINE: repo.write_timeline,
            MemoryType.PREFERENCE: repo.write_preference,
        }
        method = method_map.get(memory_type)
        if method:
            await method(memory)
    
    async def _write_to_qdrant(self, repo: QdrantRepository, memory: Any, memory_type: MemoryType) -> Optional[str]:
        """Write memory to Qdrant for vector search."""
        method_map = {
            MemoryType.EPISODIC: repo.write_episodic,
            MemoryType.SEMANTIC: repo.write_semantic,
            MemoryType.EMOTIONAL: repo.write_emotional,
        }
        method = method_map.get(memory_type)
        if method:
            return await method(memory)
        return None
    
    async def _write_to_kuzu(self, repo: KuzuRepository, memory: Any, memory_type: MemoryType) -> int:
        """Write memory to Kuzu graph database."""
        if memory_type == MemoryType.SEMANTIC:
            await repo.write_semantic(memory)
            # Count entities as nodes created
            return len(getattr(memory, "entities", []))
        elif memory_type == MemoryType.TIMELINE:
            await repo.write_timeline(memory)
            return len(getattr(memory, "events", []))
        return 0
    
    async def _write_to_redis(self, repo: RedisRepository, memory: Any, memory_type: MemoryType) -> None:
        """Write memory to Redis cache."""
        method_map = {
            MemoryType.EPISODIC: repo.write_episodic,
            MemoryType.SEMANTIC: repo.write_semantic,
            MemoryType.EMOTIONAL: repo.write_emotional,
            MemoryType.PREFERENCE: repo.write_preference,
        }
        method = method_map.get(memory_type)
        if method:
            await method(memory)
    
    async def read(self, request: MemoryRead) -> Optional[MemoryResponse]:
        """Read a memory by ID."""
        start_time = datetime.utcnow()
        
        with self._tracer.start_as_current_span("memory_read") as span:
            span.set_attribute("memory_id", request.memory_id)
            span.set_attribute("companion_id", request.companion_id)
            
            # Try cache first
            if self.redis:
                cached = await self.redis.get_by_id(request.memory_id, request.type)
                if cached:
                    self._read_counter.add(1, {"type": request.type.value, "source": "cache"})
                    return MemoryResponse(
                        memory_id=cached["id"],
                        type=request.type,
                        content=cached,
                        version=cached.get("version", 1),
                        created_at=cached.get("created_at", ""),
                        updated_at=cached.get("updated_at", ""),
                    )
            
            # Try primary storage
            repo = self._get_primary_repo(request.type)
            if repo:
                memory = await repo.get_by_id(request.memory_id, request.type)
                if memory:
                    # Cache for future
                    if self.redis:
                        await self.redis.cache_memory(request.memory_id, request.type, memory.model_dump())
                    
                    self._read_counter.add(1, {"type": request.type.value, "source": "primary"})
                    return MemoryResponse(
                        memory_id=memory.id,
                        type=request.type,
                        content=memory.model_dump(),
                        version=memory.version,
                        created_at=memory.created_at,
                        updated_at=memory.updated_at,
                    )
            
            return None
    
    def _get_primary_repo(self, memory_type: MemoryType) -> Optional[MemoryRepository]:
        """Get primary repository for a memory type."""
        if memory_type in [MemoryType.EPISODIC, MemoryType.SEMANTIC, MemoryType.EMOTIONAL]:
            return self.qdrant or self.postgres
        elif memory_type in [MemoryType.RELATIONSHIP, MemoryType.PREFERENCE]:
            return self.postgres
        elif memory_type == MemoryType.TIMELINE:
            return self.kuzu or self.postgres
        return None
    
    async def recall(self, query: RecallQuery) -> RecallResponse:
        """Context-aware memory recall with reranking."""
        start_time = datetime.utcnow()
        
        with self._tracer.start_as_current_span("memory_recall") as span:
            span.set_attribute("query", query.query[:100])
            span.set_attribute("companion_id", query.companion_id)
            span.set_attribute("limit", query.limit)
            
            # Check recall cache
            if self.redis:
                query_hash = hashlib.md5(
                    f"{query.query}:{query.companion_id}:{query.filters.model_dump() if query.filters else ''}".encode()
                ).hexdigest()
                cached = await self.redis.get_cached_recall(query_hash, query.companion_id)
                if cached:
                    self._recall_counter.add(1, {"source": "cache"})
                    latency = (datetime.utcnow() - start_time).total_seconds() * 1000
                    return RecallResponse(
                        memories=cached,
                        total_candidates=len(cached),
                        latency_ms=latency,
                        query=query.query,
                        companion_id=query.companion_id,
                    )
            
            # Perform recall via Qdrant
            if self.qdrant:
                context = query.context or RecallContext()
                response = await self.qdrant.recall(query, context)
                
                # Cache results
                if self.redis:
                    await self.redis.cache_recall(query_hash, query.companion_id, [m.model_dump() for m in response.memories])
                
                self._recall_counter.add(1, {"source": "qdrant"})
                return response
            
            # Fallback to PostgreSQL query
            if self.postgres and query.filters:
                memories = await self.postgres.query(query.filters)
                # Convert to recall response format
                recalled = []
                for mem in memories[:query.limit]:
                    recalled.append(type('RecalledMemory', (), {
                        'id': mem.id,
                        'type': mem.type,
                        'content': mem.model_dump(),
                        'relevance_score': 0.5,
                        'conversation_score': 0.5,
                        'recall_reason': 'postgres_query',
                    })())
                
                latency = (datetime.utcnow() - start_time).total_seconds() * 1000
                self._recall_counter.add(1, {"source": "postgres"})
                return RecallResponse(
                    memories=recalled,
                    total_candidates=len(recalled),
                    latency_ms=latency,
                    query=query.query,
                    companion_id=query.companion_id,
                )
            
            # No results
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            return RecallResponse(
                memories=[],
                total_candidates=0,
                latency_ms=latency,
                query=query.query,
                companion_id=query.companion_id,
            )
    
    async def update(self, request: MemoryUpdate) -> MemoryResponse:
        """Update a memory (reconsolidation)."""
        start_time = datetime.utcnow()
        
        with self._tracer.start_as_current_span("memory_update") as span:
            span.set_attribute("memory_id", request.memory_id)
            span.set_attribute("companion_id", request.companion_id)
            
            # Get current memory
            current = await self.read(MemoryRead(
                memory_id=request.memory_id,
                companion_id=request.companion_id,
            ))
            
            if not current:
                raise ValueError(f"Memory {request.memory_id} not found")
            
            new_version = current.version + 1
            
            # Update in all repositories
            repos = self._get_repo_for_type(current.type)
            for repo in repos:
                try:
                    await repo.update(
                        request.memory_id,
                        current.type,
                        request.updates,
                        new_version,
                        request.reason,
                    )
                except Exception as e:
                    logger.error(f"Failed to update in {type(repo).__name__}", error=str(e))
            
            # Invalidate caches
            if self.redis:
                await self.redis.invalidate_memory_cache(request.memory_id, current.type)
                await self.redis.invalidate_recall_cache(request.companion_id)
            
            # Get updated memory
            updated = await self.read(MemoryRead(
                memory_id=request.memory_id,
                companion_id=request.companion_id,
            ))
            
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.info(
                "Memory updated",
                memory_id=request.memory_id,
                new_version=new_version,
                latency_ms=latency,
            )
            
            return updated
    
    async def delete(self, request: MemoryDelete) -> Dict[str, Any]:
        """Delete a memory with verification."""
        if not request.confirm:
            raise ValueError("Deletion requires confirmation")
        
        start_time = datetime.utcnow()
        
        with self._tracer.start_as_current_span("memory_delete") as span:
            span.set_attribute("memory_id", request.memory_id)
            span.set_attribute("companion_id", request.companion_id)
            
            # Get memory first to know type
            current = await self.read(MemoryRead(
                memory_id=request.memory_id,
                companion_id=request.companion_id,
            ))
            
            if not current:
                raise ValueError(f"Memory {request.memory_id} not found")
            
            verification_results = {}
            
            # Delete from all repositories
            repos = self._get_repo_for_type(current.type)
            for repo in repos:
                try:
                    result = await repo.delete(
                        request.memory_id,
                        current.type,
                        verification=request.verification == "full",
                    )
                    verification_results[type(repo).__name__] = result
                except Exception as e:
                    logger.error(f"Failed to delete from {type(repo).__name__}", error=str(e))
                    verification_results[type(repo).__name__] = {"error": str(e)}
            
            # Invalidate caches
            if self.redis:
                await self.redis.invalidate_memory_cache(request.memory_id, current.type)
                await self.redis.invalidate_recall_cache(request.companion_id)
            
            self._delete_counter.add(1, {"type": current.type.value})
            
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.info(
                "Memory deleted",
                memory_id=request.memory_id,
                type=current.type.value,
                latency_ms=latency,
            )
            
            return {
                "memory_id": request.memory_id,
                "deleted_at": datetime.utcnow().isoformat(),
                "deletion_proof": verification_results,
            }
    
    async def bulk_delete(self, companion_id: str, scope: Dict[str, Any], 
                          confirm: bool = False) -> Dict[str, Any]:
        """Bulk delete memories by scope (topic, time, type, etc.)."""
        if not confirm:
            raise ValueError("Bulk deletion requires confirmation")
        
        # Build filter from scope
        filter = MemoryFilter(
            companion_id=companion_id,
            types=scope.get("types"),
            date_range=scope.get("date_range"),
            topics=scope.get("topics"),
            tags=scope.get("tags"),
        )
        
        verification_results = {}
        total_deleted = 0
        
        # Delete from each repository
        for repo in [self.postgres, self.qdrant, self.kuzu, self.redis]:
            if repo:
                try:
                    result = await repo.bulk_delete(filter, confirm=True)
                    verification_results[type(repo).__name__] = result
                    total_deleted += result.get("deleted_count", 0)
                except Exception as e:
                    logger.error(f"Bulk delete failed for {type(repo).__name__}", error=str(e))
                    verification_results[type(repo).__name__] = {"error": str(e)}
        
        return {
            "memories_affected": total_deleted,
            "types": scope.get("types", []),
            "deletion_proofs": verification_results,
        }
    
    async def export(self, companion_id: str, user_id: str, 
                     formats: List[str]) -> Dict[str, str]:
        """Export all memories for a companion."""
        export_jobs = {}
        
        # Export from each repository
        for repo in [self.postgres, self.qdrant, self.kuzu, self.redis]:
            if repo:
                try:
                    result = await repo.export_all(companion_id, user_id, formats)
                    export_jobs[type(repo).__name__] = result
                except Exception as e:
                    logger.error(f"Export failed for {type(repo).__name__}", error=str(e))
                    export_jobs[type(repo).__name__] = {"error": str(e)}
        
        return export_jobs
    
    async def get_consolidation_candidates(self, companion_id: str) -> List[ConsolidationCandidate]:
        """Get episodic memories ready for consolidation."""
        if self.postgres:
            memories = await self.postgres.get_consolidation_candidates(companion_id)
            candidates = []
            for mem in memories:
                candidates.append(ConsolidationCandidate(
                    memory_id=mem.id,
                    type=mem.type,
                    content=mem.model_dump(),
                    age_days=(datetime.utcnow() - datetime.fromisoformat(mem.created_at.replace('Z', '+00:00'))).days,
                    access_count=getattr(mem, 'access_count', 0),
                ))
            return candidates
        return []
    
    async def mark_consolidated(self, memory_ids: List[str], semantic_memory_ids: List[str]) -> None:
        """Mark episodic memories as consolidated."""
        for repo in [self.postgres, self.qdrant, self.redis]:
            if repo:
                try:
                    await repo.mark_consolidated(memory_ids, semantic_memory_ids)
                except Exception as e:
                    logger.error(f"Mark consolidated failed for {type(repo).__name__}", error=str(e))
    
    async def run_consistency_validation(self, companion_id: str) -> Dict[str, Any]:
        """Run consistency validation across all memory types."""
        # This would be implemented by ConsistencyService
        return {"status": "not_implemented"}
    
    async def get_memory_stats(self, companion_id: str) -> Dict[str, Any]:
        """Get memory statistics for a companion."""
        stats = {"companion_id": companion_id}
        
        # Get counts from PostgreSQL
        if self.postgres:
            for mem_type in MemoryType:
                filter = MemoryFilter(companion_id=companion_id, type=mem_type, limit=1)
                memories = await self.postgres.query(filter)
                stats[f"{mem_type.value}_count"] = len(memories)
        
        return stats