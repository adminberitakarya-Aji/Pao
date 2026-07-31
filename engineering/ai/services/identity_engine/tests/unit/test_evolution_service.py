"""Unit tests for Evolution Service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from identity_engine.services.evolution_service import EvolutionService
from identity_engine.models.evolution import (
    EvolutionProposal,
    EvolutionResult,
    EvolutionTrigger,
    EvolutionTriggerType,
    EvolutionChange,
    EvolutionChangeType,
    EvolutionProposalStatus,
    EvolutionEvidence,
    EvolutionEvidenceSource,
    EvolutionRule,
)
from identity_engine.models.identity import IdentityConfig
from identity_engine.models.personality import PersonalityConfig
from identity_engine.models.values import ValuesConfig
from identity_engine.models.voice import VoiceProfile
from identity_engine.models.boundaries import Boundary
from identity_engine.models.goals import Goal


class TestEvolutionService:
    """Test EvolutionService."""

    @pytest.fixture
    def evolution_service(self):
        return EvolutionService()

    @pytest.fixture
    def mock_repo(self):
        return AsyncMock()

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

    @pytest.mark.asyncio
    async def test_create_proposal(self, evolution_service, mock_repo, sample_identity):
        mock_repo.get.return_value = sample_identity
        mock_repo.save_evolution_proposal.return_value = None
        evolution_service.repository = mock_repo

        trigger = EvolutionTrigger(
            type=EvolutionTriggerType.USER_FEEDBACK,
            trigger_id="feedback_123",
            description="User wants more creative responses",
        )
        changes = [
            EvolutionChange(
                id="change_1",
                type=EvolutionChangeType.MODIFY_PERSONALITY,
                target="big_five.openness",
                current_value=0.5,
                proposed_value=0.7,
                rationale="Increase creativity",
                impact_score=0.3,
                risk_level="low",
            )
        ]

        proposal = await evolution_service.create_proposal(
            companion_id="comp_123",
            identity_id="identity_1",
            baseline_version=1,
            name="Increase Openness",
            description="Make companion more creative",
            trigger=trigger,
            changes=changes,
            created_by="user_123",
        )

        assert isinstance(proposal, EvolutionProposal)
        assert proposal.companion_id == "comp_123"
        assert proposal.status == EvolutionProposalStatus.PENDING_REVIEW
        assert len(proposal.changes) == 1
        mock_repo.save_evolution_proposal.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_proposal(self, evolution_service, mock_repo):
        mock_proposal = MagicMock(spec=EvolutionProposal)
        mock_proposal.id = "prop_1"
        mock_repo.get_evolution_proposal.return_value = mock_proposal
        evolution_service.repository = mock_repo

        proposal = await evolution_service.get_proposal("prop_1")

        assert proposal == mock_proposal
        mock_repo.get_evolution_proposal.assert_called_once_with("prop_1")

    @pytest.mark.asyncio
    async def test_list_proposals(self, evolution_service, mock_repo):
        mock_proposals = [
            MagicMock(id="prop_1", status=EvolutionProposalStatus.PENDING_REVIEW),
            MagicMock(id="prop_2", status=EvolutionProposalStatus.APPROVED),
        ]
        mock_repo.list_evolution_proposals.return_value = mock_proposals
        evolution_service.repository = mock_repo

        proposals = await evolution_service.list_proposals(companion_id="comp_123", status="pending_review")

        assert len(proposals) == 2
        mock_repo.list_evolution_proposals.assert_called_once_with(companion_id="comp_123", status="pending_review", limit=50, offset=0)

    @pytest.mark.asyncio
    async def test_approve_proposal(self, evolution_service, mock_repo):
        mock_proposal = EvolutionProposal(
            id="prop_1",
            companion_id="comp_123",
            identity_id="identity_1",
            baseline_version=1,
            name="Test",
            description="Test",
            trigger=EvolutionTrigger(
                type=EvolutionTriggerType.USER_FEEDBACK,
                trigger_id="fb_1",
                description="Feedback",
            ),
            changes=[
                EvolutionChange(
                    id="change_1",
                    type=EvolutionChangeType.MODIFY_PERSONALITY,
                    target="big_five.openness",
                    current_value=0.5,
                    proposed_value=0.7,
                    rationale="Test",
                    impact_score=0.3,
                    risk_level="low",
                )
            ],
            status=EvolutionProposalStatus.PENDING_REVIEW,
            overall_impact_score=0.3,
            overall_risk_level="low",
            required_approvals=2,
            approval_count=1,
            rejection_count=0,
            reviewer_ids=["reviewer_1"],
            review_notes={},
            created_by="user_123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_repo.get_evolution_proposal.return_value = mock_proposal
        mock_repo.save_evolution_proposal.return_value = None
        evolution_service.repository = mock_repo

        result = await evolution_service.approve_proposal("prop_1", "reviewer_2", "Looks good")

        assert result.status == EvolutionProposalStatus.APPROVED
        assert result.approval_count == 2
        assert "reviewer_2" in result.reviewer_ids
        mock_repo.save_evolution_proposal.assert_called_once()

    @pytest.mark.asyncio
    async def test_reject_proposal(self, evolution_service, mock_repo):
        mock_proposal = EvolutionProposal(
            id="prop_1",
            companion_id="comp_123",
            identity_id="identity_1",
            baseline_version=1,
            name="Test",
            description="Test",
            trigger=EvolutionTrigger(
                type=EvolutionTriggerType.USER_FEEDBACK,
                trigger_id="fb_1",
                description="Feedback",
            ),
            changes=[
                EvolutionChange(
                    id="change_1",
                    type=EvolutionChangeType.MODIFY_PERSONALITY,
                    target="big_five.openness",
                    current_value=0.5,
                    proposed_value=0.7,
                    rationale="Test",
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
        mock_repo.get_evolution_proposal.return_value = mock_proposal
        mock_repo.save_evolution_proposal.return_value = None
        evolution_service.repository = mock_repo

        result = await evolution_service.reject_proposal("prop_1", "reviewer_1", "Too risky")

        assert result.status == EvolutionProposalStatus.REJECTED
        assert result.rejection_count == 1
        mock_repo.save_evolution_proposal.assert_called_once()

    @pytest.mark.asyncio
    async def test_implement_proposal(self, evolution_service, mock_repo, sample_identity):
        mock_proposal = EvolutionProposal(
            id="prop_1",
            companion_id="comp_123",
            identity_id="identity_1",
            baseline_version=1,
            name="Test",
            description="Test",
            trigger=EvolutionTrigger(
                type=EvolutionTriggerType.USER_FEEDBACK,
                trigger_id="fb_1",
                description="Feedback",
            ),
            changes=[
                EvolutionChange(
                    id="change_1",
                    type=EvolutionChangeType.MODIFY_PERSONALITY,
                    target="big_five.openness",
                    current_value=0.5,
                    proposed_value=0.7,
                    rationale="Test",
                    impact_score=0.3,
                    risk_level="low",
                )
            ],
            status=EvolutionProposalStatus.APPROVED,
            overall_impact_score=0.3,
            overall_risk_level="low",
            required_approvals=2,
            approval_count=2,
            rejection_count=0,
            reviewer_ids=["r1", "r2"],
            review_notes={},
            created_by="user_123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_repo.get_evolution_proposal.return_value = mock_proposal
        mock_repo.get.return_value = sample_identity
        mock_repo.save.return_value = None
        mock_repo.save_version.return_value = None
        mock_repo.save_evolution_result.return_value = None
        mock_repo.save_evolution_proposal.return_value = None
        evolution_service.repository = mock_repo

        # Mock validation service
        evolution_service.validation_service = MagicMock()
        evolution_service.validation_service.validate_identity.return_value = MagicMock(is_valid=True, errors=[], warnings=[])

        result = await evolution_service.implement_proposal("prop_1", "system")

        assert isinstance(result, EvolutionResult)
        assert result.status == "implemented"
        assert result.new_version == 2
        assert "change_1" in result.implemented_changes
        mock_repo.save.assert_called_once()
        mock_repo.save_version.assert_called_once()
        mock_repo.save_evolution_result.assert_called_once()

    @pytest.mark.asyncio
    async def test_rollback_proposal(self, evolution_service, mock_repo, sample_identity):
        mock_proposal = EvolutionProposal(
            id="prop_1",
            companion_id="comp_123",
            identity_id="identity_1",
            baseline_version=1,
            name="Test",
            description="Test",
            trigger=EvolutionTrigger(
                type=EvolutionTriggerType.USER_FEEDBACK,
                trigger_id="fb_1",
                description="Feedback",
            ),
            changes=[
                EvolutionChange(
                    id="change_1",
                    type=EvolutionChangeType.MODIFY_PERSONALITY,
                    target="big_five.openness",
                    current_value=0.5,
                    proposed_value=0.7,
                    rationale="Test",
                    impact_score=0.3,
                    risk_level="low",
                )
            ],
            status=EvolutionProposalStatus.IMPLEMENTED,
            overall_impact_score=0.3,
            overall_risk_level="low",
            required_approvals=2,
            approval_count=2,
            rejection_count=0,
            reviewer_ids=["r1", "r2"],
            review_notes={},
            created_by="user_123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_repo.get_evolution_proposal.return_value = mock_proposal
        mock_repo.get.return_value = sample_identity
        mock_repo.get_evolution_result_by_proposal.return_value = EvolutionResult(
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
        mock_repo.save.return_value = None
        mock_repo.save_version.return_value = None
        mock_repo.save_evolution_result.return_value = None
        mock_repo.save_evolution_proposal.return_value = None
        evolution_service.repository = mock_repo

        result = await evolution_service.rollback_proposal("prop_1", "system", "User reported issues")

        assert result.status == "rolled_back"
        assert result.rollback_reason == "User reported issues"
        assert result.rollback_version == 1
        mock_repo.save.assert_called_once()
        mock_repo.save_version.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_evolution_history(self, evolution_service, mock_repo):
        mock_results = [
            MagicMock(id="result_1", companion_id="comp_123", new_version=2),
            MagicMock(id="result_2", companion_id="comp_123", new_version=3),
        ]
        mock_repo.get_evolution_history.return_value = mock_results
        evolution_service.repository = mock_repo

        history = await evolution_service.get_evolution_history("comp_123", limit=10)

        assert len(history) == 2
        mock_repo.get_evolution_history.assert_called_once_with("comp_123", 10)

    @pytest.mark.asyncio
    async def test_get_pending_proposals(self, evolution_service, mock_repo):
        mock_proposals = [
            MagicMock(id="prop_1", status=EvolutionProposalStatus.PENDING_REVIEW),
        ]
        mock_repo.get_pending_evolution_proposals.return_value = mock_proposals
        evolution_service.repository = mock_repo

        pending = await evolution_service.get_pending_proposals("comp_123")

        assert len(pending) == 1
        mock_repo.get_pending_evolution_proposals.assert_called_once_with("comp_123")

    @pytest.mark.asyncio
    async def test_save_evidence(self, evolution_service, mock_repo):
        mock_repo.save_evolution_evidence.return_value = None
        evolution_service.repository = mock_repo

        evidence = EvolutionEvidence(
            id="ev_1",
            proposal_id="prop_1",
            change_id="change_1",
            source=EvolutionEvidenceSource.USER_FEEDBACK,
            description="User feedback",
            data={"message": "Be more creative"},
            strength=0.8,
            collected_at=datetime.utcnow(),
            collected_by="user_123",
        )

        await evolution_service.save_evidence(evidence)

        mock_repo.save_evolution_evidence.assert_called_once_with(evidence)

    @pytest.mark.asyncio
    async def test_save_rule(self, evolution_service, mock_repo):
        mock_repo.save_evolution_rule.return_value = None
        evolution_service.repository = mock_repo

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

        await evolution_service.save_rule(rule)

        mock_repo.save_evolution_rule.assert_called_once_with(rule)

    @pytest.mark.asyncio
    async def test_get_rules(self, evolution_service, mock_repo):
        mock_rules = [
            MagicMock(id="rule_1", name="Rule 1"),
            MagicMock(id="rule_2", name="Rule 2"),
        ]
        mock_repo.get_evolution_rules.return_value = mock_rules
        evolution_service.repository = mock_repo

        rules = await evolution_service.get_rules(active_only=True)

        assert len(rules) == 2
        mock_repo.get_evolution_rules.assert_called_once_with(active_only=True)