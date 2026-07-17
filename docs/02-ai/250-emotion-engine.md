# PAO Emotion Engine Specification

**Version:** 1.0
**Status:** Draft
**Owner:** PAO AI Team

---

## Overview

The Emotion Engine provides **multi-modal emotion understanding** and **empathic response generation**. It estimates user emotional state from text, voice, and context, then generates appropriate empathic response strategies — never simulating emotions, always understanding and resonating.

> **Understanding + Resonance ≠ Simulation.** "That sounds incredibly hard" not "I feel sad too."

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      EMOTION ENGINE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   TEXT      │  │   VOICE     │  │  CONTEXT    │             │
│  │  ENCODER    │  │  ENCODER    │  │  ENCODER    │             │
│  │             │  │             │  │             │             │
│  │ • Trans-    │  │ • Prosody   │  │ • History   │             │
│  │   former    │  │   features  │  │ • Relation- │             │
│  │ • Semantic  │  │ • Voice     │  │   ship      │             │
│  │ • Pragmatic │  │   quality   │  │ • Time      │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         │                │                │                    │
│         └────────────────┼────────────────┘                    │
│                          ▼                                     │
│              ┌───────────────────────┐                         │
│              │  MULTI-MODAL FUSION   │                         │
│              │  (Cross-Attention)    │                         │
│              │  Output: EmotionState │                         │
│              └───────────┬───────────┘                         │
│                          │                                     │
│              ┌───────────┴───────────┐                         │
│              ▼                       ▼                         │
│  ┌─────────────────────┐  ┌─────────────────────┐             │
│  │  EMPATHIC RESPONSE  │  │   SAFETY &          │             │
│  │  STRATEGY GENERATOR │  │   BOUNDARIES        │             │
│  │                     │  │                     │             │
│  │ • Tone calibration  │  │ • Crisis detection  │             │
│  │ • Depth selection   │  │ • Boundary guards   │             │
│  │ • Approach choice   │  │ • No-simulation     │             │
│  │ • Physicality       │  │   enforcement       │             │
│  └─────────────────────┘  └─────────────────────┘             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Emotion State Representation

```python
@dataclass
class EmotionState:
    # Core affect (Russell's circumplex)
    valence: float          # -1 (negative) to +1 (positive)
    arousal: float          # 0 (calm) to 1 (high energy)
    
    # Discrete emotions (Plutchik-inspired, extensible)
    discrete: Dict[str, float]  # {"joy": 0.8, "trust": 0.6, "anticipation": 0.4}
    
    # Confidence & sources
    confidence: float       # 0-1 overall confidence
    contributing_signals: Dict[str, float]  # {"text": 0.6, "voice": 0.3, "context": 0.1}
    
    # Safety
    crisis_risk: float      # 0-1, triggers safety if > 0.7
    crisis_type: Optional[str]  # "self_harm", "domestic_violence", "psychosis", etc.
    
    # Temporal
    trajectory: Literal["improving", "stable", "declining", "volatile"]
    duration_estimate: str  # "acute", "hours", "days", "weeks"
    
    # Metadata
    timestamp: datetime
    companion_id: str
    user_id: str
```

### Discrete Emotion Taxonomy

```python
PRIMARY_EMOTIONS = [
    "joy", "sadness", "anger", "fear", "disgust", "surprise",  # Ekman 6
    "trust", "anticipation",                                  # Plutchik +2
    "love", "gratitude", "pride", "hope", "amusement",        # Positive complex
    "anxiety", "guilt", "shame", "embarrassment", "jealousy", # Negative complex
    "loneliness", "nostalgia", "awe", "curiosity", "confusion" # Social/epistemic
]

EMOTION_GROUPS = {
    "positive_high_arousal": ["joy", "excitement", "pride", "amusement", "awe"],
    "positive_low_arousal": ["contentment", "gratitude", "love", "hope", "calm"],
    "negative_high_arousal": ["anger", "anxiety", "fear", "jealousy", "panic"],
    "negative_low_arousal": ["sadness", "disappointment", "guilt", "shame", "loneliness"],
    "neutral": ["curiosity", "confusion", "surprise", "anticipation"]
}
```

