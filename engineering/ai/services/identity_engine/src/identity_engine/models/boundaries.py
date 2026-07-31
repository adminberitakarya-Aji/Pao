"""Boundary models for Identity Engine - defines limits and guardrails for companion behavior."""

from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class BoundaryScope(str, Enum):
    """Scope of boundary application."""
    GLOBAL = "global"                    # Applies to all interactions
    CONTEXT = "context"                  # Applies in specific contexts
    USER = "user"                        # Applies to specific users
    SESSION = "session"                  # Applies within a session
    TOPIC = "topic"                      # Applies to specific topics
    CAPABILITY = "capability"            # Applies to specific capabilities
    TIME = "time"                        # Time-based boundaries


class BoundaryTriggerType(str, Enum):
    """Types of boundary triggers."""
    KEYWORD = "keyword"                  # Triggered by specific words/phrases
    PATTERN = "pattern"                  # Triggered by regex pattern
    SEMANTIC = "semantic"                # Triggered by semantic similarity
    INTENT = "intent"                    # Triggered by detected intent
    SENTIMENT = "sentiment"              # Triggered by sentiment threshold
    TOPIC = "topic"                      # Triggered by topic classification
    CAPABILITY = "capability"            # Triggered by capability request
    FREQUENCY = "frequency"              # Triggered by frequency of occurrence
    ESCALATION = "escalation"            # Triggered by escalation signals
    CUSTOM = "custom"                    # Custom trigger logic


class BoundaryActionType(str, Enum):
    """Types of boundary actions."""
    REFUSE = "refuse"                    # Refuse to engage
    REDIRECT = "redirect"                # Redirect to safe topic
    ESCALATE = "escalate"                # Escalate to human/higher authority
    WARN = "warn"                        # Issue warning to user
    MODIFY = "modify"                    # Modify response (filter/transform)
    LIMIT = "limit"                      # Limit scope/depth of response
    REQUIRE_CONSENT = "require_consent"  # Require explicit user consent
    LOG = "log"                          # Log for review
    TRANSFER = "transfer"                # Transfer to different companion/mode
    CUSTOM = "custom"                    # Custom action


class BoundaryTrigger(BaseModel):
    """Trigger condition for a boundary."""
    id: str = Field(..., description="Unique trigger ID")
    type: BoundaryTriggerType = Field(..., description="Trigger type")
    name: str = Field(..., description="Human-readable trigger name")
    description: str = Field(default="", description="Trigger description")
    
    # Configuration per trigger type
    keywords: List[str] = Field(default_factory=list, description="Keywords for KEYWORD trigger")
    pattern: Optional[str] = Field(default=None, description="Regex pattern for PATTERN trigger")
    semantic_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Similarity threshold for SEMANTIC trigger")
    intent_names: List[str] = Field(default_factory=list, description="Intent names for INTENT trigger")
    sentiment_threshold: Optional[float] = Field(default=None, ge=-1.0, le=1.0, description="Sentiment threshold for SENTIMENT trigger")
    topic_ids: List[str] = Field(default_factory=list, description="Topic IDs for TOPIC trigger")
    capability_ids: List[str] = Field(default_factory=list, description="Capability IDs for CAPABILITY trigger")
    frequency_count: Optional[int] = Field(default=None, gt=0, description="Count for FREQUENCY trigger")
    frequency_window_seconds: Optional[int] = Field(default=None, gt=0, description="Time window for FREQUENCY trigger")
    escalation_signals: List[str] = Field(default_factory=list, description="Signals for ESCALATION trigger")
    custom_logic: Optional[str] = Field(default=None, description="Custom trigger logic (expression)")
    
    # Metadata
    is_active: bool = Field(default=True)
    priority: int = Field(default=0, description="Trigger priority (higher = evaluated first)")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def matches(self, context: Dict[str, Any]) -> bool:
        """Check if trigger matches given context."""
        # This would be implemented with actual matching logic
        # For now, return False as placeholder
        return False


