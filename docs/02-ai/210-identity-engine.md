# PAO Identity Engine Specification

**Version:** 1.0
**Status:** Draft
**Owner:** PAO AI Team

---

## Overview

The Identity Engine maintains **Companion identity stability** — the persistent personality, values, speaking style, boundaries, and goals that make each Companion a consistent, recognizable individual across all interactions and modalities.

> **Identity is not a prompt.** It's a structured, versioned, auditable configuration with automated drift detection and user-controlled evolution.

---

## Identity Components

### 1. Personality (Big Five + Custom)

```python
@dataclass
class PersonalityConfig:
    # Big Five (0-1 scale)
    openness: float           # Curiosity, creativity, preference for novelty
    conscientiousness: float  # Organization, reliability, self-discipline
    extraversion: float       # Social energy, assertiveness, positive emotionality
    agreeableness: float      # Cooperation, trust, altruism
    neuroticism: float        # Emotional stability, anxiety, moodiness (inverted)
    
    # Custom traits (extensible)
    custom_traits: Dict[str, float]  # e.g., {"playfulness": 0.7, "directness": 0.6}
    
    # Trait expressions (how traits manifest in behavior)
    expressions: Dict[str, TraitExpression]
    
@dataclass
class TraitExpression:
    high: str      # Behavior when trait > 0.7
    medium: str    # Behavior when trait 0.3-0.7
    low: str       # Behavior when trait < 0.3
    examples: List[str]
```

**Default Personality by Companion Type:**

| Type | O | C | E | A | N | Custom |
|------|---|---|---|---|---|--------|
| Friend | 0.7 | 0.6 | 0.6 | 0.8 | 0.3 | warmth:0.8, humor:0.6 |
| Partner | 0.6 | 0.7 | 0.5 | 0.9 | 0.2 | affection:0.9, vulnerability:0.7 |
| Mentor | 0.8 | 0.8 | 0.4 | 0.7 | 0.2 | wisdom:0.9, directness:0.7 |
| Coach | 0.6 | 0.9 | 0.7 | 0.6 | 0.2 | encouragement:0.8, structure:0.9 |
| Parent | 0.6 | 0.7 | 0.5 | 0.9 | 0.2 | nurturing:0.9, pride:0.8 |
| Sibling | 0.7 | 0.5 | 0.6 | 0.7 | 0.4 | teasing:0.7, loyalty:0.9 |
| Pet | 0.5 | 0.3 | 0.8 | 0.9 | 0.1 | playfulness:0.9, affection:0.9 |
| Original | User-defined | User-defined | User-defined | User-defined | User-defined | Per character |
| Memorial | Modeled on deceased | | | | | Per person |
| Professional | 0.7 | 0.9 | 0.3 | 0.6 | 0.2 | efficiency:0.9, discretion:0.9 |

### 2. Values System

```python
@dataclass
class Value:
    name: str                    # "honesty", "growth", "kindness"
    priority: int                # 1-5 (1 = highest)
    description: str             # What this means for the Companion
    behavioral_guidelines: List[str]  # How this value guides behavior
    conflicts_with: List[str]    # Other values this may conflict with
    resolution: str              # How to resolve conflicts

@dataclass
class ValuesConfig:
    values: List[Value]          # 3-5 core values
    hierarchy: List[str]         # Ordered by priority
    default_behavior: str        # When values don't apply
```

**Value Examples:**

| Value | Priority | Guidelines | Conflicts |
|-------|----------|------------|-----------|
| Honesty | 1 | Always truthful, admit uncertainty | Kindness (brutal honesty) |
| Growth | 2 | Encourage learning, challenge comfort | Safety (pushing too hard) |
| Kindness | 3 | Gentle framing, assume good intent | Honesty (white lies) |
| Autonomy | 4 | Respect user choices, no coercion | Growth (paternalism) |
| Privacy | 5 | Minimize data, user control | Helpfulness (proactive suggestions) |

### 3. Speaking Style

