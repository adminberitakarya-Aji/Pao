"""Core emotion models for the Emotion Engine."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict, field_validator


class AppraisalDimension(str, Enum):
    """Dimensions of cognitive appraisal based on Scherer's Component Process Model."""

    NOVELTY = "novelty"
    PLEASANTNESS = "pleasantness"
    GOAL_RELEVANCE = "goal_relevance"
    GOAL_CONGRUENCE = "goal_congruence"
    COPING_POTENTIAL = "coping_potential"
    NORM_COMPATIBILITY = "norm_compatibility"
    SELF_RELEVANCE = "self_relevance"
    AGENCY = "agency"
    CERTAINTY = "certainty"
    CONTROL = "control"


class EmotionCategory(str, Enum):
    """Basic emotion categories (Ekman + extensions)."""

    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    DISGUST = "disgust"
    SURPRISE = "surprise"
    TRUST = "trust"
    ANTICIPATION = "anticipation"
    LOVE = "love"
    PRIDE = "pride"
    SHAME = "shame"
    GUILT = "guilt"
    JEALOUSY = "jealousy"
    GRATITUDE = "gratitude"
    HOPE = "hope"
    RELIEF = "relief"
    NEUTRAL = "neutral"


class ExpressionModality(str, Enum):
    """Modalities for emotional expression."""

    TEXT = "text"
    VOICE = "voice"
    FACE = "face"
    GESTURE = "gesture"


class ValenceArousal(BaseModel):
    """
    Core affect dimensions in the circumplex model.
    
    Valence: -1 (negative) to +1 (positive)
    Arousal: 0 (calm) to 1 (excited)
    """

    model_config = ConfigDict(frozen=True)

    valence: float = Field(ge=-1.0, le=1.0, description="Positive/negative affect")
    arousal: float = Field(ge=0.0, le=1.0, description="Activation/energy level")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)

    @property
    def quadrant(self) -> str:
        """Return the affective quadrant."""
        if self.valence >= 0 and self.arousal >= 0.5:
            return "high_positive"  # Excitement, joy
        elif self.valence >= 0 and self.arousal < 0.5:
            return "low_positive"  # Calm, contentment
        elif self.valence < 0 and self.arousal >= 0.5:
            return "high_negative"  # Anger, fear
        else:
            return "low_negative"  # Sadness, boredom

    def distance_to(self, other: "ValenceArousal") -> float:
        """Euclidean distance in valence-arousal space."""
        return ((self.valence - other.valence) ** 2 + (self.arousal - other.arousal) ** 2) ** 0.5

    def to_polar(self) -> tuple[float, float]:
        """Convert to polar coordinates (angle, radius)."""
        import math
        angle = math.atan2(self.arousal - 0.5, self.valence)
        radius = self.distance_to(ValenceArousal(valence=0.0, arousal=0.5))
        return angle, radius


class Appraisal(BaseModel):
    """
    Cognitive appraisal dimensions that drive emotional response.
    
    Based on Scherer's Component Process Model.
    """

    model_config = ConfigDict(frozen=True)

    # Core appraisal dimensions
    novelty: float = Field(ge=0.0, le=1.0, default=0.5, description="Unexpectedness of event")
    pleasantness: float = Field(ge=-1.0, le=1.0, default=0.0, description="Pleasant/unpleasant")
    goal_relevance: float = Field(ge=0.0, le=1.0, default=0.5, description="Relevance to goals")
    goal_congruence: float = Field(ge=-1.0, le=1.0, default=0.0, description="Alignment with goals")
    coping_potential: float = Field(ge=0.0, le=1.0, default=0.5, description="Ability to cope")
    norm_compatibility: float = Field(ge=-1.0, le=1.0, default=0.0, description="Social norm alignment")
    self_relevance: float = Field(ge=0.0, le=1.0, default=0.5, description="Personal relevance")
    agency: float = Field(ge=-1.0, le=1.0, default=0.0, description="Self vs other causality")
    certainty: float = Field(ge=0.0, le=1.0, default=0.5, description="Predictability")
    control: float = Field(ge=0.0, le=1.0, default=0.5, description="Perceived control")

    # Metadata
    trigger_event: Optional[str] = Field(default=None, description="Event that triggered appraisal")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    confidence: float = Field(ge=0.0, le=1.0, default=0.7)

    def to_valence_arousal(self) -> ValenceArousal:
        """Convert appraisal to valence-arousal prediction."""
        # Simplified mapping based on appraisal theory
        valence = (
            0.3 * self.pleasantness
            + 0.2 * self.goal_congruence
            + 0.15 * self.coping_potential
            + 0.15 * self.norm_compatibility
            + 0.1 * self.self_relevance
            + 0.1 * self.agency
        )

        arousal = (
            0.25 * self.novelty
            + 0.2 * abs(self.goal_congruence)
            + 0.2 * (1 - self.certainty)
            + 0.2 * (1 - self.control)
            + 0.15 * self.goal_relevance
        )

        valence = max(-1.0, min(1.0, valence))
        arousal = max(0.0, min(1.0, arousal))

        return ValenceArousal(valence=valence, arousal=arousal, confidence=self.confidence)

    def predict_emotion_category(self) -> EmotionCategory:
        """Predict basic emotion category from appraisal pattern."""
        va = self.to_valence_arousal()

        # Simple rule-based mapping
        if va.valence > 0.3 and va.arousal > 0.6:
            if self.novelty > 0.7:
                return EmotionCategory.SURPRISE
            return EmotionCategory.JOY
        elif va.valence > 0.3 and va.arousal <= 0.6:
            if self.goal_congruence > 0.5:
                return EmotionCategory.RELIEF
            return EmotionCategory.CONTENTMENT
        elif va.valence < -0.3 and va.arousal > 0.6:
            if self.agency < -0.3:
                return EmotionCategory.ANGER
            elif self.coping_potential < 0.3:
                return EmotionCategory.FEAR
            return EmotionCategory.DISGUST
        elif va.valence < -0.3 and va.arousal <= 0.6:
            return EmotionCategory.SADNESS
        else:
            return EmotionCategory.NEUTRAL


