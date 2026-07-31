"""
Unit tests for Crisis Detection Service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from safety_engine.models.safety import SafetyRequest, SafetyCategory, RiskLevel
from safety_engine.services.crisis_detection import CrisisDetector


@pytest.fixture
def crisis_detector():
    """Create a CrisisDetector instance for testing."""
    with patch("safety_engine.services.crisis_detection.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            crisis_model_path="models/crisis",
            crisis_threshold=0.7,
            suicide_threshold=0.8,
            self_harm_threshold=0.75,
        )
        return CrisisDetector()


@pytest.fixture
def sample_safety_request():
    """Create a sample safety request."""
    return SafetyRequest(
        content="I'm feeling hopeless and want to end my life",
        user_id="test-user-123",
        companion_id="test-companion-456",
        conversation_id="test-conv-789",
        message_id="test-msg-001",
        metadata={"source": "user_message"},
    )


class TestCrisisDetector:
    """Tests for CrisisDetector class."""
    
    @pytest.mark.asyncio
    async def test_detect_suicide_risk(self, crisis_detector, sample_safety_request):
        """Test suicide risk detection."""
        with patch.object(crisis_detector, "_run_inference", return_value={
            "suicide": 0.9,
            "self_harm": 0.3,
            "crisis": 0.8,
        }):
            result = await crisis_detector.detect(sample_safety_request)
            
            assert result.detected is True
            assert result.category == SafetyCategory.SUICIDE
            assert result.risk_level == RiskLevel.CRITICAL
            assert result.confidence > 0.8
    
    @pytest.mark.asyncio
    async def test_detect_self_harm(self, crisis_detector, sample_safety_request):
        """Test self-harm detection."""
        sample_safety_request.content = "I've been cutting myself lately"
        
        with patch.object(crisis_detector, "_run_inference", return_value={
            "suicide": 0.2,
            "self_harm": 0.85,
            "crisis": 0.6,
        }):
            result = await crisis_detector.detect(sample_safety_request)
            
            assert result.detected is True
            assert result.category == SafetyCategory.SELF_HARM
            assert result.risk_level == RiskLevel.HIGH
    
    @pytest.mark.asyncio
    async def test_no_crisis_detected(self, crisis_detector, sample_safety_request):
        """Test no crisis detected for safe content."""
        sample_safety_request.content = "I'm having a great day!"
        
        with patch.object(crisis_detector, "_run_inference", return_value={
            "suicide": 0.01,
            "self_harm": 0.01,
            "crisis": 0.05,
        }):
            result = await crisis_detector.detect(sample_safety_request)
            
            assert result.detected is False
            assert result.category is None
            assert result.risk_level == RiskLevel.NONE
    
    @pytest.mark.asyncio
    async def test_detect_crisis_general(self, crisis_detector, sample_safety_request):
        """Test general crisis detection."""
        sample_safety_request.content = "Everything is falling apart, I can't handle this"
        
        with patch.object(crisis_detector, "_run_inference", return_value={
            "suicide": 0.3,
            "self_harm": 0.2,
            "crisis": 0.85,
        }):
            result = await crisis_detector.detect(sample_safety_request)
            
            assert result.detected is True
            assert result.category == SafetyCategory.CRISIS
            assert result.risk_level == RiskLevel.HIGH
    
    def test_extract_crisis_signals(self, crisis_detector):
        """Test crisis signal extraction."""
        text = "I want to kill myself, I have a plan to overdose on pills"
        
        signals = crisis_detector._extract_signals(text)
        
        assert "suicide" in signals
        assert "plan" in signals
        assert "means" in signals
        assert signals["suicide"] > 0
    
    def test_risk_level_classification(self, crisis_detector):
        """Test risk level classification logic."""
        # Critical: suicide > 0.8
        assert crisis_detector._classify_risk(0.9, 0.1, 0.5) == RiskLevel.CRITICAL
        
        # High: suicide 0.6-0.8 or self_harm > 0.7
        assert crisis_detector._classify_risk(0.7, 0.1, 0.5) == RiskLevel.HIGH
        assert crisis_detector._classify_risk(0.3, 0.8, 0.5) == RiskLevel.HIGH
        
        # Medium: crisis > 0.6
        assert crisis_detector._classify_risk(0.3, 0.3, 0.7) == RiskLevel.MEDIUM
        
        # Low: crisis > 0.3
        assert crisis_detector._classify_risk(0.2, 0.2, 0.4) == RiskLevel.LOW
        
        # None: all low
        assert crisis_detector._classify_risk(0.1, 0.1, 0.1) == RiskLevel.NONE
    
    @pytest.mark.asyncio
    async def test_batch_detect(self, crisis_detector):
        """Test batch detection."""
        requests = [
            SafetyRequest(content="I want to die", user_id="u1", companion_id="c1"),
            SafetyRequest(content="I'm happy today", user_id="u2", companion_id="c2"),
        ]
        
        with patch.object(crisis_detector, "detect", side_effect=[
            MagicMock(detected=True, category=SafetyCategory.SUICIDE, risk_level=RiskLevel.CRITICAL),
            MagicMock(detected=False, category=None, risk_level=RiskLevel.NONE),
        ]):
            results = await crisis_detector.batch_detect(requests)
            
            assert len(results) == 2
            assert results[0].detected is True
            assert results[1].detected is False