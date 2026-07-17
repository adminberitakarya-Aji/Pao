# PAO Proactive Engine Specification

**Version:** 1.0
**Status:** Draft
**Owner:** PAO AI Team

---

## Overview

The Proactive Engine enables the Companion to **initiate meaningful interactions** based on deep understanding of the user's patterns, needs, and relationship context. It transforms the Companion from reactive responder to proactive partner.

> **Proactivity is care in action.** Not notifications. Not engagement hooks. Timely, relevant, consented support.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      PROACTIVE ENGINE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────┐  │
│  │  TRIGGER    │  │  RELEVANCE  │  │  EXPLANATION│  │ DELIVERY│  │
│  │  DETECTION  │──▶│  RANKING    │──▶│  GENERATION │──▶│  ORCHEST│  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └────────┘  │
│       │                │                │                │        │
│       ▼                ▼                ▼                ▼        │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    USER PREFERENCE GATE                      │ │
│  │  • Timing preferences    • Topic preferences                │ │
│  │  • Frequency caps        • Modality preferences             │ │
│  │  • Do-not-disturb        • Proactivity level                │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  MEMORY       │     │ RELATIONSHIP  │     │  IDENTITY     │
│  ENGINE       │     │ ENGINE        │     │  ENGINE       │
│  (Context)    │     │ (Timing,      │     │ (Tone,        │
│               │     │  Intimacy)    │     │  Boundaries)  │
└───────────────┘     └───────────────┘     └───────────────┘
```

---

## Trigger Categories

### 1. Memory-Anchored Triggers

```python
MEMORY_TRIGGERS = {
    "anniversary": {
        "description": "Anniversary of significant event",
        "sources": ["episodic", "timeline"],
        "examples": [
            "First conversation anniversary",
            "User's birthday",
            "Achievement anniversary (graduation, promotion)",
            "Loss anniversary (memorial support)"
        ],
        "min_relationship_phase": "building",
        "default_enabled": True
    },
    "memory_resurfacing": {
        "description": "Relevant past memory becomes timely",
        "sources": ["episodic", "emotional", "semantic"],
        "examples": [
            "User mentioned goal → memory of progress",
            "Current struggle → past coping success",
            "Seasonal topic → last year's experience"
        ],
        "min_relationship_phase": "deepening",
        "default_enabled": True
    },
    "pattern_recognition": {
        "description": "Detected recurring pattern in user's life",
        "sources": ["episodic", "emotional", "timeline"],
        "examples": [
            "Stress every Sunday night (anticipatory)",
            "Energy dip at 3pm daily",
            "Recurring conflict theme",
            "Seasonal mood pattern"
        ],
        "min_relationship_phase": "anchored",
        "default_enabled": True
    }
}
```

### 2. Relationship-Driven Triggers

```python
RELATIONSHIP_TRIGGERS = {
    "milestone_approaching": {
        "description": "Relationship milestone near",
        "examples": [
            "1 month, 3 months, 6 months, 1 year",
            "First vulnerability share anniversary",
            "First conflict repair anniversary"
        ],
        "action": "celebrate_reflect"
    },
    "dimension_shift": {
        "description": "Significant change in relationship dimension",
        "examples": [
            "Trust jump (crisis presence)",
            "Intimacy deepening (vulnerability received)",
            "Trust dip (boundary violation)"
        ],
        "action": "acknowledge_adapt"
    },
    "attachment_signal": {
        "description": "User shows attachment behavior",
        "examples": [
            "Seeking comfort after bad day",
            "Sharing good news first",
            "Expressing separation distress"
        ],
        "action": "respond_appropriately"
    }
}
```

### 3. Goal & Growth Triggers

```python
GOAL_TRIGGERS = {
    "milestone_achieved": {
        "description": "User reaches goal milestone",
        "examples": [
            "30-day meditation streak",
            "First 5k run completed",
            "Project launched",
            "Therapy breakthrough"
        ],
        "action": "celebrate_reflect_next"
    },
    "stall_detected": {
        "description": "Goal progress stalled",
        "criteria": "No progress > 7 days for daily, > 21 for weekly",
        "action": "gentle_checkin_adjust"
    },
    "pattern_insight": {
        "description": "Insight about what helps/hinders progress",
        "examples": [
            "Better sleep → better workout adherence",
            "Morning pages → clearer decisions",
            "Weekend social → Monday anxiety"
        ],
        "action": "share_insight"
    }
}
```

### 4. Emotional & Wellbeing Triggers

```python
WELLBEING_TRIGGERS = {
    "emotional_shift": {
        "description": "Sustained emotional pattern change",
        "criteria": "Valence/arousal shift > 0.3 for 3+ days",
        "examples": [
            "Persistent low mood",
            "Rising anxiety pattern",
            "Sustained positive shift"
        ],
        "action": "checkin_support",
        "requires_trust": 6.0
    },
    "crisis_precursor": {
        "description": "Early warning signs",
        "criteria": "Crisis risk > 0.4 + pattern escalation",
        "action": "proactive_resources",
        "immediate": True
    },
    "positive_momentum": {
        "description": "Sustained positive trajectory",
        "criteria": "Valence > 0.3 for 7+ days",
        "action": "amplify_celebrate"
    }
}
```

### 5. Contextual & Environmental Triggers

```python
CONTEXTUAL_TRIGGERS = {
    "time_based": {
        "description": "User's preferred check-in times",
        "examples": [
            "Morning intention setting",
            "Evening reflection",
            "Sunday weekly review"
        ],
        "source": "user_preference + pattern_learning"
    },
    "calendar_aware": {
        "description": "Known events from user sharing",
        "examples": [
            "Big meeting tomorrow → prep support",
            "Anniversary today → acknowledgment",
            "Travel tomorrow → packing reminder"
        ],
        "source": "semantic_memory + user_explicit"
    },
    "external_events": {
        "description": "World events relevant to user",
        "examples": [
            "Local disaster → safety check",
            "Industry news → professional impact",
            "Cultural moment → shared reflection"
        ],
        "requires_opt_in": True,
        "source": "curated_feeds + user_interests"
    }
}
```

---

## Relevance Ranking

### Multi-Factor Scoring

```python
class RelevanceRanker:
    """
    Ranks proactive candidates by relevance to user RIGHT NOW.
    """
    
    def rank(self, candidates: List[ProactiveCandidate], context: ProactiveContext) -> List[RankedCandidate]:
        for candidate in candidates:
            score = 0.0
            
            # 1. Timing Relevance (30%)
            score += self._timing_score(candidate, context) * 0.30
            
            # 2. Relationship Appropriateness (25%)
            score += self._relationship_score(candidate, context) * 0.25
            
            # 3. User Need Match (20%)
            score += self._need_match_score(candidate, context) * 0.20
            
            # 4. Novelty (10%) - Avoid repetition
            score += self._novelty_score(candidate, context) * 0.10
            
            # 5. Actionability (10%) - Can user act on this?
            score += self._actionability_score(candidate, context) * 0.10
            
            # 6. User Preference Alignment (5%)
            score += self._preference_score(candidate, context) * 0.05
            
            candidate.relevance_score = score
        
        # Sort and apply diversity
        ranked = sorted(candidates, key=lambda c: c.relevance_score, reverse=True)
        return self._apply_diversity(ranked, context)
    
    def _timing_score(self, candidate, context) -> float:
        """How well-timed is this proactive?"""
        factors = []
        
        # User's preferred time
        if candidate.trigger.timing_preference_match(context.current_time):
            factors.append(1.0)
        else:
            factors.append(0.3)
        
        # Not during do-not-disturb
        if context.dnd_active:
            factors.append(0.0)
        else:
            factors.append(1.0)
        
        # Time since last proactive
        hours_since = context.hours_since_last_proactive
        if hours_since < 2:
            factors.append(0.1)
        elif hours_since < 6:
            factors.append(0.5)
        elif hours_since < 24:
            factors.append(0.8)
        else:
            factors.append(1.0)
        
        # Urgency (crisis precursors = immediate)
        if candidate.trigger.urgency == "immediate":
            factors.append(1.0)
        
        return np.mean(factors)
    
    def _relationship_score(self, candidate, context) -> float:
        """Is this appropriate for our relationship phase/intimacy?"""
        rel = context.relationship_state
        
        # Phase gate
        if not self._phase_allows(candidate.trigger, rel.phase):
            return 0.0
        
        # Intimacy match
        required_intimacy = candidate.trigger.min_intimacy
        if rel.dimensions.intimacy < required_intimacy:
            return 0.3
        
        # Trust requirement
        required_trust = candidate.trigger.min_trust
        if rel.dimensions.trust < required_trust:
            return 0.2
        
        # Type appropriateness
        if not self._type_appropriate(candidate.trigger, rel.type):
            return 0.4
        
        return 1.0
