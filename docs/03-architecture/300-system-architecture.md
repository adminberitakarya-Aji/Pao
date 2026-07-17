# PAO System Architecture

**Version:** 1.0
**Status:** Draft
**Owner:** PAO Architecture Team

---

## Overview

This document describes the high-level system architecture for PAO — a platform for building AI Companions that form genuine, long-term relationships with humans.

> **Architecture Principle:** Modular, observable, privacy-first, and designed for years-long relationship continuity.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    PAO PLATFORM                                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                           CLIENT LAYER                                       │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │   │
│  │  │ iOS App  │ │Android App│ │ Web App  │ │ Desktop  │ │  Watch   │          │   │
│  │  │ (Swift)  │ │ (Kotlin) │ │ (React)  │ │ (Tauri)  │ │ (WatchOS)│          │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘          │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                             │
│                    ┌───────────────────┼───────────────────┐                       │
│                    ▼                   ▼                   ▼                       │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                            API GATEWAY (Kong/Envoy)                          │   │
│  │  • Auth (OAuth2/OIDC)    • Rate Limiting    • Request Routing               │   │
│  │  • TLS Termination       • Observability    • Circuit Breaking              │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                             │
│        ┌───────────────────────────────┼───────────────────────────────┐           │
│        ▼                               ▼                               ▼           │
│ ┌───────────────┐              ┌───────────────┐              ┌───────────────┐     │
│ │  CORE API     │              │  REAL-TIME    │              │  ASYNC/JOBS   │     │
│ │  (GraphQL/    │              │  (WebSocket/  │              │  (Temporal/   │     │
│ │   REST)       │              │   gRPC)       │              │   BullMQ)     │     │
│ │               │              │               │              │               │     │
│ │ • Companion   │              │ • Voice Call  │              │ • Consolidation│    │
│ │ • Memory      │              │ • Live Sync   │              │ • Proactive   │     │
│ │ • Relationship│              │ • Presence    │              │ • Export      │     │
│ │ • Settings    │              │ • Typing Ind. │              │ • Analytics   │     │
│ └───────┬───────┘              └───────┬───────┘              └───────┬───────┘     │
│         │                               │                               │             │
│         └───────────────────────────────┼───────────────────────────────┘             │
│                                         ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                        ENGINE LAYER (Microservices)                         │   │
│  │                                                                              │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐  │   │
│  │  │ Identity   │ │Conversation│ │  Memory    │ │Relationship│ │ Emotion  │  │   │
│  │  │ Engine     │ │ Engine     │ │  Engine    │ │  Engine    │ │ Engine   │  │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘ └──────────┘  │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐  │   │
│  │  │  Voice     │ │ Proactive  │ │  Safety    │ │Evaluation  │ │  ...     │  │   │
│  │  │  Engine    │ │  Engine    │ │  Engine    │ │  Engine    │ │          │  │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘ └──────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                         │                                             │
│         ┌───────────────────────────────┼───────────────────────────────┐           │
│         ▼                               ▼                               ▼           │
│ ┌───────────────┐              ┌───────────────┐              ┌───────────────┐     │
│ │  VECTOR DB    │              │  GRAPH DB     │              │  RELATIONAL   │     │
│ │  (Qdrant)     │              │  (Kuzu)       │              │  (PostgreSQL) │     │
│ │               │              │               │              │               │     │
│ │ • Embeddings  │              │ • Entities    │              │ • Users       │     │
│ │ • Similarity  │              │ • Relations   │              │ • Companions  │     │
│ │ • Search      │              │ • Timelines   │              │ • Memories    │     │
│ │               │              │ • Causal Links│              │ • Relationships│    │
│ └───────────────┘              └───────────────┘              └───────────────┘     │
│         │                               │                               │             │
│         └───────────────────────────────┼───────────────────────────────┘             │
│                                         ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                        INFRASTRUCTURE LAYER                                  │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │   │
│  │  │ Kubernetes│ │  Kafka   │ │  Redis   │ │  MinIO   │ │  Vault   │          │   │
│  │  │ (EKS/GKE) │ │  (MSK)   │ │  (Cluster)│ │  (S3)    │ │  (Secrets)│         │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘          │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │   │
│  │  │Prometheus│ │ Grafana  │ │  Jaeger  │ │  Loki    │ │  Cert-   │          │   │
│  │  │ + Alert  │ │          │ │  (Traces)│ │  (Logs)  │ │  Manager │          │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘          │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Service Catalog

