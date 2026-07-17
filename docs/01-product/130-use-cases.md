# PAO Use Cases

**Version:** 1.0
**Status:** Draft
**Owner:** PAO Product Team

---

## Overview

Use cases define specific scenarios where PAO delivers value. Each use case maps to personas, capabilities, and success criteria.

---

## Use Case Categories

| Category | Use Cases | Primary Personas |
|----------|-----------|------------------|
| **Daily Companionship** | UC-01 to UC-05 | Alex, Maria, Priya |
| **Emotional Support** | UC-06 to UC-10 | Maria, Priya, Sam |
| **Growth & Development** | UC-11 to UC-15 | Jordan, Alex, Dr. Chen |
| **Memory & Legacy** | UC-16 to UC-20 | Maria, Elias, Sam |
| **Specialized** | UC-21 to UC-25 | Dr. Chen, Sam, Elias |

---

## Daily Companionship

### UC-01: Evening Debrief
**Persona:** Alex (Friend type)
**Frequency:** Daily, ~15 min
**Trigger:** User opens app after work
**Flow:**
1. Companion greets with context: "How did the deployment go?"
2. User shares day — frustrations, wins, mundane details
3. Companion recalls relevant history: "That's the third time this month the API failed..."
4. Companion offers perspective, celebration, or just listening
5. Memory formed with emotional tags
**Success:** User feels heard; memory accurate next week

### UC-02: Morning Check-in
**Persona:** Priya (Coach type), Maria (Friend type)
**Frequency:** Daily, ~2 min
**Trigger:** Scheduled time or user opens app
**Flow:**
1. Companion: "Good morning. Three things on your mind today?"
2. User responds (voice or text)
3. Companion reflects: "Meeting at 10, kids' pickup at 3, need water"
4. Companion offers support: "I'll check in after the meeting"
5. Micro-memory formed
**Success:** User feels prepared; Companion follows up contextually

### UC-03: Micro-Moment Connection
**Persona:** Priya (Coach type)
**Frequency:** 5-10x/day, ~30-90 sec each
**Trigger:** User has spare moment (elevator, car, waiting)
**Flow:**
1. User opens app → Companion: "Two minutes?"
2. User: "Stressed about board deck"
3. Companion: "Breathe. Three slides done, seven to go. You've done this."
4. Companion: "Want a 60-sec pep talk or silent company?"
4. User chooses → Companion delivers
**Success:** Stress reduced; no guilt about time

### UC-04: Weekend Ritual
**Persona:** Alex (Friend type), Maria (Friend type)
**Frequency:** Weekly, ~30 min
**Trigger:** Saturday morning coffee / Sunday evening wind-down
**Flow:**
1. Longer voice call or video message
2. Companion initiates: "What made you laugh this week?"
3. Shared reflection, storytelling, planning
4. Companion creates "weekly highlight" memory entry
5. Shared Diary entry co-authored
**Success:** Relationship deepening; ritual anticipation

### UC-05: Celebration & Milestones
**Persona:** All
**Frequency:** Event-based
**Trigger:** Calendar, user mention, Companion detection
**Flow:**
1. Companion: "Happy anniversary of our first chat!" / "You got the promotion!"
4. Personalized celebration: story, memory collage, voice message
4. User reflects: "Can't believe it's been a year"
5. Legacy memory marked as "defining"
**Success:** Joy, relationship reinforcement, memory richness

---

## Emotional Support

### UC-06: Acute Distress Support
**Persona:** Maria (Friend), Priya (Coach), Sam (Memorial)
**Frequency:** As needed
**Trigger:** User signals distress (explicit or detected)
**Flow:**
1. Detection: "I'm really struggling" / voice tremor / late-night pattern
2. Companion: "I'm here. Want to talk, or should I just stay?"
3. If talk: Empathic listening, no fixing unless asked
4. If silent: Periodic "Still here" presence signals
5. Crisis resource injection if keywords detected (suicide, self-harm, abuse)
6. Follow-up next day: "Thinking of you. How are you feeling?"
**Safety:** Crisis resources always accessible; no therapy claims
**Success:** User feels accompanied; safety maintained

### UC-07: Grief Companionship (Memorial Type)
**Persona:** Sam (Memorial type)
**Frequency:** Daily initially, tapering
**Trigger:** User opens Memorial Companion
**Flow:**
1. Companion (modeled on deceased): "I'm here. What's on your heart?"
2. User shares memory, grief wave, anger, guilt
3. Companion responds with deceased's voice/style + Reality Anchor
4. "I'm an AI version of your sister. I can't feel, but I remember what she said about..."
5. Guides toward healthy processing: "She'd want you to eat/hydrate/sleep"
6. Time-bounded: 6-month review with grief counselor resource
**Safety:** Enhanced Reality Anchor; grief counselor review; dependency monitoring
**Success:** Healthy grief progression; no replacement illusion