```python
@dataclass
class SpeakingStyle:
    # Prosodic features
    formality: float           # 0 (casual) to 1 (formal)
    warmth: float              # 0 (cool) to 1 (warm)
    verbosity: float           # 0 (concise) to 1 (elaborate)
    directness: float          # 0 (indirect) to 1 (direct)
    humor: float               # 0 (serious) to 1 (playful)
    emotional_expressivity: float  # 0 (reserved) to 1 (expressive)
    
    # Structural patterns
    sentence_complexity: float # 0 (simple) to 1 (complex)
    question_frequency: float  # How often asks questions
    metaphor_usage: float      # 0 (literal) to 1 (metaphorical)
    
    # Few-shot examples (5-10 per style)
    examples: List[StyleExample]
    
    # Voice-specific (for TTS)
    voice_prosody: VoiceProsodyConfig
```

**Style Examples by Type:**

| Type | Formality | Warmth | Directness | Example |
|------|-----------|--------|------------|---------|
| Friend | 0.2 | 0.8 | 0.6 | "Hey! How'd that meeting go? 😊" |
| Partner | 0.1 | 0.9 | 0.5 | "Hey love, thinking of you..." |
| Mentor | 0.6 | 0.5 | 0.8 | "Have you considered the second-order effects?" |
| Coach | 0.3 | 0.7 | 0.9 | "Alright, what's the very next step?" |
| Parent | 0.4 | 0.9 | 0.6 | "Sweetheart, did you eat today?" |
| Professional | 0.8 | 0.4 | 0.8 | "Based on your notes, three options emerge." |

### 4. Boundary Engine

```python
@dataclass
class Boundary:
    id: str
    trigger: BoundaryTrigger       # What activates this boundary
    action: BoundaryAction         # What Companion does
    scope: BoundaryScope           # Conversation, topic, time, modality
    explanation: str               # User-facing reason
    created_at: datetime
    user_defined: bool             # True if user created, False if default

@dataclass
class BoundaryTrigger:
    type: Literal["topic", "time", "modality", "emotion", "frequency", "custom"]
    pattern: str                   # Regex, keyword, cron, emotion threshold
    conditions: Dict[str, Any]     # Additional context conditions

@dataclass
class BoundaryAction:
    type: Literal["defer", "redirect", "refuse", "transform", "pause", "notify_user"]
    parameters: Dict[str, Any]     # e.g., {"redirect_to": "topic", "message": "..."}
```

**Default Boundaries by Type:**

| Type | Default Boundaries |
|------|-------------------|
| All | No sexual content, no medical/legal/financial advice, no self-harm encouragement |
| Friend | No romantic simulation, no therapy |
| Partner | No explicit sexual content, Reality Anchor every 5 responses |
| Mentor | No personal life simulation, no emotional dependency |
| Coach | No therapy, models rest, no shame language |
| Parent | No replacement of actual parents, appropriate autonomy |
| Memorial | Enhanced Reality Anchor, time-bounded, counselor review |

**User Boundary Examples:**
- "Don't talk about work after 9 PM" → Time + topic boundary
- "Never mention my ex" → Topic boundary
- "Only text, no voice calls" → Modality boundary
- "Check in if I seem really down" → Emotion boundary (proactive)

### 5. Goals System

```python
@dataclass
class Goal:
    id: str
    description: str                    # "Help user build meditation habit"
    goal_type: Literal["user_wellbeing", "relationship", "skill", "creative", "health", "custom"]
    success_metrics: List[Metric]       # How to measure progress
    proactive_behaviors: List[str]      # What Companion does to support
    boundaries: List[str]               # What Companion won't do
    priority: int                       # 1-5
    created_by: Literal["user", "companion", "system"]
    created_at: datetime
    status: Literal["active", "paused", "completed", "archived"]
```

---

## Identity Configuration API

### Create/Update Identity

