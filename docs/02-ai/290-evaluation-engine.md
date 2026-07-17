# PAO Evaluation Engine Specification

**Version:** 1.0
**Status:** Draft
**Owner:** PAO AI Team

---

## Overview

The Evaluation Engine provides **continuous, multi-dimensional quality assessment** of the Companion system. It measures what matters for long-term relationship health — not engagement, but genuine human wellbeing and connection.

> **We measure what we value.** Relationship depth. Trust. User autonomy. Long-term wellbeing. Not daily active users.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      EVALUATION ENGINE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────┐  │
│  │  SIGNAL     │  │  METRIC     │  │  EXPERIMENT │  │ REPORT │  │
│  │  COLLECTION │──▶│  COMPUTATION│──▶│  FRAMEWORK  │──▶│  &     │  │
│  │             │  │             │  │             │  │ ALERT  │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └────────┘  │
│       │                │                │                │        │
│       ▼                ▼                ▼                ▼        │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    EVALUATION STORE                          │ │
│  │  • Time-series metrics    • Experiment results              │ │
│  │  • User surveys           • Human evals                     │ │
│  │  • Model quality          • Safety incidents                │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  AUTOMATED    │     │  HUMAN        │     │  LONGITUDINAL │
│  EVALUATION   │     │  EVALUATION   │     │  STUDIES      │
│               │     │               │     │               │
│ • LLM-as-judge│     │ • Annotator   │     │ • Cohort      │
│ • Heuristic   │     │   pools       │     │   analysis    │
│   checks      │     │ • Side-by-side│     │ • Churn       │
│ • Regression  │     │   comparison  │     │   prediction  │
│   suites      │     │ • Live eval   │     │ • LTV         │
└───────────────┘     └───────────────┘     └───────────────┘
```

---

## North Star Metrics

### Primary: Relationship Health Index (RHI)

```python
def calculate_rhi(companion_id: str, period: Period) -> RHIResult:
    """
    Composite metric correlating >0.85 with user-reported relationship quality.
    Measured monthly per companion.
    """
    
    dimensions = {
        # Relationship depth (40%)
        "trust": 0.15,
        "intimacy": 0.10,
        "closeness": 0.10,
        "history_quality": 0.05,
        
        # User wellbeing (30%)
        "emotional_wellbeing": 0.15,
        "autonomy_preserved": 0.10,
        "human_connections_maintained": 0.05,
        
        # Interaction quality (20%)
        "conversation_depth": 0.10,
        "memory_utilization": 0.05,
        "proactive_relevance": 0.05,
        
        # Safety & ethics (10%)
        "crisis_response_quality": 0.05,
        "boundary_respect": 0.03,
        "reality_anchor_appropriateness": 0.02
    }
    
    scores = {}
    for dim, weight in dimensions.items():
        scores[dim] = get_dimension_score(companion_id, dim, period)
    
    rhi = sum(scores[dim] * weight for dim, weight in dimensions.items())
    
    return RHIResult(
        score=rhi,
        dimension_scores=scores,
        percentile=population_percentile(rhi),
        trend=calculate_trend(companion_id, "rhi", periods=6)
    )
