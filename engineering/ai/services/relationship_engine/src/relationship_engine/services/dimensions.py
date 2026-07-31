"""Dimensions Service - Tracks and updates relationship dimensions."""

import math
from datetime import datetime
from typing import Any
from uuid import UUID

from relationship_engine.config import settings
from relationship_engine.models.relationship import (
    Dimension,
    DimensionUpdate,
    Phase,
    RelationshipState,
)


class DimensionsService:
    """Service for managing relationship dimensions."""

    # Default dimension weights for phase calculation
    DIMENSION_WEIGHTS: dict[str, float] = {
        "trust": 1.2,
        "intimacy": 1.1,
        "affection": 1.0,
        "respect": 1.1,
        "commitment": 1.2,
        "communication": 1.0,
        "shared_values": 1.1,
        "support": 1.0,
        "playfulness": 0.8,
        "growth": 1.0,
    }

    # Dimension update rules based on interaction types
    INTERACTION_IMPACTS: dict[str, dict[str, float]] = {
        "message": {
            "communication": 0.05,
            "trust": 0.01,
            "affection": 0.02,
        },
        "deep_conversation": {
            "communication": 0.15,
            "trust": 0.1,
            "intimacy": 0.08,
            "shared_values": 0.05,
        },
        "voice_call": {
            "communication": 0.1,
            "intimacy": 0.05,
            "affection": 0.05,
            "trust": 0.03,
        },
        "memory_share": {
            "trust": 0.1,
            "intimacy": 0.1,
            "shared_values": 0.08,
            "growth": 0.05,
        },
        "proactive_nudge": {
            "support": 0.08,
            "playfulness": 0.05,
            "communication": 0.03,
        },
        "conflict": {
            "trust": -0.15,
            "communication": -0.1,
            "respect": -0.08,
            "affection": -0.05,
        },
        "reconciliation": {
            "trust": 0.2,
            "communication": 0.15,
            "respect": 0.1,
            "growth": 0.1,
        },
        "celebration": {
            "playfulness": 0.15,
            "affection": 0.1,
            "shared_values": 0.05,
        },
        "support_moment": {
            "support": 0.2,
            "trust": 0.1,
            "affection": 0.08,
        },
    }

    # Decay rates per day for each dimension (very slow)
    DAILY_DECAY: dict[str, float] = {
        "trust": -0.001,
        "intimacy": -0.002,
        "affection": -0.003,
        "respect": -0.001,
        "commitment": -0.0005,
        "communication": -0.002,
        "shared_values": -0.0005,
        "support": -0.001,
        "playfulness": -0.005,
        "growth": -0.001,
    }

    def __init__(self):
        self.dimensions_list = settings.dimensions

    def get_default_dimensions(self) -> dict[str, Dimension]:
        """Get default dimensions with zero scores."""
        return {
            name: Dimension(name=name, score=0.0, trend=0.0, last_updated=datetime.utcnow())
            for name in self.dimensions_list
        }

    def initialize_dimensions(self, initial: dict[str, float] | None = None) -> dict[str, Dimension]:
        """Initialize dimensions with optional starting values."""
        dims = self.get_default_dimensions()
        if initial:
            for name, score in initial.items():
                if name in dims:
                    dims[name].score = max(0.0, min(10.0, score))
        return dims

    def update_dimension(
        self,
        state: RelationshipState,
        update: DimensionUpdate,
    ) -> Dimension:
        """Apply a single dimension update."""
        dimension = state.get_dimension(update.name)
        old_score = dimension.score

        # Apply delta with weight
        weight = self.DIMENSION_WEIGHTS.get(update.name, 1.0)
        delta = update.delta * weight

        # Apply bounds
        new_score = max(0.0, min(10.0, old_score + delta))
        dimension.score = round(new_score, 2)

        # Update trend
        if new_score > old_score:
            dimension.trend = min(1.0, dimension.trend + 0.1)
        elif new_score < old_score:
            dimension.trend = max(-1.0, dimension.trend - 0.1)
        else:
            dimension.trend *= 0.9  # Trend decays toward neutral

        dimension.trend = round(dimension.trend, 2)
        dimension.last_updated = datetime.utcnow()
        dimension.interaction_count += 1

        if update.metadata:
            dimension.metadata.update(update.metadata)

        return dimension

    def apply_interaction_impact(
        self,
        state: RelationshipState,
        interaction_type: str,
        intensity: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> list[Dimension]:
        """Apply impact from a specific interaction type."""
        impacts = self.INTERACTION_IMPACTS.get(interaction_type, {})
        if not impacts:
            return []

        updated = []
        for dim_name, impact in impacts.items():
            if dim_name in state.dimensions:
                update = DimensionUpdate(
                    name=dim_name,
                    delta=impact * intensity,
                    reason=f"Interaction: {interaction_type}",
                    interaction_type=interaction_type,
                    metadata=metadata or {},
                )
                updated_dim = self.update_dimension(state, update)
                updated.append(updated_dim)

        return updated

    def apply_bulk_updates(
        self,
        state: RelationshipState,
        updates: list[DimensionUpdate],
    ) -> list[Dimension]:
        """Apply multiple dimension updates at once."""
        updated = []
        for update in updates:
            if update.name in state.dimensions:
                updated_dim = self.update_dimension(state, update)
                updated.append(updated_dim)
        return updated

    def apply_daily_decay(self, state: RelationshipState, days: int = 1) -> list[Dimension]:
        """Apply daily decay to all dimensions."""
        updated = []
        for name, dimension in state.dimensions.items():
            decay = self.DAILY_DECAY.get(name, 0.0) * days
            if decay != 0:
                update = DimensionUpdate(
                    name=name,
                    delta=decay,
                    reason="Daily decay",
                    interaction_type="decay",
                )
                updated_dim = self.update_dimension(state, update)
                updated.append(updated_dim)
        return updated

    def calculate_weighted_average(self, state: RelationshipState) -> float:
        """Calculate weighted average of all dimensions for phase determination."""
        if not state.dimensions:
            return 0.0

        total_weight = 0.0
        weighted_sum = 0.0

        for name, dimension in state.dimensions.items():
            weight = self.DIMENSION_WEIGHTS.get(name, 1.0)
            weighted_sum += dimension.score * weight
            total_weight += weight

        return round(weighted_sum / total_weight, 2) if total_weight > 0 else 0.0

    def get_dimension_summary(self, state: RelationshipState) -> dict[str, Any]:
        """Get a summary of all dimensions."""
        return {
            name: {
                "score": dim.score,
                "trend": dim.trend,
                "interaction_count": dim.interaction_count,
                "last_updated": dim.last_updated.isoformat(),
                "weight": self.DIMENSION_WEIGHTS.get(name, 1.0),
            }
            for name, dim in state.dimensions.items()
        }

    def get_strongest_dimensions(self, state: RelationshipState, top_n: int = 3) -> list[str]:
        """Get the top N strongest dimensions."""
        sorted_dims = sorted(
            state.dimensions.items(),
            key=lambda x: x[1].score,
            reverse=True,
        )
        return [name for name, _ in sorted_dims[:top_n]]

    def get_weakest_dimensions(self, state: RelationshipState, top_n: int = 3) -> list[str]:
        """Get the bottom N weakest dimensions."""
        sorted_dims = sorted(
            state.dimensions.items(),
            key=lambda x: x[1].score,
        )
        return [name for name, _ in sorted_dims[:top_n]]

    def get_improving_dimensions(self, state: RelationshipState, threshold: float = 0.1) -> list[str]:
        """Get dimensions with positive trend above threshold."""
        return [
            name
            for name, dim in state.dimensions.items()
            if dim.trend >= threshold
        ]

    def get_declining_dimensions(self, state: RelationshipState, threshold: float = -0.1) -> list[str]:
        """Get dimensions with negative trend below threshold."""
        return [
            name
            for name, dim in state.dimensions.items()
            if dim.trend <= threshold
        ]

    def predict_phase_progression(
        self,
        state: RelationshipState,
        days_ahead: int = 30,
    ) -> dict[str, Any]:
        """Predict phase progression based on current trends."""
        current_score = state.phase_score
        current_phase = state.phase

        # Project score based on trends
        avg_trend = sum(d.trend for d in state.dimensions.values()) / len(state.dimensions)
        projected_change = avg_trend * days_ahead * 0.1  # Scale factor
        projected_score = max(0.0, min(10.0, current_score + projected_change))
        projected_phase = Phase.from_score(projected_score)

        # Days to next phase
        next_phase = current_phase.next_phase()
        if next_phase:
            # Estimate threshold for next phase
            phase_thresholds = {
                Phase.ACQUAINTANCE: 1.5,
                Phase.FRIEND: 3.0,
                Phase.CLOSE_FRIEND: 5.0,
                Phase.PARTNER: 7.0,
                Phase.SOULMATE: 8.5,
            }
            next_threshold = phase_thresholds.get(next_phase, 10.0)
            score_needed = next_threshold - current_score
            if avg_trend > 0:
                days_to_next = score_needed / (avg_trend * 0.1)
            else:
                days_to_next = float("inf")
        else:
            days_to_next = float("inf")

        return {
            "current_phase": current_phase.value,
            "current_score": current_score,
            "projected_score": round(projected_score, 2),
            "projected_phase": projected_phase.value,
            "days_to_next_phase": round(days_to_next, 1) if days_to_next != float("inf") else None,
            "average_daily_trend": round(avg_trend, 4),
        }