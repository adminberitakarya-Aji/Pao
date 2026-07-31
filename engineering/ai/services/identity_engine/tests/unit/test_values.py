"""Unit tests for Values models."""

import pytest
from pydantic import ValidationError

from identity_engine.models.values import (
    ValuesConfig,
    ValuesTemplate,
    ValueCategory,
    ValuePriority,
    ValueDefinition,
    BUILTIN_VALUE_TEMPLATES,
)


class TestValueDefinition:
    """Test ValueDefinition model."""

    def test_valid_value_definition(self):
        val = ValueDefinition(
            category=ValueCategory.CARE,
            priority=ValuePriority.HIGH,
            weight=0.8,
            description="Helping others",
            keywords=["help", "support", "care"],
        )
        assert val.category == ValueCategory.CARE
        assert val.priority == ValuePriority.HIGH
        assert val.weight == 0.8

    def test_weight_bounds(self):
        with pytest.raises(ValidationError):
            ValueDefinition(
                category=ValueCategory.CARE,
                priority=ValuePriority.HIGH,
                weight=1.5,
            )

        with pytest.raises(ValidationError):
            ValueDefinition(
                category=ValueCategory.CARE,
                priority=ValuePriority.HIGH,
                weight=-0.1,
            )


class TestValuesConfig:
    """Test ValuesConfig model."""

    def test_valid_config(self):
        config = ValuesConfig(
            values={
                ValueCategory.CARE: ValueDefinition(
                    category=ValueCategory.CARE,
                    priority=ValuePriority.HIGH,
                    weight=0.9,
                ),
                ValueCategory.TRUTH: ValueDefinition(
                    category=ValueCategory.TRUTH,
                    priority=ValuePriority.MEDIUM,
                    weight=0.7,
                ),
            },
            version=1,
            companion_id="comp_123",
        )
        assert len(config.values) == 2
        assert config.values[ValueCategory.CARE].weight == 0.9

    def test_get_top_values(self):
        config = ValuesConfig(
            values={
                ValueCategory.CARE: ValueDefinition(
                    category=ValueCategory.CARE,
                    priority=ValuePriority.HIGH,
                    weight=0.9,
                ),
                ValueCategory.TRUTH: ValueDefinition(
                    category=ValueCategory.TRUTH,
                    priority=ValuePriority.HIGH,
                    weight=0.8,
                ),
                ValueCategory.CREATIVITY: ValueDefinition(
                    category=ValueCategory.CREATIVITY,
                    priority=ValuePriority.LOW,
                    weight=0.3,
                ),
            },
            companion_id="comp_123",
        )
        top = config.get_top_values(2)
        assert len(top) == 2
        assert top[0][0] == ValueCategory.CARE
        assert top[1][0] == ValueCategory.TRUTH

    def test_get_value_weight(self):
        config = ValuesConfig(
            values={
                ValueCategory.CARE: ValueDefinition(
                    category=ValueCategory.CARE,
                    priority=ValuePriority.HIGH,
                    weight=0.9,
                ),
            },
            companion_id="comp_123",
        )
        assert config.get_value_weight(ValueCategory.CARE) == 0.9
        assert config.get_value_weight(ValueCategory.TRUTH) == 0.0

    def test_config_defaults(self):
        config = ValuesConfig(companion_id="comp_123")
        assert config.version == 1
        assert len(config.values) == 0


class TestValuesTemplate:
    """Test ValuesTemplate model."""

    def test_builtin_templates_exist(self):
        assert "supportive" in BUILTIN_VALUE_TEMPLATES
        assert "analytical" in BUILTIN_VALUE_TEMPLATES
        assert "creative" in BUILTIN_VALUE_TEMPLATES
        assert "balanced" in BUILTIN_VALUE_TEMPLATES
        assert "principled" in BUILTIN_VALUE_TEMPLATES

    def test_template_structure(self):
        template = BUILTIN_VALUE_TEMPLATES["supportive"]
        assert template.name == "supportive"
        assert template.description is not None
        assert len(template.values) > 0
        assert all(isinstance(k, ValueCategory) for k in template.values.keys())

    def test_create_config_from_template(self):
        template = BUILTIN_VALUE_TEMPLATES["supportive"]
        config = template.create_config("comp_123")
        assert config.companion_id == "comp_123"
        assert len(config.values) == len(template.values)
        assert config.version == 1