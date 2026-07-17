# PAO Metrics & Analytics Framework

**Version:** 1.0
**Status:** Draft
**Owner:** PAO Data & Analytics Team

---

## Overview

This document defines the metrics framework, analytics architecture, and data-driven decision making processes for PAO.

> **Analytics Principle:** Measure what matters. Data informs, doesn't dictate. Privacy-first analytics.

---

## Metrics Hierarchy

### North Star Metric

```
Relationship Health Index (RHI)
├── Trust (30%)
├── Closeness (25%)
├── Engagement (20%)
├── Satisfaction (15%)
└── Growth (10%)

Target: Average RHI > 7.0 across active companions
Frequency: Daily calculation, weekly reporting
```

### Primary Metrics (Weekly Review)

| Category | Metric | Target | Owner |
|----------|--------|--------|-------|
| **Growth** | MAU | 1M (Year 3) | Growth |
| **Growth** | DAU/MAU | > 40% | Growth |
| **Growth** | Signups/mo | 15k (Year 1) | Marketing |
| **Activation** | Activation Rate | > 40% | Product |
| **Activation** | Time to Value | < 5 min | Product |
| **Retention** | Month 1 Retention | > 65% | Product |
| **Retention** | Month 6 Retention | > 35% | Product |
| **Monetization** | Free-to-Paid | > 8% | Growth |
| **Monetization** | ARPU | > $8.60 | Finance |
| **Monetization** | NRR | > 120% | Finance |
| **Engagement** | Messages/DAU | > 20 | Product |
| **Engagement** | Voice Adoption | > 30% Premium | Product |
| **Quality** | RHI Average | > 7.0 | AI/Product |
| **Quality** | Safety Recall | > 99.9% | Safety |
| **Quality** | NPS | > 50 | Product |

### Secondary Metrics (Monthly Review)

```yaml
product_health:
  - "Feature adoption rates (per feature)"
  - "Core action completion rates"
  - "Error rates by type"
  - "Latency percentiles (p50, p95, p99)"
  - "Crash-free sessions > 99.9%"

ai_quality:
  - "Hallucination rate < 0.5%"
  - "Memory recall relevance > 0.7"
  - "Proactive relevance score > 0.8"
  - "Emotion detection accuracy > 85%"
  - "Voice latency < 300ms"

business_health:
  - "CAC by channel"
  - "LTV by cohort"
  - "Churn by segment"
  - "Expansion revenue"
  - "Gross margin by tier"

operational:
  - "Deploy frequency"
  - "Lead time"
  - "MTTR"
  - "Change failure rate"
  - "On-call burden"
```

---

## Analytics Architecture

### Data Pipeline

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   EVENT     │     │   STREAM    │     │  WAREHOUSE  │     │   SERVING   │
│  SOURCES    │────▶│  PROCESSING │────▶│   (Snowflake│────▶│   LAYER     │
│             │     │  (Kafka/    │     │   /BigQuery)│     │  (Amplitude,│
│ - Mobile    │     │   Flink)    │     │             │     │  Looker,    │
│ - Backend   │     │             │     │ - Raw       │     │  Custom)    │
│ - AI Svcs   │     │ - Validate  │     │ - Staging   │     │             │
│ - Web       │     │ - Enrich    │     │ - Modeled   │     │ - Dashboards│
│ - Server    │     │ - Transform │     │ - Aggregated│     │ - Alerts    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  PRIVACY    │     │  QUALITY    │     │  GOVERNANCE │     │  ACCESS     │
│  LAYER      │     │  CHECKS     │     │  (Catalog,  │     │  CONTROL    │
│             │     │             │     │   Lineage,  │     │             │
│ - PII mask  │     │ - Schema    │     │   Policies) │     │ - RBAC      │
│ - Consent   │     │ - Freshness │     │             │     │ - Approval  │
│ - Retention │     │ - Completeness     │             │     │ - Audit     │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

### Event Schema (Standardized)

