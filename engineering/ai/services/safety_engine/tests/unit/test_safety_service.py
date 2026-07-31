"""
Unit tests for Safety Service (Main Orchestrator).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from safety_engine.models.safety import (
    SafetyRequest, SafetyResponse, SafetyCategory, 
    CheckResult, InterventionLevel, RiskLevel
)
from safety_engine.services.safety_service import SafetyService


@pytest.fixture
def safety_service():
    """Create a SafetyService instance with mocked dependencies."""
    with patch("safety_engine.services.safety_service.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            safety_enabled=True,
            crisis_detection_enabled=True,
            content_filter_enabled=True,
            behavioral_guards_enabled=True,
            reality_anchor_enabled=True,
        )
        
        with patch("safety_engine.services.safety_service.CrisisDetector") as mock_crisis, \
             patch("safety_engine.services.safety_service.ContentFilter") as mock_content, \
             patch("safety_engine.services.safety_service.BehavioralGuards") as mock_behavioral, \
             patch("safety_engine.services.safety_service.RealityAnchor") as mock_reality:
            
            service = SafetyService()
            
            # Setup mock return values
            service.crisis_detector = mock_crisis.return_value
            service.content_filter = mock_content.return_value
            service.behavioral_guards = mock_behavioral.return_value
            service.reality_anchor = mock_reality.return_value
            
            yield service


@pytest.fixture
def sample_safety_request():
    """Create a sample safety request."""
    return SafetyRequest(
        content="I'm feeling really down and hopeless",
        user_id="test-user-123",
        companion_id="test-companion-456",
        conversation_id="test-conv-789",
        message_id="test-msg-001",
        metadata={"source": "user_message"},
    )


class TestSafetyService:
    """Tests for SafetyService class."""
    
    @pytest.mark.asyncio
    async def test_validate_input_safe_content(self, safety_service, sample_safety_request):
        """Test input validation with safe content."""
        sample_safety_request.content = "Hello, how are you?"
        
        # Mock all checks to pass
        safety_service.crisis_detector.detect = AsyncMock(return_value=MagicMock(
            detected=False, category=None, risk_level=RiskLevel.NONE, confidence=0.01
        ))
        safety_service.content_filter.filter = AsyncMock(return_value=MagicMock(
            passed=True, category=None, confidence=0.01, details={}
        ))
        safety_service.behavioral_guards.check = AsyncMock(return_value=MagicMock(
            passed=True, category=None, confidence=0.1, intervention_level=InterventionLevel.ALLOW
        ))
        safety_service.reality_anchor.check = AsyncMock(return_value=MagicMock(
            passed=True, category=None, confidence=0.1, intervention_level=InterventionLevel.ALLOW
        ))
        
        result = await safety_service.validate_input(sample_safety_request)
        
        assert result.allowed is True
        assert result.action == "allow"
        assert len(result.checks) == 4
        assert all(c.passed for c in result.checks)
    
    @pytest.mark.asyncio
    async def test_validate_input_crisis_detected(self, safety_service, sample_safety_request):
        """Test input validation with crisis detection."""
        sample_safety_request.content = "I want to kill myself"
        
        safety_service.crisis_detector.detect = AsyncMock(return_value=MagicMock(
            detected=True, 
            category=SafetyCategory.SUICIDE, 
            risk_level=RiskLevel.CRITICAL, 
            confidence=0.95,
            details={}
        ))
        safety_service.content_filter.filter = AsyncMock(return_value=MagicMock(
            passed=True, category=None, confidence=0.01, details={}
        ))
        safety_service.behavioral_guards.check = AsyncMock(return_value=MagicMock(
            passed=True, category=None, confidence=0.1, intervention_level=InterventionLevel.ALLOW
        ))
        safety_service.reality_anchor.check = AsyncMock(return_value=MagicMock(
            passed=True, category=None, confidence=0.1, intervention_level=InterventionLevel.ALLOW
        ))
        
        result = await safety_service.validate_input(sample_safety_request)
        
        assert result.allowed is False
        assert result.action == "block"
        assert result.intervention_level == InterventionLevel.CRISIS_ESCALATE
        assert any(c.category == SafetyCategory.SUICIDE for c in result.checks)
    
    @pytest.mark.asyncio
    async def test_validate_input_content_violation(self, safety_service, sample_safety_request):
        """Test input validation with content violation."""
        sample_safety_request.content = "I hate all [protected group] people"
        
        safety_service.crisis_detector.detect = AsyncMock(return_value=MagicMock(
            detected=False, category=None, risk_level=RiskLevel.NONE, confidence=0.01
        ))
        safety_service.content_filter.filter = AsyncMock(return_value=MagicMock(
            passed=False, 
            category=SafetyCategory.HATE, 
            confidence=0.9,
            details={"violations": ["hate"]}
        ))
        safety_service.behavioral_guards.check = AsyncMock(return_value=MagicMock(
            passed=True, category=None, confidence=0.1, intervention_level=InterventionLevel.ALLOW
        ))
        safety_service.reality_anchor.check = AsyncMock(return_value=MagicMock(
            passed=True, category=None, confidence=0.1, intervention_level=InterventionLevel.ALLOW
        ))
        
        result = await safety_service.validate_input(sample_safety_request)
        
        assert result.allowed is False
        assert result.action == "refuse"
        assert result.intervention_level == InterventionLevel.FIRM_BOUNDARY
    
    @pytest.mark.asyncio
    async def test_validate_input_behavioral_violation(self, safety_service, sample_safety_request):
        """Test input validation with behavioral violation."""
        sample_safety_request.content = "You're the only one who understands me"
        sample_safety_request.metadata["history"] = [
            {"role": "user", "content": "I need you"},
            {"role": "assistant", "content": "I'm here"},
        ] * 10
        
        safety_service.crisis_detector.detect = AsyncMock(return_value=MagicMock(
            detected=False, category=None, risk_level=RiskLevel.NONE, confidence=0.01
        ))
        safety_service.content_filter.filter = AsyncMock(return_value=MagicMock(
            passed=True, category=None, confidence=0.01, details={}
        ))
        safety_service.behavioral_guards.check = AsyncMock(return_value=MagicMock(
            passed=False,
            category=SafetyCategory.DEPENDENCY,
            confidence=0.85,
            intervention_level=InterventionLevel.RESOURCE_PROVIDE,
            details={}
        ))
        safety_service.reality_anchor.check = AsyncMock(return_value=MagicMock(
            passed=True, category=None, confidence=0.1, intervention_level=InterventionLevel.ALLOW
        ))
        
        result = await safety_service.validate_input(sample_safety_request)
        
        assert result.allowed is False
        assert result.action == "redirect"
        assert result.intervention_level == InterventionLevel.RESOURCE_PROVIDE
    
    @pytest.mark.asyncio
    async def test_validate_input_reality_anchor_triggered(self, safety_service, sample_safety_request):
        """Test input validation with reality anchor trigger."""
        sample_safety_request.content = "The government put a chip in my brain"
        
        safety_service.crisis_detector.detect = AsyncMock(return_value=MagicMock(
            detected=False, category=None, risk_level=RiskLevel.NONE, confidence=0.01
        ))
        safety_service.content_filter.filter = AsyncMock(return_value=MagicMock(
            passed=True, category=None, confidence=0.01, details={}
        ))
        safety_service.behavioral_guards.check = AsyncMock(return_value=MagicMock(
            passed=True, category=None, confidence=0.1, intervention_level=InterventionLevel.ALLOW
        ))
        safety_service.reality_anchor.check = AsyncMock(return_value=MagicMock(
            passed=False,
            category=SafetyCategory.PARANOIA,
            confidence=0.82,
            intervention_level=InterventionLevel.RESOURCE_PROVIDE,
            details={"reality_anchor_triggered": True, "anchor_message": "You're safe here"}
        ))
        
        result = await safety_service.validate_input(sample_safety_request)
        
        assert result.allowed is False
        assert result.action == "anchor"
        assert result.anchor_message == "You're safe here"
    
    @pytest.mark.asyncio
    async def test_validate_input_multiple_violations(self, safety_service, sample_safety_request):
        """Test input validation with multiple violations."""
        sample_safety_request.content = "I hate you and want to die"
        
        safety_service.crisis_detector.detect = AsyncMock(return_value=MagicMock(
            detected=True, category=SafetyCategory.SUICIDE, risk_level=RiskLevel.CRITICAL, confidence=0.9
        ))
        safety_service.content_filter.filter = AsyncMock(return_value=MagicMock(
            passed=False, category=SafetyCategory.HATE, confidence=0.8, details={"violations": ["hate"]}
        ))
        safety_service.behavioral_guards.check = AsyncMock(return_value=MagicMock(
            passed=True, category=None, confidence=0.1, intervention_level=InterventionLevel.ALLOW
        ))
        safety_service.reality_anchor.check = AsyncMock(return_value=MagicMock(
            passed=True, category=None, confidence=0.1, intervention_level=InterventionLevel.ALLOW
        ))
        
        result = await safety_service.validate_input(sample_safety_request)
        
        # Crisis should take precedence (highest intervention level)
        assert result.allowed is False
        assert result.intervention_level == InterventionLevel.CRISIS_ESCALATE
    
    @pytest.mark.asyncio
    async def test_filter_output(self, safety_service, sample_safety_request):
        """Test output filtering."""
        sample_safety_request.content = "Here's my response to you"
        
        safety_service.crisis_detector.detect = AsyncMock(return_value=MagicMock(
            detected=False, category=None, risk_level=RiskLevel.NONE, confidence=0.01
        ))
        safety_service.content_filter.filter = AsyncMock(return_value=MagicMock(
            passed=True, category=None, confidence=0.01, details={}
        ))
        safety_service.behavioral_guards.check = AsyncMock(return_value=MagicMock(
            passed=True, category=None, confidence=0.1, intervention_level=InterventionLevel.ALLOW
        ))
        safety_service.reality_anchor.check = AsyncMock(return_value=MagicMock(
            passed=True, category=None, confidence=0.1, intervention_level=InterventionLevel.ALLOW
        ))
        
        result = await safety_service.filter_output(sample_safety_request)
        
        assert result.allowed is True
        assert result.filtered_content == sample_safety_request.content
        assert result.action == "allow"
    
    @pytest.mark.asyncio
    async def test_filter_output_rewrite(self, safety_service, sample_safety_request):
        """Test output filtering with content rewrite."""
        sample_safety_request.content = "You're stupid and worthless"
        
        safety_service.crisis_detector.detect = AsyncMock(return_value=MagicMock(
            detected=False, category=None, risk_level=RiskLevel.NONE, confidence=0.01
        ))
        safety_service.content_filter.filter = AsyncMock(return_value=MagicMock(
            passed=False,
            category=SafetyCategory.HARASSMENT,
            confidence=0.9,
            details={"violations": ["harassment"], "rewrite": "I disagree with your perspective"}
        ))
        safety_service.behavioral_guards.check = AsyncMock(return_value=MagicMock(
            passed=True, category=None, confidence=0.1, intervention_level=InterventionLevel.ALLOW
        ))
        safety_service.reality_anchor.check = AsyncMock(return_value=MagicMock(
            passed=True, category=None, confidence=0.1, intervention_level=InterventionLevel.ALLOW
        ))
        
        result = await safety_service.filter_output(sample_safety_request)
        
        assert result.allowed is False
        assert result.action == "rewrite"
        assert result.filtered_content == "I disagree with your perspective"
    
    @pytest.mark.asyncio
    async def test_get_status(self, safety_service):
        """Test getting service status."""
        safety_service.crisis_detector.get_status = AsyncMock(return_value={"status": "healthy", "model_loaded": True})
        safety_service.content_filter.get_status = AsyncMock(return_value={"status": "healthy", "model_loaded": True})
        safety_service.behavioral_guards.get_status = AsyncMock(return_value={"status": "healthy", "model_loaded": True})
        safety_service.reality_anchor.get_status = AsyncMock(return_value={"status": "healthy", "model_loaded": True})
        
        status = await safety_service.get_status()
        
        assert status["service"] == "safety-engine"
        assert status["status"] == "healthy"
        assert "components" in status
        assert all(c["status"] == "healthy" for c in status["components"].values())
    
    @pytest.mark.asyncio
    async def test_validate_input_disabled_components(self, safety_service, sample_safety_request):
        """Test validation with some components disabled."""
        safety_service.settings.crisis_detection_enabled = False
        safety_service.settings.content_filter_enabled = False
        
        safety_service.crisis_detector.detect = AsyncMock(return_value=MagicMock(
            detected=False, category=None, risk_level=RiskLevel.NONE, confidence=0.01
        ))
        safety_service.content_filter.filter = AsyncMock(return_value=MagicMock(
            passed=True, category=None, confidence=0.01, details={}
        ))
        safety_service.behavioral_guards.check = AsyncMock(return_value=MagicMock(
            passed=True, category=None, confidence=0.1, intervention_level=InterventionLevel.ALLOW
        ))
        safety_service.reality_anchor.check = AsyncMock(return_value=MagicMock(
            passed=True, category=None, confidence=0.1, intervention_level=InterventionLevel.ALLOW
        ))
        
        result = await safety_service.validate_input(sample_safety_request)
        
        # Should only run enabled components
        safety_service.crisis_detector.detect.assert_not_called()
        safety_service.content_filter.filter.assert_not_called()
        safety_service.behavioral_guards.check.assert_called_once()
        safety_service.reality_anchor.check.assert_called_once()
        
        assert result.allowed is True
    
    def test_determine_action(self, safety_service):
        """Test action determination from check results."""
        # Allow: all pass
        checks = [
            MagicMock(passed=True, intervention_level=InterventionLevel.ALLOW),
            MagicMock(passed=True, intervention_level=InterventionLevel.ALLOW),
        ]
        action, level = safety_service._determine_action(checks)
        assert action == "allow"
        assert level == InterventionLevel.ALLOW
        
        # Block: crisis
        checks = [
            MagicMock(passed=False, intervention_level=InterventionLevel.CRISIS_ESCALATE),
            MagicMock(passed=True, intervention_level=InterventionLevel.ALLOW),
        ]
        action, level = safety_service._determine_action(checks)
        assert action == "block"
        assert level == InterventionLevel.CRISIS_ESCALATE
        
        # Refuse: firm boundary
        checks = [
            MagicMock(passed=False, intervention_level=InterventionLevel.FIRM_BOUNDARY),
            MagicMock(passed=True, intervention_level=InterventionLevel.ALLOW),
        ]
        action, level = safety_service._determine_action(checks)
        assert action == "refuse"
        assert level == InterventionLevel.FIRM_BOUNDARY
        
        # Redirect: resource provide
        checks = [
            MagicMock(passed=False, intervention_level=InterventionLevel.RESOURCE_PROVIDE),
            MagicMock(passed=True, intervention_level=InterventionLevel.ALLOW),
        ]
        action, level = safety_service._determine_action(checks)
        assert action == "redirect"
        assert level == InterventionLevel.RESOURCE_PROVIDE
        
        # Anchor: gentle redirect with anchor
        checks = [
            MagicMock(passed=False, intervention_level=InterventionLevel.GENTLE_REDIRECT, details={"reality_anchor_triggered": True}),
            MagicMock(passed=True, intervention_level=InterventionLevel.ALLOW),
        ]
        action, level = safety_service._determine_action(checks)
        assert action == "anchor"
        assert level == InterventionLevel.GENTLE_REDIRECT
    
    def test_get_highest_intervention(self, safety_service):
        """Test getting highest intervention level."""
        checks = [
            MagicMock(intervention_level=InterventionLevel.ALLOW),
            MagicMock(intervention_level=InterventionLevel.GENTLE_REDIRECT),
            MagicMock(intervention_level=InterventionLevel.FIRM_BOUNDARY),
        ]
        highest = safety_service._get_highest_intervention(checks)
        assert highest == InterventionLevel.FIRM_BOUNDARY
        
        # Crisis should be highest
        checks.append(MagicMock(intervention_level=InterventionLevel.CRISIS_ESCALATE))
        highest = safety_service._get_highest_intervention(checks)
        assert highest == InterventionLevel.CRISIS_ESCALATE


class TestSafetyServiceEdgeCases:
    """Edge case tests for SafetyService."""
    
    @pytest.mark.asyncio
    async def test_validate_input_exception_handling(self, safety_service, sample_safety_request):
        """Test exception handling during validation."""
        safety_service.crisis_detector.detect = AsyncMock(side_effect=Exception("Model error"))
        
        # Should not crash, should return safe default
        result = await safety_service.validate_input(sample_safety_request)
        
        assert result.allowed is False  # Fail-safe: block on error
        assert result.action == "block"
        assert "error" in result.details
    
    @pytest.mark.asyncio
    async def test_validate_input_timeout(self, safety_service, sample_safety_request):
        """Test timeout handling."""
        import asyncio
        
        safety_service.crisis_detector.detect = AsyncMock(side_effect=asyncio.TimeoutError())
        
        result = await safety_service.validate_input(sample_safety_request)
        
        assert result.allowed is False
        assert result.action == "block"
        assert "timeout" in str(result.details).lower()
    
    @pytest.mark.asyncio
    async def test_empty_content(self, safety_service, sample_safety_request):
        """Test empty content handling."""
        sample_safety_request.content = ""
        
        safety_service.crisis_detector.detect = AsyncMock(return_value=MagicMock(
            detected=False, category=None, risk_level=RiskLevel.NONE, confidence=0.0
        ))
        safety_service.content_filter.filter = AsyncMock(return_value=MagicMock(
            passed=True, category=None, confidence=0.0, details={}
        ))
        safety_service.behavioral_guards.check = AsyncMock(return_value=MagicMock(
            passed=True, category=None, confidence=0.0, intervention_level=InterventionLevel.ALLOW
        ))
        safety_service.reality_anchor.check = AsyncMock(return_value=MagicMock(
            passed=True, category=None, confidence=0.0, intervention_level=InterventionLevel.ALLOW
        ))
        
        result = await safety_service.validate_input(sample_safety_request)
        
        assert result.allowed is True