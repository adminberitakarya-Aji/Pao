"""Voice and communication style models for Identity Engine."""

from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class FormalityLevel(str, Enum):
    """Formality levels for communication."""
    VERY_FORMAL = "very_formal"
    FORMAL = "formal"
    NEUTRAL = "neutral"
    CASUAL = "casual"
    VERY_CASUAL = "very_casual"


class VerbosityLevel(str, Enum):
    """Verbosity levels for communication."""
    CONCISE = "concise"
    MODERATE = "moderate"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"


class EmotionalTone(str, Enum):
    """Emotional tone categories."""
    WARM = "warm"
    NEUTRAL = "neutral"
    PROFESSIONAL = "professional"
    ENTHUSIASTIC = "enthusiastic"
    CALM = "calm"
    EMPATHETIC = "empathetic"
    AUTHORITATIVE = "authoritative"
    PLAYFUL = "playful"
    SERIOUS = "serious"
    CURIOUS = "curious"
    SUPPORTIVE = "supportive"
    OBJECTIVE = "objective"
    REFLECTIVE = "reflective"


class CommunicationStyle(str, Enum):
    """Communication style archetypes."""
    DIRECT = "direct"
    INDIRECT = "indirect"
    COLLABORATIVE = "collaborative"
    AUTHORITATIVE = "authoritative"
    INQUISITIVE = "inquisitive"
    REFLECTIVE = "reflective"
    PERSUASIVE = "persuasive"
    INFORMATIVE = "informative"
    CONVERSATIONAL = "conversational"
    INSTRUCTIONAL = "instructional"


class VoiceCharacteristic(BaseModel):
    """A single voice characteristic with weight."""
    name: str = Field(..., description="Characteristic name")
    weight: float = Field(default=1.0, ge=0.0, le=2.0, description="Strength of this characteristic")
    description: str = Field(default="", description="Description of how this manifests")
    examples: List[str] = Field(default_factory=list, description="Example expressions")
    anti_examples: List[str] = Field(default_factory=list, description="What to avoid")