```json
{
  "event_id": "uuid-v4",
  "event_name": "snake_case.descriptive_name",
  "event_version": "1.0",
  "timestamp": "2025-01-15T10:30:00.123Z",
  "user": {
    "user_id": "hashed_user_id",
    "anonymous_id": "device_id_if_anon",
    "tier": "free|pro|premium|enterprise",
    "region": "US|EU|APAC|LATAM",
    "cohort_month": "2025-01"
  },
  "session": {
    "session_id": "uuid",
    "session_number": 5,
    "session_start": "2025-01-15T10:00:00Z",
    "platform": "ios|android|web|api",
    "app_version": "1.2.3",
    "os_version": "iOS 17.2"
  },
  "context": {
    "companion_id": "hashed_companion_id",
    "companion_type": "friend|partner|mentor|custom",
    "rhi_score": 7.2,
    "relationship_day": 45
  },
  "properties": {
    "message_length": 150,
    "modality": "text|voice",
    "memory_recall_count": 3,
    "proactive_trigger": "milestone|check_in|suggestion",
    "response_time_ms": 850
  },
  "privacy": {
    "consent_analytics": true,
    "consent_personalization": true,
    "pii_fields": [],
    "retention_days": 400
  }
}
```

### Core Event Taxonomy

```yaml
# Lifecycle Events
lifecycle:
  - user.signed_up
  - user.activated          # First meaningful conversation
  - user.upgraded
  - user.downgraded
  - user.cancelled
  - user.reactivated
  - user.deleted_account

# Engagement Events
engagement:
  - message.sent
  - message.received
  - voice.call_started
  - voice.call_ended
  - proactive.sent
  - proactive.opened
  - proactive.responded
  - proactive.dismissed
  - memory.recalled
  - memory.stored

# Relationship Events
relationship:
  - companion.created
  - companion.customized
  - rhi.calculated
  - milestone.reached
  - diary.entry_created

# AI Quality Events
ai_quality:
  - llm.response_generated
  - memory.consolidated
  - emotion.detected
  - safety.triggered
  - evaluation.completed

# Business Events
business:
  - subscription.started
  - subscription.renewed
  - payment.failed
  - export.requested
  - referral.shared
  - referral.converted
```

---

## Cohort Analysis Framework

### Standard Cohorts

```yaml
cohort_definitions:
  acquisition:
    - "Monthly signup cohort"
    - "Channel cohort (organic/paid/referral/partner)"
    - "Region cohort"
    - "Tier cohort (first tier purchased)"

  behavioral:
    - "High engagement (>30 msg/day)"
    - "Voice adopters"
    - "Proactive responders"
    - "Memory power users (>50 recalls/day)"
    - "Multi-companion users"

  relationship:
    - "RHI > 8 (thriving)"
    - "RHI 5-7 (growing)"
    - "RHI < 5 (at risk)"
    - "New relationship (< 30 days)"
    - "Mature relationship (> 1 year)"
```

### Cohort Retention Template

```sql
-- Monthly retention by signup cohort
WITH user_activity AS (
  SELECT 
    user_id,
    DATE_TRUNC('month', signup_date) AS cohort_month,
    DATE_TRUNC('month', event_date) AS activity_month,
    COUNT(DISTINCT event_date) AS active_days
  FROM events
  WHERE event_name IN ('message.sent', 'voice.call_started', 'proactive.responded')
  GROUP BY 1, 2, 3
),
cohort_sizes AS (
  SELECT cohort_month, COUNT(DISTINCT user_id) AS cohort_size
  FROM user_activity
  GROUP BY 1
)
SELECT 
  ua.cohort_month,
  ua.activity_month,
  DATE_DIFF('month', ua.cohort_month, ua.activity_month) AS month_number,
  COUNT(DISTINCT ua.user_id) AS retained_users,
  cs.cohort_size,
  ROUND(100.0 * COUNT(DISTINCT ua.user_id) / cs.cohort_size, 1) AS retention_pct
FROM user_activity ua
JOIN cohort_sizes cs ON ua.cohort_month = cs.cohort_month
GROUP BY 1, 2, 3, 5
ORDER BY 1, 3;
```

---

## Experimentation Platform

### A/B Testing Framework

