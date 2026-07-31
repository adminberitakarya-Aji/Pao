"""Unit tests for Template Service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from identity_engine.services.template_service import TemplateService
from identity_engine.models.personality import PersonalityConfig, PersonalityTraits, CompanionType
from identity_engine.models.values import ValuesConfig, Value, ValueCategory, ValuePriority
from identity_engine.models.voice import VoiceProfile, FormalityLevel, EmotionalTone, CommunicationStyle
from identity_engine.models.boundaries import Boundary, BoundaryTrigger, BoundaryAction, BoundaryScope, BoundaryTriggerType, BoundaryActionType
from identity_engine.models.goals import Goal, GoalType, GoalStatus, Metric, MetricType
from identity_engine.models.identity import IdentityConfig, IdentityStatus, IdentitySource


class TestTemplateService:
    """Test TemplateService."""

    @pytest.fixture
    def template_service(self):
        return TemplateService()

    def test_builtin_templates_exist(self, template_service):
        """Test that all built-in templates are loaded."""
        templates = template_service._builtin_templates
        assert "supportive_companion" in templates
        assert "professional_assistant" in templates
        assert "creative_partner" in templates
        assert "learning_companion" in templates
        assert "research_analyst" in templates

    def test_supportive_companion_template(self, template_service):
        """Test supportive companion template structure."""
        template = template_service._builtin_templates["supportive_companion"]
        assert template["id"] == "supportive_companion"
        assert template["name"] == "Supportive Companion"
        assert template["category"] == "wellbeing"
        assert template["companion_type"] == CompanionType.LEARNING_COMPANION
        assert template["personality"] is not None
        assert template["values"] is not None
        assert template["voice"] is not None
        assert len(template["boundaries"]) == 4
        assert len(template["goals"]) == 3
        assert "supportive" in template["tags"]
        assert template["is_active"] is True

    def test_professional_assistant_template(self, template_service):
        """Test professional assistant template structure."""
        template = template_service._builtin_templates["professional_assistant"]
        assert template["category"] == "productivity"
        assert template["companion_type"] == CompanionType.ASSISTANT
        assert len(template["boundaries"]) == 5
        assert len(template["goals"]) == 3

    def test_creative_partner_template(self, template_service):
        """Test creative partner template structure."""
        template = template_service._builtin_templates["creative_partner"]
        assert template["category"] == "creative"
        assert template["companion_type"] == CompanionType.CREATIVE_PARTNER
        assert len(template["boundaries"]) == 3
        assert len(template["goals"]) == 3

    def test_learning_companion_template(self, template_service):
        """Test learning companion template structure."""
        template = template_service._builtin_templates["learning_companion"]
        assert template["category"] == "education"
        assert template["companion_type"] == CompanionType.LEARNING_COMPANION
        assert len(template["boundaries"]) == 3
        assert len(template["goals"]) == 3

    def test_research_analyst_template(self, template_service):
        """Test research analyst template structure."""
        template = template_service._builtin_templates["research_analyst"]
        assert template["category"] == "research"
        assert template["companion_type"] == CompanionType.ASSISTANT
        assert len(template["boundaries"]) == 5
        assert len(template["goals"]) == 3

    @pytest.mark.asyncio
    async def test_get_template_builtin(self, template_service):
        """Test getting built-in template."""
        template = await template_service.get_template("supportive_companion")
        assert template is not None
        assert template["id"] == "supportive_companion"

    @pytest.mark.asyncio
    async def test_get_template_nonexistent(self, template_service):
        """Test getting non-existent template."""
        template = await template_service.get_template("nonexistent")
        assert template is None

    @pytest.mark.asyncio
    async def test_get_template_from_repo(self, template_service):
        """Test getting template from repository."""
        mock_repo = AsyncMock()
        mock_repo.get_template.return_value = {"id": "custom_1", "name": "Custom"}
        template_service.repository = mock_repo

        template = await template_service.get_template("custom_1")
        assert template is not None
        assert template["id"] == "custom_1"
        mock_repo.get_template.assert_called_once_with("custom_1")

    @pytest.mark.asyncio
    async def test_list_templates(self, template_service):
        """Test listing templates."""
        templates = await template_service.list_templates()
        assert len(templates) == 5  # 5 built-in templates

    @pytest.mark.asyncio
    async def test_list_templates_by_category(self, template_service):
        """Test listing templates by category."""
        templates = await template_service.list_templates(category="wellbeing")
        assert len(templates) == 1
        assert templates[0]["category"] == "wellbeing"

    @pytest.mark.asyncio
    async def test_list_templates_by_companion_type(self, template_service):
        """Test listing templates by companion type."""
        templates = await template_service.list_templates(companion_type=CompanionType.ASSISTANT)
        assert len(templates) == 2  # professional_assistant, research_analyst

    @pytest.mark.asyncio
    async def test_list_templates_with_repo(self, template_service):
        """Test listing templates including custom ones from repo."""
        mock_repo = AsyncMock()
        mock_repo.list_templates.return_value = [
            {"id": "custom_1", "name": "Custom 1", "category": "custom"},
            {"id": "custom_2", "name": "Custom 2", "category": "custom"},
        ]
        template_service.repository = mock_repo

        templates = await template_service.list_templates()
        assert len(templates) == 7  # 5 built-in + 2 custom

    @pytest.mark.asyncio
    async def test_create_identity_from_template(self, template_service):
        """Test creating identity from template."""
        identity = await template_service.create_identity_from_template(
            template_id="supportive_companion",
            companion_id="comp_123",
            name="My Companion",
        )
        assert isinstance(identity, IdentityConfig)
        assert identity.companion_id == "comp_123"
        assert identity.name == "My Companion"
        assert identity.personality is not None
        assert identity.values is not None
        assert identity.voice is not None
        assert len(identity.boundaries) == 4
        assert len(identity.goals) == 3
        assert identity.status == IdentityStatus.DRAFT
        assert identity.source == IdentitySource.TEMPLATE
        assert identity.template_id == "supportive_companion"

    @pytest.mark.asyncio
    async def test_create_identity_with_customizations(self, template_service):
        """Test creating identity with customizations."""
        identity = await template_service.create_identity_from_template(
            template_id="supportive_companion",
            companion_id="comp_123",
            name="Custom Companion",
            customizations={"tags": ["custom", "test"]},
        )
        assert "custom" in identity.tags
        assert "test" in identity.tags

    @pytest.mark.asyncio
    async def test_create_identity_invalid_template(self, template_service):
        """Test creating identity with invalid template raises error."""
        with pytest.raises(ValueError, match="Template not found"):
            await template_service.create_identity_from_template(
                template_id="invalid_template",
                companion_id="comp_123",
                name="Test",
            )

    @pytest.mark.asyncio
    async def test_get_categories(self, template_service):
        """Test getting template categories."""
        categories = await template_service.get_categories()
        assert "wellbeing" in categories
        assert "productivity" in categories
        assert "creative" in categories
        assert "education" in categories
        assert "research" in categories

    @pytest.mark.asyncio
    async def test_get_categories_with_repo(self, template_service):
        """Test getting categories including custom from repo."""
        mock_repo = AsyncMock()
        mock_repo.get_template_categories.return_value = ["custom_category"]
        template_service.repository = mock_repo

        categories = await template_service.get_categories()
        assert "custom_category" in categories

    @pytest.mark.asyncio
    async def test_save_template(self, template_service):
        """Test saving custom template."""
        mock_repo = AsyncMock()
        template_service.repository = mock_repo

        template_data = {
            "name": "Custom Template",
            "description": "A custom template",
            "category": "custom",
            "companion_type": CompanionType.COMPANION,
            "personality": {},
            "values": {},
            "voice": {},
            "boundaries": [],
            "goals": [],
            "tags": ["custom"],
            "is_active": True,
            "created_by": "user_123",
        }

        template_id = await template_service.save_template(template_data)
        assert template_id is not None
        assert template_id.startswith("tmpl_")
        mock_repo.save_template.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_template_no_repo(self, template_service):
        """Test saving template without repository raises error."""
        with pytest.raises(ValueError, match="Repository not configured"):
            await template_service.save_template({"name": "Test"})

    @pytest.mark.asyncio
    async def test_update_template(self, template_service):
        """Test updating custom template."""
        mock_repo = AsyncMock()
        mock_repo.get_template.return_value = {
            "id": "custom_1", "name": "Original", "category": "custom", "is_builtin": False
        }
        template_service.repository = mock_repo

        result = await template_service.update_template("custom_1", {"name": "Updated"})
        assert result["name"] == "Updated"
        mock_repo.save_template.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_builtin_template_raises(self, template_service):
        """Test updating built-in template raises error."""
        with pytest.raises(ValueError, match="Cannot modify built-in templates"):
            await template_service.update_template("supportive_companion", {"name": "Hacked"})

    @pytest.mark.asyncio
    async def test_update_nonexistent_template_raises(self, template_service):
        """Test updating non-existent template raises error."""
        mock_repo = AsyncMock()
        mock_repo.get_template.return_value = None
        template_service.repository = mock_repo

        with pytest.raises(ValueError, match="Template not found"):
            await template_service.update_template("nonexistent", {"name": "Test"})

    @pytest.mark.asyncio
    async def test_delete_template(self, template_service):
        """Test deleting custom template."""
        mock_repo = AsyncMock()
        mock_repo.delete_template.return_value = True
        template_service.repository = mock_repo

        result = await template_service.delete_template("custom_1")
        assert result is True
        mock_repo.delete_template.assert_called_once_with("custom_1")

    @pytest.mark.asyncio
    async def test_delete_builtin_template_raises(self, template_service):
        """Test deleting built-in template raises error."""
        with pytest.raises(ValueError, match="Cannot delete built-in templates"):
            await template_service.delete_template("supportive_companion")

    @pytest.mark.asyncio
    async def test_create_template_from_identity(self, template_service):
        """Test creating template from existing identity."""
        mock_repo = AsyncMock()
        template_service.repository = mock_repo

        # Create minimal identity
        personality = PersonalityConfig(
            companion_id="comp_123", name="Test",
            traits=PersonalityTraits(openness=0.5, conscientiousness=0.5, extraversion=0.5, agreeableness=0.5, neuroticism=0.5),
            created_at="2024-01-01T00:00:00", updated_at="2024-01-01T00:00:00",
        )
        values = ValuesConfig(companion_id="comp_123", hierarchy={}, created_at="2024-01-01T00:00:00", updated_at="2024-01-01T00:00:00")
        voice = VoiceProfile(companion_id="comp_123", name="Test", formality=FormalityLevel.NEUTRAL, primary_tone=EmotionalTone.NEUTRAL, communication_style=CommunicationStyle.CONVERSATIONAL, created_at="2024-01-01T00:00:00", updated_at="2024-01-01T00:00:00")
        
        identity = IdentityConfig(
            id="id_1", companion_id="comp_123",
            personality=personality, values=values, voice=voice,
            boundaries=[], goals=[],
            name="Test Identity",
        )

        result = await template_service.create_template_from_identity(
            identity=identity,
            template_id="from_identity_1",
            name="From Identity",
            description="Created from identity",
            category="custom",
        )
        assert result["id"] == "from_identity_1"
        assert result["name"] == "From Identity"
        mock_repo.save_template.assert_called_once()
