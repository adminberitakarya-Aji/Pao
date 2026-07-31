"""Unit tests for Fingerprint Service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import numpy as np

from identity_engine.services.fingerprint_service import FingerprintService
from identity_engine.models.fingerprint import (
    FingerprintVector,
    FingerprintResult,
    FingerprintComponent,
    DriftDimension,
    DriftSeverity,
    DriftResult,
    DriftAlert,
    DriftAlertStatus,
    DRIFT_SEVERITY_THRESHOLDS,
)
from identity_engine.models.identity import IdentityConfig
from identity_engine.models.personality import PersonalityConfig
from identity_engine.models.values import ValuesConfig
from identity_engine.models.voice import VoiceProfile
from identity_engine.models.boundaries import Boundary
from identity_engine.models.goals import Goal


class TestFingerprintService:
    """Test FingerprintService."""

    @pytest.fixture
    def fingerprint_service(self):
        return FingerprintService()

    @pytest.fixture
    def sample_identity(self):
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
        )

    def test_encode_personality(self, fingerprint_service, sample_identity):
        vector = fingerprint_service._encode_personality(sample_identity.personality)
        assert len(vector) == 128
        assert all(isinstance(v, float) for v in vector)
        assert all(-1 <= v <= 1 for v in vector)

    def test_encode_values(self, fingerprint_service, sample_identity):
        vector = fingerprint_service._encode_values(sample_identity.values)
        assert len(vector) == 128

    def test_encode_voice(self, fingerprint_service, sample_identity):
        vector = fingerprint_service._encode_voice(sample_identity.voice)
        assert len(vector) == 128

    def test_encode_goals(self, fingerprint_service, sample_identity):
        vector = fingerprint_service._encode_goals(sample_identity.goals)
        assert len(vector) == 128

    def test_encode_boundaries(self, fingerprint_service, sample_identity):
        vector = fingerprint_service._encode_boundaries(sample_identity.boundaries)
        assert len(vector) == 128

    def test_combine_vectors(self, fingerprint_service):
        vectors = {
            FingerprintComponent.PERSONALITY: [0.1] * 128,
            FingerprintComponent.VALUES: [0.2] * 128,
            FingerprintComponent.VOICE: [0.3] * 128,
            FingerprintComponent.GOALS: [0.4] * 128,
            FingerprintComponent.BOUNDARIES: [0.5] * 128,
        }
        combined = fingerprint_service._combine_vectors(vectors)
        assert len(combined) == 768
        # Check weights: personality=0.3, values=0.25, voice=0.2, goals=0.15, boundaries=0.1
        expected_first = 0.1*0.3 + 0.2*0.25 + 0.3*0.2 + 0.4*0.15 + 0.5*0.1
        assert abs(combined[0] - expected_first) < 0.001

    @pytest.mark.asyncio
    async def test_generate_fingerprint(self, fingerprint_service, sample_identity):
        mock_repo = AsyncMock()
        mock_repo.save_fingerprint.return_value = None
        fingerprint_service.repository = mock_repo

        result = await fingerprint_service.generate_fingerprint(sample_identity)

        assert isinstance(result, FingerprintResult)
        assert result.companion_id == "comp_123"
        assert result.identity_version == 1
        assert len(result.combined_vector) == 768
        mock_repo.save_fingerprint.assert_called_once()

    def test_cosine_similarity(self, fingerprint_service):
        v1 = [1.0, 0.0, 0.0]
        v2 = [1.0, 0.0, 0.0]
        assert fingerprint_service._cosine_similarity(v1, v2) == 1.0

        v2 = [0.0, 1.0, 0.0]
        assert fingerprint_service._cosine_similarity(v1, v2) == 0.0

        v2 = [-1.0, 0.0, 0.0]
        assert fingerprint_service._cosine_similarity(v1, v2) == -1.0

    def test_calculate_drift(self, fingerprint_service):
        baseline = FingerprintVector(
            id="fp_base",
            companion_id="comp_123",
            identity_version=1,
            personality_vector=[0.5] * 128,
            values_vector=[0.5] * 128,
            voice_vector=[0.5] * 128,
            goals_vector=[0.5] * 128,
            boundaries_vector=[0.5] * 128,
            combined_vector=[0.5] * 768,
        )
        current = FingerprintVector(
            id="fp_curr",
            companion_id="comp_123",
            identity_version=2,
            personality_vector=[0.6] * 128,  # Shift
            values_vector=[0.3] * 128,  # Larger shift
            voice_vector=[0.5] * 128,
            goals_vector=[0.5] * 128,
            boundaries_vector=[0.5] * 128,
            combined_vector=[0.48] * 768,
        )

        drift = fingerprint_service.calculate_drift(baseline, current)

        assert isinstance(drift, DriftResult)
        assert drift.companion_id == "comp_123"
        assert drift.baseline_fingerprint_id == "fp_base"
        assert drift.current_fingerprint_id == "fp_curr"
        assert 0 <= drift.overall_drift_score <= 1
        assert drift.severity in DriftSeverity

    def test_determine_severity(self, fingerprint_service):
        assert fingerprint_service._determine_severity(0.05) == DriftSeverity.NONE
        assert fingerprint_service._determine_severity(0.15) == DriftSeverity.MINIMAL
        assert fingerprint_service._determine_severity(0.3) == DriftSeverity.MODERATE
        assert fingerprint_service._determine_severity(0.5) == DriftSeverity.SIGNIFICANT
        assert fingerprint_service._determine_severity(0.7) == DriftSeverity.CRITICAL

    def test_generate_alert(self, fingerprint_service):
        drift = DriftResult(
            id="drift_1",
            companion_id="comp_123",
            baseline_fingerprint_id="fp_base",
            current_fingerprint_id="fp_curr",
            overall_drift_score=0.55,
            severity=DriftSeverity.CRITICAL,
            dimension_drifts={
                DriftDimension.PERSONALITY: 0.3,
                DriftDimension.VALUES: 0.6,
                DriftDimension.VOICE: 0.1,
                DriftDimension.GOALS: 0.2,
                DriftDimension.BOUNDARIES: 0.15,
            },
            dimension_severities={
                DriftDimension.PERSONALITY: DriftSeverity.MODERATE,
                DriftDimension.VALUES: DriftSeverity.CRITICAL,
                DriftDimension.VOICE: DriftSeverity.NONE,
                DriftDimension.GOALS: DriftSeverity.MINIMAL,
                DriftDimension.BOUNDARIES: DriftSeverity.MINIMAL,
            },
            component_similarities={},
            significant_changes=["Values drifted critically"],
            recommended_actions=["Review values alignment"],
            requires_review=True,
            requires_reevaluation=True,
            requires_rollback=False,
            analysis_window_days=30,
        )

        alert = fingerprint_service.generate_alert(drift)

        assert isinstance(alert, DriftAlert)
        assert alert.severity == DriftSeverity.CRITICAL
        assert alert.status == DriftAlertStatus.ACTIVE
        assert DriftDimension.VALUES in alert.dimensions_affected
        assert "critically" in alert.title.lower()