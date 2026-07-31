"""Base repository interface for Identity Engine."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..models import (
    IdentityConfig, IdentityVersion, FingerprintVector, FingerprintResult,
    DriftResult, DriftAlert, EvolutionProposal, EvolutionResult,
    EvolutionTrigger, EvolutionEvidence, EvolutionRule,
)


class BaseRepository(ABC):
    """Abstract base repository for Identity Engine data persistence."""
    
    # ==================== Identity ====================
    
    @abstractmethod
    async def save(self, identity: IdentityConfig) -> None:
        """Save an identity configuration."""
        pass
    
    @abstractmethod
    async def get(self, identity_id: str) -> Optional[IdentityConfig]:
        """Get an identity by ID."""
        pass
    
    @abstractmethod
    async def get_active(self, companion_id: str) -> Optional[IdentityConfig]:
        """Get the active identity for a companion."""
        pass
    
    @abstractmethod
    async def get_version(self, companion_id: str, version: int) -> Optional[IdentityConfig]:
        """Get a specific version of identity for a companion."""
        pass
    
    @abstractmethod
    async def list(
        self,
        companion_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[IdentityConfig]:
        """List identities with optional filters."""
        pass
    
    @abstractmethod
    async def deactivate_companion_identities(self, companion_id: str) -> None:
        """Deactivate all identities for a companion."""
        pass
    
    @abstractmethod
    async def get_identities_by_companion(self, companion_id: str) -> List[IdentityConfig]:
        """Get all identities for a companion."""
        pass
    
    # ==================== Identity Versions ====================
    
    @abstractmethod
    async def save_version(self, version: IdentityVersion) -> None:
        """Save an identity version snapshot."""
        pass
    
    @abstractmethod
    async def get_version_history(self, companion_id: str) -> List[IdentityVersion]:
        """Get version history for a companion."""
        pass
    
    # ==================== Fingerprints ====================
    
    @abstractmethod
    async def save_fingerprint(self, fingerprint: FingerprintVector) -> None:
        """Save a fingerprint vector."""
        pass
    
    @abstractmethod
    async def get_fingerprint(self, fingerprint_id: str) -> Optional[FingerprintVector]:
        """Get a fingerprint by ID."""
        pass
    
    @abstractmethod
    async def get_fingerprint_by_version(
        self, companion_id: str, version: int
    ) -> Optional[FingerprintVector]:
        """Get fingerprint for a specific identity version."""
        pass
    
    @abstractmethod
    async def get_latest_fingerprint(self, companion_id: str) -> Optional[FingerprintVector]:
        """Get the latest fingerprint for a companion."""
        pass
    
    @abstractmethod
    async def get_earliest_fingerprint(self, companion_id: str) -> Optional[FingerprintVector]:
        """Get the earliest fingerprint for a companion."""
        pass
    
    # ==================== Drift ====================
    
    @abstractmethod
    async def save_drift_result(self, drift: DriftResult) -> None:
        """Save a drift detection result."""
        pass
    
    @abstractmethod
    async def get_latest_drift(self, companion_id: str) -> Optional[DriftResult]:
        """Get the latest drift result for a companion."""
        pass
    
    @abstractmethod
    async def get_drift_history(
        self, companion_id: str, days: int = 30
    ) -> List[DriftResult]:
        """Get drift history for a companion."""
        pass
    
    @abstractmethod
    async def get_companions_with_recent_drift(
        self, min_severity: str
    ) -> List[Dict[str, Any]]:
        """Get companions that have recent drift above threshold."""
        pass
    
    # ==================== Drift Alerts ====================
    
    @abstractmethod
    async def save_drift_alert(self, alert: DriftAlert) -> None:
        """Save a drift alert."""
        pass
    
    @abstractmethod
    async def get_active_drift_alerts(
        self, companion_id: Optional[str] = None, severity: Optional[str] = None
    ) -> List[DriftAlert]:
        """Get active drift alerts."""
        pass
    
    @abstractmethod
    async def acknowledge_drift_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge a drift alert."""
        pass
    
    @abstractmethod
    async def resolve_drift_alert(
        self, alert_id: str, resolved_by: str, notes: str
    ) -> bool:
        """Resolve a drift alert."""
        pass
    
    # ==================== Evolution Proposals ====================
    
    @abstractmethod
    async def save_evolution_proposal(self, proposal: EvolutionProposal) -> None:
        """Save an evolution proposal."""
        pass
    
    @abstractmethod
    async def get_evolution_proposal(self, proposal_id: str) -> Optional[EvolutionProposal]:
        """Get an evolution proposal by ID."""
        pass
    
    @abstractmethod
    async def list_evolution_proposals(
        self,
        companion_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[EvolutionProposal]:
        """List evolution proposals with filters."""
        pass
    
    @abstractmethod
    async def get_pending_evolution_proposals(self, companion_id: str) -> List[EvolutionProposal]:
        """Get pending proposals for a companion."""
        pass
    
    @abstractmethod
    async def get_recent_proposals_by_rule(
        self, companion_id: str, rule_id: str, period_days: int
    ) -> List[EvolutionProposal]:
        """Get recent proposals created by a specific rule."""
        pass
    
    # ==================== Evolution Results ====================
    
    @abstractmethod
    async def save_evolution_result(self, result: EvolutionResult) -> None:
        """Save an evolution implementation result."""
        pass
    
    @abstractmethod
    async def get_evolution_result_by_proposal(
        self, proposal_id: str
    ) -> Optional[EvolutionResult]:
        """Get result for a proposal."""
        pass
    
    @abstractmethod
    async def get_evolution_history(
        self, companion_id: str, limit: int = 50
    ) -> List[EvolutionResult]:
        """Get evolution history for a companion."""
        pass
    
    # ==================== Evolution Evidence ====================
    
    @abstractmethod
    async def save_evolution_evidence(self, evidence: EvolutionEvidence) -> None:
        """Save evolution evidence."""
        pass
    
    # ==================== Evolution Rules ====================
    
    @abstractmethod
    async def save_evolution_rule(self, rule: EvolutionRule) -> None:
        """Save an evolution rule."""
        pass
    
    @abstractmethod
    async def get_evolution_rules(self, active_only: bool = True) -> List[EvolutionRule]:
        """Get all evolution rules."""
        pass
    
    # ==================== Drift Monitoring ====================
    
    @abstractmethod
    async def save_drift_schedule(self, schedule: Dict[str, Any]) -> None:
        """Save a drift monitoring schedule."""
        pass
    
    @abstractmethod
    async def update_drift_schedule_next_run(self, companion_id: str) -> None:
        """Update next run time for drift schedule."""
        pass
    
    @abstractmethod
    async def save_drift_monitoring_config(self, config: Dict[str, Any]) -> None:
        """Save drift monitoring configuration."""
        pass
    
    # ==================== Templates ====================
    
    @abstractmethod
    async def save_template(self, template: Dict[str, Any]) -> None:
        """Save a custom template."""
        pass
    
    @abstractmethod
    async def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a template by ID."""
        pass
    
    @abstractmethod
    async def list_templates(
        self,
        category: Optional[str] = None,
        companion_type: Optional[str] = None,
        is_active: bool = True,
    ) -> List[Dict[str, Any]]:
        """List custom templates with filters."""
        pass
    
    @abstractmethod
    async def delete_template(self, template_id: str) -> bool:
        """Delete a custom template."""
        pass
    
    @abstractmethod
    async def get_template_categories(self) -> List[str]:
        """Get all custom template categories."""
        pass
    
    # ==================== References ====================
    
    @abstractmethod
    async def get_boundary_references(self, boundary_id: str) -> List[str]:
        """Get references to a boundary."""
        pass
    
    @abstractmethod
    async def get_goal_references(self, goal_id: str) -> List[str]:
        """Get references to a goal."""
        pass