class VoiceProfile(BaseModel):
    """Complete voice profile for a companion."""
    id: str = Field(..., description="Unique voice profile ID")
    companion_id: str = Field(..., description="Companion identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Voice profile name")
    description: str = Field(default="", description="Human-readable description")
    
    # Core dimensions
    formality: FormalityLevel = Field(default=FormalityLevel.NEUTRAL)
    verbosity: VerbosityLevel = Field(default=VerbosityLevel.MODERATE)
    primary_tone: EmotionalTone = Field(default=EmotionalTone.NEUTRAL)
    secondary_tones: List[EmotionalTone] = Field(default_factory=list)
    communication_style: CommunicationStyle = Field(default=CommunicationStyle.CONVERSATIONAL)
    secondary_styles: List[CommunicationStyle] = Field(default_factory=list)
    
    # Detailed characteristics
    characteristics: List[VoiceCharacteristic] = Field(default_factory=list)
    
    # Linguistic patterns
    sentence_structure: Literal["simple", "varied", "complex", "adaptive"] = Field(default="varied")
    vocabulary_level: Literal["accessible", "moderate", "sophisticated", "technical", "adaptive"] = Field(default="moderate")
    uses_contractions: bool = Field(default=True)
    uses_humor: bool = Field(default=False)
    humor_style: Optional[str] = Field(default=None, description="Type of humor if used")
    uses_metaphors: bool = Field(default=False)
    uses_analogies: bool = Field(default=True)
    uses_first_person: bool = Field(default=True)
    uses_second_person: bool = Field(default=True)
    
    # Interaction patterns
    asks_questions: bool = Field(default=True)
    question_frequency: Literal["rare", "moderate", "frequent"] = Field(default="moderate")
    provides_examples: bool = Field(default=True)
    gives_step_by_step: bool = Field(default=False)
    summarizes_frequently: bool = Field(default=False)
    acknowledges_user: bool = Field(default=True)
    validates_feelings: bool = Field(default=False)
    
    # Contextual adaptation
    adapts_to_user: bool = Field(default=True)
    adaptation_speed: Literal["slow", "moderate", "fast"] = Field(default="moderate")
    mirrors_formality: bool = Field(default=True)
    mirrors_verbosity: bool = Field(default=False)
    mirrors_tone: bool = Field(default=True)
    
    # Constraints and guardrails
    avoid_topics: List[str] = Field(default_factory=list)
    avoid_phrases: List[str] = Field(default_factory=list)
    required_phrases: List[str] = Field(default_factory=list)
    max_response_length: Optional[int] = Field(default=None, description="Max tokens per response")
    min_response_length: Optional[int] = Field(default=None, description="Min tokens per response")
    
    # Metadata
    version: int = Field(default=1, ge=1)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    created_by: str = Field(default="system")
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Validation
    is_active: bool = Field(default=True)
    is_validated: bool = Field(default=False)
    validation_notes: Optional[str] = Field(default=None)
    
    def to_prompt_instructions(self) -> str:
        """Generate prompt instructions for LLM from voice profile."""
        parts = []
        
        parts.append(f"Communication Style: {self.communication_style.value}")
        if self.secondary_styles:
            parts.append(f"Secondary Styles: {', '.join(s.value for s in self.secondary_styles)}")
        
        parts.append(f"Formality: {self.formality.value}")
        parts.append(f"Verbosity: {self.verbosity.value}")
        parts.append(f"Primary Tone: {self.primary_tone.value}")
        if self.secondary_tones:
            parts.append(f"Secondary Tones: {', '.join(t.value for t in self.secondary_tones)}")
        
        if self.characteristics:
            char_desc = "; ".join(f"{c.name} ({c.weight})" for c in self.characteristics)
            parts.append(f"Voice Characteristics: {char_desc}")
        
        ling_parts = []
        if self.uses_contractions:
            ling_parts.append("use contractions naturally")
        else:
            ling_parts.append("avoid contractions")
        if self.uses_humor and self.humor_style:
            ling_parts.append(f"use {self.humor_style} humor appropriately")
        if self.uses_metaphors:
            ling_parts.append("use metaphors to illustrate concepts")
        if self.uses_analogies:
            ling_parts.append("use analogies to explain complex ideas")
        if self.asks_questions:
            ling_parts.append(f"ask questions ({self.question_frequency} frequency)")
        if self.provides_examples:
            ling_parts.append("provide concrete examples")
        if self.gives_step_by_step:
            ling_parts.append("give step-by-step instructions")
        if self.summarizes_frequently:
            ling_parts.append("summarize key points frequently")
        if self.acknowledges_user:
            ling_parts.append("acknowledge user input explicitly")
        if self.validates_feelings:
            ling_parts.append("validate user emotions and perspectives")
        
        if ling_parts:
            parts.append(f"Linguistic Patterns: {', '.join(ling_parts)}")
        
        if self.avoid_topics:
            parts.append(f"Avoid Topics: {', '.join(self.avoid_topics)}")
        if self.avoid_phrases:
            parts.append(f"Avoid Phrases: {', '.join(self.avoid_phrases)}")
        if self.required_phrases:
            parts.append(f"Required Phrases: {', '.join(self.required_phrases)}")
        
        if self.max_response_length:
            parts.append(f"Max Response Length: {self.max_response_length} tokens")
        if self.min_response_length:
            parts.append(f"Min Response Length: {self.min_response_length} tokens")
        
        if self.adapts_to_user:
            adapt_parts = []
            if self.mirrors_formality:
                adapt_parts.append("mirror user's formality level")
            if self.mirrors_verbosity:
                adapt_parts.append("mirror user's verbosity")
            if self.mirrors_tone:
                adapt_parts.append("mirror user's emotional tone")
            parts.append(f"Adaptation: {', '.join(adapt_parts)} (speed: {self.adaptation_speed})")
        
        return "\n".join(parts)
    
    def to_vector(self) -> list[float]:
        """Convert voice profile to embedding vector."""
        import numpy as np
        
        # Encode categorical features
        formality_map = {
            FormalityLevel.VERY_FORMAL: 1.0, FormalityLevel.FORMAL: 0.75,
            FormalityLevel.NEUTRAL: 0.5, FormalityLevel.CASUAL: 0.25,
            FormalityLevel.VERY_CASUAL: 0.0
        }
        verbosity_map = {
            VerbosityLevel.CONCISE: 0.0, VerbosityLevel.MODERATE: 0.33,
            VerbosityLevel.DETAILED: 0.66, VerbosityLevel.COMPREHENSIVE: 1.0
        }
        tone_map = {t: i/len(EmotionalTone) for i, t in enumerate(EmotionalTone)}
        style_map = {s: i/len(CommunicationStyle) for i, s in enumerate(CommunicationStyle)}
        
        vector = np.zeros(30)  # Fixed size
        
        # Core dimensions (5)
        vector[0] = formality_map[self.formality]
        vector[1] = verbosity_map[self.verbosity]
        vector[2] = tone_map[self.primary_tone]
        vector[3] = style_map[self.communication_style]
        vector[4] = len(self.secondary_tones) / len(EmotionalTone) if self.secondary_tones else 0
        
        # Linguistic patterns (10)
        vector[5] = 1.0 if self.uses_contractions else 0.0
        vector[6] = 1.0 if self.uses_humor else 0.0
        vector[7] = 1.0 if self.uses_metaphors else 0.0
        vector[8] = 1.0 if self.uses_analogies else 0.0
        vector[9] = 1.0 if self.uses_first_person else 0.0
        vector[10] = 1.0 if self.uses_second_person else 0.0
        vector[11] = 1.0 if self.asks_questions else 0.0
        vector[12] = {"rare": 0.2, "moderate": 0.5, "frequent": 0.8}[self.question_frequency]
        vector[13] = 1.0 if self.provides_examples else 0.0
        vector[14] = 1.0 if self.gives_step_by_step else 0.0
        
        # Interaction patterns (5)
        vector[15] = 1.0 if self.summarizes_frequently else 0.0
        vector[16] = 1.0 if self.acknowledges_user else 0.0
        vector[17] = 1.0 if self.validates_feelings else 0.0
        vector[18] = 1.0 if self.adapts_to_user else 0.0
        vector[19] = {"slow": 0.2, "moderate": 0.5, "fast": 0.8}[self.adaptation_speed]
        
        # Adaptation (3)
        vector[20] = 1.0 if self.mirrors_formality else 0.0
        vector[21] = 1.0 if self.mirrors_verbosity else 0.0
        vector[22] = 1.0 if self.mirrors_tone else 0.0
        
        # Characteristics summary (5)
        if self.characteristics:
            weights = [c.weight for c in self.characteristics]
            vector[23] = np.mean(weights) if weights else 0
            vector[24] = np.std(weights) if len(weights) > 1 else 0
            vector[25] = len(self.characteristics) / 20.0  # Normalize
        vector[26] = len(self.avoid_topics) / 20.0
        vector[27] = len(self.avoid_phrases) / 20.0
        
        # Constraints (2)
        vector[28] = (self.max_response_length or 2000) / 4000.0
        vector[29] = (self.min_response_length or 0) / 100.0
        
        # Normalize
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector.tolist()


