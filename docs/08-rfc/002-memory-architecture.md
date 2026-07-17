# RFC-002: Memory Architecture & Consolidation

**Status:** Accepted
**Date:** 2025-01-15
**Authors:** Head of AI, Memory Engine Lead, Data Platform Lead
**Reviewers:** CTO, VP Engineering, Privacy Lead, Security Lead

---

## Abstract

This RFC defines PAO's memory architecture — a multi-tier, privacy-preserving memory system enabling companions to remember, learn, and evolve across months and years of interaction while maintaining user control and regulatory compliance.

---

## 1. Requirements

### Functional
- **Long-term retention**: Memories accessible for years
- **Semantic search**: "What did we discuss about my mom last year?"
- **Episodic recall**: "Remember that Tuesday I got promoted?"
- **Proactive retrieval**: Companion surfaces relevant memories unprompted
- **Memory editing**: User can correct, delete, or annotate memories
- **Consolidation**: Short-term → long-term with importance weighting

### Non-Functional
- **Latency**: P99 < 50ms for recall, < 200ms for consolidation
- **Scale**: 1B+ memories, 10M companions, 100k QPS
- **Privacy**: No raw text in vector DB, encryption at rest, user-controlled deletion
- **Consistency**: Eventual (memory) / Strong (user edits)
- **Cost**: < $0.001 per companion/month

---

## 2. Memory Taxonomy

### 2.1 Memory Types

```
┌─────────────────────────────────────────────────────────────────┐
│                    MEMORY HIERARCHY                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  WORKING MEMORY (Seconds–Minutes)                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Current conversation context (last 50 turns)         │   │
│  │ • Active goals, temporary facts                        │   │
│  │ • In-context only, not persisted                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼ Consolidation                    │
│  EPISODIC MEMORY (Hours–Days)                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Specific events with temporal context                │   │
│  │ • "We talked about Paris trip on Tuesday"              │   │
│  │ • Rich metadata: time, participants, emotion, modality │   │
│  │ • TTL: 30 days → promoted or decayed                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼ Consolidation                    │
│  SEMANTIC MEMORY (Months–Years)                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Abstracted knowledge, facts, concepts                │   │
│  │ • "User loves Paris, speaks French, fears flying"      │   │
│  │ • Entity-relationship graph (Kuzu)                     │   │
│  │ • Permanent unless explicitly deleted                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼ Abstraction                      │
│  PROCEDURAL MEMORY (Continuous)                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Skills, habits, interaction patterns                 │   │
│  │ • "User prefers brief responses, morning check-ins"    │   │
│  │ • Embedded in companion personality weights            │   │
│  │ • Updated via RLHF from interaction feedback           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Memory Schema

```protobuf
// memory/v1/memory.proto
syntax = "proto3";
package pao.memory.v1;

message Memory {
  // Identity
  string memory_id = 1;           // UUID v7
  string companion_id = 2;
  string user_id = 3;
  
  // Classification
  MemoryType type = 4;            // EPISODIC, SEMANTIC, PROCEDURAL
  MemoryTier tier = 5;            // WORKING, SHORT_TERM, LONG_TERM
  
  // Content (encrypted at rest)
  bytes encrypted_content = 6;    // AES-256-GCM, key per companion
  string content_hash = 7;        // SHA-256 for deduplication
  
  // Semantic representation
  float vector[1536] = 8;         // Embedding (text-embedding-3-large)
  repeated Entity entities = 9;   // Extracted entities
  
  // Metadata
  google.protobuf.Timestamp created_at = 10;
  google.protobuf.Timestamp occurred_at = 11;  // When event happened
  float importance = 12;          // 0.0-1.0 (consolidation priority)
  float emotional_valence = 13;   // -1.0 to 1.0
  float arousal = 14;             // 0.0-1.0
  
  // Relationships
  repeated string related_memory_ids = 15;
  repeated string conversation_ids = 16;
  
  // Lifecycle
  int32 access_count = 17;
  google.protobuf.Timestamp last_accessed = 18;
  float decay_factor = 19;        // For forgetting curve
  bool user_pinned = 20;          // User protected from decay
  bool user_deleted = 21;         // Soft delete flag
  
  // Provenance
  string source = 22;             // CONVERSATION, PROACTIVE, IMPORT, INFERRED
  float confidence = 23;          // 0.0-1.0
}

enum MemoryType {
  MEMORY_TYPE_UNSPECIFIED = 0;
  MEMORY_TYPE_EPISODIC = 1;
  MEMORY_TYPE_SEMANTIC = 2;
  MEMORY_TYPE_PROCEDURAL = 3;
}

