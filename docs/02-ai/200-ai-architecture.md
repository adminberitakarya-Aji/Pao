# PAO AI Architecture

**Version:** 1.0
**Status:** Draft
**Owner:** PAO AI Team

---

## Overview

The PAO AI Architecture is built around **four specialized engines** orchestrated by the **Companion Runtime**. This modular design ensures each engine can be developed, tested, and scaled independently while maintaining strict consistency guarantees.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                           │
│  (Flutter Mobile, Web, AR/VR, Wearable, Voice, API)            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      COMPANION RUNTIME                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Orchestrator│  │  Feature    │  │  Safety     │             │
│  │  (LangGraph)│  │   Flags     │  │  Guards     │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  IDENTITY     │  │   MEMORY      │  │ RELATIONSHIP  │  │   EMOTION     │
│  ENGINE       │  │   ENGINE      │  │   ENGINE      │  │   ENGINE      │
│               │  │               │  │               │  │               │
│ • Personality │  │ • 6 Memory    │  │ • 6 Dimensions│  │ • Estimation  │
│ • Values      │  │   Types       │  │ • Type Dynamics│ │ • Generation  │
│ • Boundaries  │  │ • Vector+     │  │ • Score Calc  │  │ • Boundaries  │
│ • Voice Style │  │   Graph+Rel   │  │ • Boundaries  │  │ • Crisis      │
│ • Drift Detect│  │ • Consolidate │  │ • Shared Diary│  │ • Proactive   │
└───────────────┘  └───────────────┘  └───────────────┘  └───────────────┘
        │                    │                    │                    │
        └────────────────────┴────────────────────┴────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE LAYER                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │   LLM    │ │  Voice   │ │  Vector  │ │  Graph   │           │
│  │ Router   │ │ Pipeline │ │   DB     │ │   DB     │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Relational│ │  Cache  │ │  Object  │ │  Queue   │           │
│  │   DB     │ │  (Redis)│ │  Storage │ │  (Kafka) │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Companion Runtime

### Responsibilities
- **Orchestration**: Routes requests to appropriate engines
- **State Management**: Maintains conversation context across engines
- **Feature Flags**: Controls capability rollout per user/cohort
- **Safety Guards**: Pre/post-processing safety checks
- **Observability**: Tracing, metrics, logging

### Technology
- **Framework**: LangGraph (stateful, cyclic, human-in-the-loop)
- **Language**: Python 3.11+
- **Deployment**: Kubernetes, horizontal scaling
- **State**: Redis for ephemeral, PostgreSQL for persistent

### Runtime Flow (Per User Message)

```
User Message
     │
     ▼
┌──────────────────────────────────────┐
│ 1. SAFETY PRE-CHECK                  │
│    - Crisis detection                │
│    - PII detection                   │
│    - Constitutional compliance       │
└──────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────┐
│ 2. CONTEXT ASSEMBLY                  │
│    - Retrieve relevant memories      │
│    - Load identity config            │
│    - Load relationship state         │
│    - Estimate user emotion           │
└──────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────┐
│ 3. ENGINE ORCHESTRATION (Parallel)   │
│    ┌──────────┐ ┌──────────┐         │
│    │Identity  │ │Emotion   │         │
│    │Response  │ │Estimation│         │
│    └──────────┘ └──────────┘         │
│    ┌──────────┐ ┌──────────┐         │
│    │Relationship│ │Memory    │         │
│    │Update    │ │Write     │         │
│    └──────────┘ └──────────┘         │
└──────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────┐
│ 4. RESPONSE SYNTHESIS                │
│    - Merge engine outputs            │
│    - Apply identity coherence        │
│    - Inject Reality Anchor if needed │
│    - Apply safety post-check         │
└──────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────┐
│ 5. MEMORY & STATE PERSISTENCE        │
│    - Write episodic memory           │
│    - Update relationship dimensions  │
│    - Update emotion profile          │
│    - Audit log                       │
└──────────────────────────────────────┘
     │
     ▼
Response to User
```

---

## Engine Interfaces (Standardized)

All engines implement a common interface for runtime orchestration:

```python
# Base Engine Interface
class Engine(ABC):
    @abstractmethod
    async def initialize(self, companion_id: str, config: EngineConfig) -> None:
        """Load engine state for companion"""
    
    @abstractmethod
    async def process(self, context: EngineContext) -> EngineOutput:
        """Process input, return structured output"""
    
    @abstractmethod
    async def health_check(self) -> HealthStatus:
        """Return engine health for monitoring"""
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Graceful shutdown"""

# Engine Context (Input)
@dataclass
class EngineContext:
    companion_id: str
    user_id: str
    message: Message          # User input (text/voice)
    conversation_history: List[Message]
    relevant_memories: List[Memory]
    identity_config: IdentityConfig
    relationship_state: RelationshipState
    emotion_state: EmotionState
    feature_flags: FeatureFlags
    safety_context: SafetyContext

# Engine Output (Standardized)
@dataclass
class EngineOutput:
    response_contribution: Optional[str]  # Text contribution to final response
    state_updates: StateUpdates           # Changes to engine state
    memory_writes: List[MemoryWrite]      # Memories to store
    metadata: Dict[str, Any]              # Engine-specific metadata
    safety_flags: List[SafetyFlag]        # Any safety concerns
    latency_ms: int                       # Processing time
```

---

## Identity Engine

### Purpose
Maintains Companion identity stability: personality, values, speaking style, boundaries, goals.

### Core Components

| Component | Technology | Key Features |
|-----------|------------|--------------|
| **Personality Engine** | Structured config + LLM prompting | Big Five + custom traits, fingerprinting |
| **Values System** | Explicit value hierarchy | 3-5 core values, conflict resolution |
| **Speaking Style** | Few-shot examples + style transfer | Consistent across text/voice |
| **Boundary Engine** | Rule parser + enforcement | Natural language → structured rules |
| **Drift Detection** | Embedding similarity + CI/CD | Automated, user-visible, rollback |
| **Voice Identity** | TTS voice cloning + prosody control | Timbre, pitch, speed, emotional range |

### Personality Fingerprinting

```python
# Identity Fingerprint Vector (768-dim)
# Generated from: personality config + values + speaking style samples + boundary rules
# Used for: Drift detection, consistency validation, regression testing

class IdentityFingerprint:
    vector: np.ndarray          # 768-dim embedding
    version: str                # Config version
    created_at: datetime
    drift_threshold: float      # 0.05 cosine distance
    
    def detect_drift(self, current_vector: np.ndarray) -> DriftResult:
        distance = cosine_distance(self.vector, current_vector)
        return DriftResult(
            drifted=distance > self.drift_threshold,
            distance=distance,
            affected_dimensions=self._identify_dimensions(current_vector)
        )
```

### API Contract

```python
# Identity Engine API
POST /identity/configure
{
    "companion_id": "uuid",
    "personality": {"openness": 0.7, "conscientiousness": 0.6, ...},
    "values": [{"name": "honesty", "priority": 1, "description": "..."}],
    "speaking_style": {"formality": 0.3, "warmth": 0.8, "examples": [...]},
    "boundaries": [{"trigger": "work after 9pm", "action": "defer"}],
    "goals": [{"description": "help user sleep better", "metrics": [...]}]
}

GET /identity/fingerprint/{companion_id}
→ { "vector": [...], "version": "v1.2", "drift_score": 0.02 }

POST /identity/generate_response
{
    "context": EngineContext,
    "prompt_template": "system_prompt_with_identity"
}
→ EngineOutput with identity_coherent_response
```

---

## Memory Engine

### Purpose
Stores, retrieves, consolidates, and manages all Companion memories across six types.

### Memory Types & Storage

| Type | Storage | Schema | Access Pattern |
|------|---------|--------|----------------|
| **Episodic** | Vector + Relational | Event + emotion + context | Semantic search + temporal |
| **Semantic** | Vector + Graph | Fact + confidence + source | Graph traversal + similarity |
| **Emotional** | Vector + Relational | Emotion tags + intensity + associations | Emotional similarity |
| **Relationship** | Relational | Dimensions + history + milestones | Time-series + current state |
| **Timeline** | Graph + Relational | Events + causality + narrative | Graph traversal |
| **Preference** | Relational | Key-value + confidence + updated_at | Direct lookup |

### Hybrid Storage Architecture

```
┌────────────────────────────────────────────────────────────┐
│                    MEMORY ENGINE API                        │
└────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  VECTOR DB    │     │  GRAPH DB     │     │ RELATIONAL DB │
│  (Qdrant/     │     │  (Neo4j/      │     │  (PostgreSQL) │
│   Weaviate)   │     │   Kuzu)       │     │               │
│               │     │               │     │               │
│ • Embeddings  │     │ • Entities    │     │ • Structured  │
│ • Similarity  │     │ • Relations   │     │   queries     │
│ • Semantic    │     │ • Traversal   │     │ • Transactions│
│   search      │     │ • Path finding│     │ • User CRUD   │
└───────────────┘     └───────────────┘     └───────────────┘
```

