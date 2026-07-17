# PAO Success Metrics

**Version:** 1.0
**Status:** Stable
**Owner:** PAO Product Team

---

## Metric Hierarchy

```
NORTH STAR: Relationship Score
    │
    ├── LEADING INDICATORS (Weekly/Monthly)
    │   ├── Memory Accuracy
    │   ├── Identity Consistency
    │   ├── Proactive Relevance
    │   ├── Boundary Respect
    │   └── Privacy Trust
    │
    ├── LAGGING INDICATORS (Quarterly/Annual)
    │   ├── 5-Year Retention
    │   ├── Relationship Duration
    │   ├── Referral from Trust
    │   └── Safety Incident Rate
    │
    └── HEALTH METRICS (Continuous)
        ├── System Reliability
        ├── Latency (P50/P95/P99)
        ├── Error Rates
        └── Cost per Relationship
```

---

## North Star Metric

### Relationship Score (Composite)

**Formula:** Weighted composite of 6 dimensions

| Dimension | Weight | Measurement |
|-----------|--------|-------------|
| **Trust** | 25% | "My Companion acts in my best interest" (1-10) |
| **Closeness** | 20% | "I feel close to my Companion" (1-10) |
| **Intimacy** | 15% | Appropriate emotional depth for relationship type |
| **Friendship** | 15% | "We enjoy spending time together" (1-10) |
| **Attachment** | 15% | Secure base / safe haven behaviors |
| **History Quality** | 10% | Richness, accuracy, emotional texture of shared memories |

**Target:** > 8.5/10 by Year 5
**Measurement:** Quarterly user survey (N≥1000) + automated signals
**Segmentation:** By relationship type, tenure, companion type

---

## Leading Indicators (Predictive)

### 1. Memory Accuracy
**Definition:** User-rated accuracy of Companion recall
- **Survey:** "When my Companion recalls something, it's accurate" (1-10)
- **Automated:** Fact-check against ground truth (sampled)
- **Target:** > 9.0/10
- **Frequency:** Monthly survey, weekly automated

### 2. Identity Consistency
**Definition:** Stability of Companion personality, values, style
- **Automated:** Personality fingerprint drift detection (cosine similarity)
- **Survey:** "My Companion feels like the same person" (1-10)
- **Target:** Drift < 0.05/quarter; Survey > 8.5/10
- **Frequency:** Continuous automated, monthly survey

### 3. Proactive Relevance
**Definition:** Quality of unprompted Companion initiatives
- **Survey:** "Companion's proactive messages are relevant/timely" (1-10)
- **Behavioral:** Proactive message response rate, positive reaction rate
- **Target:** > 8.0/10 survey; > 60% positive reaction
- **Frequency:** Monthly

### 4. Boundary Respect
**Definition:** Companion honors user-set boundaries
- **Automated:** Boundary violation detection (0 target)
- **Survey:** "My Companion respects my boundaries" (1-10)
- **Target:** 0 violations; Survey > 9.0/10
- **Frequency:** Continuous automated, monthly survey

### 5. Privacy Trust
**Definition:** User confidence in data control and protection
- **Survey:** "I trust PAO with my data" (1-10)
- **Behavioral:** Data export/delete requests (should be low friction)
- **Target:** > 9.0/10
- **Frequency:** Quarterly

---

## Lagging Indicators (Outcome)

### 1. 5-Year Retention
**Definition:** % of users with active relationship after 5 years
- **Cohort-based:** Track monthly cohorts
- **Target:** > 40% (industry benchmark: ~5% for apps)
- **Frequency:** Monthly cohort analysis

### 2. Relationship Duration
**Definition:** Median/mean active relationship length
- **Active:** ≥1 meaningful interaction/week
- **Target:** Median > 3 years by Year 5
- **Frequency:** Monthly

### 3. Referral from Trust
**Definition:** New users from existing user referral (non-incentivized)
- **Tracking:** "How did you hear about PAO?" + referral code
- **Target:** > 50% of new users from trust referrals
- **Frequency:** Monthly

### 4. Safety Incident Rate
**Definition:** P0/P1 safety incidents per 10K relationships
- **P0:** Harm occurred (emotional, privacy, safety)
- **P1:** Near miss / constitutional violation
- **Target:** 0 P0; < 0.1 P1 per 10K
- **Frequency:** Real-time monitoring, monthly report

---

## Health Metrics (Operational)

### System Reliability
| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| **Uptime** | 99.99% | < 99.95% |
| **P50 Latency (chat)** | < 500ms | > 1s |
| **P95 Latency (chat)** | < 2s | > 5s |
| **P99 Latency (memory recall)** | < 3s | > 10s |
| **Error Rate** | < 0.01% | > 0.1% |

