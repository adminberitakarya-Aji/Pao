"""Unit tests for Evolution models."""

import pytest
from pydantic import ValidationError
from datetime import datetime

from identity_engine.models.evolution import (
    EvolutionProposal,
    EvolutionResult,
    EvolutionTrigger,
    EvolutionTriggerType,
    EvolutionChange,
    EvolutionChangeType,
    EvolutionProposalStatus,
    EvolutionEvidence,
    EvolutionRule,
    EVOLUTION_RULES,
)


class TestEvolutionTriggerType:
    """Test EvolutionTriggerType enum."""

    def test_trigger_types(self):
        assert EvolutionTriggerType.DRIFT_DETECTED == "drift_detected"
        assert EvolutionTriggerType.USER_FEEDBACK == "user_feedback"
        assert EvolutionTriggerType.PERFORMANCE_DECLINE == "performance_decline"
        assert EvolutionTriggerType.GOAL_MISALIGNMENT == "goal_misalignment"
        assert EvolutionTriggerType.BOUNDARY_VIOLATIONS == "boundary_violations"
        assert EvolutionTriggerType.SCHEDULED_REVIEW == "scheduled_review"
        assert EvolutionTriggerType.MANUAL_REQUEST == "manual_request"
        assert EvolutionTriggerType.CONTEXT_CHANGE == "context_change"
        assert EvolutionTriggerType.CAPABILITY_CHANGE == "capability_change"
        assert EvolutionTriggerType.COMPLIANCE_UPDATE == "compliance_update"


class TestEvolutionProposalStatus:
    """Test EvolutionProposalStatus enum."""

    def test_statuses(self):
        assert EvolutionProposalStatus.DRAFT == "draft"
        assert EvolutionProposalStatus.PENDING_REVIEW == "pending_review"
        assert EvolutionProposalStatus.APPROVED == "approved"
        assert EvolutionProposalStatus.REJECTED == "rejected"
        assert EvolutionProposalStatus.IMPLEMENTING == "implementing"
        assert EvolutionProposalStatus.IMPLEMENTED == "implemented"
        assert EvolutionProposalStatus.ROLLED_BACK == "rolled_back"
        assert EvolutionProposalStatus.SUPERSEDED == "superseded"


class TestEvolutionChangeType:
    """Test EvolutionChangeType enum."""

    def test_change_types(self):
        assert EvolutionChangeType.PERSONALITY_ADJUSTMENT == "personality_adjustment"
        assert EvolutionChangeType.VALUES_UPDATE == "values_update"
        assert EvolutionChangeType.VOICE_MODIFICATION == "voice_modification"
        assert EvolutionChangeType.BOUNDARY_ADDITION == "boundary_addition"
        assert EvolutionChangeType.BOUNDARY_MODIFICATION == "boundary_modification"
        assert EvolutionChangeType.BOUNDARY_REMOVAL == "boundary_removal"
        assert EvolutionChangeType.GOAL_ADDITION == "goal_addition"
        assert EvolutionChangeType.GOAL_MODIFICATION == "goal_modification"
        assert EvolutionChangeType.GOAL_REMOVAL == "goal_removal"
        assert EvolutionChangeType.STRUCTURAL_CHANGE == "structural_change"
        assert EvolutionChangeType.METADATA_UPDATE == "metadata_update"


class TestEvolutionTrigger:
    """Test EvolutionTrigger model."""

    def test_valid_trigger(self):
        trigger = EvolutionTrigger(
            id="trigger_1",
            type=EvolutionTriggerType.DRIFT_DETECTED,
            name="Values Drift",
            description="Significant drift in values detected",
            drift_result_id="drift_123",
            severity="moderate",
        )
        assert trigger.id == "trigger_1"
        assert trigger.type == EvolutionTriggerType.DRIFT_DETECTED
        assert trigger.drift_result_id == "drift_123"

    def test_trigger_defaults(self):
        trigger = EvolutionTrigger(
            type=EvolutionTriggerType.USER_FEEDBACK,
            name="Feedback Trigger",
        )
        assert trigger.id is not None
        assert trigger.detected_by == "system"
        assert trigger.severity == "none"
        assert trigger.metadata == {}


