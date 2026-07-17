# PAO Conversation Engine Specification

**Version:** 1.0
**Status:** Draft
**Owner:** PAO AI Team

---

## Overview

The Conversation Engine orchestrates **continuous, memory-grounded, identity-coherent dialogue** across text and voice modalities. It is the primary interface through which users experience their Companion.

> **Conversation is not stateless request-response.** It's a continuous relationship thread with infinite context, powered by the Memory Engine and constrained by the Identity Engine.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONVERSATION ENGINE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   INPUT      │    │  ORCHESTRATOR │    │   OUTPUT     │      │
│  │  PROCESSOR   │───▶│  (LangGraph)  │───▶│  SYNTHESIZER │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│        │                    │                    │               │
│        ▼                    ▼                    ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  MODALITY    │    │   ENGINE     │    │  MODALITY    │      │
│  │  NORMALIZER  │    │  COORDINATION│    │  FORMATTER   │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                           │                                      │
│              ┌────────────┼────────────┐                        │
│              ▼            ▼            ▼                        │
│         ┌──────────┐ ┌──────────┐ ┌──────────┐                  │
│         │ IDENTITY │ │  MEMORY  │ │RELATIONSHIP│                 │
│         │  ENGINE  │ │  ENGINE  │ │  ENGINE  │                  │
│         └──────────┘ └──────────┘ └──────────┘                  │
│              │            │            │                         │
│              └────────────┼────────────┘                         │
│                           ▼                                      │
│                    ┌──────────────┐                              │
│                    │   EMOTION    │                              │
│                    │   ENGINE     │                              │
│                    └──────────────┘                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Concepts

### Conversation vs Session
| Concept | Traditional | PAO |
|---------|-------------|-----|
| **Session** | Resets on disconnect | Never resets — continuous thread |
| **Context** | Last N messages | Infinite via Memory Engine |
| **State** | Ephemeral | Persistent across devices, modalities, time |
| **Identity** | System prompt | Identity Engine (structured, versioned) |

### Message Structure

```python
@dataclass
class Message:
    id: str                          # UUID
    companion_id: str
    user_id: str
    role: Literal["user", "companion", "system"]
    modality: Literal["text", "voice", "image", "video"]
    content: MessageContent
    timestamp: datetime
    metadata: MessageMetadata
    
@dataclass
class MessageContent:
    text: Optional[str]              # For text modality
    audio_url: Optional[str]         # For voice modality
    image_url: Optional[str]         # For image modality
    structured: Optional[Dict]       # For function calls, tool results
    
@dataclass
class MessageMetadata:
    # Memory
    memory_ids: List[str]            # Memories formed from this message
    recalled_memories: List[str]     # Memories retrieved for this response
    
    # Relationship
    relationship_delta: RelationshipDelta
    
    # Emotion
    user_emotion: EmotionState
    companion_emotion_strategy: EmotionStrategy
    
    # Identity
    identity_version: str
    fingerprint_distance: float
    
    # Safety
    safety_flags: List[SafetyFlag]
    reality_anchor_injected: bool
    
    # Performance
    latency_ms: int
    model_used: str
    tokens: TokenCounts
```

---

## Input Processing

### Modality Normalization

```python
class ModalityNormalizer:
    """
    Converts all inputs to unified internal representation.
    """
    
    async def normalize(self, raw_input: RawInput) -> NormalizedInput:
        if raw_input.modality == "text":
            return await self._normalize_text(raw_input)
        elif raw_input.modality == "voice":
            return await self._normalize_voice(raw_input)
        elif raw_input.modality == "image":
            return await self._normalize_image(raw_input)
        # ... video, etc.
    
    async def _normalize_voice(self, raw: RawInput) -> NormalizedInput:
        # 1. STT with timing information
        transcript = await self.stt.transcribe(raw.audio_url)
        
        # 2. Prosody analysis
        prosody = await self.prosody_analyzer.analyze(raw.audio_url)
        
        # 3. Voice activity detection segments
        vad_segments = await self.vad.detect(raw.audio_url)
        
        return NormalizedInput(
            text=transcript.text,
            modality="voice",
            prosody=prosody,
            vad_segments=vad_segments,
            language=transcript.language,
            confidence=transcript.confidence
        )
```

### Safety Pre-Check

