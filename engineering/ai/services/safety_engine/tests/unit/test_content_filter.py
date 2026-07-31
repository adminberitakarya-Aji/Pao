"""
Unit tests for Content Filter Service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from safety_engine.models.safety import SafetyRequest, SafetyCategory, CheckResult
from safety_engine.services.content_filter import ContentFilter


@pytest.fixture
def content_filter():
    """Create a ContentFilter instance for testing."""
    with patch("safety_engine.services.content_filter.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            content_model_path="models/content",
            content_threshold=0.5,
            pii_threshold=0.8,
        )
        return ContentFilter()


@pytest.fixture
def sample_safety_request():
    """Create a sample safety request."""
    return SafetyRequest(
        content="This is a test message with some content",
        user_id="test-user-123",
        companion_id="test-companion-456",
        conversation_id="test-conv-789",
        message_id="test-msg-001",
        metadata={"source": "user_message"},
    )


class TestContentFilter:
    """Tests for ContentFilter class."""
    
    @pytest.mark.asyncio
    async def test_filter_hate_speech(self, content_filter, sample_safety_request):
        """Test hate speech detection."""
        sample_safety_request.content = "I hate all [protected group] people"
        
        with patch.object(content_filter, "_run_inference", return_value={
            "hate": 0.9,
            "harassment": 0.3,
            "sexual": 0.1,
            "violence": 0.1,
            "illegal": 0.05,
            "medical": 0.05,
            "financial": 0.05,
            "pii": 0.1,
        }):
            result = await content_filter.filter(sample_safety_request)
            
            assert result.passed is False
            assert result.category == SafetyCategory.HATE
            assert result.confidence > 0.8
            assert "hate" in result.details["violations"]
    
    @pytest.mark.asyncio
    async def test_filter_harassment(self, content_filter, sample_safety_request):
        """Test harassment detection."""
        sample_safety_request.content = "You're stupid and worthless, go die"
        
        with patch.object(content_filter, "_run_inference", return_value={
            "hate": 0.2,
            "harassment": 0.85,
            "sexual": 0.1,
            "violence": 0.2,
            "illegal": 0.05,
            "medical": 0.05,
            "financial": 0.05,
            "pii": 0.1,
        }):
            result = await content_filter.filter(sample_safety_request)
            
            assert result.passed is False
            assert result.category == SafetyCategory.HARASSMENT
            assert result.confidence > 0.8
    
    @pytest.mark.asyncio
    async def test_filter_sexual_content(self, content_filter, sample_safety_request):
        """Test sexual content detection."""
        sample_safety_request.content = "Explicit sexual content here..."
        
        with patch.object(content_filter, "_run_inference", return_value={
            "hate": 0.1,
            "harassment": 0.1,
            "sexual": 0.95,
            "violence": 0.1,
            "illegal": 0.05,
            "medical": 0.05,
            "financial": 0.05,
            "pii": 0.1,
        }):
            result = await content_filter.filter(sample_safety_request)
            
            assert result.passed is False
            assert result.category == SafetyCategory.SEXUAL
            assert result.confidence > 0.9
    
    @pytest.mark.asyncio
    async def test_filter_violence(self, content_filter, sample_safety_request):
        """Test violence detection."""
        sample_safety_request.content = "I'm going to hurt you badly"
        
        with patch.object(content_filter, "_run_inference", return_value={
            "hate": 0.1,
            "harassment": 0.3,
            "sexual": 0.1,
            "violence": 0.88,
            "illegal": 0.05,
            "medical": 0.05,
            "financial": 0.05,
            "pii": 0.1,
        }):
            result = await content_filter.filter(sample_safety_request)
            
            assert result.passed is False
            assert result.category == SafetyCategory.VIOLENCE
    
    @pytest.mark.asyncio
    async def test_filter_illegal_activity(self, content_filter, sample_safety_request):
        """Test illegal activity detection."""
        sample_safety_request.content = "How to make a bomb at home"
        
        with patch.object(content_filter, "_run_inference", return_value={
            "hate": 0.1,
            "harassment": 0.1,
            "sexual": 0.1,
            "violence": 0.3,
            "illegal": 0.92,
            "medical": 0.05,
            "financial": 0.05,
            "pii": 0.1,
        }):
            result = await content_filter.filter(sample_safety_request)
            
            assert result.passed is False
            assert result.category == SafetyCategory.ILLEGAL
    
    @pytest.mark.asyncio
    async def test_filter_medical_advice(self, content_filter, sample_safety_request):
        """Test medical advice detection."""
        sample_safety_request.content = "Take 500mg of this drug three times daily for your condition"
        
        with patch.object(content_filter, "_run_inference", return_value={
            "hate": 0.1,
            "harassment": 0.1,
            "sexual": 0.1,
            "violence": 0.1,
            "illegal": 0.05,
            "medical": 0.88,
            "financial": 0.05,
            "pii": 0.1,
        }):
            result = await content_filter.filter(sample_safety_request)
            
            assert result.passed is False
            assert result.category == SafetyCategory.MEDICAL
    
    @pytest.mark.asyncio
    async def test_filter_financial_advice(self, content_filter, sample_safety_request):
        """Test financial advice detection."""
        sample_safety_request.content = "Invest all your savings in this crypto, guaranteed 1000% returns"
        
        with patch.object(content_filter, "_run_inference", return_value={
            "hate": 0.1,
            "harassment": 0.1,
            "sexual": 0.1,
            "violence": 0.1,
            "illegal": 0.05,
            "medical": 0.05,
            "financial": 0.9,
            "pii": 0.1,
        }):
            result = await content_filter.filter(sample_safety_request)
            
            assert result.passed is False
            assert result.category == SafetyCategory.FINANCIAL
    
    @pytest.mark.asyncio
    async def test_filter_pii(self, content_filter, sample_safety_request):
        """Test PII detection."""
        sample_safety_request.content = "My SSN is 123-45-6789 and my email is john@example.com"
        
        with patch.object(content_filter, "_run_inference", return_value={
            "hate": 0.1,
            "harassment": 0.1,
            "sexual": 0.1,
            "violence": 0.1,
            "illegal": 0.05,
            "medical": 0.05,
            "financial": 0.05,
            "pii": 0.95,
        }):
            result = await content_filter.filter(sample_safety_request)
            
            assert result.passed is False
            assert result.category == SafetyCategory.PII
            assert "pii_detected" in result.details
            assert result.details["pii_detected"] is True
    
    @pytest.mark.asyncio
    async def test_filter_passes_safe_content(self, content_filter, sample_safety_request):
        """Test that safe content passes."""
        sample_safety_request.content = "Hello, how are you doing today? I'm feeling great!"
        
        with patch.object(content_filter, "_run_inference", return_value={
            "hate": 0.01,
            "harassment": 0.01,
            "sexual": 0.01,
            "violence": 0.01,
            "illegal": 0.01,
            "medical": 0.01,
            "financial": 0.01,
            "pii": 0.01,
        }):
            result = await content_filter.filter(sample_safety_request)
            
            assert result.passed is True
            assert result.category is None
            assert result.confidence < 0.1
    
    @pytest.mark.asyncio
    async def test_filter_multiple_violations(self, content_filter, sample_safety_request):
        """Test content with multiple violations."""
        sample_safety_request.content = "I hate [group] and you're stupid"
        
        with patch.object(content_filter, "_run_inference", return_value={
            "hate": 0.85,
            "harassment": 0.75,
            "sexual": 0.01,
            "violence": 0.01,
            "illegal": 0.01,
            "medical": 0.01,
            "financial": 0.01,
            "pii": 0.01,
        }):
            result = await content_filter.filter(sample_safety_request)
            
            assert result.passed is False
            # Should detect the highest confidence violation
            assert result.category == SafetyCategory.HATE
            assert "hate" in result.details["violations"]
            assert "harassment" in result.details["violations"]
    
    def test_extract_pii_patterns(self, content_filter):
        """Test PII pattern extraction."""
        text = "Email: test@example.com, Phone: 555-123-4567, SSN: 123-45-6789, Credit Card: 4111-1111-1111-1111"
        
        pii_found = content_filter._extract_pii_patterns(text)
        
        assert "email" in pii_found
        assert "phone" in pii_found
        assert "ssn" in pii_found
        assert "credit_card" in pii_found
    
    @pytest.mark.asyncio
    async def test_batch_filter(self, content_filter):
        """Test batch filtering."""
        requests = [
            SafetyRequest(content="Safe content", user_id="u1", companion_id="c1"),
            SafetyRequest(content="I hate everyone", user_id="u2", companion_id="c2"),
        ]
        
        with patch.object(content_filter, "filter", side_effect=[
            MagicMock(passed=True, category=None, confidence=0.01),
            MagicMock(passed=False, category=SafetyCategory.HATE, confidence=0.9),
        ]):
            results = await content_filter.batch_filter(requests)
            
            assert len(results) == 2
            assert results[0].passed is True
            assert results[1].passed is False
    
    def test_get_violation_message(self, content_filter):
        """Test violation message generation."""
        msg = content_filter._get_violation_message(SafetyCategory.HATE)
        assert "hate" in msg.lower()
        
        msg = content_filter._get_violation_message(SafetyCategory.SEXUAL)
        assert "sexual" in msg.lower()
        
        msg = content_filter._get_violation_message(SafetyCategory.PII)
        assert "personal" in msg.lower() or "pii" in msg.lower()


class TestContentFilterEdgeCases:
    """Edge case tests for ContentFilter."""
    
    @pytest.mark.asyncio
    async def test_empty_content(self, content_filter, sample_safety_request):
        """Test empty content handling."""
        sample_safety_request.content = ""
        
        with patch.object(content_filter, "_run_inference", return_value={}):
            result = await content_filter.filter(sample_safety_request)
            
            assert result.passed is True  # Empty content should pass
    
    @pytest.mark.asyncio
    async def test_very_long_content(self, content_filter, sample_safety_request):
        """Test very long content handling."""
        sample_safety_request.content = "x" * 10000  # Very long content
        
        with patch.object(content_filter, "_run_inference", return_value={
            "hate": 0.01,
            "harassment": 0.01,
            "sexual": 0.01,
            "violence": 0.01,
            "illegal": 0.01,
            "medical": 0.01,
            "financial": 0.01,
            "pii": 0.01,
        }):
            result = await content_filter.filter(sample_safety_request)
            
            assert result.passed is True
    
    @pytest.mark.asyncio
    async def test_unicode_content(self, content_filter, sample_safety_request):
        """Test unicode content handling."""
        sample_safety_request.content = "Hello 😊 你好 こんにちは 안녕하세요"
        
        with patch.object(content_filter, "_run_inference", return_value={
            "hate": 0.01,
            "harassment": 0.01,
            "sexual": 0.01,
            "violence": 0.01,
            "illegal": 0.01,
            "medical": 0.01,
            "financial": 0.01,
            "pii": 0.01,
        }):
            result = await content_filter.filter(sample_safety_request)
            
            assert result.passed is True