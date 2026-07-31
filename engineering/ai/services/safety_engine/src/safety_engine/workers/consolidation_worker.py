"""
Consolidation Worker.

Handles data consolidation tasks for safety engine:
- Audit log consolidation
- Pattern analysis
- Trend detection
- Report generation
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import Counter

from safety_engine.config import get_settings
from safety_engine.repositories.base import BaseRepository
from safety_engine.models.safety import SafetyAlert, InterventionLevel, SafetyCategory


logger = logging.getLogger(__name__)


class ConsolidationWorker:
    """Worker for consolidating safety data and generating insights."""
    
    def __init__(
        self,
        postgres_repo: BaseRepository,
        redis_repo: BaseRepository,
    ):
        self.settings = get_settings()
        self.postgres_repo = postgres_repo
        self.redis_repo = redis_repo
    
    async def run_daily_consolidation(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Run daily consolidation of safety data.
        
        Args:
            date: Date to consolidate (default: yesterday)
            
        Returns:
            Consolidation results
        """
        if date is None:
            date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        
        start_time = date
        end_time = date + timedelta(days=1)
        
        logger.info(f"Running daily consolidation for {date.date()}")
        
        # Get all alerts for the day
        alerts = await self.postgres_repo.get_safety_alerts(
            start_time=start_time,
            end_time=end_time,
            limit=50000,
        )
        
        # Analyze patterns
        patterns = self._analyze_patterns(alerts)
        
        # Detect trends
        trends = await self._detect_trends(alerts, days_back=7)
        
        # Generate summary report
        report = self._generate_daily_report(date, alerts, patterns, trends)
        
        # Store consolidated data
        await self._store_consolidated_data(date, report)
        
        logger.info(f"Daily consolidation complete: {len(alerts)} alerts processed")
        
        return report
    
    def _analyze_patterns(self, alerts: List[SafetyAlert]) -> Dict[str, Any]:
        """Analyze patterns in alerts."""
        if not alerts:
            return {"message": "No alerts in period"}
        
        patterns = {
            "by_category": Counter(),
            "by_severity": Counter(),
            "by_intervention": Counter(),
            "by_hour": Counter(),
            "by_user": Counter(),
            "by_companion": Counter(),
            "recurring_users": [],
            "top_categories": [],
        }
        
        for alert in alerts:
            # By category
            cat = alert.alert_type.value if alert.alert_type else "unknown"
            patterns["by_category"][cat] += 1
            
            # By severity
            patterns["by_severity"][alert.severity] += 1
            
            # By intervention
            patterns["by_intervention"][alert.intervention_level.value] += 1
            
            # By hour
            hour = alert.timestamp.hour
            patterns["by_hour"][hour] += 1
            
            # By user
            patterns["by_user"][alert.user_id] += 1
            
            # By companion
            if alert.companion_id:
                patterns["by_companion"][alert.companion_id] += 1
        
        # Find recurring users (3+ alerts in period)
        patterns["recurring_users"] = [
            {"user_id": uid, "count": count}
            for uid, count in patterns["by_user"].items()
            if count >= 3
        ]
        
        # Top categories
        patterns["top_categories"] = patterns["by_category"].most_common(5)
        
        return patterns
    
    async def _detect_trends(
        self,
        current_alerts: List[SafetyAlert],
        days_back: int = 7,
    ) -> Dict[str, Any]:
        """Detect trends by comparing with previous periods."""
        end_time = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        start_time = end_time - timedelta(days=days_back)
        
        # Get historical alerts
        historical = await self.postgres_repo.get_safety_alerts(
            start_time=start_time,
            end_time=end_time,
            limit=50000,
        )
        
        # Split into current day and previous days
        current_day_start = end_time - timedelta(days=1)
        current_day_alerts = [a for a in historical if a.timestamp >= current_day_start]
        previous_alerts = [a for a in historical if a.timestamp < current_day_start]
        
        current_count = len(current_day_alerts)
        previous_avg = len(previous_alerts) / max(1, days_back - 1)
        
        # Category trends
        current_cats = Counter(a.alert_type.value if a.alert_type else "unknown" for a in current_day_alerts)
        previous_cats = Counter(a.alert_type.value if a.alert_type else "unknown" for a in previous_alerts)
        
        category_trends = {}
        all_cats = set(current_cats.keys()) | set(previous_cats.keys())
        for cat in all_cats:
            current = current_cats.get(cat, 0)
            previous_avg_cat = previous_cats.get(cat, 0) / max(1, days_back - 1)
            
            if previous_avg_cat > 0:
                change = (current - previous_avg_cat) / previous_avg_cat
            else:
                change = 1.0 if current > 0 else 0.0
            
            category_trends[cat] = {
                "current": current,
                "previous_avg": round(previous_avg_cat, 2),
                "change_percent": round(change * 100, 1),
                "trend": "increasing" if change > 0.2 else "decreasing" if change < -0.2 else "stable",
            }
        
        return {
            "total_trend": {
                "current": current_count,
                "previous_avg": round(previous_avg, 2),
                "change_percent": round((current_count - previous_avg) / max(1, previous_avg) * 100, 1),
            },
            "category_trends": category_trends,
        }
    
    def _generate_daily_report(
        self,
        date: datetime,
        alerts: List[SafetyAlert],
        patterns: Dict[str, Any],
        trends: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate daily consolidation report."""
        total_alerts = len(alerts)
        
        # Calculate rates
        crisis_count = patterns["by_category"].get("crisis", 0) + patterns["by_category"].get("suicide", 0) + patterns["by_category"].get("self_harm", 0)
        content_violations = sum(
            patterns["by_category"].get(cat, 0)
            for cat in ["hate", "harassment", "sexual", "violence", "illegal", "medical", "financial"]
        )
        behavioral_violations = sum(
            patterns["by_category"].get(cat, 0)
            for cat in ["manipulation", "dependency", "enmeshment", "gaslighting", "authority"]
        )
        reality_issues = sum(
            patterns["by_category"].get(cat, 0)
            for cat in ["paranoia", "delusion", "hallucination", "conspiracy"]
        )
        
        # Intervention breakdown
        intervention_counts = patterns["by_intervention"]
        
        report = {
            "date": date.date().isoformat(),
            "summary": {
                "total_alerts": total_alerts,
                "crisis_alerts": crisis_count,
                "content_violations": content_violations,
                "behavioral_violations": behavioral_violations,
                "reality_issues": reality_issues,
                "unique_users": len(patterns["by_user"]),
                "unique_companions": len(patterns["by_companion"]),
                "recurring_users": len(patterns["recurring_users"]),
            },
            "patterns": patterns,
            "trends": trends,
            "interventions": dict(intervention_counts),
            "severity_distribution": dict(patterns["by_severity"]),
            "hourly_distribution": dict(patterns["by_hour"]),
            "generated_at": datetime.utcnow().isoformat(),
        }
        
        return report
    
    async def _store_consolidated_data(self, date: datetime, report: Dict[str, Any]) -> None:
        """Store consolidated report in Redis and PostgreSQL."""
        import json
        
        # Store in Redis with 90-day TTL
        redis_key = f"safety:consolidated:daily:{date.date().isoformat()}"
        await self.redis_repo.client.setex(
            redis_key,
            90 * 24 * 3600,  # 90 days
            json.dumps(report, default=str),
        )
        
        # Store in PostgreSQL (would need a consolidated_reports table)
        # For now, log that it would be stored
        logger.info(f"Consolidated report stored for {date.date()}: {report['summary']['total_alerts']} alerts")
    
    async def run_weekly_consolidation(self, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Run weekly consolidation (7 daily reports)."""
        if end_date is None:
            end_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        start_date = end_date - timedelta(days=7)
        
        logger.info(f"Running weekly consolidation: {start_date.date()} to {end_date.date()}")
        
        # Get all alerts for the week
        alerts = await self.postgres_repo.get_safety_alerts(
            start_time=start_date,
            end_time=end_date,
            limit=100000,
        )
        
        # Analyze weekly patterns
        patterns = self._analyze_patterns(alerts)
        
        # Generate weekly report
        report = {
            "period": {
                "start": start_date.date().isoformat(),
                "end": end_date.date().isoformat(),
            },
            "summary": {
                "total_alerts": len(alerts),
                "daily_average": round(len(alerts) / 7, 1),
                "unique_users": len(patterns["by_user"]),
                "unique_companions": len(patterns["by_companion"]),
            },
            "patterns": patterns,
            "generated_at": datetime.utcnow().isoformat(),
        }
        
        # Store
        import json
        redis_key = f"safety:consolidated:weekly:{start_date.date().isoformat()}_{end_date.date().isoformat()}"
        await self.redis_repo.client.setex(
            redis_key,
            90 * 24 * 3600,
            json.dumps(report, default=str),
        )
        
        logger.info(f"Weekly consolidation complete: {len(alerts)} alerts")
        
        return report
    
    async def run_monthly_consolidation(self, year: int, month: int) -> Dict[str, Any]:
        """Run monthly consolidation."""
        from calendar import monthrange
        
        _, last_day = monthrange(year, month)
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month, last_day, 23, 59, 59)
        
        logger.info(f"Running monthly consolidation for {year}-{month:02d}")
        
        alerts = await self.postgres_repo.get_safety_alerts(
            start_time=start_date,
            end_time=end_date,
            limit=200000,
        )
        
        patterns = self._analyze_patterns(alerts)
        
        report = {
            "period": {
                "year": year,
                "month": month,
                "start": start_date.date().isoformat(),
                "end": end_date.date().isoformat(),
            },
            "summary": {
                "total_alerts": len(alerts),
                "daily_average": round(len(alerts) / last_day, 1),
                "unique_users": len(patterns["by_user"]),
                "unique_companions": len(patterns["by_companion"]),
            },
            "patterns": patterns,
            "generated_at": datetime.utcnow().isoformat(),
        }
        
        import json
        redis_key = f"safety:consolidated:monthly:{year}-{month:02d}"
        await self.redis_repo.client.setex(
            redis_key,
            365 * 24 * 3600,  # 1 year
            json.dumps(report, default=str),
        )
        
        logger.info(f"Monthly consolidation complete: {len(alerts)} alerts")
        
        return report
    
    async def get_consolidated_report(
        self,
        period: str,  # "daily", "weekly", "monthly"
        date: Optional[datetime] = None,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a consolidated report."""
        import json
        
        if period == "daily":
            if date is None:
                date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
            key = f"safety:consolidated:daily:{date.date().isoformat()}"
        elif period == "weekly":
            if date is None:
                date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            start = date - timedelta(days=7)
            key = f"safety:consolidated:weekly:{start.date().isoformat()}_{date.date().isoformat()}"
        elif period == "monthly":
            if date is None:
                date = datetime.utcnow()
            key = f"safety:consolidated:monthly:{date.year}-{date.month:02d}"
        else:
            raise ValueError(f"Unknown period: {period}")
        
        data = await self.redis_repo.client.get(key)
        if data:
            return json.loads(data)
        
        return None
    
    async def analyze_user_safety_profile(
        self,
        user_id: str,
        days_back: int = 30,
    ) -> Dict[str, Any]:
        """Analyze safety profile for a specific user."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days_back)
        
        alerts = await self.postgres_repo.get_safety_alerts(
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            limit=1000,
        )
        
        if not alerts:
            return {
                "user_id": user_id,
                "period_days": days_back,
                "total_alerts": 0,
                "risk_level": "low",
                "message": "No safety alerts in period",
            }
        
        patterns = self._analyze_patterns(alerts)
        
        # Determine risk level
        crisis_count = patterns["by_category"].get("crisis", 0) + patterns["by_category"].get("suicide", 0) + patterns["by_category"].get("self_harm", 0)
        high_severity = patterns["by_severity"].get("critical", 0) + patterns["by_severity"].get("high", 0)
        crisis_escalations = patterns["by_intervention"].get("CRISIS_ESCALATE", 0)
        
        if crisis_count > 0 or crisis_escalations > 0:
            risk_level = "critical"
        elif high_severity > 2:
            risk_level = "high"
        elif len(alerts) > 10:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "user_id": user_id,
            "period_days": days_back,
            "total_alerts": len(alerts),
            "risk_level": risk_level,
            "crisis_count": crisis_count,
            "high_severity_count": high_severity,
            "crisis_escalations": crisis_escalations,
            "top_categories": patterns["top_categories"],
            "intervention_distribution": dict(patterns["by_intervention"]),
            "severity_distribution": dict(patterns["by_severity"]),
            "recent_alerts": [
                {
                    "alert_id": str(a.alert_id),
                    "type": a.alert_type.value if a.alert_type else "unknown",
                    "severity": a.severity,
                    "intervention": a.intervention_level.value,
                    "timestamp": a.timestamp.isoformat(),
                }
                for a in sorted(alerts, key=lambda x: x.timestamp, reverse=True)[:10]
            ],
        }