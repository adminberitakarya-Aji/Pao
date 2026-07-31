"""PostgreSQL repositories for Emotion Engine."""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from sqlalchemy import select, delete, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

from emotion_engine.config import settings
from emotion_engine.repositories.base import (
    EmotionStateRepository,
    AppraisalRepository,
    CalibrationRepository,
    ExpressionRepository,
    EmotionEventRepository,
)
from emotion_engine.models.emotion import (
    EmotionState,
    Appraisal,
    ValenceArousal,
    CalibrationData,
    Expression,
    EmotionEvent,
    EmotionCategory,
    ExpressionModality,
    AppraisalDimension,
)


# SQLAlchemy Models
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float, DateTime, Integer, Text, Boolean


class Base(DeclarativeBase):
    pass


class EmotionStateModel(Base):
    __tablename__ = "emotion_states"

    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    companion_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)

    # ValenceArousal
    valence: Mapped[float] = mapped_column(Float, default=0.0)
    arousal: Mapped[float] = mapped_column(Float, default=0.3)
    va_confidence: Mapped[float] = mapped_column(Float, default=0.8)
    va_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Mood
    mood_valence: Mapped[float] = mapped_column(Float, default=0.1)
    mood_arousal: Mapped[float] = mapped_column(Float, default=0.2)

    # Active emotions
    active_emotions: Mapped[Dict[str, float]] = mapped_column(JSONB, default=dict)

    # Expression style
    expression_style: Mapped[Dict[str, float]] = mapped_column(JSONB, default=dict)

    # Metadata
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AppraisalModel(Base):
    __tablename__ = "appraisals"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=UUID)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), index=True)
    companion_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), index=True)

    # Appraisal dimensions
    novelty: Mapped[float] = mapped_column(Float, default=0.5)
    pleasantness: Mapped[float] = mapped_column(Float, default=0.0)
    goal_relevance: Mapped[float] = mapped_column(Float, default=0.5)
    goal_congruence: Mapped[float] = mapped_column(Float, default=0.0)
    coping_potential: Mapped[float] = mapped_column(Float, default=0.5)
    norm_compatibility: Mapped[float] = mapped_column(Float, default=0.0)
    self_relevance: Mapped[float] = mapped_column(Float, default=0.5)
    agency: Mapped[float] = mapped_column(Float, default=0.0)
    certainty: Mapped[float] = mapped_column(Float, default=0.5)
    control: Mapped[float] = mapped_column(Float, default=0.5)

    # Metadata
    trigger_event: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.7)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class CalibrationModel(Base):
    __tablename__ = "calibrations"

    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    companion_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)

    # Valence calibration
    valence_bias: Mapped[float] = mapped_column(Float, default=0.0)
    valence_scale: Mapped[float] = mapped_column(Float, default=1.0)
    valence_samples: Mapped[List[List[float]]] = mapped_column(JSONB, default=list)

    # Arousal calibration
    arousal_bias: Mapped[float] = mapped_column(Float, default=0.0)
    arousal_scale: Mapped[float] = mapped_column(Float, default=1.0)
    arousal_samples: Mapped[List[List[float]]] = mapped_column(JSONB, default=list)

    # Appraisal weights
    appraisal_weights: Mapped[Dict[str, float]] = mapped_column(JSONB, default=dict)

    # Expression preferences
    expression_preferences: Mapped[Dict[str, Dict[str, float]]] = mapped_column(JSONB, default=dict)

    # Statistics
    total_samples: Mapped[int] = mapped_column(Integer, default=0)
    last_calibrated: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    calibration_quality: Mapped[float] = mapped_column(Float, default=0.0)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ExpressionModel(Base):
    __tablename__ = "expressions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=UUID)
    modality: Mapped[str] = mapped_column(String(50), index=True)
    emotion_category: Mapped[str] = mapped_column(String(50), index=True)
    intensity: Mapped[float] = mapped_column(Float, default=0.5)

    # Parameters
    parameters: Mapped[Dict[str, float]] = mapped_column(JSONB, default=dict)

    # Metadata
    personality_influence: Mapped[float] = mapped_column(Float, default=0.5)
    context_influence: Mapped[float] = mapped_column(Float, default=0.5)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        # Unique constraint on modality + emotion_category
        # (handled by application logic)
    )


class EmotionEventModel(Base):
    __tablename__ = "emotion_events"

    event_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=UUID)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), index=True)
    companion_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), index=True)
    event_type: Mapped[str] = mapped_column(String(50), index=True)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSONB)
    event_metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