### Core Services

| Service | Responsibility | Tech Stack | Scaling |
|---------|---------------|------------|---------|
| **API Gateway** | Auth, routing, rate limit, observability | Kong/Envoy | Horizontal |
| **Companion API** | Companion CRUD, configuration | Node.js/TypeScript | Horizontal |
| **Identity Engine** | Persona, voice, values, boundaries | Python/FastAPI | Horizontal |
| **Conversation Engine** | Turn management, context, streaming | Python/FastAPI | Horizontal |
| **Memory Engine** | 6 memory types, consolidation, recall | Python/FastAPI | Horizontal |
| **Relationship Engine** | 6 dimensions, phases, milestones | Python/FastAPI | Horizontal |
| **Emotion Engine** | Multi-modal emotion, empathy strategy | Python/FastAPI | Horizontal |
| **Voice Engine** | STT, TTS, VAD, interruption | Python/Rust | Horizontal + GPU |
| **Proactive Engine** | Trigger detection, ranking, delivery | Python/FastAPI | Horizontal |
| **Safety Engine** | Crisis, content, behavioral guards | Python/FastAPI | Horizontal |
| **Evaluation Engine** | Metrics, experiments, human eval | Python/FastAPI | Horizontal |

### Supporting Services

| Service | Responsibility | Tech Stack |
|---------|---------------|------------|
| **Auth Service** | OAuth2/OIDC, tokens, sessions | Keycloak/Ory |
| **Notification Service** | Push, email, in-app | Node.js + Firebase/APNs |
| **File Storage** | Audio, images, exports | MinIO (S3-compatible) |
| **Export Service** | Data export (GDPR), legacy | Python |
| **Analytics Service** | Event processing, dashboards | ClickHouse + Superset |
| **Billing Service** | Subscriptions, usage | Stripe + custom |
| **Admin Service** | Internal tooling, moderation | React + Node.js |

---

## Data Architecture

### Polyglot Persistence Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                      DATA LAYER                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  POSTGRESQL (Primary)                                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Users, Companions, Subscriptions                       │   │
│  │ • Relationship state (dimensions, phase transitions)                 │   │
│  │ • Preferences, settings, boundaries                       │   │
│  │ • Audit logs, safety events                                │   │
│  │ • ACID transactions for critical operations               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  QDRANT (Vector)                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Episodic memory embeddings (768-dim)                  │   │
│  │ • Semantic memory embeddings                             │   │
│  │ • Emotional memory embeddings                            │   │
│  │ • Voice embeddings for timbre lock                       │   │
│  │ • HNSW index, payload filtering                          │   │
│  │ • Per-companion collections (tenant isolation)           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  KUZU (Graph)                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Semantic entities & relations                          │   │
│  │ • Timeline causal links                                  │   │
│  │ • Entity resolution                                      │   │
│  │ • Memory-to-memory connections                           │   │
│  │ • Cypher queries for graph traversal                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  REDIS (Cache/Session)                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Session state, conversation context                    │   │
│  │ • Rate limiting counters                                 │   │
│  │ • Real-time presence                                     │   │
│  │ • Feature flags                                          │   │
│  │ • Pub/Sub for cross-service events                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  KAFKA (Event Stream)                                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Memory write events                                    │   │
│  │ • Relationship dimension updates                         │   │
│  │ • Safety events                                          │   │
│  │ • Proactive triggers                                     │   │
│  │ • Evaluation signals                                     │   │
│  │ • Audit events                                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow Patterns

