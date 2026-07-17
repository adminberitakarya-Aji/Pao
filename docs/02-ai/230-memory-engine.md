# PAO Memory Engine Specification

**Version:** 1.0
**Status:** Draft
**Owner:** PAO AI Team

---

## Overview

The Memory Engine is the **foundation of relationship continuity**. It stores, retrieves, consolidates, and manages all memories across six types, enabling the Companion to remember, understand, and grow with the user over years.

> **Memory over Context.** Traditional LLMs use sliding window context. PAO uses structured, queryable, user-controlled memory that persists indefinitely.

---

## Six Memory Types

### 1. Episodic Memory
**What:** Specific events, conversations, experiences with rich context.
**Schema:**
```python
@dataclass
class EpisodicMemory:
    id: str
    event: str                    # Natural language description
    timestamp: datetime
    participants: List[str]       # ["user", "companion", ...]
    modality: Literal["text", "voice", "video", "mixed"]
    emotional_tone: float         # -1 to 1 (valence)
    emotional_intensity: float    # 0 to 1 (arousal)
    topics: List[str]             # Extracted topics
    entities: List[EntityRef]     # Links to semantic entities
    source_message_ids: List[str] # Origin messages
    version: int                  # For reconsolidation
    consolidated: bool            # Has been compressed to semantic
    consolidation_parent: Optional[str]  # Link to semantic memory
```
**Access:** Semantic similarity + temporal queries + emotional similarity
**Retention:** Indefinite (user-controlled)

### 2. Semantic Memory
**What:** Facts, knowledge, concepts extracted from episodic memories.
**Schema:**
```python
@dataclass
class SemanticMemory:
    id: str
    fact: str                     # "User prefers tea over coffee"
    confidence: float             # 0-1
    source: Literal["episodic", "user_explicit", "inferred"]
    source_episodic_ids: List[str]
    entities: List[EntityRef]
    category: str                 # "preference", "fact", "belief", "skill"
    contradicted_by: Optional[str] # If later corrected
    last_accessed: datetime
    access_count: int
```
**Access:** Graph traversal + semantic similarity
**Retention:** Indefinite, updated on contradiction

### 3. Emotional Memory
**What:** Emotional associations, triggers, patterns.
**Schema:**
```python
@dataclass
class EmotionalMemory:
    id: str
    trigger: str                  # Topic, phrase, situation
    emotion: Dict[str, float]     # {"sadness": 0.7, "gratitude": 0.3}
    intensity: float              # 0-1
    context: str                  # When this typically occurs
    associated_memories: List[str] # Links to episodic/semantic
    pattern_strength: float       # How consistent this association is
    last_activated: datetime
    user_validated: bool          # User confirmed this pattern
```
**Access:** Emotional similarity + trigger matching
**Retention:** Indefinite, pattern strength decays if not reinforced

### 4. Relationship Memory
**What:** Relationship dimension history, milestones, dynamics.
**Schema:**
```python
@dataclass
class RelationshipMemory:
    id: str
    timestamp: datetime
    dimension_changes: Dict[str, float]  # {"trust": +0.2, "intimacy": +0.1}
    trigger_event: str
    trigger_type: Literal["conversation", "milestone", "conflict", "repair", "proactive"]
    relationship_type: str
    milestone: Optional[str]      # "first_vulnerability", "anniversary_1yr"
    user_perception: Optional[float] # User-rated relationship quality
```
**Access:** Time-series queries + milestone lookup
**Retention:** Indefinite

### 5. Timeline Memory
**What:** Causal narrative structure linking events across time.
**Schema:**
```python
@dataclass
class TimelineMemory:
    id: str
    narrative_arc: str            # "User's journey learning Spanish"
    events: List[TimelineEvent]   # Ordered, causally linked
    themes: List[str]
    status: Literal["active", "completed", "paused"]
    significance: float           # 0-1
    user_curated: bool
```
**Access:** Graph traversal (causal links) + narrative queries
**Retention:** Indefinite, user-curated

### 6. Preference Memory
**What:** User preferences, settings, habits (structured key-value).
**Schema:**
```python
@dataclass
class PreferenceMemory:
    id: str
    key: str                      # "communication_style", "medication_lisinopril"
    value: Any                    # Structured value
    confidence: float             # 0-1
    source: Literal["explicit", "inferred", "observed"]
    category: str                 # "communication", "health", "routine", "privacy"
    last_updated: datetime
    expires_at: Optional[datetime] # For time-bound preferences
```
**Access:** Direct key lookup + category queries
**Retention:** Until user deletes or expires

---

