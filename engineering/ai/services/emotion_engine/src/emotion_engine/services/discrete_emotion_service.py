"""Discrete Emotion Service for categorical emotion classification."""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, List
from uuid import UUID

import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from emotion_engine.config import settings
from emotion_engine.models.requests import EmotionAnalysisRequest, BatchEmotionRequest
from emotion_engine.models.responses import EmotionAnalysisResponse, BatchEmotionResponse

logger = logging.getLogger(__name__)


class DiscreteEmotionService:
    """Service for discrete emotion classification using transformer models."""
    
    # Ekman's 6 basic emotions + extended set
    EMOTION_LABELS = [
        "joy", "sadness", "anger", "fear", "surprise", "disgust",
        "trust", "anticipation", "neutral"
    ]
    
    # Plutchik's wheel emotions (extended)
    EXTENDED_LABELS = [
        "joy", "sadness", "anger", "fear", "surprise", "disgust",
        "trust", "anticipation", "neutral",
        "love", "optimism", "pessimism", "submission", "dominance",
        "awe", "contempt", "remorse", "aggressiveness", "gratitude",
        "pride", "shame", "envy", "hope", "curiosity", "confusion",
        "excitement", "anxiety", "relief", "disappointment", "satisfaction"
    ]
    
    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.device = settings.emotion_device
        self._initialized = False
        self.label_map = {i: label for i, label in enumerate(self.EMOTION_LABELS)}
    
    async def initialize(self) -> None:
        """Initialize the discrete emotion classification model."""
        logger.info("Loading Discrete Emotion model")
        
        try:
            model_name = settings.discrete_emotion_model_name
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                num_labels=len(self.EMOTION_LABELS),
                problem_type="multi_label_classification"
            ).to(self.device)
            self.model.eval()
            
            self._initialized = True
            logger.info("Discrete Emotion model loaded successfully")
            
        except Exception as e:
            logger.error("Failed to load Discrete Emotion model", error=str(e))
            raise
    
    async def predict_emotions(self, request: EmotionAnalysisRequest) -> EmotionAnalysisResponse:
        """Predict discrete emotions for given text."""
        start_time = time.time()
        
        # Preprocess text
        inputs = self.tokenizer(
            request.text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        ).to(self.device)
        
        # Predict
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits.squeeze()
            probabilities = torch.sigmoid(logits).cpu().numpy()
        
        # Map to labels
        emotion_probs = {
            self.label_map[i]: float(prob)
            for i, prob in enumerate(probabilities)
            if prob > 0.01  # Filter very low probabilities
        }
        
        # Sort by probability
        emotion_probs = dict(sorted(emotion_probs.items(), key=lambda x: x[1], reverse=True))
        
        # Get top emotion
        top_emotion = list(emotion_probs.keys())[0] if emotion_probs else "neutral"
        top_confidence = list(emotion_probs.values())[0] if emotion_probs else 0.0
        
        processing_time = (time.time() - start_time) * 1000
        
        return EmotionAnalysisResponse(
            user_id=request.user_id,
            companion_id=request.companion_id,
            top_emotion=top_emotion,
            confidence=top_confidence,
            emotion_probabilities=emotion_probs,
            processing_time_ms=processing_time,
            request_id=request.request_id,
        )
    
    async def predict_batch(self, request: BatchEmotionRequest) -> BatchEmotionResponse:
        """Batch emotion prediction."""
        start_time = time.time()
        results = []
        
        # Tokenize batch
        inputs = self.tokenizer(
            request.texts,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probabilities = torch.sigmoid(logits).cpu().numpy()
        
        for i, text in enumerate(request.texts):
            emotion_probs = {
                self.label_map[j]: float(prob)
                for j, prob in enumerate(probabilities[i])
                if prob > 0.01
            }
            emotion_probs = dict(sorted(emotion_probs.items(), key=lambda x: x[1], reverse=True))
            
            top_emotion = list(emotion_probs.keys())[0] if emotion_probs else "neutral"
            top_confidence = list(emotion_probs.values())[0] if emotion_probs else 0.0
            
            results.append({
                "text": text,
                "top_emotion": top_emotion,
                "confidence": top_confidence,
                "emotion_probabilities": emotion_probs,
            })
        
        processing_time = (time.time() - start_time) * 1000
        
        return BatchEmotionResponse(
            user_id=request.user_id,
            companion_id=request.companion_id,
            results=results,
            total_processing_time_ms=processing_time,
            request_id=request.request_id,
        )
    
    async def predict_from_text(self, text: str) -> Dict[str, float]:
        """Simple prediction from raw text."""
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits.squeeze()
            probabilities = torch.sigmoid(logits).cpu().numpy()
        
        return {
            self.label_map[i]: float(prob)
            for i, prob in enumerate(probabilities)
            if prob > 0.01
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the service."""
        return {
            "initialized": self._initialized,
            "device": str(self.device),
            "model_loaded": self.model is not None,
            "tokenizer_loaded": self.tokenizer is not None,
            "num_labels": len(self.EMOTION_LABELS),
        }
    
    async def close(self) -> None:
        """Cleanup resources."""
        self.model = None
        self.tokenizer = None
        self._initialized = False
        logger.info("Discrete Emotion service closed")


# Singleton instance
_discrete_emotion_service: Optional[DiscreteEmotionService] = None


async def get_discrete_emotion_service() -> DiscreteEmotionService:
    """Get or create Discrete Emotion service singleton."""
    global _discrete_emotion_service
    if _discrete_emotion_service is None:
        _discrete_emotion_service = DiscreteEmotionService()
        await _discrete_emotion_service.initialize()
    return _discrete_emotion_service


async def close_discrete_emotion_service() -> None:
    """Close Discrete Emotion service."""
    global _discrete_emotion_service
    if _discrete_emotion_service:
        await _discrete_emotion_service.close()
        _discrete_emotion_service = None