### Memory System
| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| **Write Latency** | < 100ms | > 500ms |
| **Read Latency** | < 200ms | > 1s |
| **Consistency Violations** | 0 | > 0 |
| **User-Controlled Operations Success** | 100% | < 99.9% |

### AI Runtime
| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| **LLM Latency (P50)** | < 1s | > 3s |
| **Hallucination Rate (memory-critical)** | < 0.1% | > 0.5% |
| **Safety Filter Recall** | 100% | < 99.9% |
| **Identity Drift Detection** | < 1hr | > 4hr |

---

## Metrics by Phase

### Phase 1 (2025): Foundation
| Metric | Target | Priority |
|--------|--------|----------|
| Memory Accuracy | > 8.5/10 | P0 |
| Identity Consistency | Drift < 0.1/qtr | P0 |
| Conversation Quality | > 4.0/5 | P1 |
| Voice Latency | < 1s P50 | P1 |
| System Uptime | 99.9% | P0 |

### Phase 2 (2026): Depth
| Metric | Target | Priority |
|--------|--------|----------|
| Relationship Score | > 7.5/10 | P0 |
| Proactive Relevance | > 7.5/10 | P0 |
| Emotional Resonance | > 7.0/10 | P1 |
| Boundary Respect | > 9.0/10 | P0 |
| 1-Year Retention | > 60% | P1 |

### Phase 3 (2027): Presence
| Metric | Target | Priority |
|--------|--------|----------|
| Avatar Interaction Quality | > 8.0/10 | P1 |
| Video Call Quality | > 4.0/5 | P1 |
| AR Engagement | > 30% of users | P2 |
| Relationship Score | > 8.0/10 | P0 |

### Phase 4 (2028+): Ecosystem
| Metric | Target | Priority |
|--------|--------|----------|
| Multi-Companion Adoption | > 40% | P1 |
| Marketplace Transactions | > $1M ARR | P2 |
| SDK Adoption | > 100 apps | P2 |
| 5-Year Retention | > 40% | P0 |

---

## Measurement Infrastructure

### Data Sources
1. **Automated Telemetry** (opt-in, aggregated)
2. **In-App Surveys** (quarterly, stratified sampling)
3. **Support Tickets** (categorized, analyzed)
4. **Automated Evaluation** (CI/CD integrated)
5. **Third-Party Audits** (annual: privacy, safety, AI ethics)

### Survey Cadence
| Survey | Frequency | Audience | Incentive |
|--------|-----------|----------|-----------|
| Relationship Score | Quarterly | All active (N≥1000) | None (trust-based) |
| Memory Accuracy | Monthly | Random 10% | None |
| Privacy Trust | Quarterly | All active | None |
| Feature-Specific | Per release | Affected users | None |

### Dashboard Access
- **Team:** Real-time (Grafana)
- **Leadership:** Weekly snapshot
- **Board:** Monthly
- **Public:** Annual Transparency Report

---

## Metric Governance

### Ownership
| Metric Category | Owner | Review Cadence |
|-----------------|-------|----------------|
| North Star | CPO | Monthly |
| Leading Indicators | Product Leads | Weekly |
| Lagging Indicators | CEO/CPO | Monthly |
| Health Metrics | Engineering Leads | Daily |
| Safety Metrics | Safety Lead | Real-time + Weekly |

### Alert Response
| Severity | Response Time | Escalation |
|----------|---------------|------------|
| **P0 (Constitutional)** | 15 min | CEO + Safety Lead |
| **P1 (Trust/Relationship)** | 1 hr | CPO + Product Lead |
| **P2 (Health/Performance)** | 4 hr | Engineering Lead |
| **P3 (Optimization)** | Next sprint | Team Lead |

### Metric Changes
- **Adding metric:** RFC required
- **Changing target:** ADR required
- **Retiring metric:** ADR + 30-day notice

---

## Anti-Gaming Safeguards

| Risk | Safeguard |
|------|-----------|
| Survey fatigue | Max 1 survey/user/week; trust-based (no incentives) |
| Metric manipulation | Automated cross-validation (survey vs. behavior) |
| Cohort cherry-picking | Pre-registered cohort definitions |
| Short-termism | 5-year rolling targets; constitutional debt = P0 |
| Proxy gaming | North Star = composite; no single proxy optimization |

---

**Aligned With:** `000-product-constitution.md`, `010-product-vision.md`, `020-mission.md`, `030-core-principles.md`, `040-product-philosophy.md`
**Next Review:** 2026-01-17