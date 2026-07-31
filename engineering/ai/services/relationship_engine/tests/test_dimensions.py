"""Tests for Dimensions Service."""

import pytest
from datetime import datetime
from uuid import uuid4

from relationship_engine.models.relationship import (
    Dimension,
    DimensionUpdate,
    Phase,
    RelationshipState,
)
from relationship_engine.services.dimensions import DimensionsService


@pytest.fixture
def dimensions_service():
    """Create a dimensions service instance."""
    return DimensionsService()


@pytest.fixture
def sample_state():
    """Create a sample relationship state."""
    state = RelationshipState(
        user_id=uuid4(),
        companion_id=uuid4(),
    )
    return state


class TestDimensionsService:
    """Test cases for DimensionsService."""

    def test_get_default_dimensions(self, dimensions_service):
        """Test getting default dimensions."""
        dims = dimensions_service.get_default_dimensions()
        assert len(dims) == 10
        assert all(isinstance(d, Dimension) for d in dims.values())
        assert all(d.score == 0.0 for d in dims.values())
        assert "trust" in dims
        assert "intimacy" in dims
        assert "affection" in dims

    def test_initialize_dimensions(self, dimensions_service):
        """Test initializing dimensions with custom values."""
        initial = {"trust": 5.0, "intimacy": 3.0}
        dims = dimensions_service.initialize_dimensions(initial)
        assert dims["trust"].score == 5.0
        assert dims["intimacy"].score == 3.0
        assert dims["affection"].score == 0.0

    def test_initialize_dimensions_bounds(self, dimensions_service):
        """Test that dimension scores are clamped to 0-10."""
        dims = dimensions_service.initialize_dimensions({"trust": 15.0, "intimacy": -2.0})
        assert dims["trust"].score == 10.0
        assert dims["intimacy"].score == 0.0

    def test_update_dimension(self, dimensions_service, sample_state):
        """Test updating a single dimension."""
        update = DimensionUpdate(
            name="trust",
            delta=1.0,
            reason="Test update",
        )
        updated = dimensions_service.update_dimension(sample_state, update)
        assert updated.name == "trust"
        assert updated.score == 1.2  # 1.0 * 1.2 weight
        assert updated.trend > 0
        assert updated.interaction_count == 1

    def test_update_dimension_bounds(self, dimensions_service, sample_state):
        """Test that dimension updates are bounded."""
        # Set initial high value
        sample_state.dimensions["trust"] = Dimension(name="trust", score=9.5)
        
        update = DimensionUpdate(name="trust", delta=2.0)
        updated = dimensions_service.update_dimension(sample_state, update)
        assert updated.score == 10.0  # Capped at 10

    def test_apply_interaction_impact_message(self, dimensions_service, sample_state):
        """Test applying message interaction impact."""
        updated = dimensions_service.apply_interaction_impact(
            sample_state, "message", intensity=1.0
        )
        assert len(updated) == 3  # communication, trust, affection
        dim_names = [d.name for d in updated]
        assert "communication" in dim_names
        assert "trust" in dim_names
        assert "affection" in dim_names

    def test_apply_interaction_impact_voice_call(self, dimensions_service, sample_state):
        """Test applying voice call interaction impact."""
        updated = dimensions_service.apply_interaction_impact(
            sample_state, "voice_call", intensity=1.0
        )
        dim_names = [d.name for d in updated]
        assert "communication" in dim_names
        assert "intimacy" in dim_names
        assert "affection" in dim_names
        assert "trust" in dim_names

    def test_apply_interaction_impact_conflict(self, dimensions_service, sample_state):
        """Test applying conflict interaction impact."""
        # Set initial values
        sample_state.dimensions["trust"] = Dimension(name="trust", score=5.0)
        sample_state.dimensions["communication"] = Dimension(name="communication", score=5.0)
        
        updated = dimensions_service.apply_interaction_impact(
            sample_state, "conflict", intensity=1.0
        )
        dim_names = [d.name for d in updated]
        assert "trust" in dim_names
        assert "communication" in dim_names
        assert "respect" in dim_names
        assert "affection" in dim_names
        
        # Scores should decrease
        assert sample_state.dimensions["trust"].score < 5.0
        assert sample_state.dimensions["communication"].score < 5.0

    def test_apply_daily_decay(self, dimensions_service, sample_state):
        """Test applying daily decay."""
        # Set initial values
        for name in sample_state.dimensions:
            sample_state.dimensions[name].score = 5.0
        
        updated = dimensions_service.apply_daily_decay(sample_state, days=1)
        assert len(updated) == 10  # All dimensions
        # Scores should slightly decrease
        for dim in updated:
            assert dim.score < 5.0

    def test_calculate_weighted_average(self, dimensions_service, sample_state):
        """Test calculating weighted average."""
        # Set known values
        sample_state.dimensions["trust"] = Dimension(name="trust", score=10.0)
        sample_state.dimensions["intimacy"] = Dimension(name="intimacy", score=10.0)
        sample_state.dimensions["affection"] = Dimension(name="affection", score=10.0)
        
        avg = dimensions_service.calculate_weighted_average(sample_state)
        # Weighted by trust(1.2) + intimacy(1.1) + affection(1.0) + others(1.0 * 7)
        # = (10*1.2 + 10*1.1 + 10*1.0 + 0*7) / (1.2+1.1+1.0+7*1.0) = 33 / 10.3 ≈ 3.2
        assert 0 < avg <= 10

    def test_get_dimension_summary(self, dimensions_service, sample_state):
        """Test getting dimension summary."""
        summary = dimensions_service.get_dimension_summary(sample_state)
        assert len(summary) == 10
        for name, data in summary.items():
            assert "score" in data
            assert "trend" in data
            assert "interaction_count" in data
            assert "last_updated" in data
            assert "weight" in data

    def test_get_strongest_dimensions(self, dimensions_service, sample_state):
        """Test getting strongest dimensions."""
        sample_state.dimensions["trust"].score = 9.0
        sample_state.dimensions["intimacy"].score = 8.0
        sample_state.dimensions["affection"].score = 7.0
        
        strongest = dimensions_service.get_strongest_dimensions(sample_state, top_n=2)
        assert strongest == ["trust", "intimacy"]

    def test_get_weakest_dimensions(self, dimensions_service, sample_state):
        """Test getting weakest dimensions."""
        sample_state.dimensions["trust"].score = 1.0
        sample_state.dimensions["intimacy"].score = 2.0
        sample_state.dimensions["affection"].score = 3.0
        
        weakest = dimensions_service.get_weakest_dimensions(sample_state, top_n=2)
        assert weakest == ["trust", "intimacy"]

    def test_get_improving_dimensions(self, dimensions_service, sample_state):
        """Test getting improving dimensions."""
        sample_state.dimensions["trust"].trend = 0.5
        sample_state.dimensions["intimacy"].trend = -0.1
        sample_state.dimensions["affection"].trend = 0.2
        
        improving = dimensions_service.get_improving_dimensions(sample_state, threshold=0.2)
        assert "trust" in improving
        assert "affection" in improving
        assert "intimacy" not in improving

    def test_get_declining_dimensions(self, dimensions_service, sample_state):
        """Test getting declining dimensions."""
        sample_state.dimensions["trust"].trend = -0.5
        sample_state.dimensions["intimacy"].trend = 0.1
        sample_state.dimensions["affection"].trend = -0.2
        
        declining = dimensions_service.get_declining_dimensions(sample_state, threshold=-0.2)
        assert "trust" in declining
        assert "affection" in declining
        assert "intimacy" not in declining

    def test_predict_phase_progression(self, dimensions_service, sample_state):
        """Test phase progression prediction."""
        # Set all dimensions to moderate values
        for name in sample_state.dimensions:
            sample_state.dimensions[name].score = 5.0
            sample_state.dimensions[name].trend = 0.1
        
        prediction = dimensions_service.predict_phase_progression(sample_state, days_ahead=30)
        assert "current_phase" in prediction
        assert "projected_phase" in prediction
        assert "projected_score" in prediction
        assert "days_to_next_phase" in prediction
        assert "average_daily_trend" in prediction