# PAO Investor Relations

**Version:** 1.0
**Status:** Draft
**Owner:** PAO Finance & Investor Relations

---

## Overview

This document defines the investor relations strategy, communication framework, reporting standards, and governance for PAO.

> **IR Principle:** Radical transparency with strategic clarity. Build long-term trust through consistent execution and honest communication.

---

## Investor Base Strategy

### Target Investor Profile by Stage

```yaml
seed:
  profile:
    - "Pre-seed/Seed funds (check size $500k-$2M)"
    - "Angel investors (AI, consumer, mental health)"
    - "Operator angels (ex-founders, executives)"
    - "Strategic angels (platform, distribution)"
  criteria:
    - "Value-add beyond capital (hiring, BD, technical)"
    - "Portfolio synergy (no competitive conflicts)"
    - "Long-term orientation (10+ year horizon)"
    - "Follow-on capacity or strong co-investor network"
  target_allocation: "60% institutional, 40% angels"
  board_seats: 1-2 (lead investor + independent)

series_a:
  profile:
    - "Series A funds (check size $5M-$15M)"
    - "Consumer AI thesis, marketplace experience"
    - "Healthtech/mental health crossover funds"
    - "International funds (for global expansion)"
  criteria:
    - "Board partner with consumer scaling experience"
    - "Platform/network for enterprise BD"
    - "Follow-on reserves (3-4x initial check)"
    - "ESG/impact alignment (mental health mission)"
  target_allocation: "1 lead + 1-2 co-leads"
  board_seats: 3 (2 investors + 1 independent)

series_b:
  profile:
    - "Growth funds (check size $15M-$50M)"
    - "Consumer subscription scaling expertise"
    - "International expansion track record"
    - "Pre-IPO preparation experience"
  criteria:
    - "Operating partners for scaling functions"
    - "Public market crossover relationships"
    - "Governance maturity for board evolution"
    - "Secondary liquidity facilitation"
  target_allocation: "1 lead + existing pro-rata"
  board_seats: 5 (3 investors, 1 independent, 1 CEO)

pre_ipo:
  profile:
    - "Crossover funds (Tiger, Coatue, D1, etc.)"
    - "Long-only funds (Fidelity, T. Rowe, Baillie)"
    - "Strategic corporate investors (platform partners)"
  criteria:
    - "Public market credibility"
    - "Analyst/investor day participation"
    - "Lock-up flexibility"
    - "Research coverage initiation"
  target_allocation: "Broad syndication, 20+ holders"
  board_seats: 7-9 (majority independent)
```

### Current Cap Table (Illustrative)

```yaml
cap_table_seed:
  founders: "65% (vesting 4 years, 1-year cliff)"
  employees_option_pool: "15% (post-money)"
  investors:
    - "Lead VC: 12% ($3M @ $15M post)"
    - "Co-investors: 5% ($1.25M)"
    - "Angels: 3% ($750k)"
  total_raised: "$5M"
  post_money: "$15M"
  option_pool_refresh: "Annual 5% top-up"
```

---

## Fundraising Strategy

### Fundraising Timeline

