"""Evolution models for Identity Engine - handles identity evolution over time."""

from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

from .fingerprint import DriftResult, DriftSeverity


class EvolutionTriggerType(str, Enum):
    """Types of triggers that can initiate evolution."""
    DRIFT_DETECTED = "drift_detected"
    USER_FEEDBACK = "user_feedback"
    PERFORMANCE_DECLINE = "performance_decline"
    GOAL_MISALIGNMENT = "goal_misalignment"
    BOUNDARY_VIOLATIONS = "boundary_violations"
    SCHEDULED_REVIEW = "scheduled_review"
    MANUAL_REQUEST = "manual_request"
    CONTEXT_CHANGE = "context_change"
    CAPABILITY_CHANGE = "capability_change"
    COMPLIANCE_UPDATE = "compliance_update"


class EvolutionProposalStatus(str, Enum):
    """Status of an evolution proposal."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTING = "implementing"
    IMPLEMENTED = "implemented"
    ROLLED_BACK = "rolled_back"
    SUPERSEDED = "superseded"


class EvolutionChangeType(str, Enum):
    """Types of changes in an evolution."""
    PERSONALITY_ADJUSTMENT = "personality_adjustment"
    VALUES_UPDATE = "values_update"
    VOICE_MODIFICATION = "voice_modification"
    BOUNDARY_ADDITION = "boundary_addition"
    BOUNDARY_MODIFICATION = "boundary_modification"
    BOUNDARY_REMOVAL = "boundary_removal"
    GOAL_ADDITION = "goal_addition"
    GOAL_MODIFICATION = "goal_modification"
    GOAL_REMOVAL = "goal_removal"
    STRUCTURAL_CHANGE = "structural_change"
    METADATA_UPDATE = "metadata_update"


class EvolutionTrigger(BaseModel):
    """Trigger that initiated an evolution proposal."""
    id: str = Field(..., description="Trigger ID")
    type: EvolutionTriggerType = Field(..., description="Trigger type")
    name: str = Field(..., description="Trigger name")
    description: str = Field(default="", description="Trigger description")
    
    # Trigger data
    drift_result_id: Optional[str] = Field(default=None)
    feedback_ids: List[str] = Field(default_factory=list)
    metric_ids: List[str] = Field(default_factory=list)
    context_changes: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    detected_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    detected_by: str = Field(default="system")
    severity: DriftSeverity = Field(default=DriftSeverity.NONE)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvolutionEvidence(BaseModel):
    """Evidence supporting an evolution change."""
    id: str = Field(..., description="Evidence ID")
    proposal_id: str = Field(..., description="Associated proposal ID")
    change_id: str = Field(..., description="Associated change ID")
    
    # Evidence details
    source: Literal["drift_analysis", "user_feedback", "metrics", "evaluation", "manual", "benchmark"] = Field(...)
    description: str = Field(..., description="What this evidence shows")
    data: Dict[str, Any] = Field(default_factory=dict, description="Raw evidence data")
    strength: float = Field(default=0.5, ge=0.0, le=1.0, description="Evidence strength (0-1)")
    
    # Metadata
    collected_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    collected_by: str = Field(default="system")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvolutionChange(BaseModel):
    """A single change in an evolution proposal."""
    id: str = Field(..., description="Change ID")
    proposal_id: str = Field(..., description="Parent proposal ID")
    type: EvolutionChangeType = Field(..., description="Change type")
    
    # Target
    target_component: Literal["personality", "values", "voice", "boundaries", "goals", "metadata"] = Field(...)
    target_field: str = Field(..., description="Specific field being changed")
    target_id: Optional[str] = Field(default=None, description="ID of specific item (e.g., boundary ID)")
    
    # Change details
    current_value: Any = Field(default=None, description="Current value")
    proposed_value: Any = Field(default=None, description="Proposed new value")
    change_description: str = Field(..., description="Human-readable change description")
    rationale: str = Field(default="", description="Why this change is proposed")
    
    # Impact assessment
    impact_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Estimated impact (0-1)")
    risk_level: Literal["low", "medium", "high", "critical"] = Field(default="low")
    affected_dimensions: List[str] = Field(default_factory=list, description="Identity dimensions affected")
    
    # Evidence
    evidence_ids: List[str] = Field(default_factory=list, description="Supporting evidence IDs")
    
    # Validation
    is_validated: bool = Field(default=False)
    validation_notes: Optional[str] = Field(default=None)
    
    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvolutionProposal(BaseModel):
    """A proposal for evolving a companion's identity."""
    id: str = Field(..., description="Proposal ID")
    companion_id: str = Field(..., description="Companion identifier")
    identity_id: str = Field(..., description="Identity configuration ID")
    baseline_version: int = Field(..., description="Baseline identity version")
    
    # Proposal details
    name: str = Field(..., min_length=1, max_length=200, description="Proposal name")
    description: str = Field(default="", description="Proposal description")
    trigger: EvolutionTrigger = Field(..., description="What triggered this proposal")
    
    # Changes
    changes: List[EvolutionChange] = Field(default_factory=list, description="Proposed changes")
    
    # Status
    status: EvolutionProposalStatus = Field(default=EvolutionProposalStatus.DRAFT)
    
    # Assessment
    overall_impact: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall impact score")
    overall_risk: Literal["low", "medium", "high", "critical"] = Field(default="low")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence in proposal")
    
    # Review
    reviewer_ids: List[str] = Field(default_factory=list, description="Assigned reviewers")
    review_deadline: Optional[str] = Field(default=None, description="Review deadline")
    review_notes: List[str] = Field(default_factory=list)
    approval_count: int = Field(default=0)
    rejection_count: int = Field(default=0)
    required_approvals: int = Field(default=1)
    
    # Implementation
    implementation_plan: Optional[str] = Field(default=None)
    rollback_plan: Optional[str] = Field(default=None)
    test_cases: List[str] = Field(default_factory=list)
    
    # Results (after implementation)
    implemented_version: Optional[int] = Field(default=None)
    implementation_notes: Optional[str] = Field(default=None)
    post_implementation_drift: Optional[float] = Field(default=None)
    
    # Metadata
    version: int = Field(default=1)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    created_by: str = Field(default="system")
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def get_changes_by_component(self) -> Dict[str, List[EvolutionChange]]:
        """Group changes by target component."""
        grouped = {}
        for change in self.changes:
            if change.target_component not in grouped:
                grouped[change.target_component] = []
            grouped[change.target_component].append(change)
        return grouped
    
    def get_high_risk_changes(self) -> List[EvolutionChange]:
        """Get changes with high or critical risk."""
        return [c for c in self.changes if c.risk_level in ["high", "critical"]]
    
    def compute_overall_metrics(self):
        """Compute overall impact and risk from changes."""
        if not self.changes:
            self.overall_impact = 0.0
            self.overall_risk = "low"
            return
        
        self.overall_impact = sum(c.impact_score for c in self.changes) / len(self.changes)
        
        risk_levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        max_risk = max(risk_levels.get(c.risk_level, 1) for c in self.changes)
        self.overall_risk = {v: k for k, v in risk_levels.items()}[max_risk]
    
    def can_approve(self) -> bool:
        """Check if proposal has enough approvals."""
        return self.approval_count >= self.required_approvals and self.rejection_count == 0
    
    def is_ready_for_implementation(self) -> bool:
        """Check if proposal is ready to implement."""
        return (
            self.status == EvolutionProposalStatus.APPROVED and
            all(c.is_validated for c in self.changes) and
            self.implementation_plan is not None
        )