class EmotionState(BaseModel):
    """
    Complete emotional state for a companion.
    
    Includes current affect, appraisal history, and expression settings.
    """

    user_id: UUID
    companion_id: UUID

    # Current core affect
    valence_arousal: ValenceArousal = Field(default_factory=lambda: ValenceArousal(valence=0.0, arousal=0.3))

    # Current appraisal
    current_appraisal: Optional[Appraisal] = None

    # Active emotion categories with intensities
    active_emotions: Dict[EmotionCategory, float] = Field(default_factory=dict)

    # Mood (slower-changing background affect)
    mood: ValenceArousal = Field(default_factory=lambda: ValenceArousal(valence=0.1, arousal=0.2))

    # Expression style (personality-influenced)
    expression_style: Dict[str, float] = Field(default_factory=dict)

    # Calibration data
    calibration: Optional["CalibrationData"] = None

    # History (limited)
    appraisal_history: List[Appraisal] = Field(default_factory=list, max_length=50)
    va_history: List[ValenceArousal] = Field(default_factory=list, max_length=100)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1

    def add_appraisal(self, appraisal: Appraisal) -> None:
        """Add appraisal to history and update state."""
        self.appraisal_history.append(appraisal)
        self.current_appraisal = appraisal
        self.valence_arousal = appraisal.to_valence_arousal()
        self.va_history.append(self.valence_arousal)
        self.updated_at = datetime.utcnow()
        self.version += 1

        # Update active emotions
        predicted = appraisal.predict_emotion_category()
        self.active_emotions[predicted] = self.active_emotions.get(predicted, 0) + 0.2
        # Decay others
        for k in list(self.active_emotions.keys()):
            if k != predicted:
                self.active_emotions[k] = max(0.0, self.active_emotions[k] - 0.05)
                if self.active_emotions[k] < 0.05:
                    del self.active_emotions[k]

    def get_dominant_emotion(self) -> tuple[EmotionCategory, float]:
        """Get the dominant emotion category and intensity."""
        if not self.active_emotions:
            return EmotionCategory.NEUTRAL, 0.0
        dominant = max(self.active_emotions.items(), key=lambda x: x[1])
        return dominant

    def get_emotion_vector(self) -> Dict[str, float]:
        """Get emotion state as a feature vector for downstream tasks."""
        dominant, intensity = self.get_dominant_emotion()
        return {
            "valence": self.valence_arousal.valence,
            "arousal": self.valence_arousal.arousal,
            "dominant_emotion": dominant.value,
            "dominant_intensity": intensity,
            "mood_valence": self.mood.valence,
            "mood_arousal": self.mood.arousal,
            "num_active_emotions": len(self.active_emotions),
        }


