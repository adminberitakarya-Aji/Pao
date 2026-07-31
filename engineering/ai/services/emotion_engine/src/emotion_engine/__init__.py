"""PAO Emotion Engine - Emotional state inference, expression, and regulation."""

__version__ = "0.1.0"
__author__ = "PAO Team"
__email__ = "team@pao.ai"

from emotion_engine.config import settings
from emotion_engine.services.emotion_service import get_emotion_service, close_emotion_service

__all__ = [
    "settings",
    "get_emotion_service",
    "close_emotion_service",
]