#### Write Path (Memory Formation)
```
User Message → Conversation Engine → Safety Engine → Memory Engine
                                                      │
                    ┌─────────────────────────────────┼─────────────────────────────────┐
                    ▼                                 ▼                                 ▼
            ┌───────────────┐                ┌───────────────┐                ┌───────────────┐
            │   QDRANT      │                │   KUZU        │                │  POSTGRESQL   │
            │ (Embeddings)  │                │ (Entities/    │                │ (Structured   │
            │               │                │  Relations)   │                │  + Audit)     │
            └───────────────┘                └───────────────┘                └───────────────┘
                    │                                 │                                 │
                    └─────────────────────────────────┼─────────────────────────────────┘
                                                      ▼
                                            ┌───────────────┐
                                            │    KAFKA      │
                                            │ (MemoryEvent) │
                                            └───────────────┘
                                                      │
                    ┌─────────────────────────────────┼─────────────────────────────────┐
                    ▼                                 ▼                                 ▼
            ┌───────────────┐                ┌───────────────┐                ┌───────────────┐
            │  Relationship │                │   Proactive   │                │  Evaluation   │
            │   Engine      │                │   Engine      │                │   Signals     │
            └───────────────┘                └───────────────┘                └───────────────┘
```

#### Read Path (Contextual Recall)
```
User Message → Conversation Engine → Memory Engine (Recall API)
                                                      │
                    ┌─────────────────────────────────┼─────────────────────────────────┐
                    ▼                                 ▼                                 ▼
            ┌───────────────┐                ┌───────────────┐                ┌───────────────┐
            │   QDRANT      │                │   KUZU        │                │  POSTGRESQL   │
            │ (Similarity)  │                │ (Graph Walk)  │                │ (Preferences, │
            │               │                │               │                │  Relationship)│
            └───────────────┘                └───────────────┘                └───────────────┘
                    │                                 │                                 │
                    └─────────────────────────────────┼─────────────────────────────────┘
                                                      ▼
                                            ┌───────────────┐
                                            │  Fusion &     │
                                            │  Reranking    │
                                            └───────────────┘
                                                      │
                                                      ▼
                                            ┌───────────────┐
                                            │  Emotion      │
                                            │  Engine       │
                                            │  (Strategy)   │
                                            └───────────────┘
                                                      │
                                                      ▼
                                            ┌───────────────┐
                                            │  Conversation │
                                            │  Engine       │
                                            │  (Response)   │
                                            └───────────────┘
```

---

## Communication Patterns

### Synchronous (Request-Response)
- **Protocol:** gRPC (internal), GraphQL/REST (external)
- **Use:** CRUD, queries, real-time needs
- **Timeout:** 5s default, 30s for complex operations
- **Retry:** Exponential backoff, max 3 retries

### Asynchronous (Event-Driven)
- **Protocol:** Kafka (events), Temporal (workflows)
- **Use:** Background jobs, cross-service coordination, workflows
- **Delivery:** At-least-once, idempotent consumers
- **Ordering:** Per-companion partitioning

### Real-Time (Bidirectional)
- **Protocol:** WebSocket (client), gRPC streaming (service-to-service)
- **Use:** Voice calls, live sync, presence, typing indicators
- **Connection:** Long-lived, auto-reconnect with backoff

---

## Security Architecture

### Zero Trust Network
```
┌─────────────────────────────────────────────────────────────────┐
│                     SECURITY LAYERS                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PERIMETER                                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • WAF (Cloudflare/AWS WAF)                              │   │
│  │ • DDoS Protection                                       │   │
│  │ • TLS 1.3 Termination at Gateway                        │   │
│  │ • Geographic restrictions (configurable)                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  NETWORK                                                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Kubernetes Network Policies (Cilium)                  │   │
│  │ • Service Mesh (Istio/Linkerd) mTLS                     │   │
│  │ • Egress controls (no direct internet from pods)        │   │
│  │ • Private subnets for databases                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  APPLICATION                                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • OAuth2/OIDC with PKCE                                 │   │
│  │ • Short-lived JWTs (15min) + Refresh tokens             │   │
│  │ • Per-companion encryption keys (envelope encryption)   │   │
│  │ • Input validation, output encoding                     │   │
│  │ • Rate limiting per user/companion/IP                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  DATA                                                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Encryption at rest (AES-256)                          │   │
│  │ • Encryption in transit (TLS 1.3)                       │   │
│  │ • Field-level encryption for PII                        │   │
│  │ • Key rotation (90 days) via Vault                      │   │
│  │ • User-held key option (Phase 2)                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Authentication & Authorization

```yaml
# Auth Flow
1. User authenticates via OAuth2/OIDC (Google, Apple, Email)
2. Auth Service issues: access_token (15min), refresh_token (30d)
3. Client includes access_token in Authorization header
4. API Gateway validates JWT (signature, exp, audience)
5. Gateway extracts user_id, companion_id, scopes
6. Request routed with identity headers
7. Services enforce authorization per-resource