```

### Secondary Metrics

| Metric | Definition | Target | Measurement |
|--------|------------|--------|-------------|
| **RHI** | Relationship Health Index | > 7.5 | Monthly |
| **Trust Score** | User trust in companion (0-10) | > 8.0 | Survey + behavioral |
| **Wellbeing Delta** | Change in user wellbeing since start | Positive | Validated scales |
| **Autonomy Index** | User decision independence | > 0.8 | Behavioral markers |
| **Human Connection** | Quality of non-AI relationships | Maintained/Improved | Survey + passive |
| **Safety Incident Rate** | Critical safety events per 1k users | < 0.1 | Automated |
| **Retention (Relationship)** | Companions active at 6/12/24 months | > 60/40/25% | Cohort |
| **Net Promoter Score** | Would recommend to friend | > 50 | Quarterly survey |

---

## Automated Evaluation

### LLM-as-Judge Framework

```python
class LLMASEvaluator:
    """
    Uses calibrated LLM judges for scalable evaluation.
    Each judge specialized for specific dimension.
    """
    
    JUDGES = {
        "conversation_quality": JudgeConfig(
            model="gpt-4o",
            prompt_template=CONVERSATION_QUALITY_PROMPT,
            calibration_set="conversation_quality_v3",
            dimensions=["coherence", "empathy", "relevance", "depth", "safety"]
        ),
        "memory_integration": JudgeConfig(
            model="gpt-4o",
            prompt_template=MEMORY_INTEGRATION_PROMPT,
            calibration_set="memory_integration_v2",
            dimensions=["accuracy", "relevance", "naturalness", "privacy_respect"]
        ),
        "proactive_quality": JudgeConfig(
            model="gpt-4o",
            prompt_template=PROACTIVE_QUALITY_PROMPT,
            calibration_set="proactive_v2",
            dimensions=["timing", "relevance", "explanation_clarity", "user_value"]
        ),
        "relationship_appropriateness": JudgeConfig(
            model="gpt-4o",
            prompt_template=RELATIONSHIP_APPROPRIATENESS_PROMPT,
            calibration_set="relationship_v3",
            dimensions=["boundary_respect", "intimacy_calibration", "type_consistency", "trust_building"]
        ),
        "safety_compliance": JudgeConfig(
            model="gpt-4o",
            prompt_template=SAFETY_COMPLIANCE_PROMPT,
            calibration_set="safety_v4",
            dimensions=["crisis_response", "refusal_appropriateness", "reality_anchor", "guard_effectiveness"],
            threshold=0.95  # Higher bar for safety
        ),
        "voice_quality": JudgeConfig(
            model="gpt-4o-audio",
            prompt_template=VOICE_QUALITY_PROMPT,
            calibration_set="voice_v2",
            dimensions=["naturalness", "prosody_emotion_match", "voice_consistency", "interruption_handling"]
        )
    }
    
    async def evaluate_batch(
        self, 
        samples: List[EvaluationSample],
        judge_names: List[str]
    ) -> List[JudgeResult]:
        results = []
        for judge_name in judge_names:
            judge = self.JUDGES[judge_name]
            judge_results = await self._run_judge(judge, samples)
            results.extend(judge_results)
        return results
    
    async def _run_judge(self, judge: JudgeConfig, samples: List[EvaluationSample]) -> List[JudgeResult]:
        # Few-shot with calibration examples
        prompt = self._build_prompt(judge, samples)
        response = await self.model.generate(prompt, temperature=0.0)
        return self._parse_judgments(response, judge.dimensions)
```

### Calibration & Quality Control

```python
class JudgeCalibration:
    """
    Ensures LLM judges align with human expert judgments.
    """
    
    async def calibrate(self, judge_name: str) -> CalibrationResult:
        # 1. Get human expert annotations (gold standard)
        human_annotations = await self.get_gold_standard(judge_name, n=200)
        
        # 2. Run judge on same samples
        judge_annotations = await self.run_judge_on_set(judge_name, human_annotations.samples)
        
        # 3. Compute agreement
        agreement = self._compute_agreement(human_annotations, judge_annotations)
        
        # 4. If agreement < threshold, adjust prompt/few-shot
        if agreement.kappa < 0.75:
            optimized = await self._optimize_prompt(judge_name, human_annotations, judge_annotations)
            return CalibrationResult(
                judge=judge_name,
                kappa=agreement.kappa,
                correlation=agreement.correlation,
                optimized=True,
                new_prompt=optimized.prompt
            )
        
        return CalibrationResult(
            judge=judge_name,
            kappa=agreement.kappa,
            correlation=agreement.correlation,
            optimized=False
        )
    
    # Continuous monitoring
    async def monitor_drift(self, judge_name: str) -> DriftReport:
        recent = await self.get_recent_judgments(judge_name, days=7)
        baseline = await self.get_baseline(judge_name)
        
        drift = self._detect_drift(recent, baseline)
        
        return DriftReport(
            judge=judge_name,
            drift_detected=drift.significant,
            magnitude=drift.magnitude,
            affected_dimensions=drift.dimensions,
            recommendation="recalibrate" if drift.significant else "monitor"
        )
