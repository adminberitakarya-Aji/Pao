"""Unit tests for Validation Service."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta

from identity_engine.services.validation_service import ValidationService
from identity_engine.models import (
    IdentityConfig, PersonalityConfig, PersonalityTraits, CompanionType,
    ValuesConfig, Value, ValueCategory, ValuePriority,
    VoiceProfile, FormalityLevel, EmotionalTone, CommunicationStyle,
    Boundary, BoundaryTrigger, BoundaryAction, BoundaryScope, BoundaryTriggerType, BoundaryActionType,
    Goal, GoalType, GoalStatus, Metric, MetricType,
    EvolutionChange, EvolutionChangeType,
)


class TestValidationService:
    """Test ValidationService."""

    @pytest.fixture
    def validation_service(self):
        return ValidationService()

    @pytest.fixture
    def minimal_identity(self):
        """Create a minimal valid identity for testing."""
        personality = PersonalityConfig(
            companion_id="comp_123",
            name="Test",
            traits=PersonalityTraits(
                openness=0.5, conscientiousness=0.5, extraversion=0.5,
                agreeableness=0.5, neuroticism=0.5,
            ),
            created_at="2024-01-01T00:00:00", updated_at="2024-01-01T00:00:00",
        )
        values = ValuesConfig(
            companion_id="comp_123",
            hierarchy={},
            created_at="2024-01-01T00:00:00", updated_at="2024-01-01T00:00:00",
        )
        voice = VoiceProfile(
            companion_id="comp_123", name="Test",
            formality=FormalityLevel.NEUTRAL, primary_tone=EmotionalTone.NEUTRAL,
            communication_style=CommunicationStyle.CONVERSATIONAL,
            created_at="2024-01-01T00:00:00", updated_at="2024-01-01T00:00:00",
        )
        return IdentityConfig(
            id="id_1", companion_id="comp_123",
            personality=personality, values=values, voice=voice,
            boundaries=[], goals=[],
            name="Test Identity",
        )

    class TestValidatePersonality:
        """Test personality validation."""

        @pytest.mark.asyncio
        async def test_valid_personality(self, validation_service, minimal_identity):
            errors, warnings = await validation_service._validate_personality(minimal_identity.personality)
            assert errors == []
            assert warnings == []

        @pytest.mark.asyncio
        async def test_invalid_trait_range(self, validation_service, minimal_identity):
            minimal_identity.personality.traits.openness = 1.5
            errors, warnings = await validation_service._validate_personality(minimal_identity.personality)
            assert any("openness" in e for e in errors)

        @pytest.mark.asyncio
        async def test_negative_trait(self, validation_service, minimal_identity):
            minimal_identity.personality.traits.neuroticism = -0.1
            errors, warnings = await validation_service._validate_personality(minimal_identity.personality)
            assert any("neuroticism" in e for e in errors)

        @pytest.mark.asyncio
        async def test_high_neuroticism_agreeableness_warning(self, validation_service, minimal_identity):
            minimal_identity.personality.traits.neuroticism = 0.9
            minimal_identity.personality.traits.agreeableness = 0.9
            errors, warnings = await validation_service._validate_personality(minimal_identity.personality)
            assert any("neuroticism" in w and "agreeableness" in w for w in warnings)

        @pytest.mark.asyncio
        async def test_low_openness_high_conscientiousness_warning(self, validation_service, minimal_identity):
            minimal_identity.personality.traits.openness = 0.1
            minimal_identity.personality.traits.conscientiousness = 0.9
            errors, warnings = await validation_service._validate_personality(minimal_identity.personality)
            assert any("openness" in w and "conscientiousness" in w for w in warnings)

        @pytest.mark.asyncio
        async def test_companion_type_alignment_warning(self, validation_service, minimal_identity):
            minimal_identity.personality.companion_type = CompanionType.ASSISTANT
            minimal_identity.personality.traits.neuroticism = 0.6  # Outside expected 0.0-0.4
            minimal_identity.personality.traits.agreeableness = 0.3  # Outside expected 0.5-1.0
            errors, warnings = await validation_service._validate_personality(minimal_identity.personality)
            assert len(warnings) >= 2

    class TestValidateValues:
        """Test values validation."""

        @pytest.mark.asyncio
        async def test_empty_values_warning(self, validation_service, minimal_identity):
            errors, warnings = await validation_service._validate_values(minimal_identity.values)
            assert any("No values defined" in w for w in warnings)

        @pytest.mark.asyncio
        async def test_no_core_values_warning(self, validation_service, minimal_identity):
            minimal_identity.values.values = [
                Value(name="test", category=ValueCategory.PERSONAL_GROWTH, priority=ValuePriority.HIGH, weight=0.5)
            ]
            errors, warnings = await validation_service._validate_values(minimal_identity.values)
            assert any("No core values" in w for w in warnings)

        @pytest.mark.asyncio
        async def test_conflicting_values(self, validation_service, minimal_identity):
            minimal_identity.values.values = [
                Value(name="honesty", category=ValueCategory.ETHICAL, priority=ValuePriority.CORE, weight=0.9),
                Value(name="deception", category=ValueCategory.ETHICAL, priority=ValuePriority.HIGH, weight=0.5),
            ]
            errors, warnings = await validation_service._validate_values(minimal_identity.values)
            assert any("Conflicting values" in e for e in errors)

        @pytest.mark.asyncio
        async def test_too_many_critical_values_warning(self, validation_service, minimal_identity):
            minimal_identity.values.values = [
                Value(name=f"value_{i}", category=ValueCategory.ETHICAL, priority=ValuePriority.CORE, weight=0.9)
                for i in range(6)
            ]
            errors, warnings = await validation_service._validate_values(minimal_identity.values)
            assert any("More than 5 critical" in w for w in warnings)

    class TestValidateVoice:
        """Test voice profile validation."""

        @pytest.mark.asyncio
        async def test_missing_id_error(self, validation_service, minimal_identity):
            minimal_identity.voice.id = ""
            errors, warnings = await validation_service._validate_voice(minimal_identity.voice)
            assert any("missing ID" in e for e in errors)

        @pytest.mark.asyncio
        async def test_missing_companion_id_error(self, validation_service, minimal_identity):
            minimal_identity.voice.companion_id = ""
            errors, warnings = await validation_service._validate_voice(minimal_identity.voice)
            assert any("missing companion_id" in e for e in errors)

        @pytest.mark.asyncio
        async def test_humor_without_style_warning(self, validation_service, minimal_identity):
            minimal_identity.voice.uses_humor = True
            minimal_identity.voice.humor_style = None
            errors, warnings = await validation_service._validate_voice(minimal_identity.voice)
            assert any("humor" in w.lower() for w in warnings)

        @pytest.mark.asyncio
        async def test_formal_with_contractions_warning(self, validation_service, minimal_identity):
            minimal_identity.voice.formality = FormalityLevel.FORMAL
            minimal_identity.voice.uses_contractions = True
            errors, warnings = await validation_service._validate_voice(minimal_identity.voice)
            assert any("formal" in w.lower() and "contraction" in w.lower() for w in warnings)

        @pytest.mark.asyncio
        async def test_concise_with_step_by_step_warning(self, validation_service, minimal_identity):
            minimal_identity.voice.verbosity = "concise"
            minimal_identity.voice.gives_step_by_step = True
            errors, warnings = await validation_service._validate_voice(minimal_identity.voice)
            assert any("concise" in w.lower() and "step" in w.lower() for w in warnings)

        @pytest.mark.asyncio
        async def test_max_less_than_min_error(self, validation_service, minimal_identity):
            minimal_identity.voice.max_response_length = 50
            minimal_identity.voice.min_response_length = 100
            errors, warnings = await validation_service._validate_voice(minimal_identity.voice)
            assert any("max_response_length must be >=" in e for e in errors)

    class TestValidateBoundaries:
        """Test boundaries validation."""

        @pytest.mark.asyncio
        async def test_no_boundaries_warning(self, validation_service, minimal_identity):
            errors, warnings = await validation_service._validate_boundaries([])
            assert any("No boundaries defined" in w for w in warnings)

        @pytest.mark.asyncio
        async def test_duplicate_boundary_ids_error(self, validation_service, minimal_identity):
            boundary = Boundary(
                companion_id="comp_123", name="Test", scope=BoundaryScope.GLOBAL,
                triggers=[], actions=[], is_active=True,
            )
            boundaries = [boundary, boundary]  # Same ID
            errors, warnings = await validation_service._validate_boundaries(boundaries)
            assert any("Duplicate boundary IDs" in e for e in errors)

        @pytest.mark.asyncio
        async def test_boundary_without_triggers_error(self, validation_service, minimal_identity):
            boundary = Boundary(
                companion_id="comp_123", name="Test", scope=BoundaryScope.GLOBAL,
                triggers=[], actions=[BoundaryAction(id="a1", type=BoundaryActionType.REFUSE, name="Refuse", is_active=True)],
                is_active=True,
            )
            errors, warnings = await validation_service._validate_boundaries([boundary])
            assert any("has no triggers" in e for e in errors)

        @pytest.mark.asyncio
        async def test_boundary_without_actions_error(self, validation_service, minimal_identity):
            boundary = Boundary(
                companion_id="comp_123", name="Test", scope=BoundaryScope.GLOBAL,
                triggers=[BoundaryTrigger(id="t1", type=BoundaryTriggerType.KEYWORD, name="Test", is_active=True)],
                actions=[], is_active=True,
            )
            errors, warnings = await validation_service._validate_boundaries([boundary])
            assert any("has no actions" in e for e in errors)

        @pytest.mark.asyncio
        async def test_pattern_trigger_missing_pattern_error(self, validation_service, minimal_identity):
            trigger = BoundaryTrigger(id="t1", type=BoundaryTriggerType.PATTERN, name="Test", is_active=True)
            boundary = Boundary(
                companion_id="comp_123", name="Test", scope=BoundaryScope.GLOBAL,
                triggers=[trigger], actions=[BoundaryAction(id="a1", type=BoundaryActionType.REFUSE, name="Refuse", is_active=True)],
                is_active=True,
            )
            errors, warnings = await validation_service._validate_boundaries([boundary])
            assert any("missing pattern" in e for e in errors)

        @pytest.mark.asyncio
        async def test_keyword_trigger_missing_keywords_error(self, validation_service, minimal_identity):
            trigger = BoundaryTrigger(id="t1", type=BoundaryTriggerType.KEYWORD, name="Test", is_active=True)
            boundary = Boundary(
                companion_id="comp_123", name="Test", scope=BoundaryScope.GLOBAL,
                triggers=[trigger], actions=[BoundaryAction(id="a1", type=BoundaryActionType.REFUSE, name="Refuse", is_active=True)],
                is_active=True,
            )
            errors, warnings = await validation_service._validate_boundaries([boundary])
            assert any("missing keywords" in e for e in errors)

        @pytest.mark.asyncio
        async def test_semantic_trigger_missing_threshold_error(self, validation_service, minimal_identity):
            trigger = BoundaryTrigger(id="t1", type=BoundaryTriggerType.SEMANTIC, name="Test", is_active=True)
            boundary = Boundary(
                companion_id="comp_123", name="Test", scope=BoundaryScope.GLOBAL,
                triggers=[trigger], actions=[BoundaryAction(id="a1", type=BoundaryActionType.REFUSE, name="Refuse", is_active=True)],
                is_active=True,
            )
            errors, warnings = await validation_service._validate_boundaries([boundary])
            assert any("missing threshold" in e for e in errors)

        @pytest.mark.asyncio
        async def test_refuse_without_message_warning(self, validation_service, minimal_identity):
            action = BoundaryAction(id="a1", type=BoundaryActionType.REFUSE, name="Refuse", is_active=True)
            boundary = Boundary(
                companion_id="comp_123", name="Test", scope=BoundaryScope.GLOBAL,
                triggers=[BoundaryTrigger(id="t1", type=BoundaryTriggerType.KEYWORD, name="Test", is_active=True, keywords=["test"])],
                actions=[action], is_active=True,
            )
            errors, warnings = await validation_service._validate_boundaries([boundary])
            assert any("refusal message" in w for w in warnings)

        @pytest.mark.asyncio
        async def test_many_global_boundaries_warning(self, validation_service, minimal_identity):
            boundaries = []
            for i in range(11):
                boundaries.append(Boundary(
                    companion_id="comp_123", name=f"Test {i}", scope=BoundaryScope.GLOBAL,
                    triggers=[BoundaryTrigger(id=f"t{i}", type=BoundaryTriggerType.KEYWORD, name="Test", is_active=True, keywords=["test"])],
                    actions=[BoundaryAction(id=f"a{i}", type=BoundaryActionType.REFUSE, name="Refuse", is_active=True, refusal_message="No")],
                    is_active=True,
                ))
            errors, warnings = await validation_service._validate_boundaries(boundaries)
            assert any("Many global boundaries" in w for w in warnings)

        @pytest.mark.asyncio
        async def test_narrow_priority_range_warning(self, validation_service, minimal_identity):
            boundaries = []
            for i, p in enumerate([50, 52, 55, 53]):
                boundaries.append(Boundary(
                    companion_id="comp_123", name=f"Test {i}", scope=BoundaryScope.GLOBAL, priority=p,
                    triggers=[BoundaryTrigger(id=f"t{i}", type=BoundaryTriggerType.KEYWORD, name="Test", is_active=True, keywords=["test"])],
                    actions=[BoundaryAction(id=f"a{i}", type=BoundaryActionType.REFUSE, name="Refuse", is_active=True, refusal_message="No")],
                    is_active=True,
                ))
            errors, warnings = await validation_service._validate_boundaries(boundaries)
            assert any("Narrow priority range" in w for w in warnings)

    class TestValidateGoals:
        """Test goals validation."""

        @pytest.mark.asyncio
        async def test_no_goals_warning(self, validation_service, minimal_identity):
            errors, warnings = await validation_service._validate_goals([])
            assert any("No goals defined" in w for w in warnings)

        @pytest.mark.asyncio
        async def test_duplicate_goal_ids_error(self, validation_service, minimal_identity):
            goal = Goal(companion_id="comp_123", name="Test", type=GoalType.LEARNING)
            goals = [goal, goal]
            errors, warnings = await validation_service._validate_goals(goals)
            assert any("Duplicate goal IDs" in e for e in errors)

        @pytest.mark.asyncio
        async def test_goal_without_metrics_warning(self, validation_service, minimal_identity):
            goal = Goal(companion_id="comp_123", name="Test", type=GoalType.LEARNING, metrics=[])
            errors, warnings = await validation_service._validate_goals([goal])
            assert any("has no metrics" in w for w in warnings)

        @pytest.mark.asyncio
        async def test_metric_no_target_warning(self, validation_service, minimal_identity):
            metric = Metric(id="m1", name="Test", goal_id="g1", type=MetricType.QUANTITATIVE, target_direction="increase")
            goal = Goal(companion_id="comp_123", name="Test", type=GoalType.LEARNING, metrics=[metric])
            errors, warnings = await validation_service._validate_goals([goal])
            assert any("no target value" in w for w in warnings)

        @pytest.mark.asyncio
        async def test_target_direction_target_requires_value_error(self, validation_service, minimal_identity):
            metric = Metric(id="m1", name="Test", goal_id="g1", type=MetricType.QUANTITATIVE, target_direction="target")
            goal = Goal(companion_id="comp_123", name="Test", type=GoalType.LEARNING, metrics=[metric])
            errors, warnings = await validation_service._validate_goals([goal])
            assert any("requires target value" in e for e in errors)

        @pytest.mark.asyncio
        async def test_goal_target_date_in_past_warning(self, validation_service, minimal_identity):
            past_date = (datetime.utcnow() - timedelta(days=1)).isoformat()
            goal = Goal(companion_id="comp_123", name="Test", type=GoalType.LEARNING, target_date=past_date)
            errors, warnings = await validation_service._validate_goals([goal])
            assert any("target date is in the past" in w for w in warnings)

        @pytest.mark.asyncio
        async def test_goal_invalid_date_format_error(self, validation_service, minimal_identity):
            goal = Goal(companion_id="comp_123", name="Test", type=GoalType.LEARNING, target_date="invalid-date")
            errors, warnings = await validation_service._validate_goals([goal])
            assert any("invalid target_date format" in e for e in errors)

        @pytest.mark.asyncio
        async def test_goal_hierarchy_cycle_error(self, validation_service, minimal_identity):
            goal1 = Goal(id="g1", companion_id="comp_123", name="G1", type=GoalType.LEARNING, parent_goal_id="g2")
            goal2 = Goal(id="g2", companion_id="comp_123", name="G2", type=GoalType.LEARNING, parent_goal_id="g1")
            errors, warnings = await validation_service._validate_goals([goal1, goal2])
            assert any("Circular goal hierarchy" in e for e in errors)

        @pytest.mark.asyncio
        async def test_high_total_weight_warning(self, validation_service, minimal_identity):
            goals = []
            for i in range(5):
                goals.append(Goal(id=f"g{i}", companion_id="comp_123", name=f"G{i}", type=GoalType.LEARNING, weight=5.0))
            errors, warnings = await validation_service._validate_goals(goals)
            assert any("Total goal weight" in w for w in warnings)

    class TestValidateCrossComponent:
        """Test cross-component validation."""

        @pytest.mark.asyncio
        async def test_high_agreeableness_no_caring_values_warning(self, validation_service, minimal_identity):
            minimal_identity.personality.traits.agreeableness = 0.8
            minimal_identity.values.values = [
                Value(name="honesty", category=ValueCategory.ETHICAL, priority=ValuePriority.CORE, weight=0.9)
            ]
            errors, warnings = await validation_service._validate_cross_component(minimal_identity)
            assert any("caring" in w.lower() or "compassion" in w.lower() for w in warnings)

        @pytest.mark.asyncio
        async def test_high_openness_no_growth_values_warning(self, validation_service, minimal_identity):
            minimal_identity.personality.traits.openness = 0.8
            minimal_identity.values.values = [
                Value(name="honesty", category=ValueCategory.ETHICAL, priority=ValuePriority.CORE, weight=0.9)
            ]
            errors, warnings = await validation_service._validate_cross_component(minimal_identity)
            assert any("growth" in w.lower() or "learning" in w.lower() for w in warnings)

        @pytest.mark.asyncio
        async def test_high_extraversion_formal_voice_warning(self, validation_service, minimal_identity):
            minimal_identity.personality.traits.extraversion = 0.8
            minimal_identity.voice.formality = FormalityLevel.FORMAL
            errors, warnings = await validation_service._validate_cross_component(minimal_identity)
            assert any("extraversion" in w.lower() and "formal" in w.lower() for w in warnings)

        @pytest.mark.asyncio
        async def test_high_playfulness_no_humor_warning(self, validation_service, minimal_identity):
            minimal_identity.personality.traits.playfulness = 0.8
            minimal_identity.voice.uses_humor = False
            errors, warnings = await validation_service._validate_cross_component(minimal_identity)
            assert any("playfulness" in w.lower() and "humor" in w.lower() for w in warnings)

        @pytest.mark.asyncio
        async def test_creative_goal_with_restrictive_boundaries_warning(self, validation_service, minimal_identity):
            goal = Goal(companion_id="comp_123", name="Creative", type=GoalType.CREATIVE_COLLABORATION)
            minimal_identity.goals = [goal]
            
            boundary = Boundary(
                companion_id="comp_123", name="Strict", scope=BoundaryScope.GLOBAL, priority=90,
                triggers=[BoundaryTrigger(id="t1", type=BoundaryTriggerType.KEYWORD, name="Test", is_active=True, keywords=["bad"])],
                actions=[BoundaryAction(id="a1", type=BoundaryActionType.REFUSE, name="Refuse", is_active=True, refusal_message="No")],
                is_active=True,
            )
            minimal_identity.boundaries = [boundary]
            
            errors, warnings = await validation_service._validate_cross_component(minimal_identity)
            assert any("creative" in w.lower() and "boundar" in w.lower() for w in warnings)

        @pytest.mark.asyncio
        async def test_safety_goal_without_safety_boundaries_warning(self, validation_service, minimal_identity):
            goal = Goal(companion_id="comp_123", name="Safety", type=GoalType.SAFETY_COMPLIANCE)
            minimal_identity.goals = [goal]
            minimal_identity.boundaries = []
            
            errors, warnings = await validation_service._validate_cross_component(minimal_identity)
            assert any("safety" in w.lower() and "boundar" in w.lower() for w in warnings)

    class TestValidateUniqueness:
        """Test uniqueness validation."""

        @pytest.mark.asyncio
        async def test_duplicate_boundary_ids_error(self, validation_service, minimal_identity):
            boundary = Boundary(companion_id="comp_123", name="Test", scope=BoundaryScope.GLOBAL,
                                triggers=[], actions=[], is_active=True)
            minimal_identity.boundaries = [boundary, boundary]
            errors, warnings = await validation_service._validate_uniqueness(minimal_identity)
            assert any("Duplicate boundary IDs" in e for e in errors)

        @pytest.mark.asyncio
        async def test_duplicate_goal_ids_error(self, validation_service, minimal_identity):
            goal = Goal(companion_id="comp_123", name="Test", type=GoalType.LEARNING)
            minimal_identity.goals = [goal, goal]
            errors, warnings = await validation_service._validate_uniqueness(minimal_identity)
            assert any("Duplicate goal IDs" in e for e in errors)

    class TestValidateChanges:
        """Test change validation."""

        @pytest.mark.asyncio
        async def test_personality_change_invalid_trait(self, validation_service):
            change = EvolutionChange(
                id="ch1", type=EvolutionChangeType.PERSONALITY_ADJUSTMENT,
                target_field="traits", proposed_value={"openness": 1.5},
            )
            errors = await validation_service._validate_personality_change(change)
            assert any("Invalid trait value" in e for e in errors)

        @pytest.mark.asyncio
        async def test_voice_change_invalid_field(self, validation_service):
            change = EvolutionChange(
                id="ch1", type=EvolutionChangeType.VOICE_MODIFICATION,
                target_field="invalid_field",
            )
            errors = await validation_service._validate_voice_change(change)
            assert any("Invalid voice field" in e for e in errors)

        @pytest.mark.asyncio
        async def test_values_change_not_list_error(self, validation_service):
            change = EvolutionChange(
                id="ch1", type=EvolutionChangeType.VALUES_UPDATE,
                target_field="values", proposed_value="not a list",
            )
            errors = await validation_service._validate_values_change(change)
            assert any("must be a list" in e for e in errors)

        @pytest.mark.asyncio
        async def test_values_change_missing_name_error(self, validation_service):
            change = EvolutionChange(
                id="ch1", type=EvolutionChangeType.VALUES_UPDATE,
                target_field="values", proposed_value=[{"weight": 0.5}],
            )
            errors = await validation_service._validate_values_change(change)
            assert any("missing required 'name'" in e for e in errors)

        @pytest.mark.asyncio
        async def test_boundary_removal_with_references_error(self, validation_service):
            mock_repo = AsyncMock()
            mock_repo.get_boundary_references.return_value = ["goal_1", "goal_2"]
            validation_service.repository = mock_repo

            change = EvolutionChange(
                id="ch1", type=EvolutionChangeType.BOUNDARY_REMOVAL,
                target_id="boundary_1",
            )
            errors = await validation_service._validate_boundary_change(change)
            assert any("is referenced by" in e for e in errors)

        @pytest.mark.asyncio
        async def test_goal_removal_with_references_error(self, validation_service):
            mock_repo = AsyncMock()
            mock_repo.get_goal_references.return_value = ["evolution_1"]
            validation_service.repository = mock_repo

            change = EvolutionChange(
                id="ch1", type=EvolutionChangeType.GOAL_REMOVAL,
                target_id="goal_1",
            )
            errors = await validation_service._validate_goal_change(change)
            assert any("is referenced by" in e for e in errors)