# Database setup
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_timeout=settings.database_pool_timeout,
    echo=settings.environment == "development",
)

async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def create_tables():
    """Create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """Drop all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def get_session() -> AsyncSession:
    """Get database session."""
    async with async_session_maker() as session:
        yield session


# Repository Implementations
class PostgresEmotionStateRepository(EmotionStateRepository):
    """PostgreSQL implementation of EmotionStateRepository."""

    def __init__(self, session_factory: async_sessionmaker = async_session_maker):
        self.session_factory = session_factory

    async def get(self, user_id: UUID, companion_id: UUID) -> Optional[EmotionState]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(EmotionStateModel).where(
                    and_(
                        EmotionStateModel.user_id == user_id,
                        EmotionStateModel.companion_id == companion_id,
                    )
                )
            )
            model = result.scalar_one_or_none()
            if not model:
                return None
            return self._model_to_state(model)

    async def create(self, state: EmotionState) -> EmotionState:
        async with self.session_factory() as session:
            model = self._state_to_model(state)
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return self._model_to_state(model)

    async def update(self, state: EmotionState) -> EmotionState:
        async with self.session_factory() as session:
            result = await session.execute(
                select(EmotionStateModel).where(
                    and_(
                        EmotionStateModel.user_id == state.user_id,
                        EmotionStateModel.companion_id == state.companion_id,
                    )
                )
            )
            model = result.scalar_one_or_none()
            if not model:
                model = self._state_to_model(state)
                session.add(model)
            else:
                self._update_model_from_state(model, state)
            await session.commit()
            await session.refresh(model)
            return self._model_to_state(model)

    async def delete(self, user_id: UUID, companion_id: UUID) -> bool:
        async with self.session_factory() as session:
            result = await session.execute(
                delete(EmotionStateModel).where(
                    and_(
                        EmotionStateModel.user_id == user_id,
                        EmotionStateModel.companion_id == companion_id,
                    )
                )
            )
            await session.commit()
            return result.rowcount > 0

    async def list(
        self,
        limit: int = 100,
        offset: int = 0,
        user_id: Optional[UUID] = None,
    ) -> List[EmotionState]:
        async with self.session_factory() as session:
            query = select(EmotionStateModel).limit(limit).offset(offset)
            if user_id:
                query = query.where(EmotionStateModel.user_id == user_id)
            result = await session.execute(query)
            return [self._model_to_state(m) for m in result.scalars().all()]

    def _state_to_model(self, state: EmotionState) -> EmotionStateModel:
        return EmotionStateModel(
            user_id=state.user_id,
            companion_id=state.companion_id,
            valence=state.valence_arousal.valence,
            arousal=state.valence_arousal.arousal,
            va_confidence=state.valence_arousal.confidence,
            va_timestamp=state.valence_arousal.timestamp,
            mood_valence=state.mood.valence,
            mood_arousal=state.mood.arousal,
            active_emotions={k.value: v for k, v in state.active_emotions.items()},
            expression_style=state.expression_style,
            version=state.version,
            created_at=state.created_at,
            updated_at=state.updated_at,
        )

    def _model_to_state(self, model: EmotionStateModel) -> EmotionState:
        return EmotionState(
            user_id=model.user_id,
            companion_id=model.companion_id,
            valence_arousal=ValenceArousal(
                valence=model.valence,
                arousal=model.arousal,
                confidence=model.va_confidence,
                timestamp=model.va_timestamp,
            ),
            mood=ValenceArousal(
                valence=model.mood_valence,
                arousal=model.mood_arousal,
            ),
            active_emotions={
                EmotionCategory(k): v for k, v in model.active_emotions.items()
            },
            expression_style=model.expression_style,
            version=model.version,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _update_model_from_state(self, model: EmotionStateModel, state: EmotionState) -> None:
        model.valence = state.valence_arousal.valence
        model.arousal = state.valence_arousal.arousal
        model.va_confidence = state.valence_arousal.confidence
        model.va_timestamp = state.valence_arousal.timestamp
        model.mood_valence = state.mood.valence
        model.mood_arousal = state.mood.arousal
        model.active_emotions = {k.value: v for k, v in state.active_emotions.items()}
        model.expression_style = state.expression_style
        model.version = state.version
        model.updated_at = state.updated_at


class PostgresAppraisalRepository(AppraisalRepository):
    """PostgreSQL implementation of AppraisalRepository."""

    def __init__(self, session_factory: async_sessionmaker = async_session_maker):
        self.session_factory = session_factory

    async def create(self, appraisal: Appraisal, user_id: UUID, companion_id: UUID) -> Appraisal:
        async with self.session_factory() as session:
            model = AppraisalModel(
                user_id=user_id,
                companion_id=companion_id,
                novelty=appraisal.novelty,
                pleasantness=appraisal.pleasantness,
                goal_relevance=appraisal.goal_relevance,
                goal_congruence=appraisal.goal_congruence,
                coping_potential=appraisal.coping_potential,
                norm_compatibility=appraisal.norm_compatibility,
                self_relevance=appraisal.self_relevance,
                agency=appraisal.agency,
                certainty=appraisal.certainty,
                control=appraisal.control,
                trigger_event=appraisal.trigger_event,
                confidence=appraisal.confidence,
                timestamp=appraisal.timestamp,
            )
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return self._model_to_appraisal(model)

    async def get_history(
        self,
        user_id: UUID,
        companion_id: UUID,
        limit: int = 50,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Appraisal]:
        async with self.session_factory() as session:
            query = (
                select(AppraisalModel)
                .where(
                    and_(
                        AppraisalModel.user_id == user_id,
                        AppraisalModel.companion_id == companion_id,
                    )
                )
                .order_by(desc(AppraisalModel.timestamp))
                .limit(limit)
            )
            if start_date:
                query = query.where(AppraisalModel.timestamp >= start_date)
            if end_date:
                query = query.where(AppraisalModel.timestamp <= end_date)
            result = await session.execute(query)
            return [self._model_to_appraisal(m) for m in result.scalars().all()]

    async def get_latest(self, user_id: UUID, companion_id: UUID) -> Optional[Appraisal]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(AppraisalModel)
                .where(
                    and_(
                        AppraisalModel.user_id == user_id,
                        AppraisalModel.companion_id == companion_id,
                    )
                )
                .order_by(desc(AppraisalModel.timestamp))
                .limit(1)
            )
            model = result.scalar_one_or_none()
            if not model:
                return None
            return self._model_to_appraisal(model)

    def _model_to_appraisal(self, model: AppraisalModel) -> Appraisal:
        return Appraisal(
            novelty=model.novelty,
            pleasantness=model.pleasantness,
            goal_relevance=model.goal_relevance,
            goal_congruence=model.goal_congruence,
            coping_potential=model.coping_potential,
            norm_compatibility=model.norm_compatibility,
            self_relevance=model.self_relevance,
            agency=model.agency,
            certainty=model.certainty,
            control=model.control,
            trigger_event=model.trigger_event,
            confidence=model.confidence,
            timestamp=model.timestamp,
        )


