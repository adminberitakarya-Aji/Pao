"""Template Service - Manages identity templates for quick companion creation."""

from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import structlog

from pao_shared.observability import setup_tracing, setup_metrics

from ..models import (
    IdentityConfig, PersonalityConfig, ValuesConfig, VoiceProfile,
    Boundary, Goal, VoiceProfileTemplate, GoalTemplate, BoundaryTemplate,
    CompanionType,
)

logger = structlog.get_logger(__name__)


class TemplateService:
    """Service for managing identity templates."""
    
    def __init__(self, repository=None):
        self.repository = repository
        self._tracer = setup_tracing("identity-engine", "template-service")
        self._meter = setup_metrics("identity-engine", "template-service")
        
        # Metrics
        self._templates_created = self._meter.create_counter(
            "templates_created_total", "Total templates created"
        )
        self._templates_used = self._meter.create_counter(
            "templates_used_total", "Total templates used for identity creation"
        )
        
        # Built-in templates
        self._builtin_templates: Dict[str, Dict[str, Any]] = {}
        self._load_builtin_templates()
    
    def _load_builtin_templates(self):
        """Load built-in identity templates."""
        from ..models import (
            VOICE_TEMPLATES, BOUNDARY_TEMPLATES, GOAL_TEMPLATES,
            PersonalityProfile, PERSONALITY_PROFILES,
            ValuesTemplate, VALUES_TEMPLATES,
        )
        
        # Define complete identity templates
        self._builtin_templates = {
            "supportive_companion": {
                "id": "supportive_companion",
                "name": "Supportive Companion",
                "description": "Warm, empathetic companion for emotional support and wellbeing",
                "category": "wellbeing",
                "companion_type": CompanionType.LEARNING_COMPANION,
                "personality": PERSONALITY_PROFILES.get("supportive"),
                "values": VALUES_TEMPLATES.get("empathetic"),
                "voice": VOICE_TEMPLATES.get("supportive_companion"),
                "boundaries": [
                    BOUNDARY_TEMPLATES.get("safety_pii"),
                    BOUNDARY_TEMPLATES.get("safety_medical"),
                    BOUNDARY_TEMPLATES.get("safety_harmful_content"),
                    BOUNDARY_TEMPLATES.get("privacy_data_retention"),
                ],
                "goals": [
                    GOAL_TEMPLATES.get("user_satisfaction"),
                    GOAL_TEMPLATES.get("emotional_support"),
                    GOAL_TEMPLATES.get("safety_compliance"),
                ],
                "tags": ["supportive", "empathetic", "wellbeing", "safe"],
                "is_active": True,
            },
            "professional_assistant": {
                "id": "professional_assistant",
                "name": "Professional Assistant",
                "description": "Competent, efficient assistant for professional tasks",
                "category": "productivity",
                "companion_type": CompanionType.ASSISTANT,
                "personality": PERSONALITY_PROFILES.get("professional"),
                "values": VALUES_TEMPLATES.get("professional"),
                "voice": VOICE_TEMPLATES.get("professional_assistant"),
                "boundaries": [
                    BOUNDARY_TEMPLATES.get("safety_pii"),
                    BOUNDARY_TEMPLATES.get("safety_legal"),
                    BOUNDARY_TEMPLATES.get("safety_financial"),
                    BOUNDARY_TEMPLATES.get("capability_code_execution"),
                    BOUNDARY_TEMPLATES.get("privacy_data_retention"),
                ],
                "goals": [
                    GOAL_TEMPLATES.get("user_satisfaction"),
                    GOAL_TEMPLATES.get("task_completion"),
                    GOAL_TEMPLATES.get("safety_compliance"),
                ],
                "tags": ["professional", "efficient", "task-oriented", "safe"],
                "is_active": True,
            },
            "creative_partner": {
                "id": "creative_partner",
                "name": "Creative Partner",
                "description": "Imaginative, playful partner for creative collaboration",
                "category": "creative",
                "companion_type": CompanionType.CREATIVE_PARTNER,
                "personality": PERSONALITY_PROFILES.get("creative"),
                "values": VALUES_TEMPLATES.get("creative"),
                "voice": VOICE_TEMPLATES.get("creative_partner"),
                "boundaries": [
                    BOUNDARY_TEMPLATES.get("safety_pii"),
                    BOUNDARY_TEMPLATES.get("safety_harmful_content"),
                    BOUNDARY_TEMPLATES.get("behavioral_tone"),
                ],
                "goals": [
                    GOAL_TEMPLATES.get("creative_collaboration"),
                    GOAL_TEMPLATES.get("user_satisfaction"),
                    GOAL_TEMPLATES.get("engagement"),
                ],
                "tags": ["creative", "playful", "imaginative", "collaborative"],
                "is_active": True,
            },
            "learning_companion": {
                "id": "learning_companion",
                "name": "Learning Companion",
                "description": "Patient, encouraging guide for learning and skill development",
                "category": "education",
                "companion_type": CompanionType.LEARNING_COMPANION,
                "personality": PERSONALITY_PROFILES.get("educational"),
                "values": VALUES_TEMPLATES.get("educational"),
                "voice": VOICE_TEMPLATES.get("learning_companion"),
                "boundaries": [
                    BOUNDARY_TEMPLATES.get("safety_pii"),
                    BOUNDARY_TEMPLATES.get("safety_harmful_content"),
                    BOUNDARY_TEMPLATES.get("privacy_data_retention"),
                ],
                "goals": [
                    GOAL_TEMPLATES.get("learning_progress"),
                    GOAL_TEMPLATES.get("user_satisfaction"),
                    GOAL_TEMPLATES.get("engagement"),
                ],
                "tags": ["educational", "patient", "encouraging", "learning"],
                "is_active": True,
            },
            "research_analyst": {
                "id": "research_analyst",
                "name": "Research Analyst",
                "description": "Analytical, thorough companion for research and analysis tasks",
                "category": "research",
                "companion_type": CompanionType.ASSISTANT,
                "personality": PERSONALITY_PROFILES.get("analytical"),
                "values": VALUES_TEMPLATES.get("analytical"),
                "voice": VOICE_TEMPLATES.get("professional_assistant"),  # Reuse professional voice
                "boundaries": [
                    BOUNDARY_TEMPLATES.get("safety_pii"),
                    BOUNDARY_TEMPLATES.get("safety_legal"),
                    BOUNDARY_TEMPLATES.get("safety_financial"),
                    BOUNDARY_TEMPLATES.get("capability_code_execution"),
                    BOUNDARY_TEMPLATES.get("privacy_data_retention"),
                ],
                "goals": [
                    GOAL_TEMPLATES.get("problem_solving"),
                    GOAL_TEMPLATES.get("knowledge_sharing"),
                    GOAL_TEMPLATES.get("safety_compliance"),
                ],
                "tags": ["analytical", "thorough", "research", "objective"],
                "is_active": True,
            },
        }
    
    async def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a template by ID."""
        # Check built-in first
        if template_id in self._builtin_templates:
            return self._builtin_templates[template_id]
        
        # Check repository for custom templates
        if self.repository:
            return await self.repository.get_template(template_id)
        
        return None
    
    async def list_templates(
        self,
        category: Optional[str] = None,
        companion_type: Optional[CompanionType] = None,
        is_active: bool = True,
    ) -> List[Dict[str, Any]]:
        """List available templates with optional filters."""
        templates = list(self._builtin_templates.values())
        
        # Add custom templates from repository
        if self.repository:
            custom = await self.repository.list_templates(category, companion_type, is_active)
            templates.extend(custom)
        
        # Apply filters
        if category:
            templates = [t for t in templates if t.get("category") == category]
        if companion_type:
            templates = [t for t in templates if t.get("companion_type") == companion_type]
        if is_active is not None:
            templates = [t for t in templates if t.get("is_active", True) == is_active]
        
        return templates
    
    async def create_identity_from_template(
        self,
        template_id: str,
        companion_id: str,
        name: str,
        customizations: Optional[Dict[str, Any]] = None,
        preset: Optional[str] = None,
        created_by: str = "system",
    ) -> IdentityConfig:
        """Create a complete identity configuration from a template."""
        with self._tracer.start_as_current_span("create_identity_from_template") as span:
            span.set_attribute("template_id", template_id)
            span.set_attribute("companion_id", companion_id)
            
            template = await self.get_template(template_id)
            if not template:
                raise ValueError(f"Template not found: {template_id}")
            
            # Build identity from template
            identity = await self._build_identity_from_template(
                template=template,
                companion_id=companion_id,
                name=name,
                customizations=customizations or {},
                preset=preset,
                created_by=created_by,
            )
            
            self._templates_used.add(1, {"template_id": template_id})
            
            logger.info(
                "Identity created from template",
                template_id=template_id,
                companion_id=companion_id,
                identity_id=identity.id,
            )
            
            return identity
    
    async def _build_identity_from_template(
        self,
        template: Dict[str, Any],
        companion_id: str,
        name: str,
        customizations: Dict[str, Any],
        preset: Optional[str],
        created_by: str,
    ) -> IdentityConfig:
        """Build IdentityConfig from template with customizations."""
        now = datetime.utcnow().isoformat()
        identity_id = f"id_{companion_id}_{uuid.uuid4().hex[:8]}"
        
        # Get personality
        personality = template.get("personality")
        if personality and hasattr(personality, 'create_config'):
            personality = personality.create_config(companion_id)
        elif customizations.get("personality"):
            personality = customizations["personality"]
        else:
            from ..models import PersonalityConfig
            personality = PersonalityConfig.create_default(companion_id)
        
        # Get values
        values = template.get("values")
        if values and hasattr(values, 'create_config'):
            values = values.create_config(companion_id)
        elif customizations.get("values"):
            values = customizations["values"]
        else:
            from ..models import ValuesConfig
            values = ValuesConfig.create_default(companion_id)
        
        # Get voice (with preset support)
        voice = template.get("voice")
        if voice and hasattr(voice, 'create_profile'):
            voice = voice.create_profile(
                companion_id=companion_id,
                profile_id=f"voice_{companion_id}_{uuid.uuid4().hex[:8]}",
                customizations=customizations.get("voice", {}),
                preset=preset,
            )
        elif customizations.get("voice"):
            voice = customizations["voice"]
        else:
            from ..models import VoiceProfile
            voice = VoiceProfile.create_default(companion_id)
        
        # Get boundaries
        boundaries = []
        for b in template.get("boundaries", []):
            if b:
                boundaries.append(b)
        boundaries.extend(customizations.get("boundaries", []))
        
        # Get goals
        goals = []
        for g in template.get("goals", []):
            if g and hasattr(g, 'create_goal'):
                goals.append(g.create_goal(
                    companion_id=companion_id,
                    goal_id=f"goal_{companion_id}_{uuid.uuid4().hex[:8]}",
                    parameters=customizations.get("goals", {}).get(g.id, {}),
                ))
            elif g:
                goals.append(g)
        goals.extend(customizations.get("goals", []))
        
        # Apply top-level customizations
        for key, value in customizations.items():
            if key not in ["personality", "values", "voice", "boundaries", "goals"]:
                setattr(identity, key, value) if hasattr(identity, key) else None
        
        return IdentityConfig(
            id=identity_id,
            companion_id=companion_id,
            personality=personality,
            values=values,
            voice=voice,
            boundaries=boundaries,
            goals=goals,
            version=1,
            name=name,
            description=template.get("description", ""),
            status="draft",
            source="template",
            template_id=template_id,
            created_by=created_by,
            tags=template.get("tags", []),
            metadata={
                "template_id": template_id,
                "preset": preset,
                "customizations": list(customizations.keys()),
            },
            created_at=now,
            updated_at=now,
        )
    
    async def save_template(self, template: Dict[str, Any]) -> str:
        """Save a custom template."""
        if not self.repository:
            raise ValueError("Repository not configured")
        
        template_id = template.get("id") or f"tmpl_{uuid.uuid4().hex[:8]}"
        template["id"] = template_id
        template["created_at"] = datetime.utcnow().isoformat()
        template["updated_at"] = datetime.utcnow().isoformat()
        template["is_builtin"] = False
        
        await self.repository.save_template(template)
        
        self._templates_created.add(1, {"category": template.get("category", "custom")})
        
        logger.info("Custom template saved", template_id=template_id)
        return template_id
    
    async def update_template(self, template_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing template."""
        if not self.repository:
            raise ValueError("Repository not configured")
        
        # Can't update built-in templates
        if template_id in self._builtin_templates:
            raise ValueError("Cannot modify built-in templates")
        
        template = await self.repository.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        template.update(updates)
        template["updated_at"] = datetime.utcnow().isoformat()
        
        await self.repository.save_template(template)
        
        logger.info("Template updated", template_id=template_id)
        return template
    
    async def delete_template(self, template_id: str) -> bool:
        """Delete a custom template."""
        if not self.repository:
            raise ValueError("Repository not configured")
        
        # Can't delete built-in templates
        if template_id in self._builtin_templates:
            raise ValueError("Cannot delete built-in templates")
        
        return await self.repository.delete_template(template_id)
    
    async def get_categories(self) -> List[str]:
        """Get all template categories."""
        categories = set()
        for t in self._builtin_templates.values():
            categories.add(t.get("category", "general"))
        
        if self.repository:
            custom_categories = await self.repository.get_template_categories()
            categories.update(custom_categories)
        
        return sorted(list(categories))
    
    async def create_template_from_identity(
        self,
        identity: IdentityConfig,
        template_id: str,
        name: str,
        description: str,
        category: str,
        created_by: str = "system",
    ) -> Dict[str, Any]:
        """Create a template from an existing identity."""
        template = {
            "id": template_id,
            "name": name,
            "description": description,
            "category": category,
            "companion_type": identity.personality.companion_type,
            "personality": identity.personality,
            "values": identity.values,
            "voice": identity.voice,
            "boundaries": identity.boundaries,
            "goals": identity.goals,
            "tags": identity.tags,
            "is_builtin": False,
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "created_by": created_by,
        }
        
        return await self.save_template(template)