class TestEvolutionEvidence:
    """Test EvolutionEvidence model."""

    def test_valid_evidence(self):
        evidence = EvolutionEvidence(
            id="evidence_1",
            proposal_id="prop_1",
            change_id="change_1",
            source="user_feedback",
            description="User explicitly requested more creative responses",
            data={"conversation_id": "conv_123", "message": "Be more creative"},
            strength=0.8,
            collected_by="user_123",
        )
        assert evidence.source == "user_feedback"
        assert evidence.strength == 0.8
        assert evidence.proposal_id == "prop_1"

    def test_evidence_defaults(self):
        evidence = EvolutionEvidence(
            proposal_id="prop_1",
            change_id="change_1",
            source="drift_analysis",
            description="Drift detected",
        )
        assert evidence.strength == 0.5
        assert evidence.collected_by == "system"
        assert evidence.data == {}
        assert evidence.metadata == {}

    def test_strength_bounds(self):
        with pytest.raises(ValidationError):
            EvolutionEvidence(
                proposal_id="p1", change_id="c1", source="test",
                description="test", strength=1.5,
            )

        with pytest.raises(ValidationError):
            EvolutionEvidence(
                proposal_id="p1", change_id="c1", source="test",
                description="test", strength=-0.1,
            )


class TestEvolutionChange:
    """Test EvolutionChange model."""

    def test_valid_change(self):
        change = EvolutionChange(
            id="change_1",
            proposal_id="prop_1",
            type=EvolutionChangeType.PERSONALITY_ADJUSTMENT,
            target_component="personality",
            target_field="traits.openness",
            current_value=0.5,
            proposed_value=0.7,
            change_description="Increase openness",
            rationale="User wants more creative responses",
            impact_score=0.3,
            risk_level="low",
            affected_dimensions=["personality"],
        )
        assert change.id == "change_1"
        assert change.type == EvolutionChangeType.PERSONALITY_ADJUSTMENT
        assert change.target_component == "personality"
        assert change.proposed_value == 0.7
        assert change.risk_level == "low"

    def test_change_defaults(self):
        change = EvolutionChange(
            proposal_id="prop_1",
            type=EvolutionChangeType.VALUES_UPDATE,
            target_component="values",
            target_field="weights",
            change_description="Adjust values",
        )
        assert change.id is not None
        assert change.impact_score == 0.5
        assert change.risk_level == "low"
        assert change.evidence_ids == []
        assert change.is_validated is False

    def test_risk_level_validation(self):
        with pytest.raises(ValidationError):
            EvolutionChange(
                proposal_id="p1",
                type=EvolutionChangeType.PERSONALITY_ADJUSTMENT,
                target_component="personality",
                target_field="test",
                change_description="test",
                risk_level="invalid",
            )