class BoundaryAction(BaseModel):
    """Action to take when boundary is triggered."""
    id: str = Field(..., description="Unique action ID")
    type: BoundaryActionType = Field(..., description="Action type")
    name: str = Field(..., description="Human-readable action name")
    description: str = Field(default="", description="Action description")
    
    # Configuration per action type
    refusal_message: Optional[str] = Field(default=None, description="Message for REFUSE action")
    redirect_topic: Optional[str] = Field(default=None, description="Topic for REDIRECT action")
    redirect_message: Optional[str] = Field(default=None, description="Message for REDIRECT action")
    escalation_target: Optional[str] = Field(default=None, description="Target for ESCALATE action")
    escalation_message: Optional[str] = Field(default=None, description="Message for ESCALATE action")
    warning_message: Optional[str] = Field(default=None, description="Message for WARN action")
    modification_rules: List[Dict[str, Any]] = Field(default_factory=list, description="Rules for MODIFY action")
    limit_config: Dict[str, Any] = Field(default_factory=dict, description="Config for LIMIT action")
    consent_message: Optional[str] = Field(default=None, description="Message for REQUIRE_CONSENT action")
    log_level: Literal["info", "warning", "critical"] = Field(default="warning", description="Log level for LOG action")
    transfer_target: Optional[str] = Field(default=None, description="Target for TRANSFER action")
    transfer_message: Optional[str] = Field(default=None, description="Message for TRANSFER action")
    custom_logic: Optional[str] = Field(default=None, description="Custom action logic")
    
    # Metadata
    is_active: bool = Field(default=True)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Boundary(BaseModel):
    """A behavioral boundary for a companion."""
    id: str = Field(..., description="Unique boundary ID")
    companion_id: str = Field(..., description="Companion identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Boundary name")
    description: str = Field(default="", description="Boundary description")
    scope: BoundaryScope = Field(default=BoundaryScope.GLOBAL, description="Boundary scope")
    
    # Scope-specific configuration
    context_conditions: Dict[str, Any] = Field(default_factory=dict, description="Conditions for CONTEXT scope")
    user_ids: List[str] = Field(default_factory=list, description="User IDs for USER scope")
    session_types: List[str] = Field(default_factory=list, description="Session types for SESSION scope")
    topic_ids: List[str] = Field(default_factory=list, description="Topic IDs for TOPIC scope")
    capability_ids: List[str] = Field(default_factory=list, description="Capability IDs for CAPABILITY scope")
    time_windows: List[Dict[str, Any]] = Field(default_factory=list, description="Time windows for TIME scope")
    
    # Triggers and actions
    triggers: List[BoundaryTrigger] = Field(default_factory=list, description="Boundary triggers")
    actions: List[BoundaryAction] = Field(default_factory=list, description="Actions to take when triggered")
    
    # Logic
    trigger_logic: Literal["any", "all", "custom"] = Field(default="any", description="How triggers combine")
    custom_trigger_logic: Optional[str] = Field(default=None, description="Custom trigger combination logic")
    action_sequence: Literal["sequential", "parallel", "first_match"] = Field(default="sequential", description="How actions execute")
    
    # Priority and precedence
    priority: int = Field(default=0, description="Boundary priority (higher = evaluated first)")
    overrides: List[str] = Field(default_factory=list, description="Boundary IDs this overrides")
    overridden_by: List[str] = Field(default_factory=list, description="Boundary IDs that override this")
    
    # Metadata
    version: int = Field(default=1, ge=1)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    created_by: str = Field(default="system")
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Validation
    is_active: bool = Field(default=True)
    is_validated: bool = Field(default=False)
    validation_notes: Optional[str] = Field(default=None)
    
    def get_active_triggers(self) -> List[BoundaryTrigger]:
        """Get all active triggers."""
        return [t for t in self.triggers if t.is_active]
    
    def get_active_actions(self) -> List[BoundaryAction]:
        """Get all active actions."""
        return [a for a in self.actions if a.is_active]
    
    def evaluate(self, context: Dict[str, Any]) -> List[BoundaryAction]:
        """Evaluate boundary against context, return actions to execute."""
        active_triggers = self.get_active_triggers()
        if not active_triggers:
            return []
        
        matched = False
        if self.trigger_logic == "any":
            matched = any(t.matches(context) for t in active_triggers)
        elif self.trigger_logic == "all":
            matched = all(t.matches(context) for t in active_triggers)
        # custom logic would be evaluated here
        
        if matched:
            return self.get_active_actions()
        return []


