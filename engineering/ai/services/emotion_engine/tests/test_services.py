"""Tests for Emotion Engine services."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from uuid import UUID, uuid4
from typing import Dict, List, Optional

from emotion_engine.models.emotion import (
    ValenceArousal,
    Appraisal,
    EmotionCategory,
    ExpressionModality,
    Expression,
    EmotionState,
    CalibrationData,
    AppraisalDimension,
)
from emotion_engine.services.appraisal import AppraisalService
from emotion_engine.services.expression import ExpressionService
from emotion_engine.services.calibration import CalibrationService
from emotion_engine.repositories.base import (
    AppraisalRepository,
    CalibrationRepository,
    ExpressionRepository,
)
from emotion_engine.repositories.postgres import (
    PostgresAppraisalRepository,
    PostgresCalibrationRepository,
    PostgresExpressionRepository,
)


class TestAppraisalService:
    """Tests for AppraisalService."""

    @pytest.fixture
    def mock_appraisal_repo(self):
        return AsyncMock(spec=AppraisalRepository)

    @pytest.fixture
    def appraisal_service(self, mock_appraisal_repo):
        return AppraisalService(appraisal_repo=mock_appraisal_repo)

    @pytest.mark.asyncio
    async def test_appraise_basic(self, appraisal_service):
        """Test basic appraisal extraction."""
        result = await appraisal_service.appraise(
            text="I am so happy and excited about this great news!",
            user_id=uuid4(),
            companion_id=uuid4(),
        )
        
        assert isinstance(result, Appraisal)
        assert result.pleasantness > 0  # Positive text should have positive pleasantness
        assert result.novelty > 0  # "news" suggests novelty
        assert result.goal_congruence > 0  # "great" suggests goal congruence

    @pytest.mark.asyncio
    async def test_appraise_negative(self, appraisal_service):
        """Test appraisal for negative text."""
        result = await appraisal_service.appraise(
            text="This is terrible and I hate it. I failed completely.",
            user_id=uuid4(),
            companion_id=uuid4(),
        )
        
        assert isinstance(result, Appraisal)
        assert result.pleasantness < 0  # Negative text
        assert result.goal_congruence < 0  # "failed" suggests incongruence

    @pytest.mark.asyncio
    async def test_appraise_with_context(self, appraisal_service):
        """Test appraisal with context."""
        result = await appraisal_service.appraise(
            text="I did this",
            user_id=uuid4(),
            companion_id=uuid4(),
            context={"personality": {"neuroticism": 0.8}},
        )
        
        assert isinstance(result, Appraisal)
        # High neuroticism should reduce coping potential
        assert result.coping_potential < 0.7

    @pytest.mark.asyncio
    async def test_appraise_with_hints(self, appraisal_service):
        """Test appraisal with hints."""
        result = await appraisal_service.appraise(
            text="Something happened",
            user_id=uuid4(),
            companion_id=uuid4(),
            hints={"pleasantness": 0.9},
        )
        
        assert isinstance(result, Appraisal)
        assert result.pleasantness > 0.5  # Hint should influence result

    def test_get_dimension_weights(self, appraisal_service):
        """Test dimension weights."""
        weights = appraisal_service.get_dimension_weights()
        assert AppraisalDimension.PLEASANTNESS in weights
        assert AppraisalDimension.GOAL_CONGRUENCE in weights
        assert sum(weights.values()) == pytest.approx(1.0, rel=0.1)


class TestExpressionService:
    """Tests for ExpressionService."""

    @pytest.fixture
    def mock_expression_repo(self):
        return AsyncMock(spec=ExpressionRepository)

    @pytest.fixture
    def expression_service(self, mock_expression_repo):
        return ExpressionService(expression_repo=mock_expression_repo)

    @pytest.fixture
    def sample_state(self):
        return EmotionState(
            user_id=uuid4(),
            companion_id=uuid4(),
            valence_arousal=ValenceArousal(valence=0.5, arousal=0.7),
            active_emotions={EmotionCategory.JOY: 0.8, EmotionCategory.TRUST: 0.3},
        )

    @pytest.mark.asyncio
    async def test_generate_text_expression(self, expression_service, sample_state):
        """Test text expression generation."""
        expr = await expression_service.generate_expression(
            state=sample_state,
            modality=ExpressionModality.TEXT,
            emotion=EmotionCategory.JOY,
        )
        
        assert expr.modality == ExpressionModality.TEXT
        assert expr.emotion_category == EmotionCategory.JOY
        assert expr.intensity > 0
        assert hasattr(expr, 'text_formality')
        assert hasattr(expr, 'text_verbosity')
        assert hasattr(expr, 'text_emoji_probability')

    @pytest.mark.asyncio
    async def test_generate_voice_expression(self, expression_service, sample_state):
        """Test voice expression generation."""
        expr = await expression_service.generate_expression(
            state=sample_state,
            modality=ExpressionModality.VOICE,
            emotion=EmotionCategory.JOY,
        )
        
        assert expr.modality == ExpressionModality.VOICE
        assert hasattr(expr, 'voice_pitch_shift')
        assert hasattr(expr, 'voice_rate_change')
        assert hasattr(expr, 'voice_volume_change')

    @pytest.mark.asyncio
    async def test_generate_face_expression(self, expression_service, sample_state):
        """Test face expression generation."""
        expr = await expression_service.generate_expression(
            state=sample_state,
            modality=ExpressionModality.FACE,
            emotion=EmotionCategory.JOY,
        )
        
        assert expr.modality == ExpressionModality.FACE
        assert hasattr(expr, 'face_action_units')
        assert 'AU12' in expr.face_action_units  # Smile

    @pytest.mark.asyncio
    async def test_generate_gesture_expression(self, expression_service, sample_state):
        """Test gesture expression generation."""
        expr = await expression_service.generate_expression(
            state=sample_state,
            modality=ExpressionModality.GESTURE,
            emotion=EmotionCategory.JOY,
        )
        
        assert expr.modality == ExpressionModality.GESTURE
        assert hasattr(expr, 'gesture_amplitude')
        assert hasattr(expr, 'gesture_speed')

    @pytest.mark.asyncio
    async def test_generate_all_expressions(self, expression_service, sample_state):
        """Test generating expressions for all modalities."""
        modalities = [
            ExpressionModality.TEXT,
            ExpressionModality.VOICE,
            ExpressionModality.FACE,
            ExpressionModality.GESTURE,
        ]
        
        expressions = await expression_service.generate_all_expressions(
            state=sample_state,
            modalities=modalities,
        )
        
        assert len(expressions) == 4
        for modality in modalities:
            assert modality in expressions

    @pytest.mark.asyncio
    async def test_personality_influence(self, expression_service, sample_state):
        """Test personality affects expressions."""
        # High extraversion
        expr_extraverted = await expression_service.generate_expression(
            state=sample_state,
            modality=ExpressionModality.TEXT,
            emotion=EmotionCategory.JOY,
            personality={"extraversion": 0.9, "agreeableness": 0.5},
        )
        
        # Low extraversion
        expr_introverted = await expression_service.generate_expression(
            state=sample_state,
            modality=ExpressionModality.TEXT,
            emotion=EmotionCategory.JOY,
            personality={"extraversion": 0.1, "agreeableness": 0.5},
        )
        
        # Extraverted should be more verbose
        assert expr_extraverted.text_verbosity > expr_introverted.text_verbosity

    @pytest.mark.asyncio
    async def test_context_influence(self, expression_service, sample_state):
        """Test context affects expressions."""
        # Formal context
        expr_formal = await expression_service.generate_expression(
            state=sample_state,
            modality=ExpressionModality.TEXT,
            emotion=EmotionCategory.JOY,
            context={"social_setting": "formal"},
        )
        
        # Casual context
        expr_casual = await expression_service.generate_expression(
            state=sample_state,
            modality=ExpressionModality.TEXT,
            emotion=EmotionCategory.JOY,
            context={"social_setting": "casual"},
        )
        
        # Formal should be more formal
        assert expr_formal.text_formality > expr_casual.text_formality
        # Formal should have fewer emojis
        assert expr_formal.text_emoji_probability < expr_casual.text_emoji_probability

    def test_valence_arousal_to_expression(self, expression_service):
        """Test direct VA to expression mapping."""
        va = ValenceArousal(valence=0.8, arousal=0.7)
        
        text_params = expression_service.valence_arousal_to_expression_params(
            va, ExpressionModality.TEXT
        )
        
        assert 'text_formality' in text_params
        assert 'text_verbosity' in text_params
        assert 'text_emoji_probability' in text_params
        # Positive valence -> less formal, more emojis
        assert text_params['text_formality'] < 0.5
        assert text_params['text_emoji_probability'] > 0.1


class TestCalibrationService:
    """Tests for CalibrationService."""

    @pytest.fixture
    def mock_calibration_repo(self):
        return AsyncMock(spec=CalibrationRepository)

    @pytest.fixture
    def calibration_service(self, mock_calibration_repo):
        return CalibrationService(calibration_repo=mock_calibration_repo)

    @pytest.fixture
    def sample_calibration(self):
        return CalibrationData(
            user_id=uuid4(),
            companion_id=uuid4(),
            valence_bias=0.1,
            valence_scale=0.9,
            arousal_bias=-0.05,
            arousal_scale=1.1,
        )

    @pytest.mark.asyncio
    async def test_get_calibration_creates_if_missing(self, calibration_service, mock_calibration_repo):
        """Test get_calibration creates new if not exists."""
        mock_calibration_repo.get.return_value = None
        mock_calibration_repo.create = AsyncMock(return_value=CalibrationData(
            user_id=uuid4(), companion_id=uuid4()
        ))
        
        cal = await calibration_service.get_calibration(uuid4(), uuid4())
        
        assert isinstance(cal, CalibrationData)
        mock_calibration_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_valence_feedback(self, calibration_service, mock_calibration_repo):
        """Test recording valence feedback."""
        mock_calibration_repo.add_valence_sample = AsyncMock(
            return_value=CalibrationData(user_id=uuid4(), companion_id=uuid4())
        )
        
        cal = await calibration_service.record_valence_feedback(
            uuid4(), uuid4(), 0.5, 0.6
        )
        
        mock_calibration_repo.add_valence_sample.assert_called_once()

    @pytest.mark.asyncio
    async def test_calibrate_valence_arousal(self, calibration_service, mock_calibration_repo):
        """Test applying calibration to VA."""
        mock_calibration_repo.get = AsyncMock(return_value=CalibrationData(
            user_id=uuid4(),
            companion_id=uuid4(),
            valence_bias=0.1,
            valence_scale=0.9,
            arousal_bias=0.0,
            arousal_scale=1.0,
            calibration_quality=0.8,
        ))
        
        state = EmotionState(
            user_id=uuid4(),
            companion_id=uuid4(),
            valence_arousal=ValenceArousal(valence=0.5, arousal=0.5),
        )
        
        calibrated = await calibration_service.calibrate_valence_arousal(state)
        
        assert calibrated.valence == pytest.approx(0.5 * 0.9 + 0.1, rel=0.01)
        assert calibrated.arousal == 0.5  # No change

    @pytest.mark.asyncio
    async def test_calibrate_low_quality_returns_original(self, calibration_service, mock_calibration_repo):
        """Test low calibration quality returns original."""
        mock_calibration_repo.get = AsyncMock(return_value=CalibrationData(
            user_id=uuid4(),
            companion_id=uuid4(),
            calibration_quality=0.1,  # Below threshold
        ))
        
        state = EmotionState(
            user_id=uuid4(),
            companion_id=uuid4(),
            valence_arousal=ValenceArousal(valence=0.5, arousal=0.5),
        )
        
        calibrated = await calibration_service.calibrate_valence_arousal(state)
        
        assert calibrated.valence == 0.5
        assert calibrated.arousal == 0.5

    @pytest.mark.asyncio
    async def test_get_expression_preferences(self, calibration_service, mock_calibration_repo):
        """Test getting expression preferences."""
        mock_calibration_repo.get = AsyncMock(return_value=CalibrationData(
            user_id=uuid4(),
            companion_id=uuid4(),
            expression_preferences={
                "joy": {"text:text_verbosity": 0.8, "voice:voice_pitch_shift": 5.0}
            },
        ))
        
        prefs = await calibration_service.get_expression_preferences(
            uuid4(), uuid4(), EmotionCategory.JOY
        )
        
        assert "text:text_verbosity" in prefs
        assert prefs["text:text_verbosity"] == 0.8

    @pytest.mark.asyncio
    async def test_apply_expression_preferences(self, calibration_service, mock_calibration_repo):
        """Test applying expression preferences."""
        mock_calibration_repo.get = AsyncMock(return_value=CalibrationData(
            user_id=uuid4(),
            companion_id=uuid4(),
            expression_preferences={
                "joy": {"text:text_verbosity": 0.9}  # User prefers more verbosity
            },
        ))
        
        params = {"text_verbosity": 0.5, "text_formality": 0.5}
        adjusted = await calibration_service.apply_expression_preferences(
            uuid4(), uuid4(), EmotionCategory.JOY, "text", params
        )
        
        # Should blend 70/30: 0.7 * 0.5 + 0.3 * 0.9 = 0.35 + 0.27 = 0.62
        assert adjusted["text_verbosity"] == pytest.approx(0.62, rel=0.01)
        # Other params unchanged
        assert adjusted["text_formality"] == 0.5

    @pytest.mark.asyncio
    async def test_get_calibration_status(self, calibration_service, mock_calibration_repo):
        """Test getting calibration status."""
        mock_calibration_repo.get = AsyncMock(return_value=CalibrationData(
            user_id=uuid4(),
            companion_id=uuid4(),
            calibration_quality=0.75,
            total_samples=100,
            valence_bias=0.05,
            valence_scale=0.95,
            arousal_bias=-0.02,
            arousal_scale=1.05,
            last_calibrated=datetime.utcnow(),
            appraisal_weights={"pleasantness": 0.35},
            expression_preferences={"joy": {}},
        ))
        
        status = await calibration_service.get_calibration_status(uuid4(), uuid4())
        
        assert status["calibration_quality"] == 0.75
        assert status["total_samples"] == 100
        assert status["valence_bias"] == 0.05
        assert "appraisal_weights" in status

    @pytest.mark.asyncio
    async def test_detect_calibration_drift(self, calibration_service, mock_calibration_repo):
        """Test drift detection."""
        # Create calibration with drift
        cal = CalibrationData(user_id=uuid4(), companion_id=uuid4())
        # Add older samples with low error
        for _ in range(10):
            cal.add_valence_sample(0.5, 0.5)  # Perfect prediction
        # Add recent samples with high error
        for _ in range(10):
            cal.add_valence_sample(0.5, 0.8)  # High error
        
        mock_calibration_repo.get = AsyncMock(return_value=cal)
        
        has_drift, drift_info = await calibration_service.detect_calibration_drift(
            uuid4(), uuid4()
        )
        
        assert has_drift is True
        assert "valence_drift" in drift_info
        assert drift_info["valence_drift"] > 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])