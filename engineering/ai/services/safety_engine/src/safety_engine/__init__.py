"""
PAO Safety Engine - Crisis detection, content filtering, behavioral guards, reality anchoring.

This module provides safety-critical functionality for the PAO AI Companion platform.
All engine outputs pass through safety gates before reaching users.
"""

__version__ = "1.0.0"
__author__ = "PAO Engineering"
__email__ = "engineering@pao.app"

from safety_engine.config import Settings, get_settings
from safety_engine.models.safety import (
    SafetyCheckRequest,
    SafetyCheckResponse,
    CrisisDetectionResult,
    ContentFilterResult,
    BehavioralGuardResult,
    RealityAnchorResult,
    SafetyViolation,
    InterventionLevel,
    SafetyCategory,
)

__all__ = [
    "Settings",
    "get_settings",
    "SafetyCheckRequest",
    "SafetyCheckResponse",
    "CrisisDetectionResult",
    "ContentFilterResult",
    "BehavioralGuardResult",
    "RealityAnchorResult",
    "SafetyViolation",
    "InterventionLevel",
    "SafetyCategory",
]