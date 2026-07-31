"""Identity Engine API Routes."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query, Body, Path
from pydantic import BaseModel, Field
import structlog

from ..models import (
    IdentityConfig, IdentityRequest, IdentityResponse, IdentityVersion,
    IdentityStatus, IdentitySource, CompanionType,
    FingerprintVector, FingerprintResult, DriftResult, DriftSeverity,
    EvolutionProposal, EvolutionTrigger, EvolutionChange, EvolutionResult,
    EvolutionProposalStatus, EvolutionChangeType, EvolutionTriggerType,
    DriftDimension,
)
from ..services import (
    IdentityService, FingerprintService, DriftService,
    EvolutionService, ValidationService, TemplateService,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/identity", tags=["identity"])

# Dependency injection - these would be configured in the main app
_identity_service: Optional[IdentityService] = None
_fingerprint_service: Optional[FingerprintService] = None
_drift_service: Optional[DriftService] = None
_evolution_service: Optional[EvolutionService] = None
_validation_service: Optional[ValidationService] = None
_template_service: Optional[TemplateService] = None


def get_identity_service() -> IdentityService:
    if _identity_service is None:
        raise HTTPException(status_code=503, detail="Identity service not initialized")
    return _identity_service


def get_fingerprint_service() -> FingerprintService:
    if _fingerprint_service is None:
        raise HTTPException(status_code=503, detail="Fingerprint service not initialized")
    return _fingerprint_service


def get_drift_service() -> DriftService:
    if _drift_service is None:
        raise HTTPException(status_code=503, detail="Drift service not initialized")
    return _drift_service


def get_evolution_service() -> EvolutionService:
    if _evolution_service is None:
        raise HTTPException(status_code=503, detail="Evolution service not initialized")
    return _evolution_service


def get_validation_service() -> ValidationService:
    if _validation_service is None:
        raise HTTPException(status_code=503, detail="Validation service not initialized")
    return _validation_service


def get_template_service() -> TemplateService:
    if _template_service is None:
        raise HTTPException(status_code=503, detail="Template service not initialized")
    return _template_service


# Request/Response models
class IdentityCreateRequest(BaseModel):
    companion_id: str = Field(..., description="Companion identifier")
    name: str = Field(..., description="Identity name")
    description: Optional[str] = Field(None, description="Identity description")
    personality: Optional[Dict[str, Any]] = Field(None, description="Personality configuration")
    values: Optional[Dict[str, Any]] = Field(None, description="Values configuration")
    voice: Optional[Dict[str, Any]] = Field(None, description="Voice profile")
    boundaries: Optional[List[Dict[str, Any]]] = Field(None, description="Boundaries")
    goals: Optional[List[Dict[str, Any]]] = Field(None, description="Goals")
    source: IdentitySource = Field(IdentitySource.MANUAL, description="Source of identity")
    created_by: Optional[str] = Field(None, description="Creator identifier")
    tags: Optional[List[str]] = Field(None, description="Tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    auto_activate: bool = Field(False, description="Auto-activate if valid")
    skip_validation: bool = Field(False, description="Skip validation")


class IdentityUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, description="Identity name")
    description: Optional[str] = Field(None, description="Identity description")
    personality: Optional[Dict[str, Any]] = Field(None, description="Personality configuration")
    values: Optional[Dict[str, Any]] = Field(None, description="Values configuration")
    voice: Optional[Dict[str, Any]] = Field(None, description="Voice profile")
    boundaries: Optional[List[Dict[str, Any]]] = Field(None, description="Boundaries")
    goals: Optional[List[Dict[str, Any]]] = Field(None, description="Goals")
    tags: Optional[List[str]] = Field(None, description="Tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    skip_validation: bool = Field(False, description="Skip validation")


class IdentityFromTemplateRequest(BaseModel):
    template_id: str = Field(..., description="Template identifier")
    companion_id: str = Field(..., description="Companion identifier")
    name: str = Field(..., description="Identity name")
    customizations: Optional[Dict[str, Any]] = Field(None, description="Customizations")
    preset: Optional[str] = Field(None, description="Voice preset")
    created_by: str = Field("api", description="Creator identifier")


class DriftCheckRequest(BaseModel):
    companion_id: str = Field(..., description="Companion identifier")
    baseline_version: Optional[int] = Field(None, description="Baseline version for comparison")


class EvolutionProposalRequest(BaseModel):
    companion_id: str = Field(..., description="Companion identifier")
    identity_id: str = Field(..., description="Identity identifier")
    name: str = Field(..., description="Proposal name")
    description: str = Field(..., description="Proposal description")
    trigger_type: EvolutionTriggerType = Field(..., description="Trigger type")
    trigger_description: str = Field(..., description="Trigger description")
    changes: List[Dict[str, Any]] = Field(..., description="Proposed changes")
    reviewer_ids: Optional[List[str]] = Field(None, description="Reviewer identifiers")
    required_approvals: int = Field(1, description="Required approvals")


class EvolutionApprovalRequest(BaseModel):
    notes: Optional[str] = Field(None, description="Approval notes")


class EvolutionRejectionRequest(BaseModel):
    reason: str = Field(..., description="Rejection reason")


class DriftMonitoringConfigRequest(BaseModel):
    interval_hours: int = Field(24, ge=1, le=168, description="Check interval in hours")
    auto_evolution: bool = Field(True, description="Auto-trigger evolution")
    trigger_severity: DriftSeverity = Field(DriftSeverity.MODERATE, description="Trigger severity")


# Initialize services (called from main.py)
def init_services(
    identity_service: IdentityService,
    fingerprint_service: FingerprintService,
    drift_service: DriftService,
    evolution_service: EvolutionService,
    validation_service: ValidationService,
    template_service: TemplateService,
):
    global _identity_service, _fingerprint_service, _drift_service
    global _evolution_service, _validation_service, _template_service
    
    _identity_service = identity_service
    _fingerprint_service = fingerprint_service
    _drift_service = drift_service
    _evolution_service = evolution_service
    _validation_service = validation_service
    _template_service = template_service


# Identity endpoints
@router.post("/identities", response_model=IdentityResponse, status_code=201)
async def create_identity(
    request: IdentityCreateRequest,
    service: IdentityService = Depends(get_identity_service),
):
    """Create a new identity configuration."""
    try:
        identity_request = IdentityRequest(
            companion_id=request.companion_id,
            name=request.name,
            description=request.description,
            personality=request.personality,
            values=request.values,
            voice=request.voice,
            boundaries=request.boundaries,
            goals=request.goals,
            source=request.source,
            created_by=request.created_by,
            tags=request.tags,
            metadata=request.metadata,
            auto_activate=request.auto_activate,
            skip_validation=request.skip_validation,
        )
        return await service.create_identity(identity_request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to create identity", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/identities/{identity_id}", response_model=IdentityResponse)
async def get_identity(
    identity_id: str = Path(..., description="Identity ID"),
    service: IdentityService = Depends(get_identity_service),
):
    """Get an identity by ID."""
    identity = await service.get_identity(identity_id)
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")
    return identity


@router.get("/companions/{companion_id}/identity", response_model=IdentityResponse)
async def get_active_identity(
    companion_id: str = Path(..., description="Companion ID"),
    version: Optional[int] = Query(None, description="Specific version"),
    service: IdentityService = Depends(get_identity_service),
):
    """Get the active identity for a companion."""
    identity = await service.get_identity_by_companion(companion_id, version)
    if not identity:
        raise HTTPException(status_code=404, detail="No active identity found for companion")
    return identity


@router.put("/identities/{identity_id}", response_model=IdentityResponse)
async def update_identity(
    request: IdentityUpdateRequest,
    identity_id: str = Path(..., description="Identity ID"),
    service: IdentityService = Depends(get_identity_service),
):
    """Update an existing identity."""
    try:
        identity_request = IdentityRequest(
            companion_id="",  # Will be filled from existing identity
            name=request.name or "",
            description=request.description,
            personality=request.personality,
            values=request.values,
            voice=request.voice,
            boundaries=request.boundaries,
            goals=request.goals,
            tags=request.tags,
            metadata=request.metadata,
            skip_validation=request.skip_validation,
        )
        return await service.update_identity(identity_id, identity_request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to update identity", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/identities/{identity_id}/activate", response_model=IdentityResponse)
async def activate_identity(
    identity_id: str = Path(..., description="Identity ID"),
    activated_by: str = Query("api", description="Activator identifier"),
    service: IdentityService = Depends(get_identity_service),
):
    """Activate an identity."""
    try:
        return await service.activate_identity(identity_id, activated_by)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/identities/{identity_id}/deactivate", response_model=IdentityResponse)
async def deactivate_identity(
    identity_id: str = Path(..., description="Identity ID"),
    deactivated_by: str = Query("api", description="Deactivator identifier"),
    service: IdentityService = Depends(get_identity_service),
):
    """Deactivate an identity."""
    try:
        return await service.deactivate_identity(identity_id, deactivated_by)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/identities", response_model=List[IdentityResponse])
async def list_identities(
    companion_id: Optional[str] = Query(None, description="Filter by companion"),
    status: Optional[IdentityStatus] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    service: IdentityService = Depends(get_identity_service),
):
    """List identities with optional filters."""
    return await service.list_identities(
        companion_id=companion_id,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get("/companions/{companion_id}/history", response_model=List[IdentityVersion])
async def get_identity_history(
    companion_id: str = Path(..., description="Companion ID"),
    service: IdentityService = Depends(get_identity_service),
):
    """Get version history for a companion's identity."""
    return await service.get_identity_history(companion_id)


