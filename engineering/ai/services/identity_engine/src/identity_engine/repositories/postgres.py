"""PostgreSQL repository implementation for Identity Engine (production)."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import asyncpg
import structlog

from .base import BaseRepository
from ..models import (
    IdentityConfig, IdentityVersion, FingerprintVector, FingerprintResult,
    DriftResult, DriftAlert, EvolutionProposal, EvolutionResult,
    EvolutionTrigger, EvolutionEvidence, EvolutionRule,
    IdentityStatus,
)

logger = structlog.get_logger(__name__)


class PostgresRepository(BaseRepository):
    """PostgreSQL repository for production use."""
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    @classmethod
    async def create(cls, dsn: str, min_size: int = 5, max_size: int = 20) -> "PostgresRepository":
        """Create a new PostgresRepository with connection pool."""
        pool = await asyncpg.create_pool(dsn, min_size=min_size, max_size=max_size)
        return cls(pool)
    
    async def close(self) -> None:
        """Close the connection pool."""
        await self.pool.close()
    
    # ==================== Identity ====================
    
    async def save(self, identity: IdentityConfig) -> None:
        """Save an identity configuration."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO identities (
                    id, companion_id, personality, values, voice, boundaries, goals,
                    version, name, description, status, source, template_id,
                    is_valid, validation_errors, validation_warnings,
                    parent_version_id, tags, metadata, created_by,
                    created_at, updated_at, activated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23)
                ON CONFLICT (id) DO UPDATE SET
                    personality = EXCLUDED.personality,
                    values = EXCLUDED.values,
                    voice = EXCLUDED.voice,
                    boundaries = EXCLUDED.boundaries,
                    goals = EXCLUDED.goals,
                    version = EXCLUDED.version,
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    status = EXCLUDED.status,
                    source = EXCLUDED.source,
                    template_id = EXCLUDED.template_id,
                    is_valid = EXCLUDED.is_valid,
                    validation_errors = EXCLUDED.validation_errors,
                    validation_warnings = EXCLUDED.validation_warnings,
                    parent_version_id = EXCLUDED.parent_version_id,
                    tags = EXCLUDED.tags,
                    metadata = EXCLUDED.metadata,
                    updated_at = EXCLUDED.updated_at,
                    activated_at = EXCLUDED.activated_at
                """,
                identity.id,
                identity.companion_id,
                json.dumps(identity.personality.model_dump()),
                json.dumps(identity.values.model_dump()),
                json.dumps(identity.voice.model_dump()),
                json.dumps([b.model_dump() for b in identity.boundaries]),
                json.dumps([g.model_dump() for g in identity.goals]),
                identity.version,
                identity.name,
                identity.description,
                identity.status.value,
                identity.source.value,
                identity.template_id,
                identity.is_valid,
                json.dumps(identity.validation_errors),
                json.dumps(identity.validation_warnings),
                identity.parent_version_id,
                json.dumps(identity.tags),
                json.dumps(identity.metadata),
                identity.created_by,
                identity.created_at,
                identity.updated_at,
                identity.activated_at,
            )
    
    async def get(self, identity_id: str) -> Optional[IdentityConfig]:
        """Get an identity by ID."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM identities WHERE id = $1", identity_id
            )
            if not row:
                return None
            return self._row_to_identity(row)
    
    async def get_active(self, companion_id: str) -> Optional[IdentityConfig]:
        """Get the active identity for a companion."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM identities 
                WHERE companion_id = $1 AND status = $2
                ORDER BY version DESC LIMIT 1
                """,
                companion_id, IdentityStatus.ACTIVE.value,
            )
            if not row:
                return None
            return self._row_to_identity(row)
    
    async def get_version(self, companion_id: str, version: int) -> Optional[IdentityConfig]:
        """Get a specific version of identity for a companion."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM identities WHERE companion_id = $1 AND version = $2",
                companion_id, version,
            )
            if not row:
                return None
            return self._row_to_identity(row)
    
    async def list(
        self,
        companion_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[IdentityConfig]:
        """List identities with optional filters."""
        async with self.pool.acquire() as conn:
            query = "SELECT * FROM identities WHERE 1=1"
            params = []
            param_idx = 1
            
            if companion_id:
                query += f" AND companion_id = ${param_idx}"
                params.append(companion_id)
                param_idx += 1
            
            if status:
                query += f" AND status = ${param_idx}"
                params.append(status)
                param_idx += 1
            
            query += f" ORDER BY created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
            params.extend([limit, offset])
            
            rows = await conn.fetch(query, *params)
            return [self._row_to_identity(row) for row in rows]
    
    async def deactivate_companion_identities(self, companion_id: str) -> None:
        """Deactivate all identities for a companion."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE identities 
                SET status = $1, updated_at = $2
                WHERE companion_id = $3 AND status = $4
                """,
                IdentityStatus.DEPRECATED.value,
                datetime.utcnow().isoformat(),
                companion_id,
                IdentityStatus.ACTIVE.value,
            )
    
    async def get_identities_by_companion(self, companion_id: str) -> List[IdentityConfig]:
        """Get all identities for a companion."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM identities WHERE companion_id = $1 ORDER BY version DESC",
                companion_id,
            )
            return [self._row_to_identity(row) for row in rows]
    
    # ==================== Identity Versions ====================
    
    async def save_version(self, version: IdentityVersion) -> None:
        """Save an identity version snapshot."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO identity_versions (
                    id, identity_id, companion_id, version, personality, values,
                    voice, boundaries, goals, change_type, change_summary,
                    changed_fields, changed_by, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                ON CONFLICT (id) DO NOTHING
                """,
                version.id,
                version.identity_id,
                version.companion_id,
                version.version,
                json.dumps(version.personality),
                json.dumps(version.values),
                json.dumps(version.voice),
                json.dumps(version.boundaries),
                json.dumps(version.goals),
                version.change_type,
                version.change_summary,
                json.dumps(version.changed_fields),
                version.changed_by,
                version.created_at,
            )
    
    async def get_version_history(self, companion_id: str) -> List[IdentityVersion]:
        """Get version history for a companion."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM identity_versions 
                WHERE companion_id = $1 
                ORDER BY version ASC
                """,
                companion_id,
            )
            return [self._row_to_version(row) for row in rows]
    
    # ==================== Fingerprints ====================
    
    async def save_fingerprint(self, fingerprint: FingerprintVector) -> None:
        """Save a fingerprint vector."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO fingerprints (
                    id, companion_id, identity_version, personality_vector,
                    values_vector, voice_vector, goals_vector, boundaries_vector,
                    combined_vector, vector_dimension, computed_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (id) DO NOTHING
                """,
                fingerprint.id,
                fingerprint.companion_id,
                fingerprint.identity_version,
                fingerprint.personality_vector,
                fingerprint.values_vector,
                fingerprint.voice_vector,
                fingerprint.goals_vector,
                fingerprint.boundaries_vector,
                fingerprint.combined_vector,
                fingerprint.vector_dimension,
                fingerprint.computed_at,
            )
    
    async def get_fingerprint(self, fingerprint_id: str) -> Optional[FingerprintVector]:
        """Get a fingerprint by ID."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM fingerprints WHERE id = $1", fingerprint_id
            )
            if not row:
                return None
            return self._row_to_fingerprint(row)
    
    async def get_fingerprint_by_version(
        self, companion_id: str, version: int
    ) -> Optional[FingerprintVector]:
        """Get fingerprint for a specific identity version."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM fingerprints 
                WHERE companion_id = $1 AND identity_version = $2
                """,
                companion_id, version,
            )
            if not row:
                return None
            return self._row_to_fingerprint(row)
    
    async def get_latest_fingerprint(self, companion_id: str) -> Optional[FingerprintVector]:
        """Get the latest fingerprint for a companion."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM fingerprints 
                WHERE companion_id = $1 
                ORDER BY identity_version DESC LIMIT 1
                """,
                companion_id,
            )
            if not row:
                return None
            return self._row_to_fingerprint(row)
    
    async def get_earliest_fingerprint(self, companion_id: str) -> Optional[FingerprintVector]:
        """Get the earliest fingerprint for a companion."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM fingerprints 
                WHERE companion_id = $1 
                ORDER BY identity_version ASC LIMIT 1
                """,
                companion_id,
            )
            if not row:
                return None
            return self._row_to_fingerprint(row)
    
    # ==================== Drift ====================
    
    async def save_drift_result(self, drift: DriftResult) -> None:
        """Save a drift detection result."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO drift_results (
                    id, companion_id, baseline_fingerprint_id, current_fingerprint_id,
                    overall_drift_score, severity, dimension_drifts, dimension_severities,
                    component_similarities, significant_changes, recommended_actions,
                    requires_review, requires_reevaluation, requires_rollback,
                    analysis_window_days, analyzed_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                ON CONFLICT (id) DO NOTHING
                """,
                drift.id,
                drift.companion_id,
                drift.baseline_fingerprint_id,
                drift.current_fingerprint_id,
                drift.overall_drift_score,
                drift.severity.value,
                json.dumps({k.value: v for k, v in drift.dimension_drifts.items()}),
                json.dumps({k.value: v.value for k, v in drift.dimension_severities.items()}),
                json.dumps(drift.component_similarities),
                json.dumps(drift.significant_changes),
                json.dumps(drift.recommended_actions),
                drift.requires_review,
                drift.requires_reevaluation,
                drift.requires_rollback,
                drift.analysis_window_days,
                drift.analyzed_at,
            )
    
    async def get_latest_drift(self, companion_id: str) -> Optional[DriftResult]:
        """Get the latest drift result for a companion."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM drift_results 
                WHERE companion_id = $1 
                ORDER BY analyzed_at DESC LIMIT 1
                """,
                companion_id,
            )
            if not row:
                return None
            return self._row_to_drift_result(row)
    
    async def get_drift_history(
        self, companion_id: str, days: int = 30
    ) -> List[DriftResult]:
        """Get drift history for a companion."""
        async with self.pool.acquire() as conn:
            cutoff = datetime.utcnow() - timedelta(days=days)
            rows = await conn.fetch(
                """
                SELECT * FROM drift_results 
                WHERE companion_id = $1 AND analyzed_at >= $2
                ORDER BY analyzed_at ASC
                """,
                companion_id, cutoff.isoformat(),
            )
            return [self._row_to_drift_result(row) for row in rows]
    
    async def get_companions_with_recent_drift(
        self, min_severity: str
    ) -> List[Dict[str, Any]]:
        """Get companions that have recent drift above threshold."""
        severity_order = {"none": 0, "minimal": 1, "moderate": 2, "significant": 3, "critical": 4}
        min_level = severity_order.get(min_severity, 2)
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT DISTINCT ON (companion_id) companion_id, *
                FROM drift_results
                WHERE severity IN (
                    SELECT unnest($1::text[])
                )
                ORDER BY companion_id, analyzed_at DESC
                """,
                [k for k, v in severity_order.items() if v >= min_level],
            )
            return [
                {
                    "companion_id": row["companion_id"],
                    "latest_drift": self._row_to_drift_result(row),
                }
                for row in rows
            ]
    
    # ==================== Drift Alerts ====================
    
    async def save_drift_alert(self, alert: DriftAlert) -> None:
        """Save a drift alert."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO drift_alerts (
                    id, companion_id, drift_result_id, severity, title, message,
                    dimensions_affected, status, acknowledged_at, acknowledged_by,
                    resolved_at, resolved_by, resolution_notes, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                ON CONFLICT (id) DO NOTHING
                """,
                alert.id,
                alert.companion_id,
                alert.drift_result_id,
                alert.severity.value,
                alert.title,
                alert.message,
                json.dumps([d.value for d in alert.dimensions_affected]),
                alert.status,
                alert.acknowledged_at,
                alert.acknowledged_by,
                alert.resolved_at,
                alert.resolved_by,
                alert.resolution_notes,
                alert.created_at,
            )
    
    async def get_active_drift_alerts(
        self, companion_id: Optional[str] = None, severity: Optional[str] = None
    ) -> List[DriftAlert]:
        """Get active drift alerts."""
        async with self.pool.acquire() as conn:
            query = "SELECT * FROM drift_alerts WHERE status = 'active'"
            params = []
            param_idx = 1
            
            if companion_id:
                query += f" AND companion_id = ${param_idx}"
                params.append(companion_id)
                param_idx += 1
            
            if severity:
                query += f" AND severity = ${param_idx}"
                params.append(severity)
                param_idx += 1
            
            query += " ORDER BY created_at DESC"
            
            rows = await conn.fetch(query, *params)
            return [self._row_to_drift_alert(row) for row in rows]
    
    async def acknowledge_drift_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge a drift alert."""
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE drift_alerts 
                SET status = 'acknowledged', acknowledged_at = $1, acknowledged_by = $2
                WHERE id = $3 AND status = 'active'
                """,
                datetime.utcnow().isoformat(), acknowledged_by, alert_id,
            )
            return result == "UPDATE 1"
    
    async def resolve_drift_alert(
        self, alert_id: str, resolved_by: str, notes: str
    ) -> bool:
        """Resolve a drift alert."""
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE drift_alerts 
                SET status = 'resolved', resolved_at = $1, resolved_by = $2, resolution_notes = $3
                WHERE id = $4 AND status IN ('active', 'acknowledged')
                """,
                datetime.utcnow().isoformat(), resolved_by, notes, alert_id,
            )
            return result == "UPDATE 1"
    
    # ==================== Evolution Proposals ====================
    
    async def save_evolution_proposal(self, proposal: EvolutionProposal) -> None:
        """Save an evolution proposal."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO evolution_proposals (
                    id, companion_id, identity_id, baseline_version, name, description,
                    trigger, changes, status, overall_impact_score, overall_risk_level,
                    required_approvals, approval_count, rejection_count, reviewer_ids,
                    review_notes, created_by, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
                ON CONFLICT (id) DO UPDATE SET
                    status = EXCLUDED.status,
                    approval_count = EXCLUDED.approval_count,
                    rejection_count = EXCLUDED.rejection_count,
                    review_notes = EXCLUDED.review_notes,
                    updated_at = EXCLUDED.updated_at
                """,
                proposal.id,
                proposal.companion_id,
                proposal.identity_id,
                proposal.baseline_version,
                proposal.name,
                proposal.description,
                json.dumps(proposal.trigger.model_dump()),
                json.dumps([c.model_dump() for c in proposal.changes]),
                proposal.status.value,
                proposal.overall_impact_score,
                proposal.overall_risk_level,
                proposal.required_approvals,
                proposal.approval_count,
                proposal.rejection_count,
                json.dumps(proposal.reviewer_ids),
                json.dumps(proposal.review_notes),
                proposal.created_by,
                proposal.created_at,
                proposal.updated_at,
            )
    
    async def get_evolution_proposal(self, proposal_id: str) -> Optional[EvolutionProposal]:
        """Get an evolution proposal by ID."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM evolution_proposals WHERE id = $1", proposal_id
            )
            if not row:
                return None
            return self._row_to_proposal(row)
    
    async def list_evolution_proposals(
        self,
        companion_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[EvolutionProposal]:
        """List evolution proposals with filters."""
        async with self.pool.acquire() as conn:
            query = "SELECT * FROM evolution_proposals WHERE 1=1"
            params = []
            param_idx = 1
            
            if companion_id:
                query += f" AND companion_id = ${param_idx}"
                params.append(companion_id)
                param_idx += 1
            
            if status:
                query += f" AND status = ${param_idx}"
                params.append(status)
                param_idx += 1
            
            query += f" ORDER BY created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
            params.extend([limit, offset])
            
            rows = await conn.fetch(query, *params)
            return [self._row_to_proposal(row) for row in rows]
    
    async def get_pending_evolution_proposals(self, companion_id: str) -> List[EvolutionProposal]:
        """Get pending proposals for a companion."""
        return await self.list_evolution_proposals(
            companion_id=companion_id, status="pending_review", limit=100
        )
    
    async def get_recent_proposals_by_rule(
        self, companion_id: str, rule_id: str, period_days: int
    ) -> List[EvolutionProposal]:
        """Get recent proposals created by a specific rule."""
        async with self.pool.acquire() as conn:
            cutoff = datetime.utcnow() - timedelta(days=period_days)
            rows = await conn.fetch(
                """
                SELECT * FROM evolution_proposals 
                WHERE companion_id = $1 
                AND trigger->'metadata'->>'rule_id' = $2
                AND created_at >= $3
                ORDER BY created_at DESC
                """,
                companion_id, rule_id, cutoff.isoformat(),
            )
            return [self._row_to_proposal(row) for row in rows]
    
    # ==================== Evolution Results ====================
    
    async def save_evolution_result(self, result: EvolutionResult) -> None:
        """Save an evolution implementation result."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO evolution_results (
                    id, proposal_id, companion_id, status, implemented_changes,
                    failed_changes, previous_version, new_version,
                    post_implementation_validation, validation_errors,
                    validation_warnings, post_implementation_drift,
                    rollback_reason, rollback_version,
                    implemented_at, implemented_by, duration_ms
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                ON CONFLICT (id) DO NOTHING
                """,
                result.id,
                result.proposal_id,
                result.companion_id,
                result.status,
                json.dumps(result.implemented_changes),
                json.dumps(result.failed_changes),
                result.previous_version,
                result.new_version,
                result.post_implementation_validation,
                json.dumps(result.validation_errors),
                json.dumps(result.validation_warnings),
                result.post_implementation_drift,
                result.rollback_reason,
                result.rollback_version,
                result.implemented_at,
                result.implemented_by,
                result.duration_ms,
            )
    
    async def get_evolution_result_by_proposal(
        self, proposal_id: str
    ) -> Optional[EvolutionResult]:
        """Get result for a proposal."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM evolution_results WHERE proposal_id = $1", proposal_id
            )
            if not row:
                return None
            return self._row_to_result(row)
    
    async def get_evolution_history(
        self, companion_id: str, limit: int = 50
    ) -> List[EvolutionResult]:
        """Get evolution history for a companion."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM evolution_results 
                WHERE companion_id = $1 
                ORDER BY implemented_at DESC LIMIT $2
                """,
                companion_id, limit,
            )
            return [self._row_to_result(row) for row in rows]
    
    # ==================== Evolution Evidence ====================
    
    async def save_evolution_evidence(self, evidence: EvolutionEvidence) -> None:
        """Save evolution evidence."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO evolution_evidence (
                    id, proposal_id, change_id, source, description, data,
                    strength, collected_at, collected_by
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (id) DO NOTHING
                """,
                evidence.id,
                evidence.proposal_id,
                evidence.change_id,
                evidence.source,
                evidence.description,
                json.dumps(evidence.data),
                evidence.strength,
                evidence.collected_at,
                evidence.collected_by,
            )
    
    # ==================== Evolution Rules ====================
    
    async def save_evolution_rule(self, rule: EvolutionRule) -> None:
        """Save an evolution rule."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO evolution_rules (
                    id, name, description, trigger_conditions, change_template,
                    is_active, requires_human_approval, max_proposals_per_period,
                    period_days, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    trigger_conditions = EXCLUDED.trigger_conditions,
                    change_template = EXCLUDED.change_template,
                    is_active = EXCLUDED.is_active,
                    requires_human_approval = EXCLUDED.requires_human_approval,
                    max_proposals_per_period = EXCLUDED.max_proposals_per_period,
                    period_days = EXCLUDED.period_days,
                    updated_at = EXCLUDED.updated_at
                """,
                rule.id,
                rule.name,
                rule.description,
                json.dumps(rule.trigger_conditions),
                json.dumps(rule.change_template),
                rule.is_active,
                rule.requires_human_approval,
                rule.max_proposals_per_period,
                rule.period_days,
                rule.created_at,
                rule.updated_at,
            )
    
    async def get_evolution_rules(self, active_only: bool = True) -> List[EvolutionRule]:
        """Get all evolution rules."""
        async with self.pool.acquire() as conn:
            query = "SELECT * FROM evolution_rules"
            if active_only:
                query += " WHERE is_active = true"
            query += " ORDER BY name"
            
            rows = await conn.fetch(query)
            return [self._row_to_rule(row) for row in rows]
    
    # ==================== Drift Monitoring ====================
    
    async def save_drift_schedule(self, schedule: Dict[str, Any]) -> None:
        """Save a drift monitoring schedule."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO drift_schedules (
                    id, companion_id, interval_hours, enabled, next_run, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (id) DO UPDATE SET
                    interval_hours = EXCLUDED.interval_hours,
                    enabled = EXCLUDED.enabled,
                    next_run = EXCLUDED.next_run
                """,
                schedule["id"],
                schedule["companion_id"],
                schedule["interval_hours"],
                schedule["enabled"],
                schedule["next_run"],
                schedule["created_at"],
            )
    
    async def update_drift_schedule_next_run(self, companion_id: str) -> None:
        """Update next run time for drift schedule."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE drift_schedules 
                SET next_run = $1
                WHERE companion_id = $2
                """,
                (datetime.utcnow() + timedelta(hours=24)).isoformat(),
                companion_id,
            )
    
    async def save_drift_monitoring_config(self, config: Dict[str, Any]) -> None:
        """Save drift monitoring configuration."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO drift_monitoring_configs (
                    companion_id, interval_hours, auto_evolution, trigger_severity, updated_at
                ) VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (companion_id) DO UPDATE SET
                    interval_hours = EXCLUDED.interval_hours,
                    auto_evolution = EXCLUDED.auto_evolution,
                    trigger_severity = EXCLUDED.trigger_severity,
                    updated_at = EXCLUDED.updated_at
                """,
                config["companion_id"],
                config["interval_hours"],
                config["auto_evolution"],
                config["trigger_severity"],
                config["updated_at"],
            )
    
    # ==================== Templates ====================
    
    async def save_template(self, template: Dict[str, Any]) -> None:
        """Save a custom template."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO custom_templates (
                    id, name, description, category, companion_type, personality,
                    values, voice, boundaries, goals, tags, is_active,
                    created_by, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    category = EXCLUDED.category,
                    companion_type = EXCLUDED.companion_type,
                    personality = EXCLUDED.personality,
                    values = EXCLUDED.values,
                    voice = EXCLUDED.voice,
                    boundaries = EXCLUDED.boundaries,
                    goals = EXCLUDED.goals,
                    tags = EXCLUDED.tags,
                    is_active = EXCLUDED.is_active,
                    updated_at = EXCLUDED.updated_at
                """,
                template["id"],
                template["name"],
                template["description"],
                template["category"],
                template["companion_type"],
                json.dumps(template["personality"]),
                json.dumps(template["values"]),
                json.dumps(template["voice"]),
                json.dumps(template["boundaries"]),
                json.dumps(template["goals"]),
                json.dumps(template["tags"]),
                template["is_active"],
                template["created_by"],
                template["created_at"],
                template["updated_at"],
            )
    
    async def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a template by ID."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM custom_templates WHERE id = $1", template_id
            )
            if not row:
                return None
            return self._row_to_template(row)
    
    async def list_templates(
        self,
        category: Optional[str] = None,
        companion_type: Optional[str] = None,
        is_active: bool = True,
    ) -> List[Dict[str, Any]]:
        """List custom templates with filters."""
        async with self.pool.acquire() as conn:
            query = "SELECT * FROM custom_templates WHERE is_active = $1"
            params = [is_active]
            param_idx = 2
            
            if category:
                query += f" AND category = ${param_idx}"
                params.append(category)
                param_idx += 1
            
            if companion_type:
                query += f" AND companion_type = ${param_idx}"
                params.append(companion_type)
                param_idx += 1
            
            query += " ORDER BY name"
            
            rows = await conn.fetch(query, *params)
            return [self._row_to_template(row) for row in rows]
    
    async def delete_template(self, template_id: str) -> bool:
        """Delete a custom template."""
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM custom_templates WHERE id = $1", template_id
            )
            return result == "DELETE 1"
    
    async def get_template_categories(self) -> List[str]:
        """Get all custom template categories."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT DISTINCT category FROM custom_templates WHERE is_active = true"
            )
            return [row["category"] for row in rows]
    
    # ==================== References ====================
    
    async def get_boundary_references(self, boundary_id: str) -> List[str]:
        """Get references to a boundary."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id FROM identities 
                WHERE boundaries @> $1
                """,
                json.dumps([{"id": boundary_id}]),
            )
            return [f"identity:{row['id']}" for row in rows]
    
    async def get_goal_references(self, goal_id: str) -> List[str]:
        """Get references to a goal."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id FROM identities 
                WHERE goals @> $1
                """,
                json.dumps([{"id": goal_id}]),
            )
            return [f"identity:{row['id']}" for row in rows]
    
    # ==================== Helper Methods ====================
    
    def _row_to_identity(self, row: asyncpg.Record) -> IdentityConfig:
        """Convert database row to IdentityConfig."""
        from ..models import (
            PersonalityConfig, ValuesConfig, VoiceProfile,
            Boundary, Goal,
        )
        
        return IdentityConfig(
            id=row["id"],
            companion_id=row["companion_id"],
            personality=PersonalityConfig(**row["personality"]),
            values=ValuesConfig(**row["values"]),
            voice=VoiceProfile(**row["voice"]),
            boundaries=[Boundary(**b) for b in row["boundaries"]],
            goals=[Goal(**g) for g in row["goals"]],
            version=row["version"],
            name=row["name"],
            description=row["description"],
            status=IdentityStatus(row["status"]),
            source=row["source"],
            template_id=row["template_id"],
            is_valid=row["is_valid"],
            validation_errors=row["validation_errors"],
            validation_warnings=row["validation_warnings"],
            parent_version_id=row["parent_version_id"],
            tags=row["tags"],
            metadata=row["metadata"],
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            activated_at=row["activated_at"],
        )
    
    def _row_to_version(self, row: asyncpg.Record) -> IdentityVersion:
        """Convert database row to IdentityVersion."""
        return IdentityVersion(
            id=row["id"],
            identity_id=row["identity_id"],
            companion_id=row["companion_id"],
            version=row["version"],
            personality=row["personality"],
            values=row["values"],
            voice=row["voice"],
            boundaries=row["boundaries"],
            goals=row["goals"],
            change_type=row["change_type"],
            change_summary=row["change_summary"],
            changed_fields=row["changed_fields"],
            changed_by=row["changed_by"],
            created_at=row["created_at"],
        )
    
    def _row_to_fingerprint(self, row: asyncpg.Record) -> FingerprintVector:
        """Convert database row to FingerprintVector."""
        return FingerprintVector(
            id=row["id"],
            companion_id=row["companion_id"],
            identity_version=row["identity_version"],
            personality_vector=row["personality_vector"],
            values_vector=row["values_vector"],
            voice_vector=row["voice_vector"],
            goals_vector=row["goals_vector"],
            boundaries_vector=row["boundaries_vector"],
            combined_vector=row["combined_vector"],
            vector_dimension=row["vector_dimension"],
            computed_at=row["computed_at"],
        )
    
    def _row_to_drift_result(self, row: asyncpg.Record) -> DriftResult:
        """Convert database row to DriftResult."""
        from ..models import DriftSeverity, DriftDimension
        
        return DriftResult(
            id=row["id"],
            companion_id=row["companion_id"],
            baseline_fingerprint_id=row["baseline_fingerprint_id"],
            current_fingerprint_id=row["current_fingerprint_id"],
            overall_drift_score=row["overall_drift_score"],
            severity=DriftSeverity(row["severity"]),
            dimension_drifts={
                DriftDimension(k): v for k, v in row["dimension_drifts"].items()
            },
            dimension_severities={
                DriftDimension(k): DriftSeverity(v) 
                for k, v in row["dimension_severities"].items()
            },
            component_similarities=row["component_similarities"],
            significant_changes=row["significant_changes"],
            recommended_actions=row["recommended_actions"],
            requires_review=row["requires_review"],
            requires_reevaluation=row["requires_reevaluation"],
            requires_rollback=row["requires_rollback"],
            analysis_window_days=row["analysis_window_days"],
            analyzed_at=row["analyzed_at"],
        )
    
    def _row_to_drift_alert(self, row: asyncpg.Record) -> DriftAlert:
        """Convert database row to DriftAlert."""
        from ..models import DriftSeverity, DriftDimension
        
        return DriftAlert(
            id=row["id"],
            companion_id=row["companion_id"],
            drift_result_id=row["drift_result_id"],
            severity=DriftSeverity(row["severity"]),
            title=row["title"],
            message=row["message"],
            dimensions_affected=[DriftDimension(d) for d in row["dimensions_affected"]],
            status=row["status"],
            acknowledged_at=row["acknowledged_at"],
            acknowledged_by=row["acknowledged_by"],
            resolved_at=row["resolved_at"],
            resolved_by=row["resolved_by"],
            resolution_notes=row["resolution_notes"],
            created_at=row["created_at"],
        )
    
    def _row_to_proposal(self, row: asyncpg.Record) -> EvolutionProposal:
        """Convert database row to EvolutionProposal."""
        from ..models import (
            EvolutionTrigger, EvolutionChange, EvolutionProposalStatus,
        )
        
        return EvolutionProposal(
            id=row["id"],
            companion_id=row["companion_id"],
            identity_id=row["identity_id"],
            baseline_version=row["baseline_version"],
            name=row["name"],
            description=row["description"],
            trigger=EvolutionTrigger(**row["trigger"]),
            changes=[EvolutionChange(**c) for c in row["changes"]],
            status=EvolutionProposalStatus(row["status"]),
            overall_impact_score=row["overall_impact_score"],
            overall_risk_level=row["overall_risk_level"],
            required_approvals=row["required_approvals"],
            approval_count=row["approval_count"],
            rejection_count=row["rejection_count"],
            reviewer_ids=row["reviewer_ids"],
            review_notes=row["review_notes"],
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
    
    def _row_to_result(self, row: asyncpg.Record) -> EvolutionResult:
        """Convert database row to EvolutionResult."""
        return EvolutionResult(
            id=row["id"],
            proposal_id=row["proposal_id"],
            companion_id=row["companion_id"],
            status=row["status"],
            implemented_changes=row["implemented_changes"],
            failed_changes=row["failed_changes"],
            previous_version=row["previous_version"],
            new_version=row["new_version"],
            post_implementation_validation=row["post_implementation_validation"],
            validation_errors=row["validation_errors"],
            validation_warnings=row["validation_warnings"],
            post_implementation_drift=row["post_implementation_drift"],
            rollback_reason=row["rollback_reason"],
            rollback_version=row["rollback_version"],
            implemented_at=row["implemented_at"],
            implemented_by=row["implemented_by"],
            duration_ms=row["duration_ms"],
        )
    
    def _row_to_rule(self, row: asyncpg.Record) -> EvolutionRule:
        """Convert database row to EvolutionRule."""
        return EvolutionRule(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            trigger_conditions=row["trigger_conditions"],
            change_template=row["change_template"],
            is_active=row["is_active"],
            requires_human_approval=row["requires_human_approval"],
            max_proposals_per_period=row["max_proposals_per_period"],
            period_days=row["period_days"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
    
    def _row_to_template(self, row: asyncpg.Record) -> Dict[str, Any]:
        """Convert database row to template dict."""
        return {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "category": row["category"],
            "companion_type": row["companion_type"],
            "personality": row["personality"],
            "values": row["values"],
            "voice": row["voice"],
            "boundaries": row["boundaries"],
            "goals": row["goals"],
            "tags": row["tags"],
            "is_active": row["is_active"],
            "created_by": row["created_by"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }