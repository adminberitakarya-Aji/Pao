"""Calibration Service - Personalize emotion recognition and expression."""

from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID

import numpy as np

from emotion_engine.config import settings
from emotion_engine.models.emotion import (
    CalibrationData,
    ValenceArousal,
    EmotionCategory,
    EmotionState,
    AppraisalDimension,
)
from emotion_engine.repositories.base import CalibrationRepository
from emotion_engine.repositories.postgres import PostgresCalibrationRepository


class CalibrationService:
    """
    Service for calibrating emotion predictions to individual users.
    
    Tracks user feedback and adjusts model predictions for better personalization.
    """

    def __init__(
        self,
        calibration_repo: Optional[CalibrationRepository] = None,
    ):
        self.calibration_repo = calibration_repo or PostgresCalibrationRepository()
        self._min_samples = settings.calibration_min_samples
        self._window_size = settings.calibration_window_size
        self._drift_threshold = settings.calibration_drift_threshold

    async def get_calibration(
        self,
        user_id: UUID,
        companion_id: UUID,
    ) -> CalibrationData:
        """Get calibration data, creating if not exists."""
        calibration = await self.calibration_repo.get(user_id, companion_id)
        if not calibration:
            calibration = CalibrationData(
                user_id=user_id,
                companion_id=companion_id,
            )
            calibration = await self.calibration_repo.create(calibration)
        return calibration

    async def record_valence_feedback(
        self,
        user_id: UUID,
        companion_id: UUID,
        predicted_valence: float,
        actual_valence: float,
    ) -> CalibrationData:
        """Record user feedback on valence prediction."""
        return await self.calibration_repo.add_valence_sample(
            user_id, companion_id, predicted_valence, actual_valence
        )

    async def record_arousal_feedback(
        self,
        user_id: UUID,
        companion_id: UUID,
        predicted_arousal: float,
        actual_arousal: float,
    ) -> CalibrationData:
        """Record user feedback on arousal prediction."""
        return await self.calibration_repo.add_arousal_sample(
            user_id, companion_id, predicted_arousal, actual_arousal
        )

    async def record_emotion_feedback(
        self,
        user_id: UUID,
        companion_id: UUID,
        predicted_emotion: EmotionCategory,
        actual_emotion: EmotionCategory,
        confidence: float,
    ) -> CalibrationData:
        """Record feedback on emotion category prediction."""
        calibration = await self.get_calibration(user_id, companion_id)
        
        # Update emotion-specific preferences
        if actual_emotion.value not in calibration.expression_preferences:
            calibration.expression_preferences[actual_emotion.value] = {}
        
        pref = calibration.expression_preferences[actual_emotion.value]
        pref["prediction_accuracy"] = pref.get("prediction_accuracy", 0.5) * 0.9 + 0.1 * (1.0 if predicted_emotion == actual_emotion else 0.0)
        pref["confidence_calibration"] = pref.get("confidence_calibration", 0.5) * 0.9 + 0.1 * confidence
        
        calibration.total_samples += 1
        calibration.last_calibrated = datetime.utcnow()
        calibration._recalculate_calibration()
        
        return await self.calibration_repo.update(calibration)

    async def record_expression_feedback(
        self,
        user_id: UUID,
        companion_id: UUID,
        emotion: EmotionCategory,
        modality: str,
        parameter: str,
        predicted_value: float,
        preferred_value: float,
    ) -> CalibrationData:
        """Record feedback on expression parameters."""
        calibration = await self.get_calibration(user_id, companion_id)
        
        emotion_key = emotion.value
        if emotion_key not in calibration.expression_preferences:
            calibration.expression_preferences[emotion_key] = {}
        
        pref = calibration.expression_preferences[emotion_key]
        param_key = f"{modality}:{parameter}"
        
        if param_key not in pref:
            pref[param_key] = preferred_value
        else:
            # Exponential moving average
            pref[param_key] = 0.8 * pref[param_key] + 0.2 * preferred_value
        
        calibration.total_samples += 1
        calibration.last_calibrated = datetime.utcnow()
        calibration._recalculate_calibration()
        
        return await self.calibration_repo.update(calibration)

    async def calibrate_valence_arousal(
        self,
        state: EmotionState,
    ) -> ValenceArousal:
        """Apply calibration to valence/arousal prediction."""
        calibration = await self.get_calibration(state.user_id, state.companion_id)
        
        if calibration.calibration_quality < 0.3:
            # Not enough calibration data, return original
            return state.valence_arousal
        
        calibrated_valence = calibration.apply_valence_calibration(state.valence_arousal.valence)
        calibrated_arousal = calibration.apply_arousal_calibration(state.valence_arousal.arousal)
        
        return ValenceArousal(
            valence=calibrated_valence,
            arousal=calibrated_arousal,
            confidence=state.valence_arousal.confidence * calibration.calibration_quality,
            timestamp=datetime.utcnow(),
        )

    async def calibrate_appraisal_weights(
        self,
        user_id: UUID,
        companion_id: UUID,
    ) -> Dict[AppraisalDimension, float]:
        """Get calibrated appraisal dimension weights."""
        calibration = await self.get_calibration(user_id, companion_id)
        
        # Start with default weights
        default_weights = {
            AppraisalDimension.PLEASANTNESS: 0.30,
            AppraisalDimension.GOAL_CONGRUENCE: 0.20,
            AppraisalDimension.COPING_POTENTIAL: 0.15,
            AppraisalDimension.NORM_COMPATIBILITY: 0.15,
            AppraisalDimension.SELF_RELEVANCE: 0.10,
            AppraisalDimension.AGENCY: 0.10,
        }
        
        # Apply calibrated weights if available
        if calibration.appraisal_weights:
            for dim, weight in calibration.appraisal_weights.items():
                if dim in default_weights:
                    default_weights[dim] = weight
        
        return default_weights

    async def get_expression_preferences(
        self,
        user_id: UUID,
        companion_id: UUID,
        emotion: EmotionCategory,
    ) -> Dict[str, float]:
        """Get user's expression preferences for an emotion."""
        calibration = await self.get_calibration(user_id, companion_id)
        return calibration.expression_preferences.get(emotion.value, {})

    async def apply_expression_preferences(
        self,
        user_id: UUID,
        companion_id: UUID,
        emotion: EmotionCategory,
        modality: str,
        parameters: Dict[str, float],
    ) -> Dict[str, float]:
        """Apply user's expression preferences to parameters."""
        prefs = await self.get_expression_preferences(user_id, companion_id, emotion)
        
        adjusted = parameters.copy()
        for param_key, pref_value in prefs.items():
            if ":" in param_key:
                pref_modality, pref_param = param_key.split(":", 1)
                if pref_modality == modality and pref_param in adjusted:
                    # Blend predicted with preferred (70/30)
                    adjusted[pref_param] = 0.7 * adjusted[pref_param] + 0.3 * pref_value
        
        return adjusted

    async def get_calibration_status(
        self,
        user_id: UUID,
        companion_id: UUID,
    ) -> Dict[str, Any]:
        """Get calibration status and quality metrics."""
        calibration = await self.get_calibration(user_id, companion_id)
        
        return {
            "user_id": str(user_id),
            "companion_id": str(companion_id),
            "calibration_quality": calibration.calibration_quality,
            "total_samples": calibration.total_samples,
            "valence_bias": calibration.valence_bias,
            "valence_scale": calibration.valence_scale,
            "arousal_bias": calibration.arousal_bias,
            "arousal_scale": calibration.arousal_scale,
            "last_calibrated": calibration.last_calibrated.isoformat() if calibration.last_calibrated else None,
            "valence_samples_count": len(calibration.valence_samples),
            "arousal_samples_count": len(calibration.arousal_samples),
            "appraisal_weights": {k.value: v for k, v in calibration.appraisal_weights.items()},
            "expression_preferences_count": len(calibration.expression_preferences),
        }

    async def detect_calibration_drift(
        self,
        user_id: UUID,
        companion_id: UUID,
    ) -> Tuple[bool, Dict[str, float]]:
        """Detect if calibration has drifted significantly."""
        calibration = await self.get_calibration(user_id, companion_id)
        
        if len(calibration.valence_samples) < 20 or len(calibration.arousal_samples) < 20:
            return False, {}
        
        # Check recent vs older samples
        recent_valence = calibration.valence_samples[-10:]
        older_valence = calibration.valence_samples[-20:-10]
        
        recent_arousal = calibration.arousal_samples[-10:]
        older_arousal = calibration.arousal_samples[-20:-10]
        
        drift_info = {}
        has_drift = False
        
        if recent_valence and older_valence:
            recent_error = np.mean([abs(p - a) for p, a in recent_valence])
            older_error = np.mean([abs(p - a) for p, a in older_valence])
            valence_drift = abs(recent_error - older_error)
            drift_info["valence_drift"] = valence_drift
            if valence_drift > self._drift_threshold:
                has_drift = True
        
        if recent_arousal and older_arousal:
            recent_error = np.mean([abs(p - a) for p, a in recent_arousal])
            older_error = np.mean([abs(p - a) for p, a in older_arousal])
            arousal_drift = abs(recent_error - older_error)
            drift_info["arousal_drift"] = arousal_drift
            if arousal_drift > self._drift_threshold:
                has_drift = True
        
        return has_drift, drift_info

    async def reset_calibration(
        self,
        user_id: UUID,
        companion_id: UUID,
    ) -> CalibrationData:
        """Reset calibration to defaults."""
        calibration = CalibrationData(
            user_id=user_id,
            companion_id=companion_id,
        )
        return await self.calibration_repo.create(calibration)

    async def export_calibration_data(
        self,
        user_id: UUID,
        companion_id: UUID,
    ) -> Dict[str, Any]:
        """Export calibration data for backup/transfer."""
        calibration = await self.get_calibration(user_id, companion_id)
        
        return {
            "user_id": str(user_id),
            "companion_id": str(companion_id),
            "valence_bias": calibration.valence_bias,
            "valence_scale": calibration.valence_scale,
            "valence_samples": calibration.valence_samples,
            "arousal_bias": calibration.arousal_bias,
            "arousal_scale": calibration.arousal_scale,
            "arousal_samples": calibration.arousal_samples,
            "appraisal_weights": {k.value: v for k, v in calibration.appraisal_weights.items()},
            "expression_preferences": calibration.expression_preferences,
            "total_samples": calibration.total_samples,
            "last_calibrated": calibration.last_calibrated.isoformat() if calibration.last_calibrated else None,
            "calibration_quality": calibration.calibration_quality,
        }

    async def import_calibration_data(
        self,
        data: Dict[str, Any],
    ) -> CalibrationData:
        """Import calibration data from backup."""
        calibration = CalibrationData(
            user_id=UUID(data["user_id"]),
            companion_id=UUID(data["companion_id"]),
            valence_bias=data.get("valence_bias", 0.0),
            valence_scale=data.get("valence_scale", 1.0),
            valence_samples=data.get("valence_samples", []),
            arousal_bias=data.get("arousal_bias", 0.0),
            arousal_scale=data.get("arousal_scale", 1.0),
            arousal_samples=data.get("arousal_samples", []),
            appraisal_weights={
                AppraisalDimension(k): v for k, v in data.get("appraisal_weights", {}).items()
            },
            expression_preferences=data.get("expression_preferences", {}),
            total_samples=data.get("total_samples", 0),
            last_calibrated=datetime.fromisoformat(data["last_calibrated"]) if data.get("last_calibrated") else None,
            calibration_quality=data.get("calibration_quality", 0.0),
        )
        
        return await self.calibration_repo.create(calibration)