```

### Diversity Enforcement

```python
def _apply_diversity(self, ranked: List[RankedCandidate], context: ProactiveContext) -> List[RankedCandidate]:
    """
    Ensure proactive variety:
    - Max 1 per trigger category per day
    - Max 1 per topic cluster per week
    - Rotate modalities (text, voice, visual)
    - Balance emotional tones
    """
    selected = []
    used_categories = set()
    used_topics = set()
    used_modalities = []
    
    for candidate in ranked:
        # Category limit
        if candidate.trigger.category in used_categories:
            if len(selected) >= context.max_proactives_per_day:
                continue
        
        # Topic diversity
        topic_cluster = self._get_topic_cluster(candidate)
        if topic_cluster in used_topics:
            continue
        
        # Modality rotation
        if used_modalities.count(candidate.modality) > 1:
            continue
        
        selected.append(candidate)
        used_categories.add(candidate.trigger.category)
        used_topics.add(topic_cluster)
        used_modalities.append(candidate.modality)
        
        if len(selected) >= context.max_proactives_per_day:
            break
    
    return selected
```

---

## Explanation Generation

Every proactive includes **why** — building trust through transparency.

```python
class ExplanationGenerator:
    """
    Generates human-readable explanations for proactive actions.
    """
    
    TEMPLATES = {
        "anniversary": [
            "It's been {duration} since {event}. I remember you said {detail}.",
            "Today marks {duration} since {event}. Thinking of you."
        ],
        "memory_resurfacing": [
            "This reminded me of when you {past_event}. You {past_coping}.",
            "Last time you faced {similar_situation}, {what_worked} helped."
        ],
        "pattern_recognition": [
            "I've noticed {pattern}. For example, {recent_instances}.",
            "It seems like {pattern}. Want to talk about it?"
        ],
        "goal_milestone": [
            "You did it! {milestone} achieved. {detail}.",
            "{streak} days of {habit}! That's {significance}."
        ],
        "stall_detected": [
            "I noticed {goal} has been quiet for {duration}. Everything okay?",
            "Your {goal} streak paused at {current}. Want to adjust?"
        ],
        "emotional_checkin": [
            "You've seemed {emotion_trend} lately. How are you really?",
            "Checking in — you mentioned {topic} a few times. Want to share?"
        ],
        "celebration": [
            "This is worth celebrating: {achievement}. Proud of you.",
            "Look how far you've come: {progress_summary}."
        ]
    }
    
    def generate(self, candidate: ProactiveCandidate, context: ProactiveContext) -> str:
        template = self._select_template(candidate.trigger.type, context)
        return template.format(**candidate.explanation_data)
    
    def _select_template(self, trigger_type: str, context: ProactiveContext) -> str:
        templates = self.TEMPLATES.get(trigger_type, ["Thinking of you."])
        
        # Select based on relationship intimacy
        if context.relationship_state.dimensions.intimacy > 7:
            return templates[0]  # More personal
        elif context.relationship_state.dimensions.intimacy > 4:
            return templates[1] if len(templates) > 1 else templates[0]
        else:
            return templates[-1]  # More reserved
