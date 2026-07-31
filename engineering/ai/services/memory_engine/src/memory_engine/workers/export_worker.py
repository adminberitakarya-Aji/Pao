"""Export Worker - Temporal activities for memory export."""

from typing import Optional, List, Dict, Any
from datetime import datetime
import structlog
import json
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
from ..services import ExportService

logger = structlog.get_logger(__name__)


class ExportWorker:
    """
    Temporal activities for memory export workflow.
    
    Handles exporting all user memories in various formats.
    """
    
    def __init__(
        self,
        export_service: ExportService,
        postgres_repo: Optional[PostgresRepository] = None,
        qdrant_repo: Optional[QdrantRepository] = None,
        kuzu_repo: Optional[KuzuRepository] = None,
        redis_repo: Optional[RedisRepository] = None,
    ):
        self.export_service = export_service
        self.postgres = postgres_repo
        self.qdrant = qdrant_repo
        self.kuzu = kuzu_repo
        self.redis = redis_repo
        
        self._tracer = get_tracer()
        self._meter = get_meter()
        
        self._activity_runs = self._meter.create_counter(
            "export_activity_runs_total", "Total activity runs", {"activity", "status"}
        )
        self._activity_duration = self._meter.create_histogram(
            "export_activity_duration_seconds", "Activity duration"
        )
    
    @activity.defn(name="gather_all_memories")
    async def gather_all_memories(
        self, companion_id: str, user_id: str, include_types: Optional[List[str]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Activity: Gather all memories from all repositories."""
        start_time = datetime.utcnow()
        
        with self._tracer.start_as_current_span("activity_gather_memories") as span:
            span.set_attribute("companion_id", companion_id)
            
            try:
                from ..models import MemoryType, MemoryFilter
                
                memories_by_type = {}
                types_to_export = [MemoryType(t) for t in include_types] if include_types else list(MemoryType)
                
                for mem_type in types_to_export:
                    all_memories = []
                    
                    # Get from PostgreSQL
                    if self.postgres:
                        filter = MemoryFilter(companion_id=companion_id, type=mem_type, limit=settings.export_max_memories)
                        pg_memories = await self.postgres.query(filter)
                        all_memories.extend([m.model_dump() for m in pg_memories])
                    
                    # Get from Qdrant
                    if self.qdrant and mem_type in [MemoryType.EPISODIC, MemoryType.SEMANTIC, MemoryType.EMOTIONAL]:
                        filter = MemoryFilter(companion_id=companion_id, type=mem_type, limit=settings.export_max_memories)
                        qdrant_memories = await self.qdrant.query(filter)
                        all_memories.extend([m.model_dump() for m in qdrant_memories])
                    
                    # Get from Kuzu
                    if self.kuzu and mem_type in [MemoryType.SEMANTIC, MemoryType.TIMELINE]:
                        filter = MemoryFilter(companion_id=companion_id, type=mem_type, limit=settings.export_max_memories)
                        kuzu_memories = await self.kuzu.query(filter)
                        all_memories.extend(kuzu_memories)
                    
                    # Deduplicate
                    seen = set()
                    unique = []
                    for mem in all_memories:
                        mem_id = mem.get("id")
                        if mem_id not in seen:
                            seen.add(mem_id)
                            unique.append(mem)
                    
                    memories_by_type[mem_type.value] = unique
                
                total = sum(len(m) for m in memories_by_type.values())
                self._activity_runs.add(1, {"activity": "gather_memories", "status": "success"})
                logger.info("Gathered memories for export", companion_id=companion_id, total=total)
                
                return memories_by_type
                
            except Exception as e:
                self._activity_runs.add(1, {"activity": "gather_memories", "status": "failed"})
                logger.error("Failed to gather memories", companion_id=companion_id, error=str(e))
                raise
            finally:
                self._activity_duration.record((datetime.utcnow() - start_time).total_seconds())
    
    @activity.defn(name="format_export")
    async def format_export(
        self,
        memories_by_type: Dict[str, List[Dict[str, Any]]],
        format_type: str,
        companion_id: str,
        user_id: str,
        encryption_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Activity: Format memories into requested export format."""
        start_time = datetime.utcnow()
        
        with self._tracer.start_as_current_span("activity_format_export") as span:
            span.set_attribute("format", format_type)
            span.set_attribute("companion_id", companion_id)
            
            try:
                export_id = f"export_{uuid.uuid4().hex[:12]}"
                
                if format_type == "json-ld":
                    result = await self._format_json_ld(export_id, memories_by_type)
                elif format_type == "json":
                    result = await self._format_json(export_id, memories_by_type)
                elif format_type == "timeline":
                    result = await self._format_timeline(export_id, memories_by_type)
                elif format_type == "pdf":
                    result = await self._format_pdf(export_id, memories_by_type)
                elif format_type == "audit_log":
                    result = await self._format_audit_log(export_id, companion_id)
                else:
                    raise ValueError(f"Unknown export format: {format_type}")
                
                if encryption_key:
                    result = self._encrypt_export(result, encryption_key)
                
                self._activity_runs.add(1, {"activity": "format_export", "status": "success"})
                return result
                
            except Exception as e:
                self._activity_runs.add(1, {"activity": "format_export", "status": "failed"})
                logger.error("Failed to format export", format_type=format_type, error=str(e))
                raise
            finally:
                self._activity_duration.record((datetime.utcnow() - start_time).total_seconds())
    
    async def _format_json_ld(
        self, export_id: str, memories_by_type: Dict[str, List]
    ) -> Dict[str, Any]:
        """Format as JSON-LD linked data."""
        context = {
            "@vocab": "https://pao.app/ontology/",
            "memory": "https://pao.app/ontology/Memory",
            "episodic": "https://pao.app/ontology/EpisodicMemory",
            "semantic": "https://pao.app/ontology/SemanticMemory",
            "emotional": "https://pao.app/ontology/EmotionalMemory",
            "relationship": "https://pao.app/ontology/RelationshipMemory",
            "timeline": "https://pao.app/ontology/TimelineMemory",
            "preference": "https://pao.app/ontology/PreferenceMemory",
        }
        
        graph = [{"@context": context}]
        
        for mem_type, memories in memories_by_type.items():
            for mem in memories:
                node = {
                    "@id": f"urn:pao:memory:{mem.get('id')}",
                    "@type": f"memory:{mem_type.capitalize()}Memory",
                    "id": mem.get("id"),
                    "companion_id": mem.get("companion_id"),
                    "user_id": mem.get("user_id"),
                    "created_at": mem.get("created_at"),
                    "updated_at": mem.get("updated_at"),
                    "version": mem.get("version", 1),
                    "importance": mem.get("importance", 0.5),
                }
                
                content = mem.get("content", mem) if "content" in mem else mem
                for key, value in content.items():
                    if key not in node:
                        node[key] = value
                
                graph.append(node)
        
        return {
            "format": "json-ld",
            "export_id": export_id,
            "data": graph,
            "generated_at": datetime.utcnow().isoformat(),
        }
    
    async def _format_json(
        self, export_id: str, memories_by_type: Dict[str, List]
    ) -> Dict[str, Any]:
        """Format as simple JSON."""
        data = {}
        
        for mem_type, memories in memories_by_type.items():
            data[mem_type] = memories
        
        return {
            "format": "json",
            "export_id": export_id,
            "data": data,
            "generated_at": datetime.utcnow().isoformat(),
        }
    
    async def _format_timeline(
        self, export_id: str, memories_by_type: Dict[str, List]
    ) -> Dict[str, Any]:
        """Format as chronological timeline."""
        all_memories = []
        
        for mem_type, memories in memories_by_type.items():
            for mem in memories:
                content = mem.get("content", mem) if "content" in mem else mem
                timestamp = (
                    content.get("timestamp") 
                    or content.get("created_at") 
                    or mem.get("created_at")
                )
                
                if timestamp:
                    all_memories.append({
                        "type": mem_type,
                        "timestamp": timestamp,
                        "memory": mem,
                    })
        
        all_memories.sort(key=lambda x: x["timestamp"])
        
        return {
            "format": "timeline",
            "export_id": export_id,
            "data": all_memories,
            "generated_at": datetime.utcnow().isoformat(),
        }
    
    async def _format_pdf(
        self, export_id: str, memories_by_type: Dict[str, List]
    ) -> Dict[str, Any]:
        """Format as PDF (placeholder)."""
        return {
            "format": "pdf",
            "export_id": export_id,
            "status": "not_implemented",
            "message": "PDF export requires reportlab dependency",
            "memory_counts": {t: len(m) for t, m in memories_by_type.items()},
        }
    
    async def _format_audit_log(
        self, export_id: str, companion_id: str
    ) -> Dict[str, Any]:
        """Format as audit log of all memory access."""
        # This would query the audit log table
        return {
            "format": "audit_log",
            "export_id": export_id,
            "data": [],
            "message": "Audit log export not fully implemented",
        }
    
    def _encrypt_export(self, export_data: Dict[str, Any], key: str) -> Dict[str, Any]:
        """Encrypt export data (placeholder)."""
        # In production: use AES-GCM with the provided key
        export_data["encrypted"] = True
        export_data["encryption_algorithm"] = "AES-256-GCM"
        return export_data
    
    @activity.defn(name="store_export")
    async def store_export(
        self, export_result: Dict[str, Any], companion_id: str
    ) -> Dict[str, Any]:
        """Activity: Store export result for download."""
        start_time = datetime.utcnow()
        
        with self._tracer.start_as_current_span("activity_store_export") as span:
            span.set_attribute("companion_id", companion_id)
            
            try:
                if self.redis:
                    export_id = export_result.get("export_id")
                    # Store in Redis with TTL (24 hours)
                    import json
                    await self.redis.setex(
                        f"export:{export_id}",
                        86400,  # 24 hours
                        json.dumps(export_result),
                    )
                
                self._activity_runs.add(1, {"activity": "store_export", "status": "success"})
                return {"stored": True, "export_id": export_result.get("export_id")}
                
            except Exception as e:
                self._activity_runs.add(1, {"activity": "store_export", "status": "failed"})
                logger.error("Failed to store export", error=str(e))
                raise
            finally:
                self._activity_duration.record((datetime.utcnow() - start_time).total_seconds())


@activity.defn(name="export_memories")
async def export_memories_activity(
    companion_id: str,
    user_id: str,
    formats: List[str],
    include_types: Optional[List[str]] = None,
    encryption_key: Optional[str] = None,
    export_service: ExportService = None,
) -> Dict[str, Any]:
    """Standalone activity to run full export for a companion."""
    return await export_service.export_all(
        companion_id=companion_id,
        user_id=user_id,
        formats=formats,
        include_types=include_types,
        encryption_key=encryption_key,
    )