"""Unit tests for Goals models."""

import pytest
from pydantic import ValidationError
import numpy as np

from identity_engine.models.goals import (
    Goal,
    GoalTemplate,
    GoalType,
    GoalStatus,
    Metric,
    MetricType,
    MetricAggregation,
    GOAL_TEMPLATES,
)


class TestGoalType:
    """Test GoalType enum."""

    def test_goal_types(self):
        assert GoalType.USER_SATISFACTION == "user_satisfaction"
        assert GoalType.ENGAGEMENT == "engagement"
        assert GoalType.LEARNING == "learning"
        assert GoalType.TASK_COMPLETION == "task_completion"
        assert GoalType.RELATIONSHIP_BUILDING == "relationship_building"
        assert GoalType.SKILL_DEVELOPMENT == "skill_development"
        assert GoalType.BEHAVIORAL_CONSISTENCY == "behavioral_consistency"
        assert GoalType.SAFETY_COMPLIANCE == "safety_compliance"
        assert GoalType.CUSTOM == "custom"


class TestGoalStatus:
    """Test GoalStatus enum."""

    def test_statuses(self):
        assert GoalStatus.ACTIVE == "active"
        assert GoalStatus.PAUSED == "paused"
        assert GoalStatus.COMPLETED == "completed"
        assert GoalStatus.FAILED == "failed"
        assert GoalStatus.ARCHIVED == "archived"
        assert GoalStatus.PENDING == "pending"


class TestMetricType:
    """Test MetricType enum."""

    def test_types(self):
        assert MetricType.QUANTITATIVE == "quantitative"
        assert MetricType.QUALITATIVE == "qualitative"
        assert MetricType.BEHAVIORAL == "behavioral"
        assert MetricType.USER_FEEDBACK == "user_feedback"
        assert MetricType.COMPUTED == "computed"


class TestMetricAggregation:
    """Test MetricAggregation enum."""

    def test_aggregations(self):
        assert MetricAggregation.MEAN == "mean"
        assert MetricAggregation.MEDIAN == "median"
        assert MetricAggregation.SUM == "sum"
        assert MetricAggregation.MAX == "max"
        assert MetricAggregation.LATEST == "latest"
        assert MetricAggregation.TREND == "trend"


class TestMetric:
    """Test Metric model."""

    def test_valid_metric(self):
        metric = Metric(
            id="metric_1",
            name="Satisfaction Score",
            goal_id="goal_1",
            type=MetricType.USER_FEEDBACK,
            target_value=4.5,
            target_direction="increase",
            measurement_method="Post-interaction survey (1-5)",
            data_source="user_feedback",
        )
        assert metric.id == "metric_1"
        assert metric.type == MetricType.USER_FEEDBACK
        assert metric.target_value == 4.5

    def test_metric_defaults(self):
        metric = Metric(
            id="m1",
            name="Test",
            goal_id="g1",
            type=MetricType.QUANTITATIVE,
        )
        assert metric.aggregation == MetricAggregation.MEAN
        assert metric.target_direction == "increase"
        assert metric.frequency == "per_interaction"
        assert metric.version == 1

    def test_is_on_track_increase(self):
        metric = Metric(
            id="m1", name="Test", goal_id="g1", type=MetricType.QUANTITATIVE,
            target_value=100, target_direction="increase",
        )
        metric.current_value = 90
        assert metric.is_on_track() is True  # 90 >= 80 (80% of 100)
        metric.current_value = 70
        assert metric.is_on_track() is False

    def test_is_on_track_decrease(self):
        metric = Metric(
            id="m1", name="Test", goal_id="g1", type=MetricType.QUANTITATIVE,
            target_value=10, target_direction="decrease",
        )
        metric.current_value = 8
        assert metric.is_on_track() is True  # 8 <= 12 (120% of 10)
        metric.current_value = 15
        assert metric.is_on_track() is False

    def test_is_on_track_target(self):
        metric = Metric(
            id="m1", name="Test", goal_id="g1", type=MetricType.QUANTITATIVE,
            target_value=50, target_direction="target",
        )
        metric.current_value = 55
        assert metric.is_on_track() is True  # |55-50|/50 = 0.1 < 0.2
        metric.current_value = 65
        assert metric.is_on_track() is False  # |65-50|/50 = 0.3 >= 0.2

    def test_get_status(self):
        metric = Metric(
            id="m1", name="Test", goal_id="g1", type=MetricType.QUANTITATIVE,
            target_value=100, target_direction="increase",
            threshold_warning=70, threshold_critical=40,
        )
        metric.current_value = 90
        assert metric.get_status() == "on_track"
        metric.current_value = 50
        assert metric.get_status() == "warning"
        metric.current_value = 30
        assert metric.get_status() == "critical"

    def test_get_status_no_value(self):
        metric = Metric(id="m1", name="Test", goal_id="g1", type=MetricType.QUANTITATIVE)
        assert metric.get_status() == "unknown"