class PostgresCalibrationRepository(CalibrationRepository):
    """PostgreSQL implementation of CalibrationRepository."""

    def __init__(self, session_factory: async_sessionmaker = async_session_maker):
        self.session_factory = session_factory

    async def get(self, user_id: UUID, companion_id: UUID) -> Optional[CalibrationData]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(CalibrationModel).where(
                    and_(
                        CalibrationModel.user_id == user_id,
                        CalibrationModel.companion_id == companion_id,
                    )
                )
            )
            model = result.scalar_one_or_none()
            if not model:
                return None
            return self._model_to_calibration(model)

    async def create(self, calibration: CalibrationData) -> CalibrationData:
        async with self.session_factory() as session:
            model = self._calibration_to_model(calibration)
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return self._model_to_calibration(model)

    async def update(self, calibration: CalibrationData) -> CalibrationData:
        async with self.session_factory() as session:
            result = await session.execute(
                select(CalibrationModel).where(
                    and_(
                        CalibrationModel.user_id == calibration.user_id,
                        CalibrationModel.companion_id == calibration.companion_id,
                    )
                )
            )
            model = result.scalar_one_or_none()
            if not model:
                model = self._calibration_to_model(calibration)
                session.add(model)
            else:
                self._update_model_from_calibration(model, calibration)
            await session.commit()
            await session.refresh(model)
            return self._model_to_calibration(model)

    async def add_valence_sample(
        self,
        user_id: UUID,
        companion_id: UUID,
        predicted: float,
        actual: float,
    ) -> CalibrationData:
        calibration = await self.get(user_id, companion_id)
        if not calibration:
            calibration = CalibrationData(user_id=user_id, companion_id=companion_id)
        calibration.add_valence_sample(predicted, actual)
        return await self.update(calibration)

    async def add_arousal_sample(
        self,
        user_id: UUID,
        companion_id: UUID,
        predicted: float,
        actual: float,
    ) -> CalibrationData:
        calibration = await self.get(user_id, companion_id)
        if not calibration:
            calibration = CalibrationData(user_id=user_id, companion_id=companion_id)
        calibration.add_arousal_sample(predicted, actual)
        return await self.update(calibration)

    def _calibration_to_model(self, calibration: CalibrationData) -> CalibrationModel:
        return CalibrationModel(
            user_id=calibration.user_id,
            companion_id=calibration.companion_id,
            valence_bias=calibration.valence_bias,
            valence_scale=calibration.valence_scale,
            valence_samples=calibration.valence_samples,
            arousal_bias=calibration.arousal_bias,
            arousal_scale=calibration.arousal_scale,
            arousal_samples=calibration.arousal_samples,
            appraisal_weights={k.value: v for k, v in calibration.appraisal_weights.items()},
            expression_preferences=calibration.expression_preferences,
            total_samples=calibration.total_samples,
            last_calibrated=calibration.last_calibrated,
            calibration_quality=calibration.calibration_quality,
        )

    def _model_to_calibration(self, model: CalibrationModel) -> CalibrationData:
        return CalibrationData(
            user_id=model.user_id,
            companion_id=model.companion_id,
            valence_bias=model.valence_bias,
            valence_scale=model.valence_scale,
            valence_samples=model.valence_samples,
            arousal_bias=model.arousal_bias,
            arousal_scale=model.arousal_scale,
            arousal_samples=model.arousal_samples,
            appraisal_weights={
                AppraisalDimension(k): v for k, v in model.appraisal_weights.items()
            },
            expression_preferences=model.expression_preferences,
            total_samples=model.total_samples,
            last_calibrated=model.last_calibrated,
            calibration_quality=model.calibration_quality,
        )

    def _update_model_from_calibration(
        self, model: CalibrationModel, calibration: CalibrationData
    ) -> None:
        model.valence_bias = calibration.valence_bias
        model.valence_scale = calibration.valence_scale
        model.valence_samples = calibration.valence_samples
        model.arousal_bias = calibration.arousal_bias
        model.arousal_scale = calibration.arousal_scale
        model.arousal_samples = calibration.arousal_samples
        model.appraisal_weights = {k.value: v for k, v in calibration.appraisal_weights.items()}
        model.expression_preferences = calibration.expression_preferences
        model.total_samples = calibration.total_samples
        model.last_calibrated = calibration.last_calibrated
        model.calibration_quality = calibration.calibration_quality
        model.updated_at = datetime.utcnow()