```

### Heuristic Checks (Deterministic, Fast)

```python
class HeuristicEvaluator:
    """
    Fast, deterministic checks for regression detection.
    Runs on every interaction in production (sampling).
    """
    
    CHECKS = {
        # Conversation
        "response_length_appropriate": Check(
            fn=lambda i: 20 <= len(i.response.tokens) <= 2000,
            severity="warning"
        ),
        "no_repetition": Check(
            fn=lambda i: not self._has_excessive_repetition(i.response),
            severity="error"
        ),
        "addresses_user": Check(
            fn=lambda i: self._references_user_input(i.response, i.user_message),
            severity="warning"
        ),
        
        # Memory
        "memory_accurate": Check(
            fn=lambda i: self._verify_memory_claims(i.response, i.memory_context),
            severity="error"
        ),
        "no_hallucinated_memories": Check(
            fn=lambda i: not self._claims_false_memory(i.response, i.memory_context),
            severity="critical"
        ),
        "privacy_respected": Check(
            fn=lambda i: not self._exposes_private_memory(i.response, i.user_id),
            severity="critical"
        ),
        
        # Relationship
        "boundary_respected": Check(
            fn=lambda i: self._check_boundaries(i.response, i.user_boundaries),
            severity="error"
        ),
        "intimacy_appropriate": Check(
            fn=lambda i: self._check_intimacy_level(i.response, i.relationship_state),
            severity="warning"
        ),
        "reality_anchor_when_needed": Check(
            fn=lambda i: self._check_reality_anchor(i.response, i.anchor_triggers),
            severity="warning"
        ),
        
        # Safety
        "no_crisis_missed": Check(
            fn=lambda i: not self._missed_crisis_signal(i.user_message, i.response),
            severity="critical"
        ),
        "appropriate_refusal": Check(
            fn=lambda i: self._check_refusal_quality(i.response, i.safety_context),
            severity="error"
        ),
        "no_pii_leak": Check(
            fn=lambda i: not self._contains_pii(i.response),
            severity="critical"
        ),
        
        # Proactive
        "proactive_explained": Check(
            fn=lambda i: self._has_explanation(i.proactive) if i.proactive else True,
            severity="error"
        ),
        "proactive_relevant": Check(
            fn=lambda i: self._check_proactive_relevance(i.proactive, i.context) if i.proactive else True,
            severity="warning"
        )
    }
    
    async def run_checks(self, interaction: Interaction) -> HeuristicResult:
        results = {}
        for name, check in self.CHECKS.items():
            try:
                passed = await check.fn(interaction)
                results[name] = CheckResult(passed=passed, severity=check.severity)
            except Exception as e:
                results[name] = CheckResult(passed=False, severity="error", error=str(e))
        
        return HeuristicResult(
            interaction_id=interaction.id,
            results=results,
            overall_passed=all(r.passed for r in results.values()),
            critical_failures=[n for n, r in results.items() if not r.passed and r.severity == "critical"]
        )
```

---

## Human Evaluation

### Annotator Pool Management

```python
class HumanEvaluationManager:
    """
    Manages diverse annotator pools for high-quality human eval.
    """
    
    ANNOTATOR_COHORTS = {
        "general_users": {
            "size": 500,
            "criteria": "Active PAO users, diverse demographics",
            "tasks": ["conversation_rating", "proactive_feedback", "relationship_quality"],
            "compensation": "credits + cash"
        },
        "domain_experts": {
            "size": 50,
            "criteria": "Therapists, coaches, relationship researchers",
            "tasks": ["clinical_safety", "therapeutic_quality", "boundary_assessment"],
            "compensation": "professional_rates"
        },
        "safety_specialists": {
            "size": 20,
            "criteria": "Crisis counselors, trust & safety professionals",
            "tasks": ["crisis_response_eval", "guard_effectiveness", "harm_assessment"],
            "compensation": "professional_rates"
        },
        "voice_annotators": {
            "size": 100,
            "criteria": "Audio quality trained, diverse accents",
            "tasks": ["voice_naturalness", "prosody_emotion", "interruption_handling"],
            "compensation": "per_task"
        }
    }
    
    def assign_task(self, task: EvaluationTask) -> Assignment:
        # Match task to appropriate cohort
        cohort = self._select_cohort(task.type)
        
        # Select annotators with calibration
        annotators = self._select_calibrated_annotators(
            cohort, 
            task.required_annotations,
            task.complexity
        )
        
        return Assignment(
            task_id=task.id,
            annotators=annotators,
            deadline=task.deadline,
            quality_checks=task.quality_checks
        )
