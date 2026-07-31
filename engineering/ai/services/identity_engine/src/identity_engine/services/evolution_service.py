"""Evolution Service - Manages identity evolution proposals and implementations."""

from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import structlog

from pao_shared.observability import setup_tracing, setup_metrics

from ..models import (
    IdentityConfig, EvolutionProposal, EvolutionTrigger, EvolutionEvidence,
    EvolutionChange, EvolutionResult, EvolutionProposalStatus,
    EvolutionChangeType, EvolutionTriggerType, EvolutionRule,
    DriftResult, DriftSeverity, DriftDimension,
)
from .fingerprint_service import FingerprintService

logger = structlog.get_logger(__name__)


class EvolutionService:
    """Service for managing identity evolution."""
    
    def __init__(
        self,
        repository=None,
        fingerprint_service: Optional[FingerprintService] = None,
        validation_service=None,
        identity_service=None,
        notification_service=None,
    ):
        self.repository = repository
        self.fingerprint_service = fingerprint_service
        self.validation_service = validation_service
        self.identity_service = identity_service
        self.notification_service = notification_service
        self._tracer = setup_tracing("identity-engine", "evolution-service")
        self._meter = setup_metrics("identity-engine", "evolution-service")
        
        # Metrics
        self._proposals_created = self._meter.create_counter(
            "evolution_proposals_created_total", "Total evolution proposals created"
        )
        self._proposals_approved = self._meter.create_counter(
            "evolution_proposals_approved_total", "Total proposals approved"
        )
        self._proposals_rejected = self._meter.create_counter(
            "evolution_proposals_rejected_total", "Total proposals rejected"
        )
        self._proposals_implemented = self._meter.create_counter(
            "evolution_proposals_implemented_total", "Total proposals implemented"
        )
        self._proposals_rolled_back = self._meter.create_counter(
            "evolution_proposals_rolled_back_total", "Total proposals rolled back"
        )
        self._implementation_duration = self._meter.create_histogram(
            "evolution_implementation_duration_seconds", "Implementation duration"
        )
        
        # Predefined rules
        self._rules: Dict[str, EvolutionRule] = {}
        self._load_default_rules()
    
    def _load_default_rules(self):
        """Load default evolution rules."""
        from ..models import EVOLUTION_RULES
        for rule_id, rule in EVOLUTION_RULES.items():
            self._rules[rule_id] = rule
    
    async def create_proposal(
        self,
        companion_id: str,
        identity_id: str,
        name: str,
        description: str,
        trigger: EvolutionTrigger,
        changes: List[EvolutionChange],
        created_by: str = "system",
        reviewer_ids: Optional[List[str]] = None,
        required_approvals: int = 1,
    ) -> EvolutionProposal:
        """Create a new evolution proposal."""
        with self._tracer.start_as_current_span("create_proposal") as span:
            span.set_attribute("companion_id", companion_id)
            span.set_attribute("identity_id", identity_id)
            
            proposal = EvolutionProposal(
                id=f"evol_{companion_id}_{uuid.uuid4().hex[:8]}",
                companion_id=companion_id,
                identity_id=identity_id,
                baseline_version=0,  # Will be set from identity
                name=name,
                description=description,
                trigger=trigger,
                changes=changes,
                status=EvolutionProposalStatus.DRAFT,
                reviewer_ids=reviewer_ids or [],
                required_approvals=required_approvals,
                created_by=created_by,
            )
            
            # Get baseline version from identity
            if self.identity_service:
                identity = await self.identity_service.get_identity(identity_id)
                if identity:
                    proposal.baseline_version = identity.version
            
            # Compute overall metrics
            proposal.compute_overall_metrics()
            
            # Save to repository
            if self.repository:
                await self.repository.save_evolution_proposal(proposal)
            
            self._proposals_created.add(1, {"companion_id": companion_id})
            
            logger.info(
                "Evolution proposal created",
                proposal_id=proposal.id,
                companion_id=companion_id,
                changes_count=len(changes),
            )
            
            # Notify reviewers
            if self.notification_service and reviewer_ids:
                await self.notification_service.notify_reviewers(proposal)
            
            return proposal
    
    async def create_proposal_from_drift(
        self,
        companion_id: str,
        drift_result: DriftResult,
        created_by: str = "system",
    ) -> EvolutionProposal:
        """Create an evolution proposal from drift detection."""
        with self._tracer.start_as_current_span("create_proposal_from_drift") as span:
            span.set_attribute("companion_id", companion_id)
            span.set_attribute("drift_severity", drift_result.severity.value)
            
            # Get current active identity
            if not self.identity_service:
                raise ValueError("Identity service required for drift-based proposals")
            
            identity = await self.identity_service.get_identity_by_companion(companion_id)
            if not identity:
                raise ValueError(f"No active identity for companion {companion_id}")
            
            # Create trigger
            trigger = EvolutionTrigger(
                id=f"trig_{uuid.uuid4().hex[:8]}",
                type=EvolutionTriggerType.DRIFT_DETECTED,
                name=f"Drift Detection: {drift_result.severity.value}",
                description=f"Auto-generated from drift analysis (score: {drift_result.overall_drift_score:.2%})",
                drift_result_id=drift_result.id,
                severity=drift_result.severity,
            )
            
            # Generate changes based on drift
            changes = await self._generate_changes_from_drift(identity, drift_result)
            
            # Create evidence from drift result
            evidence = EvolutionEvidence(
                id=f"ev_{uuid.uuid4().hex[:8]}",
                proposal_id="",  # Will be set after proposal created
                change_id="",  # Will be set after changes created
                source="drift_analysis",
                description=f"Drift analysis shows {drift_result.severity.value} drift",
                data={
                    "drift_result_id": drift_result.id,
                    "overall_drift": drift_result.overall_drift_score,
                    "dimension_drifts": {k.value: v for k, v in drift_result.dimension_drifts.items()},
                },
                strength=min(1.0, drift_result.overall_drift_score * 2),
            )
            
            # Create proposal
            proposal = await self.create_proposal(
                companion_id=companion_id,
                identity_id=identity.id,
                name=f"Drift Correction: {drift_result.severity.value.title()}",
                description=f"Auto-generated proposal to address {drift_result.severity.value} drift "
                           f"(overall score: {drift_result.overall_drift_score:.2%})",
                trigger=trigger,
                changes=changes,
                created_by=created_by,
            )
            
            # Link evidence
            evidence.proposal_id = proposal.id
            for change in changes:
                evidence.change_id = change.id
                if self.repository:
                    await self.repository.save_evolution_evidence(evidence)
            
            logger.info(
                "Drift-based evolution proposal created",
                proposal_id=proposal.id,
                companion_id=companion_id,
                drift_severity=drift_result.severity.value,
            )
            
            return proposal
    
    async def _generate_changes_from_drift(
        self,
        identity: IdentityConfig,
        drift_result: DriftResult,
    ) -> List[EvolutionChange]:
        """Generate evolution changes based on drift analysis."""
        changes = []
        
        for dim, drift_score in drift_result.dimension_drifts.items():
            if drift_score < 0.1:  # Skip minor drift
                continue
            
            severity = drift_result.dimension_severities.get(dim, DriftSeverity.NONE)
            
            if dim == DriftDimension.PERSONALITY:
                change = EvolutionChange(
                    id=f"chg_{uuid.uuid4().hex[:8]}",
                    proposal_id="",  # Will be set later
                    type=EvolutionChangeType.PERSONALITY_ADJUSTMENT,
                    target_component="personality",
                    target_field="traits",
                    change_description=f"Adjust personality traits to correct {severity.value} drift",
                    rationale=f"Personality drift of {drift_score:.1%} detected. "
                             f"Traits may have shifted from baseline due to interaction patterns.",
                    impact_score=drift_score,
                    risk_level="medium" if severity in [DriftSeverity.MODERATE, DriftSeverity.SIGNIFICANT] else "low",
                    affected_dimensions=["personality", "behavior"],
                )
                changes.append(change)
            
            elif dim == DriftDimension.VOICE:
                change = EvolutionChange(
                    id=f"chg_{uuid.uuid4().hex[:8]}",
                    proposal_id="",
                    type=EvolutionChangeType.VOICE_MODIFICATION,
                    target_component="voice",
                    target_field="formality",  # Could be more specific
                    change_description=f"Review and adjust voice profile to correct {severity.value} drift",
                    rationale=f"Voice drift of {drift_score:.1%} detected. "
                             f"Communication style may have shifted from intended profile.",
                    impact_score=drift_score,
                    risk_level="medium" if severity in [DriftSeverity.MODERATE, DriftSeverity.SIGNIFICANT] else "low",
                    affected_dimensions=["voice", "communication"],
                )
                changes.append(change)
            
            elif dim == DriftDimension.VALUES:
                change = EvolutionChange(
                    id=f"chg_{uuid.uuid4().hex[:8]}",
                    proposal_id="",
                    type=EvolutionChangeType.VALUES_UPDATE,
                    target_component="values",
                    target_field="values",
                    change_description=f"Realign values configuration to correct {severity.value} drift",
                    rationale=f"Values drift of {drift_score:.1%} detected. "
                             f"Value priorities may have shifted from intended configuration.",
                    impact_score=drift_score,
                    risk_level="high" if severity == DriftSeverity.CRITICAL else "medium",
                    affected_dimensions=["values", "decision_making"],
                )
                changes.append(change)
            
            elif dim == DriftDimension.BOUNDARIES:
                change = EvolutionChange(
                    id=f"chg_{uuid.uuid4().hex[:8]}",
                    proposal_id="",
                    type=EvolutionChangeType.BOUNDARY_MODIFICATION,
                    target_component="boundaries",
                    target_field="boundaries",
                    change_description=f"Review boundaries to address {severity.value} drift",
                    rationale=f"Boundary configuration drift of {drift_score:.1%} detected. "
                             f"Safety boundaries may need adjustment.",
                    impact_score=drift_score,
                    risk_level="high",
                    affected_dimensions=["safety", "compliance"],
                )
                changes.append(change)
            
            elif dim == DriftDimension.GOALS:
                change = EvolutionChange(
                    id=f"chg_{uuid.uuid4().hex[:8]}",
                    proposal_id="",
                    type=EvolutionChangeType.GOAL_MODIFICATION,
                    target_component="goals",
                    target_field="goals",
                    change_description=f"Adjust goals to correct {severity.value} drift",
                    rationale=f"Goal configuration drift of {drift_score:.1%} detected. "
                             f"Goal priorities or metrics may need realignment.",
                    impact_score=drift_score,
                    risk_level="medium",
                    affected_dimensions=["goals", "performance"],
                )
                changes.append(change)
        
        return changes
    
    async def get_proposal(self, proposal_id: str) -> Optional[EvolutionProposal]:
        """Get a proposal by ID."""
        if not self.repository:
            return None
        return await self.repository.get_evolution_proposal(proposal_id)
    
    async def list_proposals(
        self,
        companion_id: Optional[str] = None,
        status: Optional[EvolutionProposalStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[EvolutionProposal]:
        """List evolution proposals."""
        if not self.repository:
            return []
        return await self.repository.list_evolution_proposals(
            companion_id=companion_id,
            status=status,
            limit=limit,
            offset=offset,
        )
    
    async def submit_for_review(self, proposal_id: str, submitted_by: str) -> EvolutionProposal:
        """Submit a draft proposal for review."""
        proposal = await self.get_proposal(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal not found: {proposal_id}")
        
        if proposal.status != EvolutionProposalStatus.DRAFT:
            raise ValueError(f"Proposal not in draft status: {proposal.status}")
        
        # Validate all changes
        if self.validation_service:
            for change in proposal.changes:
                is_valid, notes = await self.validation_service.validate_change(change)
                change.is_validated = is_valid
                change.validation_notes = notes
        
        proposal.status = EvolutionProposalStatus.PENDING_REVIEW
        proposal.updated_at = datetime.utcnow().isoformat()
        
        if self.repository:
            await self.repository.save_evolution_proposal(proposal)
        
        # Notify reviewers
        if self.notification_service and proposal.reviewer_ids:
            await self.notification_service.notify_reviewers(proposal)
        
        logger.info("Proposal submitted for review", proposal_id=proposal_id, by=submitted_by)
        return proposal
    
    async def approve_proposal(
        self,
        proposal_id: str,
        approved_by: str,
        notes: Optional[str] = None,
    ) -> EvolutionProposal:
        """Approve a proposal."""
        proposal = await self.get_proposal(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal not found: {proposal_id}")
        
        if proposal.status != EvolutionProposalStatus.PENDING_REVIEW:
            raise ValueError(f"Proposal not pending review: {proposal.status}")
        
        proposal.approval_count += 1
        if notes:
            proposal.review_notes.append(f"Approved by {approved_by}: {notes}")
        
        if proposal.can_approve():
            proposal.status = EvolutionProposalStatus.APPROVED
            logger.info("Proposal approved", proposal_id=proposal_id, by=approved_by)
            self._proposals_approved.add(1, {"companion_id": proposal.companion_id})
            
            # Notify creator
            if self.notification_service:
                await self.notification_service.notify_proposal_approved(proposal)
        else:
            logger.info("Proposal approval recorded", proposal_id=proposal_id, 
                       approvals=proposal.approval_count, required=proposal.required_approvals)
        
        proposal.updated_at = datetime.utcnow().isoformat()
        
        if self.repository:
            await self.repository.save_evolution_proposal(proposal)
        
        return proposal
    
    async def reject_proposal(
        self,
        proposal_id: str,
        rejected_by: str,
        reason: str,
    ) -> EvolutionProposal:
        """Reject a proposal."""
        proposal = await self.get_proposal(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal not found: {proposal_id}")
        
        if proposal.status != EvolutionProposalStatus.PENDING_REVIEW:
            raise ValueError(f"Proposal not pending review: {proposal.status}")
        
        proposal.rejection_count += 1
        proposal.review_notes.append(f"Rejected by {rejected_by}: {reason}")
        proposal.status = EvolutionProposalStatus.REJECTED
        proposal.updated_at = datetime.utcnow().isoformat()
        
        if self.repository:
            await self.repository.save_evolution_proposal(proposal)
        
        self._proposals_rejected.add(1, {"companion_id": proposal.companion_id})
        
        logger.info("Proposal rejected", proposal_id=proposal_id, by=rejected_by, reason=reason)
        
        # Notify creator
        if self.notification_service:
            await self.notification_service.notify_proposal_rejected(proposal, reason)
        
        return proposal
    
    async def implement_proposal(
        self,
        proposal_id: str,
        implemented_by: str = "system",
    ) -> EvolutionResult:
        """Implement an approved evolution proposal."""
        with self._tracer.start_as_current_span("implement_proposal") as span:
            span.set_attribute("proposal_id", proposal_id)
            
            start_time = datetime.utcnow()
            
            proposal = await self.get_proposal(proposal_id)
            if not proposal:
                raise ValueError(f"Proposal not found: {proposal_id}")
            
            if proposal.status != EvolutionProposalStatus.APPROVED:
                raise ValueError(f"Proposal not approved: {proposal.status}")
            
            if not proposal.is_ready_for_implementation():
                raise ValueError("Proposal not ready for implementation")
            
            # Get current identity
            if not self.identity_service:
                raise ValueError("Identity service required for implementation")
            
            identity = await self.identity_service.get_identity(proposal.identity_id)
            if not identity:
                raise ValueError(f"Identity not found: {proposal.identity_id}")
            
            previous_version = identity.version
            
            # Apply changes
            implemented_changes = []
            failed_changes = []
            
            for change in proposal.changes:
                try:
                    await self._apply_change(identity, change)
                    implemented_changes.append(change.id)
                except Exception as e:
                    failed_changes.append({
                        "change_id": change.id,
                        "error": str(e),
                    })
                    logger.error("Change implementation failed", change_id=change.id, error=str(e))
            
            # Determine overall status
            if failed_changes:
                if implemented_changes:
                    status = "partial"
                else:
                    status = "failed"
            else:
                status = "success"
            
            # Create new version
            new_version = previous_version + 1
            identity.version = new_version
            identity.updated_at = datetime.utcnow().isoformat()
            
            if status == "success":
                identity.status = IdentityStatus.ACTIVE
                identity.activated_at = datetime.utcnow().isoformat()
            
            # Validate new identity
            validation_errors = []
            validation_warnings = []
            if self.validation_service:
                is_valid, errors, warnings = await self.validation_service.validate_identity(identity)
                identity.is_valid = is_valid
                identity.validation_errors = errors
                identity.validation_warnings = warnings
                validation_errors = errors
                validation_warnings = warnings
            
            # Save updated identity
            if self.repository:
                await self.repository.save(identity)
            
            # Create version snapshot
            version = identity.create_version(
                change_type="evolve",
                change_summary=f"Evolution: {proposal.name}",
                changed_fields=[c.target_component for c in proposal.changes],
                changed_by=implemented_by,
            )
            if self.repository:
                await self.repository.save_version(version)
            
            # Compute post-implementation drift
            post_drift = None
            if self.fingerprint_service and previous_version > 0:
                try:
                    drift_result = await self.fingerprint_service.detect_drift(
                        companion_id=proposal.companion_id,
                        baseline_version=previous_version,
                        current_version=new_version,
                    )
                    post_drift = drift_result.overall_drift_score
                except Exception as e:
                    logger.warning("Post-implementation drift check failed", error=str(e))
            
            # Create result
            result = EvolutionResult(
                id=f"res_{uuid.uuid4().hex[:8]}",
                proposal_id=proposal.id,
                companion_id=proposal.companion_id,
                status=status,
                implemented_changes=implemented_changes,
                failed_changes=failed_changes,
                previous_version=previous_version,
                new_version=new_version,
                post_implementation_validation=len(validation_errors) == 0,
                validation_errors=validation_errors,
                validation_warnings=validation_warnings,
                post_implementation_drift=post_drift,
                implemented_at=datetime.utcnow().isoformat(),
                implemented_by=implemented_by,
                duration_ms=(datetime.utcnow() - start_time).total_seconds() * 1000,
            )
            
            # Update proposal
            proposal.status = EvolutionProposalStatus.IMPLEMENTED
            proposal.implemented_version = new_version
            proposal.implementation_notes = f"Implemented with status: {status}"
            proposal.updated_at = datetime.utcnow().isoformat()
            
            if self.repository:
                await self.repository.save_evolution_proposal(proposal)
                await self.repository.save_evolution_result(result)
            
            # Recompute fingerprint
            if self.fingerprint_service:
                await self.fingerprint_service.compute_fingerprint(identity)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            self._proposals_implemented.add(1, {
                "companion_id": proposal.companion_id,
                "status": status,
            })
            self._implementation_duration.record(duration)
            
            logger.info(
                "Evolution proposal implemented",
                proposal_id=proposal_id,
                status=status,
                implemented=len(implemented_changes),
                failed=len(failed_changes),
                new_version=new_version,
            )
            
            return result
    
    async def _apply_change(self, identity: IdentityConfig, change: EvolutionChange):
        """Apply a single change to an identity."""
        # This would implement the actual change logic
        # For now, we'll use a simplified approach
        
        if change.target_component == "personality":
            # Personality adjustments would be applied here
            pass
        elif change.target_component == "voice":
            # Voice modifications
            pass
        elif change.target_component == "values":
            # Values updates
            pass
        elif change.target_component == "boundaries":
            # Boundary changes
            pass
        elif change.target_component == "goals":
            # Goal modifications
            pass
        
        # In a real implementation, this would modify the identity object
        # based on change.proposed_value
    
    async def rollback_proposal(
        self,
        proposal_id: str,
        rolled_back_by: str,
        reason: str,
    ) -> EvolutionResult:
        """Rollback an implemented proposal."""
        with self._tracer.start_as_current_span("rollback_proposal") as span:
            span.set_attribute("proposal_id", proposal_id)
            
            proposal = await self.get_proposal(proposal_id)
            if not proposal:
                raise ValueError(f"Proposal not found: {proposal_id}")
            
            if proposal.status != EvolutionProposalStatus.IMPLEMENTED:
                raise ValueError(f"Proposal not implemented: {proposal.status}")
            
            if not self.identity_service:
                raise ValueError("Identity service required for rollback")
            
            # Rollback identity to previous version
            result = await self.identity_service.rollback_identity(
                companion_id=proposal.companion_id,
                target_version=proposal.baseline_version,
                rolled_back_by=rolled_back_by,
            )
            
            # Update proposal status
            proposal.status = EvolutionProposalStatus.ROLLED_BACK
            proposal.updated_at = datetime.utcnow().isoformat()
            
            if self.repository:
                await self.repository.save_evolution_proposal(proposal)
            
            # Create rollback result
            rollback_result = EvolutionResult(
                id=f"rb_{uuid.uuid4().hex[:8]}",
                proposal_id=proposal.id,
                companion_id=proposal.companion_id,
                status="rolled_back",
                implemented_changes=[],
                failed_changes=[],
                previous_version=proposal.implemented_version or 0,
                new_version=result.version,
                rollback_reason=reason,
                rollback_version=proposal.baseline_version,
                implemented_at=datetime.utcnow().isoformat(),
                implemented_by=rolled_back_by,
            )
            
            if self.repository:
                await self.repository.save_evolution_result(rollback_result)
            
            self._proposals_rolled_back.add(1, {"companion_id": proposal.companion_id})
            
            logger.info("Proposal rolled back", proposal_id=proposal_id, by=rolled_back_by, reason=reason)
            
            return rollback_result
    
    async def get_evolution_history(
        self,
        companion_id: str,
        limit: int = 50,
    ) -> List[EvolutionResult]:
        """Get evolution history for a companion."""
        if not self.repository:
            return []
        return await self.repository.get_evolution_history(companion_id, limit)
    
    async def get_proposal_result(self, proposal_id: str) -> Optional[EvolutionResult]:
        """Get the implementation result for a proposal."""
        if not self.repository:
            return None
        return await self.repository.get_evolution_result_by_proposal(proposal_id)
    
    async def evaluate_rules(self, companion_id: str) -> List[EvolutionProposal]:
        """Evaluate evolution rules and create proposals if triggered."""
        if not self.repository:
            return []
        
        # Get current context
        identity = await self.identity_service.get_identity_by_companion(companion_id)
        if not identity:
            return []
        
        latest_drift = await self.fingerprint_service.get_latest_drift(companion_id)
        
        context = {
            "companion_id": companion_id,
            "identity": identity,
            "latest_drift": latest_drift,
        }
        
        proposals = []
        for rule_id, rule in self._rules.items():
            if not rule.is_active:
                continue
            
            if rule.matches(context):
                # Check if we already have a recent proposal from this rule
                recent = await self.repository.get_recent_proposals_by_rule(
                    companion_id, rule_id, rule.period_days
                )
                
                if len(recent) < rule.max_proposals_per_period:
                    # Create proposal from rule
                    proposal = await self._create_proposal_from_rule(rule, context)
                    proposals.append(proposal)
        
        return proposals
    
    async def _create_proposal_from_rule(
        self,
        rule: EvolutionRule,
        context: Dict[str, Any],
    ) -> EvolutionProposal:
        """Create a proposal from an evolution rule."""
        identity = context["identity"]
        latest_drift = context.get("latest_drift")
        
        trigger = EvolutionTrigger(
            id=f"trig_{uuid.uuid4().hex[:8]}",
            type=EvolutionTriggerType.DRIFT_DETECTED,  # Default
            name=f"Rule Triggered: {rule.name}",
            description=rule.description,
        )
        
        changes = []
        for tmpl in rule.change_template:
            change = EvolutionChange(
                id=f"chg_{uuid.uuid4().hex[:8]}",
                proposal_id="",
                type=EvolutionChangeType(tmpl.get("type", "metadata_update")),
                target_component=tmpl.get("target_component", "metadata"),
                target_field=tmpl.get("target_field", ""),
                change_description=tmpl.get("description", ""),
                rationale=tmpl.get("rationale", ""),
                impact_score=0.5,
                risk_level="medium",
            )
            changes.append(change)
        
        return await self.create_proposal(
            companion_id=identity.companion_id,
            identity_id=identity.id,
            name=f"Rule-based: {rule.name}",
            description=f"Auto-generated from rule: {rule.name}",
            trigger=trigger,
            changes=changes,
            created_by="evolution_rule",
            required_approvals=1 if not rule.requires_human_approval else 2,
        )
    
    def add_rule(self, rule: EvolutionRule):
        """Add or update an evolution rule."""
        self._rules[rule.id] = rule
        logger.info("Evolution rule added", rule_id=rule.id)
    
    def remove_rule(self, rule_id: str):
        """Remove an evolution rule."""
        if rule_id in self._rules:
            del self._rules[rule_id]
            logger.info("Evolution rule removed", rule_id=rule_id)
    
    def get_rules(self) -> List[EvolutionRule]:
        """Get all evolution rules."""
        return list(self._rules.values())