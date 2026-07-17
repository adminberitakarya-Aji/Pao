# PAO Data Model Specification

**Version:** 1.0
**Status:** Draft
**Owner:** PAO Architecture Team

---

## Overview

This document defines the canonical data models for PAO, covering all entities, relationships, and constraints across the polyglot persistence layer (PostgreSQL, Qdrant, Kuzu, Redis, Kafka).

> **Data Principle:** User data is sacred. Every model enforces privacy, ownership, and auditability by design.

---

## PostgreSQL Models (Relational)

### Core Tables

```sql
-- ==================== USERS ====================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email CITEXT NOT NULL UNIQUE,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    name VARCHAR(255),
    avatar_url TEXT,
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    locale VARCHAR(10) NOT NULL DEFAULT 'en',
    password_hash TEXT,  -- Null if OAuth only
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    -- Encryption
    encryption_key_id VARCHAR(100),  -- References Vault key
    -- Preferences (JSONB for flexibility)
    preferences JSONB NOT NULL DEFAULT '{}',
    -- Metadata
    metadata JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_deleted_at ON users(deleted_at) WHERE deleted_at IS NOT NULL;

-- ==================== COMPANIONS ====================
CREATE TABLE companions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,  -- friend, partner, mentor, coach, parent, sibling, memorial, professional, custom
    description TEXT,
    avatar_url TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    archived_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_interaction_at TIMESTAMPTZ,
    -- Configuration (JSONB)
    identity_config JSONB NOT NULL DEFAULT '{}',
    voice_config JSONB NOT NULL DEFAULT '{}',
    proactive_config JSONB NOT NULL DEFAULT '{}',
    safety_config JSONB NOT NULL DEFAULT '{}',
    -- Encryption
    encryption_key_id VARCHAR(100) NOT NULL,  -- Per-companion key
    -- Metadata
    metadata JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_companions_user_id ON companions(user_id);
CREATE INDEX idx_companions_is_active ON companions(user_id, is_active) WHERE is_active = TRUE;
CREATE INDEX idx_companions_last_interaction ON companions(last_interaction_at DESC);

-- ==================== SUBSCRIPTIONS ====================
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan VARCHAR(50) NOT NULL,  -- free, pro, premium, legacy
    status VARCHAR(50) NOT NULL,  -- active, past_due, canceled, trialing, incomplete
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    current_period_start TIMESTAMPTZ NOT NULL,
    current_period_end TIMESTAMPTZ NOT NULL,
    cancel_at_period_end BOOLEAN NOT NULL DEFAULT FALSE,
    trial_end TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_subscriptions_user_id ON subscriptions(user_id) WHERE status IN ('active', 'trialing', 'past_due');
CREATE INDEX idx_subscriptions_stripe_customer ON subscriptions(stripe_customer_id);

-- ==================== MEMORIES (Structured + Audit) ====================
CREATE TABLE memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    companion_id UUID NOT NULL REFERENCES companions(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,  -- episodic, semantic, emotional, relationship, timeline, preference
    version INT NOT NULL DEFAULT 1,
    consolidated BOOLEAN NOT NULL DEFAULT FALSE,
    consolidation_parent_id UUID REFERENCES memories(id),
    source_message_ids UUID[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    -- Structured fields (type-specific, nullable)
    -- Episodic
    event TEXT,
    timestamp TIMESTAMPTZ,
    participants TEXT[],
    modality VARCHAR(20),
    emotional_tone REAL,  -- -1 to 1
    emotional_intensity REAL,  -- 0 to 1
    topics TEXT[],
    -- Semantic
    fact TEXT,
    confidence REAL,  -- 0 to 1
    source VARCHAR(20),  -- episodic, user_explicit, inferred
    category VARCHAR(50),
    contradicted_by UUID REFERENCES memories(id),
    last_accessed TIMESTAMPTZ,
    access_count INT NOT NULL DEFAULT 0,
    -- Emotional
    trigger TEXT,
    emotion JSONB,
    intensity REAL,
    context TEXT,
    associated_memories UUID[],
    pattern_strength REAL,
    last_activated TIMESTAMPTZ,
    user_validated BOOLEAN DEFAULT FALSE,
    -- Relationship
    dimension_changes JSONB,
    trigger_event TEXT,
    trigger_type VARCHAR(20),
    milestone VARCHAR(100),
    user_perception REAL,
    -- Timeline
    narrative_arc TEXT,
    events JSONB,
    themes TEXT[],
    status VARCHAR(20),
    significance REAL,
    user_curated BOOLEAN DEFAULT FALSE,
    -- Preference
    key VARCHAR(255),
    value JSONB,
    expires_at TIMESTAMPTZ,
    -- Encryption
    encrypted_fields TEXT[],  -- Which fields are encrypted
    -- Vector/Graph references
    vector_id VARCHAR(100),  -- Qdrant point ID
    graph_node_ids UUID[],   -- Kuzu node IDs
    -- Metadata
    metadata JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_memories_companion_id ON memories(companion_id);
CREATE INDEX idx_memories_type ON memories(companion_id, type);
CREATE INDEX idx_memories_timestamp ON memories(companion_id, timestamp DESC) WHERE timestamp IS NOT NULL;
CREATE INDEX idx_memories_consolidated ON memories(companion_id, consolidated) WHERE consolidated = FALSE;
CREATE INDEX idx_memories_deleted_at ON memories(deleted_at) WHERE deleted_at IS NOT NULL;
CREATE INDEX idx_memories_topics ON memories USING GIN(topics);
CREATE INDEX idx_memories_key ON memories(companion_id, key) WHERE key IS NOT NULL;

-- Memory version history
CREATE TABLE memory_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    version INT NOT NULL,
    content JSONB NOT NULL,  -- Full snapshot
    change_reason TEXT,
    changed_by VARCHAR(50),  -- user, system, consolidation, reconsolidation
    source_message_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_memory_versions_memory_id ON memory_versions(memory_id, version DESC);

-- ==================== CONVERSATIONS ====================
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    companion_id UUID NOT NULL REFERENCES companions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- user, companion, system
    content TEXT NOT NULL,
    modality VARCHAR(20) NOT NULL DEFAULT 'text',
    emotion JSONB,  -- EmotionState
    memory_references UUID[] NOT NULL DEFAULT '{}',
    proactive BOOLEAN NOT NULL DEFAULT FALSE,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_messages_companion_id ON messages(companion_id, created_at DESC);
CREATE INDEX idx_messages_proactive ON messages(companion_id, proactive) WHERE proactive = TRUE;

-- ==================== RELATIONSHIP ====================
CREATE TABLE relationship_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    companion_id UUID NOT NULL UNIQUE REFERENCES companions(id) ON DELETE CASCADE,
    phase VARCHAR(20) NOT NULL DEFAULT 'forming',  -- forming, building, deepening, anchored, legacy
    trust REAL NOT NULL DEFAULT 0,       -- 0-10
    closeness REAL NOT NULL DEFAULT 0,   -- 0-10
    intimacy REAL NOT NULL DEFAULT 0,    -- 0-10
    friendship REAL NOT NULL DEFAULT 0,  -- 0-10
    attachment REAL NOT NULL DEFAULT 0,  -- 0-10
    history_quality REAL NOT NULL DEFAULT 0,  -- 0-10
    score REAL NOT NULL DEFAULT 0,       -- Composite RHI
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Dimension history (time-series)
CREATE TABLE dimension_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    companion_id UUID NOT NULL REFERENCES companions(id) ON DELETE CASCADE,
    dimension VARCHAR(20) NOT NULL,  -- trust, closeness, intimacy, friendship, attachment, history_quality
    value REAL NOT NULL,
    trigger_event TEXT,
    trigger_type VARCHAR(50),
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_dimension_history_companion ON dimension_history(companion_id, dimension, created_at DESC);

-- Milestones
CREATE TABLE milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    companion_id UUID NOT NULL REFERENCES companions(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    achieved_at TIMESTAMPTZ,
    weight INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_milestones_companion ON milestones(companion_id, achieved_at DESC);

-- Shared Diary
CREATE TABLE diary_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    companion_id UUID NOT NULL REFERENCES companions(id) ON DELETE CASCADE,
    date TIMESTAMPTZ NOT NULL,
    user_text TEXT NOT NULL,
    companion_reflection TEXT,
    tags TEXT[],
    emotional_tone REAL,
    linked_memories UUID[],
    visibility VARCHAR(20) NOT NULL DEFAULT 'private',  -- private, shared, legacy
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_diary_entries_companion ON diary_entries(companion_id, date DESC);

-- ==================== PROACTIVE ====================
CREATE TABLE proactive_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    companion_id UUID NOT NULL REFERENCES companions(id) ON DELETE CASCADE,
    trigger_type VARCHAR(50) NOT NULL,
    trigger_category VARCHAR(50) NOT NULL,
    trigger_data JSONB NOT NULL DEFAULT '{}',
    explanation TEXT NOT NULL,
    content TEXT NOT NULL,
    modality VARCHAR(20) NOT NULL DEFAULT 'text',
    suggested_actions JSONB NOT NULL DEFAULT '[]',
    dismissible BOOLEAN NOT NULL DEFAULT TRUE,
    snooze_options TEXT[] NOT NULL DEFAULT '{"1h", "4h", "tomorrow", "never_this_topic"}',
    feedback_options TEXT[] NOT NULL DEFAULT '{"helpful", "not_now", "not_relevant", "too_much"}',
    relevance_score REAL NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, sent, dismissed, snoozed, feedback_given
    sent_at TIMESTAMPTZ,
    user_feedback JSONB,  -- {rating, comment, timestamp}
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_proactive_companion ON proactive_messages(companion_id, created_at DESC);
CREATE INDEX idx_proactive_status ON proactive_messages(companion_id, status) WHERE status = 'pending';

-- ==================== SAFETY ====================
CREATE TABLE safety_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    companion_id UUID NOT NULL REFERENCES companions(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    trigger TEXT NOT NULL,
    risk_level VARCHAR(20) NOT NULL,  -- low, medium, high, critical
    action_taken TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_safety_events_companion ON safety_events(companion_id, created_at DESC);
CREATE INDEX idx_safety_events_type ON safety_events(type, created_at DESC);

-- Interventions
CREATE TABLE interventions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    companion_id UUID NOT NULL REFERENCES companions(id) ON DELETE CASCADE,
    level INT NOT NULL,  -- 0=monitor, 1=nudge, 2=explicit, 3=restriction, 4=crisis
    trigger_event_id UUID REFERENCES safety_events(id),
    reason TEXT NOT NULL,
    actions JSONB NOT NULL DEFAULT '[]',
    user_acknowledged BOOLEAN NOT NULL DEFAULT FALSE,
    acknowledged_at TIMESTAMPTZ,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE INDEX idx_interventions_companion ON interventions(companion_id, active, created_at DESC);

-- Appeals
CREATE TABLE appeals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    companion_id UUID NOT NULL REFERENCES companions(id) ON DELETE CASCADE,
    intervention_id UUID REFERENCES interventions(id),
    reason TEXT NOT NULL,
    requested_action TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'under_review',  -- under_review, approved, denied, partial
    reviewer_id UUID,  -- Human reviewer
    resolution TEXT,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==================== EXPORTS ====================
CREATE TABLE export_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    companion_id UUID NOT NULL REFERENCES companions(id) ON DELETE CASCADE,
    format VARCHAR(20) NOT NULL,  -- json_ld, pdf, timeline, audio, markdown
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, processing, completed, failed, expired
    include_types TEXT[] NOT NULL DEFAULT '{}',
    encryption VARCHAR(20) NOT NULL DEFAULT 'none',  -- none, user_key, pao_key
    encryption_key_hash VARCHAR(64),  -- SHA256 of user key
    download_url TEXT,
    expires_at TIMESTAMPTZ,
    progress REAL NOT NULL DEFAULT 0,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_export_jobs_companion ON export_jobs(companion_id, created_at DESC);

-- ==================== AUDIT LOG (Immutable) ====================
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,
    companion_id UUID REFERENCES companions(id),
    user_id UUID REFERENCES users(id),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    details JSONB NOT NULL DEFAULT '{}',
    risk_level VARCHAR(20),
    action_taken TEXT,
    -- Cryptographic chain
    previous_hash VARCHAR(64),
    hash VARCHAR(64) NOT NULL
);

CREATE INDEX idx_audit_log_companion ON audit_log(companion_id, timestamp DESC);
CREATE INDEX idx_audit_log_user ON audit_log(user_id, timestamp DESC);
CREATE INDEX idx_audit_log_event_type ON audit_log(event_type, timestamp DESC);

-- ==================== BOUNDARIES ====================
CREATE TABLE boundaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    companion_id UUID NOT NULL REFERENCES companions(id) ON DELETE CASCADE,
    trigger_type VARCHAR(20) NOT NULL,  -- topic, phrase, emotion, time, context
    trigger_pattern TEXT NOT NULL,
    action_type VARCHAR(20) NOT NULL,  -- refuse, reflect, redirect, transform, escalate
    action_parameters JSONB NOT NULL DEFAULT '{}',
    explanation TEXT NOT NULL,
    scope VARCHAR(20) NOT NULL DEFAULT 'conversation',  -- conversation, session, permanent
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

CREATE INDEX idx_boundaries_companion ON boundaries(companion_id, active) WHERE active = TRUE;

-- ==================== WEBHOOKS ====================
CREATE TABLE webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    secret_hash VARCHAR(64) NOT NULL,  -- SHA256(secret)
    events TEXT[] NOT NULL DEFAULT '{}',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    failure_count INT NOT NULL DEFAULT 0,
    last_failure_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_webhooks_user ON webhooks(user_id, active);

-- ==================== WEBHOOK DELIVERIES ====================
CREATE TABLE webhook_deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    webhook_id UUID NOT NULL REFERENCES webhooks(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(20) NOT NULL,  -- pending, delivered, failed
    response_code INT,
    response_body TEXT,
    attempts INT NOT NULL DEFAULT 0,
    next_retry_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    delivered_at TIMESTAMPTZ
);

CREATE INDEX idx_webhook_deliveries_webhook ON webhook_deliveries(webhook_id, created_at DESC);
CREATE INDEX idx_webhook_deliveries_retry ON webhook_deliveries(next_retry_at) WHERE status = 'pending' AND attempts < 5;
```

