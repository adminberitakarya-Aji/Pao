"""Unit tests for Voice models."""

import pytest
from pydantic import ValidationError
import numpy as np

from identity_engine.models.voice import (
    VoiceProfile,
    VoiceProfileTemplate,
    VoiceCharacteristic,
    FormalityLevel,
    VerbosityLevel,
    EmotionalTone,
    CommunicationStyle,
    VOICE_TEMPLATES,
)


class TestVoiceEnums:
    """Test Voice enum values."""

    def test_formality_levels(self):
        assert FormalityLevel.VERY_FORMAL == "very_formal"
        assert FormalityLevel.FORMAL == "formal"
        assert FormalityLevel.NEUTRAL == "neutral"
        assert FormalityLevel.CASUAL == "casual"
        assert FormalityLevel.VERY_CASUAL == "very_casual"

    def test_verbosity_levels(self):
        assert VerbosityLevel.CONCISE == "concise"
        assert VerbosityLevel.MODERATE == "moderate"
        assert VerbosityLevel.DETAILED == "detailed"
        assert VerbosityLevel.COMPREHENSIVE == "comprehensive"

    def test_emotional_tones(self):
        assert EmotionalTone.WARM == "warm"
        assert EmotionalTone.NEUTRAL == "neutral"
        assert EmotionalTone.PROFESSIONAL == "professional"
        assert EmotionalTone.EMPATHETIC == "empathetic"
        assert EmotionalTone.SUPPORTIVE == "supportive"

    def test_communication_styles(self):
        assert CommunicationStyle.DIRECT == "direct"
        assert CommunicationStyle.COLLABORATIVE == "collaborative"
        assert CommunicationStyle.CONVERSATIONAL == "conversational"
        assert CommunicationStyle.INSTRUCTIONAL == "instructional"


class TestVoiceCharacteristic:
    """Test VoiceCharacteristic model."""

    def test_valid_characteristic(self):
        char = VoiceCharacteristic(
            name="empathetic",
            weight=1.2,
            description="Shows empathy",
            examples=["I understand", "That sounds difficult"],
            anti_examples=["Whatever", "Not my problem"],
        )
        assert char.name == "empathetic"
        assert char.weight == 1.2
        assert len(char.examples) == 2

    def test_characteristic_defaults(self):
        char = VoiceCharacteristic(name="test")
        assert char.weight == 1.0
        assert char.description == ""
        assert char.examples == []
        assert char.anti_examples == []

    def test_weight_bounds(self):
        with pytest.raises(ValidationError):
            VoiceCharacteristic(name="test", weight=2.5)

        with pytest.raises(ValidationError):
            VoiceCharacteristic(name="test", weight=-0.1)


class TestVoiceProfile:
    """Test VoiceProfile model."""

    def test_valid_profile(self):
        profile = VoiceProfile(
            id="voice_1",
            companion_id="comp_123",
            name="Supportive Voice",
            formality=FormalityLevel.CASUAL,
            verbosity=VerbosityLevel.MODERATE,
            primary_tone=EmotionalTone.WARM,
            secondary_tones=[EmotionalTone.EMPATHETIC, EmotionalTone.SUPPORTIVE],
            communication_style=CommunicationStyle.COLLABORATIVE,
            uses_contractions=True,
            uses_humor=False,
            uses_analogies=True,
            asks_questions=True,
            question_frequency="moderate",
            provides_examples=True,
            acknowledges_user=True,
            validates_feelings=True,
            adapts_to_user=True,
            mirrors_tone=True,
            mirrors_formality=True,
            avoid_topics=["medical_advice", "legal_advice"],
        )
        assert profile.id == "voice_1"
        assert profile.companion_id == "comp_123"
        assert profile.formality == FormalityLevel.CASUAL
        assert profile.primary_tone == EmotionalTone.WARM
        assert len(profile.secondary_tones) == 2

    def test_defaults(self):
        profile = VoiceProfile(
            id="voice_1",
            companion_id="comp_123",
            name="Default Voice",
        )
        assert profile.formality == FormalityLevel.NEUTRAL
        assert profile.verbosity == VerbosityLevel.MODERATE
        assert profile.primary_tone == EmotionalTone.NEUTRAL
        assert profile.communication_style == CommunicationStyle.CONVERSATIONAL
        assert profile.uses_contractions is True
        assert profile.uses_humor is False
        assert profile.uses_analogies is True
        assert profile.asks_questions is True
        assert profile.question_frequency == "moderate"
        assert profile.provides_examples is True
        assert profile.acknowledges_user is True
        assert profile.adapts_to_user is True
        assert profile.adaptation_speed == "moderate"
        assert profile.mirrors_formality is True
        assert profile.mirrors_tone is True
        assert profile.version == 1
        assert profile.is_active is True

    def test_to_prompt_instructions(self):
        profile = VoiceProfile(
            id="voice_1",
            companion_id="comp_123",
            name="Test",
            formality=FormalityLevel.CASUAL,
            verbosity=VerbosityLevel.MODERATE,
            primary_tone=EmotionalTone.WARM,
            communication_style=CommunicationStyle.CONVERSATIONAL,
            uses_contractions=True,
            uses_analogies=True,
            asks_questions=True,
            acknowledges_user=True,
        )
        instructions = profile.to_prompt_instructions()
        assert "Communication Style: conversational" in instructions
        assert "Formality: casual" in instructions
        assert "Primary Tone: warm" in instructions
        assert "use contractions naturally" in instructions
        assert "use analogies to explain complex ideas" in instructions
        assert "ask questions (moderate frequency)" in instructions

    def test_to_vector(self):
        profile = VoiceProfile(
            id="voice_1",
            companion_id="comp_123",
            name="Test",
            formality=FormalityLevel.NEUTRAL,
            verbosity=VerbosityLevel.MODERATE,
            primary_tone=EmotionalTone.NEUTRAL,
            communication_style=CommunicationStyle.CONVERSATIONAL,
        )
        vector = profile.to_vector()
        assert isinstance(vector, list)
        assert len(vector) == 30
        # Check it's normalized
        norm = np.linalg.norm(vector)
        assert abs(norm - 1.0) < 0.01

    def test_validation_bounds(self):
        with pytest.raises(ValidationError):
            VoiceProfile(
                id="v1", companion_id="c1", name="Test",
                max_response_length=0,
            )

        with pytest.raises(ValidationError):
            VoiceProfile(
                id="v1", companion_id="c1", name="Test",
                min_response_length=-1,
            )