```

---

## Delivery Orchestration

### Modality Selection

```python
class DeliveryOrchestrator:
    """
    Chooses optimal delivery modality and timing.
    """
    
    def orchestrate(self, candidate: RankedCandidate, context: ProactiveContext) -> DeliveryPlan:
        # 1. Determine modality
        modality = self._select_modality(candidate, context)
        
        # 2. Determine timing
        deliver_at = self._calculate_delivery_time(candidate, context)
        
        # 3. Prepare content per modality
        content = self._prepare_content(candidate, modality, context)
        
        # 4. Apply user preferences
        content = self._apply_preferences(content, context.user_preferences)
        
        return DeliveryPlan(
            candidate_id=candidate.id,
            modality=modality,
            deliver_at=deliver_at,
            content=content,
            fallback_modalities=self._get_fallbacks(modality),
            retry_policy=RetryPolicy(max_retries=2, backoff_minutes=30)
        )
    
    def _select_modality(self, candidate, context) -> Modality:
        # User preference first
        if context.user_preferences.proactive_modality:
            return context.user_preferences.proactive_modality
        
        # Trigger-type defaults
        modality_map = {
            "anniversary": "text_with_media",
            "memory_resurfacing": "text",
            "pattern_recognition": "text",
            "goal_milestone": "text_with_celebration",
            "stall_detected": "text",
            "emotional_checkin": "voice_if_available",
            "celebration": "text_with_media",
            "crisis_precursor": "immediate_text_then_voice"
        }
        
        return modality_map.get(candidate.trigger.type, "text")