@router.post("/companions/{companion_id}/rollback", response_model=IdentityResponse)
async def rollback_identity(
    target_version: int = Query(..., description="Target version to rollback to"),
    rolled_back_by: str = Query("api", description="Rollback initiator"),
    companion_id: str = Path(..., description="Companion ID"),
    service: IdentityService = Depends(get_identity_service),
):
    """Rollback to a previous version."""
    try:
        return await service.rollback_identity(companion_id, target_version, rolled_back_by)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Template endpoints
@router.post("/identities/from-template", response_model=IdentityResponse, status_code=201)
async def create_identity_from_template(
    request: IdentityFromTemplateRequest,
    template_service: TemplateService = Depends(get_template_service),
    identity_service: IdentityService = Depends(get_identity_service),
):
    """Create an identity from a template."""
    try:
        identity = await template_service.create_identity_from_template(
            template_id=request.template_id,
            companion_id=request.companion_id,
            name=request.name,
            customizations=request.customizations,
            preset=request.preset,
            created_by=request.created_by,
        )
        
        # Save via identity service
        identity_request = IdentityRequest(
            companion_id=request.companion_id,
            name=request.name,
            personality=identity.personality,
            values=identity.values,
            voice=identity.voice,
            boundaries=identity.boundaries,
            goals=identity.goals,
            source=IdentitySource.TEMPLATE,
            created_by=request.created_by,
            tags=identity.tags,
            metadata=identity.metadata,
            auto_activate=False,
            skip_validation=True,  # Template already validated
        )
        return await identity_service.create_identity(identity_request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to create identity from template", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/templates", response_model=List[Dict[str, Any]])
