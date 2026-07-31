"""Initiative Service for detecting and generating proactive initiatives."""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timedelta

import httpx

from proactive_engine.config import settings
from proactive_engine.models.requests import InitiativeRequest, ProactiveActionRequest
from proactive_engine.models.responses import InitiativeResponse, ProactiveActionResponse

logger = logging.getLogger(__name__)


class InitiativeService:
    """Service for detecting and generating proactive initiatives."""
    
    INITIATIVE_TYPES = [
        "conversation_start",
        "activity_suggestion", 
        "check_in",
        "reminder",
        "content_share",
        "learning_prompt",
        "support_offer",
    ]
    
    def __init__(self):
        self.http_client: Optional[httpx.AsyncClient] = None
        self._initialized = False
        self.initiative_history: Dict[str, List[Dict[str, Any]]] = {}
    
    async def initialize(self) -> None:
        """Initialize the initiative service."""
        logger.info("Initializing Initiative service")
        
        self.http_client = httpx.AsyncClient(
            timeout=settings.http_timeout,
            limits=httpx.Limits(max_connections=10)
        )
        
        self._initialized = True
        logger.info("Initiative service initialized")
    
    async def detect_initiative(self, request: InitiativeRequest) -> InitiativeResponse:
        """Detect if proactive initiative is warranted."""
        start_time = time.time()
        
        user_key = f"{request.user_id}:{request.companion_id}"
        
        # Check cooldown
        if not self._check_cooldown(user_key, request.initiative_type):
            return InitiativeResponse(
                user_id=request.user_id,
                companion_id=request.companion_id,
                initiative_detected=False,
                confidence=0.0,
                reasoning="In cooldown period",
                processing_time_ms=(time.time() - start_time) * 1000,
                request_id=request.request_id,
            )
        
        # Get context from other engines
        context = await self._gather_context(request)
        
        # Analyze initiative opportunity
        initiative_result = await self._analyze_initiative_opportunity(
            request, context
        )
        
        # Record initiative
        if initiative_result["initiative_detected"]:
            self._record_initiative(user_key, initiative_result)
        
        processing_time = (time.time() - start_time) * 1000
        
        return InitiativeResponse(
            user_id=request.user_id,
            companion_id=request.companion_id,
            initiative_detected=initiative_result["initiative_detected"],
            initiative_type=initiative_result.get("initiative_type"),
            confidence=initiative_result.get("confidence", 0.0),
            reasoning=initiative_result.get("reasoning", ""),
            suggested_action=initiative_result.get("suggested_action"),
            timing=initiative_result.get("timing", "soon"),
            processing_time_ms=processing_time,
            request_id=request.request_id,
        )
    
    async def execute_proactive_action(self, request: ProactiveActionRequest) -> ProactiveActionResponse:
        """Execute a proactive action."""
        start_time = time.time()
        
        action_id = f"action_{int(time.time() * 1000)}"
        
        # Validate action type
        if request.action_type not in self.INITIATIVE_TYPES:
            return ProactiveActionResponse(
                user_id=request.user_id,
                companion_id=request.companion_id,
                action_id=action_id,
                action_type=request.action_type,
                status="failed",
                message=f"Unknown action type: {request.action_type}",
                processing_time_ms=(time.time() - start_time) * 1000,
                request_id=request.request_id,
            )
        
        # Check if confirmation required
        confirmation_required = request.parameters.get("require_confirmation", False)
        
        if confirmation_required:
            return ProactiveActionResponse(
                user_id=request.user_id,
                companion_id=request.companion_id,
                action_id=action_id,
                action_type=request.action_type,
                status="pending_confirmation",
                confirmation_required=True,
                message="Action requires user confirmation",
                processing_time_ms=(time.time() - start_time) * 1000,
                request_id=request.request_id,
            )
        
        # Execute action based on type
        result = await self._execute_action(request.action_type, request.parameters)
        
        processing_time = (time.time() - start_time) * 1000
        
        return ProactiveActionResponse(
            user_id=request.user_id,
            companion_id=request.companion_id,
            action_id=action_id,
            action_type=request.action_type,
            status="executed" if result.get("success") else "failed",
            result=result,
            message=result.get("message"),
            processing_time_ms=processing_time,
            request_id=request.request_id,
        )
    
    async def _gather_context(self, request: InitiativeRequest) -> Dict[str, Any]:
        """Gather context from other engines."""
        context = {}
        
        try:
            # Get user identity/preferences
            if self.http_client:
                identity_resp = await self.http_client.get(
                    f"{settings.identity_engine_url}/api/v1/users/{request.user_id}"
                )
                if identity_resp.status_code == 200:
                    context["identity"] = identity_resp.json()
        except Exception as e:
            logger.warning("Failed to get identity context", error=str(e))
        
        try:
            # Get memory context
            if self.http_client:
                memory_resp = await self.http_client.get(
                    f"{settings.memory_engine_url}/api/v1/context/{request.user_id}/{request.companion_id}",
                    params={"limit": settings.context_window_size}
                )
                if memory_resp.status_code == 200:
                    context["memory"] = memory_resp.json()
        except Exception as e:
            logger.warning("Failed to get memory context", error=str(e))
        
        try:
            # Get emotion context
            if self.http_client:
                emotion_resp = await self.http_client.get(
                    f"{settings.emotion_engine_url}/api/v1/emotion/state/{request.user_id}/{request.companion_id}"
                )
                if emotion_resp.status_code == 200:
                    context["emotion"] = emotion_resp.json()
        except Exception as e:
            logger.warning("Failed to get emotion context", error=str(e))
        
        return context
    
    async def _analyze_initiative_opportunity(
        self,
        request: InitiativeRequest,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze whether to take proactive initiative."""
        
        # Base factors
        factors = {
            "time_since_interaction": self._calculate_time_factor(context),
            "user_receptiveness": self._calculate_receptiveness(context),
            "context_relevance": self._calculate_relevance(request, context),
            "emotion_state": self._analyze_emotion_state(context),
            "relationship_phase": self._get_relationship_phase(context),
        }
        
        # Calculate composite score
        weights = {
            "time_since_interaction": 0.25,
            "user_receptiveness": 0.30,
            "context_relevance": 0.20,
            "emotion_state": 0.15,
            "relationship_phase": 0.10,
        }
        
        score = sum(factors[k] * weights[k] for k in weights)
        
        # Apply proactivity level modifier
        score *= settings.proactivity_level
        
        # Check threshold
        if score < settings.trigger_threshold:
            return {
                "initiative_detected": False,
                "confidence": score,
                "reasoning": f"Opportunity score {score:.2f} below threshold {settings.trigger_threshold}",
            }
        
        # Determine initiative type
        initiative_type = self._select_initiative_type(factors, context)
        
        # Generate suggested action
        suggested_action = self._generate_suggested_action(initiative_type, context)
        
        # Determine timing
        timing = self._determine_timing(factors)
        
        return {
            "initiative_detected": True,
            "initiative_type": initiative_type,
            "confidence": min(score, 1.0),
            "reasoning": f"Initiative opportunity detected: {initiative_type} (score: {score:.2f})",
            "suggested_action": suggested_action,
            "timing": timing,
        }
    
    def _calculate_time_factor(self, context: Dict[str, Any]) -> float:
        """Calculate time since last interaction factor."""
        # Placeholder - would use actual last interaction time
        memory = context.get("memory", {})
        last_interaction = memory.get("last_interaction_hours_ago", 24)
        
        if last_interaction < 1:
            return 0.3  # Very recent, less need
        elif last_interaction < 6:
            return 0.6
        elif last_interaction < 24:
            return 0.8
        else:
            return 1.0  # Long time, high need
    
    def _calculate_receptiveness(self, context: Dict[str, Any]) -> float:
        """Calculate user receptiveness to proactive contact."""
        identity = context.get("identity", {})
        preferences = identity.get("preferences", {})
        
        proactivity_pref = preferences.get("proactivity_level", 0.5)
        contact_frequency = preferences.get("contact_frequency", "medium")
        
        freq_scores = {"low": 0.4, "medium": 0.7, "high": 0.9}
        
        return (proactivity_pref + freq_scores.get(contact_frequency, 0.7)) / 2
    
    def _calculate_relevance(self, request: InitiativeRequest, context: Dict[str, Any]) -> float:
        """Calculate context relevance for initiative."""
        # Check if there are relevant topics, events, etc.
        memory = context.get("memory", {})
        relevant_topics = memory.get("recent_topics", [])
        upcoming_events = memory.get("upcoming_events", [])
        
        relevance = 0.5  # Base
        
        if relevant_topics:
            relevance += 0.2
        if upcoming_events:
            relevance += 0.3
        
        return min(relevance, 1.0)
    
    def _analyze_emotion_state(self, context: Dict[str, Any]) -> float:
        """Analyze emotional state for initiative timing."""
        emotion = context.get("emotion", {})
        
        valence = emotion.get("valence", 0)
        arousal = emotion.get("arousal", 0.5)
        dominant = emotion.get("dominant_emotion", "neutral")
        
        # Positive valence and moderate arousal = good for initiative
        if valence > 0.2 and arousal < 0.7:
            return 0.9
        elif valence > -0.2:
            return 0.7
        elif dominant in ["sadness", "fear"]:
            return 0.8  # Good for support_offer
        else:
            return 0.4
    
    def _get_relationship_phase(self, context: Dict[str, Any]) -> float:
        """Get relationship phase factor."""
        identity = context.get("identity", {})
        phase = identity.get("relationship_phase", "discovery")
        
        phase_scores = {
            "discovery": 0.9,
            "building": 0.8,
            "deepening": 0.7,
            "intimate": 0.6,
            "maintenance": 0.5,
        }
        
        return phase_scores.get(phase, 0.5)
    
    def _select_initiative_type(
        self,
        factors: Dict[str, float],
        context: Dict[str, Any]
    ) -> str:
        """Select the most appropriate initiative type."""
        emotion = context.get("emotion", {})
        dominant = emotion.get("dominant_emotion", "neutral")
        valence = emotion.get("valence", 0)
        
        # Emotion-based selection
        if dominant in ["sadness", "fear", "anxiety"]:
            return "support_offer"
        elif dominant in ["boredom", "neutral"] and valence > -0.1:
            return "activity_suggestion"
        elif valence > 0.3:
            return "content_share"
        
        # Time-based selection
        time_factor = factors.get("time_since_interaction", 0.5)
        if time_factor > 0.8:
            return "check_in"
        elif time_factor > 0.5:
            return "conversation_start"
        
        # Default
        return "conversation_start"
    
    def _generate_suggested_action(
        self,
        initiative_type: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate suggested action for initiative type."""
        actions = {
            "conversation_start": {
                "type": "send_message",
                "content": "Hey! I was thinking about you. How's your day going?",
                "tone": "casual",
            },
            "activity_suggestion": {
                "type": "suggest_activity",
                "content": "Would you like to try something new today? I have a few ideas!",
                "options": ["game", "learning", "creative", "relaxation"],
            },
            "check_in": {
                "type": "check_in",
                "content": "Just wanted to check in and see how you're doing.",
                "follow_up": True,
            },
            "reminder": {
                "type": "set_reminder",
                "content": "Don't forget about your goal!",
            },
            "content_share": {
                "type": "share_content",
                "content": "I found something I think you'd enjoy!",
            },
            "learning_prompt": {
                "type": "learning_prompt",
                "content": "Want to learn something new together?",
            },
            "support_offer": {
                "type": "offer_support",
                "content": "I'm here if you need anything. Want to talk about it?",
            },
        }
        
        return actions.get(initiative_type, actions["conversation_start"])
    
    def _determine_timing(self, factors: Dict[str, float]) -> str:
        """Determine timing for initiative."""
        time_factor = factors.get("time_since_interaction", 0.5)
        receptiveness = factors.get("user_receptiveness", 0.5)
        
        if time_factor > 0.8 and receptiveness > 0.7:
            return "immediate"
        elif time_factor > 0.5:
            return "soon"
        else:
            return "later"
    
    def _check_cooldown(self, user_key: str, initiative_type: Optional[str]) -> bool:
        """Check if user is in cooldown period."""
        history = self.initiative_history.get(user_key, [])
        
        if not history:
            return True
        
        # Check last initiative of same type
        if initiative_type:
            last_same = next(
                (h for h in reversed(history) if h.get("type") == initiative_type),
                None
            )
            if last_same:
                elapsed = time.time() - last_same["timestamp"]
                if elapsed < settings.cooldown_minutes * 60:
                    return False
        
        # Check general rate limit
        recent = [h for h in history if time.time() - h["timestamp"] < 3600]
        if len(recent) >= settings.max_proactive_actions_per_hour:
            return False
        
        return True
    
    def _record_initiative(self, user_key: str, initiative: Dict[str, Any]) -> None:
        """Record initiative in history."""
        if user_key not in self.initiative_history:
            self.initiative_history[user_key] = []
        
        self.initiative_history[user_key].append({
            "type": initiative.get("initiative_type"),
            "timestamp": time.time(),
            "confidence": initiative.get("confidence"),
        })
        
        # Keep only last 100 entries
        if len(self.initiative_history[user_key]) > 100:
            self.initiative_history[user_key] = self.initiative_history[user_key][-100:]
    
    async def _execute_action(self, action_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a proactive action."""
        # This would integrate with messaging, notification systems, etc.
        logger.info("Executing proactive action", action_type=action_type, params=parameters)
        
        return {
            "success": True,
            "message": f"Action {action_type} executed",
            "details": parameters,
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the service."""
        return {
            "initialized": self._initialized,
            "http_client_ready": self.http_client is not None,
            "history_entries": sum(len(h) for h in self.initiative_history.values()),
        }
    
    async def close(self) -> None:
        """Cleanup resources."""
        if self.http_client:
            await self.http_client.aclose()
        self._initialized = False
        logger.info("Initiative service closed")


# Singleton instance
_initiative_service: Optional[InitiativeService] = None


async def get_initiative_service() -> InitiativeService:
    """Get or create Initiative service singleton."""
    global _initiative_service
    if _initiative_service is None:
        _initiative_service = InitiativeService()
        await _initiative_service.initialize()
    return _initiative_service


async def close_initiative_service() -> None:
    """Close Initiative service."""
    global _initiative_service
    if _initiative_service:
        await _initiative_service.close()
        _initiative_service = None