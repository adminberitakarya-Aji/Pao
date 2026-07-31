"""Valence-Arousal Service for emotion dimensional analysis."""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID

import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer

from emotion_engine.config import settings
from emotion_engine.models.requests import ValenceArousalRequest, EmotionAnalysisRequest
from emotion_engine.models.responses import ValenceArousalResponse, EmotionAnalysisResponse

logger = logging.getLogger(__name__)


class ValenceArousalService:
    """Service for predicting valence and arousal from text using transformer models."""
    
    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.sentence_encoder = None
        self.valence_head = None
        self.arousal_head = None
        self.device = settings.emotion_device
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the valence-arousal model."""
        logger.info("Loading Valence-Arousal model")
        
        try:
            # Load base transformer model
            model_name = settings.valence_arousal_model_name
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name).to(self.device)
            self.model.eval()
            
            # Load sentence encoder for context embeddings
            self.sentence_encoder = SentenceTransformer(
                settings.sentence_encoder_model,
                device=self.device
            )
            
            # Initialize regression heads (would be fine-tuned in production)
            hidden_size = self.model.config.hidden_size
            self.valence_head = torch.nn.Linear(hidden_size, 1).to(self.device)
            self.arousal_head = torch.nn.Linear(hidden_size, 1).to(self.device)
            
            # Load fine-tuned weights if available
            if settings.valence_arousal_weights_path:
                await self._load_weights()
            
            self._initialized = True
            logger.info("Valence-Arousal model loaded successfully")
            
        except Exception as e:
            logger.error("Failed to load Valence-Arousal model", error=str(e))
            raise
    
    async def _load_weights(self) -> None:
        """Load fine-tuned regression head weights."""
        try:
            checkpoint = torch.load(
                settings.valence_arousal_weights_path,
                map_location=self.device
            )
            self.valence_head.load_state_dict(checkpoint["valence_head"])
            self.arousal_head.load_state_dict(checkpoint["arousal_head"])
            logger.info("Loaded fine-tuned VA weights")
        except Exception as e:
            logger.warning("Could not load fine-tuned weights, using random initialization", error=str(e))
    
    async def predict_valence_arousal(self, request: ValenceArousalRequest) -> ValenceArousalResponse:
        """Predict valence and arousal for given text."""
        start_time = time.time()
        
        # Preprocess text
        inputs = self.tokenizer(
            request.text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        ).to(self.device)
        
        # Get embeddings
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Use CLS token representation
            cls_embedding = outputs.last_hidden_state[:, 0, :]
            
            # Predict valence and arousal
            valence_logit = self.valence_head(cls_embedding).squeeze()
            arousal_logit = self.arousal_head(cls_embedding).squeeze()
            
            # Apply sigmoid/tanh to get proper ranges
            valence = torch.tanh(valence_logit).item()  # [-1, 1]
            arousal = torch.sigmoid(arousal_logit).item()  # [0, 1]
        
        # Calculate confidence based on embedding norms
        embedding_norm = cls_embedding.norm().item()
        confidence = min(1.0, embedding_norm / 10.0)  # Normalized confidence
        
        # Get discrete emotion labels based on VA space
        discrete_emotions = self._va_to_discrete_emotions(valence, arousal)
        
        # Context adjustments if provided
        if request.context:
            valence, arousal, discrete_emotions = self._apply_context_adjustments(
                valence, arousal, discrete_emotions, request.context
            )
        
        processing_time = (time.time() - start_time) * 1000
        
        return ValenceArousalResponse(
            user_id=request.user_id,
            companion_id=request.companion_id,
            valence=valence,
            arousal=arousal,
            confidence=confidence,
            discrete_emotions=discrete_emotions,
            processing_time_ms=processing_time,
            request_id=request.request_id,
        )
    
    async def predict_batch(
        self,
        texts: List[str],
        user_id: UUID,
        companion_id: UUID,
    ) -> List[Tuple[float, float, float]]:
        """Batch prediction for multiple texts."""
        results = []
        
        # Tokenize batch
        inputs = self.tokenizer(
            texts,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            cls_embeddings = outputs.last_hidden_state[:, 0, :]
            
            valence_logits = self.valence_head(cls_embeddings).squeeze(-1)
            arousal_logits = self.arousal_head(cls_embeddings).squeeze(-1)
            
            valences = torch.tanh(valence_logits).cpu().numpy()
            arousals = torch.sigmoid(arousal_logits).cpu().numpy()
        
        for i in range(len(texts)):
            valence = float(valences[i])
            arousal = float(arousals[i])
            confidence = min(1.0, cls_embeddings[i].norm().item() / 10.0)
            results.append((valence, arousal, confidence))
        
        return results
    
    def _va_to_discrete_emotions(self, valence: float, arousal: float) -> Dict[str, float]:
        """Map valence-arousal to discrete emotion probabilities using circumplex model."""
        # Russell's circumplex model regions
        emotions = {}
        
        # High arousal, positive valence
        if valence > 0.3 and arousal > 0.5:
            emotions["excitement"] = min(1.0, (valence + arousal) / 2)
            emotions["joy"] = valence * 0.8
            emotions["anticipation"] = arousal * 0.6
        
        # High arousal, negative valence
        elif valence < -0.3 and arousal > 0.5:
            emotions["anger"] = min(1.0, (-valence + arousal) / 2)
            emotions["fear"] = (-valence) * 0.7
            emotions["distress"] = arousal * 0.8
        
        # Low arousal, positive valence
        elif valence > 0.3 and arousal < 0.5:
            emotions["contentment"] = valence * 0.9
            emotions["calmness"] = (1 - arousal) * 0.8
            emotions["relief"] = valence * 0.5
        
        # Low arousal, negative valence
        elif valence < -0.3 and arousal < 0.5:
            emotions["sadness"] = -valence * 0.8
            emotions["boredom"] = (1 - arousal) * 0.6
            emotions["depression"] = (-valence) * 0.7
        
        # Neutral region
        else:
            emotions["neutral"] = 1.0 - (abs(valence) + arousal) / 2
        
        # Normalize
        total = sum(emotions.values())
        if total > 0:
            emotions = {k: v / total for k, v in emotions.items()}
        
        return emotions
    
    def _apply_context_adjustments(
        self,
        valence: float,
        arousal: float,
        emotions: Dict[str, float],
        context: Dict[str, Any]
    ) -> Tuple[float, float, Dict[str, float]]:
        """Apply context-based adjustments to emotion predictions."""
        adjusted_valence = valence
        adjusted_arousal = arousal
        adjusted_emotions = emotions.copy()
        
        # Relationship context adjustments
        if "relationship_phase" in context:
            phase = context["relationship_phase"]
            if phase == "intimate":
                adjusted_valence = min(1.0, adjusted_valence + 0.1)
                adjusted_arousal = min(1.0, adjusted_arousal + 0.05)
            elif phase == "conflict":
                adjusted_valence = max(-1.0, adjusted_valence - 0.15)
                adjusted_arousal = min(1.0, adjusted_arousal + 0.1)
        
        # User personality adjustments
        if "user_personality" in context:
            personality = context["user_personality"]
            neuroticism = personality.get("neuroticism", 0.5)
            extraversion = personality.get("extraversion", 0.5)
            
            if neuroticism > 0.7:
                adjusted_arousal = min(1.0, adjusted_arousal + 0.1)
                adjusted_valence = max(-1.0, adjusted_valence - 0.05)
            
            if extraversion > 0.7:
                adjusted_arousal = min(1.0, adjusted_arousal + 0.05)
        
        # Recalculate discrete emotions with adjusted values
        adjusted_emotions = self._va_to_discrete_emotions(adjusted_valence, adjusted_arousal)
        
        return adjusted_valence, adjusted_arousal, adjusted_emotions
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the service."""
        return {
            "initialized": self._initialized,
            "device": str(self.device),
            "model_loaded": self.model is not None,
            "tokenizer_loaded": self.tokenizer is not None,
        }
    
    async def close(self) -> None:
        """Cleanup resources."""
        self.model = None
        self.tokenizer = None
        self.sentence_encoder = None
        self.valence_head = None
        self.arousal_head = None
        self._initialized = False
        logger.info("Valence-Arousal service closed")


# Singleton instance
_valence_arousal_service: Optional[ValenceArousalService] = None


async def get_valence_arousal_service() -> ValenceArousalService:
    """Get or create Valence-Arousal service singleton."""
    global _valence_arousal_service
    if _valence_arousal_service is None:
        _valence_arousal_service = ValenceArousalService()
        await _valence_arousal_service.initialize()
    return _valence_arousal_service


async def close_valence_arousal_service() -> None:
    """Close Valence-Arousal service."""
    global _valence_arousal_service
    if _valence_arousal_service:
        await _valence_arousal_service.close()
        _valence_arousal_service = None