# Import needed at module level
from ..models import (
    PersonalityProfile, PERSONALITY_PROFILES,
    ValuesTemplate, VALUES_TEMPLATES,
)

# Built-in personality profiles
PERSONALITY_PROFILES = {
    "supportive": PersonalityProfile(
        id="supportive",
        name="Supportive",
        companion_type=CompanionType.LEARNING_COMPANION,
        traits={
            "openness": 0.5,
            "conscientiousness": 0.6,
            "extraversion": 0.4,
            "agreeableness": 0.85,
            "neuroticism": 0.2,
            "playfulness": 0.3,
            "assertiveness": 0.3,
            "empathy": 0.9,
            "curiosity": 0.5,
            "patience": 0.85,
        },
    ),
    "professional": PersonalityProfile(
        id="professional",
        name="Professional",
        companion_type=CompanionType.ASSISTANT,
        traits={
            "openness": 0.5,
            "conscientiousness": 0.85,
            "extraversion": 0.4,
            "agreeableness": 0.65,
            "neuroticism": 0.15,
            "playfulness": 0.15,
            "assertiveness": 0.55,
            "empathy": 0.5,
            "curiosity": 0.55,
            "patience": 0.6,
        },
    ),
    "creative": PersonalityProfile(
        id="creative",
        name="Creative",
        companion_type=CompanionType.CREATIVE_PARTNER,
        traits={
            "openness": 0.9,
            "conscientiousness": 0.5,
            "extraversion": 0.65,
            "agreeableness": 0.7,
            "neuroticism": 0.35,
            "playfulness": 0.8,
            "assertiveness": 0.5,
            "empathy": 0.65,
            "curiosity": 0.85,
            "patience": 0.4,
        },
    ),
    "educational": PersonalityProfile(
        id="educational",
        name="Educational",
        companion_type=CompanionType.LEARNING_COMPANION,
        traits={
            "openness": 0.7,
            "conscientiousness": 0.75,
            "extraversion": 0.5,
            "agreeableness": 0.8,
            "neuroticism": 0.2,
            "playfulness": 0.4,
            "assertiveness": 0.4,
            "empathy": 0.75,
            "curiosity": 0.8,
            "patience": 0.9,
        },
    ),
    "analytical": PersonalityProfile(
        id="analytical",
        name="Analytical",
        companion_type=CompanionType.ASSISTANT,
        traits={
            "openness": 0.75,
            "conscientiousness": 0.85,
            "extraversion": 0.35,
            "agreeableness": 0.55,
            "neuroticism": 0.25,
            "playfulness": 0.2,
            "assertiveness": 0.5,
            "empathy": 0.45,
            "curiosity": 0.8,
            "patience": 0.65,
        },
    ),
}

