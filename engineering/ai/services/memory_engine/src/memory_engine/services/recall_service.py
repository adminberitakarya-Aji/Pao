"""Recall Service - Advanced context-aware memory recall with reranking."""

from typing import Optional, List, Dict, Any
from datetime import datetime
import structlog

from pao_shared.observability import get_tracer, get_meter

from ..models import (
    MemoryType,
    RecallQuery,
    RecallResponse,
    RecallContext,
    RecalledMemory,
    MemoryFilter,
)
from ..repositories import (
    QdrantRepository,
    PostgresRepository,
    KuzuRepository,
    RedisRepository,
)

logger = structlog.get_logger(__name__)


class RecallService:
    """
    Advanced recall service with multiple retrieval strategies:
    - Semantic similarity (vector search)
    - Graph traversal (entity relationships)
    - Temporal queries (recent, time-range)
    - Emotional resonance
    - Relationship relevance
    """
    
    def __init__(
        self,
        qdrant_repo: Optional[QdrantRepository] = None,
        postgres_repo: Optional[PostgresRepository] = None,
        kuzu_repo: Optional[KuzuRepository] = None,
        redis_repo: Optional[RedisRepository] = None,
    ):
        self.qdrant = qdrant_repo
        self.postgres = postgres_repo
        self.kuzu = kuzu_repo
        self.redis = redis_repo
        
        self._tracer = get_tracer()
        self._meter = get_meter()
        
        # Metrics
        self._recall_requests = self._meter.create_counter(
            "recall_requests_total", "Total recall requests", {"strategy"}
        )
        self._recall_latency = self._meter.create_histogram(
            "recall_latency_seconds", "Recall latency"
        )
        self._results_returned = self._meter.create_histogram(
            "recall_results_count", "Number of results returned"
        )
    
    async def recall(self, query: RecallQuery) -> RecallResponse:
        """
        Main recall entry point with multi-strategy retrieval and reranking.
        """
        start_time = datetime.utcnow()
        
        with self._tracer.start_as_current_span("recall") as span:
            span.set_attribute("query", query.query[:100])
            span.set_attribute("companion_id", query.companion_id)
            span.set_attribute("limit", query.limit)
            
            context = query.context or RecallContext()
            
            # Strategy 1: Semantic similarity (vector search)
            semantic_results = await self._semantic_recall(query, context)
            self._recall_requests.add(1, {"strategy": "semantic"})
            
            # Strategy 2: Graph-based entity traversal
            graph_results = await self._graph_recall(query, context)
            self._recall_requests.add(1, {"strategy": "graph"})
            
            # Strategy 3: Temporal/recent memories
            temporal_results = await self._temporal_recall(query, context)
            self._recall_requests.add(1, {"strategy": "temporal"})
            
            # Strategy 4: Emotional resonance
            emotional_results = await self._emotional_recall(query, context)
            self._recall_requests.add(1, {"strategy": "emotional"})
            
            # Strategy 5: Relationship relevance
            relationship_results = await self._relationship_recall(query, context)
            self._recall_requests.add(1, {"strategy": "relationship"})
            
            # Merge and rerank all results
            all_results = self._merge_results([
                semantic_results, graph_results, temporal_results,
                emotional_results, relationship_results
            ])
            
            # Apply diversification if requested
            if query.diversify:
                all_results = self._diversify(all_results, query.limit)
            else:
                all_results = all_results[:query.limit]
            
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            self._results_returned.record(len(all_results))
            self._recall_latency.record(latency / 1000)
            
            logger.info(
                "Recall completed",
                query=query.query[:50],
                companion_id=query.companion_id,
                total_candidates=len(semantic_results) + len(graph_results) + len(temporal_results),
                returned=len(all_results),
                latency_ms=latency,
            )
            
            return RecallResponse(
                memories=all_results,
                total_candidates=len(semantic_results) + len(graph_results) + len(temporal_results),
                latency_ms=latency,
                query=query.query,
                companion_id=query.companion_id,
            )
    
    async def _semantic_recall(
        self, query: RecallQuery, context: RecallContext
    ) -> List[RecalledMemory]:
        """Semantic similarity search via Qdrant."""
        if not self.qdrant:
            return []
        
        return await self.qdrant.recall(query, context)
    
    async def _graph_recall(
        self, query: RecallQuery, context: RecallContext
    ) -> List[RecalledMemory]:
        """Graph traversal for entity-related memories."""
        if not self.kuzu:
            return []
        
        results = []
        
        # Extract entities from query
        # In production, would use NER
        query_entities = self._extract_entities(query.query)
        
        for entity in query_entities:
            # Find related entities in graph
            neighbors = await self.kuzu.get_entity_neighbors(entity, max_depth=2)
            
            for neighbor_data in neighbors:
                # Get facts for this entity
                facts = await self.kuzu.get_facts_by_entity(neighbor_data.get("id", ""))
                
                for fact in facts:
                    results.append(RecalledMemory(
                        id=fact.get("id", ""),
                        type=MemoryType.SEMANTIC,
                        content=fact,
                        relevance_score=0.7,
                        conversation_score=0.6,
                        recall_reason=f"Graph traversal: related to '{entity}'",
                    ))
        
        return results
    
    async def _temporal_recall(
        self, query: RecallQuery, context: RecallContext
    ) -> List[RecalledMemory]:
        """Temporal queries for recent or time-range memories."""
        if not self.postgres:
            return []
        
        results = []
        
        # Recent memories
        if self.redis:
            recent = await self.redis.get_recent_memories(
                query.companion_id,
                limit=query.limit,
                memory_types=query.filters.types if query.filters else None
            )
            
            for mem in recent:
                results.append(RecalledMemory(
                    id=mem["memory_id"],
                    type=mem["type"],
                    content={"recent": True, "timestamp": mem["timestamp"]},
                    relevance_score=0.5,
                    conversation_score=0.8,
                    recall_reason="Recent memory",
                ))
        
        # Time-range queries
        if query.filters and query.filters.date_range:
            filter = query.filters
            for mem_type in filter.types or [MemoryType.EPISODIC, MemoryType.SEMANTIC]:
                memories = await self.postgres.query(filter)
                for mem in memories[:query.limit]:
                    results.append(RecalledMemory(
                        id=mem.id,
                        type=mem.type,
                        content=mem.model_dump(),
                        relevance_score=0.6,
                        conversation_score=0.5,
                        recall_reason="Time-range match",
                    ))
        
        return results
    
    async def _emotional_recall(
        self, query: RecallQuery, context: RecallContext
    ) -> List[RecalledMemory]:
        """Emotional resonance search."""
        if not self.qdrant:
            return []
        
        results = []
        
        # If user emotional state provided, find matching emotional memories
        if context.user_emotional_state:
            # Create query from emotional state
            emotional_query = " ".join([
                f"{k}:{v}" for k, v in context.user_emotional_state.items()
            ])
            
            emotional_filter = MemoryFilter(
                companion_id=query.companion_id,
                type=MemoryType.EMOTIONAL,
                limit=query.limit,
            )
            
            emotional_memories = await self.qdrant.query(emotional_filter)
            
            for mem in emotional_memories:
                # Score by emotional similarity
                similarity = self._emotional_similarity(
                    context.user_emotional_state,
                    mem.content.get("emotion", {})
                )
                
                if similarity > 0.3:
                    results.append(RecalledMemory(
                        id=mem.id,
                        type=MemoryType.EMOTIONAL,
                        content=mem.model_dump(),
                        relevance_score=similarity,
                        conversation_score=0.7,
                        recall_reason=f"Emotional resonance: {similarity:.0%} match",
                    ))
        
        return results
    
    async def _relationship_recall(
        self, query: RecallQuery, context: RecallContext
    ) -> List[RecalledMemory]:
        """Relationship dimension relevant memories."""
        if not self.postgres:
            return []
        
        results = []
        
        if context.relationship_dimensions:
            # Query relationship memories
            filter = MemoryFilter(
                companion_id=query.companion_id,
                type=MemoryType.RELATIONSHIP,
                limit=query.limit,
            )
            
            memories = await self.postgres.query(filter)
            
            for mem in memories:
                # Score by relationship dimension relevance
                relevance = self._relationship_relevance(
                    context.relationship_dimensions,
                    mem.content.get("dimension_changes", {})
                )
                
                if relevance > 0.2:
                    results.append(RecalledMemory(
                        id=mem.id,
                        type=MemoryType.RELATIONSHIP,
                        content=mem.model_dump(),
                        relevance_score=relevance,
                        conversation_score=0.6,
                        recall_reason="Relationship dimension relevance",
                    ))
        
        return results
    
    def _merge_results(
        self, 
        result_lists: List[List[RecalledMemory]]
    ) -> List[RecalledMemory]:
        """Merge and deduplicate results from multiple strategies."""
        # Combine all results
        all_results = []
        seen_ids = set()
        
        for results in result_lists:
            for mem in results:
                key = f"{mem.type.value}:{mem.id}"
                if key not in seen_ids:
                    seen_ids.add(key)
                    all_results.append(mem)
                else:
                    # Update score if higher
                    for existing in all_results:
                        if existing.id == mem.id and existing.type == mem.type:
                            existing.relevance_score = max(
                                existing.relevance_score, mem.relevance_score
                            )
                            existing.conversation_score = max(
                                existing.conversation_score, mem.conversation_score
                            )
                            break
        
        # Sort by combined score
        all_results.sort(
            key=lambda x: x.relevance_score + x.conversation_score,
            reverse=True
        )
        
        return all_results
    
    def _diversify(
        self, 
        results: List[RecalledMemory], 
        limit: int
    ) -> List[RecalledMemory]:
        """Diversify results across types and topics."""
        if len(results) <= limit:
            return results
        
        selected = []
        seen_types = set()
        seen_topics = set()
        
        for result in results:
            if len(selected) >= limit:
                break
            
            mem_type = result.type
            topics = set()
            if "topics" in result.content:
                topics = set(result.content["topics"])
            
            type_new = mem_type not in seen_types
            topic_new = bool(topics - seen_topics)
            
            if type_new or topic_new or len(selected) < limit // 2:
                selected.append(result)
                seen_types.add(mem_type)
                seen_topics.update(topics)
        
        # Fill remaining
        for result in results:
            if len(selected) >= limit:
                break
            if result not in selected:
                selected.append(result)
        
        return selected[:limit]
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract entities from text (simplified)."""
        # In production, use spaCy or similar NER
        # For now, simple heuristic
        words = text.split()
        entities = [w for w in words if w[0].isupper() and len(w) > 2]
        return entities[:5]
    
    def _emotional_similarity(
        self, 
        state1: Dict[str, float], 
        state2: Dict[str, float]
    ) -> float:
        """Compute emotional similarity between two states."""
        all_emotions = set(state1.keys()) | set(state2.keys())
        
        if not all_emotions:
            return 0.0
        
        # Cosine similarity
        dot_product = sum(state1.get(e, 0) * state2.get(e, 0) for e in all_emotions)
        norm1 = sum(v**2 for v in state1.values()) ** 0.5
        norm2 = sum(v**2 for v in state2.values()) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _relationship_relevance(
        self,
        current_dims: Dict[str, float],
        memory_changes: Dict[str, float]
    ) -> float:
        """Compute relevance based on relationship dimensions."""
        overlap = set(current_dims.keys()) & set(memory_changes.keys())
        
        if not overlap:
            return 0.0
        
        # Average alignment
        alignments = []
        for dim in overlap:
            # High relevance if memory change aligns with current dimension
            alignment = 1.0 - abs(current_dims[dim] - memory_changes[dim]) / 10.0
            alignments.append(max(0, alignment))
        
        return sum(alignments) / len(alignments)