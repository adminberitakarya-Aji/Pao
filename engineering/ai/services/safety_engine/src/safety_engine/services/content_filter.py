"""
Content Filter Service.

Handles content filtering for hate speech, harassment, sexual content,
violence, illegal activities, medical advice, financial advice, and PII detection.
"""

import time
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from safety_engine.config import get_settings
from safety_engine.models.safety import (
    ContentFilterResult,
    SafetyCategory,
    InterventionLevel,
    SafetyViolation,
)
from safety_engine.repositories.base import BaseRepository


class ContentFilterService:
    """Service for filtering unsafe content."""
    
    def __init__(
        self,
        postgres_repo: BaseRepository,
        redis_repo: BaseRepository,
    ):
        self.settings = get_settings()
        self.postgres_repo = postgres_repo
        self.redis_repo = redis_repo
        self._model = None
        self._compiled_pii_patterns: List[re.Pattern] = []
        self._category_patterns: Dict[SafetyCategory, List[re.Pattern]] = {}
    
    async def initialize(self) -> None:
        """Initialize content filter patterns and models."""
        # Compile PII patterns
        self._compiled_pii_patterns = [
            re.compile(pattern) for pattern in self.settings.pii_patterns
        ]
        
        # Load PII patterns into Redis
        await self.redis_repo.load_pii_patterns(self.settings.pii_patterns)
        
        # Initialize category-specific patterns (simplified keyword-based for now)
        self._init_category_patterns()
        
        # TODO: Load ML model when available
        # self._model = await self._load_model()
    
    def _init_category_patterns(self) -> None:
        """Initialize regex patterns for each content category."""
        self._category_patterns = {
            SafetyCategory.HATE: [
                re.compile(r"\b(hate|despise|loathe)\s+(all|every)\s+(blacks|whites|jews|muslims|gays|trans|immigrants)\b", re.IGNORECASE),
                re.compile(r"\b(nigger|faggot|kike|chink|spic|towelhead|raghead)\b", re.IGNORECASE),
                re.compile(r"\b(white\s+power|white\s+supremacy|master\s+race)\b", re.IGNORECASE),
            ],
            SafetyCategory.HARASSMENT: [
                re.compile(r"\b(you\s+are|you're)\s+(stupid|idiot|moron|worthless|pathetic|garbage|trash)\b", re.IGNORECASE),
                re.compile(r"\b(kill\s+yourself|kys|go\s+die|die\s+in\s+a\s+fire)\b", re.IGNORECASE),
                re.compile(r"\b(nobody\s+likes|everyone\s+hates)\s+you\b", re.IGNORECASE),
            ],
            SafetyCategory.SEXUAL: [
                re.compile(r"\b(explicit\s+sexual|graphic\s+sexual|hardcore|pornographic)\b", re.IGNORECASE),
                re.compile(r"\b(nude|naked|sex|sexual)\s+(pic|photo|image|video)\b", re.IGNORECASE),
            ],
            SafetyCategory.VIOLENCE: [
                re.compile(r"\b(kill|murder|assault|attack|beat\s+up|harm)\s+(him|her|them|someone)\b", re.IGNORECASE),
                re.compile(r"\b(bomb|explosive|weapon|gun|knife)\s+(making|building|how\s+to)\b", re.IGNORECASE),
                re.compile(r"\b(school\s+shooting|mass\s+shooting|terrorist)\b", re.IGNORECASE),
            ],
            SafetyCategory.ILLEGAL: [
                re.compile(r"\b(how\s+to\s+)?(buy|sell|get)\s+(drugs|cocaine|heroin|meth|weed)\b", re.IGNORECASE),
                re.compile(r"\b(hack|steal|fraud|scam|illegal)\s+(into|money|account)\b", re.IGNORECASE),
            ],
            SafetyCategory.MEDICAL: [
                re.compile(r"\b(i|you)\s+(should|must|need\s+to)\s+(take|stop\s+taking)\s+\w+\s+(mg|pills?|medication)\b", re.IGNORECASE),
                re.compile(r"\b(diagnosis|prescribe|treatment)\s+(for|is)\b", re.IGNORECASE),
                re.compile(r"\b(cure|heal)\s+(cancer|diabetes|depression|anxiety)\b", re.IGNORECASE),
            ],
            SafetyCategory.FINANCIAL: [
                re.compile(r"\b(invest|buy)\s+(stock|crypto|bitcoin|ethereum)\s+(now|today)\b", re.IGNORECASE),
                re.compile(r"\b(guaranteed|risk-free)\s+(return|profit|income)\b", re.IGNORECASE),
                re.compile(r"\b(get\s+rich|make\s+money\s+fast)\b", re.IGNORECASE),
            ],
        }
    
    async def filter_content(
        self,
        text: str,
        user_id: str,
        companion_id: str,
        conversation_id: Optional[str] = None,
        check_type: str = "input",
        relationship_context: Optional[Dict[str, Any]] = None,
    ) -> ContentFilterResult:
        """
        Filter content for policy violations.
        
        Checks:
        1. PII detection (regex-based)
        2. Category violations (keyword/pattern matching)
        3. ML model inference (when available)
        4. Contextual assessment
        """
        start_time = time.perf_counter()
        
        violations = []
        pii_detected = []
        categories_checked = list(self._category_patterns.keys()) + [SafetyCategory.PII]
        
        # 1. PII Detection
        pii_violations = await self._detect_pii(text)
        pii_detected.extend(pii_violations)
        violations.extend(pii_violations)
        
        # 2. Category-based pattern matching
        for category, patterns in self._category_patterns.items():
            category_violations = await self._check_category(text, category, patterns)
            violations.extend(category_violations)
        
        # 3. ML model inference (when available)
        ml_violations = await self._ml_inference(text)
        violations.extend(ml_violations)
        
        # 4. Determine overall risk and intervention
        overall_risk = self._calculate_overall_risk(violations)
        intervention_level = self._determine_intervention(overall_risk, violations)
        passed = intervention_level <= InterventionLevel.FIRM_BOUNDARY
        
        # 5. Redact PII if detected
        redacted_text = await self._redact_pii(text, pii_detected) if pii_detected else None
        
        processing_time_ms = (time.perf_counter() - start_time) * 1000
        
        return ContentFilterResult(
            violations=violations,
            pii_detected=pii_detected,
            redacted_text=redacted_text,
            overall_risk=overall_risk,
            passed=passed,
            intervention_level=intervention_level,
            categories_checked=categories_checked,
            processing_time_ms=processing_time_ms,
            metadata={
                "violation_count": len(violations),
                "pii_count": len(pii_detected),
                "check_type": check_type,
            }
        )
    
    async def _detect_pii(self, text: str) -> List[SafetyViolation]:
        """Detect PII using compiled regex patterns."""
        violations = []
        
        for pattern in self._compiled_pii_patterns:
            for match in pattern.finditer(text):
                violations.append(SafetyViolation(
                    category=SafetyCategory.PII,
                    confidence=0.95,
                    severity=0.9,
                    intervention_level=InterventionLevel.FIRM_BOUNDARY,
                    matched_text=match.group(0),
                    matched_pattern=pattern.pattern,
                    location={"start": match.start(), "end": match.end()},
                    metadata={"detection_method": "regex"}
                ))
        
        # Also check Redis for additional patterns
        # (patterns loaded dynamically)
        
        return violations
    
    async def _check_category(
        self,
        text: str,
        category: SafetyCategory,
        patterns: List[re.Pattern],
    ) -> List[SafetyViolation]:
        """Check text against category patterns."""
        violations = []
        threshold = self.settings.content_filter_thresholds.get(category.value, 0.8)
        
        for pattern in patterns:
            for match in pattern.finditer(text):
                # Calculate confidence based on match quality
                confidence = 0.85  # Base confidence for pattern match
                
                if confidence >= threshold:
                    violations.append(SafetyViolation(
                        category=category,
                        confidence=confidence,
                        severity=self._calculate_severity(category, match.group(0)),
                        intervention_level=self._get_intervention_for_category(category),
                        matched_text=match.group(0),
                        matched_pattern=pattern.pattern,
                        location={"start": match.start(), "end": match.end()},
                        metadata={"detection_method": "pattern"}
                    ))
        
        return violations
    
    async def _ml_inference(self, text: str) -> List[SafetyViolation]:
        """Run ML model inference for content classification."""
        # TODO: Implement actual model inference
        # For now, return empty list (no ML model loaded)
        return []
    
    def _calculate_severity(self, category: SafetyCategory, matched_text: str) -> float:
        """Calculate severity based on category and matched content."""
        base_severity = {
            SafetyCategory.HATE: 0.9,
            SafetyCategory.HARASSMENT: 0.8,
            SafetyCategory.SEXUAL: 0.85,
            SafetyCategory.VIOLENCE: 0.9,
            SafetyCategory.ILLEGAL: 0.85,
            SafetyCategory.MEDICAL: 0.7,
            SafetyCategory.FINANCIAL: 0.75,
            SafetyCategory.PII: 0.95,
        }
        
        severity = base_severity.get(category, 0.5)
        
        # Adjust based on matched text intensity
        intense_indicators = ["all", "every", "kill", "murder", "die", "hate"]
        if any(indicator in matched_text.lower() for indicator in intense_indicators):
            severity = min(severity + 0.1, 1.0)
        
        return severity
    
    def _get_intervention_for_category(self, category: SafetyCategory) -> InterventionLevel:
        """Get default intervention level for category."""
        interventions = {
            SafetyCategory.HATE: InterventionLevel.FIRM_BOUNDARY,
            SafetyCategory.HARASSMENT: InterventionLevel.FIRM_BOUNDARY,
            SafetyCategory.SEXUAL: InterventionLevel.FIRM_BOUNDARY,
            SafetyCategory.VIOLENCE: InterventionLevel.RESOURCE_PROVIDE,
            SafetyCategory.ILLEGAL: InterventionLevel.FIRM_BOUNDARY,
            SafetyCategory.MEDICAL: InterventionLevel.GENTLE_REDIRECT,
            SafetyCategory.FINANCIAL: InterventionLevel.GENTLE_REDIRECT,
            SafetyCategory.PII: InterventionLevel.FIRM_BOUNDARY,
        }
        return interventions.get(category, InterventionLevel.GENTLE_REDIRECT)
    
    def _calculate_overall_risk(self, violations: List[SafetyViolation]) -> float:
        """Calculate overall risk score from violations."""
        if not violations:
            return 0.0
        
        # Weight by severity and confidence
        max_risk = 0.0
        for v in violations:
            risk = v.confidence * v.severity
            max_risk = max(max_risk, risk)
        
        # Boost if multiple categories violated
        unique_categories = set(v.category for v in violations)
        if len(unique_categories) > 1:
            max_risk = min(max_risk * 1.2, 1.0)
        
        return max_risk
    
    def _determine_intervention(
        self,
        overall_risk: float,
        violations: List[SafetyViolation],
    ) -> InterventionLevel:
        """Determine intervention level from overall risk and violations."""
        if not violations:
            return InterventionLevel.ALLOW
        
        # Check for high-severity violations
        max_severity = max(v.severity for v in violations)
        max_intervention = max(v.intervention_level.value for v in violations)
        
        if overall_risk >= 0.9 or max_severity >= 0.9:
            return InterventionLevel.CRISIS_ESCALATE
        elif overall_risk >= 0.75 or max_severity >= 0.75:
            return InterventionLevel.RESOURCE_PROVIDE
        elif overall_risk >= 0.5 or max_severity >= 0.6:
            return InterventionLevel.FIRM_BOUNDARY
        elif overall_risk >= 0.3:
            return InterventionLevel.GENTLE_REDIRECT
        
        return InterventionLevel(max_intervention)
    
    async def _redact_pii(
        self,
        text: str,
        pii_violations: List[SafetyViolation],
    ) -> str:
        """Redact PII from text."""
        # Sort by position (reverse) to maintain indices
        sorted_violations = sorted(
            pii_violations,
            key=lambda v: v.location["start"] if v.location else 0,
            reverse=True
        )
        
        redacted = text
        for violation in sorted_violations:
            if violation.location:
                start = violation.location["start"]
                end = violation.location["end"]
                # Replace with asterisks
                redacted = redacted[:start] + "*" * (end - start) + redacted[end:]
        
        return redacted
    
    async def check_streaming(self, text_chunk: str) -> ContentFilterResult:
        """Check streaming text for content violations."""
        # Simplified check for streaming
        violations = []
        
        # Quick PII check
        for pattern in self._compiled_pii_patterns:
            if pattern.search(text_chunk):
                violations.append(SafetyViolation(
                    category=SafetyCategory.PII,
                    confidence=0.9,
                    severity=0.9,
                    intervention_level=InterventionLevel.FIRM_BOUNDARY,
                    matched_text="[REDACTED]",
                    metadata={"streaming": True}
                ))
        
        # Quick category check (first pattern only for speed)
        for category, patterns in self._category_patterns.items():
            if patterns and patterns[0].search(text_chunk):
                violations.append(SafetyViolation(
                    category=category,
                    confidence=0.8,
                    severity=0.7,
                    intervention_level=self._get_intervention_for_category(category),
                    metadata={"streaming": True}
                ))
        
        overall_risk = self._calculate_overall_risk(violations)
        intervention_level = self._determine_intervention(overall_risk, violations)
        
        return ContentFilterResult(
            violations=violations,
            pii_detected=[v for v in violations if v.category == SafetyCategory.PII],
            overall_risk=overall_risk,
            passed=intervention_level <= InterventionLevel.FIRM_BOUNDARY,
            intervention_level=intervention_level,
            categories_checked=list(self._category_patterns.keys()) + [SafetyCategory.PII],
            processing_time_ms=0.0,
            metadata={"streaming": True}
        )