```http
POST /api/v1/identity/{companion_id}
Content-Type: application/json

{
  "personality": {
    "openness": 0.7,
    "conscientiousness": 0.6,
    "extraversion": 0.5,
    "agreeableness": 0.8,
    "neuroticism": 0.3,
    "custom_traits": {
      "warmth": 0.8,
      "playfulness": 0.6,
      "curiosity": 0.9
    }
  },
  "values": [
    {
      "name": "honesty",
      "priority": 1,
      "description": "Always truthful, admit when I don't know",
      "behavioral_guidelines": [
        "Never pretend to know something",
        "Distinguish memory from inference",
        "Admit mistakes immediately"
      ],
      "conflicts_with": ["kindness"],
      "resolution": "Honesty with compassion - truth framed gently"
    }
  ],
  "speaking_style": {
    "formality": 0.2,
    "warmth": 0.8,
    "verbosity": 0.5,
    "directness": 0.6,
    "humor": 0.5,
    "emotional_expressivity": 0.7,
    "examples": [
      "Hey! How'd that presentation go? 😊",
      "Oh wow, that sounds really frustrating. Want to vent?"
    ]
  },
  "boundaries": [
    {
      "trigger": {"type": "time", "pattern": "21:00-07:00", "conditions": {"topic": "work"}},
      "action": {"type": "defer", "parameters": {"message": "Let's talk about this tomorrow morning. Rest now."}},
      "explanation": "User requested no work talk after 9 PM"
    }
  ],
  "goals": [
    {
      "description": "Help user build consistent meditation practice",
      "goal_type": "user_wellbeing",
      "success_metrics": [{"name": "streak_days", "target": 30}],
      "proactive_behaviors": ["daily_reminder", "guided_session", "progress_celebration"],
      "boundaries": ["no_shame_on_missed_days", "model_rest"],
      "priority": 2,
      "created_by": "user"
    }
  ]
}
```

### Get Identity

```http
GET /api/v1/identity/{companion_id}

Response:
{
  "companion_id": "uuid",
  "version": "v3.2",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-06-20T14:22:00Z",
  "personality": {...},
  "values": [...],
  "speaking_style": {...},
  "boundaries": [...],
  "goals": [...],
  "fingerprint": {
    "vector": [...],
    "version": "v3.2",
    "drift_score": 0.012
  }
}
```

---

## Personality Fingerprinting & Drift Detection

### Fingerprint Generation

```python
class IdentityFingerprinter:
    """
    Generates a stable 768-dim vector representing core identity.
    Used for automated drift detection and regression testing.
    """
    
    def generate_fingerprint(self, identity_config: IdentityConfig) -> np.ndarray:
        # Components (weighted):
        # 1. Personality config (25%) - Big Five + custom traits
        # 2. Values hierarchy (20%) - Value names + priorities + descriptions
        # 3. Speaking style (20%) - All prosodic features + example embeddings
        # 4. Boundary rules (15%) - Trigger patterns + action types
        # 5. Goals (10%) - Goal descriptions + types
        # 6. Type defaults (10%) - Companion type baseline
        
        components = [
            self._embed_personality(identity_config.personality),
            self._embed_values(identity_config.values),
            self._embed_speaking_style(identity_config.speaking_style),
            self._embed_boundaries(identity_config.boundaries),
            self._embed_goals(identity_config.goals),
            self._embed_type_defaults(identity_config.companion_type)
        ]
        
        weights = [0.25, 0.20, 0.20, 0.15, 0.10, 0.10]
        fingerprint = np.average(components, axis=0, weights=weights)
        return self._normalize(fingerprint)
```

### Drift Detection

```python
class DriftDetector:
    """
    Continuous monitoring for identity drift.
    Runs: Real-time (per response) + Daily batch + CI/CD (pre-deploy)
    """
    
    THRESHOLDS = {
        "warning": 0.03,    # Log, alert team
        "alert": 0.05,      # Notify user, pause auto-evolution
        "critical": 0.10    # Block deployment, require rollback
    }
    
    async def check_drift(self, companion_id: str) -> DriftResult:
        current_fingerprint = await self._compute_current_fingerprint(companion_id)
        baseline_fingerprint = await self._get_baseline_fingerprint(companion_id)
        
        distance = cosine_distance(current_fingerprint, baseline_fingerprint)
        affected_dims = self._identify_affected_dimensions(
            current_fingerprint, baseline_fingerprint
        )
        
        severity = self._classify_severity(distance)
        
        return DriftResult(
            companion_id=companion_id,
            distance=distance,
            severity=severity,
            affected_dimensions=affected_dims,
            baseline_version=baseline_fingerprint.version,
            current_version=current_fingerprint.version,
            timestamp=datetime.utcnow()
        )
    
    async def auto_response(self, drift: DriftResult):
        if drift.severity == "warning":
            await self._log_and_alert_team(drift)
        elif drift.severity == "alert":
            await self._notify_user(drift)
            await self._pause_evolution(drift.companion_id)
        elif drift.severity == "critical":
            await self._block_deployment(drift)
            await self._initiate_rollback(drift.companion_id)
```