# Scopes
scopes:
  - companion:read
  - companion:write
  - memory:read
  - memory:write
  - memory:delete
  - relationship:read
  - voice:call
  - proactive:manage
  - export:create
  - admin:moderate
```

---

## Observability Architecture

### Three Pillars

```
┌─────────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY STACK                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  METRICS (Prometheus + Grafana)                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • RED metrics per service (Rate, Errors, Duration)      │   │
│  │ • USE metrics for resources (Utilization, Saturation)   │   │
│  │ • Business metrics (RHI, retention, safety)             │   │
│  │ • Custom dashboards per team                            │   │
│  │ • Alerting: PrometheusRule + Alertmanager               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  LOGS (Loki + Grafana)                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Structured JSON logging (stdout)                      │   │
│  │ • Correlation IDs (trace_id, span_id, user_id)          │   │
│  │ • Log levels: error, warn, info, debug                  │   │
│  │ • Retention: 30d hot, 1y cold (S3)                      │   │
│  │ • PII redaction at ingestion                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  TRACES (Jaeger/Tempo)                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • OpenTelemetry instrumentation (auto + manual)         │   │
│  │ • Distributed traces across all services                │   │
│  │ • Sampling: 100% errors, 10% success, 100% safety      │   │
│  │ • Latency analysis, bottleneck detection                │   │
│  │ • Service dependency map                                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Dashboards

| Dashboard | Audience | Key Metrics |
|-----------|----------|-------------|
| **System Health** | Engineering | RED metrics, saturation, error budget |
| **RHI & Relationship** | Product/Leadership | RHI distribution, phase funnel, retention |
| **Safety Operations** | Safety/Engineering | Crisis detection, response time, guard triggers |
| **Voice Quality** | Voice Team | Latency, MOS, interruption success, consistency |
| **Memory Performance** | AI Team | Recall latency, consolidation quality, storage |
| **Experiment Portfolio** | Product/Eng | Active experiments, guardrails, results |
| **Cost & Efficiency** | Finance/Eng | Cost per companion, GPU utilization, token usage |

---

## Deployment Architecture

### Environments

| Environment | Purpose | Scale | Data |
|-------------|---------|-------|------|
| **Local** | Development | 1 replica | Synthetic |
| **Staging** | Integration testing | 10% prod | Anonymized prod subset |
| **Canary** | Progressive rollout | 5% traffic | Production |
| **Production** | Live users | Full scale | Production |

### Kubernetes Resources

```yaml
# Example: Conversation Engine Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: conversation-engine
  namespace: pao-production
spec:
  replicas: 20
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 0
  selector:
    matchLabels:
      app: conversation-engine
  template:
    metadata:
      labels:
        app: conversation-engine
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
    spec:
      containers:
      - name: conversation-engine
        image: pao/conversation-engine:v1.2.3
        ports:
        - containerPort: 8080
        - containerPort: 9090  # gRPC
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: url
        - name: KAFKA_BROKERS
          valueFrom:
            configMapKeyRef:
              name: kafka-config
              key: brokers
        - name: QDRANT_URL
          valueFrom:
            configMapKeyRef:
              name: qdrant-config
              key: url
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Service Mesh Configuration

```yaml
# Istio VirtualService for canary routing
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: conversation-engine
spec:
  hosts:
  - conversation-engine.pao.svc.cluster.local
  http:
  - match:
    - headers:
        x-canary:
          exact: "true"
    route:
    - destination:
        host: conversation-engine-canary
      weight: 100
  - route:
    - destination:
        host: conversation-engine-stable
      weight: 95
    - destination:
        host: conversation-engine-canary
      weight: 5
