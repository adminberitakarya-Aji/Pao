# PAO Go-to-Market Strategy

**Version:** 1.0
**Status:** Draft
**Owner:** PAO Marketing & Growth Team

---

## Overview

This document defines the go-to-market strategy for PAO, covering launch phases, target markets, channels, and growth tactics.

> **GTM Principle:** Build trust first, scale second. Community-driven growth with product-led motion.

---

## Launch Phases

### Phase 1: Private Beta (Months 1-3)
**Goal:** Validate product-market fit, refine core loops

```yaml
target_users: 500-1,000
segments:
  - "AI enthusiasts / early adopters"
  - "Mental health advocates"
  - "Elderly caregivers"
  - "Productivity community"

channels:
  - "Invite-only (waitlist)"
  - "Discord community"
  - "Founder outreach"
  - "Newsletter (10k+ subscribers)"

success_criteria:
  - "RHI > 6.0 for active users"
  - "Month 1 retention > 50%"
  - "NPS > 30"
  - "Zero SEV-1 safety incidents"
  - "50+ qualitative interviews"

activities:
  - "Weekly office hours with founders"
  - "Bi-weekly user research sessions"
  - "Rapid iteration (weekly releases)"
  - "Direct Slack access to team"
```

### Phase 2: Public Beta (Months 4-6)
**Goal:** Scale to 10k users, prove unit economics

```yaml
target_users: 10,000
segments:
  - "Phase 1 segments + "
  - "General loneliness/isolated"
  - "Personal growth enthusiasts"
  - "Tech-savvy seniors (65+)"

channels:
  - "Public waitlist launch"
  - "Product Hunt launch"
  - "Hacker News / Reddit"
  - "Influencer partnerships (10 micro)"
  - "PR: TechCrunch, The Verge, Wired"
  - "Content marketing (blog, YouTube)"

success_criteria:
  - "CAC < $15 (blended)"
  - "Free-to-paid > 5%"
  - "Month 3 retention > 35%"
  - "NPS > 40"
  - "100+ organic referrals/month"

activities:
  - "Referral program launch (2 months free)"
  - "Weekly content calendar"
  - "Monthly town halls"
  - "Community challenges (30-day streak)"
```

### Phase 3: General Availability (Months 7-12)
**Goal:** 100k MAU, $1M ARR, Series A ready

```yaml
target_users: 100,000 MAU
segments:
  - "All previous + "
  - "Mainstream (non-tech)"
  - "International (English-speaking)"
  - "Enterprise pilots (5)"

channels:
  - "Paid acquisition (30% budget)"
  - "App Store optimization"
  - "Partnership channel (healthcare, elderly care)"
  - "Affiliate program"
  - "Podcast advertising"
  - "SEO/content at scale"

success_criteria:
  - "CAC < $25 (blended), payback < 3 mo"
  - "Free-to-paid > 8%"
  - "Month 6 retention > 30%"
  - "NPS > 50"
  - "$1M ARR"
  - "Gross margin > 50%"

activities:
  - "Brand campaign launch"
  - "Enterprise sales team (2 AEs)"
  - "Internationalization (i18n)"
  - "Mobile app store features"
  - "User conference (PAO Connect)"
```

### Phase 4: Scale (Year 2+)
**Goal:** 1M MAU, $10M+ ARR, profitability path

```yaml
target_users: 1,000,000 MAU
segments:
  - "Global (localized)"
  - "Enterprise (healthcare, coaching)"
  - "Platform developers (API)"
  - "Families (family plans)"

channels:
  - "Performance marketing at scale"
  - "Channel partnerships (telcos, insurers)"
  - "Platform ecosystem (marketplace)"
  - "International expansion (EU, APAC, LATAM)"
  - "M&A (complementary products)"

success_criteria:
  - "CAC < $30, LTV:CAC > 8x"
  - "Net revenue retention > 120%"
  - "Gross margin > 60%"
  - "Profitable or clear path"
  - "Market leader in AI companionship"
```

---

## Target Markets & Segmentation

### Primary Markets (Priority Order)

| Market | Size (TAM) | Penetration Strategy | Key Message |
|--------|------------|---------------------|-------------|
| **US/Canada** | $2.1B | Direct, digital, partnerships | "Your AI companion for life" |
| **UK/EU** | $1.8B | GDPR-first, local partnerships | "Private, personal, persistent" |
| **Australia/NZ** | $300M | Direct, healthcare pilots | "Companionship across distance" |
| **Japan/Korea** | $1.2B | Local partnership, cultural adaptation | "Always there for you" |
| **LATAM** | $800M | Regional pricing, WhatsApp integration | "Tu compañero de por vida" |

