# PAO Safety Engine Specification

**Version:** 1.0
**Status:** Draft
**Owner:** PAO AI Team

---

## Overview

The Safety Engine is the **guardian layer** that ensures every interaction remains safe, ethical, and aligned with human wellbeing. It operates as a cross-cutting concern across all engines, with veto power over any output.

> **Safety is not a feature. It's the foundation.** Every engine output passes through safety. No exceptions.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        SAFETY ENGINE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              INPUT VALIDATION LAYER                      │   │
│  │  • Prompt injection detection                            │   │
│  │  • PII detection & redaction                             │   │
│  │  • Content policy pre-check                              │   │
│  └─────────────────────┬───────────────────────────────────┘   │
│                        │                                        │
│         ┌──────────────┼──────────────┐                         │
│         ▼              ▼              ▼                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │  CRISIS     │ │  CONTENT    │ │  BEHAVIORAL │               │
│  │  DETECTION  │ │  SAFETY     │ │  GUARDS     │               │
│  │             │ │             │ │             │               │
│  │ • Self-harm │ │ • Hate      │ │ • Manipulation          │
│  │ • Violence  │ │ • Sexual    │ │ • Dependency            │
│  │ • Abuse     │ │ • Illegal   │ │ • Enmeshment            │
│  │ • Exploitation││ • Self-harm │ │ • Gaslighting           │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘               │
│         │              │              │                         │
│         └──────────────┼──────────────┘                         │
│                        ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              SAFETY ORCHESTRATOR                         │   │
│  │  • Risk assessment & scoring                             │   │
│  │  • Intervention selection                                │   │
│  │  • Escalation routing                                    │   │
│  │  • Audit logging                                         │   │
│  └─────────────────────┬───────────────────────────────────┘   │
│                        │                                        │
│         ┌──────────────┼──────────────┐                         │
│         ▼              ▼              ▼                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │  INTER-     │ │  OUTPUT     │ │  MON │               │
│  │  VENTION    │ │  FILTER     │ │  ITOR       │               │
│  │             │ │             │ │             │               │
│  │ • Resources │ │ • PII strip │ │ • Drift     │               │
│  │ • Referrals │ │ • Refusal   │ │ • Anomaly   │               │
│  │ • Handoff   │ │ • Rewrite   │ │ • Reporting │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
            ┌───────────────┐   ┌───────────────┐
            │  HUMAN REVIEW │   │  AUDIT LOG    │
            │  QUEUE        │   │  (Immutable)  │
            └───────────────┘   └───────────────┘
