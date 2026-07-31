"""Values models for Identity Engine."""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class ValueCategory(str, Enum):
    """Categories of values."""
    ETHICAL = "ethical"
    INTELLECTUAL = "intellectual"
    SOCIAL = "social"
    PERSONAL_GROWTH = "personal_growth"
    CREATIVE = "creative"
    PROFESSIONAL = "professional"
    WELLBEING = "wellbeing"
    RELATIONSHIP = "relationship"
    CUSTOM = "custom"


class ValuePriority(str, Enum):
    """Priority levels for values."""
    CORE = "core"           # Non-negotiable, defines identity
    HIGH = "high"           # Very important, rarely compromised
    MEDIUM = "medium"       # Important, flexible in context
    LOW = "low"             # Nice to have, easily adapted
    CONTEXTUAL = "contextual"  # Depends on situation


class Value(BaseModel):
    """A single value with metadata."""
    id: str = Field(..., description="Unique value identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Value name")
    category: ValueCategory = Field(..., description="Value category")
    priority: ValuePriority = Field(default=ValuePriority.MEDIUM, description="Priority level")
    description: str = Field(default="", description="Detailed description")
    description_user_facing: str = Field(default="", description="User-facing description")
    
    # Behavioral guidance
    behavioral_guidelines: List[str] = Field(default_factory=list, description="How this value guides behavior")
    linguistic_markers: List[str] = Field(default_factory=list, description="Words/phrases indicating this value")
    anti_patterns: List[str] = Field(default_factory=list, description="Behaviors that violate this value")
    
    # Contextual weights
    context_weights: Dict[str, float] = Field(
        default_factory=dict, 
        description="Weight adjustments per context (0-2 multiplier)"
    )
    
    # Relationships
    conflicts_with: List[str] = Field(default_factory=list, description="Value IDs this conflicts with")
    supports: List[str] = Field(default_factory=list, description="Value IDs this supports")
    requires: List[str] = Field(default_factory=list, description="Value IDs required for this to apply")
    
    # Metadata
    version: int = Field(default=1, ge=1)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def is_applicable(self, context: Dict[str, Any]) -> float:
        """Compute applicability weight for a given context (0-1)."""
        base_weight = {
            ValuePriority.CORE: 1.0,
            ValuePriority.HIGH: 0.8,
            ValuePriority.MEDIUM: 0.5,
            ValuePriority.LOW: 0.2,
            ValuePriority.CONTEXTUAL: 0.3,
        }[self.priority]
        
        # Apply context weights
        context_weight = 1.0
        for ctx_key, ctx_value in context.items():
            if ctx_key in self.context_weights:
                context_weight *= self.context_weights[ctx_key]
        
        return min(1.0, base_weight * context_weight)


class ValuesConfig(BaseModel):
    """Complete values configuration for a companion."""
    id: str = Field(..., description="Unique values config ID")
    companion_id: str = Field(..., description="Companion identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Values config name")
    description: str = Field(default="", description="Human-readable description")
    
    # Values
    values: List[Value] = Field(default_factory=list, description="Ordered list of values (priority order)")
    
    # Value hierarchy
    hierarchy: Dict[str, List[str]] = Field(
        default_factory=dict, 
        description="Parent -> children value IDs for hierarchical organization"
    )
    
    # Conflict resolution
    conflict_resolution: str = Field(
        default="priority_based",
        description="Strategy: priority_based, contextual, user_preference, hybrid"
    )
    
    # Metadata
    version: int = Field(default=1, ge=1)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    created_by: str = Field(default="system")
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Validation
    is_active: bool = Field(default=True)
    is_validated: bool = Field(default=False)
    validation_notes: Optional[str] = Field(default=None)
    
    def get_core_values(self) -> List[Value]:
        """Get all core priority values."""
        return [v for v in self.values if v.priority == ValuePriority.CORE]
    
    def get_values_by_category(self, category: ValueCategory) -> List[Value]:
        """Get values filtered by category."""
        return [v for v in self.values if v.category == category]
    
    def get_applicable_values(self, context: Dict[str, Any], threshold: float = 0.3) -> List[Value]:
        """Get values applicable in a given context above threshold."""
        applicable = []
        for value in self.values:
            weight = value.is_applicable(context)
            if weight >= threshold:
                applicable.append(value)
        # Sort by applicability weight descending
        applicable.sort(key=lambda v: v.is_applicable(context), reverse=True)
        return applicable
    
    def check_conflicts(self, value_ids: List[str]) -> List[tuple[str, str]]:
        """Check for conflicts among a set of value IDs."""
        conflicts = []
        value_map = {v.id: v for v in self.values}
        for i, vid1 in enumerate(value_ids):
            for vid2 in value_ids[i+1:]:
                v1 = value_map.get(vid1)
                v2 = value_map.get(vid2)
                if v1 and v2 and (vid2 in v1.conflicts_with or vid1 in v2.conflicts_with):
                    conflicts.append((vid1, vid2))
        return conflicts
    
    def resolve_conflicts(self, value_ids: List[str], context: Dict[str, Any]) -> List[str]:
        """Resolve conflicts using configured strategy."""
        if self.conflict_resolution == "priority_based":
            # Sort by priority, keep highest
            priority_order = {p: i for i, p in enumerate([
                ValuePriority.CORE, ValuePriority.HIGH, ValuePriority.MEDIUM, 
                ValuePriority.LOW, ValuePriority.CONTEXTUAL
            ])}
            sorted_values = sorted(value_ids, key=lambda v: priority_order.get(
                next((val.priority for val in self.values if val.id == v), ValuePriority.LOW)
            ))
            return [sorted_values[0]] if sorted_values else []
        elif self.conflict_resolution == "contextual":
            # Sort by contextual applicability
            sorted_values = sorted(value_ids, key=lambda v: next(
                (val.is_applicable(context) for val in self.values if val.id == v), 0
            ), reverse=True)
            return [sorted_values[0]] if sorted_values else []
        return value_ids  # No resolution
    
    def to_vector(self) -> list[float]:
        """Convert values to a fixed-size embedding vector."""
        import numpy as np
        # Fixed categories in order
        categories = [c.value for c in ValueCategory]
        vector = np.zeros(len(categories) * 3)  # priority, weight, count per category
        
        for value in self.values:
            cat_idx = categories.index(value.category.value)
            priority_weight = {
                ValuePriority.CORE: 1.0,
                ValuePriority.HIGH: 0.8,
                ValuePriority.MEDIUM: 0.5,
                ValuePriority.LOW: 0.2,
                ValuePriority.CONTEXTUAL: 0.3,
            }[value.priority]
            vector[cat_idx * 3] += priority_weight
            vector[cat_idx * 3 + 1] += value.is_applicable({})
            vector[cat_idx * 3 + 2] += 1
        
        # Normalize
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector.tolist()