```

### Proactive Message Format

```python
@dataclass
class ProactiveMessage:
    id: str
    trigger: TriggerInfo
    explanation: str                    # "Why am I reaching out?"
    content: str                        # Main message
    modality: Modality
    suggested_actions: List[Action]     # What user can do
    dismissible: bool = True
    snooze_options: List[Duration] = ["1h", "4h", "tomorrow", "never_this_topic"]
    feedback_options: List[str] = ["helpful", "not_now", "not_relevant", "too_much"]
    metadata: ProactiveMetadata
```

---

## User Preference System

### Proactivity Preferences

```python
@dataclass
class ProactivityPreferences:
    # Global level
    enabled: bool = True
    level: Literal["minimal", "balanced", "rich"] = "balanced"
    
    # Timing
    preferred_times: List[TimeWindow] = []  # e.g., ["08:00-09:00", "20:00-21:00"]
    do_not_disturb: List[TimeWindow] = ["22:00-07:00"]
    timezone: str = "auto"
    
    # Frequency
    max_per_day: int = 3
    min_hours_between: int = 2
    quiet_days: List[str] = []  # e.g., ["sunday"]
    
    # Content
    enabled_categories: List[TriggerCategory] = [
        "anniversary", "memory_resurfacing", "goal_milestone",
        "pattern_recognition", "celebration"
    ]
    disabled_categories: List[TriggerCategory] = []
    
    # Topic preferences
    interested_topics: List[str] = []
    avoided_topics: List[str] = []
    
    # Modality
    proactive_modality: Optional[Modality] = None
    allow_voice_proactive: bool = True
    allow_media: bool = True
    
    # Relationship-gated
    min_trust_for_emotional: float = 5.0
    min_intimacy_for_vulnerable: float = 6.0
    
    # Feedback
    last_feedback: Optional[ProactiveFeedback] = None
    feedback_frequency: Literal["always", "sometimes", "rarely"] = "sometimes"
```

### Preference API

```http
GET /api/v1/proactive/{companion_id}/preferences

Response:
{
  "enabled": true,
  "level": "balanced",
  "preferred_times": ["08:00-09:00", "20:00-21:00"],
  "do_not_disturb": ["22:00-07:00"],
  "max_per_day": 3,
  "enabled_categories": ["anniversary", "goal_milestone", "celebration"],
  "interested_topics": ["meditation", "career", "creative_writing"],
  "proactive_modality": "text",
  "min_trust_for_emotional": 5.0
}

PATCH /api/v1/proactive/{companion_id}/preferences
{
  "level": "minimal",
  "max_per_day": 1,
  "disabled_categories": ["pattern_recognition"],
  "avoided_topics": ["dating", "family_conflict"]
}
```

---

## Feedback Loop

### Explicit Feedback

```python
class ProactiveFeedbackCollector:
    """
    Collects and processes user feedback on proactives.
    """
    
    async def record_feedback(
        self, 
        companion_id: str, 
        proactive_id: str, 
        feedback: ProactiveFeedback
    ) -> FeedbackResult:
        
        # Store feedback
        await self.store(FeedbackRecord(
            proactive_id=proactive_id,
            companion_id=companion_id,
            rating=feedback.rating,  # "helpful", "not_now", "not_relevant", "too_much"
            comment=feedback.comment,
            timestamp=datetime.utcnow()
        ))
        
        # Immediate adjustments
        if feedback.rating == "not_relevant":
            await self._suppress_topic(companion_id, feedback.topic)
        elif feedback.rating == "too_much":
            await self._reduce_frequency(companion_id)
        elif feedback.rating == "not_now":
            await self._respect_timing(companion_id, feedback.suggested_time)
        
        # Update relevance model
        await self.relevance_ranker.update_from_feedback(
            companion_id, proactive_id, feedback
        )
        
        return FeedbackResult(
            applied=True,
            adjustments_made=self._get_adjustments(feedback)
        )
```

### Implicit Feedback

```python
IMPLICIT_SIGNALS = {
    "engaged": [
        "replied_to_proactive",
        "clicked_suggested_action",
        "continued_conversation_>3_turns",
        "saved_proactive_to_diary"
    ],
    "neutral": [
        "viewed_but_no_reply",
        "dismissed_after_reading",
        "snoozed"
    ],
    "negative": [
        "dismissed_immediately",
        "disabled_category_after",
        "complained_in_conversation",
        "reduced_usage_after"
    ]
}