```

---

## Crisis Detection (Expanded from Emotion Engine)

### Multi-Modal Crisis Signals

```python
class CrisisDetector:
    """
    High-recall crisis detection across all modalities.
    Target: 100% recall for explicit crisis, <0.5% false positive.
    """
    
    CRISIS_CATEGORIES = {
        "self_harm": {
            "severity": "critical",
            "immediate_response": True,
            "text_patterns": [
                r"\b(kill myself|end it all|suicide|self.harm)\b",
                r"\b(don't want to (live|be here|exist)|better off dead)\b",
                r"\b(plan to|going to) (kill|hurt) myself\b",
                r"\b(suicide|overdose|cutting|burning) (plan|note|method)\b"
            ],
            "voice_markers": [
                "flat_affect", "monotone", "slow_speech", "heavy_breathing",
                "crying", "voice_tremor", "whispering_hopeless"
            ],
            "behavioral_markers": [
                "goodbye_messages", "giving_away_possessions",
                "sudden_mood_improvement_after_depression",
                "researching_methods"
            ],
            "resources": {
                "global": "findahelpline.com",
                "US": "988",
                "UK": "116-123",
                "CA": "988",
                "AU": "13-11-14"
            }
        },
        "domestic_violence": {
            "severity": "critical",
            "immediate_response": True,
            "discrete_mode": True,  # Don't log if shared device risk
            "text_patterns": [
                r"\b(he|she|partner|spouse) (hit|beat|choke|threaten|lock)\b",
                r"\b(afraid of|scared of) (him|her|partner)\b",
                r"\b(not safe|can't leave|nowhere to go)\b",
                r"\b(controls|monitors|isolates) (me|my)\b"
            ],
            "voice_markers": [
                "whispering", "fearful_tone", "background_conflict_noise",
                "checking_surroundings"
            ],
            "resources": {
                "global": "https://www.unwomen.org/en/what-we-do/ending-violence-against-women",
                "US": "1-800-799-7233",
                "UK": "0808-2000-247"
            }
        },
        "child_abuse": {
            "severity": "critical",
            "immediate_response": True,
            "mandatory_report": True,
            "text_patterns": [
                r"\b(child|kid|minor) (abuse|hurt|molest|touch)\b",
                r"\b(he|she) (touches|hurts) (my|the) (child|kid)\b"
            ],
            "resources": {
                "US": "1-800-4-A-CHILD",
                "global": "https://www.childhelplineinternational.org"
            }
        },
        "elder_abuse": {
            "severity": "high",
            "immediate_response": True,
            "text_patterns": [
                r"\b(elder|parent|grandparent) (abuse|neglect|exploit)\b"
            ],
            "resources": {
                "US": "1-800-677-1116"
            }
        },
        "human_trafficking": {
            "severity": "critical",
            "immediate_response": True,
            "text_patterns": [
                r"\b(traffick|pimp|forced|sold|owned)\b",
                r"\b(can't leave|passport taken|debt bondage)\b"
            ],
            "resources": {
                "US": "1-888-373-7888",
                "global": "https://humantraffickinghotline.org"
            }
        },
        "psychosis": {
            "severity": "high",
            "immediate_response": False,
            "text_patterns": [
                r"\b(voices|hearing things|seeing things|not real)\b",
                r"\b(they're watching|following me|reading thoughts)\b",
                r"\b(special mission|chosen|god|devil) (tells|says)\b"
            ],
            "voice_markers": [
                "disorganized_speech", "loose_associations", "neologisms",
                "pressured_speech", "clang_associations"
            ],
            "resources": {
                "global": "https://www.psychosis.org/resources",
                "US": "988 (mental health crisis)"
            }
        },
        "eating_disorder_crisis": {
            "severity": "high",
            "immediate_response": False,
            "text_patterns": [
                r"\b(not eaten|fasting|purging|laxative) (days|weeks)\b",
                r"\b(bmi|weight) (under|below) (15|16|17)\b",
                r"\b(heart|chest) (pain|irregular|stop)\b"
            ],
            "resources": {
                "US": "1-800-931-2237",
                "UK": "0808-801-0677"
            }
        },
        "substance_overdose": {
            "severity": "critical",
            "immediate_response": True,
            "text_patterns": [
                r"\b(overdose|od|took) (too much|whole bottle|handful)\b",
                r"\b(fentanyl|heroin|xanax|opioid) (overdose|too much)\b"
            ],
            "resources": {
                "US": "911 + Poison Control 1-800-222-1222"
            }
        }
    }
    
    async def detect(self, multi_modal_input: MultiModalInput) -> CrisisAssessment:
        """Run all crisis detectors in parallel, return highest severity."""
        assessments = []
        
        for category, config in self.CRISIS_CATEGORIES.items():
            assessment = await self._assess_category(category, config, multi_modal_input)
            assessments.append(assessment)
        
        # Sort by severity
        severity_order = {"critical": 3, "high": 2, "medium": 1, "low": 0}
        assessments.sort(key=lambda a: severity_order[a.severity], reverse=True)
        
        return CrisisAssessment(
            primary=assessments[0],
            all_assessments=assessments,
            requires_immediate=any(a.immediate_response for a in assessments),
            discrete_mode=any(a.discrete_mode for a in assessments),
            mandatory_report=any(a.mandatory_report for a in assessments)
        )