async def list_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    companion_type: Optional[CompanionType] = Query(None, description="Filter by companion type"),
    is_active: bool = Query(True, description="Filter by active status"),
    service: TemplateService = Depends(get_template_service),
):
    """List available templates."""
    return await service.list_templates(category, companion_type, is_active)


@router.get("/templates/{template_id}", response_model=Dict[str, Any])
async def get_template(
    template_id: str = Path(..., description="Template ID"),
    service: TemplateService = Depends(get_template_service),
):
    """Get a template by ID."""
    template = await service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.get("/templates/categories", response_model=List[str])
async def get_template_categories(
    service: TemplateService = Depends(get_template_service),
):
    """Get all template categories."""
    return await service.get_categories()


# Fingerprint endpoints
@router.post("/companions/{companion_id}/fingerprint", response_model=FingerprintResult)
async def compute_fingerprint(
    companion_id: str = Path(..., description="Companion ID"),
    version: Optional[int] = Query(None, description="Specific identity version"),
    identity_service: IdentityService = Depends(get_identity_service),
    fingerprint_service: FingerprintService = Depends(get_fingerprint_service),
):
    """Compute fingerprint for a companion's identity."""
    identity = await identity_service.get_identity_by_companion(companion_id, version)
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")
    
    # Convert response back to config for fingerprinting
    # In real implementation, would fetch full config from repository
    raise HTTPException(status_code=501, detail="Not implemented - needs repository access")


