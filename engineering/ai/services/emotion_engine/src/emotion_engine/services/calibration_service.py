"""Emotion Calibration Service for emotion regulation and calibration."""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, List
from uuid import UUID
from dataclasses import dataclass, field

import numpy as np

from emotion_engine.config import settings
from emotion_engine.models.requests import CalibrationRequest
from emotion_engine.models.responses import CalibrationResponse

logger = logging.getLogger(__name__)


@dataclass
class EmotionState:
    """Current emotion state."""
    valence: float = 0.0
    arousal: float = 0.0
    dominant_emotion: str = "neutral"
    timestamp: float = field(default_factory=time.time)


class CalibrationService:
    """Service for emotion calibration and regulation strategies."""
    
    # Regulation strategies with effectiveness ratings
    REGULATION_STRATEGIES = {
        "reappraisal": {
            "name": "Cognitive Reappraisal",
            "description": "Reinterpret the situation to change its emotional impact",
            "base_effectiveness": 0.8,
            "best_for": ["anger", "fear", "sadness", "anxiety"],
            "steps": [
                "Identify the triggering thought",
                "Consider alternative interpretations",
                "Evaluate evidence for each interpretation",
                "Adopt a more balanced perspective",
            ],
            "valence_shift": 0.3,
            "arousal_shift": -0.2,
        },
        "suppression": {
            "name": "Expressive Suppression",
            "description": "Inhibit outward expression of emotion",
            "base_effectiveness": 0.4,
            "best_for": ["anger", "fear", "surprise"],
            "steps": [
                "Notice the urge to express the emotion",
                "Consciously relax facial muscles",
                "Control tone of voice",
                "Redirect attention",
            ],
            "valence_shift": 0.0,
            "arousal_shift": -0.1,
        },
        "distraction": {
            "name": "Attentional Distraction",
            "description": "Shift attention away from emotional trigger",
            "base_effectiveness": 0.6,
            "best_for": ["anger", "fear", "sadness", "anxiety", "craving"],
            "steps": [
                "Identify a neutral or positive focus",
                "Engage in absorbing activity",
                "Use sensory grounding (5-4-3-2-1 technique)",
                "Return to task when calmer",
            ],
            "valence_shift": 0.1,
            "arousal_shift": -0.3,
        },
        "acceptance": {
            "name": "Emotional Acceptance",
            "description": "Accept emotions without judgment or resistance",
            "base_effectiveness": 0.75,
            "best_for": ["sadness", "fear", "anxiety", "grief"],
            "steps": [
                "Notice the emotion without labeling it good/bad",
                "Allow the feeling to be present",
                "Observe physical sensations",
                "Practice self-compassion",
            ],
            "valence_shift": 0.15,
            "arousal_shift": -0.15,
        },
        "problem_solving": {
            "name": "Problem-Focused Coping",
            "description": "Take action to address the source of emotion",
            "base_effectiveness": 0.85,
            "best_for": ["anger", "fear", "anxiety", "frustration"],
            "steps": [
                "Define the problem clearly",
                "Brainstorm possible solutions",
                "Evaluate pros and cons",
                "Implement chosen solution",
            ],
            "valence_shift": 0.25,
            "arousal_shift": -0.1,
        },
        "social_support": {
            "name": "Seeking Social Support",
            "description": "Connect with others for emotional or practical support",
            "base_effectiveness": 0.7,
            "best_for": ["sadness", "fear", "anxiety", "loneliness", "grief"],
            "steps": [
                "Identify supportive person",
                "Share feelings honestly",
                "Ask for specific support needed",
                "Reciprocate support when possible",
            ],
            "valence_shift": 0.2,
            "arousal_shift": -0.15,
        },
        "rumination": {
            "name": "Rumination (Maladaptive)",
            "description": "Repetitive focus on negative emotions and causes",
            "base_effectiveness": -0.3,
            "best_for": [],
            "steps": [],
            "valence_shift": -0.2,
            "arousal_shift": 0.1,
        },
        "mindfulness": {
            "name": "Mindfulness Meditation",
            "description": "Non-judgmental present-moment awareness",
            "base_effectiveness": 0.7,
            "best_for": ["anxiety", "anger", "stress", "overwhelm"],
            "steps": [
                "Focus on breath as anchor",
                "Notice thoughts/feelings without engagement",
                "Gently return to breath when distracted",
                "Expand awareness to body sensations",
            ],
            "valence_shift": 0.1,
            "arousal_shift": -0.25,
        },
    }
    
    def __init__(self):
        self.user_histories: Dict[str, List[EmotionState]] = {}
        self.calibration_models: Dict[str, Any] = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the calibration service."""
        logger.info("Initializing Calibration service")
        self._initialized = True
        logger.info("Calibration service initialized")
    
    async def calibrate(self, request: CalibrationRequest) -> CalibrationResponse:
        """Generate emotion regulation recommendations."""
        start_time = time.time()
        
        current_state = {
            "valence": request.current_valence,
            "arousal": request.current_arousal,
        }
        
        target_state = {
            "valence": request.target_valence if request.target_valence is not None else 0.2,
            "arousal": request.target_arousal if request.target_arousal is not None else 0.3,
        }
        
        # Determine dominant emotion from current state
        dominant_emotion = self._va_to_emotion(request.current_valence, request.current_arousal)
        
        # Get strategy recommendations
        recommended = self._recommend_strategy(
            request.current_valence,
            request.current_arousal,
            target_state,
            request.strategy,
            dominant_emotion,
            request.context
        )
        
        alternatives = self._get_alternatives(
            dominant_emotion,
            request.strategy,
            request.current_valence,
            request.current_arousal
        )
        
        # Calculate expected trajectory
        trajectory = self._calculate_trajectory(
            request.current_valence,
            request.current_arousal,
            target_state,
            recommended,
            steps=5
        )
        
        # Calculate regulation difficulty
        difficulty = self._calculate_difficulty(
            request.current_valence,
            request.current_arousal,
            target_state
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        # Store in history
        user_key = f"{request.user_id}:{request.companion_id}"
        if user_key not in self.user_histories:
            self.user_histories[user_key] = []
        
        self.user_histories[user_key].append(EmotionState(
            valence=request.current_valence,
            arousal=request.current_arousal,
            dominant_emotion=dominant_emotion
        ))
        
        # Keep only recent history
        if len(self.user_histories[user_key]) > 100:
            self.user_histories[user_key] = self.user_histories[user_key][-100:]
        
        return CalibrationResponse(
            user_id=request.user_id,
            companion_id=request.companion_id,
            current_state=current_state,
            target_state=target_state,
            recommended_strategy=recommended,
            alternative_strategies=alternatives,
            expected_trajectory=trajectory,
            regulation_difficulty=difficulty,
            processing_time_ms=processing_time,
            request_id=request.request_id,
        )
    
    def _va_to_emotion(self, valence: float, arousal: float) -> str:
        """Map valence-arousal to dominant emotion."""
        if valence > 0.3 and arousal > 0.5:
            return "excitement"
        elif valence > 0.3 and arousal < 0.5:
            return "contentment"
        elif valence < -0.3 and arousal > 0.5:
            return "anger" if valence < -0.5 else "fear"
        elif valence < -0.3 and arousal < 0.5:
            return "sadness"
        else:
            return "neutral"
    
    def _recommend_strategy(
        self,
        current_valence: float,
        current_arousal: float,
        target_state: Dict[str, float],
        preferred_strategy: str,
        dominant_emotion: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Recommend the best regulation strategy."""
        
        # If preferred strategy is specified and valid, use it
        if preferred_strategy in self.REGULATION_STRATEGIES:
            strat = self.REGULATION_STRATEGIES[preferred_strategy]
            if dominant_emotion in strat["best_for"] or not strat["best_for"]:
                return self._format_strategy(preferred_strategy, strat)
        
        # Otherwise, find best strategy for the emotion
        best_strat_name = None
        best_score = -1
        
        for name, strat in self.REGULATION_STRATEGIES.items():
            if dominant_emotion in strat["best_for"] or not strat["best_for"]:
                score = strat["base_effectiveness"]
                
                # Boost score if strategy moves toward target
                valence_diff = target_state["valence"] - current_valence
                arousal_diff = target_state["arousal"] - current_arousal
                
                if (valence_diff > 0 and strat["valence_shift"] > 0) or \
                   (valence_diff < 0 and strat["valence_shift"] < 0):
                    score += 0.1
                
                if (arousal_diff > 0 and strat["arousal_shift"] > 0) or \
                   (arousal_diff < 0 and strat["arousal_shift"] < 0):
                    score += 0.1
                
                if score > best_score:
                    best_score = score
                    best_strat_name = name
        
        if best_strat_name:
            return self._format_strategy(best_strat_name, self.REGULATION_STRATEGIES[best_strat_name])
        
        # Default to reappraisal
        return self._format_strategy("reappraisal", self.REGULATION_STRATEGIES["reappraisal"])
    
    def _format_strategy(self, name: str, strat: Dict[str, Any]) -> Dict[str, Any]:
        """Format strategy for response."""
        return {
            "strategy": name,
            "name": strat["name"],
            "description": strat["description"],
            "effectiveness": strat["base_effectiveness"],
            "steps": strat["steps"],
            "valence_shift": strat["valence_shift"],
            "arousal_shift": strat["arousal_shift"],
        }
    
    def _get_alternatives(
        self,
        dominant_emotion: str,
        exclude: str,
        current_valence: float,
        current_arousal: float
    ) -> List[Dict[str, Any]]:
        """Get alternative regulation strategies."""
        alternatives = []
        
        for name, strat in self.REGULATION_STRATEGIES.items():
            if name != exclude and strat["base_effectiveness"] > 0:
                if dominant_emotion in strat["best_for"] or not strat["best_for"]:
                    alternatives.append(self._format_strategy(name, strat))
        
        # Sort by effectiveness
        alternatives.sort(key=lambda x: x["effectiveness"], reverse=True)
        return alternatives[:3]
    
    def _calculate_trajectory(
        self,
        current_valence: float,
        current_arousal: float,
        target_state: Dict[str, float],
        strategy: Dict[str, Any],
        steps: int = 5
    ) -> List[Dict[str, float]]:
        """Calculate expected emotion trajectory."""
        trajectory = []
        
        valence_shift = strategy.get("valence_shift", 0)
        arousal_shift = strategy.get("arousal_shift", 0)
        
        for i in range(1, steps + 1):
            progress = i / steps
            valence = current_valence + (target_state["valence"] - current_valence) * progress
            arousal = current_arousal + (target_state["arousal"] - current_arousal) * progress
            
            # Add strategy effect
            valence += valence_shift * progress * 0.5
            arousal += arousal_shift * progress * 0.5
            
            # Clamp
            valence = max(-1.0, min(1.0, valence))
            arousal = max(0.0, min(1.0, arousal))
            
            trajectory.append({
                "step": i,
                "valence": round(valence, 3),
                "arousal": round(arousal, 3),
                "progress": round(progress, 2),
            })
        
        return trajectory
    
    def _calculate_difficulty(
        self,
        current_valence: float,
        current_arousal: float,
        target_state: Dict[str, float]
    ) -> float:
        """Calculate regulation difficulty (0-1)."""
        valence_distance = abs(target_state["valence"] - current_valence)
        arousal_distance = abs(target_state["arousal"] - current_arousal)
        
        # High arousal emotions are harder to regulate
        arousal_factor = 1.0 + current_arousal * 0.5
        
        # Extreme valence is harder
        valence_factor = 1.0 + abs(current_valence) * 0.3
        
        distance = (valence_distance + arousal_distance) / 2.0
        difficulty = distance * arousal_factor * valence_factor
        
        return min(1.0, difficulty)
    
    async def get_user_history(self, user_id: UUID, companion_id: UUID, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's emotion history."""
        user_key = f"{user_id}:{companion_id}"
        history = self.user_histories.get(user_key, [])
        
        return [
            {
                "valence": state.valence,
                "arousal": state.arousal,
                "dominant_emotion": state.dominant_emotion,
                "timestamp": state.timestamp,
            }
            for state in history[-limit:]
        ]
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the service."""
        return {
            "initialized": self._initialized,
            "strategies_available": len(self.REGULATION_STRATEGIES),
            "users_tracked": len(self.user_histories),
        }
    
    async def close(self) -> None:
        """Cleanup resources."""
        self.user_histories.clear()
        self.calibration_models.clear()
        self._initialized = False
        logger.info("Calibration service closed")


# Singleton instance
_calibration_service: Optional[CalibrationService] = None


async def get_calibration_service() -> CalibrationService:
    """Get or create Calibration service singleton."""
    global _calibration_service
    if _calibration_service is None:
        _calibration_service = CalibrationService()
        await _calibration_service.initialize()
    return _calibration_service


async def close_calibration_service() -> None:
    """Close Calibration service."""
    global _calibration_service
    if _calibration_service:
        await _calibration_service.close()
        _calibration_service = None