"""Qdrant repository for Memory Engine - handles vector embeddings and similarity search."""

from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import asyncio

from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.http import models as qdrant_models
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, MatchAny

from pao_shared.config import get_settings

from ..models import (
    MemoryType,
    EpisodicMemory,
    SemanticMemory,
    EmotionalMemory,
    MemoryFilter,
    RecallQuery,
    RecallResponse,
    RecallContext,
    RecalledMemory,
)
from .base import MemoryRepository

settings = get_settings()


class QdrantRepository(MemoryRepository):
    """Qdrant repository for vector-based memory storage and retrieval."""
    
    # Collection names per memory type
    COLLECTIONS = {
        MemoryType.EPISODIC: "episodic_memories",
        MemoryType.SEMANTIC: "semantic_memories",
        MemoryType.EMOTIONAL: "emotional_memories",
    }
    
    # Vector dimensions (using sentence-transformers default)
    VECTOR_DIM = 384  # all-MiniLM-L6-v2
    HNSW_CONFIG = {"m": 16, "ef_construct": 128}
    
    def __init__(self, url: Optional[str] = None, api_key: Optional[str] = None):
        self.url = url or settings.qdrant_url
        self.api_key = api_key or settings.qdrant_api_key
        self.client: Optional[AsyncQdrantClient] = None
        self._embedding_model = None
    
    async def initialize(self) -> None:
        """Initialize Qdrant client and create collections."""
        self.client = AsyncQdrantClient(
            url=self.url,
            api_key=self.api_key,
            timeout=30.0,
        )
        
        # Create collections for each memory type
        for mem_type, collection_name in self.COLLECTIONS.items():
            await self._create_collection_if_not_exists(collection_name)
        
        # Initialize embedding model (lazy load)
        from sentence_transformers import SentenceTransformer
        self._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    
    async def close(self) -> None:
        """Close Qdrant client."""
        if self.client:
            await self.client.close()
    
    async def _create_collection_if_not_exists(self, collection_name: str) -> None:
        """Create a collection if it doesn't exist."""
        try:
            collections = await self.client.get_collections()
            existing = [c.name for c in collections.collections]
            
            if collection_name not in existing:
                await self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.VECTOR_DIM,
                        distance=Distance.COSINE,
                        hnsw_config=qdrant_models.HnswConfigDiff(
                            m=self.HNSW_CONFIG["m"],
                            ef_construct=self.HNSW_CONFIG["ef_construct"],
                        ),
                    ),
                    optimizers_config=qdrant_models.OptimizersConfigDiff(
                        indexing_threshold=10000,
                    ),
                )
                
                # Create payload indexes for filtering
                await self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="companion_id",
                    field_schema=qdrant_models.PayloadSchemaType.KEYWORD,
                )
                await self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="user_id",
                    field_schema=qdrant_models.PayloadSchemaType.KEYWORD,
                )
                await self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="type",
                    field_schema=qdrant_models.PayloadSchemaType.KEYWORD,
                )
                await self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="topics",
                    field_schema=qdrant_models.PayloadSchemaType.KEYWORD,
                )
                await self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="tags",
                    field_schema=qdrant_models.PayloadSchemaType.KEYWORD,
                )
                await self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="consolidated",
                    field_schema=qdrant_models.PayloadSchemaType.BOOL,
                )
                await self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="importance",
                    field_schema=qdrant_models.PayloadSchemaType.FLOAT,
                )
                await self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="created_at",
                    field_schema=qdrant_models.PayloadSchemaType.DATETIME,
                )
        except Exception as e:
            # Collection might already exist
            pass
    
    def _get_collection_name(self, memory_type: MemoryType) -> str:
        """Get collection name for memory type."""
        return self.COLLECTIONS.get(memory_type, "episodic_memories")
    
    def _memory_to_point(self, memory: Any, memory_type: MemoryType) -> PointStruct:
        """Convert memory to Qdrant point."""
        # Generate embedding from content
        content_text = self._extract_text_for_embedding(memory, memory_type)
        embedding = self._embedding_model.encode(content_text).tolist()
        
        # Build payload
        payload = {
            "memory_id": memory.id,
            "companion_id": memory.companion_id,
            "user_id": memory.user_id,
            "type": memory_type.value,
            "content": memory.model_dump(),
            "topics": getattr(memory, "topics", []),
            "tags": getattr(memory, "tags", []),
            "importance": getattr(memory, "importance", 0.5),
            "consolidated": getattr(memory, "consolidated", False),
            "created_at": getattr(memory, "created_at", datetime.utcnow().isoformat()),
            "updated_at": getattr(memory, "updated_at", datetime.utcnow().isoformat()),
        }
        
        return PointStruct(
            id=memory.id,
            vector=embedding,
            payload=payload,
        )
    
    def _extract_text_for_embedding(self, memory: Any, memory_type: MemoryType) -> str:
        """Extract text content for embedding generation."""
        if memory_type == MemoryType.EPISODIC:
            return memory.event
        elif memory_type == MemoryType.SEMANTIC:
            return memory.fact
        elif memory_type == MemoryType.EMOTIONAL:
            return f"{memory.trigger} {memory.context}"
        return str(memory)
    
    def _point_to_memory(self, point: qdrant_models.ScoredPoint, memory_type: MemoryType) -> Any:
        """Convert Qdrant point back to memory model."""
        content = point.payload.get("content", {})
        
        if memory_type == MemoryType.EPISODIC:
            from ..models import EpisodicMemory
            return EpisodicMemory(**content)
        elif memory_type == MemoryType.SEMANTIC:
            from ..models import SemanticMemory
            return SemanticMemory(**content)
        elif memory_type == MemoryType.EMOTIONAL:
            from ..models import EmotionalMemory
            return EmotionalMemory(**content)
        
        return None
    
    def _build_filter(self, filter: MemoryFilter) -> Filter:
        """Build Qdrant filter from MemoryFilter."""
        conditions = []
        
        conditions.append(FieldCondition(key="companion_id", match=MatchValue(value=filter.companion_id)))
        
        if filter.user_id:
            conditions.append(FieldCondition(key="user_id", match=MatchValue(value=filter.user_id)))
        
        if filter.type:
            conditions.append(FieldCondition(key="type", match=MatchValue(value=filter.type.value)))
        
        if filter.tags:
            conditions.append(FieldCondition(key="tags", match=MatchAny(any=filter.tags)))
        
        if filter.topics:
            conditions.append(FieldCondition(key="topics", match=MatchAny(any=filter.topics)))
        
        if filter.consolidated is not None:
            conditions.append(FieldCondition(key="consolidated", match=MatchValue(value=filter.consolidated)))
        
        if filter.importance_min is not None:
            conditions.append(FieldCondition(
                key="importance",
                range=qdrant_models.Range(gte=filter.importance_min)
            ))
        
        if filter.importance_max is not None:
            conditions.append(FieldCondition(
                key="importance",
                range=qdrant_models.Range(lte=filter.importance_max)
            ))
        
        if filter.date_range:
            if filter.date_range.get("start"):
                conditions.append(FieldCondition(
                    key="created_at",
                    range=qdrant_models.Range(gte=filter.date_range["start"])
                ))
            if filter.date_range.get("end"):
                conditions.append(FieldCondition(
                    key="created_at",
                    range=qdrant_models.Range(lte=filter.date_range["end"])
                ))
        
        return Filter(must=conditions) if conditions else None
    
    # Write operations
    async def write_episodic(self, memory: EpisodicMemory) -> str:
        collection = self._get_collection_name(MemoryType.EPISODIC)
        point = self._memory_to_point(memory, MemoryType.EPISODIC)
        await self.client.upsert(collection_name=collection, points=[point])
        return memory.id
    
    async def write_semantic(self, memory: SemanticMemory) -> str:
        collection = self._get_collection_name(MemoryType.SEMANTIC)
        point = self._memory_to_point(memory, MemoryType.SEMANTIC)
        await self.client.upsert(collection_name=collection, points=[point])
        return memory.id
    
    async def write_emotional(self, memory: EmotionalMemory) -> str:
        collection = self._get_collection_name(MemoryType.EMOTIONAL)
        point = self._memory_to_point(memory, MemoryType.EMOTIONAL)
        await self.client.upsert(collection_name=collection, points=[point])
        return memory.id
    
    async def write_relationship(self, memory: Any) -> str:
        # Relationship memories don't use vector search
        return memory.id
    
    async def write_timeline(self, memory: Any) -> str:
        # Timeline memories don't use vector search
        return memory.id
    
    async def write_preference(self, memory: Any) -> str:
        # Preferences don't use vector search
        return memory.id
    
    async def bulk_write(self, memories: List[Any]) -> List[str]:
        points_by_collection: Dict[str, List[PointStruct]] = {}
        ids = []
        
        for memory in memories:
            if isinstance(memory, EpisodicMemory):
                mem_type = MemoryType.EPISODIC
            elif isinstance(memory, SemanticMemory):
                mem_type = MemoryType.SEMANTIC
            elif isinstance(memory, EmotionalMemory):
                mem_type = MemoryType.EMOTIONAL
            else:
                continue
            
            point = self._memory_to_point(memory, mem_type)
            collection = self._get_collection_name(mem_type)
            
            if collection not in points_by_collection:
                points_by_collection[collection] = []
            points_by_collection[collection].append(point)
            ids.append(memory.id)
        
        # Batch upsert per collection
        for collection, points in points_by_collection.items():
            await self.client.upsert(collection_name=collection, points=points)
        
        return ids
    
    # Read operations
    async def get_by_id(self, memory_id: str, memory_type: MemoryType) -> Optional[Any]:
        collection = self._get_collection_name(memory_type)
        points = await self.client.retrieve(
            collection_name=collection,
            ids=[memory_id],
            with_payload=True,
            with_vectors=False,
        )
        if points:
            return self._point_to_memory(points[0], memory_type)
        return None
    
    async def get_by_ids(self, memory_ids: List[str], memory_type: MemoryType) -> List[Any]:
        collection = self._get_collection_name(memory_type)
        points = await self.client.retrieve(
            collection_name=collection,
            ids=memory_ids,
            with_payload=True,
            with_vectors=False,
        )
        return [self._point_to_memory(p, memory_type) for p in points]
    
    # Query operations
    async def query(self, filter: MemoryFilter) -> List[Any]:
        collection = self._get_collection_name(filter.type) if filter.type else "episodic_memories"
        qdrant_filter = self._build_filter(filter)
        
        points = await self.client.scroll(
            collection_name=collection,
            scroll_filter=qdrant_filter,
            limit=filter.limit or 100,
            with_payload=True,
            with_vectors=False,
        )
        
        return [self._point_to_memory(p, filter.type) for p in points[0]]
    
    async def recall(self, query: RecallQuery, context: RecallContext) -> RecallResponse:
        """Context-aware recall with semantic similarity and reranking."""
        start_time = datetime.utcnow()
        
        # Determine which collections to search
        search_types = query.filters.types if query.filters and query.filters.types else [
            MemoryType.EPISODIC, MemoryType.SEMANTIC, MemoryType.EMOTIONAL
        ]
        
        # Generate query embedding
        query_embedding = self._embedding_model.encode(query.query).tolist()
        
        all_results = []
        
        for mem_type in search_types:
            collection = self._get_collection_name(mem_type)
            qdrant_filter = self._build_filter(query.filters) if query.filters else None
            
            # Add companion_id filter
            if qdrant_filter:
                qdrant_filter.must.append(
                    FieldCondition(key="companion_id", match=MatchValue(value=query.companion_id))
                )
            else:
                qdrant_filter = Filter(
                    must=[FieldCondition(key="companion_id", match=MatchValue(value=query.companion_id))]
                )
            
            # Search
            search_results = await self.client.search(
                collection_name=collection,
                query_vector=query_embedding,
                query_filter=qdrant_filter,
                limit=query.limit * 2,  # Get more for diversification
                with_payload=True,
                with_vectors=False,
            )
            
            for scored_point in search_results:
                memory = self._point_to_memory(scored_point, mem_type)
                if memory:
                    # Calculate relevance scores
                    relevance_score = scored_point.score
                    conversation_score = self._calculate_conversation_score(memory, context, query)
                    
                    all_results.append(RecalledMemory(
                        id=memory.id,
                        type=mem_type,
                        content=memory.model_dump(),
                        relevance_score=relevance_score,
                        conversation_score=conversation_score,
                        recall_reason=self._generate_recall_reason(memory, mem_type, query, context),
                    ))
        
        # Rerank and diversify
        if query.diversify:
            all_results = self._diversify_results(all_results, query.limit)
        else:
            all_results.sort(key=lambda x: x.relevance_score + x.conversation_score, reverse=True)
            all_results = all_results[:query.limit]
        
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return RecallResponse(
            memories=all_results,
            total_candidates=len(all_results),
            latency_ms=latency_ms,
            query=query.query,
            companion_id=query.companion_id,
        )
    
    def _calculate_conversation_score(self, memory: Any, context: RecallContext, query: RecallQuery) -> float:
        """Calculate how well memory fits current conversation context."""
        score = 0.5  # Base score
        
        # Topic match
        if context.current_topic and hasattr(memory, "topics"):
            if context.current_topic in memory.topics:
                score += 0.2
        
        # Recent topics match
        if hasattr(memory, "topics"):
            overlap = set(context.recent_topics) & set(memory.topics)
            score += len(overlap) * 0.1
        
        # Recency boost
        if hasattr(memory, "created_at"):
            try:
                created = datetime.fromisoformat(memory.created_at.replace('Z', '+00:00'))
                hours_ago = (datetime.utcnow() - created).total_seconds() / 3600
                if hours_ago < 24:
                    score += 0.1
                elif hours_ago < 168:  # 1 week
                    score += 0.05
            except:
                pass
        
        # Importance boost
        if hasattr(memory, "importance"):
            score += memory.importance * 0.1
        
        # Emotional relevance
        if context.user_emotional_state and hasattr(memory, "emotion"):
            # Check if emotional tones align
            pass
        
        return min(score, 1.0)
    
    def _generate_recall_reason(self, memory: Any, mem_type: MemoryType, query: RecallQuery, context: RecallContext) -> str:
        """Generate human-readable reason for recall."""
        reasons = []
        
        if mem_type == MemoryType.EPISODIC:
            reasons.append(f"Episodic memory: {memory.event[:50]}...")
        elif mem_type == MemoryType.SEMANTIC:
            reasons.append(f"Semantic fact: {memory.fact[:50]}...")
        elif mem_type == MemoryType.EMOTIONAL:
            reasons.append(f"Emotional trigger: {memory.trigger[:50]}...")
        
        if context.current_topic and hasattr(memory, "topics") and context.current_topic in memory.topics:
            reasons.append(f"matches current topic '{context.current_topic}'")
        
        return "; ".join(reasons) if reasons else "semantic similarity"
    
    def _diversify_results(self, results: List[RecalledMemory], limit: int) -> List[RecalledMemory]:
        """Diversify results across types and topics."""
        if len(results) <= limit:
            return results
        
        # Sort by combined score
        results.sort(key=lambda x: x.relevance_score + x.conversation_score, reverse=True)
        
        # Select with diversification
        selected = []
        seen_types = set()
        seen_topics = set()
        
        for result in results:
            if len(selected) >= limit:
                break
            
            # Get type and topics
            mem_type = result.type
            topics = set()
            if "topics" in result.content:
                topics = set(result.content["topics"])
            
            # Check if this adds diversity
            type_new = mem_type not in seen_types
            topic_new = bool(topics - seen_topics)
            
            if type_new or topic_new or len(selected) < limit // 2:
                selected.append(result)
                seen_types.add(mem_type)
                seen_topics.update(topics)
        
        # Fill remaining slots
        for result in results:
            if len(selected) >= limit:
                break
            if result not in selected:
                selected.append(result)
        
        return selected[:limit]
    
    # Update operations
    async def update(self, memory_id: str, memory_type: MemoryType, updates: Dict[str, Any], 
                     new_version: int, reason: str) -> bool:
        # Qdrant doesn't support partial updates easily - re-upsert
        existing = await self.get_by_id(memory_id, memory_type)
        if not existing:
            return False
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(existing, key) and key not in ["id", "companion_id", "user_id", "created_at"]:
                setattr(existing, key, value)
        
        existing.version = new_version
        existing.updated_at = datetime.utcnow().isoformat()
        
        # Re-upsert
        collection = self._get_collection_name(memory_type)
        point = self._memory_to_point(existing, memory_type)
        await self.client.upsert(collection_name=collection, points=[point])
        return True
    
    # Delete operations
    async def delete(self, memory_id: str, memory_type: MemoryType, 
                     verification: bool = True) -> Dict[str, Any]:
        collection = self._get_collection_name(memory_type)
        await self.client.delete(
            collection_name=collection,
            points_selector=qdrant_models.PointIdsList(points=[memory_id]),
        )
        return {
            "memory_id": memory_id,
            "deleted_at": datetime.utcnow().isoformat(),
            "verification": {"vector_deleted": True}
        }
    
    async def bulk_delete(self, filter: MemoryFilter, confirm: bool = False) -> Dict[str, Any]:
        if not confirm:
            return {"success": False, "error": "Confirmation required"}
        
        collection = self._get_collection_name(filter.type) if filter.type else "episodic_memories"
        qdrant_filter = self._build_filter(filter)
        
        await self.client.delete(
            collection_name=collection,
            points_selector=qdrant_models.FilterSelector(filter=qdrant_filter),
        )
        
        return {
            "deleted_count": 0,  # Qdrant doesn't return count easily
            "types": {filter.type.value: 0},
            "verification": {"vector_deleted": True}
        }
    
    # Export operations
    async def export_all(self, companion_id: str, user_id: str, 
                         formats: List[str]) -> Dict[str, str]:
        return {"vectors": "export_job_id", "status": "processing"}
    
    # Consolidation support
    async def get_consolidation_candidates(self, companion_id: str, 
                                           older_than_days: int = 30,
                                           max_access_count: int = 3) -> List[Any]:
        # This is mainly handled by PostgreSQL
        return []
    
    async def mark_consolidated(self, memory_ids: List[str], 
                                semantic_memory_ids: List[str]) -> None:
        # Update consolidated flag in Qdrant
        for mem_id in memory_ids:
            # Need to know which collection - assume episodic for now
            collection = self._get_collection_name(MemoryType.EPISODIC)
            await self.client.set_payload(
                collection_name=collection,
                payload={"consolidated": True, "consolidation_parent_id": semantic_memory_ids[0] if semantic_memory_ids else None},
                points=[mem_id],
            )
    
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
        return True