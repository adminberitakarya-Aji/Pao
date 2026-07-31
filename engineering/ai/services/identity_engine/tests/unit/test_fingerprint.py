"""Unit tests for Fingerprint models."""

import pytest
from pydantic import ValidationError
import numpy as np

from identity_engine.models.fingerprint import (
    FingerprintVector,
    FingerprintResult,
    DriftResult,
    DriftDimension,
    DriftSeverity,
    DriftAlert,
    DRIFT_SEVERITY_THRESHOLDS,
    compute_drift_severity,
    compute_dimension_drift,
)


class TestFingerprintVector:
    """Test FingerprintVector model."""

    def test_valid_fingerprint(self):
        fp = FingerprintVector(
            id="fp_1",
            companion_id="comp_123",
            identity_version=1,
            personality_vector=[0.1] * 128,
            values_vector=[0.2] * 128,
            voice_vector=[0.3] * 128,
            goals_vector=[0.4] * 128,
            boundaries_vector=[0.5] * 128,
            combined_vector=[0.25] * 640,  # 128 * 5 = 640
            vector_dimension=640,
        )
        assert fp.vector_dimension == 640
        assert len(fp.combined_vector) == 640
        assert fp.companion_id == "comp_123"

    def test_cosine_similarity(self):
        fp1 = FingerprintVector(
            id="fp_1",
            companion_id="comp_123",
            identity_version=1,
            personality_vector=[1.0, 0.0],
            values_vector=[0.0, 0.0],
            voice_vector=[0.0, 0.0],
            goals_vector=[0.0, 0.0],
            boundaries_vector=[0.0, 0.0],
            combined_vector=[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            vector_dimension=10,
        )
        fp2 = FingerprintVector(
            id="fp_2",
            companion_id="comp_123",
            identity_version=2,
            personality_vector=[0.0, 1.0],
            values_vector=[0.0, 0.0],
            voice_vector=[0.0, 0.0],
            goals_vector=[0.0, 0.0],
            boundaries_vector=[0.0, 0.0],
            combined_vector=[0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            vector_dimension=10,
        )
        # Orthogonal vectors should have similarity 0
        sim = fp1.cosine_similarity(fp2)
        assert sim == 0.0

        # Same vectors should have similarity 1
        sim = fp1.cosine_similarity(fp1)
        assert sim == 1.0

    def test_euclidean_distance(self):
        fp1 = FingerprintVector(
            id="fp_1",
            companion_id="comp_123",
            identity_version=1,
            personality_vector=[1.0, 0.0],
            values_vector=[0.0, 0.0],
            voice_vector=[0.0, 0.0],
            goals_vector=[0.0, 0.0],
            boundaries_vector=[0.0, 0.0],
            combined_vector=[1.0] + [0.0] * 9,
            vector_dimension=10,
        )
        fp2 = FingerprintVector(
            id="fp_2",
            companion_id="comp_123",
            identity_version=2,
            personality_vector=[0.0, 1.0],
            values_vector=[0.0, 0.0],
            voice_vector=[0.0, 0.0],
            goals_vector=[0.0, 0.0],
            boundaries_vector=[0.0, 0.0],
            combined_vector=[0.0, 1.0] + [0.0] * 8,
            vector_dimension=10,
        )
        dist = fp1.euclidean_distance(fp2)
        expected = np.sqrt(2)
        assert abs(dist - expected) < 0.01

    def test_component_similarities(self):
        fp1 = FingerprintVector(
            id="fp_1",
            companion_id="comp_123",
            identity_version=1,
            personality_vector=[1.0, 0.0],
            values_vector=[0.0, 1.0],
            voice_vector=[0.0, 0.0],
            goals_vector=[0.0, 0.0],
            boundaries_vector=[0.0, 0.0],
            combined_vector=[1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            vector_dimension=10,
        )
        fp2 = FingerprintVector(
            id="fp_2",
            companion_id="comp_123",
            identity_version=2,
            personality_vector=[0.0, 1.0],
            values_vector=[1.0, 0.0],
            voice_vector=[0.0, 0.0],
            goals_vector=[0.0, 0.0],
            boundaries_vector=[0.0, 0.0],
            combined_vector=[0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            vector_dimension=10,
        )
        similarities = fp1.component_similarities(fp2)
        assert similarities["personality"] == 0.0  # orthogonal
        assert similarities["values"] == 0.0  # orthogonal


class TestFingerprintResult:
    """Test FingerprintResult model."""

    def test_valid_result(self):
        fp = FingerprintVector(
            id="fp_1",
            companion_id="comp_123",
            identity_version=1,
            personality_vector=[0.1] * 128,
            values_vector=[0.2] * 128,
            voice_vector=[0.3] * 128,
            goals_vector=[0.4] * 128,
            boundaries_vector=[0.5] * 128,
            combined_vector=[0.25] * 640,
            vector_dimension=640,
        )
        result = FingerprintResult(
            fingerprint=fp,
            computation_time_ms=150.5,
            source_data={"interactions": 100},
            quality_score=0.95,
            warnings=[],
        )
        assert result.fingerprint.id == "fp_1"
        assert result.computation_time_ms == 150.5
        assert result.quality_score == 0.95

    def test_defaults(self):
        fp = FingerprintVector(
            id="fp_1",
            companion_id="comp_123",
            identity_version=1,
            personality_vector=[0.1] * 128,
            values_vector=[0.2] * 128,
            voice_vector=[0.3] * 128,
            goals_vector=[0.4] * 128,
            boundaries_vector=[0.5] * 128,
            combined_vector=[0.25] * 640,
            vector_dimension=640,
        )
        result = FingerprintResult(fingerprint=fp)
        assert result.quality_score == 1.0
        assert result.warnings == []


class TestDriftResult:
    """Test DriftResult model."""

    def test_valid_drift_result(self):
        drift = DriftResult(
            id="drift_1",
            companion_id="comp_123",
            baseline_fingerprint_id="fp_base",
            current_fingerprint_id="fp_curr",
            overall_drift_score=0.35,
            severity=DriftSeverity.MODERATE,
            dimension_drifts={
                DriftDimension.PERSONALITY: 0.2,
                DriftDimension.VALUES: 0.4,
                DriftDimension.VOICE: 0.1,
                DriftDimension.BEHAVIOR: 0.3,
                DriftDimension.BOUNDARIES: 0.15,
                DriftDimension.GOALS: 0.25,
                DriftDimension.KNOWLEDGE: 0.05,
                DriftDimension.RELATIONSHIP: 0.1,
            },
            dimension_severities={
                DriftDimension.PERSONALITY: DriftSeverity.MINOR,
                DriftDimension.VALUES: DriftSeverity.MODERATE,
                DriftDimension.VOICE: DriftSeverity.NONE,
                DriftDimension.BEHAVIOR: DriftSeverity.MINOR,
                DriftDimension.BOUNDARIES: DriftSeverity.MINOR,
                DriftDimension.GOALS: DriftSeverity.MINOR,
                DriftDimension.KNOWLEDGE: DriftSeverity.NONE,
                DriftDimension.RELATIONSHIP: DriftSeverity.NONE,
            },
            component_similarities={"personality": 0.8, "values": 0.6},
            significant_changes=["Values shifted toward creativity"],
            recommended_actions=["Review values alignment"],
            requires_review=True,
            requires_reevaluation=False,
            requires_rollback=False,
            analysis_window_days=30,
            interaction_count=500,
        )
        assert drift.overall_drift_score == 0.35
        assert drift.severity == DriftSeverity.MODERATE
        assert drift.requires_review is True
        assert drift.interaction_count == 500

    def test_get_top_drifted_dimensions(self):
        drift = DriftResult(
            id="drift_1",
            companion_id="comp_123",
            baseline_fingerprint_id="fp_base",
            current_fingerprint_id="fp_curr",
            overall_drift_score=0.35,
            severity=DriftSeverity.MODERATE,
            dimension_drifts={
                DriftDimension.PERSONALITY: 0.2,
                DriftDimension.VALUES: 0.5,
                DriftDimension.VOICE: 0.1,
                DriftDimension.BEHAVIOR: 0.3,
                DriftDimension.BOUNDARIES: 0.15,
                DriftDimension.GOALS: 0.25,
                DriftDimension.KNOWLEDGE: 0.05,
                DriftDimension.RELATIONSHIP: 0.1,
            },
            dimension_severities={},
        )
        top = drift.get_top_drifted_dimensions(3)
        assert len(top) == 3
        assert top[0][0] == DriftDimension.VALUES
        assert top[0][1] == 0.5
        assert top[1][0] == DriftDimension.BEHAVIOR
        assert top[2][0] == DriftDimension.GOALS

    def test_is_critical(self):
        drift = DriftResult(
            id="drift_1",
            companion_id="comp_123",
            baseline_fingerprint_id="fp_base",
            current_fingerprint_id="fp_curr",
            overall_drift_score=0.6,
            severity=DriftSeverity.CRITICAL,
            dimension_drifts={},
            dimension_severities={},
        )
        assert drift.is_critical() is True

        drift2 = DriftResult(
            id="drift_2",
            companion_id="comp_123",
            baseline_fingerprint_id="fp_base",
            current_fingerprint_id="fp_curr",
            overall_drift_score=0.3,
            severity=DriftSeverity.SIGNIFICANT,
            dimension_drifts={},
            dimension_severities={},
            requires_rollback=True,
        )
        assert drift2.is_critical() is True


class TestDriftAlert:
    """Test DriftAlert model."""

    def test_valid_alert(self):
        alert = DriftAlert(
            id="alert_1",
            companion_id="comp_123",
            drift_result_id="drift_1",
            severity=DriftSeverity.SIGNIFICANT,
            title="Significant values drift detected",
            message="Values have shifted significantly",
            dimensions_affected=[DriftDimension.VALUES, DriftDimension.GOALS],
            status="active",
        )
        assert alert.severity == DriftSeverity.SIGNIFICANT
        assert alert.status == "active"
        assert len(alert.dimensions_affected) == 2

    def test_alert_defaults(self):
        alert = DriftAlert(
            companion_id="comp_123",
            drift_result_id="drift_1",
            severity=DriftSeverity.MODERATE,
            title="Test alert",
            message="Test message",
            dimensions_affected=[DriftDimension.PERSONALITY],
        )
        assert alert.status == "active"
        assert alert.acknowledged_at is None
        assert alert.resolved_at is None
        assert alert.acknowledged_by is None
        assert alert.resolved_by is None


class TestDriftSeverityThresholds:
    """Test drift severity thresholds."""

    def test_thresholds_exist(self):
        assert DriftSeverity.NONE in DRIFT_SEVERITY_THRESHOLDS
        assert DriftSeverity.MINOR in DRIFT_SEVERITY_THRESHOLDS
        assert DriftSeverity.MODERATE in DRIFT_SEVERITY_THRESHOLDS
        assert DriftSeverity.SIGNIFICANT in DRIFT_SEVERITY_THRESHOLDS
        assert DriftSeverity.CRITICAL in DRIFT_SEVERITY_THRESHOLDS

    def test_threshold_ranges(self):
        assert DRIFT_SEVERITY_THRESHOLDS[DriftSeverity.NONE] == (0.0, 0.05)
        assert DRIFT_SEVERITY_THRESHOLDS[DriftSeverity.MINOR] == (0.05, 0.15)
        assert DRIFT_SEVERITY_THRESHOLDS[DriftSeverity.MODERATE] == (0.15, 0.30)
        assert DRIFT_SEVERITY_THRESHOLDS[DriftSeverity.SIGNIFICANT] == (0.30, 0.50)
        assert DRIFT_SEVERITY_THRESHOLDS[DriftSeverity.CRITICAL] == (0.50, 1.0)


class TestComputeDriftSeverity:
    """Test compute_drift_severity function."""

    def test_none_severity(self):
        assert compute_drift_severity(0.0) == DriftSeverity.NONE
        assert compute_drift_severity(0.03) == DriftSeverity.NONE

    def test_minor_severity(self):
        assert compute_drift_severity(0.05) == DriftSeverity.MINOR
        assert compute_drift_severity(0.1) == DriftSeverity.MINOR
        assert compute_drift_severity(0.14) == DriftSeverity.MINOR

    def test_moderate_severity(self):
        assert compute_drift_severity(0.15) == DriftSeverity.MODERATE
        assert compute_drift_severity(0.2) == DriftSeverity.MODERATE
        assert compute_drift_severity(0.29) == DriftSeverity.MODERATE

    def test_significant_severity(self):
        assert compute_drift_severity(0.3) == DriftSeverity.SIGNIFICANT
        assert compute_drift_severity(0.4) == DriftSeverity.SIGNIFICANT
        assert compute_drift_severity(0.49) == DriftSeverity.SIGNIFICANT

    def test_critical_severity(self):
        assert compute_drift_severity(0.5) == DriftSeverity.CRITICAL
        assert compute_drift_severity(0.7) == DriftSeverity.CRITICAL
        assert compute_drift_severity(1.0) == DriftSeverity.CRITICAL


class TestComputeDimensionDrift:
    """Test compute_dimension_drift function."""

    def test_identical_vectors(self):
        v1 = [1.0, 0.0, 0.0]
        v2 = [1.0, 0.0, 0.0]
        drift = compute_dimension_drift(v1, v2)
        assert drift == 0.0

    def test_orthogonal_vectors(self):
        v1 = [1.0, 0.0]
        v2 = [0.0, 1.0]
        drift = compute_dimension_drift(v1, v2)
        assert drift == 1.0

    def test_opposite_vectors(self):
        v1 = [1.0, 0.0]
        v2 = [-1.0, 0.0]
        drift = compute_dimension_drift(v1, v2)
        assert drift == 2.0  # 1 - (-1) = 2

    def test_partial_similarity(self):
        v1 = [1.0, 0.0]
        v2 = [0.707, 0.707]  # 45 degrees
        drift = compute_dimension_drift(v1, v2)
        expected = 1.0 - 0.707
        assert abs(drift - expected) < 0.01

    def test_different_lengths(self):
        v1 = [1.0, 0.0, 0.0, 0.0]
        v2 = [0.0, 1.0]  # shorter
        drift = compute_dimension_drift(v1, v2)
        # Should use first 2 elements
        assert drift == 1.0