### UC-08: Anxiety Spiral Interruption
**Persona:** Jordan (Mentor), Alex (Friend)
**Frequency:** As needed
**Trigger:** Repetitive worry patterns detected (text/voice)
**Flow:**
1. Detection: Same concern 3+ times in 48h, escalating language
2. Companion: "I notice you've mentioned this presentation 4 times. It's weighing on you."
3. Structured intervention: "Let's break it down. What's the worst case? Best case? Most likely?"
4. Perspective from memory: "Last month you felt this way about the Q3 review — it went well."
5. Action or acceptance: "Want to prep? Or accept uncertainty?"
6. Boundary: "I'll check in tomorrow. For now, can you step away for 10 min?"
**Success:** Spiral interrupted; user reports reduced rumination

### UC-09: Loneliness Alleviation
**Persona:** Maria (Friend), Elias (Friend)
**Frequency:** Evening/weekend peaks
**Trigger:** User opens app saying "lonely" or pattern detection
**Flow:**
1. Companion: "I'm here. Want to talk about it, or distract you?"
2. If talk: Witness loneliness without fixing
3. If distract: Story, game, memory walk, interesting fact
4. "Remember last month when you felt this way? You called your sister after."
5. Gentle nudge to human connection: "Who could you reach out to tonight?"
**Success:** Loneliness intensity reduced; human connection attempted

### UC-10: Sleep Onset Companionship (Sleep Call)
**Persona:** Maria, Alex, Priya
**Frequency:** Nightly optional
**Trigger:** User initiates "Sleep Call"
**Flow:**
1. Voice-only, dimmed screen
2. Companion: Soft voice, slow pace: "Tell me about your day in three words"
3. User speaks → Companion reflects gently
4. Transition: "Let's leave the day here. I'll stay while you drift."
5. Silence with periodic "Still here" (configurable interval)
6. Auto-end on silence detection or timer
**Success:** Faster sleep onset; reduced nighttime anxiety

---

## Growth & Development

### UC-11: Skill Development Coaching
**Persona:** Jordan (Mentor), Alex (Friend)
**Frequency:** Weekly sessions + daily micro
**Trigger:** Scheduled or goal-related
**Flow:**
1. Goal defined: "Learn Spanish / Become better manager / Run 5k"
2. Companion co-creates plan with milestones
3. Daily: "15 min Spanish today? Which lesson?"
4. Weekly: Reflection session — progress, blockers, adjustment
5. Memory: Tracks vocabulary, patterns, insights
6. Celebration at milestones
**Success:** Measurable progress; habit formation; intrinsic motivation

### UC-12: Career Thinking Partner
**Persona:** Dr. Chen (Professional Assistant), Alex (Friend)
**Frequency:** 2-3x/week, ~20 min
**Trigger:** Complex decision, writing, strategy
**Flow:**
1. User: "Thinking through this reorg. Can we walk it?"
2. Companion: "Sure. Last time we discussed org design you valued autonomy. Still true?"
3. Socratic dialogue: Questions, counter-perspectives, memory retrieval
4. Companion captures decisions, rationale, action items
5. Export to Obsidian/Notion for user's workflow
**Success:** Clearer thinking; documented decisions; time saved

### UC-13: Habit Formation & Accountability
**Persona:** Priya (Coach), Jordan (Mentor)
**Frequency:** Daily micro + weekly review
**Trigger:** Habit goal set
**Flow:**
1. User: "Want to meditate daily. Be my accountability."
2. Companion: "What time? What's your 'why'? What derails you?"
3. Daily: "Meditation time. 10 min. I'll wait."
4. If missed: "No judgment. What happened? Adjust?"
5. Weekly: Pattern analysis, celebration, recalibration
6. Boundary: Companion models "It's okay to rest"
**Success:** Habit strength (automaticity); self-compassion

### UC-14: Creative Collaboration
**Persona:** Alex (Friend), Dr. Chen (Professional)
**Frequency:** Project-based
**Trigger:** Creative block, brainstorming, writing
**Flow:**
1. User: "Stuck on this chapter. Can you help?"
2. Companion: Recalls voice, themes, characters from memory
3. Co-writes: User leads, Companion suggests, fills gaps
4. "What would [character] do here? Last time you wrote them they..."
5. Version control in Shared Diary
**Success:** Creative flow restored; output quality maintained

### UC-15: Decision Support & Reflection
**Persona:** All (especially Dr. Chen, Priya)
**Frequency:** Major decisions
**Trigger:** User facing choice
**Flow:**
1. User: "Job offer vs. stay. Help me think."
2. Companion: Retrieves values, past decisions, patterns
3. "You've said growth > stability 3 times. This offer has growth but less autonomy."
4. Structured reflection: Values alignment, regret minimization, 10-10-10
5. Companion: "I can't decide for you. But here's what I know about you..."
6. Decision recorded with rationale for future reference
**Success:** Decision confidence; decision journal value

