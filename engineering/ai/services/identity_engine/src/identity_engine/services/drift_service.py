"""Drift Service - Monitors and manages identity drift over time."""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import uuid
import structlog

from pao_shared.observability import setup_tracing, setup_metrics

from ..models import (
    IdentityConfig, DriftResult, DriftSeverity, DriftDimension,
    DriftAlert, FingerprintVector,
)
from .fingerprint_service import FingerprintService

logger = structlog.get_logger(__name__)


class DriftService:
    """Service for monitoring and managing identity drift."""
    
    def __init__(
        self,
        repository=None,
        fingerprint_service: Optional[FingerprintService] = None,
        alert_service=None,
        evolution_service=None,
    ):
        self.repository = repository
        self.fingerprint_service = fingerprint_service
        self.alert_service = alert_service
        self.evolution_service = evolution_service
        self._tracer = setup_tracing("identity-engine", "drift-service")
        self._meter = setup_metrics("identity-engine", "drift-service")
        
        # Metrics
        self._drift_checks = self._meter.create_counter(
            "drift_checks_total", "Total drift checks performed"
        )
        self._alerts_created = self._meter.create_counter(
            "drift_alerts_created_total", "Total drift alerts created"
        )
        self._auto_evolution_triggered = self._meter.create_counter(
            "auto_evolution_triggered_total", "Auto-evolutions triggered"
        )
        self._check_duration = self._meter.create_histogram(
            "drift_check_duration_seconds", "Drift check duration"
        )
        
        # Configuration
        self.check_interval_hours = 24
        self.auto_trigger_evolution = True
        self.evolution_trigger_severity = DriftSeverity.MODERATE
    
    async def schedule_drift_monitoring(
        self,
        companion_id: str,
        interval_hours: Optional[int] = None,
    ) -> str:
        """Schedule periodic drift monitoring for a companion."""
        interval = interval_hours or self.check_interval_hours
        
        # In a real implementation, this would create a scheduled job
        # For now, return a schedule ID
        schedule_id = f"drift_schedule_{companion_id}_{uuid.uuid4().hex[:8]}"
        
        if self.repository:
            await self.repository.save_drift_schedule({
                "id": schedule_id,
                "companion_id": companion_id,
                "interval_hours": interval,
                "enabled": True,
                "created_at": datetime.utcnow().isoformat(),
                "next_run": (datetime.utcnow() + timedelta(hours=interval)).isoformat(),
            })
        
        logger.info("Drift monitoring scheduled", companion_id=companion_id, interval_hours=interval)
        return schedule_id
    
    async def run_drift_check(
        self,
        companion_id: str,
        baseline_version: Optional[int] = None,
    ) -> DriftResult:
        """Run a single drift check for a companion."""
        with self._tracer.start_as_current_span("run_drift_check") as span:
            span.set_attribute("companion_id", companion_id)
            
            start_time = datetime.utcnow()
            
            if not self.fingerprint_service:
                raise ValueError("Fingerprint service not configured")
            
            # Run drift detection
            result = await self.fingerprint_service.detect_drift(
                companion_id=companion_id,
                baseline_version=baseline_version,
            )
            
            # Check if we should trigger auto-evolution
            if self.auto_trigger_evolution and self.evolution_service:
                await self._check_auto_evolution(companion_id, result)
            
            # Update schedule next run
            if self.repository:
                await self.repository.update_drift_schedule_next_run(companion_id)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            self._drift_checks.add(1, {"companion_id": companion_id, "severity": result.severity.value})
            self._check_duration.record(duration)
            
            logger.info(
                "Drift check completed",
                companion_id=companion_id,
                severity=result.severity.value,
                drift_score=result.overall_drift_score,
            )
            
            return result
    
    async def _check_auto_evolution(self, companion_id: str, drift_result: DriftResult):
        """Check if drift warrants auto-evolution proposal."""
        if drift_result.severity.value >= self.evolution_trigger_severity.value:
            # Check if we already have a pending proposal for this drift
            existing = await self.repository.get_pending_evolution_proposals(companion_id)
            drift_proposals = [p for p in existing if p.trigger.type.value == "drift_detected"]
            
            if not drift_proposals:
                # Trigger evolution proposal
                try:
                    proposal = await self.evolution_service.create_proposal_from_drift(
                        companion_id=companion_id,
                        drift_result=drift_result,
                    )
                    self._auto_evolution_triggered.add(1, {
                        "companion_id": companion_id,
                        "severity": drift_result.severity.value,
                    })
                    logger.info(
                        "Auto-evolution triggered",
                        companion_id=companion_id,
                        proposal_id=proposal.id,
                        drift_severity=drift_result.severity.value,
                    )
                except Exception as e:
                    logger.error(
                        "Failed to create auto-evolution proposal",
                        companion_id=companion_id,
                        error=str(e),
                    )
    
    async def get_drift_summary(self, companion_id: str) -> Dict[str, Any]:
        """Get a summary of drift status for a companion."""
        latest_drift = await self.fingerprint_service.get_latest_drift(companion_id)
        
        if not latest_drift:
            return {
                "companion_id": companion_id,
                "status": "no_data",
                "message": "No drift analysis available",
            }
        
        # Get recent history
        history = await self.fingerprint_service.get_drift_history(companion_id, days=30)
        
        # Compute trends
        drift_scores = [d.overall_drift_score for d in history]
        trend = "stable"
        if len(drift_scores) >= 3:
            recent_avg = sum(drift_scores[-3:]) / 3
            older_avg = sum(drift_scores[:-3]) / max(1, len(drift_scores) - 3)
            if recent_avg > older_avg * 1.2:
                trend = "increasing"
            elif recent_avg < older_avg * 0.8:
                trend = "decreasing"
        
        # Active alerts
        active_alerts = []
        if self.repository:
            active_alerts = await self.repository.get_active_drift_alerts(companion_id)
        
        return {
            "companion_id": companion_id,
            "status": latest_drift.severity.value,
            "overall_drift_score": latest_drift.overall_drift_score,
            "severity": latest_drift.severity.value,
            "top_drifted_dimensions": [
                {"dimension": d.value, "score": s}
                for d, s in latest_drift.get_top_drifted_dimensions(3)
            ],
            "trend": trend,
            "requires_review": latest_drift.requires_review,
            "requires_reevaluation": latest_drift.requires_reevaluation,
            "requires_rollback": latest_drift.requires_rollback,
            "active_alerts": len(active_alerts),
            "last_check": latest_drift.analyzed_at,
            "check_count_30d": len(history),
        }
    
    async def get_drift_timeline(
        self,
        companion_id: str,
        days: int = 90,
    ) -> List[Dict[str, Any]]:
        """Get drift timeline for visualization."""
        history = await self.fingerprint_service.get_drift_history(companion_id, days)
        
        timeline = []
        for drift in history:
            timeline.append({
                "date": drift.analyzed_at,
                "overall_drift": drift.overall_drift_score,
                "severity": drift.severity.value,
                "dimensions": {
                    dim.value: score
                    for dim, score in drift.dimension_drifts.items()
                },
                "significant_changes": len(drift.significant_changes),
                "requires_action": drift.requires_review or drift.requires_reevaluation,
            })
        
        return timeline
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge a drift alert."""
        if not self.repository:
            return False
        
        success = await self.repository.acknowledge_drift_alert(alert_id, acknowledged_by)
        if success:
            logger.info("Drift alert acknowledged", alert_id=alert_id, by=acknowledged_by)
        return success
    
    async def resolve_alert(
        self,
        alert_id: str,
        resolved_by: str,
        resolution_notes: str,
    ) -> bool:
        """Resolve a drift alert."""
        if not self.repository:
            return False
        
        success = await self.repository.resolve_drift_alert(
            alert_id, resolved_by, resolution_notes
        )
        if success:
            logger.info("Drift alert resolved", alert_id=alert_id, by=resolved_by)
        return success
    
    async def get_active_alerts(
        self,
        companion_id: Optional[str] = None,
        severity: Optional[DriftSeverity] = None,
    ) -> List[DriftAlert]:
        """Get active drift alerts."""
        if not self.repository:
            return []
        return await self.repository.get_active_drift_alerts(
            companion_id=companion_id,
            severity=severity,
        )
    
    async def configure_monitoring(
        self,
        companion_id: str,
        interval_hours: int,
        auto_evolution: bool = True,
        trigger_severity: DriftSeverity = DriftSeverity.MODERATE,
    ) -> Dict[str, Any]:
        """Configure drift monitoring for a companion."""
        config = {
            "companion_id": companion_id,
            "interval_hours": interval_hours,
            "auto_evolution": auto_evolution,
            "trigger_severity": trigger_severity.value,
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        if self.repository:
            await self.repository.save_drift_monitoring_config(config)
        
        # Update service config
        self.check_interval_hours = interval_hours
        self.auto_trigger_evolution = auto_evolution
        self.evolution_trigger_severity = trigger_severity
        
        logger.info("Drift monitoring configured", **config)
        return config
    
    async def run_bulk_drift_check(
        self,
        companion_ids: List[str],
    ) -> Dict[str, DriftResult]:
        """Run drift checks for multiple companions."""
        results = {}
        
        for companion_id in companion_ids:
            try:
                result = await self.run_drift_check(companion_id)
                results[companion_id] = result
            except Exception as e:
                logger.error("Bulk drift check failed", companion_id=companion_id, error=str(e))
                results[companion_id] = None
        
        return results
    
    async def get_companions_needing_review(
        self,
        min_severity: DriftSeverity = DriftSeverity.MODERATE,
    ) -> List[Dict[str, Any]]:
        """Get all companions that need drift review."""
        if not self.repository:
            return []
        
        companions = await self.repository.get_companions_with_recent_drift(min_severity)
        
        results = []
        for companion in companions:
            summary = await self.get_drift_summary(companion["companion_id"])
            summary["companion_id"] = companion["companion_id"]
            results.append(summary)
        
        return results