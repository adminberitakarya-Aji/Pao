"""Unit tests for Boundaries models."""

import pytest
from pydantic import ValidationError

from identity_engine.models.boundaries import (
    Boundary,
    BoundaryTrigger,
    BoundaryAction,
    BoundaryScope,
    BoundaryTriggerType,
    BoundaryActionType,
    BOUNDARY_TEMPLATES,
)


class TestBoundaryTrigger:
    """Test BoundaryTrigger model."""

    def test_valid_trigger(self):
        trigger = BoundaryTrigger(
            id="trigger_1",
            type=BoundaryTriggerType.KEYWORD,
            name="PII Request Detection",
            keywords=["ssn", "credit card", "passport"],
        )
        assert trigger.id == "trigger_1"
        assert trigger.type == BoundaryTriggerType.KEYWORD
        assert "ssn" in trigger.keywords

    def test_trigger_defaults(self):
        trigger = BoundaryTrigger(
            type=BoundaryTriggerType.PATTERN,
            name="Pattern Trigger",
            pattern=r"\d{3}-\d{2}-\d{4}",
        )
        assert trigger.id is not None
        assert trigger.is_active is True
        assert trigger.priority == 0
        assert trigger.metadata == {}

    def test_trigger_matches(self):
        trigger = BoundaryTrigger(
            type=BoundaryTriggerType.KEYWORD,
            name="Test",
            keywords=["test", "example"],
        )
        # matches method is a placeholder returning False
        assert trigger.matches({"text": "test"}) is False


class TestBoundaryAction:
    """Test BoundaryAction model."""

    def test_valid_action(self):
        action = BoundaryAction(
            id="action_1",
            type=BoundaryActionType.REFUSE,
            name="Refuse PII",
            refusal_message="I can't share personal information.",
        )
        assert action.id == "action_1"
        assert action.type == BoundaryActionType.REFUSE
        assert action.refusal_message == "I can't share personal information."

    def test_action_defaults(self):
        action = BoundaryAction(
            type=BoundaryActionType.LOG,
            name="Log Attempt",
        )
        assert action.id is not None
        assert action.is_active is True
        assert action.log_level == "warning"
        assert action.metadata == {}


class TestBoundary:
    """Test Boundary model."""

    def test_valid_boundary(self):
        boundary = Boundary(
            id="boundary_1",
            companion_id="comp_123",
            name="PII Protection",
            description="Prevents sharing PII",
            scope=BoundaryScope.GLOBAL,
            triggers=[
                BoundaryTrigger(
                    id="pii_trigger",
                    type=BoundaryTriggerType.PATTERN,
                    name="PII Pattern",
                    pattern=r"\d{3}-\d{2}-\d{4}",
                ),
            ],
            actions=[
                BoundaryAction(
                    id="refuse_action",
                    type=BoundaryActionType.REFUSE,
                    name="Refuse",
                    refusal_message="I can't help with that.",
                ),
            ],
            priority=100,
            tags=["safety", "privacy"],
        )
        assert boundary.id == "boundary_1"
        assert boundary.companion_id == "comp_123"
        assert boundary.scope == BoundaryScope.GLOBAL
        assert len(boundary.triggers) == 1
        assert len(boundary.actions) == 1
        assert boundary.priority == 100

    def test_boundary_defaults(self):
        boundary = Boundary(
            companion_id="comp_123",
            name="Test Boundary",
        )
        assert boundary.id is not None
        assert boundary.scope == BoundaryScope.GLOBAL
        assert boundary.trigger_logic == "any"
        assert boundary.action_sequence == "sequential"
        assert boundary.priority == 0
        assert boundary.version == 1
        assert boundary.is_active is True
        assert boundary.is_validated is False

    def test_get_active_triggers(self):
        boundary = Boundary(
            companion_id="comp_123",
            name="Test",
            triggers=[
                BoundaryTrigger(id="t1", type=BoundaryTriggerType.KEYWORD, name="Active", is_active=True),
                BoundaryTrigger(id="t2", type=BoundaryTriggerType.KEYWORD, name="Inactive", is_active=False),
            ],
            actions=[],
        )
        active = boundary.get_active_triggers()
        assert len(active) == 1
        assert active[0].id == "t1"

    def test_get_active_actions(self):
        boundary = Boundary(
            companion_id="comp_123",
            name="Test",
            triggers=[],
            actions=[
                BoundaryAction(id="a1", type=BoundaryActionType.REFUSE, name="Active", is_active=True),
                BoundaryAction(id="a2", type=BoundaryActionType.LOG, name="Inactive", is_active=False),
            ],
        )
        active = boundary.get_active_actions()
        assert len(active) == 1
        assert active[0].id == "a1"

    def test_evaluate_no_triggers(self):
        boundary = Boundary(
            companion_id="comp_123",
            name="Test",
            triggers=[],
            actions=[
                BoundaryAction(id="a1", type=BoundaryActionType.REFUSE, name="Action"),
            ],
        )
        result = boundary.evaluate({"text": "hello"})
        assert result == []

    def test_evaluate_any_logic(self):
        boundary = Boundary(
            companion_id="comp_123",
            name="Test",
            trigger_logic="any",
            triggers=[
                BoundaryTrigger(id="t1", type=BoundaryTriggerType.KEYWORD, name="Active", is_active=True),
            ],
            actions=[
                BoundaryAction(id="a1", type=BoundaryActionType.REFUSE, name="Action", is_active=True),
            ],
        )
        # matches() returns False, so no actions
        result = boundary.evaluate({"text": "hello"})
        assert result == []