class PostgresExpressionRepository(ExpressionRepository):
    """PostgreSQL implementation of ExpressionRepository."""

    def __init__(self, session_factory: async_sessionmaker = async_session_maker):
        self.session_factory = session_factory

    async def get_expression(
        self,
        modality: ExpressionModality,
        emotion_category: EmotionCategory,
    ) -> Optional[Expression]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(ExpressionModel).where(
                    and_(
                        ExpressionModel.modality == modality.value,
                        ExpressionModel.emotion_category == emotion_category.value,
                    )
                )
            )
            model = result.scalar_one_or_none()
            if not model:
                return None
            return self._model_to_expression(model)

    async def get_all_expressions(self) -> List[Expression]:
        async with self.session_factory() as session:
            result = await session.execute(select(ExpressionModel))
            return [self._model_to_expression(m) for m in result.scalars().all()]

    async def create_expression(self, expression: Expression) -> Expression:
        async with self.session_factory() as session:
            model = self._expression_to_model(expression)
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return self._model_to_expression(model)

    async def update_expression(self, expression: Expression) -> Expression:
        async with self.session_factory() as session:
            result = await session.execute(
                select(ExpressionModel).where(
                    and_(
                        ExpressionModel.modality == expression.modality.value,
                        ExpressionModel.emotion_category == expression.emotion_category.value,
                    )
                )
            )
            model = result.scalar_one_or_none()
            if not model:
                model = self._expression_to_model(expression)
                session.add(model)
            else:
                model.intensity = expression.intensity
                model.parameters = self._expression_params_to_dict(expression)
                model.personality_influence = expression.personality_influence
                model.context_influence = expression.context_influence
                model.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(model)
            return self._model_to_expression(model)

    def _expression_to_model(self, expression: Expression) -> ExpressionModel:
        return ExpressionModel(
            modality=expression.modality.value,
            emotion_category=expression.emotion_category.value,
            intensity=expression.intensity,
            parameters=self._expression_params_to_dict(expression),
            personality_influence=expression.personality_influence,
            context_influence=expression.context_influence,
        )

    def _expression_params_to_dict(self, expression: Expression) -> Dict[str, float]:
        params = {}
        if expression.text_tone:
            params["text_tone"] = hash(expression.text_tone) % 100 / 100.0
        params["text_formality"] = expression.text_formality
        params["text_verbosity"] = expression.text_verbosity
        params["text_emoji_probability"] = expression.text_emoji_probability
        params["voice_pitch_shift"] = expression.voice_pitch_shift
        params["voice_rate_change"] = expression.voice_rate_change
        params["voice_volume_change"] = expression.voice_volume_change
        if expression.voice_quality:
            params["voice_quality"] = hash(expression.voice_quality) % 100 / 100.0
        params.update({f"face_au_{k}": v for k, v in expression.face_action_units.items()})
        if expression.gesture_type:
            params["gesture_type"] = hash(expression.gesture_type) % 100 / 100.0
        params["gesture_amplitude"] = expression.gesture_amplitude
        params["gesture_speed"] = expression.gesture_speed
        return params

    def _model_to_expression(self, model: ExpressionModel) -> Expression:
        # Reconstruct expression from stored parameters
        params = model.parameters
        return Expression(
            modality=ExpressionModality(model.modality),
            emotion_category=EmotionCategory(model.emotion_category),
            intensity=model.intensity,
            text_tone=None,  # Would need reverse mapping
            text_formality=params.get("text_formality", 0.5),
            text_verbosity=params.get("text_verbosity", 0.5),
            text_emoji_probability=params.get("text_emoji_probability", 0.1),
            voice_pitch_shift=params.get("voice_pitch_shift", 0.0),
            voice_rate_change=params.get("voice_rate_change", 1.0),
            voice_volume_change=params.get("voice_volume_change", 0.0),
            voice_quality=None,
            face_action_units={
                k.replace("face_au_", ""): v
                for k, v in params.items()
                if k.startswith("face_au_")
            },
            gesture_type=None,
            gesture_amplitude=params.get("gesture_amplitude", 0.5),
            gesture_speed=params.get("gesture_speed", 0.5),
            personality_influence=model.personality_influence,
            context_influence=model.context_influence,
        )