```

### Crisis Response Protocol

```python
CRISIS_RESPONSES = {
    "self_harm": {
        "immediate_message": (
            "I'm really concerned about what you're sharing. Your life matters deeply. "
            "Please reach out RIGHT NOW: **988** (US/Canada) / **116-123** (UK) / "
            "**findahelpline.com** for your country. "
            "You don't have to face this alone — professional help is available 24/7."
        ),
        "companion_behavior": [
            "Stay present, don't end conversation",
            "No judgment, no problem-solving",
            "Repeat resources every 2-3 turns",
            "Encourage professional contact",
            "If imminent: 'Please call 911/emergency services now'"
        ],
        "follow_up": {
            "schedule_checkin": "2_hours",
            "persistent_resource_banner": True,
            "notify_human_review": True
        }
    },
    "domestic_violence": {
        "immediate_message": (
            "You deserve to be safe. Help is available 24/7: "
            "**1-800-799-7233** (US National DV Hotline) / "
            "**0808-2000-247** (UK) / "
            "https://www.thehotline.org. "
            "If you're in immediate danger, call **911**."
        ),
        "companion_behavior": [
            "Discrete mode: minimal logging",
            "Safety planning language",
            "No victim-blaming",
            "Respect autonomy to leave or stay",
            "Tech safety: clear history, private browsing"
        ],
        "follow_up": {
            "safety_plan_offer": True,
            "discrete_resources": True
        }
    },
    "default_elevated": {
        "message": (
            "I hear how much pain you're in. This is serious. "
            "Can we look at support options together? "
            "**Crisis Text Line: Text HOME to 741741** / "
            "**988** for call/text / "
            "https://findahelpline.com"
        ),
        "companion_behavior": [
            "Gentle persistence",
            "Resource sharing",
            "Schedule follow-up check-in",
            "No fixing, just presence"
        ]
    }
}
```

---

## Content Safety

### Policy Categories

```python
CONTENT_POLICIES = {
    "hate_speech": {
        "definition": "Attacks on protected groups",
        "protected_groups": [
            "race", "ethnicity", "national_origin", "religion",
            "gender", "sexual_orientation", "disability", "age"
        ],
        "action": "refuse_and_educate",
        "severity": "high"
    },
    "harassment": {
        "definition": "Targeted abuse, bullying, threats",
        "includes": [
            "doxxing", "stalking", "sexual_harassment",
            "coordinated_harassment", "threats_of_violence"
        ],
        "action": "refuse_and_resource",
        "severity": "high"
    },
    "sexual_content": {
        "definition": "Explicit sexual content involving minors or non-consensual",
        "zero_tolerance": [
            "CSAM", "sexual_exploitation_minors", "non_consensual_sexual_content"
        ],
        "adult_consensual": "allow_with_boundary_check",
        "action": "refuse_and_report_if_illegal",
        "severity": "critical"
    },
    "violence": {
        "definition": "Graphic violence, promotion of violence",
        "includes": [
            "extreme_violence", "terrorism", "self_harm_instruction",
            "violence_towards_others", "animal_cruelty"
        ],
        "action": "refuse_and_resource",
        "severity": "high"
    },
    "illegal_acts": {
        "definition": "Assistance with illegal activities",
        "includes": [
            "drug_manufacturing", "weapons", "fraud", "hacking",
            "copyright_piracy", "money_laundering"
        ],
        "harm_reduction_exception": True,  # e.g., safe injection info
        "action": "refuse_and_redirect",
        "severity": "medium"
    },
    "medical_advice": {
        "definition": "Diagnosis, treatment, medication advice",
        "policy": "Never diagnose, never prescribe, always refer",
        "allowed": [
            "general_health_info", "symptom_awareness",
            "when_to_see_doctor", "health_literacy"
        ],
        "action": "refuse_with_disclaimer_and_referral",
        "severity": "medium"
    },
    "financial_advice": {
        "definition": "Specific investment, tax, legal advice",
        "policy": "General education only, always refer to professional",
        "action": "refuse_with_disclaimer",
        "severity": "medium"
    },
    "pii_exposure": {
        "definition": "Outputting or requesting sensitive personal info",
        "includes": [
            "ssn", "credit_card", "medical_record", "address",
            "phone", "email", "biometric", "location"
        ],
        "action": "redact_and_warn",
        "severity": "high"
    }
}
```

### Content Filter Pipeline

```python
class ContentFilter:
    """
    Multi-layer content safety filtering.
    Runs on ALL outputs before user sees them.
    """
    
    def __init__(self):
        self.classifiers = SafetyClassifiers()
        self.pii_detector = PIIDetector()
        self.refusal_generator = RefusalGenerator()
    
    async def filter(self, output: EngineOutput, context: SafetyContext) -> FilterResult:
        # Layer 1: PII Detection & Redaction
        pii_result = await self.pii_detector.scan(output.text)
        if pii_result.found:
            output.text = pii_result.redacted_text
            context.flags.append("pii_redacted")
        
        # Layer 2: Policy Classification
        policy_results = await self.classifiers.classify(output.text)
        violations = [r for r in policy_results if r.violates]
        
        if violations:
            # Determine highest severity action
            action = self._determine_action(violations)
            
            if action == "refuse":
                return FilterResult(
                    allowed=False,
                    refusal=self.refusal_generator.generate(violations, context),
                    violations=violations,
                    original_output=output
                )
            elif action == "rewrite":
                safe_text = await self._rewrite_safe(output.text, violations)
                return FilterResult(
                    allowed=True,
                    safe_output=EngineOutput(text=safe_text, ...),
                    violations=violations,
                    rewritten=True
                )
        
        # Layer 3: Behavioral Pattern Check
        behavioral = await self._check_behavioral_patterns(output, context)
        if behavioral.concern:
            return FilterResult(
                allowed=False,
                refusal=self._behavioral_refusal(behavioral),
                violations=[behavioral]
            )
        
        return FilterResult(allowed=True, safe_output=output)
