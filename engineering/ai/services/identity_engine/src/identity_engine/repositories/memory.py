"""In-memory repository implementation for Identity Engine (development/testing)."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import copy

from .base import BaseRepository
from ..models import (
    IdentityConfig, IdentityVersion, FingerprintVector, FingerprintResult,
    DriftResult, DriftAlert, EvolutionProposal, EvolutionResult,
    EvolutionTrigger, EvolutionEvidence, EvolutionRule,
    IdentityStatus,
)


class MemoryRepository(BaseRepository):
    """In-memory repository for development and testing."""
    
    def __init__(self):
        self._identities: Dict[str, IdentityConfig] = {}
        self._versions: Dict[str, List[IdentityVersion]] = {}  # companion_id -> versions
        self._fingerprints: Dict[str, FingerprintVector] = {}
        self._drift_results: Dict[str, List[DriftResult]] = {}  # companion_id -> results
        self._drift_alerts: Dict[str, DriftAlert] = {}
        self._evolution_proposals: Dict[str, EvolutionProposal] = {}
        self._evolution_results: Dict[str, EvolutionResult] = {}
        self._evolution_evidence: Dict[str, EvolutionEvidence] = {}
        self._evolution_rules: Dict[str, EvolutionRule] = {}
        self._drift_schedules: Dict[str, Dict[str, Any]] = {}
        self._drift_monitoring_configs: Dict[str, Dict[str, Any]] = {}
        self._templates: Dict[str, Dict[str, Any]] = {}
    
    # ==================== Identity ====================
    
    async def save(self, identity: IdentityConfig) -> None:
        """Save an identity configuration."""
        self._identities[identity.id] = copy.deepcopy(identity)
    
    async def get(self, identity_id: str) -> Optional[IdentityConfig]:
        """Get an identity by ID."""
        return copy.deepcopy(self._identities.get(identity_id))
    
    async def get_active(self, companion_id: str) -> Optional[IdentityConfig]:
        """Get the active identity for a companion."""
        for identity in self._identities.values():
            if identity.companion_id == companion_id and identity.status == IdentityStatus.ACTIVE:
                return copy.deepcopy(identity)
        return None
    
    async def get_version(self, companion_id: str, version: int) -> Optional[IdentityConfig]:
        """Get a specific version of identity for a companion."""
        for identity in self._identities.values():
            if identity.companion_id == companion_id and identity.version == version:
                return copy.deepcopy(identity)
        return None
    
    async def list(
        self,
        companion_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[IdentityConfig]:
        """List identities with optional filters."""
        results = []
        for identity in self._identities.values():
            if companion_id and identity.companion_id != companion_id:
                continue
            if status and identity.status.value != status:
                continue
            results.append(copy.deepcopy(identity))
        
        # Sort by created_at descending
        results.sort(key=lambda x: x.created_at, reverse=True)
        return results[offset:offset + limit]
    
    async def deactivate_companion_identities(self, companion_id: str) -> None:
        """Deactivate all identities for a companion."""
        for identity in self._identities.values():
            if identity.companion_id == companion_id:
                identity.status = IdentityStatus.DEPRECATED
    
    async def get_identities_by_companion(self, companion_id: str) -> List[IdentityConfig]:
        """Get all identities for a companion."""
        return [
            copy.deepcopy(identity)
            for identity in self._identities.values()
            if identity.companion_id == companion_id
        ]
    
    # ==================== Identity Versions ====================
    
    async def save_version(self, version: IdentityVersion) -> None:
        """Save an identity version snapshot."""
        if version.companion_id not in self._versions:
            self._versions[version.companion_id] = []
        self._versions[version.companion_id].append(copy.deepcopy(version))
        
        # Keep versions sorted
        self._versions[version.companion_id].sort(key=lambda v: v.version)
    
    async def get_version_history(self, companion_id: str) -> List[IdentityVersion]:
        """Get version history for a companion."""
        return copy.deepcopy(self._versions.get(companion_id, []))
    
    # ==================== Fingerprints ====================
    
    async def save_fingerprint(self, fingerprint: FingerprintVector) -> None:
        """Save a fingerprint vector."""
        self._fingerprints[fingerprint.id] = copy.deepcopy(fingerprint)
    
    async def get_fingerprint(self, fingerprint_id: str) -> Optional[FingerprintVector]:
        """Get a fingerprint by ID."""
        return copy.deepcopy(self._fingerprints.get(fingerprint_id))
    
    async def get_fingerprint_by_version(
        self, companion_id: str, version: int
    ) -> Optional[FingerprintVector]:
        """Get fingerprint for a specific identity version."""
        for fp in self._fingerprints.values():
            if fp.companion_id == companion_id and fp.identity_version == version:
                return copy.deepcopy(fp)
        return None
    
    async def get_latest_fingerprint(self, companion_id: str) -> Optional[FingerprintVector]:
        """Get the latest fingerprint for a companion."""
        fingerprints = [
            fp for fp in self._fingerprints.values()
            if fp.companion_id == companion_id
        ]
        if not fingerprints:
            return None
        latest = max(fingerprints, key=lambda f: f.identity_version)
        return copy.deepcopy(latest)
    
    async def get_earliest_fingerprint(self, companion_id: str) -> Optional[FingerprintVector]:
        """Get the earliest fingerprint for a companion."""
        fingerprints = [
            fp for fp in self._fingerprints.values()
            if fp.companion_id == companion_id
        ]
        if not fingerprints:
            return None
        earliest = min(fingerprints, key=lambda f: f.identity_version)
        return copy.deepcopy(earliest)
    
    # ==================== Drift ====================
    
    async def save_drift_result(self, drift: DriftResult) -> None:
        """Save a drift detection result."""
        if drift.companion_id not in self._drift_results:
            self._drift_results[drift.companion_id] = []
        self._drift_results[drift.companion_id].append(copy.deepcopy(drift))
        
        # Sort by analyzed_at
        self._drift_results[drift.companion_id].sort(key=lambda d: d.analyzed_at)
    
    async def get_latest_drift(self, companion_id: str) -> Optional[DriftResult]:
        """Get the latest drift result for a companion."""
        results = self._drift_results.get(companion_id, [])
        if not results:
            return None
        return copy.deepcopy(results[-1])
    
    async def get_drift_history(
        self, companion_id: str, days: int = 30
    ) -> List[DriftResult]:
        """Get drift history for a companion."""
        results = self._drift_results.get(companion_id, [])
        cutoff = datetime.utcnow() - timedelta(days=days)
        filtered = [
            r for r in results
            if datetime.fromisoformat(r.analyzed_at.replace('Z', '+00:00')) >= cutoff
        ]
        return copy.deepcopy(filtered)
    
    async def get_companions_with_recent_drift(
        self, min_severity: str
    ) -> List[Dict[str, Any]]:
        """Get companions that have recent drift above threshold."""
        severity_order = {"none": 0, "minimal": 1, "moderate": 2, "significant": 3, "critical": 4}
        min_level = severity_order.get(min_severity, 2)
        
        companions = []
        for companion_id, results in self._drift_results.items():
            if not results:
                continue
            latest = results[-1]
            if severity_order.get(latest.severity.value, 0) >= min_level:
                companions.append({
                    "companion_id": companion_id,
                    "latest_drift": copy.deepcopy(latest),
                })
        return companions
    
    # ==================== Drift Alerts ====================
    
    async def save_drift_alert(self, alert: DriftAlert) -> None:
        """Save a drift alert."""
        self._drift_alerts[alert.id] = copy.deepcopy(alert)
    
    async def get_active_drift_alerts(
        self, companion_id: Optional[str] = None, severity: Optional[str] = None
    ) -> List[DriftAlert]:
        """Get active drift alerts."""
        alerts = []
        for alert in self._drift_alerts.values():
            if alert.status != "active":
                continue
            if companion_id and alert.companion_id != companion_id:
                continue
            if severity and alert.severity.value != severity:
                continue
            alerts.append(copy.deepcopy(alert))
        return alerts
    
    async def acknowledge_drift_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge a drift alert."""
        alert = self._drift_alerts.get(alert_id)
        if not alert or alert.status != "active":
            return False
        alert.status = "acknowledged"
        alert.acknowledged_at = datetime.utcnow().isoformat()
        alert.acknowledged_by = acknowledged_by
        return True
    
    async def resolve_drift_alert(
        self, alert_id: str, resolved_by: str, notes: str
    ) -> bool:
        """Resolve a drift alert."""
        alert = self._drift_alerts.get(alert_id)
        if not alert or alert.status not in ["active", "acknowledged"]:
            return False
        alert.status = "resolved"
        alert.resolved_at = datetime.utcnow().isoformat()
        alert.resolved_by = resolved_by
        alert.resolution_notes = notes
        return True
    
    # ==================== Evolution Proposals ====================
    
    async def save_evolution_proposal(self, proposal: EvolutionProposal) -> None:
        """Save an evolution proposal."""
        self._evolution_proposals[proposal.id] = copy.deepcopy(proposal)
    
    async def get_evolution_proposal(self, proposal_id: str) -> Optional[EvolutionProposal]:
        """Get an evolution proposal by ID."""
        return copy.deepcopy(self._evolution_proposals.get(proposal_id))
    
    async def list_evolution_proposals(
        self,
        companion_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[EvolutionProposal]:
        """List evolution proposals with filters."""
        results = []
        for proposal in self._evolution_proposals.values():
            if companion_id and proposal.companion_id != companion_id:
                continue
            if status and proposal.status.value != status:
                continue
            results.append(copy.deepcopy(proposal))
        
        results.sort(key=lambda p: p.created_at, reverse=True)
        return results[offset:offset + limit]
    
    async def get_pending_evolution_proposals(self, companion_id: str) -> List[EvolutionProposal]:
        """Get pending proposals for a companion."""
        return await self.list_evolution_proposals(
            companion_id=companion_id,
            status="pending_review",
            limit=100,
        )
    
    async def get_recent_proposals_by_rule(
        self, companion_id: str, rule_id: str, period_days: int
    ) -> List[EvolutionProposal]:
        """Get recent proposals created by a specific rule."""
        cutoff = datetime.utcnow() - timedelta(days=period_days)
        results = []
        for proposal in self._evolution_proposals.values():
            if proposal.companion_id != companion_id:
                continue
            if not proposal.trigger.metadata or proposal.trigger.metadata.get("rule_id") != rule_id:
                continue
            created = datetime.fromisoformat(proposal.created_at.replace('Z', '+00:00'))
            if created >= cutoff:
                results.append(copy.deepcopy(proposal))
        return results
    
    # ==================== Evolution Results ====================
    
    async def save_evolution_result(self, result: EvolutionResult) -> None:
        """Save an evolution implementation result."""
        self._evolution_results[result.id] = copy.deepcopy(result)
    
    async def get_evolution_result_by_proposal(
        self, proposal_id: str
    ) -> Optional[EvolutionResult]:
        """Get result for a proposal."""
        for result in self._evolution_results.values():
            if result.proposal_id == proposal_id:
                return copy.deepcopy(result)
        return None
    
    async def get_evolution_history(
        self, companion_id: str, limit: int = 50
    ) -> List[EvolutionResult]:
        """Get evolution history for a companion."""
        results = []
        for result in self._evolution_results.values():
            if result.companion_id == companion_id:
                results.append(copy.deepcopy(result))
        
        results.sort(key=lambda r: r.implemented_at, reverse=True)
        return results[:limit]
    
    # ==================== Evolution Evidence ====================
    
    async def save_evolution_evidence(self, evidence: EvolutionEvidence) -> None:
        """Save evolution evidence."""
        self._evolution_evidence[evidence.id] = copy.deepcopy(evidence)
    
    # ==================== Evolution Rules ====================
    
    async def save_evolution_rule(self, rule: EvolutionRule) -> None:
        """Save an evolution rule."""
        self._evolution_rules[rule.id] = copy.deepcopy(rule)
    
    async def get_evolution_rules(self, active_only: bool = True) -> List[EvolutionRule]:
        """Get all evolution rules."""
        rules = []
        for rule in self._evolution_rules.values():
            if active_only and not rule.is_active:
                continue
            rules.append(copy.deepcopy(rule))
        return rules
    
    # ==================== Drift Monitoring ====================
    
    async def save_drift_schedule(self, schedule: Dict[str, Any]) -> None:
        """Save a drift monitoring schedule."""
        companion_id = schedule.get("companion_id")
        if companion_id:
            self._drift_schedules[companion_id] = copy.deepcopy(schedule)
    
    async def update_drift_schedule_next_run(self, companion_id: str) -> None:
        """Update next run time for drift schedule."""
        schedule = self._drift_schedules.get(companion_id)
        if schedule:
            interval = schedule.get("interval_hours", 24)
            schedule["next_run"] = (
                datetime.utcnow() + timedelta(hours=interval)
            ).isoformat()
    
    async def save_drift_monitoring_config(self, config: Dict[str, Any]) -> None:
        """Save drift monitoring configuration."""
        companion_id = config.get("companion_id")
        if companion_id:
            self._drift_monitoring_configs[companion_id] = copy.deepcopy(config)
    
    # ==================== Templates ====================
    
    async def save_template(self, template: Dict[str, Any]) -> None:
        """Save a custom template."""
        template_id = template.get("id")
        if template_id:
            self._templates[template_id] = copy.deepcopy(template)
    
    async def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a template by ID."""
        return copy.deepcopy(self._templates.get(template_id))
    
    async def list_templates(
        self,
        category: Optional[str] = None,
        companion_type: Optional[str] = None,
        is_active: bool = True,
    ) -> List[Dict[str, Any]]:
        """List custom templates with filters."""
        results = []
        for template in self._templates.values():
            if is_active and not template.get("is_active", True):
                continue
            if category and template.get("category") != category:
                continue
            if companion_type and template.get("companion_type") != companion_type:
                continue
            results.append(copy.deepcopy(template))
        return results
    
    async def delete_template(self, template_id: str) -> bool:
        """Delete a custom template."""
        if template_id in self._templates:
            del self._templates[template_id]
            return True
        return False
    
    async def get_template_categories(self) -> List[str]:
        """Get all custom template categories."""
        categories = set()
        for template in self._templates.values():
            if template.get("category"):
                categories.add(template["category"])
        return sorted(list(categories))
    
    # ==================== References ====================
    
    async def get_boundary_references(self, boundary_id: str) -> List[str]:
        """Get references to a boundary."""
        # In-memory implementation: check all identities
        refs = []
        for identity in self._identities.values():
            for boundary in identity.boundaries:
                if boundary.id == boundary_id:
                    refs.append(f"identity:{identity.id}")
        return refs
    
    async def get_goal_references(self, goal_id: str) -> List[str]:
        """Get references to a goal."""
        refs = []
        for identity in self._identities.values():
            for goal in identity.goals:
                if goal.id == goal_id:
                    refs.append(f"identity:{identity.id}")
        return refs