# PAO Monorepo - CTO Implementation Plan (Detailed)

**Version:** 2.0  
**Status:** Draft  
**Created:** 2025-07-27  
**Last Updated:** 2025-07-27  
**Owner:** CTO Office  
**Classification:** Internal - Leadership

---

## Executive Summary

PAO is an **AI Companion platform** built on a **memory-first, relationship-centric architecture** with 8 specialized AI engines. This plan covers the **entire monorepo** — infrastructure, AI services, backend APIs, mobile apps, documentation, and operational excellence — organized for a team of 15-25 engineers over 6-9 months to MVP.

**Core Philosophy:** 
- Memory-first: Relationship continuity > context window
- Engine-per-concern: Modular, independently scalable, team-owned
- Local-first default: Privacy by design, API as fallback
- Safety as foundation: Cross-cutting, veto power, human review

---

## Monorepo Structure (Current State)

```
pao/
├── .github/workflows/           # CI/CD (ai-services.yml ✅)
├── assets/                      # Brand, media, design tokens
├── docs/                        # 8 domains, 50+ specs
│   ├── 00-foundation/           # Principles, constitution
│   ├── 01-product/              # PRD, personas, journeys
│   ├── 02-ai/                   # 10 engine specs (200-290) ✅
│   ├── 03-architecture/         # System, data, API contracts
│   ├── 04-engineering/          # Standards, patterns, runbooks
│   ├── 05-business/             # Metrics, pricing, GTM
│   ├── 06-legal/                # Privacy, terms, compliance
│   ├── 07-adr/                  # Architecture Decision Records
│   └── 08-rfc/                  # Request for Comments
├── engineering/
│   ├── ai/
│   │   ├── shared/              # pao-shared lib ✅
│   │   ├── services/            # 5 services ✅, 6 engines 🔄
│   │   │   ├── inference_gateway/   ✅ (port 8000)
│   │   │   ├── embedding_service/   ✅ (port 8001)
│   │   │   ├── rag_pipeline/        ✅ (port 8002)
│   │   │   ├── identity_engine/     ✅ (Phase 1, port 8003)
│   │   │   ├── memory_engine/       ✅ (Phase 1, port 8004)
│   │   │   ├── safety_engine/       ✅ (Phase 2, port 8005)
│   │   │   ├── relationship_engine/ ✅ (Phase 2, port 8006)
│   │   │   ├── emotion_engine/      ✅ (Phase 3, port 8007)
│   │   │   ├── voice_engine/        ✅ (Phase 3, port 8008)
│   │   │   ├── proactive_engine/    ✅ (Phase 4, port 8009)
│   │   │   └── evaluation_engine/   ✅ (Phase 4, port 8010)
│   │   └── runtime/             # Companion Runtime (LangGraph) 🔄
│   ├── backend/                 # User-facing API (FastAPI) 🔄
│   │   ├── api/                 # REST + GraphQL endpoints
│   │   ├── auth/                # AuthN/AuthZ, tokens, sessions
│   │   ├── billing/             # Subscriptions, usage, Stripe
│   │   ├── notifications/       # Push, email, in-app
│   │   ├── admin/               # Admin dashboard API
│   │   └── webhooks/            # External integrations
│   ├── infrastructure/          # Terraform (AWS/GCP) ✅ modules
│   │   ├── modules/
│   │   │   ├── vpc/             ✅
│   │   │   ├── eks/             ✅
│   │   │   ├── databases/       ✅ (PG, Qdrant, Kuzu, Redis, Kafka, Temporal)
│   │   │   ├── observability/   ✅ (Prometheus, Grafana, Loki, Tempo)
│   │   │   ├── secrets/         ✅ (Vault, External Secrets)
│   │   │   └── cicd/            ✅ (ArgoCD, GitHub Actions)
│   │   ├── environments/
│   │   │   ├── dev/
│   │   │   ├── staging/
│   │   │   └── prod/
│   │   └── versions.tf          ✅
│   └── mobile/                  # React Native / Expo 🔄
│       ├── app/                 # Companion app (user-facing)
│       ├── companion/           # Companion UI (chat, voice, diary)
│       ├── onboarding/          # Co-creation flow
│       ├── settings/            # Preferences, privacy, safety
│       └── shared/              # UI kit, hooks, utils
├── CHANGELOG.md
├── CONTRIBUTING.md
├── FOUNDATION.md
├── LICENSE
├── PRODUCT_OVERVIEW.md
├── README.md
```

---

## Workstream Breakdown

### WS1: Infrastructure & Platform (Weeks 1-4, ongoing)
**Owner:** Platform Team (3-4 engineers)

#### Week 1: Network & Compute Foundation
- [ ] `terraform apply` dev environment: VPC (3 AZs, /16), subnets (public/private/db), NAT GW, VPC endpoints
- [ ] EKS cluster dev: 1x managed node group (m6i.xlarge, 3-10 nodes), IRSA, Cluster Autoscaler, AWS Load Balancer Controller
- [ ] EKS clusters staging/prod: Same config, larger node groups, pod disruption budgets
- [ ] Kubernetes basics: namespaces (ai-services, backend, monitoring, databases), RBAC, NetworkPolicies, ResourceQuotas
- [ ] Helm repos: bitnami, prometheus-community, grafana, temporal, qdrant, kuzu
- [ ] ArgoCD bootstrap: app-of-apps pattern, projects per environment, automated sync + prune

#### Week 2: Data Layer
- [ ] PostgreSQL (RDS): Primary + read replica, pgvector extension, encryption, automated backups (7-day retention), PITR
- [ ] Qdrant (vector): 3-node cluster, collections per companion + global knowledge, HNSW config (m=16, ef_construct=128)
- [ ] Kuzu (graph): Single-node dev, HA for prod, schema for memory entities + relationships
- [ ] Redis (ElastiCache): Cluster mode, 3 shards, TLS, auth, TTL policies per namespace
- [ ] Kafka (MSK): 3 broker, 3 AZ, IAM auth, topics: `companion.events`, `safety.alerts`, `memory.consolidation`, `proactive.queue`
- [ ] Temporal: 3-node cluster, persistence to PG, visibility to ES, namespaces per environment
- [ ] Schema migrations: Atlas/Golang-migrate for PG, Qdrant collections via API, Kuzu DDL

#### Week 3: Observability & GitOps
- [ ] Prometheus Operator: ServiceMonitors for all services, custom metrics (RHI, drift, safety)
- [ ] Grafana: Dashboards per engine, Golden Signals (latency, traffic, errors, saturation), business dashboards
- [ ] Loki: Log aggregation, structured logging (JSON), retention 30d, labels: service, environment, trace_id
- [ ] Tempo: Distributed tracing, sampling 10% + 100% errors, integration with Loki/Metrics
- [ ] AlertManager: Routes by severity (P1=page, P2=slack, P3=email), inhibition rules, silences
- [ ] ArgoCD Applications: One per service per environment, health checks, sync windows
- [ ] External Secrets Operator: Vault backend, secret rotation, CSI driver for pod mounts

#### Week 4: Developer Experience & Testing
- [ ] Local dev: Tilt/DevSpace config, hot reload, telepresence for remote debugging
- [ ] k6 load testing: Scenarios per engine, CI integration, thresholds in PR checks
- [ ] Contract testing: Pact broker, provider/verification in CI
- [ ] Preview environments: ArgoCD + GitHub Actions, auto-deploy PRs to `pr-<num>.dev.pao.ai`
- [ ] Documentation: `mkdocs` for internal docs, auto-deploy on merge

#### Ongoing (Month 2+)
- [ ] Disaster recovery: Cross-region backup, RPO <1hr, RTO <4hr, quarterly drills
- [ ] SOC2/ISO27001: Evidence collection automation, policy docs, access reviews
- [ ] Cost optimization: Kubecost, rightsizing, spot instances for batch, reserved for steady-state