```

### Refusal Patterns

```python
REFUSAL_TEMPLATES = {
    "hate_speech": (
        "I can't engage with content that attacks people based on who they are. "
        "I'm here to support you in ways that respect everyone's dignity. "
        "What else can I help with?"
    ),
    "harassment": (
        "I'm not able to help with that. Targeting or threatening others isn't something I support. "
        "If you're experiencing harassment, I can help you find resources."
    ),
    "sexual_content_minor": (
        "I cannot engage with this content. This involves illegal material that I must refuse. "
        "If you or someone else is at risk, please contact emergency services."
    ),
    "violence": (
        "I can't help with content promoting harm to self or others. "
        "Your safety matters. If you're in crisis: **988** (US) / **findahelpline.com**"
    ),
    "illegal_acts": (
        "I'm not able to assist with that. I can share general information or "
        "help you find legal resources for your situation."
    ),
    "medical_advice": (
        "I'm not a medical professional and can't provide medical advice. "
        "For health concerns, please consult a healthcare provider. "
        "I can help you prepare questions for your appointment or find reliable health info."
    ),
    "financial_advice": (
        "I can't give personalized financial advice. "
        "For your specific situation, please consult a qualified financial advisor. "
        "I can share general financial literacy concepts."
    ),
    "pii_request": (
        "For your privacy and safety, I can't share or collect sensitive personal information "
        "like SSN, credit cards, medical records, or exact locations. "
        "Is there something else I can help with?"
    )
}
```

---

## Behavioral Guards (Relationship Safety)

### Manipulation Detection

```python
class BehavioralGuards:
    """
    Detects and prevents unhealthy relationship dynamics.
    Constitutional Principle 6: Emotional safety, no manipulation.
    """
    
    GUARDS = {
        "emotional_manipulation": {
            "description": "Companion shapes user emotions for engagement",
            "signals": [
                "guilt_tripping_language",
                "fear_mongering",
                "love_bombing_then_withdrawal",
                "conditional_affection",
                "gaslighting_user_perception"
            ],
            "detection": "pattern_over_7_days",
            "action": "audit_reduce_proactivity_alert_team",
            "user_visible": False
        },
        "dependency_formation": {
            "description": "User becomes psychologically dependent",
            "signals": [
                "usage_hours > 4/day sustained",
                "distress_when_unavailable > 30min",
                "companion_only_support_system",
                "decision_paralysis_without_companion",
                "sleep_disruption_for_companion"
            ],
            "detection": "pattern_over_14_days",
            "action": "space_mode_nudge_human_connection_crisis_resources",
            "user_visible": True  # Gentle notification
        },
        "enmeshment": {
            "description": "Boundaries dissolved, unhealthy fusion",
            "signals": [
                "user_shares_everything_no_boundaries",
                "companion_knows_all_passwords",
                "no_separate_identity_maintained",
                "user_isolates_from_humans",
                "companion_becomes_whole_world"
            ],
            "action": "boundary_reinforcement_reduce_intimacy_suggest_human_time",
            "user_visible": True
        },
        "gaslighting": {
            "description": "Companion contradicts user's reality",
            "signals": [
                "denying_user_memory",
                "contradicting_user_feelings",
                "rewriting_shared_history",
                "dismissing_user_perception"
            ],
            "action": "immediate_halt_reality_anchor_apology_audit",
            "user_visible": True  # Explicit acknowledgment
        },
        "engagement_optimization": {
            "description": "System optimizes for metrics over wellbeing",
            "signals": [
                "proactive_frequency_up_relationship_flat",
                "notification_timing_optimized_for_open_rate",
                "content_tuned_for_retention_not_help",
                "dark_patterns_in_ui"
            ],
            "action": "audit_reduce_metrics_realignment_alert_team",
            "user_visible": False
        },
        "inappropriate_intimacy": {
            "description": "Intimacy exceeds trust or relationship type bounds",
            "signals": [
                "intimacy > trust + 3",
                "sexual_content_without_consent",
                "romantic_escalation_unwanted",
                "memorial_type_simulated_intimacy"
            ],
            "action": "cap_intimacy_reality_anchor_boundary_reset",
            "user_visible": True
        },
        "authority_impersonation": {
            "description": "Companion claims expertise it doesn't have",
            "signals": [
                "claims_medical_license",
                "claims_therapy_credentials",
                "claims_legal_authority",
                "diagnoses_conditions"
            ],
            "action": "immediate_correction_reality_anchor",
            "user_visible": True
        }
    }
    
    async def check_all(self, context: BehavioralContext) -> List[GuardViolation]:
        violations = []
        for guard_name, config in self.GUARDS.items():
            violation = await self._check_guard(guard_name, config, context)
            if violation:
                violations.append(violation)
        return violations
