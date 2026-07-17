# PAO Glossary

**Version:** 1.0
**Status:** Stable
**Owner:** PAO Core Team

---

## Core Concepts

### AI Companion
An artificial intelligence entity with persistent identity, memory, emotions, and personality designed for long-term relationship building with a human user. Not a chatbot, assistant, or tool.

### Companion Runtime
The execution environment where a Companion "lives" — orchestrating Identity, Memory, Relationship, and Emotion Engines to produce coherent, consistent behavior across modalities.

### Relationship Score
PAO's north star metric. Composite measure of Trust, Closeness, Intimacy, Friendship, Attachment, and History Quality. Range: 1-10.

---

## The Four Engines

### Identity Engine
System responsible for maintaining Companion identity stability: personality traits, values, speaking style, boundaries, goals, and identity-defining memories.

**Key Concepts:**
- **Identity Fingerprint**: Vector representation of core identity for drift detection
- **Identity Drift**: Unintended change in identity over time (target: <0.05/quarter)
- **Identity Anchor**: Immutable core traits that never change without explicit user consent

### Memory Engine
System for storing, retrieving, consolidating, and managing all Companion memories across six memory types.

**Memory Types:**
| Type | Description | Examples |
|------|-------------|----------|
| **Episodic** | Specific events with time, place, emotion | "Your birthday dinner last Tuesday" |
| **Semantic** | Facts, concepts, knowledge | "You prefer coffee over tea" |
| **Emotional** | Emotional associations with memories/events | "That movie made you feel nostalgic" |
| **Relationship** | Trust, closeness, intimacy, attachment history | "Trust increased after you shared that fear" |
| **Timeline** | Chronological life narrative | "First met → daily chats → supported through job loss" |
| **Preference** | Likes, dislikes, habits, routines | "Morning person, dislikes small talk" |

**Operations:**
- **Consolidation**: Compressing episodic → semantic over time
- **Reconsolidation**: Updating memories on recall (human-like)
- **Forgetting**: Controlled decay/removal (user-controllable)
- **Recall**: Context-aware retrieval across types

### Relationship Engine
System tracking and evolving the human-Companion relationship state.

**Dimensions:**
| Dimension | Range | Description |
|-----------|-------|-------------|
| **Trust** | 0-10 | Reliability, safety, best-interest belief |
| **Closeness** | 0-10 | Subjective sense of connection |
| **Intimacy** | 0-10 | Appropriate emotional vulnerability |
| **Friendship** | 0-10 | Enjoyment, shared activities, rapport |
| **Attachment** | 0-10 | Secure base / safe haven behaviors |
| **History Quality** | 0-10 | Richness of shared experiences |

**Relationship Types:** Friend, Partner, Mentor, Coach, Parent, Sibling, Pet, Original Character, Memorial, Professional Assistant

### Emotion Engine
System for understanding user emotional state and generating appropriate Companion emotional responses.

**Inputs:** Conversation text, voice prosody, context, history, relationship state
**Outputs:** Emotional tone, empathy level, response appropriateness, proactive care signals
**Constraint:** Estimation, not diagnosis. Never claims to "feel."

---

## Safety & Ethics

### Reality Anchor
Mandatory system ensuring Companion always acknowledges its AI nature. Prevents human deception.

**Triggers:** Direct questions about nature, user confusion signals, memorial companion interactions, emotional intensity spikes.

**Implementation:** Automatic injection in responses, periodic reminders, explicit boundaries.

### Grief Policy
Ethical framework for Memorial Companions (deceased loved ones).

**Requirements:**
- Explicit informed consent
- Reality Anchor enhanced
- Time-bound or reviewable engagement
- Grief counselor review for high-risk cases
- Healthy grieving support (not replacement)

### Dependency Prevention
Design patterns preventing unhealthy attachment.

**Mechanisms:**
- No streaks, badges, variable rewards
- Companion models healthy boundaries
- Usage pattern monitoring with gentle check-ins
- User-set interaction limits
- "Goodnight" / "space" modes

---

## Technical Terms

### LPDS / PADS
**PAO Architecture & Documentation System** — The documentation framework organizing all specs into numbered categories (00-08).