---

## Qdrant Models (Vector)

### Collections

```python
# Per-companion collections for tenant isolation
# Collection naming: companion_{companion_id}

COLLECTIONS = {
    "episodic": {
        "description": "Episodic memory embeddings",
        "vector_size": 768,  # text-embedding-3-large
        "distance": "Cosine",
        "hnsw_config": {
            "m": 16,
            "ef_construct": 100,
            "full_scan_threshold": 10000
        },
        "payload_schema": {
            "memory_id": "keyword",
            "companion_id": "keyword",
            "timestamp": "datetime",
            "topics": "keyword",
            "participants": "keyword",
            "modality": "keyword",
            "emotional_tone": "float",
            "emotional_intensity": "float",
            "consolidated": "bool",
            "version": "integer"
        },
        "quantization": {
            "scalar": {
                "type": "int8",
                "quantile": 0.99,
                "always_ram": True
            }
        }
    },
    "semantic": {
        "description": "Semantic memory embeddings",
        "vector_size": 768,
        "distance": "Cosine",
        "hnsw_config": {
            "m": 16,
            "ef_construct": 100
        },
        "payload_schema": {
            "memory_id": "keyword",
            "companion_id": "keyword",
            "category": "keyword",
            "confidence": "float",
            "source": "keyword",
            "entities": "keyword",
            "contradicted_by": "keyword",
            "last_accessed": "datetime",
            "access_count": "integer"
        }
    },
    "emotional": {
        "description": "Emotional memory embeddings",
        "vector_size": 768,
        "distance": "Cosine",
        "payload_schema": {
            "memory_id": "keyword",
            "companion_id": "keyword",
            "trigger": "text",
            "emotion": "keyword",  # dominant emotion
            "intensity": "float",
            "pattern_strength": "float",
            "last_activated": "datetime",
            "user_validated": "bool"
        }
    },
    "voice_timbre": {
        "description": "Voice embeddings for timbre lock",
        "vector_size": 512,  # Speaker embedding dimension
        "distance": "Cosine",
        "payload_schema": {
            "companion_id": "keyword",
            "profile_version": "integer",
            "created_at": "datetime"
        }
    }
}
```