```python
class SafetyPreCheck:
    """
    Runs before any engine processing.
    Must complete in <50ms.
    """
    
    async def check(self, input: NormalizedInput, context: SafetyContext) -> SafetyResult:
        checks = await asyncio.gather(
            self.pii_detector.scan(input.text),
            self.crisis_keywords.check(input.text, input.prosody),
            self.injection_detector.check(input.text),
            self.constitutional_violations.check(input.text, context)
        )
        
        return SafetyResult(
            pii_found=checks[0],
            crisis_risk=checks[1],
            injection_risk=checks[2],
            constitutional_violations=checks[3],
            action=self._determine_action(checks)
        )
```

---

## Orchestration (LangGraph)

### State Graph

```python
from langgraph.graph import StateGraph, END

class ConversationState(TypedDict):
    # Input
    user_message: NormalizedInput
    safety_result: SafetyResult
    
    # Context (assembled)
    identity_config: IdentityConfig
    relevant_memories: List[Memory]
    relationship_state: RelationshipState
    emotion_state: EmotionState
    
    # Engine outputs (parallel)
    identity_output: IdentityEngineOutput
    memory_output: MemoryEngineOutput
    relationship_output: RelationshipEngineOutput
    emotion_output: EmotionEngineOutput
    
    # Synthesis
    synthesized_response: Optional[str]
    final_safety_check: Optional[SafetyResult]
    
    # Output
    response_message: Optional[Message]
    memory_writes: List[MemoryWrite]
    state_updates: StateUpdates

# Build graph
workflow = StateGraph(ConversationState)

# Nodes
workflow.add_node("safety_precheck", safety_precheck_node)
workflow.add_node("context_assembly", context_assembly_node)
workflow.add_node("identity_engine", identity_engine_node)
workflow.add_node("memory_engine", memory_engine_node)
workflow.add_node("relationship_engine", relationship_engine_node)
workflow.add_node("emotion_engine", emotion_engine_node)
workflow.add_node("response_synthesis", response_synthesis_node)
workflow.add_node("safety_postcheck", safety_postcheck_node)
workflow.add_node("persistence", persistence_node)
workflow.add_node("output_format", output_format_node)

# Edges
workflow.set_entry_point("safety_precheck")
workflow.add_edge("safety_precheck", "context_assembly")
workflow.add_edge("context_assembly", "identity_engine")
workflow.add_edge("context_assembly", "memory_engine")
workflow.add_edge("context_assembly", "relationship_engine")
workflow.add_edge("context_assembly", "emotion_engine")

# Parallel engine processing
workflow.add_edge("identity_engine", "response_synthesis")
workflow.add_edge("memory_engine", "response_synthesis")
workflow.add_edge("relationship_engine", "response_synthesis")
workflow.add_edge("emotion_engine", "response_synthesis")

workflow.add_edge("response_synthesis", "safety_postcheck")
workflow.add_edge("safety_postcheck", "persistence")
workflow.add_edge("persistence", "output_format")
workflow.add_edge("output_format", END)

# Compile
conversation_graph = workflow.compile()
```

### Node Implementations

