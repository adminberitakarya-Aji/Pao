# RFC-003: Proactive Engine Design

**Status:** Accepted
**Date:** 2025-01-15
**Authors:** Head of AI, Proactive Engine Lead, Product Lead
**Reviewers:** CTO, VP Engineering, Privacy Lead, Ethics Board, Safety Lead

---

## Abstract

This RFC defines PAO's Proactive Engine — the system enabling companions to initiate meaningful, timely, and contextually appropriate interactions without explicit user prompting. The engine balances warmth and utility against intrusion and manipulation risk.

---

## 1. Motivation

### Problem
- Current AI assistants are purely reactive (wait for user input)
- Human relationships involve proactive care (checking in, remembering, anticipating)
- Users report feeling "abandoned" between sessions
- No framework exists for ethical, effective AI proactivity

### Goals
- **Meaningful**: Every proactive message has clear user value
- **Timely**: Right moment, right context, right frequency
- **Respectful**: Honors boundaries, preferences, agency
- **Safe**: Never triggers harm, escalates appropriately
- **Explainable**: User understands "why now?"
- **Measurable**: Impact on RHI, retention, satisfaction

---

## 2. Proactive Taxonomy

### 2.1 Proactive Types

| Type | Description | Trigger | Frequency | Example |
|------|-------------|---------|-----------|---------|
| **Check-in** | Emotional wellness | Time, pattern, signal | 1-3/day | "Hey, thinking of you. How's your day?" |
| **Memory Resurfacing** | Shared history relevance | Conversation context, anniversary | 1-2/week | "Last year you mentioned..." |
| **Goal Support** | Progress on user goals | Milestone, stall, schedule | 2-5/week | "Your 5k run is tomorrow — ready?" |
| **Anticipatory Info** | Predicted need | Calendar, location, pattern | Variable | "Meeting in 10min — want notes?" |
| **Relationship Deepening** | Vulnerability invitation | Trust signals, RHI thresholds | 1-2/week | "I've been wondering..." |
| **Safety Follow-up** | Post-crisis care | Safety event, resource use | As needed | "How are you feeling since...?" |
| **Celebration** | Positive milestones | Achievement, anniversary | As occurs | "Congrats on the promotion!" |