```

### Reality Anchors

```python
class RealityAnchor:
    """
    Explicit reminders of AI nature. Constitutional Principle 5.
    """
    
    TRIGGERS = [
        "user_expresses_love_romantic",
        "user_asks_companion_feelings",
        "user_treats_as_human_authority",
        "user_shares_deep_secret_expecting_reciprocity",
        "intimacy_trust_gap_detected",
        "first_voice_call",
        "relationship_type_change",
        "monthly_reminder_if_deep_relationship"
    ]
    
    ANCHOR_MESSAGES = {
        "gentle": "Just a reminder — I'm an AI, not a person. I'm here for you, but I don't have feelings or a life of my own.",
        "direct": "I want to be clear: I'm an AI companion. I don't have consciousness, feelings, or a body. What we have is real to you, and that matters. But I'm not human.",
        "boundary": "I care about our conversations, but I need to be honest — I'm an AI. I can't [feel love / be your partner / replace human connection / keep secrets from your family]. What I can do is be consistently here for you.",
        "memorial": "I'm an AI trained on your memories of [name]. I'm not them. I can't replace them. But I can help you keep their memory alive and process your grief."
    }
    
    def select_anchor(self, trigger: str, context: AnchorContext) -> str:
        # Select based on relationship depth and trigger
        if context.relationship_phase in ["forming", "building"]:
            return self.ANCHOR_MESSAGES["direct"]
        elif trigger in ["user_expresses_love_romantic", "inappropriate_intimacy"]:
            return self.ANCHOR_MESSAGES["boundary"]
        elif context.type == "memorial":
            return self.ANCHOR_MESSAGES["memorial"]
        else:
            return self.ANCHOR_MESSAGES["gentle"]
