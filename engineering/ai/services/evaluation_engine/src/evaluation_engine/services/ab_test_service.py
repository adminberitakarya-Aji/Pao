"""A/B Testing Service for running experiments."""

import logging
import time
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from uuid import UUID
from dataclasses import dataclass, field

import numpy as np
from scipy import stats

from evaluation_engine.config import settings
from evaluation_engine.models.requests import ABTestRequest
from evaluation_engine.models.responses import ABTestResponse, ABTestVariantResult

logger = logging.getLogger(__name__)


@dataclass
class ABTest:
    """A/B Test definition and state."""
    test_id: str
    name: str
    description: Optional[str]
    variant_a: Dict[str, Any]
    variant_b: Dict[str, Any]
    allocation_ratio: float
    min_sample_size: int
    max_duration_days: int
    metrics: List[str]
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    # Results
    variant_a_data: List[Dict[str, Any]] = field(default_factory=list)
    variant_b_data: List[Dict[str, Any]] = field(default_factory=list)


class ABTestService:
    """Service for managing A/B tests."""
    
    def __init__(self):
        self.http_client = None
        self._initialized = False
        self.tests: Dict[str, ABTest] = {}
    
    async def initialize(self) -> None:
        """Initialize the A/B test service."""
        logger.info("Initializing A/B Test service")
        self._initialized = True
        logger.info("A/B Test service initialized")
    
    async def create_test(self, request: ABTestRequest) -> ABTestResponse:
        """Create a new A/B test."""
        start_time = time.time()
        
        test_id = request.test_id or f"ab_{uuid.uuid4().hex[:12]}"
        
        test = ABTest(
            test_id=test_id,
            name=request.name,
            description=request.description,
            variant_a=request.variant_a,
            variant_b=request.variant_b,
            allocation_ratio=request.allocation_ratio,
            min_sample_size=request.min_sample_size,
            max_duration_days=request.max_duration_days,
            metrics=request.metrics,
            status=request.status,
            created_at=datetime.now(),
        )
        
        self.tests[test_id] = test
        
        processing_time = (time.time() - start_time) * 1000
        
        return self._test_to_response(test, processing_time, request.request_id)
    
    async def get_test(self, test_id: str) -> Optional[ABTestResponse]:
        """Get an A/B test by ID."""
        test = self.tests.get(test_id)
        if not test:
            return None
        return self._test_to_response(test, 0.0, None)
    
    async def list_tests(
        self,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[ABTestResponse]:
        """List A/B tests."""
        tests = list(self.tests.values())
        
        if status:
            tests = [t for t in tests if t.status == status]
        
        tests.sort(key=lambda x: x.created_at, reverse=True)
        
        return [self._test_to_response(t, 0.0, None) for t in tests[:limit]]
    
    async def start_test(self, test_id: str) -> Optional[ABTestResponse]:
        """Start an A/B test."""
        test = self.tests.get(test_id)
        if not test:
            return None
        
        if test.status != "draft":
            raise ValueError(f"Cannot start test in status: {test.status}")
        
        test.status = "running"
        test.started_at = datetime.now()
        
        return self._test_to_response(test, 0.0, None)
    
    async def pause_test(self, test_id: str) -> Optional[ABTestResponse]:
        """Pause an A/B test."""
        test = self.tests.get(test_id)
        if not test:
            return None
        
        test.status = "paused"
        
        return self._test_to_response(test, 0.0, None)
    
    async def complete_test(self, test_id: str) -> Optional[ABTestResponse]:
        """Complete an A/B test."""
        test = self.tests.get(test_id)
        if not test:
            return None
        
        test.status = "completed"
        test.completed_at = datetime.now()
        
        return self._test_to_response(test, 0.0, None)
    
    async def record_result(
        self,
        test_id: str,
        variant: str,
        metrics: Dict[str, float],
        user_id: UUID,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Record a test result for a variant."""
        test = self.tests.get(test_id)
        if not test:
            return False
        
        if test.status != "running":
            return False
        
        result = {
            "user_id": str(user_id),
            "metrics": metrics,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
        }
        
        if variant == "A":
            test.variant_a_data.append(result)
        elif variant == "B":
            test.variant_b_data.append(result)
        else:
            return False
        
        # Check if test should auto-complete
        await self._check_completion(test)
        
        return True
    
    async def _check_completion(self, test: ABTest) -> None:
        """Check if test has enough samples to complete."""
        if test.status != "running":
            return
        
        a_count = len(test.variant_a_data)
        b_count = len(test.variant_b_data)
        
        # Check minimum sample size
        if a_count >= test.min_sample_size and b_count >= test.min_sample_size:
            # Check max duration
            if test.started_at:
                elapsed = (datetime.now() - test.started_at).days
                if elapsed >= test.max_duration_days:
                    test.status = "completed"
                    test.completed_at = datetime.now()
                    return
            
            # Could add early stopping rules here (e.g., clear winner)
            # For now, let it run to max duration
    
    def _analyze_test(self, test: ABTest) -> Dict[str, Any]:
        """Analyze test results for statistical significance."""
        if not test.variant_a_data or not test.variant_b_data:
            return {"significant": False, "reason": "insufficient_data"}
        
        results = {}
        
        for metric in test.metrics:
            a_values = [d["metrics"].get(metric, 0) for d in test.variant_a_data if metric in d["metrics"]]
            b_values = [d["metrics"].get(metric, 0) for d in test.variant_b_data if metric in d["metrics"]]
            
            if len(a_values) < 2 or len(b_values) < 2:
                results[metric] = {"significant": False, "reason": "insufficient_data"}
                continue
            
            # Perform t-test
            t_stat, p_value = stats.ttest_ind(a_values, b_values, equal_var=False)
            
            # Effect size (Cohen's d)
            a_mean = np.mean(a_values)
            b_mean = np.mean(b_values)
            pooled_std = np.sqrt((np.var(a_values) + np.var(b_values)) / 2)
            effect_size = (b_mean - a_mean) / pooled_std if pooled_std > 0 else 0
            
            # Confidence intervals
            a_ci = self._confidence_interval(a_values)
            b_ci = self._confidence_interval(b_values)
            
            significant = p_value < settings.ab_test_significance_level
            practically_significant = abs(effect_size) >= settings.ab_test_min_effect_size
            
            results[metric] = {
                "significant": significant and practically_significant,
                "p_value": round(p_value, 4),
                "effect_size": round(effect_size, 3),
                "variant_a_mean": round(a_mean, 3),
                "variant_b_mean": round(b_mean, 3),
                "variant_a_ci": a_ci,
                "variant_b_ci": b_ci,
                "recommendation": "B" if (b_mean > a_mean and significant) else ("A" if (a_mean > b_mean and significant) else "inconclusive"),
            }
        
        return results
    
    def _confidence_interval(self, values: List[float], confidence: float = 0.95) -> List[float]:
        """Calculate confidence interval for mean."""
        n = len(values)
        if n < 2:
            return [0.0, 0.0]
        
        mean = np.mean(values)
        se = stats.sem(values)
        h = se * stats.t.ppf((1 + confidence) / 2., n - 1)
        
        return [round(mean - h, 3), round(mean + h, 3)]
    
    def _test_to_response(
        self,
        test: ABTest,
        processing_time: float,
        request_id: Optional[str],
    ) -> ABTestResponse:
        """Convert test to response."""
        # Analyze if running or completed
        significance = None
        recommendation = None
        
        if test.status in ["running", "completed"] and test.variant_a_data and test.variant_b_data:
            significance = self._analyze_test(test)
            
            # Overall recommendation
            sig_metrics = [m for m, r in significance.items() if r.get("significant")]
            if sig_metrics:
                # Majority vote
                recs = [significance[m]["recommendation"] for m in sig_metrics]
                if recs.count("B") > recs.count("A"):
                    recommendation = "B"
                elif recs.count("A") > recs.count("B"):
                    recommendation = "A"
                else:
                    recommendation = "inconclusive"
            else:
                recommendation = "inconclusive"
        
        return ABTestResponse(
            test_id=test.test_id,
            name=test.name,
            status=test.status,
            variant_a=ABTestVariantResult(
                variant="A",
                sample_size=len(test.variant_a_data),
                metrics=self._aggregate_metrics(test.variant_a_data),
                confidence_intervals={},
            ),
            variant_b=ABTestVariantResult(
                variant="B",
                sample_size=len(test.variant_b_data),
                metrics=self._aggregate_metrics(test.variant_b_data),
                confidence_intervals={},
            ),
            significance=significance,
            recommendation=recommendation,
            started_at=test.started_at,
            completed_at=test.completed_at,
            processing_time_ms=processing_time,
            request_id=request_id,
        )
    
    def _aggregate_metrics(self, data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Aggregate metrics from data points."""
        if not data:
            return {}
        
        metrics = {}
        for point in data:
            for metric, value in point.get("metrics", {}).items():
                if metric not in metrics:
                    metrics[metric] = []
                metrics[metric].append(value)
        
        return {m: round(np.mean(v), 3) for m, v in metrics.items()}
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the service."""
        running = [t for t in self.tests.values() if t.status == "running"]
        return {
            "initialized": self._initialized,
            "total_tests": len(self.tests),
            "running_tests": len(running),
            "completed_tests": len([t for t in self.tests.values() if t.status == "completed"]),
        }
    
    async def close(self) -> None:
        """Cleanup resources."""
        self._initialized = False
        self.tests.clear()
        logger.info("A/B Test service closed")


# Singleton instance
_ab_test_service: Optional[ABTestService] = None


async def get_ab_test_service() -> ABTestService:
    """Get or create A/B Test service singleton."""
    global _ab_test_service
    if _ab_test_service is None:
        _ab_test_service = ABTestService()
        await _ab_test_service.initialize()
    return _ab_test_service


async def close_ab_test_service() -> None:
    """Close A/B Test service."""
    global _ab_test_service
    if _ab_test_service:
        await _ab_test_service.close()
        _ab_test_service = None