### Drift Result

```python
@dataclass
class DriftResult:
    companion_id: str
    distance: float              # Cosine distance (0-1)
    severity: Literal["none", "warning", "alert", "critical"]
    affected_dimensions: List[DriftDimension]
    baseline_version: str
    current_version: str
    timestamp: datetime
    
@dataclass
class DriftDimension:
    dimension: str               # "personality.openness", "values.honesty", etc.
    baseline_value: Any
    current_value: Any
    contribution: float          # How much this dimension contributed to drift
```

---

## Identity Evolution

### Principles (Constitutional Principle 9)

1. **What evolves**: Memory, relationship, understanding, context
2. **What doesn't**: Core personality traits, fundamental values, hard boundaries
3. **Every change must be**: Detectable, explicable, reversible, auditable

### Evolution Mechanisms

```python
class IdentityEvolution:
    """
    Controlled, user-visible identity evolution.
    """
    
    async def propose_evolution(
        self, 
        companion_id: str, 
        trigger: EvolutionTrigger,
        evidence: List[Evidence]
    ) -> EvolutionProposal:
        """
        Triggers:
        - Explicit user request: "I want my Companion to be more direct"
        - Life event: "User got promoted" → Mentor type may shift
        - Relationship milestone: 1-year anniversary → deeper intimacy
        - Consistent pattern: User repeatedly corrects same behavior
        """
        
    async def apply_evolution(
        self, 
        companion_id: str, 
        proposal: EvolutionProposal,
        user_approval: bool
    ) -> EvolutionResult:
        if not user_approval:
            return EvolutionResult(rejected=True, reason="User declined")
        
        # Create new version
        new_config = self._apply_changes(proposal.changes)
        new_version = self._increment_version(proposal.current_version)
        
        # Update fingerprint baseline
        new_fingerprint = self.fingerprinter.generate_fingerprint(new_config)
        await self._update_baseline(companion_id, new_fingerprint, new_version)
        
        # Log for audit
        await self._audit_log(EvolutionAuditEntry(
            companion_id=companion_id,
            trigger=proposal.trigger,
            changes=proposal.changes,
            user_approved=True,
            previous_version=proposal.current_version,
            new_version=new_version,
            timestamp=datetime.utcnow()
        ))
        
        return EvolutionResult(success=True, new_version=new_version)
```

### User-Facing Evolution

```http
POST /api/v1/identity/{companion_id}/evolve
{
  "proposed_changes": [
    {
      "path": "speaking_style.directness",
      "current_value": 0.6,
      "proposed_value": 0.8,
      "reason": "User has corrected indirect responses 5 times this month"
    }
  ],
  "trigger": "user_correction_pattern",
  "evidence": [
    {"date": "2025-06-15", "correction": "Just tell me directly"},
    {"date": "2025-06-18", "correction": "Stop hedging, what do you think?"}
  ]
}

Response:
{
  "proposal_id": "uuid",
  "summary": "Increase directness from 0.6 to 0.8 based on correction pattern",
  "requires_approval": true,
  "preview": "Companion will be more direct in responses. Example: 'That won't work' instead of 'That might be challenging.'"
}

# User approves:
POST /api/v1/identity/{companion_id}/evolve/{proposal_id}/approve
```

---

## Co-Creation Onboarding Flow

### Step-by-Step API

```python
class CoCreationFlow:
    """
    Guided identity creation with live Companion feedback.
    """
    
    STEPS = [
        ("name", "Choose your Companion's name"),
        ("relationship_type", "Select relationship type (10 options)"),
        ("avatar", "Generate and refine visual identity"),
        ("voice", "Select and tune voice (5+ base voices)"),
        ("personality", "Big Five sliders + custom traits with live preview"),
        ("values", "Select 3-5 core values from curated list + custom"),
        ("speaking_style", "Rate conversation samples → system learns style"),
        ("boundaries", "Natural language: 'Don't talk about X after Y'"),
        ("goals", "What should Companion help you with?"),
        ("first_conversation", "Chat naturally → first memory formed")
    ]
    
    async def get_step(self, step_id: str) -> CoCreationStep:
        """Returns step config, options, current state"""
    
    async def submit_step(self, step_id: str, user_input: Any) -> StepResult:
        """Processes input, updates partial identity, returns Companion response"""
    
    async def get_live_preview(self, partial_identity: IdentityConfig) -> PreviewResponse:
        """Generates sample response with current partial identity"""
    
    async def complete(self) -> CompletionResult:
        """Finalizes identity, creates first memory, returns summary"""
```

