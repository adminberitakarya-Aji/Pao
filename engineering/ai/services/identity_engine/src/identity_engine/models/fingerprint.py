"""Fingerprint and drift detection models for Identity Engine."""

from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class DriftSeverity(str, Enum):
    """Severity levels for identity drift."""
    NONE = "none"              # No significant drift
    MINOR = "minor"            # Small drift, monitoring recommended
    MODERATE = "moderate"      # Noticeable drift, review recommended
    SIGNIFICANT = "significant" # Significant drift, action recommended
    CRITICAL = "critical"      # Critical drift, immediate action required


class DriftDimension(str, Enum):
    """Dimensions of identity that can drift."""
    PERSONALITY = "personality"
    VALUES = "values"
    VOICE = "voice"
    BEHAVIOR = "behavior"
    BOUNDARIES = "boundaries"
    GOALS = "goals"
    KNOWLEDGE = "knowledge"
    RELATIONSHIP = "relationship"


class FingerprintVector(BaseModel):
    """Vector representation of identity fingerprint."""
    id: str = Field(..., description="Fingerprint ID")
    companion_id: str = Field(..., description="Companion identifier")
    identity_version: int = Field(..., description="Identity version this fingerprint represents")
    
    # Component vectors
    personality_vector: List[float] = Field(..., description="Personality trait vector")
    values_vector: List[float] = Field(..., description="Values configuration vector")
    voice_vector: List[float] = Field(..., description="Voice profile vector")
    goals_vector: List[float] = Field(..., description="Goals configuration vector")
    boundaries_vector: List[float] = Field(..., description="Boundaries configuration vector")
    
    # Combined fingerprint
    combined_vector: List[float] = Field(..., description="Full combined fingerprint vector")
    
    # Metadata
    vector_dimension: int = Field(..., description="Dimension of combined vector")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def cosine_similarity(self, other: "FingerprintVector") -> float:
        """Compute cosine similarity with another fingerprint."""
        import numpy as np
        v1 = np.array(self.combined_vector)
        v2 = np.array(other.combined_vector)
        if len(v1) != len(v2):
            min_len = min(len(v1), len(v2))
            v1, v2 = v1[:min_len], v2[:min_len]
        dot = np.dot(v1, v2)
        norm = np.linalg.norm(v1) * np.linalg.norm(v2)
        return float(dot / norm) if norm > 0 else 0.0
    
    def euclidean_distance(self, other: "FingerprintVector") -> float:
        """Compute Euclidean distance to another fingerprint."""
        import numpy as np
        v1 = np.array(self.combined_vector)
        v2 = np.array(other.combined_vector)
        if len(v1) != len(v2):
            min_len = min(len(v1), len(v2))
            v1, v2 = v1[:min_len], v2[:min_len]
        return float(np.linalg.norm(v1 - v2))
    
    def component_similarities(self, other: "FingerprintVector") -> Dict[str, float]:
        """Compute similarity per component."""
        import numpy as np
        
        components = {
            "personality": (self.personality_vector, other.personality_vector),
            "values": (self.values_vector, other.values_vector),
            "voice": (self.voice_vector, other.voice_vector),
            "goals": (self.goals_vector, other.goals_vector),
            "boundaries": (self.boundaries_vector, other.boundaries_vector),
        }
        
        similarities = {}
        for name, (v1, v2) in components.items():
            v1_arr = np.array(v1)
            v2_arr = np.array(v2)
            if len(v1_arr) != len(v2_arr):
                min_len = min(len(v1_arr), len(v2_arr))
                v1_arr, v2_arr = v1_arr[:min_len], v2_arr[:min_len]
            dot = np.dot(v1_arr, v2_arr)
            norm = np.linalg.norm(v1_arr) * np.linalg.norm(v2_arr)
            similarities[name] = float(dot / norm) if norm > 0 else 0.0
        
        return similarities


class FingerprintResult(BaseModel):
    """Result of fingerprint computation."""
    fingerprint: FingerprintVector
    computation_time_ms: float
    source_data: Dict[str, Any] = Field(default_factory=dict, description="Source data used for computation")
    quality_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Quality of fingerprint computation")
    warnings: List[str] = Field(default_factory=list)