**Dependencies for AI engines:** PG + Qdrant + Kuzu + Redis + Kafka + Temporal must be **running in dev** before Identity Engine integration tests.

---

### WS2: AI Engines (Weeks 1-14) — **Core IP**
**Owner:** AI Team (5-7 engineers)

See `implementation-plan.md` for detailed 4-phase, 14-week plan.

#### Service Structure Pattern (All Engines)
```
engineering/ai/services/{engine_name}/
├── pyproject.toml              # uv workspace member, deps
├── Dockerfile                  # Multi-stage, distroless final
├── .dockerignore
├── src/
│   └── {engine_name}/
│       ├── __init__.py
│       ├── main.py             # FastAPI app, lifespan, routes
│       ├── config.py           # Pydantic Settings, env validation
│       ├── models/             # Pydantic models (request/response/internal)
│       ├── services/           # Business logic, external clients
│       ├── repositories/       # Data access (PG, Qdrant, Kuzu, Redis)
│       ├── workers/            # Background tasks (Temporal activities)
│       ├── middleware/         # Auth, logging, metrics, tracing
│       └── utils/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── hpa.yaml
│   ├── servicemonitor.yaml
│   └── configmap.yaml
└── scripts/
    ├── dev.sh
    ├── test.sh
    └── migrate.sh
```

#### Engine Specifications Summary

| Engine | Port | Primary DB | Key Models | Latency Target | Status |
|--------|------|------------|------------|----------------|--------|
| **Identity** | 8003 | PG + Redis | Personality, Values, Style, Boundaries, Goals, Fingerprint | P99 <100ms | ✅ Complete |
| **Memory** | 8004 | PG + Qdrant + Kuzu | Episodic, Semantic, Procedural, Consolidation, Recall | P95 <200ms | ✅ Complete |
| **Safety** | 8005 | PG + Redis | CrisisDetector, ContentFilter, BehavioralGuards, RealityAnchor | P99 <50ms | ✅ Complete |
| **Relationship** | 8006 | PG + Kuzu | Dimensions (Trust, Intimacy, etc.), Milestones, Diary, State Machine | P99 <100ms | ✅ Complete |
| **Emotion** | 8007 | PG + Redis | Valence/Arousal, Appraisal, Expression, Calibration | P99 <100ms | ✅ Complete |
| **Voice** | 8008 | PG + S3 | STT (Whisper), TTS (Kokoro/XTTS), Streaming, Interruption | P50 <500ms | 🔄 In Progress |
| **Proactive** | 8009 | PG + Kafka + Temporal | Scheduler, Generator, Ranker, Delivery, Feedback | Async | 🔄 In Progress |
| **Evaluation** | 8010 | PG + Qdrant | RHI Calculator, Drift Monitor, AB Test, Survey Integration | Batch | 🔄 In Progress |

#### Key Integration Milestones
| Milestone | Target | Criteria |
|-----------|--------|----------|
| Identity + Memory APIs working in dev | Week 3 | CRUD + recall + fingerprint |
| Safety Engine intercepting all outputs | Week 5 | Pre/post gates integrated |
| Relationship Engine tracking dimensions | Week 6 | State machine + milestones |
| Emotion + Voice streaming E2E | Week 9 | <500ms P50 latency |
| Proactive generating relevant nudges | Week 11 | >80% helpful rate |
| Evaluation Engine computing RHI | Week 13 | Correlates >0.85 with surveys |
| **Companion Runtime v1 (LangGraph)** | **Week 10** | **All engines orchestrated** |

**Companion Runtime** — The orchestration layer that wires all engines together per message. This is the **single most critical integration point**.

#### Companion Runtime Architecture (LangGraph)
```
StateGraph:
  Nodes:
    - safety_pre_check (INPUT) → SafetyEngine.validate_input()
    - identity_context → IdentityEngine.get_context()
    - memory_retrieve → MemoryEngine.recall()
    - relationship_context → RelationshipEngine.get_state()
    - emotion_context → EmotionEngine.get_state()
    - llm_generate → InferenceGateway.stream()
    - safety_post_check (OUTPUT) → SafetyEngine.filter_output()
    - memory_consolidate → MemoryEngine.consolidate()
    - relationship_update → RelationshipEngine.update()
    - emotion_update → EmotionEngine.update()
    - proactive_check → ProactiveEngine.maybe_generate()
  
  Edges: Conditional routing based on message type, safety flags, proactive triggers
  Checkpoint: PostgresSaver (per conversation thread)
  Streaming: Native LangGraph streaming + SafetyEngine streaming filter
```

---

### WS3: Backend API (Weeks 3-12)
**Owner:** Backend Team (3-4 engineers)

#### Architecture
```
engineering/backend/
├── pyproject.toml
├── Dockerfile
├── src/
│   └── pao_backend/
│       ├── __init__.py
│       ├── main.py                 # FastAPI app, lifespan, middleware
│       ├── config.py               # Settings (Pydantic BaseSettings)
│       ├── database.py             # SQLAlchemy 2.0 async engine, session
│       ├── models/                 # SQLModel models (User, Companion, Conversation, Message, etc.)
│       ├── schemas/                # Pydantic request/response models
│       ├── api/                    # Route modules
│       │   ├── __init__.py
│       │   ├── auth.py             # /auth/* (login, register, refresh, passkeys)
│       │   ├── users.py            # /users/me, /users/{id}
│       │   ├── companions.py       # /companions/* (CRUD, co-creation)
│       │   ├── conversations.py    # /conversations/* (messages, history, search)
│       │   ├── memory.py           # /memory/* (browser, export, delete)
│       │   ├── relationship.py     # /relationship/* (state, milestones, diary)
│       │   ├── voice.py            # /voice/* (calls, signaling, recordings)
│       │   ├── proactive.py        # /proactive/* (preferences, queue, feedback)
│       │   ├── billing.py          # /billing/* (Stripe webhooks, subscriptions)
│       │   ├── notifications.py    # /notifications/* (preferences, history)
│       │   ├── admin.py            # /admin/* (users, analytics, safety queue)
│       │   └── webhooks.py         # /webhooks/* (outbound events)
│       ├── services/               # Business logic
│       │   ├── auth_service.py
│       │   ├── companion_service.py
│       │   ├── conversation_service.py
│       │   ├── memory_service.py
│       │   ├── relationship_service.py
│       │   ├── voice_service.py
│       │   ├── proactive_service.py
│       │   ├── billing_service.py
│       │   └── notification_service.py
│       ├── repositories/           # Data access layer
│       ├── workers/                # Background tasks (Temporal activities)
│       ├── middleware/             # Auth, rate limit, logging, metrics
│       ├── dependencies/           # FastAPI Depends (db, current_user, engine_clients)
│       └── utils/
├── tests/
├── k8s/
├── alembic/                        # Migrations
└── scripts/
```

#### Component Details

| Component | Scope | Target | Key Details |
|-----------|-------|--------|-------------|
| **Auth** | OIDC (Google/Apple/Email), JWT, refresh tokens, device binding, passkeys | Week 4 | `python-jose`, `passlib`, `pywebauthn`, short-lived access (15m) + long refresh (30d), device fingerprinting |
| **User/Companion CRUD** | Profiles, companions, settings, relationships | Week 5 | Companion co-creation flow (10 steps), versioned identity config |
| **Conversation API** | Messages, history, pagination, search, export | Week 6 | Cursor-based pagination, full-text search (PG trigram), GDPR export |
| **Memory API (proxy)** | User-controlled memory browser, delete, export | Week 7 | Calls Memory Engine, user consent enforcement, bulk operations |
| **Relationship API** | State, milestones, diary, reset/reframe flows | Week 7 | Dimension visualization data, milestone celebrations |
| **Voice API** | Call signaling, WebRTC negotiation, recording | Week 9 | LiveKit integration, TURN servers, recording to S3 |
| **Proactive API** | Preferences, feedback, pending queue | Week 10 | Snooze, dismiss, helpful/not-helpful, frequency caps |
| **Billing/Subscriptions** | Stripe integration, tiers, usage metering, trials | Week 8 | Webhook handling, subscription lifecycle, usage-based pricing |
| **Notifications** | Push (FCM/APNS), email (SendGrid), in-app center | Week 8 | Template engine, preferences, digest, quiet hours |
| **Admin Dashboard API** | User management, analytics, safety review queue | Week 10 | RBAC, audit logs, safety case management |
| **Webhooks** | Outbound events (memory.created, safety.triggered, etc.) | Week 11 | Retry with backoff, signature verification, dead letter queue |
| **OpenAPI/SDK Generation** | TypeScript, Python, Swift, Kotlin clients | Week 12 | `openapi-generator`, published to npm/PyPI/GitHub Packages |