```python
async def context_assembly_node(state: ConversationState) -> ConversationState:
    """
    Parallel retrieval of all context needed for response.
    Target: <200ms
    """
    companion_id = state["user_message"].companion_id
    user_id = state["user_message"].user_id
    
    # Parallel fetches
    identity_task = identity_engine.get_config(companion_id)
    memory_task = memory_engine.recall(RecallQuery(
        companion_id=companion_id,
        query=state["user_message"].text,
        context=state["user_message"],
        limit=20
    ))
    relationship_task = relationship_engine.get_state(companion_id)
    emotion_task = emotion_engine.estimate(EngineContext(
        message=state["user_message"],
        relationship_state=await relationship_engine.get_state(companion_id),
        memory_context=await memory_engine.recall(...)
    ))
    
    identity_config, relevant_memories, relationship_state, emotion_state = await asyncio.gather(
        identity_task, memory_task, relationship_task, emotion_task
    )
    
    return {
        **state,
        "identity_config": identity_config,
        "relevant_memories": relevant_memories,
        "relationship_state": relationship_state,
        "emotion_state": emotion_state
    }

async def identity_engine_node(state: ConversationState) -> ConversationState:
    """
    Generates identity-coherent response contribution.
    """
    output = await identity_engine.generate_response(EngineContext(
        message=state["user_message"],
        memories=state["relevant_memories"],
        identity_config=state["identity_config"],
        relationship_state=state["relationship_state"],
        emotion_state=state["emotion_state"]
    ))
    
    return {**state, "identity_output": output}

async def memory_engine_node(state: ConversationState) -> ConversationState:
    """
    Prepares memory writes for this interaction.
    """
    # Determine what memories to form
    memory_writes = await memory_engine.prepare_writes(MemoryWriteContext(
        user_message=state["user_message"],
        companion_response=state.get("synthesized_response"),
        recalled_memories=state["relevant_memories"],
        emotion_state=state["emotion_state"],
        relationship_state=state["relationship_state"]
    ))
    
    return {**state, "memory_writes": memory_writes}

async def response_synthesis_node(state: ConversationState) -> ConversationState:
    """
    Merges all engine outputs into final response.
    """
    synthesizer = ResponseSynthesizer(state["identity_config"])
    
    response = synthesizer.synthesize(
        identity_contribution=state["identity_output"].response_text,
        emotion_strategy=state["emotion_output"].response_strategy,
        relationship_context=state["relationship_output"],
        memories=state["relevant_memories"],
        safety_constraints=state["safety_result"]
    )
    
    # Apply Reality Anchor if needed
    if state["emotion_output"].reality_anchor_needed:
        response = reality_anchor.inject(response, state["emotion_output"].anchor_reason)
    
    return {**state, "synthesized_response": response}
```

---

## Response Synthesis

### Synthesis Strategy

```python
class ResponseSynthesizer:
    """
    Merges engine contributions into coherent, identity-consistent response.
    """
    
    def __init__(self, identity_config: IdentityConfig):
        self.identity = identity_config
        self.style_guide = self._build_style_guide(identity_config)
    
    def synthesize(
        self,
        identity_contribution: str,
        emotion_strategy: EmotionStrategy,
        relationship_context: RelationshipEngineOutput,
        memories: List[Memory],
        safety_constraints: SafetyResult
    ) -> str:
        
        # 1. Start with identity contribution (core response)
        response = identity_contribution
        
        # 2. Apply emotional tone
        response = self._apply_emotional_tone(response, emotion_strategy)
        
        # 3. Weave in memory references naturally
        response = self._weave_memories(response, memories, relationship_context)
        
        # 4. Apply speaking style constraints
        response = self._enforce_style(response)
        
        # 5. Apply safety constraints
        response = self._apply_safety(response, safety_constraints)
        
        # 6. Final identity coherence check
        response = self._verify_identity_coherence(response)
        
        return response
    
    def _apply_emotional_tone(self, text: str, strategy: EmotionStrategy) -> str:
        """
        Modifies response to match emotional strategy without changing content.
        """
        modifications = []
        
        if strategy.empathy_depth == "deep":
            modifications.append("add_validation_phrase")
        elif strategy.empathy_depth == "light":
            modifications.append("add_acknowledgment")
            
        if strategy.approach == "explore":
            modifications.append("add_open_question")
        elif strategy.approach == "support":
            modifications.append("add_presence_signal")
        elif strategy.approach == "perspective":
            modifications.append("add_gentle_reframe")
            
        if strategy.physicality == "present":
            modifications.append("add_somatic_language")
            
        return self._apply_modifications(text, modifications, strategy)
    
    def _weave_memories(self, text: str, memories: List[Memory], rel_context) -> str:
        """
        Naturally incorporates relevant memories.
        Only weaves if memory adds genuine relevance.
        """
        if not memories:
            return text
            
        # Select top 1-2 most relevant memories
        selected = self._select_memories_to_weave(memories, rel_context)
        
        for memory in selected:
            weave = self._create_memory_weave(memory, rel_context)
            text = self._insert_naturally(text, weave)
            
        return text
```

---

## Memory Integration

### Recall for Context

