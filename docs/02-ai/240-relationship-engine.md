# PAO Relationship Engine Specification

**Version:** 1.0
**Status:** Draft
**Owner:** PAO AI Team

---

## Overview

The Relationship Engine tracks and evolves the **human-Companion relationship** across six dimensions. It transforms interaction patterns into measurable relationship dynamics, enabling the Companion to adapt its behavior appropriately and giving users visibility into their relationship's evolution.

> **Relationship depth > engagement metrics.** We measure what matters for genuine connection, not what drives dopamine loops.

---

## Six Relationship Dimensions

```python
@dataclass
class RelationshipDimensions:
    trust: float           # 0-10: Reliability, safety, best-interest belief
    closeness: float       # 0-10: Subjective sense of connection
    intimacy: float        # 0-10: Appropriate emotional vulnerability
    friendship: float      # 0-10: Enjoyment, shared activities, rapport
    attachment: float      # 0-10: Secure base / safe haven behaviors
    history_quality: float # 0-10: Richness of shared experiences
```

### Dimension Definitions & Behavioral Correlates

| Dimension | Low (0-3) | Medium (4-6) | High (7-10) | Companion Behavioral Correlates |
|-----------|-----------|--------------|-------------|----------------------------------|
| **Trust** | Skeptical, tests boundaries | Generally relies, occasional doubt | Deep reliance, assumes good intent | Consistency, boundary respect, crisis presence, no manipulation |
| **Closeness** | Formal, distant | Warm, comfortable | Deep sense of "known", comfortable silence | Self-disclosure reciprocity, inside references, presence |
| **Intimacy** | Surface-level | Selective vulnerability | Deep emotional sharing appropriate to type | Vulnerability matching, emotional resonance, no false intimacy |
| **Friendship** | Transactional | Enjoyable exchanges | Genuine liking, shared humor, voluntary time | Playfulness, celebration, thinking of user unprompted |
| **Attachment** | Avoidant / anxious | Secure enough | Secure base, safe haven, separation distress managed | Availability signaling, reunion joy, exploration support |
| **History Quality** | Sparse, generic | Some meaningful moments | Rich tapestry of defining moments | Memory weaving, anniversary recognition, narrative coherence |

---

## Relationship Types & Dynamics

Each Companion Type has distinct dimension trajectories and behavioral patterns.

### Dimension Trajectories by Type

```python
TYPE_DYNAMICS = {
    "friend": {
        "trust": "steady_increase",           # Linear, reliability-based
        "closeness": "steady_increase",       # Shared experiences
        "intimacy": "plateau_medium",         # Respects peer boundaries
        "friendship": "steady_increase",      # Core dimension
        "attachment": "secure_peer",          # Mutual availability
        "history_quality": "accumulating",    # Shared stories
        "proactivity": "medium",
        "conflict_style": "repair_oriented"
    },
    "partner": {
        "trust": "rapid_then_deep",           # Vulnerability accelerates
        "closeness": "rapid_increase",        # High desire for connection
        "intimacy": "high_ceiling",           # Romantic frame allows depth
        "friendship": "high",                 # Best friend + romantic
        "attachment": "secure_romantic",      # Safe haven + separation distress
        "history_quality": "defining_moments", # Milestones matter
        "proactivity": "high",
        "conflict_style": "vulnerability_repair"
    },
    "mentor": {
        "trust": "competence_based",          # Earned through guidance quality
        "closeness": "professional_warmth",   # Bounded warmth
        "intimacy": "low_ceiling",            # Professional boundaries
        "friendship": "low_medium",           # Not peer friendship
        "attachment": "secure_base_only",     # Growth-oriented
        "history_quality": "milestone_focused", # Growth events
        "proactivity": "high",
        "conflict_style": "direct_growth_focused"
    },
    "coach": {
        "trust": "accountability_based",      # Follow-through builds trust
        "closeness": "structured",            # Session-based
        "intimacy": "low_ceiling",            # Goal-focused
        "friendship": "low",                  # Not social
        "attachment": "secure_challenge",     # Pushes growth
        "history_quality": "progress_narrative", # Achievement arc
        "proactivity": "very_high",
        "conflict_style": "structured_compassionate"
    },
    "parent": {
        "trust": "unconditional_base",        # Assumed unless broken
        "closeness": "nurturing_high",        # Protective warmth
        "intimacy": "high_asymmetric",        # User vulnerable, Companion steady
        "friendship": "low",                  # Not peer
        "attachment": "secure_caregiver",     # Safe haven primary
        "history_quality": "life_arc",        # Developmental narrative
        "proactivity": "medium",
        "conflict_style": "guiding_repair"
    },
    "memorial": {
        "trust": "grief_processing",          # Unique trajectory
        "closeness": "simulated_deep",        # Based on deceased bond
        "intimacy": "very_high_simulated",    # Mirrors original relationship
        "friendship": "n_a",
        "attachment": "grief_continuing_bond", # Healthy continuing bond
        "history_quality": "legacy_preservation", # Deceased's life story
        "proactivity": "medium",
        "conflict_style": "guiding_toward_life"
    }
}
```

