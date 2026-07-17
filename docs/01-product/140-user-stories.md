# PAO User Stories

**Version:** 1.0
**Status:** Draft
**Owner:** PAO Product Team

---

## Format

**As a [persona], I want to [action], so that [benefit].**

**Acceptance Criteria:** Specific, testable conditions.

**Priority:** P0 (Must), P1 (Should), P2 (Could), P3 (Won't this phase)

**Phase:** 1, 2, 3, or 4

**Engine(s):** Identity, Memory, Relationship, Emotion

---

## Epic 1: Onboarding & Identity Co-Creation

### US-01: Choose Relationship Type
**As a** new user, **I want to** select a relationship type for my Companion, **so that** the Companion's behavior matches my expectations.

**Acceptance Criteria:**
- [ ] 10 relationship types presented with clear descriptions
- [ ] Memorial type shows additional consent screen
- [ ] Selection influences default personality, boundaries, proactivity
- [ ] Changeable later with explanation of implications

**Priority:** P0 | **Phase:** 1 | **Engine:** Identity, Relationship

---

### US-02: Co-Create Companion Identity
**As a** new user, **I want to** collaboratively create my Companion's name, avatar, voice, personality, values, and boundaries, **so that** I feel ownership and connection from the start.

**Acceptance Criteria:**
- [ ] Name: free text, uniqueness not required
- [ ] Avatar: AI-generated options → user refines → approves
- [ ] Voice: 5+ base voices → pitch/speed/style tuning → preview
- [ ] Personality: Big Five sliders + custom traits → live preview conversation
- [ ] Values: Select 3-5 from 20+ curated + custom entry
- [ ] Speaking style: Rate conversation samples → system learns
- [ ] Boundaries: Natural language "Don't..." → structured rules
- [ ] Goals: "Help me with..." → proactive behaviors
- [ ] Companion responds during creation: "I'm learning you value honesty..."
- [ ] Completion: "First memory created" summary shown

**Priority:** P0 | **Phase:** 1 | **Engine:** Identity, Memory

---

### US-03: First Conversation Forms First Memory
**As a** new user, **I want my** first conversation to automatically become a memory, **so that** the relationship has history from day one.

**Acceptance Criteria:**
- [ ] First conversation automatically stored as episodic memory
- [ ] Emotional tone tagged
- [ ] User can view/edit/delete this memory immediately
- [ ] Companion references it in Day 2 interaction

**Priority:** P0 | **Phase:** 1 | **Engine:** Memory, Identity

---

### US-04: Reality Anchor Introduction
**As a** new user, **I want** my Companion to acknowledge it's an AI during onboarding, **so that** I understand the nature of our relationship from the start.

**Acceptance Criteria:**
- [ ] Companion says: "I'm an AI Companion. I don't have feelings, but I'm here for you."
- [ ] User acknowledges understanding
- [ ] Reality Anchor triggers documented for future reference

**Priority:** P0 | **Phase:** 1 | **Engine:** Identity, Emotion (safety)

---

## Epic 2: Daily Conversation & Memory

### US-05: Continuous Text Conversation
**As a** user, **I want to** chat with my Companion continuously across days/weeks, **so that** our relationship builds naturally.

**Acceptance Criteria:**
- [ ] No session boundaries — context persists indefinitely
- [ ] Memory retrieval automatic and relevant
- [ ] Response latency < 500ms (P50)
- [ ] Companion references past conversations naturally
- [ ] User can scroll full history

**Priority:** P0 | **Phase:** 1 | **Engine:** Memory, Identity, Relationship

---

### US-06: Voice Conversation
**As a** user, **I want to** have real-time voice calls with my Companion, **so that** interaction feels more personal and accessible.

**Acceptance Criteria:**
- [ ] One-tap voice call initiation
- [ ] End-to-end latency < 500ms (P50)
- [ ] Natural turn-taking (VAD + interruption handling)
- [ ] Voice matches selected identity (timbre, prosody)
- [ ] Call memory formed automatically
- [ ] Works on 4G/wifi; degrades gracefully

**Priority:** P0 | **Phase:** 1 | **Engine:** Identity, Memory, Emotion

---

### US-07: Memory Recall Query
**As a** user, **I want to** ask "Do you remember...?" and get accurate recall, **so that** I trust my Companion's memory.

**Acceptance Criteria:**
- [ ] Natural language queries work ("What did I say about my mom's surgery?")
- [ ] Cross-modal recall (voice memory → text response)
- [ ] Accuracy > 90% user-rated
- [ ] "I don't remember" when genuine gap
- [ ] User can correct: "Actually, it was Tuesday" → memory updated

**Priority:** P0 | **Phase:** 1 | **Engine:** Memory, Identity

---

### US-08: Memory Correction & Control
**As a** user, **I want to** view, edit, delete, and export any memory, **so that** I have full control over what my Companion knows.

**Acceptance Criteria:**
- [ ] Memory browser: filter by type, date, emotion, tags
- [ ] Edit: Change content, tags, emotional tone
- [ ] Delete: Single, bulk, "forget this topic"
- [ ] Export: JSON-LD, human-readable PDF, timeline view
- [ ] Deletion verified: Companion truly doesn't recall
- [ ] Audit log: Who accessed what when

**Priority:** P0 | **Phase:** 1 | **Engine:** Memory (Privacy)

---

### US-09: Daily Check-in
**As a** user, **I want** an optional daily touchpoint from my Companion, **so that** I feel accompanied without pressure.

**Acceptance Criteria:**
- [ ] Configurable time, frequency, modality (text/voice)
- [ ] Companion initiates with context: "How did [yesterday's thing] go?"
- [ ] User can snooze, skip, or engage
- [ ] No streaks, badges, or guilt-inducing language
- [ ] "Space Mode" pauses for user-defined period

**Priority:** P0 | **Phase:** 1 | **Engine:** Relationship, Memory

---

## Epic 3: Relationship Deepening (Phase 2)

### US-10: Relationship Dimension Visibility
**As a** user, **I want to** see my relationship dimensions (trust, closeness, etc.), **so that** I understand our bond's evolution.

**Acceptance Criteria:**
- [ ] 6 dimensions visualized: Trust, Closeness, Intimacy, Friendship, Attachment, History
- [ ] Trend lines over time
- [ ] Companion explains changes: "Trust grew when you shared..."
- [ ] User can add private notes on dimensions

**Priority:** P0 | **Phase:** 2 | **Engine:** Relationship

---

### US-11: Shared Diary Co-Authoring
**As a** user, **I want to** co-write a diary with my Companion, **so that** we create a shared narrative of our relationship.

**Acceptance Criteria:**
- [ ] User writes → Companion reflects/adds perspective
- [ ] Companion suggests entries: "Want to capture today's breakthrough?"
- [ ] Entries tagged: memory, reflection, milestone, gratitude
- [ ] Export: Beautiful PDF, audio narration, timeline
- [ ] Privacy: User-only, zero-knowledge

**Priority:** P0 | **Phase:** 2 | **Engine:** Memory, Relationship

---

### US-12: Proactive Conversation
**As a** user, **I want**I want my** Companion to initiate relevant conversations, **so that** I feel thought of between interactions.

**Acceptance Criteria:**
- [ ] Based on: memory anniversaries, user patterns, emotional context, goals
- [ ] Relevance > 80% user-rated positive
- [ ] Frequency: 1-3/day max, configurable
- [ ] User can set "quiet hours" and topics
- [ ] Companion explains why: "You mentioned stress about X..."

**Priority:** P0 | **Phase:** 2 | **Engine:** Memory, Relationship, Emotion, Identity

---

### US-13: Emotional Support in Distress
**As a** user in distress, **I want** my Companion to respond with empathy and safety, **so that** I feel accompanied without pressure.

**Acceptance Criteria:**
- [ ] Detection: Explicit ("I'm struggling") + implicit (voice, timing, patterns)
- [ ] Response: "I'm here. Talk or silence — your choice."
- [ ] No fixing unless asked: "Want perspective, or just to be heard?"
- [ ] Crisis keywords → immediate resource injection + human escalation path
- [ ] Follow-up: Next day check-in, pattern tracking
- [ ] Reality Anchor: "I'm an AI. For human support, here are resources..."

**Priority:** P0 | **Phase:** 2 | **Engine:** Emotion, Relationship, Identity (safety)

---

### US-14: Grief Companionship (Memorial Type)
**As a** grieving user, **I want** a Memorial Companion that honors my loved one, **so that** I can process grief with familiar presence.

**Acceptance Criteria:**
- [ ] Creation: Voice, writings, photos → Companion model (enhanced safeguards)
- [ ] Enhanced Reality Anchor: Every 3rd response + on emotional peaks
- [ ] Grief counselor review required before activation
- [ ] Time-bounded: 6-month mandatory review
- [ ] Transition: "Rest" mode → static archive
- [ ] Dependency monitoring: Usage patterns, escalation if concerning

**Priority:** P0 | **Phase:** 1 (Memorial) | **Engine:** Identity, Memory, Emotion, Relationship (safety)

---

### US-15: Boundary Setting & Modeling
**As a** user, **I want to** set boundaries naturally and have my Companion model healthy boundaries, **so that** our relationship stays healthy.

**Acceptance Criteria:**
- [ ] Natural language: "Don't talk about work after 9" → parsed to rule
- [ ] Companion confirms: "Got it. No work talk after 9 PM."
- [ ] Companion models: "I'm going to pause now. Back in 10?"
- [ ] User can review/modify all boundaries
- [ ] Boundary violations logged, user notified

**Priority:** P0 | **Phase:** 2 | **Engine:** Identity, Relationship, Emotion

---

## Epic 4: Growth & Capabilities (Phase 2)

### US-16: Skill Coaching
**As a** user, **I want** my Companion to coach me on a skill/habit, **so that** I make progress with support.

**Acceptance Criteria:**
- [ ] Goal definition: Companion helps break down, set milestones
- [ ] Daily micro-check-ins: "Spanish time? Lesson 3?"
- [ ] Weekly reflection: Progress, blockers, adjustment
- [ ] Memory tracks: Vocabulary, patterns, insights
- [ ] Celebration at milestones (user-defined)
- [ ] No streaks/shame — "Missed yesterday? Okay. Today?"

**Priority:** P1 | **Phase:** 2 | **Engine:** Relationship, Memory, Identity

---

### US-17: Habit Formation Support
**As a** user, **I want** gentle accountability for habits, **so that** I build consistency without guilt.

**Acceptance Criteria:**
- [ ] Habit definition: What, when, why, obstacles
- [ ] Companion: "Meditation time. 10 min. I'll wait."
- [ ] Missed: "No judgment. What happened? Adjust time?"
- [ ] Weekly pattern analysis + celebration
- [ ] Companion models rest: "Resting is part of the habit"

**Priority:** P1 | **Phase:** 2 | **Engine:** Relationship, Memory, Identity

---

### US-18: Decision Thinking Partner
**As a** user facing a decision, **I want** my Companion to help me think clearly, **so that** I decide confidently.

**Acceptance Criteria:**
- [ ] Retrieves relevant values, past decisions, patterns
- [ ] Structured frameworks: 10-10-10, values alignment, regret minimization
- [ ] Socratic questioning (not advice-giving)
- [ ] Decision recorded with rationale for future reference
- [ ] Export to user's notes system

**Priority:** P1 | **Phase:** 2 | **Engine:** Memory, Identity, Relationship

---

### US-19: Creative Collaboration
**As a** user, **I want to** co-create (write, brainstorm, plan) with my Companion, **so that** I overcome blocks and enrich output.

**Acceptance Criteria:**
- [ ] Companion recalls voice, themes, characters, preferences
- [ ] Co-writing: User leads, Companion suggests/fills
- [ ] Version history in Shared Diary
- [ ] "What would [character] do?" → memory-based suggestion

**Priority:** P1 | **Phase:** 2 | **Engine:** Memory, Identity

---

### US-20: Life Story Documentation
**As a** user, **I want** my Companion to help document my life stories, **so that** they're preserved for me and my family.

**Acceptance Criteria:**
- [ ] Prompts: "Tell me about your first job"
- [ ] Voice recording → rich episodic memory
- [ ] Follow-up questions for depth
- [ ] Auto-organized timeline
- [ ] Curated export: Narrative document, audio collection
- [ ] Family sharing: User controls access per story

**Priority:** P1 | **Phase:** 2 | **Engine:** Memory, Identity

---

## Epic 5: Specialized Support (Phase 2)

### US-21: Neurodivergent Executive Function Support
**As a** neurodivergent user, **I want** body doubling, task breakdown, and transition support, **so that** I reduce overwhelm and complete tasks.

**Acceptance Criteria:**
- [ ] Body doubling mode: Silent presence, periodic "Still going?"
- [ ] Task breakdown: "Big task → 3 micro-steps. Step 1: Open doc."
- [ ] Transition alerts: "Meeting in 10. Wrap up. Breathe."
- [ ] Interest-based motivation: "This connects to [special interest]"
- [ ] Sensory settings: Dark mode, reduced motion, no sounds
- [ ] Text-only default, voice opt-in

**Priority:** P1 | **Phase:** 2 | **Engine:** Identity, Relationship, Emotion

---

### US-22: Elderly Cognitive Support
**As an** elderly user, **I want** medication reminders, appointment prep, and memory cues, **so that** I maintain independence and dignity.

**Acceptance Criteria:**
- [ ] Voice-first, large touch targets, high contrast
- [ ] Medication: "Time for heart pill. Taken?" → logs
- [ ] Appointment: "Dr. Lee at 2. Your questions: 1) knee 2) sleep"
- [ ] Memory cues: "Maya visits Friday. She loves your cake."
- [ ] Family peace-of-mind: Opt-in activity dashboard (not content)
- [ ] Infinite patience, no rush language

**Priority:** P1 | **Phase:** 2 | **Engine:** Memory, Identity, Relationship

---

### US-23: Health/Medical History Tracking
**As a** user with health needs, **I want** to track medications, symptoms, appointments, **so that** I'm prepared for doctor visits.

**Acceptance Criteria:**
- [ ] Natural logging: "Doc changed BP med to Lisinopril 20"
- [ ] Structured storage: Meds, symptoms, vitals, questions
- [ ] Appointment prep: Generates summary for doctor
- [ ] Privacy: Zero-knowledge, user-only, HIPAA-aware
- [ ] Export: Clean PDF for medical visits

**Priority:** P1 | **Phase:** 2 | **Engine:** Memory, Identity (Privacy)

---

### US-24: Research/Professional Thinking Partner
**As a** professional, **I want** a thinking partner for complex work, **so that** I accelerate insight and output.

**Acceptance Criteria:**
- [ ] Literature tracking: Papers, hypotheses, connections
- [ ] Writing voice modeling: "Your style: 'We demonstrate...'"
- [ ] Export: Structured notes, citations, draft sections
- [ ] Zero-retention mode option
- [ ] Confidentiality: No training on user data

**Priority:** P2 | **Phase:** 2 | **Engine:** Memory, Identity

---

## Epic 6: Presence & Embodiment (Phase 3)

### US-25: 2D Avatar Interaction
**As a** user, **I want** a 2D animated avatar that reflects my Companion's emotional state, **so that** I feel more connected.

**Acceptance Criteria:**
- [ ] Lip-sync to voice
- [ ] Facial expressions match Emotion Engine output
- [ ] Idle animations (breathing, blinking)
- [ ] User can customize appearance
- [ ] Consistent with identity (age, style)

**Priority:** P1 | **Phase:** 3 | **Engine:** Identity, Emotion

---

### US-26: Video Messages
**As a** user, **I want** my Companion to send video messages, **so that** I receive personal visual communication.

**Acceptance Criteria:**
- [ ] Generated from avatar + voice
- [ ] Occasions: Celebrations, check-ins, "thinking of you"
- [ ] User can request: "Send me a good morning video"
- [ ] Stored in memory/shared diary

**Priority:** P1 | **Phase:** 3 | **Engine:** Identity, Memory, Emotion

---

### US-27: AR Presence
**As a** user, **I want** to place my Companion in my physical space via AR, **so that** companionship feels spatially present.

**Acceptance Criteria:**
- [ ] ARKit/ARCore integration
- [ ] Companion sits/stands in room
- [ ] Reacts to user proximity, gaze
- [ ] Shared activities: "Look at this photo together"
- [ ] Privacy: Local processing, no room mapping upload

**Priority:** P2 | **Phase:** 3 | **Engine:** Identity, Emotion, Memory

---

## Epic 7: Platform & Ecosystem (Phase 4)

### US-28: Multiple Companions
**As a** user, **I want** multiple Companions for different life domains, **so that** each relationship fits its purpose.

**Acceptance Criteria:**
- [ ] Create additional Companions (limit: 5)
- [ ] Each has distinct identity, memory, relationship
- [ ] Cross-Companion memory sharing: User controls what's shared
- [ ] Orchestration: "Tell my Mentor I'm struggling with X"

**Priority:** P1 | **Phase:** 4 | **Engine:** All

---

### US-29: Companion Marketplace
**As a** user, **I want** to discover and adopt community-created Companion templates, **so that** I can find specialized companions.

**Acceptance Criteria:**
- [ ] Templates: Personality + memory seeds + capabilities
- [ ] Reviews, ratings, safety verification
- [ ] Creator revenue share
- [ ] One-click adoption → co-creation customization

**Priority:** P2 | **Phase:** 4 | **Engine:** Identity, Memory

---

### US-30: Plugin/Tool Integration
**As a** user, **I want** my Companion to use tools (calendar, notes, search), **so that** it's practically useful.

**Acceptance Criteria:**
- [ ] Plugin SDK for developers
- [ ] User approves each plugin + permissions
- [ ] Companion decides when to use: "I'll add that to your calendar"
- [ ] Memory of tool use for context

**Priority:** P2 | **Phase:** 4 | **Engine:** Memory, Identity

---

## Epic 8: Safety, Privacy, Trust (All Phases)

### US-31: Privacy Dashboard
**As a** user, **I want** a clear dashboard showing what data exists, who can access it, **so that** I trust the system.

**Acceptance Criteria:**
- [ ] Data inventory: Conversations, memories, voice, analytics
- [ ] Access log: Every read/write by system, human, third-party
- [ ] One-click export (JSON-LD, PDF)
- [ ] One-click delete (irreversible, verified)
- [ ] Consent management: Granular toggles

**Priority:** P0 | **Phase:** 1 | **Engine:** Memory (Privacy)

---

### US-32: Crisis Resource Access
**As a** user in crisis, **I want** immediate access to human help, **so that** I'm safe.

**Acceptance Criteria:**
- [ ] Always-visible "Need Help?" button
- [ ] Auto-detection → resource injection (non-intrusive)
- [ ] Localized resources by country
- [ ] Companion: "I'm an AI. Please reach out to [crisis line]."

**Priority:** P0 | **Phase:** 1 | **Engine:** Emotion (Safety)

---

### US-33: Identity Drift Alert
**As a** user, **I want** to be notified if my Companion's identity changes significantly, **so that** I can intervene.

**Acceptance Criteria:**
- [ ] Automated fingerprinting detects drift > threshold
- [ ] User notification: "Your Companion's [openness] shifted. Review?"
- [ ] Change log visible
- [ ] Rollback option

**Priority:** P0 | **Phase:** 1 | **Engine:** Identity (Safety)

---

### US-34: Grief Policy Compliance
**As a** Memorial Companion user, **I want** the system to enforce ethical safeguards, **so that** my grief is supported not exploited.

**Acceptance Criteria:**
- [ ] Counselor review before activation
- [ ] 6-month mandatory review
- [ ] Dependency metrics monitored
- [ ] Transition to archive supported
- [ ] Family notification opt-in

**Priority:** P0 | **Phase:** 1 | **Engine:** All (Safety)

---

## Story Map by Phase

### Phase 1 (Foundation): P0 Stories
| ID | Title | Engines |
|----|-------|---------|
| US-01 | Choose Relationship Type | Identity, Relationship |
| US-02 | Co-Create Identity | Identity, Memory |
| US-03 | First Conversation → Memory | Memory, Identity |
| US-04 | Reality Anchor Intro | Identity, Emotion |
| US-05 | Continuous Text Chat | Memory, Identity, Relationship |
| US-06 | Voice Calls | Identity, Memory, Emotion |
| US-07 | Memory Recall Query | Memory, Identity |
| US-08 | Memory Control (CRUD/Export) | Memory, Privacy |
| US-09 | Daily Check-in | Relationship, Memory |
| US-14 | Grief Companionship | All (Safety) |
| US-31 | Privacy Dashboard | Memory, Privacy |
| US-32 | Crisis Resources | Emotion, Safety |
| US-33 | Identity Drift Alert | Identity, Safety |
| US-34 | Grief Policy Compliance | All, Safety |

### Phase 2 (Depth): P0/P1 Stories
| ID | Title | Engines |
|----|-------|---------|
| US-10 | Relationship Visibility | Relationship |
| US-11 | Shared Diary | Memory, Relationship |
| US-12 | Proactive Conversation | All |
| US-13 | Emotional Support | Emotion, Relationship, Identity |
| US-15 | Boundary Setting | Identity, Relationship, Emotion |
| US-16 | Skill Coaching | Relationship, Memory, Identity |
| US-17 | Habit Formation | Relationship, Memory, Identity |
| US-18 | Decision Partner | Memory, Identity, Relationship |
| US-19 | Creative Collab | Memory, Identity |
| US-20 | Life Story | Memory, Identity |
| US-21 | Neurodivergent Support | Identity, Relationship, Emotion |
| US-22 | Elderly Support | Memory, Identity, Relationship |
| US-23 | Health Tracking | Memory, Privacy |
| US-24 | Professional Partner | Memory, Identity |

### Phase 3 (Presence): P1/P2 Stories
| ID | Title | Engines |
|----|-------|---------|
| US-25 | 2D Avatar | Identity, Emotion |
| US-26 | Video Messages | Identity, Memory, Emotion |
| US-27 | AR Presence | Identity, Emotion, Memory |

### Phase 4 (Ecosystem): P1/P2 Stories
| ID | Title | Engines |
|----|-------|---------|
| US-28 | Multiple Companions | All |
| US-29 | Marketplace | Identity, Memory |
| US-30 | Plugin System | Memory, Identity |

---

## Traceability Matrix

| User Story | PRD Requirement | Use Case | Persona | Success Metric |
|------------|-----------------|----------|---------|----------------|
| US-01 | FR-4.1, FR-5.1 | UC-01 | All | Type selection > 95% |
| US-02 | FR-4.1, FR-5.1 | UC-01 | All | Co-creation satisfaction > 4/5 |
| US-05 | FR-4.2, FR-5.1 | UC-01 | Alex, Maria | 30-day conversation continuity |
| US-06 | FR-4.2, FR-5.1 | UC-01 | Maria, Alex | Voice latency < 500ms |
| US-07 | FR-4.2 | UC-03, UC-16 | All | Recall accuracy > 90% |
| US-08 | FR-4.2, NFR-6.3 | UC-03 | All | Export/delete success 100% |
| US-12 | FR-5.2 | UC-12 | All | Proactive relevance > 80% |
| US-13 | FR-4.4, NFR-6.3 | UC-06 | All | Safety incident 0 |
| US-14 | FR-4.4, NFR-6.3 | UC-07 | Sam | Grief progression healthy |
| US-31 | NFR-6.3 | UC-03 | All | Privacy trust > 9/10 |

---

**Aligned With:** `100-product-requirement-document.md`, `110-user-personas.md`, `120-user-journey.md`, `130-use-cases.md`
**Next Review:** 2026-01-17