"""Reminder Service for managing proactive reminders."""

import logging
import time
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

import httpx

from proactive_engine.config import settings
from proactive_engine.models.requests import ReminderRequest
from proactive_engine.models.responses import ReminderResponse

logger = logging.getLogger(__name__)


class ReminderService:
    """Service for managing proactive reminders."""
    
    REMINDER_TYPES = [
        "task",
        "event", 
        "habit",
        "medication",
        "custom",
    ]
    
    def __init__(self):
        self.http_client: Optional[httpx.AsyncClient] = None
        self._initialized = False
        # In-memory storage (would be replaced with database in production)
        self.reminders: Dict[str, Dict[str, Any]] = {}
    
    async def initialize(self) -> None:
        """Initialize the reminder service."""
        logger.info("Initializing Reminder service")
        
        self.http_client = httpx.AsyncClient(
            timeout=settings.http_timeout,
            limits=httpx.Limits(max_connections=10)
        )
        
        self._initialized = True
        logger.info("Reminder service initialized")
    
    async def create_reminder(self, request: ReminderRequest) -> ReminderResponse:
        """Create a new reminder."""
        start_time = time.time()
        
        reminder_id = f"rem_{uuid.uuid4().hex[:12]}"
        
        # Determine scheduled time
        if request.scheduled_time:
            scheduled_time = request.scheduled_time
        else:
            # Default to next hour
            scheduled_time = datetime.now() + timedelta(hours=1)
        
        # Create reminder object
        reminder = {
            "id": reminder_id,
            "user_id": str(request.user_id),
            "companion_id": str(request.companion_id),
            "reminder_type": request.reminder_type,
            "title": request.title,
            "description": request.description,
            "scheduled_time": scheduled_time,
            "recurrence": request.recurrence,
            "priority": request.priority,
            "context": request.context or {},
            "status": "created",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        
        # Store reminder
        self.reminders[reminder_id] = reminder
        
        # If scheduling is enabled, schedule the reminder
        if settings.enable_scheduling and settings.scheduler_enabled:
            await self._schedule_reminder(reminder)
            reminder["status"] = "scheduled"
        
        processing_time = (time.time() - start_time) * 1000
        
        return ReminderResponse(
            user_id=request.user_id,
            companion_id=request.companion_id,
            reminder_id=reminder_id,
            title=request.title,
            description=request.description,
            scheduled_time=scheduled_time,
            recurrence=request.recurrence,
            priority=request.priority,
            status=reminder["status"],
            processing_time_ms=processing_time,
            request_id=request.request_id,
        )
    
    async def get_reminder(self, reminder_id: str) -> Optional[Dict[str, Any]]:
        """Get a reminder by ID."""
        return self.reminders.get(reminder_id)
    
    async def list_reminders(
        self,
        user_id: str,
        companion_id: str,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List reminders for a user."""
        filtered = [
            r for r in self.reminders.values()
            if r["user_id"] == user_id and r["companion_id"] == companion_id
        ]
        
        if status:
            filtered = [r for r in filtered if r["status"] == status]
        
        # Sort by scheduled time
        filtered.sort(key=lambda x: x["scheduled_time"])
        
        return filtered[:limit]
    
    async def update_reminder(
        self,
        reminder_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a reminder."""
        reminder = self.reminders.get(reminder_id)
        if not reminder:
            return None
        
        # Update allowed fields
        allowed_fields = ["title", "description", "scheduled_time", "recurrence", "priority", "context"]
        for field in allowed_fields:
            if field in updates:
                reminder[field] = updates[field]
        
        reminder["updated_at"] = datetime.now()
        
        # Reschedule if time changed
        if "scheduled_time" in updates and settings.enable_scheduling:
            await self._schedule_reminder(reminder)
        
        return reminder
    
    async def cancel_reminder(self, reminder_id: str) -> bool:
        """Cancel a reminder."""
        reminder = self.reminders.get(reminder_id)
        if not reminder:
            return False
        
        reminder["status"] = "cancelled"
        reminder["updated_at"] = datetime.now()
        
        return True
    
    async def complete_reminder(self, reminder_id: str) -> bool:
        """Mark a reminder as completed."""
        reminder = self.reminders.get(reminder_id)
        if not reminder:
            return False
        
        reminder["status"] = "completed"
        reminder["updated_at"] = datetime.now()
        reminder["completed_at"] = datetime.now()
        
        # Handle recurrence
        if reminder.get("recurrence"):
            await self._create_next_occurrence(reminder)
        
        return True
    
    async def _schedule_reminder(self, reminder: Dict[str, Any]) -> None:
        """Schedule a reminder for execution."""
        # In production, this would integrate with a scheduler (APScheduler, Celery beat, etc.)
        logger.info(
            "Scheduling reminder",
            reminder_id=reminder["id"],
            scheduled_time=reminder["scheduled_time"],
        )
    
    async def _create_next_occurrence(self, reminder: Dict[str, Any]) -> None:
        """Create next occurrence for recurring reminder."""
        # Parse cron expression or interval
        # For simplicity, just add a day
        next_time = reminder["scheduled_time"] + timedelta(days=1)
        
        new_reminder = reminder.copy()
        new_reminder["id"] = f"rem_{uuid.uuid4().hex[:12]}"
        new_reminder["scheduled_time"] = next_time
        new_reminder["status"] = "created"
        new_reminder["created_at"] = datetime.now()
        new_reminder["updated_at"] = datetime.now()
        new_reminder.pop("completed_at", None)
        
        self.reminders[new_reminder["id"]] = new_reminder
        
        if settings.enable_scheduling:
            await self._schedule_reminder(new_reminder)
    
    async def get_due_reminders(self, before: datetime) -> List[Dict[str, Any]]:
        """Get reminders due before a certain time."""
        due = [
            r for r in self.reminders.values()
            if r["status"] in ["scheduled", "active"]
            and r["scheduled_time"] <= before
        ]
        return due
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the service."""
        return {
            "initialized": self._initialized,
            "http_client_ready": self.http_client is not None,
            "total_reminders": len(self.reminders),
            "active_reminders": len([
                r for r in self.reminders.values()
                if r["status"] in ["scheduled", "active"]
            ]),
        }
    
    async def close(self) -> None:
        """Cleanup resources."""
        if self.http_client:
            await self.http_client.aclose()
        self._initialized = False
        logger.info("Reminder service closed")


# Singleton instance
_reminder_service: Optional[ReminderService] = None


async def get_reminder_service() -> ReminderService:
    """Get or create Reminder service singleton."""
    global _reminder_service
    if _reminder_service is None:
        _reminder_service = ReminderService()
        await _reminder_service.initialize()
    return _reminder_service


async def close_reminder_service() -> None:
    """Close Reminder service."""
    global _reminder_service
    if _reminder_service:
        await _reminder_service.close()
        _reminder_service = None