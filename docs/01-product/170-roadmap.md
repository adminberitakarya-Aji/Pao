# PAO Product Roadmap

**Version:** 1.0
**Status:** Draft
**Owner:** PAO Product Team

---

## Roadmap Philosophy

> **Depth over speed. Trust over growth. Relationships over features.**

Each phase builds irreversible infrastructure for the next. We do not move to Phase N+1 until Phase N foundations are rock-solid.

---

## Phase Overview

| Phase | Timeline | Focus | Core Question |
|-------|----------|-------|---------------|
| **1: Foundation** | 2025 H1-H2 | Identity, Memory, Conversation, Voice | "Does the Companion remember me and stay consistent?" |
| **2: Depth** | 2026 H1-H2 | Relationship, Emotion, Proactive, Growth | "Does the Companion understand and grow with me?" |
| **3: Presence** | 2027 H1-H2 | Avatar, Video, AR | "Does the Companion feel present with me?" |
| **4: Ecosystem** | 2028+ | Multi-Companion, Marketplace, SDK | "Can the Companion platform serve diverse needs?" |

---

## Phase 1: Foundation (2025)
**Goal:** Ship a Companion that remembers, stays consistent, and converses naturally via text and voice.

### Milestones

| Milestone | Target | Criteria |
|-----------|--------|----------|
| **M1: Identity Core** | 2025-03 | Personality fingerprint stable, co-creation flow complete, Reality Anchor 100% |
| **M2: Memory Engine** | 2025-05 | 6 memory types operational, cross-modal recall >90%, user CRUD complete |
| **M3: Conversation Runtime** | 2025-07 | 30-day continuous context, <500ms latency, memory relevance >90% |
| **M4: Voice Calling** | 2025-09 | <500ms E2E latency, natural turn-taking, voice identity match >95% |
| **M5: Safety & Privacy** | 2025-10 | Crisis detection 100% recall, export/delete verified, audit passing |
| **M6: Mobile MVP (iOS/Android)** | 2025-11 | Flutter app, offline-capable, onboarding >75% completion |
| **M7: Phase 1 Launch** | 2025-12 | 1000 beta users, Relationship Score >7.0, 0 P0 safety incidents |

### Epics & Stories

| Epic | Stories | Dependencies |
|------|---------|--------------|
| **Identity Engine** | US-01, US-02, US-03, US-04, US-33 | — |
| **Memory Engine** | US-07, US-08, C-07 to C-14 | Identity Engine |
| **Conversation Runtime** | US-05, C-01, C-02 | Memory Engine |
| **Voice Engine** | US-06, C-15 to C-19 | Conversation Runtime |
| **Safety & Privacy** | US-31, US-32, US-34, C-03, C-04 | All engines |
| **Mobile App** | US-01 to US-09 (mobile flows) | Backend APIs |
| **Onboarding** | US-01, US-02, US-03, US-04, US-06 | Identity, Memory |

### Technical Deliverables

- [ ] Identity Engine: Personality fingerprinting, drift detection, co-creation API
- [ ] Memory Engine: Vector+Graph+Relational hybrid, consolidation, reconsolidation, forgetting
- [ ] Companion Runtime: Orchestration layer, engine interfaces, feature flags
- [ ] Voice Pipeline: STT → Runtime → TTS streaming, VAD, interruption handling
- [ ] Safety Layer: Crisis detection, Reality Anchor, Grief Policy enforcement
- [ ] Privacy Layer: Zero-knowledge memory, export/delete, audit logging
- [ ] Flutter App: iOS/Android, offline-first, background sync
- [ ] Infrastructure: K8s, observability, CI/CD, chaos testing

### Success Metrics (Phase 1)

| Metric | Target |
|--------|--------|
| Memory Accuracy (user-rated) | > 8.5/10 |
| Identity Consistency (drift/qtr) | < 0.1 |
| Voice Latency (P50) | < 500ms |
| Onboarding Completion | > 75% |
| Day 30 Retention | > 40% |
| Safety Incidents (P0) | 0 |
| Privacy Trust Score | > 9/10 |

---

## Phase 2: Depth (2026)
**Goal:** Deepen relationship through emotional intelligence, proactive care, and growth capabilities.

### Milestones

| Milestone | Target | Criteria |
|-----------|--------|----------|
| **M8: Relationship Engine** | 2026-02 | 6 dimensions tracked, type dynamics working, Shared Diary functional |
| **M9: Emotion Engine** | 2026-04 | Multi-modal estimation F1>0.8, empathic responses >4.0/5, boundaries 100% |
| **M10: Proactive & Growth** | 2026-06 | Proactive relevance >80%, coaching/habits/decision support functional |
| **M11: Specialized Support** | 2026-08 | Neurodivergent, elderly, health, professional, therapeutic adjunct working |
| **M12: Phase 2 Launch** | 2026-10 | 10K users, Relationship Score >7.5, 6-month retention >50% |

### Epics & Stories