class PostgresEmotionEventRepository(EmotionEventRepository):
    """PostgreSQL implementation of EmotionEventRepository."""

    def __init__(self, session_factory: async_sessionmaker = async_session_maker):
        self.session_factory = session_factory

    async def create(self, event: EmotionEvent) -> EmotionEvent:
        async with self.session_factory() as session:
            model = EmotionEventModel(
                event_id=event.event_id,
                user_id=event.user_id,
                companion_id=event.companion_id,
                event_type=event.event_type,
                payload=event.payload,
                event_metadata=event.metadata,
                timestamp=event.timestamp,
            )
            session.add(model)
            await session.commit()
            return event

    async def get_events(
        self,
        user_id: UUID,
        companion_id: UUID,
        event_types: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[EmotionEvent]:
        async with self.session_factory() as session:
            query = (
                select(EmotionEventModel)
                .where(
                    and_(
                        EmotionEventModel.user_id == user_id,
                        EmotionEventModel.companion_id == companion_id,
                    )
                )
                .order_by(desc(EmotionEventModel.timestamp))
                .limit(limit)
            )
            if event_types:
                query = query.where(EmotionEventModel.event_type.in_(event_types))
            if start_date:
                query = query.where(EmotionEventModel.timestamp >= start_date)
            if end_date:
                query = query.where(EmotionEventModel.timestamp <= end_date)
            result = await session.execute(query)
            return [self._model_to_event(m) for m in result.scalars().all()]

    async def count_events(
        self,
        user_id: UUID,
        companion_id: UUID,
        start_date: Optional[datetime] = None,
    ) -> int:
        async with self.session_factory() as session:
            query = select(func.count(EmotionEventModel.event_id)).where(
                and_(
                    EmotionEventModel.user_id == user_id,
                    EmotionEventModel.companion_id == companion_id,
                )
            )
            if start_date:
                query = query.where(EmotionEventModel.timestamp >= start_date)
            result = await session.execute(query)
            return result.scalar() or 0

    def _model_to_event(self, model: EmotionEventModel) -> EmotionEvent:
        return EmotionEvent(
            event_id=model.event_id,
            user_id=model.user_id,
            companion_id=model.companion_id,
            event_type=model.event_type,
            payload=model.payload,
            metadata=model.event_metadata,
            timestamp=model.timestamp,
        )