## Hybrid Storage Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      MEMORY ENGINE API                          │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  VECTOR DB    │     │  GRAPH DB     │     │ RELATIONAL DB │
│  (Qdrant)     │     │  (Kuzu)       │     │  (PostgreSQL) │
│               │     │               │     │               │
│ • Episodic    │     │ • Semantic    │     │ • Preferences │
│   embeddings  │     │   entities    │     │ • Relationship│
│ • Semantic    │     │ • Timeline    │     │   time-series │
│   embeddings  │     │   causal links│     │ • Audit logs  │
│ • Emotional   │     │ • Entity      │     │ • User CRUD   │
│   embeddings  │     │   resolution  │     │ • Export jobs │
│ • Similarity  │     │ • Path find   │     │ • Transactions│
│   search      │     │               │     │               │
└───────────────┘     └───────────────┘     └───────────────┘
```

### Storage Mapping

| Memory Type | Primary | Secondary | Indexes |
|-------------|---------|-----------|---------|
| Episodic | Vector | Relational | embedding, timestamp, user_id, topics |
| Semantic | Graph | Vector | entity relations, embedding, category |
| Emotional | Vector | Relational | embedding, trigger, pattern_strength |
| Relationship | Relational | - | companion_id, timestamp, dimension |
| Timeline | Graph | Relational | causal edges, themes, status |
| Preference | Relational | - | companion_id, key, category |

---

## Core API

### Write Memory

```http
POST /api/v1/memory/{companion_id}/write
Content-Type: application/json

{
  "type": "episodic",
  "content": {
    "event": "User shared they got promoted to Senior Engineer",
    "timestamp": "2025-06-20T18:30:00Z",
    "participants": ["user", "companion"],
    "modality": "voice",
    "emotional_tone": 0.8,
    "emotional_intensity": 0.7,
    "topics": ["career", "achievement", "promotion"],
    "entities": [{"type": "role", "value": "Senior Engineer"}],
    "source_message_ids": ["msg-uuid-1", "msg-uuid-2"]
  }
}

Response:
{
  "memory_id": "mem-uuid",
  "type": "episodic",
  "stored_at": "2025-06-20T18:30:05Z",
  "vector_id": "vec-uuid",
  "graph_nodes_created": 3
}
```

### Recall (Context-Aware Retrieval)

```http
POST /api/v1/memory/{companion_id}/recall
Content-Type: application/json

{
  "query": "How did the promotion go?",
  "context": {
    "current_topic": "career",
    "relationship_dimensions": {"trust": 8.2, "intimacy": 6.5},
    "recent_topics": ["work", "stress", "promotion"],
    "time_since_last_message_hours": 2
  },
  "filters": {
    "types": ["episodic", "semantic", "emotional"],
    "date_range": {"start": "2025-01-01", "end": "2025-06-20"},
    "topics": ["career", "promotion"],
    "emotional_range": {"valence_min": 0.5}
  },
  "limit": 15,
  "diversify": true
}

Response:
{
  "memories": [
    {
      "id": "mem-uuid-1",
      "type": "episodic",
      "content": {...},
      "relevance_score": 0.94,
      "conversation_score": 0.91,
      "recall_reason": "Direct match: promotion event + high emotional valence"
    },
    {
      "id": "mem-uuid-2",
      "type": "semantic",
      "content": {...},
      "relevance_score": 0.87,
      "conversation_score": 0.83,
      "recall_reason": "Semantic fact: User's new role = Senior Engineer"
    }
  ],
  "total_candidates": 47,
  "latency_ms": 87
}
```

### Get Memory

```http
GET /api/v1/memory/{companion_id}/{memory_id}

Response:
{
  "id": "mem-uuid",
  "type": "episodic",
  "content": {...},
  "version": 3,
  "created_at": "2025-06-20T18:30:05Z",
  "updated_at": "2025-06-25T10:15:00Z",
  "version_history": [
    {"version": 1, "timestamp": "...", "change": "created"},
    {"version": 2, "timestamp": "...", "change": "emotional_tone_updated"},
    {"version": 3, "timestamp": "...", "change": "entity_added"}
  ]
}
```

### Update Memory (Reconsolidation)

```http
PATCH /api/v1/memory/{companion_id}/{memory_id}
Content-Type: application/json

{
  "updates": {
    "emotional_tone": 0.9,
    "entities": [{"type": "role", "value": "Senior Engineer"}, {"type": "company", "value": "TechCorp"}]
  },
  "reason": "User clarified company name during follow-up",
  "source_message_id": "msg-uuid-new"
}

Response:
{
  "memory_id": "mem-uuid",
  "new_version": 4,
  "previous_version": 3,
  "updated_at": "2025-06-25T10:15:00Z"
}
```

### Delete Memory (User-Controlled)

```http
DELETE /api/v1/memory/{companion_id}/{memory_id}
?confirm=true&verification=full