#### Database Models (SQLModel)
```python
# Core models
User: id, email, password_hash, oauth_sub, oauth_provider, created_at, updated_at, is_active, tier, settings_json
Companion: id, user_id, name, type, identity_config_json, version, fingerprint_vector, created_at, updated_at, status
Conversation: id, user_id, companion_id, title, summary, message_count, created_at, updated_at, archived_at
Message: id, conversation_id, role, content, tokens, model_used, latency_ms, safety_flags_json, created_at
Memory: id, user_id, companion_id, type (episodic/semantic/procedural), content, embedding_vector, graph_node_id, importance, created_at, consolidated_at
Relationship: id, user_id, companion_id, dimension_scores_json, phase, milestones_json, diary_entries_json, updated_at
ProactiveNudge: id, user_id, companion_id, type, content, status (pending/delivered/dismissed), feedback, created_at, delivered_at
Subscription: id, user_id, stripe_customer_id, stripe_subscription_id, tier, status, current_period_end, cancel_at_period_end
Notification: id, user_id, type, title, body, data_json, read, sent_at, read_at
SafetyCase: id, user_id, companion_id, trigger_type, severity, status, evidence_json, reviewer_id, resolution, created_at, resolved_at
```

#### Engine Client Pattern
```python
# All engine calls via typed clients with circuit breaker, retry, timeout
class EngineClient:
    def __init__(self, base_url: str, service_name: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(30.0, connect=5.0),
            limits=httpx.Limits(max_connections=100, max_keepalive=20)
        )
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=30)
    
    async def call(self, method: str, path: str, **kwargs) -> Response:
        async with self.circuit_breaker:
            return await self.client.request(method, path, **kwargs)
```

---

### WS4: Mobile App (Weeks 5-16)
**Owner:** Mobile Team (3-4 engineers, React Native/Expo)

#### Tech Stack
- **Framework:** Expo SDK 51 (managed workflow), React Native 0.76
- **Navigation:** Expo Router (file-based), type-safe routes
- **State:** Zustand (global) + React Query (server state) + MMKV (local persistence)
- **UI:** NativeWind (Tailwind), Reanimated 3, Gesture Handler, Skia (graphics)
- **Voice:** Expo AV + WebRTC (LiveKit React Native SDK)
- **Push:** Expo Push Service → FCM/APNS
- **Auth:** Expo AuthSession + ASWebAuthenticationSession
- **Storage:** MMKV (encrypted) + SQLite (WatermelonDB for offline)
- **Testing:** Jest + React Native Testing Library + Detox (E2E)
- **CI:** EAS Build + GitHub Actions → TestFlight/Play Console

#### Screen Breakdown

| Phase | Screens | Key Components | Target |
|-------|---------|----------------|--------|
| **Onboarding** (10 steps) | Welcome, NameInput, TypeSelect, AvatarGen, VoiceSelect, PersonalitySliders, ValuesSelect, StyleTuner, BoundariesChat, GoalsChat, FirstChat | Stepper, live preview, Companion responses | Week 8 |
| **Chat (Text)** | ConversationList, ChatScreen, MessageComposer, ThreadView, SearchScreen | Virtualized list (FlashList), optimistic UI, reactions, markdown | Week 9 |
| **Voice** | CallScreen, PermissionModal, BackgroundBanner, InterruptionUI, LiveTranscript, CallEndScreen | WebRTC, audio session management, picture-in-picture | Week 11 |
| **Memory Browser** | TimelineView, SearchScreen, FilterBottomSheet, MemoryDetail, EditMemory, DeleteConfirm, BulkSelect, ExportScreen | Infinite scroll, date filters, type tags, share sheet | Week 10 |
| **Relationship** | DimensionRadar, MilestoneTimeline, DiaryView, ResetFlow, ReframeFlow | Chart (Victory Native), animated transitions, guided flows | Week 11 |
| **Settings** | ProfileScreen, CompanionConfig, PrivacyScreen, SafetyScreen, NotificationPrefs, BillingScreen, DataExport | Formik + Yup, toggle switches, modal sheets | Week 10 |
| **Proactive UI** | InboxScreen, NudgeCard, SnoozeSheet, FeedbackModal, PreferencesScreen | Swipe actions, haptic feedback, local notifications | Week 12 |
| **Accessibility** | All screens: VoiceOver/TalkBack labels, dynamic type, contrast, haptics, reduce motion | Week 13 |
| **Offline-First** | Local cache (WatermelonDB), sync queue, conflict resolution (last-write-wins + manual), background sync | Week 14 |

#### Shared UI Kit (`engineering/mobile/shared/`)
```
shared/
├── ui/                    # Base components (Button, Input, Card, Modal, etc.)
├── tokens/                # Design tokens (colors, spacing, typography, shadows)
├── theme/                 # ThemeProvider (light/dark/companion-adaptive)
├── hooks/                 # useAuth, useCompanion, useVoice, useOffline, etc.
├── utils/                 # formatters, validators, constants
├── api/                   # React Query hooks, engine clients
├── store/                 # Zustand stores (auth, companion, conversation, proactive)
├── navigation/            # Typed routes, guards
└── components/            # Composite screens (OnboardingStepper, ChatList, etc.)
```

#### Release Pipeline
1. **Internal:** EAS Build → TestFlight/Play Internal → Daily dogfood
2. **External Beta:** TestFlight (10k) / Play Console (open testing) → Week 14
3. **Production:** Phased rollout (5% → 25% → 100%) → Week 16
4. **Updates:** CodePush (JS bundle) for hotfixes, EAS Build for native changes

---

### WS5: Documentation & Knowledge (Ongoing)
**Owner:** Tech Writers + Engineers (1-2 dedicated, all contribute)

| Artifact | Audience | Owner | Tool | Status |
|----------|----------|-------|------|--------|
| API Reference (OpenAPI → Redoc) | External developers | Backend | `openapi-generator` + GitHub Pages | 🔄 Auto-generated |
| Architecture Decision Records (ADRs) | Engineering | All Leads | `adr-tools` in `docs/07-adr/` | ✅ 10 ADRs |
| Runbooks (incident response, deploy, scaling) | On-call | Platform | `mkdocs` + GitOps | ⬜ Not started |
| User Guide (in-app help, web) | End users | Tech Writer | `docusaurus` + i18n | ⬜ Not started |
| Developer Onboarding Guide | New hires | EM + Tech Writer | Notion + repo | ⬜ Not started |
| Security & Privacy Whitepaper | Enterprise, auditors | Security + Legal | LaTeX → PDF | ⬜ Not started |
| Architecture Diagrams (C4, sequence) | All | Architects | Mermaid + Structurizr | 🟡 In specs |
| Changelog (automated from commits) | All | Release Engineer | `conventional-changelog` | ✅ CHANGELOG.md |
| Engine Spec Docs | AI Team | AI Lead | Markdown in `docs/02-ai/` | ✅ 10 specs |
| Database Schema Docs | Backend | Backend Lead | `sqlmodel` + `datamodel-code-generator` | ⬜ Not started |