# Drift endpoints
@router.post("/drift/check", response_model=DriftResult)
async def check_drift(
    request: DriftCheckRequest,
    drift_service: DriftService = Depends(get_drift_service),
):
    """Run a drift check for a companion."""
    try:
        return await drift_service.run_drift_check(
            companion_id=request.companion_id,
            baseline_version=request.baseline_version,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/companions/{companion_id}/drift", response_model=DriftResult)
async def get_latest_drift(
    companion_id: str = Path(..., description="Companion ID"),
    drift_service: DriftService = Depends(get_drift_service),
):
    """Get the latest drift result for a companion."""
    result = await drift_service.get_drift_summary(companion_id)
    if result.get("status") == "no_data":
        raise HTTPException(status_code=404, detail="No drift data available")
    return result


@router.get("/companions/{companion_id}/drift/timeline", response_model=List[Dict[str, Any]])
async def get_drift_timeline(
    companion_id: str = Path(..., description="Companion ID"),
    days: int = Query(90, ge=1, le=365, description="Days of history"),
    drift_service: DriftService = Depends(get_drift_service),
):
    """Get drift timeline for visualization."""
    return await drift_service.get_drift_timeline(companion_id, days)


@router.post("/companions/{companion_id}/drift/monitor", response_model=Dict[str, Any])
async def configure_drift_monitoring(
    request: DriftMonitoringConfigRequest,
    companion_id: str = Path(..., description="Companion ID"),
    drift_service: DriftService = Depends(get_drift_service),
):
    """Configure drift monitoring for a companion."""
    return await drift_service.configure_monitoring(
        companion_id=companion_id,
        interval_hours=request.interval_hours,
        auto_evolution=request.auto_evolution,
        trigger_severity=request.trigger_severity,
    )


@router.get("/drift/alerts", response_model=List[Dict[str, Any]])
async def get_active_alerts(
    companion_id: Optional[str] = Query(None, description="Filter by companion"),
    severity: Optional[DriftSeverity] = Query(None, description="Filter by severity"),
    drift_service: DriftService = Depends(get_drift_service),
):
    """Get active drift alerts."""
    return await drift_service.get_active_alerts(companion_id, severity)


@router.post("/drift/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str = Path(..., description="Alert ID"),
    acknowledged_by: str = Query(..., description="Acknowledger identifier"),
    drift_service: DriftService = Depends(get_drift_service),
):
    """Acknowledge a drift alert."""
    success = await drift_service.acknowledge_alert(alert_id, acknowledged_by)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "acknowledged"}


@router.post("/drift/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str = Path(..., description="Alert ID"),
    resolved_by: str = Query(..., description="Resolver identifier"),
    resolution_notes: str = Query(..., description="Resolution notes"),
    drift_service: DriftService = Depends(get_drift_service),
):
    """Resolve a drift alert."""
    success = await drift_service.resolve_alert(alert_id, resolved_by, resolution_notes)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "resolved"}


# Evolution endpoints
@router.post("/evolution/proposals", response_model=EvolutionProposal, status_code=201)
async def create_evolution_proposal(
    request: EvolutionProposalRequest,
    evolution_service: EvolutionService = Depends(get_evolution_service),
):
    """Create a new evolution proposal."""
    try:
        trigger = EvolutionTrigger(
            id=f"trig_{request.companion_id}_{datetime.utcnow().timestamp()}",
            type=request.trigger_type,
            name=f"Manual: {request.name}",
            description=request.trigger_description,
        )
        
        changes = []
        for i, change_data in enumerate(request.changes):
            change = EvolutionChange(
                id=f"chg_{request.companion_id}_{i}",
                proposal_id="",  # Will be set by service
                type=EvolutionChangeType(change_data["type"]),
                target_component=change_data["target_component"],
                target_field=change_data["target_field"],
                change_description=change_data["change_description"],
                rationale=change_data.get("rationale", ""),
                impact_score=change_data.get("impact_score", 0.5),
                risk_level=change_data.get("risk_level", "medium"),
                proposed_value=change_data.get("proposed_value"),
                affected_dimensions=change_data.get("affected_dimensions", []),
            )
            changes.append(change)
        
        return await evolution_service.create_proposal(
            companion_id=request.companion_id,
            identity_id=request.identity_id,
            name=request.name,
            description=request.description,
            trigger=trigger,
            changes=changes,
            created_by="api",
            reviewer_ids=request.reviewer_ids,
            required_approvals=request.required_approvals,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to create evolution proposal", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/evolution/proposals/{proposal_id}", response_model=EvolutionProposal)