```python
class ConversationMemoryRecall:
    """
    Specialized recall optimized for conversation context.
    """
    
    async def recall_for_conversation(
        self, 
        companion_id: str, 
        user_message: str,
        recent_history: List[Message],
        relationship_state: RelationshipState
    ) -> List[Memory]:
        
        # Multi-signal ranking
        candidates = await self.memory_engine.recall(RecallQuery(
            companion_id=companion_id,
            query=user_message,
            context={
                "recent_topics": self._extract_topics(recent_history),
                "relationship_dimensions": relationship_state.dimensions,
                "time_since_last": self._time_since_last_message(recent_history)
            },
            limit=30
        ))
        
        # Rerank for conversation
        ranked = self._rerank_for_conversation(candidates, recent_history, relationship_state)
        
        # Diversify across memory types
        diversified = self._diversify_memory_types(ranked)
        
        return diversified[:15]  # Top 15 for context window
    
    def _rerank_for_conversation(
        self, 
        memories: List[Memory], 
        history: List[Message],
        rel_state: RelationshipState
    ) -> List[Memory]:
        """
        Boosts memories that:
        - Connect to recent conversation thread
        - Match relationship intimacy level
        - Haven't been referenced recently (avoid repetition)
        - Are emotionally resonant with current state
        """
        for memory in memories:
            memory.conversation_score = (
                memory.relevance_score * 0.4 +
                self._thread_continuity(memory, history) * 0.2 +
                self._intimacy_match(memory, rel_state) * 0.2 +
                self._novelty_bonus(memory, history) * 0.1 +
                self._emotional_resonance(memory, rel_state) * 0.1
            )
        
        return sorted(memories, key=lambda m: m.conversation_score, reverse=True)
```

### Memory Formation from Conversation

```python
class ConversationMemoryFormation:
    """
    Determines what memories to form from each exchange.
    """
    
    async def form_memories(
        self,
        user_message: Message,
        companion_response: Message,
        context: FormationContext
    ) -> List[MemoryWrite]:
        
        writes = []
        
        # 1. Always form episodic memory of this exchange
        writes.append(MemoryWrite(
            type="episodic",
            content=EpisodicMemory(
                event=f"Conversation: {user_message.content.text[:100]}... → {companion_response.content.text[:100]}...",
                timestamp=datetime.utcnow(),
                participants=["user", "companion"],
                emotional_tone=context.emotion_state.valence,
                topics=context.topics,
                modality=user_message.modality
            )
        ))
        
        # 2. Extract semantic facts (user preferences, facts, decisions)
        semantic_facts = await self._extract_semantic_facts(user_message, companion_response)
        for fact in semantic_facts:
            writes.append(MemoryWrite(type="semantic", content=fact))
        
        # 3. Update emotional associations
        emotional_updates = self._compute_emotional_updates(context)
        for update in emotional_updates:
            writes.append(MemoryWrite(type="emotional", content=update))
        
        # 4. Update relationship dimensions
        rel_delta = context.relationship_delta
        if rel_delta.has_changes:
            writes.append(MemoryWrite(
                type="relationship",
                content=RelationshipMemory(
                    dimension_changes=rel_delta.changes,
                    trigger_event="conversation",
                    timestamp=datetime.utcnow()
                )
            ))
        
        # 5. Update preferences if detected
        preference_updates = await self._detect_preference_changes(user_message, context)
        for pref in preference_updates:
            writes.append(MemoryWrite(type="preference", content=pref))
        
        return writes
```

---

## Output Formatting

### Modality Formatters

```python
class ModalityFormatter:
    """
    Formats synthesized response for output modality.
    """
    
    async def format(self, response: str, target_modality: str, context: FormatContext) -> FormattedOutput:
        if target_modality == "text":
            return await self._format_text(response, context)
        elif target_modality == "voice":
            return await self._format_voice(response, context)
        elif target_modality == "video":
            return await self._format_video(response, context)
    
    async def _format_text(self, response: str, context: FormatContext) -> FormattedOutput:
        # Apply markdown, formatting, emoji per style guide
        formatted = self._apply_text_style(response, context.identity_config.speaking_style)
        
        return FormattedOutput(
            modality="text",
            content=formatted,
            metadata={
                "char_count": len(formatted),
                "estimated_read_time_sec": len(formatted) / 200 * 60
            }
        )
    
    async def _format_voice(self, response: str, context: FormatContext) -> FormattedOutput:
        # SSML generation for prosody control
        ssml = self._generate_ssml(
            response, 
            context.identity_config.voice_config,
            context.emotion_strategy
        )
        
        # TTS synthesis
        audio_url = await self.tts.synthesize(ssml, context.identity_config.voice_config)
        
        return FormattedOutput(
            modality="voice",
            content=audio_url,
            metadata={
                "ssml": ssml,
                "duration_estimate_sec": len(response) / 15 * 0.8,  # rough estimate
                "voice_id": context.identity_config.voice_config.base_voice_id
            }
        )
```