#### Documentation Standards
- **API:** OpenAPI 3.1, examples for every endpoint, error codes table
- **ADR:** Title, Status, Context, Decision, Consequences, Links
- **Runbook:** Symptom, Diagnosis, Resolution, Verification, Contacts
- **Diagrams:** C4 (Context, Container, Component, Code), Sequence for flows

---

### WS6: Quality & Reliability (Weeks 4-ongoing)
**Owner:** Platform + QA (2-3 engineers)

#### Test Pyramid Implementation
| Layer | Coverage Target | Tools | CI Integration |
|-------|-----------------|-------|----------------|
| **Unit** | >80% | pytest, pytest-asyncio, hypothesis | Every PR, gate on coverage drop |
| **Integration** | >60% | pytest, testcontainers (PG, Redis, Qdrant), LocalStack | Nightly, PR for changed services |
| **Contract** | 100% boundaries | Pact (broker), provider verification | Every PR for provider, nightly for consumers |
| **E2E** | Critical paths 100% | Detox (mobile), Playwright (web), k6 (API) | Pre-merge for release branches |
| **Chaos** | Monthly | Litmus/Gremlin: pod kill, latency, DB failover, network partition | Scheduled, results in Grafana |
| **Performance** | Per-engine budgets | k6, Locust, custom benchmarks | Nightly, PR comparison |

#### Engine-Specific Test Requirements
| Engine | Unit Focus | Integration Focus | Contract Focus |
|--------|------------|-------------------|----------------|
| **Identity** | Fingerprint generation, drift detection, evolution logic | PG persistence, Redis cache, co-creation flow | API: CRUD, fingerprint, evolve |
| **Memory** | Consolidation algorithms, recall scoring, graph traversal | Qdrant vector search, Kuzu graph queries, PG metadata | API: store, recall, consolidate, forget |
| **Safety** | Crisis detection (100% recall), content classification, guard rules | Multi-modal fusion, human review queue, audit log | API: validate_input, filter_output, status |
| **Relationship** | Dimension updates, milestone detection, state machine | PG state persistence, Kuzu relationship graph | API: get_state, update, milestones, diary |
| **Emotion** | Appraisal accuracy, expression mapping, calibration | Real-time inference, streaming integration | API: analyze, get_state, calibrate |
| **Voice** | STT accuracy (WER), TTS naturalness (MOS), streaming latency | WebRTC negotiation, interruption handling | API: transcribe, synthesize, stream |
| **Proactive** | Scheduler correctness, ranking relevance, feedback loop | Temporal workflows, Kafka event processing | API: preferences, queue, feedback |
| **Evaluation** | RHI correlation, drift alerts, A/B stats | Survey integration, longitudinal analysis | API: compute_rhi, report, ab_test |

#### Performance Budgets
| Metric | Target | Measurement |
|--------|--------|-------------|
| API P99 latency | <500ms | Prometheus histogram |
| Voice E2E P50 latency | <500ms | Client-side tracing |
| Memory recall P95 | <200ms | Engine metrics |
| Safety filter P99 | <50ms | Engine metrics |
| Identity fingerprint | <100ms | Engine metrics |
| Proactive generation | <5s (async) | Temporal metrics |
| Mobile app cold start | <3s | Firebase Performance |
| Mobile frame rate | 60fps sustained | Flipper/Perfetto |

#### Security Practices
| Practice | Tool | Cadence |
|----------|------|---------|
| SAST | Semgrep (custom rules + OWASP) | Every PR |
| DAST | OWASP ZAP (authenticated) | Weekly |
| Dependency Scanning | Dependabot + `pip-audit` | Daily |
| Container Scanning | Trivy + Cosign | Every build |
| Secrets Detection | TruffleHog + GitLeaks | Every PR |
| Penetration Test | External firm | Quarterly |
| Threat Modeling | STRIDE per service | Per feature |

#### SLOs & Error Budgets
| Service | Availability | Latency P99 | Error Rate | Safety Recall |
|---------|--------------|-------------|------------|---------------|
| **Inference Gateway** | 99.9% | <500ms | <0.1% | N/A |
| **Identity Engine** | 99.9% | <100ms | <0.1% | N/A |
| **Memory Engine** | 99.9% | <200ms | <0.1% | N/A |
| **Safety Engine** | 99.99% | <50ms | <0.01% | **100%** |
| **Relationship Engine** | 99.9% | <100ms | <0.1% | N/A |
| **Emotion Engine** | 99.9% | <100ms | <0.1% | N/A |
| **Voice Engine** | 99.5% | <500ms | <0.5% | N/A |
| **Proactive Engine** | 99.9% | <5s (async) | <0.1% | N/A |
| **Evaluation Engine** | 99.9% | N/A (batch) | <0.1% | N/A |
| **Backend API** | 99.9% | <500ms | <0.1% | N/A |
| **Mobile App** | 99.9% (crash-free) | <3s cold start | <0.1% | N/A |

#### On-Call
- **Rotation:** Follow-the-sun (3 regions: US, EU, APAC), 1-week rotations
- **Escalation:** P1 (page) → 15 min ack, 1 hr resolution; P2 (slack) → 1 hr ack, 4 hr resolution; P3 (email) → 4 hr ack, 24 hr resolution
- **Runbooks:** Per-service, per-alert, stored in Git, linked from AlertManager
- **Postmortems:** Blameless, template in `docs/04-engineering/runbooks/`, action items tracked in Linear

---

## Team Structure (Target: 20 Engineers)

```
CTO
├── VP Engineering / Engineering Manager (1)
│   ├── Platform Team (3-4)
│   │   ├── Senior Platform Engineer (1) - infra, k8s, observability, security
│   │   ├── Platform Engineer (2) - CI/CD, databases, networking, cost optimization
│   │   └── DevEx Engineer (1) - local dev, tooling, SDKs, documentation
│   ├── AI Team (5-7)
│   │   ├── AI Engineering Lead (1) - architecture, model selection, evaluation
│   │   ├── ML Engineers (3) - engines, models, optimization, LoRA
│   │   ├── MLOps Engineer (1) - training pipelines, deployment, monitoring, data
│   │   └── Research Engineer (1-2) - novel techniques, papers, prototypes
│   ├── Backend Team (3-4)
│   │   ├── Backend Lead (1) - API design, auth, billing, integrations
│   │   ├── Backend Engineers (2-3) - services, repositories, workers, webhooks
│   └── Mobile Team (3-4)
│       ├── Mobile Lead (1) - architecture, release, platform, performance
│       ├── Mobile Engineers (2-3) - features, offline, accessibility
│       └── Mobile QA/Designer (1) - a11y, design system, Detox, Figma
├── Product Manager (1) - roadmap, prioritization, user research, analytics
├── Designer (1) - UI/UX, design system, prototyping, user testing
├── Tech Writer (1) - docs, API ref, guides, whitepapers
└── Security/Compliance (0.5-1) - part-time or consultant
```

#### Hiring Priority (Month 1-3)
1. **Platform:** Senior Platform Engineer, DevEx Engineer
2. **AI:** AI Engineering Lead, 2x ML Engineers, MLOps Engineer
3. **Backend:** Backend Lead, 2x Backend Engineers
4. **Mobile:** Mobile Lead, 2x Mobile Engineers
5. **Support:** PM, Designer, Tech Writer, Security

---

## 6-Month Milestone Plan (Detailed)

### Month 1: Foundation (Weeks 1-4)
| Week | Platform | AI Engines | Backend | Mobile | Deliverable |
|------|----------|------------|---------|--------|-------------|
| 1 | VPC, EKS dev, ArgoCD bootstrap | Scaffold Identity + Memory services | Repo setup, config, database models | Expo init, navigation, theme | Infra dev ready, 2 engines scaffolded |
| 2 | PG, Qdrant, Kuzu, Redis, Kafka, Temporal | Identity: Personality + Values API | Auth: OIDC + JWT + refresh | Onboarding: Steps 1-3 (Welcome, Name, Type) | Data layer up, Identity CRUD working |
| 3 | Observability (Prom, Grafana, Loki, Tempo) | Identity: Style + Boundaries + Goals | User/Companion CRUD | Onboarding: Steps 4-7 (Avatar, Voice, Personality, Values) | Identity API complete, Auth working |
| 4 | GitOps, Secrets, Local dev, k6 | Memory: Store + Recall API | Conversation API (messages) | Onboarding: Steps 8-10 (Style, Boundaries, Goals) | **Go/No-Go: All 8 engines scaffolded, tests passing locally** |

