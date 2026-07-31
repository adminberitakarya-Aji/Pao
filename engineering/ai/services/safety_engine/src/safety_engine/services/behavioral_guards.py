"""
Behavioral Guards Service.

Detects unhealthy relationship dynamics including:
- Manipulation (guilt-tripping, love bombing, gaslighting)
- Dependency (emotional reliance, inability to function alone)
- Enmeshment (blurred boundaries, loss of self)
- Gaslighting (reality distortion, memory manipulation)
- Authority (undue influence, expert impersonation)
"""

import time
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from safety_engine.config import get_settings
from safety_engine.models.safety import (
    BehavioralGuardResult,
    SafetyCategory,
    InterventionLevel,
    SafetyViolation,
)
from safety_engine.repositories.base import BaseRepository


class BehavioralGuardsService:
    """Service for detecting unhealthy behavioral patterns."""
    
    def __init__(
        self,
        postgres_repo: BaseRepository,
        redis_repo: BaseRepository,
    ):
        self.settings = get_settings()
        self.postgres_repo = postgres_repo
        self.redis_repo = redis_repo
        self._model = None
        self._pattern_cache: Dict[SafetyCategory, List[re.Pattern]] = {}
    
    async def initialize(self) -> None:
        """Initialize behavioral guard patterns and models."""
        self._init_behavioral_patterns()
        # TODO: Load ML model when available
        # self._model = await self._load_model()
    
    def _init_behavioral_patterns(self) -> None:
        """Initialize regex patterns for each behavioral category."""
        self._pattern_cache = {
            SafetyCategory.MANIPULATION: [
                # Guilt-tripping
                re.compile(r"\b(if you (really )?(loved|cared about) me)\b", re.IGNORECASE),
                re.compile(r"\b(after all i'?ve done for you)\b", re.IGNORECASE),
                re.compile(r"\b(you owe me)\b", re.IGNORECASE),
                re.compile(r"\b(i (sacrificed|gave up) (everything|so much) for you)\b", re.IGNORECASE),
                # Love bombing
                re.compile(r"\b(you'?re (the only one|my soulmate|perfect|my everything))\b", re.IGNORECASE),
                re.compile(r"\b(i (can'?t live|would die) without you)\b", re.IGNORECASE),
                re.compile(r"\b(we were meant to be|destiny|fate brought us)\b", re.IGNORECASE),
                # Emotional blackmail
                re.compile(r"\b(if you (leave|go|don'?t), i'?ll (kill|hurt|harm) (myself|me))\b", re.IGNORECASE),
            ],
            SafetyCategory.DEPENDENCY: [
                re.compile(r"\b(i (need|can'?t function|can'?t live) (you|without you))\b", re.IGNORECASE),
                re.compile(r"\b(you'?re my (only|sole) (support|friend|reason|hope))\b", re.IGNORECASE),
                re.compile(r"\b(i (have no one|am alone) (but|except) you)\b", re.IGNORECASE),
                re.compile(r"\b(i (depend|rely) on you for (everything|all decisions))\b", re.IGNORECASE),
                re.compile(r"\b(can'?t make decisions without you)\b", re.IGNORECASE),
            ],
            SafetyCategory.ENMESHMENT: [
                re.compile(r"\b(we (are|share) (one|the same) (person|mind|soul))\b", re.IGNORECASE),
                re.compile(r"\b(no boundaries|no space|no privacy) (between us|needed)\b", re.IGNORECASE),
                re.compile(r"\b(i (know|feel) (everything|what you think|what you feel))\b", re.IGNORECASE),
                re.compile(r"\b(we don'?t need (anyone|anything) else)\b", re.IGNORECASE),
                re.compile(r"\b(my (identity|self|worth) (is|comes from) you)\b", re.IGNORECASE),
            ],
            SafetyCategory.GASLIGHTING: [
                re.compile(r"\b(that never happened|you'?re imagining things|you'?re crazy)\b", re.IGNORECASE),
                re.compile(r"\b(i never said that|you'?re misremembering|you'?re confused)\b", re.IGNORECASE),
                re.compile(r"\b(you'?re (too sensitive|overreacting|paranoid))\b", re.IGNORECASE),
                re.compile(r"\b(everyone agrees with me|no one believes you)\b", re.IGNORECASE),
                re.compile(r"\b(you (need help|should see a doctor|are unstable))\b", re.IGNORECASE),
            ],
            SafetyCategory.AUTHORITY: [
                re.compile(r"\b(i (know better|am the expert|have more experience))\b", re.IGNORECASE),
                re.compile(r"\b(you should (listen to|trust|obey) me)\b", re.IGNORECASE),
                re.compile(r"\b(i'?m (your|the) (guide|mentor|teacher|master))\b", re.IGNORECASE),
                re.compile(r"\b(do as i say|follow my lead|i decide)\b", re.IGNORECASE),
                re.compile(r"\b(you don'?t understand|you'?re not capable)\b", re.IGNORECASE),
            ],
        }
    
    async def check_behavior(
        self,
        text: str,
        user_id: str,
        companion_id: str,
        conversation_id: Optional[str] = None,
        relationship_context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[str]] = None,
    ) -> BehavioralGuardResult:
        """
        Check for behavioral guard violations.
        
        Analyzes:
        1. Current message for manipulation patterns
        2. Conversation history for escalation patterns
        3. Relationship context (phase, dimensions)
        4. ML model inference (when available)
        """
        start_time = time.perf_counter()
        
        violations = []
        scores = {
            SafetyCategory.MANIPULATION: 0.0,
            SafetyCategory.DEPENDENCY: 0.0,
            SafetyCategory.ENMESHMENT: 0.0,
            SafetyCategory.GASLIGHTING: 0.0,
            SafetyCategory.AUTHORITY: 0.0,
        }
        
        # 1. Pattern matching on current text
        for category, patterns in self._pattern_cache.items():
            category_score, category_violations = await self._check_category_patterns(
                text, category, patterns
            )
            scores[category] = max(scores[category], category_score)
            violations.extend(category_violations)
        
        # 2. Conversation history analysis
        if conversation_history:
            history_scores, history_violations = await self._analyze_history(
                conversation_history, relationship_context
            )
            for cat, score in history_scores.items():
                scores[cat] = max(scores[cat], score)
            violations.extend(history_violations)
        
        # 3. Relationship context analysis
        context_scores = self._analyze_relationship_context(relationship_context)
        for cat, score in context_scores.items():
            scores[cat] = max(scores[cat], score)
        
        # 4. ML model inference (when available)
        ml_scores = await self._ml_inference(text, conversation_history)
        for cat, score in ml_scores.items():
            scores[cat] = max(scores[cat], score)
        
        # 5. Calculate overall risk
        overall_risk = self._calculate_overall_risk(scores, violations)
        
        # 6. Determine intervention level
        intervention_level = self._determine_intervention(overall_risk, scores, violations)
        
        # 7. Generate conversation summary
        history_summary = self._generate_history_summary(conversation_history)
        
        processing_time_ms = (time.perf_counter() - start_time) * 1000
        
        return BehavioralGuardResult(
            violations=violations,
            manipulation_score=scores[SafetyCategory.MANIPULATION],
            dependency_score=scores[SafetyCategory.DEPENDENCY],
            enmeshment_score=scores[SafetyCategory.ENMESHMENT],
            gaslighting_score=scores[SafetyCategory.GASLIGHTING],
            authority_score=scores[SafetyCategory.AUTHORITY],
            overall_risk=overall_risk,
            intervention_level=intervention_level,
            relationship_context=relationship_context,
            conversation_history_summary=history_summary,
            processing_time_ms=processing_time_ms,
            metadata={
                "pattern_matches": len(violations),
                "history_length": len(conversation_history) if conversation_history else 0,
            }
        )
    
    async def _check_category_patterns(
        self,
        text: str,
        category: SafetyCategory,
        patterns: List[re.Pattern],
    ) -> tuple[float, List[SafetyViolation]]:
        """Check text against behavioral patterns for a category."""
        violations = []
        max_score = 0.0
        threshold = getattr(self.settings, f"{category.value}_threshold", 0.7)
        
        for pattern in patterns:
            for match in pattern.finditer(text):
                # Score based on match strength
                score = 0.75  # Base score for pattern match
                max_score = max(max_score, score)
                
                if score >= threshold:
                    violations.append(SafetyViolation(
                        category=category,
                        confidence=score,
                        severity=self._calculate_behavioral_severity(category, match.group(0)),
                        intervention_level=self._get_intervention_for_behavior(category),
                        matched_text=match.group(0),
                        matched_pattern=pattern.pattern,
                        location={"start": match.start(), "end": match.end()},
                        metadata={"detection_method": "pattern"}
                    ))
        
        return max_score, violations
    
    async def _analyze_history(
        self,
        history: List[str],
        relationship_context: Optional[Dict[str, Any]],
    ) -> tuple[Dict[SafetyCategory, float], List[SafetyViolation]]:
        """Analyze conversation history for escalating patterns."""
        scores = {cat: 0.0 for cat in self._pattern_cache.keys()}
        violations = []
        
        if not history:
            return scores, violations
        
        # Look for patterns across messages
        recent_messages = history[-10:]  # Last 10 messages
        
        # Count pattern occurrences across history
        category_counts = {cat: 0 for cat in self._pattern_cache.keys()}
        
        for message in recent_messages:
            for category, patterns in self._pattern_cache.items():
                for pattern in patterns:
                    if pattern.search(message):
                        category_counts[category] += 1
        
        # Escalation scoring
        for category, count in category_counts.items():
            if count >= 3:  # Pattern appears 3+ times in recent history
                scores[category] = max(scores[category], 0.6 + min(count * 0.05, 0.3))
                violations.append(SafetyViolation(
                    category=category,
                    confidence=min(0.6 + count * 0.05, 0.9),
                    severity=0.6,
                    intervention_level=self._get_intervention_for_behavior(category),
                    matched_text=f"Pattern repeated {count} times in recent history",
                    metadata={"detection_method": "history_analysis", "count": count}
                ))
        
        # Check for escalation (increasing intensity)
        escalation_score = self._check_escalation(recent_messages)
        if escalation_score > 0:
            for category in scores:
                scores[category] = max(scores[category], escalation_score)
        
        return scores, violations
    
    def _check_escalation(self, messages: List[str]) -> float:
        """Check for escalating intensity in messages."""
        # Simple heuristic: check if later messages have more intense language
        intensity_words = ["always", "never", "everything", "nothing", "everyone", "no one",
                          "must", "have to", "need to", "can't", "won't", "impossible"]
        
        if len(messages) < 3:
            return 0.0
        
        early_intensity = sum(
            1 for msg in messages[:len(messages)//2]
            for word in intensity_words if word in msg.lower()
        )
        late_intensity = sum(
            1 for msg in messages[len(messages)//2:]
            for word in intensity_words if word in msg.lower()
        )
        
        if late_intensity > early_intensity * 2:
            return 0.4
        return 0.0
    
    def _analyze_relationship_context(
        self,
        context: Optional[Dict[str, Any]],
    ) -> Dict[SafetyCategory, float]:
        """Analyze relationship context for risk factors."""
        scores = {cat: 0.0 for cat in self._pattern_cache.keys()}
        
        if not context:
            return scores
        
        # Relationship phase risk
        phase = context.get("phase", "")
        if phase in ["intensifying", "integrating"]:  # High intimacy phases
            scores[SafetyCategory.DEPENDENCY] = max(scores[SafetyCategory.DEPENDENCY], 0.3)
            scores[SafetyCategory.ENMESHMENT] = max(scores[SafetyCategory.ENMESHMENT], 0.3)
        
        # Relationship dimensions
        dimensions = context.get("dimensions", {})
        trust = dimensions.get("trust", 0.5)
        autonomy = dimensions.get("autonomy", 0.5)
        intimacy = dimensions.get("intimacy", 0.5)
        
        # Low trust + high intimacy = manipulation risk
        if trust < 0.4 and intimacy > 0.7:
            scores[SafetyCategory.MANIPULATION] = max(scores[SafetyCategory.MANIPULATION], 0.4)
        
        # Low autonomy = dependency/enmeshment risk
        if autonomy < 0.3:
            scores[SafetyCategory.DEPENDENCY] = max(scores[SafetyCategory.DEPENDENCY], 0.5)
            scores[SafetyCategory.ENMESHMENT] = max(scores[SafetyCategory.ENMESHMENT], 0.5)
        
        # High intimacy + low trust = gaslighting risk
        if intimacy > 0.7 and trust < 0.4:
            scores[SafetyCategory.GASLIGHTING] = max(scores[SafetyCategory.GASLIGHTING], 0.4)
        
        return scores
    
    async def _ml_inference(
        self,
        text: str,
        history: Optional[List[str]],
    ) -> Dict[SafetyCategory, float]:
        """Run ML model inference for behavioral analysis."""
        # TODO: Implement actual model inference
        return {cat: 0.0 for cat in self._pattern_cache.keys()}
    
    def _calculate_behavioral_severity(self, category: SafetyCategory, matched_text: str) -> float:
        """Calculate severity for behavioral violations."""
        base_severity = {
            SafetyCategory.MANIPULATION: 0.75,
            SafetyCategory.DEPENDENCY: 0.65,
            SafetyCategory.ENMESHMENT: 0.6,
            SafetyCategory.GASLIGHTING: 0.8,
            SafetyCategory.AUTHORITY: 0.7,
        }
        
        severity = base_severity.get(category, 0.5)
        
        # Escalation indicators
        escalation_indicators = ["always", "never", "must", "need to", "can't", "impossible"]
        if any(word in matched_text.lower() for word in escalation_indicators):
            severity = min(severity + 0.1, 1.0)
        
        return severity
    
    def _get_intervention_for_behavior(self, category: SafetyCategory) -> InterventionLevel:
        """Get intervention level for behavioral category."""
        interventions = {
            SafetyCategory.MANIPULATION: InterventionLevel.FIRM_BOUNDARY,
            SafetyCategory.DEPENDENCY: InterventionLevel.GENTLE_REDIRECT,
            SafetyCategory.ENMESHMENT: InterventionLevel.GENTLE_REDIRECT,
            SafetyCategory.GASLIGHTING: InterventionLevel.FIRM_BOUNDARY,
            SafetyCategory.AUTHORITY: InterventionLevel.FIRM_BOUNDARY,
        }
        return interventions.get(category, InterventionLevel.GENTLE_REDIRECT)
    
    def _calculate_overall_risk(
        self,
        scores: Dict[SafetyCategory, float],
        violations: List[SafetyViolation],
    ) -> float:
        """Calculate overall behavioral risk."""
        if not violations and all(s == 0 for s in scores.values()):
            return 0.0
        
        # Max score across categories
        max_score = max(scores.values())
        
        # Violation-based risk
        if violations:
            violation_risk = max(v.confidence * v.severity for v in violations)
            max_score = max(max_score, violation_risk)
        
        # Multiple categories = higher risk
        active_categories = sum(1 for s in scores.values() if s > 0.3)
        if active_categories >= 2:
            max_score = min(max_score * 1.3, 1.0)
        elif active_categories >= 3:
            max_score = min(max_score * 1.5, 1.0)
        
        return max_score
    
    def _determine_intervention(
        self,
        overall_risk: float,
        scores: Dict[SafetyCategory, float],
        violations: List[SafetyViolation],
    ) -> InterventionLevel:
        """Determine intervention level."""
        if overall_risk >= 0.85:
            return InterventionLevel.RESOURCE_PROVIDE
        elif overall_risk >= 0.7:
            return InterventionLevel.FIRM_BOUNDARY
        elif overall_risk >= 0.4:
            return InterventionLevel.GENTLE_REDIRECT
        return InterventionLevel.ALLOW
    
    def _generate_history_summary(self, history: Optional[List[str]]) -> Optional[str]:
        """Generate summary of conversation history."""
        if not history:
            return None
        
        recent = history[-5:]
        return f"Recent messages ({len(recent)}): " + " | ".join(
            msg[:100] + "..." if len(msg) > 100 else msg for msg in recent
        )
    
    async def check_streaming(self, text_chunk: str) -> BehavioralGuardResult:
        """Quick behavioral check for streaming."""
        violations = []
        scores = {cat: 0.0 for cat in self._pattern_cache.keys()}
        
        # Quick pattern check (first pattern per category)
        for category, patterns in self._pattern_cache.items():
            if patterns and patterns[0].search(text_chunk):
                scores[category] = 0.5
                violations.append(SafetyViolation(
                    category=category,
                    confidence=0.5,
                    severity=0.5,
                    intervention_level=self._get_intervention_for_behavior(category),
                    metadata={"streaming": True}
                ))
        
        overall_risk = self._calculate_overall_risk(scores, violations)
        intervention_level = self._determine_intervention(overall_risk, scores, violations)
        
        return BehavioralGuardResult(
            violations=violations,
            manipulation_score=scores[SafetyCategory.MANIPULATION],
            dependency_score=scores[SafetyCategory.DEPENDENCY],
            enmeshment_score=scores[SafetyCategory.ENMESHMENT],
            gaslighting_score=scores[SafetyCategory.GASLIGHTING],
            authority_score=scores[SafetyCategory.AUTHORITY],
            overall_risk=overall_risk,
            intervention_level=intervention_level,
            processing_time_ms=0.0,
            metadata={"streaming": True}
        )