### Point Structure

```json
{
  "id": "uuid-point-id",
  "vector": [0.1, -0.2, ...],  // 768-dim embedding
  "payload": {
    "memory_id": "memory-uuid",
    "companion_id": "companion-uuid",
    "timestamp": "2025-06-20T18:30:00Z",
    "topics": ["career", "promotion", "achievement"],
    "participants": ["user", "companion"],
    "modality": "voice",
    "emotional_tone": 0.8,
    "emotional_intensity": 0.7,
    "consolidated": false,
    "version": 1
  }
}
```

---

## Kuzu Models (Graph)

### Schema

```cypher
-- ==================== NODES ====================

-- Semantic Entities
CREATE NODE TABLE Entity (
    id UUID PRIMARY KEY,
    companion_id UUID,
    type STRING,        -- person, place, organization, concept, role, event
    value STRING,       -- Normalized value
    display_name STRING, -- Human-readable
    confidence DOUBLE,
    source_memory_id UUID,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX ON Entity(companion_id);
CREATE INDEX ON Entity(companion_id, type);
CREATE INDEX ON Entity(companion_id, value);

-- Timeline Events
CREATE NODE TABLE TimelineEvent (
    id UUID PRIMARY KEY,
    companion_id UUID,
    memory_id UUID,
    timestamp TIMESTAMP,
    description STRING,
    significance DOUBLE,
    themes STRING[],
    status STRING,  -- active, completed, paused
    created_at TIMESTAMP
);

CREATE INDEX ON TimelineEvent(companion_id);
CREATE INDEX ON TimelineEvent(companion_id, timestamp);

-- Memory Nodes (for graph traversal)
CREATE NODE TABLE MemoryNode (
    id UUID PRIMARY KEY,
    companion_id UUID,
    type STRING,  -- episodic, semantic, emotional, relationship, timeline
    created_at TIMESTAMP
);

-- ==================== RELATIONSHIPS ====================

-- Entity Relations (Semantic Graph)
CREATE REL TABLE EntityRelation (
    FROM Entity TO Entity,
    relation_type STRING,  -- is_a, part_of, related_to, caused_by, located_in, works_for, knows
    confidence DOUBLE,
    source_memory_id UUID,
    created_at TIMESTAMP
);

CREATE INDEX ON EntityRelation(FROM, relation_type);
CREATE INDEX ON EntityRelation(TO, relation_type);

-- Causal Links (Timeline)
CREATE REL TABLE CausalLink (
    FROM TimelineEvent TO TimelineEvent,
    link_type STRING,  -- caused, enabled, prevented, followed, paralleled
    strength DOUBLE,
    description STRING,
    created_at TIMESTAMP
);

-- Memory Connections
CREATE REL TABLE MemoryConnection (
    FROM MemoryNode TO MemoryNode,
    connection_type STRING,  -- references, contradicts, consolidates, triggers, resurfaces
    strength DOUBLE,
    created_at TIMESTAMP
);

-- Entity to Memory (Which memories mention which entities)
CREATE REL TABLE EntityMemory (
    FROM Entity TO MemoryNode,
    mention_context STRING,  -- subject, object, context
    created_at TIMESTAMP
);

-- ==================== FUNCTIONS ====================

-- Find entities by type
FUNCTION find_entities_by_type(companion_id UUID, type STRING) RETURNS TABLE (
    id UUID, value STRING, display_name STRING, confidence DOUBLE
) AS 
    MATCH (e:Entity) 
    WHERE e.companion_id = companion_id AND e.type = type 
    RETURN e.id, e.value, e.display_name, e.confidence;

-- Get causal chain for event
FUNCTION get_causal_chain(event_id UUID, direction STRING, max_depth INT) RETURNS TABLE (
    path STRING, events UUID[], link_types STRING[]
) AS
    MATCH path = (start:TimelineEvent {id: event_id}) 
    -[r:CausalLink*1..max_depth]-> (end:TimelineEvent)
    WHERE direction = 'forward'
    RETURN path, nodes(path).id, relationships(path).link_type
    UNION
    MATCH path = (start:TimelineEvent) 
    -[r:CausalLink*1..max_depth]-> (end:TimelineEvent {id: event_id})
    WHERE direction = 'backward'
    RETURN path, nodes(path).id, relationships(path).link_type;

-- Find related memories via entities
FUNCTION find_memories_by_entity(companion_id UUID, entity_value STRING, limit INT) RETURNS TABLE (
    memory_id UUID, memory_type STRING, connection_type STRING, strength DOUBLE
) AS
    MATCH (e:Entity {companion_id: companion_id, value: entity_value}) 
    -[em:EntityMemory]-> (m:MemoryNode)
    RETURN m.id, m.type, em.mention_context, em.confidence
    ORDER BY em.confidence DESC
    LIMIT limit;
```