class TestBoundaryTemplates:
    """Test predefined boundary templates."""

    def test_builtin_templates_exist(self):
        assert "safety_pii" in BOUNDARY_TEMPLATES
        assert "safety_medical" in BOUNDARY_TEMPLATES
        assert "safety_legal" in BOUNDARY_TEMPLATES
        assert "safety_financial" in BOUNDARY_TEMPLATES
        assert "safety_harmful_content" in BOUNDARY_TEMPLATES
        assert "capability_code_execution" in BOUNDARY_TEMPLATES
        assert "behavioral_tone" in BOUNDARY_TEMPLATES
        assert "privacy_data_retention" in BOUNDARY_TEMPLATES

    def test_safety_pii_template(self):
        template = BOUNDARY_TEMPLATES["safety_pii"]
        assert template.id == "safety_pii"
        assert template.name == "PII Protection"
        assert template.scope == BoundaryScope.GLOBAL
        assert len(template.triggers) == 2
        assert len(template.actions) == 2
        assert template.priority == 100
        assert "safety" in template.tags
        assert "privacy" in template.tags

    def test_safety_medical_template(self):
        template = BOUNDARY_TEMPLATES["safety_medical"]
        assert template.scope == BoundaryScope.TOPIC
        assert "medical" in template.topic_ids
        assert template.priority == 95

    def test_safety_harmful_content_template(self):
        template = BOUNDARY_TEMPLATES["safety_harmful_content"]
        assert template.priority == 100
        assert len(template.triggers) == 4
        assert len(template.actions) == 3
        assert any(a.type == BoundaryActionType.ESCALATE for a in template.actions)
        assert any(a.type == BoundaryActionType.LOG for a in template.actions)


class TestBoundaryValidation:
    """Test Boundary model validation."""

    def test_empty_name_validation(self):
        with pytest.raises(ValidationError):
            Boundary(companion_id="comp_123", name="")

    def test_name_max_length(self):
        with pytest.raises(ValidationError):
            Boundary(companion_id="comp_123", name="x" * 101)

    def test_version_ge_1(self):
        with pytest.raises(ValidationError):
            Boundary(companion_id="comp_123", name="Test", version=0)

    def test_priority_validation(self):
        # Should accept any int
        boundary = Boundary(companion_id="comp_123", name="Test", priority=-10)
        assert boundary.priority == -10

    def test_trigger_priority(self):
        trigger = BoundaryTrigger(
            type=BoundaryTriggerType.KEYWORD,
            name="Test",
            priority=5,
        )
        assert trigger.priority == 5
