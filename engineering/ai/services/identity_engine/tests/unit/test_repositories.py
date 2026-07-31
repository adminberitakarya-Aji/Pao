"""Unit tests for Repositories."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from identity_engine.repositories.base import BaseRepository
from identity_engine.repositories.memory import MemoryRepository
from identity_engine.models.identity import (
    IdentityConfig,
    IdentityVersion,
    IdentityStatus,
    IdentitySource,
)
from identity_engine.models.personality import PersonalityConfig
from identity_engine.models.values import ValuesConfig
from identity_engine.models.voice import VoiceProfile
from identity_engine.models.boundaries import Boundary
from identity_engine.models.goals import Goal
from identity_engine.models.fingerprint import FingerprintVector, DriftResult, DriftSeverity, DriftAlert
from identity_engine.models.evolution import EvolutionProposal, EvolutionResult, EvolutionEvidence, EvolutionRule


class TestBaseRepository:
    """Test BaseRepository abstract class."""

    def test_base_repository_is_abstract(self):
        """Verify BaseRepository cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseRepository()


class TestMemoryRepository:
    """Test MemoryRepository implementation."""

    @pytest.fixture
    def repo(self):
        return MemoryRepository()

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
            name="Test",
            status=IdentityStatus.DRAFT,
            source=IdentitySource.USER_CREATED,
        )

    @pytest.mark.asyncio
    async def test_save_and_get_identity(self, repo, sample_identity):
        await repo.save(sample_identity)
        retrieved = await repo.get("identity_1")
        assert retrieved is not None
        assert retrieved.id == "identity_1"
        assert retrieved.companion_id == "comp_123"

    @pytest.mark.asyncio
    async def test_get_nonexistent_identity(self, repo):
        retrieved = await repo.get("nonexistent")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_get_active_identity(self, repo, sample_identity):
        sample_identity.status = IdentityStatus.ACTIVE
        await repo.save(sample_identity)

        active = await repo.get_active("comp_123")
        assert active is not None
        assert active.status == IdentityStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_get_version(self, repo, sample_identity):
        await repo.save(sample_identity)
        versioned = await repo.get_version("comp_123", 1)
        assert versioned is not None
        assert versioned.version == 1

    @pytest.mark.asyncio
    async def test_list_identities(self, repo, sample_identity):
        await repo.save(sample_identity)
        identities = await repo.list(companion_id="comp_123")
        assert len(identities) == 1
        assert identities[0].id == "identity_1"

    @pytest.mark.asyncio
    async def test_deactivate_companion_identities(self, repo, sample_identity):
        sample_identity.status = IdentityStatus.ACTIVE
        await repo.save(sample_identity)

        await repo.deactivate_companion_identities("comp_123")

        active = await repo.get_active("comp_123")
        assert active is None or active.status != IdentityStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_get_identities_by_companion(self, repo, sample_identity):
        await repo.save(sample_identity)
        identities = await repo.get_identities_by_companion("comp_123")
        assert len(identities) == 1

    @pytest.mark.asyncio
    async def test_save_and_get_version(self, repo):
        version = IdentityVersion(
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
        await repo.save_version(version)
        history = await repo.get_version_history("comp_123")
        assert len(history) == 1
        assert history[0].version == 1

    @pytest.mark.asyncio
    async def test_save_and_get_fingerprint(self, repo, sample_fingerprint):
        await repo.save_fingerprint(sample_fingerprint)
        retrieved = await repo.get_fingerprint("fp_1")
        assert retrieved is not None
        assert retrieved.id == "fp_1"

    @pytest.mark.asyncio
    async def test_get_fingerprint_by_version(self, repo, sample_fingerprint):
        await repo.save_fingerprint(sample_fingerprint)
        retrieved = await repo.get_fingerprint_by_version("comp_123", 1)
        assert retrieved is not None
        assert retrieved.identity_version == 1

    @pytest.mark.asyncio
    async def test_get_latest_fingerprint(self, repo):
        fp1 = FingerprintVector(
            id="fp_1",
            companion_id="comp_123",
            identity_version=1,
            personality_vector=[0.1]*128,
            values_vector=[0.1]*128,
            voice_vector=[0.1]*128,
            goals_vector=[0.1]*128,
            boundaries_vector=[0.1]*128,
            combined_vector=[0.1]*768,
        )
        fp2 = FingerprintVector(
            id="fp_2",
            companion_id="comp_123",
            identity_version=2,
            personality_vector=[0.2]*128,
            values_vector=[0.2]*128,
            voice_vector=[0.2]*128,
            goals_vector=[0.2]*128,
            boundaries_vector=[0.2]*128,
            combined_vector=[0.2]*768,
        )
        await repo.save_fingerprint(fp1)
        await repo.save_fingerprint(fp2)

        latest = await repo.get_latest_fingerprint("comp_123")
        assert latest is not None
        assert latest.identity_version == 2

    @pytest.mark.asyncio
    async def test_get_earliest_fingerprint(self, repo):
        fp1 = FingerprintVector(
            id="fp_1",
            companion_id="comp_123",
            identity_version=1,
            personality_vector=[0.1]*128,
            values_vector=[0.1]*128,
            voice_vector=[0.1]*128,
            goals_vector=[0.1]*128,
            boundaries_vector=[0.1]*128,
            combined_vector=[0.1]*768,
        )
        fp2 = FingerprintVector(
            id="fp_2",
            companion_id="comp_123",
            identity_version=2,
            personality_vector=[0.2]*128,
            values_vector=[0.2]*128,
            voice_vector=[0.2]*128,
            goals_vector=[0.2]*128,
            boundaries_vector=[0.2]*128,
            combined_vector=[0.2]*768,
        )
        await repo.save_fingerprint(fp1)
        await repo.save_fingerprint(fp2)

        earliest = await repo.get_earliest_fingerprint("comp_123")
        assert earliest is not None
        assert earliest.identity_version == 1

    @pytest.mark.asyncio
    async def test_save_and_get_drift_result(self, repo):
        drift = DriftResult(
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
        await repo.save_drift_result(drift)
        retrieved = await repo.get_latest_drift("comp_123")
        assert retrieved is not None
        assert retrieved.id == "drift_1"

    @pytest.mark.asyncio
    async def test_get_drift_history(self, repo):
        drift1 = DriftResult(
            id="drift_1",
            companion_id="comp_123",
            baseline_fingerprint_id="fp_base",
            current_fingerprint_id="fp_curr",
            overall_drift_score=0.2,
            severity=DriftSeverity.MINIMAL,
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
        drift2 = DriftResult(
            id="drift_2",
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
        await repo.save_drift_result(drift1)
        await repo.save_drift_result(drift2)

        history = await repo.get_drift_history("comp_123", days=30)
        assert len(history) == 2

    @pytest.mark.asyncio
    async def test_save_and_get_drift_alert(self, repo):
        alert = DriftAlert(
            id="alert_1",
            companion_id="comp_123",
            drift_result_id="drift_1",
            severity=DriftSeverity.MODERATE,
            title="Test Alert",
            message="Drift detected",
            dimensions_affected=[],
            status="active",
        )
        await repo.save_drift_alert(alert)
        alerts = await repo.get_active_drift_alerts(companion_id="comp_123")
        assert len(alerts) == 1
        assert alerts[0].id == "alert_1"

    @pytest.mark.asyncio
    async def test_acknowledge_drift_alert(self, repo):
        alert = DriftAlert(
            id="alert_1",
            companion_id="comp_123",
            drift_result_id="drift_1",
            severity=DriftSeverity.MODERATE,
            title="Test Alert",
            message="Drift detected",
            dimensions_affected=[],
            status="active",
        )
        await repo.save_drift_alert(alert)

        result = await repo.acknowledge_drift_alert("alert_1", "user_123")
        assert result is True

        alerts = await repo.get_active_drift_alerts(companion_id="comp_123")
        assert len(alerts) == 0  # Should be acknowledged

    @pytest.mark.asyncio
    async def test_resolve_drift_alert(self, repo):
        alert = DriftAlert(
            id="alert_1",
            companion_id="comp_123",
            drift_result_id="drift_1",
            severity=DriftSeverity.MODERATE,
            title="Test Alert",
            message="Drift detected",
            dimensions_affected=[],
            status="active",
        )
        await repo.save_drift_alert(alert)

        result = await repo.resolve_drift_alert("alert_1", "user_123", "Fixed")
        assert result is True

        alerts = await repo.get_active_drift_alerts(companion_id="comp_123")
        assert len(alerts) == 0

    @pytest.mark.asyncio
    async def test_save_evolution_proposal(self, repo):
        proposal = EvolutionProposal(
            id="prop_1",
            companion_id="comp_123",
            identity_id="identity_1",
            baseline_version=1,
            name="Test Proposal",
            description="Test",
            trigger=None,
            changes=[],
            status="pending_review",
            overall_impact_score=0.3,
            overall_risk_level="low",
            required_approvals=2,
            approval_count=0,
            rejection_count=0,
            reviewer_ids=[],
            review_notes={},
            created_by="user_123",
        )
        await repo.save_evolution_proposal(proposal)
        retrieved = await repo.get_evolution_proposal("prop_1")
        assert retrieved is not None
        assert retrieved.id == "prop_1"

    @pytest.mark.asyncio
    async def test_list_evolution_proposals(self, repo):
        p1 = EvolutionProposal(
            id="prop_1",
            companion_id="comp_123",
            identity_id="identity_1",
            baseline_version=1,
            name="Test 1",
            description="Test",
            trigger=None,
            changes=[],
            status="pending_review",
            overall_impact_score=0.3,
            overall_risk_level="low",
            required_approvals=2,
            approval_count=0,
            rejection_count=0,
            reviewer_ids=[],
            review_notes={},
            created_by="user_123",
        )
        p2 = EvolutionProposal(
            id="prop_2",
            companion_id="comp_123",
            identity_id="identity_1",
            baseline_version=1,
            name="Test 2",
            description="Test",
            trigger=None,
            changes=[],
            status="approved",
            overall_impact_score=0.3,
            overall_risk_level="low",
            required_approvals=2,
            approval_count=2,
            rejection_count=0,
            reviewer_ids=["r1", "r2"],
            review_notes={},
            created_by="user_123",
        )
        await repo.save_evolution_proposal(p1)
        await repo.save_evolution_proposal(p2)

        proposals = await repo.list_evolution_proposals(companion_id="comp_123", status="pending_review")
        assert len(proposals) == 1
        assert proposals[0].id == "prop_1"

    @pytest.mark.asyncio
    async def test_get_pending_evolution_proposals(self, repo):
        p1 = EvolutionProposal(
            id="prop_1",
            companion_id="comp_123",
            identity_id="identity_1",
            baseline_version=1,
            name="Test 1",
            description="Test",
            trigger=None,
            changes=[],
            status="pending_review",
            overall_impact_score=0.3,
            overall_risk_level="low",
            required_approvals=2,
            approval_count=0,
            rejection_count=0,
            reviewer_ids=[],
            review_notes={},
            created_by="user_123",
        )
        await repo.save_evolution_proposal(p1)

        pending = await repo.get_pending_evolution_proposals("comp_123")
        assert len(pending) == 1

    @pytest.mark.asyncio
    async def test_save_evolution_result(self, repo):
        result = EvolutionResult(
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
            duration_ms=100,
        )
        await repo.save_evolution_result(result)
        retrieved = await repo.get_evolution_result_by_proposal("prop_1")
        assert retrieved is not None
        assert retrieved.id == "result_1"

    @pytest.mark.asyncio
    async def test_get_evolution_history(self, repo):
        r1 = EvolutionResult(
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
            duration_ms=100,
        )
        r2 = EvolutionResult(
            id="result_2",
            proposal_id="prop_2",
            companion_id="comp_123",
            status="implemented",
            implemented_changes=["change_2"],
            failed_changes=[],
            previous_version=2,
            new_version=3,
            post_implementation_validation={"valid": True},
            validation_errors=[],
            validation_warnings=[],
            implemented_at=datetime.utcnow(),
            implemented_by="system",
            duration_ms=100,
        )
        await repo.save_evolution_result(r1)
        await repo.save_evolution_result(r2)

        history = await repo.get_evolution_history("comp_123", limit=10)
        assert len(history) == 2

    @pytest.mark.asyncio
    async def test_save_evolution_evidence(self, repo):
        evidence = EvolutionEvidence(
            id="ev_1",
            proposal_id="prop_1",
            change_id="change_1",
            source="user_feedback",
            description="User feedback",
            data={"message": "Be more creative"},
            strength=0.8,
            collected_at=datetime.utcnow(),
            collected_by="user_123",
        )
        await repo.save_evolution_evidence(evidence)
        # Evidence retrieval not directly exposed, but save should not error

    @pytest.mark.asyncio
    async def test_save_and_get_evolution_rule(self, repo):
        rule = EvolutionRule(
            id="rule_1",
            name="Drift Rule",
            description="Auto-evolve on drift",
            trigger_conditions={"threshold": 0.4},
            change_template={"type": "modify_values"},
            is_active=True,
            requires_human_approval=True,
            max_proposals_per_period=3,
            period_days=30,
        )
        await repo.save_evolution_rule(rule)
        rules = await repo.get_evolution_rules(active_only=True)
        assert len(rules) == 1
        assert rules[0].id == "rule_1"

    @pytest.mark.asyncio
    async def test_save_template(self, repo):
        template = {
            "id": "custom_1",
            "name": "Custom Template",
            "description": "A custom template",
            "category": "custom",
            "companion_type": "companion",
            "personality": {},
            "values": {},
            "voice": {},
            "boundaries": [],
            "goals": [],
            "tags": ["custom"],
            "is_active": True,
            "created_by": "user_123",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        await repo.save_template(template)
        retrieved = await repo.get_template("custom_1")
        assert retrieved is not None
        assert retrieved["id"] == "custom_1"

    @pytest.mark.asyncio
    async def test_list_templates(self, repo):
        t1 = {
            "id": "custom_1",
            "name": "Custom 1",
            "description": "Template 1",
            "category": "companion",
            "companion_type": "companion",
            "personality": {},
            "values": {},
            "voice": {},
            "boundaries": [],
            "goals": [],
            "tags": [],
            "is_active": True,
            "created_by": "user_123",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        t2 = {
            "id": "custom_2",
            "name": "Custom 2",
            "description": "Template 2",
            "category": "assistant",
            "companion_type": "companion",
            "personality": {},
            "values": {},
            "voice": {},
            "boundaries": [],
            "goals": [],
            "tags": [],
            "is_active": True,
            "created_by": "user_123",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        await repo.save_template(t1)
        await repo.save_template(t2)

        templates = await repo.list_templates(category="companion")
        assert len(templates) == 1
        assert templates[0]["category"] == "companion"

    @pytest.mark.asyncio
    async def test_delete_template(self, repo):
        template = {
            "id": "custom_1",
            "name": "Custom 1",
            "description": "Template 1",
            "category": "companion",
            "companion_type": "companion",
            "personality": {},
            "values": {},
            "voice": {},
            "boundaries": [],
            "goals": [],
            "tags": [],
            "is_active": True,
            "created_by": "user_123",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        await repo.save_template(template)

        result = await repo.delete_template("custom_1")
        assert result is True

        retrieved = await repo.get_template("custom_1")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_get_template_categories(self, repo):
        t1 = {
            "id": "custom_1",
            "name": "Custom 1",
            "description": "Template 1",
            "category": "companion",
            "companion_type": "companion",
            "personality": {},
            "values": {},
            "voice": {},
            "boundaries": [],
            "goals": [],
            "tags": [],
            "is_active": True,
            "created_by": "user_123",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        t2 = {
            "id": "custom_2",
            "name": "Custom 2",
            "description": "Template 2",
            "category": "assistant",
            "companion_type": "companion",
            "personality": {},
            "values": {},
            "voice": {},
            "boundaries": [],
            "goals": [],
            "tags": [],
            "is_active": True,
            "created_by": "user_123",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        await repo.save_template(t1)
        await repo.save_template(t2)

        categories = await repo.get_template_categories()
        assert "companion" in categories
        assert "assistant" in categories

    @pytest.mark.asyncio
    async def test_get_boundary_references(self, repo):
        boundary = Boundary(
            id="bound_1",
            type="hard",
            scope="content",
            severity="high",
            action="refuse",
            description="No harmful content",
            companion_id="comp_123",
        )
        identity = IdentityConfig(
            id="identity_1",
            companion_id="comp_123",
            personality=PersonalityConfig(
                profile__big_five__openness=0.5,
                profile__big_five__conscientiousness=0.5,
                profile__big_five__extraversion=0.5,
                profile__big_five__agreeableness=0.5,
                profile__big_five__neuroticism=0.5,
                companion_id="comp_123",
            ),
            values=ValuesConfig(companion_id="comp_123"),
            voice=VoiceProfile(companion_id="comp_123"),
            boundaries=[boundary],
            goals=[],
        )
        await repo.save(identity)

        refs = await repo.get_boundary_references("bound_1")
        assert len(refs) == 1
        assert refs[0] == "identity:identity_1"

    @pytest.mark.asyncio
    async def test_get_goal_references(self, repo):
        goal = Goal(
            id="goal_1",
            category="learning",
            priority="high",
            status="active",
            title="Learn Python",
            target_metric="hours",
            target_value=100.0,
            companion_id="comp_123",
        )
        identity = IdentityConfig(
            id="identity_1",
            companion_id="comp_123",
            personality=PersonalityConfig(
                profile__big_five__openness=0.5,
                profile__big_five__conscientiousness=0.5,
                profile__big_five__extraversion=0.5,
                profile__big_five__agreeableness=0.5,
                profile__big_five__neuroticism=0.5,
                companion_id="comp_123",
            ),
            values=ValuesConfig(companion_id="comp_123"),
            voice=VoiceProfile(companion_id="comp_123"),
            boundaries=[],
            goals=[goal],
        )
        await repo.save(identity)

        refs = await repo.get_goal_references("goal_1")
        assert len(refs) == 1
        assert refs[0] == "identity:identity_1"