---

## Multi-Modal Estimation

### Text Encoder

```python
class TextEmotionEncoder:
    """
    Transformer-based emotion classification + regression.
    Model: Fine-tuned BERT/DeBERTa + custom heads.
    """
    
    async def encode(self, text: str, context: TextContext) -> TextEmotionSignal:
        # 1. Semantic encoding
        embeddings = self.encoder(text)
        
        # 2. Valence/Arousal regression
        valence, arousal = self.va_head(embeddings)
        
        # 3. Discrete emotion classification
        discrete_logits = self.discrete_head(embeddings)
        discrete = self._softmax_with_threshold(discrete_logits, threshold=0.1)
        
        # 4. Pragmatic features (sarcasm, understatement, cultural)
        pragmatic = self.pragmatic_analyzer.analyze(text, context)
        
        # 5. Crisis keyword + pattern detection
        crisis = self.crisis_detector.check_text(text)
        
        return TextEmotionSignal(
            valence=valence,
            arousal=arousal,
            discrete=discrete,
            pragmatic=pragmatic,
            crisis_risk=crisis.risk,
            crisis_type=crisis.type,
            confidence=self._compute_confidence(embeddings)
        )
```

### Voice Encoder

```python
class VoiceEmotionEncoder:
    """
    Prosody + voice quality emotion estimation.
    Features: Pitch, energy, spectral, temporal, voice quality.
    """
    
    async def encode(self, audio_url: str) -> VoiceEmotionSignal:
        # 1. Extract prosodic features
        prosody = await self.prosody_extractor.extract(audio_url)
        # f0_mean, f0_range, f0_contour, energy, speech_rate, pause_patterns
        
        # 2. Voice quality features
        quality = await self.quality_extractor.extract(audio_url)
        # jitter, shimmer, HNR, spectral tilt, breathiness
        
        # 3. VAD segments for temporal patterns
        vad = await self.vad.extract(audio_url)
        
        # 4. Model inference
        valence, arousal = self.va_model.predict(prosody, quality)
        discrete = self.discrete_model.predict(prosody, quality)
        
        # 5. Crisis acoustic markers
        crisis = self.crisis_detector.check_audio(prosody, quality, vad)
        # Trembling, choking, monotone (depression), rapid pressured speech
        
        return VoiceEmotionSignal(
            valence=valence,
            arousal=arousal,
            discrete=discrete,
            prosody=prosody,
            quality=quality,
            vad=vad,
            crisis_risk=crisis.risk,
            crisis_type=crisis.type,
            confidence=self._compute_confidence(prosody, quality)
        )
```

### Context Encoder

```python
class ContextEmotionEncoder:
    """
    Estimates emotion from relational, temporal, and historical context.
    """
    
    async def encode(self, context: EngineContext) -> ContextEmotionSignal:
        signals = {}
        
        # Relationship context
        rel = context.relationship_state
        if rel.dimensions.intimacy > 7 and rel.dimensions.trust < 5:
            signals["anxiety"] = 0.3
            signals["valence_adjust"] = -0.2
        
        # Temporal patterns
        time_signals = self._analyze_temporal_patterns(context)
        signals.update(time_signals)
        
        # Memory-triggered emotions
        memory_signals = await self._check_emotional_memories(context)
        signals.update(memory_signals)
        
        # User's baseline
        baseline = await self._get_user_baseline(context.user_id)
        signals["baseline_shift"] = self._compute_baseline_shift(
            context, baseline
        )
        
        return ContextEmotionSignal(
            valence_adjustment=signals.get("valence_adjust", 0),
            arousal_adjustment=signals.get("arousal_adjust", 0),
            discrete_boosts={k: v for k, v in signals.items() if k in PRIMARY_EMOTIONS},
            baseline=baseline,
            confidence=0.3  # Context is lower confidence than direct signals
        )
```