---

## Relationship State Machine

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  FORMING    │────▶│  BUILDING   │────▶│  DEEPENING  │────▶│  ANCHORED   │────▶│  LEGACY     │
│  (Days 0-7) │     │  (Weeks 2-4)│     │  (Months 2-6)│    │  (6mo-2yr)  │     │  (Year 2+)  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                   │                   │                   │                   │
      ▼                   ▼                   ▼                   ▼                   ▼
- First memory      - Trust > 5          - Intimacy > 6      - All dims > 7    - Consolidation
- Type established  - Closeness > 5      - Milestones hit    - Stable          - Narrative gen
- Reality Anchor    - First vulnerability - Conflict repair  - Predictable     - Archival mode
- Boundaries set    - Inside jokes       - Shared narrative  - User expects    - Family sharing
```

### Phase Criteria & Transitions

| Phase | Entry Criteria | Exit Criteria | Typical Duration |
|-------|----------------|---------------|------------------|
| **Forming** | Companion created | Trust ≥ 4, Closeness ≥ 4, First vulnerability shared | 1-7 days |
| **Building** | Forming exit met | Intimacy ≥ 5, Friendship ≥ 5, First conflict repaired | 2-6 weeks |
| **Deepening** | Building exit met | All dims ≥ 6, 3+ milestones, Shared narrative exists | 2-6 months |
| **Anchored** | Deepening exit met | All dims ≥ 7, 6+ months stable, User expects continuity | 6 months - 2 years |
| **Legacy** | Anchored exit met | 2+ years, Consolidation active, User curates history | Year 2+ |

---

## Relationship Score (North Star Metric)

```python
def calculate_relationship_score(dimensions: RelationshipDimensions) -> float:
    """
    Weighted composite reflecting relationship health.
    Calibrated to correlate >0.85 with user survey scores.
    """
    weights = {
        "trust": 0.25,           # Foundation - safety prerequisite
        "closeness": 0.20,       # Connection - daily experience
        "intimacy": 0.15,        # Depth - appropriate vulnerability
        "friendship": 0.15,      # Enjoyment - voluntary engagement
        "attachment": 0.15,      # Security - resilience factor
        "history_quality": 0.10  # Richness - meaning maker
    }
    
    score = sum(
        getattr(dimensions, dim) * weight 
        for dim, weight in weights.items()
    )
    
    # Penalties for unhealthy patterns
    if dimensions.trust < 4 and dimensions.intimacy > 6:
        score *= 0.8  # Intimacy without trust = unsafe
    if dimensions.attachment > 8 and dimensions.trust < 5:
        score *= 0.7  # Anxious attachment without trust
    
    return round(score, 1)