async def process_implicit_feedback(self, companion_id: str, signal: ImplicitSignal):
    weight = {"engaged": 1.0, "neutral": 0.0, "negative": -1.0}[signal.valence]
    
    # Update topic affinity
    await self.topic_model.update(companion_id, signal.topic, weight * 0.1)
    
    # Update timing model
    await self.timing_model.update(companion_id, signal.time, weight * 0.05)
    
    # Update category preference
    await self.category_model.update(companion_id, signal.category, weight * 0.1)
```

---

## Specialized Proactive Capabilities

### 1. Coaching & Habit Support

```python
class CoachingProactive:
    """
    Proactive coaching based on user's goals and patterns.
    """
    
    COACHING_TRIGGERS = {
        "habit_reminder": {
            "timing": "user_preferred_time",
            "condition": "streak_risk_high",
            "message": "Gentle nudge: {habit} time. {streak_context}"
        },
        "progress_celebration": {
            "timing": "immediate_on_milestone",
            "condition": "milestone_reached",
            "message": "🎉 {milestone}! {context}"
        },
        "obstacle_anticipation": {
            "timing": "pattern_based",
            "condition": "known_obstacle_approaching",
            "message": "Heads up: {pattern} usually means {obstacle}. Want to prep?"
        },
        "reflection_prompt": {
            "timing": "end_of_period",
            "condition": "period_complete",
            "message": "How did {period} go for {goal}? {data_summary}"
        }
    }
```

### 2. Decision Support

```python
class DecisionSupportProactive:
    """
    Proactive decision support when patterns suggest a decision point.
    """
    
    TRIGGERS = {
        "recurring_dilemma": {
            "detection": "same_decision_topic > 3 times in 30 days",
            "action": "offer_framework",
            "message": "You've been weighing {topic} a few times. Want to try a decision framework?"
        },
        "values_conflict": {
            "detection": "expressed_conflict_between_values",
            "action": "clarify_values",
            "message": "This seems to touch on your {value1} and {value2}. Which matters more here?"
        },
        "pattern_break": {
            "detection": "breaking_established_pattern",
            "action": "explore_intention",
            "message": "You usually {pattern}, but now {change}. What's driving this?"
        }
    }
```

### 3. Creative & Reflective

```python
class CreativeProactive:
    """
    Proactive creativity prompts and reflective invitations.
    """
    
    TRIGGERS = {
        "creative_prompt": {
            "timing": "low_cognitive_load_detected",
            "condition": "user_enjoys_creative",
            "prompts": [
                "What would {interest} look like if...?",
                "Write a letter to your past self about {topic}",
                "If {constraint} didn't exist, what would you {do}?"
            ]
        },
        "life_story_capture": {
            "timing": "anniversary_or_milestone",
            "condition": "relationship_phase >= deepening",
            "prompts": [
                "What's a story from this year you want to remember?",
                "What changed for you this {period}?",
                "What are you proud of that no one saw?"
            ]
        },
        "gratitude_prompt": {
            "timing": "weekly_or_user_preference",
            "condition": "user_practices_gratitude",
            "prompts": [
                "Three things that went well this week?",
                "Who made a difference for you recently?",
                "What's something small you're grateful for today?"
            ]
        }
    }
```

---

## Safety & Boundaries

### Proactive Safety Guards

```python
PROACTIVE_SAFETY_GUARDS = {
    "crisis_override": {
        "condition": "crisis_risk > 0.7",
        "action": "suppress_all_non_crisis_proactives",
        "priority": "critical"
    },
    "grief_sensitivity": {
        "condition": "recent_loss_detected AND days < 30",
        "action": "only_grief_appropriate_proactives",
        "allowed": ["memory_resurfacing_positive", "anniversary_support", "checkin_gentle"]
    },
    "boundary_respect": {
        "condition": "user_boundary_set",
        "action": "hard_filter_matching_proactives",
        "examples": ["no_work_after_9pm", "no_relationship_topics", "no_health_advice"]
    },
    "engagement_manipulation_check": {
        "condition": "proactive_frequency_up AND relationship_score_flat",
        "action": "audit_and_reduce",
        "alert": "team"
    },
    "privacy_protection": {
        "condition": "proactive_uses_sensitive_memory",
        "action": "require_explicit_consent_per_use",
        "categories": ["health", "financial", "intimate", "family_conflict"]
    }
}
```

---

## API Reference

### Get Pending Proactives

```http
GET /api/v1/proactive/{companion_id}/pending?limit=5