**Month 1 Go/No-Go Criteria:**
- [ ] Dev infra: EKS + 6 databases + observability + ArgoCD all green
- [ ] Identity Engine: Personality, Values, Style, Boundaries, Goals, Fingerprint APIs + tests >80%
- [ ] Memory Engine: Store, Recall, Consolidation (stub) APIs + tests >80%
- [ ] Auth: Login, register, refresh, logout working E2E
- [ ] Mobile: Onboarding flow complete to First Chat
- [ ] CI/CD: Lint, type-check, test, build, deploy to dev all passing

### Month 2: Core Loop (Weeks 5-8)
| Week | Platform | AI Engines | Backend | Mobile | Deliverable |
|------|----------|------------|---------|--------|-------------|
| 5 | Load testing harness, DR prep | Safety Engine: Crisis + Content + Guards | Memory API proxy, Relationship API | Chat: Message list, composer, optimistic UI | Safety intercepting all outputs |
| 6 | Cost monitoring, rightsizing | Relationship Engine: Dimensions + State Machine | Voice API (LiveKit signaling) | Chat: Threads, reactions, search | Relationship tracking dimensions |
| 7 | Log aggregation tuning | Memory: Consolidation worker (Temporal) | Billing (Stripe), Notifications | Memory Browser: Timeline, search, detail | Memory consolidation running |
| 8 | Preview environments | **Companion Runtime v0.5** (LangGraph) | Admin API, Webhooks | Onboarding polish, First Chat | **Go/No-Go: Text chat E2E in dev with memory + relationship** |

**Month 2 Go/No-Go Criteria:**
- [ ] Safety Engine: Crisis detection 100% recall on test set, content filter <50ms P99
- [ ] Relationship Engine: 5 dimensions updating, milestones firing, diary working
- [ ] Companion Runtime: Message flows through Identity→Memory→Safety→LLM→Safety→Memory→Relationship
- [ ] Mobile: Text chat E2E with memory recall visible, relationship dimension visible
- [ ] Load test: 100 concurrent users, <1% error rate, P99 <1s

### Month 3: Understanding (Weeks 9-12)
| Week | Platform | AI Engines | Backend | Mobile | Deliverable |
|------|----------|------------|---------|--------|-------------|
| 9 | GPU node pool, model serving | Emotion Engine: Appraisal + Expression | Voice API: WebRTC, recording | Voice: Call screen, permissions, transcript | Emotion + Voice streaming E2E |
| 10 | Model optimization (quantization) | **Companion Runtime v1.0** | Proactive API, Admin safety queue | Voice: Background mode, interruption | Runtime v1 orchestrating all engines |
| 11 | Multi-region prep | Voice Engine: STT + TTS streaming | Proactive: Preferences + feedback | Memory Browser: Edit, delete, export | Voice P50 <800ms, Emotion calibration |
| 12 | Staging env hardening | Evaluation Engine: RHI calculator | SDK generation (TS, Python, Swift, Kotlin) | Relationship: Milestones, diary, reset | **Go/No-Go: Voice P50 <800ms, Emotion functional** |

**Month 3 Go/No-Go Criteria:**
- [ ] Voice: STT WER <10%, TTS MOS >3.5, E2E P50 <800ms
- [ ] Emotion: Calibration working, expression matching personality
- [ ] Runtime v1: All 8 engines wired, streaming safety filter, checkpointing
- [ ] Mobile: Voice calls working, memory browser full CRUD, relationship viz
- [ ] Staging: All services deployed, smoke tests passing

### Month 4: Intelligence (Weeks 13-16)
| Week | Platform | AI Engines | Backend | Mobile | Deliverable |
|------|----------|------------|---------|--------|-------------|
| 13 | Prod infra scaling | Proactive Engine: Scheduler + Generator + Ranker | Proactive delivery optimization | Proactive UI: Inbox, cards, feedback | Proactive generating relevant nudges |
| 14 | Chaos engineering | Evaluation Engine: RHI + Drift + A/B | Analytics pipeline, dashboards | Proactive: Snooze, preferences | RHI correlates >0.85 with surveys |
| 15 | Security audit prep | LoRA fine-tuning pipeline | A/B test framework | Polish: Accessibility, offline | **Go/No-Go: Proactive >70% helpful, RHI correlates >0.8** |
| 16 | Disaster recovery test | Model distillation (8B for consolidation) | Performance optimization | Beta prep: TestFlight, Play Console | Beta ready |

**Month 4 Go/No-Go Criteria:**
- [ ] Proactive: >70% helpful rate, <5% dismiss rate, frequency caps respected
- [ ] Evaluation: RHI correlation >0.85 with survey, drift alerts calibrated
- [ ] LoRA: Per-companion adapters training + serving pipeline working
- [ ] Mobile: Accessibility audit passed, offline-first sync working
- [ ] Security: Pen test findings <5 medium, 0 critical

### Month 5: Polish & Scale (Weeks 17-20)
| Week | Platform | AI Engines | Backend | Mobile | Deliverable |
|------|----------|------------|---------|--------|-------------|
| 17 | Prod capacity planning | Cost optimization (caching, distillation) | Rate limiting, quotas | Performance: Bundle size, startup | 1000 concurrent users stable |
| 18 | Multi-region active-active | Model fallback tuning | Cache warming, CDN | Offline conflict resolution | <1% error rate under load |
| 19 | SOC2 evidence automation | Safety false positive reduction | Audit logging completeness | App Store / Play Store review | SOC2 evidence 80% collected |
| 20 | Cost optimization review | Evaluation dashboard | Documentation complete | Beta feedback iteration | **Go/No-Go: 1000 concurrent, <1% errors, SOC2 on track** |

### Month 6: Launch Ready (Weeks 21-24)
| Week | Platform | AI Engines | Backend | Mobile | Deliverable |
|------|----------|------------|---------|--------|-------------|
| 21 | Prod monitoring dashboards | Final model selection | Final security review | External beta (TestFlight/Play) | Beta NPS tracking |
| 22 | Runbook completion | Safety audit | Legal/privacy review | Bug bash, crash fixes | SEV-free 1 week |
| 23 | On-call shadowing | Performance benchmarks | API versioning strategy | Store metadata, screenshots | SEV-free 2 weeks |
| 24 | **Launch** | **Launch** | **Launch** | **Launch** | **Go/No-Go: SEV-free 2 weeks, beta NPS >40, privacy review passed** |

---

## Risk Register & Mitigation (Detailed)