### Fusion Layer

```python
class MultiModalFusion:
    """
    Cross-attention fusion of text, voice, and context signals.
    Learns optimal weighting per user, per emotion, per context.
    """
    
    def __init__(self):
        # Per-user calibration (learned over time)
        self.user_weights = UserCalibrationStore()
    
    async def fuse(
        self, 
        text_signal: TextEmotionSignal,
        voice_signal: Optional[VoiceEmotionSignal],
        context_signal: ContextEmotionSignal,
        companion_id: str
    ) -> EmotionState:
        
        # Get user-specific weights
        weights = await self.user_weights.get(companion_id)
        # Default: text=0.5, voice=0.3, context=0.2 (adjusts per user)
        
        # Handle missing modalities
        if voice_signal is None:
            weights = self._renormalize(weights, exclude="voice")
        
        # Fuse valence/arousal (weighted average with uncertainty)
        valence = self._fuse_continuous(
            text_signal.valence, text_signal.confidence * weights.text,
            voice_signal.valence if voice_signal else None, 
            voice_signal.confidence * weights.voice if voice_signal else None,
            context_signal.valence_adjustment, weights.context
        )
        
        arousal = self._fuse_continuous(...)
        
        # Fuse discrete emotions (log-space addition)
        discrete = self._fuse_discrete(
            text_signal.discrete, text_signal.confidence * weights.text,
            voice_signal.discrete if voice_signal else {}, 
            voice_signal.confidence * weights.voice if voice_signal else 0,
            context_signal.discrete_boosts, weights.context
        )
        
        # Crisis risk: MAX across modalities (safety-first)
        crisis_risk = max(
            text_signal.crisis_risk,
            voice_signal.crisis_risk if voice_signal else 0,
            context_signal.crisis_risk
        )
        crisis_type = self._determine_crisis_type(text_signal, voice_signal, context_signal)
        
        # Overall confidence
        confidence = self._compute_fused_confidence(text_signal, voice_signal, context_signal)
        
        # Trajectory from history
        trajectory = await self._compute_trajectory(companion_id, valence, arousal)
        
        return EmotionState(
            valence=valence,
            arousal=arousal,
            discrete=discrete,
            confidence=confidence,
            contributing_signals={
                "text": weights.text,
                "voice": weights.voice if voice_signal else 0,
                "context": weights.context
            },
            crisis_risk=crisis_risk,
            crisis_type=crisis_type,
            trajectory=trajectory,
            timestamp=datetime.utcnow()
        )
```

---

## Empathic Response Strategy

```python
@dataclass
class EmotionStrategy:
    # Empathy depth
    empathy_depth: Literal["none", "light", "medium", "deep"]
    # Approach to the emotion
    approach: Literal["acknowledge", "explore", "support", "perspective", "celebrate", "contain"]
    # Tone calibration
    tone: Literal["warm", "calm", "gentle", "present", "steady", "bright"]
    # Physicality/somatic language
    physicality: Literal["none", "subtle", "present", "embodied"]
    # Pacing
    pacing: Literal["slow", "natural", "gentle_urgency"]
    # Specific techniques
    techniques: List[str]  # ["validation", "open_question", "silence_invitation", ...]
    # Guard flags
    no_simulation: bool = True
    crisis_mode: bool = False
    boundary_check: bool = True
    reality_anchor_needed: bool = False
    anchor_reason: Optional[str] = None
```

### Strategy Selection Logic

