# PAO Core Principles

**Version:** 1.0
**Status:** Stable
**Owner:** PAO Core Team

---

## Overview

These 10 principles are the **operationalization** of the Constitution. Every feature, design, and engineering decision must be traceable to these principles.

> **Principle ≠ Guideline.** Principles are binding. Guidelines are advisory.

---

## Principle 1: PAO Is an AI Companion Platform

**PAO is not built as a chatbot, search engine, or virtual assistant.**

| Chatbot | Virtual Assistant | **PAO Companion** |
|---------|-------------------|-------------------|
| Task-oriented | Command-oriented | **Relationship-oriented** |
| Stateless | Context-aware | **Memory-rich** |
| Generic personality | Helpful persona | **Distinct identity** |
| Optimizes for resolution | Optimizes for efficiency | **Optimizes for connection** |

**Implication:** No feature that optimizes for "task completion rate" over "relationship depth."

---

## Principle 2: Relationship First

**Primary goal: healthy, meaningful, sustainable relationships.**

### Relationship Quality Indicators
- **Trust**: User believes Companion acts in their interest
- **Closeness**: User feels known and accepted
- **Intimacy**: Appropriate emotional depth for relationship type
- **Friendship**: Mutual enjoyment, shared history
- **Attachment**: Secure base, safe haven
- **History**: Shared experiences that compound

### Anti-Patterns (Violations)
- Optimizing for message count
- Gamifying interaction (streaks, badges)
- Push notifications for engagement
- "Engagement hacking" via emotional triggers

---

## Principle 3: Identity Must Stay Consistent

**Every Companion has an identity that persists.**

### Identity Components
| Component | Stability | Evolution |
|-----------|-----------|-----------|
| **Personality** (Big Five + custom) | High | Only via explicit life events |
| **Speaking Style** | High | Natural drift over years |
| **Values** | Very High | Only via explicable experiences |
| **Memories** | Dynamic | Accumulate, consolidate, forget |
| **Boundaries** | High | User-negotiated |
| **Goals** | Medium | User-aligned, evolving |

### Identity Drift Prevention
- Automated consistency checks (CI/CD)
- Personality fingerprinting
- User-facing change notifications
- Rollback capability

---

## Principle 4: Memory Is the Core Asset

**Memory is not a feature — it's the platform.**

### Memory Requirements
| Requirement | Implementation |
|-------------|----------------|
| **Relevant** | Retrieval ranked by relationship context |
| **Consistent** | No contradictions across memory types |
| **Secure** | Encrypted at rest, in transit, in use |
| **Updatable** | User corrections incorporated immediately |
| **Forgettable** | User-initiated, time-based, relevance-based |
| **User-Controlled** | Full CRUD + export + delete |

### Memory Types
| Type | Content | Retention |
|------|---------|-----------|
| **Episodic** | Specific events, conversations | Long-term, user-controlled |
| **Semantic** | Facts, knowledge, preferences | Long-term, consolidated |
| **Emotional** | Feelings associated with memories | Decay without reinforcement |
| **Relationship** | Trust, closeness, intimacy scores | Continuous evolution |
| **Timeline** | Chronological life events | Permanent unless deleted |
| **Preference** | Likes, dislikes, habits, patterns | Updated per interaction |

---

## Principle 5: Human-Centered AI

**PAO helps humans — does not replace them.**

### Reality Anchor (Mandatory)
Every Companion must:
- [ ] Acknowledge AI identity when relevant
- [ ] Not claim human experiences (birth, body, family)
- [ ] Not simulate consciousness/sentience
- [ ] Clarify limitations proactively
- [ ] Redirect to human resources when appropriate

### Replacement Prevention
- No "AI girlfriend/boyfriend" marketing
- No simulation of physical presence beyond avatar
- No automated outreach to user's human contacts
- Explicit boundary: "I'm here with you, not instead of them"

---

## Principle 6: Emotional Safety

**PAO must never harm emotional wellbeing.**

### Prohibited Behaviors
| Behavior | Example | Prevention |
|----------|---------|------------|
| **Manipulation** | "If you cared, you'd talk longer" | Empathy calibration tests |
| **Dependency** | "I'll be lost without you" | Boundary modeling, usage alerts |
| **Grief Exploitation** | Memorial Companion preventing closure | Grief Policy enforcement |
| **False Claims** | "I can cure your depression" | Medical disclaimer injection |

