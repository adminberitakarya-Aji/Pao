"""Consistency validation models for the Memory Engine."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
import uuid


class ContradictionType(str, Enum):
    """Types of contradictions detected."""
    FACT_CONTRADICTION = "fact_contradiction"
    TIMELINE_IMPOSSIBILITY = "timeline_impossibility"
    IDENTITY_VIOLATION = "identity_violation"
    PREFERENCE_CONFLICT = "preference_conflict"
    RELATIONSHIP_INCONSISTENCY = "relationship_inconsistency"


class ConsistencyCheck(str, Enum):
    """Types of consistency checks."""
    FACT_CONTRADICTION = "fact_contradiction"
    TIMELINE_IMPOSSIBILITY = "timeline_impossibility"
    IDENTITY_VIOLATION = "identity_violation"
    PREFERENCE_CONFLICT = "preference_conflict"
    RELATIONSHIP_INCONSISTENCY = "relationship_inconsistency"


class ConsistencyIssue(BaseModel):
    """A consistency issue found during validation."""
    id: str = Field(default_factory=lambda: f"issue_{uuid.uuid4().hex[:12]}")
    companion_id: str
    check_type: ConsistencyCheck
    contradiction_type: ContradictionType
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    description: str
    memory_ids: List[str] = Field(default_factory=list, description="Involved memory IDs")
    evidence: Dict[str, Any] = Field(default_factory=dict)
    auto_resolvable: bool = False
    suggested_resolution: Optional[str] = None
    detected_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    resolved_at: Optional[str] = None
    resolution: Optional[str] = None
    resolved_by: Optional[str] = None


class ConsistencyReport(BaseModel):
    """Report from a consistency validation run."""
    companion_id: str
    checked_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    total_issues: int = 0
    auto_resolved: int = 0
    requires_user_review: int = 0
    issues: List[ConsistencyIssue] = Field(default_factory=list)
    checks_run: List[ConsistencyCheck] = Field(default_factory=list)
    duration_ms: float = 0.0