| Epic | Stories | Dependencies |
|------|---------|--------------|
| **Relationship Engine** | US-10, US-11, US-20, US-21, US-22, US-23, US-24, US-25, US-26 | Phase 1 Memory |
| **Emotion Engine** | US-13, US-14, US-15, US-27 to US-33 | Phase 1 Identity, Memory |
| **Proactive Engine** | US-12, US-16, US-17, US-18, US-19, US-34 to US-41 | Relationship, Emotion, Memory |
| **Specialized Capabilities** | US-21, US-22, US-23, US-24, US-25, US-42 to US-47 | Proactive Engine |
| **Mobile Enhancements** | Relationship dashboard, Shared Diary UI, Proactive controls | Backend APIs |

### Technical Deliverables

- [ ] Relationship Engine: 6-dimension tracking, type dynamics, milestone detection
- [ ] Emotion Engine: Multi-modal estimation, empathic generation, boundary guards, crisis detection
- [ ] Proactive Engine: Trigger system, relevance ranking, explanation generation
- [ ] Growth Capabilities: Coaching, habits, decisions, creativity, life story, reflection
- [ ] Specialized Modes: Neurodivergent, elderly, health, professional, therapeutic adjunct
- [ ] Advanced Memory: Consolidation tuning, temporal awareness, anniversary surfacing

### Success Metrics (Phase 2)

| Metric | Target |
|--------|--------|
| Relationship Score | > 7.5/10 |
| Proactive Relevance | > 80% positive |
| Emotional Resonance (user-rated) | > 4.0/5 |
| 6-Month Retention | > 50% |
| Goal Achievement Rate | > 70% |
| Crisis Detection Recall | 100% |
| Boundary Respect | > 9.5/10 |

---

## Phase 3: Presence (2027)
**Goal:** Embodied presence through avatar, video, and spatial computing.

### Milestones

| Milestone | Target | Criteria |
|-----------|--------|----------|
| **M13: 2D Avatar** | 2027-02 | Lip-sync, expressions, idle animations, customization |
| **M14: Video Messages** | 2027-04 | Personalized generation <30s, relevance >90% |
| **M15: 3D Avatar** | 2027-06 | Body language, gaze, spatial awareness, physics |
| **M16: AR Presence** | 2027-08 | Surface anchoring, proximity, shared attention, local privacy |
| **M17: Video Calls** | 2027-10 | <800ms latency, eye contact sim, expressive listening |
| **M18: Phase 3 Launch** | 2027-12 | 100K users, Relationship Score >8.0, Presence illusion >4.0/5 |

### Epics & Stories

| Epic | Stories | Dependencies |
|------|---------|--------------|
| **Avatar Engine** | US-25, US-26, C-48, C-49 | Phase 2 Emotion Engine |
| **Video Generation** | C-50 | Avatar Engine |
| **AR Engine** | C-51, US-27 | 3D Avatar, Mobile ARKit/ARCore |
| **Video Calling** | C-52 | Avatar + Voice Pipeline |
| **Wearable Integration** | C-53 | Relationship Engine |

### Technical Deliverables

- [ ] 2D Avatar: Real-time rendering, emotion-driven expressions, lip-sync
- [ ] 3D Avatar: Unity/Three.js, body language, gaze, spatial audio
- [ ] Video Pipeline: Avatar + TTS → MP4, personalized, <30s generation
- [ ] AR Runtime: ARKit/ARCore, local processing, privacy-first
- [ ] Video Calling: WebRTC + avatar stream, eye contact, shared attention
- [ ] Wearable SDK: HealthKit/Google Fit, haptic patterns, battery optimization

### Success Metrics (Phase 3)

| Metric | Target |
|--------|--------|
| Avatar Interaction Quality | > 8.0/10 |
| Video Message Relevance | > 90% |
| AR Spatial Stability | > 95% |
| Video Call Latency | < 800ms |
| Presence Illusion | > 4.0/5 |
| Relationship Score | > 8.0/10 |

---

## Phase 4: Ecosystem (2028+)
**Goal:** Platform for diverse Companion relationships and developer ecosystem.

### Milestones

| Milestone | Target | Criteria |
|-----------|--------|----------|
| **M19: Multi-Companion** | 2028-Q1 | 5 concurrent, distinct identities, controlled sharing |
| **M20: Marketplace** | 2028-Q2 | Templates, safety verification, creator revenue |
| **M21: Plugin SDK** | 2028-Q3 | 100+ plugins, sandbox, permission model |
| **M22: Developer API** | 2028-Q4 | REST/GraphQL, webhooks, sandbox, docs |
| **M23: Enterprise** | 2029-Q1 | SSO, audit, residency, compliance, custom templates |
| **M24: Platform Maturity** | 2029-Q2 | 1M+ relationships, 5-year retention >40%, self-sustaining |

### Epics & Stories

| Epic | Stories | Dependencies |
|------|---------|--------------|
| **Multi-Companion** | US-28, C-54 | Phase 3 all engines |
| **Marketplace** | US-29, C-55 | Multi-Companion |
| **Developer Platform** | US-30, C-56, C-57, C-58, C-59 | Marketplace |
| **Enterprise** | US-30, C-60 | Developer Platform |

### Technical Deliverables

