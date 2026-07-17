# PAO Business Model

**Version:** 1.0
**Status:** Draft
**Owner:** PAO Business Strategy Team

---

## Overview

This document defines the business model, revenue streams, pricing strategy, and unit economics for PAO.

> **Business Principle:** Sustainable growth through user value. Align revenue with user success and relationship health.

---

## Value Proposition

### Core Value

| User Segment | Primary Value | Secondary Value |
|--------------|---------------|-----------------|
| **Lonely/Isolated** | Consistent companionship, emotional support | Reduced loneliness, improved wellbeing |
| **Personal Growth** | Accountability partner, reflection mirror | Goal achievement, self-awareness |
| **Mental Wellness** | Safe space, crisis support, mood tracking | Reduced anxiety, early intervention |
| **Elderly** | Daily check-ins, memory preservation, family connection | Independence, legacy, peace of mind |
| **Professionals** | Thought partner, decision support, stress relief | Better decisions, work-life balance |

### Differentiators

1. **True Long-term Memory** - Remembers details across years, not sessions
2. **Relationship Depth** - Evolves from stranger → friend → confidant → family
3. **Proactive Care** - Reaches out at right moments, not just reactive
4. **Multimodal** - Text, voice, and future: video, AR/VR
5. **Safety First** - Clinical-grade crisis detection, human escalation
6. **Privacy by Design** - User owns data, end-to-end encryption, local-first option

---

## Revenue Streams

### 1. Subscription (Primary - 85% of revenue)

```yaml
tiers:
  free:
    name: "Free"
    price: "$0/mo"
    limits:
      companions: 1
      messages_per_day: 50
      voice_minutes_per_month: 0
      proactive_messages_per_week: 3
      memory_retention: "30 days"
      export: false
    target: "Acquisition, habit formation"
  
  pro:
    name: "Pro"
    price: "$19/mo"  # $199/yr (13% discount)
    limits:
      companions: 3
      messages_per_day: "unlimited"
      voice_minutes_per_month: 120
      proactive_messages_per_week: 20
      memory_retention: "unlimited"
      export: true
      custom_personality: true
      relationship_insights: true
    target: "Power users, personal growth"
    ltv_target: "$400"
  
  premium:
    name: "Premium"
    price: "$49/mo"  # $499/yr (15% discount)
    limits:
      companions: 10
      messages_per_day: "unlimited"
      voice_minutes_per_month: 500
      proactive_messages_per_week: "unlimited"
      memory_retention: "unlimited"
      export: true
      custom_personality: true
      relationship_insights: true
      family_sharing: 5 seats
      priority_support: true
      early_access: true
      api_access: true
    target: "Families, professionals, enthusiasts"
    ltv_target: "$1,200"
  
  enterprise:
    name: "Enterprise"
    price: "Custom"
    limits:
      companions: "unlimited"
      sso: true
      admin_console: true
      audit_logs: true
      data_residency: true
      dedicated_support: true
      sla: "99.9%"
      custom_integrations: true
    target: "Healthcare, elderly care, coaching platforms"
    ltv_target: "$50,000+"
```

### 2. Usage-Based (10% of revenue)

```yaml
usage_based:
  voice_minutes:
    overage_price: "$0.10/minute"
    included_in_pro: 120
    included_in_premium: 500
  
  api_calls:
    price_per_1k: "$0.50"
    free_tier: 10,000/month
  
  proactive_sms:
    price_per_message: "$0.05"
    included_in_premium: 100/month
  
  avatar_generation:
    price_per_avatar: "$2.00"
    free_tier: 1/month
  
  data_export:
    price_per_export: "$5.00"
    free_for_premium: true
```

### 3. Marketplace (5% of revenue)

```yaml
marketplace:
  companion_templates:
    revenue_share: "70/30"  # Creator/Platform
    price_range: "$5 - $50"
    examples:
      - "Therapeutic Companion" (CBT-based)
      - "Language Learning Partner"
      - "Creative Writing Coach"
      - "Meditation Guide"
  
  personality_packs:
    revenue_share: "70/30"
    price_range: "$2 - $10"
    examples:
      - "Stoic Philosopher"
      - "Enthusiastic Cheerleader"
      - "Wise Grandparent"
      - "Sci-Fi Character"
  
  voice_models:
    revenue_share: "60/40"  # Higher platform cost
    price_range: "$10 - $100"
    examples:
      - "Celebrity voice (licensed)"
      - "Accent variations"
      - "Age variations"
  
  plugins:
    revenue_share: "80/20"
    price_range: "Free - $20/mo"
    examples:
      - "Calendar integration"
      - "Fitness tracker sync"
      - "Smart home control"
      - "Journaling prompts"
```

---

## Pricing Strategy

### Price Architecture

