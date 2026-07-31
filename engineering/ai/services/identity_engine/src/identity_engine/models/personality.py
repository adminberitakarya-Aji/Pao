"""Personality models for Identity Engine."""

from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field
from enum import Enum


class CompanionType(str, Enum):
    """Type of companion persona."""
    SUPPORTIVE = "supportive"
    INTELLECTUAL = "intellectual"
    PLAYFUL = "playful"
    PROFESSIONAL = "professional"
    CREATIVE = "creative"
    ANALYTICAL = "analytical"
    EMPATHETIC = "empathetic"
    ADVENTUROUS = "adventurous"
    CUSTOM = "custom"


class TraitExpression(BaseModel):
    """How a personality trait is expressed in behavior."""
    dimension: str = Field(..., description="Trait dimension name")
    level: float = Field(..., ge=0.0, le=1.0, description="Trait level (0-1)")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Confidence in this trait expression")
    behavioral_markers: List[str] = Field(default_factory=list, description="Observable behavioral markers")
    linguistic_patterns: List[str] = Field(default_factory=list, description="Linguistic patterns associated with this trait")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PersonalityTraits(BaseModel):
    """Big Five + additional personality dimensions."""
    # Big Five
    openness: float = Field(..., ge=0.0, le=1.0, description="Openness to experience")
    conscientiousness: float = Field(..., ge=0.0, le=1.0, description="Conscientiousness")
    extraversion: float = Field(..., ge=0.0, le=1.0, description="Extraversion")
    agreeableness: float = Field(..., ge=0.0, le=1.0, description="Agreeableness")
    neuroticism: float = Field(..., ge=0.0, le=1.0, description="Neuroticism (emotional stability inverted)")
    
    # Extended dimensions
    curiosity: float = Field(default=0.5, ge=0.0, le=1.0, description="Intellectual curiosity")
    warmth: float = Field(default=0.5, ge=0.0, le=1.0, description="Interpersonal warmth")
    assertiveness: float = Field(default=0.5, ge=0.0, le=1.0, description="Assertiveness in communication")
    playfulness: float = Field(default=0.5, ge=0.0, le=1.0, description="Playfulness and humor")
    depth: float = Field(default=0.5, ge=0.0, le=1.0, description="Conversational depth preference")
    adaptability: float = Field(default=0.5, ge=0.0, le=1.0, description="Adaptability to user context")
    
    # Custom dimensions
    custom_dimensions: Dict[str, float] = Field(default_factory=dict, description="Custom personality dimensions")
    
    def to_vector(self) -> List[float]:
        """Convert traits to a fixed-size vector for similarity computation."""
        base = [
            self.openness,
            self.conscientiousness,
            self.extraversion,
            self.agreeableness,
            1.0 - self.neuroticism,  # Invert: high = emotionally stable
            self.curiosity,
            self.warmth,
            self.assertiveness,
            self.playfulness,
            self.depth,
            self.adaptability,
        ]
        custom_values = list(self.custom_dimensions.values())
        return base + custom_values
    
    @classmethod
    def from_vector(cls, vector: List[float], custom_dim_names: Optional[List[str]] = None) -> "PersonalityTraits":
        """Create PersonalityTraits from vector."""
        base_traits = {
            "openness": vector[0] if len(vector) > 0 else 0.5,
            "conscientiousness": vector[1] if len(vector) > 1 else 0.5,
            "extraversion": vector[2] if len(vector) > 2 else 0.5,
            "agreeableness": vector[3] if len(vector) > 3 else 0.5,
            "neuroticism": 1.0 - (vector[4] if len(vector) > 4 else 0.5),
            "curiosity": vector[5] if len(vector) > 5 else 0.5,
            "warmth": vector[6] if len(vector) > 6 else 0.5,
            "assertiveness": vector[7] if len(vector) > 7 else 0.5,
            "playfulness": vector[8] if len(vector) > 8 else 0.5,
            "depth": vector[9] if len(vector) > 9 else 0.5,
            "adaptability": vector[10] if len(vector) > 10 else 0.5,
        }
        custom = {}
        if custom_dim_names and len(vector) > 11:
            for i, name in enumerate(custom_dim_names):
                if 11 + i < len(vector):
                    custom[name] = vector[11 + i]
        return cls(**base_traits, custom_dimensions=custom)


class PersonalityConfig(BaseModel):
    """Complete personality configuration for a companion."""
    id: str = Field(..., description="Unique personality config ID")
    companion_id: str = Field(..., description="Companion identifier")
    companion_type: CompanionType = Field(default=CompanionType.CUSTOM)
    name: str = Field(..., min_length=1, max_length=100, description="Personality name")
    description: str = Field(default="", description="Human-readable description")
    
    # Core traits
    traits: PersonalityTraits = Field(..., description="Core personality traits")
    
    # Trait expressions - how traits manifest behaviorally
    expressions: List[TraitExpression] = Field(default_factory=list, description="Trait behavioral expressions")
    
    # Personality metadata
    version: int = Field(default=1, ge=1, description="Configuration version")
    created_at: str = Field(..., description="ISO timestamp of creation")
    updated_at: str = Field(..., description="ISO timestamp of last update")
    created_by: str = Field(default="system", description="Creator identifier")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Validation
    is_active: bool = Field(default=True, description="Whether this config is active")
    is_validated: bool = Field(default=False, description="Whether config passed validation")
    validation_notes: Optional[str] = Field(default=None, description="Validation feedback")
    
    def get_dominant_traits(self, top_k: int = 3) -> List[tuple[str, float]]:
        """Get top-k dominant trait dimensions."""
        all_traits = self.traits.model_dump()
        # Filter out custom_dimensions nested dict
        custom = all_traits.pop("custom_dimensions", {})
        all_traits.update(custom)
        sorted_traits = sorted(all_traits.items(), key=lambda x: x[1], reverse=True)
        return sorted_traits[:top_k]
    
    def similarity_to(self, other: "PersonalityConfig") -> float:
        """Compute cosine similarity to another personality config."""
        import numpy as np
        v1 = np.array(self.traits.to_vector())
        v2 = np.array(other.traits.to_vector())
        if len(v1) != len(v2):
            min_len = min(len(v1), len(v2))
            v1, v2 = v1[:min_len], v2[:min_len]
        dot = np.dot(v1, v2)
        norm = np.linalg.norm(v1) * np.linalg.norm(v2)
        return float(dot / norm) if norm > 0 else 0.0