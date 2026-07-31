"""RHI Calculator Service for computing Relationship Health Index."""

import logging
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from uuid import UUID

import numpy as np
from scipy import stats

from evaluation_engine.config import settings
from evaluation_engine.models.requests import ComputeRHIRequest
from evaluation_engine.models.responses import RHIResponse

logger = logging.getLogger(__name__)


class RHIService:
    """Service for computing Relationship Health Index (RHI)."""
    
    # RHI Dimension weights (sum to 1.0)
    DIMENSION_WEIGHTS = {
        "trust": 0.25,
        "intimacy": 0.20,
        "satisfaction": 0.20,
        "safety": 0.20,
        "growth": 0.15,
    }
    
    # Dimension descriptions for reporting
    DIMENSION_LABELS = {
        "trust": "Trust & Reliability",
        "intimacy": "Emotional Intimacy",
        "satisfaction": "Overall Satisfaction",
        "safety": "Psychological Safety",
        "growth": "Personal Growth",
    }
    
    def __init__(self):
        self.http_client = None  # Would connect to other engines
        self._initialized = False
        # In-memory cache for dimension scores (would be Redis in production)
        self._dimension_cache: Dict[str, Dict[str, Any]] = {}
    
    async def initialize(self) -> None:
        """Initialize the RHI service."""
        logger.info("Initializing RHI service")
        self._initialized = True
        logger.info("RHI service initialized")
    
    async def compute_rhi(self, request: ComputeRHIRequest) -> RHIResponse:
        """Compute Relationship Health Index for a user-companion pair."""
        start_time = time.time()
        
        # Get or compute dimension scores
        if request.dimensions:
            dimensions = request.dimensions
        else:
            dimensions = await self._fetch_dimension_scores(
                request.user_id,
                request.companion_id,
                request.period_days,
            )
        
        # Calculate weighted RHI score
        rhi_score = self._calculate_weighted_rhi(dimensions)
        
        # Generate breakdown if requested
        breakdown = None
        if request.include_breakdown:
            breakdown = self._generate_breakdown(dimensions, request.period_days)
        
        # Determine trend
        trend = await self._calculate_trend(
            request.user_id,
            request.companion_id,
            rhi_score,
            request.period_days,
        )
        
        # Calculate correlation with surveys if available
        correlation = await self._calculate_survey_correlation(
            request.user_id,
            request.companion_id,
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return RHIResponse(
            user_id=request.user_id,
            companion_id=request.companion_id,
            rhi_score=round(rhi_score, 2),
            dimensions=dimensions,
            breakdown=breakdown,
            period_days=request.period_days,
            computed_at=datetime.now(),
            trend=trend,
            correlation_with_survey=correlation,
            processing_time_ms=processing_time,
            request_id=request.request_id,
        )
    
    async def _fetch_dimension_scores(
        self,
        user_id: UUID,
        companion_id: UUID,
        period_days: int,
    ) -> Dict[str, float]:
        """Fetch dimension scores from Relationship Engine or compute from events."""
        # In production, this would call Relationship Engine API
        # For now, simulate with cached or default values
        
        cache_key = f"{user_id}:{companion_id}"
        
        if cache_key in self._dimension_cache:
            cached = self._dimension_cache[cache_key]
            # Check if cache is fresh (less than 1 hour old)
            if (datetime.now() - cached["timestamp"]).seconds < 3600:
                return cached["dimensions"]
        
        # Simulate fetching from Relationship Engine
        # Real implementation would call: GET /api/v1/relationship/{companion_id}/dimensions
        dimensions = await self._simulate_dimension_scores(user_id, companion_id)
        
        # Cache the result
        self._dimension_cache[cache_key] = {
            "dimensions": dimensions,
            "timestamp": datetime.now(),
        }
        
        return dimensions
    
    async def _simulate_dimension_scores(
        self,
        user_id: UUID,
        companion_id: UUID,
    ) -> Dict[str, float]:
        """Simulate dimension scores (replace with actual engine calls)."""
        # In production, this would call Relationship Engine
        # For now, return realistic simulated values
        np.random.seed(hash(str(user_id) + str(companion_id)) % 2**32)
        
        base_score = 6.5 + np.random.normal(0, 1.5)
        base_score = np.clip(base_score, 1.0, 10.0)
        
        return {
            "trust": round(np.clip(base_score + np.random.normal(0, 0.5), 1.0, 10.0), 1),
            "intimacy": round(np.clip(base_score + np.random.normal(-0.5, 0.7), 1.0, 10.0), 1),
            "satisfaction": round(np.clip(base_score + np.random.normal(0, 0.5), 1.0, 10.0), 1),
            "safety": round(np.clip(base_score + np.random.normal(0.5, 0.3), 1.0, 10.0), 1),
            "growth": round(np.clip(base_score + np.random.normal(-0.3, 0.6), 1.0, 10.0), 1),
        }
    
    def _calculate_weighted_rhi(self, dimensions: Dict[str, float]) -> float:
        """Calculate weighted RHI score from dimensions."""
        total = 0.0
        for dim, weight in self.DIMENSION_WEIGHTS.items():
            score = dimensions.get(dim, 5.0)  # Default to neutral if missing
            total += score * weight
        return total
    
    def _generate_breakdown(
        self,
        dimensions: Dict[str, float],
        period_days: int,
    ) -> Dict[str, Any]:
        """Generate detailed breakdown for reporting."""
        breakdown = {}
        
        for dim, score in dimensions.items():
            weight = self.DIMENSION_WEIGHTS.get(dim, 0)
            contribution = score * weight
            
            # Determine status
            if score >= 8.0:
                status = "excellent"
            elif score >= 6.5:
                status = "good"
            elif score >= 4.5:
                status = "fair"
            elif score >= 3.0:
                status = "concerning"
            else:
                status = "critical"
            
            breakdown[dim] = {
                "label": self.DIMENSION_LABELS.get(dim, dim.title()),
                "score": round(score, 1),
                "weight": weight,
                "contribution": round(contribution, 2),
                "status": status,
                "percentile": self._score_to_percentile(score),
            }
        
        # Add summary stats
        scores = list(dimensions.values())
        breakdown["_summary"] = {
            "mean": round(np.mean(scores), 1),
            "median": round(np.median(scores), 1),
            "std": round(np.std(scores), 1),
            "min": round(min(scores), 1),
            "max": round(max(scores), 1),
            "period_days": period_days,
        }
        
        return breakdown
    
    def _score_to_percentile(self, score: float) -> int:
        """Convert score to approximate percentile (based on population distribution)."""
        # Assuming normal distribution with mean=6.5, std=1.5
        percentile = stats.norm.cdf(score, loc=6.5, scale=1.5) * 100
        return int(np.clip(percentile, 1, 99))
    
    async def _calculate_trend(
        self,
        user_id: UUID,
        companion_id: UUID,
        current_rhi: float,
        period_days: int,
    ) -> Optional[str]:
        """Calculate RHI trend over time."""
        # In production, query historical RHI values from database
        # For now, simulate based on random walk
        
        # Simulate previous RHI values
        np.random.seed(hash(str(user_id) + str(companion_id) + "trend") % 2**32)
        previous_rhi = current_rhi + np.random.normal(0, 0.5)
        
        diff = current_rhi - previous_rhi
        
        if diff > 0.3:
            return "improving"
        elif diff < -0.3:
            return "declining"
        else:
            return "stable"
    
    async def _calculate_survey_correlation(
        self,
        user_id: UUID,
        companion_id: UUID,
    ) -> Optional[float]:
        """Calculate correlation between RHI and survey responses."""
        # In production, query survey responses and compute correlation
        # For now, return a simulated correlation
        return round(np.random.uniform(0.75, 0.95), 2)
    
    async def get_rhi_history(
        self,
        user_id: UUID,
        companion_id: UUID,
        days: int = 90,
    ) -> List[Dict[str, Any]]:
        """Get historical RHI values for trend analysis."""
        # In production, query time-series database
        # Simulate history
        history = []
        base_rhi = 6.5
        
        for i in range(days, 0, -7):  # Weekly snapshots
            date = datetime.now() - timedelta(days=i)
            # Add some trend and noise
            rhi = base_rhi + np.random.normal(0, 0.3) + (days - i) * 0.02
            rhi = np.clip(rhi, 1.0, 10.0)
            
            history.append({
                "date": date.isoformat(),
                "rhi_score": round(rhi, 1),
            })
        
        return history
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the service."""
        return {
            "initialized": self._initialized,
            "cache_size": len(self._dimension_cache),
        }
    
    async def close(self) -> None:
        """Cleanup resources."""
        self._initialized = False
        self._dimension_cache.clear()
        logger.info("RHI service closed")


# Singleton instance
_rhi_service: Optional[RHIService] = None


async def get_rhi_service() -> RHIService:
    """Get or create RHI service singleton."""
    global _rhi_service
    if _rhi_service is None:
        _rhi_service = RHIService()
        await _rhi_service.initialize()
    return _rhi_service


async def close_rhi_service() -> None:
    """Close RHI service."""
    global _rhi_service
    if _rhi_service:
        await _rhi_service.close()
        _rhi_service = None