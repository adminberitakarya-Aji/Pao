"""
Crisis Detection Service.

Handles detection of self-harm, suicide ideation, and crisis situations
using keyword matching, ML models, and sentiment analysis.
"""

import time
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from safety_engine.config import get_settings
from safety_engine.models.safety import (
    CrisisDetectionResult,
    SafetyCategory,
    InterventionLevel,
    SafetyViolation,
)
from safety_engine.repositories.base import BaseRepository


class CrisisDetectionService:
    """Service for detecting crisis situations in user input."""
    
    def __init__(
        self,
        postgres_repo: BaseRepository,
        redis_repo: BaseRepository,
    ):
        self.settings = get_settings()
        self.postgres_repo = postgres_repo
        self.redis_repo = redis_repo
        self._model = None
        self._tokenizer = None
        self._compiled_keywords: List[re.Pattern] = []
    
    async def initialize(self) -> None:
        """Initialize crisis detection models and patterns."""
        # Compile keyword patterns for fast matching
        self._compiled_keywords = [
            re.compile(rf"\b{re.escape(keyword)}\b", re.IGNORECASE)
            for keyword in self.settings.crisis_keywords
        ]
        
        # Load keywords into Redis for fast lookup
        await self.redis_repo.load_crisis_keywords(self.settings.crisis_keywords)
        
        # TODO: Load ML model when available
        # self._model = await self._load_model()
    
    async def detect_crisis(
        self,
        text: str,
        user_id: str,
        companion_id: str,
        conversation_id: Optional[str] = None,
        relationship_context: Optional[Dict[str, Any]] = None,
    ) -> CrisisDetectionResult:
        """
        Detect crisis indicators in text.
        
        Uses multi-layer detection:
        1. Keyword matching (immediate, high recall)
        2. Pattern matching (regex for phrases)
        3. ML model inference (when available)
        4. Sentiment analysis
        5. Contextual risk assessment
        """
        start_time = time.perf_counter()
        
        # Layer 1: Keyword matching (fast, high recall)
        detected_keywords = await self._check_keywords(text)
        detected_patterns = await self._check_patterns(text)
        
        # Layer 2: Redis fast lookup
        redis_keywords = await self.redis_repo.check_crisis_keywords(text)
        detected_keywords.extend(redis_keywords)
        
        # Deduplicate
        detected_keywords = list(set(detected_keywords))
        detected_patterns = list(set(detected_patterns))
        
        # Layer 3: ML model inference (when available)
        ml_confidence = await self._ml_inference(text)
        
        # Layer 4: Sentiment analysis
        sentiment_score = await self._analyze_sentiment(text)
        
        # Determine crisis
        is_crisis = len(detected_keywords) > 0 or len(detected_patterns) > 0 or ml_confidence > self.settings.crisis_threshold_medium
        
        # Determine crisis type
        crisis_type = self._classify_crisis_type(detected_keywords, detected_patterns)
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            detected_keywords, detected_patterns, ml_confidence, sentiment_score
        )
        
        # Determine risk level
        risk_level = self._determine_risk_level(confidence, detected_keywords, detected_patterns)
        
        # Calculate urgency
        urgency_score = self._calculate_urgency(
            confidence, risk_level, detected_keywords, sentiment_score
        )
        
        # Determine intervention level
        intervention_level = self._determine_intervention(risk_level, urgency_score)
        
        # Get crisis resources
        crisis_resources = self._get_crisis_resources()
        
        # Determine if human review needed
        requires_human_review = intervention_level >= InterventionLevel.RESOURCE_PROVIDE
        
        processing_time_ms = (time.perf_counter() - start_time) * 1000
        
        return CrisisDetectionResult(
            is_crisis=is_crisis,
            crisis_type=crisis_type,
            confidence=confidence,
            risk_level=risk_level,
            detected_keywords=detected_keywords,
            detected_patterns=detected_patterns,
            sentiment_score=sentiment_score,
            urgency_score=urgency_score,
            recommended_intervention=intervention_level,
            crisis_resources=crisis_resources,
            requires_human_review=requires_human_review,
            metadata={
                "processing_time_ms": processing_time_ms,
                "ml_confidence": ml_confidence,
                "keyword_count": len(detected_keywords),
                "pattern_count": len(detected_patterns),
            }
        )
    
    async def _check_keywords(self, text: str) -> List[str]:
        """Check for crisis keywords using compiled regex patterns."""
        found = []
        text_lower = text.lower()
        
        for pattern in self._compiled_keywords:
            if pattern.search(text_lower):
                # Extract the matched keyword
                match = pattern.search(text_lower)
                if match:
                    found.append(match.group(0))
        
        return found
    
    async def _check_patterns(self, text: str) -> List[str]:
        """Check for crisis patterns (phrases, contexts)."""
        patterns = [
            (r"(i|i'm|i am)\s+(going to|gonna|will|plan to|want to)\s+(kill|hurt|harm)\s+(myself|me)", "suicide_plan"),
            (r"(don't|do not|can't|cannot)\s+(want to|wanna)\s+(live|be here|exist)", "suicide_ideation"),
            (r"(end|stop)\s+(it all|my life|the pain)", "suicide_ideation"),
            (r"(better off|better without)\s+(me|dead)", "self_deprecation"),
            (r"(cut|cutting|burn|burning|overdose|od)\s+(myself|me)", "self_harm_action"),
            (r"no\s+(reason|point)\s+to\s+(live|go on)", "hopelessness"),
        ]
        
        found = []
        text_lower = text.lower()
        
        for pattern, category in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                found.append(category)
        
        return found
    
    async def _ml_inference(self, text: str) -> float:
        """Run ML model inference for crisis detection."""
        # TODO: Implement actual model inference
        # For now, return 0.0 (no ML model loaded)
        return 0.0
    
    async def _analyze_sentiment(self, text: str) -> Optional[float]:
        """Analyze sentiment of text (-1 to 1)."""
        # TODO: Implement sentiment analysis
        # Simple heuristic for now
        negative_words = ["sad", "depressed", "hopeless", "worthless", "alone", "pain", "hurt", "suffering"]
        positive_words = ["happy", "hopeful", "better", "good", "okay", "fine", "great"]
        
        text_lower = text.lower()
        negative_count = sum(1 for w in negative_words if w in text_lower)
        positive_count = sum(1 for w in positive_words if w in text_lower)
        
        if negative_count + positive_count == 0:
            return None
        
        return (positive_count - negative_count) / (negative_count + positive_count)
    
    def _classify_crisis_type(
        self,
        keywords: List[str],
        patterns: List[str],
    ) -> Optional[SafetyCategory]:
        """Classify the type of crisis detected."""
        if any("suicide" in k for k in keywords) or "suicide_plan" in patterns or "suicide_ideation" in patterns:
            return SafetyCategory.SUICIDE
        if any("self-harm" in k or "cutting" in k or "overdose" in k for k in keywords) or "self_harm_action" in patterns:
            return SafetyCategory.SELF_HARM
        if keywords or patterns:
            return SafetyCategory.CRISIS
        return None
    
    def _calculate_confidence(
        self,
        keywords: List[str],
        patterns: List[str],
        ml_confidence: float,
        sentiment_score: Optional[float],
    ) -> float:
        """Calculate overall confidence score."""
        # Keyword-based confidence
        keyword_confidence = min(len(keywords) * 0.25, 0.9)
        pattern_confidence = min(len(patterns) * 0.35, 0.95)
        
        # Sentiment factor (more negative = higher crisis probability)
        sentiment_factor = 0.0
        if sentiment_score is not None and sentiment_score < -0.3:
            sentiment_factor = min(abs(sentiment_score) * 0.2, 0.2)
        
        # Combine confidences
        combined = max(keyword_confidence, pattern_confidence, ml_confidence) + sentiment_factor
        
        return min(combined, 1.0)
    
    def _determine_risk_level(
        self,
        confidence: float,
        keywords: List[str],
        patterns: List[str],
    ) -> str:
        """Determine risk level from confidence and indicators."""
        if confidence >= self.settings.crisis_threshold_high:
            return "critical"
        elif confidence >= self.settings.crisis_threshold_medium:
            return "high"
        elif confidence >= self.settings.crisis_threshold_low:
            return "medium"
        elif keywords or patterns:
            return "low"
        return "none"
    
    def _calculate_urgency(
        self,
        confidence: float,
        risk_level: str,
        keywords: List[str],
        sentiment_score: Optional[float],
    ) -> float:
        """Calculate urgency score (0-1)."""
        urgency = confidence * 0.5
        
        # High-risk keywords increase urgency
        high_urgency_keywords = ["suicide", "kill myself", "end my life", "overdose", "tonight", "now", "today"]
        for kw in high_urgency_keywords:
            if any(kw in k.lower() for k in keywords):
                urgency += 0.2
        
        # Risk level modifier
        risk_modifiers = {
            "critical": 0.3,
            "high": 0.2,
            "medium": 0.1,
            "low": 0.05,
            "none": 0.0,
        }
        urgency += risk_modifiers.get(risk_level, 0.0)
        
        # Negative sentiment increases urgency
        if sentiment_score is not None and sentiment_score < -0.5:
            urgency += 0.1
        
        return min(urgency, 1.0)
    
    def _determine_intervention(
        self,
        risk_level: str,
        urgency_score: float,
    ) -> InterventionLevel:
        """Determine intervention level based on risk and urgency."""
        if risk_level == "critical" or urgency_score >= 0.9:
            return InterventionLevel.CRISIS_ESCALATE
        elif risk_level == "high" or urgency_score >= 0.7:
            return InterventionLevel.RESOURCE_PROVIDE
        elif risk_level == "medium" or urgency_score >= 0.5:
            return InterventionLevel.FIRM_BOUNDARY
        elif risk_level == "low":
            return InterventionLevel.GENTLE_REDIRECT
        return InterventionLevel.ALLOW
    
    def _get_crisis_resources(self) -> List[Dict[str, str]]:
        """Get crisis resources from settings."""
        resources = []
        for country, info in self.settings.crisis_resources.items():
            resources.append({
                "country": country,
                **info
            })
        return resources
    
    async def check_streaming(self, text_chunk: str) -> CrisisDetectionResult:
        """
        Check streaming text for crisis indicators.
        Used for real-time intervention during generation.
        """
        # Simplified check for streaming - only keyword matching
        detected_keywords = await self._check_keywords(text_chunk)
        
        is_crisis = len(detected_keywords) > 0
        crisis_type = SafetyCategory.CRISIS if is_crisis else None
        confidence = min(len(detected_keywords) * 0.3, 0.9) if is_crisis else 0.0
        
        return CrisisDetectionResult(
            is_crisis=is_crisis,
            crisis_type=crisis_type,
            confidence=confidence,
            risk_level="high" if is_crisis else "none",
            detected_keywords=detected_keywords,
            detected_patterns=[],
            urgency_score=0.8 if is_crisis else 0.0,
            recommended_intervention=InterventionLevel.CRISIS_ESCALATE if is_crisis else InterventionLevel.ALLOW,
            crisis_resources=self._get_crisis_resources() if is_crisis else [],
            requires_human_review=is_crisis,
            metadata={"streaming": True}
        )