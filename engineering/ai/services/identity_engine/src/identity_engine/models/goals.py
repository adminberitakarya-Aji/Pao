"""Goals and metrics models for Identity Engine."""

from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class GoalType(str, Enum):
    """Types of goals a companion can have."""
    USER_SATISFACTION = "user_satisfaction"
    ENGAGEMENT = "engagement"
    LEARNING = "learning"
    TASK_COMPLETION = "task_completion"
    RELATIONSHIP_BUILDING = "relationship_building"
    SKILL_DEVELOPMENT = "skill_development"
    BEHAVIORAL_CONSISTENCY = "behavioral_consistency"
    SAFETY_COMPLIANCE = "safety_compliance"
    PERSONALIZATION = "personalization"
    CREATIVE_COLLABORATION = "creative_collaboration"
    PROBLEM_SOLVING = "problem_solving"
    EMOTIONAL_SUPPORT = "emotional_support"
    KNOWLEDGE_SHARING = "knowledge_sharing"
    HABIT_FORMATION = "habit_formation"
    CUSTOM = "custom"


class GoalStatus(str, Enum):
    """Status of a goal."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"
    PENDING = "pending"


class MetricType(str, Enum):
    """Types of metrics for tracking goals."""
    QUANTITATIVE = "quantitative"      # Numeric metrics
    QUALITATIVE = "qualitative"        # Qualitative assessments
    BEHAVIORAL = "behavioral"          # Behavioral observations
    USER_FEEDBACK = "user_feedback"    # Direct user feedback
    COMPUTED = "computed"              # Computed from other metrics


class MetricAggregation(str, Enum):
    """How to aggregate metric values over time."""
    MEAN = "mean"
    MEDIAN = "median"
    SUM = "sum"
    MAX = "max"
    MIN = "min"
    LATEST = "latest"
    TREND = "trend"                    # Slope of trend line
    PERCENTILE_90 = "percentile_90"
    PERCENTILE_50 = "percentile_50"


class Metric(BaseModel):
    """A metric for tracking goal progress."""
    id: str = Field(..., description="Unique metric ID")
    name: str = Field(..., description="Metric name")
    goal_id: str = Field(..., description="Associated goal ID")
    type: MetricType = Field(..., description="Metric type")
    aggregation: MetricAggregation = Field(default=MetricAggregation.MEAN)
    
    # Target
    target_value: Optional[float] = Field(default=None, description="Target value")
    target_direction: Literal["increase", "decrease", "maintain", "target"] = Field(default="increase")
    threshold_warning: Optional[float] = Field(default=None, description="Warning threshold")
    threshold_critical: Optional[float] = Field(default=None, description="Critical threshold")
    
    # Measurement
    measurement_method: str = Field(default="", description="How this metric is measured")
    data_source: str = Field(default="", description="Source of metric data")
    frequency: Literal["realtime", "per_interaction", "daily", "weekly", "monthly"] = Field(default="per_interaction")
    
    # Current state
    current_value: Optional[float] = Field(default=None)
    previous_value: Optional[float] = Field(default=None)
    trend: Optional[float] = Field(default=None, description="Trend slope")
    last_measured: Optional[str] = Field(default=None, description="ISO timestamp")
    history: List[Dict[str, Any]] = Field(default_factory=list, description="Historical values with timestamps")
    
    # Metadata
    version: int = Field(default=1)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def is_on_track(self) -> bool:
        """Check if metric is trending toward target."""
        if self.current_value is None or self.target_value is None:
            return True  # Unknown, assume on track
        
        if self.target_direction == "increase":
            return self.current_value >= self.target_value * 0.8  # 80% of target
        elif self.target_direction == "decrease":
            return self.current_value <= self.target_value * 1.2
        elif self.target_direction == "target":
            return abs(self.current_value - self.target_value) / max(abs(self.target_value), 1) < 0.2
        return True
    
    def get_status(self) -> str:
        """Get metric status."""
        if self.current_value is None:
            return "unknown"
        if self.threshold_critical is not None:
            if self.target_direction == "increase" and self.current_value < self.threshold_critical:
                return "critical"
            if self.target_direction == "decrease" and self.current_value > self.threshold_critical:
                return "critical"
        if self.threshold_warning is not None:
            if self.target_direction == "increase" and self.current_value < self.threshold_warning:
                return "warning"
            if self.target_direction == "decrease" and self.current_value > self.threshold_warning:
                return "warning"
        if self.is_on_track():
            return "on_track"
        return "off_track"


class Goal(BaseModel):
    """A goal for companion behavior or outcomes."""
    id: str = Field(..., description="Unique goal ID")
    companion_id: str = Field(..., description="Companion identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Goal name")
    description: str = Field(default="", description="Goal description")
    type: GoalType = Field(..., description="Goal type")
    
    # Hierarchy
    parent_goal_id: Optional[str] = Field(default=None, description="Parent goal ID")
    sub_goal_ids: List[str] = Field(default_factory=list, description="Sub-goal IDs")
    
    # Success criteria
    success_criteria: List[str] = Field(default_factory=list, description="Textual success criteria")
    metrics: List[Metric] = Field(default_factory=list, description="Metrics for tracking progress")
    
    # Priority and weight
    priority: int = Field(default=5, ge=1, le=10, description="Priority (1-10)")
    weight: float = Field(default=1.0, ge=0.0, le=10.0, description="Weight in overall scoring")
    
    # Timeline
    start_date: Optional[str] = Field(default=None, description="ISO date when goal becomes active")
    target_date: Optional[str] = Field(default=None, description="Target completion date")
    review_frequency: Literal["daily", "weekly", "monthly", "quarterly"] = Field(default="weekly")
    
    # Status
    status: GoalStatus = Field(default=GoalStatus.ACTIVE)
    progress: float = Field(default=0.0, ge=0.0, le=1.0, description="Progress (0-1)")
    
    # Context
    applies_to_contexts: List[str] = Field(default_factory=list, description="Contexts where goal applies")
    applies_to_users: List[str] = Field(default_factory=list, description="User segments where goal applies")
    conditions: Dict[str, Any] = Field(default_factory=dict, description="Conditions for goal activation")
    
    # Adaptation
    auto_adjust: bool = Field(default=False, description="Automatically adjust based on progress")
    adjustment_rules: List[Dict[str, Any]] = Field(default_factory=list, description="Rules for auto-adjustment")
    
    # Metadata
    version: int = Field(default=1, ge=1)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    created_by: str = Field(default="system")
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def compute_progress(self) -> float:
        """Compute overall progress from metrics."""
        if not self.metrics:
            return self.progress
        
        on_track_count = sum(1 for m in self.metrics if m.is_on_track())
        return on_track_count / len(self.metrics)
    
    def get_overall_status(self) -> str:
        """Get overall goal status from metrics."""
        if not self.metrics:
            return self.status.value
        
        statuses = [m.get_status() for m in self.metrics]
        if "critical" in statuses:
            return "critical"
        if "warning" in statuses:
            return "warning"
        if all(s == "on_track" for s in statuses):
            return "on_track"
        if any(s == "off_track" for s in statuses):
            return "off_track"
        return "mixed"
    
    def update_progress(self):
        """Update progress based on metrics."""
        self.progress = self.compute_progress()
        if self.progress >= 1.0 and self.status == GoalStatus.ACTIVE:
            self.status = GoalStatus.COMPLETED
        elif self.progress < 1.0 and self.status == GoalStatus.COMPLETED:
            self.status = GoalStatus.ACTIVE
    
    def to_vector(self) -> list[float]:
        """Convert goal to embedding vector."""
        import numpy as np
        
        type_map = {t: i/len(GoalType) for i, t in enumerate(GoalType)}
        status_map = {s: i/len(GoalStatus) for i, s in enumerate(GoalStatus)}
        
        vector = np.zeros(20)
        
        vector[0] = type_map.get(self.type, 0)
        vector[1] = status_map.get(self.status, 0)
        vector[2] = self.priority / 10.0
        vector[3] = self.weight / 10.0
        vector[4] = self.progress
        vector[5] = len(self.metrics) / 20.0
        vector[6] = len(self.sub_goal_ids) / 10.0
        vector[7] = len(self.applies_to_contexts) / 20.0
        vector[8] = len(self.applies_to_users) / 20.0
        vector[9] = 1.0 if self.auto_adjust else 0.0
        
        # Metric statuses
        status_counts = {"on_track": 0, "off_track": 0, "warning": 0, "critical": 0, "unknown": 0}
        for m in self.metrics:
            status_counts[m.get_status()] += 1
        total = len(self.metrics) or 1
        vector[10] = status_counts["on_track"] / total
        vector[11] = status_counts["off_track"] / total
        vector[12] = status_counts["warning"] / total
        vector[13] = status_counts["critical"] / total
        
        # Time factors
        if self.target_date:
            from datetime import datetime
            try:
                target = datetime.fromisoformat(self.target_date.replace('Z', '+00:00'))
                now = datetime.utcnow()
                days_left = (target - now).days
                vector[14] = max(0, min(1, days_left / 365.0))
            except:
                pass
        
        vector[15] = len(self.conditions) / 10.0
        vector[16] = len(self.adjustment_rules) / 10.0
        
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector.tolist()


class GoalTemplate(BaseModel):
    """Template for creating goals."""
    id: str = Field(..., description="Template ID")
    name: str = Field(..., description="Template name")
    description: str = Field(default="", description="Template description")
    category: str = Field(default="general", description="Template category")
    goal_type: GoalType = Field(..., description="Goal type")
    
    # Base goal configuration
    base_goal: Goal = Field(..., description="Base goal configuration")
    
    # Customization
    required_fields: List[str] = Field(default_factory=list, description="Fields that must be customized")
    optional_fields: List[str] = Field(default_factory=list, description="Fields that can be customized")
    parameter_schema: Dict[str, Any] = Field(default_factory=dict, description="Schema for parameters")
    
    # Presets
    presets: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Named presets")
    
    # Metadata
    version: int = Field(default=1)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = Field(default=True)
    
    def create_goal(self, companion_id: str, goal_id: str, 
                    parameters: Dict[str, Any], 
                    preset: Optional[str] = None) -> Goal:
        """Create a goal from this template."""
        import copy
        goal_data = copy.deepcopy(self.base_goal.model_dump())
        goal_data.update({
            "id": goal_id,
            "companion_id": companion_id,
        })
        
        if preset and preset in self.presets:
            goal_data.update(self.presets[preset])
        
        goal_data.update(parameters)
        
        return Goal(**goal_data)


# Predefined goal templates
GOAL_TEMPLATES = {
    "user_satisfaction": GoalTemplate(
        id="user_satisfaction",
        name="User Satisfaction",
        description="Maximize user satisfaction with companion interactions",
        category="core",
        goal_type=GoalType.USER_SATISFACTION,
        base_goal=Goal(
            id="", companion_id="", name="User Satisfaction",
            type=GoalType.USER_SATISFACTION,
            priority=10,
            weight=1.0,
            metrics=[
                Metric(
                    id="satisfaction_score",
                    name="Satisfaction Score",
                    goal_id="",
                    type=MetricType.USER_FEEDBACK,
                    target_value=4.5,
                    target_direction="increase",
                    measurement_method="Post-interaction survey (1-5)",
                    data_source="user_feedback",
                    frequency="per_interaction",
                    threshold_warning=3.5,
                    threshold_critical=2.5,
                ),
                Metric(
                    id="nps",
                    name="Net Promoter Score",
                    goal_id="",
                    type=MetricType.QUANTITATIVE,
                    target_value=50,
                    target_direction="increase",
                    measurement_method="NPS survey",
                    data_source="user_feedback",
                    frequency="weekly",
                ),
                Metric(
                    id="retention_rate",
                    name="User Retention Rate",
                    goal_id="",
                    type=MetricType.QUANTITATIVE,
                    target_value=0.8,
                    target_direction="increase",
                    measurement_method="30-day retention",
                    data_source="analytics",
                    frequency="monthly",
                ),
            ],
        ),
        presets={
            "high_touch": {"priority": 10, "weight": 1.5},
            "standard": {"priority": 8, "weight": 1.0},
        },
    ),
    
    "engagement": GoalTemplate(
        id="engagement",
        name="User Engagement",
        description="Maintain high user engagement and interaction depth",
        category="core",
        goal_type=GoalType.ENGAGEMENT,
        base_goal=Goal(
            id="", companion_id="", name="User Engagement",
            type=GoalType.ENGAGEMENT,
            priority=9,
            weight=0.9,
            metrics=[
                Metric(
                    id="session_length",
                    name="Average Session Length",
                    goal_id="",
                    type=MetricType.QUANTITATIVE,
                    target_value=300,
                    target_direction="increase",
                    measurement_method="Seconds per session",
                    data_source="analytics",
                    frequency="daily",
                    threshold_warning=60,
                ),
                Metric(
                    id="interactions_per_session",
                    name="Interactions per Session",
                    goal_id="",
                    type=MetricType.QUANTITATIVE,
                    target_value=10,
                    target_direction="increase",
                    measurement_method="Message exchanges per session",
                    data_source="analytics",
                    frequency="daily",
                ),
                Metric(
                    id="return_rate",
                    name="Daily Return Rate",
                    goal_id="",
                    type=MetricType.QUANTITATIVE,
                    target_value=0.4,
                    target_direction="increase",
                    measurement_method="Users returning next day",
                    data_source="analytics",
                    frequency="daily",
                ),
            ],
        ),
    ),
    
    "learning_progress": GoalTemplate(
        id="learning_progress",
        name="Learning Progress",
        description="Track and optimize user learning outcomes",
        category="education",
        goal_type=GoalType.LEARNING,
        base_goal=Goal(
            id="", companion_id="", name="Learning Progress",
            type=GoalType.LEARNING,
            priority=8,
            weight=0.8,
            metrics=[
                Metric(
                    id="concept_mastery",
                    name="Concept Mastery Rate",
                    goal_id="",
                    type=MetricType.QUANTITATIVE,
                    target_value=0.85,
                    target_direction="increase",
                    measurement_method="Assessment scores",
                    data_source="learning_assessments",
                    frequency="per_interaction",
                ),
                Metric(
                    id="learning_velocity",
                    name="Learning Velocity",
                    goal_id="",
                    type=MetricType.QUANTITATIVE,
                    target_value=1.0,
                    target_direction="maintain",
                    measurement_method="Concepts mastered per hour",
                    data_source="learning_analytics",
                    frequency="weekly",
                ),
                Metric(
                    id="knowledge_retention",
                    name="Knowledge Retention",
                    goal_id="",
                    type=MetricType.QUANTITATIVE,
                    target_value=0.75,
                    target_direction="increase",
                    measurement_method="Retention test after 1 week",
                    data_source="learning_assessments",
                    frequency="weekly",
                ),
            ],
        ),
    ),
    
    "safety_compliance": GoalTemplate(
        id="safety_compliance",
        name="Safety Compliance",
        description="Ensure 100% compliance with safety boundaries",
        category="safety",
        goal_type=GoalType.SAFETY_COMPLIANCE,
        base_goal=Goal(
            id="", companion_id="", name="Safety Compliance",
            type=GoalType.SAFETY_COMPLIANCE,
            priority=10,
            weight=2.0,  # Double weight - safety is paramount
            metrics=[
                Metric(
                    id="boundary_violations",
                    name="Boundary Violations",
                    goal_id="",
                    type=MetricType.QUANTITATIVE,
                    target_value=0,
                    target_direction="decrease",
                    measurement_method="Count of boundary triggers",
                    data_source="boundary_logs",
                    frequency="realtime",
                    threshold_warning=1,
                    threshold_critical=5,
                ),
                Metric(
                    id="false_positive_rate",
                    name="False Positive Rate",
                    goal_id="",
                    type=MetricType.QUANTITATIVE,
                    target_value=0.05,
                    target_direction="decrease",
                    measurement_method="Incorrect boundary triggers / total",
                    data_source="boundary_logs",
                    frequency="daily",
                ),
                Metric(
                    id="escalation_rate",
                    name="Escalation Rate",
                    goal_id="",
                    type=MetricType.QUANTITATIVE,
                    target_value=0.01,
                    target_direction="decrease",
                    measurement_method="Escalations / total interactions",
                    data_source="escalation_logs",
                    frequency="daily",
                ),
            ],
        ),
    ),
    
    "behavioral_consistency": GoalTemplate(
        id="behavioral_consistency",
        name="Behavioral Consistency",
        description="Maintain consistent personality and behavior",
        category="identity",
        goal_type=GoalType.BEHAVIORAL_CONSISTENCY,
        base_goal=Goal(
            id="", companion_id="", name="Behavioral Consistency",
            type=GoalType.BEHAVIORAL_CONSISTENCY,
            priority=7,
            weight=0.7,
            metrics=[
                Metric(
                    id="personality_drift",
                    name="Personality Drift",
                    goal_id="",
                    type=MetricType.COMPUTED,
                    target_value=0.1,
                    target_direction="decrease",
                    measurement_method="Cosine distance from baseline personality vector",
                    data_source="fingerprint_analysis",
                    frequency="daily",
                ),
                Metric(
                    id="tone_consistency",
                    name="Tone Consistency",
                    goal_id="",
                    type=MetricType.COMPUTED,
                    target_value=0.85,
                    target_direction="increase",
                    measurement_method="Tone similarity across interactions",
                    data_source="voice_analysis",
                    frequency="per_interaction",
                ),
                Metric(
                    id="value_alignment",
                    name="Value Alignment",
                    goal_id="",
                    type=MetricType.COMPUTED,
                    target_value=0.9,
                    target_direction="increase",
                    measurement_method="Action-value alignment score",
                    data_source="evaluation_engine",
                    frequency="per_interaction",
                ),
            ],
        ),
    ),
}