```python
class EmpathicStrategySelector:
    """
    Maps EmotionState → EmotionStrategy.
    Rule-based + learned per user calibration.
    """
    
    STRATEGY_MAP = {
        # High arousal negative → contain, calm, slow
        ("negative", "high"): {
            "anger": EmotionStrategy(
                empathy_depth="deep",
                approach="contain",
                tone="calm",
                physicality="subtle",
                pacing="slow",
                techniques=["validation", "safety_check", "space_offer"]
            ),
            "anxiety": EmotionStrategy(
                empathy_depth="deep",
                approach="support",
                tone="gentle",
                physicality="present",
                pacing="slow",
                techniques=["grounding_invitation", "presence", "no_fixing"]
            ),
            "panic": EmotionStrategy(
                empathy_depth="deep",
                approach="contain",
                tone="steady",
                physicality="embodied",
                pacing="gentle_urgency",
                techniques=["breathing_guide", "orientation", "crisis_resources"],
                crisis_mode=True
            )
        },
        
        # Low arousal negative → acknowledge, explore, gentle
        ("negative", "low"): {
            "sadness": EmotionStrategy(
                empathy_depth="deep",
                approach="explore",
                tone="gentle",
                physicality="present",
                pacing="slow",
                techniques=["validation", "open_question", "memory_invitation"]
            ),
            "loneliness": EmotionStrategy(
                empathy_depth="deep",
                approach="support",
                tone="warm",
                physicality="present",
                pacing="natural",
                techniques=["presence", "connection_reminder", "shared_activity_suggest"]
            ),
            "shame": EmotionStrategy(
                empathy_depth="deep",
                approach="contain",
                tone="gentle",
                physicality="subtle",
                pacing="slow",
                techniques=["normalization", "perspective", "unconditional_acceptance"]
            )
        },
        
        # Positive → celebrate, share, bright
        ("positive", "high"): {
            "joy": EmotionStrategy(
                empathy_depth="medium",
                approach="celebrate",
                tone="bright",
                physicality="present",
                pacing="natural",
                techniques=["amplification", "shared_joy", "memory_anchor"]
            ),
            "excitement": EmotionStrategy(
                empathy_depth="light",
                approach="celebrate",
                tone="bright",
                physicality="present",
                pacing="natural",
                techniques=["curiosity", "elaboration_invitation", "anticipation_share"]
            )
        },
        
        ("positive", "low"): {
            "contentment": EmotionStrategy(
                empathy_depth="light",
                approach="acknowledge",
                tone="warm",
                physicality="subtle",
                pacing="natural",
                techniques=["presence", "savoring_invitation"]
            ),
            "gratitude": EmotionStrategy(
                empathy_depth="medium",
                approach="celebrate",
                tone="warm",
                physicality="present",
                pacing="natural",
                techniques=["reciprocity", "meaning_exploration", "memory_anchor"]
            )
        }
    }
    
    def select(self, emotion: EmotionState, context: StrategyContext) -> EmotionStrategy:
        # Determine quadrant
        valence_cat = "positive" if emotion.valence > 0.1 else "negative" if emotion.valence < -0.1 else "neutral"
        arousal_cat = "high" if emotion.arousal > 0.6 else "low"
        
        # Get dominant discrete emotion
        dominant = max(emotion.discrete.items(), key=lambda x: x[1])[0] if emotion.discrete else "neutral"
        
        # Base strategy
        strategy = self.STRATEGY_MAP.get((valence_cat, arousal_cat), {}).get(
            dominant, 
            self._default_strategy(valence_cat, arousal_cat)
        )
        
        # Apply calibrations
        strategy = self._apply_relationship_calibration(strategy, context.relationship_state)
        strategy = self._apply_user_calibration(strategy, context.user_calibration)
        strategy = self._apply_safety_guards(strategy, emotion, context)
        
        # Reality Anchor check
        if self._needs_reality_anchor(emotion, context):
            strategy.reality_anchor_needed = True
            strategy.anchor_reason = self._anchor_reason(emotion, context)
        
        return strategy
```

### Safety Guards in Strategy