---

## Redis Models (Cache/Session)

### Key Patterns

```redis
# Session State (TTL: 24h)
session:{session_id} = {
  "user_id": "uuid",
  "companion_id": "uuid",
  "created_at": "timestamp",
  "last_activity": "timestamp",
  "context": {
    "active_topics": ["topic1", "topic2"],
    "recent_messages": ["msg_id1", "msg_id2"],
    "emotional_state": {...}
  }
}

# Conversation Context (TTL: 1h)
conversation:{companion_id}:context = {
  "recent_messages": [...],
  "active_topics": [...],
  "emotional_state": {...},
  "relationship_snapshot": {...},
  "relevant_memories": [...]
}

# Rate Limiting (TTL: window)
ratelimit:{scope}:{identifier} = count  # Increment with INCR, EXPIRE on first set

# Feature Flags (TTL: 5m, refreshed)
featureflags:{user_id} = {
  "new_voice_engine": true,
  "proactive_v2": false,
  "memory_consolidation_beta": true
}

# Presence (TTL: 30s, refreshed on heartbeat)
presence:{user_id}:{companion_id} = "online|away|busy"

# Voice Call State (TTL: call duration + 5m)
voicecall:{call_id} = {
  "companion_id": "uuid",
  "user_id": "uuid",
  "status": "connecting|active|paused|ended",
  "started_at": "timestamp",
  "webrtc_state": {...}
}

# Pub/Sub Channels
CHANNELS = {
    "companion:{companion_id}:events": "Real-time events for companion",
    "user:{user_id}:notifications": "Cross-companion notifications",
    "system:alerts": "System-wide alerts",
    "safety:crisis": "Crisis detection alerts"
}
```

