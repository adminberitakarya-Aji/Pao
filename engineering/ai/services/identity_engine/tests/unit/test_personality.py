"""Unit tests for Personality models."""

import pytest
from pydantic import ValidationError
import numpy as np

from identity_engine.models.personality import (
    PersonalityConfig,
    PersonalityTraits,
    TraitExpression,
    CompanionType,
)


class TestCompanionType:
    """Test CompanionType enum."""

    def test_companion_types(self):
        assert CompanionType.SUPPORTIVE == "supportive"
        assert CompanionType.INTELLECTUAL == "intellectual"
        assert CompanionType.PLAYFUL == "playful"
        assert CompanionType.PROFESSIONAL == "professional"
        assert CompanionType.CREATIVE == "creative"
        assert CompanionType.ANALYTICAL == "analytical"
        assert CompanionType.EMPATHETIC == "empathetic"
        assert CompanionType.ADVENTUROUS == "adventurous"
        assert CompanionType.CUSTOM == "custom"


class TestTraitExpression:
    """Test TraitExpression model."""

    def test_valid_expression(self):
        expr = TraitExpression(
            dimension="openness",
            level=0.7,
            confidence=0.8,
            behavioral_markers=["asks questions", "explores ideas"],
            linguistic_patterns=["what if", "imagine"],
        )
        assert expr.dimension == "openness"
        assert expr.level == 0.7
        assert len(expr.behavioral_markers) == 2

    def test_expression_defaults(self):
        expr = TraitExpression(dimension="test", level=0.5)
        assert expr.confidence == 0.8
        assert expr.behavioral_markers == []
        assert expr.linguistic_patterns == []
        assert expr.metadata == {}

    def test_bounds_validation(self):
        with pytest.raises(ValidationError):
            TraitExpression(dimension="test", level=1.5)

        with pytest.raises(ValidationError):
            TraitExpression(dimension="test", level=-0.1)


class TestPersonalityTraits:
    """Test PersonalityTraits model (Big Five + extended)."""

    def test_valid_traits(self):
        traits = PersonalityTraits(
            openness=0.7,
            conscientiousness=0.6,
            extraversion=0.5,
            agreeableness=0.8,
            neuroticism=0.3,
            curiosity=0.8,
            warmth=0.6,
            assertiveness=0.4,
            playfulness=0.5,
            depth=0.7,
            adaptability=0.6,
        )
        assert traits.openness == 0.7
        assert traits.neuroticism == 0.3
        assert traits.curiosity == 0.8

    def test_bounds_validation(self):
        with pytest.raises(ValidationError):
            PersonalityTraits(
                openness=1.5,
                conscientiousness=0.5,
                extraversion=0.5,
                agreeableness=0.5,
                neuroticism=0.5,
            )

        with pytest.raises(ValidationError):
            PersonalityTraits(
                openness=-0.1,
                conscientiousness=0.5,
                extraversion=0.5,
                agreeableness=0.5,
                neuroticism=0.5,
            )

    def test_to_vector(self):
        traits = PersonalityTraits(
            openness=0.7,
            conscientiousness=0.6,
            extraversion=0.5,
            agreeableness=0.8,
            neuroticism=0.3,
            curiosity=0.8,
            warmth=0.6,
            assertiveness=0.4,
            playfulness=0.5,
            depth=0.7,
            adaptability=0.6,
        )
        vector = traits.to_vector()
        assert len(vector) == 11  # 5 Big Five + 6 extended
        assert vector[0] == 0.7  # openness
        assert vector[4] == 0.7  # 1 - neuroticism (inverted)

    def test_from_vector(self):
        vector = [0.7, 0.6, 0.5, 0.8, 0.3, 0.8, 0.6, 0.4, 0.5, 0.7, 0.6]
        traits = PersonalityTraits.from_vector(vector)
        assert traits.openness == 0.7
        assert traits.conscientiousness == 0.6
        assert traits.extraversion == 0.5
        assert traits.agreeableness == 0.8
        assert traits.neuroticism == 0.7  # 1 - 0.3
        assert traits.curiosity == 0.8
        assert traits.adaptability == 0.6

    def test_from_vector_with_custom(self):
        vector = [0.7, 0.6, 0.5, 0.8, 0.3, 0.8, 0.6, 0.4, 0.5, 0.7, 0.6, 0.9, 0.2]
        traits = PersonalityTraits.from_vector(vector, custom_dim_names=["custom1", "custom2"])
        assert traits.custom_dimensions["custom1"] == 0.9
        assert traits.custom_dimensions["custom2"] == 0.2


