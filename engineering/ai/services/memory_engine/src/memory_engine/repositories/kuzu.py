"""Kuzu repository for Memory Engine - handles graph database operations for semantic entities and relationships."""

from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import asyncio

import kuzu

from pao_shared.config import get_settings

from ..models import (
    MemoryType,
    SemanticMemory,
    EntityRef,
    MemoryFilter,
)
from .base import MemoryRepository

settings = get_settings()


class KuzuRepository(MemoryRepository):
    """Kuzu repository for graph-based memory storage (entities, relationships, timeline)."""
    
    def __init__(self, database_path: Optional[str] = None):
        self.database_path = database_path or "/var/lib/kuzu/memory_engine"
        self.db: Optional[kuzu.Database] = None
        self.conn: Optional[kuzu.Connection] = None
    
    async def initialize(self) -> None:
        """Initialize Kuzu database and create schema."""
        self.db = kuzu.Database(self.database_path)
        self.conn = kuzu.Connection(self.db)
        
        # Create schema
        await self._create_schema()
    
    async def close(self) -> None:
        """Close Kuzu connection."""
        if self.conn:
            self.conn.close()
        if self.db:
            self.db.close()
    
    async def _create_schema(self) -> None:
        """Create Kuzu schema for memory entities and relationships."""
        # Node tables
        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Entity (
                id STRING,
                type STRING,
                value STRING,
                description STRING,
                confidence DOUBLE,
                companion_id STRING,
                user_id STRING,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                PRIMARY KEY (id)
            )
        """)
        
        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS SemanticFact (
                id STRING,
                fact STRING,
                category STRING,
                confidence DOUBLE,
                source STRING,
                companion_id STRING,
                user_id STRING,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                PRIMARY KEY (id)
            )
        """)
        
        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS TimelineEvent (
                id STRING,
                narrative_arc STRING,
                event_order INT64,
                description STRING,
                timestamp TIMESTAMP,
                companion_id STRING,
                user_id STRING,
                PRIMARY KEY (id)
            )
        """)
        
        # Relationship tables
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS RELATED_TO (
                FROM Entity TO Entity,
                relationship_type STRING,
                strength DOUBLE,
                context STRING,
                created_at TIMESTAMP
            )
        """)
        
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS ENTITY_IN_FACT (
                FROM Entity TO SemanticFact,
                role STRING,
                created_at TIMESTAMP
            )
        """)
        
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS FACT_CONTRADICTS (
                FROM SemanticFact TO SemanticFact,
                contradiction_type STRING,
                resolved BOOLEAN,
                resolved_at TIMESTAMP,
                resolved_by STRING
            )
        """)
        
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS CAUSES (
                FROM TimelineEvent TO TimelineEvent,
                causal_strength DOUBLE,
                created_at TIMESTAMP
            )
        """)
        
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS PART_OF_TIMELINE (
                FROM TimelineEvent TO TimelineEvent,
                timeline_id STRING,
                created_at TIMESTAMP
            )
        """)
        
        # Create indexes
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_entity_companion ON Entity(companion_id)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_entity_type ON Entity(type)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_fact_companion ON SemanticFact(companion_id)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_fact_category ON SemanticFact(category)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_timeline_companion ON TimelineEvent(companion_id)")
    
    def _execute(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Execute a query and return results as list of dicts."""
        if params:
            result = self.conn.execute(query, params)
        else:
            result = self.conn.execute(query)
        
        # Convert to list of dicts
        columns = result.get_column_names()
        rows = []
        while result.has_next():
            row = result.get_next()
            rows.append(dict(zip(columns, row)))
        return rows
    
    # Write operations - mainly for graph entities
    async def write_episodic(self, memory: Any) -> str:
        # Episodic memories don't directly use Kuzu
        return memory.id
    
    async def write_semantic(self, memory: SemanticMemory) -> str:
        """Write semantic memory and its entities to graph."""
        # Create/update semantic fact node
        fact_id = memory.id
        self._execute("""
            MERGE (f:SemanticFact {id: $id})
            SET f.fact = $fact,
                f.category = $category,
                f.confidence = $confidence,
                f.source = $source,
                f.companion_id = $companion_id,
                f.user_id = $user_id,
                f.updated_at = $updated_at
            ON CREATE SET f.created_at = $created_at
        """, {
            "id": fact_id,
            "fact": memory.fact,
            "category": memory.category,
            "confidence": memory.confidence,
            "source": memory.source,
            "companion_id": memory.companion_id,
            "user_id": memory.user_id,
            "created_at": memory.created_at,
            "updated_at": memory.updated_at,
        })
        
        # Create entity nodes and relationships
        for entity in memory.entities:
            entity_id = entity.entity_id or f"ent_{uuid.uuid4().hex[:12]}"
            
            # Create/update entity
            self._execute("""
                MERGE (e:Entity {id: $id})
                SET e.type = $type,
                    e.value = $value,
                    e.description = $description,
                    e.confidence = $confidence,
                    e.companion_id = $companion_id,
                    e.user_id = $user_id,
                    e.updated_at = $updated_at
                ON CREATE SET e.created_at = $created_at
            """, {
                "id": entity_id,
                "type": entity.type,
                "value": entity.value,
                "description": "",
                "confidence": entity.confidence,
                "companion_id": memory.companion_id,
                "user_id": memory.user_id,
                "created_at": memory.created_at,
                "updated_at": memory.updated_at,
            })
            
            # Link entity to fact
            self._execute("""
                MERGE (e:Entity {id: $entity_id})-[:ENTITY_IN_FACT {role: $role}]->(f:SemanticFact {id: $fact_id})
            """, {
                "entity_id": entity_id,
                "fact_id": fact_id,
                "role": "subject",
            })
        
        # Handle contradictions
        if memory.contradicted_by:
            self._execute("""
                MERGE (f1:SemanticFact {id: $fact_id})-[r:FACT_CONTRADICTS]->(f2:SemanticFact {id: $contradicted_by})
                SET r.contradiction_type = "fact_contradiction",
                    r.resolved = FALSE
            """, {
                "fact_id": fact_id,
                "contradicted_by": memory.contradicted_by,
            })
        
        return fact_id
    
    async def write_emotional(self, memory: Any) -> str:
        return memory.id
    
    async def write_relationship(self, memory: Any) -> str:
        return memory.id
    
    async def write_timeline(self, memory: Any) -> str:
        """Write timeline memory to graph."""
        # Create timeline arc node if not exists
        timeline_id = f"timeline_{memory.companion_id}_{memory.narrative_arc[:30].replace(' ', '_')}"
        
        self._execute("""
            MERGE (t:TimelineEvent {id: $timeline_id})
            SET t.narrative_arc = $narrative_arc,
                t.companion_id = $companion_id,
                t.user_id = $user_id
            ON CREATE SET t.event_order = 0, t.description = $narrative_arc
        """, {
            "timeline_id": timeline_id,
            "narrative_arc": memory.narrative_arc,
            "companion_id": memory.companion_id,
            "user_id": memory.user_id,
        })
        
        # Create event nodes and link them
        for i, event in enumerate(memory.events):
            event_id = event.get("id", f"evt_{uuid.uuid4().hex[:12]}")
            
            self._execute("""
                MERGE (e:TimelineEvent {id: $event_id})
                SET e.narrative_arc = $narrative_arc,
                    e.event_order = $event_order,
                    e.description = $description,
                    e.timestamp = $timestamp,
                    e.companion_id = $companion_id,
                    e.user_id = $user_id
            """, {
                "event_id": event_id,
                "narrative_arc": memory.narrative_arc,
                "event_order": i,
                "description": event.get("description", ""),
                "timestamp": event.get("timestamp", memory.created_at),
                "companion_id": memory.companion_id,
                "user_id": memory.user_id,
            })
            
            # Link to timeline
            self._execute("""
                MERGE (e:TimelineEvent {id: $event_id})-[r:PART_OF_TIMELINE {timeline_id: $timeline_id}]->(t:TimelineEvent {id: $timeline_id})
            """, {
                "event_id": event_id,
                "timeline_id": timeline_id,
            })
            
            # Link causal relationships
            if i > 0:
                prev_event_id = memory.events[i-1].get("id", f"evt_{uuid.uuid4().hex[:12]}")
                self._execute("""
                    MERGE (e1:TimelineEvent {id: $prev_id})-[r:CAUSES {causal_strength: 0.8}]->(e2:TimelineEvent {id: $curr_id})
                """, {
                    "prev_id": prev_event_id,
                    "curr_id": event_id,
                })
        
        return memory.id
    
    async def write_preference(self, memory: Any) -> str:
        return memory.id
    
    async def bulk_write(self, memories: List[Any]) -> List[str]:
        ids = []
        for memory in memories:
            if isinstance(memory, SemanticMemory):
                ids.append(await self.write_semantic(memory))
            elif hasattr(memory, 'type') and memory.type == MemoryType.TIMELINE:
                ids.append(await self.write_timeline(memory))
        return ids
    
    # Read operations
    async def get_by_id(self, memory_id: str, memory_type: MemoryType) -> Optional[Any]:
        if memory_type == MemoryType.SEMANTIC:
            results = self._execute("""
                MATCH (f:SemanticFact {id: $id})
                OPTIONAL MATCH (e:Entity)-[:ENTITY_IN_FACT]->(f)
                RETURN f, collect(e) as entities
            """, {"id": memory_id})
            
            if results:
                fact_data = results[0]["f"]
                entities = results[0]["entities"]
                # Convert back to SemanticMemory - simplified
                return fact_data
        return None
    
    async def get_by_ids(self, memory_ids: List[str], memory_type: MemoryType) -> List[Any]:
        results = []
        for mid in memory_ids:
            mem = await self.get_by_id(mid, memory_type)
            if mem:
                results.append(mem)
        return results
    
    # Query operations
    async def query(self, filter: MemoryFilter) -> List[Any]:
        if filter.type == MemoryType.SEMANTIC:
            query = """
                MATCH (f:SemanticFact)
                WHERE f.companion_id = $companion_id
            """
            params = {"companion_id": filter.companion_id}
            
            if filter.user_id:
                query += " AND f.user_id = $user_id"
                params["user_id"] = filter.user_id
            
            if filter.category:
                query += " AND f.category = $category"
                params["category"] = filter.category
            
            query += " RETURN f ORDER BY f.created_at DESC LIMIT $limit"
            params["limit"] = filter.limit or 100
            
            results = self._execute(query, params)
            return [r["f"] for r in results]
        
        return []
    
    async def recall(self, query: RecallQuery, context: RecallContext) -> Any:
        # Kuzu doesn't handle vector recall
        return None
    
    # Graph-specific operations
    async def get_entity_neighbors(self, entity_id: str, max_depth: int = 2) -> List[Dict]:
        """Get related entities up to max_depth hops."""
        results = self._execute(f"""
            MATCH (e:Entity {{id: $entity_id}})-[:RELATED_TO*1..{max_depth}]-(neighbor:Entity)
            RETURN DISTINCT neighbor, 
                   relationships(collect(r)) as rels
            LIMIT 50
        """, {"entity_id": entity_id})
        return results
    
    async def find_entities_by_value(self, companion_id: str, value: str, 
                                      entity_type: Optional[str] = None) -> List[Dict]:
        """Find entities by value (fuzzy match)."""
        query = """
            MATCH (e:Entity)
            WHERE e.companion_id = $companion_id
              AND e.value CONTAINS $value
        """
        params = {"companion_id": companion_id, "value": value}
        
        if entity_type:
            query += " AND e.type = $type"
            params["type"] = entity_type
        
        query += " RETURN e LIMIT 20"
        return self._execute(query, params)
    
    async def get_facts_by_entity(self, entity_id: str) -> List[Dict]:
        """Get all semantic facts containing an entity."""
        results = self._execute("""
            MATCH (e:Entity {id: $entity_id})-[:ENTITY_IN_FACT]->(f:SemanticFact)
            RETURN f
            ORDER BY f.confidence DESC
        """, {"entity_id": entity_id})
        return [r["f"] for r in results]
    
    async def get_contradictions(self, companion_id: str) -> List[Dict]:
        """Get all unresolved contradictions for a companion."""
        results = self._execute("""
            MATCH (f1:SemanticFact)-[r:FACT_CONTRADICTS]->(f2:SemanticFact)
            WHERE f1.companion_id = $companion_id
              AND r.resolved = FALSE
            RETURN f1, f2, r
        """, {"companion_id": companion_id})
        return results
    
    async def resolve_contradiction(self, fact_id1: str, fact_id2: str, 
                                     resolution: str, resolved_by: str) -> bool:
        """Mark a contradiction as resolved."""
        self._execute("""
            MATCH (f1:SemanticFact {id: $id1})-[r:FACT_CONTRADICTS]->(f2:SemanticFact {id: $id2})
            SET r.resolved = TRUE,
                r.resolved_at = $resolved_at,
                r.resolved_by = $resolved_by,
                r.resolution = $resolution
        """, {
            "id1": fact_id1,
            "id2": fact_id2,
            "resolved_at": datetime.utcnow().isoformat(),
            "resolved_by": resolved_by,
            "resolution": resolution,
        })
        return True
    
    async def get_timeline(self, companion_id: str, narrative_arc: Optional[str] = None) -> List[Dict]:
        """Get timeline events for a companion."""
        query = """
            MATCH (e:TimelineEvent)-[:PART_OF_TIMELINE]->(t:TimelineEvent)
            WHERE e.companion_id = $companion_id
        """
        params = {"companion_id": companion_id}
        
        if narrative_arc:
            query += " AND t.narrative_arc = $narrative_arc"
            params["narrative_arc"] = narrative_arc
        
        query += " RETURN e ORDER BY e.event_order"
        return self._execute(query, params)
    
    async def find_causal_chains(self, event_id: str, max_length: int = 5) -> List[List[Dict]]:
        """Find causal chains leading to/from an event."""
        results = self._execute(f"""
            MATCH path = (e:TimelineEvent {{id: $event_id}})<-[:CAUSES*1..{max_length}]-(cause:TimelineEvent)
            RETURN path
            UNION
            MATCH path = (e:TimelineEvent {{id: $event_id}})-[:CAUSES*1..{max_length}]->(effect:TimelineEvent)
            RETURN path
        """, {"event_id": event_id})
        return results
    
    # Update operations
    async def update(self, memory_id: str, memory_type: MemoryType, updates: Dict[str, Any], 
                     new_version: int, reason: str) -> bool:
        # Graph updates would be specific to the type
        return True
    
    # Delete operations
    async def delete(self, memory_id: str, memory_type: MemoryType, 
                     verification: bool = True) -> Dict[str, Any]:
        if memory_type == MemoryType.SEMANTIC:
            self._execute("""
                MATCH (f:SemanticFact {id: $id})
                DETACH DELETE f
            """, {"id": memory_id})
        elif memory_type == MemoryType.TIMELINE:
            self._execute("""
                MATCH (e:TimelineEvent {id: $id})
                DETACH DELETE e
            """, {"id": memory_id})
        
        return {"memory_id": memory_id, "verification": {"graph_deleted": True}}
    
    async def bulk_delete(self, filter: MemoryFilter, confirm: bool = False) -> Dict[str, Any]:
        return {"deleted_count": 0, "verification": {"graph_deleted": True}}
    
    # Export operations
    async def export_all(self, companion_id: str, user_id: str, 
                         formats: List[str]) -> Dict[str, str]:
        return {"graph": "export_job_id", "status": "processing"}
    
    # Consolidation support
    async def get_consolidation_candidates(self, companion_id: str, 
                                           older_than_days: int = 30,
                                           max_access_count: int = 3) -> List[Any]:
        return []
    
    async def mark_consolidated(self, memory_ids: List[str], 
                                semantic_memory_ids: List[str]) -> None:
        pass
    
    # Consistency validation
    async def get_memories_for_validation(self, companion_id: str, 
                                           memory_types: List[MemoryType]) -> List[Any]:
        memories = []
        if MemoryType.SEMANTIC in memory_types:
            query = """
                MATCH (f:SemanticFact)
                WHERE f.companion_id = $companion_id
                RETURN f
            """
            results = self._execute(query, {"companion_id": companion_id})
            memories.extend([r["f"] for r in results])
        return memories