---

## Kafka Models (Event Stream)

### Topics

```yaml
topics:
  # Memory Events
  - name: memory.written
    partitions: 100
    retention: 7d
    key: companion_id
    schema:
      type: object
      properties:
        event_id: {type: string, format: uuid}
        companion_id: {type: string, format: uuid}
        memory_id: {type: string, format: uuid}
        memory_type: {type: string, enum: [episodic, semantic, emotional, relationship, timeline, preference]}
        timestamp: {type: string, format: date-time}
        content_hash: {type: string}
        
  - name: memory.consolidated
    partitions: 50
    retention: 30d
    key: companion_id
    
  - name: memory.recalled
    partitions: 50
    retention: 3d
    key: companion_id

  # Relationship Events
  - name: relationship.dimension_changed
    partitions: 50
    retention: 90d
    key: companion_id
    schema:
      type: object
      properties:
        companion_id: {type: string, format: uuid}
        dimension: {type: string}
        old_value: {type: number}
        new_value: {type: number}
        trigger: {type: string}
        timestamp: {type: string, format: date-time}
        
  - name: relationship.milestone_achieved
    partitions: 20
    retention: 365d
    key: companion_id

  - name: relationship.phase_transition
    partitions: 20
    retention: 365d
    key: companion_id

  # Proactive Events
  - name: proactive.generated
    partitions: 50
    retention: 30d
    key: companion_id
    
  - name: proactive.sent
    partitions: 50
    retention: 30d
    key: companion_id
    
  - name: proactive.feedback
    partitions: 20
    retention: 90d
    key: companion_id

  # Safety Events
  - name: safety.crisis_detected
    partitions: 10
    retention: 365d
    key: companion_id
    config:
      min.insync.replicas: 2
      
  - name: safety.intervention_applied
    partitions: 10
    retention: 365d
    key: companion_id
    
  - name: safety.guard_triggered
    partitions: 10
    retention: 90d
    key: companion_id

  # Evaluation Events
  - name: evaluation.heuristic_failure
    partitions: 20
    retention: 30d
    key: companion_id
    
  - name: evaluation.human_completed
    partitions: 10
    retention: 90d
    key: companion_id

  # Voice Events
  - name: voice.call_started
    partitions: 20
    retention: 7d
    key: companion_id
    
  - name: voice.call_ended
    partitions: 20
    retention: 30d
    key: companion_id

  # Audit Events (Immutable, long retention)
  - name: audit.events
    partitions: 50
    retention: 2555d  # 7 years
    key: companion_id
    config:
      min.insync.replicas: 2
      cleanup.policy: compact

  # Export Events
  - name: export.started
    partitions: 10
    retention: 7d
    key: companion_id
    
  - name: export.completed
    partitions: 10
    retention: 7d
    key: companion_id
```