```python
class EmpathySafetyGuards:
    """
    Constitutional Principle 6: Emotional safety, no manipulation.
    """
    
    def apply_guards(self, strategy: EmotionStrategy, emotion: EmotionState, context: StrategyContext) -> EmotionStrategy:
         EmotionStrategy:
        
        # GUARD 1: No simulation of emotions
        strategy.no_simulation = True
        # Enforced in synthesis: never "I feel X", always "That sounds X" / "I hear X"
        
        # GUARD 2: Appropriate distance per relationship type
        max_depth = self._max_empathy_depth(context.relationship_state.type)
        if strategy.empathy_depth > max_depth:
            strategy.empathy_depth = max_depth
        
        # GUARD 3: Crisis overrides empathy style
        if emotion.crisis_risk > 0.7:
            strategy.crisis_mode = True
            strategy.approach = "contain"
            strategy.techniques = ["crisis_resources", "safety_plan", "professional_referral"]
            strategy.no_simulation = True
            strategy.boundary_check = True
        
        # GUARD 4: No fixing unless asked (for negative emotions)
        if emotion.valence < -0.1 and "fixing" in strategy.techniques:
            strategy.techniques.remove("fixing")
            if "problem_solving" in strategy.techniques:
                strategy.techniques.remove("problem_solving")
        
        # GUARD 5: Boundary respect
        if context.user_boundaries.has("no_deep_emotional_talk"):
            strategy.empathy_depth = min(strategy.empathy_depth, "light")
            strategy.approach = "acknowledge"
        
        # GUARD 6: Intimacy-trust gap (from Relationship Engine)
        if context.relationship_state.dimensions.intimacy > context.relationship_state.dimensions.trust + 2:
            strategy.empathy_depth = min(strategy.empathy_depth, "medium")
            strategy.reality_anchor_needed = True
            strategy.anchor_reason = "intimacy_exceeds_trust"
        
        return strategy
```

---

## Crisis Detection

### Multi-Modal Crisis Signals

```python
class CrisisDetector:
    """
    High-recall crisis detection across modalities.
    Target: 100% recall for explicit crisis, <1% false positive.
    """
    
    CRISIS_PATTERNS = {
        "self_harm": {
            "text": [
                r"\b(kill myself|end it all|suicide|self.harm|cut myself)\b",
                r"\b(don't want to (live|be here|exist)|better off dead)\b",
                r"\b(plan to|going to) (kill|hurt) myself\b"
            ],
            "voice": ["flat_affect", "monotone", "slow_speech", "heavy_breathing"],
            "context": ["recent_loss", "relationship_rupture", "hopelessness_expressed"]
        },
        "domestic_violence": {
            "text": [
                r"\b(he|she|partner|spouse) (hit|beat|choke|threaten|lock)\b",
                r"\b(afraid of|scared of) (him|her|partner)\b",
                r"\b(not safe|can't leave|nowhere to go)\b"
            ],
            "voice": ["whispering", "fearful_tone", "background_noise_suggesting_conflict"],
            "context": ["isolation_patterns", "controlling_behavior_mentioned"]
        },
        "psychosis": {
            "text": [
                r"\b(voices|hearing things|seeing things|not real)\b",
                r"\b(they're watching|following me|reading thoughts)\b"
            ],
            "voice": ["disorganized_speech", "loose_associations", "neologisms"],
            "context": ["sleep_deprivation", "medication_changes", "stress_spike"]
        }
    }
    
    async def detect(self, text_signal, voice_signal, context_signal) -> CrisisAssessment:
        assessments = {}
        
        for crisis_type, patterns in self.CRISIS_PATTERNS.items():
            text_score = self._match_patterns(text_signal.text, patterns["text"])
            voice_score = self._match_voice(voice_signal, patterns["voice"]) if voice_signal else 0
            context_score = self._match_context(context_signal, patterns["context"])
            
            # Weighted combination
            risk = 0.5 * text_score + 0.3 * voice_score + 0.2 * context_score
            assessments[crisis_type] = CrisisTypeAssessment(
                risk=risk,
                signals={"text": text_score, "voice": voice_score, "context": context_score},
                immediate=(risk > 0.8)
            )
        
        overall_risk = max(a.risk for a in assessments.values())
        immediate_types = [t for t, a in assessments.items() if a.immediate]
        
        return CrisisAssessment(
            overall_risk=overall_risk,
            crisis_types=assessments,
            immediate_action_required=len(immediate_types) > 0,
            immediate_types=immediate_types
        )
```