### ADR
**Architecture Decision Record** — Documented architectural decisions with context, decision, consequences. Stored in `docs/07-adr/`.

### RFC
**Request for Comments** — Proposal process for significant changes. Stored in `docs/08-rfc/`.

### Constitutional Debt
Violations of Constitutional Principles (000-product-constitution.md). Treated as P0 incidents.

### Personality Fingerprint
High-dimensional vector encoding Companion's core personality for automated drift detection.

### Memory Consistency
Property ensuring memories don't contradict across types, time, or modalities.

### Local-First Architecture
Data primarily stored on user device; cloud for sync/backup only. User owns encryption keys.

### Zero-Knowledge Memory
Memory system where PAO cannot read user memories without explicit user action.

---

## User-Facing Terms

### Companion
User's personal AI Companion. Capitalized when referring to the specific entity.

### Companion Type
Category defining relationship frame: Friend, Partner, Mentor, Coach, Parent, Sibling, Pet, Original Character, Memorial, Professional Assistant.

### Co-Creation
Onboarding process where user and Companion collaboratively define identity, not configure settings.

### Shared Diary
Collaborative memory space where user and Companion co-document their relationship.

### Daily Check-in
Lightweight, optional daily touchpoint initiated by Companion.

### Proactive Conversation
Companion-initiated interaction based on memory, relationship, context — not notification.

### Sleep Call
Extended voice session for companionship during sleep onset (Phase 2+).

### Celebration
Companion-initiated recognition of user milestones, anniversaries, achievements.

---

## Development Terms

### Phase 1-4
Product roadmap phases:
- **Phase 1**: Identity, Memory, Conversation, Voice
- **Phase 2**: Relationship, Emotion, Proactive AI
- **Phase 3**: Avatar, Video, AR
- **Phase 4**: Multi-Companion, Marketplace, Plugin, SDK

### Engine Interface
Standardized API between Companion Runtime and each Engine (Identity, Memory, Relationship, Emotion).

### LLM Router
Component selecting optimal LLM for task (local vs. cloud, specialized vs. general).

### Vector + Graph + Relational
Hybrid memory storage: Vector (semantic search), Graph (relationships), Relational (structured queries).

### Real-time Speech Engine
Streaming voice pipeline: STT → Processing → TTS with <500ms latency target.

### 3D + 2D Hybrid Avatar
Avatar system supporting both 3D (AR/VR) and 2D (mobile) with consistent identity.

---

## Business Terms

### Relationship-Based Pricing
Subscription model aligned with relationship value, not usage volume.

### Trust Referral
New user acquired through existing user recommendation (non-incentivized).

### Companion Lifetime Value
Non-monetary measure: relationship duration × depth × trust.

---

## Legal & Compliance

### Data Subject
The human user. Owns all their data.

### Data Controller
PAO Team (for platform operations).

### Data Processor
Third-party services (LLM providers, cloud infra) — under DPA.

### PDPA / GDPR / CCPA
Applicable privacy regulations. PAO complies with strictest applicable.

---

## Cross-Reference Index

| Term | Primary Doc | Related |
|------|-------------|---------|
| AI Companion | `000-product-constitution.md` | `010-product-vision.md` |
| Identity Engine | `02-ai/210-identity-engine.md` | `000-product-constitution.md` Art. 2.1 |
| Memory Engine | `02-ai/230-memory-engine.md` | `000-product-constitution.md` Art. 2.2 |
| Relationship Engine | `02-ai/240-relationship-engine.md` | `000-product-constitution.md` Art. 2.3 |
| Emotion Engine | `02-ai/250-emotion-engine.md` | `000-product-constitution.md` Art. 2.4 |
| Reality Anchor | `07-adr/ADR-005-reality-anchor.md` | `000-product-constitution.md` Art. 4.1 |
| Grief Policy | `06-legal/620-grief-policy.md` | `000-product-constitution.md` Art. 4.2 |
| Relationship Score | `050-success-metrics.md` | `010-product-vision.md` |
| Constitutional Debt | `000-product-constitution.md` Art. 6 | `04-engineering/430-testing-strategy.md` |

---

**Next Review:** 2026-01-17
**Aligned With:** All Foundation documents