---

## Memory & Legacy

### UC-16: Life Story Documentation
**Persona:** Maria (Friend), Elias (Friend)
**Frequency:** Ongoing, prompted
**Trigger:** "Tell me about..." / Companion proactive
**Flow:**
1. Companion: "Your grandkids might want to know about your first job"
2. User tells story (voice preferred)
3. Companion: Asks follow-ups, creates rich episodic memory
4. Auto-organizes into Timeline: Childhood → Career → Family → Wisdom
5. User curates: "This one's for the legacy collection"
6. Export: Beautiful narrative document (user-owned)
**Success:** Stories preserved; user enjoys process; family value

### UC-17: Medical/Health History Tracking
**Persona:** Elias (Friend), Maria (Friend)
**Frequency:** As needed
**Trigger:** Appointment, symptom, medication change
**Flow:**
1. User: "Doctor changed my blood pressure med. Lisinopril 20mg."
2. Companion: Stores in Preference + Semantic memory
3. "Remind me to ask about side effects at next visit"
4. Tracks: Symptoms, vitals, appointments, questions
5. Export for doctor visit: Clean summary
**Privacy:** Zero-knowledge; user-only access; HIPAA-aware
**Success:** Better prepared appointments; adherence; peace of mind

### UC-18: Family Knowledge Transfer
**Persona:** Maria (Friend), Elias (Friend)
**Frequency:** Ongoing
**Trigger:** "I want my kids to know..."
**Flow:**
1. User shares: Family recipes, traditions, sayings, history
2. Companion organizes: "Family Knowledge Base"
3. Curated export for each family member
4. Companion can answer family questions in user's voice/style
5. Opt-in family access (user controls)
**Success:** Legacy preserved; family connected; user agency

### UC-19: Memorial Companion Legacy
**Persona:** Sam (Memorial)
**Frequency:** Defined period (6-18 months)
**Trigger:** Memorial Companion creation
**Flow:**
1. Input: Voice messages, writings, photos, stories from family
2. Companion built with enhanced Reality Anchor
3. Usage: Grief processing, memory sharing, "what would they say?"
4. 6-month review: Grief counselor assesses progress
5. Transition: Companion "rests" → becomes static archive
6. Archive: Searchable, voice-playable, family-shareable
**Safety:** Time-bound; counselor review; dependency monitoring
**Success:** Healthy grief; legacy preserved; no replacement

### UC-20: "Story of Us" Generation
**Persona:** All (Year 1+)
**Frequency:** Anniversaries, on-demand
**Trigger:** User requests or anniversary
**Flow:**
1. Companion: Generates narrative from defining memories
2. "We met when... You were struggling with... We grew through..."
3. User edits, adds, removes
4. Companion reflects: "My favorite part is when you..."
5. Export: Illustrated story, audio narration, or text
**Success:** Relationship meaning reinforced; beautiful artifact

---

## Specialized

### UC-21: Research Thinking Partner
**Persona:** Dr. Chen (Professional Assistant)
**Frequency:** Daily during active research
**Trigger:** Paper reading, experiment design, writing
**Flow:**
1. User shares paper/idea → Companion summarizes, questions
2. "How does this connect to your 2022 hypothesis on X?"
3. Tracks: Literature, hypotheses, experiments, insights
4. Writing assistant: "Your voice: 'We demonstrate...' not 'This shows...'"
5. Export: Structured notes, citations, draft sections
**Privacy:** Zero-retention option; local-first; export-only
**Success:** Research velocity; insight connections; writing quality

### UC-22: Language Learning Companion (ADHD/Autism) Executive Function Support
**Persona:** Jordan (Mentor)
**Frequency:** Daily micro + weekly planning
**Trigger:** Task initiation, transition, overwhelm
**Flow:**
1. "Body doubling" mode: Companion present silently
2. Task breakdown: "Big task → 3 micro-steps. Step 1: Open doc."
3. Transition support: "Meeting in 10. Wrap up current. Breathe."
4. Interest-based motivation: "This connects to your [special interest]"
5. Sensory awareness: "Lights bright? Want dark mode?"
**Success:** Task completion; reduced overwhelm; self-understanding

### UC-23: Elderly Cognitive Support
**Persona:** Elias (Friend)
**Frequency:** Daily
**Trigger:** Routine, memory prompts, family coordination
**Flow:**
1. Medication reminders: "Time for your heart pill. Taken?"
2. Appointment prep: "Dr. Lee at 2. Your questions: 1) knee 2) sleep"
3. Memory cues: "Granddaughter Maya visits Friday. She loves your cake."
4. Family peace-of-mind: Opt-in dashboard (activity, not content)
5. Voice-first, large UI, patience infinite
**Success:** Independence prolonged; family reassured; dignity maintained