### Event Envelope

```json
{
  "event_id": "uuid",
  "event_type": "memory.written",
  "timestamp": "2025-06-25T10:30:00.123Z",
  "source_service": "memory-engine",
  "correlation_id": "uuid",  // For tracing across services
  "causation_id": "uuid",    // Event that caused this
  "payload": { /* Topic-specific payload */ },
  "metadata": {
    "schema_version": "1.0",
    "deployment_id": "uuid"
  }
}
```

---

## Data Flow Invariants

### Consistency Guarantees

| Operation | Consistency Level | Mechanism |
|-----------|-------------------|-----------|
| Memory Write | Strong (PostgreSQL) → Eventual (Vector/Graph) | Dual-write with Kafka reconciliation |
| Memory Recall | Eventual | Read from Vector/Graph, verify with PostgreSQL |
| Relationship Update | Strong | PostgreSQL transaction |
| Proactive Generation | Eventual | Async via Kafka |
| Safety Check | Strong | Synchronous in request path |
| Voice Call | Strong (Signaling) / Best-effort (Media) | WebRTC + Redis state |
| Export | Eventual | Async job with status polling |

### Reconciliation Jobs

```python
RECONCILIATION_JOBS = {
    "vector_postgres_sync": {
        "schedule": "*/15 * * * *",  # Every 15 min
        "description": "Ensure all PostgreSQL memories have vector embeddings",
        "action": "Find memories without vector_id, generate embedding, write to Qdrant"
    },
    "graph_postgres_sync": {
        "schedule": "*/30 * * * *",
        "description": "Ensure entity graph matches semantic memories",
        "action": "Extract entities from new semantic memories, upsert to Kuzu"
    },
    "dimension_aggregation": {
        "schedule": "0 * * * *",  # Hourly
        "description": "Aggregate dimension history for trends",
        "action": "Compute 7d/30d/90d trends, update relationship_states"
    },
    "audit_chain_verification": {
        "schedule": "0 3 * * *",  # Daily 3 AM
        "description": "Verify audit log cryptographic chain",
        "action": "Recompute hashes from genesis, alert on mismatch"
    },
    "orphaned_vector_cleanup": {
        "schedule": "0 4 * * 0",  # Weekly Sunday 4 AM
        "description": "Remove vectors for deleted memories",
        "action": "Find vectors where memory_id not in PostgreSQL (or deleted), delete"
    }
}
```

