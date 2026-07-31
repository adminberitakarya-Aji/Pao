"""Base repository interfaces for Emotion Engine."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from emotion_engine.models.emotion import (
    EmotionState,
    Appraisal,
    ValenceArousal,
    CalibrationData,
    Expression,
    EmotionEvent,
    EmotionCategory,
    ExpressionModality,
)


class EmotionStateRepository(ABC):
    """Abstract repository for emotion state persistence."""

    @abstractmethod
    async def get(self, user_id: UUID, companion_id: UUID) -> Optional[EmotionState]:
        """Get emotion state by user and companion."""
        pass

    @abstractmethod
    async def create(self, state: EmotionState) -> EmotionState:
        """Create new emotion state."""
        pass

    @abstractmethod
    async def update(self, state: EmotionState) -> EmotionState:
        """Update existing emotion state."""
        pass

    @abstractmethod
    async def delete(self, user_id: UUID, companion_id: UUID) -> bool:
        """Delete emotion state."""
        pass

    @abstractmethod
    async def list(
        self,
        limit: int = 100,
        offset: int = 0,
        user_id: Optional[UUID] = None,
    ) -> List[EmotionState]:
        """List emotion states with optional filtering."""
        pass


class AppraisalRepository(ABC):
    """Abstract repository for appraisal persistence."""

    @abstractmethod
    async def create(self, appraisal: Appraisal, user_id: UUID, companion_id: UUID) -> Appraisal:
        """Store an appraisal."""
        pass

    @abstractmethod
    async def get_history(
        self,
        user_id: UUID,
        companion_id: UUID,
        limit: int = 50,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Appraisal]:
        """Get appraisal history."""
        pass

    @abstractmethod
    async def get_latest(self, user_id: UUID, companion_id: UUID) -> Optional[Appraisal]:
        """Get most recent appraisal."""
        pass


class CalibrationRepository(ABC):
    """Abstract repository for calibration data."""

    @abstractmethod
    async def get(self, user_id: UUID, companion_id: UUID) -> Optional[CalibrationData]:
        """Get calibration data."""
        pass

    @abstractmethod
    async def create(self, calibration: CalibrationData) -> CalibrationData:
        """Create new calibration data."""
        pass

    @abstractmethod
    async def update(self, calibration: CalibrationData) -> CalibrationData:
        """Update calibration data."""
        pass

    @abstractmethod
    async def add_valence_sample(
        self,
        user_id: UUID,
        companion_id: UUID,
        predicted: float,
        actual: float,
    ) -> CalibrationData:
        """Add a valence calibration sample."""
        pass

    @abstractmethod
    async def add_arousal_sample(
        self,
        user_id: UUID,
        companion_id: UUID,
        predicted: float,
        actual: float,
    ) -> CalibrationData:
        """Add an arousal calibration sample."""
        pass


class ExpressionRepository(ABC):
    """Abstract repository for expression templates."""

    @abstractmethod
    async def get_expression(
        self,
        modality: ExpressionModality,
        emotion_category: EmotionCategory,
    ) -> Optional[Expression]:
        """Get expression template."""
        pass

    @abstractmethod
    async def get_all_expressions(self) -> List[Expression]:
        """Get all expression templates."""
        pass

    @abstractmethod
    async def create_expression(self, expression: Expression) -> Expression:
        """Create expression template."""
        pass

    @abstractmethod
    async def update_expression(self, expression: Expression) -> Expression:
        """Update expression template."""
        pass


class EmotionEventRepository(ABC):
    """Abstract repository for emotion events (audit trail)."""

    @abstractmethod
    async def create(self, event: EmotionEvent) -> EmotionEvent:
        """Store an emotion event."""
        pass

    @abstractmethod
    async def get_events(
        self,
        user_id: UUID,
        companion_id: UUID,
        event_types: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[EmotionEvent]:
        """Get emotion events with filters."""
        pass

    @abstractmethod
    async def count_events(
        self,
        user_id: UUID,
        companion_id: UUID,
        start_date: Optional[datetime] = None,
    ) -> int:
        """Count emotion events."""
        pass