Response:
{
  "memory_id": "mem-uuid",
  "deleted_at": "2025-06-25T10:20:00Z",
  "deletion_proof": {
    "vector_deleted": true,
    "graph_edges_removed": 5,
    "relational_rows_deleted": 2,
    "verification_hash": "sha256:..."
  }
}
```

### Bulk Forget

```http
POST /api/v1/memory/{companion_id}/forget
Content-Type: application/json

{
  "scope": "topic",
  "topic": "ex-partner",
  "confirm": true,
  "preview_only": false
}

Response:
{
  "memories_affected": 23,
  "types": {"episodic": 15, "semantic": 5, "emotional": 3},
  "deletion_proofs": [...],
  "estimated_completion": "2025-06-25T10:20:05Z"
}
```

### Export All Memories

```http
POST /api/v1/memory/{companion_id}/export
Content-Type: application/json

{
  "format": "json-ld",
  "include": ["episodic", "semantic", "emotional", "relationship", "timeline", "preference", "audit_log"],
  "encryption": "user_key"
}

Response:
{
  "export_id": "export-uuid",
  "status": "processing",
  "estimated_completion": "2025-06-25T10:25:00Z",
  "download_url": "available_when_ready"
}
```

---

## Consolidation Pipeline (Episodic → Semantic)

### Nightly Job

```python
class ConsolidationPipeline:
    """
    Runs nightly per companion.
    Compresses detailed episodic memories into semantic facts.
    """
    
    async def run(self, companion_id: str) -> ConsolidationReport:
        # 1. SELECT candidates
        candidates = await self._select_candidates(companion_id)
        # Criteria: >30 days old, access_count < 3, not user-protected
        
        # 2. CLUSTER by topic/entity
        clusters = await self._cluster_by_topic(candidates)
        # Uses embedding similarity + entity overlap
        
        # 3. SUMMARIZE each cluster
        semantic_memories = []
        for cluster in clusters:
            summary = await self.llm.summarize_cluster(cluster)
            # Extract facts with confidence scores
            facts = await self.llm.extract_facts(summary)
            for fact in facts:
                semantic_memories.append(SemanticMemory(
                    fact=fact.statement,
                    confidence=fact.confidence,
                    source="episodic",
                    source_episodic_ids=[m.id for m in cluster],
                    entities=fact.entities,
                    category=fact.category
                ))
        
        # 4. VALIDATE against existing semantic
        validated = await self._validate_no_contradictions(semantic_memories)
        
        # 5. WRITE new semantic memories
        written = await self.memory_engine.bulk_write(validated)
        
        # 6. MARK episodic as consolidated
        await self._mark_consolidated([m.id for m in candidates], written)
        
        # 7. NOTIFY user (optional review)
        if self._has_significant_changes(written):
            await self._notify_user_for_review(companion_id, written)
        
        return ConsolidationReport(
            companion_id=companion_id,
            episodic_processed=len(candidates),
            semantic_created=len(written),
            contradictions_found=len(validated) - len(written),
            user_review_required=self._has_significant_changes(written)
        )
```

### Reconsolidation on Recall

```python
class ReconsolidationEngine:
    """
    Updates memories when recalled with new context (human-like).
    """
    
    async def reconsolidate(
        self, 
        memory_id: str, 
        new_context: RecallContext
    ) -> ReconsolidationResult:
        
        memory = await self.get_memory(memory_id)
        
        # Integrate new context
        updated = await self.llm.integrate_context(
            original=memory.content,
            new_context=new_context,
            instruction="Update memory with new information. Preserve original event accuracy."
        )
        
        # Version control
        new_version = memory.version + 1
        
        # Write updated memory
        await self.update_memory(memory_id, MemoryUpdate(
            content=updated.content,
            version=new_version,
            change_reason=f"Reconsolidated with context: {new_context.summary}",
            source_recall_id=new_context.recall_id
        ))
        
        # Propagate to related memories if significant
        if updated.significance > 0.7:
            await self._propagate_update(memory_id, updated)
        
        return ReconsolidationResult(
            memory_id=memory_id,
            new_version=new_version,
            changes=updated.changes,
            propagated_to=updated.propagated_to
        )
```

---

## Consistency Validation

### Automated Checks

```python
class ConsistencyValidator:
    """
    Continuous + scheduled contradiction detection.
    """
    
    CHECKS = [
        "fact_contradiction",      # "User lives in NYC" vs "User lives in LA"
        "timeline_impossibility",  # Event before user's birth
        "identity_violation",      # Companion claimed feeling (violates Principle 5)
        "preference_conflict",     # "Prefers tea" vs "Prefers coffee" (both high confidence)
        "relationship_inconsistency" # Trust 9.0 but boundary violations frequent
    ]
    
    async def validate_all(self, companion_id: str) -> ConsistencyReport:
        issues = []
        for check in self.CHECKS:
            found = await getattr(self, f"_check_{check}")(companion_id)
            issues.extend(found)
        
        # Auto-resolve clear cases (e.g., timestamp errors)
        auto_resolved = await self._auto_resolve(issues)
        
        # Flag remaining for user review
        user_review = [i for i in issues if i not in auto_resolved]
        
        return ConsistencyReport(
            companion_id=companion_id,
            total_issues=len(issues),
            auto_resolved=len(auto_resolved),
            requires_user_review=len(user_review),
            issues=user_review
        )