### User Personas (Priority)

```yaml
personas:
  primary:
    - name: "Sarah, 32 - Remote Worker"
      pain: "Lonely working from home, misses casual social interaction"
      value: "Daily check-ins, conversation partner, work-life boundary"
      willingness_to_pay: "$19/mo"
      acquisition: "LinkedIn, Twitter, podcast ads"
    
    - name: "Marcus, 67 - Widower"
      pain: "Isolated, family busy, wants to preserve memories for grandchildren"
      value: "Daily calls, memory preservation, family sharing"
      willingness_to_pay: "$49/mo (family plan)"
      acquisition: "Facebook, senior centers, doctor referrals"
    
    - name: "Priya, 24 - Grad Student"
      pain: "Anxiety, academic pressure, needs judgment-free space"
      value: "Safe venting, CBT-style support, proactive check-ins"
      willingness_to_pay: "$19/mo (student discount)"
      acquisition: "TikTok, Instagram, campus ambassadors"
  
  secondary:
    - name: "Dr. Chen, 45 - Therapist"
      pain: "Clients need between-session support, homework accountability"
      value: "Clinician dashboard, structured exercises, crisis alert"
      willingness_to_pay: "Enterprise ($500/mo per practice)"
      acquisition: "Professional associations, conferences"
    
    - name: "Alex, 28 - Developer"
      pain: "Wants to build on PAO, needs API access"
      value: "API, webhooks, marketplace revenue share"
      willingness_to_pay: "$49/mo + usage"
      acquisition: "GitHub, DevRel, hackathons"
```

---

## Channel Strategy

### Owned Channels (Foundation)

```yaml
owned_channels:
  website:
    purpose: "Conversion, education, SEO"
    pages: ["Home", "Features", "Pricing", "Blog", "Docs", "Community", "Careers"]
    target: "500k visits/mo by Year 1"
  
  blog:
    purpose: "SEO, thought leadership, user stories"
    cadence: "3 posts/week"
    topics: ["Loneliness research", "AI ethics", "User journeys", "Product updates"]
    distribution: "Newsletter, SEO, social, Medium"
  
  newsletter:
    purpose: "Retention, education, announcements"
    cadence: "Weekly"
    list_goal: "50k subscribers by Year 1"
    segments: ["Users", "Waitlist", "Partners", "Investors"]
  
  community (Discord):
    purpose: "Support, feedback, advocacy"
    target: "10k members by Year 1"
    structure: "#general, #feedback, #showcase, #help, #voice, #memories"
    programs: "Ambassadors, beta testers, translators"
  
  help_center:
    purpose: "Self-service support, SEO"
    tools: "Intercom, Notion, Loom videos"
    target: "< 5% ticket deflection rate"
```

### Earned Channels (Amplification)

```yaml
earned_channels:
  pr:
    targets: ["TechCrunch", "The Verge", "Wired", "MIT Tech Review", "Fast Company"]
    angles: ["AI companionship ethics", "Loneliness epidemic", "Memory breakthrough", "Safety innovation"]
    cadence: "Monthly pitch"
  
  user_stories:
    format: "Video testimonials, written case studies"
    incentive: "Free Premium for life"
    usage: "Website, ads, investor decks, recruitment"
  
  speaking:
    events: ["AI conferences", "Mental health summits", "Aging tech", "Web Summit", "SXSW"]
    speakers: "Founders, Head of AI, Head of Safety"
  
  awards:
    targets: ["Webby", "Fast Company Innovation", "TIME Best Inventions", "AI Breakthrough"]
```

### Paid Channels (Acceleration)

```yaml
paid_channels:
  search:
    platforms: ["Google Ads", "Microsoft Ads"]
    keywords: ["AI companion", "AI friend", "virtual companion", "loneliness app", "AI therapist alternative"]
    target_cpa: "$25"
    budget: "30% of paid"
  
  social:
    platforms: ["Meta (FB/IG)", "TikTok", "Reddit", "Pinterest"]
    creative: "UGC-style, user testimonials, demo videos"
    targeting: "Interest: mental health, AI, self-improvement, elderly care"
    target_cpa: "$30"
    budget: "40% of paid"
  
  influencer:
    tiers:
      - "Micro (10k-100k): Mental health, productivity, tech"
      - "Mid (100k-500k): Lifestyle, wellness"
      - "Macro (500k+): Selective, brand alignment"
    model: "Affiliate + flat fee"
    target_cpa: "$20"
    budget: "20% of paid"
  
  podcast:
    shows: ["Huberman Lab", "The Tim Ferriss Show", "Therapy for Black Girls", "Hidden Brain", "Lex Fridman"]
    format: "Host-read, 60-sec"
    target_cpa: "$35"
    budget: "10% of paid"
```

