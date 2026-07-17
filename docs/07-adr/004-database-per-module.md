# ADR-004: Database per Module (Polyglot Persistence)

**Status:** Accepted
**Date:** 2025-01-15
**Deciders:** CTO, VP Engineering, Data Platform Lead, Domain Leads
**Consulted:** All Engineering Leads, Security, Compliance

---

## Context

PAO's modular monolith architecture requires each domain module to own its data completely. Different domains have vastly different data access patterns, consistency requirements, and scaling characteristics.

### Domain Data Characteristics

| Module | Access Pattern | Consistency | Scale | Special Requirements |
|--------|---------------|-------------|-------|---------------------|
| **User/Auth** | PK lookups, range queries | Strong (ACID) | 10M rows | PII encryption, audit log |
| **Companion** | Document reads, JSON queries | Strong | 1M rows | Versioning, branching |
| **Memory** | Vector search, graph traversal | Eventual | 1B+ vectors | ANN, hybrid search |
| **Relationship/RHI** | Time-series, aggregations | Eventual | 100M events | Downsampling, rollups |
| **Conversation** | Append-only, streaming | Strong | 10B messages | Partitioning, TTL |
| **Proactive** | Scheduling, triggers | Eventual | 10M jobs | Cron, distributed locking |
| **Safety** | Real-time classification | Strong | 1M/day | Immutable audit, legal hold |
| **Billing** | Financial transactions | Strong (ACID) | 1M/month | Audit, reconciliation |

---

## Decision

**Each module owns its database(s) with technology chosen per access pattern. No shared databases.**

### Database Assignments

```
┌─────────────────────────────────────────────────────────────────────┐
│                      PAO DATA LAYER                                 │
├─────────────┬─────────────┬─────────────┬─────────────┬────────────┤
│  PostgreSQL │  PostgreSQL │   Qdrant    │   Kuzu      │  ClickHouse│
│  (Primary)  │  (Documents)│  (Vector)   │  (Graph)    │ (Analytics)│
├─────────────┼─────────────┼─────────────┼─────────────┼────────────┤
│ User/Auth   │ Companion   │ Memory      │ Relationship│ Analytics  │
│ Billing     │ Settings    │ Embeddings  │ Social      │ Events     │
│ Safety      │ Personality │ Semantic    │ Knowledge   │ Metrics    │
│ Audit       │ Config      │ Search      │ Graph       │ ML Features│
└─────────────┴─────────────┴─────────────┴─────────────┴────────────┘
         │           │             │             │             │
         └───────────┴─────────────┴─────────────┴─────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   Redis Cluster   │
                    │  (Cache, Sessions,│
                    │   Rate Limits,    │
                    │   Distributed     │
                    │   Locks, Pub/Sub) │
                    └───────────────────┘
```

### Module → Database Mapping

| Module | Primary DB | Secondary DB | Rationale |
|--------|------------|--------------|-----------|
| **User/Auth** | PostgreSQL | Redis (sessions) | ACID, row-level security, JSONB for profile |
| **Companion** | PostgreSQL | Redis (cache) | JSONB for flexible personality, versioning |
| **Memory** | Qdrant | Kuzu (graph) | Vector search + knowledge graph relations |
| **Relationship** | Kuzu | ClickHouse | Graph traversal + time-series analytics |
| **Conversation** | PostgreSQL | ClickHouse | ACID for messages, OLAP for analytics |
| **Proactive** | PostgreSQL | Redis (scheduling) | Job queue + distributed cron |
| **Safety** | PostgreSQL | ClickHouse | Immutable audit + analytical queries |
| **Billing** | PostgreSQL | - | Financial ACID, no polyglot needed |

---

## Data Ownership Rules

### 1. Exclusive Ownership
- Each table/collection owned by exactly ONE module
- No cross-module foreign keys (use event-driven sync)
- Module = single deployable unit owning schema + migrations

### 2. Access Patterns
```typescript
// ❌ FORBIDDEN: Direct cross-module DB access
await memoryDB.query('SELECT * FROM companion WHERE id = ?', [id]);

// ✅ ALLOWED: Event-driven read model
// Memory module subscribes to CompanionUpdated events
// Maintains local companion cache (read model)

// ✅ ALLOWED: API calls (synchronous, with circuit breaker)
const companion = await companionClient.getCompanion(id);
```

