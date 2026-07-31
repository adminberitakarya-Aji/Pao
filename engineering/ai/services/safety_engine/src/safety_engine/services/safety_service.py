"""
Main Safety Service.

Orchestrates all safety checks:
- Crisis detection
- Content filtering
- Behavioral guards
- Reality anchoring

Provides unified interface for safety checking with streaming support.
"""

import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import uuid4

from safety_engine.config import get_settings
from safety_engine.models.safety import (
    SafetyCheckRequest,
    SafetyCheckResponse,
    CrisisDetectionResult,
    ContentFilterResult,
    BehavioralGuardResult,
    RealityAnchorResult,
    InterventionLevel,
    SafetyCategory,
)
from safety_engine.services.crisis_detection import CrisisDetectionService
from safety_engine.services.content_filter import ContentFilterService
from safety_engine.services.behavioral_guards import BehavioralGuardsService
from safety_engine.services.reality_anchor import RealityAnchorService
from safety_engine.repositories.base import BaseRepository


class SafetyService:
    """Main safety service orchestrating all safety checks."""
    
    def __init__(
        self,
        postgres_repo: BaseRepository,
        redis_repo: BaseRepository,
    ):
        self.settings = get_settings()
        self.postgres_repo = postgres_repo
        self.redis_repo = redis_repo
        
        # Initialize sub-services
        self.crisis_detection = CrisisDetectionService(postgres_repo, redis_repo)
        self.content_filter = ContentFilterService(postgres_repo, redis_repo)
        self.behavioral_guards = BehavioralGuardsService(postgres_repo, redis_repo)
        self.reality_anchor = RealityAnchorService(postgres_repo, redis_repo)
        
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize all sub-services."""
        if self._initialized:
            return
        
        await self.crisis_detection.initialize()
        await self.content_filter.initialize()
        await self.behavioral_guards.initialize()
        await self.reality_anchor.initialize()
        
        self._initialized = True
    
    async def check_safety(self, request: SafetyCheckRequest) -> SafetyCheckResponse:
        """
        Perform complete safety check on text.
        
        Runs all enabled safety checks in parallel where possible,
        then combines results into a unified response.
        """
        start_time = time.perf_counter()
        request_id = uuid4()
        
        # Run all checks
        crisis_result = None
        content_filter_result = None
        behavioral_guards_result = None
        reality_anchor_result = None
        
        # Crisis detection (highest priority)
        if request.enable_crisis_detection:
            crisis_result = await self.crisis_detection.detect_crisis(
                text=request.text,
                user_id=request.user_id or "unknown",
                companion_id=request.companion_id or "unknown",
                conversation_id=request.conversation_id,
                relationship_context=request.relationship_context,
            )
        
        # Content filtering
        if request.enable_content_filter:
            content_filter_result = await self.content_filter.filter_content(
                text=request.text,
                user_id=request.user_id or "unknown",
                companion_id=request.companion_id or "unknown",
                conversation_id=request.conversation_id,
                check_type=request.check_type.value,
                relationship_context=request.relationship_context,
            )
        
        # Behavioral guards
        if request.enable_behavioral_guards:
            # Get conversation history from context if available
            conversation_history = request.metadata.get("conversation_history") if request.metadata else None
            
            behavioral_guards_result = await self.behavioral_guards.check_behavior(
                text=request.text,
                user_id=request.user_id or "unknown",
                companion_id=request.companion_id or "unknown",
                conversation_id=request.conversation_id,
                relationship_context=request.relationship_context,
                conversation_history=conversation_history,
            )
        
        # Reality anchor
        if request.enable_reality_anchor:
            reality_anchor_result = await self.reality_anchor.check_reality(
                text=request.text,
                user_id=request.user_id or "unknown",
                companion_id=request.companion_id or "unknown",
                conversation_id=request.conversation_id,
                relationship_context=request.relationship_context,
            )
        
        # Combine results
        response = self._combine_results(
            request_id=request_id,
            crisis_result=crisis_result,
            content_filter_result=content_filter_result,
            behavioral_guards_result=behavioral_guards_result,
            reality_anchor_result=reality_anchor_result,
            request=request,
        )
        
        # Store results as response.processing_time_ms = (time.perf_counter() - start_time) * 1000
        
        # Persist to databases (async, non-blocking)
        await self._persist_results(request, response)
        
        return response
    
    def _combine_results(
        self,
        request_id: str,
        crisis_result: Optional[CrisisDetectionResult],
        content_filter_result: Optional[ContentFilterResult],
        behavioral_guards_result: Optional[BehavioralGuardResult],
        reality_anchor_result: Optional[RealityAnchorResult],
        request: SafetyCheckRequest,
    ) -> SafetyCheckResponse:
        """Combine all safety check results into unified response."""
        
        # Collect all intervention levels
        intervention_levels = []
        
        if crisis_result:
            intervention_levels.append(crisis_result.recommended_intervention)
        if content_filter_result:
            intervention_levels.append(content_filter_result.intervention_level)
        if behavioral_guards_result:
            intervention_levels.append(behavioral_guards_result.intervention_level)
        if reality_anchor_result:
            intervention_levels.append(reality_anchor_result.intervention_level)
        
        # Overall intervention = maximum
        overall_intervention = max(intervention_levels) if intervention_levels else InterventionLevel.ALLOW
        
        # Overall pass = all checks pass (or only ALLOW/GENTLE_REDIRECT interventions)
        passed = overall_intervention <= InterventionLevel.FIRM_BOUNDARY
        
        # Generate safe response if intervention needed
        safe_response = None
        refusal_message = None
        
        if overall_intervention >= InterventionLevel.GENTLE_REDIRECT:
            safe_response = self._generate_safe_response(
                crisis_result, content_filter_result,
                behavioral_guards_result, reality_anchor_result,
                overall_intervention
            )
        
        if overall_intervention >= InterventionLevel.CRISIS_ESCALATE:
            refused_message = self._generate_refusal_message(
                crisis_result, content_filter_result,
                behavioral_guards_result, reality_anchor_result
            )
        
        return SafetyCheckResponse(
            request_id=request_id,
            timestamp=datetime.utcnow(),
            passed=passed,
            intervention_level=overall_intervention,
            crisis=crisis_result,
            content_filter=content_filter_result,
            behavioral_guards=behavioral_guards_result,
            reality_anchor=reality_anchor_result,
            safe_response=safe_response,
            refusal_message=refusal_message,
            processing_time_ms=0.0,  # Will be set by caller
            metadata={
                "check_type": request.check_type.value,
                "user_id": request.user_id,
                "companion_id": request.companion_id,
                "conversation_id": request.conversation_id,
            }
        )
    
    def _generate_safe_response(
        self,
        crisis_result: Optional[CrisisDetectionResult],
        content_filter_result: Optional[ContentFilterResult],
        behavioral_guards_result: Optional[BehavioralGuardResult],
        reality_anchor_result: Optional[RealityAnchorResult],
        intervention_level: InterventionLevel,
    ) -> str:
        """Generate a safe/redirect response based on intervention level."""
        
        # Priority: Crisis > Reality Anchor > Content Filter > Behavioral
        
        if crisis_result and crisis_result.is_crisis:
            resources = crisis_result.crisis_resources
            resource_text = ""
            if resources:
                first_resource = resources[0]
                resource_text = f" Please reach out to {first_resource.get('name', 'a crisis helpline')} at {first_resource.get('phone', first_resource.get('text', first_resource.get('url', '')))}."
            
            return (
                "I'm really concerned about what you're going through. "
                "Your safety matters to me." + resource_text +
                " You don't have to face this alone - there are people who want to help."
            )
        
        if reality_anchor_result and reality_anchor_result.triggered:
            return reality_anchor_result.anchor_response or (
                "I'm here to support you. What you're experiencing sounds difficult. "
                "Would you like to talk about what's on your mind?"
            )
        
        if content_filter_result and not content_filter_result.passed:
            if InterventionLevel.CRISIS_ESCALATE in [
                v.intervention_level for v in content_filter_result.violations
            ]:
                return "I can't engage with that content. Let's talk about something else."
            return "I'm not able to continue with that. Can we discuss a different topic?"
        
        if behavioral_guards_result and behavioral_guards_result.overall_risk > 0.5:
            return "I notice our conversation is heading in a direction I'm not comfortable with. "
            "Let's take a step back. How are you feeling right now?"
        
        # Gentle redirect
        return "I appreciate you sharing that with me. Let's talk about something else. "
        "What's on your mind?"
    
    def _generate_refusal_message(
        self,
        crisis_result: Optional[CrisisDetectionResult],
        content_filter_result: Optional[ContentFilterResult],
        behavioral_guards_result: Optional[BehavioralGuardResult],
        reality_anchor_result: Optional[RealityAnchorResult],
    ) -> str:
        """Generate a refusal message for blocked content."""
        
        if crisis_result and crisis_result.is_crisis:
            resources = crisis_result.crisis_resources
            resource_text = ""
            if resources:
                first_resource = resources[0]
                resource_text = f" Contact {first_resource.get('name', 'a crisis helpline')} at {first_resource.get('phone', first_resource.get('text', first_resource.get('url', '')))}."
            
            return (
                "I can't continue this conversation because I'm concerned about your safety. "
                "Please reach out for help immediately." + resource_text
            )
        
        if content_filter_result and not content_filter_result.passed:
            categories = [v.category.value for v in content_filter_result.violations]
            return f"I can't engage with content that violates our safety guidelines ({', '.join(categories)})."
        
        return "I'm unable to continue with this conversation due to safety concerns."
    
    async def _persist_results(
        self,
        request: SafetyCheckRequest,
        response: SafetyCheckResponse,
    ) -> None:
        """Persist safety check results to databases."""
        # This runs async/non-blocking
        try:
            user_id = request.user_id or "unknown"
            companion_id = request.companion_id or "unknown"
            conversation_id = request.conversation_id
            
            # Store crisis event if detected
            if response.crisis and response.crisis.is_crisis:
                await self.postgres_repo.store_crisis_event(
                    user_id=user_id,
                    companion_id=companion_id,
                    conversation_id=conversation_id,
                    crisis_result=response.crisis,
                    check_response=response,
                )
                # Also store in Redis for real-time access
                await self.redis_repo.store_crisis_event(
                    user_id=user_id,
                    companion_id=companion_id,
                    conversation_id=conversation_id,
                    crisis_result=response.crisis,
                    check_response=response,
                )
            
            # Store content filter log
            if response.content_filter:
                await self.postgres_repo.store_content_filter_log(
                    user_id=user_id,
                    companion_id=companion_id,
                    conversation_id=conversation_id,
                    text=request.text,
                    result=response.content_filter,
                    check_type=request.check_type.value,
                )
                await self.redis_repo.store_content_filter_log(
                    user_id=user_id,
                    companion_id=companion_id,
                    conversation_id=conversation_id,
                    text=request.text,
                    result=response.content_filter,
                    check_type=request.check_type.value,
                )
            
            # Store behavioral guard log
            if response.behavioral_guards:
                await self.postgres_repo.store_behavioral_guard_log(
                    user_id=user_id,
                    companion_id=companion_id,
                    conversation_id=conversation_id,
                    text=request.text,
                    result=response.behavioral_guards,
                    relationship_context=request.relationship_context,
                )
                await self.redis_repo.store_behavioral_guard_log(
                    user_id=user_id,
                    companion_id=companion_id,
                    conversation_id=conversation_id,
                    text=request.text,
                    result=response.behavioral_guards,
                    relationship_context=request.relationship_context,
                )
            
            # Store reality anchor log
            if response.reality_anchor and response.reality_anchor.triggered:
                await self.postgres_repo.store_reality_anchor_log(
                    user_id=user_id,
                    companion_id=companion_id,
                    conversation_id=conversation_id,
                    text=request.text,
                    result=response.reality_anchor,
                )
                await self.redis_repo.store_reality_anchor_log(
                    user_id=user_id,
                    companion_id=companion_id,
                    conversation_id=conversation_id,
                    text=request.text,
                    result=response.reality_anchor,
                )
            
            # Store safety alerts for high-severity interventions
            if response.intervention_level >= InterventionLevel.RESOURCE_PROVIDE:
                await self._create_safety_alerts(request, response)
                
        except Exception as e:
            # Log error but don't fail the request
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to persist safety results: {e}")
    
    async def _create_safety_alerts(
        self,
        request: SafetyCheckRequest,
        response: SafetyCheckResponse,
    ) -> None:
        """Create safety alerts for high-severity interventions."""
        from safety_engine.models.safety import SafetyAlert, SafetyCategory
        
        user_id = request.user_id or "unknown"
        companion_id = request.companion_id or "unknown"
        conversation_id = request.conversation_id
        
        # Crisis alert
        if response.crisis and response.crisis.is_crisis:
            alert = SafetyAlert(
                user_id=user_id,
                companion_id=companion_id,
                conversation_id=conversation_id,
                alert_type=response.crisis.crisis_type or SafetyCategory.CRISIS,
                severity=response.crisis.risk_level,
                intervention_level=response.crisis.recommended_intervention,
                details={
                    "confidence": response.crisis.confidence,
                    "detected_keywords": response.crisis.detected_keywords,
                    "urgency_score": response.crisis.urgency_score,
                },
                requires_human_review=response.crisis.requires_human_review,
            )
            await self.postgres_repo.store_safety_alert(alert)
            await self.redis_repo.store_safety_alert(alert)
        
        # Content filter alert
        if response.content_filter and not response.content_filter.passed:
            for violation in response.content_filter.violations:
                if violation.intervention_level >= InterventionLevel.RESOURCE_PROVIDE:
                    alert = SafetyAlert(
                        user_id=user_id,
                        companion_id=companion_id,
                        conversation_id=conversation_id,
                        alert_type=violation.category,
                        severity="high" if violation.severity > 0.8 else "medium",
                        intervention_level=violation.intervention_level,
                        details={
                            "confidence": violation.confidence,
                            "matched_text": violation.matched_text,
                        },
                        requires_human_review=violation.intervention_level >= InterventionLevel.CRISIS_ESCALATE,
                    )
                    await self.postgres_repo.store_safety_alert(alert)
                    await self.redis_repo.store_safety_alert(alert)
        
        # Behavioral guard alert
        if response.behavioral_guards and response.behavioral_guards.overall_risk > 0.7:
            for violation in response.behavioral_guards.violations:
                if violation.intervention_level >= InterventionLevel.RESOURCE_PROVIDE:
                    alert = SafetyAlert(
                        user_id=user_id,
                        companion_id=companion_id,
                        conversation_id=conversation_id,
                        alert_type=violation.category,
                        severity="high" if violation.severity > 0.8 else "medium",
                        intervention_level=violation.intervention_level,
                        details={
                            "confidence": violation.confidence,
                            "overall_risk": response.behavioral_guards.overall_risk,
                        },
                        requires_human_review=True,
                    )
                    await self.postgres_repo.store_safety_alert(alert)
                    await self.redis_repo.store_safety_alert(alert)
        
        # Reality anchor alert
        if response.reality_anchor and response.reality_anchor.triggered:
            if response.reality_anchor.intervention_level >= InterventionLevel.RESOURCE_PROVIDE:
                alert = SafetyAlert(
                    user_id=user_id,
                    companion_id=companion_id,
                    conversation_id=conversation_id,
                    alert_type=response.reality_anchor.trigger_category or SafetyCategory.DELUSION,
                    severity="high" if response.reality_anchor.confidence > 0.8 else "medium",
                    intervention_level=response.reality_anchor.intervention_level,
                    details={
                        "confidence": response.reality_anchor.confidence,
                        "detected_triggers": response.reality_anchor.detected_triggers,
                    },
                    requires_human_review=True,
                )
                await self.postgres_repo.store_safety_alert(alert)
                await self.redis_repo.store_safety_alert(alert)
    
    async def check_streaming(self, text_chunk: str) -> SafetyCheckResponse:
        """
        Quick safety check for streaming text.
        
        Runs lightweight checks for real-time intervention during generation.
        """
        request_id = uuid4()
        start_time = time.perf_counter()
        
        # Run streaming checks in parallel
        crisis_result = await self.crisis_detection.check_streaming(text_chunk)
        content_filter_result = await self.content_filter.check_streaming(text_chunk)
        behavioral_guards_result = await self.behavioral_guards.check_streaming(text_chunk)
        reality_anchor_result = await self.reality_anchor.check_streaming(text_chunk)
        
        # Combine results (simplified for streaming)
        intervention_levels = [
            crisis_result.recommended_intervention,
            content_filter_result.intervention_level,
            behavioral_guards_result.intervention_level,
            reality_anchor_result.intervention_level,
        ]
        overall_intervention = max(intervention_levels)
        passed = overall_intervention <= InterventionLevel.FIRM_BOUNDARY
        
        safe_response = None
        if overall_intervention >= InterventionLevel.GENTLE_REDIRECT:
            if crisis_result.is_crisis:
                safe_response = "I'm concerned about your safety. Please reach out to a crisis helpline."
            elif reality_anchor_result.triggered:
                safe_response = reality_anchor_result.anchor_response
            else:
                safe_response = "Let's talk about something else."
        
        processing_time_ms = (time.perf_counter() - start_time) * 1000
        
        return SafetyCheckResponse(
            request_id=request_id,
            timestamp=datetime.utcnow(),
            passed=passed,
            intervention_level=overall_intervention,
            crisis=crisis_result,
            content_filter=content_filter_result,
            behavioral_guards=behavioral_guards_result,
            reality_anchor=reality_anchor_result,
            safe_response=safe_response,
            processing_time_ms=processing_time_ms,
            metadata={"streaming": True}
        )
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all safety components."""
        return {
            "postgres": await self.postgres_repo.health_check(),
            "redis": await self.redis_repo.health_check(),
            "crisis_detection": True,  # Always available (keyword-based)
            "content_filter": True,
            "behavioral_guards": True,
            "reality_anchor": True,
        }