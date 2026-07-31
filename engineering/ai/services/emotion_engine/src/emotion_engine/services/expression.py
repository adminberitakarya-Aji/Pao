"""Expression Service - Generate emotional expressions across modalities."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from emotion_engine.config import settings
from emotion_engine.models.emotion import (
    Expression,
    EmotionState,
    ValenceArousal,
    EmotionCategory,
    ExpressionModality,
    Appraisal,
)
from emotion_engine.repositories.base import ExpressionRepository
from emotion_engine.repositories.postgres import PostgresExpressionRepository


class ExpressionService:
    """
    Service for generating emotional expressions across modalities.
    
    Maps internal emotion state to external expression parameters
    for text, voice, face, and gesture modalities.
    """

    def __init__(
        self,
        expression_repo: Optional[ExpressionRepository] = None,
    ):
        self.expression_repo = expression_repo or PostgresExpressionRepository()
        self._templates_cache: Dict[str, Expression] = {}
        self._cache_loaded = False

        # Default expression templates (personality-neutral baseline)
        self._default_templates = self._create_default_templates()

    def _create_default_templates(self) -> Dict[str, Expression]:
        """Create default expression templates for each modality/emotion."""
        templates = {}

        # Text templates
        text_templates = {
            EmotionCategory.JOY: {
                "text_tone": "cheerful",
                "text_formality": 0.3,
                "text_verbosity": 0.7,
                "text_emoji_probability": 0.3,
            },
            EmotionCategory.SADNESS: {
                "text_tone": "gentle",
                "text_formality": 0.5,
                "text_verbosity": 0.4,
                "text_emoji_probability": 0.1,
            },
            EmotionCategory.ANGER: {
                "text_tone": "firm",
                "text_formality": 0.6,
                "text_verbosity": 0.5,
                "text_emoji_probability": 0.05,
            },
            EmotionCategory.FEAR: {
                "text_tone": "concerned",
                "text_formality": 0.5,
                "text_verbosity": 0.6,
                "text_emoji_probability": 0.1,
            },
            EmotionCategory.SURPRISE: {
                "text_tone": "excited",
                "text_formality": 0.3,
                "text_verbosity": 0.8,
                "text_emoji_probability": 0.4,
            },
            EmotionCategory.TRUST: {
                "text_tone": "warm",
                "text_formality": 0.4,
                "text_verbosity": 0.6,
                "text_emoji_probability": 0.15,
            },
            EmotionCategory.LOVE: {
                "text_tone": "affectionate",
                "text_formality": 0.3,
                "text_verbosity": 0.7,
                "text_emoji_probability": 0.35,
            },
            EmotionCategory.PRIDE: {
                "text_tone": "confident",
                "text_formality": 0.5,
                "text_verbosity": 0.5,
                "text_emoji_probability": 0.1,
            },
            EmotionCategory.SHAME: {
                "text_tone": "apologetic",
                "text_formality": 0.6,
                "text_verbosity": 0.4,
                "text_emoji_probability": 0.05,
            },
            EmotionCategory.GRATITUDE: {
                "text_tone": "appreciative",
                "text_formality": 0.4,
                "text_verbosity": 0.6,
                "text_emoji_probability": 0.2,
            },
            EmotionCategory.HOPE: {
                "text_tone": "optimistic",
                "text_formality": 0.4,
                "text_verbosity": 0.6,
                "text_emoji_probability": 0.15,
            },
            EmotionCategory.RELIEF: {
                "text_tone": "relieved",
                "text_formality": 0.4,
                "text_verbosity": 0.5,
                "text_emoji_probability": 0.1,
            },
            EmotionCategory.NEUTRAL: {
                "text_tone": "neutral",
                "text_formality": 0.5,
                "text_verbosity": 0.5,
                "text_emoji_probability": 0.05,
            },
        }

        # Voice templates
        voice_templates = {
            EmotionCategory.JOY: {
                "voice_pitch_shift": 3.0,
                "voice_rate_change": 1.15,
                "voice_volume_change": 2.0,
                "voice_quality": "bright",
            },
            EmotionCategory.SADNESS: {
                "voice_pitch_shift": -2.0,
                "voice_rate_change": 0.85,
                "voice_volume_change": -3.0,
                "voice_quality": "soft",
            },
            EmotionCategory.ANGER: {
                "voice_pitch_shift": 2.0,
                "voice_rate_change": 1.2,
                "voice_volume_change": 4.0,
                "voice_quality": "pressed",
            },
            EmotionCategory.FEAR: {
                "voice_pitch_shift": 4.0,
                "voice_rate_change": 1.1,
                "voice_volume_change": -1.0,
                "voice_quality": "breathy",
            },
            EmotionCategory.SURPRISE: {
                "voice_pitch_shift": 5.0,
                "voice_rate_change": 1.25,
                "voice_volume_change": 3.0,
                "voice_quality": "bright",
            },
            EmotionCategory.LOVE: {
                "voice_pitch_shift": 1.0,
                "voice_rate_change": 0.95,
                "voice_volume_change": -1.0,
                "voice_quality": "warm",
            },
            EmotionCategory.NEUTRAL: {
                "voice_pitch_shift": 0.0,
                "voice_rate_change": 1.0,
                "voice_volume_change": 0.0,
                "voice_quality": "neutral",
            },
        }

        # Face templates (Action Units based on FACS)
        face_templates = {
            EmotionCategory.JOY: {"AU12": 1.0, "AU6": 0.8, "AU25": 0.5},  # Smile + cheek raise + lips part
            EmotionCategory.SADNESS: {"AU1": 0.7, "AU4": 0.6, "AU15": 0.5},  # Inner brow raise + brow lower + lip corner depress
            EmotionCategory.ANGER: {"AU4": 1.0, "AU5": 0.8, "AU7": 0.6, "AU23": 0.5},  # Brow lower + upper lid raise + lid tighten + lip tighten
            EmotionCategory.FEAR: {"AU1": 1.0, "AU2": 0.8, "AU4": 0.5, "AU5": 0.7, "AU20": 0.6},  # Brow raise + upper lid raise + lip stretch
            EmotionCategory.SURPRISE: {"AU1": 1.0, "AU2": 1.0, "AU5": 0.8, "AU26": 0.7},  # Brow raise + lid raise + jaw drop
            EmotionCategory.DISGUST: {"AU9": 0.8, "AU10": 0.7, "AU17": 0.5},  # Nose wrinkle + upper lip raise + chin raise
            EmotionCategory.NEUTRAL: {},
        }

        # Gesture templates
        gesture_templates = {
            EmotionCategory.JOY: {"gesture_type": "open_arms", "gesture_amplitude": 0.8, "gesture_speed": 0.7},
            EmotionCategory.SADNESS: {"gesture_type": "head_down", "gesture_amplitude": 0.4, "gesture_speed": 0.3},
            EmotionCategory.ANGER: {"gesture_type": "pointing", "gesture_amplitude": 0.9, "gesture_speed": 0.9},
            EmotionCategory.FEAR: {"gesture_type": "protective", "gesture_amplitude": 0.6, "gesture_speed": 0.8},
            EmotionCategory.SURPRISE: {"gesture_type": "hands_up", "gesture_amplitude": 0.8, "gesture_speed": 1.0},
            EmotionCategory.LOVE: {"gesture_type": "hand_on_heart", "gesture_amplitude": 0.5, "gesture_speed": 0.4},
            EmotionCategory.NEUTRAL: {"gesture_type": "none", "gesture_amplitude": 0.0, "gesture_speed": 0.5},
        }

        # Build complete templates
        for emotion in EmotionCategory:
            key = f"text:{emotion.value}"
            text_params = text_templates.get(emotion, text_templates[EmotionCategory.NEUTRAL])
            templates[key] = Expression(
                modality=ExpressionModality.TEXT,
                emotion_category=emotion,
                intensity=0.7,
                **text_params,
                personality_influence=0.5,
                context_influence=0.5,
            )

            key = f"voice:{emotion.value}"
            voice_params = voice_templates.get(emotion, voice_templates[EmotionCategory.NEUTRAL])
            templates[key] = Expression(
                modality=ExpressionModality.VOICE,
                emotion_category=emotion,
                intensity=0.7,
                **voice_params,
                personality_influence=0.5,
                context_influence=0.5,
            )

            key = f"face:{emotion.value}"
            face_params = face_templates.get(emotion, {})
            templates[key] = Expression(
                modality=ExpressionModality.FACE,
                emotion_category=emotion,
                intensity=0.7,
                face_action_units=face_params,
                personality_influence=0.5,
                context_influence=0.5,
            )

            key = f"gesture:{emotion.value}"
            gesture_params = gesture_templates.get(emotion, gesture_templates[EmotionCategory.NEUTRAL])
            templates[key] = Expression(
                modality=ExpressionModality.GESTURE,
                emotion_category=emotion,
                intensity=0.7,
                **gesture_params,
                personality_influence=0.5,
                context_influence=0.5,
            )

        return templates

    async def load_templates(self) -> None:
        """Load expression templates from database."""
        if self._cache_loaded:
            return

        try:
            expressions = await self.expression_repo.get_all_expressions()
            for expr in expressions:
                key = f"{expr.modality.value}:{expr.emotion_category.value}"
                self._templates_cache[key] = expr
            self._cache_loaded = True
        except Exception:
            # Fall back to defaults
            self._templates_cache = self._default_templates.copy()
            self._cache_loaded = True

    def _get_template(
        self,
        modality: ExpressionModality,
        emotion: EmotionCategory,
    ) -> Expression:
        """Get expression template for modality and emotion."""
        key = f"{modality.value}:{emotion.value}"
        return self._templates_cache.get(key, self._default_templates.get(key))

    def _apply_personality(
        self,
        template: Expression,
        personality: Dict[str, float],
        intensity: float,
    ) -> Dict[str, float]:
        """Apply personality traits to expression parameters."""
        params = {}

        # Copy base parameters
        if template.modality == ExpressionModality.TEXT:
            params = {
                "text_formality": template.text_formality,
                "text_verbosity": template.text_verbosity,
                "text_emoji_probability": template.text_emoji_probability,
            }
            # Personality adjustments
            extraversion = personality.get("extraversion", 0.5)
            agreeableness = personality.get("agreeableness", 0.5)

            params["text_verbosity"] = params["text_verbosity"] * (0.7 + 0.6 * extraversion)
            params["text_formality"] = params["text_formality"] * (0.8 + 0.4 * (1 - extraversion))
            params["text_emoji_probability"] = params["text_emoji_probability"] * (0.5 + extraversion)

        elif template.modality == ExpressionModality.VOICE:
            params = {
                "voice_pitch_shift": template.voice_pitch_shift,
                "voice_rate_change": template.voice_rate_change,
                "voice_volume_change": template.voice_volume_change,
            }
            neuroticism = personality.get("neuroticism", 0.5)
            extraversion = personality.get("extraversion", 0.5)

            params["voice_pitch_shift"] *= (0.8 + 0.4 * extraversion)
            params["voice_rate_change"] = 1.0 + (params["voice_rate_change"] - 1.0) * (0.8 + 0.4 * extraversion)
            params["voice_volume_change"] *= (0.7 + 0.6 * extraversion)

        elif template.modality == ExpressionModality.FACE:
            params = dict(template.face_action_units)
            # Scale all AUs by intensity and personality
            extraversion = personality.get("extraversion", 0.5)
            scale = 0.7 + 0.6 * extraversion
            params = {k: v * scale for k, v in params.items()}

        elif template.modality == ExpressionModality.GESTURE:
            params = {
                "gesture_amplitude": template.gesture_amplitude,
                "gesture_speed": template.gesture_speed,
            }
            extraversion = personality.get("extraversion", 0.5)
            params["gesture_amplitude"] *= (0.6 + 0.8 * extraversion)
            params["gesture_speed"] *= (0.7 + 0.6 * extraversion)

        # Apply intensity
        for k, v in params.items():
            if isinstance(v, (int, float)):
                params[k] = v * intensity

        return params

    def _apply_context(
        self,
        params: Dict[str, float],
        template: Expression,
        context: Dict[str, Any],
        intensity: float,
    ) -> Dict[str, float]:
        """Apply contextual adjustments to expression parameters."""
        adjusted = params.copy()

        # Social context
        social_setting = context.get("social_setting", "casual")
        if social_setting == "formal":
            if "text_formality" in adjusted:
                adjusted["text_formality"] = min(1.0, adjusted["text_formality"] + 0.3)
            if "text_emoji_probability" in adjusted:
                adjusted["text_emoji_probability"] *= 0.3
            if "voice_volume_change" in adjusted:
                adjusted["voice_volume_change"] *= 0.7
            if "gesture_amplitude" in adjusted:
                adjusted["gesture_amplitude"] *= 0.6

        elif social_setting == "intimate":
            if "text_formality" in adjusted:
                adjusted["text_formality"] = max(0.0, adjusted["text_formality"] - 0.2)
            if "voice_volume_change" in adjusted:
                adjusted["voice_volume_change"] -= 2.0
            if "gesture_amplitude" in adjusted:
                adjusted["gesture_amplitude"] *= 0.8

        # Topic sensitivity
        topic_sensitivity = context.get("topic_sensitivity", 0.0)
        if topic_sensitivity > 0.5:
            # Reduce expressiveness for sensitive topics
            for k in adjusted:
                if isinstance(adjusted[k], (int, float)):
                    adjusted[k] *= (1.0 - topic_sensitivity * 0.5)

        # Time of day
        hour = context.get("hour", datetime.utcnow().hour)
        if hour < 6 or hour > 22:  # Late night/early morning
            if "voice_volume_change" in adjusted:
                adjusted["voice_volume_change"] -= 3.0
            if "gesture_amplitude" in adjusted:
                adjusted["gesture_amplitude"] *= 0.5
            if "text_verbosity" in adjusted:
                adjusted["text_verbosity"] *= 0.7

        return adjusted

    async def generate_expression(
        self,
        state: EmotionState,
        modality: ExpressionModality,
        emotion: Optional[EmotionCategory] = None,
        intensity: Optional[float] = None,
        personality: Optional[Dict[str, float]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Expression:
        """
        Generate expression parameters for a given modality.
        
        Combines base template with personality, context, and current state.
        """
        await self.load_templates()

        # Determine emotion if not specified
        if emotion is None:
            emotion, _ = state.get_dominant_emotion()

        # Determine intensity
        if intensity is None:
            _, intensity = state.get_dominant_emotion()
            intensity = max(0.3, min(1.0, intensity))

        # Get base template
        template = self._get_template(modality, emotion)
        if not template:
            # Fallback to neutral
            template = self._get_template(modality, EmotionCategory.NEUTRAL)

        # Apply personality
        personality = personality or state.expression_style or {}
        params = self._apply_personality(template, personality, intensity)

        # Apply context
        context = context or {}
        params = self._apply_context(params, template, context, intensity)

        # Build final expression
        expression = Expression(
            modality=modality,
            emotion_category=emotion,
            intensity=intensity,
            **params,
            personality_influence=0.6,
            context_influence=0.4,
        )

        return expression

    async def generate_all_expressions(
        self,
        state: EmotionState,
        modalities: List[ExpressionModality],
        personality: Optional[Dict[str, float]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[ExpressionModality, Expression]:
        """Generate expressions for all requested modalities."""
        expressions = {}
        for modality in modalities:
            expressions[modality] = await self.generate_expression(
                state, modality, personality=personality, context=context
            )
        return expressions

    async def get_expression_parameters(
        self,
        modality: ExpressionModality,
        emotion: EmotionCategory,
    ) -> Dict[str, float]:
        """Get raw expression parameters for a modality/emotion."""
        await self.load_templates()
        template = self._get_template(modality, emotion)
        if not template:
            return {}

        if modality == ExpressionModality.TEXT:
            return {
                "text_formality": template.text_formality,
                "text_verbosity": template.text_verbosity,
                "text_emoji_probability": template.text_emoji_probability,
            }
        elif modality == ExpressionModality.VOICE:
            return {
                "voice_pitch_shift": template.voice_pitch_shift,
                "voice_rate_change": template.voice_rate_change,
                "voice_volume_change": template.voice_volume_change,
            }
        elif modality == ExpressionModality.FACE:
            return dict(template.face_action_units)
        elif modality == ExpressionModality.GESTURE:
            return {
                "gesture_amplitude": template.gesture_amplitude,
                "gesture_speed": template.gesture_speed,
            }
        return {}

    async def update_expression_template(
        self,
        modality: ExpressionModality,
        emotion: EmotionCategory,
        parameters: Dict[str, float],
        intensity: float = 0.7,
    ) -> Expression:
        """Update or create an expression template."""
        expression = Expression(
            modality=modality,
            emotion_category=emotion,
            intensity=intensity,
            **parameters,
        )
        saved = await self.expression_repo.create_expression(expression)
        # Update cache
        key = f"{modality.value}:{emotion.value}"
        self._templates_cache[key] = saved
        return saved

    def valence_arousal_to_expression_params(
        self,
        va: ValenceArousal,
        modality: ExpressionModality,
    ) -> Dict[str, float]:
        """
        Convert valence-arousal directly to expression parameters.
        
        Useful when no discrete emotion category is available.
        """
        valence, arousal = va.valence, va.arousal

        if modality == ExpressionModality.TEXT:
            # Map VA to text parameters
            formality = 0.5 - valence * 0.2  # Positive = less formal
            verbosity = 0.5 + arousal * 0.3  # High arousal = more verbose
            emoji_prob = max(0.0, valence * 0.3) * (0.5 + arousal * 0.5)
            return {
                "text_formality": max(0.0, min(1.0, formality)),
                "text_verbosity": max(0.0, min(1.0, verbosity)),
                "text_emoji_probability": max(0.0, min(1.0, emoji_prob)),
            }

        elif modality == ExpressionModality.VOICE:
            pitch = valence * 4.0 + (arousal - 0.5) * 4.0
            rate = 1.0 + (arousal - 0.5) * 0.4
            volume = (arousal - 0.5) * 6.0
            return {
                "voice_pitch_shift": max(-12.0, min(12.0, pitch)),
                "voice_rate_change": max(0.5, min(2.0, rate)),
                "voice_volume_change": max(-12.0, min(12.0, volume)),
            }

        elif modality == ExpressionModality.FACE:
            # Map to key Action Units
            au12 = max(0.0, valence * 0.8) * (0.5 + arousal)  # Smile
            au4 = max(0.0, -valence * 0.8) * (0.5 + arousal)  # Brow lower
            au1 = max(0.0, -valence * 0.5) * arousal  # Inner brow raise
            au5 = arousal * 0.6  # Upper lid raise
            return {
                "AU12": au12,
                "AU4": au4,
                "AU1": au1,
                "AU5": au5,
            }

        elif modality == ExpressionModality.GESTURE:
            amplitude = (0.5 + abs(valence) * 0.3) * (0.5 + arousal)
            speed = 0.5 + arousal * 0.5
            return {
                "gesture_amplitude": max(0.0, min(1.0, amplitude)),
                "gesture_speed": max(0.0, min(1.0, speed)),
            }

        return {}