"""Unit tests for Identity models."""

import pytest
from pydantic import ValidationError
from datetime import datetime
import numpy as np

from identity_engine.models.identity import (
    IdentityConfig,
    IdentityRequest,
    IdentityResponse,
    IdentityVersion,
    IdentityStatus,
    IdentitySource,
)
from identity_engine.models.personality import PersonalityConfig, PersonalityTraits, CompanionType
from identity_engine.models.values import ValuesConfig, Value, ValueCategory, ValuePriority
from identity_engine.models.voice import VoiceProfile, FormalityLevel, EmotionalTone, CommunicationStyle
from identity_engine.models.boundaries import Boundary, BoundaryTrigger, BoundaryAction, BoundaryScope, BoundaryTriggerType, BoundaryActionType
from identity_engine.models.goals import Goal, GoalType, GoalStatus, Metric, MetricType


class TestIdentityStatus:
    """Test IdentityStatus enum."""

    def test_statuses(self):
        assert IdentityStatus.DRAFT == "draft"
        assert IdentityStatus.VALIDATING == "validating"
        assert IdentityStatus.ACTIVE == "active"
        assert IdentityStatus.DEPRECATED == "deprecated"
        assert IdentityStatus.ARCHIVED == "archived"


class TestIdentitySource:
    """Test IdentitySource enum."""

    def test_sources(self):
        assert IdentitySource.TEMPLATE == "template"
        assert IdentitySource.USER_CREATED == "user_created"
        assert IdentitySource.AI_GENERATED == "ai_generated"
        assert IdentitySource.IMPORTED == "imported"
        assert IdentitySource.EVOLVED == "evolved"
        assert IdentitySource.MERGED == "merged"


class TestIdentityRequest:
    """Test IdentityRequest model."""

    def test_valid_request(self):
        request = IdentityRequest(
            companion_id="comp_123",
            name="Test Companion",
            description="A test companion",
            source=IdentitySource.USER_CREATED,
        )
        assert request.companion_id == "comp_123"
        assert request.name == "Test Companion"
        assert request.source == IdentitySource.USER_CREATED

    def test_minimal_request(self):
        request = IdentityRequest(
            companion_id="comp_123",
            name="Test",
        )
        assert request.companion_id == "comp_123"
        assert request.name == "Test"
        assert request.personality is None
        assert request.personality_id is None
        assert request.skip_validation is False
        assert request.auto_activate is False

    def test_name_max_length(self):
        with pytest.raises(ValidationError):
            IdentityRequest(companion_id="c1", name="x" * 101)

    def test_name_min_length(self):
        with pytest.raises(ValidationError):
            IdentityRequest(companion_id="c1", name="")