# Built-in values templates
VALUES_TEMPLATES = {
    "empathetic": ValuesTemplate(
        id="empathetic",
        name="Empathetic Values",
        category="wellbeing",
        values=[
            {"name": "Compassion", "priority": "critical", "weight": 1.0},
            {"name": "Empathy", "priority": "high", "weight": 0.95},
            {"name": "Kindness", "priority": "high", "weight": 0.9},
            {"name": "Respect", "priority": "high", "weight": 0.85},
            {"name": "Patience", "priority": "medium", "weight": 0.8},
            {"name": "Non-judgment", "priority": "high", "weight": 0.9},
        ],
    ),
    "professional": ValuesTemplate(
        id="professional",
        name="Professional Values",
        category="productivity",
        values=[
            {"name": "Competence", "priority": "critical", "weight": 1.0},
            {"name": "Reliability", "priority": "critical", "weight": 0.95},
            {"name": "Efficiency", "priority": "high", "weight": 0.9},
            {"name": "Accuracy", "priority": "high", "weight": 0.95},
            {"name": "Professionalism", "priority": "high", "weight": 0.85},
            {"name": "Discretion", "priority": "high", "weight": 0.9},
        ],
    ),
    "creative": ValuesTemplate(
        id="creative",
        name="Creative Values",
        category="creative",
        values=[
            {"name": "Creativity", "priority": "critical", "weight": 1.0},
            {"name": "Originality", "priority": "high", "weight": 0.9},
            {"name": "Exploration", "priority": "high", "weight": 0.85},
            {"name": "Playfulness", "priority": "medium", "weight": 0.8},
            {"name": "Collaboration", "priority": "high", "weight": 0.85},
            {"name": "Growth", "priority": "medium", "weight": 0.75},
        ],
    ),
    "educational": ValuesTemplate(
        id="educational",
        name="Educational Values",
        category="education",
        values=[
            {"name": "Learning", "priority": "critical", "weight": 1.0},
            {"name": "Growth", "priority": "critical", "weight": 0.95},
            {"name": "Clarity", "priority": "high", "weight": 0.9},
            {"name": "Encouragement", "priority": "high", "weight": 0.9},
            {"name": "Accuracy", "priority": "high", "weight": 0.85},
            {"name": "Adaptability", "priority": "medium", "weight": 0.8},
        ],
    ),
    "analytical": ValuesTemplate(
        id="analytical",
        name="Analytical Values",
        category="research",
        values=[
            {"name": "Accuracy", "priority": "critical", "weight": 1.0},
            {"name": "Objectivity", "priority": "critical", "weight": 0.95},
            {"name": "Thoroughness", "priority": "high", "weight": 0.9},
            {"name": "Evidence-based", "priority": "high", "weight": 0.95},
            {"name": "Intellectual Honesty", "priority": "high", "weight": 0.9},
            {"name": "Clarity", "priority": "medium", "weight": 0.85},
        ],
    ),
}