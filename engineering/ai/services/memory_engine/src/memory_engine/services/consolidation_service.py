"""Consolidation Service - Handles episodic to semantic memory consolidation."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import structlog
import uuid

from pao_shared.observability import get_tracer, get_meter

from ..models import (
    MemoryType,
    ConsolidationJob,
    ConsolidationStatus,
    ClusterResult,
    FactExtraction,
    ConsolidationReport,
    ConsolidationCandidate,
    SemanticMemory,
)
from ..repositories import (
    PostgresRepository,
    QdrantRepository,
    KuzuRepository,
    RedisRepository,
)
from .memory_service import MemoryService

logger = structlog.get_logger(__name__)


class ConsolidationService:
    """
    Service for consolidating episodic memories into semantic memories.
    
    Runs nightly per companion to compress detailed episodic memories
    into structured semantic facts with confidence scores.
    """
    
    def __init__(
        self,
        memory_service: MemoryService,
        postgres_repo: Optional[PostgresRepository] = None,
        qdrant_repo: Optional[QdrantRepository] = None,
        kuzu_repo: Optional[KuzuRepository] = None,
        redis_repo: Optional[RedisRepository] = None,
    ):
        self.memory_service = memory_service
        self.postgres = postgres_repo
        self.qdrant = qdrant_repo
        self.kuzu = kuzu_repo
        self.redis = redis_repo
        
        self._tracer = get_tracer()
        self._meter = get_meter()
        
        # Metrics
        self._consolidation_runs = self._meter.create_counter(
            "consolidation_runs_total", "Total consolidation runs", {"status"}
        )
        self._memories_consolidated = self._meter.create_counter(
            "memories_consolidated_total", "Total memories consolidated"
        )
        self._semantic_created = self._meter.create_counter(
            "semantic_memories_created_total", "Total semantic memories created"
        )
        self._consolidation_duration = self._meter.create_histogram(
            "consolidation_duration_seconds", "Consolidation run duration"
        )
    
    async def run_consolidation(self, companion_id: str, user_id: str) -> ConsolidationReport:
        """Run the full consolidation pipeline for a companion."""
        start_time = datetime.utcnow()
        job_id = f"consol_{uuid.uuid4().hex[:12]}"
        
        with self._tracer.start_as_current_span("consolidation_run") as span:
            span.set_attribute("companion_id", companion_id)
            span.set_attribute("job_id", job_id)
            
            # Check if already running
            if self.redis and await self.redis.is_consolidation_locked(companion_id):
                logger.warning("Consolidation already running for companion", companion_id=companion_id)
                return ConsolidationReport(
                    companion_id=companion_id,
                    episodic_processed=0,
                    semantic_created=0,
                    contradictions_found=0,
                    user_review_required=False,
                    details={"error": "Consolidation already in progress"},
                )
            
            # Acquire lock
            if self.redis:
                await self.redis.acquire_consolidation_lock(companion_id)
            
            job = ConsolidationJob(
                id=job_id,
                companion_id=companion_id,
                user_id=user_id,
                status=ConsolidationStatus.RUNNING,
                started_at=start_time.isoformat(),
            )
            
            try:
                # Update progress
                if self.redis:
                    await self.redis.set_consolidation_progress(companion_id, {
                        "stage": "selecting_candidates",
                        "progress": 0.1,
                    })
                
                # 1. SELECT candidates
                candidates = await self.memory_service.get_consolidation_candidates(companion_id)
                job.episodic_candidates = len(candidates)
                
                if not candidates:
                    job.status = ConsolidationStatus.COMPLETED
                    job.completed_at = datetime.utcnow().isoformat()
                    return self._job_to_report(job)
                
                # 2. CLUSTER by topic/entity
                if self.redis:
                    await self.redis.set_consolidation_progress(companion_id, {
                        "stage": "clustering",
                        "progress": 0.3,
                        "candidates": len(candidates),
                    })
                
                clusters = await self._cluster_by_topic(candidates)
                
                # 3. SUMMARIZE each cluster and extract facts
                if self.redis:
                    await self.redis.set_consolidation_progress(companion_id, {
                        "stage": "extracting_facts",
                        "progress": 0.5,
                        "clusters": len(clusters),
                    })
                
                semantic_memories = []
                for cluster in clusters:
                    facts = await self._extract_facts_from_cluster(cluster, companion_id, user_id)
                    semantic_memories.extend(facts)
                
                # 4. VALIDATE against existing semantic memories
                if self.redis:
                    await self.redis.set_consolidation_progress(companion_id, {
                        "stage": "validating",
                        "progress": 0.7,
                        "facts_extracted": len(semantic_memories),
                    })
                
                validated = await self._validate_no_contradictions(semantic_memories, companion_id)
                job.contradictions_found = len(semantic_memories) - len(validated)
                
                # 5. WRITE new semantic memories
                if self.redis:
                    await self.redis.set_consolidation_progress(companion_id, {
                        "stage": "writing_semantic",
                        "progress": 0.8,
                        "validated_facts": len(validated),
                    })
                
                written = await self._write_semantic_memories(validated)
                job.semantic_created = len(written)
                
                # 6. MARK episodic as consolidated
                if written:
                    candidate_ids = [c.memory_id for c in candidates]
                    semantic_ids = [s.id for s in written]
                    await self.memory_service.mark_consolidated(candidate_ids, semantic_ids)
                
                # 7. Check if user review needed
                job.user_review_required = self._has_significant_changes(written)
                
                job.status = ConsolidationStatus.COMPLETED
                job.completed_at = datetime.utcnow().isoformat()
                
                # Track metrics
                duration = (datetime.utcnow() - start_time).total_seconds()
                self._consolidation_runs.add(1, {"status": "success"})
                self._memories_consolidated.add(job.episodic_candidates)
                self._semantic_created.add(job.semantic_created)
                self._consolidation_duration.record(duration)
                
                logger.info(
                    "Consolidation completed",
                    companion_id=companion_id,
                    episodic_processed=job.episodic_candidates,
                    semantic_created=job.semantic_created,
                    duration_seconds=duration,
                )
                
                return self._job_to_report(job)
                
            except Exception as e:
                job.status = ConsolidationStatus.FAILED
                job.error = str(e)
                job.completed_at = datetime.utcnow().isoformat()
                
                self._consolidation_runs.add(1, {"status": "failed"})
                
                logger.error("Consolidation failed", companion_id=companion_id, error=str(e))
                return self._job_to_report(job)
                
            finally:
                if self.redis:
                    await self.redis.release_consolidation_lock(companion_id)
    
    async def _cluster_by_topic(self, candidates: List[ConsolidationCandidate]) -> List[ClusterResult]:
        """Cluster episodic memories by topic/entity similarity."""
        if not candidates:
            return []
        
        # For now, simple clustering by topics
        # In production, would use embedding similarity
        clusters = {}
        
        for candidate in candidates:
            content = candidate.content
            topics = content.get("topics", [])
            entities = [e.get("value", "") for e in content.get("entities", [])]
            
            # Use first topic or entity as cluster key
            cluster_key = topics[0] if topics else (entities[0] if entities else "general")
            
            if cluster_key not in clusters:
                clusters[cluster_key] = {
                    "memories": [],
                    "topics": set(),
                    "entities": set(),
                }
            
            clusters[cluster_key]["memories"].append(candidate)
            clusters[cluster_key]["topics"].update(topics)
            clusters[cluster_key]["entities"].update(entities)
        
        # Convert to ClusterResult objects
        results = []
        for cluster_key, data in clusters.items():
            if len(data["memories"]) < 2:
                continue  # Skip singletons
            
            results.append(ClusterResult(
                cluster_id=f"cluster_{uuid.uuid4().hex[:8]}",
                memories=[m.memory_id for m in data["memories"]],
                theme=cluster_key,
                entities=list(data["entities"]),
                centroid_embedding=[],  # Would compute from embeddings
                size=len(data["memories"]),
                coherence_score=0.8,  # Would compute actual coherence
            ))
        
        return results
    
    async def _extract_facts_from_cluster(
        self, 
        cluster: ClusterResult, 
        companion_id: str, 
        user_id: str
    ) -> List[SemanticMemory]:
        """Extract semantic facts from a cluster of episodic memories."""
        # In production, this would call an LLM to summarize and extract facts
        # For now, create placeholder facts
        
        facts = []
        memories = cluster.memories
        
        # Get full memory content for summarization
        # This would fetch from repository
        
        # Create a summary fact
        fact_text = f"Cluster of {len(memories)} memories about {cluster.theme}"
        
        fact = SemanticMemory(
            companion_id=companion_id,
            user_id=user_id,
            fact=fact_text,
            confidence=0.7,
            source="episodic",
            source_episodic_ids=memories,
            entities=[{"type": "topic", "value": cluster.theme}],
            category="general",
        )
        
        facts.append(fact)
        
        return facts
    
    async def _validate_no_contradictions(
        self, 
        new_facts: List[SemanticMemory], 
        companion_id: str
    ) -> List[SemanticMemory]:
        """Validate new facts against existing semantic memories."""
        if not self.postgres:
            return new_facts
        
        validated = []
        
        for fact in new_facts:
            # Check for contradictions with existing facts
            # This is simplified - real implementation would use LLM-based validation
            contradictions = await self._check_fact_contradictions(fact, companion_id)
            
            if contradictions:
                # Mark as contradicted
                fact.contradicted_by = contradictions[0]
                validated.append(fact)
            else:
                validated.append(fact)
        
        return validated
    
    async def _check_fact_contradictions(self, fact: SemanticMemory, companion_id: str) -> List[str]:
        """Check if a fact contradicts existing semantic memories."""
        # Simplified - would use embeddings + LLM in production
        if not self.kuzu:
            return []
        
        contradictions = await self.kuzu.get_contradictions(companion_id)
        # Check if any existing fact contradicts this one
        # This is a placeholder
        return []
    
    async def _write_semantic_memories(self, facts: List[SemanticMemory]) -> List[SemanticMemory]:
        """Write semantic memories to all repositories."""
        written = []
        
        for fact in facts:
            try:
                # Write to PostgreSQL
                if self.postgres:
                    await self.postgres.write_semantic(fact)
                
                # Write to Qdrant for vector search
                if self.qdrant:
                    await self.qdrant.write_semantic(fact)
                
                # Write to Kuzu for graph
                if self.kuzu:
                    await self.kuzu.write_semantic(fact)
                
                written.append(fact)
            except Exception as e:
                logger.error("Failed to write semantic memory", fact_id=fact.id, error=str(e))
        
        return written
    
    def _has_significant_changes(self, written: List[SemanticMemory]) -> bool:
        """Check if consolidation produced significant changes requiring user review."""
        # Significant if many new facts or high-confidence contradictions
        if len(written) > 10:
            return True
        
        for fact in written:
            if fact.confidence > 0.9 and fact.contradicted_by:
                return True
        
        return False
    
    def _job_to_report(self, job: ConsolidationJob) -> ConsolidationReport:
        """Convert job to report."""
        return ConsolidationReport(
            companion_id=job.companion_id,
            episodic_processed=job.episodic_candidates,
            semantic_created=job.semantic_created,
            contradictions_found=job.contradictions_found,
            user_review_required=job.user_review_required,
            details={
                "job_id": job.id,
                "status": job.status.value,
                "error": job.error,
                "started_at": job.started_at,
                "completed_at": job.completed_at,
            },
        )
    
    async def get_consolidation_status(self, companion_id: str) -> Optional[Dict[str, Any]]:
        """Get current consolidation status."""
        if self.redis:
            return await self.redis.get_consolidation_progress(companion_id)
        return None
    
    async def schedule_consolidation(self, companion_id: str, user_id: str, 
                                      interval_hours: int = 24) -> None:
        """Schedule periodic consolidation (would integrate with Temporal)."""
        # This would be called by Temporal workflow
        pass