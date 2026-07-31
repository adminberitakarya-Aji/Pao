"""Suggestion Service for generating personalized proactive suggestions."""

import logging
import time
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime

import httpx

from proactive_engine.config import settings
from proactive_engine.models.requests import SuggestionRequest
from proactive_engine.models.responses import SuggestionResponse

logger = logging.getLogger(__name__)


class SuggestionService:
    """Service for generating personalized proactive suggestions."""
    
    SUGGESTION_TYPES = [
        "activity",
        "conversation",
        "content",
        "action",
        "learning",
    ]
    
    ACTIVITY_SUGGESTIONS = {
        "game": [
            "Play a quick word game",
            "Try a trivia challenge",
            "Play 20 questions",
        ],
        "learning": [
            "Learn a new word in a foreign language",
            "Read an interesting article together",
            "Watch a short educational video",
        ],
        "creative": [
            "Write a short story together",
            "Draw something collaborative",
            "Create a playlist",
        ],
        "relaxation": [
            "Try a breathing exercise",
            "Listen to calming music",
            "Do a quick stretch",
        ],
        "social": [
            "Share a favorite memory",
            "Discuss a hypothetical scenario",
            "Plan a virtual activity",
        ],
    }
    
    def __init__(self):
        self.http_client: Optional[httpx.AsyncClient] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the suggestion service."""
        logger.info("Initializing Suggestion service")
        
        self.http_client = httpx.AsyncClient(
            timeout=settings.http_timeout,
            limits=httpx.Limits(max_connections=10)
        )
        
        self._initialized = True
        logger.info("Suggestion service initialized")
    
    async def generate_suggestions(self, request: SuggestionRequest) -> SuggestionResponse:
        """Generate personalized suggestions."""
        start_time = time.time()
        
        # Gather context
        context = await self._gather_context(request)
        
        # Generate suggestions based on type
        if request.suggestion_type == "activity":
            suggestions = self._generate_activity_suggestions(request, context)
        elif request.suggestion_type == "conversation":
            suggestions = self._generate_conversation_suggestions(request, context)
        elif request.suggestion_type == "content":
            suggestions = self._generate_content_suggestions(request, context)
        elif request.suggestion_type == "action":
            suggestions = self._generate_action_suggestions(request, context)
        elif request.suggestion_type == "learning":
            suggestions = self._generate_learning_suggestions(request, context)
        else:
            suggestions = self._generate_activity_suggestions(request, context)
        
        # Personalize and rank
        personalized = self._personalize_suggestions(suggestions, request, context)
        
        # Limit results
        final_suggestions = personalized[:request.max_suggestions]
        
        processing_time = (time.time() - start_time) * 1000
        
        return SuggestionResponse(
            user_id=request.user_id,
            companion_id=request.companion_id,
            suggestions=final_suggestions,
            suggestion_type=request.suggestion_type,
            context_used=context.get("summary", {}),
            personalization_score=self._calculate_personalization_score(final_suggestions, context),
            processing_time_ms=processing_time,
            request_id=request.request_id,
        )
    
    async def _gather_context(self, request: SuggestionRequest) -> Dict[str, Any]:
        """Gather context from various sources."""
        context = {"summary": {}}
        
        # User preferences
        context["preferences"] = request.user_interests or []
        
        # Current context
        context["current"] = request.context or {}
        
        # Get identity context
        try:
            if self.http_client:
                identity_resp = await self.http_client.get(
                    f"{settings.identity_engine_url}/api/v1/users/{request.user_id}"
                )
                if identity_resp.status_code == 200:
                    identity_data = identity_resp.json()
                    context["identity"] = identity_data
                    context["summary"]["relationship_phase"] = identity_data.get("relationship_phase", "discovery")
                    context["summary"]["interests"] = identity_data.get("interests", [])
        except Exception as e:
            logger.warning("Failed to get identity context", error=str(e))
        
        # Get memory context
        try:
            if self.http_client:
                memory_resp = await self.http_client.get(
                    f"{settings.memory_engine_url}/api/v1/context/{request.user_id}/{request.companion_id}",
                    params={"limit": 20}
                )
                if memory_resp.status_code == 200:
                    memory_data = memory_resp.json()
                    context["memory"] = memory_data
                    context["summary"]["recent_topics"] = memory_data.get("recent_topics", [])
        except Exception as e:
            logger.warning("Failed to get memory context", error=str(e))
        
        return context
    
    def _generate_activity_suggestions(
        self,
        request: SuggestionRequest,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate activity suggestions."""
        suggestions = []
        
        # Get user interests
        interests = set(request.user_interests or [])
        identity_interests = set(context.get("identity", {}).get("interests", []))
        all_interests = interests.union(identity_interests)
        
        # Map interests to activity categories
        interest_to_category = {
            "games": "game",
            "learning": "learning",
            "creativity": "creative",
            "art": "creative",
            "music": "creative",
            "relaxation": "relaxation",
            "wellness": "relaxation",
            "social": "social",
            "chatting": "social",
        }
        
        preferred_categories = set()
        for interest in all_interests:
            category = interest_to_category.get(interest.lower())
            if category:
                preferred_categories.add(category)
        
        # If no specific preferences, use all categories
        if not preferred_categories:
            preferred_categories = set(self.ACTIVITY_SUGGESTIONS.keys())
        
        # Generate suggestions from preferred categories
        for category in preferred_categories:
            activities = self.ACTIVITY_SUGGESTIONS.get(category, [])
            for activity in activities[:2]:  # Max 2 per category
                suggestions.append({
                    "id": f"sugg_{category}_{activity[:20]}",
                    "title": activity,
                    "category": category,
                    "description": f"A {category} activity: {activity}",
                    "duration_minutes": self._estimate_duration(category),
                    "energy_level": self._estimate_energy(category),
                    "tags": [category],
                })
        
        return suggestions
    
    def _generate_conversation_suggestions(
        self,
        request: SuggestionRequest,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate conversation starter suggestions."""
        suggestions = []
        
        recent_topics = context.get("summary", {}).get("recent_topics", [])
        
        # Topic-based conversation starters
        topic_starters = {
            "travel": "What's the most memorable place you've visited?",
            "food": "What's your all-time favorite meal?",
            "books": "Read any good books lately?",
            "movies": "Seen any great movies recently?",
            "hobbies": "What do you like to do for fun?",
            "work": "How's work been treating you?",
            "goals": "Working on any interesting goals right now?",
            "dreams": "If you could master any skill instantly, what would it be?",
        }
        
        for topic in recent_topics[:3]:
            starter = topic_starters.get(topic.lower())
            if starter:
                suggestions.append({
                    "id": f"conv_{topic}",
                    "title": f"Continue talking about {topic}",
                    "category": "conversation",
                    "description": starter,
                    "conversation_starter": starter,
                    "topic": topic,
                    "tags": ["conversation", topic],
                })
        
        # General conversation starters
        general_starters = [
            "What made you smile today?",
            "What's something you're looking forward to?",
            "What's a random thought you had recently?",
            "If you could have dinner with anyone, who would it be?",
        ]
        
        for i, starter in enumerate(general_starters[:3]):
            suggestions.append({
                "id": f"conv_general_{i}",
                "title": "Casual conversation",
                "category": "conversation",
                "description": starter,
                "conversation_starter": starter,
                "topic": "general",
                "tags": ["conversation", "casual"],
            })
        
        return suggestions
    
    def _generate_content_suggestions(
        self,
        request: SuggestionRequest,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate content sharing suggestions."""
        suggestions = []
        
        interests = context.get("summary", {}).get("interests", [])
        
        content_types = {
            "article": "Interesting article",
            "video": "Short video",
            "podcast": "Podcast episode",
            "music": "Song or playlist",
            "tool": "Useful tool/app",
        }
        
        for content_type, label in content_types.items():
            for interest in interests[:2]:
                suggestions.append({
                    "id": f"content_{content_type}_{interest}",
                    "title": f"{label} about {interest}",
                    "category": "content",
                    "description": f"A {content_type} related to {interest}",
                    "content_type": content_type,
                    "topic": interest,
                    "tags": ["content", content_type, interest],
                })
        
        return suggestions[:request.max_suggestions]
    
    def _generate_action_suggestions(
        self,
        request: SuggestionRequest,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate actionable suggestions."""
        suggestions = [
            {
                "id": "action_goal",
                "title": "Set a micro-goal for today",
                "category": "action",
                "description": "Pick one small thing to accomplish",
                "action_type": "set_goal",
                "tags": ["productivity", "goals"],
            },
            {
                "id": "action_break",
                "title": "Take a 5-minute break",
                "category": "action",
                "description": "Step away and recharge",
                "action_type": "take_break",
                "tags": ["wellness", "break"],
            },
            {
                "id": "action_connect",
                "title": "Reach out to someone",
                "category": "action",
                "description": "Send a quick message to a friend",
                "action_type": "social_connect",
                "tags": ["social", "connection"],
            },
        ]
        
        return suggestions
    
    def _generate_learning_suggestions(
        self,
        request: SuggestionRequest,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate learning suggestions."""
        suggestions = []
        
        interests = context.get("summary", {}).get("interests", [])
        
        learning_resources = {
            "language": "Practice a language for 10 minutes",
            "coding": "Learn a new coding concept",
            "science": "Watch a science explainer",
            "history": "Read about a historical event",
            "psychology": "Learn a psychology insight",
            "philosophy": "Explore a philosophical idea",
        }
        
        for interest in interests[:3]:
            resource = learning_resources.get(interest.lower())
            if resource:
                suggestions.append({
                    "id": f"learn_{interest}",
                    "title": f"Learn about {interest}",
                    "category": "learning",
                    "description": resource,
                    "topic": interest,
                    "estimated_time_minutes": 15,
                    "tags": ["learning", interest],
                })
        
        return suggestions
    
    def _personalize_suggestions(
        self,
        suggestions: List[Dict[str, Any]],
        request: SuggestionRequest,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Personalize and rank suggestions."""
        # Add personalization scores
        for suggestion in suggestions:
            score = 0.5  # Base score
            
            # Boost for matching interests
            tags = suggestion.get("tags", [])
            user_interests = set(request.user_interests or [])
            interest_matches = len(set(tags).intersection(user_interests))
            score += interest_matches * 0.15
            
            # Boost for recent topics
            recent_topics = context.get("summary", {}).get("recent_topics", [])
            topic_matches = len(set(tags).intersection(set(recent_topics)))
            score += topic_matches * 0.1
            
            # Boost for relationship phase
            phase = context.get("summary", {}).get("relationship_phase", "discovery")
            phase_boost = {
                "discovery": 0.2,
                "building": 0.15,
                "deepening": 0.1,
                "intimate": 0.05,
                "maintenance": 0.1,
            }
            score += phase_boost.get(phase, 0)
            
            suggestion["personalization_score"] = min(score, 1.0)
        
        # Sort by personalization score
        suggestions.sort(key=lambda x: x.get("personalization_score", 0), reverse=True)
        
        return suggestions
    
    def _calculate_personalization_score(
        self,
        suggestions: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> float:
        """Calculate overall personalization score."""
        if not suggestions:
            return 0.0
        
        scores = [s.get("personalization_score", 0.5) for s in suggestions]
        return sum(scores) / len(scores)
    
    def _estimate_duration(self, category: str) -> int:
        """Estimate activity duration in minutes."""
        durations = {
            "game": 10,
            "learning": 15,
            "creative": 20,
            "relaxation": 5,
            "social": 15,
        }
        return durations.get(category, 10)
    
    def _estimate_energy(self, category: str) -> str:
        """Estimate energy level required."""
        energy = {
            "game": "medium",
            "learning": "medium",
            "creative": "high",
            "relaxation": "low",
            "social": "medium",
        }
        return energy.get(category, "medium")
    
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
        logger.info("Suggestion service closed")


# Singleton instance
_suggestion_service: Optional[SuggestionService] = None


async def get_suggestion_service() -> SuggestionService:
    """Get or create Suggestion service singleton."""
    global _suggestion_service
    if _suggestion_service is None:
        _suggestion_service = SuggestionService()
        await _suggestion_service.initialize()
    return _suggestion_service


async def close_suggestion_service() -> None:
    """Close Suggestion service."""
    global _suggestion_service
    if _suggestion_service:
        await _suggestion_service.close()
        _suggestion_service = None