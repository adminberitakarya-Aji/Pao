"""Unit tests for Drift Service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from identity_engine.services.drift_service import DriftService
from identity_engine.models.fingerprint import (
    FingerprintVector,
    DriftDimension,
    DriftSeverity,
    DriftResult,
    DriftAlert,
    DriftAlertStatus,
)
from identity_engine.models.identity import IdentityConfig
from identity_engine.models.personality import PersonalityConfig
from identity_engine.models.values import ValuesConfig
from identity_engine.models.voice import VoiceProfile


class TestDriftService:
    """Test DriftService."""

    @pytest.fixture
    def drift_service(self):
        return DriftService()

    @pytest.fixture
    def mock_repo(self):
        return AsyncMock()

    @pytest.fixture
    def sample_fingerprints(self):
        base = FingerprintVector(
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
            personality_vector=[0.6] * 128,
            values_vector=[0.3] * 128,
            voice_vector=[0.5] * 128,
            goals_vector=[0.5] * 128,
            boundaries_vector=[0.5] * 128,
            combined_vector=[0.48] * 768,
        )
        return base, current

    @pytest.mark.asyncio
    async def test_check_drift(self, drift_service, mock_repo, sample_fingerprints):
        base_fp, current_fp = sample_fingerprints
        mock_repo.get_fingerprint_by_version.side_effect = [base_fp, current_fp]
        mock_repo.save_drift_result.return_value = None
        mock_repo.save_drift_alert.return_value = None
        drift_service.repository = mock_repo

        # Mock fingerprint service
        drift_service.fingerprint_service = MagicMock()
        drift_service.fingerprint_service.calculate_drift.return_value = MagicMock(
            id="drift_1",
            companion_id="comp_123",
            baseline_fingerprint_id="fp_base",
            current_fingerprint_id="fp_curr",
            overall_drift_score=0.35,
            severity=DriftSeverity.MODERATE,
            dimension_drifts={},
            dimension_severities={},
            component_similarities={},
            significant_changes=[],
            recommended_actions=[],
            requires_review=False,
            requires_reevaluation=False,
            requires_rollback=False,
            analysis_window_days=30,
        )
        drift_service.fingerprint_service.generate_alert.return_value = None

        result = await drift_service.check_drift("comp_123", baseline_version=1, current_version=2)

        assert result is not None
        assert result.companion_id == "comp_123"
        mock_repo.get_fingerprint_by_version.assert_any_call("comp_123", 1)
        mock_repo.get_fingerprint_by_version.assert_any_call("comp_123", 2)

    @pytest.mark.asyncio
    async def test_check_drift_no_baseline(self, drift_service, mock_repo):
        mock_repo.get_fingerprint_by_version.side_effect = [None, MagicMock()]
        mock_repo.get_latest_fingerprint.return_value = MagicMock()
        drift_service.repository = mock_repo

        result = await drift_service.check_drift("comp_123")

        assert result is not None
        mock_repo.get_latest_fingerprint.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_drift_history(self, drift_service, mock_repo):
        mock_drift_results = [
            MagicMock(
                id="drift_1",
                companion_id="comp_123",
                overall_drift_score=0.2,
            ),
            MagicMock(
                id="drift_2",
                companion_id="comp_123",
                overall_drift_score=0.35,
            ),
        ]
        mock_repo.get_drift_history.return_value = mock_drift_results
        drift_service.repository = mock_repo

        history = await drift_service.get_drift_history("comp_123", days=30)

        assert len(history) == 2
        mock_repo.get_drift_history.assert_called_once_with("comp_123", 30)

    @pytest.mark.asyncio
    async def test_acknowledge_alert(self, drift_service, mock_repo):
        mock_repo.acknowledge_drift_alert.return_value = True
        drift_service.repository = mock_repo

        result = await drift_service.acknowledge_alert("alert_1", "user_123")

        assert result is True
        mock_repo.acknowledge_drift_alert.assert_called_once_with("alert_1", "user_123")

    @pytest.mark.asyncio
    async def test_resolve_alert(self, drift_service, mock_repo):
        mock_repo.resolve_drift_alert.return_value = True
        drift_service.repository = mock_repo

        result = await drift_service.resolve_alert("alert_1", "user_123", "Fixed")

        assert result is True
        mock_repo.resolve_drift_alert.assert_called_once_with("alert_1", "user_123", "Fixed")

    @pytest.mark.asyncio
    async def test_get_active_alerts(self, drift_service, mock_repo):
        mock_alerts = [
            MagicMock(id="alert_1", status=DriftAlertStatus.ACTIVE),
            MagicMock(id="alert_2", status=DriftAlertStatus.ACTIVE),
        ]
        mock_repo.get_active_drift_alerts.return_value = mock_alerts
        drift_service.repository = mock_repo

        alerts = await drift_service.get_active_alerts("comp_123")

        assert len(alerts) == 2
        mock_repo.get_active_drift_alerts.assert_called_once_with(companion_id="comp_123", severity=None)

    @pytest.mark.asyncio
    async def test_get_companions_with_drift(self, drift_service, mock_repo):
        mock_companions = [
            {"companion_id": "comp_1", "latest_drift": MagicMock()},
            {"companion_id": "comp_2", "latest_drift": MagicMock()},
        ]
        mock_repo.get_companions_with_recent_drift.return_value = mock_companions
        drift_service.repository = mock_repo

        companions = await drift_service.get_companions_with_drift("moderate")

        assert len(companions) == 2
        mock_repo.get_companions_with_recent_drift.assert_called_once_with("moderate")