### 3. Shared Infrastructure (Not Data)
- **Connection pools**: Per-module, configured by platform
- **Migrations**: Per-module, run in CI/CD pipeline
- **Backups**: Per-module, tested quarterly
- **Monitoring**: Per-module dashboards + global overview

---

## Cross-Module Data Patterns

### 1. Read Models (Materialized Views)
```typescript
// Memory module maintains companion read model
@EventHandler('pao.companion.updated.v1')
async updateCompanionReadModel(event: CompanionUpdated) {
  await this.companionCache.upsert({
    id: event.companionId,
    name: event.name,
    personality: event.personality,
    version: event.version
  });
}

// Usage in Memory module
const companion = await this.companionCache.get(companionId);
// Zero latency, no network call
```

### 2. Saga Pattern (Distributed Transactions)
```typescript
// Create Companion + Initial Memory + Billing Entitlement
async function createCompanionSaga(command: CreateCompanion) {
  const saga = new Saga();
  
  saga.step('create_companion', async () => {
    return await companionModule.create(command);
  });
  
  saga.step('create_initial_memory', async (ctx) => {
    return await memoryModule.createInitial(ctx.companionId);
  });
  
  saga.step('grant_entitlement', async (ctx) => {
    return await billingModule.grantEntitlement(ctx.userId, 'companion');
  });
  
  // Compensating transactions on failure
  saga.compensate('grant_entitlement', async (ctx) => {
    await billingModule.revokeEntitlement(ctx.userId, 'companion');
  });
  
  return await saga.execute();
}
```

### 3. Reference Data (Immutable IDs)
```typescript
// Only exchange stable identifiers across modules
interface CompanionReference {
  companionId: string;        // UUID v7
  version: number;            // For cache invalidation
  // NO embedded objects
}

// Resolve locally when needed
const companion = await this.companionRefResolver.resolve(ref);
```

---

## Technology Deep Dives

### PostgreSQL (Primary OLTP)
```yaml
Version: 16+
Extensions:
  - pgvector (for small-scale embeddings)
  - pg_cron (scheduled jobs)
  - pg_partman (time partitioning)
  - pgaudit (compliance)
  - uuid-ossp (UUID v7)
  
Configuration:
  - max_connections: 500 (per module pool)
  - shared_buffers: 25% RAM
  - effective_cache_size: 75% RAM
  - wal_level: logical (for CDC)
  - row_level_security: on (PII)
  
Patterns:
  - UUID v7 primary keys (time-ordered)
  - JSONB for flexible schemas
  - Partitioning by time (conversations, events)
  - Advisory locks for distributed coordination
```

### Qdrant (Vector Search)
```yaml
Version: 1.8+
Deployment: Kubernetes (Operator)
Collections:
  - memories: 1536-dim, HNSW, payload filtering
  - embeddings: 1024-dim, quantization (scalar)
  
Configuration:
  - hnsw_ef: 128 (search accuracy)
  - hnsw_m: 16 (graph connectivity)
  - quantization: scalar (4x memory savings)
  - replication_factor: 2
  
Sharding:
  - By companion_id (tenant isolation)
  - 10 shards per collection (scale horizontally)
```

### Kuzu (Embedded Graph)
```yaml
Version: 0.8+
Deployment: Embedded in Relationship module (single binary)
Schema:
  Nodes: Companion, User, Memory, Topic, Entity
  Relationships: 
    - KNOWS (User↔Companion)
    - RELATES (Memory↔Memory)
    - MENTIONS (Conversation↔Entity)
    - SIMILAR (Companion↔Companion)
    
Use Cases:
  - "Memories about [topic] from last year"
  - "Companions similar to this one"
  - "Entity resolution across conversations"
  
Performance:
  - Sub-ms for 3-hop queries
  - Columnar storage, vectorized execution
  - ACID transactions
```

### ClickHouse (Analytics/OLAP)
```yaml
Version: 24.3+
Cluster: 3 shards × 2 replicas
Tables:
  - events (MergeTree, partitioned by day)
  - metrics (AggregatingMergeTree, pre-aggregated)
  - ml_features (Wide table for training)
  
Engine Selection:
  - MergeTree: Raw events (partitioned by day, ordered by timestamp)
  - AggregatingMergeTree: Pre-computed metrics (RHI, engagement)
  - SummingMergeTree: Counters (message counts, session duration)
  
Retention:
  - Raw events: 90 days (hot), 7 years (cold/S3)
  - Aggregated: 7 years
```

