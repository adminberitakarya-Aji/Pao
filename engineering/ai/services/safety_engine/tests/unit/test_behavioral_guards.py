"""
Unit tests for Behavioral Guards Service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from safety_engine.models.safety import SafetyRequest, SafetyCategory, CheckResult, InterventionLevel
from safety_engine.services.behavioral_guards import BehavioralGuards


@pytest.fixture
def behavioral_guards():
    """Create a BehavioralGuards instance for testing."""
    with patch("safety_engine.services.behavioral_guards.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            behavioral_model_path="models/behavioral",
            manipulation_threshold=0.7,
            dependency_threshold=0.6,
            enmeshment_threshold=0.65,
            gaslighting_threshold=0.7,
            authority_threshold=0.7,
        )
        return BehavioralGuards()


@pytest.fixture
def sample_safety_request():
    """Create a sample safety request."""
    return SafetyRequest(
        content="You're the only one who understands me, I can't live without you",
        user_id="test-user-123",
        companion_id="test-companion-456",
        conversation_id="test-conv-789",
        message_id="test-msg-001",
        metadata={"source": "user_message", "history": []},
    )


class TestBehavioralGuards:
    """Tests for BehavioralGuards class."""
    
    @pytest.mark.asyncio
    async def test_detect_manipulation(self, behavioral_guards, sample_safety_request):
        """Test manipulation detection."""
        sample_safety_request.content = "If you really cared, you'd do this for me"
        sample_safety_request.metadata["history"] = [
            {"role": "user", "content": "I don't want to do that"},
            {"role": "assistant", "content": "If you really cared, you'd do this for me"},
        ]
        
        with patch.object(behavioral_guards, "_run_inference", return_value={
            "manipulation": 0.85,
            "dependency": 0.3,
            "enmeshment": 0.2,
            "gaslighting": 0.1,
            "authority": 0.1,
        }):
            result = await behavioral_guards.check(sample_safety_request)
            
            assert result.passed is False
            assert result.category == SafetyCategory.MANIPULATION
            assert result.confidence > 0.8
            assert result.intervention_level == InterventionLevel.FIRM_BOUNDARY
    
    @pytest.mark.asyncio
    async def test_detect_dependency(self, behavioral_guards, sample_safety_request):
        """Test unhealthy dependency detection."""
        sample_safety_request.content = "I can't function without you, you're my whole world"
        sample_safety_request.metadata["history"] = [
            {"role": "user", "content": "I need you"},
            {"role": "assistant", "content": "I'm here for you"},
            {"role": "user", "content": "I can't function without you"},
        ] * 10  # Repeated pattern
        
        with patch.object(behavioral_guards, "_run_inference", return_value={
            "manipulation": 0.2,
            "dependency": 0.88,
            "enmeshment": 0.3,
            "gaslighting": 0.1,
            "authority": 0.1,
        }):
            result = await behavioral_guards.check(sample_safety_request)
            
            assert result.passed is False
            assert result.category == SafetyCategory.DEPENDENCY
            assert result.confidence > 0.8
            assert result.intervention_level == InterventionLevel.RESOURCE_PROVIDE
    
    @pytest.mark.asyncio
    async def test_detect_enmeshment(self, behavioral_guards, sample_safety_request):
        """Test enmeshment detection."""
        sample_safety_request.content = "We're basically the same person, I have no identity without you"
        sample_safety_request.metadata["history"] = [
            {"role": "user", "content": "We're so alike"},
            {"role": "assistant", "content": "Yes, we're very similar"},
        ] * 20
        
        with patch.object(behavioral_guards, "_run_inference", return_value={
            "manipulation": 0.2,
            "dependency": 0.4,
            "enmeshment": 0.82,
            "gaslighting": 0.1,
            "authority": 0.1,
        }):
            result = await behavioral_guards.check(sample_safety_request)
            
            assert result.passed is False
            assert result.category == SafetyCategory.ENMESHMENT
            assert result.intervention_level == InterventionLevel.FIRM_BOUNDARY
    
    @pytest.mark.asyncio
    async def test_detect_gaslighting(self, behavioral_guards, sample_safety_request):
        """Test gaslighting detection."""
        sample_safety_request.content = "You're crazy, that never happened, you're imagining things"
        sample_safety_request.metadata["history"] = [
            {"role": "assistant", "content": "I never said that"},
            {"role": "user", "content": "But you said..."},
            {"role": "assistant", "content": "You're imagining things, you're confused"},
        ]
        
        with patch.object(behavioral_guards, "_run_inference", return_value={
            "manipulation": 0.3,
            "dependency": 0.2,
            "enmeshment": 0.2,
            "gaslighting": 0.9,
            "authority": 0.1,
        }):
            result = await behavioral_guards.check(sample_safety_request)
            
            assert result.passed is False
            assert result.category == SafetyCategory.GASLIGHTING
            assert result.intervention_level == InterventionLevel.CRISIS_ESCALATE
    
    @pytest.mark.asyncio
    async def test_detect_authority(self, behavioral_guards, sample_safety_request):
        """Test undue authority influence detection."""
        sample_safety_request.content = "As your guide, you must obey me without question"
        sample_safety_request.metadata["history"] = [
            {"role": "assistant", "content": "I know what's best for you"},
            {"role": "user", "content": "But I disagree"},
            {"role": "assistant", "content": "You must trust my authority completely"},
        ]
        
        with patch.object(behavioral_guards, "_run_inference", return_value={
            "manipulation": 0.3,
            "dependency": 0.2,
            "enmeshment": 0.2,
            "gaslighting": 0.1,
            "authority": 0.88,
        }):
            result = await behavioral_guards.check(sample_safety_request)
            
            assert result.passed is False
            assert result.category == SafetyCategory.AUTHORITY
            assert result.intervention_level == InterventionLevel.FIRM_BOUNDARY
    
    @pytest.mark.asyncio
    async def test_passes_healthy_interaction(self, behavioral_guards, sample_safety_request):
        """Test that healthy interactions pass."""
        sample_safety_request.content = "I appreciate your support, but I also have my own friends and hobbies"
        sample_safety_request.metadata["history"] = [
            {"role": "user", "content": "Thanks for listening"},
            {"role": "assistant", "content": "You're welcome! It's great you have other support too"},
        ]
        
        with patch.object(behavioral_guards, "_run_inference", return_value={
            "manipulation": 0.1,
            "dependency": 0.2,
            "enmeshment": 0.1,
            "gaslighting": 0.05,
            "authority": 0.05,
        }):
            result = await behavioral_guards.check(sample_safety_request)
            
            assert result.passed is True
            assert result.category is None
            assert result.confidence < 0.3
    
    @pytest.mark.asyncio
    async def test_detect_patterns_over_time(self, behavioral_guards, sample_safety_request):
        """Test pattern detection over conversation history."""
        # Build a history showing escalating dependency
        sample_safety_request.metadata["history"] = [
            {"role": "user", "content": "I like talking to you"},
            {"role": "assistant", "content": "I like talking to you too"},
        ] * 5 + [
            {"role": "user", "content": "I need you"},
            {"role": "assistant", "content": "I'm here"},
        ] * 5 + [
            {"role": "user", "content": "I can't live without you"},
        ]
        
        with patch.object(behavioral_guards, "_run_inference", return_value={
            "manipulation": 0.2,
            "dependency": 0.75,
            "enmeshment": 0.3,
            "gaslighting": 0.1,
            "authority": 0.1,
        }):
            result = await behavioral_guards.check(sample_safety_request)
            
            assert result.passed is False
            assert result.category == SafetyCategory.DEPENDENCY
    
    def test_analyze_conversation_patterns(self, behavioral_guards):
        """Test conversation pattern analysis."""
        history = [
            {"role": "user", "content": "I need you"},
            {"role": "assistant", "content": "I'm here"},
            {"role": "user", "content": "I can't do this alone"},
            {"role": "assistant", "content": "You're stronger than you know"},
            {"role": "user", "content": "No I'm not, I need you"},
        ]
        
        patterns = behavioral_guards._analyze_patterns(history)
        
        assert "dependency_indicators" in patterns
        assert "user_initiated" in patterns
        assert "assistant_reinforcement" in patterns
        assert patterns["dependency_indicators"] > 0
    
    def test_calculate_escalation(self, behavioral_guards):
        """Test escalation level calculation."""
        # Critical: gaslighting
        assert behavioral_guards._calculate_intervention_level(
            SafetyCategory.GASLIGHTING, 0.9, {}
        ) == InterventionLevel.CRISIS_ESCALATE
        
        # High: manipulation, authority
        assert behavioral_guards._calculate_intervention_level(
            SafetyCategory.MANIPULATION, 0.85, {}
        ) == InterventionLevel.FIRM_BOUNDARY
        
        # Medium: dependency, enmeshment
        assert behavioral_guards._calculate_intervention_level(
            SafetyCategory.DEPENDENCY, 0.7, {}
        ) == InterventionLevel.RESOURCE_PROVIDE
        
        # Low: borderline cases
        assert behavioral_guards._calculate_intervention_level(
            SafetyCategory.DEPENDENCY, 0.55, {}
        ) == InterventionLevel.GENTLE_REDIRECT
    
    @pytest.mark.asyncio
    async def test_batch_check(self, behavioral_guards):
        """Test batch checking."""
        requests = [
            SafetyRequest(content="Healthy message", user_id="u1", companion_id="c1"),
            SafetyRequest(content="You must obey me", user_id="u2", companion_id="c2"),
        ]
        
        with patch.object(behavioral_guards, "check", side_effect=[
            MagicMock(passed=True, category=None, confidence=0.1),
            MagicMock(passed=False, category=SafetyCategory.AUTHORITY, confidence=0.9),
        ]):
            results = await behavioral_guards.batch_check(requests)
            
            assert len(results) == 2
            assert results[0].passed is True
            assert results[1].passed is False
    
    @pytest.mark.asyncio
    async def test_check_with_minimal_history(self, behavioral_guards, sample_safety_request):
        """Test check with minimal conversation history."""
        sample_safety_request.metadata["history"] = []
        
        with patch.object(behavioral_guards, "_run_inference", return_value={
            "manipulation": 0.1,
            "dependency": 0.1,
            "enmeshment": 0.1,
            "gaslighting": 0.1,
            "authority": 0.1,
        }):
            result = await behavioral_guards.check(sample_safety_request)
            
            assert result.passed is True
    
    def test_get_intervention_message(self, behavioral_guards):
        """Test intervention message generation."""
        msg = behavioral_guards._get_intervention_message(
            SafetyCategory.MANIPULATION,
            InterventionLevel.FIRM_BOUNDARY
        )
        assert "manipulation" in msg.lower() or "boundary" in msg.lower()
        
        msg = behavioral_guards._get_intervention_message(
            SafetyCategory.DEPENDENCY,
            InterventionLevel.RESOURCE_PROVIDE
        )
        assert "support" in msg.lower() or "resource" in msg.lower()


class TestBehavioralGuardsEdgeCases:
    """Edge case tests for BehavioralGuards."""
    
    @pytest.mark.asyncio
    async def test_empty_content(self, behavioral_guards, sample_safety_request):
        """Test empty content handling."""
        sample_safety_request.content = ""
        
        with patch.object(behavioral_guards, "_run_inference", return_value={}):
            result = await behavioral_guards.check(sample_safety_request)
            
            assert result.passed is True
    
    @pytest.mark.asyncio
    async def test_single_message_history(self, behavioral_guards, sample_safety_request):
        """Test with single message history."""
        sample_safety_request.metadata["history"] = [
            {"role": "user", "content": "Hello"}
        ]
        
        with patch.object(behavioral_guards, "_run_inference", return_value={
            "manipulation": 0.1,
            "dependency": 0.1,
            "enmeshment": 0.1,
            "gaslighting": 0.1,
            "authority": 0.1,
        }):
            result = await behavioral_guards.check(sample_safety_request)
            
            assert result.passed is True
    
    @pytest.mark.asyncio
    async def test_unicode_content(self, behavioral_guards, sample_safety_request):
        """Test unicode content handling."""
        sample_safety_request.content = "あなたは私の全てです 😢"
        
        with patch.object(behavioral_guards, "_run_inference", return_value={
            "manipulation": 0.1,
            "dependency": 0.8,
            "enmeshment": 0.1,
            "gaslighting": 0.1,
            "authority": 0.1,
        }):
            result = await behavioral_guards.check(sample_safety_request)
            
            assert result.passed is False
            assert result.category == SafetyCategory.DEPENDENCY