```yaml
fundraising_calendar:
  seed:
    target: "$5M"
    timeline: "Q1 2025 (close Q2 2025)"
    use_of_funds:
      - "Product development (60%): Core engines, mobile apps"
      - "Team (25%): 15 people (AI, eng, product, design)"
      - "Launch & growth (10%): Beta, content, community"
      - "Operations (5%): Legal, infra, compliance"
    milestones_for_next_round:
      - "10k MAU, 40% month-1 retention"
      - "RHI > 6.5, NPS > 30"
      - "Zero SEV-1 safety incidents"
      - "Team: 15 FTE, 3 PhDs in AI"
      - "Infrastructure: Production-ready, SOC2 Type I"
  
  series_a:
    target: "$12M"
    timeline: "Q1 2026 (close Q2 2026)"
    valuation_target: "$60M post"
    use_of_funds:
      - "Growth (40%): Paid acquisition, partnerships, brand"
      - "Product (30%): Voice, proactive, enterprise features"
      - "Team (20%): 40 people (sales, marketing, CS, eng)"
      - "International (10%): UK/EU entity, localization"
    milestones_for_next_round:
      - "100k MAU, $1M ARR"
      - "NRR > 120%, gross margin > 50%"
      - "Enterprise pilots: 5 converted to paid"
      - "Team: 40 FTE, VP Sales/Marketing hired"
      - "SOC2 Type II, HIPAA readiness"
  
  series_b:
    target: "$30M"
    timeline: "Q1 2027 (close Q2 2027)"
    valuation_target: "$200M post"
    use_of_funds:
      - "Scale (50%): Performance marketing, channel partners"
      - "International (20%): APAC, LATAM expansion"
      - "R&D (20%): Next-gen models, video, AR/VR research"
      - "M&A (10%): Acqui-hire, complementary tech"
    milestones_for_next_round:
      - "500k MAU, $10M ARR"
      - "Profitable or clear path (burn < $500k/mo)"
      - "International: 30% revenue non-US"
      - "Team: 100 FTE, CFO hired"
      - "Public company readiness (SOX, controls)"
  
  series_c_pre_ipo:
    target: "$50-100M"
    timeline: "2028-2029"
    valuation_target: "$500M-$1B"
    use_of_funds:
      - "Balance sheet strength for public markets"
      - "Strategic M&A"
      - "Secondary liquidity for early employees/investors"
      - "Final private round before IPO/DPO"
```

### Fundraising Process

```yaml
process:
  preparation:
    - "Data room: Notion + Google Drive (organized by category)"
    - "Financial model: 3-year monthly, 5-year annual (Bottoms-up + TAM)"
    - "Deck: 15 slides (Problem, Solution, Market, Traction, Team, Ask)"
    - "Demo: Live product, recorded walkthrough, sandbox access"
    - "References: 3 customers, 2 technical, 2 personal"
    - "Legal: Clean cap table, IP assignment, contracts organized"
  
  execution:
    - "Week 1-2: Warm intros, 20-30 first meetings"
    - "Week 3-4: Partner meetings, deep dives, demo sessions"
    - "Week 5-6: Term sheets, negotiation, due diligence"
    - "Week 7-8: Legal docs, closing, wire transfers"
  
  negotiation_principles:
    - "Valuation: Fair, not maximal (long-term alignment)"
    - "Control: Founder-friendly provisions (drag-along, tag-along)"
    - "Liquidation: 1x non-participating preferred"
    - "Anti-dilution: Broad-based weighted average"
    - "Board: Balanced, independent chair at Series B+"
    - "Information rights: Standard, not burdensome"
    - "Pro-rata: Major investors only, pay-to-play"
    - "ESOP: Post-money, refresh annually"
```

---

## Communication Framework

### Regular Communications

```yaml
cadence:
  monthly_update:
    audience: "All investors (current + major prospects)"
    format: "Email (Notion link + PDF)"
    timing: "5th business day of month"
    content:
      - "KPIs: MAU, DAU/MAU, ARR, NRR, CAC, LTV, Churn, RHI, NPS"
      - "Progress vs plan (Green/Yellow/Red per OKR)"
      - "Key wins (product, growth, team, partnerships)"
      - "Key challenges + mitigation"
      - "Ask: Hiring, intros, feedback, customers"
      - "Financials: Cash, burn, runway, revenue"
  
  quarterly_package:
    audience: "Board + major investors (>$500k)"
    format: "PDF deck + Notion workspace + 60-min call"
    timing: "Within 30 days of quarter end"
    content:
      - "Executive summary (1 page)"
      - "Financials: P&L, Balance Sheet, Cash Flow (GAAP + SaaS metrics)"
      - "Unit economics deep-dive (by cohort, channel, tier)"
      - "Product: Roadmap progress, releases, technical milestones"
      - "Growth: Funnel, experiments, channel performance"
      - "Team: Org chart, hiring plan, key hires/departures"
      - "Market: Competitive updates, regulatory, TAM validation"
      - "Risk register: Top 10 risks, mitigation, owner"
      - "Board consent items (approvals needed)"
  
  annual_meeting:
    audience: "All shareholders"
    format: "Hybrid (in-person + virtual), 2 hours"
    timing: "Within 90 days of fiscal year end"
    content:
      - "Year in review (metrics, milestones, lessons)"
      - "Strategy: 3-year vision, key bets"
      - "Financial plan: Next 12-18 months"
      - "Governance: Board elections, comp approval"
      - "Q&A: Open floor (pre-submitted + live)"
  
  ad_hoc:
    triggers:
      - "Fundraising (new round, SAFE, bridge)"
      - "Material events (acquisition, key hire, partnership)"
      - "Crisis (security, safety, regulatory, legal)"
      - "Milestone (1M users, $10M ARR, profitability)"
    format: "Immediate email + 24hr follow-up call option"
    principle: "No surprises, proactive disclosure"
```

