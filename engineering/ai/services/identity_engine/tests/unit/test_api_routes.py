"""Unit tests for API Routes."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from fastapi.testclient import TestClient
from identity_engine.main import app
from identity_engine.models.identity import (
    IdentityConfig,
    IdentityRequest,
    IdentityResponse,
    IdentityVersion,
    IdentityStatus,
    IdentitySource,
)
from identity_engine.models.personality import PersonalityConfig
from identity_engine.models.values import ValuesConfig
from identity_engine.models.voice import VoiceProfile
from identity_engine.models.boundaries import Boundary
from identity_engine.models.goals import Goal
from identity_engine.models.fingerprint import (
    FingerprintVector,
    FingerprintResult,
    DriftResult,
    DriftSeverity,
    DriftAlert,
    DriftAlertStatus,
    DriftDimension,
)
from identity_engine.models.evolution import (
    EvolutionProposal,
    EvolutionTrigger,
    EvolutionTriggerType,
    EvolutionChange,
    EvolutionChangeType,
    EvolutionProposalStatus,
    EvolutionResult,
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_identity_service():
    with patch("identity_engine.api.routes.get_identity_service") as mock:
        service = AsyncMock()
        mock.return_value = service
        yield service


@pytest.fixture
def mock_fingerprint_service():
    with patch("identity_engine.api.routes.get_fingerprint_service") as mock:
        service = AsyncMock()
        mock.return_value = service
        yield service


@pytest.fixture
def mock_drift_service():
    with patch("identity_engine.api.routes.get_drift_service") as mock:
        service = AsyncMock()
        mock.return_value = service
        yield service


@pytest.fixture
def mock_evolution_service():
    with patch("identity_engine.api.routes.get_evolution_service") as mock:
        service = AsyncMock()
        mock.return_value = service
        yield service


@pytest.fixture
def mock_template_service():
    with patch("identity_engine.api.routes.get_template_service") as mock:
        service = MagicMock()
        mock.return_value = service
        yield service


@pytest.fixture
def sample_identity():
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
def sample_fingerprint():
    return FingerprintResult(
        fingerprint_id="fp_1",
        companion_id="comp_123",
        identity_version=1,
        components={
            "personality": [0.1] * 128,
            "values": [0.2] * 128,
            "voice": [0.3] * 128,
            "goals": [0.4] * 128,
            "boundaries": [0.5] * 128,
        },
        combined_vector=[0.25] * 768,
    )


@pytest.fixture
def sample_drift():
    return DriftResult(
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
            DriftDimension.GOALS: 0.3,
            DriftDimension.BOUNDARIES: 0.15,
        },
        dimension_severities={
            DriftDimension.PERSONALITY: DriftSeverity.MINIMAL,
            DriftDimension.VALUES: DriftSeverity.MODERATE,
            DriftDimension.VOICE: DriftSeverity.NONE,
            DriftDimension.GOALS: DriftSeverity.MINIMAL,
            DriftDimension.BOUNDARIES: DriftSeverity.MINIMAL,
        },
        component_similarities={"personality": 0.8, "values": 0.6},
        significant_changes=["Values shifted toward creativity"],
        recommended_actions=["Review values alignment"],
        requires_review=True,
        requires_reevaluation=False,
        requires_rollback=False,
        analysis_window_days=30,
    )


class TestIdentityRoutes:
    """Test Identity API routes."""

    def test_create_identity(self, client, mock_identity_service, sample_identity):
        mock_identity_service.create_identity.return_value = IdentityResponse(
            identity_id="identity_1",
            companion_id="comp_123",
            version=1,
            status=IdentityStatus.DRAFT,
            fingerprint="abc123",
            created_at=datetime.utcnow(),
        )

        response = client.post(
            "/api/v1/identity/comp_123",
            json={
                "companion_id": "comp_123",
                "name": "Test Companion",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["identity_id"] == "identity_1"
        assert data["companion_id"] == "comp_123"
        mock_identity_service.create_identity.assert_called_once()

    def test_get_identity(self, client, mock_identity_service, sample_identity):
        mock_identity_service.get_identity.return_value = sample_identity

        response = client.get("/api/v1/identity/identity_1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "identity_1"
        assert data["companion_id"] == "comp_123"

    def test_get_active_identity(self, client, mock_identity_service, sample_identity):
        mock_identity_service.get_active_identity.return_value = sample_identity

        response = client.get("/api/v1/identity/companion/comp_123/active")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "identity_1"
        mock_identity_service.get_active_identity.assert_called_once_with("comp_123")

    def test_update_identity(self, client, mock_identity_service, sample_identity):
        updated_identity = sample_identity.model_copy()
        updated_identity.name = "Updated Name"
        updated_identity.version = 2
        mock_identity_service.update_identity.return_value = updated_identity

        response = client.patch(
            "/api/v1/identity/identity_1",
            json={"name": "Updated Name"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["version"] == 2

    def test_activate_identity(self, client, mock_identity_service, sample_identity):
        sample_identity.status = IdentityStatus.ACTIVE
        mock_identity_service.activate_identity.return_value = sample_identity

        response = client.post("/api/v1/identity/identity_1/activate")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"

    def test_deactivate_identity(self, client, mock_identity_service, sample_identity):
        sample_identity.status = IdentityStatus.DEPRECATED
        mock_identity_service.deactivate_identity.return_value = sample_identity

        response = client.post("/api/v1/identity/identity_1/deactivate")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deprecated"

    def test_list_identities(self, client, mock_identity_service, sample_identity):
        mock_identity_service.list_identities.return_value = [sample_identity]

        response = client.get("/api/v1/identity/companion/comp_123")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "identity_1"

    def test_get_version_history(self, client, mock_identity_service):
        mock_versions = [
            IdentityVersion(
                id="ver_1",
                identity_id="identity_1",
                companion_id="comp_123",
                version=1,
                personality={},
                values={},
                voice={},
                boundaries=[],
                goals=[],
                change_type="create",
                change_summary="Initial",
                changed_fields=[],
                changed_by="user_123",
                created_at=datetime.utcnow(),
            )
        ]
        mock_identity_service.get_version_history.return_value = mock_versions

        response = client.get("/api/v1/identity/companion/comp_123/versions")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["version"] == 1

    def test_rollback_identity(self, client, mock_identity_service, sample_identity):
        rolled_back = sample_identity.model_copy()
        rolled_back.version = 3
        rolled_back.parent_version_id = "identity_1"
        mock_identity_service.rollback_identity.return_value = rolled_back

        response = client.post("/api/v1/identity/identity_1/rollback?target_version=1")

        assert response.status_code == 200
        data = response.json()
        assert data["version"] == 3
        assert data["parent_version_id"] == "identity_1"


class TestTemplateRoutes:
    """Test Template API routes."""

    def test_list_templates(self, client, mock_template_service):
        mock_template_service.get_builtin_templates.return_value = {
            "supportive_companion": {"id": "supportive_companion", "name": "Supportive Companion"},
            "professional_assistant": {"id": "professional_assistant", "name": "Professional Assistant"},
        }

        response = client.get("/api/v1/templates/")

        assert response.status_code == 200
        data = response.json()
        assert "supportive_companion" in data
        assert "professional_assistant" in data

    def test_get_template(self, client, mock_template_service):
        mock_template_service.get_template.return_value = {
            "id": "supportive_companion",
            "name": "Supportive Companion",
            "description": "A supportive companion",
        }

        response = client.get("/api/v1/templates/supportive_companion")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "supportive_companion"
        assert data["name"] == "Supportive Companion"

    def test_get_template_not_found(self, client, mock_template_service):
        mock_template_service.get_template.return_value = None

        response = client.get("/api/v1/templates/nonexistent")

        assert response.status_code == 404

    def test_create_identity_from_template(self, client, mock_template_service, sample_identity):
        mock_template_service.create_identity_from_template.return_value = sample_identity

        response = client.post(
            "/api/v1/templates/supportive_companion/create",
            json={"companion_id": "comp_123", "name": "My Companion"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "identity_1"

    def test_list_templates_by_category(self, client, mock_template_service):
        mock_template_service.list_templates.return_value = [
            {"id": "t1", "name": "Template 1", "category": "companion"},
        ]

        response = client.get("/api/v1/templates/?category=companion")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["category"] == "companion"

    def test_get_categories(self, client, mock_template_service):
        mock_template_service.get_categories.return_value = ["companion", "assistant", "partner"]

        response = client.get("/api/v1/templates/categories")

        assert response.status_code == 200
        data = response.json()
        assert "companion" in data
        assert "assistant" in data


class TestFingerprintRoutes:
    """Test Fingerprint API routes."""

    def test_generate_fingerprint(self, client, mock_fingerprint_service, sample_fingerprint):
        mock_fingerprint_service.generate_fingerprint.return_value = sample_fingerprint

        response = client.post("/api/v1/fingerprint/comp_123/generate?version=1")

        assert response.status_code == 200
        data = response.json()
        assert data["fingerprint_id"] == "fp_1"
        assert data["companion_id"] == "comp_123"

    def test_get_fingerprint(self, client, mock_fingerprint_service, sample_fingerprint):
        mock_fingerprint_service.get_fingerprint.return_value = sample_fingerprint

        response = client.get("/api/v1/fingerprint/fp_1")

        assert response.status_code == 200
        data = response.json()
        assert data["fingerprint_id"] == "fp_1"


class TestDriftRoutes:
    """Test Drift API routes."""

    def test_check_drift(self, client, mock_drift_service, sample_drift):
        mock_drift_service.check_drift.return_value = sample_drift

        response = client.post("/api/v1/drift/comp_123/check?baseline_version=1&current_version=2")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "drift_1"
        assert data["severity"] == "moderate"

    def test_get_drift_history(self, client, mock_drift_service, sample_drift):
        mock_drift_service.get_drift_history.return_value = [sample_drift]

        response = client.get("/api/v1/drift/comp_123/history?days=30")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "drift_1"

    def test_get_active_alerts(self, client, mock_drift_service):
        mock_alerts = [
            DriftAlert(
                id="alert_1",
                companion_id="comp_123",
                drift_result_id="drift_1",
                severity=DriftSeverity.MODERATE,
                title="Moderate drift",
                message="Values drifted",
                dimensions_affected=[DriftDimension.VALUES],
                status=DriftAlertStatus.ACTIVE,
            )
        ]
        mock_drift_service.get_active_alerts.return_value = mock_alerts

        response = client.get("/api/v1/drift/alerts?companion_id=comp_123")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "alert_1"

    def test_acknowledge_alert(self, client, mock_drift_service):
        mock_drift_service.acknowledge_alert.return_value = True

        response = client.post("/api/v1/drift/alerts/alert_1/acknowledge?acknowledged_by=user_123")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_resolve_alert(self, client, mock_drift_service):
        mock_drift_service.resolve_alert.return_value = True

        response = client.post(
            "/api/v1/drift/alerts/alert_1/resolve",
            json={"resolved_by": "user_123", "resolution_notes": "Fixed"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_companions_with_drift(self, client, mock_drift_service):
        mock_drift_service.get_companions_with_drift.return_value = [
            {"companion_id": "comp_1", "latest_drift": {"id": "drift_1"}},
        ]

        response = client.get("/api/v1/drift/companions?severity=moderate")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["companion_id"] == "comp_1"


class TestEvolutionRoutes:
    """Test Evolution API routes."""

    def test_create_proposal(self, client, mock_evolution_service):
        mock_proposal = EvolutionProposal(
            id="prop_1",
            companion_id="comp_123",
            identity_id="identity_1",
            baseline_version=1,
            name="Increase Openness",
            description="Make more creative",
            trigger=EvolutionTrigger(
                type=EvolutionTriggerType.USER_FEEDBACK,
                trigger_id="fb_1",
                description="User feedback",
            ),
            changes=[
                EvolutionChange(
                    id="change_1",
                    type=EvolutionChangeType.MODIFY_PERSONALITY,
                    target="big_five.openness",
                    current_value=0.5,
                    proposed_value=0.7,
                    rationale="User wants creativity",
                    impact_score=0.3,
                    risk_level="low",
                )
            ],
            status=EvolutionProposalStatus.PENDING_REVIEW,
            overall_impact_score=0.3,
            overall_risk_level="low",
            required_approvals=2,
            approval_count=0,
            rejection_count=0,
            reviewer_ids=[],
            review_notes={},
            created_by="user_123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_evolution_service.create_proposal.return_value = mock_proposal

        response = client.post(
            "/api/v1/evolution/comp_123/proposals",
            json={
                "identity_id": "identity_1",
                "baseline_version": 1,
                "name": "Increase Openness",
                "description": "Make more creative",
                "trigger": {
                    "type": "user_feedback",
                    "trigger_id": "fb_1",
                    "description": "User feedback",
                },
                "changes": [
                    {
                        "type": "modify_personality",
                        "target": "big_five.openness",
                        "current_value": 0.5,
                        "proposed_value": 0.7,
                        "rationale": "User wants creativity",
                        "impact_score": 0.3,
                        "risk_level": "low",
                    }
                ],
                "created_by": "user_123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "prop_1"
        assert data["status"] == "pending_review"

    def test_get_proposal(self, client, mock_evolution_service):
        mock_proposal = MagicMock()
        mock_proposal.id = "prop_1"
        mock_proposal.model_dump.return_value = {"id": "prop_1", "status": "pending_review"}
        mock_evolution_service.get_proposal.return_value = mock_proposal

        response = client.get("/api/v1/evolution/proposals/prop_1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "prop_1"

    def test_list_proposals(self, client, mock_evolution_service):
        mock_proposals = [
            MagicMock(model_dump=lambda: {"id": "prop_1", "status": "pending_review"}),
            MagicMock(model_dump=lambda: {"id": "prop_2", "status": "approved"}),
        ]
        mock_evolution_service.list_proposals.return_value = mock_proposals

        response = client.get("/api/v1/evolution/comp_123/proposals?status=pending_review")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_approve_proposal(self, client, mock_evolution_service):
        mock_proposal = MagicMock()
        mock_proposal.model_dump.return_value = {"id": "prop_1", "status": "approved", "approval_count": 2}
        mock_evolution_service.approve_proposal.return_value = mock_proposal

        response = client.post(
            "/api/v1/evolution/proposals/prop_1/approve",
            json={"reviewer_id": "reviewer_2", "notes": "Looks good"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"
        assert data["approval_count"] == 2

    def test_reject_proposal(self, client, mock_evolution_service):
        mock_proposal = MagicMock()
        mock_proposal.model_dump.return_value = {"id": "prop_1", "status": "rejected", "rejection_count": 1}
        mock_evolution_service.reject_proposal.return_value = mock_proposal

        response = client.post(
            "/api/v1/evolution/proposals/prop_1/reject",
            json={"reviewer_id": "reviewer_1", "notes": "Too risky"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"
        assert data["rejection_count"] == 1

    def test_implement_proposal(self, client, mock_evolution_service):
        mock_result = EvolutionResult(
            id="result_1",
            proposal_id="prop_1",
            companion_id="comp_123",
            status="implemented",
            implemented_changes=["change_1"],
            failed_changes=[],
            previous_version=1,
            new_version=2,
            post_implementation_validation={"valid": True},
            validation_errors=[],
            validation_warnings=[],
            implemented_at=datetime.utcnow(),
            implemented_by="system",
            duration_ms=150,
        )
        mock_evolution_service.implement_proposal.return_value = mock_result

        response = client.post("/api/v1/evolution/proposals/prop_1/implement?implemented_by=system")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "implemented"
        assert data["new_version"] == 2

    def test_rollback_proposal(self, client, mock_evolution_service):
        mock_result = EvolutionResult(
            id="result_1",
            proposal_id="prop_1",
            companion_id="comp_123",
            status="rolled_back",
            implemented_changes=[],
            failed_changes=[],
            previous_version=2,
            new_version=1,
            post_implementation_validation={},
            validation_errors=[],
            validation_warnings=[],
            rollback_reason="User reported issues",
            rollback_version=1,
            implemented_at=datetime.utcnow(),
            implemented_by="system",
            duration_ms=100,
        )
        mock_evolution_service.rollback_proposal.return_value = mock_result

        response = client.post(
            "/api/v1/evolution/proposals/prop_1/rollback",
            json={"implemented_by": "system", "reason": "User reported issues"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rolled_back"
        assert data["rollback_reason"] == "User reported issues"

    def test_get_evolution_history(self, client, mock_evolution_service):
        mock_results = [
            MagicMock(model_dump=lambda: {"id": "result_1", "new_version": 2}),
            MagicMock(model_dump=lambda: {"id": "result_2", "new_version": 3}),
        ]
        mock_evolution_service.get_evolution_history.return_value = mock_results

        response = client.get("/api/v1/evolution/comp_123/history?limit=10")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_pending_proposals(self, client, mock_evolution_service):
        mock_proposals = [
            MagicMock(model_dump=lambda: {"id": "prop_1", "status": "pending_review"}),
        ]
        mock_evolution_service.get_pending_proposals.return_value = mock_proposals

        response = client.get("/api/v1/evolution/comp_123/pending")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1


class TestHealthRoutes:
    """Test Health check routes."""

    def test_health_live(self, client):
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"

    def test_health_ready(self, client):
        response = client.get("/health/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"

    def test_metrics(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]