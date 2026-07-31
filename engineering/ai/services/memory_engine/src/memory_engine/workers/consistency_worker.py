"""Consistency Worker - Temporal activities for consistency validation."""

from typing import Optional, List, Dict, Any
from datetime import datetime
import structlog

from temporalio import activity

from pao_shared.observability import get_tracer, get_meter

from ..config import settings
from ..repositories import (
    PostgresRepository,
    QdrantRepository,
    KuzuRepository,
)
from ..services import ConsistencyService

logger = structlog.get_logger(__name__)


class ConsistencyWorker:
    """
    Temporal activities for consistency validation workflow.
    
    Runs periodic consistency checks across all memory types.
    """
    
    def __init__(
        self,
        consistency_service: ConsistencyService,
        postgres_repo: Optional[PostgresRepository] = None,
        qdrant_repo: Optional[QdrantRepository] = None,
        kuzu_repo: Optional[KuzuRepository] = None,
    ):
        self.consistency_service = consistency_service
        self.postgres = postgres_repo
        self.qdrant = qdrant_repo
        self.kuzu = kuzu_repo
        
        self._tracer = get_tracer()
        self._meter = get_meter()
        
        self._activity_runs = self._meter.create_counter(
            "consistency_activity_runs_total", "Total activity runs", {"activity", "status"}
        )
        self._activity_duration = self._meter.create_histogram(
            "consistency_activity_duration_seconds", "Activity duration"
        )
    
    @activity.defn(name="run_consistency_checks")
    async def run_consistency_checks(
        self, companion_id: str, check_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Activity: Run all consistency checks for a companion."""
        start_time = datetime.utcnow()
        
        with self._tracer.start_as_current_span("activity_run_consistency") as span:
            span.set_attribute("companion_id", companion_id)
            
            try:
                report = await self.consistency_service.validate_all(companion_id)
                
                result = {
                    "companion_id": companion_id,
                    "checked_at": report.checked_at,
                    "total_issues": report.total_issues,
                    "auto_resolved": report.auto_resolved,
                    "requires_user_review": report.requires_user_review,
                    "issues": [issue.model_dump() for issue in report.issues],
                    "checks_run": [c.value for c in report.checks_run],
                    "duration_ms": report.duration_ms,
                }
                
                self._activity_runs.add(1, {"activity": "run_consistency_checks", "status": "success"})
                logger.info("Consistency checks completed", companion_id=companion_id, total_issues=report.total_issues)
                return result
                
            except Exception as e:
                self._activity_runs.add(1, {"activity": "run_consistency_checks", "status": "failed"})
                logger.error("Failed to run consistency checks", companion_id=companion_id, error=str(e))
                raise
            finally:
                self._activity_duration.record((datetime.utcnow() - start_time).total_seconds())
    
    @activity.defn(name="resolve_issues")
    async def resolve_issues(
        self, companion_id: str, issue_resolutions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Activity: Resolve consistency issues."""
        start_time = datetime.utcnow()
        
        with self._tracer.start_as_current_span("activity_resolve_issues") as span:
            span.set_attribute("companion_id", companion_id)
            span.set_attribute("issue_count", len(issue_resolutions))
            
            try:
                resolved_count = 0
                
                for resolution in issue_resolutions:
                    issue_id = resolution.get("issue_id")
                    resolution_text = resolution.get("resolution")
                    resolved_by = resolution.get("resolved_by", "system")
                    
                    if issue_id and resolution_text:
                        success = await self.consistency_service.resolve_issue(
                            issue_id, resolution_text, resolved_by
                        )
                        if success:
                            resolved_count += 1
                
                result = {
                    "companion_id": companion_id,
                    "resolved": resolved_count,
                    "total": len(issue_resolutions),
                }
                
                self._activity_runs.add(1, {"activity": "resolve_issues", "status": "success"})
                return result
                
            except Exception as e:
                self._activity_runs.add(1, {"activity": "resolve_issues", "status": "failed"})
                logger.error("Failed to resolve issues", companion_id=companion_id, error=str(e))
                raise
            finally:
                self._activity_duration.record((datetime.utcnow() - start_time).total_seconds())
    
    @activity.defn(name="emit_consistency_events")
    async def emit_consistency_events(
        self, companion_id: str, report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Activity: Emit consistency check events to Kafka."""
        start_time = datetime.utcnow()
        
        with self._tracer.start_as_current_span("activity_emit_consistency_events") as span:
            span.set_attribute("companion_id", companion_id)
            
            try:
                event = {
                    "event_type": "consistency.validated",
                    "companion_id": companion_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "payload": {
                        "total_issues": report.get("total_issues", 0),
                        "auto_resolved": report.get("auto_resolved", 0),
                        "requires_user_review": report.get("requires_user_review", 0),
                    },
                }
                
                # In production: await kafka_producer.send_and_wait("memory.events", event)
                logger.info("Consistency event emitted", companion_id=companion_id, event=event)
                
                self._activity_runs.add(1, {"activity": "emit_consistency_events", "status": "success"})
                return {"emitted": 1}
                
            except Exception as e:
                self._activity_runs.add(1, {"activity": "emit_consistency_events", "status": "failed"})
                logger.error("Failed to emit consistency events", companion_id=companion_id, error=str(e))
                raise
            finally:
                self._activity_duration.record((datetime.utcnow() - start_time).total_seconds())


@activity.defn(name="validate_consistency")
async def validate_consistency_activity(
    companion_id: str,
    consistency_service: ConsistencyService,
) -> Dict[str, Any]:
    """Standalone activity to run full consistency validation for a companion."""
    report = await consistency_service.validate_all(companion_id)
    return report.model_dump()