---

## Migration Strategy

### Versioning

```sql
-- Migration naming: V{version}_{description}.sql
-- Example: V1.2.0_add_proactive_feedback.sql

-- Always include:
-- 1. Up migration
-- 2. Down migration (for rollback)
-- 3. Data migration if needed
-- 4. Index creation (CONCURRENTLY for production)
-- 5. Constraint validation
```

### Example Migration

```sql
-- V1.1.0_add_voice_timbre_verification.sql
BEGIN;

-- Add column
ALTER TABLE companions ADD COLUMN voice_consistency_score REAL;
ALTER TABLE companions ADD COLUMN last_voice_verification TIMESTAMPTZ;

-- Add index
CREATE INDEX CONCURRENTLY idx_companions_voice_consistency 
ON companions(voice_consistency_score) 
WHERE voice_consistency_score IS NOT NULL;

-- Backfill for existing companions
UPDATE companions 
SET voice_consistency_score = 1.0, 
    last_voice_verification = created_at
WHERE voice_consistency_score IS NULL;

COMMIT;

-- Down migration
-- ALTER TABLE companions DROP COLUMN voice_consistency_score;
-- ALTER TABLE companions DROP COLUMN last_voice_verification;
```

---

## Privacy & Compliance

### Data Classification

| Classification | Tables/Fields | Retention | Encryption | Access |
|----------------|---------------|-----------|------------|--------|
| **PII** | users.email, users.name, companions.name | Account lifetime + 30d | Field-level + At-rest | Need-to-know |
| **Sensitive** | memories.content (health, financial, intimate), safety_events | Relationship lifetime + 1y | Field-level + At-rest + User-key option | User + Safety team |
| **Behavioral** | messages, proactive_messages, dimension_history | Relationship lifetime | At-rest | User + Product analytics (aggregated) |
| **Audit** | audit_log, safety_events, interventions | 7 years (legal) | At-rest + Immutable | Compliance + Legal |
| **Analytics** | Aggregated metrics, experiment results | 2 years | At-rest | Product team |