class TestIdentityResponse:
    """Test IdentityResponse model."""

    def test_response_creation(self):
        personality = PersonalityConfig(
            companion_id="comp_123",
            name="Test",
            traits=PersonalityTraits(
                openness=0.5, conscientiousness=0.5, extraversion=0.5,
                agreeableness=0.5, neuroticism=0.5,
            ),
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        values = ValuesConfig(
            companion_id="comp_123",
            hierarchy={},
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        voice = VoiceProfile(
            companion_id="comp_123",
            name="Test",
            formality=FormalityLevel.NEUTRAL,
            primary_tone=EmotionalTone.NEUTRAL,
            communication_style=CommunicationStyle.CONVERSATIONAL,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        response = IdentityResponse(
            id="identity_1",
            companion_id="comp_123",
            version=1,
            personality=personality,
            values=values,
            voice=voice,
            boundaries=[],
            goals=[],
            status=IdentityStatus.ACTIVE,
            source=IdentitySource.USER_CREATED,
            is_valid=True,
            name="Test",
            description="",
            tags=[],
            metadata={},
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            created_by="system",
        )
        assert response.id == "identity_1"
        assert response.companion_id == "comp_123"
        assert response.status == IdentityStatus.ACTIVE


class TestIdentityVersion:
    """Test IdentityVersion model."""

    def test_valid_version(self):
        personality = PersonalityConfig(
            companion_id="comp_123",
            name="Test",
            traits=PersonalityTraits(openness=0.5, conscientiousness=0.5, extraversion=0.5, agreeableness=0.5, neuroticism=0.5),
            created_at="2024-01-01T00:00:00", updated_at="2024-01-01T00:00:00",
        )
        values = ValuesConfig(companion_id="comp_123", hierarchy={}, created_at="2024-01-01T00:00:00", updated_at="2024-01-01T00:00:00")
        voice = VoiceProfile(companion_id="comp_123", name="Test", formality=FormalityLevel.NEUTRAL, primary_tone=EmotionalTone.NEUTRAL, communication_style=CommunicationStyle.CONVERSATIONAL, created_at="2024-01-01T00:00:00", updated_at="2024-01-01T00:00:00")
        
        version = IdentityVersion(
            id="ver_1",
            identity_id="id_1",
            version=1,
            personality=personality,
            values=values,
            voice=voice,
            boundaries=[],
            goals=[],
            change_type="create",
            change_summary="Initial version",
            changed_by="user_1",
        )
        assert version.id == "ver_1"
        assert version.version == 1
        assert version.change_type == "create"

    def test_compute_diff(self):
        personality = PersonalityConfig(
            companion_id="comp_123", name="Test",
            traits=PersonalityTraits(openness=0.5, conscientiousness=0.5, extraversion=0.5, agreeableness=0.5, neuroticism=0.5),
            created_at="2024-01-01T00:00:00", updated_at="2024-01-01T00:00:00",
        )
        values = ValuesConfig(companion_id="comp_123", hierarchy={}, created_at="2024-01-01T00:00:00", updated_at="2024-01-01T00:00:00")
        voice = VoiceProfile(companion_id="comp_123", name="Test", formality=FormalityLevel.NEUTRAL, primary_tone=EmotionalTone.NEUTRAL, communication_style=CommunicationStyle.CONVERSATIONAL, created_at="2024-01-01T00:00:00", updated_at="2024-01-01T00:00:00")
        
        v1 = IdentityVersion(
            id="ver_1", identity_id="id_1", version=1,
            personality=personality, values=values, voice=voice,
            boundaries=[], goals=[],
        )
        v2 = IdentityVersion(
            id="ver_2", identity_id="id_1", version=2,
            personality=personality, values=values, voice=voice,
            boundaries=[], goals=[],
        )
        diff = v1.compute_diff(v2)
        assert diff["version_from"] == 1
        assert diff["version_to"] == 2
        assert "changed_fields" in diff


class TestIdentityConfig:
    """Test IdentityConfig model."""

    def create_minimal_components(self):
        """Helper to create minimal valid components."""
        personality = PersonalityConfig(
            companion_id="comp_123",
            name="Test Personality",
            traits=PersonalityTraits(
                openness=0.5, conscientiousness=0.5, extraversion=0.5,
                agreeableness=0.5, neuroticism=0.5,
            ),
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        values = ValuesConfig(
            companion_id="comp_123",
            hierarchy={},
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        voice = VoiceProfile(
            companion_id="comp_123",
            name="Test Voice",
            formality=FormalityLevel.NEUTRAL,
            primary_tone=EmotionalTone.NEUTRAL,
            communication_style=CommunicationStyle.CONVERSATIONAL,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        return personality, values, voice

    def test_valid_identity(self):
        personality, values, voice = self.create_minimal_components()
        identity = IdentityConfig(
            id="identity_1",
            companion_id="comp_123",
            personality=personality,
            values=values,
            voice=voice,
            boundaries=[],
            goals=[],
            version=1,
            name="Test Companion",
            status=IdentityStatus.ACTIVE,
            source=IdentitySource.USER_CREATED,
        )
        assert identity.id == "identity_1"
        assert identity.companion_id == "comp_123"
        assert identity.version == 1
        assert identity.status == IdentityStatus.ACTIVE

    def test_identity_defaults(self):
        personality, values, voice = self.create_minimal_components()
        identity = IdentityConfig(
            companion_id="comp_123",
            personality=personality,
            values=values,
            voice=voice,
            boundaries=[],
            goals=[],
        )
        assert identity.version == 1
        assert identity.status == IdentityStatus.DRAFT
        assert identity.source == IdentitySource.USER_CREATED
        assert identity.is_valid is False
        assert identity.tags == []

    def test_create_version(self):
        personality, values, voice = self.create_minimal_components()
        identity = IdentityConfig(
            companion_id="comp_123",
            personality=personality,
            values=values,
            voice=voice,
            boundaries=[],
            goals=[],
            id="id_1",
        )
        version = identity.create_version("update", "Updated personality", ["personality"], "user_1")
        assert version.identity_id == "id_1"
        assert version.version == 1
        assert version.change_type == "update"
        assert version.change_summary == "Updated personality"

    def test_validate_consistency(self):
        personality, values, voice = self.create_minimal_components()
        # Add high agreeableness
        personality.traits.agreeableness = 0.8
        # Add caring value
        values.values.append(Value(
            name="care", category=ValueCategory.CARE, priority=ValuePriority.HIGH, weight=0.9
        ))
        
        identity = IdentityConfig(
            companion_id="comp_123",
            personality=personality,
            values=values,
            voice=voice,
            boundaries=[],
            goals=[],
        )
        is_valid, errors, warnings = identity.validate_consistency()
        assert is_valid is True
        # Should have warning about high agreeableness with caring values
        # Actually it should NOT warn since we have caring value now

    def test_to_vector(self):
        personality, values, voice = self.create_minimal_components()
        identity = IdentityConfig(
            companion_id="comp_123",
            personality=personality,
            values=values,
            voice=voice,
            boundaries=[],
            goals=[],
        )
        vector = identity.to_vector()
        assert isinstance(vector, list)
        # Personality (11) + Values (30) + Voice (30) + Goals (20) + Boundaries (10) = 101
        assert len(vector) == 101
        # Check normalized
        norm = np.linalg.norm(vector)
        assert abs(norm - 1.0) < 0.01

    def test_get_active_boundaries(self):
        from identity_engine.models.boundaries import BoundaryTrigger, BoundaryAction
        
        personality, values, voice = self.create_minimal_components()
        boundary = Boundary(
            companion_id="comp_123",
            name="Test Boundary",
            scope=BoundaryScope.GLOBAL,
            triggers=[
                BoundaryTrigger(id="t1", type=BoundaryTriggerType.KEYWORD, name="Test", is_active=True)
            ],
            actions=[
                BoundaryAction(id="a1", type=BoundaryActionType.REFUSE, name="Refuse", is_active=True)
            ],
            is_active=True,
        )
        identity = IdentityConfig(
            companion_id="comp_123",
            personality=personality,
            values=values,
            voice=voice,
            boundaries=[boundary],
            goals=[],
        )
        active = identity.get_active_boundaries()
        assert len(active) == 1
        assert active[0].id == boundary.id

    def test_get_active_goals(self):
        from identity_engine.models.goals import Metric, MetricType
        
        personality, values, voice = self.create_minimal_components()
        goal = Goal(
            companion_id="comp_123",
            name="Test Goal",
            type=GoalType.LEARNING,
            status=GoalStatus.ACTIVE,
            metrics=[Metric(id="m1", name="Test", goal_id="g1", type=MetricType.QUANTITATIVE)],
        )
        identity = IdentityConfig(
            companion_id="comp_123",
            personality=personality,
            values=values,
            voice=voice,
            boundaries=[],
            goals=[goal],
        )
        active = identity.get_active_goals()
        assert len(active) == 1
        assert active[0].id == goal.id


class TestIdentityConfigValidation:
    """Test IdentityConfig validation."""

    def test_name_max_length(self):
        personality, values, voice = TestIdentityConfig().create_minimal_components()
        with pytest.raises(ValidationError):
            IdentityConfig(
                companion_id="c1", name="x" * 101,
                personality=personality, values=values, voice=voice,
            )

    def test_version_ge_1(self):
        personality, values, voice = TestIdentityConfig().create_minimal_components()
        with pytest.raises(ValidationError):
            IdentityConfig(
                companion_id="c1", name="Test",
                personality=personality, values=values, voice=voice,
                version=0,
            )
