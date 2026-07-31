"""Relationship Engine API Routes."""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from relationship_engine.api import router
from relationship_engine.models.requests import (
    AddDiaryEntryRequest,
    AddMilestoneRequest,
    BulkDimensionUpdateRequest,
    CreateRelationshipRequest,
    RecalculatePhaseRequest,
    StateTransitionRequest,
    UpdateDimensionsRequest,
)
from relationship_engine.models.responses import (
    AddDiaryEntryResponse,
    AddMilestoneResponse,
    CreateRelationshipResponse,
    GetStateResponse,
    HealthResponse,
    ListDiaryEntriesResponse,
    ListMilestonesResponse,
    MetricsResponse,
    StateTransitionResponse,
    UpdateDimensionsResponse,
)
from relationship_engine.services.relationship_service import RelationshipService


# Dependency to get relationship service
async def get_relationship_service(request) -> RelationshipService:
    """Get relationship service from app state."""
    return request.app.state.relationship_service


@router.post(
    "/relationships",
    response_model=CreateRelationshipResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new relationship",
)
async def create_relationship(
    request: CreateRelationshipRequest,
    service: RelationshipService = Depends(get_relationship_service),
) -> CreateRelationshipResponse:
    """Create a new relationship between a user and companion."""
    try:
        return await service.create_relationship(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create relationship: {str(e)}")


@router.get(
    "/state",
    response_model=GetStateResponse,
    summary="Get relationship state",
)
async def get_relationship_state(
    user_id: UUID = Query(..., description="User ID"),
    companion_id: UUID = Query(..., description="Companion ID"),
    include_milestones: bool = Query(True, description="Include milestones in response"),
    include_diary: bool = Query(True, description="Include diary entries in response"),
    diary_limit: int = Query(10, ge=1, le=100, description="Max diary entries to return"),
    service: RelationshipService = Depends(get_relationship_service),
) -> GetStateResponse:
    """Get the current state of a relationship."""
    result = await service.get_relationship_state(
        user_id=user_id,
        companion_id=companion_id,
        include_milestones=include_milestones,
        include_diary=include_diary,
        diary_limit=diary_limit,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return result


@router.post(
    "/dimensions/update",
    response_model=UpdateDimensionsResponse,
    summary="Update relationship dimensions",
)
async def update_dimensions(
    request: UpdateDimensionsRequest,
    service: RelationshipService = Depends(get_relationship_service),
) -> UpdateDimensionsResponse:
    """Update relationship dimensions based on interactions."""
    try:
        return await service.update_dimensions(request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update dimensions: {str(e)}")


@router.post(
    "/interaction",
    response_model=UpdateDimensionsResponse,
    summary="Process a single interaction",
)
async def process_interaction(
    user_id: UUID,
    companion_id: UUID,
    interaction_type: str = Query(..., pattern="^(message|voice_call|memory_share|proactive_nudge|conflict|reconciliation|celebration|support_moment)$"),
    intensity: float = Query(1.0, ge=0.1, le=2.0),
    metadata: dict[str, Any] | None = None,
    service: RelationshipService = Depends(get_relationship_service),
) -> UpdateDimensionsResponse:
    """Process a single interaction and update dimensions accordingly."""
    try:
        return await service.process_interaction(
            user_id=user_id,
            companion_id=companion_id,
            interaction_type=interaction_type,
            intensity=intensity,
            metadata=metadata,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process interaction: {str(e)}")


@router.post(
    "/bulk-update",
    response_model=UpdateDimensionsResponse,
    summary="Bulk update dimensions from multiple interactions",
)
async def bulk_update_dimensions(
    request: BulkDimensionUpdateRequest,
    service: RelationshipService = Depends(get_relationship_service),
) -> UpdateDimensionsResponse:
    """Process multiple interactions in bulk."""
    try:
        return await service.bulk_update_dimensions(request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process bulk update: {str(e)}")


@router.post(
    "/milestones",
    response_model=AddMilestoneResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a custom milestone",
)
async def add_milestone(
    request: AddMilestoneRequest,
    service: RelationshipService = Depends(get_relationship_service),
) -> AddMilestoneResponse:
    """Add a custom milestone to a relationship."""
    try:
        return await service.add_milestone(request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add milestone: {str(e)}")


@router.get(
    "/milestones",
    response_model=ListMilestonesResponse,
    summary="List milestones",
)
async def list_milestones(
    user_id: UUID = Query(..., description="User ID"),
    companion_id: UUID = Query(..., description="Companion ID"),
    achieved_only: bool = Query(False, description="Show only achieved milestones"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: RelationshipService = Depends(get_relationship_service),
) -> ListMilestonesResponse:
    """List milestones for a relationship."""
    milestones = await service.milestones_service.get_milestones(
        user_id=user_id,
        companion_id=companion_id,
        achieved_only=achieved_only,
        limit=limit,
        offset=offset,
    )

    # Get total count
    all_milestones = await service.milestones_service.get_milestones(
        user_id=user_id,
        companion_id=companion_id,
        achieved_only=False,
        limit=1000,
        offset=0,
    )

    from relationship_engine.models.responses import MilestoneResponse
    return ListMilestonesResponse(
        milestones=[MilestoneResponse.from_milestone(m) for m in milestones],
        total=len(all_milestones),
        limit=limit,
        offset=offset,
    )


@router.post(
    "/diary",
    response_model=AddDiaryEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a diary entry",
)
async def add_diary_entry(
    request: AddDiaryEntryRequest,
    service: RelationshipService = Depends(get_relationship_service),
) -> AddDiaryEntryResponse:
    """Add a diary entry to a relationship."""
    try:
        return await service.add_diary_entry(request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add diary entry: {str(e)}")


@router.get(
    "/diary",
    response_model=ListDiaryEntriesResponse,
    summary="List diary entries",
)
async def list_diary_entries(
    user_id: UUID = Query(..., description="User ID"),
    companion_id: UUID = Query(..., description="Companion ID"),
    author: str | None = Query(None, pattern="^(system|user|companion)$"),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    tags: list[str] = Query([]),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: RelationshipService = Depends(get_relationship_service),
) -> ListDiaryEntriesResponse:
    """List diary entries with filters."""
    entries = await service.diary_service.list_entries(
        user_id=user_id,
        companion_id=companion_id,
        author=author,
        start_date=start_date,
        end_date=end_date,
        tags=tags,
        limit=limit,
        offset=offset,
    )

    total = await service.diary_service.count_entries(user_id, companion_id, start_date, end_date)

    from relationship_engine.models.responses import DiaryEntryResponse
    return ListDiaryEntriesResponse(
        entries=[DiaryEntryResponse.from_entry(e) for e in entries],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/state/transition",
    response_model=StateTransitionResponse,
    summary="Trigger a state transition",
)
async def trigger_state_transition(
    request: StateTransitionRequest,
    service: RelationshipService = Depends(get_relationship_service),
) -> StateTransitionResponse:
    """Manually trigger a relationship state transition."""
    try:
        return await service.trigger_state_transition(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger transition: {str(e)}")


@router.post(
    "/phase/recalculate",
    response_model=GetStateResponse,
    summary="Recalculate phase from dimensions",
)
async def recalculate_phase(
    request: RecalculatePhaseRequest,
    service: RelationshipService = Depends(get_relationship_service),
) -> GetStateResponse:
    """Recalculate the relationship phase from current dimensions."""
    try:
        return await service.recalculate_phase(request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to recalculate phase: {str(e)}")


@router.post(
    "/diary/generate",
    response_model=AddDiaryEntryResponse | None,
    summary="Auto-generate diary entry",
)
async def generate_diary_entry(
    user_id: UUID,
    companion_id: UUID,
    period_start: datetime,
    period_end: datetime,
    service: RelationshipService = Depends(get_relationship_service),
) -> AddDiaryEntryResponse | None:
    """Auto-generate a diary entry for a time period."""
    try:
        return await service.generate_diary_entry(user_id, companion_id, period_start, period_end)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate diary: {str(e)}")


@router.get(
    "/summary",
    summary="Get comprehensive relationship summary",
)
async def get_relationship_summary(
    user_id: UUID = Query(..., description="User ID"),
    companion_id: UUID = Query(..., description="Companion ID"),
    service: RelationshipService = Depends(get_relationship_service),
) -> dict[str, Any]:
    """Get a comprehensive summary of the relationship."""
    try:
        return await service.get_relationship_summary(user_id, companion_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


@router.get(
    "/user/{user_id}",
    response_model=list[GetStateResponse],
    summary="List relationships for a user",
)
async def list_user_relationships(
    user_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: RelationshipService = Depends(get_relationship_service),
) -> list[GetStateResponse]:
    """List all relationships for a user."""
    states = await service.list_relationships_by_user(user_id, limit, offset)
    return [
        GetStateResponse(
            relationship=s,
            phase_changed=False,
        )
        for s in states
    ]


@router.delete(
    "/{user_id}/{companion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a relationship",
)
async def delete_relationship(
    user_id: UUID,
    companion_id: UUID,
    service: RelationshipService = Depends(get_relationship_service),
):
    """Delete a relationship."""
    deleted = await service.delete_relationship(user_id, companion_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)


# Health and Metrics endpoints
@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["health"],
    summary="Health check",
)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service="relationship-engine",
        version="0.1.0",
        checks={
            "database": "ok",
            "redis": "ok",
            "kuzu": "ok",
        },
    )


@router.get(
    "/health/live",
    tags=["health"],
    summary="Liveness probe",
)
async def liveness_probe() -> dict[str, str]:
    """Kubernetes liveness probe."""
    return {"status": "alive"}


@router.get(
    "/health/ready",
    tags=["health"],
    summary="Readiness probe",
)
async def readiness_probe(
    service: RelationshipService = Depends(get_relationship_service),
) -> dict[str, Any]:
    """Kubernetes readiness probe."""
    # Check database connectivity
    try:
        await service.relationship_repo.list_by_user(UUID("00000000-0000-0000-0000-000000000000"), limit=1)
        return {"status": "ready", "checks": {"database": "ok"}}
    except Exception:
        return {"status": "not ready", "checks": {"database": "failed"}}


@router.get(
    "/metrics",
    response_model=MetricsResponse,
    tags=["metrics"],
    summary="Get service metrics",
)
async def get_metrics(
    service: RelationshipService = Depends(get_relationship_service),
) -> MetricsResponse:
    """Get service metrics."""
    # This would typically come from a metrics collector
    # For now, return placeholder
    return MetricsResponse(
        total_relationships=0,
        active_relationships_24h=0,
        average_phase_score=0.0,
        phase_distribution={},
        milestone_achievement_rate=0.0,
        diary_entries_per_relationship=0.0,
    )