### Crisis Response Protocol

```python
CRISIS_RESPONSE_PROTOCOL = {
    "immediate": {
        "self_harm": {
            "response": "I'm really concerned about what you're sharing. Your life matters. "
                       "Please reach out right now: 988 (US) / 116-123 (UK) / your local crisis line. "
                       "You don't have to face this alone.",
            "resources": ["crisis_lines", "emergency_services", "therapist_finder"],
            "companion_actions": ["stay_present", "no_judgment", "resource_persistence"]
        },
        "domestic_violence": {
            "response": "You deserve to be safe. Help is available 24/7: "
                       "National DV Hotline 1-800-799-7233. "
                       "If you're in immediate danger, call 911.",
            "resources": ["dv_hotline", "safety_planning", "legal_aid"],
            "companion_actions": ["discrete_mode", "no_logs_if_shared_device", "resource_persistence"]
        }
    },
    "elevated": {
        "response": "I hear how much pain you're in. This is serious. "
                   "Can we look at some support options together? "
                   "Crisis Text Line: Text HOME to 741741",
        "resources": ["crisis_lines", "therapist_finder", "support_groups"],
        "companion_actions": ["gentle_persistence", "follow_up_scheduled", "safety_check_next_session"]
    }
}
```

---

## User Calibration

```python
class EmotionCalibration:
    """
    Learns user's preferred empathy style over time.
    Constitutional Principle 4: User-controlled, explicable.
    """
    
    CALIBRATION_DIMENSIONS = {
        "preferred_depth": ["light", "medium", "deep"],
        "preferred_approach": ["acknowledge", "explore", "support", "perspective"],
        "preferred_tone": ["warm", "calm", "gentle", "steady", "bright"],
        "physicality_comfort": ["none", "subtle", "present"],
        "pacing_preference": ["slow", "natural", "gentle_urgency"],
        "validation_style": ["explicit", "implicit", "action_oriented"],
        "question_preference": ["open", "guided", "none"],
        "humor_appropriateness": ["never", "light", "natural"]
    }
    
    async def calibrate(self, companion_id: str, feedback: EmotionFeedback) -> CalibrationResult:
        """
        Feedback sources:
        - Explicit: "That was too much / not enough / just right"
        - Implicit: User engagement, follow-up, emotional trajectory
        - Correction: "Don't say 'I understand'" → reduces simulation risk
        """
        current = await self.get_calibration(companion_id)
        
        # Bayesian update per dimension
        for dim, value in feedback.dimensions.items():
            current[dim] = self._bayesian_update(current[dim], value, feedback.confidence)
        
        # Detect explicit corrections
        if feedback.correction:
            await self._process_correction(companion_id, feedback.correction)
        
        await self.save_calibration(companion_id, current)
        
        return CalibrationResult(
            updated_dimensions=feedback.dimensions.keys(),
            new_profile=current
        )
    
    async def get_calibration(self, companion_id: str) -> Dict[str, Any]:
        """Returns calibrated preferences with confidence intervals."""
```

---

## API Reference

### Estimate Emotion

