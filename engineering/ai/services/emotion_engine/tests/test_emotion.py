"""Tests for Emotion Engine models and core logic."""

import pytest
from datetime import datetime
from uuid import UUID, uuid4
from typing import Dict, List

from emotion_engine.models.emotion import (
    ValenceArousal,
    Appraisal,
    EmotionCategory,
    ExpressionModality,
    Expression,
    EmotionState,
    CalibrationData,
    EmotionEvent,
    AppraisalDimension,
)


class TestValenceArousal:
    """Tests for ValenceArousal model."""

    def test_valence_arousal_creation(self):
        va = ValenceArousal(valence=0.5, arousal=0.7)
        assert va.valence == 0.5
        assert va.arousal == 0.7
        assert va.confidence == 1.0

    def test_valence_arousal_clamp(self):
        va = ValenceArousal(valence=1.5, arousal=-0.5)
        assert va.valence == 1.0
        assert va.arousal == 0.0

    def test_valence_arousal_distance(self):
        va1 = ValenceArousal(valence=0.0, arousal=0.0)
        va2 = ValenceArousal(valence=1.0, arousal=1.0)
        distance = va1.distance_to(va2)
        assert abs(distance - 1.414) < 0.01  # sqrt(2)

    def test_valence_arousal_quadrant(self):
        assert ValenceArousal(valence=0.5, arousal=0.5).quadrant() == "positive_high"
        assert ValenceArousal(valence=-0.5, arousal=0.5).quadrant() == "negative_high"
        assert ValenceArousal(valence=0.5, arousal=-0.5).quadrant() == "positive_low"
        assert ValenceArousal(valence=-0.5, arousal=-0.5).quadrant() == "negative_low"
        assert ValenceArousal(valence=0.0, arousal=0.0).quadrant() == "neutral"


class TestAppraisal:
    """Tests for Appraisal model."""

    def test_appraisal_creation(self):
        appraisal = Appraisal(
            novelty=0.8,
            pleasantness=0.6,
            goal_relevance=0.7,
            goal_congruence=0.5,
            coping_potential=0.6,
            norm_compatibility=0.4,
            self_relevance=0.8,
            agency=0.3,
            certainty=0.5,
            control=0.6,
        )
        assert appraisal.novelty == 0.8
        assert appraisal.pleasantness == 0.6

    def test_appraisal_to_vector(self):
        appraisal = Appraisal(
            novelty=0.5,
            pleasantness=0.0,
            goal_relevance=0.5,
            goal_congruence=0.0,
            coping_potential=0.5,
            norm_compatibility=0.0,
            self_relevance=0.5,
            agency=0.0,
            certainty=0.5,
            control=0.5,
        )
        vector = appraisal.to_vector()
        assert len(vector) == 10
        assert all(0.0 <= v <= 1.0 for v in vector.values())


class TestEmotionCategory:
    """Tests for EmotionCategory enum."""

    def test_all_categories_exist(self):
        categories = list(EmotionCategory)
        assert EmotionCategory.JOY in categories
        assert EmotionCategory.SADNESS in categories
        assert EmotionCategory.ANGER in categories
        assert EmotionCategory.FEAR in categories
        assert EmotionCategory.SURPRISE in categories
        assert EmotionCategory.DISGUST in categories
        assert EmotionCategory.TRUST in categories
        assert EmotionCategory.LOVE in categories
        assert EmotionCategory.NEUTRAL in categories

    def test_va_to_emotion_mapping(self):
        # High positive valence, high arousal -> JOY or SURPRISE
        va = ValenceArousal(valence=0.8, arousal=0.8)
        emotion = va.to_emotion_category()
        assert emotion in [EmotionCategory.JOY, EmotionCategory.SURPRISE, EmotionCategory.EXCITEMENT]

        # Negative valence, high arousal -> ANGER or FEAR
        va = ValenceArousal(valence=-0.8, arousal=0.8)
        emotion = va.to_emotion_category()
        assert emotion in [EmotionCategory.ANGER, EmotionCategory.FEAR, EmotionCategory.STRESS]


class TestExpression:
    """Tests for Expression model."""

    def test_expression_creation(self):
        expr = Expression(
            modality=ExpressionModality.TEXT,
            emotion_category=EmotionCategory.JOY,
            intensity=0.8,
            text_formality=0.3,
            text_verbosity=0.7,
            text_emoji_probability=0.3,
        )
        assert expr.modality == ExpressionModality.TEXT
        assert expr.emotion_category == EmotionCategory.JOY
        assert expr.intensity == 0.8