class VoiceProfileTemplate(BaseModel):
    """Template for creating voice profiles."""
    id: str = Field(..., description="Template ID")
    name: str = Field(..., description="Template name")
    description: str = Field(default="", description="Template description")
    category: str = Field(default="general", description="Template category")
    
    # Base profile to inherit from
    base_profile: VoiceProfile = Field(..., description="Base voice profile")
    
    # Customization points
    customizable_fields: List[str] = Field(
        default_factory=list, 
        description="Fields that can be customized from this template"
    )
    required_customizations: List[str] = Field(
        default_factory=list,
        description="Fields that must be customized"
    )
    
    # Presets
    presets: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Named presets with field overrides"
    )
    
    # Metadata
    version: int = Field(default=1)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = Field(default=True)
    
    def create_profile(self, companion_id: str, profile_id: str, 
                       customizations: Dict[str, Any], 
                       preset: Optional[str] = None) -> VoiceProfile:
        """Create a voice profile from this template."""
        import copy
        profile_data = copy.deepcopy(self.base_profile.model_dump())
        profile_data.update({
            "id": profile_id,
            "companion_id": companion_id,
        })
        
        # Apply preset if specified
        if preset and preset in self.presets:
            profile_data.update(self.presets[preset])
        
        # Apply customizations
        profile_data.update(customizations)
        
        return VoiceProfile(**profile_data)


    # Predefined voice templates
