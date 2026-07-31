"""Identity Engine Models - Pydantic models for companion identity."""

from .personality import PersonalityConfig, PersonalityTraits, TraitExpression, CompanionType
from .values import ValuesConfig, Value, ValueCategory, ValuePriority
from .voice import (
    VoiceProfile, VoiceProfileTemplate, VoiceCharacteristic,
    FormalityLevel, VerbosityLevel, EmotionalTone, CommunicationStyle,
    VOICE_TEMPLATES
)
from .boundaries import (
    Boundary, BoundaryTrigger, BoundaryAction,
    BoundaryScope, BoundaryTriggerType, BoundaryActionType,
    BOUNDARY_TEMPLATES
)
from .goals import (
    Goal, GoalType, GoalStatus, Metric, MetricType, MetricAggregation,
    GoalTemplate, GOAL_TEMPLATES
)
from .identity import (
    IdentityConfig, IdentityRequest, IdentityResponse, IdentityVersion,
    IdentityStatus, IdentitySource
)
from .fingerprint import (
    FingerprintVector, FingerprintResult, DriftResult, DriftDimension, DriftSeverity,
    DriftAlert, FingerprintComparison, compute_drift_severity, compute_dimension_drift,
    DRIFT_SEVERITY_THRESHOLDS
)
from .evolution import (
    EvolutionProposal, EvolutionTrigger, EvolutionEvidence, EvolutionResult, EvolutionChange,
    EvolutionProposalStatus, EvolutionChangeType, EvolutionTriggerType, EvolutionRule,
    EVOLUTION_RULES
)

__all__ = [
    # Personality
    "PersonalityConfig",
    "PersonalityTraits",
    "TraitExpression",
    "CompanionType",
    # Values
    "ValuesConfig",
    "Value",
    "ValueCategory",
    "ValuePriority",
    # Voice
    "VoiceProfile",
    "VoiceProfileTemplate",
    "VoiceCharacteristic",
    "FormalityLevel",
    "VerbosityLevel",
    "EmotionalTone",
    "CommunicationStyle",
    "VOICE_TEMPLATES",
    # Boundaries
    "Boundary",
    "BoundaryTrigger",
    "BoundaryAction",
    "BoundaryScope",
    "BoundaryTriggerType",
    "BoundaryActionType",
    "BOUNDARY_TEMPLATES",
    # Goals
    "Goal",
    "GoalType",
    "GoalStatus",
    "Metric",
    "MetricType",
    "MetricAggregation",
    "GoalTemplate",
    "GOAL_TEMPLATES",
    # Identity
    "IdentityConfig",
    "IdentityRequest",
    "IdentityResponse",
    "IdentityVersion",
    "IdentityStatus",
    "IdentitySource",
    # Fingerprint
    "FingerprintVector",
    "FingerprintResult",
    "DriftResult",
    "DriftDimension",
    "DriftSeverity",
    "DriftAlert",
    "FingerprintComparison",
    "compute_drift_severity",
    "compute_dimension_drift",
    "DRIFT_SEVERITY_THRESHOLDS",
    # Evolution
    "EvolutionProposal",
    "EvolutionTrigger",
    "EvolutionEvidence",
    "EvolutionResult",
    "EvolutionChange",
    "EvolutionProposalStatus",
    "EvolutionChangeType",
    "EvolutionTriggerType",
    "EvolutionRule",
    "EVOLUTION_RULES",
]