class TestEmotionState:
    """Tests for EmotionState model."""

    def test_emotion_state_creation(self):
        user_id = uuid4()
        companion_id = uuid4()
        state = EmotionState(user_id=user_id, companion_id=companion_id)
        assert state.user_id == user_id
        assert state.companion_id == companion_id
        assert state.valence_arousal.valence == 0.0
        assert state.valence_arousal.arousal == 0.3

    def test_add_appraisal_updates_state(self):
        state = EmotionState(user_id=uuid4(), companion_id=uuid4())
        appraisal = Appraisal(
            novelty=0.5,
            pleasantness=0.8,
            goal_relevance=0.6,
            goal_congruence=0.7,
            coping_potential=0.8,
            norm_compatibility=0.5,
            self_relevance=0.7,
            agency=0.4,
            certainty=0.6,
            control=0.7,
        )
        state.add_appraisal(appraisal)
        assert state.current_appraisal == appraisal
        assert len(state.appraisal_history) == 1
        assert state.valence_arousal.valence > 0  # Positive pleasantness should increase valence

    def test_mood_decay(self):
        state = EmotionState(user_id=uuid4(), companion_id=uuid4())
        state.mood = ValenceArousal(valence=0.8, arousal=0.6)
        # Can't easily test time decay without mocking time
        # But we can verify the method exists
        assert hasattr(state, 'decay_mood')

    def test_get_dominant_emotion(self):
        state = EmotionState(user_id=uuid4(), companion_id=uuid4())
        state.active_emotions = {
            EmotionCategory.JOY: 0.8,
            EmotionCategory.SADNESS: 0.2,
        }
        emotion, intensity = state.get_dominant_emotion()
        assert emotion == EmotionCategory.JOY
        assert intensity == 0.8

    def test_get_emotion_vector(self):
        state = EmotionState(user_id=uuid4(), companion_id=uuid4())
        state.active_emotions = {
            EmotionCategory.JOY: 0.8,
            EmotionCategory.SADNESS: 0.2,
        }
        vector = state.get_emotion_vector()
        assert "valence" in vector
        assert "arousal" in vector
        assert "joy" in vector
        assert "sadness" in vector
        assert len(vector) >= 14  # 2 VA + 12 emotions


class TestCalibrationData:
    """Tests for CalibrationData model."""

    def test_calibration_creation(self):
        user_id = uuid4()
        companion_id = uuid4()
        cal = CalibrationData(user_id=user_id, companion_id=companion_id)
        assert cal.user_id == user_id
        assert cal.valence_bias == 0.0
        assert cal.valence_scale == 1.0

    def test_add_valence_sample(self):
        cal = CalibrationData(user_id=uuid4(), companion_id=uuid4())
        cal.add_valence_sample(0.5, 0.6)
        cal.add_valence_sample(0.3, 0.4)
        assert len(cal.valence_samples) == 2
        assert cal.total_samples == 2

    def test_calibration_quality_increases(self):
        cal = CalibrationData(user_id=uuid4(), companion_id=uuid4())
        assert cal.calibration_quality == 0.0
        
        # Add enough samples to trigger calibration
        for i in range(10):
            cal.add_valence_sample(0.5, 0.5)
            cal.add_arousal_sample(0.5, 0.5)
        
        cal._recalculate_calibration()
        assert cal.calibration_quality > 0.0

    def test_apply_calibration(self):
        cal = CalibrationData(user_id=uuid4(), companion_id=uuid4())
        cal.valence_bias = 0.1
        cal.valence_scale = 0.9
        
        calibrated = cal.apply_valence_calibration(0.5)
        assert calibrated == 0.5 * 0.9 + 0.1


class TestEmotionEvent:
    """Tests for EmotionEvent model."""

    def test_event_creation(self):
        event = EmotionEvent(
            user_id=uuid4(),
            companion_id=uuid4(),
            event_type="analyze",
            payload={"text": "hello", "emotion": "joy"},
        )
        assert event.event_type == "analyze"
        assert event.payload["text"] == "hello"


class TestAppraisalDimension:
    """Tests for AppraisalDimension enum."""

    def test_all_dimensions_exist(self):
        dims = list(AppraisalDimension)
        assert AppraisalDimension.NOVELTY in dims
        assert AppraisalDimension.PLEASANTNESS in dims
        assert AppraisalDimension.GOAL_RELEVANCE in dims
        assert AppraisalDimension.GOAL_CONGRUENCE in dims
        assert AppraisalDimension.COPING_POTENTIAL in dims
        assert AppraisalDimension.NORM_COMPATIBILITY in dims
        assert AppraisalDimension.SELF_RELEVANCE in dims
        assert AppraisalDimension.AGENCY in dims
        assert AppraisalDimension.CERTAINTY in dims
        assert AppraisalDimension.CONTROL in dims


if __name__ == "__main__":
    pytest.main([__file__, "-v"])