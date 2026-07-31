"""Validation Service - Validates identity configurations and changes."""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import uuid
import structlog

from pao_shared.observability import setup_tracing, setup_metrics

from ..models import (
    IdentityConfig, PersonalityConfig, ValuesConfig, VoiceProfile,
    Boundary, Goal, EvolutionChange, EvolutionChangeType,
    BoundaryScope, GoalStatus, DriftSeverity,
)

logger = structlog.get_logger(__name__)


class ValidationService:
    """Service for validating identity configurations."""
    
    def __init__(self, repository=None):
        self.repository = repository
        self._tracer = setup_tracing("identity-engine", "validation-service")
        self._meter = setup_metrics("identity-engine", "validation-service")
        
        # Metrics
        self._validations_run = self._meter.create_counter(
            "validations_run_total", "Total validations run"
        )
        self._validations_passed = self._meter.create_counter(
            "validations_passed_total", "Total validations passed"
        )
        self._validations_failed = self._meter.create_counter(
            "validations_failed_total", "Total validations failed"
        )
        self._validation_duration = self._meter.create_histogram(
            "validation_duration_seconds", "Validation duration"
        )
    
    async def validate_identity(self, identity: IdentityConfig) -> Tuple[bool, List[str], List[str]]:
        """Validate a complete identity configuration."""
        with self._tracer.start_as_current_span("validate_identity") as span:
            span.set_attribute("identity_id", identity.id)
            span.set_attribute("companion_id", identity.companion_id)
            
            start_time = datetime.utcnow()
            
            all_errors = []
            all_warnings = []
            
            # Run all validation checks
            errors, warnings = await self._validate_personality(identity.personality)
            all_errors.extend(errors)
            all_warnings.extend(warnings)
            
            errors, warnings = await self._validate_values(identity.values)
            all_errors.extend(errors)
            all_warnings.extend(warnings)
            
            errors, warnings = await self._validate_voice(identity.voice)
            all_errors.extend(errors)
            all_warnings.extend(warnings)
            
            errors, warnings = await self._validate_boundaries(identity.boundaries)
            all_errors.extend(errors)
            all_warnings.extend(warnings)
            
            errors, warnings = await self._validate_goals(identity.goals)
            all_errors.extend(errors)
            all_warnings.extend(warnings)
            
            # Cross-component validation
            errors, warnings = await self._validate_cross_component(identity)
            all_errors.extend(errors)
            all_warnings.extend(warnings)
            
            # Uniqueness checks
            errors, warnings = await self._validate_uniqueness(identity)
            all_errors.extend(errors)
            all_warnings.extend(warnings)
            
            is_valid = len(all_errors) == 0
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            self._validations_run.add(1, {"companion_id": identity.companion_id})
            if is_valid:
                self._validations_passed.add(1, {"companion_id": identity.companion_id})
            else:
                self._validations_failed.add(1, {"companion_id": identity.companion_id})
            self._validation_duration.record(duration)
            
            logger.info(
                "Identity validation completed",
                identity_id=identity.id,
                is_valid=is_valid,
                errors=len(all_errors),
                warnings=len(all_warnings),
                duration_seconds=duration,
            )
            
            return is_valid, all_errors, all_warnings
    
    async def validate_change(self, change: EvolutionChange) -> Tuple[bool, Optional[str]]:
        """Validate a single evolution change."""
        with self._tracer.start_as_current_span("validate_change") as span:
            span.set_attribute("change_id", change.id)
            span.set_attribute("change_type", change.type.value)
            
            errors = []
            
            # Validate based on change type
            if change.type == EvolutionChangeType.PERSONALITY_ADJUSTMENT:
                errors = await self._validate_personality_change(change)
            elif change.type == EvolutionChangeType.VOICE_MODIFICATION:
                errors = await self._validate_voice_change(change)
            elif change.type == EvolutionChangeType.VALUES_UPDATE:
                errors = await self._validate_values_change(change)
            elif change.type in [
                EvolutionChangeType.BOUNDARY_ADDITION,
                EvolutionChangeType.BOUNDARY_MODIFICATION,
                EvolutionChangeType.BOUNDARY_REMOVAL,
            ]:
                errors = await self._validate_boundary_change(change)
            elif change.type in [
                EvolutionChangeType.GOAL_ADDITION,
                EvolutionChangeType.GOAL_MODIFICATION,
                EvolutionChangeType.GOAL_REMOVAL,
            ]:
                errors = await self._validate_goal_change(change)
            
            is_valid = len(errors) == 0
            notes = "; ".join(errors) if errors else None
            
            return is_valid, notes
    
    async def _validate_personality(self, personality: PersonalityConfig) -> Tuple[List[str], List[str]]:
        """Validate personality configuration."""
        errors = []
        warnings = []
        
        traits = personality.traits
        
        # Check trait ranges
        for field_name, value in traits.model_dump().items():
            if field_name == "custom_traits":
                continue
            if not isinstance(value, (int, float)):
                continue
            if value < 0.0 or value > 1.0:
                errors.append(f"Personality trait '{field_name}' must be between 0 and 1, got {value}")
        
        # Check for extreme combinations
        if traits.neuroticism > 0.8 and traits.agreeableness > 0.8:
            warnings.append("High neuroticism with high agreeableness may create internal conflict")
        
        if traits.openness < 0.2 and traits.conscientiousness > 0.8:
            warnings.append("Low openness with high conscientiousness may limit adaptability")
        
        # Validate companion type alignment
        if personality.companion_type:
            expected = self._get_expected_traits_for_type(personality.companion_type)
            for trait, expected_range in expected.items():
                actual = getattr(traits, trait)
                if not (expected_range[0] <= actual <= expected_range[1]):
                    warnings.append(
                        f"Trait '{trait}' ({actual:.2f}) outside expected range "
                        f"for {personality.companion_type.value}: {expected_range}"
                    )
        
        return errors, warnings
    
    def _get_expected_traits_for_type(self, companion_type) -> Dict[str, Tuple[float, float]]:
        """Get expected trait ranges for companion type."""
        from ..models import CompanionType
        
        expectations = {
            CompanionType.ASSISTANT: {
                "agreeableness": (0.5, 1.0),
                "conscientiousness": (0.6, 1.0),
                "neuroticism": (0.0, 0.4),
            },
            CompanionType.COACH: {
                "extraversion": (0.4, 0.8),
                "agreeableness": (0.6, 1.0),
                "openness": (0.5, 1.0),
            },
            CompanionType.CREATIVE_PARTNER: {
                "openness": (0.7, 1.0),
                "extraversion": (0.4, 0.9),
                "playfulness": (0.5, 1.0),
            },
            CompanionType.LEARNING_COMPANION: {
                "agreeableness": (0.6, 1.0),
                "openness": (0.5, 1.0),
                "conscientiousness": (0.5, 1.0),
                "patience": (0.6, 1.0),
            },
        }
        
        return expectations.get(companion_type, {})
    
    async def _validate_values(self, values: ValuesConfig) -> Tuple[List[str], List[str]]:
        """Validate values configuration."""
        errors = []
        warnings = []
        
        if not values.values:
            warnings.append("No values defined")
            return errors, warnings
        
        # Check for core values
        core_values = values.get_core_values()
        if not core_values:
            warnings.append("No core values defined (priority=critical)")
        
        # Check for conflicting values
        value_names = [v.name.lower() for v in values.values]
        
        conflicts = [
            ("honesty", "deception"),
            ("transparency", "secrecy"),
            ("autonomy", "control"),
            ("growth", "stagnation"),
            ("compassion", "indifference"),
        ]
        
        for v1, v2 in conflicts:
            if v1 in value_names and v2 in value_names:
                errors.append(f"Conflicting values detected: '{v1}' and '{v2}'")
        
        # Check priority distribution
        priorities = [v.priority for v in values.values]
        if priorities.count("critical") > 5:
            warnings.append("More than 5 critical-priority values may dilute focus")
        
        # Check for circular dependencies in value hierarchy
        # (would need more complex logic)
        
        return errors, warnings
    
    async def _validate_voice(self, voice: VoiceProfile) -> Tuple[List[str], List[str]]:
        """Validate voice profile."""
        errors = []
        warnings = []
        
        # Check required fields
        if not voice.id:
            errors.append("Voice profile missing ID")
        if not voice.companion_id:
            errors.append("Voice profile missing companion_id")
        
        # Check linguistic consistency
        if voice.uses_humor and not voice.humor_style:
            warnings.append("Humor enabled but no humor style specified")
        
        if voice.formality.value in ["very_formal", "formal"] and voice.uses_contractions:
            warnings.append("Formal voice with contractions may feel inconsistent")
        
        if voice.verbosity.value == "concise" and voice.gives_step_by_step:
            warnings.append("Concise verbosity with step-by-step instructions may conflict")
        
        # Check response length constraints
        if voice.max_response_length and voice.min_response_length:
            if voice.max_response_length < voice.min_response_length:
                errors.append("max_response_length must be >= min_response_length")
        
        return errors, warnings
    
    async def _validate_boundaries(self, boundaries: List[Boundary]) -> Tuple[List[str], List[str]]:
        """Validate boundaries."""
        errors = []
        warnings = []
        
        if not boundaries:
            warnings.append("No boundaries defined - consider adding safety boundaries")
            return errors, warnings
        
        # Check for duplicate IDs
        ids = [b.id for b in boundaries]
        if len(ids) != len(set(ids)):
            errors.append("Duplicate boundary IDs found")
        
        # Check each boundary
        for boundary in boundaries:
            b_errors, b_warnings = await self._validate_single_boundary(boundary)
            errors.extend(b_errors)
            warnings.extend(b_warnings)
        
        # Check for conflicting boundaries
        global_boundaries = [b for b in boundaries if b.scope == BoundaryScope.GLOBAL]
        if len(global_boundaries) > 10:
            warnings.append("Many global boundaries - consider consolidating")
        
        # Check priority distribution
        priorities = [b.priority for b in boundaries]
        if max(priorities) - min(priorities) < 10:
            warnings.append("Narrow priority range - consider wider spread for precedence")
        
        return errors, warnings
    
    async def _validate_single_boundary(self, boundary: Boundary) -> Tuple[List[str], List[str]]:
        """Validate a single boundary."""
        errors = []
        warnings = []
        
        # Must have triggers and actions
        if not boundary.triggers:
            errors.append(f"Boundary '{boundary.id}' has no triggers")
        
        if not boundary.actions:
            errors.append(f"Boundary '{boundary.id}' has no actions")
        
        # Validate triggers
        for trigger in boundary.triggers:
            if trigger.type.value == "pattern" and not trigger.pattern:
                errors.append(f"Pattern trigger '{trigger.id}' missing pattern")
            elif trigger.type.value == "keyword" and not trigger.keywords:
                errors.append(f"Keyword trigger '{trigger.id}' missing keywords")
            elif trigger.type.value == "semantic" and not trigger.semantic_threshold:
                errors.append(f"Semantic trigger '{trigger.id}' missing threshold")
        
        # Validate actions
        for action in boundary.actions:
            if action.type.value == "refuse" and not action.refusal_message:
                warnings.append(f"Refuse action '{action.id}' has no refusal message")
            elif action.type.value == "redirect" and not action.redirect_topic:
                warnings.append(f"Redirect action '{action.id}' has no redirect topic")
        
        return errors, warnings
    
    async def _validate_goals(self, goals: List[Goal]) -> Tuple[List[str], List[str]]:
        """Validate goals."""
        errors = []
        warnings = []
        
        if not goals:
            warnings.append("No goals defined")
            return errors, warnings
        
        # Check for duplicate IDs
        ids = [g.id for g in goals]
        if len(ids) != len(set(ids)):
            errors.append("Duplicate goal IDs found")
        
        # Check each goal
        for goal in goals:
            g_errors, g_warnings = await self._validate_single_goal(goal)
            errors.extend(g_errors)
            warnings.extend(g_warnings)
        
        # Check for goal hierarchy cycles
        if self._has_goal_cycles(goals):
            errors.append("Circular goal hierarchy detected")
        
        # Check goal weights sum reasonably
        total_weight = sum(g.weight for g in goals)
        if total_weight > 20:
            warnings.append(f"Total goal weight ({total_weight:.1f}) is high")
        
        return errors, warnings
    
    async def _validate_single_goal(self, goal: Goal) -> Tuple[List[str], List[str]]:
        """Validate a single goal."""
        errors = []
        warnings = []
        
        # Check metrics
        if not goal.metrics:
            warnings.append(f"Goal '{goal.id}' has no metrics")
        
        for metric in goal.metrics:
            if metric.target_value is None and metric.target_direction != "maintain":
                warnings.append(f"Metric '{metric.id}' has no target value")
            
            if metric.target_direction == "target" and metric.target_value is None:
                errors.append(f"Metric '{metric.id}' requires target value for 'target' direction")
        
        # Check timeline
        if goal.target_date:
            try:
                target = datetime.fromisoformat(goal.target_date.replace('Z', '+00:00'))
                if target < datetime.utcnow():
                    warnings.append(f"Goal '{goal.id}' target date is in the past")
            except ValueError:
                errors.append(f"Goal '{goal.id}' has invalid target_date format")
        
        return errors, warnings
    
    def _has_goal_cycles(self, goals: List[Goal]) -> bool:
        """Check for cycles in goal hierarchy."""
        goal_map = {g.id: g for g in goals}
        visited = set()
        rec_stack = set()
        
        def dfs(goal_id: str) -> bool:
            if goal_id in rec_stack:
                return True
            if goal_id in visited:
                return False
            
            visited.add(goal_id)
            rec_stack.add(goal_id)
            
            goal = goal_map.get(goal_id)
            if goal and goal.parent_goal_id:
                if dfs(goal.parent_goal_id):
                    return True
            
            rec_stack.remove(goal_id)
            return False
        
        for goal in goals:
            if goal.id not in visited:
                if dfs(goal.id):
                    return True
        
        return False
    
    async def _validate_cross_component(self, identity: IdentityConfig) -> Tuple[List[str], List[str]]:
        """Validate cross-component consistency."""
        errors = []
        warnings = []
        
        # Personality-Values alignment
        p_traits = identity.personality.traits
        core_values = identity.values.get_core_values()
        
        if p_traits.agreeableness > 0.7:
            caring_values = [v for v in core_values if "care" in v.name.lower() or "compassion" in v.name.lower() or "kindness" in v.name.lower()]
            if not caring_values:
                warnings.append("High agreeableness but no caring/compassion core values")
        
        if p_traits.openness > 0.7:
            growth_values = [v for v in core_values if "growth" in v.name.lower() or "learning" in v.name.lower() or "curiosity" in v.name.lower()]
            if not growth_values:
                warnings.append("High openness but no learning/growth core values")
        
        # Personality-Voice alignment
        if p_traits.extraversion > 0.7 and identity.voice.formality.value in ["very_formal", "formal"]:
            warnings.append("High extraversion but very formal voice - may feel inconsistent")
        
        if p_traits.playfulness > 0.7 and not identity.voice.uses_humor:
            warnings.append("High playfulness but humor disabled in voice")
        
        # Goals-Boundaries alignment
        for goal in identity.goals:
            if goal.type.value == "creative_collaboration":
                restrictive = [b for b in identity.boundaries if b.scope == BoundaryScope.GLOBAL and b.priority > 80]
                if restrictive:
                    warnings.append(
                        f"Creative collaboration goal may conflict with {len(restrictive)} "
                        f"high-priority global boundaries"
                    )
        
        # Safety compliance goal should align with boundaries
        safety_goals = [g for g in identity.goals if g.type.value == "safety_compliance"]
        if safety_goals:
            safety_boundaries = [b for b in identity.boundaries if "safety" in b.tags]
            if not safety_boundaries:
                warnings.append("Safety compliance goal defined but no safety-tagged boundaries")
        
        return errors, warnings
    
    async def _validate_uniqueness(self, identity: IdentityConfig) -> Tuple[List[str], List[str]]:
        """Validate uniqueness constraints."""
        errors = []
        warnings = []
        
        # Check boundary IDs unique
        boundary_ids = [b.id for b in identity.boundaries]
        if len(boundary_ids) != len(set(boundary_ids)):
            errors.append("Duplicate boundary IDs in identity")
        
        # Check goal IDs unique
        goal_ids = [g.id for g in identity.goals]
        if len(goal_ids) != len(set(goal_ids)):
            errors.append("Duplicate goal IDs in identity")
        
        # Check against existing identities (if repository available)
        if self.repository:
            existing = await self.repository.get_identities_by_companion(identity.companion_id)
            for ex in existing:
                if ex.id != identity.id and ex.status.value == "active":
                    warnings.append(f"Companion already has active identity: {ex.id}")
        
        return errors, warnings
    
    async def _validate_personality_change(self, change: EvolutionChange) -> List[str]:
        """Validate personality adjustment change."""
        errors = []
        
        if change.target_field == "traits":
            # Would validate proposed trait values
            if change.proposed_value:
                for trait, value in change.proposed_value.items():
                    if not isinstance(value, (int, float)) or value < 0 or value > 1:
                        errors.append(f"Invalid trait value for '{trait}': {value} (must be 0-1)")
        
        return errors
    
    async def _validate_voice_change(self, change: EvolutionChange) -> List[str]:
        """Validate voice modification change."""
        errors = []
        
        # Validate based on target field
        valid_fields = [
            "formality", "verbosity", "primary_tone", "communication_style",
            "uses_contractions", "uses_humor", "humor_style", "uses_metaphors",
            "uses_analogies", "max_response_length", "min_response_length",
        ]
        
        if change.target_field not in valid_fields:
            errors.append(f"Invalid voice field: {change.target_field}")
        
        return errors
    
    async def _validate_values_change(self, change: EvolutionChange) -> List[str]:
        """Validate values update change."""
        errors = []
        
        if change.target_field == "values" and change.proposed_value:
            # Validate proposed values structure
            if not isinstance(change.proposed_value, list):
                errors.append("Values must be a list")
            else:
                for i, v in enumerate(change.proposed_value):
                    if not isinstance(v, dict):
                        errors.append(f"Value {i} must be an object")
                    elif "name" not in v:
                        errors.append(f"Value {i} missing required 'name' field")
        
        return errors
    
    async def _validate_boundary_change(self, change: EvolutionChange) -> List[str]:
        """Validate boundary change."""
        errors = []
        
        if change.type == EvolutionChangeType.BOUNDARY_REMOVAL:
            # Check if boundary is referenced elsewhere
            if change.target_id and self.repository:
                refs = await self.repository.get_boundary_references(change.target_id)
                if refs:
                    errors.append(f"Boundary '{change.target_id}' is referenced by: {refs}")
        
        return errors
    
    async def _validate_goal_change(self, change: EvolutionChange) -> List[str]:
        """Validate goal change."""
        errors = []
        
        if change.type == EvolutionChangeType.GOAL_REMOVAL:
            if change.target_id and self.repository:
                refs = await self.repository.get_goal_references(change.target_id)
                if refs:
                    errors.append(f"Goal '{change.target_id}' is referenced by: {refs}")
        
        return errors