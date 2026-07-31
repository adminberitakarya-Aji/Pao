"""Fingerprint Service - Computes and manages identity fingerprints for drift detection."""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import uuid
import structlog
import numpy as np

from pao_shared.observability import setup_tracing, setup_metrics

from ..models import (
    IdentityConfig, FingerprintVector, FingerprintResult, DriftResult,
    DriftSeverity, DriftDimension, DriftAlert, FingerprintComparison,
    compute_drift_severity, compute_dimension_drift,
)

logger = structlog.get_logger(__name__)


class FingerprintService:
    """Service for computing identity fingerprints and detecting drift."""
    
    def __init__(self, repository=None, alert_service=None):
        self.repository = repository
        self.alert_service = alert_service
        self._tracer = setup_tracing("identity-engine", "fingerprint-service")
        self._meter = setup_metrics("identity-engine", "fingerprint-service")
        
        # Metrics
        self._fingerprint_computed = self._meter.create_counter(
            "fingerprint_computed_total", "Total fingerprints computed"
        )
        self._drift_detected = self._meter.create_counter(
            "drift_detected_total", "Total drift detections"
        )
        self._drift_severity = self._meter.create_histogram(
            "drift_severity_score", "Drift severity scores"
        )
        self._computation_duration = self._meter.create_histogram(
            "fingerprint_computation_duration_seconds", "Computation duration"
        )
    
    async def compute_fingerprint(self, identity: IdentityConfig) -> FingerprintResult:
        """Compute fingerprint for an identity."""
        with self._tracer.start_as_current_span("compute_fingerprint") as span:
            span.set_attribute("companion_id", identity.companion_id)
            span.set_attribute("identity_version", identity.version)
            
            start_time = datetime.utcnow()
            
            # Compute component vectors
            personality_vec = identity.personality.traits.to_vector()
            values_vec = identity.values.to_vector()
            voice_vec = identity.voice.to_vector()
            goals_vec = self._compute_goals_vector(identity.goals)
            boundaries_vec = self._compute_boundaries_vector(identity.boundaries)
            
            # Combined vector
            combined = np.concatenate([
                personality_vec, values_vec, voice_vec, goals_vec, boundaries_vec
            ])
            
            # Normalize
            norm = np.linalg.norm(combined)
            if norm > 0:
                combined = combined / norm
            
            # Create fingerprint
            fingerprint = FingerprintVector(
                id=f"fp_{identity.companion_id}_{uuid.uuid4().hex[:8]}",
                companion_id=identity.companion_id,
                identity_version=identity.version,
                personality_vector=personality_vec,
                values_vector=values_vec,
                voice_vector=voice_vec,
                goals_vector=goals_vec,
                boundaries_vector=boundaries_vec,
                combined_vector=combined.tolist(),
                vector_dimension=len(combined),
            )
            
            computation_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            result = FingerprintResult(
                fingerprint=fingerprint,
                computation_time_ms=computation_time,
                source_data={
                    "identity_id": identity.id,
                    "identity_version": identity.version,
                },
                quality_score=1.0,
            )
            
            # Save fingerprint
            if self.repository:
                await self.repository.save_fingerprint(fingerprint)
            
            self._fingerprint_computed.add(1, {"companion_id": identity.companion_id})
            self._computation_duration.record(computation_time / 1000)
            
            logger.info(
                "Fingerprint computed",
                fingerprint_id=fingerprint.id,
                companion_id=identity.companion_id,
                computation_time_ms=computation_time,
            )
            
            return result
    
    def _compute_goals_vector(self, goals: List) -> List[float]:
        """Compute combined vector for goals."""
        if not goals:
            return np.zeros(20).tolist()
        
        vectors = [np.array(g.to_vector()) for g in goals]
        avg = np.mean(vectors, axis=0)
        return avg.tolist()
    
    def _compute_boundaries_vector(self, boundaries: List) -> List[float]:
        """Compute combined vector for boundaries."""
        if not boundaries:
            return np.zeros(10).tolist()
        
        vec = np.zeros(10)
        vec[0] = len(boundaries) / 20.0
        vec[1] = sum(b.priority for b in boundaries) / (len(boundaries) * 100)
        
        scopes = [b.scope.value for b in boundaries]
        vec[2] = scopes.count("global") / len(boundaries)
        vec[3] = scopes.count("topic") / len(boundaries)
        
        tags = set()
        for b in boundaries:
            tags.update(b.tags)
        vec[4] = len(tags) / 20.0
        
        return vec.tolist()
    
    async def detect_drift(
        self,
        companion_id: str,
        baseline_version: Optional[int] = None,
        current_version: Optional[int] = None,
        analysis_window_days: int = 7,
    ) -> DriftResult:
        """Detect drift between baseline and current identity."""
        with self._tracer.start_as_current_span("detect_drift") as span:
            span.set_attribute("companion_id", companion_id)
            
            if not self.repository:
                raise ValueError("Repository not configured")
            
            # Get baseline fingerprint
            if baseline_version:
                baseline_fp = await self.repository.get_fingerprint_by_version(
                    companion_id, baseline_version
                )
            else:
                # Get earliest fingerprint
                baseline_fp = await self.repository.get_earliest_fingerprint(companion_id)
            
            if not baseline_fp:
                raise ValueError(f"No baseline fingerprint found for companion {companion_id}")
            
            # Get current fingerprint
            if current_version:
                current_fp = await self.repository.get_fingerprint_by_version(
                    companion_id, current_version
                )
            else:
                # Get latest fingerprint
                current_fp = await self.repository.get_latest_fingerprint(companion_id)
            
            if not current_fp:
                raise ValueError(f"No current fingerprint found for companion {companion_id}")
            
            # If same version, no drift
            if baseline_fp.identity_version == current_fp.identity_version:
                return DriftResult(
                    id=f"drift_{companion_id}_{uuid.uuid4().hex[:8]}",
                    companion_id=companion_id,
                    baseline_fingerprint_id=baseline_fp.id,
                    current_fingerprint_id=current_fp.id,
                    overall_drift_score=0.0,
                    severity=DriftSeverity.NONE,
                )
            
            # Compute drift
            drift_score = 1.0 - baseline_fp.cosine_similarity(current_fp)
            severity = compute_drift_severity(drift_score)
            
            # Per-dimension drift
            component_sims = baseline_fp.component_similarities(current_fp)
            dimension_drifts = {}
            dimension_severities = {}
            
            dim_mapping = {
                "personality": DriftDimension.PERSONALITY,
                "values": DriftDimension.VALUES,
                "voice": DriftDimension.VOICE,
                "goals": DriftDimension.GOALS,
                "boundaries": DriftDimension.BOUNDARIES,
            }
            
            for comp_name, similarity in component_sims.items():
                if comp_name in dim_mapping:
                    drift = 1.0 - similarity
                    dimension_drifts[dim_mapping[comp_name]] = drift
                    dimension_severities[dim_mapping[comp_name]] = compute_drift_severity(drift)
            
            # Identify significant changes
            significant_changes = []
            for dim, drift in dimension_drifts.items():
                if drift > 0.2:  # Threshold for significant
                    significant_changes.append({
                        "dimension": dim.value,
                        "drift_score": drift,
                        "severity": dimension_severities[dim].value,
                    })
            
            # Generate recommendations
            recommended_actions = self._generate_recommendations(
                dimension_drifts, dimension_severities, significant_changes
            )
            
            result = DriftResult(
                id=f"drift_{companion_id}_{uuid.uuid4().hex[:8]}",
                companion_id=companion_id,
                baseline_fingerprint_id=baseline_fp.id,
                current_fingerprint_id=current_fp.id,
                overall_drift_score=drift_score,
                severity=severity,
                dimension_drifts=dimension_drifts,
                dimension_severities=dimension_severities,
                component_similarities=component_sims,
                significant_changes=significant_changes,
                recommended_actions=recommended_actions,
                requires_review=severity in [DriftSeverity.MODERATE, DriftSeverity.SIGNIFICANT, DriftSeverity.CRITICAL],
                requires_reevaluation=severity in [DriftSeverity.SIGNIFICANT, DriftSeverity.CRITICAL],
                requires_rollback=severity == DriftSeverity.CRITICAL,
                analysis_window_days=analysis_window_days,
            )
            
            # Save drift result
            if self.repository:
                await self.repository.save_drift_result(result)
            
            # Create alerts if needed
            if severity in [DriftSeverity.SIGNIFICANT, DriftSeverity.CRITICAL]:
                await self._create_drift_alerts(result)
            
            self._drift_detected.add(1, {"companion_id": companion_id, "severity": severity.value})
            self._drift_severity.record(drift_score)
            
            logger.info(
                "Drift detected",
                companion_id=companion_id,
                drift_score=drift_score,
                severity=severity.value,
                top_dimensions=[d.value for d, _ in result.get_top_drifted_dimensions(3)],
            )
            
            return result
    
    def _generate_recommendations(
        self,
        dimension_drifts: Dict[DriftDimension, float],
        dimension_severities: Dict[DriftDimension, DriftSeverity],
        significant_changes: List[Dict],
    ) -> List[str]:
        """Generate recommendations based on drift analysis."""
        recommendations = []
        
        # Check each dimension
        if DriftDimension.PERSONALITY in dimension_drifts:
            drift = dimension_drifts[DriftDimension.PERSONALITY]
            if drift > 0.3:
                recommendations.append(
                    "Consider reviewing personality traits - significant drift detected. "
                    "Run personality consistency evaluation."
                )
            elif drift > 0.15:
                recommendations.append(
                    "Monitor personality drift. Schedule consistency check."
                )
        
        if DriftDimension.VOICE in dimension_drifts:
            drift = dimension_drifts[DriftDimension.VOICE]
            if drift > 0.25:
                recommendations.append(
                    "Voice profile has drifted. Review tone, formality, and linguistic patterns."
                )
        
        if DriftDimension.VALUES in dimension_drifts:
            drift = dimension_drifts[DriftDimension.VALUES]
            if drift > 0.2:
                recommendations.append(
                    "Values configuration has shifted. Verify alignment with companion purpose."
                )
        
        if DriftDimension.BOUNDARIES in dimension_drifts:
            drift = dimension_drifts[DriftDimension.BOUNDARIES]
            if drift > 0.2:
                recommendations.append(
                    "Boundary configuration changed. Review safety and compliance implications."
                )
        
        if DriftDimension.GOALS in dimension_drifts:
            drift = dimension_drifts[DriftDimension.GOALS]
            if drift > 0.15:
                recommendations.append(
                    "Goal structure modified. Validate goal alignment with user outcomes."
                )
        
        # Overall recommendations
        max_severity = max(dimension_severities.values()) if dimension_severities else DriftSeverity.NONE
        
        if max_severity == DriftSeverity.CRITICAL:
            recommendations.insert(0, "CRITICAL: Immediate review required. Consider rollback to baseline.")
        elif max_severity == DriftSeverity.SIGNIFICANT:
            recommendations.insert(0, "Significant drift detected. Schedule comprehensive identity review.")
        elif max_severity == DriftSeverity.MODERATE:
            recommendations.insert(0, "Moderate drift detected. Review and validate recent changes.")
        
        return recommendations
    
    async def _create_drift_alerts(self, drift_result: DriftResult):
        """Create alerts for significant drift."""
        if not self.alert_service:
            return
        
        for dim, severity in drift_result.dimension_severities.items():
            if severity in [DriftSeverity.SIGNIFICANT, DriftSeverity.CRITICAL]:
                alert = DriftAlert(
                    id=f"alert_{drift_result.companion_id}_{uuid.uuid4().hex[:8]}",
                    companion_id=drift_result.companion_id,
                    drift_result_id=drift_result.id,
                    severity=severity,
                    title=f"{severity.value.title()} Drift in {dim.value}",
                    message=f"Drift score: {drift_result.dimension_drifts[dim]:.2%}",
                    dimensions_affected=[dim],
                )
                await self.alert_service.create_alert(alert)
    
    async def compare_fingerprints(
        self,
        baseline_id: str,
        current_id: str,
        companion_id: str,
    ) -> FingerprintComparison:
        """Compare two fingerprints and generate detailed analysis."""
        with self._tracer.start_as_current_span("compare_fingerprints") as span:
            span.set_attribute("baseline_id", baseline_id)
            span.set_attribute("current_id", current_id)
            
            if not self.repository:
                raise ValueError("Repository not configured")
            
            baseline = await self.repository.get_fingerprint(baseline_id)
            current = await self.repository.get_fingerprint(current_id)
            
            if not baseline or not current:
                raise ValueError("Fingerprint not found")
            
            similarity = baseline.cosine_similarity(current)
            component_sims = baseline.component_similarities(current)
            
            # Determine drifted dimensions
            drifted_dims = []
            for comp_name, sim in component_sims.items():
                drift = 1.0 - sim
                if drift > 0.15:
                    dim_map = {
                        "personality": DriftDimension.PERSONALITY,
                        "values": DriftDimension.VALUES,
                        "voice": DriftDimension.VOICE,
                        "goals": DriftDimension.GOALS,
                        "boundaries": DriftDimension.BOUNDARIES,
                    }
                    if comp_name in dim_map:
                        drifted_dims.append(dim_map[comp_name])
            
            # Generate narrative
            narrative = self._generate_drift_narrative(component_sims, drifted_dims)
            
            # Risk assessment
            max_drift = max(1.0 - s for s in component_sims.values())
            if max_drift > 0.5:
                risk = "critical"
            elif max_drift > 0.3:
                risk = "high"
            elif max_drift > 0.15:
                risk = "medium"
            else:
                risk = "low"
            
            # Recommendations
            recommendations = []
            if risk in ["high", "critical"]:
                recommendations.append("Immediate review recommended")
            if risk == "critical":
                recommendations.append("Consider rollback to baseline")
            if DriftDimension.PERSONALITY in drifted_dims:
                recommendations.append("Run personality consistency evaluation")
            if DriftDimension.VOICE in drifted_dims:
                recommendations.append("Review voice profile alignment")
            
            return FingerprintComparison(
                baseline_id=baseline_id,
                current_id=current_id,
                companion_id=companion_id,
                overall_similarity=similarity,
                component_similarities=component_sims,
                drifted_dimensions=drifted_dims,
                significant_changes=[
                    {"dimension": d.value, "drift": 1.0 - component_sims.get(
                        {"personality": "personality", "values": "values", 
                         "voice": "voice", "goals": "goals", "boundaries": "boundaries"}.get(d.value, ""), 0)}
                    for d in drifted_dims
                ],
                drift_narrative=narrative,
                risk_assessment=risk,
                recommended_actions=recommendations,
            )
    
    def _generate_drift_narrative(
        self,
        component_sims: Dict[str, float],
        drifted_dims: List[DriftDimension],
    ) -> str:
        """Generate human-readable drift narrative."""
        if not drifted_dims:
            return "No significant drift detected. Identity remains stable."
        
        parts = ["Drift detected in: " + ", ".join(d.value for d in drifted_dims)]
        
        for dim in drifted_dims:
            dim_map = {
                DriftDimension.PERSONALITY: "personality",
                DriftDimension.VALUES: "values",
                DriftDimension.VOICE: "voice",
                DriftDimension.GOALS: "goals",
                DriftDimension.BOUNDARIES: "boundaries",
            }
            comp = dim_map.get(dim)
            if comp and comp in component_sims:
                drift = 1.0 - component_sims[comp]
                parts.append(f"{dim.value} drifted by {drift:.1%}")
        
        return ". ".join(parts)
    
    async def get_drift_history(
        self,
        companion_id: str,
        days: int = 30,
    ) -> List[DriftResult]:
        """Get drift detection history for a companion."""
        if not self.repository:
            return []
        return await self.repository.get_drift_history(companion_id, days)
    
    async def get_latest_drift(self, companion_id: str) -> Optional[DriftResult]:
        """Get the most recent drift result for a companion."""
        if not self.repository:
            return None
        return await self.repository.get_latest_drift(companion_id)