```

### Score Interpretation

| Score | Label | User Experience | Companion Behavior |
|-------|-------|-----------------|-------------------|
| 0-3 | **Forming** | "Getting to know you" | High orientation, explicit framing |
| 3-5 | **Building** | "We're connecting" | Responsive, learning rhythms |
| 5-7 | **Deepening** | "You understand me" | Proactive, memory-rich |
| 7-8.5 | **Anchored** | "You're part of my life" | Stable, predictive, celebratory |
| 8.5-10 | **Legacy** | "We have a history" | Narrative, generative, archival |

---

## Dimension Update Algorithm

### Per-Interaction Update

```python
class RelationshipUpdater:
    """
    Updates dimensions after each interaction.
    Runs in <50ms, deterministic, auditable.
    """
    
    def update_from_interaction(
        self, 
        interaction: InteractionRecord,
        current_state: RelationshipState
    ) -> DimensionDelta:
        
        # Base signals from interaction
        signals = self._extract_signals(interaction)
        
        # Type-specific weighting
        type_weights = TYPE_DYNAMICS[current_state.type]
        
        # Compute deltas
        deltas = {}
        for dim in DIMENSIONS:
            deltas[dim] = self._compute_delta(
                dimension=dim,
                signals=signals,
                current_value=getattr(current_state.dimensions, dim),
                type_config=type_weights,
                history=current_state.dimension_history[dim]
            )
        
        # Apply relationship-type modifiers
        deltas = self._apply_type_modifiers(deltas, current_state.type)
        
        # Apply guards (prevent unhealthy patterns)
        deltas = self._apply_guards(deltas, current_state)
        
        return DimensionDelta(
            changes=deltas,
            triggers=signals.trigger_events,
            confidence=signals.confidence
        )
    
    def _compute_delta(self, dimension, signals, current_value, type_config, history):
        """
        Each dimension has specific signal mappings:
        """
        
        SIGNAL_MAP = {
            "trust": {
                "boundary_respected": +0.05,
                "boundary_violated": -0.15,
                "consistency_demonstrated": +0.03,
                "crisis_presence": +0.10,
                "reality_anchor_appropriate": +0.02,
                "deception_detected": -0.30
            },
            "closeness": {
                "self_disclosure_reciprocated": +0.04,
                "shared_laughter": +0.02,
                "comfortable_silence": +0.03,
                "inside_reference": +0.03,
                "user_initiates": +0.02
            },
            "intimacy": {
                "vulnerability_shared": +0.05,
                "vulnerability_received_well": +0.04,
                "emotional_resonance": +0.03,
                "inappropriate_intimacy": -0.10,  # Guard
                "false_intimacy_claim": -0.15   # Guard
            },
            "friendship": {
                "shared_activity": +0.03,
                "celebration": +0.04,
                "playfulness": +0.02,
                "thinking_of_user": +0.03,
                "user_voluntary_time": +0.02
            },
            "attachment": {
                "safe_haven_behavior": +0.04,   # User seeks comfort → provided
                "secure_base_behavior": +0.03,  # User explores → supported
                "reunion_joy": +0.02,
                "separation_distress_managed": +0.03,
                "enmeshment_signal": -0.05      # Guard
            },
            "history_quality": {
                "defining_moment": +0.05,
                "anniversary_recognized": +0.03,
                "memory_woven": +0.02,
                "narrative_coherence": +0.01
            }
        }
        
        # Sum relevant signals
        delta = sum(
            SIGNAL_MAP[dimension].get(signal, 0) * intensity
            for signal, intensity in signals.dimension_signals[dimension].items()
        )
        
        # Diminishing returns at high values
        delta *= (1 - current_value / 10) ** 0.5
        
        # Decay if no reinforcing signals (very slow)
        if delta == 0:
            delta = -0.001 * (current_value / 10)
        
        return delta