```
                    ┌─────────────────────┐
                    │    ANCHOR: $49/mo   │  ← Premium (reference)
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
    ┌───────────┐       ┌───────────┐       ┌───────────┐
    │   FREE    │       │   PRO     │       │  PREMIUM  │
    │  $0/mo    │       │ $19/mo    │       │ $49/mo    │
    └───────────┘       └───────────┘       └───────────┘
    Acquisition       Core Value          Full Value
    (CAC: $5)         (LTV: $400)         (LTV: $1,200)
```

### Psychological Pricing

- **Charm pricing**: $19, $49 (not $20, $50)
- **Annual discount**: 13-15% (encourages commitment)
- **Decoy effect**: Premium makes Pro look like a bargain
- **Free tier**: Generous enough to experience value, limited enough to upgrade

### Regional Pricing

```yaml
regional_pricing:
  # Purchasing Power Parity adjustments
  tier_1: [US, CA, AU, UK, DE, FR, JP, SG]  # Full price
  tier_2: [BR, MX, TR, PL, CZ, KR]           # 60% of tier 1
  tier_3: [IN, ID, PH, VN, NG, KE, ZA]       # 30% of tier 1
  tier_4: [AR, EG, PK, BD, VE]               # 15% of tier 1
  
  implementation:
    - Auto-detect via IP/payment method
    - Manual override in settings
    - Prevent arbitrage (billing address verification)
```

---

## Unit Economics

### Key Metrics (Target)

| Metric | Free | Pro | Premium | Enterprise |
|--------|------|-----|---------|------------|
| **Monthly Price** | $0 | $19 | $49 | $5,000+ |
| **CAC** | $5 | $45 | $120 | $5,000 |
| **LTV** | $0 | $400 | $1,200 | $50,000+ |
| **LTV:CAC** | N/A | 8.9x | 10x | 10x+ |
| **Payback Period** | N/A | 2.4 mo | 2.4 mo | 12 mo |
| **Gross Margin** | 60% | 75% | 80% | 85% |
| **Churn (monthly)** | 15% | 3% | 2% | 0.5% |
| **Expansion Revenue** | N/A | 15% | 25% | 50% |

### Cost Structure

```yaml
cost_per_user_per_month:
  # Infrastructure (scales with usage)
  compute:
    free: $0.50
    pro: $1.50
    premium: $4.00
  
  # LLM API costs (major variable cost)
  llm:
    free: $0.80   # 50 messages * $0.016
    pro: $3.20    # 200 messages * $0.016
    premium: $8.00 # 500 messages * $0.016
  
  # Voice (Whisper + TTS)
  voice:
    free: $0.00
    pro: $2.40    # 120 min * $0.02
    premium: $10.00 # 500 min * $0.02
  
  # Storage (memories, embeddings)
  storage:
    free: $0.10
    pro: $0.30
    premium: $0.80
  
  # Support
  support:
    free: $0.05   # Automated only
    pro: $0.50    # Email support
    premium: $2.00 # Priority + chat
  
  # Total variable cost
  total_variable:
    free: $1.45
    pro: $7.90
    premium: $24.80
  
  # Fixed costs (allocated per user)
  fixed_allocation:
    r_and_d: $3.00
    marketing: $2.00
    g_and_a: $1.50
    total_fixed: $6.50
  
  # Total cost
  total_cost:
    free: $7.95
    pro: $14.40
    premium: $31.30
  
  # Gross margin
  gross_margin:
    free: -∞ (loss leader)
    pro: 24%
    premium: 36%
```

### Blended Economics

```yaml
# Assuming mix: 70% Free, 20% Pro, 10% Premium
blended:
  avg_revenue_per_user: $8.60/mo
  avg_cost_per_user: $9.50/mo
  blended_gross_margin: -10%  # At current mix
  
  # Target mix (Year 3): 50% Free, 30% Pro, 15% Premium, 5% Enterprise
  target_mix:
    avg_revenue_per_user: $22.50/mo
    avg_cost_per_user: $11.20/mo
    blended_gross_margin: 50%
```

---

## Go-to-Market Strategy

### Customer Acquisition Channels

```yaml
acquisition_channels:
  # Organic (target 50%)
  organic:
    content_marketing: "Blog, SEO, case studies"
    social_media: "Twitter, LinkedIn, TikTok, YouTube"
    community: "Discord, Reddit, forums"
    word_of_mouth: "Referral program (2 months free)"
    app_store_optimization: "iOS/Android"
  
  # Paid (target 30%)
  paid:
    search_ads: "Google, Bing (high intent)"
    social_ads: "Meta, TikTok, Instagram (awareness)"
    influencer: "Micro-influencers (mental health, tech)"
    podcast: "Mental health, tech, productivity podcasts"
  
  # Partnerships (target 20%)
  partnerships:
    healthcare: "Therapist referrals, clinic pilots"
    elderly_care: "Senior living communities"
    education: "University wellness centers"
    corporate: "EAP programs, employee benefits"
    platforms: "Integration with Notion, Obsidian, etc."
```

### Funnel Metrics