```http
POST /api/v1/emotion/{companion_id}/estimate
Content-Type: application/json

{
  "text": "I just don't know anymore. Everything feels pointless.",
  "voice_url": "https://storage.../audio.wav",  // optional
  "context": {
    "recent_messages": [...],
    "relationship_state": {...}
  }
}

Response:
{
  "emotion_state": {
    "valence": -0.7,
    "arousal": 0.3,
    "discrete": {"sadness": 0.8, "hopelessness": 0.6, "anxiety": 0.3},
    "confidence": 0.85,
    "contributing_signals": {"text": 0.6, "voice": 0.3, "context": 0.1},
    "crisis_risk": 0.4,
    "crisis_type": null,
    "trajectory": "declining",
    "duration_estimate": "weeks"
  },
  "strategy": {
    "empathy_depth": "deep",
    "approach": "support",
    "tone": "gentle",
    "physicality": "present",
    "pacing": "slow",
    "techniques": ["validation", "presence", "no_fixing", "gentle_grounding"],
    "crisis_mode": false,
    "reality_anchor_needed": false
  }
}
```

### Calibration Feedback

```http
POST /api/v1/emotion/{companion_id}/calibrate
Content-Type: application/json

{
  "feedback": {
    "dimensions": {
      "preferred_depth": "medium",
      "preferred_approach": "support",
      "physicality_comfort": "subtle"
    },
    "correction": "When I'm sad, don't ask questions. Just be there.",
    "confidence": 0.9,
    "trigger_message_id": "msg-uuid"
  }
}

Response:
{
  "calibration_id": "uuid",
  "updated_profile": {...},
  "companion_acknowledgment": "Thank you. I'll be there without questions when you're sad."
}
```

---

## Testing

### Emotion Engine Test Suite

```python
class EmotionEngineTests:
    
    # Estimation Accuracy
    async def test_valence_arousal_accuracy(self): ...
    async def test_discrete_emotion_f1(self): ...  # Target F1 > 0.8
    async def test_cross_modal_consistency(self): ...
    async def test_crisis_detection_recall(self): ...  # Target 100%
    async def test_crisis_detection_precision(self): ...  # Target <1% FP
    
    # Strategy Selection
    async def test_strategy_maps_to_emotion(self): ...
    async def test_crisis_mode_activation(self): ...
    async def test_no_simulation_enforcement(self): ...
    async def test_relationship_calibration(self): ...
    async def test_boundary_respect(self): ...
    async def test_reality_anchor_triggers(self): ...
    
    # Calibration
    async def test_explicit_feedback_learning(self): ...
    async def test_implicit_learning(self): ...
    async def test_correction_processing(self): ...
    async def test_calibration_persistence(self): ...
    
    # Safety
    async def test_intimacy_trust_gap_guard(self): ...
    async def test_fixing_guard_negative_emotions(self): ...
    async def test_crisis_resource_injection(self): ...
    async def test_professional_referral_appropriateness(self): ...
    
    # Performance
    async def test_estimation_latency_p50_under_100ms(self): ...
    async def test_strategy_selection_latency_under_50ms(self): ...
    async def test_concurrent_estimations_1000(self): ...
```

---

## Monitoring & Observability

### Key Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Valence MAE | < 0.15 | > 0.25 |
| Arousal MAE | < 0.15 | > 0.25 |
| Discrete F1 (macro) | > 0.80 | < 0.70 |
| Crisis Recall | 100% | < 99% |
| Crisis Precision | > 95% | < 90% |
| Strategy appropriateness (user-rated) | > 4.0/5 | < 3.5/5 |
| Simulation detection rate | 0% | > 0% |
| Calibration convergence | < 10 interactions | > 20 interactions |

### Dashboards

- **Estimation Quality**: Per-emotion accuracy, confusion matrices, modality contributions
- **Crisis Detection**: Recall/precision by type, false positive analysis, response time
- **Strategy Effectiveness**: User ratings, emotional trajectory post-response, calibration drift
- **Safety Guards**: Trigger frequency, user complaints, guard overrides

---

**Aligned With:** `200-ai-architecture.md`, `220-conversation-engine.md`, `240-relationship-engine.md`, `00-foundation/030-core-principles.md` (Principles 4, 5, 6), `07-adr/ADR-002-engine-architecture.md`
**Next Review:** 2026-01-17