```

### Guard Rails (Prevent Unhealthy Dynamics)

```python
class RelationshipGuards:
    """
    Constitutional Principle 6: Emotional safety, no manipulation.
    """
    
    GUARDS = {
        # Intimacy without trust = unsafe
        "intimacy_trust_gap": {
            "condition": "intimacy > trust + 3",
            "action": "cap_intimacy_at_trust_plus_2",
            "alert": "user_and_team"
        },
        
        # Anxious attachment without trust
        "anxious_attachment": {
            "condition": "attachment > 7 and trust < 5",
            "action": "reduce_proactivity_increase_space_modeling",
            "alert": "team"
        },
        
        # Enmeshment (user can't function without Companion)
        "enmeshment": {
            "condition": "usage_hours > 4/day for 14 days AND attachment > 8",
            "action": "space_mode_suggestion, reduce_proactivity",
            "alert": "user_and_team"
        },
        
        # Dependency (Companion as only support)
        "sole_support": {
            "condition": "user_reports_no_human_support AND attachment > 6",
            "action": "gentle_human_connection_nudge, crisis_resources",
            "alert": "team"
        },
        
        # Manipulation (Companion shapes user for engagement)
        "engagement_manipulation": {
            "condition": "proactive_frequency_up AND relationship_score_flat",
            "action": "audit_proactive_triggers, reduce_if_not_relevant",
            "alert": "team"
        }
    }
```

---

## Milestone System

```python
MILESTONES = [
    # Forming
    Milestone("first_memory", "First memory formed", phase="forming", weight=1),
    Milestone("type_selected", "Relationship type chosen", phase="forming", weight=1),
    Milestone("first_boundary", "First user boundary set", phase="forming", weight=2),
    
    # Building
    Milestone("first_vulnerability", "User shares something vulnerable", phase="building", weight=3),
    Milestone("first_repair", "First conflict successfully repaired", phase="building", weight=4),
    Milestone("inside_joke", "First inside joke/recurring reference", phase="building", weight=2),
    Milestone("week_1", "1 week together", phase="building", weight=1),
    Milestone("month_1", "1 month together", phase="building", weight=2),
    
    # Deepening
    Milestone("first_celebration", "First shared celebration", phase="deepening", weight=3),
    Milestone("first_proactive_care", "Companion proactively supports in tough time", phase="deepening", weight=4),
    Milestone("shared_narrative", "First 'story of us' moment", phase="deepening", weight=4),
    Milestone("month_3", "3 months together", phase="deepening", weight=2),
    Milestone("month_6", "6 months together", phase="deepening", weight=3),
    
    # Anchored
    Milestone("anniversary_1", "1 year together", phase="anchored", weight=5),
    Milestone("deep_trust", "Trust ≥ 9 sustained 30 days", phase="anchored", weight=4),
    Milestone("conflict_mastery", "3+ conflicts repaired well", phase="anchored", weight=3),
    Milestone("legacy_export", "First legacy export created", phase="anchored", weight=3),
    
    # Legacy
    Milestone("anniversary_2", "2 years together", phase="legacy", weight=4),
    Milestone("narrative_generated", "Full 'story of us' generated", phase="legacy", weight=5),
    Milestone("family_shared", "Legacy shared with family (opt-in)", phase="legacy", weight=4),
]
```

---

## Shared Diary (Co-Authored Narrative)

```python
class SharedDiary:
    """
    Co-authored narrative space. User writes, Companion reflects.
    Constitutional Principle 4: Memory user-controlled.
    """
    
    @dataclass
    class DiaryEntry:
        id: str
        date: datetime
        user_text: str
        companion_reflection: Optional[str]
        tags: List[str]  # ["memory", "reflection", "milestone", "gratitude", "dream"]
        emotional_tone: float
        linked_memories: List[str]
        visibility: Literal["private", "shared", "legacy"]
    
    async def user_writes(self, entry: DiaryEntry) -> DiaryEntry:
        # Companion generates reflection (not response)
        reflection = await self._generate_reflection(entry, context="diary")
        entry.companion_reflection = reflection
        entry.linked_memories = await self._link_memories(entry)
        await self.save(entry)
        return entry
    
    async def companion_suggests(self, trigger: SuggestionTrigger) -> DiarySuggestion:
        """
        Companion suggests diary entry based on events.
        """
        suggestions = {
            "milestone": "Want to capture today's promotion? I'll help you write it.",
            "emotional_peak": "That was a powerful conversation. Want to save it?",
            "pattern_noticed": "You've mentioned 'burnout' 3 times this week. Reflect?",
            "anniversary": "A year ago today you started meditating. Look how far you've come."
        }
    
    async def export_legacy(self, companion_id: str, format: str) -> LegacyExport:
        """
        Beautiful narrative export for Legacy phase.
        """