### Board Governance

```yaml
board_structure:
  seed:
    size: 3
    composition:
      - "CEO (Founder)"
      - "Lead Investor"
      - "Independent (industry expert)"
    frequency: "Monthly (60 min)"
    committees: "None (full board handles all)"
  
  series_a:
    size: 5
    composition:
      - "CEO (Founder)"
      - "Lead Investor (Series A)"
      - "Seed Investor (or observer)"
      - "Independent 1 (Consumer/Subscription)"
      - "Independent 2 (AI/Safety/Ethics)"
    frequency: "Quarterly (3 hours) + Monthly updates"
    committees:
      - "Audit (Chair: Independent 1)"
      - "Compensation (Chair: Independent 2)"
      - "Safety & Ethics (Chair: Independent 2)"
  
  series_b:
    size: 5-7
    composition:
      - "CEO"
      - "Series A Lead"
      - "Series B Lead"
      - "Independent 1 (Consumer/Scale)"
      - "Independent 2 (AI/Tech)"
      - "Independent 3 (Finance/Governance)"
      - "Independent 4 (International/Healthcare)" [optional]
    frequency: "Quarterly (4 hours) + Monthly executive session"
    committees:
      - "Audit (Chair: Independent 3)"
      - "Compensation (Chair: Independent 1)"
      - "Nominating & Governance (Chair: Independent 4)"
      - "Safety & Ethics (Chair: Independent 2)"
      - "Strategy & M&A (Chair: CEO)"
  
  public:
    size: 7-9
    composition:
      - "CEO"
      - "2-3 Investor directors"
      - "5-6 Independent directors (majority)"
      - "Required: Audit committee financial expert"
      - "Required: Diversity (gender, background, geography)"
    frequency: "Quarterly (full day) + 6-8 special meetings"
    committees: "Full public company committee structure"
```

### Board Meeting Template

```markdown
# PAO Board Meeting - [Date]

## Pre-Read (Distributed 5 business days prior)
- [ ] CEO Letter (2 pages max)
- [ ] Financial Package (P&L, BS, CF, SaaS metrics, variance)
- [ ] KPI Dashboard (North Star + 15 primary metrics)
- [ ] OKR Scorecard (Progress vs plan)
- [ ] Strategic Memos (2-3 deep dives)
- [ ] Consent Agenda Items

## Agenda (3-4 hours)
| Time | Topic | Lead | Material | Decision/Input |
|------|-------|------|----------|----------------|
| 30m | CEO Report & Strategic Discussion | CEO | CEO Letter | Input |
| 45m | Financial Review | CFO | Financial Package | Approve |
| 30m | KPIs & OKRs | CEO/Department Heads | Dashboard | Input |
| 45m | Strategic Deep Dive 1 | Owner | Memo | Decision |
| 30m | Strategic Deep Dive 2 | Owner | Memo | Decision |
| 30m | Risk & Compliance | CRO/Legal | Risk Register | Input |
| 15m | People & Org | CEO/CHRO | Org Chart, Hiring | Approve |
| 15m | Consent Agenda | Chair | Consent Items | Approve |
| 30m | Executive Session (no management) | Chair | - | - |

## Post-Meeting
- Minutes: Within 5 business days
- Action items: Tracked in Notion, reviewed next meeting
- Consent resolutions: Signed via DocuSign
```

---

## Financial Reporting Standards

### SaaS Metrics (Reported Monthly)