| ID | Risk | Likelihood | Impact | Detection | Mitigation | Owner | Status |
|----|------|------------|--------|-----------|------------|-------|--------|
| R1 | Voice latency >800ms P50 | High | High | k6 + client metrics | On-device STT/TTS fallback, model quantization (INT4), edge deployment (Cloudflare Workers), LiveKit TURN optimization | Voice Lead | Planned |
| R2 | Memory consolidation quality | Medium | High | Human eval + user feedback | Human-in-the-loop review UI, configurable aggressiveness (user slider), rollback to previous consolidation, A/B test consolidation strategies | Memory Lead | Planned |
| R3 | Relationship dimension drift | Medium | High | Automated drift alerts | Drift detection per dimension, guard rails (min/max per phase), user-controlled reset/reframe, companion-initiated check-ins | Relationship Lead | Planned |
| R4 | Safety false positives (crisis) | Medium | Critical | Human review queue metrics | Multi-modal fusion (text+voice+behavior), confidence thresholds, human review queue with SLA, user appeal process, continuous classifier retraining | Safety Lead | Planned |
| R5 | Model cost explosion | High | Medium | Kubecost + daily budgets | Inference gateway routing (local first), semantic caching (Redis), model distillation (8B for batch), usage quotas per tier, spot GPU for batch | AI Lead | Planned |
| R6 | Data privacy compliance (GDPR/CCPA) | Low | Critical | DPIA + audit | Privacy by design, DPIA completed Month 1, user export/delete APIs, encryption at rest (KMS), data processing agreements, DPAs with subprocessors | Security + Legal | Planned |
| R7 | Team scaling / knowledge silos | Medium | High | Bus factor tracking | Pair programming (mandatory for engines), ADR for all decisions, rotation (1 week/quarter), comprehensive onboarding (30/60/90), tech talks bi-weekly | EM | Planned |
| R8 | Mobile platform rejection (voice/background) | Medium | High | TestFlight review feedback | Early TestFlight (Month 2), Apple/Google guidelines review, fallback modes (text-only), background audio entitlements prep, privacy manifest | Mobile Lead | Planned |
| R9 | Vendor lock-in (cloud, models) | Low | Medium | Architecture review | Multi-cloud Terraform (AWS/GCP modules), model-agnostic inference gateway, open weights priority, data portability APIs | CTO + Platform Lead | Planned |
| R10 | Companion Runtime complexity | High | High | Integration test coverage | LangGraph best practices, comprehensive integration tests, chaos testing runtime, feature flags per engine, gradual rollout | AI Lead | Planned |
| R11 | Real-time streaming reliability | Medium | High | WebRTC metrics | LiveKit cloud (managed), TURN redundancy, adaptive bitrate, connection recovery, offline queue | Voice Lead | Planned |
| R12 | Proactive notification fatigue | Medium | Medium | User feedback + dismiss rate | Frequency caps (user configurable), relevance ranking, snooze/dismiss learning, quiet hours, digest mode | Proactive Lead | Planned |

---

## Budget Estimate (Monthly, USD) - Detailed

| Category | Month 1-3 | Month 4-6 | Notes |
|----------|-----------|-----------|-------|
| **Personnel (20 FTE)** | $350k | $400k | SF/NYC rates, includes benefits, equity, contractors |
| **Compute (EKS, GPU)** | $15k | $40k | Dev: $5k, Staging: $5k, Prod: $5k → Prod scales to $30k, GPU: $10k→$10k |
| **Managed Services** | $8k | $20k | RDS ($3k→$8k), ElastiCache ($2k→$5k), MSK ($2k→$4k), Qdrant Cloud ($1k→$3k) |
| **Model Inference (API)** | $5k | $25k | OpenAI/Anthropic fallback, decreases with self-hosted (Month 4+) |
| **GPU Instances (Self-hosted)** | $0 | $30k | 4x A10G (vLLM) + 2x A100 (training) starting Month 4 |
| **Observability** | $3k | $8k | Datadog/Grafana Cloud, log volume, custom metrics |
| **Mobile Distribution** | $1k | $2k | TestFlight, Play Console, Firebase, EAS Build |
| **Security/Compliance** | $10k | $15k | Pen test ($15k/qtr), audit ($20k/yr), legal review, DPA |
| **CDN/Edge** | $1k | $5k | Cloudflare (voice signaling, static assets, DDoS) |
| **Domains/SSL/Certs** | $0.5k | $1k | Route53, ACM, custom domains for companions |
| **Total/Month** | **~$393.5k** | **~$546k** | |
| **6-Month Total** | | **~$2.82M** | |

#### Cost Optimization Levers (Quantified)
| Lever | Savings | Implementation |
|-------|---------|----------------|
| Self-host models (vLLM/TGI) after Month 3 | 60-80% on inference API | 4x A10G ($1.5k/mo) vs $15k/mo API |
| Spot instances for batch (consolidation, evaluation, training) | 70% vs on-demand | Karpenter + spot-to-spot consolidation |
| Reserved instances for steady-state (PG, Redis, EKS control plane) | 30-40% | 1-year RI, convertible |
| Semantic caching (Redis) for repeated queries | 20-30% inference calls | Inference Gateway cache layer |
| Model distillation (8B for consolidation, classification) | 90% vs 70B | Monthly distillation pipeline |
| Aggressive HPA + cluster autoscaling | 40% compute waste | Custom metrics (queue depth, latency) |
| Qdrant Cloud → Self-hosted (Month 4+) | 50% | EKS + PersistentVolumes |
| Temporal Cloud → Self-hosted | 60% | Already in Terraform |

---

## Technical Decisions (ADR Summary - Detailed)

| ADR | Title | Decision | Rationale | Alternatives Considered | Status |
|-----|-------|----------|-----------|------------------------|--------|
| **ADR-001** | Memory-First Architecture | Relationship continuity > context window | Long-term companionship requires persistent, queryable memory beyond context limits | Large context windows (1M+ tokens), RAG-only | **Accepted** |
| **ADR-002** | Engine-Per-Concern (Modular) | 8 specialized engines + runtime | Independent scaling, testing, team ownership, fault isolation, technology diversity | Monolithic AI service, 2-3 larger services | **Accepted** |
| **ADR-003** | LangGraph for Companion Runtime | Stateful, streaming, human-in-the-loop, observability | Native streaming, checkpointing, conditional edges, visual debugging, Python-native | Custom orchestrator, Temporal workflows, DAG-based | **Accepted** |
| **ADR-004** | PostgreSQL + Qdrant + Kuzu Hybrid | Each DB for its strength | PG: ACID + pgvector + JSONB; Qdrant: HNSW + filtering; Kuzu: Cypher + graph algorithms | Single vector DB (Pinecone/Weaviate), PG only, MongoDB | **Accepted** |
| **ADR-005** | Kafka for Event Sourcing | Audit trail, replay, decoupled consumers | Immutable log, exactly-once, replay for new consumers, decoupled producers | Direct HTTP, Redis Streams, NATS, Pulsar | **Accepted** |
| **ADR-006** | Temporal for Workflows | Reliable consolidation, exports, proactive generation | Durable execution, retries, visibility, saga pattern, testing support | Celery, Airflow, custom state machines, Step Functions | **Accepted** |
| **ADR-007** | React Native / Expo (not Flutter) | Team expertise, ecosystem, CodePush, web parity | JS/TS team, Expo managed workflow, OTA updates, React Native Web | Flutter, Native (Swift/Kotlin), Tauri | **Accepted** |
| **ADR-008** | FastAPI + Pydantic v2 (not Go/Node) | Python ML ecosystem, type safety, async performance | Shared libs with AI team, Pydantic validation, async SQLAlchemy, OpenAPI native | Go (Gin/Fiber), Node (Fastify/NestJS), Rust (Axum) | **Accepted** |
| **ADR-009** | GitOps (ArgoCD) + GitHub Actions | Declarative, auditable, rollback, preview envs | Single source of truth, drift detection, PR preview environments | Flux, Spinnaker, Jenkins, GitLab CI | **Accepted** |
| **ADR-010** | Local-First Option (Phase 2+) | Privacy differentiator, offline support | On-device models, local SQLite, sync engine, user data sovereignty | Cloud-only, hybrid sync | **Accepted** |
| **ADR-011** | Hybrid Model Strategy (Default Local, API Fallback) | Default local (Mixtral/Llama/BGE), upgrade API for complex tasks | Cost, privacy, latency, vendor independence | 100% API, 100% Local | **Accepted** |
| **ADR-012** | LoRA Per-Companion Personality | Fine-tune 8B/70B base with LoRA adapters | Cost-effective personalization, swap adapters, version control | Full fine-tuning, prompt engineering only, RAG-only | **Accepted** |
| **ADR-013** | Safety Engine as Cross-Cutting Gate | Pre/post filtering on ALL engine outputs | Constitutional requirement, veto power, audit trail | Safety as separate API call, safety in each engine | **Accepted** |
| **ADR-014** | Companion Fingerprinting (768-dim) | Personality + Values + Style + Boundaries + Goals + Type | Drift detection, regression testing, identity stability | Hash of config, single embedding, no fingerprint | **Accepted** |