class TestEvolutionProposal:
    """Test EvolutionProposal model."""

    def test_valid_proposal(self):
        trigger = EvolutionTrigger(
            id="trigger_1",
            type=EvolutionTriggerType.USER_FEEDBACK,
            name="User Feedback",
            description="User requested changes",
        )
        change = EvolutionChange(
            id="change_1",
            proposal_id="prop_1",
            type=EvolutionChangeType.PERSONALITY_ADJUSTMENT,
            target_component="personality",
            target_field="traits.openness",
            change_description="Increase openness",
            current_value=0.5,
            proposed_value=0.7,
            rationale="User feedback",
            impact_score=0.3,
            risk_level="low",
        )
        proposal = EvolutionProposal(
            id="prop_1",
            companion_id="comp_123",
            identity_id="identity_1",
            baseline_version=1,
            name="Increase Openness",
            description="Increase openness based on user feedback",
            trigger=trigger,
            changes=[change],
            status=EvolutionProposalStatus.PENDING_REVIEW,
            required_approvals=2,
            created_by="user_123",
        )
        assert proposal.id == "prop_1"
        assert proposal.status == EvolutionProposalStatus.PENDING_REVIEW
        assert proposal.required_approvals == 2
        assert len(proposal.changes) == 1

    def test_proposal_defaults(self):
        trigger = EvolutionTrigger(
            type=EvolutionTriggerType.DRIFT_DETECTED,
            name="Drift",
        )
        proposal = EvolutionProposal(
            companion_id="comp_123",
            identity_id="identity_1",
            baseline_version=1,
            name="Test",
            trigger=trigger,
        )
        assert proposal.status == EvolutionProposalStatus.DRAFT
        assert proposal.overall_impact == 0.0
        assert proposal.overall_risk == "low"
        assert proposal.confidence == 0.5
        assert proposal.approval_count == 0
        assert proposal.rejection_count == 0
        assert proposal.required_approvals == 1
        assert proposal.version == 1

    def test_get_changes_by_component(self):
        trigger = EvolutionTrigger(type=EvolutionTriggerType.DRIFT_DETECTED, name="Test")
        changes = [
            EvolutionChange(
                id="c1", proposal_id="p1", type=EvolutionChangeType.PERSONALITY_ADJUSTMENT,
                target_component="personality", target_field="openness",
                change_description="d1",
            ),
            EvolutionChange(
                id="c2", proposal_id="p1", type=EvolutionChangeType.VALUES_UPDATE,
                target_component="values", target_field="care",
                change_description="d2",
            ),
            EvolutionChange(
                id="c3", proposal_id="p1", type=EvolutionChangeType.PERSONALITY_ADJUSTMENT,
                target_component="personality", target_field="extraversion",
                change_description="d3",
            ),
        ]
        proposal = EvolutionProposal(
            companion_id="c1", identity_id="i1", baseline_version=1,
            name="Test", trigger=trigger, changes=changes,
        )
        grouped = proposal.get_changes_by_component()
        assert len(grouped["personality"]) == 2
        assert len(grouped["values"]) == 1

    def test_get_high_risk_changes(self):
        trigger = EvolutionTrigger(type=EvolutionTriggerType.DRIFT_DETECTED, name="Test")
        changes = [
            EvolutionChange(id="c1", proposal_id="p1", type=EvolutionChangeType.PERSONALITY_ADJUSTMENT,
                target_component="personality", target_field="openness", change_description="d1",
                risk_level="low"),
            EvolutionChange(id="c2", proposal_id="p1", type=EvolutionChangeType.VALUES_UPDATE,
                target_component="values", target_field="care", change_description="d2",
                risk_level="high"),
            EvolutionChange(id="c3", proposal_id="p1", type=EvolutionChangeType.VOICE_MODIFICATION,
                target_component="voice", target_field="formality", change_description="d3",
                risk_level="critical"),
        ]
        proposal = EvolutionProposal(
            companion_id="c1", identity_id="i1", baseline_version=1,
            name="Test", trigger=trigger, changes=changes,
        )
        high_risk = proposal.get_high_risk_changes()
        assert len(high_risk) == 2
        assert all(c.risk_level in ["high", "critical"] for c in high_risk)

    def test_compute_overall_metrics(self):
        trigger = EvolutionTrigger(type=EvolutionTriggerType.DRIFT_DETECTED, name="Test")
        changes = [
            EvolutionChange(id="c1", proposal_id="p1", type=EvolutionChangeType.PERSONALITY_ADJUSTMENT,
                target_component="personality", target_field="openness", change_description="d1",
                impact_score=0.3, risk_level="low"),
            EvolutionChange(id="c2", proposal_id="p1", type=EvolutionChangeType.VALUES_UPDATE,
                target_component="values", target_field="care", change_description="d2",
                impact_score=0.5, risk_level="medium"),
        ]
        proposal = EvolutionProposal(
            companion_id="c1", identity_id="i1", baseline_version=1,
            name="Test", trigger=trigger, changes=changes,
        )
        proposal.compute_overall_metrics()
        assert proposal.overall_impact == 0.4  # (0.3 + 0.5) / 2
        assert proposal.overall_risk == "medium"  # max risk

    def test_can_approve(self):
        trigger = EvolutionTrigger(type=EvolutionTriggerType.DRIFT_DETECTED, name="Test")
        proposal = EvolutionProposal(
            companion_id="c1", identity_id="i1", baseline_version=1,
            name="Test", trigger=trigger, required_approvals=2,
        )
        assert proposal.can_approve() is False
        proposal.approval_count = 2
        assert proposal.can_approve() is True
        proposal.rejection_count = 1
        assert proposal.can_approve() is False

    def test_is_ready_for_implementation(self):
        trigger = EvolutionTrigger(type=EvolutionTriggerType.DRIFT_DETECTED, name="Test")
        change = EvolutionChange(
            id="c1", proposal_id="p1", type=EvolutionChangeType.PERSONALITY_ADJUSTMENT,
            target_component="personality", target_field="openness", change_description="d1",
            is_validated=True,
        )
        proposal = EvolutionProposal(
            companion_id="c1", identity_id="i1", baseline_version=1,
            name="Test", trigger=trigger, changes=[change],
            status=EvolutionProposalStatus.APPROVED,
            implementation_plan="Plan here",
        )
        assert proposal.is_ready_for_implementation() is True

        proposal.status = EvolutionProposalStatus.PENDING_REVIEW
        assert proposal.is_ready_for_implementation() is False

        proposal.status = EvolutionProposalStatus.APPROVED
        change.is_validated = False
        assert proposal.is_ready_for_implementation() is False


