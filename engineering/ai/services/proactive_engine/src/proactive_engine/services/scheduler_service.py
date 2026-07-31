"""Scheduler Service for managing proactive scheduling and recurring actions."""

import logging
import time
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from proactive_engine.config import settings
from proactive_engine.models.requests import ScheduleRequest
from proactive_engine.models.responses import ScheduleResponse

logger = logging.getLogger(__name__)


@dataclass
class ScheduledJob:
    """Represents a scheduled job."""
    id: str
    user_id: str
    companion_id: str
    action_type: str
    schedule: Dict[str, Any]  # cron expression or interval
    content_template: str
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    next_execution: Optional[datetime] = None
    last_execution: Optional[datetime] = None
    execution_count: int = 0


class SchedulerService:
    """Service for managing proactive scheduling."""
    
    def __init__(self):
        self.http_client = None  # Would be set if needed
        self._initialized = False
        self.jobs: Dict[str, ScheduledJob] = {}
        self._running = False
    
    async def initialize(self) -> None:
        """Initialize the scheduler service."""
        logger.info("Initializing Scheduler service")
        
        self._initialized = True
        self._running = True
        
        # In production, start background scheduler task
        # asyncio.create_task(self._scheduler_loop())
        
        logger.info("Scheduler service initialized")
    
    async def create_schedule(self, request: ScheduleRequest) -> ScheduleResponse:
        """Create a new scheduled action."""
        start_time = time.time()
        
        schedule_id = f"sched_{uuid.uuid4().hex[:12]}"
        
        # Calculate next execution time
        next_execution = self._calculate_next_execution(request.schedule)
        
        # Create job
        job = ScheduledJob(
            id=schedule_id,
            user_id=str(request.user_id),
            companion_id=str(request.companion_id),
            action_type=request.action_type,
            schedule=request.schedule,
            content_template=request.content_template,
            conditions=request.conditions or [],
            active=request.active,
            next_execution=next_execution,
        )
        
        self.jobs[schedule_id] = job
        
        processing_time = (time.time() - start_time) * 1000
        
        return ScheduleResponse(
            user_id=request.user_id,
            companion_id=request.companion_id,
            schedule_id=schedule_id,
            action_type=request.action_type,
            schedule=request.schedule,
            content_template=request.content_template,
            conditions=request.conditions or [],
            active=request.active,
            next_execution=next_execution,
            processing_time_ms=processing_time,
            request_id=request.request_id,
        )
    
    async def get_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """Get a schedule by ID."""
        job = self.jobs.get(schedule_id)
        if not job:
            return None
        return self._job_to_dict(job)
    
    async def list_schedules(
        self,
        user_id: str,
        companion_id: str,
        active_only: bool = True,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List schedules for a user."""
        filtered = [
            self._job_to_dict(job) for job in self.jobs.values()
            if job.user_id == user_id and job.companion_id == companion_id
        ]
        
        if active_only:
            filtered = [j for j in filtered if j["active"]]
        
        # Sort by next execution
        filtered.sort(key=lambda x: x.get("next_execution") or datetime.max)
        
        return filtered[:limit]
    
    async def update_schedule(
        self,
        schedule_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a schedule."""
        job = self.jobs.get(schedule_id)
        if not job:
            return None
        
        # Update allowed fields
        allowed_fields = ["action_type", "schedule", "content_template", "conditions", "active"]
        for field in allowed_fields:
            if field in updates:
                setattr(job, field, updates[field])
        
        job.updated_at = datetime.now()
        
        # Recalculate next execution if schedule changed
        if "schedule" in updates:
            job.next_execution = self._calculate_next_execution(updates["schedule"])
        
        return self._job_to_dict(job)
    
    async def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a schedule."""
        if schedule_id in self.jobs:
            del self.jobs[schedule_id]
            return True
        return False
    
    async def pause_schedule(self, schedule_id: str) -> bool:
        """Pause a schedule."""
        job = self.jobs.get(schedule_id)
        if not job:
            return False
        job.active = False
        job.updated_at = datetime.now()
        return True
    
    async def resume_schedule(self, schedule_id: str) -> bool:
        """Resume a schedule."""
        job = self.jobs.get(schedule_id)
        if not job:
            return False
        job.active = True
        job.updated_at = datetime.now()
        job.next_execution = self._calculate_next_execution(job.schedule)
        return True
    
    async def execute_due_jobs(self) -> List[Dict[str, Any]]:
        """Execute all due jobs (called by scheduler loop)."""
        now = datetime.now()
        executed = []
        
        for job in self.jobs.values():
            if (job.active and job.next_execution and job.next_execution <= now):
                result = await self._execute_job(job)
                executed.append(result)
                
                # Update job
                job.last_execution = now
                job.execution_count += 1
                job.next_execution = self._calculate_next_execution(job.schedule, from_time=now)
        
        return executed
    
    async def _execute_job(self, job: ScheduledJob) -> Dict[str, Any]:
        """Execute a scheduled job."""
        logger.info("Executing scheduled job", job_id=job.id, action_type=job.action_type)
        
        # Render content template
        content = self._render_template(job.content_template, job)
        
        # Check conditions
        if job.conditions:
            conditions_met = await self._check_conditions(job.conditions, job)
            if not conditions_met:
                return {
                    "job_id": job.id,
                    "status": "skipped",
                    "reason": "Conditions not met",
                }
        
        # Execute action based on type
        result = await self._execute_action(job.action_type, {
            "user_id": job.user_id,
            "companion_id": job.companion_id,
            "content": content,
            "template": job.content_template,
        })
        
        return {
            "job_id": job.id,
            "status": "executed" if result.get("success") else "failed",
            "result": result,
            "executed_at": datetime.now().isoformat(),
        }
    
    def _calculate_next_execution(
        self,
        schedule: Dict[str, Any],
        from_time: Optional[datetime] = None
    ) -> Optional[datetime]:
        """Calculate next execution time from schedule."""
        base_time = from_time or datetime.now()
        
        schedule_type = schedule.get("type", "interval")
        
        if schedule_type == "interval":
            # Interval schedule: {"type": "interval", "seconds": 3600}
            seconds = schedule.get("seconds", 3600)
            return base_time + timedelta(seconds=seconds)
        
        elif schedule_type == "cron":
            # Cron schedule: {"type": "cron", "expression": "0 9 * * *"}
            # In production, use a cron parser like croniter
            expression = schedule.get("expression", "0 * * * *")
            # Simplified: assume hourly
            return base_time + timedelta(hours=1)
        
        elif schedule_type == "daily":
            # Daily at specific time: {"type": "daily", "hour": 9, "minute": 0}
            hour = schedule.get("hour", 9)
            minute = schedule.get("minute", 0)
            next_time = base_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_time <= base_time:
                next_time += timedelta(days=1)
            return next_time
        
        elif schedule_type == "weekly":
            # Weekly: {"type": "weekly", "weekday": 0, "hour": 9, "minute": 0}
            weekday = schedule.get("weekday", 0)  # 0 = Monday
            hour = schedule.get("hour", 9)
            minute = schedule.get("minute", 0)
            
            days_ahead = weekday - base_time.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            
            next_time = base_time + timedelta(days=days_ahead)
            return next_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        return base_time + timedelta(hours=1)  # Default
    
    def _render_template(self, template: str, job: ScheduledJob) -> str:
        """Render content template with context."""
        # Simple template rendering
        context = {
            "user_id": job.user_id,
            "companion_id": job.companion_id,
            "execution_count": job.execution_count,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M"),
        }
        
        result = template
        for key, value in context.items():
            result = result.replace(f"{{{key}}}", str(value))
        
        return result
    
    async def _check_conditions(
        self,
        conditions: List[Dict[str, Any]],
        job: ScheduledJob
    ) -> bool:
        """Check if conditions are met for execution."""
        # In production, evaluate conditions against user state
        # For now, always return True
        return True
    
    async def _execute_action(self, action_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an action based on type."""
        logger.info("Executing action", action_type=action_type, params=params)
        
        # This would integrate with other services
        return {
            "success": True,
            "action_type": action_type,
            "message": f"Action {action_type} executed",
        }
    
    def _job_to_dict(self, job: ScheduledJob) -> Dict[str, Any]:
        """Convert job to dictionary."""
        return {
            "id": job.id,
            "user_id": job.user_id,
            "companion_id": job.companion_id,
            "action_type": job.action_type,
            "schedule": job.schedule,
            "content_template": job.content_template,
            "conditions": job.conditions,
            "active": job.active,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
            "next_execution": job.next_execution.isoformat() if job.next_execution else None,
            "last_execution": job.last_execution.isoformat() if job.last_execution else None,
            "execution_count": job.execution_count,
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the service."""
        active_jobs = [j for j in self.jobs.values() if j.active]
        due_jobs = [
            j for j in active_jobs 
            if j.next_execution and j.next_execution <= datetime.now()
        ]
        
        return {
            "initialized": self._initialized,
            "running": self._running,
            "total_jobs": len(self.jobs),
            "active_jobs": len(active_jobs),
            "due_jobs": len(due_jobs),
        }
    
    async def close(self) -> None:
        """Cleanup resources."""
        self._running = False
        self._initialized = False
        logger.info("Scheduler service closed")


# Singleton instance
_scheduler_service: Optional[SchedulerService] = None


async def get_scheduler_service() -> SchedulerService:
    """Get or create Scheduler service singleton."""
    global _scheduler_service
    if _scheduler_service is None:
        _scheduler_service = SchedulerService()
        await _scheduler_service.initialize()
    return _scheduler_service


async def close_scheduler_service() -> None:
    """Close Scheduler service."""
    global _scheduler_service
    if _scheduler_service:
        await _scheduler_service.close()
        _scheduler_service = None