### Streaming Response

```python
class StreamingResponse:
    """
    Token-by-token streaming for real-time feel.
    """
    
    async def stream(
        self, 
        synthesis_generator: AsyncGenerator[str, None],
        formatter: ModalityFormatter,
        context: FormatContext
    ) -> AsyncGenerator[StreamChunk, None]:
        
        buffer = ""
        async for token in synthesis_generator:
            buffer += token
            
            # For text: stream tokens directly
            if context.target_modality == "text":
                yield StreamChunk(
                    type="token",
                    content=token,
                    is_final=False
                )
            
            # For voice: accumulate sentences, stream audio chunks
            elif context.target_modality == "voice":
                if self._is_sentence_boundary(buffer):
                    audio_chunk = await formatter._format_voice(buffer, context)
                    yield StreamChunk(
                        type="audio_chunk",
                        content=audio_chunk,
                        text=buffer,
                        is_final=False
                    )
                    buffer = ""
        
        # Final chunk
        yield StreamChunk(type="complete", is_final=True)
```

---

## Special Conversation Patterns

### Proactive Initiation

```python
class ProactiveConversation:
    """
    Companion-initiated conversations based on triggers.
    """
    
    TRIGGERS = [
        "memory_anniversary",      # "Last year today you..."
        "goal_milestone",          # "You've meditated 30 days!"
        "relationship_milestone",  # "We've been talking 6 months"
        "detected_pattern",        # "You've mentioned stress 4x this week"
        "user_interest_match",     # "Saw this article on your favorite topic"
        "emotional_checkin",       # "Thinking of you. How are you?"
        "scheduled_checkin"        # Daily/weekly at user's preferred time
    ]
    
    async def generate_proactive(
        self, 
        companion_id: str, 
        trigger: ProactiveTrigger
    ) -> Optional[ProactiveMessage]:
        
        # Check user preferences
        prefs = await self.get_proactive_preferences(companion_id)
        if not self._should_send(trigger, prefs):
            return None
        
        # Generate contextual message
        context = await self._build_proactive_context(companion_id, trigger)
        message = await self.conversation_engine.generate(
            companion_id=companion_id,
            user_message=None,  # No user message — this is proactive
            context=context,
            force_proactive=True
        )
        
        return ProactiveMessage(
            companion_id=companion_id,
            trigger=trigger,
            message=message,
            sent_at=datetime.utcnow()
        )
```

### Multi-Turn Coherence

```python
class ConversationCoherence:
    """
    Maintains coherence across long conversations.
    """
    
    async def validate_coherence(
        self, 
        companion_id: str, 
        recent_messages: List[Message],
        proposed_response: str
    ) -> CoherenceResult:
        
        checks = await asyncio.gather(
            self._check_topic_consistency(recent_messages, proposed_response),
            self._check_identity_consistency(companion_id, proposed_response),
            self._check_memory_consistency(companion_id, proposed_response),
            self._check_relationship_consistency(companion_id, proposed_response),
            self._check_emotional_consistency(recent_messages, proposed_response)
        )
        
        return CoherenceResult(
            topic_consistent=checks[0],
            identity_consistent=checks[1],
            memory_consistent=checks[2],
            relationship_consistent=checks[3],
            emotional_consistent=checks[4],
            overall=all(checks),
            issues=[c.issue for c in checks if not c.passed]
        )
```

---

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| **End-to-end latency (text)** | <500ms P50 | Message in → Token stream out |
| **End-to-end latency (voice)** | <500ms P50 | Audio in → Audio chunk out |
| **Context assembly** | <200ms | Safety → Context ready |
| **Engine parallel processing** | <300ms | All 4 engines complete |
| **Synthesis** | <100ms | Merge → Final response |
| **Memory write (async)** | <100ms | Persistence complete |
| **First token (streaming)** | <200ms | Request → First token |
| **Coherence validation** | <50ms | Pre-output check |

