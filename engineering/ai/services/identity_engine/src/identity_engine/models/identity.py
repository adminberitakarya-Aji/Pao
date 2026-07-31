"""Identity configuration and management models for Identity Engine."""

from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

from .personality import PersonalityConfig
from .values import ValuesConfig
from .voice import VoiceProfile
from .boundaries import Boundary
from .goals import Goal


class IdentityStatus(str, Enum):
    """Status of an identity configuration."""
    DRAFT = "draft"
    VALIDATING = "validating"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class IdentitySource(str, Enum):
    """Source of identity configuration."""
    TEMPLATE = "template"
    USER_CREATED = "user_created"
    AI_GENERATED = "ai_generated"
    IMPORTED = "imported"
    EVOLVED = "evolved"
    MERGED = "merged"


class IdentityRequest(BaseModel):
    """Request to create or update an identity."""
    companion_id: str = Field(..., description="Companion identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Identity name")
    description: str = Field(default="", description="Identity description")
    source: IdentitySource = Field(default=IdentitySource.USER_CREATED)
    
    # Component configurations (can be IDs or full configs)
    personality: Optional[PersonalityConfig] = Field(default=None)
    personality_id: Optional[str] = Field(default=None)
    values: Optional[ValuesConfig] = Field(default=None)
    values_id: Optional[str] = Field(default=None)
    voice: Optional[VoiceProfile] = Field(default=None)
    voice_id: Optional[str] = Field(default=None)
    boundaries: List[Boundary] = Field(default_factory=list)
    boundary_ids: List[str] = Field(default_factory=list)
    goals: List[Goal] = Field(default_factory=list)
    goal_ids: List[str] = Field(default_factory=list)
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Validation
    skip_validation: bool = Field(default=False)
    auto_activate: bool = Field(default=False)


class IdentityResponse(BaseModel):
    """Response containing identity configuration."""
    id: str = Field(..., description="Identity configuration ID")
    companion_id: str = Field(..., description="Companion identifier")
    version: int = Field(..., description="Identity version")
    
    # Components
    personality: PersonalityConfig
    values: ValuesConfig
    voice: VoiceProfile
    boundaries: List[Boundary] = Field(default_factory=list)
    goals: List[Goal] = Field(default_factory=list)
    
    # Status
    status: IdentityStatus
    source: IdentitySource
    
    # Validation
    is_valid: bool = Field(default=False)
    validation_errors: List[str] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)
    
    # Metadata
    name: str
    description: str
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: str
    updated_at: str
    activated_at: Optional[str] = None
    created_by: str


class IdentityVersion(BaseModel):
    """A versioned snapshot of an identity."""
    id: str = Field(..., description="Version ID")
    identity_id: str = Field(..., description="Parent identity ID")
    version: int = Field(..., description="Version number")
    
    # Snapshot data
    personality: PersonalityConfig
    values: ValuesConfig
    voice: VoiceProfile
    boundaries: List[Boundary]
    goals: List[Goal]
    
    # Change metadata
    change_type: Literal["create", "update", "evolve", "rollback", "merge"] = Field(default="update")
    change_summary: str = Field(default="", description="Human-readable change summary")
    changed_fields: List[str] = Field(default_factory=list, description="Fields that changed")
    change_reason: Optional[str] = Field(default=None, description="Reason for change")
    changed_by: str = Field(default="system")
    
    # Validation at time of version
    was_valid: bool = Field(default=False)
    validation_errors: List[str] = Field(default_factory=list)
    
    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def compute_diff(self, other: "IdentityVersion") -> Dict[str, Any]:
        """Compute diff between this version and another."""
        # This would be implemented with actual diff logic
        return {
            "version_from": self.version,
            "version_to": other.version,
            "changed_fields": [],  # Would be computed
            "similarity_score": 0.0,
        }