class TestPersonalityConfig:
    """Test PersonalityConfig model."""

    def test_valid_config(self):
        config = PersonalityConfig(
            id="pers_1",
            companion_id="comp_123",
            companion_type=CompanionType.SUPPORTIVE,
            name="Supportive Personality",
            description="Warm and helpful",
            traits=PersonalityTraits(
                openness=0.7,
                conscientiousness=0.6,
                extraversion=0.5,
                agreeableness=0.8,
                neuroticism=0.3,
            ),
            expressions=[
                TraitExpression(dimension="openness", level=0.7, behavioral_markers=["asks questions"]),
            ],
            version=1,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        assert config.id == "pers_1"
        assert config.companion_type == CompanionType.SUPPORTIVE
        assert len(config.expressions) == 1

    def test_config_defaults(self):
        config = PersonalityConfig(
            companion_id="comp_123",
            name="Test",
            traits=PersonalityTraits(
                openness=0.5, conscientiousness=0.5, extraversion=0.5,
                agreeableness=0.5, neuroticism=0.5,
            ),
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        assert config.companion_type == CompanionType.CUSTOM
        assert config.version == 1
        assert config.is_active is True
        assert config.is_validated is False

    def test_get_dominant_traits(self):
        config = PersonalityConfig(
            companion_id="comp_123",
            name="Test",
            traits=PersonalityTraits(
                openness=0.9,
                conscientiousness=0.3,
                extraversion=0.7,
                agreeableness=0.5,
                neuroticism=0.2,
                curiosity=0.8,
                warmth=0.4,
                assertiveness=0.6,
                playfulness=0.5,
                depth=0.7,
                adaptability=0.5,
            ),
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        dominant = config.get_dominant_traits(3)
        assert len(dominant) == 3
        assert dominant[0][0] == "openness"
        assert dominant[0][1] == 0.9

    def test_similarity_to(self):
        config1 = PersonalityConfig(
            companion_id="comp_123",
            name="Test1",
            traits=PersonalityTraits(
                openness=1.0, conscientiousness=0.0, extraversion=0.0,
                agreeableness=0.0, neuroticism=0.0,
            ),
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        config2 = PersonalityConfig(
            companion_id="comp_123",
            name="Test2",
            traits=PersonalityTraits(
                openness=0.0, conscientiousness=1.0, extraversion=0.0,
                agreeableness=0.0, neuroticism=0.0,
            ),
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        # Orthogonal vectors should have 0 similarity
        sim = config1.similarity_to(config2)
        assert sim == 0.0

        # Same vectors should have 1.0 similarity
        sim = config1.similarity_to(config1)
        assert sim == 1.0


class TestPersonalityValidation:
    """Test Personality model validation."""

    def test_traits_bounds(self):
        with pytest.raises(ValidationError):
            PersonalityTraits(
                openness=0.5, conscientiousness=0.5, extraversion=0.5,
                agreeableness=0.5, neuroticism=1.5,
            )

    def test_extended_traits_bounds(self):
        with pytest.raises(ValidationError):
            PersonalityTraits(
                openness=0.5, conscientiousness=0.5, extraversion=0.5,
                agreeableness=0.5, neuroticism=0.5,
                curiosity=1.5,
            )

    def test_version_ge_1(self):
        with pytest.raises(ValidationError):
            PersonalityConfig(
                companion_id="c1", name="Test",
                traits=PersonalityTraits(openness=0.5, conscientiousness=0.5,
                    extraversion=0.5, agreeableness=0.5, neuroticism=0.5),
                created_at="2024-01-01", updated_at="2024-01-01",
                version=0,
            )

    def test_name_length(self):
        with pytest.raises(ValidationError):
            PersonalityConfig(
                companion_id="c1", name="",
                traits=PersonalityTraits(openness=0.5, conscientiousness=0.5,
                    extraversion=0.5, agreeableness=0.5, neuroticism=0.5),
                created_at="2024-01-01", updated_at="2024-01-01",
            )

        with pytest.raises(ValidationError):
            PersonalityConfig(
                companion_id="c1", name="x" * 101,
                traits=PersonalityTraits(openness=0.5, conscientiousness=0.5,
                    extraversion=0.5, agreeableness=0.5, neuroticism=0.5),
                created_at="2024-01-01", updated_at="2024-01-01",
            )
