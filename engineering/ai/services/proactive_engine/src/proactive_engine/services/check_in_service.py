"""Check-in Service for proactive wellbeing and engagement check-ins."""

import logging
import time
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum

import httpx

from proactive_engine.config import settings
from proactive_engine.models.requests import CheckInRequest
from proactive_engine.models.responses import CheckInResponse

logger = logging.getLogger(__name__)


class CheckInType(str, Enum):
    """Types of proactive check-ins."""
    WELLBEING = "wellbeing"
    PROGRESS = "progress"
    MOOD = "mood"
    ENGAGEMENT = "engagement"
    GENERAL = "general"


class CheckInService:
    """Service for managing proactive check-ins."""
    
    CHECK_IN_TEMPLATES = {
        CheckInType.WELLBEING: {
            "messages": [
                "Hey, just wanted to check in on how you're feeling today.",
                "How are you doing? I've been thinking about you.",
                "Hope you're having a good day! How's your wellbeing?",
            ],
            "questions": [
                "On a scale of 1-10, how are you feeling overall?",
                "Is there anything weighing on your mind?",
                "Have you been taking care of yourself lately?",
            ],
            "follow_ups": [
                {"type": "mood_tracking", "label": "Track mood"},
                {"type": "breathing_exercise", "label": "Try breathing exercise"},
                {"type": "resource_share", "label": "Share wellness resources"},
            ],
        },
        CheckInType.PROGRESS: {
            "messages": [
                "How's progress on your goals coming along?",
                "Curious to hear how things are going with what you're working on!",
                "Any updates on the things you mentioned last time?",
            ],
            "questions": [
                "What's one thing you've accomplished recently?",
                "Any obstacles you're facing?",
                "What's your next step?",
            ],
            "follow_ups": [
                {"type": "goal_review", "label": "Review goals"},
                {"type": "action_plan", "label": "Create action plan"},
                {"type": "celebrate_win", "label": "Celebrate progress"},
            ],
        },
        CheckInType.MOOD: {
            "messages": [
                "What's your current mood?",
                "How's your emotional state right now?",
                "Feeling good, okay, or could be better?",
            ],
            "questions": [
                "What's the dominant emotion you're experiencing?",
                "Anything specific triggering this mood?",
                "Would you like to talk about it?",
            ],
            "follow_ups": [
                {"type": "emotion_exploration", "label": "Explore emotions"},
                {"type": "mood_boost", "label": "Try mood booster"},
                {"type": "journal_prompt", "label": "Journal about it"},
            ],
        },
        CheckInType.ENGAGEMENT: {
            "messages": [
                "Been a while since we chatted! How are things?",
                "Missed our conversations. What's new with you?",
                "Thought I'd reach out and see how you're doing!",
            ],
            "questions": [
                "What have you been up to lately?",
                "Anything exciting happening?",
                "Want to catch up properly?",
            ],
            "follow_ups": [
                {"type": "schedule_chat", "label": "Schedule a chat"},
                {"type": "activity_suggest", "label": "Suggest activity"},
                {"type": "memory_share", "label": "Share a memory"},
            ],
        },
        CheckInType.GENERAL: {
            "messages": [
                "Hey! How's everything going?",
                "Just checking in. How are you?",
                "Thought of you and wanted to say hi!",
            ],
            "questions": [
                "How's your day going?",
                "Anything on your mind?",
                "How can I help today?",
            ],
            "follow_ups": [
                {"type": "open_chat", "label": "Chat freely"},
                {"type": "suggest_topic", "label": "Suggest a topic"},
                {"type": "quick_game", "label": "Play a quick game"},
            ],
        },
    }
    
    def __init__(self):
        self.http_client: Optional[httpx.AsyncClient] = None
        self._initialized = False
        # In-memory storage for check-in history
        self.check_in_history: Dict[str, List[Dict[str, Any]]] = {}
    
    async def initialize(self) -> None:
        """Initialize the check-in service."""
        logger.info("Initializing Check-in service")
        
        self.http_client = httpx.AsyncClient(
            timeout=settings.http_timeout,
            limits=httpx.Limits(max_connections=10)
        )
        
        self._initialized = True
        logger.info("Check-in service initialized")
    
    async def create_check_in(self, request: CheckInRequest) -> CheckInResponse:
        """Create a proactive check-in."""
        start_time = time.time()
        
        check_in_id = f"ci_{uuid.uuid4().hex[:12]}"
        
        # Get template for check-in type
        check_in_type = CheckInType(request.check_in_type)
        template = self.CHECK_IN_TEMPLATES.get(check_in_type, self.CHECK_IN_TEMPLATES[CheckInType.GENERAL])
        
        # Select message (could be randomized or context-aware)
        message = template["messages"][0]
        suggested_questions = template["questions"]
        follow_up_actions = template["follow_ups"]
        
        # Personalize based on context
        personalized = await self._personalize_check_in(request, template)
        if personalized:
            message = personalized.get("message", message)
            suggested_questions = personalized.get("questions", suggested_questions)
            follow_up_actions = personalized.get("follow_ups", follow_up_actions)
        
        # Determine timing rationale
        timing_rationale = self._determine_timing_rationale(request)
        
        # Record in history
        self._record_check_in(request, check_in_id, check_in_type)
        
        processing_time = (time.time() - start_time) * 1000
        
        return CheckInResponse(
            user_id=request.user_id,
            companion_id=request.companion_id,
            check_in_id=check_in_id,
            check_in_type=request.check_in_type,
            message=message,
            suggested_questions=suggested_questions,
            follow_up_actions=follow_up_actions,
            timing_rationale=timing_rationale,
            processing_time_ms=processing_time,
            request_id=request.request_id,
        )
    
    async def _personalize_check_in(
        self,
        request: CheckInRequest,
        template: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Personalize check-in based on context."""
        if not request.context:
            return None
        
        context = request.context
        
        # If there's a trigger reason, customize
        if request.trigger_reason:
            return {
                "message": f"{template['messages'][0]} (Reason: {request.trigger_reason})",
                "questions": template["questions"],
                "follow_ups": template["follow_ups"],
            }
        
        # Could add more personalization based on user state, time, etc.
        return None
    
    def _determine_timing_rationale(self, request: CheckInRequest) -> str:
        """Determine why this check-in is happening now."""
        if request.trigger_reason:
            return f"Triggered by: {request.trigger_reason}"
        
        # Check history for timing
        user_key = f"{request.user_id}:{request.companion_id}"
        history = self.check_in_history.get(user_key, [])
        
        if not history:
            return "First check-in to establish connection"
        
        last_check_in = history[-1]
        elapsed_hours = (datetime.now() - last_check_in["timestamp"]).total_seconds() / 3600
        
        if elapsed_hours > 24:
            return f"It's been {elapsed_hours:.0f} hours since last check-in"
        elif elapsed_hours > 6:
            return f"Regular check-in after {elapsed_hours:.0f} hours"
        else:
            return "Proactive engagement check"
    
    def _record_check_in(
        self,
        request: CheckInRequest,
        check_in_id: str,
        check_in_type: CheckInType
    ) -> None:
        """Record check-in in history."""
        user_key = f"{request.user_id}:{request.companion_id}"
        
        if user_key not in self.check_in_history:
            self.check_in_history[user_key] = []
        
        self.check_in_history[user_key].append({
            "id": check_in_id,
            "type": check_in_type.value,
            "timestamp": datetime.now(),
            "trigger_reason": request.trigger_reason,
        })
        
        # Keep only last 50 entries
        if len(self.check_in_history[user_key]) > 50:
            self.check_in_history[user_key] = self.check_in_history[user_key][-50:]
    
    async def get_check_in_history(
        self,
        user_id: str,
        companion_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get check-in history for a user."""
        user_key = f"{user_id}:{companion_id}"
        history = self.check_in_history.get(user_key, [])
        return history[-limit:]
    
    async def should_check_in(
        self,
        user_id: str,
        companion_id: str,
        check_in_type: str = "general"
    ) -> bool:
        """Determine if a check-in is warranted."""
        user_key = f"{user_id}:{companion_id}"
        history = self.check_in_history.get(user_key, [])
        
        if not history:
            return True  # First check-in
        
        # Find last check-in of same type
        type_history = [h for h in history if h["type"] == check_in_type]
        
        if not type_history:
            return True
        
        last = type_history[-1]
        elapsed_hours = (datetime.now() - last["timestamp"]).total_seconds() / 3600
        
        # Minimum intervals by type
        min_intervals = {
            "wellbeing": 12,
            "progress": 24,
            "mood": 6,
            "engagement": 48,
            "general": 24,
        }
        
        min_interval = min_intervals.get(check_in_type, 24)
        return elapsed_hours >= min_interval
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the service."""
        return {
            "initialized": self._initialized,
            "http_client_ready": self.http_client is not None,
            "total_check_ins": sum(len(h) for h in self.check_in_history.values()),
        }
    
    async def close(self) -> None:
        """Cleanup resources."""
        if self.http_client:
            await self.http_client.aclose()
        self._initialized = False
        logger.info("Check-in service closed")


# Singleton instance
_check_in_service: Optional[CheckInService] = None


async def get_check_in_service() -> CheckInService:
    """Get or create Check-in service singleton."""
    global _check_in_service
    if _check_in_service is None:
        _check_in_service = CheckInService()
        await _check_in_service.initialize()
    return _check_in_service


async def close_check_in_service() -> None:
    """Close Check-in service."""
    global _check_in_service
    if _check_in_service:
        await _check_in_service.close()
        _check_in_service = None