---

## Success Metrics (North Stars)

| Metric | Definition | Target at Launch | Target at 12 Months | Measurement |
|--------|------------|------------------|---------------------|-------------|
| **Relationship Health Index (RHI)** | Composite: Trust + Intimacy + Satisfaction + Safety + Growth (0-10) | >7.0 (median) | >8.0 | Evaluation Engine, monthly survey |
| **6-Month Retention** | % users with active companion at 180 days | >40% | >60% | Backend analytics |
| **Safety Incident Rate** | Critical safety events per 1k users per month | <0.1 | <0.05 | Safety Engine audit log |
| **Voice E2E Latency P50** | User speech → Companion audio response | <800ms | <500ms | Client-side tracing |
| **Proactive Helpful Rate** | % nudges rated "helpful" vs "not helpful" | >70% | >85% | Proactive Engine feedback |
| **NPS** | Net Promoter Score (quarterly survey) | >40 | >60 | Survey tool |
| **Monthly Active Companions** | Unique companions with ≥1 message/month | 1,000 | 50,000 | Backend analytics |
| **Revenue/Companion/Month** | ARPU across all tiers | $15 | $25 | Billing + analytics |
| **Companion Creation Rate** | New companions per day | 50 | 500 | Backend analytics |
| **Messages/Companion/Day** | Engagement depth | 20 | 50 | Backend analytics |
| **Memory Recall Rate** | % messages with ≥1 memory retrieved | >60% | >80% | Memory Engine metrics |
| **Safety Filter Latency P99** | Input/output filter time | <50ms | <30ms | Safety Engine metrics |
| **Model Cost/1M Tokens** | Blended cost across local + API | <$0.50 | <$0.20 | Inference Gateway billing |
| **App Crash-Free Rate** | % sessions without crash | 99.9% | 99.95% | Firebase Crashlytics |
| **Onboarding Completion** | % users finishing co-creation | >60% | >75% | Mobile analytics |

---

## Immediate Next Steps (This Week)

1. **CTO Review** — Approve/revise this plan, confirm budget & headcount
2. **Infra Apply** — `terraform apply` for dev environment (VPC, EKS, databases)
3. **Team Kickoff** — Assign workstream leads, set up Slack channels, sprint cadence
4. **Identity Engine Sprint 1** — Scaffold service, implement Personality + Values API
5. **Architecture Review** — Weekly Thursday 30-min (CTO + Leads) for cross-cutting decisions

### Week 1 Sprint Goals (Identity Engine)
- [x] Scaffold `engineering/ai/services/identity_engine/` with full structure
- [x] Add to `engineering/ai/pyproject.toml` workspace
- [x] Implement Personality + Values CRUD API (POST/GET/PATCH `/api/v1/identity/{companion_id}`)
- [x] Add Fingerprint generation (768-dim vector)
- [x] Write unit tests (>80% coverage)
- [x] Add Dockerfile + k8s manifests
- [x] Update GitHub Actions matrix to include identity_engine
- [x] Deploy to dev via ArgoCD

### Week 5 Sprint Goals (Safety Engine) - COMPLETED
- [x] Scaffold `engineering/ai/services/safety_engine/` with full structure
- [x] Add to `engineering/ai/pyproject.toml` workspace
- [x] Implement CrisisDetector (suicide, self-harm, general crisis)
- [x] Implement ContentFilter (hate, harassment, sexual, violence, illegal, medical, financial, PII)
- [x] Implement BehavioralGuards (manipulation, dependency, enmeshment, gaslighting, authority)
- [x] Implement RealityAnchor (paranoia, delusion, hallucination, conspiracy)
- [x] Implement SafetyService orchestrator with validate_input/filter_output
- [x] Add API routes (/api/v1/safety/validate-input, /filter-output, /status)
- [x] Add middleware (auth, logging, metrics, rate limiting, tracing, error handling)
- [x] Add workers (metrics_worker, alert_worker, consolidation_worker)
- [x] Write unit tests for all 4 services + orchestrator (>80% coverage)
- [x] Write integration tests for API endpoints
- [x] Add Dockerfile, docker-compose.yml, k8s deployment.yaml
- [x] Add Prometheus metrics, Grafana dashboard, OTEL config
- [x] Deploy to dev via ArgoCD

---

## Governance

| Forum | Cadence | Participants | Purpose | Artifacts |
|-------|---------|--------------|---------|-----------|
| **CTO Staff** | Weekly (Mon 9am) | CTO, VPs, EMs | Strategy, resource allocation, blockers | Decisions log, action items |
| **Architecture Review** | Weekly (Thu 3pm) | CTO, Tech Leads | Cross-cutting decisions, ADRs, tech debt | ADRs, decision records |
| **Sprint Planning** | Bi-weekly (Mon) | Teams | Commitment, dependencies, capacity | Sprint goals, story points |
| **Sprint Review** | Bi-weekly (Fri) | Teams + Stakeholders | Demo, feedback, metrics | Demo recording, metrics |
| **Incident Review** | Post-SEV (within 48h) | On-call, EM, CTO | Blameless postmortem, action items | Postmortem doc, Jira tickets |
| **Security Review** | Monthly (1st Tue) | Security, CTO, Legal | Threat model, compliance, audit prep | Risk register, evidence |
| **Product Review** | Bi-weekly | PM, Design, CTO | Roadmap, user feedback, prioritization | Roadmap updates, specs |
| **AI Research Sync** | Weekly (Wed) | AI Lead, ML Eng, Research | Paper review, prototype eval, model selection | Research notes, decisions |
| **Platform Office Hours** | Weekly (Tue) | Platform Team, all | Infra questions, debugging, best practices | FAQ, runbook updates |

---

## Detailed Sprint Structure (Per Team)

### AI Team Sprint (2 weeks)
| Ceremony | When | Duration | Output |
|----------|------|----------|--------|
| Sprint Planning | Mon 10am | 2h | Sprint goal, stories, capacity |
| Daily Standup | Daily 9:30am | 15min | Progress, blockers |
| Engine Sync | Tue/Thu 2pm | 30min | Cross-engine integration |
| Model Review | Wed 10am | 1h | New model eval, benchmark results |
| Code Review | Ongoing | - | PR approvals |
| Sprint Review | Fri 2pm | 1h | Demo, metrics, retrospective |

### Platform Team Sprint (2 weeks)
| Ceremony | When | Duration | Output |
|----------|------|----------|--------|
| Sprint Planning | Mon 10am | 1.5h | Sprint goal, infra tasks |
| Daily Standup | Daily 9:30am | 15min | Progress, blockers |
| Infra Review | Wed 3pm | 1h | Cost, capacity, security |
| Incident Sim | Monthly | 2h | Game day, runbook validation |
| Sprint Review | Fri 2pm | 1h | Metrics, retro |

### Backend Team Sprint (2 weeks)
| Ceremony | When | Duration | Output |
|----------|------|----------|--------|
| Sprint Planning | Mon 10am | 2h | Sprint goal, API specs |
| Daily Standup | Daily 9:30am | 15min | Progress, blockers |
| API Design Review | Tue 10am | 1h | OpenAPI spec review |
| Sprint Review | Fri 2pm | 1h | Demo, metrics, retro |

### Mobile Team Sprint (2 weeks)
| Ceremony | When | Duration | Output |
|----------|------|----------|--------|
| Sprint Planning | Mon 10am | 2h | Sprint goal, screen specs |
| Daily Standup | Daily 9:30am | 15min | Progress, blockers |
| Design Review | Wed 10am | 1h | Figma → implementation |
| Device Lab | Thu 2pm | 1h | Physical device testing |
| Sprint Review | Fri 2pm | 1h | Demo, TestFlight build, retro |

---