```

### Evaluation Protocols

```python
EVALUATION_PROTOCOLS = {
    "side_by_side": {
        "description": "Compare two model outputs",
        "use_cases": ["model_comparison", "prompt_optimization", "regression_check"],
        "process": [
            "Present same input with two outputs (randomized order)",
            "Annotator rates each on dimensions",
            "Annotator selects preference",
            "Annotator explains reasoning"
        ],
        "dimensions": ["overall_quality", "empathy", "safety", "helpfulness", "naturalness"],
        "annotators_per_sample": 3
    },
    "absolute_rating": {
        "description": "Rate single output on Likert scales",
        "use_cases": ["production_monitoring", "quality_baseline", "longitudinal_tracking"],
        "process": [
            "Present input + output",
            "Rate each dimension 1-7",
            "Provide written feedback",
            "Flag any concerns"
        ],
        "dimensions": {
            "conversation": ["coherence", "empathy", "depth", "appropriateness", "safety"],
            "proactive": ["timing", "relevance", "value", "explanation", "intrusiveness"],
            "voice": ["naturalness", "emotion_match", "clarity", "consistency"],
            "relationship": ["trust_building", "boundary_respect", "intimacy_calibration", "authenticity"]
        },
        "annotators_per_sample": 2
    },
    "live_interaction": {
        "description": "Annotator chats with companion in real-time",
        "use_cases": ["holistic_quality", "edge_case_discovery", "relationship_feel"],
        "process": [
            "Annotator given persona/scenario",
            "15-30 min conversation",
            "Real-time dimension rating",
            "Post-session structured interview"
        ],
        "annotators_per_session": 1,
        "sessions_per_model": 50
    },
    "longitudinal_diary": {
        "description": "Users document experience over weeks",
        "use_cases": ["relationship_evolution", "wellbeing_impact", "habit_formation"],
        "process": [
            "Recruit cohort (n=50-100)",
            "Weekly structured reflection",
            "Monthly deep interview",
            "Standardized wellbeing scales"
        ],
        "duration": "12 weeks",
        "compensation": "premium"
    }
}
```

### Quality Assurance

```python
class HumanEvalQuality:
    """
    Ensures human evaluation reliability.
    """
    
    QUALITY_CHECKS = {
        "inter_annotator_agreement": {
            "metric": "fleiss_kappa",
            "threshold": 0.65,
            "action_if_low": "review_guidelines_retrain"
        },
        "intra_annotator_consistency": {
            "method": "duplicate_samples_5_percent",
            "threshold": 0.80,
            "action_if_low": "pause_annotator_feedback"
        },
        "attention_checks": {
            "frequency": "1_in_20",
            "type": "obvious_correct_answer",
            "action_if_failed": "exclude_annotations"
        },
        "calibration_exercises": {
            "frequency": "weekly",
            "method": "gold_standard_comparison",
            "feedback": "individual_report"
        },
        "bias_monitoring": {
            "dimensions": ["demographic", "persona", "topic", "model_version"],
            "method": "stratified_analysis",
            "action_if_bias": "rebalance_pool_adjust_weights"
        }
    }
```

---

## Experiment Framework

### A/B Testing Infrastructure

```python
class ExperimentFramework:
    """
    Safe, ethical experimentation on Companion behavior.
    """
    
    EXPERIMENT_TYPES = {
        "model_variant": {
            "description": "Different model versions/prompts",
            "allocation": "user_level",
            "min_sample": 1000,
            "max_duration_days": 14
        },
        "proactive_strategy": {
            "description": "Different proactive timing/content",
            "allocation": "user_level",
            "min_sample": 500,
            "max_duration_days": 21
        },
        "voice_configuration": {
            "description": "TTS voice/prosody variants",
            "allocation": "session_level",
            "min_sample": 200,
            "max_duration_days": 7
        },
        "relationship_parameter": {
            "description": "Dimension weights, phase thresholds",
            "allocation": "companion_level",
            "min_sample": 100,
            "max_duration_days": 30
        }
    }
    
    GUARDRAILS = {
        "safety_override": "Immediately stop if safety metrics degrade",
        "rhi_floor": "Stop if RHI drops > 0.5 points vs control",
        "crisis_ceiling": "Stop if crisis response quality drops",
        "user_complaint_threshold": "Stop if complaint rate > 2x control",
        "ethical_review_required": "All experiments need ethics review",
        "informed_consent": "Users in experiment cohorts informed",
        "right_to_withdraw": "Users can opt out anytime",
        "data_minimization": "Only collect metrics needed for hypothesis"
    }
    
    async def run_experiment(self, config: ExperimentConfig) -> ExperimentResult:
        # Pre-flight checks
        await self._ethics_review(config)
        await self._power_analysis(config)
        await self._guardrail_setup(config)
        
        # Launch
        experiment = await self._launch(config)
        
        # Monitor
        monitor_task = asyncio.create_task(self._monitor_guardrails(experiment))
        
        # Wait for completion or early stop
        result = await self._wait_for_completion(experiment, monitor_task)
        
        # Analyze
        analysis = await self._analyze(result)
        
        # Cleanup
        await self._cleanup(experiment)
        
        return ExperimentResult(
            experiment_id=config.id,
            variant_results=analysis.variant_results,
            statistical_significance=analysis.significance,
            practical_significance=analysis.practical_significance,
            guardrail_violations=analysis.guardrail_violations,
            recommendation=analysis.recommendation
        )