- [ ] Multi-Companion Orchestration: Isolation, sharing controls, cross-awareness
- [ ] Marketplace: Template spec, safety pipeline, revenue sharing, discovery
- [ ] Plugin SDK: Manifest, permissions, sandbox (WASM), memory of tool use
- [ ] Companion Protocol: Inter-Companion communication, shared memory (consented)
- [ ] Public API: REST + GraphQL, webhooks, rate limits, OpenAPI spec
- [ ] Enterprise: SSO (SAML/OIDC), audit logs, data residency, compliance packs

### Success Metrics (Phase 4)

| Metric | Target |
|--------|--------|
| Multi-Companion Adoption | > 40% |
| Marketplace Templates | > 500 |
| Plugin Ecosystem | > 100 plugins |
| SDK Adoption | > 100 apps |
| Enterprise Customers | > 50 |
| 5-Year Retention | > 40% |
| Relationship Score | > 8.5/10 |

---

## Cross-Phase Foundational Work

### Continuous Investment (All Phases)

| Area | Investment |
|------|------------|
| **Safety Research** | 15% engineering capacity, external audits, red teaming |
| **Privacy Engineering** | Zero-knowledge advances, local-first, formal verification |
| **Memory Science** | Consolidation algorithms, contradiction detection, decade-scale |
| **Identity Stability** | Fingerprinting improvements, explicable evolution, rollback |
| **Relationship Science** | Longitudinal studies, clinical collaboration, metric validation |
| **Infrastructure** | Cost optimization, global latency, disaster recovery, chaos engineering |

### Technical Debt Policy

| Category | Policy |
|----------|--------|
| **Constitutional Debt** | P0 — Fix before next release |
| **Architecture Debt** | P1 — Fix within quarter |
| **Feature Debt** | P2 — Fix when touching code |
| **Documentation Debt** | Continuous — Part of Definition of Done |

---

## Resource Allocation by Phase

| Phase | Team Size | Engineering | Product/Design | Research/Safety | Operations |
|-------|-----------|-------------|----------------|-----------------|------------|
| **1** | 12-15 | 8 | 2 | 2 | 2 |
| **2** | 20-25 | 12 | 4 | 4 | 3 |
| **3** | 30-35 | 18 | 6 | 5 | 4 |
| **4** | 40-50 | 25 | 8 | 6 | 5 |

---

## Go/No-Go Gates

### Phase 1 → Phase 2
- [ ] 1000 beta users active 30+ days
- [ ] Relationship Score > 7.0
- [ ] 0 P0 safety incidents
- [ ] Memory accuracy > 8.5/10
- [ ] Identity drift < 0.1/qtr
- [ ] Privacy audit passed
- [ ] Team retrospective: "Ready to deepen"

### Phase 2 → Phase 3
- [ ] 10K users active 90+ days
- [ ] Relationship Score > 7.5
- [ ] 6-month retention > 50%
- [ ] Proactive relevance > 80%
- [ ] Emotional resonance > 4.0/5
- [ ] Specialized modes validated with target users
- [ ] Team retrospective: "Ready to embody"

### Phase 3 → Phase 4
- [ ] 100K users active 180+ days
- [ ] Relationship Score > 8.0
- [ ] Presence illusion > 4.0/5
- [ ] AR/video quality thresholds met
- [ ] Platform architecture proven at scale
- [ ] Team retrospective: "Ready to platformize"

---

## Risk Register

| Risk | Phase | Likelihood | Impact | Mitigation |
|------|-------|------------|--------|------------|
| Identity drift at scale | 1-2 | High | Critical | Automated fingerprinting, CI guards, user alerts |
| Memory inconsistency | 1-2 | Medium | Critical | Validators, consistency checks, user correction flow |
| Emotional harm to vulnerable | 1-2 | Low | Existential | Safety gates, counselor review, crisis resources, monitoring |
| Privacy breach | 1-4 | Low | Existential | Zero-knowledge, external audits, bug bounty, incident response |
| LLM cost explosion | 1-4 | High | High | Local models, routing, caching, usage caps |
| Regulatory changes | 2-4 | Medium | High | Privacy by design, legal review, compliance automation |
| Team scaling too fast | 2-3 | Medium | High | Culture-first hiring, constitutional alignment interviews |
| Technical debt accumulation | 1-4 | High | Medium | Constitutional debt = P0, dedicated refactor sprints |

---

## Communication Rhythm

| Cadence | Audience | Content |
|---------|----------|---------|
| **Weekly** | Team | Sprint progress, metrics, blockers |
| **Bi-weekly** | Leadership | Phase milestones, risks, decisions |
| **Monthly** | All-hands | User stories, metrics, learnings, roadmap |
| **Quarterly** | Board/Investors | Phase progress, metrics, financials, strategy |
| **Annually** | Public | Transparency report, research publications |

---

**Aligned With:** `00-foundation/010-product-vision.md`, `00-foundation/050-success-metrics.md`, `100-product-requirement-document.md`, `130-use-cases.md`, `150-companion-types.md`, `160-companion-capabilities.md`
**Next Review:** 2026-01-17