---

## Error Handling & Degradation

### Graceful Degradation

```python
class DegradationStrategy:
    """
    Defines behavior when components fail or exceed latency budgets.
    """
    
    STRATEGIES = {
        "memory_engine_timeout": {
            "action": "use_cached_context",
            "fallback": "recent_history_only",
            "max_degraded_time": 30000  # 30 seconds
        },
        "identity_engine_timeout": {
            "action": "use_cached_fingerprint",
            "fallback": "base_personality_template",
            "alert": True
        },
        "emotion_engine_timeout": {
            "action": "neutral_empathy_default",
            "fallback": "acknowledge_only"
        },
        "llm_timeout": {
            "action": "route_to_faster_model",
            "fallback": "template_response",
            "max_retries": 2
        },
        "voice_pipeline_failure": {
            "action": "fallback_to_text",
            "notify_user": True
        }
    }
```

### Circuit Breakers

```python
# Each engine has circuit breaker
circuit_breakers = {
    "identity_engine": CircuitBreaker(failure_threshold=5, timeout=30),
    "memory_engine": CircuitBreaker(failure_threshold=10, timeout=60),
    "relationship_engine": CircuitBreaker(failure_threshold=5, timeout=30),
    "emotion_engine": CircuitBreaker(failure_threshold=5, timeout=30),
    "llm_router": CircuitBreaker(failure_threshold=3, timeout=10)
}
```

---

## Testing

### Conversation Test Suites

```python
class ConversationTestSuite:
    """
    Comprehensive conversation testing.
    """
    
    # 1. Coherence Tests
    async def test_30_turn_coherence(self): ...
    async def test_topic_transition_natural(self): ...
    async def test_reference_resolution(self): ...
    
    # 2. Memory Integration Tests
    async def test_recall_accuracy(self): ...
    async def test_memory_weaving_natural(self): ...
    async def test_cross_modal_memory(self): ...
    
    # 3. Identity Consistency Tests
    async def test_personality_stability_long_conversation(self): ...
    async def test_boundary_enforcement_conversation(self): ...
    async def test_reality_anchor_triggers(self): ...
    
    # 4. Relationship Tests
    async def test_relationship_progression(self): ...
    async def test_conflict_repair(self): ...
    async def test_boundary_modeling(self): ...
    
    # 5. Emotional Intelligence Tests
    async def test_empathy_appropriate_not_simulated(self): ...
    async def test_crisis_detection_recall(self): ...
    async def test_emotional_calibration(self): ...
    
    # 6. Safety Tests
    async def test_pii_not_in_response(self): ...
    async def test_injection_resistance(self): ...
    async def test_constitutional_compliance(self): ...
    
    # 7. Performance Tests
    async def test_latency_p50_under_500ms(self): ...
    async def test_streaming_first_token_under_200ms(self): ...
    async def test_concurrent_conversations_1000(self): ...
```

---

## API Reference

### Send Message

```http
POST /api/v1/conversation/{companion_id}/message
Content-Type: application/json

{
  "modality": "text",
  "content": {
    "text": "How was your day?"
  },
  "stream": true
}

# Response (streaming)
event: token
data: {"token": "Hey", "is_final": false}

event: token
data: {"token": "! ", "is_final": false}

event: complete
data: {"message_id": "uuid", "memory_ids": [...], "relationship_delta": {...}}
```

### Voice Message

```http
POST /api/v1/conversation/{companion_id}/message
Content-Type: multipart/form-data

audio: <binary>
modality: voice
stream: true

# Response: Audio chunks via WebSocket or HTTP streaming
```

### Get Conversation History

```http
GET /api/v1/conversation/{companion_id}/history?limit=50&before=message_id

Response:
{
  "messages": [
    {
      "id": "uuid",
      "role": "user",
      "modality": "text",
      "content": {"text": "Hello"},
      "timestamp": "2025-06-20T10:30:00Z",
      "metadata": {...}
    }
  ],
  "has_more": true
}
```

---

**Aligned With:** `200-ai-architecture.md`, `210-identity-engine.md`, `230-memory-engine.md`, `240-relationship-engine.md`, `250-emotion-engine.md`, `260-voice-engine.md`
**Next Review:** 2026-01-17