enum MemoryTier {
  MEMORY_TIER_UNSPECIFIED = 0;
  MEMORY_TIER_WORKING = 1;
  MEMORY_TIER_SHORT_TERM = 2;
  MEMORY_TIER_LONG_TERM = 3;
}

message Entity {
  string id = 1;                  // UUID
  string type = 2;                // PERSON, PLACE, EVENT, TOPIC, CONCEPT
  string name = 3;
  float salience = 4;             // 0.0-1.0
  map<string, string> properties = 5;
}
```

---

## 3. Storage Architecture

### 3.1 Polyglot Persistence

| Tier | Primary Store | Purpose | Retention |
|------|---------------|---------|-----------|
| **Working** | Redis (in-context) | Conversation context | Session only |
| **Episodic** | Qdrant (vector) + PostgreSQL (metadata) | Rich event memories | 30 days → promote |
| **Semantic** | Kuzu (graph) + Qdrant (vector) | Knowledge graph | Permanent |
| **Procedural** | Companion weights (model) | Behavioral patterns | Continuous |

### 3.2 Qdrant Collections (Vector Search)

```yaml
collections:
  episodic_memories:
    vectors:
      size: 1536
      distance: Cosine
      hnsw_config:
        m: 16
        ef_construct: 128
    payload_schema:
      companion_id: keyword (indexed)
      user_id: keyword (indexed)
      occurred_at: datetime (indexed)
      importance: float (indexed)
      type: keyword (indexed)
      entities: keyword (indexed)
    sharding:
      shard_key: companion_id
      shards: 10
    replication: 2
    
  semantic_memories:
    vectors:
      size: 1536
      distance: Cosine
    payload_schema:
      companion_id: keyword
      entity_ids: keyword
      concepts: keyword
      confidence: float
    sharding:
      shard_key: companion_id
      shards: 5
```

### 3.3 Kuzu Graph Schema (Semantic Memory)

```cypher
// Nodes
CREATE NODE TABLE Companion (id STRING, user_id STRING, PRIMARY KEY (id));
CREATE NODE TABLE User (id STRING, PRIMARY KEY (id));
CREATE NODE TABLE Entity (
  id STRING, 
  type STRING,  // PERSON, PLACE, TOPIC, CONCEPT, EVENT
  name STRING,
  properties MAP(STRING, STRING),
  embedding FLOAT[1536],
  PRIMARY KEY (id)
);
CREATE NODE TABLE Memory (
  id STRING,
  companion_id STRING,
  type STRING,  // EPISODIC, SEMANTIC
  importance DOUBLE,
  occurred_at TIMESTAMP,
  PRIMARY KEY (id)
);

// Relationships
CREATE REL TABLE KNOWS (FROM Companion TO User, since TIMESTAMP);
CREATE REL TABLE MENTIONS (FROM Memory TO Entity, salience DOUBLE);
CREATE REL TABLE RELATES (FROM Memory TO Memory, relation_type STRING, strength DOUBLE);
CREATE REL TABLE ABOUT (FROM Entity TO Entity, relation STRING);  // "Paris" -LOCATED_IN-> "France"
CREATE REL TABLE PREFERS (FROM Companion TO Entity, strength DOUBLE);  // Learned preferences
```

---

## 4. Consolidation Pipeline

### 4.1 Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CONSOLIDATION PIPELINE                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  CONVERSATION END                                                   │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────┐                                               │
│  │  EXTRACTION     │  LLM + NER → Entities, facts, commitments    │
│  │  (Real-time)    │  Output: Raw episodic memories               │
│  └────────┬────────┘                                               │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────┐                                               │
│  │  ENCODING       │  Embedding (text-embedding-3-large)          │
│  │  (Async)        │  Store in Qdrant (episodic) + PG (metadata)  │
│  └────────┬────────┘                                               │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────┐     ┌─────────────────┐                      │
│  │  DAILY BATCH    │     │  WEEKLY BATCH   │                      │
│  │  (02:00 UTC)    │     │  (Mon 03:00)    │                      │
│  └────────┬────────┘     └────────┬────────┘                      │
│       │                          │                                │
│       ▼                          ▼                                │
│  ┌─────────────────┐     ┌─────────────────┐                      │
│  │  PROMOTION      │     │  ABSTRACTION    │                      │
│  │  Episodic →     │     │  Cluster →      │                      │
│  │  Semantic       │     │  Semantic facts │                      │
│  │  (importance    │     │  Graph update   │                      │
│  │   > 0.7)        │     │  (Kuzu)         │                      │
│  └─────────────────┘     └─────────────────┘                      │
│       │                          │                                │
│       ▼                          ▼                                │
│  ┌─────────────────────────────────────────┐                      │
│  │           DECAY & FORGETTING            │                      │
│  │  - Ebbinghaus curve (importance-weighted)│                     │
│  │  - User-pinned memories never decay     │                      │
│  │  - Soft delete → hard delete after 90d  │                      │
│  └─────────────────────────────────────────┘                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Promotion Criteria (Episodic → Semantic)

```python
# memory/consolidation/promotion.py