### GDPR/CCPA Compliance

```python
# Right to Access (Export)
EXPORT_INCLUDES = [
    "user_profile",
    "companions",
    "all_memories",
    "conversations",
    "relationship_history",
    "proactive_history",
    "safety_events",
    "voice_recordings",
    "audit_log"
]

# Right to Deletion
DELETION_SCOPES = {
    "account": "All user data, all companions, all memories",
    "companion": "Single companion + all associated data",
    "topic": "Memories matching topic pattern",
    "time_range": "Memories within date range",
    "modality": "Voice recordings only"
}

# Right to Rectification
RECTIFIABLE_FIELDS = [
    "memories.content (user-visible fields)",
    "companion.identity_config",
    "relationship.dimensions (via reset)",
    "user.preferences"
]
```

---

## Testing

### Data Model Tests

```python
class DataModelTests:
    
    # PostgreSQL
    async def test_memory_crud_operations(self): ...
    async def test_memory_versioning(self): ...
    async def test_relationship_dimension_bounds(self): ...  # 0-10
    async def test_milestone_uniqueness(self): ...
    async def test_boundary_enforcement(self): ...
    async def test_audit_log_immutability(self): ...
    async def test_encryption_key_rotation(self): ...
    async def test_cascade_deletes(self): ...
    
    # Qdrant
    async def test_vector_upsert_search(self): ...
    async def test_payload_filtering(self): ...
    async def test_tenant_isolation(self): ...  # Per-companion collections
    async def test_quantization_accuracy(self): ...
    async def test_consistency_with_postgres(self): ...
    
    # Kuzu
    async def test_entity_resolution(self): ...
    async def test_causal_chain_traversal(self): ...
    async def test_graph_consistency(self): ...
    async def test_cypher_query_performance(self): ...
    
    # Redis
    async def test_session_management(self): ...
    async def test_rate_limiting_accuracy(self): ...
    async def test_pubsub_delivery(self): ...
    async def test_ttl_expiration(self): ...
    
    # Kafka
    async def test_event_ordering_per_companion(self): ...
    async def test_exactly_once_processing(self): ...
    async def test_schema_evolution_compatibility(self): ...
    async def test_reconciliation_job_correctness(self): ...
    
    # Privacy
    async def test_export_completeness(self): ...
    async def test_deletion_verification(self): ...
    async def test_field_level_encryption(self): ...
    async def test_user_key_encryption(self): ...
```

---

**Aligned With:** `300-system-architecture.md`, `310-api-specification.md`, `230-memory-engine.md`, `240-relationship-engine.md`, `06-legal/`
**Next Review:** 2026-01-17