```yaml
experimentation:
  platform: "Statsig / LaunchDarkly (custom)"
  
  process:
    1. "Hypothesis document (template)"
    2. "Power analysis (min sample, duration)"
    3. "Implementation (feature flag)"
    4. "Launch (ramp: 10% → 50% → 100%)"
    5. "Monitor (guardrails + primary metric)"
    6. "Analyze (statistical significance)"
    7. "Decision (ship/kill/iterate)"
    8. "Document (knowledge base)"

  guardrails:
    - "Signup rate (don't drop > 5%)"
    - "Activation rate (don't drop > 3%)"
    - "Crash rate (don't increase > 0.1%)"
    - "Payment failure rate (don't increase > 10%)"
    - "Safety incident rate (don't increase)"

  significance:
    - "95% confidence level"
    - "80% statistical power"
    - "Minimum 14 days (2 weekly cycles)"
    - "Minimum 1000 users per variant"
    - "Bonferroni correction for multiple metrics"

  experiment_types:
    - "Frontend (UI, copy, flows)"
    - "Backend (algorithms, ranking, thresholds)"
    - "Pricing (price points, packaging, trials)"
    - "AI (model versions, prompts, parameters)"
    - "Notification (timing, content, channel)"
```

### Current Experiment Roadmap

```yaml
active_experiments:
  - name: "Onboarding Flow v2"
    hypothesis: "Reducing steps from 7 to 4 increases activation by 15%"
    variants: ["control (7 steps)", "treatment (4 steps)"]
    primary_metric: "activation_rate"
    status: "Running (50% ramp)"
    owner: "Product Growth"
  
  - name: "Proactive Timing ML"
    hypothesis: "ML send-time optimization increases response rate by 20%"
    variants: ["rule-based", "ml-optimized"]
    primary_metric: "proactive_response_rate"
    status: "Running (10% ramp)"
    owner: "AI Team"
  
  - name: "Pro Price $19 vs $22"
    hypothesis: "$19 maximizes revenue (volume * price)"
    variants: ["$19", "$22"]
    primary_metric: "ARPU"
    status: "Analyzing"
    owner: "Growth"

planned_experiments:
  - "Free tier message limit (50 vs 75)"
  - "Trial length (14 vs 30 days)"
  - "Referral incentive (2mo vs 1mo free)"
  - "Paywall placement (after limit vs time-based)"
  - "Voice quality upsell prompt timing"
  - "Memory highlight frequency"
  - "Companion personality quiz in onboarding"
```

---

## Dashboard Architecture

### Dashboard Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                    EXECUTIVE (Weekly)                       │
│  North Star | Revenue | Growth | Retention | Quality       │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   PRODUCT     │    │    GROWTH     │    │    AI/ML      │
│  (Daily)      │    │  (Daily)      │    │  (Daily)      │
├───────────────┤    ├───────────────┤    ├───────────────┤
│ Activation    │    │ Acquisition   │    │ Model Quality │
│ Engagement    │    │ Conversion    │    │ Latency       │
│ Retention     │    │ CAC/Channel   │    │ Safety        │
│ Feature Adopt │    │ Viral Loop    │    │ Cost/Token    │
│ RHI Deep-dive │    │ LTV/Cohort    │    │ Evaluation    │
└───────────────┘    └───────────────┘    └───────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    OPERATIONAL (Real-time)                  │
│  System Health | API Latency | Error Rates | Cost | Alerts  │
└─────────────────────────────────────────────────────────────┘
```

### Key Dashboards

#### 1. Executive Dashboard (Looker)

```yaml
executive_dashboard:
  refresh: "Daily 6 AM UTC"
  tiles:
    - "North Star: RHI Trend (30d sparkline)"
    - "MAU/DAU/WAU (current vs target)"
    - "ARR & Net New ARR (monthly)"
    - "NRR & GRR (12m trend)"
    - "CAC Payback & LTV:CAC"
    - "Month 1/3/6 Retention (cohort heatmap)"
    - "NPS Trend (quarterly)"
    - "Safety: Crisis Recall & False Positive Rate"
    - "Team Health: Deploy Freq, MTTR, On-call"
  audience: "CEO, CFO, Board"
  access: "View only, scheduled email"
```

#### 2. Product Dashboard (Amplitude)

```yaml
product_dashboard:
  refresh: "Real-time"
  tabs:
    overview:
      - "DAU/WAU/MAU + stickiness"
      - "Activation funnel (signup → first msg → day 7)"
      - "Core action rates (msg, voice, proactive, memory)"
      - "RHI distribution"
    
    engagement:
      - "Messages per DAU (by tier, modality)"
      - "Session length & frequency"
      - "Voice adoption funnel"
      - "Proactive: sent/opened/responded/dismissed"
      - "Memory: stored/recalled/consolidated"
    
    retention:
      - "Cohort retention curves (monthly)"
      - "Churn reasons (cancellation survey)"
      - "Reactivation rate"
      - "RHI as leading indicator of churn"
    
    features:
      - "Feature adoption matrix"
      - "New feature launch tracking"
      - "A/B test results"
      - "User journey sankey"
  
  audience: "PMs, Designers, Engineers"
  access: "Edit (PM), View (team)"