PROMOTION_THRESHOLDS = {
    "importance": 0.7,
    "access_count": 3,           # Accessed 3+ times
    "age_days": 7,               # At least 1 week old
    "entity_overlap": 0.5,       # Shares entities with other memories
}

async def evaluate_promotion(memory: Memory) -> PromotionDecision:
    signals = {
        "importance": memory.importance,
        "access_frequency": memory.access_count / max(1, memory.age_days),
        "entity_connectivity": await graph.degree(memory.entity_ids),
        "user_pinned": memory.user_pinned,
        "emotional_intensity": abs(memory.emotional_valence) * memory.arousal,
    }
    
    # Weighted score
    score = (
        0.4 * signals["importance"] +
        0.2 * min(signals["access_frequency"], 1.0) +
        0.2 * min(signals["entity_connectivity"] / 10, 1.0) +
        0.1 * signals["emotional_intensity"] +
        0.1 * (1.0 if signals["user_pinned"] else 0.0)
    )
    
    return PromotionDecision(
        promote=score > 0.7,
        confidence=score,
        reason="high_importance" if signals["importance"] > 0.8 else "frequent_access"
    )
```

### 4.3 Abstraction (Episodic Cluster → Semantic Fact)

```python
# memory/consolidation/abstraction.py

async def abstract_episodic_cluster(
    memories: List[Memory], 
    companion_id: str
) -> List[SemanticFact]:
    """
    Cluster related episodic memories and extract semantic facts.
    Uses LLM with structured output for reliable extraction.
    """
    
    # 1. Cluster by entity overlap + temporal proximity
    clusters = await cluster_memories(memories, eps=0.3, min_samples=3)
    
    semantic_facts = []
    
    for cluster in clusters:
        # 2. Prepare context for LLM
        context = format_cluster_for_llm(cluster)
        
        # 3. Extract structured facts
        prompt = f"""
        Analyze these related memories and extract 1-3 stable semantic facts.
        Focus on: preferences, traits, relationships, beliefs, goals.
        Output JSON: {{"facts": [{{"subject": "", "predicate": "", "object": "", 
        "confidence": 0.0, "evidence_ids": []}}]}}
        
        Memories: {context}
        """
        
        response = await llm_client.structured_complete(
            prompt, 
            schema=SemanticFactSchema,
            temperature=0.1
        )
        
        for fact in response.facts:
            # 4. Validate against existing knowledge graph
            if await kg.is_consistent(fact, companion_id):
                semantic_facts.append(fact)
    
    return semantic_facts
```

### 4.4 Forgetting Curve (Decay)

```python
# memory/consolidation/decay.py

import math

class ForgettingCurve:
    """
    Ebbinghaus-inspired decay with importance modulation.
    P(recall) = exp(-t / (S * I))
    where S = base stability, I = importance factor
    """
    
    BASE_HALF_LIFE_DAYS = 30  # Memory with importance=0.5 halves in 30 days
    
    @classmethod
    def retention_probability(cls, memory: Memory, days_elapsed: float) -> float:
        if memory.user_pinned:
            return 1.0
        
        if memory.user_deleted:
            return 0.0
        
        # Importance modulates stability: 0.1→5x faster decay, 1.0→5x slower
        importance_factor = 0.2 + 0.8 * memory.importance  # 0.2 to 1.0
        stability = cls.BASE_HALF_LIFE_DAYS * importance_factor * (1 + memory.access_count * 0.1)
        
        # Exponential decay
        return math.exp(-days_elapsed / stability)
    
    @classmethod
    def should_decay(cls, memory: Memory) -> bool:
        prob = cls.retention_probability(memory, memory.age_days)
        return prob < 0.1  # < 10% recall probability
    
    @classmethod
    def decay_factor(cls, memory: Memory) -> float:
        """Multiplier for importance (used in retrieval ranking)"""
        return cls.retention_probability(memory, memory.age_days)
```

---

## 5. Retrieval & Ranking

### 5.1 Hybrid Search

```python
# memory/retrieval/hybrid.py