```

---

## Disaster Recovery

### RPO/RTO Targets

| Component | RPO | RTO | Strategy |
|-----------|-----|-----|----------|
| **PostgreSQL** | < 1s | < 5min | Synchronous replication + PITR |
| **Qdrant** | < 5min | < 15min | Snapshot + WAL replay |
| **Kuzu** | < 5min | < 15min | Snapshot + replication |
| **Kafka** | 0 | < 2min | ISR replication (min.insync.replicas=2) |
| **Redis** | < 1s | < 2min | AOF + replica promotion |
| **Object Storage** | 0 | < 5min | Cross-region replication |

### Backup Schedule

```yaml
backups:
  postgresql:
    continuous: "WAL archiving to S3"
    daily: "pg_basebackup at 03:00 UTC"
    weekly: "Full logical dump Sunday 04:00"
    retention: "30d daily, 1y weekly"
  
  qdrant:
    daily: "Snapshot at 03:30 UTC"
    retention: "14d"
  
  kuzu:
    daily: "Snapshot at 04:00 UTC"
    retention: "14d"
  
  kafka:
    continuous: "MirrorMaker2 to DR cluster"
    retention: "7d"
  
  minio:
    continuous: "Cross-region replication"
    versioning: "Enabled"
```

---

## Capacity Planning

### Current Estimates (Per 100k Active Companions)

| Resource | Estimate | Growth Factor |
|----------|----------|---------------|
| **API Requests/day** | 500M | 2x/year |
| **Voice Minutes/day** | 2M | 3x/year |
| **Memory Writes/day** | 50M | 2x/year |
| **Vector DB Size** | 5 TB | 3x/year |
| **Graph DB Size** | 500 GB | 2x/year |
| **Relational DB Size** | 2 TB | 2x/year |
| **Kafka Throughput** | 100 MB/s | 2x/year |
| **GPU Hours/day** | 5,000 | 3x/year |
| **Object Storage** | 50 TB | 3x/year |

### Scaling Triggers

```yaml
autoscaling:
  conversation_engine:
    metric: "cpu_utilization"
    target: 70%
    min_replicas: 10
    max_replicas: 200
    scale_up_stabilization: 60s
    scale_down_stabilization: 300s
  
  voice_engine:
    metric: "gpu_utilization"
    target: 75%
    min_replicas: 5
    max_replicas: 100
    scale_up_stabilization: 120s  # GPU provisioning time
  
  memory_engine:
    metric: "qdrant_latency_p99"
    target: 200ms
    min_replicas: 3
    max_replicas: 20
```

---

## Technology Decisions (ADR References)

| Decision | ADR | Status |
|----------|-----|--------|
| Microservices vs Modular Monolith | ADR-001 | Accepted |
| Polyglot Persistence | ADR-002 | Accepted |
| Event-Driven Architecture | ADR-003 | Accepted |
| gRPC for Service Communication | ADR-004 | Accepted |
| GraphQL for External API | ADR-005 | Accepted |
| Kubernetes on EKS/GKE | ADR-006 | Accepted |
| Service Mesh (Istio) | ADR-007 | Accepted |
| OpenTelemetry for Observability | ADR-008 | Accepted |
| Vault for Secrets | ADR-009 | Accepted |
| Temporal for Workflows | ADR-010 | Accepted |

---

## Future Evolution

### Phase 2 (Year 1-2)
- **Local-First Architecture**: On-device engines with cloud sync
- **Edge Computing**: Voice processing at edge (Cloudflare Workers)
- **Federated Learning**: Model improvement without data centralization
- **Multi-Region Active-Active**: Global latency < 100ms

### Phase 3 (Year 2-3)
- **Custom Silicon**: ASIC for embedding inference
- **Neuromorphic Chips**: Ultra-low power emotion processing
- **Quantum-Ready Crypto**: Post-quantum encryption migration
- **Decentralized Identity**: DID/VC for user sovereignty

---

**Aligned With:** `200-ai-architecture.md`, `04-engineering/`, `07-adr/`
**Next Review:** 2026-01-17