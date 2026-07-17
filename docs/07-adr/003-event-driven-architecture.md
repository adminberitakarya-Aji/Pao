# ADR-003: Event-Driven Architecture

**Status:** Accepted
**Date:** 2025-01-15
**Deciders:** CTO, VP Engineering, Platform Lead, AI Leads
**Consulted:** All Domain Leads, Security, Data Engineering

---

## Context

PAO's domain modules (User, Companion, Memory, Relationship, Proactive, Safety, etc.) need to communicate asynchronously to maintain loose coupling, enable independent scaling, and support real-time features like proactive messaging and memory consolidation.

### Requirements

| Requirement | Priority |
|-------------|----------|
| Loose coupling between modules | Critical |
| Event ordering guarantees (per companion) | High |
| Exactly-once processing (billing, safety) | Critical |
| Replay capability (debugging, new consumers) | High |
| Multi-region replication | High |
| Schema evolution & validation | Critical |
| Low latency (< 10ms publish) | High |
| Operational simplicity | Medium |

---

## Decision

**Adopt Apache Kafka (Redpanda) as the event backbone with a structured event-driven architecture.**

### Event Bus: Redpanda (Kafka-compatible)

```yaml
Why Redpanda over Kafka:
  - Single binary, no JVM/ZooKeeper
  - 10x lower resource usage
  - Native Kafka protocol compatibility
  - Built-in schema registry
  - WASM transforms for enrichment
  - Tiered storage (S3) for cost-effective retention
  - Better tail latency (P99 < 5ms)

Cluster Topology:
  - 3 AZs per region (US-East, EU-West, APAC-Singapore)
  - 9 brokers minimum (3 per AZ)
  - Replication factor: 3
  - Min insync replicas: 2
  - Retention: 7 days hot (SSD), 90 days cold (S3)
```

### Event Categories & Topics

```yaml
# Core Domain Events (per companion partitioning)
companion.events:
  partitions: 100 (scale to 1000)
  key: companion_id (ensures ordering per companion)
  retention: 30 days
  events:
    - CompanionCreated
    - CompanionUpdated
    - CompanionDeleted
    - PersonalityChanged
    - MemoryStored
    - MemoryRecalled
    - RHIUpdated

conversation.events:
  partitions: 200
  key: conversation_id
  retention: 90 days
  events:
    - MessageSent
    - MessageReceived
    - VoiceCallStarted
    - VoiceCallEnded
    - TypingIndicator

user.events:
  partitions: 50
  key: user_id
  retention: 365 days
  events:
    - UserRegistered
    - UserActivated
    - SubscriptionChanged
    - TierUpgraded
    - TierDowngraded
    - ConsentUpdated

# Cross-Domain Events
system.events:
  partitions: 10
  retention: 7 days
  events:
    - SafetyTriggered
    - CrisisDetected
    - ProactiveScheduled
    - ProactiveSent
    - ProactiveResponded
    - EvaluationCompleted
    - ModelSwitched

# Integration Events (external)
integration.events:
  partitions: 20
  retention: 30 days
  events:
    - PaymentSucceeded
    - PaymentFailed
    - WebhookDelivered
    - ExportCompleted
```

### Event Schema (CloudEvents + Protobuf)

```protobuf
// events/v1/base.proto
syntax = "proto3";
package pao.events.v1;

import "google/protobuf/any.proto";
import "google/protobuf/timestamp.proto";

message CloudEvent {
  string specversion = 1;           // "1.0"
  string id = 2;                    // UUID v7 (time-ordered)
  string source = 3;                // "pao.memory-engine"
  string type = 4;                  // "pao.memory.stored.v1"
  string datacontenttype = 5;       // "application/protobuf"
  google.protobuf.Timestamp time = 6;
  string subject = 7;               // companion_id, user_id, etc.
  string traceparent = 8;           // W3C traceparent
  map<string, string> extensions = 9;
  google.protobuf.Any data = 10;    // Typed payload
}

// Example: MemoryStored
message MemoryStored {
  string memory_id = 1;
  string companion_id = 2;
  string user_id = 3;
  MemoryType type = 4;
  string content = 5;
  float importance = 6;
  repeated string tags = 7;
  google.protobuf.Timestamp occurred_at = 8;
}
```

### Producer Patterns