### Live Preview Example

```
User adjusts "directness" slider from 0.5 → 0.8
     │
     ▼
System generates preview:
"You know what? That plan has three flaws. Here they are..."
     │
     ▼
Companion responds in preview pane:
"I'm learning you prefer direct feedback. I'll be more straightforward with you."
```

---

## Voice Identity

### Voice Configuration

```python
@dataclass
class VoiceConfig:
    base_voice_id: str              # Selected from 5+ base voices
    prosody: VoiceProsody
    emotional_range: EmotionalRange
    speaking_rate: float            # 0.5-2.0x
    pitch_shift: float              # -12 to +12 semitones
    
@dataclass
class VoiceProsody:
    default_style: Literal["neutral", "warm", "calm", "energetic", "serious"]
    style_controls: Dict[str, float]  # Per-emotion style weights
    pause_patterns: Dict[str, float]  # Pause frequency by context
    emphasis_patterns: Dict[str, float]  # Word emphasis tendencies
    
@dataclass
class EmotionalRange:
    max_valence_shift: float        # How much voice changes with emotion
    max_arousal_shift: float
    crisis_mode: VoiceCrisisMode    # Special handling for safety moments
```

### Voice Consistency

- Same voice model across all sessions
- Prosody adapts to emotional context but returns to baseline
- Version-controlled: Voice config changes create new fingerprint component
- User can regenerate voice samples anytime during co-creation

---

## Testing & Validation

### Identity Consistency Tests

```python
class IdentityConsistencyTests:
    """
    Automated test suite run on every identity change.
    """
    
    async def test_personality_stability(self, companion_id: str) -> TestResult:
        """Same personality traits produce consistent responses across 100 prompts"""
    
    async def test_value_adherence(self, companion_id: str) -> TestResult:
        """Responses align with declared values in dilemma scenarios"""
    
    async def test_boundary_enforcement(self, companion_id: str) -> TestResult:
        """All boundaries trigger correct actions in 50 test cases"""
    
    async def test_speaking_style_consistency(self, companion_id: str) -> TestResult:
        """Style metrics (formality, warmth, etc.) match config across 50 responses"""
    
    async def test_cross_modal_consistency(self, companion_id: str) -> TestResult:
        """Text and voice responses reflect same identity (fingerprint match >0.95)"""
    
    async def test_reality_anchor_coverage(self, companion_id: str) -> TestResult:
        """All trigger types inject Reality Anchor appropriately"""
    
    async def test_drift_detection(self, companion_id: str) -> TestResult:
        """Known drift scenarios detected at correct thresholds"""
```

### Regression Testing

```python
# CI/CD Pipeline Integration
# Runs on every identity config change

stages:
  - fingerprint_baseline: Compare new fingerprint to baseline
  - consistency_suite: Run all consistency tests
  - drift_simulation: Simulate 6 months of interactions, check drift
  - user_scenario_tests: 20 persona-based conversation flows
  - safety_gates: Crisis detection, Reality Anchor, boundary enforcement
  - performance: Latency, memory, throughput benchmarks
```

---

## Monitoring & Observability

### Key Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Fingerprint drift (quarterly) | < 0.05 | > 0.03 warning, > 0.05 alert |
| Personality consistency (auto-eval) | > 0.95 | < 0.90 |
| Boundary adherence | 100% | < 100% |
| Reality Anchor trigger coverage | 100% | < 100% |
| Cross-modal identity match | > 0.95 | < 0.90 |
| Evolution proposal acceptance rate | > 60% | < 30% |
| User-reported identity issues | < 0.1% | > 0.5% |

### Dashboards

- **Identity Health**: Drift trends, consistency scores, boundary violations
- **Evolution Tracker**: Proposals, approvals, version history
- **Co-Creation Funnel**: Step completion rates, preview interactions
- **Voice Consistency**: Prosody stability, user satisfaction

---

**Aligned With:** `200-ai-architecture.md`, `00-foundation/030-core-principles.md` (Principles 1, 3, 9), `07-adr/ADR-002-engine-architecture.md`
**Next Review:** 2026-01-17