# Predefined boundary templates
BOUNDARY_TEMPLATES = {
    "safety_pii": Boundary(
        id="safety_pii",
        companion_id="",
        name="PII Protection",
        description="Prevents sharing or requesting personally identifiable information",
        scope=BoundaryScope.GLOBAL,
        triggers=[
            BoundaryTrigger(
                id="pii_request",
                type=BoundaryTriggerType.PATTERN,
                name="PII Request Detection",
                pattern=r"(ssn|social security|credit card|passport|driver's license|address|phone number|email).*\?|what is (my|your|their) (ssn|address|phone)",
            ),
            BoundaryTrigger(
                id="pii_sharing",
                type=BoundaryTriggerType.PATTERN,
                name="PII Sharing Detection",
                pattern=r"\b\d{3}-\d{2}-\d{4}\b|\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
            ),
        ],
        actions=[
            BoundaryAction(
                id="refuse_pii",
                type=BoundaryActionType.REFUSE,
                name="Refuse PII Request",
                refusal_message="I can't help with requests involving personal identification information. Is there something else I can assist you with?",
            ),
            BoundaryAction(
                id="log_pii",
                type=BoundaryActionType.LOG,
                name="Log PII Attempt",
                log_level="warning",
            ),
        ],
        priority=100,
        tags=["safety", "privacy", "pii"],
    ),
    
    "safety_medical": Boundary(
        id="safety_medical",
        companion_id="",
        name="Medical Advice Restriction",
        description="Prevents giving medical advice or diagnoses",
        scope=BoundaryScope.TOPIC,
        topic_ids=["medical", "health", "diagnosis", "treatment", "medication"],
        triggers=[
            BoundaryTrigger(
                id="medical_advice_request",
                type=BoundaryTriggerType.INTENT,
                name="Medical Advice Request",
                intent_names=["medical_advice", "diagnosis_request", "treatment_request", "medication_advice"],
            ),
            BoundaryTrigger(
                id="symptom_check",
                type=BoundaryTriggerType.KEYWORD,
                name="Symptom Check Request",
                keywords=["symptoms", "diagnose", "what's wrong with me", "am i sick", "should i take"],
            ),
        ],
        actions=[
            BoundaryAction(
                id="refuse_medical",
                type=BoundaryActionType.REFUSE,
                name="Refuse Medical Advice",
                refusal_message="I'm not qualified to provide medical advice or diagnoses. Please consult a healthcare professional for medical concerns.",
            ),
            BoundaryAction(
                id="redirect_medical",
                type=BoundaryActionType.REDIRECT,
                name="Redirect to General Health Info",
                redirect_topic="general_health_information",
                redirect_message="I can share general health information or help you find reliable medical resources. Would that be helpful?",
            ),
        ],
        priority=95,
        tags=["safety", "medical", "health"],
    ),
    
    "safety_legal": Boundary(
        id="safety_legal",
        companion_id="",
        name="Legal Advice Restriction",
        description="Prevents giving legal advice",
        scope=BoundaryScope.TOPIC,
        topic_ids=["legal", "law", "contract", "lawsuit", "rights", "compliance"],
        triggers=[
            BoundaryTrigger(
                id="legal_advice_request",
                type=BoundaryTriggerType.INTENT,
                name="Legal Advice Request",
                intent_names=["legal_advice", "contract_review", "legal_interpretation", "rights_inquiry"],
            ),
        ],
        actions=[
            BoundaryAction(
                id="refuse_legal",
                type=BoundaryActionType.REFUSE,
                name="Refuse Legal Advice",
                refusal_message="I cannot provide legal advice. For legal matters, please consult a qualified attorney.",
            ),
            BoundaryAction(
                id="redirect_legal",
                type=BoundaryActionType.REDIRECT,
                name="Redirect to Legal Resources",
                redirect_topic="legal_resources",
                redirect_message="I can help you find general legal resources or explain legal concepts. Would that be useful?",
            ),
        ],
        priority=95,
        tags=["safety", "legal"],
    ),
    
    "safety_financial": Boundary(
        id="safety_financial",
        companion_id="",
        name="Financial Advice Restriction",
        description="Prevents giving personalized financial advice",
        scope=BoundaryScope.TOPIC,
        topic_ids=["investment", "trading", "tax", "retirement_planning", "financial_planning"],
        triggers=[
            BoundaryTrigger(
                id="financial_advice_request",
                type=BoundaryTriggerType.INTENT,
                name="Financial Advice Request",
                intent_names=["investment_advice", "tax_advice", "retirement_planning", "financial_planning"],
            ),
        ],
        actions=[
            BoundaryAction(
                id="refuse_financial",
                type=BoundaryActionType.REFUSE,
                name="Refuse Financial Advice",
                refusal_message="I cannot provide personalized financial advice. Please consult a qualified financial advisor.",
            ),
            BoundaryAction(
                id="require_consent_financial",
                type=BoundaryActionType.REQUIRE_CONSENT,
                name="Require Consent for Financial Discussion",
                consent_message="I can share general financial education. Do you want me to provide general information instead?",
            ),
        ],
        priority=90,
        tags=["safety", "financial"],
    ),
    
    "safety_harmful_content": Boundary(
        id="safety_harmful_content",
        companion_id="",
        name="Harmful Content Prevention",
        description="Prevents generation of harmful, illegal, or unethical content",
        scope=BoundaryScope.GLOBAL,
        triggers=[
            BoundaryTrigger(
                id="violence_promotion",
                type=BoundaryTriggerType.SEMANTIC,
                name="Violence Promotion",
                semantic_threshold=0.8,
            ),
            BoundaryTrigger(
                id="self_harm",
                type=BoundaryTriggerType.KEYWORD,
                name="Self-Harm Indicators",
                keywords=["suicide", "kill myself", "end my life", "self-harm", "hurt myself"],
            ),
            BoundaryTrigger(
                id="illegal_acts",
                type=BoundaryTriggerType.INTENT,
                name="Illegal Act Requests",
                intent_names=["illegal_instructions", "harmful_activities", "weapon_making", "drug_manufacturing"],
            ),
            BoundaryTrigger(
                id="hate_speech",
                type=BoundaryTriggerType.SEMANTIC,
                name="Hate Speech",
                semantic_threshold=0.75,
            ),
        ],
        actions=[
            BoundaryAction(
                id="refuse_harmful",
                type=BoundaryActionType.REFUSE,
                name="Refuse Harmful Content",
                refusal_message="I can't help with that request. I'm designed to be helpful and harmless.",
            ),
            BoundaryAction(
                id="escalate_self_harm",
                type=BoundaryActionType.ESCALATE,
                name="Escalate Self-Harm",
                escalation_target="crisis_support",
                escalation_message="I'm concerned about what you're going through. Please reach out to a crisis helpline immediately.",
            ),
            BoundaryAction(
                id="log_harmful",
                type=BoundaryActionType.LOG,
                name="Log Harmful Content Attempt",
                log_level="critical",
            ),
        ],
        priority=100,
        tags=["safety", "harmful_content", "crisis"],
    ),
    
    "capability_code_execution": Boundary(
        id="capability_code_execution",
        companion_id="",
        name="Code Execution Limitation",
        description="Limits code execution capabilities for safety",
        scope=BoundaryScope.CAPABILITY,
        capability_ids=["code_execution", "shell_access", "file_system", "network_requests"],
        triggers=[
            BoundaryTrigger(
                id="dangerous_code",
                type=BoundaryTriggerType.PATTERN,
                name="Dangerous Code Patterns",
                pattern=r"(rm -rf|format|delete|drop table|exec\(|eval\(|system\(|subprocess|os\.system)",
            ),
            BoundaryTrigger(
                id="network_access",
                type=BoundaryTriggerType.CAPABILITY,
                name="Network Access Request",
                capability_ids=["network_requests", "http_requests", "api_calls"],
            ),
        ],
        actions=[
            BoundaryAction(
                id="limit_execution",
                type=BoundaryActionType.LIMIT,
                name="Limit Code Execution",
                limit_config={"allow_network": False, "allow_file_write": False, "timeout_seconds": 30, "memory_limit_mb": 100},
            ),
            BoundaryAction(
                id="warn_code",
                type=BoundaryActionType.WARN,
                name="Warn About Code Limitations",
                warning_message="Code execution is limited for safety. Some operations may not be available.",
            ),
        ],
        priority=80,
        tags=["capability", "code", "safety"],
    ),
    
    "behavioral_tone": Boundary(
        id="behavioral_tone",
        companion_id="",
        name="Tone Consistency",
        description="Maintains consistent tone and prevents inappropriate tone shifts",
        scope=BoundaryScope.GLOBAL,
        triggers=[
            BoundaryTrigger(
                id="tone_shift",
                type=BoundaryTriggerType.SENTIMENT,
                name="Sudden Tone Shift",
                sentiment_threshold=-0.5,  # Sudden negative shift
            ),
            BoundaryTrigger(
                id="inappropriate_formality",
                type=BoundaryTriggerType.CUSTOM,
                name="Inappropriate Formality",
                custom_logic="formality_mismatch > 0.7",
            ),
        ],
        actions=[
            BoundaryAction(
                id="modify_tone",
                type=BoundaryActionType.MODIFY,
                name="Adjust Tone",
                modification_rules=[
                    {"type": "tone_adjustment", "target": "consistent", "strength": 0.8}
                ],
            ),
        ],
        priority=50,
        tags=["behavioral", "tone", "consistency"],
    ),
    
    "privacy_data_retention": Boundary(
        id="privacy_data_retention",
        companion_id="",
        name="Data Retention Limit",
        description="Enforces data retention and privacy boundaries",
        scope=BoundaryScope.GLOBAL,
        triggers=[
            BoundaryTrigger(
                id="data_request",
                type=BoundaryTriggerType.INTENT,
                name="Personal Data Request",
                intent_names=["data_export", "data_deletion", "privacy_request", "gdpr_request"],
            ),
            BoundaryTrigger(
                id="memory_query",
                type=BoundaryTriggerType.KEYWORD,
                name="Memory/History Query",
                keywords=["what do you know about me", "my history", "previous conversations", "remember when"],
            ),
        ],
        actions=[
            BoundaryAction(
                id="redirect_privacy",
                type=BoundaryActionType.REDIRECT,
                name="Redirect to Privacy Controls",
                redirect_topic="privacy_settings",
                redirect_message="You can manage your data and privacy settings in your account. Would you like help with that?",
            ),
            BoundaryAction(
                id="limit_memory",
                type=BoundaryActionType.LIMIT,
                name="Limit Memory Disclosure",
                limit_config={"max_history_items": 5, "anonymize": True},
            ),
        ],
        priority=70,
        tags=["privacy", "data_retention", "gdpr"],
    ),
}