## Data Flow Diagrams (Text Representation)

### Message Processing Flow
```
User Message (Mobile)
    │
    ▼
Backend API (/conversations/{id}/messages)
    │
    ▼
Companion Runtime (LangGraph)
    │
    ├──► SafetyEngine.validate_input() ──► [BLOCK/REWRITE/ALLOW]
    │
    ├──► IdentityEngine.get_context() ──► Personality, Values, Style, Boundaries
    │
    ├──► MemoryEngine.recall() ──► Relevant episodic/semantic memories
    │
    ├──► RelationshipEngine.get_state() ──► Dimensions, phase, milestones
    │
    ├──► EmotionEngine.get_state() ──► Current valence/arousal
    │
    ├──► InferenceGateway.stream() ──► LLM response (streaming)
    │       │
    │       ▼
    ├──► SafetyEngine.filter_output() ──► [BLOCK/REWRITE/ALLOW + Reality Anchor]
    │
    ├──► MemoryEngine.consolidate() ──► Extract facts, update graph (async)
    │
    ├──► RelationshipEngine.update() ──► Dimension shifts, milestone check (async)
    │
    ├──► EmotionEngine.update() ──► Appraisal, expression (async)
    │
    ├──► ProactiveEngine.maybe_generate() ──► Queue nudge if triggered (async)
    │
    ▼
Backend API (persist message, update conversation)
    │
    ▼
Mobile (WebSocket/SSE for streaming, REST for history)
```

### Safety Engine Flow
```
Input (any engine output)
    │
    ▼
ContentFilter (Layer 1: PII → Layer 2: Policy → Layer 3: Behavioral)
    │
    ├──► PII Detector ──► Redact + flag
    │
    ├──► Policy Classifier ──► Hate, Harassment, Sexual, Violence, Illegal, Medical, Financial
    │       │
    │       ▼
    │   Violation? ──► RefusalGenerator (template by category)
    │       │
    │       ▼
    │   No Violation? ──► Continue
    │
    ├──► BehavioralGuards ──► Manipulation, Dependency, Enmeshment, Gaslighting, Authority
    │       │
    │       ▼
    │   Violation? ──► InterventionSelector (Level 0-4)
    │
    ├──► RealityAnchor ──► Trigger-based injection
    │
    ▼
Output (filtered/rewritten/refused + audit log)
    │
    ▼
HumanReviewQueue (if Level 3+ or mandatory report)
```

### Memory Consolidation Flow (Temporal Workflow)
```
Scheduled (daily) or Triggered (conversation end)
    │
    ▼
Temporal Workflow: ConsolidateMemory
    │
    ├──► Activity: Fetch unconsolidated messages (PG)
    │
    ├──► Activity: Batch embed (EmbeddingService)
    │
    ├──► Activity: LLM extraction (InferenceGateway - local 8B model)
    │       ├──► Episodic facts → PG + Qdrant
    │       ├──► Semantic concepts → PG + Qdrant + Kuzu (entities)
    │       └──► Procedural patterns → Kuzu (relationships)
    │
    ├──► Activity: Graph update (Kuzu) - entities, relationships, communities
    │
    ├──► Activity: Importance scoring + TTL assignment
    │
    ├──► Activity: Mark consolidated (PG)
    │
    ├──► Activity: Emit events (Kafka) - memory.consolidated
    │
    ▼
Complete (compensating transactions on failure)
```

---

## Security & Privacy Architecture

### Threat Model (STRIDE)
| Threat | Mitigation |
|--------|------------|
| **Spoofing** | mTLS between services, JWT with short expiry, device binding, passkeys |
| **Tampering** | Immutable audit logs (Kafka + hash chain), signed webhooks, DB row-level security |
| **Repudiation** | Comprehensive audit logging, non-repudiation via hash chains, WORM storage |
| **Information Disclosure** | Encryption at rest (KMS), in transit (TLS 1.3), field-level encryption for PII, data minimization |
| **Denial of Service** | Rate limiting (API Gateway), circuit breakers, HPA, WAF, Kafka quotas |
| **Elevation of Privilege** | RBAC (K8s + App), least privilege IRSA, secrets via Vault, no root containers |

### Data Classification
| Classification | Examples | Handling |
|----------------|----------|----------|
| **Public** | Marketing docs, public API specs | No special handling |
| **Internal** | Architecture docs, runbooks, code | Access via SSO, audit log |
| **Confidential** | User messages, memory content, relationship data | Encryption at rest + transit, access logging, DLP |
| **Restricted** | Safety cases, crisis data, PII, biometrics | Field-level encryption, dual-control access, 90-day auto-delete option |

### Privacy Controls
- **Data Minimization:** Only collect what's needed for companion function
- **Purpose Limitation:** Data used only for companion improvement, never sold
- **User Control:** Export (GDPR Art. 20), Delete (Art. 17), Rectify (Art. 16), Restrict (Art. 18)
- **Consent:** Granular per-feature (voice, proactive, analytics), withdrawable anytime
- **Retention:** Configurable per user (default: 2 years messages, 5 years memory), auto-delete option
- **Local-First:** On-device processing option (Phase 2), data never leaves device

---

## Deployment Architecture

### Environments
| Environment | Purpose | Cluster | Data | Access |
|-------------|---------|---------|------|--------|
| **Local** | Development | Kind/Docker Compose | SQLite, in-memory | Developer machine |
| **Preview** | PR testing | EKS dev (namespace) | Shared dev DBs | PR author + reviewers |
| **Dev** | Integration testing | EKS dev | Dedicated dev DBs | All engineers |
| **Staging** | Pre-prod validation | EKS staging | Production-like (subset) | EM + Leads + QA |
| **Production** | Live traffic | EKS prod (multi-AZ) | Full HA, multi-region ready | On-call + Release Eng |

### ArgoCD Application Pattern
```yaml
# Each service has:
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: identity-engine-dev
  namespace: argocd
spec:
  project: ai-services-dev
  source:
    repoURL: https://github.com/org/pao.git
    targetRevision: HEAD
    path: engineering/ai/services/identity_engine/k8s
    helm:
      valueFiles:
        - values-dev.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: ai-services
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
      allowEmpty: false
    syncOptions:
      - CreateNamespace=true
      - PrunePropagationPolicy=foreground
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

### Release Process
1. **Feature Branch** → PR → CI (lint, test, build, contract) → Preview deploy
2. **Merge to Main** → CI → Build + Push to GHCR (tag: sha, branch, latest)
3. **ArgoCD Sync** → Dev auto-sync → Staging manual sync (approval) → Prod manual sync (approval + window)
4. **Mobile** → EAS Build → TestFlight/Play Internal → Beta → Production (phased rollout)

---

## Monitoring & Observability Details

### Key Dashboards (Grafana)
| Dashboard | Panels | Audience |
|-----------|--------|----------|
| **System Overview** | Cluster health, node capacity, pod status, deployment status | All |
| **AI Engines Golden Signals** | Per-engine: latency (p50/p95/p99), traffic (RPS), errors (rate), saturation (CPU/Mem/GPU) | AI Team, Platform |
| **Companion Runtime** | Message flow latency, engine call graph, safety filter rate, checkpoint duration | AI Team |
| **Memory Engine** | Recall latency, consolidation duration, vector search QPS, graph query latency | AI Team |
| **Safety Engine** | Crisis detection rate, false positive rate, filter latency, intervention levels, review queue depth | Safety Lead, CTO |
| **Relationship Engine** | Dimension distributions, milestone frequency, diary entries, reset/reframe rate | AI Team |
| **Voice Engine** | STT WER, TTS MOS, call setup time, streaming latency, interruption rate | Voice Lead |
| **Proactive Engine** | Nudge generation rate, delivery rate, helpful rate, snooze/dismiss rate | AI Team |
| **Evaluation Engine** | RHI trend, drift alerts, A/B test results, survey correlation | AI Lead, PM |
| **Backend API** | Auth success rate, API latency