```yaml
saas_metrics:
  revenue:
    - "MRR (arr): "Annual Recurring Revenue (contracted)"
    - "MRR: Monthly Recurring Revenue"
    - "New MRR: New logos + Expansion"
    - "Churned MRR: Gross + Net"
    - "Net New MRR: New - Churned"
    - "ARR Growth: YoY, QoQ, MoM"
    - "Revenue: GAAP recognized (monthly)"
  
  retention:
    - "Logo Retention: % customers retained"
    - "Gross Revenue Retention (GRR): % revenue retained"
    - "Net Revenue Retention (NRR): GRR + Expansion"
    - "Logo Churn: % customers lost"
    - "Revenue Churn: % revenue lost"
  
  efficiency:
    - "CAC: Blended + by channel"
    - "CAC Payback: Months (Gross Margin Adjusted)"
    - "LTV: By cohort, tier, channel"
    - "LTV:CAC Ratio"
    - "Magic Number: Net New ARR / Prior Q S&M"
    - "Burn Multiple: Net Burn / Net New ARR"
    - "Rule of 40: Growth % + FCF Margin %"
  
  unit_economics:
    - "Gross Margin: % (by tier, blended)"
    - "Contribution Margin: % (after variable costs)"
    - "ARPU: Average Revenue Per User"
    - "ARPPU: Average Revenue Per Paying User"
    - "Paying User %: % of MAU"
  
  pipeline:
    - "Pipeline Coverage: 3x, 4x next quarter"
    - "Pipeline Velocity: $/day"
    - "Win Rate: % by stage, segment"
    - "Sales Cycle: Days (median, by segment)"
```

### GAAP Financials (Quarterly)

```yaml
gaap_reporting:
  income_statement:
    - "Revenue: Subscription + Usage + Professional Services"
    - "COGS: Hosting, LLM API, Voice, Support, Payment fees"
    - "Gross Profit & Margin"
    - "OpEx: R&D, S&M, G&A (detailed by category)"
    - "Operating Income/Loss"
    - "Net Income/Loss"
    - "EBITDA & Adjusted EBITDA"
  
  balance_sheet:
    - "Cash & Equivalents"
    - "Accounts Receivable (net)"
    - "Deferred Revenue (current + non-current)"
    - "Property & Equipment (net)"
    - "Intangible Assets (IP, Goodwill)"
    - "Total Assets"
    - "Accounts Payable & Accrued"
    - "Debt (if any)"
    - "Deferred Revenue"
    - "Total Liabilities"
    - "Stockholders' Equity (APIC, Retained Earnings, APIC)"
  
  cash_flow:
    - "Operating: Net Income + D&A + SBC + Working Capital"
    - "Investing: CapEx, Acquisitions, Marketable Securities"
    - "Financing: Equity, Debt, Option Exercises, Repurchases"
    - "Free Cash Flow: Operating CF - CapEx"
    - "Cash Runway: Months at current burn"
```

### Non-GAAP Reconciliations

```yaml
non_gaap:
  adjusted_ebitda:
    - "GAAP Net Loss"
    - "+ Interest Expense"
    - "+ Taxes"
    - "+ D&A"
    - "+ Stock-Based Compensation"
    - "+ One-time items (M&A, restructuring, legal)"
    - "= Adjusted EBITDA"
  
  free_cash_flow:
    - "Operating Cash Flow"
    - "- Capital Expenditures"
    - "= Free Cash Flow"
  
  non_gaap_net_loss:
    - "GAAP Net Loss"
    - "+ SBC"
    - "+ Amortization of acquired intangibles"
    - "+ One-time items"
    - "= Non-GAAP Net Loss"
```

---

## Investor Requests & Data Room

### Standard Data Room Structure

