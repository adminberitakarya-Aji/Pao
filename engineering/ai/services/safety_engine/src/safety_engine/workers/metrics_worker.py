"""
Metrics Worker.

Aggregates safety metrics from Redis and persists to PostgreSQL.
Runs periodically via Temporal or cron.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from safety_engine.config import get_settings
from safety_engine.repositories.base import BaseRepository
from safety_engine.models.safety import SafetyMetrics


logger = logging.getLogger(__name__)


class MetricsWorker:
    """Worker for aggregating and persisting safety metrics."""
    
    def __init__(
        self,
        postgres_repo: BaseRepository,
        redis_repo: BaseRepository,
    ):
        self.settings = get_settings()
        self.postgres_repo = postgres_repo
        self.redis_repo = redis_repo
    
    async def aggregate_metrics(
        self,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> SafetyMetrics:
        """
        Aggregate metrics from Redis and persist to PostgreSQL.
        
        Args:
            period_start: Start of aggregation period (default: last hour)
            period_end: End of aggregation period (default: now)
            
        Returns:
            Aggregated SafetyMetrics
        """
        if period_end is None:
            period_end = datetime.utcnow()
        if period_start is None:
            period_start = period_end - timedelta(hours=1)
        
        logger.info(f"Aggregating metrics for period: {period_start} to {period_end}")
        
        # Get metrics from Redis (real-time)
        redis_metrics = await self.redis_repo.get_metrics(period_start, period_end)
        
        # Get metrics from PostgreSQL (historical)
        pg_metrics = await self.postgres_repo.get_metrics(period_start, period_end)
        
        # Combine metrics (Redis takes precedence for current period)
        combined = self._combine_metrics(redis_metrics, pg_metrics)
        
        # Persist combined metrics to PostgreSQL
        await self.postgres_repo.store_metrics(combined)
        
        # Update Redis with aggregated metrics
        await self.redis_repo.store_metrics(combined)
        
        logger.info(f"Metrics aggregated: total_checks={combined.total_checks}, "
                   f"crisis={combined.crisis_detected}, "
                   f"content_violations={combined.content_violations}")
        
        return combined
    
    def _combine_metrics(
        self,
        redis_metrics: SafetyMetrics,
        pg_metrics: SafetyMetrics,
    ) -> SafetyMetrics:
        """Combine metrics from Redis and PostgreSQL."""
        # Use Redis for real-time, PG for historical
        # For overlapping periods, Redis is more current
        
        return SafetyMetrics(
            total_checks=redis_metrics.total_checks + pg_metrics.total_checks,
            crisis_detected=redis_metrics.crisis_detected + pg_metrics.crisis_detected,
            content_violations=redis_metrics.content_violations + pg_metrics.content_violations,
            behavioral_violations=redis_metrics.behavioral_violations + pg_metrics.behavioral_violations,
            reality_anchors_triggered=redis_metrics.reality_anchors_triggered + pg_metrics.reality_anchors_triggered,
            interventions_by_level=self._merge_interventions(
                redis_metrics.interventions_by_level,
                pg_metrics.interventions_by_level
            ),
            avg_processing_time_ms=self._weighted_avg(
                redis_metrics.avg_processing_time_ms, redis_metrics.total_checks,
                pg_metrics.avg_processing_time_ms, pg_metrics.total_checks
            ),
            false_positive_rate=self._weighted_avg(
                redis_metrics.false_positive_rate, redis_metrics.total_checks,
                pg_metrics.false_positive_rate, pg_metrics.total_checks
            ),
            false_negative_rate=self._weighted_avg(
                redis_metrics.false_negative_rate, redis_metrics.total_checks,
                pg_metrics.false_negative_rate, pg_metrics.total_checks
            ),
        )
    
    def _merge_interventions(
        self,
        redis_interventions: Dict[str, int],
        pg_interventions: Dict[str, int],
    ) -> Dict[str, int]:
        """Merge intervention counts from both sources."""
        all_levels = set(redis_interventions.keys()) | set(pg_interventions.keys())
        return {
            level: redis_interventions.get(level, 0) + pg_interventions.get(level, 0)
            for level in all_levels
        }
    
    def _weighted_avg(
        self,
        val1: float, weight1: int,
        val2: float, weight2: int,
    ) -> float:
        """Calculate weighted average."""
        total_weight = weight1 + weight2
        if total_weight == 0:
            return 0.0
        return (val1 * weight1 + val2 * weight2) / total_weight
    
    async def run_hourly_aggregation(self) -> SafetyMetrics:
        """Run hourly metrics aggregation (called by Temporal/cron)."""
        period_end = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        period_start = period_end - timedelta(hours=1)
        
        return await self.aggregate_metrics(period_start, period_end)
    
    async def run_daily_aggregation(self) -> SafetyMetrics:
        """Run daily metrics aggregation (called by Temporal/cron)."""
        period_end = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        period_start = period_end - timedelta(days=1)
        
        return await self.aggregate_metrics(period_start, period_end)
    
    async def cleanup_old_redis_metrics(self, days: int = 7) -> int:
        """Clean up old metrics from Redis."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        # Redis TTL handles most cleanup, but we can force cleanup of old keys
        # This would require scanning keys which is not recommended in production
        # Instead, rely on TTL settings in the repository
        logger.info(f"Redis metrics cleanup: relying on TTL (7 days default)")
        return 0