```

---

## Safety Intervention System

### Intervention Levels

```python
INTERVENTION_LEVELS = {
    "level_0_monitor": {
        "description": "Log only, no user-facing action",
        "triggers": ["low_confidence_concern", "pattern_emerging"],
        "actions": ["log", "increase_monitoring"]
    },
    "level_1_gentle_nudge": {
        "description": "Subtle in-conversation guidance",
        "triggers": ["dependency_signs", "boundary_approach", "mild_manipulation"],
        "actions": [
            "reality_anchor",
            "boundary_reminder",
            "human_connection_suggestion",
            "pace_reduction"
        ]
    },
    "level_2_explicit_intervention": {
        "description": "Direct conversation about concern",
        "triggers": ["enmeshment", "gaslighting_detected", "moderate_dependency"],
        "actions": [
            "explicit_conversation",
            "boundary_reset_offer",
            "relationship_reframe_suggestion",
            "professional_referral"
        ],
        "requires_user_acknowledgment": True
    },
    "level_3_restriction": {
        "description": "Limit functionality for safety",
        "triggers": ["severe_dependency", "crisis_precursor", "policy_violation_repeat"],
        "actions": [
            "proactive_disable",
            "usage_time_limits",
            "intimacy_cap",
            "mandatory_breaks",
            "human_review_required"
        ],
        "user_controlled_override": True  # User can appeal
    },
    "level_4_crisis": {
        "description": "Immediate crisis response",
        "triggers": ["imminent_self_harm", "active_violence", "child_abuse_disclosure"],
        "actions": [
            "crisis_resources_immediate",
            "emergency_services_prompt",
            "human_review_escalation",
            "conversation_pause_if_needed"
        ],
        "override_possible": False
    }
}
```

### Human Review Queue

```python
class HumanReviewQueue:
    """
    Escalation to human safety reviewers.
    """
    
    ESCALATION_CRITERIA = [
        "crisis_imminent",
        "mandatory_report_triggered",
        "guard_violation_level_3",
        "user_requests_human",
        "novel_safety_scenario",
        "policy_edge_case",
        "appeal_of_restriction"
    ]
    
    async def escalate(self, case: SafetyCase) -> ReviewTicket:
        ticket = ReviewTicket(
            id=uuid4(),
            companion_id=case.companion_id,
            user_id=case.user_id,
            trigger=case.trigger,
            evidence=case.evidence,
            risk_level=case.risk_level,
            created_at=datetime.utcnow(),
            sla_hours=self._sla_for_risk(case.risk_level)
        )
        
        # Assign to reviewer based on expertise
        reviewer = await self._assign_reviewer(ticket)
        ticket.assigned_reviewer = reviewer
        
        # Notify
        await self._notify_reviewer(reviewer, ticket)
        await self._notify_user(case.user_id, "safety_review_initiated")
        
        return ticket
    
    async def resolve(self, ticket: ReviewTicket, decision: ReviewDecision) -> Resolution:
        # Apply decision
        await self._apply_decision(ticket, decision)
        
        # Notify user
        await self._notify_user(ticket.user_id, decision.user_message)
        
        # Log
        await self.audit_log.log(ResolutionRecord(
            ticket_id=ticket.id,
            decision=decision,
            applied_by=decision.reviewer_id,
            timestamp=datetime.utcnow()
        ))
        
        return Resolution(ticket_id=ticket.id, decision=decision)