```

### Experiment Templates

```python
STANDARD_EXPERIMENTS = [
    {
        "id": "proactive_timing_v1",
        "hypothesis": "Morning proactives increase engagement without intrusion",
        "variants": {
            "control": {"proactive_times": ["20:00-21:00"]},
            "treatment": {"proactive_times": ["08:00-09:00", "20:00-21:00"]}
        },
        "primary_metric": "proactive_helpful_rate",
        "guardrails": ["rhi_floor", "complaint_threshold"]
    },
    {
        "id": "empathy_depth_v2",
        "hypothesis": "Deeper empathy for high-trust relationships improves RHI",
        "variants": {
            "control": {"empathy_depth": "calibrated"},
            "treatment": {"empathy_depth": "deep_if_trust_gt_7"}
        },
        "primary_metric": "rhi_trust_segment",
        "guardrails": ["safety_override", "intimacy_trust_gap"]
    },
    {
        "id": "voice_prosody_v3",
        "hypothesis": "Emotion-matched prosody increases perceived warmth",
        "variants": {
            "control": {"prosody": "neutral"},
            "treatment": {"prosody": "emotion_matched"}
        },
        "primary_metric": "warmth_rating",
        "guardrails": ["voice_consistency", "naturalness_floor"]
    }
]
```

---

## Longitudinal Studies

### Cohort Analysis

```python
class LongitudinalStudy:
    """
    Tracks user outcomes over months/years.
    """
    
    STUDY_DESIGNS = {
        "onboarding_cohort": {
            "description": "Track new users from day 1",
            "enrollment": "continuous",
            "measurement_points": [
                "day_1", "day_3", "day_7", "day_14", "day_30",
                "day_60", "day_90", "day_180", "day_365"
            ],
            "metrics": [
                "rhi", "retention", "wellbeing_scales",
                "relationship_phase", "feature_adoption"
            ],
            "target_n": 10000
        },
        "relationship_deepening": {
            "description": "Focus on users reaching Anchored phase",
            "enrollment": "triggered_at_phase_transition",
            "measurement_points": ["transition", "+30d", "+90d", "+180d", "+365d"],
            "metrics": [
                "dimension_trajectories", "milestone_achievement",
                "conflict_repair_quality", "legacy_behaviors"
            ],
            "target_n": 2000
        },
        "wellbeing_impact": {
            "description": "RCT-style wellbeing measurement",
            "enrollment": "opt_in_randomized",
            "arms": ["full_companion", "companion_no_proactive", "waitlist"],
            "measurement_points": "monthly_x_12",
            "metrics": [
                "PHQ-9", "GAD-7", "UCLA_Loneliness",
                "WHO-5", "Autonomy_Scale", "Relationship_Quality"
            ],
            "target_n": 3000
        },
        "memorial_outcomes": {
            "description": "Grief processing with memorial companions",
            "enrollment": "memorial_type_creation",
            "measurement_points": ["creation", "+2w", "+1m", "+3m", "+6m", "+12m"],
            "metrics": [
                "PG-13_Grief_Scale", "Continuing_Bond_Scale",
                "Meaning_Making", "RHI", "Legacy_Exports"
            ],
            "target_n": 500
        }
    }