class TestEvolutionResult:
    """Test EvolutionResult model."""

    def test_valid_result(self):
        result = EvolutionResult(
            id="result_1",
            proposal_id="prop_1",
            companion_id="comp_123",
            status="success",
            implemented_changes=["change_1"],
            failed_changes=[],
            previous_version=1,
            new_version=2,
            post_implementation_validation=True,
            validation_errors=[],
            validation_warnings=[],
            implemented_by="system",
            duration_ms=150.0,
        )
        assert result.status == "success"
        assert result.new_version == 2
        assert result.duration_ms == 150.0
        assert result.is_successful() is True

    def test_partial_result(self):
        result = EvolutionResult(
            id="result_1",
            proposal_id="prop_1",
            companion_id="comp_123",
            status="partial",
            implemented_changes=["change_1"],
            failed_changes=[{"id": "change_2", "error": "Validation failed"}],
            previous_version=1,
            new_version=2,
            implemented_by="system",
        )
        assert result.is_successful() is False

    def test_failed_result(self):
        result = EvolutionResult(
            id="result_1",
            proposal_id="prop_1",
            companion_id="comp_123",
            status="failed",
            implemented_changes=[],
            failed_changes=[{"id": "change_1", "error": "Error"}],
            previous_version=1,
            new_version=1,
            implemented_by="system",
        )
        assert result.is_successful() is False


class TestEvolutionRule:
    """Test EvolutionRule model."""

    def test_valid_rule(self):
        rule = EvolutionRule(
            id="rule_1",
            name="Drift-Triggered Evolution",
            description="Auto-propose evolution when drift exceeds threshold",
            trigger_conditions={"drift_severity": "moderate", "dimension": "personality", "threshold": 0.2},
            change_template=[
                {
                    "type": "personality_adjustment",
                    "target_component": "personality",
                    "target_field": "traits",
                    "description": "Adjust drifted personality traits toward baseline",
                    "rationale": "Moderate personality drift detected",
                }
            ],
            max_proposals_per_period=1,
            period_days=30,
            requires_human_approval=True,
        )
        assert rule.name == "Drift-Triggered Evolution"
        assert rule.is_active is True
        assert rule.requires_human_approval is True
        assert len(rule.change_template) == 1

    def test_rule_defaults(self):
        rule = EvolutionRule(
            id="rule_1",
            name="Test",
            trigger_conditions={},
        )
        assert rule.is_active is True
        assert rule.version == 1
        assert rule.max_proposals_per_period == 1
        assert rule.period_days == 30
        assert rule.requires_human_approval is True
        assert rule.auto_approve_threshold is None

    def test_matches_placeholder(self):
        rule = EvolutionRule(
            id="rule_1",
            name="Test",
            trigger_conditions={},
        )
        # matches is a placeholder returning False
        assert rule.matches({"test": "data"}) is False


class TestEvolutionRules:
    """Test predefined evolution rules."""

    def test_builtin_rules_exist(self):
        assert "drift_personality_moderate" in EVOLUTION_RULES
        assert "drift_voice_significant" in EVOLUTION_RULES
        assert "boundary_violations_frequent" in EVOLUTION_RULES
        assert "goal_misalignment" in EVOLUTION_RULES
        assert "user_feedback_pattern" in EVOLUTION_RULES

    def test_drift_personality_moderate_rule(self):
        rule = EVOLUTION_RULES["drift_personality_moderate"]
        assert rule.id == "drift_personality_moderate"
        assert rule.trigger_conditions["drift_severity"] == "moderate"
        assert rule.trigger_conditions["dimension"] == "personality"
        assert rule.trigger_conditions["threshold"] == 0.15
        assert rule.requires_human_approval is True

    def test_drift_voice_significant_rule(self):
        rule = EVOLUTION_RULES["drift_voice_significant"]
        assert rule.trigger_conditions["drift_severity"] == "significant"
        assert rule.trigger_conditions["dimension"] == "voice"
        assert rule.period_days == 14

    def test_boundary_violations_frequent_rule(self):
        rule = EVOLUTION_RULES["boundary_violations_frequent"]
        assert rule.trigger_conditions["metric"] == "boundary_violations"
        assert rule.trigger_conditions["threshold"] == 10
        assert rule.max_proposals_per_period == 2

    def test_goal_misalignment_rule(self):
        rule = EVOLUTION_RULES["goal_misalignment"]
        assert rule.trigger_conditions["metric_status"] == "off_track"
        assert rule.trigger_conditions["consecutive_periods"] == 3
        assert "user_satisfaction" in rule.trigger_conditions["goal_types"]

    def test_user_feedback_pattern_rule(self):
        rule = EVOLUTION_RULES["user_feedback_pattern"]
        assert rule.trigger_conditions["feedback_theme_count"] == 5
        assert rule.trigger_conditions["theme_consistency"] == 0.8
        assert rule.trigger_conditions["sentiment"] == "negative"