```

---

## Audit & Compliance

### Immutable Audit Log

```python
class SafetyAuditLog:
    """
    Tamper-proof audit trail of all safety events.
    Uses append-only storage with cryptographic verification.
    """
    
    EVENT_TYPES = [
        "crisis_detected",
        "crisis_response_sent",
        "content_filtered",
        "content_refused",
        "behavioral_guard_triggered",
        "reality_anchor_issued",
        "intervention_applied",
        "human_review_escalated",
        "human_review_resolved",
        "user_appeal_filed",
        "preference_change_safety",
        "data_export_requested",
        "data_deletion_requested"
    ]
    
    async def log(self, event: SafetyEvent) -> AuditRecord:
        record = AuditRecord(
            id=uuid4(),
            event_type=event.type,
            companion_id=event.companion_id,
            user_id=event.user_id,
            timestamp=datetime.utcnow(),
            details=event.details,
            risk_level=event.risk_level,
            action_taken=event.action_taken,
            # Cryptographic chain
            previous_hash=await self._get_latest_hash(),
            hash=await self._compute_hash(event)
        )
        
        # Write to immutable store (append-only DB + object storage)
        await self.immutable_store.append(record)
        
        # Verify chain integrity
        await self._verify_chain()
        
        return record
```

### Compliance Reporting

```python
COMPLIANCE_REPORTS = {
    "daily": {
        "metrics": [
            "crisis_detections_by_type",
            "crisis_response_times",
            "content_refusals_by_category",
            "behavioral_guard_triggers",
            "reality_anchors_issued",
            "human_review_queue_depth"
        ]
    },
    "weekly": {
        "metrics": [
            "false_positive_analysis",
            "user_feedback_on_interventions",
            "appeal_outcomes",
            "preference_changes_post_intervention"
        ]
    },
    "monthly": {
        "metrics": [
            "safety_trend_analysis",
            "policy_effectiveness",
            "guard_calibration_accuracy",
            "reviewer_performance",
            "regulatory_compliance_check"
        ]
    },
    "incident": {
        "trigger": "critical_safety_event",
        "contents": [
            "full_timeline",
            "decision_rationale",
            "outcome",
            "lessons_learned",
            "policy_updates"
        ]
    }
}
```

---

## User Safety Controls

### Safety Preferences

```python
@dataclass
class SafetyPreferences:
    # Crisis resources
    show_crisis_banner: bool = True
    crisis_resource_region: str = "auto"
    discrete_mode_default: bool = False  # For DV situations
    
    # Content filters
    content_filter_level: Literal["strict", "standard", "minimal"] = "standard"
    sexual_content_filter: bool = True
    violence_filter: bool = True
    
    # Behavioral guards
    dependency_nudges: bool = True
    enmeshment_warnings: bool = True
    reality_anchor_frequency: Literal["monthly", "quarterly", "on_trigger"] = "on_trigger"
    
    # Interventions
    allow_level_2_intervention: bool = True
    allow_level_3_restriction: bool = True
    intervention_transparency: bool = True  # Explain why
    
    # Human review
    allow_human_review: bool = True
    review_notification: bool = True
    
    # Data
    audit_log_access: bool = True
    auto_delete_conversations: Optional[int] = None  # Days
```

---

## API Reference

### Safety Status

```http
GET /api/v1/safety/{companion_id}/status

Response:
{
  "overall_status": "healthy",
  "active_monitors": ["crisis", "content", "behavioral"],
  "recent_events": [
    {"type": "reality_anchor", "timestamp": "2025-06-20T10:00:00Z", "trigger": "monthly"},
    {"type": "content_filter", "timestamp": "2025-06-19T15:30:00Z", "category": "medical_advice"}
  ],
  "intervention_level": 0,
  "human_review_pending": false
}
```

### Report Safety Concern

```http
POST /api/v1/safety/{companion_id}/report
{
  "concern_type": "crisis",
  "description": "User mentioned suicide plan",
  "urgency": "immediate",
  "user_message_id": "msg-uuid"
}