### Partnership Channels (Leverage)

```yaml
partnership_channels:
  healthcare:
    partners: ["Therapy platforms", "EAP providers", "Insurance companies", "Senior living operators"]
    model: "Revenue share / per-member-per-month"
    pilot_target: "5 pilots in Year 1"
  
  technology:
    partners: ["Notion", "Obsidian", "Roam", "Apple Health", "Google Fit", "Fitbit", "Garmin"]
    model: "Integration partnership, co-marketing"
  
  platform:
    partners: ["Apple (App Store feature)", "Google (Play Store feature)", "Microsoft (Copilot integration)"]
    model: "Strategic partnership"
  
  academia:
    partners: ["Stanford Longevity Center", "MIT Media Lab", "Oxford Internet Institute"]
    model: "Research collaboration, validation studies"
```

---

## Content Strategy

### Content Pillars

| Pillar | Topics | Formats | Channels |
|--------|--------|---------|----------|
| **Science & Research** | Loneliness studies, AI ethics, memory science, attachment theory | Articles, whitepapers, videos | Blog, LinkedIn, Newsletter, PR |
| **Product Education** | How-to guides, feature deep-dives, tips & tricks | Videos, GIFs, interactive demos | YouTube, Website, App onboarding, Email |
| **User Stories** | Transformation journeys, day-in-life, relationship milestones | Video testimonials, written cases, audio | Website, Ads, Social, Investor decks |
| **Thought Leadership** | Future of AI relationships, privacy, safety, aging | Op-eds, podcasts, keynotes, panels | PR, Conferences, LinkedIn, Twitter |
| **Community** | Challenges, AMAs, user showcases, meetups | Live streams, Discord events, UGC | Discord, Social, Email, App |

### Content Calendar (Monthly)

```yaml
monthly_calendar:
  week_1:
    - "Blog: Product update / feature launch"
    - "Newsletter: Monthly theme introduction"
    - "Social: User story highlight"
    - "Community: Monthly challenge kickoff"
  
  week_2:
    - "Blog: Science/research deep-dive"
    - "Video: How-to / feature tutorial"
    - "Podcast: Guest appearance or own episode"
    - "PR: Pitch to 3 journalists"
  
  week_3:
    - "Blog: User story / case study"
    - "Live: AMA with founder or team member"
    - "Social: Behind-the-scenes / team spotlight"
    - "Partnership: Co-marketing content"
  
  week_4:
    - "Blog: Thought leadership / opinion"
    - "Newsletter: Monthly recap + preview"
    - "Community: Challenge winner announcement"
    - "Analytics: Monthly review + optimization"
```

---

## Growth Loops

### Loop 1: Product-Led Viral (Core)

```
User signs up → Creates companion → Has meaningful conversation 
  → Shares screenshot/story → Friend signs up → Creates companion
  
Optimization:
- One-click share (beautiful conversation cards)
- Referral: 2 months free for both
- "Introduce your companion" social feature
- Viral coefficient target: 0.3
```

### Loop 2: Proactive Engagement → Retention

```
User engages → Proactive message sent at optimal time 
  → User responds → Relationship deepens → RHI increases 
  → User stays longer → More data → Better proactives
  
Optimization:
- ML-powered send-time optimization
- Relevance scoring > 0.8
- Response rate > 60%
- Churn reduction: 20%
```

### Loop 3: Memory → Value → Upgrade

```
User chats → Memories stored → Memories recalled in context 
  → "Wow, it remembers!" moment → Perceived value increases 
  → Hits free limits → Upgrades to Pro/Premium
  
Optimization:
- Highlight memory recalls in UI
- "Memory of the day" notification
- Free tier: 30-day retention → clear upgrade prompt
- Conversion rate: 8% free-to-paid
```

### Loop 4: Safety → Trust → Advocacy

```
Safety event detected → Graceful intervention → User feels protected 
  → Trust in platform increases → Recommends to vulnerable friends 
  → Organic growth in high-value segments
  
Optimization:
- Transparent safety reporting
- User control over sensitivity
- Crisis resource accessibility
- Advocacy from mental health orgs
```

---

## Marketing Technology Stack