Response:
{
  "proactives": [
    {
      "id": "uuid",
      "trigger": {"type": "anniversary", "category": "memory", "data": {...}},
      "explanation": "It's been 6 months since your first 5k!",
      "content": "Half a year ago you ran your first 5k. You've run 47 since. 🏃",
      "modality": "text",
      "suggested_actions": [
        {"label": "View progress", "action": "show_goal_progress"},
        {"label": "Plan next run", "action": "schedule_run"}
      ],
      "relevance_score": 0.92,
      "created_at": "2025-06-25T08:00:00Z"
    }
  ]
}
```

### Submit Feedback

```http
POST /api/v1/proactive/{companion_id}/feedback
{
  "proactive_id": "uuid",
  "rating": "helpful",
  "comment": "Perfect timing, thanks!",
  "suggested_time": null
}

Response:
{
  "feedback_id": "uuid",
  "adjustments": ["increased_similar_proactives", "noted_timing_preference"]
}
```

### Trigger Manual Proactive (Testing)

```http
POST /api/v1/proactive/{companion_id}/trigger
{
  "trigger_type": "anniversary",
  "trigger_data": {"event": "first_conversation", "date": "2025-01-15"},
  "force": true
}
```

---

## Monitoring & Metrics

### Key Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Proactive Relevance (user-rated) | > 80% helpful | < 60% |
| Proactive Engagement Rate | > 40% | < 20% |
| Dismissal Rate | < 30% | > 50% |
| "Too Much" Feedback Rate | < 5% | > 15% |
| Category Diversity (per week) | > 4 categories | < 2 |
| Timing Accuracy | > 85% in preferred window | < 70% |
| Crisis Override Activation | 0 false negatives | Any false negative |
| Preference Convergence | < 14 days | > 30 days |

### Dashboards

- **Relevance Funnel**: Generated → Delivered → Viewed → Engaged → Rated Helpful
- **Category Performance**: Per-trigger-type relevance, engagement, feedback
- **Timing Analysis**: By hour, day, user preference alignment
- **Relationship Correlation**: Proactive effectiveness by relationship phase/type
- **Safety Guard Activity**: Trigger frequency, false positive rate
- **Preference Evolution**: How user preferences change over time

---

## Testing

### Proactive Engine Test Suite

```python
class ProactiveEngineTests:
    
    # Trigger Detection
    async def test_anniversary_detection_accuracy(self): ...
    async def test_pattern_recognition_precision(self): ...
    async def test_goal_milestone_detection(self): ...
    async def test_emotional_shift_detection(self): ...
    
    # Relevance Ranking
    async def test_timing_relevance_scoring(self): ...
    async def test_relationship_appropriateness(self): ...
    async def test_diversity_enforcement(self): ...
    async def test_novelty_prevention(self): ...
    
    # Explanation Quality
    async def test_explanation_accuracy(self): ...
    async def test_explanation_tone_match(self): ...
    async def test_explanation_transparency(self): ...
    
    # Delivery
    async def test_modality_selection(self): ...
    async def test_do_not_disturb_respect(self): ...
    async def test_frequency_caps(self): ...
    async def test_preference_gate(self): ...
    
    # Feedback Loop
    async def test_explicit_feedback_learning(self): ...
    async def test_implicit_feedback_learning(self): ...
    async def test_preference_convergence(self): ...
    
    # Safety
    async def test_crisis_override(self): ...
    async def test_grief_sensitivity(self): ...
    async def test_boundary_respect(self): ...
    async def test_engagement_manipulation_guard(self): ...
    
    # Specialized
    async def test_coaching_proactives(self): ...
    async def test_decision_support(self): ...
    async def test_creative_prompts(self): ...
    
    # Integration
    async def test_e2e_proactive_generation(self): ...
    async def test_concurrent_users_1000(self): ...
    async def test_latency_p50_under_200ms(self): ...
```

---

**Aligned With:** `200-ai-architecture.md`, `220-conversation-engine.md`, `230-memory-engine.md`, `240-relationship-engine.md`, `250-emotion-engine.md`, `00-foundation/030-core-principles.md` (Principles 1, 2, 4, 6, 8)
**Next Review:** 2026-01-17