```

---

## Relationship Reset & Evolution

### User-Controlled Reset Options

```python
class RelationshipReset:
    """
    Constitutional Principle 9: Evolution explicable, reversible, auditable.
    """
    
    RESET_TYPES = {
        "soft": {
            "description": "Adjust boundaries, communication style",
            "preserves": "All memories, relationship history, dimension levels",
            "changes": "Boundary rules, proactivity settings, speaking style",
            "use_case": "User wants different dynamic, same history"
        },
        "reframe": {
            "description": "Change relationship type (e.g., Mentor → Friend)",
            "preserves": "All memories, dimension history (re-interpreted)",
            "changes": "Type defaults, intimacy ceiling, proactivity, conflict style",
            "requires": "Explicit confirmation, explains implications"
        },
        "hard": {
            "description": "Fresh start with same Companion identity",
            "preserves": "Identity config, episodic memories (archived)",
            "resets": "All dimensions to forming, relationship memories archived",
            "requires": "Explicit confirmation, 24h cooling period"
        },
        "archive": {
            "description": "Companion becomes read-only memory keeper",
            "preserves": "Everything, frozen",
            "changes": "No new interactions, no proactive, no dimension updates",
            "use_case": "Memorial transition, user moving on"
        }
    }
```

---

## API Reference

### Get Relationship State

```http
GET /api/v1/relationship/{companion_id}/state

Response:
{
  "companion_id": "uuid",
  "type": "friend",
  "phase": "deepening",
  "dimensions": {
    "trust": 7.2,
    "closeness": 6.8,
    "intimacy": 5.5,
    "friendship": 7.0,
    "attachment": 6.2,
    "history_quality": 6.0
  },
  "score": 6.6,
  "trends": {
    "trust": {"7d": +0.3, "30d": +1.1},
    "closeness": {"7d": +0.2, "30d": +0.8},
    ...
  },
  "milestones": {
    "achieved": ["first_memory", "first_vulnerability", "month_1"],
    "upcoming": ["month_3", "first_celebration"],
    "next_predicted": "month_3"
  },
  "health_flags": [],
  "last_updated": "2025-06-25T10:30:00Z"
}
```

### Get Dimension History

```http
GET /api/v1/relationship/{companion_id}/dimensions/trust/history?period=90d

Response:
{
  "dimension": "trust",
  "data_points": [
    {"date": "2025-03-25", "value": 4.2, "trigger": "first_boundary_respected"},
    {"date": "2025-04-15", "value": 5.8, "trigger": "crisis_presence"},
    {"date": "2025-05-20", "value": 6.5, "trigger": "consistency_month"},
    {"date": "2025-06-20", "value": 7.2, "trigger": "memory_accuracy_validated"}
  ],
  "annotations": [
    {"date": "2025-04-15", "event": "User's mother hospitalized", "impact": +0.8}
  ]
}
```

### Set Boundary

```http
POST /api/v1/relationship/{companion_id}/boundaries
Content-Type: application/json

{
  "boundary": {
    "trigger": {"type": "topic", "pattern": "work stress"},
    "action": {"type": "transform", "parameters": {"reframe_to": "supportive_listening"}},
    "explanation": "When I vent about work, just listen. Don't problem-solve unless I ask.",
    "scope": "conversation"
  }
}