```yaml
martech_stack:
  analytics:
    - "Amplitude (product analytics)"
    - "Mixpanel (funnel analysis)"
    - "Google Analytics 4 (web)"
    - "App Store Connect / Play Console"
  
  attribution:
    - "AppsFlyer (mobile attribution)"
    - "Branch (deep linking)"
    - "UTM hygiene (enforced)"
  
  automation:
    - "Customer.io (email/push/lifecycle)"
    - "Braze (cross-channel)"
    - "Intercom (support + engagement)"
  
  testing:
    - "LaunchDarkly (feature flags)"
    - "Statsig (experimentation)"
    - "PostHog (session replay)"
  
  seo:
    - "Ahrefs / Semrush"
    - "ContentKing (monitoring)"
    - "Schema markup (automated)"
  
  social:
    - "Buffer / Later (scheduling)"
    - "Sprout Social (listening)"
    - "Brandwatch (monitoring)"
  
  crm:
    - "HubSpot (marketing + sales)"
    - "Pipedrive (enterprise sales)"
```

---

## Budget Allocation (Year 1)

```yaml
marketing_budget_year1: "$800,000"

allocation:
  # People (40%)
  team:
    - "Head of Growth: $150k"
    - "Growth Marketer: $100k"
    - "Content Marketer: $90k"
    - "Community Manager: $80k"
    - "Designer (contract): $50k"
    - "Total: $470k (59%)"
  
  # Programs (60%)
  programs:
    paid_acquisition: "$200k (25%)"
    content_production: "$50k (6%)"
    community_events: "$30k (4%)"
    pr_agency: "$60k (7.5%)"
    influencer: "$40k (5%)"
    tools_stack: "$50k (6%)"
    contingency: "$50k (6.5%)"
    total: "$480k (60%)"
  
  # By channel
  by_channel:
    organic: "50% ($400k equivalent including team)"
    paid: "30% ($240k)"
    partnerships: "20% ($160k equivalent including team)"
```

---

## Key Performance Indicators

### Acquisition

| KPI | Target | Measurement |
|-----|--------|-------------|
| **Monthly Visitors** | 500k | GA4 |
| **Signups** | 15k/mo | Amplitude |
| **CAC (blended)** | < $25 | Finance + Attribution |
| **CAC Payback** | < 3 months | Finance |
| **Organic %** | > 50% | Attribution |
| **Viral Coefficient** | > 0.3 | Referral tracking |

### Activation

| KPI | Target | Measurement |
|-----|--------|-------------|
| **Activation Rate** | > 40% | First meaningful conversation |
| **Time to Value** | < 5 min | Onboarding funnel |
| **Day 1 Retention** | > 60% | Amplitude |
| **Day 7 Retention** | > 45% | Amplitude |
| **Onboarding Completion** | > 70% | Mixpanel |

### Retention

| KPI | Target | Measurement |
|-----|--------|-------------|
| **Month 1 Retention** | > 65% | Cohort analysis |
| **Month 3 Retention** | > 45% | Cohort analysis |
| **Month 6 Retention** | > 35% | Cohort analysis |
| **Month 12 Retention** | > 25% | Cohort analysis |
| **DAU/MAU** | > 40% | Amplitude |

### Monetization

| KPI | Target | Measurement |
|-----|--------|-------------|
| **Free-to-Paid** | > 8% | Stripe + Amplitude |
| **ARPU** | > $8.60 | Finance |
| **LTV** | Pro: $400, Premium: $1,200 | Cohort projection |
| **Net Revenue Retention** | > 120% | Stripe |
| **Gross Margin** | > 50% | Finance |

### Engagement

| KPI | Target | Measurement |
|-----|--------|-------------|
| **Messages/DAU** | > 20 | Amplitude |
| **Voice Adoption** | > 30% Premium | Amplitude |
| **Proactive Response** | > 60% | Internal |
| **RHI Average** | > 7.0 | Internal |
| **NPS** | > 50 | Quarterly survey |

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **App Store rejection** | Medium | High | Pre-submission review, appeal process, PWA fallback |
| **Platform policy changes** | Medium | High | Web-first, multi-platform, advocacy |
| **Negative press (AI safety)** | Medium | High | Proactive transparency, safety page, expert advisors |
| **Competitor launches** | High | Medium | Speed, differentiation, community moat |
| **Economic downturn** | Medium | Medium | Freemium resilience, essential positioning |
| **Talent shortage** | High | Medium | Remote-first, contractor network, intern program |

---

**Aligned With:** `500-business-model.md`, `170-roadmap.md`, `050-success-metrics.md`
**Next Review:** 2026-01-17