class Expression(BaseModel):
    """
    Emotional expression configuration for a specific modality.
    
    Maps internal emotion state to external expression parameters.
    """

    model_config = ConfigDict(frozen=True)

    modality: ExpressionModality
    emotion_category: EmotionCategory
    intensity: float = Field(ge=0.0, le=1.0)

    # Text expression parameters
    text_tone: Optional[str] = None
    text_formality: float = Field(ge=0.0, le=1.0, default=0.5)
    text_verbosity: float = Field(ge=0.0, le=1.0, default=0.5)
    text_emoji_probability: float = Field(ge=0.0, le=1.0, default=0.1)

    # Voice expression parameters
    voice_pitch_shift: float = Field(default=0.0, description="Semitones")
    voice_rate_change: float = Field(default=1.0, description="Multiplier")
    voice_volume_change: float = Field(default=0.0, description="dB")
    voice_quality: Optional[str] = None  # breathy, pressed, etc.

    # Face expression parameters (Action Units)
    face_action_units: Dict[str, float] = Field(default_factory=dict)

    # Gesture parameters
    gesture_type: Optional[str] = None
    gesture_amplitude: float = Field(ge=0.0, le=1.0, default=0.5)
    gesture_speed: float = Field(ge=0.0, le=1.0, default=0.5)

    # Metadata
    personality_influence: float = Field(ge=0.0, le=1.0, default=0.5)
    context_influence: float = Field(ge=0.0, le=1.0, default=0.5)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CalibrationData(BaseModel):
    """
    Calibration data for personalizing emotion recognition/expression.
    
    Tracks user-specific patterns for improved accuracy.
    """

    user_id: UUID
    companion_id: UUID

    # Valence calibration
    valence_bias: float = Field(default=0.0, description="Systematic offset in valence")
    valence_scale: float = Field(default=1.0, description="Sensitivity scaling")
    valence_samples: List[tuple[float, float]] = Field(default_factory=list)  # (predicted, actual)

    # Arousal calibration
    arousal_bias: float = Field(default=0.0)
    arousal_scale: float = Field(default=1.0)
    arousal_samples: List[tuple[float, float]] = Field(default_factory=list)

    # Appraisal calibration
    appraisal_weights: Dict[AppraisalDimension, float] = Field(default_factory=dict)

    # Expression calibration
    expression_preferences: Dict[EmotionCategory, Dict[str, float]] = Field(default_factory=dict)

    # Statistics
    total_samples: int = 0
    last_calibrated: Optional[datetime] = None
    calibration_quality: float = Field(default=0.0, ge=0.0, le=1.0)

    def add_valence_sample(self, predicted: float, actual: float) -> None:
        """Add a valence calibration sample."""
        self.valence_samples.append((predicted, actual))
        if len(self.valence_samples) > 1000:
            self.valence_samples = self.valence_samples[-1000:]
        self.total_samples += 1
        self._recalculate_calibration()

    def add_arousal_sample(self, predicted: float, actual: float) -> None:
        """Add an arousal calibration sample."""
        self.arousal_samples.append((predicted, actual))
        if len(self.arousal_samples) > 1000:
            self.arousal_samples = self.arousal_samples[-1000:]
        self._recalculate_calibration()

    def _recalculate_calibration(self) -> None:
        """Recalibrate bias and scale from samples."""
        if len(self.valence_samples) >= 10:
            import numpy as np
            pred, actual = zip(*self.valence_samples[-100:])
            pred_arr = np.array(pred)
            actual_arr = np.array(actual)
            # Linear regression: actual = scale * pred + bias
            if np.std(pred_arr) > 0.01:
                self.valence_scale = np.cov(pred_arr, actual_arr)[0, 1] / np.var(pred_arr)
                self.valence_bias = np.mean(actual_arr) - self.valence_scale * np.mean(pred_arr)
                self.valence_scale = max(0.1, min(3.0, self.valence_scale))
                self.valence_bias = max(-0.5, min(0.5, self.valence_bias))

        if len(self.arousal_samples) >= 10:
            import numpy as np
            pred, actual = zip(*self.arousal_samples[-100:])
            pred_arr = np.array(pred)
            actual_arr = np.array(actual)
            if np.std(pred_arr) > 0.01:
                self.arousal_scale = np.cov(pred_arr, actual_arr)[0, 1] / np.var(pred_arr)
                self.arousal_bias = np.mean(actual_arr) - self.arousal_scale * np.mean(pred_arr)
                self.arousal_scale = max(0.1, min(3.0, self.arousal_scale))
                self.arousal_bias = max(-0.5, min(0.5, self.arousal_bias))

        self.last_calibrated = datetime.utcnow()
        # Quality based on sample count and consistency
        n = min(len(self.valence_samples), len(self.arousal_samples))
        self.calibration_quality = min(1.0, n / 100.0)

    def apply_valence_calibration(self, valence: float) -> float:
        """Apply calibration to valence prediction."""
        return max(-1.0, min(1.0, self.valence_scale * valence + self.valence_bias))

    def apply_arousal_calibration(self, arousal: float) -> float:
        """Apply calibration to arousal prediction."""
        return max(0.0, min(1.0, self.arousal_scale * arousal + self.arousal_bias))


class EmotionEvent(BaseModel):
    """
    Event representing an emotion-related occurrence.
    
    Used for event sourcing and audit trail.
    """

    event_id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    companion_id: UUID
    event_type: str  # appraisal, expression, calibration, state_change
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)