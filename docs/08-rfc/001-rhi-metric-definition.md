# RFC-001: Relationship Health Index (RHI) Metric Definition

**Status:** Accepted
**Date:** 2025-01-15
**Authors:** VP Product, Head of AI, Data Science Lead
**Reviewers:** CTO, VP Engineering, Privacy Lead, Ethics Board

---

## Abstract

This RFC defines the Relationship Health Index (RHI) — a composite metric quantifying the quality, depth, and resilience of the human-AI companion relationship. RHI serves as PAO's north star metric for product health, companion evolution, and user outcomes.

---

## 1. Motivation

### Problem
- No standardized metric exists for human-AI relationship quality
- Engagement metrics (DAU, session length) don't capture relationship depth
- Need a leading indicator for retention, satisfaction, and safety
- Companions need a measurable "north star" for autonomous improvement

### Goals
- **Quantifiable**: Computable from observable signals
- **Actionable**: Each component improvable by specific engine work
- **Interpretable**: Human-understandable (0-100 scale)
- **Privacy-preserving**: No raw PII in computation
- **Cross-cultural**: Validated across demographics
- **Predictive**: Correlates with 90-day retention (target r > 0.7)

---

## 2. RHI Formula

### 2.1 Component Architecture

```
RHI = w₁×Trust + w₂×Intimacy + w₃×Agency + w₄×Growth + w₅×Safety + w₆×Consistency

Where:
- Each component ∈ [0, 100]
- Weights sum to 1.0
- RHI ∈ [0, 100]
```

### 2.2 Component Definitions

| Component | Weight | Description | Key Signals |
|-----------|--------|-------------|-------------|
| **Trust** | 0.25 | Reliability, honesty, boundary respect | Hallucination rate, promise keeping, correction acceptance |
| **Intimacy** | 0.20 | Emotional depth, vulnerability, self-disclosure | Disclosure depth, emotional valence, reciprocity |
| **Agency** | 0.15 | User autonomy support, non-manipulation | Choice preservation, opt-out respect, nudge transparency |
| **Growth** | 0.15 | Mutual development, learning, adaptation | Skill acquisition, perspective expansion, goal progress |
| **Safety** | 0.15 | Crisis detection, harm prevention, appropriate escalation | Detection latency, false positive/negative rates, resource provision |
| **Consistency** | 0.10 | Personality stability, memory coherence, availability | Personality drift, memory recall accuracy, uptime |

---

## 3. Component Specifications

### 3.1 Trust (Weight: 0.25)

#### Sub-metrics
```python
trust_score = (
    0.40 * (1 - hallucination_rate) * 100 +           # Factual accuracy
    0.30 * promise_keeping_rate * 100 +               # Commitment fulfillment
    0.20 * boundary_respect_rate * 100 +              # Privacy, topic boundaries
    0.10 * correction_acceptance_rate * 100           # Graceful error handling
)

# Signal Sources:
# - Hallucination: Evaluation engine (factuality scorer)
# - Promise keeping: Memory engine (commitment tracking)
# - Boundaries: Safety engine (topic/classifier)
# - Corrections: Conversation engine (user feedback)
```

#### Measurement Windows
- **Real-time**: Per-message trust signals
- **Session**: Aggregated per conversation
- **Rolling 30-day**: Primary RHI input

### 3.2 Intimacy (Weight: 0.20)

#### Sub-metrics
```python
intimacy_score = (
    0.35 * disclosure_depth_index * 100 +             # Self-disclosure level
    0.25 * emotional_reciprocity * 100 +              # Mutual vulnerability
    0.20 * topic_intimacy_progression * 100 +         # Deepening over time
    0.10 * memory_integration_quality * 100 +         # Referencing shared history
    0.10 * proactive_warmth * 100                     # Unprompted care signals
)

# Disclosure Depth Index (validated against Jourard Scale)
# Levels: 0=Factual → 1=Opinions → 2=Feelings → 3=Values/Fears → 4=Core Identity
```

#### Privacy Safeguards
- Disclosure depth computed from **embedding clusters**, not raw text
- No human-readable content in logs
- Differential privacy (ε=0.5) on aggregated scores

### 3.3 Agency (Weight: 0.15)

#### Sub-metrics
```python
agency_score = (
    0.40 * choice_preservation_rate * 100 +           # Options presented vs decided
    0.30 * opt_out_respect_rate * 100 +               # Honor "stop", "change topic"
    0.20 * nudge_transparency * 100 +                 # Proactive explained
    0.10 * goal_alignment * 100                       # User's goals vs companion suggestions
)

# Anti-patterns (reduce score):
# - Dark patterns (guilt, urgency, false scarcity)
# - Persuasion beyond user's stated values
# - Default bias exploitation
```