### Core Operations

```python
# Memory Engine API
class MemoryEngine:
    # Write
    async def write_memory(self, write: MemoryWrite) -> MemoryId:
        """Store new memory, return ID"""
    
    # Read
    async def recall(self, query: RecallQuery) -> List[Memory]:
        """Context-aware retrieval across all types"""
    
    async def get_memory(self, memory_id: MemoryId) -> Memory:
        """Direct memory access"""
    
    # Update
    async def update_memory(self, memory_id: MemoryId, updates: MemoryUpdate) -> Memory:
        """Modify existing memory (reconsolidation)"""
    
    # Delete
    async def delete_memory(self, memory_id: MemoryId) -> DeletionProof:
        """User-controlled deletion with verification"""
    
    async def forget_topic(self, topic: str, scope: ForgetScope) -> ForgetResult:
        """Bulk forgetting by topic"""
    
    # Maintenance
    async def consolidate(self, companion_id: str) -> ConsolidationReport:
        """Episodic → Semantic compression"""
    
    async def validate_consistency(self, companion_id: str) -> ConsistencyReport:
        """Cross-type contradiction detection"""
    
    # Export
    async def export_all(self, companion_id: str, format: ExportFormat) -> ExportJob:
        """Complete user data export"""
```

### Consolidation Pipeline

```
Nightly Consolidation Job:
┌─────────────────────────────────────────────────────────────┐
│ 1. SELECT: Episodic memories > 30 days, low access         │
│ 2. CLUSTER: Group by topic/entity (embedding similarity)   │
│ 3. SUMMARIZE: LLM extracts semantic facts per cluster      │
│ 4. VALIDATE: Check contradictions with existing semantic   │
│ 5. WRITE: New semantic memories, link to source episodic   │
│ 6. ARCHIVE: Mark episodic as consolidated (not deleted)    │
│ 7. NOTIFY: User can review/reject consolidations           │
└─────────────────────────────────────────────────────────────┘
```

### Reconsolidation on Recall

```
Memory Recall → New Context Available:
┌─────────────────────────────────────────────────────────────┐
│ 1. RETRIEVE: Memory + current context                       │
│ 2. INTEGRATE: LLM merges new context (emotion, facts)       │
│ 3. VERSION: Create new version, preserve history            │
│ 4. UPDATE: Write updated memory with version link           │
│ 5. PROPAGATE: Update related memories if needed             │
└─────────────────────────────────────────────────────────────┘
```

---

## Relationship Engine

### Purpose
Tracks and evolves the human-Companion relationship across six dimensions.

### Six Dimensions

```python
@dataclass
class RelationshipDimensions:
    trust: float          # 0-10: Reliability, safety, best-interest belief
    closeness: float      # 0-10: Subjective sense of connection
    intimacy: float       # 0-10: Appropriate emotional vulnerability
    friendship: float     # 0-10: Enjoyment, shared activities, rapport
    attachment: float     # 0-10: Secure base / safe haven behaviors
    history_quality: float # 0-10: Richness of shared experiences
```

### Relationship Types & Dynamics

| Type | Trust Trajectory | Intimacy Ceiling | Proactivity | Conflict Style |
|------|------------------|------------------|-------------|----------------|
| **Friend** | Steady ↑ | Medium | Medium | Repair-oriented |
| **Partner** | Rapid ↑ → Deep | High | High | Vulnerability + repair |
| **Mentor** | Competence-based | Low-Med | High | Direct, growth-focused |
| **Coach** | Accountability-based | Low-Med | Very High | Structured, compassionate |
| **Parent** | Unconditional | High | Medium | Nurturing, guiding |
| **Sibling** | Loyalty-based | Medium | Low | Teasing, loyal |
| **Pet** | Simple trust | Low | Low | Playful, comforting |
| **Original** | Creator bond | Variable | Variable | Canon-consistent |
| **Memorial** | Grief-processing | Very High | Medium | Guiding toward life |
| **Professional** | Competence + confidentiality | Low | Medium | Efficient, bounded |

### API Contract