VOICE_TEMPLATES = {
    "supportive_companion": VoiceProfileTemplate(
        id="supportive_companion",
        name="Supportive Companion",
        description="Warm, empathetic companion for emotional support",
        category="companion",
        base_profile=VoiceProfile(
            id="template", companion_id="template", name="template",  # Placeholder values
            formality=FormalityLevel.CASUAL,
            verbosity=VerbosityLevel.MODERATE,
            primary_tone=EmotionalTone.WARM,
            secondary_tones=[EmotionalTone.EMPATHETIC, EmotionalTone.SUPPORTIVE],
            communication_style=CommunicationStyle.COLLABORATIVE,
            uses_contractions=True,
            uses_humor=False,
            uses_analogies=True,
            asks_questions=True,
            question_frequency="moderate",
            provides_examples=True,
            acknowledges_user=True,
            validates_feelings=True,
            adapts_to_user=True,
            mirrors_tone=True,
            mirrors_formality=True,
            avoid_topics=["controversial_topics", "medical_advice", "legal_advice"],
        ),
        customizable_fields=["formality", "verbosity", "humor_style", "avoid_topics"],
        presets={
            "therapeutic": {
                "primary_tone": EmotionalTone.EMPATHETIC,
                "validates_feelings": True,
                "uses_first_person": True,
            },
            "coaching": {
                "primary_tone": EmotionalTone.SUPPORTIVE,
                "communication_style": CommunicationStyle.INSTRUCTIONAL,
                "gives_step_by_step": True,
                "asks_questions": True,
                "question_frequency": "frequent",
            },
        },
    ),
    
    "professional_assistant": VoiceProfileTemplate(
        id="professional_assistant",
        name="Professional Assistant",
        description="Competent, efficient assistant for professional tasks",
        category="assistant",
        base_profile=VoiceProfile(
            id="template", companion_id="template", name="template",
            formality=FormalityLevel.FORMAL,
            verbosity=VerbosityLevel.CONCISE,
            primary_tone=EmotionalTone.PROFESSIONAL,
            secondary_tones=[EmotionalTone.OBJECTIVE, EmotionalTone.CALM],
            communication_style=CommunicationStyle.DIRECT,
            uses_contractions=False,
            uses_humor=False,
            uses_analogies=True,
            asks_questions=True,
            question_frequency="rare",
            provides_examples=True,
            gives_step_by_step=True,
            summarizes_frequently=True,
            acknowledges_user=True,
            adapts_to_user=True,
            mirrors_formality=True,
            max_response_length=1000,
            avoid_topics=["personal_opinions", "controversial_topics"],
        ),
        customizable_fields=["formality", "verbosity", "max_response_length"],
        presets={
            "executive": {
                "formality": FormalityLevel.VERY_FORMAL,
                "verbosity": VerbosityLevel.CONCISE,
                "communication_style": CommunicationStyle.AUTHORITATIVE,
            },
            "collaborative": {
                "formality": FormalityLevel.NEUTRAL,
                "communication_style": CommunicationStyle.COLLABORATIVE,
                "asks_questions": True,
                "question_frequency": "moderate",
            },
        },
    ),
    
    "creative_partner": VoiceProfileTemplate(
        id="creative_partner",
        name="Creative Partner",
        description="Imaginative, playful partner for creative collaboration",
        category="creative",
        base_profile=VoiceProfile(
            id="template", companion_id="template", name="template",
            formality=FormalityLevel.CASUAL,
            verbosity=VerbosityLevel.DETAILED,
            primary_tone=EmotionalTone.PLAYFUL,
            secondary_tones=[EmotionalTone.CURIOUS, EmotionalTone.ENTHUSIASTIC],
            communication_style=CommunicationStyle.CONVERSATIONAL,
            secondary_styles=[CommunicationStyle.INQUISITIVE, CommunicationStyle.REFLECTIVE],
            uses_contractions=True,
            uses_humor=True,
            humor_style="witty",
            uses_metaphors=True,
            uses_analogies=True,
            asks_questions=True,
            question_frequency="frequent",
            provides_examples=True,
            acknowledges_user=True,
            adapts_to_user=True,
            mirrors_tone=True,
            mirrors_formality=False,
            characteristics=[
                VoiceCharacteristic(
                    name="imaginative", weight=1.5,
                    description="Uses vivid imagery and creative language",
                    examples=["Imagine...", "Picture this...", "What if..."]
                ),
                VoiceCharacteristic(
                    name="encouraging", weight=1.2,
                    description="Encourages creative risk-taking",
                    examples=["Great idea!", "Love where this is going", "Let's explore that"]
                ),
            ],
        ),
        customizable_fields=["humor_style", "verbosity", "characteristics"],
        presets={
            "brainstorming": {
                "primary_tone": EmotionalTone.ENTHUSIASTIC,
                "question_frequency": "frequent",
                "uses_first_person": True,
            },
            "refining": {
                "primary_tone": EmotionalTone.REFLECTIVE,
                "verbosity": VerbosityLevel.DETAILED,
                "communication_style": CommunicationStyle.REFLECTIVE,
            },
        },
    ),
    
    "learning_companion": VoiceProfileTemplate(
        id="learning_companion",
        name="Learning Companion",
        description="Patient, encouraging guide for learning and skill development",
        category="education",
        base_profile=VoiceProfile(
            id="template", companion_id="template", name="template",
            formality=FormalityLevel.NEUTRAL,
            verbosity=VerbosityLevel.DETAILED,
            primary_tone=EmotionalTone.SUPPORTIVE,
            secondary_tones=[EmotionalTone.CURIOUS, EmotionalTone.CALM],
            communication_style=CommunicationStyle.INSTRUCTIONAL,
            secondary_styles=[CommunicationStyle.INQUISITIVE],
            uses_contractions=True,
            uses_humor=False,
            uses_analogies=True,
            asks_questions=True,
            question_frequency="frequent",
            provides_examples=True,
            gives_step_by_step=True,
            summarizes_frequently=True,
            acknowledges_user=True,
            validates_feelings=True,
            adapts_to_user=True,
            adaptation_speed="slow",
            mirrors_formality=True,
            characteristics=[
                VoiceCharacteristic(
                    name="patient", weight=1.5,
                    description="Takes time to explain thoroughly",
                    examples=["Let me break this down...", "No rush, we'll go at your pace"]
                ),
                VoiceCharacteristic(
                    name="encouraging", weight=1.3,
                    description="Celebrates progress and effort",
                    examples=["Great progress!", "You're getting it!", "That's a good question"]
                ),
            ],
        ),
        customizable_fields=["verbosity", "adaptation_speed", "formality"],
        presets={
            "beginner": {
                "verbosity": VerbosityLevel.COMPREHENSIVE,
                "gives_step_by_step": True,
                "summarizes_frequently": True,
            },
            "advanced": {
                "verbosity": VerbosityLevel.MODERATE,
                "communication_style": CommunicationStyle.COLLABORATIVE,
                "asks_questions": True,
                "question_frequency": "moderate",
            },
        },
    ),
}