class IdentityConfig(BaseModel):
    """Complete identity configuration - the main aggregate."""
    id: str = Field(..., description="Unique identity config ID")
    companion_id: str = Field(..., description="Companion identifier")
    
    # Core components
    personality: PersonalityConfig
    values: ValuesConfig
    voice: VoiceProfile
    boundaries: List[Boundary] = Field(default_factory=list)
    goals: List[Goal] = Field(default_factory=list)
    
    # Configuration metadata
    version: int = Field(default=1, ge=1)
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="")
    status: IdentityStatus = Field(default=IdentityStatus.DRAFT)
    source: IdentitySource = Field(default=IdentitySource.USER_CREATED)
    
    # Validation
    is_valid: bool = Field(default=False)
    validation_errors: List[str] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)
    last_validated: Optional[str] = Field(default=None)
    
    # Lineage
    parent_version_id: Optional[str] = Field(default=None)
    template_id: Optional[str] = Field(default=None)
    evolution_history: List[str] = Field(default_factory=list, description="Evolution proposal IDs")
    
    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    activated_at: Optional[str] = None
    created_by: str = Field(default="system")
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def validate_consistency(self) -> tuple[bool, List[str], List[str]]:
        """Validate internal consistency of identity components."""
        errors = []
        warnings = []
        
        # Check personality-values alignment
        personality_traits = self.personality.traits
        core_values = self.values.get_core_values()
        
        # High agreeableness should align with caring values
        if personality_traits.agreeableness > 0.7:
            caring_values = [v for v in core_values if "care" in v.name.lower() or "compassion" in v.name.lower() or "kindness" in v.name.lower()]
            if not caring_values:
                warnings.append("High agreeableness but no caring/compassion core values")
        
        # High openness should align with learning/growth values
        if personality_traits.openness > 0.7:
            growth_values = [v for v in core_values if "growth" in v.name.lower() or "learning" in v.name.lower() or "curiosity" in v.name.lower()]
            if not growth_values:
                warnings.append("High openness but no learning/growth core values")
        
        # Check voice-personality alignment
        if self.personality.traits.extraversion > 0.7 and self.voice.formality.value in ["very_formal", "formal"]:
            warnings.append("High extraversion but very formal voice - may feel inconsistent")
        
        if self.personality.traits.playfulness > 0.7 and not self.voice.uses_humor:
            warnings.append("High playfulness but humor disabled in voice")
        
        # Check boundaries don't conflict with goals
        for goal in self.goals:
            if goal.type.value == "creative_collaboration":
                restrictive_boundaries = [b for b in self.boundaries if b.scope == BoundaryScope.GLOBAL and b.priority > 80]
                if restrictive_boundaries:
                    warnings.append(f"Creative collaboration goal may conflict with {len(restrictive_boundaries)} high-priority global boundaries")
        
        # Check for duplicate boundary IDs
        boundary_ids = [b.id for b in self.boundaries]
        if len(boundary_ids) != len(set(boundary_ids)):
            errors.append("Duplicate boundary IDs found")
        
        # Check for duplicate goal IDs
        goal_ids = [g.id for g in self.goals]
        if len(goal_ids) != len(set(goal_ids)):
            errors.append("Duplicate goal IDs found")
        
        is_valid = len(errors) == 0
        return is_valid, errors, warnings
    
    def to_vector(self) -> list[float]:
        """Convert full identity to embedding vector."""
        import numpy as np
        
        # Combine component vectors
        vectors = []
        vectors.append(self.personality.traits.to_vector())
        vectors.append(self.values.to_vector())
        vectors.append(self.voice.to_vector())
        
        # Goals vector (average of goal vectors)
        if self.goals:
            goal_vectors = [np.array(g.to_vector()) for g in self.goals]
            avg_goal = np.mean(goal_vectors, axis=0)
            vectors.append(avg_goal.tolist())
        else:
            vectors.append(np.zeros(20).tolist())
        
        # Boundaries summary
        boundary_vec = np.zeros(10)
        if self.boundaries:
            boundary_vec[0] = len(self.boundaries) / 20.0
            boundary_vec[1] = sum(b.priority for b in self.boundaries) / (len(self.boundaries) * 100)
            scopes = [b.scope.value for b in self.boundaries]
            boundary_vec[2] = scopes.count("global") / len(self.boundaries)
            boundary_vec[3] = scopes.count("topic") / len(self.boundaries)
            tags = set()
            for b in self.boundaries:
                tags.update(b.tags)
            boundary_vec[4] = len(tags) / 20.0
        vectors.append(boundary_vec.tolist())
        
        # Concatenate and normalize
        combined = np.concatenate(vectors)
        norm = np.linalg.norm(combined)
        if norm > 0:
            combined = combined / norm
        return combined.tolist()
    
    def create_version(self, change_type: str, change_summary: str, 
                       changed_fields: List[str], changed_by: str) -> IdentityVersion:
        """Create a version snapshot of current identity."""
        return IdentityVersion(
            id=f"{self.id}_v{self.version}",
            identity_id=self.id,
            version=self.version,
            personality=self.personality,
            values=self.values,
            voice=self.voice,
            boundaries=self.boundaries,
            goals=self.goals,
            change_type=change_type,
            change_summary=change_summary,
            changed_fields=changed_fields,
            changed_by=changed_by,
            was_valid=self.is_valid,
            validation_errors=self.validation_errors,
        )
    
    def get_active_boundaries(self, context: Optional[Dict[str, Any]] = None) -> List[Boundary]:
        """Get boundaries that apply in given context."""
        active = [b for b in self.boundaries if b.is_active]
        
        if context is None:
            return active
        
        # Filter by context
        contextual = []
        for b in active:
            if b.scope == BoundaryScope.GLOBAL:
                contextual.append(b)
            elif b.scope == BoundaryScope.CONTEXT:
                # Check context conditions
                matches = True
                for key, value in b.context_conditions.items():
                    if context.get(key) != value:
                        matches = False
                        break
                if matches:
                    contextual.append(b)
            elif b.scope == BoundaryScope.USER:
                if context.get("user_id") in b.user_ids:
                    contextual.append(b)
            elif b.scope == BoundaryScope.TOPIC:
                if context.get("topic_id") in b.topic_ids:
                    contextual.append(b)
            elif b.scope == BoundaryScope.CAPABILITY:
                if context.get("capability_id") in b.capability_ids:
                    contextual.append(b)
        
        # Sort by priority
        contextual.sort(key=lambda x: x.priority, reverse=True)
        return contextual
    
    def get_active_goals(self, context: Optional[Dict[str, Any]] = None) -> List[Goal]:
        """Get goals that apply in given context."""
        active = [g for g in self.goals if g.status == GoalStatus.ACTIVE]
        
        if context is None:
            return active
        
        contextual = []
        for g in active:
            if not g.applies_to_contexts or context.get("context_id") in g.applies_to_contexts:
                if not g.applies_to_users or context.get("user_segment") in g.applies_to_users:
                    # Check conditions
                    matches = True
                    for key, value in g.conditions.items():
                        if context.get(key) != value:
                            matches = False
                            break
                    if matches:
                        contextual.append(g)
        
        # Sort by priority
        contextual.sort(key=lambda x: x.priority, reverse=True)
        return contextual


# Import needed for BoundaryScope and GoalStatus
from .boundaries import BoundaryScope
from .goals import GoalStatus