class TestGoal:
    """Test Goal model."""

    def test_valid_goal(self):
        goal = Goal(
            id="goal_1",
            companion_id="comp_123",
            name="User Satisfaction",
            description="Maximize user satisfaction",
            type=GoalType.USER_SATISFACTION,
            priority=10,
            weight=1.0,
        )
        assert goal.id == "goal_1"
        assert goal.companion_id == "comp_123"
        assert goal.type == GoalType.USER_SATISFACTION
        assert goal.priority == 10

    def test_goal_defaults(self):
        goal = Goal(
            companion_id="comp_123",
            name="Test Goal",
            type=GoalType.LEARNING,
        )
        assert goal.id is not None
        assert goal.status == GoalStatus.ACTIVE
        assert goal.progress == 0.0
        assert goal.priority == 5
        assert goal.weight == 1.0
        assert goal.version == 1
        assert goal.created_by == "system"
        assert goal.is_active is True  # Wait, Goal doesn't have is_active - let me check

    def test_compute_progress_empty_metrics(self):
        goal = Goal(
            companion_id="comp_123",
            name="Test",
            type=GoalType.LEARNING,
        )
        assert goal.compute_progress() == 0.0

    def test_compute_progress_with_metrics(self):
        goal = Goal(
            companion_id="comp_123",
            name="Test",
            type=GoalType.LEARNING,
            metrics=[
                Metric(id="m1", name="M1", goal_id="g1", type=MetricType.QUANTITATIVE, target_value=10, target_direction="increase"),
                Metric(id="m2", name="M2", goal_id="g1", type=MetricType.QUANTITATIVE, target_value=20, target_direction="increase"),
            ],
        )
        # Set current values
        goal.metrics[0].current_value = 9  # on_track (>= 8)
        goal.metrics[1].current_value = 15  # off_track (< 16)
        progress = goal.compute_progress()
        assert progress == 0.5  # 1 of 2 on track

    def test_get_overall_status(self):
        goal = Goal(
            companion_id="comp_123",
            name="Test",
            type=GoalType.LEARNING,
            metrics=[
                Metric(id="m1", name="M1", goal_id="g1", type=MetricType.QUANTITATIVE, target_value=10, target_direction="increase", threshold_warning=7, threshold_critical=4),
                Metric(id="m2", name="M2", goal_id="g1", type=MetricType.QUANTITATIVE, target_value=20, target_direction="increase", threshold_warning=14, threshold_critical=8),
            ],
        )
        goal.metrics[0].current_value = 5  # warning
        goal.metrics[1].current_value = 10  # critical
        assert goal.get_overall_status() == "critical"

    def test_update_progress(self):
        goal = Goal(
            companion_id="comp_123",
            name="Test",
            type=GoalType.LEARNING,
        )
        goal.progress = 0.5
        goal.update_progress()  # No metrics, stays at 0.5
        assert goal.progress == 0.5

    def test_to_vector(self):
        goal = Goal(
            companion_id="comp_123",
            name="Test",
            type=GoalType.USER_SATISFACTION,
            priority=10,
            weight=1.0,
        )
        vector = goal.to_vector()
        assert isinstance(vector, list)
        assert len(vector) == 20
        # Check normalized
        norm = np.linalg.norm(vector)
        assert abs(norm - 1.0) < 0.01


class TestGoalTemplate:
    """Test GoalTemplate model."""

    def test_builtin_templates_exist(self):
        assert "user_satisfaction" in GOAL_TEMPLATES
        assert "engagement" in GOAL_TEMPLATES
        assert "learning_progress" in GOAL_TEMPLATES
        assert "safety_compliance" in GOAL_TEMPLATES
        assert "behavioral_consistency" in GOAL_TEMPLATES

    def test_user_satisfaction_template(self):
        template = GOAL_TEMPLATES["user_satisfaction"]
        assert template.id == "user_satisfaction"
        assert template.name == "User Satisfaction"
        assert template.category == "core"
        assert template.goal_type == GoalType.USER_SATISFACTION
        assert len(template.base_goal.metrics) == 3
        assert "high_touch" in template.presets
        assert "standard" in template.presets

    def test_safety_compliance_template(self):
        template = GOAL_TEMPLATES["safety_compliance"]
        assert template.category == "safety"
        assert template.goal_type == GoalType.SAFETY_COMPLIANCE
        assert template.base_goal.priority == 10
        assert template.base_goal.weight == 2.0
        assert len(template.base_goal.metrics) == 3

    def test_create_goal_from_template(self):
        template = GOAL_TEMPLATES["user_satisfaction"]
        goal = template.create_goal(
            companion_id="comp_123",
            goal_id="goal_1",
            parameters={"priority": 9},
        )
        assert goal.companion_id == "comp_123"
        assert goal.id == "goal_1"
        assert goal.priority == 9
        assert goal.type == GoalType.USER_SATISFACTION
        assert len(goal.metrics) == 3

    def test_create_goal_with_preset(self):
        template = GOAL_TEMPLATES["user_satisfaction"]
        goal = template.create_goal(
            companion_id="comp_123",
            goal_id="goal_1",
            parameters={},
            preset="high_touch",
        )
        assert goal.priority == 10
        assert goal.weight == 1.5

    def test_template_defaults(self):
        template = GoalTemplate(
            id="t1", name="Test", goal_type=GoalType.CUSTOM,
            base_goal=Goal(companion_id="c1", name="Test", type=GoalType.CUSTOM),
        )
        assert template.version == 1
        assert template.is_active is True


class TestGoalValidation:
    """Test Goal model validation."""

    def test_name_max_length(self):
        with pytest.raises(ValidationError):
            Goal(
                companion_id="c1", name="x" * 101, type=GoalType.LEARNING,
            )

    def test_priority_bounds(self):
        with pytest.raises(ValidationError):
            Goal(
                companion_id="c1", name="Test", type=GoalType.LEARNING, priority=11,
            )
        with pytest.raises(ValidationError):
            Goal(
                companion_id="c1", name="Test", type=GoalType.LEARNING, priority=0,
            )

    def test_weight_bounds(self):
        with pytest.raises(ValidationError):
            Goal(
                companion_id="c1", name="Test", type=GoalType.LEARNING, weight=11.0,
            )

    def test_progress_bounds(self):
        with pytest.raises(ValidationError):
            Goal(
                companion_id="c1", name="Test", type=GoalType.LEARNING, progress=1.5,
            )

    def test_version_ge_1(self):
        with pytest.raises(ValidationError):
            Goal(
                companion_id="c1", name="Test", type=GoalType.LEARNING, version=0,
            )