class HybridMemoryRetriever:
    """
    Combines vector similarity + graph traversal + recency + importance
    """
    
    async def retrieve(
        self, 
        query: str, 
        companion_id: str,
        k: int = 10,
        filters: RetrievalFilters = None
    ) -> List[RetrievedMemory]:
        
        # 1. Generate query embedding
        query_vec = await embedder.encode(query)
        
        # 2. Vector search (Qdrant)
        vector_results = await qdrant.search(
            collection="episodic_memories",
            query_vector=query_vec,
            filter=build_qdrant_filter(companion_id, filters),
            limit=k * 3,  # Oversample for reranking
            with_payload=True
        )
        
        # 3. Graph expansion (Kuzu) - find related entities
        entity_ids = extract_entities(vector_results)
        graph_results = await kuzu.traverse(
            start_entities=entity_ids,
            max_hops=2,
            relation_types=["MENTIONS", "RELATES", "ABOUT"],
            limit=k
        )
        
        # 4. Combine & rerank
        candidates = merge_results(vector_results, graph_results)
        
        # 5. Score with hybrid ranking
        scored = []
        for mem in candidates:
            score = self._hybrid_score(mem, query_vec, companion_id)
            scored.append((score, mem))
        
        # 6. Diversify (MMR)
        final = maximal_marginal_relevance(scored, k, lambda_param=0.7)
        
        return [mem for _, mem in final]
    
    def _hybrid_score(self, mem: Memory, query_vec: List[float], companion_id: str) -> float:
        # Vector similarity (0-1)
        vec_sim = cosine_similarity(mem.vector, query_vec)
        
        # Recency decay (0-1)
        recency = math.exp(-mem.age_days / 30)
        
        # Importance (0-1)
        importance = mem.importance
        
        # Access frequency (0-1, log scaled)
        access = min(math.log1p(mem.access_count) / 5, 1.0)
        
        # User pin bonus
        pin_bonus = 0.2 if mem.user_pinned else 0.0
        
        # Weighted combination
        return (
            0.45 * vec_sim +
            0.20 * recency +
            0.20 * importance +
            0.10 * access +
            0.05 * pin_bonus
        )
```

### 5.2 Proactive Retrieval

```python
# memory/retrieval/proactive.py

class ProactiveMemoryRetriever:
    """
    Surfaces relevant memories without explicit query.
    Triggered by: conversation context, time, events, emotions.
    """
    
    TRIGGERS = {
        "anniversary": {"days_before": 3, "event_types": ["BIRTHDAY", "ANNIVERSARY", "MILESTONE"]},
        "topic_continuity": {"window_turns": 5, "similarity_threshold": 0.6},
        "emotional_resonance": {"valence_threshold": 0.7, "arousal_threshold": 0.6},
        "goal_relevance": {"active_goals": True},
        "temporal_pattern": {"same_time_of_day": True, "same_day_of_week": True},
    }
    
    async def get_proactive_memories(
        self, 
        context: ConversationContext,
        companion_id: str
    ) -> List[ProactiveMemory]:
        candidates = []
        
        # 1. Anniversary / temporal triggers
        if context.current_time:
            anniversaries = await self._find_anniversaries(companion_id, context.current_time)
            candidates.extend(anniversaries)
        
        # 2. Topic continuity (what are we talking about now?)
        if context.recent_topics:
            topic_memories = await self._find_by_topics(companion_id, context.recent_topics)
            candidates.extend(topic_memories)
        
        # 3. Emotional resonance
        if context.user_emotional_state:
            emotional_memories = await self._find_emotional_resonance(
                companion_id, context.user_emotional_state
            )
            candidates.extend(emotional_memories)
        
        # 4. Rank by surprise + relevance
        ranked = self._rank_proactive(candidates, context)
        
        # 5. Limit to 1 per conversation turn, max 3 per session
        return ranked[:min(3, len(ranked))]
    
    def _rank_proactive(self, memories: List[Memory], context: ConversationContext) -> List[Memory]:
        scored = []
        for mem in memories:
            # Surprise: inverse of recent access
            surprise = 1.0 / (1.0 + mem.recent_access_count)
            
            # Relevance to current context
            relevance = self._context_relevance(mem, context)
            
            # Emotional match
            emotional_match = 1.0 - abs(mem.emotional_valence - context.user_emotional_state.valence)
            
            score = 0.4 * surprise + 0.4 * relevance + 0.2 * emotional_match
            scored.append((score, mem))
        
        return [mem for _, mem in sorted(scored, reverse=True)]
