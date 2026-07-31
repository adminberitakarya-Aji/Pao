"""Core memory models for the Memory Engine."""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
import uuid


class MemoryType(str, Enum):
    """Types of memory supported by the engine."""
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    EMOTIONAL = "emotional"
    RELATIONSHIP = "relationship"
    TIMELINE = "timeline"
    PREFERENCE = "preference"


class EntityRef(BaseModel):
    """Reference to an entity in the knowledge graph."""
    type: str = Field(..., description="Entity type (person, place, concept, etc.)")
    value: str = Field(..., description="Entity value/name")
    entity_id: Optional[str] = Field(None, description="Graph node ID if resolved")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in entity resolution")


class MemoryBase(BaseModel):
    """Base model for all memory types."""
    id: str = Field(default_factory=lambda: f"mem_{uuid.uuid4().hex[:12]}")
    companion_id: str = Field(..., description="Companion identifier")
    user_id: str = Field(..., description="User identifier")
    type: MemoryType
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    version: int = Field(default=1, ge=1, description="Version for optimistic locking")
    source_message_ids: List[str] = Field(default_factory=list, description="Originating message IDs")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    importance: float = Field(default=0.5, ge=0.0, le=1.0, description="Importance score for retention")
    consolidated: bool = Field(default=False, description="Whether consolidated to semantic")
    consolidation_parent_id: Optional[str] = Field(None, description="Parent semantic memory ID")


class EpisodicMemory(MemoryBase):
    """Specific events, conversations, experiences with rich context."""
    type: Literal[MemoryType.EPISODIC] = MemoryType.EPISODIC
    event: str = Field(..., description="Natural language description of the event")
    timestamp: str = Field(..., description="When the event occurred")
    participants: List[str] = Field(default_factory=lambda: ["user", "companion"])
    modality: Literal["text", "voice", "video", "mixed"] = Field(default="text")
    emotional_tone: float = Field(default=0.0, ge=-1.0, le=1.0, description="Valence (-1 to 1)")
    emotional_intensity: float = Field(default=0.0, ge=0.0, le=1.0, description="Arousal (0 to 1)")
    topics: List[str] = Field(default_factory=list, description="Extracted topics")
    entities: List[EntityRef] = Field(default_factory=list, description="Linked entities")


class SemanticMemory(MemoryBase):
    """Facts, knowledge, concepts extracted from episodic memories."""
    type: Literal[MemoryType.SEMANTIC] = MemoryType.SEMANTIC
    fact: str = Field(..., description="Factual statement")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Confidence in fact")
    source: Literal["episodic", "user_explicit", "inferred"] = Field(default="episodic")
    source_episodic_ids: List[str] = Field(default_factory=list)
    entities: List[EntityRef] = Field(default_factory=list)
    category: str = Field(default="general", description="Category: preference, fact, belief, skill")
    contradicted_by: Optional[str] = Field(None, description="ID of memory that contradicts this")
    last_accessed: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    access_count: int = Field(default=0, ge=0)


class EmotionalMemory(MemoryBase):
    """Emotional associations, triggers, patterns."""
    type: Literal[MemoryType.EMOTIONAL] = MemoryType.EMOTIONAL
    trigger: str = Field(..., description="Topic, phrase, or situation that triggers emotion")
    emotion: Dict[str, float] = Field(..., description="Emotion profile: {'sadness': 0.7, 'gratitude': 0.3}")
    intensity: float = Field(default=0.5, ge=0.0, le=1.0)
    context: str = Field(default="", description="When this typically occurs")
    associated_memories: List[str] = Field(default_factory=list, description="Links to episodic/semantic")
    pattern_strength: float = Field(default=0.5, ge=0.0, le=1.0, description="Consistency of association")
    last_activated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    user_validated: bool = Field(default=False, description="User confirmed this pattern")


class RelationshipMemory(MemoryBase):
    """Relationship dimension history, milestones, dynamics."""
    type: Literal[MemoryType.RELATIONSHIP] = MemoryType.RELATIONSHIP
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    dimension_changes: Dict[str, float] = Field(..., description="Changes: {'trust': +0.2, 'intimacy': +0.1}")
    trigger_event: str = Field(..., description="What caused the change")
    trigger_type: Literal["conversation", "milestone", "conflict", "repair", "proactive"] = Field(...)
    relationship_type: str = Field(default="companion", description="Type of relationship")
    milestone: Optional[str] = Field(None, description="Milestone name if applicable")
    user_perception: Optional[float] = Field(None, ge=0.0, le=10.0, description="User-rated relationship quality")