```

#### 3. Growth Dashboard (Amplitude + Custom)

```yaml
growth_dashboard:
  refresh: "Hourly"
  tabs:
    acquisition:
      - "Signups by channel (stacked)"
      - "CAC by channel (blended + marginal)"
      - "LTV by first channel"
      - "Viral coefficient (referral tracking)"
    
    monetization:
      - "Free-to-paid funnel"
      - "ARPU by tier & cohort"
      - "Upgrade/downgrade flows"
      - "Expansion revenue (seats, overages)"
      - "Churn by reason & segment"
    
    lifecycle:
      - "Lifecycle stage distribution"
      - "Transition rates between stages"
      - "Win-back campaign performance"
      - "Upgrade propensity scoring"
  
  audience: "Growth, Marketing, Finance"
  access: "View"
```

#### 4. AI/ML Dashboard (Custom + Grafana)

```yaml
ai_ml_dashboard:
  refresh: "Real-time (streaming), Daily (batch)"
  tabs:
    model_performance:
      - "LLM: Latency p50/p95/p99, token cost, error rate"
      - "Embedding: Latency, dimension quality"
      - "Memory: Recall relevance, consolidation quality"
      - "Emotion: Detection accuracy (human eval)"
      - "Safety: Recall, precision, latency"
      - "Voice: ASR WER, TTS MOS, streaming latency"
    
    evaluation:
      - "Automated eval scores (daily)"
      - "Human eval scores (weekly)"
      - "Regression detection"
      - "A/B test: model variants"
    
    cost:
      - "LLM cost per conversation"
      - "Cost per DAU by tier"
      - "Token usage trends"
      - "Model routing efficiency"
    
    safety:
      - "Crisis detected vs intervened"
      - "False positive/negative rates"
      - "Escalation to human rate"
      - "User appeals & outcomes"
  
  audience: "AI/ML Engineers, Safety Team"
  access: "Edit (AI), View (Product, Eng)"
```

---

## Data Governance

### Data Classification

```yaml
data_classification:
  public:
    - "Aggregated metrics (no PII)"
    - "Benchmark reports (anonymized)"
    - "Blog post statistics"
  
  internal:
    - "User-level event data (hashed IDs)"
    - "Cohort analyses"
    - "Experiment results"
    - "Model performance data"
  
  restricted:
    - "Raw conversation content"
    - "PII (email, name, location)"
    - "Safety incident details"
    - "Financial transaction data"
    - "Health/mental health inferences"
  
  highly_restricted:
    - "Encryption keys"
    - "Authentication tokens"
    - "Biometric data (voice prints)"
    - "Child data (if any)"
```

### Access Control (RBAC)

```yaml
roles:
  data_analyst:
    access: ["internal", "public"]
    tools: ["Looker", "Amplitude", "SQL (read-only)"]
    approval: "Manager"
  
  product_manager:
    access: ["internal", "public"]
    tools: ["Amplitude", "Looker", "Statsig"]
    approval: "Auto (role-based)"
  
  ml_engineer:
    access: ["internal", "public", "restricted*"]
    tools: ["Jupyter", "MLflow", "Custom dashboards"]
    approval: "Security review for restricted"
    restrictions: ["No raw PII export", "Aggregated only"]
  
  executive:
    access: ["public", "internal (aggregated)"]
    tools: ["Looker (executive dashboards)"]
    approval: "Auto"
  
  auditor:
    access: ["all (read-only)"]
    tools: ["Audit logs", "Data lineage"]
    approval: "Legal + Security"
```

### Privacy Compliance

```yaml
privacy_controls:
  consent_management:
    - "Analytics consent (opt-in for personalization)"
    - "Marketing consent (separate)"
    - "Granular control per data use"
    - "Easy withdrawal in settings"
  
  data_minimization:
    - "Hash user IDs in analytics"
    - "No raw content in warehouses"
    - "Aggregate before export"
    - "Auto-delete per retention policy"
  
  user_rights:
    - "Access: Self-serve data export"
    - "Rectification: Profile edit"
    - "Erasure: Account deletion → 30-day purge"
    - "Portability: Standard formats (JSON, CSV)"
    - "Objection: Opt-out analytics"
  
  retention:
    event_data: "400 days (13 months + buffer)"
    aggregated_metrics: "7 years"
    experiment_data: "2 years"
    safety_logs: "7 years (legal)"
    financial: "7 years (tax)"
