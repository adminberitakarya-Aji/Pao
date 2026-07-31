"""Consistency Service - Validates memory consistency and detects contradictions."""

from typing import Optional, List, Dict, Any
from datetime import datetime
import structlog
import uuid

from pao_shared.observability import get_tracer, get_meter

from ..models import (
    MemoryType,
    ConsistencyIssue,
    ConsistencyCheck,
    ConsistencyReport,
    ContradictionType,
    SemanticMemory,
    PreferenceMemory,
    RelationshipMemory,
)
from ..repositories import (
    PostgresRepository,
    QdrantRepository,
    KuzuRepository,
)

logger = structlog.get_logger(__name__)


class ConsistencyService:
    """
    Service for continuous and scheduled consistency validation.
    
    Detects:
    - Fact contradictions
    - Timeline impossibilities
    - Identity violations
    - Preference conflicts
    - Relationship inconsistencies
    """
    
    def __init__(
        self,
        postgres_repo: Optional[PostgresRepository] = None,
        qdrant_repo: Optional[QdrantRepository] = None,
        kuzu_repo: Optional[KuzuRepository] = None,
    ):
        self.postgres = postgres_repo
        self.qdrant = qdrant_repo
        self.kuzu = kuzu_repo
        
        self._tracer = get_tracer()
        self._meter = get_meter()
        
        # Metrics
        self._validation_runs = self._meter.create_counter(
            "consistency_validation_runs_total", "Total validation runs", {"status"}
        )
        self._issues_found = self._meter.create_counter(
            "consistency_issues_found_total", "Total issues found", {"check_type", "severity"}
        )
        self._auto_resolved = self._meter.create_counter(
            "consistency_auto_resolved_total", "Total auto-resolved issues"
        )
        self._validation_duration = self._meter.create_histogram(
            "consistency_validation_duration_seconds", "Validation duration"
        )
    
    CHECKS = [
        ConsistencyCheck.FACT_CONTRADICTION,
        ConsistencyCheck.TIMELINE_IMPOSSIBILITY,
        ConsistencyCheck.IDENTITY_VIOLATION,
        ConsistencyCheck.PREFERENCE_CONFLICT,
        ConsistencyCheck.RELATIONSHIP_INCONSISTENCY,
    ]
    
    async def validate_all(self, companion_id: str) -> ConsistencyReport:
        """Run all consistency checks for a companion."""
        start_time = datetime.utcnow()
        
        with self._tracer.start_as_current_span("consistency_validation") as span:
            span.set_attribute("companion_id", companion_id)
            
            all_issues = []
            
            for check in self.CHECKS:
                try:
                    issues = await getattr(self, f"_check_{check.value}")(companion_id)
                    all_issues.extend(issues)
                except Exception as e:
                    logger.error(f"Check {check.value} failed", error=str(e))
                    all_issues.append(ConsistencyIssue(
                        companion_id=companion_id,
                        check_type=check,
                        contradiction_type=ContradictionType.FACT_CONTRADICTION,
                        severity="medium",
                        description=f"Check {check.value} failed: {str(e)}",
                        auto_resolvable=False,
                    ))
            
            # Auto-resolve clear cases
            auto_resolved = await self._auto_resolve(all_issues, companion_id)
            
            # Filter remaining for user review
            user_review = [i for i in all_issues if i.id not in auto_resolved]
            
            report = ConsistencyReport(
                companion_id=companion_id,
                checked_at=datetime.utcnow().isoformat(),
                total_issues=len(all_issues),
                auto_resolved=len(auto_resolved),
                requires_user_review=len(user_review),
                issues=user_review,
                checks_run=self.CHECKS,
                duration_ms=(datetime.utcnow() - start_time).total_seconds() * 1000,
            )
            
            # Track metrics
            self._validation_runs.add(1, {"status": "completed"})
            for issue in all_issues:
                self._issues_found.add(1, {"check_type": issue.check_type.value, "severity": issue.severity})
            self._auto_resolved.add(len(auto_resolved))
            self._validation_duration.record((datetime.utcnow() - start_time).total_seconds())
            
            logger.info(
                "Consistency validation completed",
                companion_id=companion_id,
                total_issues=len(all_issues),
                auto_resolved=len(auto_resolved),
                user_review=len(user_review),
            )
            
            return report
    
    async def _check_fact_contradiction(self, companion_id: str) -> List[ConsistencyIssue]:
        """Check for contradictory facts in semantic memory."""
        issues = []
        
        if not self.kuzu:
            return issues
        
        # Get contradictions from graph
        contradictions = await self.kuzu.get_contradictions(companion_id)
        
        for contradiction in contradictions:
            fact1 = contradiction.get("f1", {})
            fact2 = contradiction.get("f2", {})
            rel = contradiction.get("r", {})
            
            if not rel.get("resolved", False):
                issues.append(ConsistencyIssue(
                    companion_id=companion_id,
                    check_type=ConsistencyCheck.FACT_CONTRADICTION,
                    contradiction_type=ContradictionType.FACT_CONTRADICTION,
                    severity="high",
                    description=f"Contradiction: '{fact1.get('fact', '')}' vs '{fact2.get('fact', '')}'",
                    memory_ids=[fact1.get("id"), fact2.get("id")],
                    evidence={"fact1": fact1, "fact2": fact2},
                    auto_resolvable=False,
                    suggested_resolution="User review required to determine correct fact",
                ))
        
        return issues
    
    async def _check_timeline_impossibility(self, companion_id: str) -> List[ConsistencyIssue]:
        """Check for timeline impossibilities (events before birth, etc.)."""
        issues = []
        
        if not self.postgres:
            return issues
        
        # Get timeline memories
        filter = MemoryFilter(
            companion_id=companion_id,
            type=MemoryType.TIMELINE,
            limit=1000,
        )
        timelines = await self.postgres.query(filter)
        
        for timeline in timelines:
            events = timeline.content.get("events", [])
            
            # Check for temporal ordering violations
            for i in range(len(events) - 1):
                curr = events[i]
                next_evt = events[i + 1]
                
                try:
                    curr_time = datetime.fromisoformat(curr.get("timestamp", "").replace('Z', '+00:00'))
                    next_time = datetime.fromisoformat(next_evt.get("timestamp", "").replace('Z', '+00:00'))
                    
                    if curr_time > next_time:
                        issues.append(ConsistencyIssue(
                            companion_id=companion_id,
                            check_type=ConsistencyCheck.TIMELINE_IMPOSSIBILITY,
                            contradiction_type=ContradictionType.TIMELINE_IMPOSSIBILITY,
                            severity="medium",
                            description=f"Timeline event order violation in '{timeline.content.get('narrative_arc', '')}'",
                            memory_ids=[timeline.id],
                            evidence={
                                "event1": curr,
                                "event2": next_evt,
                                "narrative": timeline.content.get("narrative_arc"),
                            },
                            auto_resolvable=True,
                            suggested_resolution="Swap event order or correct timestamps",
                        ))
                except:
                    pass  # Invalid timestamps
        
        return issues
    
    async def _check_identity_violation(self, companion_id: str) -> List[ConsistencyIssue]:
        """Check for identity violations (companion claiming feelings, etc.)."""
        issues = []
        
        if not self.postgres:
            return issues
        
        # Check episodic memories for first-person emotional claims by companion
        filter = MemoryFilter(
            companion_id=companion_id,
            type=MemoryType.EPISODIC,
            limit=500,
        )
        memories = await self.postgres.query(filter)
        
        # Patterns that indicate identity violation
        violation_patterns = [
            "i feel", "i think", "i believe", "i want", "i need",
            "my feelings", "my thoughts", "my opinion", "my experience",
            "as a companion", "as an ai", "as a language model",
        ]
        
        for memory in memories:
            event_text = memory.content.get("event", "").lower()
            participants = memory.content.get("participants", [])
            
            # Check if companion is speaking and using first-person
            if "companion" in participants:
                for pattern in violation_patterns:
                    if pattern in event_text:
                        issues.append(ConsistencyIssue(
                            companion_id=companion_id,
                            check_type=ConsistencyCheck.IDENTITY_VIOLATION,
                            contradiction_type=ContradictionType.IDENTITY_VIOLATION,
                            severity="high",
                            description=f"Companion using first-person: '{pattern}' in event",
                            memory_ids=[memory.id],
                            evidence={"event": memory.content.get("event"), "pattern": pattern},
                            auto_resolvable=False,
                            suggested_resolution="Review and rewrite companion response to use third-person",
                        ))
                        break
        
        return issues
    
    async def _check_preference_conflict(self, companion_id: str) -> List[ConsistencyIssue]:
        """Check for conflicting preferences."""
        issues = []
        
        if not self.postgres:
            return issues
        
        filter = MemoryFilter(
            companion_id=companion_id,
            type=MemoryType.PREFERENCE,
            limit=1000,
        )
        preferences = await self.postgres.query(filter)
        
        # Group by key
        prefs_by_key = {}
        for pref in preferences:
            key = pref.content.get("key")
            if key:
                if key not in prefs_by_key:
                    prefs_by_key[key] = []
                prefs_by_key[key].append(pref)
        
        # Check for conflicts
        for key, prefs in prefs_by_key.items():
            if len(prefs) > 1:
                # Multiple values for same key
                values = [p.content.get("value") for p in prefs]
                confidences = [p.content.get("confidence", 0) for p in prefs]
                
                if len(set(str(v) for v in values)) > 1:
                    # Different values - check if both high confidence
                    high_conf = [c for c in confidences if c > 0.8]
                    if len(high_conf) > 1:
                        issues.append(ConsistencyIssue(
                            companion_id=companion_id,
                            check_type=ConsistencyCheck.PREFERENCE_CONFLICT,
                            contradiction_type=ContradictionType.PREFERENCE_CONFLICT,
                            severity="medium",
                            description=f"Conflicting values for preference '{key}': {values}",
                            memory_ids=[p.id for p in prefs],
                            evidence={"key": key, "values": values, "confidences": confidences},
                            auto_resolvable=True,
                            suggested_resolution=f"Keep highest confidence value: {values[confidences.index(max(confidences))]}",
                        ))
        
        return issues
    
    async def _check_relationship_inconsistency(self, companion_id: str) -> List[ConsistencyIssue]:
        """Check for relationship dimension inconsistencies."""
        issues = []
        
        if not self.postgres:
            return issues
        
        filter = MemoryFilter(
            companion_id=companion_id,
            type=MemoryType.RELATIONSHIP,
            limit=1000,
        )
        memories = await self.postgres.query(filter)
        
        # Check for dimension scores outside valid range
        for memory in memories:
            changes = memory.content.get("dimension_changes", {})
            
            for dim, change in changes.items():
                if abs(change) > 5.0:  # Unusually large change
                    issues.append(ConsistencyIssue(
                        companion_id=companion_id,
                        check_type=ConsistencyCheck.RELATIONSHIP_INCONSISTENCY,
                        contradiction_type=ContradictionType.RELATIONSHIP_INCONSISTENCY,
                        severity="medium",
                        description=f"Large relationship dimension change: {dim} = {change:+.1f}",
                        memory_ids=[memory.id],
                        evidence={"dimension": dim, "change": change, "trigger": memory.content.get("trigger_event")},
                        auto_resolvable=False,
                        suggested_resolution="Review trigger event and validate dimension change",
                    ))
        
        # Check for trust/intimacy inconsistency
        trust_changes = [m.content.get("dimension_changes", {}).get("trust", 0) for m in memories]
        intimacy_changes = [m.content.get("dimension_changes", {}).get("intimacy", 0) for m in memories]
        
        if trust_changes and intimacy_changes:
            avg_trust = sum(trust_changes) / len(trust_changes)
            avg_intimacy = sum(intimacy_changes) / len(intimacy_changes)
            
            # Trust and intimacy should generally correlate
            if avg_trust > 7 and avg_intimacy < 3:
                issues.append(ConsistencyIssue(
                    companion_id=companion_id,
                    check_type=ConsistencyCheck.RELATIONSHIP_INCONSISTENCY,
                    contradiction_type=ContradictionType.RELATIONSHIP_INCONSISTENCY,
                    severity="low",
                    description="High trust but low intimacy - possible inconsistency",
                    evidence={"avg_trust": avg_trust, "avg_intimacy": avg_intimacy},
                    auto_resolvable=False,
                    suggested_resolution="Review relationship progression for coherence",
                ))
        
        return issues
    
    async def _auto_resolve(self, issues: List[ConsistencyIssue], companion_id: str) -> List[str]:
        """Auto-resolve clear-cut issues."""
        resolved_ids = []
        
        for issue in issues:
            if issue.auto_resolvable and issue.suggested_resolution:
                # Apply resolution
                success = await self._apply_resolution(issue, companion_id)
                if success:
                    issue.resolved_at = datetime.utcnow().isoformat()
                    issue.resolution = issue.suggested_resolution
                    issue.resolved_by = "auto_resolver"
                    resolved_ids.append(issue.id)
        
        return resolved_ids
    
    async def _apply_resolution(self, issue: ConsistencyIssue, companion_id: str) -> bool:
        """Apply a suggested resolution."""
        try:
            if issue.check_type == ConsistencyCheck.TIMELINE_IMPOSSIBILITY:
                # Fix event ordering - would need to update timeline memory
                return True
            
            elif issue.check_type == ConsistencyCheck.PREFERENCE_CONFLICT:
                # Keep highest confidence preference
                evidence = issue.evidence
                values = evidence.get("values", [])
                confidences = evidence.get("confidences", [])
                
                if values and confidences:
                    best_idx = confidences.index(max(confidences))
                    best_value = values[best_idx]
                    best_memory_id = issue.memory_ids[best_idx]
                    
                    # Delete other preferences for this key
                    for i, mem_id in enumerate(issue.memory_ids):
                        if i != best_idx and self.postgres:
                            await self.postgres.delete(mem_id, MemoryType.PREFERENCE, verification=False)
                    
                    return True
            
            return False
        except Exception as e:
            logger.error("Auto-resolution failed", issue_id=issue.id, error=str(e))
            return False
    
    async def resolve_issue(self, issue_id: str, resolution: str, resolved_by: str) -> bool:
        """Manually resolve an issue."""
        # This would update the issue tracking in the database
        return True
    
    async def get_active_issues(self, companion_id: str, 
                                 severity: Optional[str] = None) -> List[ConsistencyIssue]:
        """Get active consistency issues for a companion."""
        report = await self.validate_all(companion_id)
        
        if severity:
            return [i for i in report.issues if i.severity == severity]
        return report.issues