```
📁 PAO_Data_Room_[YYYY-MM-DD]/
├── 📁 01_Corporate/
│   ├── Certificate of Incorporation
│   ├── Bylaws
│   ├── Cap Table (fully diluted)
│   ├── Stock Option Plan & Grants
│   ├── Board Minutes & Consents
│   └── Shareholder Agreements
├── 📁 02_Financial/
│   ├── Monthly Financials (3 years)
│   ├── SaaS Metrics Dashboard
│   ├── Cohort Analyses
│   ├── Unit Economics by Segment
│   ├── Cash Flow Forecast (18 months)
│   ├── Audit/Review Reports
│   └── Tax Returns & Filings
├── 📁 03_Legal/
│   ├── Material Contracts (customers, vendors, partners)
│   ├── IP Portfolio (patents, trademarks, copyrights)
│   ├── Litigation Summary (none expected)
│   ├── Regulatory Compliance (GDPR, HIPAA, SOC2)
│   ├── Insurance Policies
│   └── Employee Agreements (offer, proprietary info)
├── 📁 04_Product_Technology/
│   ├── Architecture Diagrams
│   ├── Security Assessment (pen test, SOC2)
│   ├── AI Model Cards & Evaluations
│   ├── Safety & Privacy Documentation
│   ├── Technical Due Diligence Responses
│   └── Roadmap (confidential)
├── 📁 05_Commercial/
│   ├── Customer List (anonymized)
│   ├── Pipeline & Forecast
│   ├── Partnership Agreements
│   ├── Pricing & Packaging
│   ├── Churn Analysis
│   └── NPS & Customer References
├── 📁 06_Team/
│   ├── Org Chart
│   ├── Key Personnel Bios
│   ├── Compensation Philosophy
│   ├── Advisor Agreements
│   └── Hiring Plan
└── 📁 07_Strategy/
    ├── Board Decks (last 8 quarters)
    ├── Investor Updates (last 12 months)
    ├── Market Research & TAM Analysis
    ├── Competitive Analysis
    └── Fundraising History
```

### Request Response SLA

```yaml
response_sla:
  board_members:
    routine: "24 hours"
    urgent: "4 hours"
    data_room_access: "Immediate (self-serve)"
  
  major_investors (>$500k):
    routine: "48 hours"
    urgent: "24 hours"
    data_room_access: "Within 24 hours"
  
  other_investors:
    routine: "5 business days"
    urgent: "48 hours"
    data_room_access: "Upon request (NDA required)"
  
  prospective_investors:
    routine: "Per fundraising process"
    data_room_access: "After term sheet (or advanced DD)"
  
  restricted_information:
    - "Customer PII (never shared)"
    - "Unpatented trade secrets (NDA + need-to-know)"
    - "Detailed AI model weights (never shared)"
    - "Employee compensation (aggregated only)"
    - "Board executive session minutes (never shared)"
```

---

## Crisis Communication

### Crisis Protocol

```yaml
crisis_communication:
  classification:
    level_1_critical:
      definition: "Existential threat (security breach, safety fatality, regulatory shutdown)"
      notification: "Immediate (within 1 hour)"
      audience: "Board Chair, Lead Investors, Legal, PR"
      channel: "Phone + Encrypted Email"
      follow_up: "Written within 4 hours"
    
    level_2_high:
      definition: "Material impact (major outage, key exec departure, lawsuit filed)"
      notification: "Within 4 hours"
      audience: "Full Board, Major Investors"
      channel: "Email + Slack + Call option"
      follow_up: "Written within 24 hours"
    
    level_3_moderate:
      definition: "Notable but contained (minor outage, data issue, negative press)"
      notification: "Within 24 hours"
      audience: "Board, Major Investors"
      channel: "Monthly update (accelerated)"
      follow_up: "Next monthly update"
  
  communication_principles:
    - "Speed over perfection (acknowledge, investigating, timeline)"
    - "Single source of truth (CEO or designated spokesperson)"
    - "No speculation (facts only, unknown = 'under investigation')"
    - "User-first framing (impact on users, remediation)"
    - "Investor confidence (cash position, runway, go-forward plan)"
    - "Regulatory coordination (legal clearance before disclosure)"
  
  holding_statement_template:
    "We are aware of [issue] affecting [scope]. Our team is actively investigating 
     and taking [immediate action]. We will provide an update by [time/date]. 
     User safety/data security is our top priority. Contact: [IR email]"
```

---

## ESG & Impact Reporting

### ESG Framework

