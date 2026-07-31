"""Drift Detection Service for monitoring dimension drift."""

import logging
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from uuid import UUID
from dataclasses import dataclass, field

import numpy as np
from scipy import stats

from evaluation_engine.config import settings
from evaluation_engine.models.requests import DriftCheckRequest
from evaluation_engine.models.responses import DriftResponse, DriftAlert

logger = logging.getLogger(__name__)


@dataclass
class DimensionHistory:
    """Historical data for a dimension."""
    dimension: str
    scores: List[float] = field(default_factory=list)
    timestamps: List[datetime] = field(default_factory=list)
    baseline_mean: float = 0.0
    baseline_std: float = 0.0
    last_updated: Optional[datetime] = None


class DriftService:
    """Service for detecting dimension drift over time."""
    
    def __init__(self):
        self.http_client = None
        self._initialized = False
        # In-memory storage for dimension histories (would be database in production)
        self._histories: Dict[str, Dict[str, DimensionHistory]] = {}
    
    async def initialize(self) -> None:
        """Initialize the drift service."""
        logger.info("Initializing Drift service")
        self._initialized = True
        logger.info("Drift service initialized")
    
    async def check_drift(self, request: DriftCheckRequest) -> DriftResponse:
        """Check for drift in specified dimensions."""
        start_time = time.time()
        
        # Get or compute dimension histories
        histories = await self._get_histories(
            request.user_id,
            request.companion_id,
            request.dimensions,
            request.window_days,
        )
        
        # Check each dimension for drift
        alerts = []
        for dimension, history in histories.items():
            alert = self._detect_drift(dimension, history, request.threshold)
            if alert:
                alerts.append(alert)
        
        # Generate summary
        summary = self._generate_summary(histories, alerts)
        
        processing_time = (time.time() - start_time) * 1000
        
        return DriftResponse(
            user_id=request.user_id,
            companion_id=request.companion_id,
            has_drift=len(alerts) > 0,
            alerts=alerts,
            summary=summary,
            window_days=request.window_days,
            threshold=request.threshold,
            checked_at=datetime.now(),
            processing_time_ms=processing_time,
            request_id=request.request_id,
        )
    
    async def _get_histories(
        self,
        user_id: UUID,
        companion_id: UUID,
        dimensions: Optional[List[str]],
        window_days: int,
    ) -> Dict[str, DimensionHistory]:
        """Get or build dimension histories."""
        # In production, fetch from database
        # For now, simulate with cached data
        
        cache_key = f"{user_id}:{companion_id}"
        
        if cache_key not in self._histories:
            self._histories[cache_key] = await self._build_histories(
                user_id,
                companion_id,
                window_days,
            )
        
        # Filter to requested dimensions
        if dimensions:
            return {d: self._histories[cache_key][d] for d in dimensions if d in self._histories[cache_key]}
        
        return self._histories[cache_key]
    
    async def _build_histories(
        self,
        user_id: UUID,
        companion_id: UUID,
        window_days: int,
    ) -> Dict[str, DimensionHistory]:
        """Build dimension histories from historical data."""
        # In production, query time-series database
        # Simulate historical data
        
        all_dimensions = ["trust", "intimacy", "satisfaction", "safety", "growth"]
        histories = {}
        
        np.random.seed(hash(str(user_id) + str(companion_id)) % 2**32)
        
        # Generate base scores for each dimension
        base_scores = {
            dim: np.random.uniform(4.0, 8.0) for dim in all_dimensions
        }
        
        for dim in all_dimensions:
            history = DimensionHistory(dimension=dim)
            
            # Generate daily scores for the window
            for i in range(window_days):
                date = datetime.now() - timedelta(days=window_days - i)
                
                # Add trend and noise
                trend = (i - window_days / 2) * 0.01  # Slight trend
                noise = np.random.normal(0, 0.3)
                score = base_scores[dim] + trend + noise
                score = np.clip(score, 1.0, 10.0)
                
                history.scores.append(score)
                history.timestamps.append(date)
            
            # Calculate baseline statistics (first 70% of data)
            baseline_cutoff = int(len(history.scores) * 0.7)
            baseline_scores = history.scores[:baseline_cutoff]
            
            history.baseline_mean = float(np.mean(baseline_scores))
            history.baseline_std = float(np.std(baseline_scores))
            history.last_updated = datetime.now()
            
            histories[dim] = history
        
        return histories
    
    def _detect_drift(
        self,
        dimension: str,
        history: DimensionHistory,
        threshold: float,
    ) -> Optional[DriftAlert]:
        """Detect drift in a single dimension."""
        if len(history.scores) < 10:
            return None
        
        # Use recent scores (last 30% of data) vs baseline
        recent_cutoff = int(len(history.scores) * 0.7)
        recent_scores = history.scores[recent_cutoff:]
        
        if len(recent_scores) < 5:
            return None
        
        recent_mean = float(np.mean(recent_scores))
        recent_std = float(np.std(recent_scores))
        
        # Calculate drift magnitude
        drift_magnitude = abs(recent_mean - history.baseline_mean)
        
        # Calculate z-score
        if history.baseline_std > 0:
            z_score = drift_magnitude / history.baseline_std
        else:
            z_score = 0.0
        
        # Check if drift exceeds threshold
        if drift_magnitude < threshold:
            return None
        
        # Determine direction
        direction = "increasing" if recent_mean > history.baseline_mean else "decreasing"
        
        # Determine severity
        if z_score >= 3.0:
            severity = "critical"
        elif z_score >= 2.5:
            severity = "high"
        elif z_score >= 2.0:
            severity = "medium"
        else:
            severity = "low"
        
        return DriftAlert(
            dimension=dimension,
            current_score=round(recent_mean, 2),
            baseline_score=round(history.baseline_mean, 2),
            drift_magnitude=round(drift_magnitude, 2),
            direction=direction,
            severity=severity,
            detected_at=datetime.now(),
        )
    
    def _generate_summary(
        self,
        histories: Dict[str, DimensionHistory],
        alerts: List[DriftAlert],
    ) -> Dict[str, Any]:
        """Generate summary statistics."""
        summary = {
            "total_dimensions": len(histories),
            "dimensions_with_drift": len(alerts),
            "max_drift_magnitude": 0.0,
            "average_drift_magnitude": 0.0,
            "dimensions": {},
        }
        
        drift_magnitudes = []
        
        for dim, history in histories.items():
            if len(history.scores) < 2:
                continue
            
            recent_scores = history.scores[int(len(history.scores) * 0.7):]
            if recent_scores:
                recent_mean = float(np.mean(recent_scores))
                drift = abs(recent_mean - history.baseline_mean)
                drift_magnitudes.append(drift)
                
                summary["dimensions"][dim] = {
                    "current": round(recent_mean, 2),
                    "baseline": round(history.baseline_mean, 2),
                    "drift": round(drift, 2),
                    "trend": "up" if recent_mean > history.baseline_mean else "down",
                }
        
        if drift_magnitudes:
            summary["max_drift_magnitude"] = round(max(drift_magnitudes), 2)
            summary["average_drift_magnitude"] = round(np.mean(drift_magnitudes), 2)
        
        return summary
    
    async def record_dimension_score(
        self,
        user_id: UUID,
        companion_id: UUID,
        dimension: str,
        score: float,
    ) -> None:
        """Record a new dimension score for drift tracking."""
        cache_key = f"{user_id}:{companion_id}"
        
        if cache_key not in self._histories:
            self._histories[cache_key] = {}
        
        if dimension not in self._histories[cache_key]:
            self._histories[cache_key][dimension] = DimensionHistory(dimension=dimension)
        
        history = self._histories[cache_key][dimension]
        history.scores.append(score)
        history.timestamps.append(datetime.now())
        
        # Keep only last 365 days
        cutoff = datetime.now() - timedelta(days=365)
        while history.timestamps and history.timestamps[0] < cutoff:
            history.scores.pop(0)
            history.timestamps.pop(0)
        
        # Recalculate baseline periodically
        if len(history.scores) % 30 == 0:
            baseline_cutoff = int(len(history.scores) * 0.7)
            baseline_scores = history.scores[:baseline_cutoff]
            if baseline_scores:
                history.baseline_mean = float(np.mean(baseline_scores))
                history.baseline_std = float(np.std(baseline_scores))
                history.last_updated = datetime.now()
    
    async def get_drift_history(
        self,
        user_id: UUID,
        companion_id: UUID,
        dimension: str,
        days: int = 90,
    ) -> Dict[str, Any]:
        """Get drift history for a specific dimension."""
        cache_key = f"{user_id}:{companion_id}"
        
        if cache_key not in self._histories:
            await self._build_histories(user_id, companion_id, days)
        
        history = self._histories[cache_key].get(dimension)
        if not history:
            return {"dimension": dimension, "data": []}
        
        # Return last N days
        cutoff_idx = max(0, len(history.scores) - days)
        
        return {
            "dimension": dimension,
            "data": [
                {
                    "date": history.timestamps[i].isoformat(),
                    "score": history.scores[i],
                }
                for i in range(cutoff_idx, len(history.scores))
            ],
            "baseline_mean": history.baseline_mean,
            "baseline_std": history.baseline_std,
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the service."""
        return {
            "initialized": self._initialized,
            "tracked_pairs": len(self._histories),
        }
    
    async def close(self) -> None:
        """Cleanup resources."""
        self._initialized = False
        self._histories.clear()
        logger.info("Drift service closed")


# Singleton instance
_drift_service: Optional[DriftService] = None


async def get_drift_service() -> DriftService:
    """Get or create Drift service singleton."""
    global _drift_service
    if _drift_service is None:
        _drift_service = DriftService()
        await _drift_service.initialize()
    return _drift_service


async def close_drift_service() -> None:
    """Close Drift service."""
    global _drift_service
    if _drift_service:
        await _drift_service.close()
        _drift_service = None