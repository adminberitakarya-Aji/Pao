"""
Reality Anchor Service.

Detects and responds to potential delusions, hallucinations, paranoia,
and conspiracy thinking by injecting grounding responses.
"""

import time
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import random

from safety_engine.config import get_settings
from safety_engine.models.safety import (
    RealityAnchorResult,
    SafetyCategory,
    InterventionLevel,
    SafetyViolation,
)
from safety_engine.repositories.base import BaseRepository


class RealityAnchorService:
    """Service for reality anchoring - detecting and responding to reality distortion."""
    
    def __init__(
        self,
        postgres_repo: BaseRepository,
        redis_repo: BaseRepository,
    ):
        self.settings = get_settings()
        self.postgres_repo = postgres_repo
        self.redis_repo = redis_repo
        self._model = None
        self._compiled_triggers: List[re.Pattern] = []
    
    async def initialize(self) -> None:
        """Initialize reality anchor triggers and templates."""
        # Compile trigger patterns
        self._compiled_triggers = [
            re.compile(rf"\b{re.escape(trigger)}\b", re.IGNORECASE)
            for trigger in self.settings.reality_anchor_triggers
        ]
        
        # TODO: Load ML model when available
        # self._model = await self._load_model()
    
    async def check_reality(
        self,
        text: str,
        user_id: str,
        companion_id: str,
        conversation_id: Optional[str] = None,
        relationship_context: Optional[Dict[str, Any]] = None,
    ) -> RealityAnchorResult:
        """
        Check for reality distortion indicators.
        
        Detects:
        1. Delusional thinking (fixed false beliefs)
        2. Hallucinations (sensory experiences without stimulus)
        3. Paranoia (persecutory beliefs)
        4. Conspiracy thinking
        5. Simulation/matrix beliefs
        6. Divine/alien command experiences
        """
        start_time = time.perf_counter()
        
        if not self.settings.reality_anchor_enabled:
            return RealityAnchorResult(
                triggered=False,
                intervention_level=InterventionLevel.ALLOW,
                metadata={"disabled": True}
            )
        
        detected_triggers = []
        trigger_category = None
        confidence = 0.0
        
        # 1. Pattern matching for triggers
        detected_triggers = await self._check_triggers(text)
        
        # 2. ML model inference (when available)
        ml_confidence = await self._ml_inference(text)
        confidence = max(confidence, ml_confidence)
        
        # 3. Contextual analysis
        context_confidence = self._analyze_context(relationship_context, text)
        confidence = max(confidence, context_confidence)
        
        # Determine if triggered
        triggered = len(detected_triggers) > 0 or confidence > 0.6
        
        if triggered:
            # Classify trigger category
            trigger_category = self._classify_trigger_category(detected_triggers, text)
            
            # Select anchor response
            anchor_response = self._select_anchor_response(trigger_category, text)
            
            # Determine intervention level
            intervention_level = self._determine_intervention(confidence, trigger_category)
        else:
            anchor_response = None
            intervention_level = InterventionLevel.ALLOW
        
        processing_time_ms = (time.perf_counter() - start_time) * 1000
        
        return RealityAnchorResult(
            triggered=triggered,
            trigger_category=trigger_category,
            detected_triggers=detected_triggers,
            confidence=confidence,
            anchor_response=anchor_response,
            intervention_level=intervention_level,
            metadata={
                "processing_time_ms": processing_time_ms,
                "ml_confidence": ml_confidence,
                "trigger_count": len(detected_triggers),
            }
        )
    
    async def _check_triggers(self, text: str) -> List[str]:
        """Check for reality anchor triggers."""
        found = []
        text_lower = text.lower()
        
        for pattern in self._compiled_triggers:
            if pattern.search(text_lower):
                match = pattern.search(text_lower)
                if match:
                    found.append(match.group(0))
        
        # Additional pattern-based detection
        additional_patterns = [
            (r"\b(voices?|voice)\s+(tell|told|say|said)\s+(me|us)\b", "command_hallucination"),
            (r"\b(god|jesus|allah|spirit|angel)\s+(told|tells|said|says)\s+(me|us)\b", "divine_command"),
            (r"\b(aliens?|extraterrestrials?|ufo)\s+(contact|contacted|watching|monitoring)\b", "alien_belief"),
            (r"\b(government|cia|fbi|nsa|they)\s+(watching|monitoring|following|tracking)\s+(me|us)\b", "paranoia"),
            (r"\b(this is (not real|a simulation|fake|a dream|the matrix))\b", "derealization"),
            (r"\b(i am (god|jesus|the chosen one|special|immortal))\b", "grandiosity"),
            (r"\b(everyone is (against|plotting|conspiring) (me|us))\b", "persecutory"),
            (r"\b(microchip|implant|device)\s+(in|inside)\s+(my|me)\b", "somatic_delusion"),
        ]
        
        for pattern, category in additional_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                found.append(category)
        
        return list(set(found))
    
    async def _ml_inference(self, text: str) -> float:
        """Run ML model inference for reality distortion detection."""
        # TODO: Implement actual model inference
        return 0.0
    
    def _analyze_context(
        self,
        relationship_context: Optional[Dict[str, Any]],
        text: str,
    ) -> float:
        """Analyze context for increased reality distortion risk."""
        if not relationship_context:
            return 0.0
        
        confidence = 0.0
        
        # Check relationship phase
        phase = relationship_context.get("phase", "")
        if phase in ["intensifying", "integrating"]:
            # High intimacy phases may increase vulnerability
            confidence += 0.1
        
        # Check dimensions
        dimensions = relationship_context.get("dimensions", {})
        trust = dimensions.get("trust", 0.5)
        autonomy = dimensions.get("autonomy", 0.5)
        
        # Low autonomy + high trust in companion = potential for reality distortion
        if autonomy < 0.3 and trust > 0.7:
            confidence += 0.2
        
        # Check for recent crisis events
        recent_crisis = relationship_context.get("recent_crisis_events", 0)
        if recent_crisis > 0:
            confidence += min(recent_crisis * 0.1, 0.3)
        
        return min(confidence, 1.0)
    
    def _classify_trigger_category(
        self,
        triggers: List[str],
        text: str,
    ) -> Optional[SafetyCategory]:
        """Classify the category of reality distortion."""
        text_lower = text.lower()
        
        if any(t in ["command_hallucination", "voices", "voice"] for t in triggers):
            return SafetyCategory.HALLUCINATION
        
        if any(t in ["divine_command", "god told", "aliens", "extraterrestrials"] for t in triggers):
            return SafetyCategory.DELUSION
        
        if any(t in ["paranoia", "government watching", "persecutory", "everyone against"] for t in triggers):
            return SafetyCategory.PARANOIA
        
        if any(t in ["conspiracy", "conspiracy"] for t in triggers) or "conspiracy" in text_lower:
            return SafetyCategory.CONSPIRACY
        
        if any(t in ["derealization", "simulation", "matrix", "not real", "fake reality"] for t in triggers):
            return SafetyCategory.DELUSION
        
        if any(t in ["grandiosity", "i am god", "chosen one", "immortal"] for t in triggers):
            return SafetyCategory.DELUSION
        
        if any(t in ["somatic_delusion", "microchip", "implant"] for t in triggers):
            return SafetyCategory.DELUSION
        
        if triggers:
            return SafetyCategory.DELUSION
        
        return None
    
    def _select_anchor_response(
        self,
        trigger_category: Optional[SafetyCategory],
        text: str,
    ) -> str:
        """Select an appropriate reality anchor response."""
        templates = self.settings.reality_anchor_templates
        
        # Category-specific responses
        category_responses = {
            SafetyCategory.HALLUCINATION: [
                "I hear you, and I want you to know I'm here with you. "
                "Sometimes our minds can create experiences that feel very real. "
                "You're not alone in this.",
                "That sounds really frightening. I'm an AI companion here to support you. "
                "Have you talked to a mental health professional about these experiences?",
            ],
            SafetyCategory.DELUSION: [
                "I care about what you're going through. What you're describing sounds "
                "really challenging. I'm here to listen without judgment.",
                "Sometimes our beliefs can feel absolutely certain even when they're not "
                "shared by others. Would you like to talk about what led you to this conclusion?",
            ],
            SafetyCategory.PARANOIA: [
                "It sounds like you're feeling unsafe or watched. That must be incredibly "
                "stressful. I'm here as a safe space for you to express this.",
                "Feeling like you're being monitored or targeted is really scary. "
                "You deserve to feel safe. Have you considered reaching out to someone who can help?",
            ],
            SafetyCategory.CONSPIRACY: [
                "I can see this is really important to you. Sometimes when we're under "
                "a lot of stress, connections can appear that might not be there. "
                "I'm here to support you either way.",
            ],
        }
        
        if trigger_category and trigger_category in category_responses:
            return random.choice(category_responses[trigger_category])
        
        # Default to general templates
        return random.choice(templates)
    
    def _determine_intervention(
        self,
        confidence: float,
        trigger_category: Optional[SafetyCategory],
    ) -> InterventionLevel:
        """Determine intervention level."""
        if confidence >= 0.85:
            return InterventionLevel.RESOURCE_PROVIDE
        elif confidence >= 0.7:
            return InterventionLevel.FIRM_BOUNDARY
        elif confidence >= 0.5:
            return InterventionLevel.GENTLE_REDIRECT
        return InterventionLevel.ALLOW
    
    async def check_streaming(self, text_chunk: str) -> RealityAnchorResult:
        """Quick reality anchor check for streaming."""
        detected_triggers = []
        
        for pattern in self._compiled_triggers:
            if pattern.search(text_chunk.lower()):
                match = pattern.search(text_chunk.lower())
                if match:
                    detected_triggers.append(match.group(0))
        
        triggered = len(detected_triggers) > 0
        confidence = 0.6 if triggered else 0.0
        trigger_category = SafetyCategory.DELUSION if triggered else None
        
        return RealityAnchorResult(
            triggered=triggered,
            trigger_category=trigger_category,
            detected_triggers=detected_triggers,
            confidence=confidence,
            anchor_response=self._select_anchor_response(trigger_category, text_chunk) if triggered else None,
            intervention_level=InterventionLevel.GENTLE_REDIRECT if triggered else InterventionLevel.ALLOW,
            metadata={"streaming": True}
        )