"""Proactive Engine API routes."""

import time
import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from proactive_engine.config import settings
from proactive_engine.services import (
    get_proactive_service,
    close_proactive_service,
    get_initiative_service,
    get_anticipation_service,
    get_suggestion_service,
    get_reminder_service,
    get_check_in_service,
    get_scheduler_service,
)
from proactive_engine.models.requests import (
    InitiativeRequest,
    AnticipationRequest,
    SuggestionRequest,
    ReminderRequest,
    CheckInRequest,
    ScheduleRequest,
    ProactiveActionRequest,
)
from proactive_engine.models.responses import (
    InitiativeResponse,
    AnticipationResponse,
    SuggestionResponse,
    ReminderResponse,
    CheckInResponse,
    ScheduleResponse,
    ProactiveActionResponse,
    HealthResponse,
    ErrorResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["proactive-engine"])


# Health endpoints
@router.get("/health/live", response_model=HealthResponse)
async def liveness_check() -> HealthResponse:
    """Liveness probe."""
    return HealthResponse(
        status="healthy",
        processing_time_ms=0.0,
    )


@router.get("/health/ready", response_model=HealthResponse)
async def readiness_check() -> HealthResponse:
    """Readiness probe with full health check."""
    service = await get_proactive_service()
    return await service.health_check()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Full health check."""
    service = await get_proactive_service()
    return await service.health_check()


# Initiative endpoints
@router.post("/initiative/detect", response_model=InitiativeResponse)
async def detect_initiative(request: InitiativeRequest) -> InitiativeResponse:
    """Detect if proactive initiative is warranted."""
    service = await get_proactive_service()
    return await service.detect_initiative(request)


@router.post("/initiative/action", response_model=ProactiveActionResponse)
async def execute_proactive_action(request: ProactiveActionRequest) -> ProactiveActionResponse:
    """Execute a proactive action."""
    service = await get_proactive_service()
    return await service.execute_proactive_action(request)


# Anticipation endpoints
@router.post("/anticipation/needs", response_model=AnticipationResponse)
async def anticipate_needs(request: AnticipationRequest) -> AnticipationResponse:
    """Anticipate user needs based on context and history."""
    service = await get_proactive_service()
    return await service.anticipate_needs(request)


# Suggestion endpoints
@router.post("/suggestions/generate", response_model=SuggestionResponse)
async def generate_suggestions(request: SuggestionRequest) -> SuggestionResponse:
    """Generate personalized proactive suggestions."""
    service = await get_proactive_service()
    return await service.generate_suggestions(request)


# Reminder endpoints
@router.post("/reminders", response_model=ReminderResponse)
async def create_reminder(request: ReminderRequest) -> ReminderResponse:
    """Create a proactive reminder."""
    service = await get_proactive_service()
    return await service.create_reminder(request)


@router.get("/reminders", response_model=List[Dict[str, Any]])
async def list_reminders(
    user_id: UUID = Query(...),
    companion_id: UUID = Query(...),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
) -> List[Dict[str, Any]]:
    """List reminders for a user."""
    service = await get_proactive_service()
    return await service.list_reminders(str(user_id), str(companion_id), status, limit)


@router.post("/reminders/{reminder_id}/cancel", response_model=Dict[str, bool])
async def cancel_reminder(reminder_id: str) -> Dict[str, bool]:
    """Cancel a reminder."""
    service = await get_proactive_service()
    success = await service.cancel_reminder(reminder_id)
    if not success:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return {"success": True}


@router.post("/reminders/{reminder_id}/complete", response_model=Dict[str, bool])
async def complete_reminder(reminder_id: str) -> Dict[str, bool]:
    """Mark a reminder as completed."""
    service = await get_proactive_service()
    success = await service.complete_reminder(reminder_id)
    if not success:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return {"success": True}


# Check-in endpoints
@router.post("/check-ins", response_model=CheckInResponse)
async def create_check_in(request: CheckInRequest) -> CheckInResponse:
    """Create a proactive check-in."""
    service = await get_proactive_service()
    return await service.create_check_in(request)


@router.get("/check-ins/should-check-in", response_model=Dict[str, bool])
async def should_check_in(
    user_id: UUID = Query(...),
    companion_id: UUID = Query(...),
    check_in_type: str = Query("general"),
) -> Dict[str, bool]:
    """Determine if a check-in is warranted."""
    service = await get_proactive_service()
    should = await service.should_check_in(str(user_id), str(companion_id), check_in_type)
    return {"should_check_in": should}


@router.get("/check-ins/history", response_model=List[Dict[str, Any]])
async def get_check_in_history(
    user_id: UUID = Query(...),
    companion_id: UUID = Query(...),
    limit: int = Query(20, ge=1, le=50),
) -> List[Dict[str, Any]]:
    """Get check-in history for a user."""
    service = await get_proactive_service()
    return await service.get_check_in_history(str(user_id), str(companion_id), limit)


# Scheduler endpoints
@router.post("/schedules", response_model=ScheduleResponse)
async def create_schedule(request: ScheduleRequest) -> ScheduleResponse:
    """Create a scheduled proactive action."""
    service = await get_proactive_service()
    return await service.create_schedule(request)


@router.get("/schedules", response_model=List[Dict[str, Any]])
async def list_schedules(
    user_id: UUID = Query(...),
    companion_id: UUID = Query(...),
    active_only: bool = Query(True),
    limit: int = Query(50, ge=1, le=100),
) -> List[Dict[str, Any]]:
    """List schedules for a user."""
    service = await get_proactive_service()
    return await service.list_schedules(str(user_id), str(companion_id), active_only, limit)


@router.get("/schedules/{schedule_id}", response_model=Dict[str, Any])
async def get_schedule(schedule_id: str) -> Dict[str, Any]:
    """Get a schedule by ID."""
    scheduler = await get_scheduler_service()
    schedule = await scheduler.get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule


@router.patch("/schedules/{schedule_id}", response_model=Dict[str, Any])
async def update_schedule(schedule_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update a schedule."""
    service = await get_proactive_service()
    updated = await service.update_schedule(schedule_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return updated


@router.delete("/schedules/{schedule_id}", response_model=Dict[str, bool])
async def delete_schedule(schedule_id: str) -> Dict[str, bool]:
    """Delete a schedule."""
    service = await get_proactive_service()
    success = await service.delete_schedule(schedule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"success": True}


@router.post("/schedules/{schedule_id}/pause", response_model=Dict[str, bool])
async def pause_schedule(schedule_id: str) -> Dict[str, bool]:
    """Pause a schedule."""
    scheduler = await get_scheduler_service()
    success = await scheduler.pause_schedule(schedule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"success": True}


@router.post("/schedules/{schedule_id}/resume", response_model=Dict[str, bool])
async def resume_schedule(schedule_id: str) -> Dict[str, bool]:
    """Resume a schedule."""
    scheduler = await get_scheduler_service()
    success = await scheduler.resume_schedule(schedule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"success": True}


@router.post("/schedules/execute-due", response_model=List[Dict[str, Any]])
async def execute_due_schedules() -> List[Dict[str, Any]]:
    """Execute all due scheduled jobs (admin endpoint)."""
    service = await get_proactive_service()
    return await service.execute_due_jobs()


# Metrics endpoint
@router.get("/metrics")
async def metrics() -> str:
    """Prometheus metrics endpoint."""
    # In production, this would return actual Prometheus metrics
    return "# Proactive Engine metrics placeholder\n"


# Service lifecycle
@router.on_event("startup")
async def startup_event() -> None:
    """Initialize services on startup."""
    logger.info("Starting Proactive Engine API")
    await get_proactive_service()


@router.on_event("shutdown")
async def shutdown_event() -> None:
    """Clean up services on shutdown."""
    logger.info("Shutting down Proactive Engine API")
    await close_proactive_service()