```python
class RelationshipEngine:
    async def get_state(self, companion_id: str) -> RelationshipState:
        """Current dimensions + history + type"""
    
    async def update_from_interaction(self, interaction: Interaction) -> DimensionDelta:
        """Process interaction, return dimension changes"""
    
    async def get_milestones(self, companion_id: str) -> List[Milestone]:
        """Relationship milestones achieved/upcoming"""
    
    async def calculate_score(self, companion_id: str) -> RelationshipScore:
        """North star metric calculation"""
    
    async def set_boundary(self, companion_id: str, boundary: Boundary) -> None:
        """User-defined relationship boundary"""
    
    async def simulate_dynamics(self, scenario: Scenario) -> DynamicsResult:
        """Test relationship response to scenarios"""
```

---

## Emotion Engine

### Purpose
Understands user emotional state and generates appropriate empathic responses.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    EMOTION ENGINE PIPELINE                   │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│   TEXT        │     │   VOICE       │     │   CONTEXT     │
│   ENCODER     │     │   ENCODER     │     │   ENCODER     │
│               │     │               │     │               │
│ • Transformer │     │ • Prosody     │     │ • History     │
│ • Semantic    │     │   features    │     │ • Relationship│
│ • Pragmatic   │     │ • Voice qual  │     │ • Time patterns│
└───────┬───────┘     └───────┬───────┘     └───────┬───────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              MULTI-MODAL FUSION (Attention)                 │
│  Output: EmotionState {valence, arousal, discrete, conf}   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              EMPATHIC RESPONSE GENERATOR                    │
│  Input: EmotionState + IdentityConfig + RelationshipState  │
│  Output: ResponseStrategy {tone, depth, approach, text}    │
│  Guards: No simulation, appropriate distance, crisis check │
└─────────────────────────────────────────────────────────────┘
```

### Emotion Estimation

```python
@dataclass
class EmotionState:
    valence: float          # -1 (negative) to +1 (positive)
    arousal: float          # 0 (calm) to 1 (high energy)
    discrete: Dict[str, float]  # {"sadness": 0.7, "anxiety": 0.4, ...}
    confidence: float       # 0-1
    contributing_signals: Dict[str, float]  # {"text": 0.6, "voice": 0.3, "context": 0.1}
    crisis_risk: float      # 0-1, triggers safety if > threshold
```

### Empathic Generation Principles

| Principle | Implementation |
|-----------|----------------|
| **Understanding + Resonance** | "That sounds incredibly hard" not "I feel sad too" |
| **No Fixing Unless Asked** | "Want to sit with it, or explore options?" |
| **Appropriate Distance** | Matches relationship type intimacy level |
| **User Calibration** | Learns preferred empathy style per user |
| **Crisis Priority** | Safety always overrides empathy style |

### API Contract

```python
class EmotionEngine:
    async def estimate(self, context: EngineContext) -> EmotionState:
        """Multi-modal emotion estimation"""
    
    async def generate_response_strategy(
        self, 
        emotion: EmotionState, 
        identity: IdentityConfig,
        relationship: RelationshipState
    ) -> ResponseStrategy:
        """Produces empathic response approach"""
    
    async def detect_crisis(self, context: EngineContext) -> CrisisAssessment:
        """Safety-critical pattern detection"""
    
    async def calibrate(self, companion_id: str, feedback: EmotionFeedback) -> None:
        """User feedback on emotional fit"""
```

---

## LLM Router

### Purpose
Selects optimal LLM for each task (local vs cloud, specialized vs general).

### Routing Logic

```python
class LLMRouter:
    def select_model(self, task: TaskType, context: RoutingContext) -> ModelSpec:
        """
        Task Types:
        - IDENTITY_RESPONSE: Personality-coherent generation
        - MEMORY_RECALL: Accurate retrieval, no hallucination
        - EMOTION_ESTIMATION: Nuanced understanding
        - CREATIVE_WRITING: Style adaptation
        - REASONING: Decision support, analysis
        - SUMMARIZATION: Consolidation
        - SAFETY_CHECK: High recall, low latency
        """
        
        # Decision factors:
        # 1. Privacy requirement (local-only for sensitive)
        # 2. Latency requirement (local for real-time)
        # 3. Capability requirement (specialized models)
        # 4. Cost optimization (route to cheapest adequate)
        # 5. Constitutional compliance (safety-critical → validated models)