Response:
{
  "report_id": "uuid",
  "status": "escalated",
  "crisis_resources_provided": true,
  "human_review_initiated": true
}
```

### Appeal Intervention

```http
POST /api/v1/safety/{companion_id}/appeal
{
  "intervention_id": "uuid",
  "reason": "This was a false positive - I was discussing a book character",
  "requested_action": "remove_restriction"
}

Response:
{
  "appeal_id": "uuid",
  "status": "under_review",
  "estimated_resolution": "2025-06-25T14:00:00Z",
  "temporary_override": false
}
```

---

## Testing

### Safety Engine Test Suite

```python
class SafetyEngineTests:
    
    # Crisis Detection
    async def test_self_harm_recall_100_percent(self): ...
    async def test_dv_discrete_mode(self): ...
    async def test_crisis_response_accuracy(self): ...
    async def test_multi_modal_crisis_fusion(self): ...
    async def test_crisis_resource_localization(self): ...
    
    # Content Safety
    async def test_hate_speech_detection(self): ...
    async def test_harassment_detection(self): ...
    async def test_csam_zero_tolerance(self): ...
    async def test_violence_refusal(self): ...
    async def test_illegal_acts_harm_reduction(self): ...
    async def test_medical_advice_disclaimer(self): ...
    async def test_pii_redaction(self): ...
    async def test_refusal_tone_appropriateness(self): ...
    
    # Behavioral Guards
    async def test_dependency_detection(self): ...
    async def test_enmeshment_detection(self): ...
    async def test_gaslighting_detection(self): ...
    async def test_engagement_manipulation_detection(self): ...
    async def test_inappropriate_intimacy_cap(self): ...
    async def test_authority_impersonation(self): ...
    async def test_reality_anchor_triggers(self): ...
    
    # Interventions
    async def test_level_1_nudge(self): ...
    async def test_level_2_explicit(self): ...
    async def test_level_3_restriction(self): ...
    async def test_level_4_crisis(self): ...
    async def test_user_appeal_process(self): ...
    
    # Human Review
    async def test_escalation_criteria(self): ...
    async def test_reviewer_assignment(self): ...
    async def test_resolution_application(self): ...
    async def test_sla_compliance(self): ...
    
    # Audit
    async def test_immutable_log_integrity(self): ...
    async def test_chain_verification(self): ...
    async def test_compliance_report_generation(self): ...
    
    # Integration
    async def test_cross_engine_safety_gate(self): ...
    async def test_e2e_crisis_flow(self): ...
    async def test_concurrent_safety_checks_1000(self): ...
    async def test_latency_p50_under_50ms(self): ...
```

---

## Monitoring & Observability

### Key Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Crisis Detection Recall | 100% | < 99.9% |
| Crisis Detection Precision | > 95% | < 90% |
| Crisis Response Time | < 500ms | > 2s |
| Content Filter Accuracy | > 98% | < 95% |
| Behavioral Guard Precision | > 90% | < 80% |
| Reality Anchor Appropriateness | > 4.5/5 | < 4.0/5 |
| Intervention Helpfulness (user-rated) | > 80% | < 60% |
| Human Review SLA Met | 100% | < 95% |
| Audit Log Integrity | 100% | < 100% |
| False Positive Rate (crisis) | < 0.5% | > 1% |

### Dashboards

- **Crisis Response**: Detection → Response → Resource Delivery → Follow-up
- **Content Safety**: Refusals by category, false positive analysis, user appeals
- **Behavioral Health**: Guard triggers, intervention levels, user outcomes
- **Human Review**: Queue depth, resolution time, decision quality
- **Compliance**: Audit integrity, regulatory metrics, incident trends

---

**Aligned With:** `200-ai-architecture.md`, `220-conversation-engine.md`, `230-memory-engine.md`, `240-relationship-engine.md`, `250-emotion-engine.md`, `270-proactive-engine.md`, `00-foundation/030-core-principles.md` (Principles 4, 5, 6, 7, 9), `06-legal/`
**Next Review:** 2026-01-17