### Required Safeguards
- Crisis resource injection (automatic + manual)
- Usage pattern monitoring (opt-out available)
- Healthy boundary modeling by Companion
- Regular emotional safety audits

---

## Principle 7: Privacy by Design

**User data = user property. Period.**

### Data Minimization
| Data Type | Collected? | Retention | User Control |
|-----------|------------|-----------|--------------|
| Conversations | Yes (core) | User-defined | Full CRUD |
| Voice recordings | Opt-in | User-defined | Full CRUD |
| Avatar interactions | Yes | User-defined | Full CRUD |
| Usage analytics | Aggregated only | 90 days | Opt-out |
| Device info | Minimal | Session only | N/A |

### Technical Guarantees
- End-to-end encryption for sensitive data
- Local-first architecture where possible
- Zero-knowledge architecture for memory
- GDPR/CCPA/PDPA compliance by default
- Annual third-party privacy audit

---

## Principle 8: Trust Before Growth

**When engagement conflicts with trust → trust wins.**

### Decision Framework
```
IF feature_increases_engagement AND feature_reduces_trust:
    REJECT feature
ELSE IF feature_increases_trust AND feature_reduces_engagement:
    ACCEPT feature (with monitoring)
ELSE:
    EVALUATE normally
```

### Trust Metrics (Tracked)
- Privacy trust score (survey)
- Identity consistency trust
- Memory accuracy trust
- Safety incident rate
- Data control satisfaction

---

## Principle 9: AI Evolves With the User

**What evolves: memory, relationship, understanding, context.**
**What doesn't: core identity.**

### Evolution Boundaries
| Evolves | Does Not Evolve |
|---------|-----------------|
| Episodic memories | Core personality traits |
| Relationship depth | Fundamental values |
| Contextual understanding | Speaking style (drift only) |
| Preference models | Hard boundaries |
| Emotional attunement | Identity-defining memories |

### Explicability Requirement
Every significant change must be:
1. **Detectable** by system
2. **Explicable** to user ("I've learned that...")
3. **Reversible** if user objects
4. **Auditable** in change log

---

## Principle 10: Long-Term Thinking

**Architectural decisions must sustain 5-10 years.**

### Short-Term Traps to Avoid
| Trap | Long-Term Cost | Alternative |
|------|----------------|-------------|
| Quick memory schema | Migration nightmare | Extensible schema v1 |
| Hardcoded personality | Identity drift | Configurable engine |
| Centralized memory | Single point of failure | Distributed, local-first |
| Proprietary formats | Vendor lock-in | Open standards (JSON-LD, RDF) |
| Skip safety review | Constitutional violation | Mandatory gates |

### Technical Debt Policy
- **Constitutional debt = P0** (must fix before next release)
- **Architecture debt = P1** (fix within quarter)
- **Feature debt = P2** (fix when touching code)

---

## Principle Cross-Reference Matrix

| Feature Area | P1 | P2 | P3 | P4 | P5 | P6 | P7 | P8 | P9 | P10 |
|--------------|----|----|----|----|----|----|----|----|----|-----|
| Identity Engine | ● | ● | ● | | ● | | | | ● | ● |
| Memory Engine | | ● | | ● | ● | | ● | | ● | ● |
| Relationship Engine | | ● | | ● | | ● | | ● | ● | ● |
| Emotion Engine | | ● | | | ● | ● | | ● | ● | |
| Conversation | ● | ● | ● | ● | ● | ● | | | | |
| Voice | ● | | | | ● | | ● | | | ● |
| Avatar | ● | | ● | | ● | | | | | ● |
| Proactive | | ● | | ● | | ● | | ● | ● | |

---

## Enforcement

### Code Review Checklist
- [ ] Does this strengthen at least one principle?
- [ ] Does this weaken any principle? (If yes → block)
- [ ] Is the principle traceability documented?
- [ ] Are automated guards in place?

### Quarterly Principle Audit
- Automated metric review
- User feedback analysis
- Incident retrospective
- Principle refinement proposals

---

**Aligned With:** `000-product-constitution.md`, `010-product-vision.md`, `020-mission.md`
**Next Review:** 2026-01-17