class DriftResult(BaseModel):
    """Result of drift detection analysis."""
    id: str = Field(..., description="Drift analysis ID")
    companion_id: str = Field(..., description="Companion identifier")
    baseline_fingerprint_id: str = Field(..., description="Baseline fingerprint ID")
    current_fingerprint_id: str = Field(..., description="Current fingerprint ID")
    
    # Overall drift
    overall_drift_score: float = Field(..., ge=0.0, le=1.0, description="Overall drift (0-1)")
    severity: DriftSeverity = Field(..., description="Drift severity level")
    
    # Per-dimension drift
    dimension_drifts: Dict[DriftDimension, float] = Field(
        default_factory=dict, description="Drift score per dimension (0-1)"
    )
    dimension_severities: Dict[DriftDimension, DriftSeverity] = Field(
        default_factory=dict, description="Severity per dimension"
    )
    
    # Component similarities
    component_similarities: Dict[str, float] = Field(default_factory=dict)
    
    # Significant changes detected
    significant_changes: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of significant changes detected"
    )
    
    # Recommendations
    recommended_actions: List[str] = Field(default_factory=list)
    requires_review: bool = Field(default=False)
    requires_reevaluation: bool = Field(default=False)
    requires_rollback: bool = Field(default=False)
    
    # Metadata
    analyzed_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    analysis_window_days: int = Field(default=7, description="Analysis window in days")
    interaction_count: int = Field(default=0, description="Number of interactions analyzed")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def get_top_drifted_dimensions(self, top_k: int = 3) -> List[tuple[DriftDimension, float]]:
        """Get top-k most drifted dimensions."""
        sorted_dims = sorted(self.dimension_drifts.items(), key=lambda x: x[1], reverse=True)
        return sorted_dims[:top_k]
    
    def is_critical(self) -> bool:
        """Check if drift is critical."""
        return self.severity == DriftSeverity.CRITICAL or self.requires_rollback


class DriftAlert(BaseModel):
    """Alert for detected drift."""
    id: str = Field(..., description="Alert ID")
    companion_id: str = Field(..., description="Companion identifier")
    drift_result_id: str = Field(..., description="Associated drift result ID")
    
    # Alert details
    severity: DriftSeverity
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")
    dimensions_affected: List[DriftDimension] = Field(default_factory=list)
    
    # Status
    status: Literal["active", "acknowledged", "resolved", "dismissed"] = Field(default="active")
    acknowledged_by: Optional[str] = Field(default=None)
    acknowledged_at: Optional[str] = Field(default=None)
    resolved_by: Optional[str] = Field(default=None)
    resolved_at: Optional[str] = Field(default=None)
    resolution_notes: Optional[str] = Field(default=None)
    
    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FingerprintComparison(BaseModel):
    """Comparison between two fingerprints."""
    baseline_id: str
    current_id: str
    companion_id: str
    
    # Similarities
    overall_similarity: float
    component_similarities: Dict[str, float]
    
    # Differences
    drifted_dimensions: List[DriftDimension]
    significant_changes: List[Dict[str, Any]]
    
    # Interpretation
    drift_narrative: str = Field(default="", description="Human-readable drift explanation")
    risk_assessment: Literal["low", "medium", "high", "critical"] = Field(default="low")
    recommended_actions: List[str] = Field(default_factory=list)
    
    # Metadata
    compared_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Drift severity thresholds
DRIFT_SEVERITY_THRESHOLDS = {
    DriftSeverity.NONE: (0.0, 0.05),
    DriftSeverity.MINOR: (0.05, 0.15),
    DriftSeverity.MODERATE: (0.15, 0.30),
    DriftSeverity.SIGNIFICANT: (0.30, 0.50),
    DriftSeverity.CRITICAL: (0.50, 1.0),
}


def compute_drift_severity(drift_score: float) -> DriftSeverity:
    """Compute drift severity from drift score."""
    for severity, (low, high) in DRIFT_SEVERITY_THRESHOLDS.items():
        if low <= drift_score < high:
            return severity
    return DriftSeverity.CRITICAL


def compute_dimension_drift(baseline_vec: List[float], current_vec: List[float]) -> float:
    """Compute drift score for a single dimension."""
    import numpy as np
    v1 = np.array(baseline_vec)
    v2 = np.array(current_vec)
    if len(v1) != len(v2):
        min_len = min(len(v1), len(v2))
        v1, v2 = v1[:min_len], v2[:min_len]
    # Drift = 1 - cosine_similarity
    dot = np.dot(v1, v2)
    norm = np.linalg.norm(v1) * np.linalg.norm(v2)
    similarity = float(dot / norm) if norm > 0 else 0.0
    return 1.0 - similarity