"""Emotional Expression Service for generating emotional outputs."""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, List
from uuid import UUID

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

from emotion_engine.config import settings
from emotion_engine.models.requests import ExpressionRequest
from emotion_engine.models.responses import ExpressionResponse

logger = logging.getLogger(__name__)


class ExpressionService:
    """Service for generating emotional expressions across modalities."""
    
    # Expression templates by emotion
    TEXT_TEMPLATES = {
        "joy": [
            "I'm so happy that {context}! 😊",
            "That's wonderful news! {context} makes me really glad.",
            "I can't help but smile thinking about {context}.",
        ],
        "sadness": [
            "I feel sad about {context}... 😔",
            "It's disappointing that {context}.",
            "My heart feels heavy with {context}.",
        ],
        "anger": [
            "I'm frustrated that {context}! 😠",
            "That's really upsetting. {context} shouldn't happen.",
            "I feel angry about {context}.",
        ],
        "fear": [
            "I'm worried about {context}... 😰",
            "The thought of {context} scares me.",
            "I feel anxious about {context}.",
        ],
        "surprise": [
            "Wow, I didn't expect {context}! 😮",
            "That's surprising! {context} caught me off guard.",
            "I'm amazed by {context}.",
        ],
        "disgust": [
            "That's gross! {context} really bothers me. 🤢",
            "I find {context} really unpleasant.",
            "Ugh, {context} is just wrong.",
        ],
        "trust": [
            "I feel confident that {context}. 🤝",
            "I trust that {context} will work out.",
            "It's reassuring that {context}.",
        ],
        "anticipation": [
            "I'm looking forward to {context}! 🤞",
            "I can't wait for {context}.",
            "I'm excited about the possibility of {context}.",
        ],
        "love": [
            "I care deeply about {context} ❤️",
            "{context} means so much to me.",
            "My heart is full with {context}.",
        ],
        "neutral": [
            "I understand that {context}.",
            "That's an interesting point about {context}.",
            "I see what you mean about {context}.",
        ],
    }
    
    # Voice parameter mappings
    VOICE_PARAMS = {
        "joy": {"pitch": 1.2, "speed": 1.1, "energy": 0.8, "warmth": 0.9},
        "sadness": {"pitch": 0.8, "speed": 0.9, "energy": 0.3, "warmth": 0.4},
        "anger": {"pitch": 1.1, "speed": 1.2, "energy": 0.9, "warmth": 0.1},
        "fear": {"pitch": 1.15, "speed": 1.15, "energy": 0.4, "warmth": 0.2},
        "surprise": {"pitch": 1.3, "speed": 1.0, "energy": 0.7, "warmth": 0.5},
        "disgust": {"pitch": 0.9, "speed": 0.95, "energy": 0.4, "warmth": 0.1},
        "trust": {"pitch": 1.0, "speed": 1.0, "energy": 0.6, "warmth": 0.8},
        "anticipation": {"pitch": 1.1, "speed": 1.1, "energy": 0.7, "warmth": 0.6},
        "love": {"pitch": 1.05, "speed": 0.95, "energy": 0.5, "warmth": 1.0},
        "neutral": {"pitch": 1.0, "speed": 1.0, "energy": 0.5, "warmth": 0.5},
    }
    
    # Facial expression parameters (for animation)
    FACIAL_PARAMS = {
        "joy": {"smile": 0.9, "eyebrow_raise": 0.3, "eye_open": 0.7, "cheek_raise": 0.8},
        "sadness": {"smile": -0.6, "eyebrow_raise": -0.4, "eye_open": 0.4, "cheek_raise": -0.2},
        "anger": {"smile": -0.7, "eyebrow_raise": -0.8, "eye_open": 0.9, "cheek_raise": 0.1},
        "fear": {"smile": -0.3, "eyebrow_raise": 0.9, "eye_open": 1.0, "cheek_raise": 0.2},
        "surprise": {"smile": 0.1, "eyebrow_raise": 1.0, "eye_open": 1.0, "cheek_raise": 0.3},
        "disgust": {"smile": -0.5, "eyebrow_raise": -0.2, "eye_open": 0.5, "cheek_raise": -0.3},
        "trust": {"smile": 0.4, "eyebrow_raise": 0.2, "eye_open": 0.7, "cheek_raise": 0.3},
        "anticipation": {"smile": 0.3, "eyebrow_raise": 0.5, "eye_open": 0.8, "cheek_raise": 0.2},
        "love": {"smile": 0.8, "eyebrow_raise": 0.3, "eye_open": 0.6, "cheek_raise": 0.7},
        "neutral": {"smile": 0.0, "eyebrow_raise": 0.0, "eye_open": 0.6, "cheek_raise": 0.0},
    }
    
    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.device = settings.emotion_device
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the expression generation model."""
        logger.info("Loading Expression model")
        
        try:
            model_name = settings.expression_model_name
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(model_name).to(self.device)
            self.model.eval()
            
            # Set pad token if not exists
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            self._initialized = True
            logger.info("Expression model loaded successfully")
            
        except Exception as e:
            logger.error("Failed to load Expression model", error=str(e))
            raise
    
    async def generate_expression(self, request: ExpressionRequest) -> ExpressionResponse:
        """Generate emotional expression based on target emotion and modality."""
        start_time = time.time()
        
        if request.modality == "text":
            return await self._generate_text_expression(request, start_time)
        elif request.modality == "voice":
            return await self._generate_voice_expression(request, start_time)
        elif request.modality == "facial":
            return await self._generate_facial_expression(request, start_time)
        elif request.modality == "multimodal":
            return await self._generate_multimodal_expression(request, start_time)
        else:
            raise ValueError(f"Unknown modality: {request.modality}")
    
    async def _generate_text_expression(
        self,
        request: ExpressionRequest,
        start_time: float
    ) -> ExpressionResponse:
        """Generate text-based emotional expression."""
        # Get templates for target emotion
        templates = self.TEXT_TEMPLATES.get(request.target_emotion, self.TEXT_TEMPLATES["neutral"])
        
        # Prepare context
        context_text = ""
        if request.context:
            if "event" in request.context:
                context_text = request.context["event"]
            elif "topic" in request.context:
                context_text = request.context["topic"]
            else:
                context_text = str(request.context)
        
        # Select template based on intensity
        template_idx = min(int(request.intensity * len(templates)), len(templates) - 1)
        template = templates[template_idx]
        
        # Fill template
        expression = template.format(context=context_text) if "{context}" in template else template
        
        # Add personality/style modifications
        if request.personality_traits:
            expression = self._apply_personality_style(expression, request.personality_traits)
        
        # Add relationship context
        if request.relationship_context:
            expression = self._apply_relationship_style(expression, request.relationship_context)
        
        # Generate alternatives
        alternatives = [
            t.format(context=context_text) if "{context}" in t else t
            for i, t in enumerate(templates) if i != template_idx
        ][:3]
        
        processing_time = (time.time() - start_time) * 1000
        
        return ExpressionResponse(
            user_id=request.user_id,
            companion_id=request.companion_id,
            target_emotion=request.target_emotion,
            intensity=request.intensity,
            modality="text",
            expression=expression,
            alternative_expressions=alternatives,
            style_parameters={"intensity": request.intensity},
            processing_time_ms=processing_time,
            request_id=request.request_id,
        )
    
    async def _generate_voice_expression(
        self,
        request: ExpressionRequest,
        start_time: float
    ) -> ExpressionResponse:
        """Generate voice parameters for emotional expression."""
        base_params = self.VOICE_PARAMS.get(request.target_emotion, self.VOICE_PARAMS["neutral"])
        
        # Scale by intensity
        voice_params = {
            k: v * request.intensity + (1 - request.intensity) * self.VOICE_PARAMS["neutral"][k]
            for k, v in base_params.items()
        }
        
        # Apply personality adjustments
        if request.personality_traits:
            extraversion = request.personality_traits.get("extraversion", 0.5)
            neuroticism = request.personality_traits.get("neuroticism", 0.5)
            
            voice_params["energy"] *= (0.7 + 0.6 * extraversion)
            voice_params["pitch"] *= (0.9 + 0.2 * neuroticism)
        
        processing_time = (time.time() - start_time) * 1000
        
        return ExpressionResponse(
            user_id=request.user_id,
            companion_id=request.companion_id,
            target_emotion=request.target_emotion,
            intensity=request.intensity,
            modality="voice",
            expression="",  # Voice doesn't have text expression
            voice_parameters=voice_params,
            processing_time_ms=processing_time,
            request_id=request.request_id,
        )
    
    async def _generate_facial_expression(
        self,
        request: ExpressionRequest,
        start_time: float
    ) -> ExpressionResponse:
        """Generate facial animation parameters for emotional expression."""
        base_params = self.FACIAL_PARAMS.get(request.target_emotion, self.FACIAL_PARAMS["neutral"])
        
        # Scale by intensity
        facial_params = {
            k: v * request.intensity
            for k, v in base_params.items()
        }
        
        # Add blendshapes for animation
        blendshapes = {
            f"blendshape_{k}": v for k, v in facial_params.items()
        }
        
        # Add timing parameters
        blendshapes["duration_ms"] = int(2000 * request.intensity + 500)
        blendshapes["easing"] = "ease_in_out"
        
        processing_time = (time.time() - start_time) * 1000
        
        return ExpressionResponse(
            user_id=request.user_id,
            companion_id=request.companion_id,
            target_emotion=request.target_emotion,
            intensity=request.intensity,
            modality="facial",
            expression="",
            facial_parameters=blendshapes,
            processing_time_ms=processing_time,
            request_id=request.request_id,
        )
    
    async def _generate_multimodal_expression(
        self,
        request: ExpressionRequest,
        start_time: float
    ) -> ExpressionResponse:
        """Generate coordinated multimodal emotional expression."""
        # Generate text
        text_response = await self._generate_text_expression(request, start_time)
        
        # Generate voice
        voice_response = await self._generate_voice_expression(request, start_time)
        
        # Generate facial
        facial_response = await self._generate_facial_expression(request, start_time)
        
        # Combine
        processing_time = (time.time() - start_time) * 1000
        
        return ExpressionResponse(
            user_id=request.user_id,
            companion_id=request.companion_id,
            target_emotion=request.target_emotion,
            intensity=request.intensity,
            modality="multimodal",
            expression=text_response.expression,
            alternative_expressions=text_response.alternative_expressions,
            voice_parameters=voice_response.voice_parameters,
            facial_parameters=facial_response.facial_parameters,
            style_parameters=text_response.style_parameters,
            processing_time_ms=processing_time,
            request_id=request.request_id,
        )
    
    def _apply_personality_style(
        self,
        expression: str,
        personality: Dict[str, float]
    ) -> str:
        """Apply personality traits to expression style."""
        # Openness -> more creative/unconventional language
        if personality.get("openness", 0.5) > 0.7:
            expression = expression.replace("I'm", "I find myself")
            expression = expression.replace("That's", "It strikes me as")
        
        # Conscientiousness -> more structured/precise
        if personality.get("conscientiousness", 0.5) > 0.7:
            expression = expression.replace("!", ".")
        
        # Extraversion -> more enthusiastic
        if personality.get("extraversion", 0.5) > 0.7:
            if not expression.endswith("!"):
                expression += "!"
        
        return expression
    
    def _apply_relationship_style(
        self,
        expression: str,
        relationship: Dict[str, Any]
    ) -> str:
        """Apply relationship context to expression."""
        phase = relationship.get("phase", "acquaintance")
        intimacy = relationship.get("intimacy", 0.3)
        
        if phase == "intimate" and intimacy > 0.7:
            # More vulnerable, personal language
            expression = expression.replace("I feel", "I really feel")
            expression = expression.replace("I'm", "I'm truly")
        elif phase == "professional":
            # More formal
            expression = expression.replace("I'm", "I am")
            expression = expression.replace("can't", "cannot")
        
        return expression
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the service."""
        return {
            "initialized": self._initialized,
            "device": str(self.device),
            "model_loaded": self.model is not None,
            "tokenizer_loaded": self.tokenizer is not None,
            "supported_emotions": list(self.TEXT_TEMPLATES.keys()),
            "supported_modalities": ["text", "voice", "facial", "multimodal"],
        }
    
    async def close(self) -> None:
        """Cleanup resources."""
        self.model = None
        self.tokenizer = None
        self._initialized = False
        logger.info("Expression service closed")


# Singleton instance
_expression_service: Optional[ExpressionService] = None


async def get_expression_service() -> ExpressionService:
    """Get or create Expression service singleton."""
    global _expression_service
    if _expression_service is None:
        _expression_service = ExpressionService()
        await _expression_service.initialize()
    return _expression_service


async def close_expression_service() -> None:
    """Close Expression service."""
    global _expression_service
    if _expression_service:
        await _expression_service.close()
        _expression_service = None