"""Response models for Emotion Engine API."""

from typing import Optional, List, Dict, Any, Literal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class ValenceArousalResponse(BaseModel):
    """Response for valence-arousal prediction."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    valence: float = Field(..., ge=-1.0, le=1.0, description="Valence: -1 (negative) to 1 (positive)")
    arousal: float = Field(..., ge=0.0, le=1.0, description="Arousal: 0 (calm) to 1 (excited)")
    confidence: float = Field(..., ge=0.0, le=1.0)
    quadrant: Literal["positive_high", "positive_low", "negative_high", "negative_low"]
    processing_time_ms: float
    request_id: Optional[str] = None


class DiscreteEmotion(BaseModel):
    """Discrete emotion with intensity."""
    
    model_config = ConfigDict(extra="forbid")
    
    emotion: str
    intensity: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)


class AppraisalDimension(BaseModel):
    """Single appraisal dimension score."""
    
    model_config = ConfigDict(extra="forbid")
    
    dimension: str
    score: float = Field(..., ge=-1.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    label: str


class AppraisalResponse(BaseModel):
    """Response for cognitive appraisal analysis."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    dimensions: List[AppraisalDimension]
    primary_appraisal: Dict[str, float]
    secondary_appraisal: Dict[str, float]
    coping_potential: float = Field(..., ge=0.0, le=1.0)
    processing_time_ms: float
    request_id: Optional[str] = None


class EmotionAnalysisResponse(BaseModel):
    """Comprehensive emotion analysis response."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    valence_arousal: ValenceArousalResponse
    discrete_emotions: List[DiscreteEmotion]
    appraisal: Optional[AppraisalResponse] = None
    dominant_emotion: str
    emotional_complexity: float = Field(..., ge=0.0, le=1.0)
    processing_time_ms: float
    request_id: Optional[str] = None


class ExpressionResponse(BaseModel):
    """Response for emotional expression generation."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    target_emotion: str
    intensity: float
    modality: str
    expression: str = Field(..., description="Generated emotional expression")
    alternative_expressions: List[str] = []
    style_parameters: Dict[str, float] = {}
    voice_parameters: Optional[Dict[str, float]] = None
    facial_parameters: Optional[Dict[str, Any]] = None
    processing_time_ms: float
    request_id: Optional[str] = None


class CalibrationStrategy(BaseModel):
    """Regulation strategy recommendation."""
    
    model_config = ConfigDict(extra="forbid")
    
    strategy: str
    description: str
    effectiveness: float = Field(..., ge=0.0, le=1.0)
    steps: List[str] = []


class CalibrationResponse(BaseModel):
    """Response for emotion calibration/regulation."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    current_state: Dict[str, float]
    target_state: Dict[str, float]
    recommended_strategy: CalibrationStrategy
    alternative_strategies: List[CalibrationStrategy] = []
    expected_trajectory: List[Dict[str, float]] = []
    regulation_difficulty: float = Field(..., ge=0.0, le=1.0)
    processing_time_ms: float
    request_id: Optional[str] = None


class BatchEmotionResponse(BaseModel):
    """Response for batch emotion analysis."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    results: List[EmotionAnalysisResponse]
    aggregate_stats: Dict[str, float] = {}
    processing_time_ms: float
    request_id: Optional[str] = None


class StreamEmotionResponse(BaseModel):
    """Response for streaming emotion analysis."""
    
    model_config = ConfigDict(extra="forbid")
    
    session_id: UUID
    chunk_index: int
    valence: float
    arousal: float
    dominant_emotion: str
    discrete_emotions: List[DiscreteEmotion]
    is_final: bool
    confidence: float
    processing_time_ms: float


class HealthResponse(BaseModel):
    """Health check response."""
    
    model_config = ConfigDict(extra="forbid")
    
    service: str = "emotion-engine"
    version: str = "0.1.0"
    status: Literal["healthy", "degraded", "unhealthy"] = "healthy"
    checks: Dict[str, bool] = {}
    models_loaded: Dict[str, bool] = {}
    processing_time_ms: float = 0.0


class ErrorResponse(BaseModel):
    """Error response."""
    
    model_config = ConfigDict(extra="forbid")
    
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None