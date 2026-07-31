"""Cognitive Appraisal Service for emotion appraisal analysis."""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, List
from uuid import UUID

import torch
from transformers import AutoTokenizer, AutoModel

from emotion_engine.config import settings
from emotion_engine.models.requests import AppraisalRequest
from emotion_engine.models.responses import AppraisalResponse

logger = logging.getLogger(__name__)


class AppraisalService:
    """Service for cognitive appraisal analysis based on Scherer's component process model."""
    
    # Appraisal dimensions from Scherer's model
    APPRAISAL_DIMENSIONS = [
        "novelty",           # How new/unexpected is the event
        "pleasantness",      # How pleasant/unpleasant
        "goal_relevance",    # Relevance to goals
        "goal_congruence",   # Consistency with goals
        "coping_potential",  # Ability to cope
        "norm_compatibility",# Social/moral norm compatibility
        "self_compatibility",# Self-concept compatibility
        "agency",            # Who/Causality attribution (self/other/chance)
        "certainty",         # Predictability
        "controllability",   # Degree of control
        "expectedness",      # How expected was the event
    ]
    
    DIMENSION_DESCRIPTIONS = {
        "novelty": "Degree of novelty or unexpectedness of the event",
        "pleasantness": "Intrinsic pleasantness or unpleasantness",
        "goal_relevance": "Relevance to current goals and needs",
        "goal_congruence": "Consistency with goal attainment",
        "coping_potential": "Perceived ability to cope with consequences",
        "norm_compatibility": "Compatibility with social and moral norms",
        "self_compatibility": "Compatibility with self-concept and ideals",
        "agency": "Attribution of responsibility (self, other, circumstance)",
        "certainty": "Predictability and certainty of outcome",
        "controllability": "Degree of perceived control over event",
        "expectedness": "How much the event was anticipated",
    }
    
    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.appraisal_heads = {}
        self.device = settings.emotion_device
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the appraisal model."""
        logger.info("Loading Cognitive Appraisal model")
        
        try:
            model_name = settings.appraisal_model_name
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name).to(self.device)
            self.model.eval()
            
            # Initialize appraisal dimension heads
            hidden_size = self.model.config.hidden_size
            for dim in self.APPRAISAL_DIMENSIONS:
                self.appraisal_heads[dim] = torch.nn.Linear(hidden_size, 1).to(self.device)
            
            # Load fine-tuned weights if available
            if settings.appraisal_weights_path:
                await self._load_weights()
            
            self._initialized = True
            logger.info("Cognitive Appraisal model loaded successfully")
            
        except Exception as e:
            logger.error("Failed to load Cognitive Appraisal model", error=str(e))
            raise
    
    async def _load_weights(self) -> None:
        """Load fine-tuned appraisal head weights."""
        try:
            checkpoint = torch.load(
                settings.appraisal_weights_path,
                map_location=self.device
            )
            for dim, head in self.appraisal_heads.items():
                if dim in checkpoint:
                    head.load_state_dict(checkpoint[dim])
            logger.info("Loaded fine-tuned appraisal weights")
        except Exception as e:
            logger.warning("Could not load appraisal weights", error=str(e))
    
    async def analyze_appraisal(self, request: AppraisalRequest) -> AppraisalResponse:
        """Analyze cognitive appraisals for given text/event."""
        start_time = time.time()
        
        # Prepare input text
        input_text = request.text
        if request.event_description:
            input_text = f"Event: {request.event_description}. Reaction: {request.text}"
        
        # Tokenize
        inputs = self.tokenizer(
            input_text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        ).to(self.device)
        
        # Get embeddings
        with torch.no_grad():
            outputs = self.model(**inputs)
            cls_embedding = outputs.last_hidden_state[:, 0, :]
        
        # Predict each appraisal dimension
        appraisals = {}
        confidences = {}
        
        dimensions = request.dimensions or self.APPRAISAL_DIMENSIONS
        
        for dim in dimensions:
            if dim in self.appraisal_heads:
                with torch.no_grad():
                    logit = self.appraisal_heads[dim](cls_embedding).squeeze()
                    # Map to [-1, 1] range for most dimensions
                    value = torch.tanh(logit).item()
                    appraisals[dim] = value
                    confidences[dim] = min(1.0, abs(value) + 0.1)
        
        # Derive higher-level appraisal patterns
        appraisal_pattern = self._derive_appraisal_pattern(appraisals)
        
        # Generate interpretation
        interpretation = self._generate_interpretation(appraisals, request.context)
        
        processing_time = (time.time() - start_time) * 1000
        
        return AppraisalResponse(
            user_id=request.user_id,
            companion_id=request.companion_id,
            appraisals=appraisals,
            confidences=confidences,
            appraisal_pattern=appraisal_pattern,
            interpretation=interpretation,
            processing_time_ms=processing_time,
            request_id=request.request_id,
        )
    
    def _derive_appraisal_pattern(self, appraisals: Dict[str, float]) -> str:
        """Derive high-level appraisal pattern from dimension scores."""
        patterns = []
        
        # Goal relevance
        if appraisals.get("goal_relevance", 0) > 0.3:
            patterns.append("goal_relevant")
        else:
            patterns.append("goal_irrelevant")
        
        # Goal congruence
        if appraisals.get("goal_congruence", 0) > 0.3:
            patterns.append("goal_congruent")
        elif appraisals.get("goal_congruence", 0) < -0.3:
            patterns.append("goal_incongruent")
        
        # Coping potential
        coping = appraisals.get("coping_potential", 0)
        if coping > 0.3:
            patterns.append("high_coping")
        elif coping < -0.3:
            patterns.append("low_coping")
        
        # Agency
        agency = appraisals.get("agency", 0)
        if agency > 0.3:
            patterns.append("self_agent")
        elif agency < -0.3:
            patterns.append("other_agent")
        else:
            patterns.append("circumstance_agent")
        
        return "_".join(patterns)
    
    def _generate_interpretation(
        self,
        appraisals: Dict[str, float],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate human-readable interpretation of appraisal profile."""
        interpretations = []
        
        # Novelty
        novelty = appraisals.get("novelty", 0)
        if novelty > 0.5:
            interpretations.append("highly unexpected event")
        elif novelty > 0.2:
            interpretations.append("somewhat novel event")
        elif novelty < -0.5:
            interpretations.append("very familiar/expected event")
        
        # Pleasantness
        pleasant = appraisals.get("pleasantness", 0)
        if pleasant > 0.5:
            interpretations.append("intrinsically pleasant")
        elif pleasant < -0.5:
            interpretations.append("intrinsically unpleasant")
        
        # Goal congruence
        congruence = appraisals.get("goal_congruence", 0)
        if congruence > 0.5:
            interpretations.append("strongly supports goals")
        elif congruence < -0.5:
            interpretations.append("strongly obstructs goals")
        
        # Coping
        coping = appraisals.get("coping_potential", 0)
        if coping > 0.5:
            interpretations.append("high perceived ability to cope")
        elif coping < -0.5:
            interpretations.append("low perceived ability to cope")
        
        # Agency
        agency = appraisals.get("agency", 0)
        if agency > 0.5:
            interpretations.append("self-caused")
        elif agency < -0.5:
            interpretations.append("other-caused")
        else:
            interpretations.append("situational/circumstantial")
        
        return "; ".join(interpretations) if interpretations else "neutral appraisal profile"
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the service."""
        return {
            "initialized": self._initialized,
            "device": str(self.device),
            "model_loaded": self.model is not None,
            "tokenizer_loaded": self.tokenizer is not None,
            "num_dimensions": len(self.APPRAISAL_DIMENSIONS),
        }
    
    async def close(self) -> None:
        """Cleanup resources."""
        self.model = None
        self.tokenizer = None
        self.appraisal_heads.clear()
        self._initialized = False
        logger.info("Appraisal service closed")


# Singleton instance
_appraisal_service: Optional[AppraisalService] = None


async def get_appraisal_service() -> AppraisalService:
    """Get or create Appraisal service singleton."""
    global _appraisal_service
    if _appraisal_service is None:
        _appraisal_service = AppraisalService()
        await _appraisal_service.initialize()
    return _appraisal_service


async def close_appraisal_service() -> None:
    """Close Appraisal service."""
    global _appraisal_service
    if _appraisal_service:
        await _appraisal_service.close()
        _appraisal_service = None