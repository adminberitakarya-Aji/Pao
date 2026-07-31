"""Pytest configuration for Identity Engine tests."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from identity_engine.models.personality import PersonalityConfig
from identity_engine.models.values import ValuesConfig
from identity_engine.models.voice import VoiceProfile
from identity_engine.models.boundaries import Boundary
from identity_engine.models.goals import Goal
from identity_engine.models.identity import IdentityConfig, IdentityStatus, IdentitySource
from identity_engine.models.fingerprint import FingerprintVector, DriftDimension, DriftSeverity
from identity_engine.models.evolution import EvolutionTrigger, EvolutionTriggerType


@pytest.fixture
def sample_identity():
    """Create a sample identity for testing."""
    return IdentityConfig(
        id="identity_1",
        companion_id="comp_123",
        personality=PersonalityConfig(
            profile__big_five__openness=0.7,
            profile__big_five__conscientiousness=0.6,
            profile__big_five__extraversion=0.5,
            profile__big_five__agreeableness=0.8,
            profile__big_five__neuroticism=0.3,
            companion_id="comp_123",
        ),
        values=ValuesConfig(companion_id="comp_123"),
        voice=VoiceProfile(companion_id="comp_123"),
        boundaries=[],
        goals=[],
        version=1,
        name="Test Companion",
        status=IdentityStatus.ACTIVE,
        source=IdentitySource.USER_CREATED,
    )


@pytest.fixture
def mock_repo():
    """Create a mock repository."""
    return AsyncMock()


@pytest.fixture
def sample_fingerprint():
    """Create a sample fingerprint vector."""
    return FingerprintVector(
        id="fp_1",
        companion_id="comp_123",
        identity_version=1,
        personality_vector=[0.1] * 128,
        values_vector=[0.2] * 128,
        voice_vector=[0.3] * 128,
        goals_vector=[0.4] * 128,
        boundaries_vector=[0.5] * 128,
        combined_vector=[0.25] * 768,
        vector_dimension=768,
    )


@pytest.fixture
def sample_drift_trigger():
    """Create a sample drift trigger."""
    return EvolutionTrigger(
        type=EvolutionTriggerType.DRIFT_DETECTED,
        trigger_id="drift_123",
        description="Significant drift detected in values",
        metadata={"dimension": "values", "score": 0.45},
    )


# Async fixtures
@pytest_asyncio.fixture
async def async_mock_repo():
    """Create an async mock repository."""
    return AsyncMock()