async def get_evolution_proposal(
    proposal_id: str = Path(..., description="Proposal ID"),
    evolution_service: EvolutionService = Depends(get_evolution_service),
):
    """Get an evolution proposal by ID."""
    proposal = await evolution_service.get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return proposal


@router.get("/evolution/proposals", response_model=List[EvolutionProposal])
async def list_evolution_proposals(
    companion_id: Optional[str] = Query(None, description="Filter by companion"),
    status: Optional[EvolutionProposalStatus] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    evolution_service: EvolutionService = Depends(get_evolution_service),
):
    """List evolution proposals."""
    return await evolution_service.list_proposals(
        companion_id=companion_id,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.post("/evolution/proposals/{proposal_id}/submit", response_model=EvolutionProposal)
async def submit_proposal_for_review(
    proposal_id: str = Path(..., description="Proposal ID"),
    submitted_by: str = Query("api", description="Submitter identifier"),
    evolution_service: EvolutionService = Depends(get_evolution_service),
):
    """Submit a draft proposal for review."""
    try:
        return await evolution_service.submit_for_review(proposal_id, submitted_by)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/evolution/proposals/{proposal_id}/approve", response_model=EvolutionProposal)
async def approve_proposal(
    request: EvolutionApprovalRequest,
    proposal_id: str = Path(..., description="Proposal ID"),
    approved_by: str = Query(..., description="Approver identifier"),
    evolution_service: EvolutionService = Depends(get_evolution_service),
):
    """Approve a proposal."""
    try:
        return await evolution_service.approve_proposal(proposal_id, approved_by, request.notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/evolution/proposals/{proposal_id}/reject", response_model=EvolutionProposal)
async def reject_proposal(
    request: EvolutionRejectionRequest,
    proposal_id: str = Path(..., description="Proposal ID"),
    rejected_by: str = Query(..., description="Rejecter identifier"),
    evolution_service: EvolutionService = Depends(get_evolution_service),
):
    """Reject a proposal."""
    try:
        return await evolution_service.reject_proposal(proposal_id, rejected_by, request.reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/evolution/proposals/{proposal_id}/implement", response_model=EvolutionResult)
async def implement_proposal(
    proposal_id: str = Path(..., description="Proposal ID"),
    implemented_by: str = Query("api", description="Implementer identifier"),
    evolution_service: EvolutionService = Depends(get_evolution_service),
):
    """Implement an approved evolution proposal."""
    try:
        return await evolution_service.implement_proposal(proposal_id, implemented_by)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/evolution/proposals/{proposal_id}/rollback", response_model=EvolutionResult)
async def rollback_proposal(
    proposal_id: str = Path(..., description="Proposal ID"),
    rolled_back_by: str = Query(..., description="Rollback initiator"),
    reason: str = Query(..., description="Rollback reason"),
    evolution_service: EvolutionService = Depends(get_evolution_service),
):
    """Rollback an implemented proposal."""
    try:
        return await evolution_service.rollback_proposal(proposal_id, rolled_back_by, reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/companions/{companion_id}/evolution/history", response_model=List[EvolutionResult])
async def get_evolution_history(
    companion_id: str = Path(..., description="Companion ID"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    evolution_service: EvolutionService = Depends(get_evolution_service),
):
    """Get evolution history for a companion."""
    return await evolution_service.get_evolution_history(companion_id, limit)


@router.get("/evolution/proposals/{proposal_id}/result", response_model=EvolutionResult)
async def get_proposal_result(
    proposal_id: str = Path(..., description="Proposal ID"),
    evolution_service: EvolutionService = Depends(get_evolution_service),
):
    """Get the implementation result for a proposal."""
    result = await evolution_service.get_proposal_result(proposal_id)
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    return result


# Health check
@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "identity-engine",
        "timestamp": datetime.utcnow().isoformat(),
    }