```typescript
// Transactional Outbox Pattern (for consistency)
async function publishMemoryStored(memory: Memory) {
  await db.transaction(async (tx) => {
    // 1. Write to domain table
    await tx.memory.create({ data: memory });
    
    // 2. Write to outbox table (same transaction)
    await tx.outbox.create({
      data: {
        aggregateId: memory.companionId,
        eventType: 'pao.memory.stored.v1',
        payload: serialize(memory),
        metadata: { traceId: getTraceId() }
      }
    });
  });
  
  // 3. Outbox poller publishes to Redpanda (separate process)
  // Guarantees: At-least-once, idempotent consumers
}

// Direct Publish (for non-critical, high-throughput)
async function publishTypingIndicator(event: TypingIndicator) {
  await producer.send({
    topic: 'conversation.events',
    messages: [{
      key: event.conversationId,
      value: serialize(event),
      headers: { traceparent: getTraceParent() }
    }],
    acks: 'all' // Wait for ISR
  });
}
```

### Consumer Patterns

```typescript
// Idempotent Consumer (exactly-once semantics)
class MemoryStoredHandler {
  async handle(event: CloudEvent) {
    const payload = deserialize(event.data);
    const idempotencyKey = `memory:${payload.memoryId}:processed`;
    
    // Check if already processed (Redis SETNX with TTL)
    const processed = await redis.setnx(idempotencyKey, '1', 'EX', 86400);
    if (!processed) return; // Already handled
    
    // Process with domain logic
    await this.memoryService.consolidate(payload);
    
    // Update read models, trigger downstream
    await this.projectionUpdater.update(payload);
  }
}

// Ordered Consumer (per companion)
class CompanionEventProcessor {
  // Kafka consumer group with sticky partition assignment
  // Processes events for assigned companions in order
  async consume(batch: ConsumerBatch) {
    for (const record of batch) {
      await this.dispatch(record);
    }
    await this.commitOffsets(batch);
  }
}

// Projection Builder (read models)
class RHIProjection {
  @EventHandler('pao.rhi.updated.v1')
  async updateRHI(event: RHIUpdated) {
    await this.readModel.upsert({
      companionId: event.companionId,
      rhiScore: event.newScore,
      components: event.components,
      updatedAt: event.timestamp
    });
  }
}
```

### Event Processing Guarantees

| Guarantee | Mechanism | Use Cases |
|-----------|-----------|-----------|
| **At-least-once** | Producer acks=all + Consumer idempotency | Most events |
| **Exactly-once** | Transactional outbox + idempotent consumer | Billing, Safety, Consent |
| **Ordering (per key)** | Partition by companion_id/conversation_id | Memory, Conversation, RHI |
| **Replay** | Compact topics + consumer offset reset | New projections, debugging |
| **Dead Letter** | Retry topic (3x) → DLQ → alert | Poison pills, bugs |

---

## Consequences

### Positive
- **Decoupling**: Modules communicate via events, no direct dependencies
- **Scalability**: Independent scaling of producers/consumers
- **Resilience**: Buffer during load spikes, replay for recovery
- **Auditability**: Complete event log for compliance, debugging
- **Extensibility**: New consumers without modifying producers
- **Temporal Queries**: Event sourcing enables "time travel" queries

### Negative
- **Complexity**: Eventual consistency, distributed tracing required
- **Operational Burden**: Kafka cluster management, monitoring
- **Schema Evolution**: Must maintain backward/forward compatibility
- **Debugging**: Harder to trace causality across async boundaries
- **Latency**: Additional hop (producer → broker → consumer)

### Mitigations
- **Schema Registry**: Enforced compatibility checks in CI
- **Observability**: OpenTelemetry + W3C tracecontext propagation
- **Tooling**: kcat, Redpanda Console, custom event debugger
- **Testing**: Contract tests, chaos engineering (broker failure)
- **Documentation**: Event catalog with examples, ownership

---

## Implementation Plan

- [ ] Provision Redpanda clusters (3 regions)
- [ ] Deploy Schema Registry (Redpanda built-in)
- [ ] Define core event schemas (protobuf)
- [ ] Implement transactional outbox pattern
- [ ] Build producer/consumer libraries (TypeScript, Go)
- [ ] Set up monitoring (lag, throughput, errors)
- [ ] Configure multi-region replication (MirrorMaker2)
- [ ] Document event catalog (AsyncAPI)
- [ ] Run chaos tests (broker loss, network partition)

---

## Related Decisions

- ADR-001: Modular Monolith (modules communicate via events)
- ADR-002: API Protocol (gRPC for sync, events for async)
- ADR-004: Database per Module (outbox pattern)
- ADR-007: CQRS/Event Sourcing for Memory/RHI

---

## References

- [Redpanda Documentation](https://docs.redpanda.com/)
- [CloudEvents Spec](https://cloudevents.io/)
- [Transactional Outbox Pattern](https://microservices.io/patterns/data/transactional-outbox.html)
- [Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html)
- [Kafka Exactly-Once Semantics](https://docs.confluent.io/platform/current/streams/developer-guide/exactly-once.html)

---

**Approval:**
- CTO: _________________ Date: __________
- VP Engineering: _________________ Date: __________
- Platform Lead: _________________ Date: __________