class TimelineMemory(MemoryBase):
    """Causal narrative structure linking events across time."""
    type: Literal[MemoryType.TIMELINE] = MemoryType.TIMELINE
    narrative_arc: str = Field(..., description="High-level narrative: 'User's journey learning Spanish'")
    events: List[Dict[str, Any]] = Field(..., description="Ordered, causally linked events")
    themes: List[str] = Field(default_factory=list)
    status: Literal["active", "completed", "paused"] = Field(default="active")
    significance: float = Field(default=0.5, ge=0.0, le=1.0)
    user_curated: bool = Field(default=False)


class PreferenceMemory(MemoryBase):
    """User preferences, settings, habits (structured key-value)."""
    type: Literal[MemoryType.PREFERENCE] = MemoryType.PREFERENCE
    key: str = Field(..., description="Preference key: 'communication_style', 'medication_lisinopril'")
    value: Any = Field(..., description="Structured value")
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    source: Literal["explicit", "inferred", "observed"] = Field(default="explicit")
    category: str = Field(default="general", description="communication, health, routine, privacy")
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    expires_at: Optional[str] = Field(None, description="For time-bound preferences")


# Union type for all memory types
Memory = EpisodicMemory | SemanticMemory | EmotionalMemory | RelationshipMemory | TimelineMemory | PreferenceMemory


# API Request/Response Models

class MemoryWrite(BaseModel):
    """Request to write a memory."""
    type: MemoryType
    content: Dict[str, Any] = Field(..., description="Memory content (matches memory type schema)")
    companion_id: str
    user_id: str
    source_message_ids: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)


class MemoryRead(BaseModel):
    """Request to read a specific memory."""
    memory_id: str
    companion_id: str
    include_version_history: bool = Field(default=False)


class MemoryUpdate(BaseModel):
    """Request to update a memory (reconsolidation)."""
    memory_id: str
    companion_id: str
    updates: Dict[str, Any] = Field(..., description="Fields to update")
    reason: str = Field(..., description="Reason for update")
    source_message_id: Optional[str] = Field(None)


class MemoryDelete(BaseModel):
    """Request to delete a memory."""
    memory_id: str
    companion_id: str
    confirm: bool = Field(default=False, description="Must be true to confirm deletion")
    verification: Literal["full", "soft"] = Field(default="full")


class MemoryResponse(BaseModel):
    """Response for memory operations."""
    memory_id: str
    type: MemoryType
    content: Dict[str, Any]
    version: int
    created_at: str
    updated_at: str
    vector_id: Optional[str] = None
    graph_nodes_created: int = Field(default=0)


class MemoryFilter(BaseModel):
    """Filters for memory queries."""
    types: Optional[List[MemoryType]] = Field(default=None)
    date_range: Optional[Dict[str, str]] = Field(default=None, description="{start, end} ISO format")
    topics: Optional[List[str]] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)
    importance_min: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    importance_max: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    emotional_range: Optional[Dict[str, float]] = Field(default=None, description="{valence_min, valence_max}")
    consolidated: Optional[bool] = Field(default=None)
    source_message_ids: Optional[List[str]] = Field(default=None)


class RecallContext(BaseModel):
    """Context for context-aware recall."""
    current_topic: Optional[str] = Field(default=None)
    relationship_dimensions: Optional[Dict[str, float]] = Field(default=None)
    recent_topics: List[str] = Field(default_factory=list)
    time_since_last_message_hours: Optional[float] = Field(default=None)
    user_emotional_state: Optional[Dict[str, float]] = Field(default=None)
    active_goals: List[str] = Field(default_factory=list)


class RecallQuery(BaseModel):
    """Context-aware memory recall request."""
    query: str = Field(..., description="Natural language query or topic")
    companion_id: str
    user_id: str
    context: Optional[RecallContext] = Field(default=None)
    filters: Optional[MemoryFilter] = Field(default=None)
    limit: int = Field(default=15, ge=1, le=100)
    diversify: bool = Field(default=True, description="Diversify results across types/topics")
    include_relevance_scores: bool = Field(default=True)


class RecalledMemory(BaseModel):
    """A recalled memory with relevance scoring."""
    id: str
    type: MemoryType
    content: Dict[str, Any]
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    conversation_score: float = Field(..., ge=0.0, le=1.0, description="Fit for current conversation")
    recall_reason: str = Field(..., description="Why this memory was recalled")


class RecallResponse(BaseModel):
    """Response for recall query."""
    memories: List[RecalledMemory]
    total_candidates: int
    latency_ms: float
    query: str
    companion_id: str


class ConsolidationCandidate(BaseModel):
    """Candidate for consolidation."""
    memory_id: str
    type: MemoryType
    content: Dict[str, Any]
    age_days: int
    access_count: int
    cluster_id: Optional[str] = None


class ConsolidationReport(BaseModel):
    """Report from consolidation run."""
    companion_id: str
    episodic_processed: int
    semantic_created: int
    contradictions_found: int
    user_review_required: bool
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    details: Dict[str, Any] = Field(default_factory=dict)