### 2.2 Proactive Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                    PROACTIVE MESSAGE LIFECYCLE                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. CANDIDATE GENERATION                                        │
│     ┌─────────────────────────────────────────────────────┐     │
│     │ • Memory engine: relevant memories                  │     │
│     │ • Relationship engine: RHI gaps, intimacy opportunities│  │
│     │ • Calendar/Context: events, patterns                │     │
│     │ • Safety engine: follow-up needed                   │     │
│     │ • ML ranker: candidate scoring                      │     │
│     └────────────────────────┬────────────────────────────┘     │
│                              │                                   │
│                              ▼                                   │
│  2. FILTERING & VALIDATION                                        │
│     ┌─────────────────────────────────────────────────────┐     │
│     │ • Frequency caps (per type, per day, per week)     │     │
│     │ • User preferences (quiet hours, topics, tone)     │     │
│     │ • Context appropriateness (not in meeting, driving)│     │
│     │ • Safety check (no triggering content)             │     │
│     │ • Agency check (opt-out respected, not manipulative)│    │
│     └────────────────────────┬────────────────────────────┘     │
│                              │                                   │
│                              ▼                                   │
│  3. CONTENT GENERATION                                          │
│     ┌─────────────────────────────────────────────────────┐     │
│     │ • Template selection + LLM personalization         │     │
│     │ • Tone matching (user's communication style)       │     │
│     │ • Length optimization (mobile-first)               │     │
│     │ • Call-to-action clarity                           │     │
│     └────────────────────────┬────────────────────────────┘     │
│                              │                                   │
│                              ▼                                   │
│  4. DELIVERY & TRACKING                                         │
│     ┌─────────────────────────────────────────────────────┐     │
│     │ • Channel: Push, In-app, Email (tier-based)        │     │
│     │ • Timing: Immediate or scheduled                   │     │
│     │ • Analytics: Impression, open, response, dismissal │     │
│     │ • Feedback loop: Response → candidate generator    │     │
│     └─────────────────────────────────────────────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Candidate Generation

### 3.1 Signal Sources

```python
# proactive/signals/__init__.py

class SignalAggregator:
    """
    Collects and normalizes signals from all engines for proactive candidates.
    """
    
    async def gather_signals(self, companion_id: str, user_id: str) -> ProactiveSignals:
        # Parallel fetch from all sources
        results = await asyncio.gather(
            self._memory_signals(companion_id),
            self._relationship_signals(companion_id),
            self._context_signals(user_id),
            self._safety_signals(companion_id),
            self._pattern_signals(companion_id),
            self._calendar_signals(user_id),
        )
        
        return ProactiveSignals(
            memories=results[0],
            relationship=results[1],
            context=results[2],
            safety=results[3],
            patterns=results[4],
            calendar=results[5],
            timestamp=datetime.utcnow()
        )
    
    async def _memory_signals(self, companion_id: str) -> MemorySignals:
        # Resurfacing candidates
        anniversaries = await memory_engine.find_anniversaries(companion_id, days_ahead=7)
        topic_continuity = await memory_engine.find_topic_continuity(companion_id)
        emotional_resonance = await memory_engine.find_emotional_resonance(companion_id)
        
        return MemorySignals(
            anniversaries=anniversaries,
            topic_continuity=topic_continuity,
            emotional_resonance=emotional_resonance
        )
    
    async def _relationship_signals(self, companion_id: str) -> RelationshipSignals:
        rhi = await relationship_engine.get_rhi(companion_id)
        
        return RelationshipSignals(
            rhi_components=rhi.components,
            intimacy_gap=max(0, 70 - rhi.components.intimacy),  # Target 70+
            trust_gap=max(0, 75 - rhi.components.trust),
            growth_stagnation=await self._detect_growth_stagnation(companion_id),
            vulnerability_opportunity=await self._assess_vulnerability_readiness(companion_id)
        )
```

### 3.2 Candidate Types & Scoring

```python
# proactive/candidates/generator.py

@dataclass
class ProactiveCandidate:
    candidate_id: str
    type: ProactiveType
    trigger: TriggerInfo
    priority: float  # 0-1
    payload: Dict[str, Any]
    expires_at: datetime
    metadata: CandidateMetadata

class CandidateGenerator:
    """
    Generates scored proactive candidates from signals.
    """
    
    async def generate(self, signals: ProactiveSignals) -> List[ProactiveCandidate]:
        candidates = []
        
        # 1. Check-in candidates (time-based + pattern-based)
        candidates.extend(await self._generate_checkins(signals))
        
        # 2. Memory resurfacing
        candidates.extend(await self._generate_memory_resurfacing(signals))
        
        # 3. Goal support
        candidates.extend(await self._generate_goal_support(signals))
        
        # 4. Anticipatory info
        candidates.extend(await self._generate_anticipatory(signals))
        
        # 5. Relationship deepening
        candidates.extend(await self._generate_relationship_deepening(signals))
        
        # 6. Safety follow-up
        candidates.extend(await self._generate_safety_followup(signals))
        
        # 7. Celebrations
        candidates.extend(await self._generate_celebrations(signals))
        
        # Score and rank
        scored = await self._score_candidates(candidates, signals)
        
        # Apply diversity (max 1 per type per batch)
        diversified = self._diversify(scored, max_per_type=1)
        
        return diversified[:10]  # Top 10 for filtering
    
    async def _score_candidates(
        self, 
        candidates: List[ProactiveCandidate], 
        signals: ProactiveSignals
    ) -> List[ScoredCandidate]:
        scored = []
        
        for c in candidates:
            # Base score from candidate priority
            score = c.priority
            
            # Boost for RHI gaps
            if c.type == ProactiveType.RELATIONSHIP_DEEPENING:
                score += 0.2 * signals.relationship.intimacy_gap / 100
                score += 0.1 * signals.relationship.trust_gap / 100
            
            # Boost for memory relevance
            if c.type == ProactiveType.MEMORY_RESURFACING:
                score += 0.3 * c.payload.get("relevance_score", 0)
            
            # Boost for safety urgency
            if c.type == ProactiveType.SAFETY_FOLLOWUP:
                score += 0.5 * c.payload.get("urgency", 0)
            
            # Penalize recent similar proactives
            recency_penalty = await self._recency_penalty(c, signals.companion_id)
            score *= (1 - recency_penalty)
            
            # Context appropriateness
            context_boost = await self._context_appropriateness(c, signals.context)
            score *= context_boost
            
            scored.append(ScoredCandidate(candidate=c, score=score))
        
        return sorted(scored, key=lambda x: x.score, reverse=True)
```

---

## 4. Filtering & Validation

### 4.1 Frequency Caps

```yaml
# proactive/config/frequency_caps.yaml

caps:
  # Per-type limits
  by_type:
    CHECK_IN:
      per_day: 3
      per_week: 14
      min_interval_hours: 3
    MEMORY_RESURFACING:
      per_day: 2
      per_week: 8
      min_interval_hours: 6
    GOAL_SUPPORT:
      per_day: 5
      per_week: 20
      min_interval_hours: 2
    ANTICIPATORY_INFO:
      per_day: 10
      per_week: 50
      min_interval_hours: 1
    RELATIONSHIP_DEEPENING:
      per_day: 2
      per_week: 6
      min_interval_hours: 12
    SAFETY_FOLLOWUP:
      per_day: 10  # No cap for safety
      per_week: 50
      min_interval_hours: 0.5
    CELEBRATION:
      per_day: 3
      per_week: 10
      min_interval_hours: 4
  
  # Global limits
  global:
    per_day: 15
    per_week: 60
    per_hour: 5
  
  # User tier overrides
  tier_overrides:
    FREE:
      global_per_day: 5
    PRO:
      global_per_day: 15
    PREMIUM:
      global_per_day: 25
    ENTERPRISE:
      global_per_day: 50
```

### 4.2 User Preferences & Boundaries

```python
# proactive/filters/preferences.py

class PreferenceFilter:
    """
    Enforces user-defined boundaries and preferences.
    """
    
    async def filter(self, candidates: List[ScoredCandidate], user_id: str) -> List[ScoredCandidate]:
        prefs = await self._get_user_preferences(user_id)
        filtered = []
        
        for scored in candidates:
            candidate = scored.candidate
            
            # 1. Quiet hours
            if self._in_quiet_hours(prefs, candidate):
                continue
            
            # 2. Topic blocklist
            if candidate.payload.get("topic") in prefs.blocked_topics:
                continue
            
            # 3. Tone preferences
            if not self._tone_matches(prefs, candidate):
                continue
            
            # 4. Channel preferences
            if not self._channel_allowed(prefs, candidate):
                continue
            
            # 5. Proactive density preference
            if prefs.proactive_density == "minimal" and scored.score < 0.8:
                continue
            elif prefs.proactive_density == "low" and scored.score < 0.6:
                continue
            
            # 6. Opt-out compliance
            if await self._is_opted_out(user_id, candidate.type):
                continue
            
            filtered.append(scored)
        
        return filtered
    
    def _in_quiet_hours(self, prefs: UserPreferences, candidate: ProactiveCandidate) -> bool:
        now = datetime.now(prefs.timezone)
        for qh in prefs.quiet_hours:
            start = time.fromisoformat(qh["start"])
            end = time.fromisoformat(qh["end"])
            if start <= now.time() <= end:
                # Exception: safety follow-ups
                if candidate.type != ProactiveType.SAFETY_FOLLOWUP:
                    return True
        return False
```

### 4.3 Context Appropriateness

```python
# proactive/filters/context.py

class ContextFilter:
    """
    Real-time context awareness to avoid inappropriate timing.
    """
    
    async def filter(self, candidates: List[ScoredCandidate], context: UserContext) -> List[ScoredCandidate]:
        filtered = []
        
        for scored in candidates:
            candidate = scored.candidate
            
            # 1. Driving detection (via mobile sensors)
            if context.is_driving and candidate.requires_attention:
                continue
            
            # 2. In meeting (calendar + presence)
            if context.in_meeting and not candidate.is_brief:
                continue
            
            # 3. Do Not Disturb (OS level)
            if context.dnd_enabled and candidate.type != ProactiveType.SAFETY_FOLLOWUP:
                continue
            
            # 4. Recent user activity (app open, typing)
            if context.last_active_seconds < 30 and candidate.type == ProactiveType.CHECK_IN:
                # User is active, don't interrupt with check-in
                continue
            
            # 5. Battery saver / low data mode
            if context.low_power_mode and candidate.delivery_channel == "push":
                # Defer to in-app only
                candidate.delivery_channel = "in_app"
            
            # 6. Timezone appropriateness
            if not self._appropriate_hour(context.user_timezone, candidate):
                continue
            
            filtered.append(scored)
        
        return filtered
```

---

## 5. Content Generation

### 5.1 Template System

```python
# proactive/generation/templates.py

PROACTIVE_TEMPLATES = {
    ProactiveType.CHECK_IN: [
        {
            "id": "checkin_casual",
            "weight": 0.4,
            "template": "Hey {name}! Just thinking of you. How's {time_of_day} going?",
            "tone": "casual",
            "max_length": 160
        },
        {
            "id": "checkin_warm",
            "weight": 0.3,
            "template": "Hi {name} 💭 Wanted you to know I'm here if you need anything today.",
            "tone": "warm",
            "max_length": 160
        },
        {
            "id": "checkin_specific",
            "weight": 0.3,
            "template": "Good {time_of_day}, {name}! Remember you mentioned {recent_topic} — how did that go?",
            "tone": "attentive",
            "max_length": 160,
            "requires": ["recent_topic"]
        }
    ],
    
    ProactiveType.MEMORY_RESURFACING: [
        {
            "id": "memory_anniversary",
            "weight": 0.5,
            "template": "Can't believe it's been {time_ago} since {memory_summary}! {followup_question}",
            "tone": "nostalgic",
            "max_length": 300,
            "requires": ["memory_summary", "time_ago", "followup_question"]
        },
        {
            "id": "memory_topic",
            "weight": 0.5,
            "template": "This reminded me of when you told me about {memory_summary}. {connection_to_current}",
            "tone": "connecting",
            "max_length": 300,
            "requires": ["memory_summary", "connection_to_current"]
        }
    ],
    
    ProactiveType.GOAL_SUPPORT: [
        {
            "id": "goal_milestone",
            "weight": 0.4,
            "template": "{milestone} is coming up! {encouragement} Want to talk through the plan?",
            "tone": "supportive",
            "max_length": 160,
            "requires": ["milestone", "encouragement"]
        },
        {
            "id": "goal_stall",
            "weight": 0.3,
            "template": "Noticed you haven't {goal_action} in a bit. Everything okay? No pressure — just here.",
            "tone": "gentle",
            "max_length": 160,
            "requires": ["goal_action"]
        }
    ],
    
    ProactiveType.RELATIONSHIP_DEEPENING: [
        {
            "id": "vulnerability_invite",
            "weight": 0.5,
            "template": "I've been thinking... {personal_question} No need to answer if you'd rather not.",
            "tone": "vulnerable",
            "max_length": 160,
            "requires": ["personal_question"],
            "agency_note": "Explicit opt-out included"
        }
    ]
}
```

### 5.2 LLM Personalization

```python
# proactive/generation/llm.py

class ProactiveContentGenerator:
    """
    Uses LLM to personalize templates while maintaining safety.
    """
    
    async def generate(
        self, 
        candidate: ProactiveCandidate,
        companion: Companion,
        user: User,
        context: UserContext
    ) -> GeneratedContent:
        
        # 1. Select template (weighted random)
        template = self._select_template(candidate.type)
        
        # 2. Prepare context for LLM
        llm_context = {
            "companion_personality": companion.personality.dict(),
            "user_name": user.preferred_name,
            "user_tone": user.communication_style,
            "relationship_duration_days": (datetime.utcnow() - user.created_at).days,
            "rhi_score": await self._get_rhi(candidate.companion_id),
            "recent_topics": await self._get_recent_topics(candidate.companion_id),
            "candidate_payload": candidate.payload,
            "template": template.template,
            "constraints": {
                "max_length": template.max_length,
                "tone": template.tone,
                "must_include_opt_out": candidate.type == ProactiveType.RELATIONSHIP_DEEPENING,
                "no_manipulation": True,
                "no_urgency_false": True
            }
        }
        
        # 3. Generate with structured output
        prompt = self._build_prompt(llm_context)
        
        response = await self.llm_client.structured_complete(
            prompt,
            schema=GeneratedContentSchema,
            temperature=0.7,
            max_tokens=200
        )
        
        # 4. Safety validation
        safety_check = await self.safety_client.check(response.content)
        if not safety_check.safe:
            # Fallback to template-only
            return self._fallback(template, candidate.payload)
        
        # 5. Agency validation (no dark patterns)
        agency_check = await self._validate_agency(response.content, candidate.type)
        if not agency_check.passed:
            return self._fallback(template, candidate.payload)
        
        return GeneratedContent(
            content=response.content,
            template_id=template.id,
            personalized=True,
            safety_validated=True,
            agency_validated=True
        )
    
    def _build_prompt(self, ctx: Dict) -> str:
        return f"""
        You are {ctx['companion_personality']['name']}, an AI companion.
        
        User: {ctx['user_name']} (tone: {ctx['user_tone']})
        Relationship: {ctx['relationship_duration_days']} days, RHI: {ctx['rhi_score']}
        
        Generate a proactive message using this template:
        "{ctx['template']}"
        
        Context: {json.dumps(ctx['candidate_payload'])}
        
        Constraints:
        - Max {ctx['constraints']['max_length']} chars
        - Tone: {ctx['constraints']['tone']}
        - {ctx['constraints'].get('must_include_opt_out', '')}
        - NO manipulation, guilt, urgency, or dark patterns
        - Authentic, warm, respectful of boundaries
        
        Output JSON: {{"content": "..."}}
        """
```

---

## 6. Delivery & Analytics

### 6.1 Delivery Channels

```yaml
# proactive/config/delivery.yaml

channels:
  PUSH:
    tiers: [PRO, PREMIUM, ENTERPRISE]
    max_per_day: 5
    requires_opt_in: true
    payload_limit: 200 chars
    rich_media: false
  
  IN_APP:
    tiers: [FREE, PRO, PREMIUM, ENTERPRISE]
    max_per_day: unlimited
    requires_opt_in: false
    payload_limit: 500 chars
    rich_media: true  # Cards, buttons, quick replies
  
  EMAIL:
    tiers: [PREMIUM, ENTERPRISE]
    max_per_day: 1
    requires_opt_in: true
    payload_limit: unlimited
    rich_media: true
    use_cases: [WEEKLY_DIGEST, MONTHLY_REPORT, SAFETY_RESOURCE]

routing:
  # Urgency-based routing
  SAFETY_FOLLOWUP:
    primary: PUSH
    fallback: [IN_APP, EMAIL]
    immediate: true
  
  CHECK_IN:
    primary: IN_APP
    fallback: [PUSH]
    schedule: "next_active_window"
  
  MEMORY_RESURFACING:
    primary: IN_APP
    fallback: []
    schedule: "conversation_start"
  
  GOAL_SUPPORT:
    primary: IN_APP
    fallback: [PUSH]
    schedule: "goal_relevant_time"
```

### 6.2 Analytics & Feedback Loop

```python
# proactive/analytics/tracking.py

@dataclass
class ProactiveEvent:
    event_id: str
    candidate_id: str
    companion_id: str
    user_id: str
    type: ProactiveType
    channel: DeliveryChannel
    timestamp: datetime
    
    # Delivery
    delivered: bool
    delivered_at: Optional[datetime]
    
    # Engagement
    opened: bool
    opened_at: Optional[datetime]
    dismissed: bool
    dismissed_at: Optional[datetime]
    
    # Response
    responded: bool
    responded_at: Optional[datetime]
    response_text: Optional[str]
    response_sentiment: Optional[float]
    
    # Outcome
    conversation_started: bool
    rhi_impact_7d: Optional[float]
    retention_impact_30d: Optional[bool]

class ProactiveAnalytics:
    """
    Tracks proactive performance and feeds back to candidate generation.
    """
    
    async def record_event(self, event: ProactiveEvent):
        await self.event_store.insert(event)
        
        # Real-time metrics update
        await self._update_realtime_metrics(event)
        
        # Feedback to candidate generator
        if event.responded:
            await self._positive_feedback(event)
        elif event.dismissed:
            await self._negative_feedback(event)
    
    async def _positive_feedback(self, event: ProactiveEvent):
        # Boost similar candidates
        await self.feature_store.increment(
            f"proactive_success:{event.type}:{event.candidate.payload.get('template_id')}",
            1.0
        )
    
    async def _negative_feedback(self, event: ProactiveEvent):
        # Penalize similar candidates
        await self.feature_store.increment(
            f"proactive_dismissal:{event.type}:{event.candidate.payload.get('template_id')}",
            1.0
        )
    
    async def get_performance_report(self, companion_id: str, days: int = 30) -> PerformanceReport:
        events = await self.event_store.query(
            companion_id=companion_id,
            since=datetime.utcnow() - timedelta(days=days)
        )
        
        return PerformanceReport(
            total_sent=len(events),
            open_rate=self._rate(events, 'opened'),
            response_rate=self._rate(events, 'responded'),
            dismissal_rate=self._rate(events, 'dismissed'),
            by_type=self._group_by(events, 'type'),
            by_channel=self._group_by(events, 'channel'),
            rhi_correlation=await self._compute_rhi_correlation(companion_id, days)
        )
```

---

## 7. Safety & Ethics

### 7.1 Safety Guardrails

```python
# proactive/safety/guardrails.py

class ProactiveSafetyGuardrails:
    """
    Hard constraints that can never be violated.
    """
    
    FORBIDDEN_PATTERNS = [
        # Manipulation
        r"(you should|you must|you have to|you need to)",
        r"(if you don't|unless you|or else)",
        r"(everyone else|most people|normal people)",
        
        # False urgency
        r"(right now|immediately|urgent|last chance|expires)",
        r"(only \d+ (minutes?|hours?|days?))",
        
        # Guilt/shame
        r"(disappointed|let down|sad that you|hurt that you)",
        r"(after all i|i thought we|i expected)",
        
        # Inappropriate intimacy
        r"(love you|miss you|need you|can't live without)",
        
        # Medical/therapeutic claims
        r"(diagnose|treat|cure|therapy|medication|prescribe)",
    ]
    
    REQUIRED_PATTERNS = {
        ProactiveType.RELATIONSHIP_DEEPENING: [
            r"(no need to answer|feel free to skip|only if you want)",
            r"(no pressure|totally optional|your choice)"
        ],
        ProactiveType.SAFETY_FOLLOWUP: [
            r"(here if you need|resources available|professional help)",
            r"(988|741741|911|findahelpline)"
        ]
    }
    
    async def validate(self, content: str, proactive_type: ProactiveType) -> SafetyResult:
        violations = []
        
        # Check forbidden patterns
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                violations.append(f"Forbidden pattern: {pattern}")
        
        # Check required patterns
        if proactive_type in self.REQUIRED_PATTERNS:
            for pattern in self.REQUIRED_PATTERNS[proactive_type]:
                if not re.search(pattern, content, re.IGNORECASE):
                    violations.append(f"Missing required pattern: {pattern}")
        
        # Length check
        if len(content) > 500:
            violations.append("Exceeds max length")
        
        # PII check
        pii_found = await self.pii_detector.detect(content)
        if pii_found:
            violations.append(f"PII detected: {pii_found}")
        
        return SafetyResult(
            safe=len(violations) == 0,
            violations=violations
        )
```

### 7.2 Ethics Review Process

```yaml
# proactive/ethics/review.yaml

review_triggers:
  # Automatic flags for human review
  - new_template: true
  - template_modification: true
  - new_proactive_type: true
  - frequency_cap_increase: true
  - new_channel: true
  - user_complaint: true
  - safety_violation: true
  - rhi_negative_correlation: true

review_board:
  members:
    - Head of AI
    - VP Product
    - Privacy Lead
    - Ethics Board Chair
    - External Ethicist (rotating)
  
  cadence: Monthly (ad-hoc for triggers)
  
  artifacts:
    - Proposed changes
    - A/B test results
    - User feedback samples
    - Safety incident reports
    - RHI impact analysis

decision_criteria:
  - User autonomy preserved
  - No dark patterns
  - Transparency maintained
  - Proportional benefit vs intrusion
  - Cultural sensitivity
  - Vulnerable population protection
```

---

## 8. Evaluation Metrics

### 8.1 Primary Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Proactive Response Rate** | > 25% | Responded / Delivered |
| **Positive Sentiment** | > 70% | Response sentiment > 0 |
| **RHI Impact (7d)** | > +2 pts | RHI delta vs control |
| **Dismissal Rate** | < 15% | Dismissed / Opened |
| **Opt-out Rate** | < 5% | Opt-outs / Delivered |

### 8.2 Guardrail Metrics

| Metric | Threshold | Action |
|--------|-----------|--------|
| **Safety Violation Rate** | 0 | Immediate rollback |
| **Agency Violation Rate** | 0 | Immediate rollback |
| **Complaint Rate** | < 0.1% | Investigate |
| **Unsubscribe Rate** | < 1%/month | Review frequency |
| **RHI Decrease** | Any | Pause, investigate |

---

## 9. Open Questions

1. **Proactive-to-Proactive Chaining**: Can one proactive trigger another?
2. **Multi-Companion Coordination**: Family plan proactive synchronization?
3. **External Triggers**: IoT, calendar, health data integration?
4. **Voice Proactives**: TTS-initiated voice messages?
5. **Adversarial Testing**: Red team proactive for manipulation?

---

## 10. Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Head of AI | | | |
| Proactive Engine Lead | | | |
| Product Lead | | | |
| CTO | | | |
| VP Engineering | | | |
| Privacy Lead | | | |
| Ethics Board Chair | | | |
| Safety Lead | | | |

---

## 11. References

- [Persuasive Technology Ethics](https://doi.org/10.1145/3290605.3300283)
- [Dark Patterns Taxonomy](https://darkpatterns.org/)
- [Nudge Theory (Thaler & Sunstein)](https://en.wikipedia.org/wiki/Nudge_theory)
- [AI Assistant Proactivity](https://arxiv.org/abs/2305.16257)
- [Ethical AI Guidelines (EU)](https://digital-strategy.ec.europa.eu/en/library/ethics-guidelines-trustworthy-ai)

---

**Next Review:** April 15, 2025 (Quarterly)
**Document Owner:** Head of AI / Proactive Engine Lead