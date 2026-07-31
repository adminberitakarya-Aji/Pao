"""Appraisal Service - Cognitive appraisal for emotion generation."""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

import numpy as np
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch

from emotion_engine.config import settings
from emotion_engine.models.emotion import (
    Appraisal,
    ValenceArousal,
    EmotionCategory,
    AppraisalDimension,
)
from emotion_engine.repositories.base import AppraisalRepository
from emotion_engine.repositories.postgres import PostgresAppraisalRepository


class AppraisalService:
    """
    Service for cognitive appraisal of events/text to generate emotional responses.
    
    Uses a combination of:
    1. Transformer-based sentiment/appraisal classifier
    2. Rule-based appraisal dimension extraction
    3. Context-aware adjustments
    """

    def __init__(
        self,
        appraisal_repo: Optional[AppraisalRepository] = None,
    ):
        self.appraisal_repo = appraisal_repo or PostgresAppraisalRepository()
        self._classifier = None
        self._tokenizer = None
        self._model = None
        self._model_loaded = False

        # Appraisal dimension keywords for rule-based extraction
        self._dimension_keywords = {
            AppraisalDimension.NOVELTY: {
                "high": ["sudden", "unexpected", "surprise", "new", "never", "first time", "shocking"],
                "low": ["routine", "usual", "expected", "familiar", "normal", "regular"],
            },
            AppraisalDimension.PLEASANTNESS: {
                "high": ["happy", "joy", "pleased", "delighted", "wonderful", "great", "amazing", "love", "beautiful"],
                "low": ["sad", "angry", "terrible", "awful", "horrible", "hate", "disgusting", "painful", "upset"],
            },
            AppraisalDimension.GOAL_RELEVANCE: {
                "high": ["important", "critical", "crucial", "deadline", "goal", "target", "objective", "priority"],
                "low": ["trivial", "minor", "irrelevant", "unimportant", "doesn't matter"],
            },
            AppraisalDimension.GOAL_CONGRUENCE: {
                "high": ["success", "achieved", "won", "accomplished", "solved", "fixed", "completed", "progress"],
                "low": ["failed", "lost", "broken", "problem", "error", "issue", "blocked", "stuck", "wrong"],
            },
            AppraisalDimension.COPING_POTENTIAL: {
                "high": ["can", "able", "capable", "confident", "easy", "simple", "manageable", "control", "handle"],
                "low": ["cannot", "unable", "impossible", "difficult", "hard", "overwhelming", "helpless", "stuck"],
            },
            AppraisalDimension.NORM_COMPATIBILITY: {
                "high": ["appropriate", "proper", "correct", "right", "ethical", "moral", "acceptable", "polite"],
                "low": ["inappropriate", "wrong", "unethical", "immoral", "offensive", "rude", "unacceptable"],
            },
            AppraisalDimension.SELF_RELEVANCE: {
                "high": ["me", "my", "mine", "myself", "personal", "affects me", "impact me"],
                "low": ["them", "they", "others", "someone else", "not my problem"],
            },
            AppraisalDimension.AGENCY: {
                "high": ["I did", "I caused", "my fault", "my choice", "I decided", "I chose"],
                "low": ["they did", "it happened", "circumstances", "luck", "fate", "beyond my control"],
            },
            AppraisalDimension.CERTAINTY: {
                "high": ["certain", "sure", "definitely", "guaranteed", "confirmed", "known"],
                "low": ["uncertain", "maybe", "possibly", "unclear", "unknown", "doubtful", "risk"],
            },
            AppraisalDimension.CONTROL: {
                "high": ["control", "manage", "influence", "decide", "choose", "determine"],
                "low": ["powerless", "helpless", "forced", "no choice", "cannot control", "out of control"],
            },
        }

    async def initialize(self):
        """Initialize the appraisal model."""
        if self._model_loaded:
            return

        try:
            # Load transformer model for sentiment/appraisal
            model_name = settings.appraisal_model_name
            self._classifier = pipeline(
                "text-classification",
                model=model_name,
                tokenizer=model_name,
                return_all_scores=True,
                device=0 if torch.cuda.is_available() else -1,
            )
            self._model_loaded = True
        except Exception as e:
            # Fallback to rule-based only
            print(f"Warning: Could not load appraisal model: {e}")
            self._model_loaded = False

    def _extract_appraisal_dimensions(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
        hints: Optional[Dict[str, float]] = None,
    ) -> Dict[AppraisalDimension, float]:
        """Extract appraisal dimensions from text using keyword matching."""
        text_lower = text.lower()
        dimensions = {}

        for dimension, keywords in self._dimension_keywords.items():
            high_matches = sum(1 for kw in keywords["high"] if kw in text_lower)
            low_matches = sum(1 for kw in keywords["low"] if kw in text_lower)

            # Normalize to 0-1 range
            total = high_matches + low_matches
            if total > 0:
                score = high_matches / total
            else:
                score = 0.5  # neutral

            # Apply hints if provided
            if hints and dimension.value in hints:
                score = 0.7 * score + 0.3 * hints[dimension.value]

            # Context adjustments
            if context:
                score = self._apply_context_adjustments(dimension, score, context)

            dimensions[dimension] = max(0.0, min(1.0, score))

        # Special handling for dimensions with -1 to 1 range
        dimensions[AppraisalDimension.PLEASANTNESS] = dimensions[AppraisalDimension.PLEASANTNESS] * 2 - 1
        dimensions[AppraisalDimension.GOAL_CONGRUENCE] = dimensions[AppraisalDimension.GOAL_CONGRUENCE] * 2 - 1
        dimensions[AppraisalDimension.NORM_COMPATIBILITY] = dimensions[AppraisalDimension.NORM_COMPATIBILITY] * 2 - 1
        dimensions[AppraisalDimension.AGENCY] = dimensions[AppraisalDimension.AGENCY] * 2 - 1

        return dimensions

    def _apply_context_adjustments(
        self,
        dimension: AppraisalDimension,
        score: float,
        context: Dict[str, Any],
    ) -> float:
        """Apply context-based adjustments to appraisal dimensions."""
        # Relationship context
        relationship_phase = context.get("relationship_phase")
        if relationship_phase == "intimate" and dimension == AppraisalDimension.SELF_RELEVANCE:
            score = min(1.0, score + 0.2)
        elif relationship_phase == "distant" and dimension == AppraisalDimension.SELF_RELEVANCE:
            score = max(0.0, score - 0.1)

        # Personality context
        personality = context.get("personality", {})
        if dimension == AppraisalDimension.COPING_POTENTIAL:
            neuroticism = personality.get("neuroticism", 0.5)
            score = score * (1 - neuroticism * 0.3)  # High neuroticism reduces coping
        elif dimension == AppraisalDimension.CERTAINTY:
            openness = personality.get("openness", 0.5)
            score = score * (1 + openness * 0.2)  # High openness increases tolerance for uncertainty

        return score

    async def _get_transformer_appraisal(self, text: str) -> Dict[str, float]:
        """Get appraisal predictions from transformer model."""
        if not self._model_loaded or not self._classifier:
            return {}

        try:
            results = self._classifier(text)
            # Process results based on model output format
            scores = {}
            for result in results[0]:
                label = result["label"].lower()
                score = result["score"]
                if "positive" in label or "joy" in label:
                    scores["pleasantness"] = score
                elif "negative" in label or "sad" in label or "anger" in label:
                    scores["pleasantness"] = -score
                elif "surprise" in label:
                    scores["novelty"] = score
            return scores
        except Exception as e:
            print(f"Transformer appraisal error: {e}")
            return {}

    async def appraise(
        self,
        text: str,
        user_id: UUID,
        companion_id: UUID,
        context: Optional[Dict[str, Any]] = None,
        hints: Optional[Dict[str, float]] = None,
    ) -> Appraisal:
        """
        Perform cognitive appraisal of text/situation.
        
        Returns an Appraisal object with all dimensions populated.
        """
        start_time = time.time()

        # Initialize model if needed
        await self.initialize()

        # Extract dimensions using rule-based approach
        dimensions = self._extract_appraisal_dimensions(text, context, hints)

        # Enhance with transformer if available
        transformer_scores = await self._get_transformer_appraisal(text)
        for dim_name, score in transformer_scores.items():
            try:
                dim = AppraisalDimension(dim_name)
                if dim in dimensions:
                    # Blend rule-based and transformer (70/30)
                    dimensions[dim] = 0.7 * dimensions[dim] + 0.3 * score
            except ValueError:
                pass

        # Create appraisal object
        appraisal = Appraisal(
            novelty=dimensions.get(AppraisalDimension.NOVELTY, 0.5),
            pleasantness=dimensions.get(AppraisalDimension.PLEASANTNESS, 0.0),
            goal_relevance=dimensions.get(AppraisalDimension.GOAL_RELEVANCE, 0.5),
            goal_congruence=dimensions.get(AppraisalDimension.GOAL_CONGRUENCE, 0.0),
            coping_potential=dimensions.get(AppraisalDimension.COPING_POTENTIAL, 0.5),
            norm_compatibility=dimensions.get(AppraisalDimension.NORM_COMPATIBILITY, 0.0),
            self_relevance=dimensions.get(AppraisalDimension.SELF_RELEVANCE, 0.5),
            agency=dimensions.get(AppraisalDimension.AGENCY, 0.0),
            certainty=dimensions.get(AppraisalDimension.CERTAINTY, 0.5),
            control=dimensions.get(AppraisalDimension.CONTROL, 0.5),
            trigger_event=text[:500] if text else None,
            confidence=0.7,
            timestamp=datetime.utcnow(),
        )

        # Store in repository
        await self.appraisal_repo.create(appraisal, user_id, companion_id)

        processing_time = (time.time() - start_time) * 1000
        # Could log metrics here

        return appraisal

    async def get_appraisal_history(
        self,
        user_id: UUID,
        companion_id: UUID,
        limit: int = 50,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Appraisal]:
        """Get appraisal history for a user-companion pair."""
        return await self.appraisal_repo.get_history(
            user_id, companion_id, limit, start_date, end_date
        )

    async def get_latest_appraisal(
        self,
        user_id: UUID,
        companion_id: UUID,
    ) -> Optional[Appraisal]:
        """Get the most recent appraisal."""
        return await self.appraisal_repo.get_latest(user_id, companion_id)

    def get_dimension_weights(self) -> Dict[AppraisalDimension, float]:
        """Get the weight of each dimension for valence/arousal prediction."""
        return {
            AppraisalDimension.PLEASANTNESS: 0.30,
            AppraisalDimension.GOAL_CONGRUENCE: 0.20,
            AppraisalDimension.COPING_POTENTIAL: 0.15,
            AppraisalDimension.NORM_COMPATIBILITY: 0.15,
            AppraisalDimension.SELF_RELEVANCE: 0.10,
            AppraisalDimension.AGENCY: 0.10,
        }