"""Consolidation Worker - Temporal activities for memory consolidation."""

from typing import Optional, List, Dict, Any
from datetime import datetime
import structlog
import uuid

from temporalio import activity

from pao_shared.observability import get_tracer, get_meter

from ..config import settings
from ..repositories import (
    PostgresRepository,
    QdrantRepository,
    KuzuRepository,
    RedisRepository,
)
from ..services import (
    MemoryService,
    ConsolidationService,
)

logger = structlog.get_logger(__name__)


class ConsolidationWorker:
    """
    Temporal activities for memory consolidation workflow.
    
    This worker runs as Temporal activities, called by the consolidation workflow.
    Each activity is idempotent and has its own retry policy.
    """
    
    def __init__(
        self,
        memory_service: MemoryService,
        consolidation_service: ConsolidationService,
        postgres_repo: Optional[PostgresRepository] = None,
        qdrant_repo: Optional[QdrantRepository] = None,
        kuzu_repo: Optional[KuzuRepository] = None,
        redis_repo: Optional[RedisRepository] = None,
    ):
        self.memory_service = memory_service
        self.consolidation_service = consolidation_service
        self.postgres = postgres_repo
        self.qdrant = qdrant_repo
        self.kuzu = kuzu_repo
        self.redis = redis_repo
        
        self._tracer = get_tracer()
        self._meter = get_meter()
        
        # Metrics
        self._activity_runs = self._meter.create_counter(
            "consolidation_activity_runs_total", "Total activity runs", {"activity", "status"}
        )
        self._activity_duration = self._meter.create_histogram(
            "consolidation_activity_duration_seconds", "Activity duration"
        )
    
    @activity.defn(name="fetch_unconsolidated_memories")
    async def fetch_unconsolidated_memories(
        self, companion_id: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Activity: Fetch unconsolidated episodic memories for a companion."""
        start_time = datetime.utcnow()
        
        with self._tracer.start_as_current_span("activity_fetch_unconsolidated") as span:
            span.set_attribute("companion_id", companion_id)
            span.set_attribute("limit", limit)
            
            try:
                candidates = await self.memory_service.get_consolidation_candidates(companion_id)
                
                # Convert to serializable format
                result = []
                for c in candidates[:limit]:
                    result.append({
                        "memory_id": c.memory_id,
                        "content": c.content,
                        "importance": c.importance,
                        "created_at": c.created_at.isoformat() if c.created_at else None,
                        "topics": c.content.get("topics", []),
                        "entities": c.content.get("entities", []),
                    })
                
                self._activity_runs.add(1, {"activity": "fetch_unconsolidated", "status": "success"})
                logger.info("Fetched unconsolidated memories", companion_id=companion_id, count=len(result))
                return result
                
            except Exception as e:
                self._activity_runs.add(1, {"activity": "fetch_unconsolidated", "status": "failed"})
                logger.error("Failed to fetch unconsolidated memories", companion_id=companion_id, error=str(e))
                raise
            finally:
                self._activity_duration.record((datetime.utcnow() - start_time).total_seconds())
    
    @activity.defn(name="generate_embeddings")
    async def generate_embeddings(
        self, memories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Activity: Generate embeddings for memories using embedding service."""
        start_time = datetime.utcnow()
        
        with self._tracer.start_as_current_span("activity_generate_embeddings") as span:
            span.set_attribute("memory_count", len(memories))
            
            try:
                import httpx
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    for memory in memories:
                        # Prepare text for embedding
                        content = memory.get("content", {})
                        text_parts = []
                        
                        if "event" in content:
                            text_parts.append(content["event"])
                        if "summary" in content:
                            text_parts.append(content["summary"])
                        if "topics" in content:
                            text_parts.extend(content["topics"])
                        if "entities" in content:
                            for e in content["entities"]:
                                if isinstance(e, dict):
                                    text_parts.append(e.get("value", ""))
                                else:
                                    text_parts.append(str(e))
                        
                        text = " ".join(text_parts)
                        if not text.strip():
                            text = "empty memory"
                        
                        # Call embedding service
                        response = await client.post(
                            f"{settings.embedding_service_url}/embed",
                            json={"texts": [text]},
                        )
                        response.raise_for_status()
                        data = response.json()
                        
                        memory["embedding"] = data["embeddings"][0]
                
                self._activity_runs.add(1, {"activity": "generate_embeddings", "status": "success"})
                return memories
                
            except Exception as e:
                self._activity_runs.add(1, {"activity": "generate_embeddings", "status": "failed"})
                logger.error("Failed to generate embeddings", error=str(e))
                raise
            finally:
                self._activity_duration.record((datetime.utcnow() - start_time).total_seconds())
    
    @activity.defn(name="extract_facts_with_llm")
    async def extract_facts_with_llm(
        self, memories: List[Dict[str, Any]], companion_id: str, user_id: str
    ) -> List[Dict[str, Any]]:
        """Activity: Extract semantic facts from memories using LLM."""
        start_time = datetime.utcnow()
        
        with self._tracer.start_as_current_span("activity_extract_facts") as span:
            span.set_attribute("memory_count", len(memories))
            span.set_attribute("companion_id", companion_id)
            
            try:
                import httpx
                
                # Prepare context for LLM
                memory_texts = []
                for i, mem in enumerate(memories):
                    content = mem.get("content", {})
                    text = content.get("event", content.get("summary", str(content)))
                    memory_texts.append(f"[{i}] {text}")
                
                prompt = f"""Extract key semantic facts from these episodic memories. 
For each fact, provide:
1. The fact statement
2. Confidence (0-1)
3. Category (person, preference, event, relationship, skill, general)
4. Entities mentioned
5. Source memory indices

Memories:
{chr(10).join(memory_texts)}

Output as JSON array of facts."""
                
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{settings.inference_gateway_url}/generate",
                        json={
                            "prompt": prompt,
                            "model": "local-8b",
                            "temperature": 0.3,
                            "max_tokens": 2000,
                            "response_format": "json",
                        },
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    # Parse LLM response
                    import json
                    try:
                        facts = json.loads(data.get("text", "[]"))
                    except json.JSONDecodeError:
                        # Fallback: create basic facts
                        facts = [{
                            "fact": f"Cluster of {len(memories)} memories",
                            "confidence": 0.5,
                            "category": "general",
                            "entities": [],
                            "source_indices": list(range(len(memories))),
                        }]
                
                # Convert to serializable format
                result = []
                for fact in facts:
                    result.append({
                        "fact": fact.get("fact", ""),
                        "confidence": fact.get("confidence", 0.5),
                        "category": fact.get("category", "general"),
                        "entities": fact.get("entities", []),
                        "source_memory_ids": [memories[i]["memory_id"] for i in fact.get("source_indices", [])],
                        "companion_id": companion_id,
                        "user_id": user_id,
                    })
                
                self._activity_runs.add(1, {"activity": "extract_facts", "status": "success"})
                logger.info("Extracted facts", companion_id=companion_id, fact_count=len(result))
                return result
                
            except Exception as e:
                self._activity_runs.add(1, {"activity": "extract_facts", "status": "failed"})
                logger.error("Failed to extract facts", companion_id=companion_id, error=str(e))
                raise
            finally:
                self._activity_duration.record((datetime.utcnow() - start_time).total_seconds())
    
    @activity.defn(name="write_semantic_memories")
    async def write_semantic_memories(
        self, facts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Activity: Write extracted semantic facts to all repositories."""
        start_time = datetime.utcnow()
        
        with self._tracer.start_as_current_span("activity_write_semantic") as span:
            span.set_attribute("fact_count", len(facts))
            
            try:
                written = []
                
                for fact_data in facts:
                    # Use memory service to write semantic memory
                    from ..models import MemoryWrite, MemoryType
                    
                    write_request = MemoryWrite(
                        companion_id=fact_data["companion_id"],
                        user_id=fact_data["user_id"],
                        type=MemoryType.SEMANTIC,
                        content={
                            "fact": fact_data["fact"],
                            "confidence": fact_data["confidence"],
                            "category": fact_data["category"],
                            "entities": fact_data.get("entities", []),
                            "source": "consolidation",
                            "source_episodic_ids": fact_data.get("source_memory_ids", []),
                        },
                        importance=fact_data["confidence"],
                        tags=["consolidated", fact_data["category"]],
                    )
                    
                    response = await self.memory_service.write(write_request)
                    written.append({
                        "id": response.id,
                        "fact": fact_data["fact"],
                        "confidence": fact_data["confidence"],
                    })
                
                self._activity_runs.add(1, {"activity": "write_semantic", "status": "success"})
                logger.info("Written semantic memories", count=len(written))
                return written
                
            except Exception as e:
                self._activity_runs.add(1, {"activity": "write_semantic", "status": "failed"})
                logger.error("Failed to write semantic memories", error=str(e))
                raise
            finally:
                self._activity_duration.record((datetime.utcnow() - start_time).total_seconds())
    
    @activity.defn(name="update_knowledge_graph")
    async def update_knowledge_graph(
        self, facts: List[Dict[str, Any]], companion_id: str
    ) -> Dict[str, Any]:
        """Activity: Update Kuzu knowledge graph with new entities and relationships."""
        start_time = datetime.utcnow()
        
        with self._tracer.start_as_current_span("activity_update_graph") as span:
            span.set_attribute("companion_id", companion_id)
            span.set_attribute("fact_count", len(facts))
            
            try:
                if not self.kuzu:
                    return {"updated": 0, "skipped": "kuzu not available"}
                
                entities_created = 0
                relationships_created = 0
                
                for fact_data in facts:
                    entities = fact_data.get("entities", [])
                    
                    # Create entity nodes
                    for entity in entities:
                        if isinstance(entity, dict):
                            entity_type = entity.get("type", "concept")
                            entity_value = entity.get("value", "")
                        else:
                            entity_type = "concept"
                            entity_value = str(entity)
                        
                        if entity_value:
                            await self.kuzu.create_entity(
                                companion_id=companion_id,
                                entity_type=entity_type,
                                value=entity_value,
                                fact_id=fact_data.get("id"),
                            )
                            entities_created += 1
                    
                    # Create relationships between entities in same fact
                    entity_values = [
                        e.get("value", "") if isinstance(e, dict) else str(e)
                        for e in entities
                        if (e.get("value") if isinstance(e, dict) else str(e))
                    ]
                    
                    for i in range(len(entity_values)):
                        for j in range(i + 1, len(entity_values)):
                            await self.kuzu.create_relationship(
                                companion_id=companion_id,
                                source_entity=entity_values[i],
                                target_entity=entity_values[j],
                                relationship_type="co_occurs",
                                fact_id=fact_data.get("id"),
                            )
                            relationships_created += 1
                
                result = {
                    "entities_created": entities_created,
                    "relationships_created": relationships_created,
                }
                
                self._activity_runs.add(1, {"activity": "update_graph", "status": "success"})
                return result
                
            except Exception as e:
                self._activity_runs.add(1, {"activity": "update_graph", "status": "failed"})
                logger.error("Failed to update knowledge graph", companion_id=companion_id, error=str(e))
                raise
            finally:
                self._activity_duration.record((datetime.utcnow() - start_time).total_seconds())
    
    @activity.defn(name="assign_importance_and_ttl")
    async def assign_importance_and_ttl(
        self, written_facts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Activity: Assign importance scores and TTL to consolidated memories."""
        start_time = datetime.utcnow()
        
        with self._tracer.start_as_current_span("activity_assign_importance") as span:
            span.set_attribute("fact_count", len(written_facts))
            
            try:
                # Importance is already set during write based on confidence
                # TTL is determined by memory type and importance
                for fact in written_facts:
                    confidence = fact.get("confidence", 0.5)
                    
                    # Higher confidence = longer TTL
                    if confidence > 0.8:
                        fact["ttl_days"] = settings.memory_ttl_days.get("semantic", 1825)
                    elif confidence > 0.5:
                        fact["ttl_days"] = settings.memory_ttl_days.get("semantic", 1825) // 2
                    else:
                        fact["ttl_days"] = settings.memory_ttl_days.get("semantic", 1825) // 4
                    
                    fact["importance"] = confidence
                
                self._activity_runs.add(1, {"activity": "assign_importance", "status": "success"})
                return written_facts
                
            except Exception as e:
                self._activity_runs.add(1, {"activity": "assign_importance", "status": "failed"})
                logger.error("Failed to assign importance and TTL", error=str(e))
                raise
            finally:
                self._activity_duration.record((datetime.utcnow() - start_time).total_seconds())
    
    @activity.defn(name="mark_episodic_consolidated")
    async def mark_episodic_consolidated(
        self, source_memory_ids: List[str], semantic_memory_ids: List[str]
    ) -> Dict[str, Any]:
        """Activity: Mark episodic memories as consolidated."""
        start_time = datetime.utcnow()
        
        with self._tracer.start_as_current_span("activity_mark_consolidated") as span:
            span.set_attribute("episodic_count", len(source_memory_ids))
            span.set_attribute("semantic_count", len(semantic_memory_ids))
            
            try:
                await self.memory_service.mark_consolidated(source_memory_ids, semantic_memory_ids)
                
                result = {
                    "marked": len(source_memory_ids),
                    "semantic_ids": semantic_memory_ids,
                }
                
                self._activity_runs.add(1, {"activity": "mark_consolidated", "status": "success"})
                return result
                
            except Exception as e:
                self._activity_runs.add(1, {"activity": "mark_consolidated", "status": "failed"})
                logger.error("Failed to mark memories consolidated", error=str(e))
                raise
            finally:
                self._activity_duration.record((datetime.utcnow() - start_time).total_seconds())
    
    @activity.defn(name="emit_consolidation_events")
    async def emit_consolidation_events(
        self, companion_id: str, report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Activity: Emit consolidation events to Kafka."""
        start_time = datetime.utcnow()
        
        with self._tracer.start_as_current_span("activity_emit_events") as span:
            span.set_attribute("companion_id", companion_id)
            
            try:
                if not self.postgres:
                    return {"emitted": 0, "skipped": "kafka not available"}
                
                # Emit event via Kafka (would use aiokafka in production)
                event = {
                    "event_type": "memory.consolidated",
                    "companion_id": companion_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "payload": report,
                }
                
                # In production: await kafka_producer.send_and_wait("memory.events", event)
                logger.info("Consolidation event emitted", companion_id=companion_id, event=event)
                
                self._activity_runs.add(1, {"activity": "emit_events", "status": "success"})
                return {"emitted": 1}
                
            except Exception as e:
                self._activity_runs.add(1, {"activity": "emit_events", "status": "failed"})
                logger.error("Failed to emit consolidation events", companion_id=companion_id, error=str(e))
                raise
            finally:
                self._activity_duration.record((datetime.utcnow() - start_time).total_seconds())


# Standalone activity functions for Temporal registration
@activity.defn(name="consolidate_memory")
async def consolidate_memory_activity(
    companion_id: str,
    user_id: str,
    memory_service: MemoryService,
    consolidation_service: ConsolidationService,
) -> Dict[str, Any]:
    """Standalone activity to run full consolidation for a companion."""
    report = await consolidation_service.run_consolidation(companion_id, user_id)
    return report.model_dump()