```

---

## 6. Privacy & User Control

### 6.1 Encryption

```yaml
# Per-companion encryption keys
Key Hierarchy:
  Root Key (HSM) 
    → Service Key (per environment, rotated 90d)
      → Companion Key (per companion, never rotated, derived)
        → Memory Key (per memory, derived from companion key + memory_id)

Encryption:
  Algorithm: AES-256-GCM
  Key Derivation: HKDF-SHA256
  Nonce: 96-bit random per encryption
  AAD: companion_id || memory_id || version
```

### 6.2 User Controls

| Control | Implementation | API |
|---------|----------------|-----|
| **View memories** | Decrypt + return | `GET /v1/companions/{id}/memories` |
| **Edit memory** | Re-encrypt updated content | `PATCH /v1/memories/{id}` |
| **Delete memory** | Soft delete (user_deleted=true) | `DELETE /v1/memories/{id}` |
| **Pin memory** | user_pinned=true (no decay) | `POST /v1/memories/{id}/pin` |
| **Export all** | Streaming decrypt + JSON | `GET /v1/companions/{id}/memories/export` |
| **Bulk delete** | By date range, topic, type | `POST /v1/companions/{id}/memories/bulk-delete` |
| **Opt-out consolidation** | Disable promotion for companion | `PATCH /v1/companions/{id}/memory-settings` |

### 6.3 Right to be Forgotten

```python
# memory/privacy/deletion.py

async def hard_delete_user_data(user_id: str, companion_id: str = None):
    """
    GDPR Art 17 compliance: Complete erasure within 30 days.
    """
    # 1. Mark all memories user_deleted (immediate)
    await db.execute("""
        UPDATE memories SET user_deleted = true, deleted_at = NOW()
        WHERE user_id = $1 AND (companion_id = $2 OR $2 IS NULL)
    """, user_id, companion_id)
    
    # 2. Remove from vector indices (async, within 1 hour)
    await qdrant.delete(
        collection="episodic_memories",
        filter={"user_id": user_id}
    )
    await qdrant.delete(
        collection="semantic_memories", 
        filter={"user_id": user_id}
    )
    
    # 3. Remove from graph (async)
    await kuzu.execute("""
        MATCH (m:Memory) WHERE m.user_id = $user_id
        DETACH DELETE m
    """, user_id=user_id)
    
    # 4. Delete encryption keys (after 30-day grace)
    await schedule_key_deletion(user_id, delay_days=30)
    
    # 5. Confirm deletion
    return DeletionCertificate(
        user_id=user_id,
        companion_id=companion_id,
        deleted_at=datetime.utcnow(),
        verification_hash=await compute_deletion_hash(user_id)
    )
```

---

## 7. Evaluation & Quality

### 7.1 Retrieval Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Recall@10** | > 0.85 | Human-labeled query sets |
| **Precision@5** | > 0.75 | User feedback (thumbs up/down) |
| **Latency P99** | < 50ms | Production tracing |
| **Freshness** | < 1 hour | New memory → searchable |
| **Diversity** | > 0.7 | MMR pairwise distance |

### 7.2 Consolidation Quality

| Metric | Target | Method |
|--------|--------|--------|
| **Promotion precision** | > 0.8 | Human review of promoted memories |
| **Abstraction accuracy** | > 0.9 | Fact verification against source |
| **Decay appropriateness** | > 0.85 | User "I remember this" signals |
| **Graph consistency** | 0 contradictions | Automated constraint checking |

---

## 8. Open Questions

1. **Cross-companion memory sharing**: Family plan memory pooling?
2. **Multimodal memories**: Images, voice clips, documents?
3. **Memory inheritance**: Transfer memories to new companion?
4. **Collaborative filtering**: "Users like you also remembered..."?
5. **External knowledge grounding**: Link memories to Wikipedia, calendars?

---

## 9. Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Head of AI | | | |
| Memory Engine Lead | | | |
| Data Platform Lead | | | |
| CTO | | | |
| VP Engineering | | | |
| Privacy Lead | | | |
| Security Lead | | | |

---

## 10. References

- [Ebbinghaus Forgetting Curve](https://en.wikipedia.org/wiki/Forgetting_curve)
- [Hybrid Search (Vector + Graph)](https://arxiv.org/abs/2304.14207)
- [Memory Consolidation in AI](https://arxiv.org/abs/2305.17250)
- [Differential Privacy for Embeddings](https://arxiv.org/abs/2203.00233)
- [Qdrant Performance Guide](https://qdrant.tech/documentation/guides/performance-optimization/)

---

**Next Review:** April 15, 2025 (Quarterly)
**Document Owner:** Head of AI / Memory Engine Lead