class TestVoiceProfileTemplate:
    """Test VoiceProfileTemplate model."""

    def test_builtin_templates_exist(self):
        assert "supportive_companion" in VOICE_TEMPLATES
        assert "professional_assistant" in VOICE_TEMPLATES
        assert "creative_partner" in VOICE_TEMPLATES
        assert "learning_companion" in VOICE_TEMPLATES

    def test_supportive_companion_template(self):
        template = VOICE_TEMPLATES["supportive_companion"]
        assert template.id == "supportive_companion"
        assert template.name == "Supportive Companion"
        assert template.category == "companion"
        assert template.base_profile.primary_tone == EmotionalTone.WARM
        assert EmotionalTone.EMPATHETIC in template.base_profile.secondary_tones
        assert template.base_profile.validates_feelings is True
        assert "formality" in template.customizable_fields
        assert "therapeutic" in template.presets
        assert "coaching" in template.presets

    def test_professional_assistant_template(self):
        template = VOICE_TEMPLATES["professional_assistant"]
        assert template.base_profile.formality == FormalityLevel.FORMAL
        assert template.base_profile.verbosity == VerbosityLevel.CONCISE
        assert template.base_profile.communication_style == CommunicationStyle.DIRECT
        assert template.base_profile.uses_contractions is False
        assert "executive" in template.presets
        assert "collaborative" in template.presets

    def test_creative_partner_template(self):
        template = VOICE_TEMPLATES["creative_partner"]
        assert template.base_profile.primary_tone == EmotionalTone.PLAYFUL
        assert template.base_profile.uses_humor is True
        assert template.base_profile.humor_style == "witty"
        assert len(template.base_profile.characteristics) == 2
        assert template.base_profile.characteristics[0].name == "imaginative"

    def test_learning_companion_template(self):
        template = VOICE_TEMPLATES["learning_companion"]
        assert template.base_profile.communication_style == CommunicationStyle.INSTRUCTIONAL
        assert template.base_profile.gives_step_by_step is True
        assert template.base_profile.summarizes_frequently is True
        assert "beginner" in template.presets
        assert "advanced" in template.presets

    def test_create_profile_from_template(self):
        template = VOICE_TEMPLATES["supportive_companion"]
        profile = template.create_profile(
            companion_id="comp_123",
            profile_id="voice_1",
            customizations={"formality": FormalityLevel.NEUTRAL},
        )
        assert profile.companion_id == "comp_123"
        assert profile.id == "voice_1"
        assert profile.formality == FormalityLevel.NEUTRAL
        assert profile.primary_tone == EmotionalTone.WARM

    def test_create_profile_with_preset(self):
        template = VOICE_TEMPLATES["professional_assistant"]
        profile = template.create_profile(
            companion_id="comp_123",
            profile_id="voice_1",
            customizations={},
            preset="executive",
        )
        assert profile.formality == FormalityLevel.VERY_FORMAL
        assert profile.communication_style == CommunicationStyle.AUTHORITATIVE


class TestVoiceProfileValidation:
    """Test VoiceProfile validation."""

    def test_question_frequency_validation(self):
        with pytest.raises(ValidationError):
            VoiceProfile(
                id="v1", companion_id="c1", name="Test",
                question_frequency="invalid",
            )

    def test_sentence_structure_validation(self):
        with pytest.raises(ValidationError):
            VoiceProfile(
                id="v1", companion_id="c1", name="Test",
                sentence_structure="invalid",
            )

    def test_vocabulary_level_validation(self):
        with pytest.raises(ValidationError):
            VoiceProfile(
                id="v1", companion_id="c1", name="Test",
                vocabulary_level="invalid",
            )

    def test_adaptation_speed_validation(self):
        with pytest.raises(ValidationError):
            VoiceProfile(
                id="v1", companion_id="c1", name="Test",
                adaptation_speed="invalid",
            )