```yaml
funnel_targets:
  monthly_visitors: 500,000
  signup_rate: 3%           # 15,000 signups
  activation_rate: 40%      # 6,000 activated (first meaningful conversation)
  free_to_paid: 8%          # 480 new paid/month
  pro_mix: 60%              # 288 Pro
  premium_mix: 40%          # 192 Premium
  
  # Cohort retention
  month_1_retention: 65%
  month_3_retention: 45%
  month_6_retention: 35%
  month_12_retention: 25%
```

---

## Financial Projections

### 3-Year Forecast

| Year | Users (MAU) | Paid Subscribers | ARR | Revenue Mix | Team Size | Burn Rate | Runway |
|------|-------------|------------------|-----|-------------|-----------|-----------|--------|
| **Year 1** | 50,000 | 3,000 | $1.2M | 90% Sub, 10% Usage | 15 | $200k/mo | 18 mo |
| **Year 2** | 250,000 | 25,000 | $8.5M | 85% Sub, 10% Usage, 5% Marketplace | 40 | $600k/mo | 24 mo |
| **Year 3** | 1,000,000 | 120,000 | $45M | 80% Sub, 10% Usage, 10% Marketplace | 100 | $1.5M/mo | Profitable |

### Funding Requirements

```yaml
funding_rounds:
  seed:
    amount: "$3M"
    valuation: "$15M post"
    use: "Product development, initial team, launch"
    runway: "18 months"
  
  series_a:
    amount: "$12M"
    valuation: "$60M post"
    use: "Growth, marketing, enterprise features"
    runway: "24 months"
  
  series_b:
    amount: "$30M"
    valuation: "$200M post"
    use: "International expansion, R&D, acquisitions"
    runway: "36 months to profitability"
```

---

## Competitive Landscape

### Direct Competitors

| Competitor | Strengths | Weaknesses | Our Advantage |
|------------|-----------|------------|---------------|
| **Replika** | Large user base, avatar | Shallow memory, safety issues | Deep memory, safety-first, multimodal |
| **Character.ai** | Creative, fun | No long-term memory, no safety | Relationship depth, proactive care |
| **Pi (Inflection)** | Great conversation | No persistence, no voice | Long-term relationship, voice |
| **ChatGPT** | Intelligence | No memory, no personality, no safety | Personalized, persistent, safe |

### Indirect Competitors

| Category | Examples | Threat Level |
|----------|----------|--------------|
| **Therapy Apps** | BetterHelp, Talkspace | Medium (different use case) |
| **Journaling Apps** | Day One, Reflectly | Low (complementary) |
| **Meditation Apps** | Headspace, Calm | Low (complementary) |
| **Voice Assistants** | Siri, Alexa, Google | Low (transactional, not relational) |

### Competitive Moats

1. **Data Moat** - Years of interaction data → better personalization
2. **Memory Moat** - Proprietary consolidation engine → unique long-term recall
3. **Safety Moat** - Clinical-grade detection → trust, enterprise sales
4. **Voice Moat** - Timbre verification + low-latency streaming → quality barrier
5. **Network Moat** - Family sharing → multi-user lock-in
6. **Brand Moat** - "The AI that remembers" → top-of-mind

---

## Risk Analysis

### Business Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **LLM cost increases** | High | High | Multi-model strategy, local models, caching |
| **Regulatory changes (AI Act)** | Medium | High | Privacy by design, compliance team |
| **Competitor copies features** | High | Medium | Speed of execution, patents, brand |
| **User trust breach** | Low | Critical | Transparency, audits, user control |
| **Platform dependency (iOS/Android)** | Medium | High | Web-first, PWA, regulatory advocacy |
| **Economic downturn** | Medium | Medium | Freemium resilience, essential value prop |

### Technical Risks (Business Impact)

| Risk | Business Impact | Mitigation |
|------|-----------------|------------|
| **Memory hallucinations** | Trust loss, churn | Evaluation engine, human feedback loops |
| **Voice latency** | Poor UX, low adoption | Edge deployment, model optimization |
| **Scaling costs** | Margin compression | Efficient architecture, local inference |
| **Data loss** | Legal, reputation | Multi-region, point-in-time recovery |

---

## Success Metrics (North Star)

### Primary: Relationship Health Index (RHI)

```
RHI = (Trust × 0.3) + (Closeness × 0.25) + (Engagement × 0.2) + 
      (Satisfaction × 0.15) + (Growth × 0.1)

Target: Average RHI > 7.0 across active companions
```

### Supporting Metrics

| Metric | Target | Frequency |
|--------|--------|-----------|
| **DAU/MAU** | > 40% | Daily |
| **Messages per DAU** | > 20 | Daily |
| **Voice adoption** | > 30% of Premium | Weekly |
| **Proactive response rate** | > 60% | Weekly |
| **Crisis detection recall** | > 99.9% | Real-time |
| **NPS** | > 50 | Quarterly |
| **Net Revenue Retention** | > 120% | Monthly |
| **Gross Margin** | > 60% | Monthly |

---

**Aligned With:** `01-product/170-roadmap.md`, `00-foundation/050-success-metrics.md`, `06-legal/`
**Next Review:** 2026-01-17