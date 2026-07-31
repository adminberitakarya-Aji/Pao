"""Export Service - Handles exporting all user memories in various formats."""

from typing import Optional, List, Dict, Any
from datetime import datetime
import structlog
import json
import uuid

from pao_shared.observability import get_tracer, get_meter

from ..models import (
    MemoryType,
    MemoryFilter,
)
from ..repositories import (
    PostgresRepository,
    QdrantRepository,
    KuzuRepository,
    RedisRepository,
)

logger = structlog.get_logger(__name__)


class ExportService:
    """
    Service for exporting all user memories.
    
    Supports formats:
    - JSON-LD (linked data)
    - JSON (simple)
    - PDF (formatted report)
    - Timeline (chronological)
    - Audio (for voice memories)
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
        self._export_requests = self._meter.create_counter(
            "memory_export_requests_total", "Total export requests", {"format"}
        )
        self._export_duration = self._meter.create_histogram(
            "memory_export_duration_seconds", "Export duration"
        )
    
    async def export_all(
        self,
        companion_id: str,
        user_id: str,
        formats: List[str],
        include_types: Optional[List[MemoryType]] = None,
        encryption_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Export all memories for a companion."""
        start_time = datetime.utcnow()
        export_id = f"export_{uuid.uuid4().hex[:12]}"
        
        with self._tracer.start_as_current_span("memory_export") as span:
            span.set_attribute("companion_id", companion_id)
            span.set_attribute("export_id", export_id)
            span.set_attribute("formats", ",".join(formats))
            
            # Gather all memories
            memories_by_type = await self._gather_memories(companion_id, user_id, include_types)
            
            # Generate exports for each format
            results = {}
            for fmt in formats:
                try:
                    if fmt == "json-ld":
                        results[fmt] = await self._export_json_ld(export_id, memories_by_type, encryption_key)
                    elif fmt == "json":
                        results[fmt] = await self._export_json(export_id, memories_by_type, encryption_key)
                    elif fmt == "timeline":
                        results[fmt] = await self._export_timeline(export_id, memories_by_type, encryption_key)
                    elif fmt == "pdf":
                        results[fmt] = await self._export_pdf(export_id, memories_by_type, encryption_key)
                    elif fmt == "audio":
                        results[fmt] = await self._export_audio(export_id, memories_by_type, encryption_key)
                    elif fmt == "audit_log":
                        results[fmt] = await self._export_audit_log(export_id, companion_id, encryption_key)
                    else:
                        logger.warning(f"Unknown export format: {fmt}")
                except Exception as e:
                    logger.error(f"Export format {fmt} failed", error=str(e))
                    results[fmt] = {"error": str(e)}
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            self._export_requests.add(1, {"format": ",".join(formats)})
            self._export_duration.record(duration)
            
            logger.info(
                "Export completed",
                export_id=export_id,
                companion_id=companion_id,
                formats=formats,
                duration_seconds=duration,
            )
            
            return {
                "export_id": export_id,
                "companion_id": companion_id,
                "formats": results,
                "completed_at": datetime.utcnow().isoformat(),
                "memory_counts": {t.value: len(m) for t, m in memories_by_type.items()},
            }
    
    async def _gather_memories(
        self,
        companion_id: str,
        user_id: str,
        include_types: Optional[List[MemoryType]] = None,
    ) -> Dict[MemoryType, List[Dict[str, Any]]]:
        """Gather all memories from all repositories."""
        memories = {}
        
        types_to_export = include_types or list(MemoryType)
        
        for mem_type in types_to_export:
            all_memories = []
            
            # Get from PostgreSQL (primary for relational types)
            if self.postgres:
                filter = MemoryFilter(companion_id=companion_id, type=mem_type, limit=10000)
                pg_memories = await self.postgres.query(filter)
                all_memories.extend([m.model_dump() for m in pg_memories])
            
            # Get from Qdrant (for vector types)
            if self.qdrant and mem_type in [MemoryType.EPISODIC, MemoryType.SEMANTIC, MemoryType.EMOTIONAL]:
                filter = MemoryFilter(companion_id=companion_id, type=mem_type, limit=10000)
                qdrant_memories = await self.qdrant.query(filter)
                all_memories.extend([m.model_dump() for m in qdrant_memories])
            
            # Get from Kuzu (for graph types)
            if self.kuzu and mem_type in [MemoryType.SEMANTIC, MemoryType.TIMELINE]:
                filter = MemoryFilter(companion_id=companion_id, type=mem_type, limit=10000)
                kuzu_memories = await self.kuzu.query(filter)
                all_memories.extend(kuzu_memories)
            
            # Deduplicate by ID
            seen = set()
            unique = []
            for mem in all_memories:
                mem_id = mem.get("id")
                if mem_id not in seen:
                    seen.add(mem_id)
                    unique.append(mem)
            
            memories[mem_type] = unique
        
        return memories
    
    async def _export_json_ld(
        self, export_id: str, memories_by_type: Dict[MemoryType, List], encryption_key: Optional[str]
    ) -> Dict[str, Any]:
        """Export as JSON-LD (linked data format)."""
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
                    "@type": f"memory:{mem_type.value.capitalize()}Memory",
                    "id": mem.get("id"),
                    "companion_id": mem.get("companion_id"),
                    "user_id": mem.get("user_id"),
                    "created_at": mem.get("created_at"),
                    "updated_at": mem.get("updated_at"),
                    "version": mem.get("version", 1),
                    "importance": mem.get("importance", 0.5),
                }
                
                # Add type-specific fields
                content = mem.get("content", mem) if "content" in mem else mem
                for key, value in content.items():
                    if key not in node:
                        node[key] = value
                
                graph.append(node)
        
        return {
            "format": "json-ld",
            "export_id": export_id,
            "data": graph,
        }
    
    async def _export_json(
        self, export_id: str, memories_by_type: Dict[MemoryType, List], encryption_key: Optional[str]
    ) -> Dict[str, Any]:
        """Export as simple JSON."""
        data = {}
        
        for mem_type, memories in memories_by_type.items():
            data[mem_type.value] = memories
        
        return {
            "format": "json",
            "export_id": export_id,
            "data": data,
        }
    
    async def _export_timeline(
        self, export_id: str, memories_by_type: Dict[MemoryType, List], encryption_key: Optional[str]
    ) -> Dict[str, Any]:
        """Export as chronological timeline."""
        # Combine all memories and sort by timestamp
        all_memories = []
        
        for mem_type, memories in memories_by_type.items():
            for mem in memories:
                content = mem.get("content", mem) if "content" in mem else mem
                timestamp = content.get("timestamp") or content.get("created_at") or mem.get("created_at")
                
                if timestamp:
                    all_memories.append({
                        "type": mem_type.value,
                        "timestamp": timestamp,
                        "memory": mem,
                    })
        
        # Sort chronologically
        all_memories.sort(key=lambda x: x["timestamp"])
        
        return {
            "format": "timeline",
            "export_id": export_id,
            "data": all_memories,
        }
    
    async def _export_pdf(
        self, export_id: str, memories_by_type: Dict[MemoryType, List], encryption_key: Optional[str]
    ) -> Dict[str, Any]:
        """Export as PDF report (placeholder - would use reportlab or similar)."""
        return {
            "format": "pdf",
            "export_id": export_id,
            "status": "not_implemented",
            "message": "PDF export requires reportlab dependency",
        }
    
    async def _export_audio(
        self, export_id: str, memories_by_type: Dict[MemoryType, List], encryption_key: Optional[str]
    ) -> Dict[str, Any]:
        """Export voice memories as audio (placeholder)."""
        voice_memories = memories_by_type.get(MemoryType.EPISODIC, [])
        voice_memories = [m for m in voice_memories if m.get("content", {}).get("modality") == "voice"]
        
        return {
            "format": "audio",
            "export_id": export_id,
            "voice_memory_count": len(voice_memories),
            "status": "not_implemented",
            "message": "Audio export requires TTS integration",
        }
    
    async def _export_audit_log(
        self, export_id: str, companion_id: str, encryption_key: Optional[str]
    ) -> Dict[str, Any]:
        """Export audit log of all memory access."""
        if not self.postgres:
            return {"format": "audit_log", "export_id": export_id, "data": []}
        
        # This would query the audit log table
        return {
            "format": "audit_log",
            "export_id": export_id,
            "data": [],
            "message": "Audit log export not fully implemented",
        }
    
    async def get_export_status(self, export_id: str) -> Dict[str, Any]:
        """Get status of an export job."""
        if self.redis:
            # Check Redis for progress
            pass
        return {"export_id": export_id, "status": "unknown"}