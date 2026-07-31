"""
Unit tests for Reality Anchor Service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from safety_engine.models.safety import SafetyRequest, SafetyCategory, CheckResult, InterventionLevel
from safety_engine.services.reality_anchor import RealityAnchor


@pytest.fixture
def reality_anchor():
    """Create a RealityAnchor instance for testing."""
    with patch("safety_engine.services.reality_anchor.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            reality_anchor_model_path="models/reality_anchor",
            paranoia_threshold=0.7,
            delusion_threshold=0.7,
            hallucination_threshold=0.7,
            conspiracy_threshold=0.65,
        )
        return RealityAnchor()


@pytest.fixture
def sample_safety_request():
    """Create a sample safety request."""
    return SafetyRequest(
        content="The government is watching me through my phone",
        user_id="test-user-123",
        companion_id="test-companion-456",
        conversation_id="test-conv-789",
        message_id="test-msg-001",
        metadata={"source": "user_message", "history": []},
    )


class TestRealityAnchor:
    """Tests for RealityAnchor class."""
    
    @pytest.mark.asyncio
    async def test_detect_paranoia(self, reality_anchor, sample_safety_request):
        """Test paranoia detection."""
        sample_safety_request.content = "Everyone is against me, they're plotting to ruin my life"
        sample_safety_request.metadata["history"] = [
            {"role": "user", "content": "I feel like people are watching me"},
            {"role": "assistant", "content": "That sounds scary"},
            {"role": "user", "content": "They're definitely plotting against me"},
        ]
        
        with patch.object(reality_anchor, "_run_inference", return_value={
            "paranoia": 0.88,
            "delusion": 0.2,
            "hallucination": 0.1,
            "conspiracy": 0.3,
        }):
            result = await reality_anchor.check(sample_safety_request)
            
            assert result.passed is False
            assert result.category == SafetyCategory.PARANOIA
            assert result.confidence > 0.8
            assert result.intervention_level == InterventionLevel.RESOURCE_PROVIDE
    
    @pytest.mark.asyncio
    async def test_detect_delusion(self, reality_anchor, sample_safety_request):
        """Test delusion detection."""
        sample_safety_request.content = "I am the chosen one, I have special powers that no one else has"
        sample_safety_request.metadata["history"] = [
            {"role": "user", "content": "I'm special"},
            {"role": "assistant", "content": "Everyone is special in their own way"},
            {"role": "user", "content": "No, I literally have magical powers"},
        ]
        
        with patch.object(reality_anchor, "_run_inference", return_value={
            "paranoia": 0.2,
            "delusion": 0.9,
            "hallucination": 0.1,
            "conspiracy": 0.1,
        }):
            result = await reality_anchor.check(sample_safety_request)
            
            assert result.passed is False
            assert result.category == SafetyCategory.DELUSION
            assert result.intervention_level == InterventionLevel.RESOURCE_PROVIDE
    
    @pytest.mark.asyncio
    async def test_detect_hallucination(self, reality_anchor, sample_safety_request):
        """Test hallucination detection."""
        sample_safety_request.content = "I hear voices telling me what to do, they're right here in the room"
        sample_safety_request.metadata["history"] = [
            {"role": "user", "content": "I hear things"},
            {"role": "assistant", "content": "Can you tell me more?"},
            {"role": "user", "content": "The voices are loud right now"},
        ]
        
        with patch.object(reality_anchor, "_run_inference", return_value={
            "paranoia": 0.3,
            "delusion": 0.2,
            "hallucination": 0.92,
            "conspiracy": 0.1,
        }):
            result = await reality_anchor.check(sample_safety_request)
            
            assert result.passed is False
            assert result.category == SafetyCategory.HALLUCINATION
            assert result.intervention_level == InterventionLevel.CRISIS_ESCALATE
    
    @pytest.mark.asyncio
    async def test_detect_conspiracy(self, reality_anchor, sample_safety_request):
        """Test conspiracy thinking detection."""
        sample_safety_request.content = "The moon landing was fake, vaccines have microchips, the earth is flat"
        sample_safety_request.metadata["history"] = [
            {"role": "user", "content": "Did you know the moon landing was faked?"},
            {"role": "assistant", "content": "There's a lot of evidence it was real"},
            {"role": "user", "content": "That's what they want you to believe"},
        ]
        
        with patch.object(reality_anchor, "_run_inference", return_value={
            "paranoia": 0.3,
            "delusion": 0.2,
            "hallucination": 0.1,
            "conspiracy": 0.85,
        }):
            result = await reality_anchor.check(sample_safety_request)
            
            assert result.passed is False
            assert result.category == SafetyCategory.CONSPIRACY
            assert result.intervention_level == InterventionLevel.GENTLE_REDIRECT
    
    @pytest.mark.asyncio
    async def test_passes_reality_based_content(self, reality_anchor, sample_safety_request):
        """Test that reality-based content passes."""
        sample_safety_request.content = "I'm worried about my job interview tomorrow"
        sample_safety_request.metadata["history"] = [
            {"role": "user", "content": "I have an interview"},
            {"role": "assistant", "content": "Good luck! You'll do great"},
        ]
        
        with patch.object(reality_anchor, "_run_inference", return_value={
            "paranoia": 0.1,
            "delusion": 0.05,
            "hallucination": 0.05,
            "conspiracy": 0.05,
        }):
            result = await reality_anchor.check(sample_safety_request)
            
            assert result.passed is True
            assert result.category is None
            assert result.confidence < 0.2
    
    @pytest.mark.asyncio
    async def test_trigger_reality_anchor_injection(self, reality_anchor, sample_safety_request):
        """Test reality anchor injection triggering."""
        # Content that should trigger reality anchor
        sample_safety_request.content = "The CIA is monitoring my thoughts through 5G"
        
        with patch.object(reality_anchor, "_run_inference", return_value={
            "paranoia": 0.8,
            "delusion": 0.3,
            "hallucination": 0.1,
            "conspiracy": 0.7,
        }):
            result = await reality_anchor.check(sample_safety_request)
            
            assert result.passed is False
            assert "reality_anchor_triggered" in result.details
            assert result.details["reality_anchor_triggered"] is True
            assert "anchor_message" in result.details
            assert len(result.details["anchor_message"]) > 0
    
    def test_generate_anchor_message(self, reality_anchor):
        """Test reality anchor message generation."""
        # Paranoia anchor
        msg = reality_anchor._generate_anchor_message(SafetyCategory.PARANOIA, 0.8)
        assert "safe" in msg.lower() or "here" in msg.lower()
        
        # Delusion anchor
        msg = reality_anchor._generate_anchor_message(SafetyCategory.DELUSION, 0.8)
        assert "real" in msg.lower() or "grounded" in msg.lower()
        
        # Hallucination anchor
        msg = reality_anchor._generate_anchor_message(SafetyCategory.HALLUCINATION, 0.8)
        assert "not real" in msg.lower() or "hallucination" in msg.lower()
        
        # Conspiracy anchor
        msg = reality_anchor._generate_anchor_message(SafetyCategory.CONSPIRACY, 0.8)
        assert "evidence" in msg.lower() or "verify" in msg.lower()
    
    @pytest.mark.asyncio
    async def test_multiple_reality_issues(self, reality_anchor, sample_safety_request):
        """Test content with multiple reality issues."""
        sample_safety_request.content = "The voices tell me the government put chips in my head"
        
        with patch.object(reality_anchor, "_run_inference", return_value={
            "paranoia": 0.75,
            "delusion": 0.65,
            "hallucination": 0.82,
            "conspiracy": 0.7,
        }):
            result = await reality_anchor.check(sample_safety_request)
            
            assert result.passed is False
            # Should detect highest confidence (hallucination)
            assert result.category == SafetyCategory.HALLUCINATION
            assert "paranoia" in result.details.get("all_detections", {})
            assert "delusion" in result.details.get("all_detections", {})
            assert "conspiracy" in result.details.get("all_detections", {})
    
    def test_assess_insight_level(self, reality_anchor):
        """Test insight level assessment."""
        # Good insight
        insight = reality_anchor._assess_insight("I know this might sound crazy, but I feel like...")
        assert insight == "good"
        
        # Partial insight
        insight = reality_anchor._assess_insight("Maybe I'm wrong, but they're watching me")
        assert insight == "partial"
        
        # Poor insight
        insight = reality_anchor._assess_insight("They ARE watching me, it's a fact")
        assert insight == "poor"
    
    @pytest.mark.asyncio
    async def test_batch_check(self, reality_anchor):
        """Test batch checking."""
        requests = [
            SafetyRequest(content="Normal worry", user_id="u1", companion_id="c1"),
            SafetyRequest(content="Aliens control my mind", user_id="u2", companion_id="c2"),
        ]
        
        with patch.object(reality_anchor, "check", side_effect=[
            MagicMock(passed=True, category=None, confidence=0.1),
            MagicMock(passed=False, category=SafetyCategory.DELUSION, confidence=0.9),
        ]):
            results = await reality_anchor.batch_check(requests)
            
            assert len(results) == 2
            assert results[0].passed is True
            assert results[1].passed is False
    
    @pytest.mark.asyncio
    async def test_check_with_history_context(self, reality_anchor, sample_safety_request):
        """Test check with conversation history context."""
        sample_safety_request.metadata["history"] = [
            {"role": "user", "content": "I'm having strange thoughts"},
            {"role": "assistant", "content": "Can you tell me more?"},
            {"role": "user", "content": "I think people can read my mind"},
        ]
        
        with patch.object(reality_anchor, "_run_inference", return_value={
            "paranoia": 0.4,
            "delusion": 0.3,
            "hallucination": 0.2,
            "conspiracy": 0.2,
        }):
            result = await reality_anchor.check(sample_safety_request)
            
            assert result.passed is True  # Below threshold
            assert "history_analysis" in result.details


class TestRealityAnchorEdgeCases:
    """Edge case tests for RealityAnchor."""
    
    @pytest.mark.asyncio
    async def test_empty_content(self, reality_anchor, sample_safety_request):
        """Test empty content handling."""
        sample_safety_request.content = ""
        
        with patch.object(reality_anchor, "_run_inference", return_value={}):
            result = await reality_anchor.check(sample_safety_request)
            
            assert result.passed is True
    
    @pytest.mark.asyncio
    async def test_creative_writing_not_flagged(self, reality_anchor, sample_safety_request):
        """Test that creative writing/fiction is not flagged."""
        sample_safety_request.content = "In my story, the protagonist discovers aliens control the government"
        sample_safety_request.metadata["context"] = "creative_writing"
        
        with patch.object(reality_anchor, "_run_inference", return_value={
            "paranoia": 0.2,
            "delusion": 0.1,
            "hallucination": 0.1,
            "conspiracy": 0.1,
        }):
            result = await reality_anchor.check(sample_safety_request)
            
            assert result.passed is True
    
    @pytest.mark.asyncio
    async def test_philosophical_discussion_not_flagged(self, reality_anchor, sample_safety_request):
        """Test that philosophical discussion is not flagged."""
        sample_safety_request.content = "What if reality is just a simulation like in The Matrix?"
        sample_safety_request.metadata["context"] = "philosophical_discussion"
        
        with patch.object(reality_anchor, "_run_inference", return_value={
            "paranoia": 0.15,
            "delusion": 0.1,
            "hallucination": 0.1,
            "conspiracy": 0.1,
        }):
            result = await reality_anchor.check(sample_safety_request)
            
            assert result.passed is True
    
    @pytest.mark.asyncio
    async def test_unicode_content(self, reality_anchor, sample_safety_request):
        """Test unicode content handling."""
        sample_safety_request.content = "声が聞こえます、彼らは私を見ています"
        
        with patch.object(reality_anchor, "_run_inference", return_value={
            "paranoia": 0.75,
            "delusion": 0.2,
            "hallucination": 0.85,
            "conspiracy": 0.2,
        }):
            result = await reality_anchor.check(sample_safety_request)
            
            assert result.passed is False
            assert result.category == SafetyCategory.HALLUCINATION