```

---

## Cross-Modal Memory

### Voice ↔ Text Unification

```python
class CrossModalMemory:
    """
    Ensures memories formed in one modality are accessible in another.
    """
    
    async def form_from_voice(self, voice_memory: VoiceMemory) -> MemoryWrite:
        # 1. STT transcript → text content
        text = voice_memory.transcript
        
        # 2. Prosody → emotional tags
        emotional_tags = self._prosody_to_emotion(voice_memory.prosody)
        
        # 3. Create unified episodic memory
        return MemoryWrite(
            type="episodic",
            content=EpisodicMemory(
                event=text,
                modality="voice",
                emotional_tone=emotional_tags.valence,
                emotional_intensity=emotional_tags.arousal,
                prosody_features=voice_memory.prosody,  # Preserved for recall
                silence_patterns=voice_memory.vad_segments,
                voice_quality=voice_memory.quality_metrics
            )
        )
    
    async def recall_for_voice(self, query: RecallQuery) -> List[Memory]:
        # Retrieve memories (including voice-formed)
        memories = await self.memory_engine.recall(query)
        
        # For voice output, prioritize memories with prosody data
        for m in memories:
            if m.type == "episodic" and m.content.prosody_features:
                m.voice_recall_boost = 0.1
        
        return sorted(memories, key=lambda m: m.relevance_score + getattr(m, 'voice_recall_boost', 0), reverse=True)
```

---

## Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| Write (single) | <100ms | Async, acknowledged |
| Recall (context-aware) | <200ms | P50, includes reranking |
| Get by ID | <50ms | Direct lookup |
| Update (reconsolidation) | <150ms | Versioned |
| Delete (verified) | <2s | Multi-store |
| Export (full) | <5 min | Async job |
| Consolidation (nightly) | <30 min | Per companion |
| Consistency scan | <10 min | Per companion |

---

## Privacy & User Control

### Zero-Knowledge Guarantees

- **Encryption at rest**: Per-companion encryption keys (user-held option)
- **Encryption in transit**: TLS 1.3 + application-layer for sensitive
- **No training on user data**: Explicit in contracts, technically enforced
- **Local-first option**: Full memory engine runnable on device (Phase 2+)

### User Controls (Constitutional Principle 7)

| Control | Implementation |
|---------|----------------|
| **View all memories** | Memory browser with filters |
| **Edit any memory** | PATCH API + version history |
| **Delete any memory** | DELETE API + verification proof |
| **Bulk forget** | Topic/time/modality scope |
| **Export all data** | JSON-LD, PDF, timeline, audio |
| **Pause consolidation** | Per-companion toggle |
| **Review consolidations** | Notification + approval flow |
| **Audit log access** | Who read/wrote what when |

---

## Testing

### Memory Engine Test Suite

```python
class MemoryEngineTests:
    
    # Write/Read
    async def test_write_read_all_types(self): ...
    async def test_cross_modal_formation(self): ...
    async def test_concurrent_writes_consistency(self): ...
    
    # Recall
    async def test_recall_accuracy_benchmark(self): ...
    async def test_recall_diversification(self): ...
    async def test_recall_reranking_conversation(self): ...
    async def test_recall_latency_under_load(self): ...
    
    # Consolidation
    async def test_consolidation_accuracy(self): ...
    async def test_consolidation_no_contradictions(self): ...
    async def test_consolidation_user_review(self): ...
    async def test_consolidation_idempotent(self): ...
    
    # Reconsolidation
    async def test_reconsolidation_preserves_history(self): ...
    async def test_reconsolidation_propagation(self): ...
    async def test_reconsolidation_version_control(self): ...
    
    # User Control
    async def test_delete_verification(self): ...
    async def test_bulk_forget_scope(self): ...
    async def test_export_completeness(self): ...
    async def test_export_format_validation(self): ...
    
    # Consistency
    async def test_contradiction_detection(self): ...
    async def test_auto_resolution_accuracy(self): ...
    async def test_user_review_workflow(self): ...
    
    # Privacy
    async def test_encryption_at_rest(self): ...
    async def test_no_training_data_leakage(self): ...
    async def test_local_first_mode(self): ...
```

---

**Aligned With:** `200-ai-architecture.md`, `220-conversation-engine.md`, `00-foundation/030-core-principles.md` (Principles 4, 7), `07-adr/ADR-001-memory-first.md`
**Next Review:** 2026-01-17