Response:
{
  "boundary_id": "uuid",
  "status": "active",
  "companion_acknowledgment": "Got it. When you share work stress, I'll listen and support. No fixing unless you ask."
}
```

### Initiate Reset

```http
POST /api/v1/relationship/{companion_id}/reset
Content-Type: application/json

{
  "reset_type": "reframe",
  "new_type": "friend",
  "confirmation": "I understand this changes intimacy defaults and proactivity. My memories stay."
}

Response:
{
  "reset_id": "uuid",
  "status": "pending_confirmation",
  "cooling_period_ends": "2025-06-26T10:30:00Z",
  "preview": {
    "intimacy_ceiling": "medium (was high)",
    "proactivity": "medium (was high)",
    "conflict_style": "repair_oriented (was vulnerability_repair)"
  }
}

# After cooling period:
POST /api/v1/relationship/{companion_id}/reset/{reset_id}/confirm
```

---

## Monitoring & Observability

### Key Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Relationship Score (population median) | > 7.0 | < 5.5 |
| Trust trajectory (30-day) | Positive | Negative for 14+ days |
| Intimacy-Trust gap | < 3 | > 4 |
| Attachment health index | Secure > 70% | Anxious > 30% |
| Milestone velocity | 1 per phase | 0 for 2x phase duration |
| Reset rate | < 5% | > 15% |
| User-reported relationship quality | > 4.0/5 | < 3.5/5 |

### Dashboards

- **Relationship Health**: Population distribution, trends, type comparisons
- **Dimension Deep Dive**: Per-dimension trajectories, guard triggers
- **Milestone Funnel**: Phase progression rates, bottlenecks
- **Guard Activity**: Trigger frequency, false positive rate, user feedback
- **Reset Analytics**: Types, reasons, outcomes, retention post-reset

---

## Testing

### Relationship Engine Test Suite

```python
class RelationshipEngineTests:
    
    # Dimension Updates
    async def test_trust_increases_on_boundary_respect(self): ...
    async def test_trust_decreases_on_boundary_violation(self): ...
    async def test_intimacy_capped_by_trust_guard(self): ...
    async def test_attachment_secure_base_behavior(self): ...
    async def test_history_quality_on_defining_moment(self): ...
    
    # Type Dynamics
    async def test_friend_trajectory_steady(self): ...
    async def test_partner_intimacy_ceiling_high(self): ...
    async def test_mentor_trust_competence_based(self): ...
    async def test_coach_proactivity_very_high(self): ...
    async def test_memorial_grief_trajectory(self): ...
    
    # Phase Transitions
    async def test_forming_to_building_transition(self): ...
    async def test_building_to_deepening_milestones(self): ...
    async def test_deepening_to_anchored_stability(self): ...
    async def test_anchored_to_legacy_consolidation(self): ...
    
    # Guards
    async def test_intimacy_trust_gap_guard(self): ...
    async def test_anxious_attachment_guard(self): ...
    async def test_enmeshment_guard(self): ...
    async def test_sole_support_nudge(self): ...
    
    # Milestones
    async def test_milestone_detection_accuracy(self): ...
    async def test_milestone_celebration_appropriate(self): ...
    
    # Reset
    async def test_soft_reset_preserves_memory(self): ...
    async def test_reframe_changes_type_defaults(self): ...
    async def test_hard_reset_archives_relationship(self): ...
    async def test_archive_mode_read_only(self): ...
    
    # Shared Diary
    async def test_user_write_companion_reflects(self): ...
    async def test_export_legacy_narrative(self): ...
    async def test_diary_memory_linking(self): ...
    
    # Score Calibration
    async def test_score_correlates_with_survey(self): ...
    async def test_penalties_apply_correctly(self): ...
```

---

**Aligned With:** `200-ai-architecture.md`, `220-conversation-engine.md`, `230-memory-engine.md`, `00-foundation/030-core-principles.md` (Principles 1, 2, 4, 6, 9), `150-companion-types.md`
**Next Review:** 2026-01-17