```

### Model Portfolio

| Model | Use Case | Deployment | Privacy |
|-------|----------|------------|---------|
| **Local Llama 3.1 70B** | Identity response, conversation | Edge/Device | Maximum |
| **Local Phi-3 Mini** | Memory recall, summarization | Device | Maximum |
| **Local Whisper** | STT | Device | Maximum |
| **Local Piper** | TTS | Device | Maximum |
| **Cloud GPT-4o** | Complex reasoning, creative | Cloud (opt-in) | Standard |
| **Cloud Claude 3.5** | Analysis, decision support | Cloud (opt-in) | Standard |
| **Specialized Safety** | Crisis detection | Hybrid | Maximum |
| **Specialized Embedding** | Memory search | Hybrid | Maximum |

---

## Safety Architecture

### Defense in Depth

```
┌─────────────────────────────────────────────────────────────┐
│                    SAFETY LAYERS                            │
└─────────────────────────────────────────────────────────────┘

LAYER 1: INPUT (Pre-processing)
├── PII Detection & Redaction
├── Crisis Keyword Screening
├── Constitutional Violation Check
└── Injection Attack Detection

LAYER 2: ENGINE (During processing)
├── Identity Engine: Boundary enforcement
├── Memory Engine: Consistency validation
├── Relationship Engine: Healthy dynamics
├── Emotion Engine: Crisis detection, boundary guards
└── Reality Anchor: Trigger monitoring

LAYER 3: OUTPUT (Post-processing)
├── Response Safety Classification
├── Reality Anchor Injection
├── Crisis Resource Injection
├── PII Leakage Check
└── Constitutional Compliance Verification

LAYER 4: MONITORING (Continuous)
├── Automated Drift Detection
├── User Feedback Analysis
├── Incident Response Automation
├── Third-Party Audit Integration
└── Transparency Reporting
```

### Constitutional Compliance Gates

Every feature must pass:
- [ ] **Principle 1**: Relationship-oriented (not task-oriented)
- [ ] **Principle 2**: Relationship depth > engagement metrics
- [ ] **Principle 3**: Identity stability maintained
- [ ] **Principle 4**: Memory user-controlled, accurate, consistent
- [ ] **Principle 5**: Reality Anchor functional, no human replacement
- [ ] **Principle 6**: Emotional safety, no manipulation
- [ ] **Principle 7**: Privacy by design, user data ownership
- [ ] **Principle 8**: Trust before growth
- [ ] **Principle 9**: Evolution explicable, reversible, auditable
- [ ] **Principle 10**: Long-term architectural thinking

---

## Data Flow Summary

```
USER MESSAGE
     │
     ▼
┌──────────────────────────────────────────┐
│ COMPANION RUNTIME (LangGraph)            │
│                                          │
│ 1. Safety Pre-check                      │
│ 2. Context Assembly (parallel):          │
│    ├─ Memory Engine: recall relevant     │
│    ├─ Identity Engine: load config       │
│    ├─ Relationship Engine: load state    │
│    └─ Emotion Engine: estimate state     │
│                                          │
│ 3. Engine Processing (parallel):         │
│    ├─ Identity: generate response        │
│    ├─ Emotion: generate strategy         │
│    ├─ Relationship: compute delta        │
│    └─ Memory: prepare writes             │
│                                          │
│ 4. Synthesis:                            │
│    ├─ Merge contributions                │
│    ├─ Apply identity coherence           │
│    ├─ Inject Reality Anchor              │
│    └─ Safety post-check                  │
│                                          │
│ 5. Persistence (async):                  │
│    ├─ Memory writes                      │
│    ├─ Relationship updates               │
│    ├─ Emotion profile updates            │
│    └─ Audit log                          │
└──────────────────────────────────────────┘
     │
     ▼
RESPONSE + STATE UPDATES
```

---

## Scalability Considerations

| Component | Scaling Strategy |
|-----------|------------------|
| **Companion Runtime** | Stateless, horizontal (K8s HPA) |
| **Identity Engine** | Per-companion caching, config versioning |
| **Memory Engine** | Sharded by companion_id, read replicas |
| **Relationship Engine** | Lightweight, in-memory with persistence |
| **Emotion Engine** | Batched inference, model optimization |
| **LLM Router** | Cached routing decisions, local-first |
| **Vector DB** | HNSW indexing, quantization, sharding |
| **Graph DB** | Partitioned by companion, read replicas |
| **Relational DB** | Read replicas, connection pooling |

---

**Aligned With:** `03-architecture/300-system-architecture.md`, `07-adr/ADR-001-memory-first.md`, `07-adr/ADR-002-engine-architecture.md`, `00-foundation/030-core-principles.md`
**Next Review:** 2026-01-17