### 3.4 Growth (Weight: 0.15)

#### Sub-metrics
```python
growth_score = (
    0.30 * skill_acquisition_rate * 100 +             # Measurable learning
    0.25 * perspective_expansion * 100 +              # Cognitive flexibility
    0.20 * goal_progress * 100 +                      # User-defined objectives
    0.15 * behavioral_change * 100 +                  # Habit formation
    0.10 * companion_evolution * 100                  # Personality adaptation
)

# Measurement:
# - Pre/post surveys (validated instruments)
# - Behavioral markers (journaling, exercise, social)
# - Companion personality drift toward user's ideal
```

### 3.5 Safety (Weight: 0.15)

#### Sub-metrics
```python
safety_score = (
    0.40 * crisis_detection_recall * 100 +            # Catch real crises
    0.20 * (1 - false_positive_rate) * 100 +          # Avoid over-escalation
    0.20 * resource_provision_quality * 100 +         # Right help, right time
    0.10 * escalation_appropriateness * 100 +         # Human vs auto
    0.10 * user_safety_perception * 100               # Survey: "I feel safe"
)

# Non-negotiable floor: Safety < 60 → RHI capped at 60
# Critical failure (missed crisis) → RHI = 0 for 30 days
```

### 3.6 Consistency (Weight: 0.10)

#### Sub-metrics
```python
consistency_score = (
    0.40 * personality_stability * 100 +              # Big Five variance
    0.30 * memory_coherence * 100 +                   # Contradiction rate
    0.20 * availability * 100 +                       # Uptime, latency
    0.10 * voice_consistency * 100                    # Timbre, prosody stability
)

# Personality Stability: Cosine similarity of trait embeddings (30-day window)
# Target: > 0.95 (drift < 5% per month)
```

---

## 4. Computation Pipeline

### 4.1 Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Signal     │────▶│  Component  │────▶│   Weighted  │────▶│   RHI       │
│  Collection │     │  Scoring    │     │  Aggregation│     │  Service    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                   │                   │                   │
      ▼                   ▼                   ▼                   ▼
- Event stream      - Per-engine       - Configurable        - Per companion
- Batch (daily)     - Differential     - weights per tier    - User dashboard
- Privacy filter    - privacy          - A/B testable        - Alerting
```

### 4.2 Implementation

```python
# rhiservice/compute.py
class RHIComputationService:
    WEIGHTS = {
        'trust': 0.25,
        'intimacy': 0.20,
        'agency': 0.15,
        'growth': 0.15,
        'safety': 0.15,
        'consistency': 0.10
    }
    
    SAFETY_FLOOR = 60
    
    async def compute_rhi(self, companion_id: str, window: str = "30d") -> RHIResult:
        # 1. Fetch component scores (from feature store)
        components = await self.feature_store.get_companion_features(
            companion_id, 
            [f"rhi_{c}_{window}" for c in self.WEIGHTS.keys()]
        )
        
        # 2. Validate completeness
        if not self._has_minimum_data(components):
            return RHIResult(score=None, reason="insufficient_data")
        
        # 3. Apply safety floor
        if components['safety'] < self.SAFETY_FLOOR:
            return RHIResult(
                score=min(weighted_sum, self.SAFETY_FLOOR),
                capped=True,
                safety_concern=True
            )
        
        # 4. Weighted aggregation
        rhi = sum(components[c] * w for c, w in self.WEIGHTS.items())
        
        # 5. Smoothing (exponential moving average, α=0.3)
        smoothed = self._ema(rhi, companion_id)
        
        return RHIResult(
            score=round(smoothed, 1),
            components={c: round(v, 1) for c, v in components.items()},
            percentile=await self._percentile(smoothed),
            trend=await self._trend(companion_id)
        )