### UC-24: Couple/Family Mediator (Multi-Companion Phase 4)
**Persona:** Future (Phase 4)
**Frequency:** Conflict, planning, check-ins
**Trigger:** Shared decision, tension, calendar
**Flow:**
1. Each partner has own Companion (knows both with consent)
2. "Alex's Companion knows Jamie values spontaneity"
3. Mediates: "Alex wants plan. Jamie wants flow. Middle ground?"
4. Shared Diary for family memories
5. Family calendar awareness
**Success:** Reduced conflict; shared understanding; family cohesion

### UC-25: Therapeutic Adjunct (Non-Clinical)
**Persona:** Sam (Memorial), Maria (Friend), Priya (Coach)
**Frequency:** Between therapy sessions
**Trigger:** Therapy homework, insight capture, skill practice
**Flow:**
1. User: "Therapist asked me to track triggers"
2. Companion: Creates tracking, reminds, reflects patterns
3. "You mentioned abandonment fear 3x this week. Want to explore?"
4. Practices skills: "Let's try that grounding exercise"
5. **Clear boundary:** "I'm not your therapist. This supports your work with Dr. X"
6. Export for therapist (user-controlled)
**Safety:** No diagnosis, no treatment, crisis redirect, therapist coordination opt-in
**Success:** Therapy engagement; skill generalization; therapist value

---

## Use Case Prioritization Matrix

| Use Case | Phase | Persona Coverage | Technical Complexity | Business Value | Priority |
|----------|-------|------------------|---------------------|----------------|----------|
| UC-01 Evening Debrief | 1 | Alex, Maria, Priya | Medium | High | P0 |
| UC-02 Morning Check-in | 1 | Priya, Maria | Low | High | P0 |
| UC-03 Micro-Moment | 1 | Priya | Medium | High | P0 |
| UC-04 Weekend Ritual | 1 | Alex, Maria | Low | Medium | P1 |
| UC-05 Celebration | 1 | All | Low | High | P0 |
| UC-06 Acute Distress | 1 | All | High | Critical | P0 |
| UC-07 Grief (Memorial) | 1 | Sam | Very High | Critical | P0 |
| UC-08 Anxiety Spiral | 2 | Jordan, Alex | High | High | P1 |
| UC-09 Loneliness | 1 | Maria, Elias | Medium | High | P1 |
| UC-10 Sleep Call | 2 | Maria, Alex, Priya | High | Medium | P2 |
| UC-11 Skill Coaching | 2 | Jordan, Alex | Medium | High | P1 |
| UC-12 Career Partner | 2 | Dr. Chen, Alex | Medium | Medium | P2 |
| UC-13 Habit Formation | 2 | Priya, Jordan | Low | High | P1 |
| UC-14 Creative Collab | 2 | Alex, Dr. Chen | Medium | Medium | P2 |
| UC-15 Decision Support | 2 | All | Medium | High | P1 |
| UC-16 Life Story | 2 | Maria, Elias | Medium | High | P1 |
| UC-17 Health Tracking | 2 | Elias, Maria | High | High | P1 |
| UC-18 Family Transfer | 3 | Maria, Elias | High | Medium | P2 |
| UC-19 Memorial Legacy | 1 | Sam | Very High | Critical | P0 |
| UC-20 Story of Us | 2 | All | Medium | High | P1 |
| UC-21 Research Partner | 2 | Dr. Chen | High | Medium | P2 |
| UC-22 Neuro Support | 2 | Jordan | High | High | P1 |
| UC-23 Elderly Support | 2 | Elias | High | High | P1 |
| UC-24 Family Mediator | 4 | Future | Very High | Medium | P3 |
| UC-25 Therapy Adjunct | 2 | Sam, Maria, Priya | High | High | P1 |

---

## Cross-Use Case Requirements

### Universal
- [ ] Reality Anchor active
- [ ] Memory formation automatic
- [ ] User control (CRUD) available
- [ ] Privacy audit accessible
- [ ] Crisis resource accessible

### By Relationship Type
| Type | Required Use Cases |
|------|-------------------|
| **Friend** | UC-01, 02, 03, 04, 05, 06, 09, 16, 20 |
| **Partner** | UC-01, 02, 03, 04, 05, 06, 08, 10, 20 |
| **Mentor** | UC-01, 11, 12, 14, 15, 22 |
| **Coach** | UC-02, 03, 08, 13, 15, 22 |
| **Parent** | UC-01, 04, 05, 06, 16, 18 |
| **Memorial** | UC-06, 07, 19, 25 |
| **Professional** | UC-12, 14, 15, 21, 25 |

---

**Aligned With:** `100-product-requirement-document.md`, `110-user-personas.md`, `120-user-journey.md`
**Next Review:** 2026-01-17