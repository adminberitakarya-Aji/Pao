"""Consolidation models for the Memory Engine."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
import uuid


class ConsolidationStatus(str, Enum):
    """Status of a consolidation job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class ConsolidationJob(BaseModel):
    """A consolidation job for a companion."""
    id: str = Field(default_factory=lambda: f"consol_{uuid.uuid4().hex[:12]}")
    companion_id: str
    user_id: str
    status: ConsolidationStatus = ConsolidationStatus.PENDING
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    episodic_candidates: int = 0
    semantic_created: int = 0
    contradictions_found: int = 0
    user_review_required: bool = False
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ClusterResult(BaseModel):
    """Result of clustering episodic memories."""
    cluster_id: str
    memories: List[str]  # Memory IDs
    theme: str
    entities: List[str]
    centroid_embedding: List[float]
    size: int
    coherence_score: float = Field(ge=0.0, le=1.0)


class FactExtraction(BaseModel):
    """A fact extracted from a cluster."""
    statement: str
    confidence: float = Field(ge=0.0, le=1.0)
    category: str  # preference, fact, belief, skill
    entities: List[Dict[str, str]]
    source_memory_ids: List[str]
    contradicts: Optional[str] = None  # ID of semantic memory this contradicts