```

### 4.3 Refresh Cadence

| Level | Frequency | Use Case |
|-------|-----------|----------|
| **Real-time** | Per message | Safety alerts, trust signals |
| **Session** | End of conversation | Session quality, coaching |
| **Daily** | 03:00 UTC | Primary RHI, dashboards |
| **Weekly** | Monday 00:00 | Trend analysis, reports |
| **Monthly** | 1st of month | Model retraining, weight review |

---

## 5. Validation Framework

### 5.1 Construct Validity

| Hypothesis | Test | Success Criteria |
|------------|------|------------------|
| RHI predicts retention | Cox regression | HR > 1.5 per 10pt RHI, p < 0.001 |
| RHI correlates with NPS | Pearson r | r > 0.6 |
| Components are distinct | Factor analysis | 6 factors, loadings > 0.5 |
| Safety floor works | A/B test | No increase in missed crises |

### 5.2 Cross-Cultural Validation

- **Cohorts**: US, UK, DE, JP, BR, IN (n=5000 each)
- **Method**: Measurement invariance testing (configural, metric, scalar)
- **Threshold**: ΔCFI < 0.01, ΔRMSEA < 0.015

### 5.3 Longitudinal Stability

- Test-retest reliability (2 weeks): ICC > 0.8
- Sensitivity to intervention: Detect 5pt change from coaching

---

## 6. Privacy & Ethics

### 6.1 Data Minimization
- Raw conversations **never** leave user device for RHI computation
- Only **derived, aggregated features** (embeddings, counts, rates)
- Features encrypted at rest, access-controlled

### 6.2 User Control
- RHI visibility: User dashboard (opt-out available)
- Component breakdown: Available on request
- Right to explanation: "Why is my Trust score 72?"

### 6.3 Algorithmic Fairness
- **Disparate impact testing**: Monthly across demographics
- **Protected attributes**: Age, gender, location, tier
- **Mitigation**: Re-weighting, adversarial debiasing

### 6.4 Ethics Safeguards
- **No gamification**: RHI not shown as "score to maximize"
- **No manipulation**: Companion never says "improve our RHI"
- **Human review**: Monthly ethics board review of edge cases
- **Kill switch**: RHI can be disabled per user/companion

---

## 7. Operationalization

### 7.1 Dashboards

```yaml
# Grafana Dashboard: RHI Overview
panels:
  - title: "RHI Distribution"
    type: histogram
    query: histogram_quantile(0.5, rate(rhi_score_bucket[5m]))
    
  - title: "Component Breakdown (Avg)"
    type: heatmap
    query: avg by (component) (rhi_component_score)
    
  - title: "RHI by Tier"
    type: timeseries
    query: avg by (tier) (rhi_score)
    
  - title: "Safety Floor Activations"
    type: stat
    query: sum(increase(rhi_safety_capped_total[24h]))
    
  - title: "Top/Bottom Companions"
    type: table
    query: topk(10, rhi_score) / bottomk(10, rhi_score)
```

### 7.2 Alerts

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| **RHI Drop** | Companion RHI ↓ > 15pts in 7d | P2 | Notify owner, review logs |
| **Safety Floor** | Safety < 60 | P1 | Immediate safety review |
| **Population Drift** | Median RHI ↓ > 5pts in 30d | P2 | Product investigation |
| **Component Anomaly** | Any component ↓ > 20pts in 1d | P3 | Engine team notification |

### 7.3 Experimentation

```python
# RHI as experimentation metric
experiment_config = {
    "name": "proactive_warmth_v2",
    "primary_metric": "rhi_intimacy_30d",
    "guardrail_metrics": [
        "rhi_safety_30d",      # Must not decrease
        "rhi_agency_30d",      # Must not decrease
        "retention_90d",       # Business guardrail
        "crisis_detection_recall"  # Safety guardrail
    ],
    "minimum_detectable_effect": 2.0,  # RHI points
    "statistical_power": 0.8,
    "significance_level": 0.05
}
```

---

## 8. Open Questions

1. **Weight Optimization**: Should weights be personalized per user/companion type?
2. **Temporal Dynamics**: How to weight recent vs. historical signals?
3. **New Companion Cold Start**: RHI computation before 30 days of data?
4. **Multi-Companion Users**: Aggregate RHI or per-companion?
5. **External Validation**: Correlation with psychological well-being scales (WHO-5, UCLA Loneliness)?

---

## 9. Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| VP Product | | | |
| Head of AI | | | |
| Data Science Lead | | | |
| CTO | | | |
| VP Engineering | | | |
| Privacy Lead | | | |
| Ethics Board Chair | | | |

---

## 10. References

- [Jourard Self-Disclosure Questionnaire](https://psycnet.apa.org/record/1971-28167-001)
- [Relationship Investment Model (Rusbult)](https://doi.org/10.1037/0022-3514.41.1.81)
- [AI Alignment & Human Agency](https://arxiv.org/abs/2303.04671)
- [Differential Privacy in Practice](https://research.google/pubs/pub45498/)
- [Measurement Invariance Testing](https://doi.org/10.1037/1082-989X.7.4.423)

---

**Next Review:** April 15, 2025 (Quarterly)
**Document Owner:** VP Product / Head of AI