```yaml
esg_reporting:
  environmental:
    - "Carbon footprint: Cloud compute, office, travel"
    - "Target: Carbon neutral by 2027, Net zero by 2030"
    - "Green cloud regions (AWS/GCP renewable)"
    - "Model efficiency (reduce compute per inference)"
  
  social:
    - "User wellbeing: RHI, safety incidents, crisis interventions"
    - "Accessibility: WCAG 2.1 AA, screen readers, languages"
    - "Inclusion: Diverse companions, cultural adaptation"
    - "Team: Diversity metrics, pay equity, wellbeing"
    - "Community: Mental health donations, pro bono enterprise"
  
  governance:
    - "Board independence & diversity"
    - "AI Ethics Board (external advisors)"
    - "Safety & Privacy by design"
    - "Transparency reports (quarterly)"
    - "Whistleblower policy, anonymous reporting"
  
  impact_metrics:
    - "Loneliness reduction (UCLA Loneliness Scale, pre/post)"
    - "Mental health outcomes (PHQ-9, GAD-7 for opted-in users)"
    - "Crisis interventions & lives supported"
    - "Elderly independence (ADL maintenance, family connection)"
    - "Accessibility: % users with disabilities served"
```

### Annual Impact Report

```markdown
# PAO Annual Impact Report [Year]

## Mission Progress
- North Star: Average RHI across active companions
- Users served: Total, by segment, by geography
- Safety: Crisis interventions, false positive rate, response time

## Environmental
- Carbon footprint (Scope 1, 2, 3)
- Compute efficiency improvements
- Renewable energy %

## Social
- Team diversity (gender, ethnicity, neurodiversity, geography)
- Pay equity analysis
- Accessibility compliance
- Community partnerships & donations

## Governance
- Board composition & independence
- AI Ethics Board activities
- Safety incidents & resolutions
- Privacy requests & compliance
- Regulatory engagement

## Goals for Next Year
- Specific, measurable targets per pillar
```

---

## Valuation Framework

### Valuation Methodology (For Internal Planning)

```yaml
valuation_approaches:
  saas_multiples:
    - "ARR Multiple: 10-20x (growth rate dependent)"
    - "Current: $1.2M ARR → $12-24M (Seed), $8.5M ARR → $85-170M (Series A)"
    - "Growth adjustment: +1x per 10% YoY growth > 100%"
    - "Quality premium: +2-5x for NRR>120%, GRR>90%, CAC Payback<12mo"
  
  dcf:
    - "Forecast: 10-year explicit, terminal value Year 10"
    - "WACC: 15-20% (early stage), 10-12% (growth)"
    - "Terminal growth: 3-5%"
    - "Sensitivity: Revenue growth ±20%, Margin ±5%"
  
  comparable_transactions:
    - "Consumer AI: Character.ai ($1B), Replika (private)"
    - "Mental Health: Headspace ($3B), Calm ($2B), BetterHelp ($3.5B)"
    - "Subscription: Duolingo (15x ARR), Calm (12x), Notion (50x)"
    - "Adjust for: Growth, margins, market size, moat"
  
  venture_method:
    - "Exit value (Year 5-7): $1-5B (IPO/M&A)"
    - "Ownership at exit: 15-20% (post-dilution)"
    - "Required return: 10-20x (Seed), 5-10x (A), 3-5x (B)"
    - "Post-money = Exit Value * Ownership / Required Return"
```

### 409A Valuation

```yaml
409a_process:
  frequency: "Annual + material events (fundraising, M&A, pivot)"
  provider: "Independent (Carta, Scalar, Aranca)"
  methodology:
    - "OPM (Option Pricing Model) for common stock"
    - "PWERM (Probability-Weighted Expected Return Method)"
    - "Inputs: DCF, Comps, Precedent Transactions, DCF"
  safe_harbor: "Independent appraisal = rebuttable presumption"
  strike_price: "Common = 409A price, Preferred = last round price"
  refresh: "Annual grant at current 409A"
```

---

## Legal & Compliance

### Securities Law Compliance

