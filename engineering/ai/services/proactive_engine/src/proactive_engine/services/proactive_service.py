"""Main Proactive Service orchestrating all proactive capabilities."""

import logging
import time
from typing import Optional, Dict, Any, List
from uuid import UUID

from proactive_engine.config import settings
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
)

from proactive_engine.services.initiative_service import InitiativeService
from proactive_engine.services.anticipation_service import AnticipationService
from proactive_engine.services.suggestion_service import SuggestionService
from proactive_engine.services.reminder_service import ReminderService
from proactive_engine.services.check_in_service import CheckInService
from proactive_engine.services.scheduler_service import SchedulerService

logger = logging.getLogger(__name__)


class ProactiveService:
    """Main service orchestrating all proactive capabilities."""
    
    def __init__(self):
        self._initialized = False
        self.initiative_service: Optional[InitiativeService] = None
        self.anticipation_service: Optional[AnticipationService] = None
        self.suggestion_service: Optional[SuggestionService] = None
        self.reminder_service: Optional[ReminderService] = None
        self.check_in_service: Optional[CheckInService] = None
        self.scheduler_service: Optional[SchedulerService] = None
    
    async def initialize(self) -> None:
        """Initialize all sub-services."""
        logger.info("Initializing Proactive Engine")
        
        # Initialize sub-services
        self.initiative_service = InitiativeService()
        await self.initiative_service.initialize()
        
        self.anticipation_service = AnticipationService()
        await self.anticipation_service.initialize()
        
        self.suggestion_service = SuggestionService()
        await self.suggestion_service.initialize()
        
        self.reminder_service = ReminderService()
        await self.reminder_service.initialize()
        
        self.check_in_service = CheckInService()
        await self.check_in_service.initialize()
        
        self.scheduler_service = SchedulerService()
        await self.scheduler_service.initialize()
        
        self._initialized = True
        logger.info("Proactive Engine initialized")
    
    # Initiative operations
    async def detect_initiative(self, request: InitiativeRequest) -> InitiativeResponse:
        """Detect proactive initiative opportunity."""
        if not self.initiative_service:
            raise RuntimeError("Initiative service not initialized")
        return await self.initiative_service.detect_initiative(request)
    
    async def execute_proactive_action(self, request: ProactiveActionRequest) -> ProactiveActionResponse:
        """Execute a proactive action."""
        if not self.initiative_service:
            raise RuntimeError("Initiative service not initialized")
        return await self.initiative_service.execute_proactive_action(request)
    
    # Anticipation operations
    async def anticipate_needs(self, request: AnticipationRequest) -> AnticipationResponse:
        """Anticipate user needs."""
        if not self.anticipation_service:
            raise RuntimeError("Anticipation service not initialized")
        return await self.anticipation_service.anticipate_needs(request)
    
    # Suggestion operations
    async def generate_suggestions(self, request: SuggestionRequest) -> SuggestionResponse:
        """Generate personalized suggestions."""
        if not self.suggestion_service:
            raise RuntimeError("Suggestion service not initialized")
        return await self.suggestion_service.generate_suggestions(request)
    
    # Reminder operations
    async def create_reminder(self, request: ReminderRequest) -> ReminderResponse:
        """Create a proactive reminder."""
        if not self.reminder_service:
            raise RuntimeError("Reminder service not initialized")
        return await self.reminder_service.create_reminder(request)
    
    async def list_reminders(
        self,
        user_id: str,
        companion_id: str,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List reminders for a user."""
        if not self.reminder_service:
            raise RuntimeError("Reminder service not initialized")
        return await self.reminder_service.list_reminders(user_id, companion_id, status, limit)
    
    async def cancel_reminder(self, reminder_id: str) -> bool:
        """Cancel a reminder."""
        if not self.reminder_service:
            raise RuntimeError("Reminder service not initialized")
        return await self.reminder_service.cancel_reminder(reminder_id)
    
    async def complete_reminder(self, reminder_id: str) -> bool:
        """Mark a reminder as completed."""
        if not self.reminder_service:
            raise RuntimeError("Reminder service not initialized")
        return await self.reminder_service.complete_reminder(reminder_id)
    
    # Check-in operations
    async def create_check_in(self, request: CheckInRequest) -> CheckInResponse:
        """Create a proactive check-in."""
        if not self.check_in_service:
            raise RuntimeError("Check-in service not initialized")
        return await self.check_in_service.create_check_in(request)
    
    async def should_check_in(
        self,
        user_id: str,
        companion_id: str,
        check_in_type: str = "general"
    ) -> bool:
        """Determine if a check-in is warranted."""
        if not self.check_in_service:
            raise RuntimeError("Check-in service not initialized")
        return await self.check_in_service.should_check_in(user_id, companion_id, check_in_type)
    
    async def get_check_in_history(
        self,
        user_id: str,
        companion_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get check-in history."""
        if not self.check_in_service:
            raise RuntimeError("Check-in service not initialized")
        return await self.check_in_service.get_check_in_history(user_id, companion_id, limit)
    
    # Scheduler operations
    async def create_schedule(self, request: ScheduleRequest) -> ScheduleResponse:
        """Create a scheduled action."""
        if not self.scheduler_service:
            raise RuntimeError("Scheduler service not initialized")
        return await self.scheduler_service.create_schedule(request)
    
    async def list_schedules(
        self,
        user_id: str,
        companion_id: str,
        active_only: bool = True,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List schedules for a user."""
        if not self.scheduler_service:
            raise RuntimeError("Scheduler service not initialized")
        return await self.scheduler_service.list_schedules(user_id, companion_id, active_only, limit)
    
    async def update_schedule(
        self,
        schedule_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a schedule."""
        if not self.scheduler_service:
            raise RuntimeError("Scheduler service not initialized")
        return await self.scheduler_service.update_schedule(schedule_id, updates)
    
    async def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a schedule."""
        if not self.scheduler_service:
            raise RuntimeError("Scheduler service not initialized")
        return await self.scheduler_service.delete_schedule(schedule_id)
    
    async def execute_due_jobs(self) -> List[Dict[str, Any]]:
        """Execute all due scheduled jobs."""
        if not self.scheduler_service:
            raise RuntimeError("Scheduler service not initialized")
        return await self.scheduler_service.execute_due_jobs()
    
    # Health check
    async def health_check(self) -> HealthResponse:
        """Comprehensive health check."""
        start_time = time.time()
        
        checks = {
            "initiative_service": False,
            "anticipation_service": False,
            "suggestion_service": False,
            "reminder_service": False,
            "check_in_service": False,
            "scheduler_service": False,
        }
        
        models_loaded = {}
        
        # Check each service
        if self.initiative_service:
            health = await self.initiative_service.health_check()
            checks["initiative_service"] = health.get("initialized", False)
        
        if self.anticipation_service:
            health = await self.anticipation_service.health_check()
            checks["anticipation_service"] = health.get("initialized", False)
        
        if self.suggestion_service:
            health = await self.suggestion_service.health_check()
            checks["suggestion_service"] = health.get("initialized", False)
        
        if self.reminder_service:
            health = await self.reminder_service.health_check()
            checks["reminder_service"] = health.get("initialized", False)
        
        if self.check_in_service:
            health = await self.check_in_service.health_check()
            checks["check_in_service"] = health.get("initialized", False)
        
        if self.scheduler_service:
            health = await self.scheduler_service.health_check()
            checks["scheduler_service"] = health.get("initialized", False)
            models_loaded["scheduler_running"] = health.get("running", False)
        
        # Determine overall status
        all_healthy = all(checks.values())
        any_healthy = any(checks.values())
        
        if all_healthy:
            status = "healthy"
        elif any_healthy:
            status = "degraded"
        else:
            status = "unhealthy"
        
        processing_time = (time.time() - start_time) * 1000
        
        return HealthResponse(
            service="proactive-engine",
            version="0.1.0",
            status=status,
            checks=checks,
            models_loaded=models_loaded,
            scheduler_status="running" if models_loaded.get("scheduler_running") else "stopped",
            processing_time_ms=processing_time,
        )
    
    async def close(self) -> None:
        """Close all services."""
        logger.info("Closing Proactive Engine")
        
        services = [
            ("initiative", self.initiative_service),
            ("anticipation", self.anticipation_service),
            ("suggestion", self.suggestion_service),
            ("reminder", self.reminder_service),
            ("check_in", self.check_in_service),
            ("scheduler", self.scheduler_service),
        ]
        
        for name, service in services:
            if service:
                try:
                    await service.close()
                    logger.info(f"Closed {name} service")
                except Exception as e:
                    logger.error(f"Error closing {name} service", error=str(e))
        
        self._initialized = False
        logger.info("Proactive Engine closed")


# Singleton instance
_proactive_service: Optional[ProactiveService] = None


async def get_proactive_service() -> ProactiveService:
    """Get or create Proactive service singleton."""
    global _proactive_service
    if _proactive_service is None:
        _proactive_service = ProactiveService()
        await _proactive_service.initialize()
    return _proactive_service


async def close_proactive_service() -> None:
    """Close Proactive service."""
    global _proactive_service
    if _proactive_service:
        await _proactive_service.close()
        _proactive_service = None