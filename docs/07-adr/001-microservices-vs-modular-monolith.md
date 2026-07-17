# ADR-001: Microservices vs Modular Monolith

**Status:** Accepted
**Date:** 2025-01-15
**Deciders:** CTO, VP Engineering, Staff Engineers
**Consulted:** All Engineering Leads, Security, Platform

---

## Context

PAO needs to choose an architectural style for the backend services. The decision impacts team autonomy, deployment complexity, operational overhead, and long-term maintainability.

### Requirements

- **Team Size**: 15-25 engineers initially, scaling to 100+
- **Domains**: 8 AI engines, User/Companion management, Billing, Safety, Analytics
- **Scale**: 100k DAU → 10M DAU over 3 years
- **Latency**: P99 < 200ms for conversation, < 500ms for proactive
- **Availability**: 99.9% (43 min/month downtime budget)
- **Compliance**: SOC2, ISO27001, GDPR, HIPAA (Enterprise)
- **Deployment**: Multiple regions (US, EU, APAC)

### Options Considered

| Option | Description |
|--------|-------------|
| **A: Microservices** | Independent deployable services per domain |
| **B: Modular Monolith** | Single deployable, strict module boundaries |
| **C: Hybrid (Strangler Fig)** | Start modular monolith, extract services incrementally |

---

## Decision

**We will adopt Option C: Hybrid approach - Start with a Modular Monolith, extract services via Strangler Fig pattern when justified.**

### Initial Architecture (Months 0-12)

```
┌─────────────────────────────────────────────────────────────┐
│                      PAO API (Single Deployable)            │
├─────────┬─────────┬─────────┬─────────┬─────────┬─────────┤
│  User   │Companion│ Memory  │Relationship│Proactive│ Safety │
│ Module  │ Module  │ Module  │ Module   │ Module  │ Module │
├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
│                    Shared Kernel (Auth, Config, Events)   │
├─────────────────────────────────────────────────────────────┤
│              Infrastructure Layer (DB, Cache, Queue)      │
└─────────────────────────────────────────────────────────────┘
```

### Extraction Criteria (When to Extract a Service)

A module graduates to independent service when **ALL** of:

1. **Team Ownership**: Dedicated team (5+ engineers) owning full lifecycle
2. **Scale Independence**: Different scaling profile (CPU vs Memory vs GPU)
3. **Deployment Independence**: Different release cadence or rollout risk
4. **Technology Divergence**: Different language/runtime requirements
5. **Organizational Boundary**: Separate product line or business unit
6. **Compliance Isolation**: Data residency or regulatory boundary

### Planned Extractions (Priority Order)

| Service | Trigger | Target | Rationale |
|---------|---------|--------|-----------|
| **Inference Gateway** | GPU scaling, model routing | Month 6 | Different infra, specialized team |
| **Voice Pipeline** | Real-time streaming, WebRTC | Month 9 | Different tech stack (Rust/Go), latency critical |
| **Safety Engine** | Compliance isolation, audit | Month 12 | Regulatory boundary, separate certifications |
| **Billing/Entitlements** | Business autonomy, partner integration | Month 15 | Different release cycle, sales-owned |
| **Analytics/ML Pipeline** | Batch vs streaming, data science team | Month 18 | Spark/Flink, different skillset |

---

## Consequences

### Positive

- **Faster Initial Velocity**: Single deploy, shared tooling, easier refactoring
- **Lower Operational Burden**: One service to monitor, deploy, secure initially
- **Stronger Consistency**: ACID transactions across domains, simpler debugging
- **Deferred Complexity**: Extract only when pain is real, not speculative
- **Team Flexibility**: Reorganize modules without network boundaries

### Negative

- **Coupling Risk**: Requires discipline to maintain module boundaries
- **Scaling Granularity**: All modules scale together initially
- **Blast Radius**: Bug in one module can affect all
- **Technology Lock-in**: Single runtime (Node.js/TypeScript) initially
- **Future Extraction Cost**: Refactoring effort when extracting

### Mitigations

```typescript
// Architectural Guardrails (enforced in CI)
1. Module boundaries: No cross-module imports (except shared kernel)
2. Database: Separate schemas per module, no cross-module FKs
3. Communication: Domain events only (no direct service calls)
4. Testing: Module tests + contract tests for event schemas
5. Observability: Module-level metrics, traces, logs
6. Deployment: Feature flags for gradual rollout within monolith
```

---

## Implementation Plan

### Phase 1: Foundation (Months 1-3)
- [ ] Set up monorepo with Nx/Turbo
- [ ] Define module structure + shared kernel
- [ ] Implement architectural linting (eslint-plugin-boundaries)
- [ ] CI pipeline: build, test, lint, contract test
- [ ] Observability: module-level dashboards

### Phase 2: Domain Modules (Months 3-9)
- [ ] Implement 6 core modules with clear boundaries
- [ ] Event-driven communication (Kafka/Redpanda)
- [ ] Integration test suite per module
- [ ] Load testing per module

### Phase 3: First Extraction (Month 6-12)
- [ ] Inference Gateway as separate service
- [ ] gRPC/Connect protocol for internal communication
- [ ] Service mesh (Istio) for mTLS, authz, observability
- [ ] Independent CI/CD for extracted service

### Phase 4: Ongoing (Month 12+)
- [ ] Evaluate extraction criteria quarterly
- [ ] Extract services meeting criteria
- [ ] Maintain modular monolith for remaining domains

---

## Alternatives Rejected

### Pure Microservices (Option A)
**Rejected because:**
- 15 engineers cannot effectively own 15+ services
- Operational overhead (service mesh, distributed tracing, debugging) too high early
- Network latency budget consumed by service-to-service calls
- Premature optimization for scale not yet needed

### Pure Modular Monolith (Option B)
**Rejected because:**
- AI Inference (GPU) and Voice (real-time) have fundamentally different scaling needs
- Safety/Compliance will require isolation for certifications
- Billing/Entitlements needs independent releases for partner integrations
- Long-term org structure demands service boundaries

---

## Related Decisions

- ADR-002: API Protocol (REST vs gRPC vs GraphQL)
- ADR-003: Event-Driven Architecture
- ADR-004: Database per Module vs Shared Database
- ADR-005: Service Mesh Adoption Timeline

---

## References

- [Modular Monolith Architecture](https://martinfowler.com/bliki/ModularMonolith.html)
- [Strangler Fig Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html)
- [Team Topologies](https://teamtopologies.com/)
- [Google's Service Weaver](https://github.com/ServiceWeaver/weaver) - relevant for gradual extraction

---

**Approval:**
- CTO: _________________ Date: __________
- VP Engineering: _________________ Date: __________
- Staff Engineer (Platform): _________________ Date: __________