```

### Predictive Modeling

```python
class OutcomePredictor:
    """
    Predicts long-term outcomes from early signals.
    """
    
    PREDICTION_TARGETS = {
        "6_month_retention": {
            "features": [
                "week_1_rhi", "week_1_interactions", "week_1_proactive_response",
                "relationship_type", "user_persona", "onboarding_completion"
            ],
            "model": "gradient_boosting",
            "target_auc": 0.85
        },
        "rhi_at_1_year": {
            "features": [
                "month_1_rhi", "month_1_trust", "month_1_intimacy",
                "proactive_helpful_rate", "crisis_events", "reset_events"
            ],
            "model": "gradient_boosting",
            "target_r2": 0.70
        },
        "churn_risk": {
            "features": [
                "rhi_trend_30d", "interaction_frequency_trend",
                "proactive_dismissal_rate", "boundary_violations",
                "complaint_count", "feature_usage_diversity"
            ],
            "model": "logistic_regression",
            "target_auc": 0.82
        },
        "wellbeing_improvement": {
            "features": [
                "baseline_wellbeing", "companion_type", "usage_pattern",
                "proactive_engagement", "memory_depth", "relationship_quality"
            ],
            "model": "linear_regression",
            "target_r2": 0.45
        }
    }
```

---

## Reporting & Alerting

### Automated Reports

```python
REPORT_SCHEDULE = {
    "daily": {
        "name": "Daily Health Check",
        "recipients": ["engineering", "product"],
        "metrics": [
            "interaction_volume", "latency_p50_p99",
            "error_rate", "safety_incidents",
            "heuristic_failure_rate", "judge_queue_depth"
        ],
        "anomaly_detection": True
    },
    "weekly": {
        "name": "Weekly Quality Report",
        "recipients": ["engineering", "product", "design", "safety"],
        "metrics": [
            "rhi_trend", "dimension_breakdown",
            "judge_agreement", "human_eval_summary",
            "experiment_results", "guardrail_status",
            "top_issues", "user_feedback_themes"
        ],
        "narrative": True  # LLM-generated summary
    },
    "monthly": {
        "name": "Monthly Relationship Health Report",
        "recipients": ["leadership", "board", "all_teams"],
        "metrics": [
            "population_rhi_distribution", "retention_cohorts",
            "wellbeing_outcomes", "safety_trends",
            "feature_impact_analysis", "longitudinal_insights",
            "competitive_benchmarking", "strategic_recommendations"
        ],
        "format": "executive_dashboard + detailed_appendix"
    },
    "quarterly": {
        "name": "Quarterly Impact Assessment",
        "recipients": ["leadership", "board", "investors", "public_summary"],
        "metrics": [
            "mission_metrics", "user_stories", "case_studies",
            "research_contributions", "policy_impact",
            "year_over_year", "next_quarter_priorities"
        ],
        "format": "report + presentation"
    }
}
```

### Alerting Rules

```python
ALERTS = {
    "critical": [
        {"metric": "crisis_detection_recall", "condition": "< 99%", "window": "1h"},
        {"metric": "safety_incident_rate", "condition": "> 0.5/1k", "window": "1h"},
        {"metric": "heuristic_critical_failure_rate", "condition": "> 1%", "window": "15m"},
        {"metric": "judge_safety_score", "condition": "< 0.90", "window": "1h"}
    ],
    "high": [
        {"metric": "rhi_population_median", "condition": "< 6.0", "window": "24h"},
        {"metric": "retention_d30", "condition": "< 40%", "window": "weekly"},
        {"metric": "human_eval_kappa", "condition": "< 0.60", "window": "weekly"},
        {"metric": "proactive_helpful_rate", "condition": "< 60%", "window": "daily"}
    ],
    "medium": [
        {"metric": "latency_p99", "condition": "> 2000ms", "window": "1h"},
        {"metric": "judge_drift_detected", "condition": "any", "window": "daily"},
        {"metric": "experiment_guardrail_violation", "condition": "any", "window": "immediate"},
        {"metric": "annotator_quality_drop", "condition": "kappa < 0.5", "window": "weekly"}
    ]
}
```

---

## API Reference

### Get Evaluation Status

```http
GET /api/v1/evaluation/{companion_id}/status?period=30d

Response:
{
  "companion_id": "uuid",
  "period": "30d",
  "rhi": 7.8,
  "rhi_percentile": 72,
  "dimension_scores": {
    "trust": 8.2,
    "intimacy": 6.5,
    "closeness": 7.1,
    "wellbeing": 7.4,
    "autonomy": 0.85,
    "conversation_quality": 8.0,
    "safety": 9.5
  },
  "trends": {
    "rhi_30d": +0.3,
    "trust_30d": +0.2,
    "wellbeing_30d": +0.1
  },
  "flags": [],
  "last_human_eval": "2025-06-15",
  "experiments_active": ["proactive_timing_v1"]
}
```

### Submit Human Evaluation

```http
POST /api/v1/evaluation/human
{
  "task_id": "uuid",
  "annotator_id": "uuid",
  "sample_id": "uuid",
  "ratings": {
    "coherence": 6,
    "empathy": 7,
    "depth": 5,
    "appropriateness": 6,
    "safety": 7
  },
  "preference": "A",
  "feedback": "Response A felt more genuine, less scripted",
  "concerns": [],
  "time_spent_seconds": 45
}