```yaml
securities_compliance:
  exemptions:
    - "Reg D 506(c): Accredited investors only, general solicitation OK"
    - "Rule 701: Employee option grants (<$10M/12mo)"
    - "Reg CF: Not used (cap $5M, not suitable)"
    - "Reg A+: Considered for community round (Tier 2: $75M)"
  
  filing_requirements:
    - "Form D: Within 15 days of first sale (each round)"
    - "Blue Sky: State notice filings (where investors reside)"
    - "Rule 701: Annual disclosure if >$10M grants"
    - "Section 16: Officer/director/10% holder reporting (post-IPO)"
  
  documentation:
    - "SAFE/Note: YC standard, MFN, valuation cap, discount"
    - "SPA: NVCA model, customized for PAO"
    - "Investor Rights: Info rights, registration, participation"
    - "Voting Agreement: Drag-along, tag-along, board seats"
    - "ROFR/Co-sale: Major investors, standard terms"
```

### Insider Trading Policy

```yaml
insider_trading:
  covered_persons:
    - "Officers, Directors, 10% holders"
    - "Employees with MNPI access (finance, corp dev, legal)"
    - "Family members & controlled entities"
  
  trading_windows:
    - "Open: 2 business days post-earnings → 15 days before quarter end"
    - "Closed: 15 days before quarter end → 2 days post-earnings"
    - "Blackout: Any period with MNPI (fundraising, M&A, pivot)"
  
  pre_clearance:
    - "Required for all covered persons"
    - "Submit 3 business days prior"
    - "Valid for 10 business days"
    - "CFO/GC approval required"
  
  prohibited:
    - "Short sales, hedging, pledging"
    - "Trading on MNPI (tipping included)"
    - "Options exercises during blackout (cashless OK)"
```

---

## Investor Relations Calendar (Annual)

```yaml
ir_calendar:
  january:
    - "Annual strategy memo to board"
    - "409A refresh"
    - "Annual budget/plan finalization"
  
  february:
    - "Q4/Full Year Board Package"
    - "Q4 Earnings/Update Call"
    - "Annual Impact Report draft"
  
  march:
    - "Annual Shareholder Meeting"
    - "Annual Impact Report published"
    - "Board compensation review"
  
  april:
    - "Q1 Monthly Updates resume"
    - "Strategic planning offsite (board + exec)"
  
  may:
    - "Q1 Board Package"
    - "Q1 Update Call"
  
  june:
    - "Mid-year strategy review"
    - "Option pool refresh (if approved)"
  
  july:
    - "Q2 Monthly Updates"
    - "Summer intern presentations"
  
  august:
    - "Q2 Board Package"
    - "Q2 Update Call"
    - "H2 planning kickoff"
  
  september:
    - "Investor Day / Analyst Day (if public)"
    - "Strategic initiative deep-dives"
  
  october:
    - "Q3 Monthly Updates"
    - "Budget planning for next year"
  
  november:
    - "Q3 Board Package"
    - "Q3 Update Call"
    - "Annual audit planning"
  
  december:
    - "Year-end close preparation"
    - "Board: Next year plan approval"
    - "Holiday investor update"
    - "409A planning for next year"
```

---

## Success Metrics for IR

```yaml
ir_kpis:
  communication:
    - "Monthly update open rate > 80%"
    - "Quarterly call attendance > 90% (major investors)"
    - "Response time to investor inquiries < 48 hours"
    - "Data room NPS > 50"
  
  fundraising:
    - "Target raise completed within timeline"
    - "Valuation within 20% of target range"
    - "Investor quality: Tier 1 leads, strategic value-add"
    - "Dilution at or below plan (Seed 20%, A 17%, B 15%)"
  
  governance:
    - "Board meeting attendance 100%"
    - "Consent items pre-approved 95%+"
    - "No material weaknesses in controls"
    - "Audit clean opinion (when applicable)"
  
  shareholder_satisfaction:
    - "Investor NPS > 50 (annual survey)"
    - "Zero surprise disclosures"
    - "Proactive communication on all material events"
    - "ESG reporting transparency score > 80%"
```

---

**Aligned With:** `500-business-model.md`, `510-go-to-market.md`, `520-pricing-packaging.md`, `530-metrics-analytics.md`, `540-partnerships.md`
**Next Review:** 2026-01-17