"""Anticipation Service for predicting user needs and future states."""

import logging
import time
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timedelta

import httpx

from proactive_engine.config import settings
from proactive_engine.models.requests import AnticipationRequest
from proactive_engine.models.responses import AnticipationResponse

logger = logging.getLogger(__name__)


class AnticipationService:
    """Service for anticipating user needs and future states."""
    
    ANTICIPATION_CATEGORIES = [
        "informational_need",
        "emotional_support",
        "task_assistance",
        "social_connection",
        "learning_opportunity",
        "health_wellness",
        "entertainment",
        "practical_help",
    ]
    
    def __init__(self):
        self.http_client: Optional[httpx.AsyncClient] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the anticipation service."""
        logger.info("Initializing Anticipation service")
        
        self.http_client = httpx.AsyncClient(
            timeout=settings.http_timeout,
            limits=httpx.Limits(max_connections=10)
        )
        
        self._initialized = True
        logger.info("Anticipation service initialized")
    
    async def anticipate_needs(self, request: AnticipationRequest) -> AnticipationResponse:
        """Anticipate user needs based on context and history."""
        start_time = time.time()
        
        # Gather comprehensive context
        context = await self._gather_context(request)
        
        # Analyze patterns
        patterns = self._analyze_patterns(request, context)
        
        # Generate anticipations
        anticipations = self._generate_anticipations(request, context, patterns)
        
        # Rank by probability and relevance
        ranked = self._rank_anticipations(anticipations, request)
        
        processing_time = (time.time() - start_time) * 1000
        
        return AnticipationResponse(
            user_id=request.user_id,
            companion_id=request.companion_id,
            anticipations=ranked[:10],  # Top 10
            time_horizon_hours=request.time_horizon_hours,
            confidence_summary=self._summarize_confidence(ranked),
            processing_time_ms=processing_time,
            request_id=request.request_id,
        )
    
    async def _gather_context(self, request: AnticipationRequest) -> Dict[str, Any]:
        """Gather context from various sources."""
        context = {}
        
        # Recent interactions
        context["recent_interactions"] = request.recent_interactions
        
        # User preferences
        context["preferences"] = request.user_preferences or {}
        
        # Current context
        context["current_context"] = request.current_context or {}
        
        # Get memory context
        try:
            if self.http_client:
                memory_resp = await self.http_client.get(
                    f"{settings.memory_engine_url}/api/v1/context/{request.user_id}/{request.companion_id}",
                    params={"limit": 50}
                )
                if memory_resp.status_code == 200:
                    context["memory"] = memory_resp.json()
        except Exception as e:
            logger.warning("Failed to get memory context", error=str(e))
        
        # Get identity context
        try:
            if self.http_client:
                identity_resp = await self.http_client.get(
                    f"{settings.identity_engine_url}/api/v1/users/{request.user_id}"
                )
                if identity_resp.status_code == 200:
                    context["identity"] = identity_resp.json()
        except Exception as e:
            logger.warning("Failed to get identity context", error=str(e))
        
        return context
    
    def _analyze_patterns(
        self,
        request: AnticipationRequest,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze behavioral patterns."""
        interactions = request.recent_interactions
        preferences = request.user_preferences or {}
        
        patterns = {
            "topic_frequency": {},
            "time_patterns": {},
            "emotion_trends": {},
            "activity_preferences": {},
            "response_patterns": {},
        }
        
        for interaction in interactions:
            # Topic frequency
            topic = interaction.get("topic", "general")
            patterns["topic_frequency"][topic] = patterns["topic_frequency"].get(topic, 0) + 1
            
            # Time patterns
            timestamp = interaction.get("timestamp")
            if timestamp:
                hour = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).hour
                patterns["time_patterns"][hour] = patterns["time_patterns"].get(hour, 0) + 1
            
            # Activity preferences
            activity = interaction.get("activity_type")
            if activity:
                patterns["activity_preferences"][activity] = patterns["activity_preferences"].get(activity, 0) + 1
        
        return patterns
    
    def _generate_anticipations(
        self,
        request: AnticipationRequest,
        context: Dict[str, Any],
        patterns: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate anticipation predictions."""
        anticipations = []
        
        # Based on time patterns
        time_patterns = patterns.get("time_patterns", {})
        current_hour = datetime.now().hour
        
        for hour, count in time_patterns.items():
            if abs(hour - current_hour) <= 2 and count > 2:
                anticipations.append({
                    "category": "informational_need",
                    "description": f"User typically active around {hour}:00",
                    "probability": min(0.8, count / 10),
                    "time_window": f"{hour}:00-{hour+1}:00",
                    "suggested_action": "send_gentle_prompt",
                    "context": {"pattern": "time_based"},
                })
        
        # Based on topic frequency
        topic_freq = patterns.get("topic_frequency", {})
        for topic, count in topic_freq.items():
            if count > 3:
                anticipations.append({
                    "category": "informational_need",
                    "description": f"User frequently discusses {topic}",
                    "probability": min(0.7, count / 15),
                    "time_window": "next_4_hours",
                    "suggested_action": "prepare_topic_content",
                    "context": {"topic": topic, "frequency": count},
                })
        
        # Based on upcoming events from memory
        memory = context.get("memory", {})
        upcoming = memory.get("upcoming_events", [])
        
        for event in upcoming[:3]:
            anticipations.append({
                "category": "task_assistance",
                "description": f"Upcoming event: {event.get('title', 'Unknown')}",
                "probability": 0.9,
                "time_window": event.get("time", "soon"),
                "suggested_action": "offer_preparation_help",
                "context": {"event": event},
            })
        
        # Based on emotional state
        identity = context.get("identity", {})
        emotional_baseline = identity.get("emotional_baseline", {})
        
        if emotional_baseline.get("stress_level", 0) > 0.6:
            anticipations.append({
                "category": "emotional_support",
                "description": "User showing signs of elevated stress",
                "probability": 0.75,
                "time_window": "ongoing",
                "suggested_action": "offer_stress_relief",
                "context": {"stress_indicators": emotional_baseline},
            })
        
        # Based on learning interests
        interests = request.user_preferences.get("interests", []) if request.user_preferences else []
        for interest in interests[:3]:
            anticipations.append({
                "category": "learning_opportunity",
                "description": f"User interested in {interest}",
                "probability": 0.6,
                "time_window": "next_24_hours",
                "suggested_action": "suggest_learning_content",
                "context": {"interest": interest},
            })
        
        return anticipations
    
    def _rank_anticipations(
        self,
        anticipations: List[Dict[str, Any]],
        request: AnticipationRequest
    ) -> List[Dict[str, Any]]:
        """Rank anticipations by probability and relevance."""
        # Filter by relevance threshold
        filtered = [
            a for a in anticipations 
            if a.get("probability", 0) >= settings.relevance_threshold
        ]
        
        # Sort by probability descending
        filtered.sort(key=lambda x: x.get("probability", 0), reverse=True)
        
        return filtered
    
    def _summarize_confidence(self, anticipations: List[Dict[str, Any]]) -> Dict[str, float]:
        """Summarize confidence by category."""
        summary = {}
        
        for antic in anticipations:
            category = antic.get("category", "unknown")
            prob = antic.get("probability", 0)
            
            if category not in summary or prob > summary[category]:
                summary[category] = prob
        
        return summary
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the service."""
        return {
            "initialized": self._initialized,
            "http_client_ready": self.http_client is not None,
        }
    
    async def close(self) -> None:
        """Cleanup resources."""
        if self.http_client:
            await self.http_client.aclose()
        self._initialized = False
        logger.info("Anticipation service closed")


# Singleton instance
_anticipation_service: Optional[AnticipationService] = None


async def get_anticipation_service() -> AnticipationService:
    """Get or create Anticipation service singleton."""
    global _anticipation_service
    if _anticipation_service is None:
        _anticipation_service = AnticipationService()
        await _anticipation_service.initialize()
    return _anticipation_service


async def close_anticipation_service() -> None:
    """Close Anticipation service."""
    global _anticipation_service
    if _anticipation_service:
        await _anticipation_service.close()
        _anticipation_service = None