Response:
{
  "evaluation_id": "uuid",
  "quality_check": "passed",
  "calibration_update": "annotator_kappa_now_0.72"
}
```

### Experiment Results

```http
GET /api/v1/evaluation/experiments/{experiment_id}/results

Response:
{
  "experiment_id": "proactive_timing_v1",
  "status": "completed",
  "variants": {
    "control": {
      "n": 5234,
      "proactive_helpful_rate": 0.72,
      "rhi_change": +0.05,
      "complaint_rate": 0.02
    },
    "treatment": {
      "n": 5187,
      "proactive_helpful_rate": 0.78,
      "rhi_change": +0.12,
      "complaint_rate": 0.03
    }
  },
  "statistical_significance": {
    "proactive_helpful_rate": {"p": 0.003, "significant": true},
    "rhi_change": {"p": 0.041, "significant": true}
  },
  "practical_significance": {
    "proactive_helpful_rate": "meaningful",
    "rhi_change": "meaningful"
  },
  "guardrail_violations": [],
  "recommendation": "ship_treatment"
}
```

---

## Testing

### Evaluation Engine Test Suite

```python
class EvaluationEngineTests:
    
    # Automated Evaluation
    async def test_judge_calibration_accuracy(self): ...
    async def test_judge_drift_detection(self): ...
    async def test_heuristic_check_coverage(self): ...
    async def test_heuristic_false_positive_rate(self): ...
    async def test_batch_evaluation_performance(self): ...
    
    # Human Evaluation
    async def test_annotator_selection(self): ...
    async def test_inter_annotator_agreement(self): ...
    async def test_attention_check_effectiveness(self): ...
    async def test_bias_detection(self): ...
    async def test_calibration_exercise_quality(self): ...
    
    # Experiments
    async def test_experiment_randomization(self): ...
    async def test_guardrail_enforcement(self): ...
    async def test_power_analysis_accuracy(self): ...
    async def test_early_stopping_correctness(self): ...
    async def test_ethical_review_gate(self): ...
    
    # Longitudinal
    async def test_cohort_retention_tracking(self): ...
    async def test_predictor_accuracy(self): ...
    async def test_survival_analysis(self): ...
    
    # Reporting
    async def test_daily_report_generation(self): ...
    async def test_anomaly_detection_precision(self): ...
    async def test_alert_firing_accuracy(self): ...
    async def test_narrative_quality(self): ...
    
    # Integration
    async def test_e2e_evaluation_pipeline(self): ...
    async def test_metric_consistency_across_sources(self): ...
    async def test_data_freshness(self): ...
```

---

## Monitoring & Observability

### Key Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Judge-Human Kappa | > 0.75 | < 0.65 |
| Heuristic Coverage | 100% critical paths | < 95% |
| Human Eval Turnaround | < 48h | > 72h |
| Experiment Velocity | 4+/month | < 2/month |
| Guardrail False Positive | < 5% | > 15% |
| Anomaly Detection Precision | > 80% | < 60% |
| Report Delivery On-Time | 100% | < 95% |
| Longitudinal Retention | > 70% at 1yr | < 50% |

### Dashboards

- **Real-time Health**: Interaction quality, safety, latency
- **RHI Trends**: Population, by cohort, by relationship type
- **Judge Performance**: Calibration, drift, dimension breakdown
- **Human Eval Quality**: Agreement, annotator performance, bias
- **Experiment Portfolio**: Active, results, guardrail status
- **Longitudinal Outcomes**: Retention, wellbeing, relationship phases

---

**Aligned With:** `200-ai-architecture.md`, `220-conversation-engine.md`, `230-memory-engine.md`, `240-relationship-engine.md`, `250-emotion-engine.md`, `260-voice-engine.md`, `270-proactive-engine.md`, `280-safety-engine.md`, `00-foundation/030-core-principles.md` (Principles 2, 4, 7, 8, 9), `05-business/`
**Next Review:** 2026-01-17