"""Proactive Engine - Proactive AI capabilities for initiative, anticipation, and scheduling."""

from proactive_engine.config import settings, get_settings
from proactive_engine.main import app, create_app

__version__ = "0.1.0"
__all__ = [
    "settings",
    "get_settings",
    "app",
    "create_app",
]