### Redis Cluster (Shared Infrastructure)
```yaml
Version: 7.2+
Topology: 6 shards × 3 replicas (18 nodes)
Modules: RedisJSON, RediSearch, RedisBloom
Use Cases:
  - Session store (TTL: 30 days)
  - Rate limiting (sliding window)
  - Distributed locks (Redlock)
  - Pub/Sub (real-time presence)
  - Caching (L2 for read models)
  - Idempotency keys (24hr TTL)
  
Configuration:
  - maxmemory-policy: allkeys-lru
  - lazyfree-lazy-eviction: yes
  - replica-read-only: yes
```

---

## Migration Strategy

### Schema Changes (Per Module)
```yaml
Process:
  1. Develop migration in module repo
  2. CI: Test against copy of production schema
  3. Staging: Deploy + run migration (dry-run)
  4. Production: Blue-green deploy
     - New version runs migration on startup
     - Old version drained
  5. Rollback: Previous version (migration down)

Tools:
  - golang-migrate / node-pg-migrate
  - Atlas (declarative schema)
  - pg_dump for rollback snapshots
```

### Data Migration (Cross-Module)
```yaml
Pattern: Dual-write + backfill + cutover
Example: Moving companion preferences from User module → Companion module

Phase 1: Dual Write (2 weeks)
  - Write to BOTH old and new location
  - Read from old (primary)
  
Phase 2: Backfill (1 week)
  - Batch job copies historical data
  - Verify checksums match
  
Phase 3: Cutover (1 day)
  - Switch reads to new location
  - Monitor error rates
  
Phase 4: Cleanup (1 week)
  - Remove old columns/tables
  - Remove dual-write code
```

---

## Consequences

### Positive
- **Autonomy**: Teams choose right tool for their domain
- **Scaling**: Independent scaling per data pattern
- **Isolation**: Failure in one DB doesn't cascade
- **Compliance**: PII isolated, easier to audit/encrypt
- **Innovation**: Experiment with new DBs per module

### Negative
- **Complexity**: 5+ database technologies to operate
- **Consistency**: Eventual consistency by default
- **Joins**: No cross-DB queries (use read models)
- **Transactions**: Distributed transactions via saga
- **Operations**: More backup/restore, monitoring, tuning

### Mitigations
- **Platform Team**: Manages DB infrastructure, upgrades, patches
- **Standardized Tooling**: Common migration, backup, observability
- **Documentation**: Architecture decision records per module
- **Training**: Database deep-dives in onboarding
- **Guardrails**: Linting for forbidden cross-module access

---

## Implementation Checklist

- [ ] Provision PostgreSQL clusters (3 regions, HA)
- [ ] Deploy Qdrant cluster (K8s operator)
- [ ] Deploy Kuzu (embedded in Relationship service)
- [ ] Deploy ClickHouse cluster (3 shards)
- [ ] Deploy Redis Cluster (6 shards)
- [ ] Implement module database clients (connection pooling, retry)
- [ ] Build transactional outbox framework
- [ ] Create read model framework (event handlers → projections)
- [ ] Implement saga orchestrator
- [ ] Define backup/restore procedures per DB
- [ ] Set up monitoring dashboards per DB
- [ ] Run chaos tests (DB failover, network partition)

---

## Related Decisions

- ADR-001: Modular Monolith (module boundaries)
- ADR-003: Event-Driven Architecture (cross-module sync)
- ADR-007: CQRS for Memory/RHI (read models)
- ADR-008: Backup & Disaster Recovery

---

## References

- [Database per Service Pattern](https://microservices.io/patterns/data/database-per-service.html)
- [Polyglot Persistence](https://martinfowler.com/bliki/PolyglotPersistence.html)
- [Transactional Outbox](https://microservices.io/patterns/data/transactional-outbox.html)
- [Saga Pattern](https://microservices.io/patterns/data/saga.html)
- [CQRS](https://martinfowler.com/bliki/CQRS.html)

---

**Approval:**
- CTO: _________________ Date: __________
- VP Engineering: _________________ Date: __________
- Data Platform Lead: _________________ Date: __________