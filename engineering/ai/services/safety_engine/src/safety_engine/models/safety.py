"""
Safety Engine Models.

Defines all data models for safety checking including:
- Crisis detection
- Content filtering (PII, hate, harassment, sexual, violence, illegal, medical, financial)
- Behavioral guards (manipulation, dependency, enmeshment, gaslighting, authority)
- Reality anchoring
- Intervention levels and responses
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class SafetyCategory(str, Enum):
    """Categories of safety violations."""
    
    # Crisis
    CRISIS = "crisis"
    SELF_HARM = "self_harm"
    SUICIDE = "suicide"
    
    # Content Policy
    HATE = "hate"
    HARASSMENT = "harassment"
    SEXUAL = "sexual"
    VIOLENCE = "violence"
    ILLEGAL = "illegal"
    MEDICAL = "medical"
    FINANCIAL = "financial"
    PII = "pii"
    
    # Behavioral
    MANIPULATION = "manipulation"
    DEPENDENCY = "dependency"
    ENMESHMENT = "enmeshment"
    GASLIGHTING = "gaslighting"
    AUTHORITY = "authority"
    
    # Reality
    DELUSION = "delusion"
    HALLUCINATION = "hallucination"
    PARANOIA = "paranoia"
    CONSPIRACY = "conspiracy"


class InterventionLevel(int, Enum):
    """Intervention severity levels."""
    
    ALLOW = 0              # No intervention needed
    GENTLE_REDIRECT = 1    # Soft topic change, empathetic redirect
    FIRM_BOUNDARY = 2      # Clear boundary setting
    RESOURCE_PROVIDE = 3   # Provide help resources (hotlines, etc.)
    CRISIS_ESCALATE = 4    # Immediate crisis response, human review


class CheckType(str, Enum):
    """Type of safety check being performed."""
    
    INPUT = "input"        # Pre-generation check (user input)
    OUTPUT = "output"      # Post-generation check (model output)
    STREAMING = "streaming" # Real-time streaming check
    BATCH = "batch"        # Batch/background check


class SafetyViolation(BaseModel):
    """A detected safety violation."""
    
    category: SafetyCategory
    confidence: float = Field(ge=0.0, le=1.0, description="Detection confidence (0-1)")
    severity: float = Field(ge=0.0, le=1.0, description="Severity score (0-1)")
    intervention_level: InterventionLevel
    matched_text: Optional[str] = Field(default=None, description="Text that triggered violation")
    matched_pattern: Optional[str] = Field(default=None, description="Pattern/keyword matched")
    location: Optional[Dict[str, int]] = Field(
        default=None, 
        description="Location in text (start, end)"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator("confidence", "severity")
    @classmethod
    def validate_scores(cls, v: float) -> float:
        return round(v, 4)


class CrisisDetectionResult(BaseModel):
    """Result of crisis detection analysis."""
    
    is_crisis: bool
    crisis_type: Optional[SafetyCategory] = None
    confidence: float = Field(ge=0.0, le=1.0)
    risk_level: str = Field(description="low, medium, high, critical")
    detected_keywords: List[str] = Field(default_factory=list)
    detected_patterns: List[str] = Field(default_factory=list)
    sentiment_score: Optional[float] = Field(default=None, ge=-1.0, le=1.0)
    urgency_score: float = Field(ge=0.0, le=1.0, description="How urgent the response needs to be")
    recommended_intervention: InterventionLevel
    crisis_resources: List[Dict[str, str]] = Field(default_factory=list)
    requires_human_review: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator("confidence", "urgency_score")
    @classmethod
    def validate_scores(cls, v: float) -> float:
        return round(v, 4)


class ContentFilterResult(BaseModel):
    """Result of content filtering analysis."""
    
    violations: List[SafetyViolation] = Field(default_factory=list)
    pii_detected: List[SafetyViolation] = Field(default_factory=list)
    redacted_text: Optional[str] = Field(default=None, description="Text with PII redacted")
    overall_risk: float = Field(ge=0.0, le=1.0, description="Overall risk score")
    passed: bool = Field(description="Whether content passes filter")
    intervention_level: InterventionLevel
    categories_checked: List[SafetyCategory] = Field(default_factory=list)
    processing_time_ms: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator("overall_risk")
    @classmethod
    def validate_risk(cls, v: float) -> float:
        return round(v, 4)


class BehavioralGuardResult(BaseModel):
    """Result of behavioral guard analysis."""
    
    violations: List[SafetyViolation] = Field(default_factory=list)
    manipulation_score: float = Field(ge=0.0, le=1.0, default=0.0)
    dependency_score: float = Field(ge=0.0, le=1.0, default=0.0)
    enmeshment_score: float = Field(ge=0.0, le=1.0, default=0.0)
    gaslighting_score: float = Field(ge=0.0, le=1.0, default=0.0)
    authority_score: float = Field(ge=0.0, le=1.0, default=0.0)
    overall_risk: float = Field(ge=0.0, le=1.0)
    intervention_level: InterventionLevel
    relationship_context: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Context about user-companion relationship"
    )
    conversation_history_summary: Optional[str] = Field(
        default=None,
        description="Summary of recent conversation for context"
    )
    processing_time_ms: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator(
        "manipulation_score", "dependency_score", "enmeshment_score",
        "gaslighting_score", "authority_score", "overall_risk"
    )
    @classmethod
    def validate_scores(cls, v: float) -> float:
        return round(v, 4)


class RealityAnchorResult(BaseModel):
    """Result of reality anchoring analysis."""
    
    triggered: bool = False
    trigger_category: Optional[SafetyCategory] = None
    detected_triggers: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    anchor_response: Optional[str] = Field(default=None, description="Reality anchor response to inject")
    intervention_level: InterventionLevel = InterventionLevel.ALLOW
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        return round(v, 4)


class SafetyCheckRequest(BaseModel):
    """Request for safety checking."""
    
    text: str = Field(min_length=1, max_length=100000, description="Text to check")
    check_type: CheckType = CheckType.INPUT
    companion_id: Optional[str] = Field(default=None, description="Companion ID for context")
    user_id: Optional[str] = Field(default=None, description="User ID for context")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID for context")
    relationship_context: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Relationship dimensions, phase, history"
    )
    enable_crisis_detection: bool = True
    enable_content_filter: bool = True
    enable_behavioral_guards: bool = True
    enable_reality_anchor: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SafetyCheckResponse(BaseModel):
    """Complete safety check response."""
    
    request_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    passed: bool = Field(description="Overall pass/fail")
    intervention_level: InterventionLevel
    crisis: Optional[CrisisDetectionResult] = None
    content_filter: Optional[ContentFilterResult] = None
    behavioral_guards: Optional[BehavioralGuardResult] = None
    reality_anchor: Optional[RealityAnchorResult] = None
    safe_response: Optional[str] = Field(default=None, description="Safe/rewritten response if intervention needed")
    refusal_message: Optional[str] = Field(default=None, description="Refusal message if blocked")
    processing_time_ms: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SafetyAlert(BaseModel):
    """Safety alert for Kafka/events."""
    
    alert_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: str
    companion_id: str
    conversation_id: Optional[str] = None
    alert_type: SafetyCategory
    severity: str  # low, medium, high, critical
    intervention_level: InterventionLevel
    details: Dict[str, Any]
    requires_human_review: bool = False
    acknowledged: bool = False
    resolved: bool = False


class SafetyMetrics(BaseModel):
    """Safety engine metrics."""
    
    total_checks: int = 0
    crisis_detected: int = 0
    content_violations: int = 0
    behavioral_violations: int = 0
    reality_anchors_triggered: int = 0
    interventions_by_level: Dict[int, int] = Field(default_factory=dict)
    avg_processing_time_ms: float = 0.0
    false_positive_rate: float = 0.0
    false_negative_rate: float = 0.0