class EvolutionResult(BaseModel):
    """Result of implementing an evolution proposal."""
    id: str = Field(..., description="Result ID")
    proposal_id: str = Field(..., description="Implemented proposal ID")
    companion_id: str = Field(..., description="Companion identifier")
    
    # Implementation details
    status: Literal["success", "partial", "failed", "rolled_back"] = Field(...)
    implemented_changes: List[str] = Field(default_factory=list, description="Change IDs successfully implemented")
    failed_changes: List[Dict[str, Any]] = Field(default_factory=list, description="Failed changes with errors")
    
    # Versioning
    previous_version: int = Field(..., description="Version before evolution")
    new_version: int = Field(..., description="Version after evolution")
    
    # Validation
    post_implementation_validation: bool = Field(default=False)
    validation_errors: List[str] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)
    
    # Drift measurement
    pre_implementation_drift: Optional[float] = Field(default=None)
    post_implementation_drift: Optional[float] = Field(default=None)
    drift_reduction: Optional[float] = Field(default=None)
    
    # Performance impact
    performance_metrics: Dict[str, float] = Field(default_factory=dict)
    user_feedback_summary: Optional[str] = Field(default=None)
    
    # Rollback info
    rollback_reason: Optional[str] = Field(default=None)
    rollback_version: Optional[int] = Field(default=None)
    
    # Metadata
    implemented_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    implemented_by: str = Field(default="system")
    duration_ms: float = Field(default=0.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def is_successful(self) -> bool:
        """Check if evolution was successful."""
        return self.status == "success" and len(self.failed_changes) == 0


class EvolutionRule(BaseModel):
    """Rule for automatic evolution proposals."""
    id: str = Field(..., description="Rule ID")
    name: str = Field(..., description="Rule name")
    description: str = Field(default="", description="Rule description")
    
    # Trigger conditions
    trigger_conditions: Dict[str, Any] = Field(..., description="Conditions that trigger this rule")
    # Example: {"drift_severity": "moderate", "dimension": "personality", "threshold": 0.2}
    
    # Proposed changes template
    change_template: List[Dict[str, Any]] = Field(default_factory=list, description="Template for changes")
    
    # Constraints
    max_proposals_per_period: int = Field(default=1, description="Max proposals per time period")
    period_days: int = Field(default=30, description="Time period in days")
    requires_human_approval: bool = Field(default=True)
    auto_approve_threshold: Optional[float] = Field(default=None, description="Auto-approve if confidence > threshold")
    
    # Metadata
    is_active: bool = Field(default=True)
    version: int = Field(default=1)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    created_by: str = Field(default="system")
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def matches(self, context: Dict[str, Any]) -> bool:
        """Check if rule matches current context."""
        # This would be implemented with actual rule matching logic
        return False


# Predefined evolution rules
EVOLUTION_RULES = {
    "drift_personality_moderate": EvolutionRule(
        id="drift_personality_moderate",
        name="Moderate Personality Drift Correction",
        description="Automatically propose personality adjustments when moderate drift detected",
        trigger_conditions={
            "drift_severity": "moderate",
            "dimension": "personality",
            "threshold": 0.15,
        },
        change_template=[
            {
                "type": "personality_adjustment",
                "target_component": "personality",
                "target_field": "traits",
                "description": "Adjust drifted personality traits toward baseline",
                "rationale": "Moderate personality drift detected, correcting toward established baseline",
            }
        ],
        max_proposals_per_period=1,
        period_days=30,
        requires_human_approval=True,
    ),
    
    "drift_voice_significant": EvolutionRule(
        id="drift_voice_significant",
        name="Significant Voice Drift Review",
        description="Flag significant voice drift for human review",
        trigger_conditions={
            "drift_severity": "significant",
            "dimension": "voice",
            "threshold": 0.30,
        },
        change_template=[
            {
                "type": "voice_modification",
                "target_component": "voice",
                "target_field": "formality",
                "description": "Review and adjust voice formality",
                "rationale": "Significant voice drift affecting user experience",
            }
        ],
        max_proposals_per_period=1,
        period_days=14,
        requires_human_approval=True,
    ),
    
    "boundary_violations_frequent": EvolutionRule(
        id="boundary_violations_frequent",
        name="Frequent Boundary Violations",
        description="Propose boundary adjustments when violations are frequent",
        trigger_conditions={
            "metric": "boundary_violations",
            "threshold": 10,
            "window_days": 7,
        },
        change_template=[
            {
                "type": "boundary_modification",
                "target_component": "boundaries",
                "description": "Review and adjust frequently triggered boundaries",
                "rationale": "High boundary violation rate indicates misalignment",
            }
        ],
        max_proposals_per_period=2,
        period_days=30,
        requires_human_approval=True,
    ),
    
    "goal_misalignment": EvolutionRule(
        id="goal_misalignment",
        name="Goal Misalignment Correction",
        description="Propose goal adjustments when metrics consistently off-track",
        trigger_conditions={
            "metric_status": "off_track",
            "consecutive_periods": 3,
            "goal_types": ["user_satisfaction", "engagement", "learning"],
        },
        change_template=[
            {
                "type": "goal_modification",
                "target_component": "goals",
                "description": "Adjust goal targets or add supporting sub-goals",
                "rationale": "Consistent goal misalignment requires strategic adjustment",
            }
        ],
        max_proposals_per_period=1,
        period_days=60,
        requires_human_approval=True,
    ),
    
    "user_feedback_pattern": EvolutionRule(
        id="user_feedback_pattern",
        name="User Feedback Pattern",
        description="Propose changes based on consistent user feedback themes",
        trigger_conditions={
            "feedback_theme_count": 5,
            "theme_consistency": 0.8,
            "sentiment": "negative",
        },
        change_template=[
            {
                "type": "voice_modification",
                "target_component": "voice",
                "description": "Adjust voice based on user feedback",
                "rationale": "Consistent user feedback indicates voice misalignment",
            }
        ],
        max_proposals_per_period=1,
        period_days=30,
        requires_human_approval=True,
    ),
}