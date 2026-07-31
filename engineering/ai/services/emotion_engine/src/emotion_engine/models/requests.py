"""Request models for Emotion Engine API."""

from typing import Optional, List, Dict, Any, Literal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class EmotionAnalysisRequest(BaseModel):
    """Request for comprehensive emotion analysis of text."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    text: str = Field(..., min_length=1, max_length=10000)
    context: Optional[Dict[str, Any]] = None
    include_valence_arousal: bool = True
    include_appraisal: bool = True
    include_discrete_emotions: bool = True
    language: Optional[str] = "en"
    request_id: Optional[str] = None


class ValenceArousalRequest(BaseModel):
    """Request for valence-arousal prediction."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    text: str = Field(..., min_length=1, max_length=10000)
    context: Optional[Dict[str, Any]] = None
    language: Optional[str] = "en"
    request_id: Optional[str] = None


class AppraisalRequest(BaseModel):
    """Request for cognitive appraisal analysis."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    text: str = Field(..., min_length=1, max_length=10000)
    event_description: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    dimensions: Optional[List[Literal[
        "novelty", "pleasantness", "goal_relevance", "goal_congruence",
        "coping_potential", "norm_compatibility", "self_compatibility",
        "agency", "certainty", "controllability", "expectedness"
    ]]] = None
    language: Optional[str] = "en"
    request_id: Optional[str] = None


class ExpressionRequest(BaseModel):
    """Request for emotional expression generation."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    target_emotion: str = Field(..., description="Target emotion to express")
    intensity: float = Field(default=0.5, ge=0.0, le=1.0, description="Expression intensity 0-1")
    modality: Literal["text", "voice", "facial", "multimodal"] = "text"
    context: Optional[Dict[str, Any]] = None
    personality_traits: Optional[Dict[str, float]] = None
    relationship_context: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


class CalibrationRequest(BaseModel):
    """Request for emotion calibration/regulation."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    current_valence: float = Field(..., ge=-1.0, le=1.0)
    current_arousal: float = Field(..., ge=0.0, le=1.0)
    target_valence: Optional[float] = Field(None, ge=-1.0, le=1.0)
    target_arousal: Optional[float] = Field(None, ge=0.0, le=1.0)
    strategy: Literal[
        "reappraisal", "suppression", "distraction", "acceptance",
        "problem_solving", "social_support", "rumination", "mindfulness"
    ] = "reappraisal"
    context: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


class BatchEmotionRequest(BaseModel):
    """Request for batch emotion analysis."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    texts: List[str] = Field(..., min_length=1, max_length=100)
    include_valence_arousal: bool = True
    include_appraisal: bool = False
    include_discrete_emotions: bool = True
    language: Optional[str] = "en"
    request_id: Optional[str] = None


class StreamEmotionRequest(BaseModel):
    """Request for streaming emotion analysis."""
    
    model_config = ConfigDict(extra="forbid")
    
    user_id: UUID
    companion_id: UUID
    session_id: UUID
    text_chunk: str = Field(..., min_length=1, max_length=5000)
    chunk_index: int = Field(..., ge=0)
    is_final: bool = False
    context: Optional[Dict[str, Any]] = None
    language: Optional[str] = "en"