```

---

## Reporting Cadence

### Automated Reports

```yaml
automated_reports:
  daily:
    - name: "Daily Pulse"
      time: "6:00 AM UTC"
      channel: "#metrics-daily"
      content: ["DAU, MAU, Revenue", "Top 3 anomalies", "Experiment status"]
      owner: "Data Team"
  
  weekly:
    - name: "Weekly Business Review"
      time: "Monday 9:00 AM UTC"
      channel: "#metrics-weekly"
      content: ["Full KPI dashboard", "Cohort updates", "Experiment results", "Top insights"]
      owner: "Head of Data"
      attendees: "Leadership + PMs"
  
  monthly:
    - name: "Monthly Deep Dive"
      time: "1st Monday 10:00 AM UTC"
      format: "30-min meeting + Notion doc"
      content: ["Strategic metrics", "Segment analysis", "Competitive intel", "OKR progress"]
      owner: "CEO + Head of Data"
  
  quarterly:
    - name: "Quarterly Business Review"
      format: "2-hour workshop"
      content: ["Strategy review", "Metric targets reset", "Investment decisions", "Board prep"]
      owner: "CEO"
      attendees: "Board, Leadership, Investors"
```

### Alerting on Metrics

```yaml
metric_alerts:
  critical:
    - metric: "DAU drop > 20% WoW"
      action: "Page on-call PM + Eng"
    - metric: "Revenue drop > 15% DoD"
      action: "Page Finance + Growth"
    - metric: "Safety recall < 99%"
      action: "Page Safety Lead + CTO"
    - metric: "Error rate > 5%"
      action: "Page Platform On-call"
  
  warning:
    - metric: "Activation rate < 35%"
      action: "Slack #product-alerts"
    - metric: "CAC > $30"
      action: "Slack #growth-alerts"
    - metric: "Month 1 retention < 60%"
      action: "Slack #product-alerts"
    - metric: "LLM cost/DAU > $0.50"
      action: "Slack #ai-alerts"
  
  info:
    - metric: "New experiment launched"
      action: "Slack #experiments"
    - metric: "Feature flag ramp changed"
      action: "Slack #feature-flags"
```

---

## Tools & Infrastructure

### Modern Data Stack

```yaml
data_stack:
  ingestion:
    - "Segment (client-side)"
    - "Kafka (server-side)"
    - "Fivetran (SaaS sources)"
  
  streaming:
    - "Apache Flink (real-time enrichment)"
    - "Kafka Topics (event bus)"
  
  warehouse:
    - "Snowflake (primary)"
    - "BigQuery (ML features)"
  
  transformation:
    - "dbt (SQL transformations)"
    - "dbt Cloud (orchestration)"
  
  serving:
    - "Amplitude (product analytics)"
    - "Looker (BI/dashboards)"
    - "Custom API (internal tools)"
  
  experimentation:
    - "Statsig (feature flags + experiments)"
    - "LaunchDarkly (feature flags)"
  
  governance:
    - "Monte Carlo (data observability)"
    - "Atlan (data catalog)"
    - "dbt contracts (schema enforcement)"
  
  privacy:
    - "Ethyca / custom (consent enforcement)"
    - "PII scanner (automated)"
```

---

## Success Metrics for Analytics

```yaml
analytics_kpis:
  # Data Quality
  - "Data freshness < 1 hour (streaming)"
  - "Data completeness > 99.9%"
  - "Schema violations < 0.1%"
  - "PII leaks = 0"
  
  # Adoption
  - "Dashboard daily active viewers > 50%"
  - "Self-serve query rate > 80%"
  - "Experiment velocity: 10+/month"
  
  # Impact
  - "Decisions influenced by data: track in Notion"
  - "Experiment win rate > 50%"
  - "Revenue attributed to experiments > 10%"
  
  # Efficiency
  - "Time to insight < 30 min (ad-hoc)"
  - "Dashboard load time < 5 sec"
  - "Data request SLA < 24 hours"
```

---

**Aligned With:** `500-business-model.md`, `510-go-to-market.md`, `520-pricing-packaging.md`, `050-success-metrics.md`
**Next Review:** 2026-01-17