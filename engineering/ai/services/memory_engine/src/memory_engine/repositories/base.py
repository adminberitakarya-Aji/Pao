"""Base repository interface for Memory Engine."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime

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


class MemoryRepository(ABC):
    """Abstract base class for memory storage backends."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the repository (create tables, collections, etc.)."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close connections and cleanup."""
        pass
    
    # Write operations
    @abstractmethod
    async def write_episodic(self, memory: EpisodicMemory) -> str:
        """Write an episodic memory. Returns memory ID."""
        pass
    
    @abstractmethod
    async def write_semantic(self, memory: SemanticMemory) -> str:
        """Write a semantic memory. Returns memory ID."""
        pass
    
    @abstractmethod
    async def write_emotional(self, memory: EmotionalMemory) -> str:
        """Write an emotional memory. Returns memory ID."""
        pass
    
    @abstractmethod
    async def write_relationship(self, memory: RelationshipMemory) -> str:
        """Write a relationship memory. Returns memory ID."""
        pass
    
    @abstractmethod
    async def write_timeline(self, memory: TimelineMemory) -> str:
        """Write a timeline memory. Returns memory ID."""
        pass
    
    @abstractmethod
    async def write_preference(self, memory: PreferenceMemory) -> str:
        """Write a preference memory. Returns memory ID."""
        pass
    
    @abstractmethod
    async def bulk_write(self, memories: List[Any]) -> List[str]:
        """Bulk write multiple memories. Returns list of memory IDs."""
        pass
    
    # Read operations
    @abstractmethod
    async def get_by_id(self, memory_id: str, memory_type: MemoryType) -> Optional[Any]:
        """Get a memory by ID and type."""
        pass
    
    @abstractmethod
    async def get_by_ids(self, memory_ids: List[str], memory_type: MemoryType) -> List[Any]:
        """Get multiple memories by IDs."""
        pass
    
    # Query operations
    @abstractmethod
    async def query(self, filter: MemoryFilter) -> List[Any]:
        """Query memories with filter."""
        pass
    
    @abstractmethod
    async def recall(self, query: RecallQuery, context: RecallContext) -> RecallResponse:
        """Context-aware recall with reranking."""
        pass
    
    # Update operations
    @abstractmethod
    async def update(self, memory_id: str, memory_type: MemoryType, updates: Dict[str, Any], 
                     new_version: int, reason: str) -> bool:
        """Update a memory with version control."""
        pass
    
    # Delete operations
    @abstractmethod
    async def delete(self, memory_id: str, memory_type: MemoryType, 
                     verification: bool = True) -> Dict[str, Any]:
        """Delete a memory with verification."""
        pass
    
    @abstractmethod
    async def bulk_delete(self, filter: MemoryFilter, confirm: bool = False) -> Dict[str, Any]:
        """Bulk delete memories matching filter."""
        pass
    
    # Export operations
    @abstractmethod
    async def export_all(self, companion_id: str, user_id: str, 
                         formats: List[str]) -> Dict[str, str]:
        """Export all memories for a companion."""
        pass
    
    # Consolidation support
    @abstractmethod
    async def get_consolidation_candidates(self, companion_id: str, 
                                           older_than_days: int = 30,
                                           max_access_count: int = 3) -> List[Any]:
        """Get episodic memories ready for consolidation."""
        pass
    
    @abstractmethod
    async def mark_consolidated(self, memory_ids: List[str], 
                                semantic_memory_ids: List[str]) -> None:
        """Mark episodic memories as consolidated."""
        pass
    
    # Consistency validation
    @abstractmethod
    async def get_memories_for_validation(self, companion_id: str, 
                                           memory_types: List[MemoryType]) -> List[Any]:
        """Get memories for consistency validation."""
        pass
    
    @abstractmethod
    async def resolve_contradiction(self, issue_id: str, resolution: str,
                                     resolved_by: str) -> bool:
        """Mark a contradiction as resolved."""
        pass