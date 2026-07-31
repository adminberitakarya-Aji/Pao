"""Unit tests for Identity Service."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from identity_engine.services.identity_service import IdentityService
from identity_engine.models import (
    IdentityConfig, IdentityRequest, IdentityResponse, IdentityVersion,
    IdentityStatus, IdentitySource, PersonalityConfig, PersonalityTraits, CompanionType,
    ValuesConfig, Value, ValueCategory, ValuePriority,
    VoiceProfile, FormalityLevel, EmotionalTone, CommunicationStyle,
    Boundary, BoundaryTrigger, BoundaryAction, BoundaryScope, BoundaryTriggerType, BoundaryActionType,
    Goal, GoalType, GoalStatus, Metric, MetricType,
)


class TestIdentityService:
    """Test IdentityService."""

    @pytest.fixture
    def mock_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_fingerprint_service(self):
        return AsyncMock()

    @pytest.fixture
    def mock_validation_service(self):
        return AsyncMock()

    @pytest.fixture
    def identity_service(self, mock_repo, mock_fingerprint_service, mock_validation_service):
        return IdentityService(
            repository=mock_repo,
            fingerprint_service=mock_fingerprint_service,
            validation_service=mock_validation_service,
        )

    @pytest.fixture
    def minimal_personality(self):
        return PersonalityConfig(
            companion_id="comp_123",
            name="Test",
            traits=PersonalityTraits(
                openness=0.5, conscientiousness=0.5, extraversion=0.5,
                agreeableness=0.5, neuroticism=0.5,
            ),
            created_at="2024-01-01T00:00:00", updated_at="2024-01-01T00:00:00",
        )

    @pytest.fixture
    def minimal_values(self):
        return ValuesConfig(
            companion_id="comp_123",
            hierarchy={},
            created_at="2024-01-01T00:00:00", updated_at="2024-01-01T00:00:00",
        )

    @pytest.fixture
    def minimal_voice(self):
        return VoiceProfile(
            companion_id="comp_123", name="Test",
            formality=FormalityLevel.NEUTRAL, primary_tone=EmotionalTone.NEUTRAL,
            communication_style=CommunicationStyle.CONVERSATIONAL,
            created_at="2024-01-01T00:00:00", updated_at="2024-01-01T00:00:00",
        )

    @pytest.fixture
    def minimal_boundaries(self):
        return [
            Boundary(
                companion_id="comp_123", name="Safety", scope=BoundaryScope.GLOBAL, priority=100,
                triggers=[BoundaryTrigger(id="t1", type=BoundaryTriggerType.KEYWORD, name="Test", is_active=True, keywords=["harm"])],
                actions=[BoundaryAction(id="a1", type=BoundaryActionType.REFUSE, name="Refuse", is_active=True, refusal_message="I cannot")],
                is_active=True,
            )
        ]

    @pytest.fixture
    def minimal_goals(self):
        return [
            Goal(
                companion_id="comp_123", name="Satisfaction", type=GoalType.USER_SATISFACTION,
                metrics=[Metric(id="m1", name="Score", goal_id="g1", type=MetricType.USER_FEEDBACK)],
            )
        ]

    @pytest.fixture
    def sample_identity(self, minimal_personality, minimal_values, minimal_voice, minimal_boundaries, minimal_goals):
        return IdentityConfig(
            id="id_1",
            companion_id="comp_123",
            personality=minimal_personality,
            values=minimal_values,
            voice=minimal_voice,
            boundaries=minimal_boundaries,
            goals=minimal_goals,
            version=1,
            name="Test Identity",
            description="Test",
            status=IdentityStatus.DRAFT,
            source=IdentitySource.USER_CREATED,
            created_by="test",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )

    class TestCreateIdentity:
        """Test create_identity."""

        @pytest.mark.asyncio
        async def test_create_identity_basic(self, identity_service, mock_repo, mock_fingerprint_service, mock_validation_service, minimal_personality, minimal_values, minimal_voice, minimal_boundaries, minimal_goals):
            mock_repo.save.return_value = None
            mock_repo.save_version.return_value = None
            mock_validation_service.validate_identity.return_value = (True, [], [])

            request = IdentityRequest(
                companion_id="comp_123",
                name="Test Companion",
                personality=minimal_personality,
                values=minimal_values,
                voice=minimal_voice,
                boundaries=minimal_boundaries,
                goals=minimal_goals,
            )

            response = await identity_service.create_identity(request)

            assert isinstance(response, IdentityResponse)
            assert response.companion_id == "comp_123"
            assert response.name == "Test Companion"
            assert response.status == IdentityStatus.DRAFT
            assert response.is_valid is True
            mock_repo.save.assert_called_once()
            mock_repo.save_version.assert_called_once()
            mock_fingerprint_service.compute_fingerprint.assert_called_once()
            mock_validation_service.validate_identity.assert_called_once()

        @pytest.mark.asyncio
        async def test_create_identity_with_defaults(self, identity_service, mock_repo, mock_fingerprint_service, mock_validation_service):
            mock_repo.save.return_value = None
            mock_repo.save_version.return_value = None
            mock_validation_service.validate_identity.return_value = (True, [], [])

            request = IdentityRequest(
                companion_id="comp_123",
                name="Test Companion",
            )

            response = await identity_service.create_identity(request)

            assert response.companion_id == "comp_123"
            assert response.name == "Test Companion"
            assert response.personality is not None
            assert response.values is not None
            assert response.voice is not None

        @pytest.mark.asyncio
        async def test_create_identity_auto_activate(self, identity_service, mock_repo, mock_fingerprint_service, mock_validation_service, minimal_personality, minimal_values, minimal_voice, minimal_boundaries, minimal_goals):
            mock_repo.save.return_value = None
            mock_repo.save_version.return_value = None
            mock_repo.deactivate_companion_identities.return_value = None
            mock_validation_service.validate_identity.return_value = (True, [], [])

            request = IdentityRequest(
                companion_id="comp_123",
                name="Test Companion",
                personality=minimal_personality,
                values=minimal_values,
                voice=minimal_voice,
                boundaries=minimal_boundaries,
                goals=minimal_goals,
                auto_activate=True,
            )

            response = await identity_service.create_identity(request)

            assert response.status == IdentityStatus.ACTIVE
            assert response.activated_at is not None
            mock_repo.deactivate_companion_identities.assert_called_once()

        @pytest.mark.asyncio
        async def test_create_identity_skip_validation(self, identity_service, mock_repo, mock_fingerprint_service, mock_validation_service, minimal_personality, minimal_values, minimal_voice, minimal_boundaries, minimal_goals):
            mock_repo.save.return_value = None
            mock_repo.save_version.return_value = None

            request = IdentityRequest(
                companion_id="comp_123",
                name="Test Companion",
                personality=minimal_personality,
                values=minimal_values,
                voice=minimal_voice,
                boundaries=minimal_boundaries,
                goals=minimal_goals,
                skip_validation=True,
            )

            response = await identity_service.create_identity(request)

            mock_validation_service.validate_identity.assert_not_called()

        @pytest.mark.asyncio
        async def test_create_identity_invalid(self, identity_service, mock_repo, mock_fingerprint_service, mock_validation_service, minimal_personality, minimal_values, minimal_voice, minimal_boundaries, minimal_goals):
            mock_repo.save.return_value = None
            mock_repo.save_version.return_value = None
            mock_validation_service.validate_identity.return_value = (False, ["Error"], ["Warning"])

            request = IdentityRequest(
                companion_id="comp_123",
                name="Test Companion",
                personality=minimal_personality,
                values=minimal_values,
                voice=minimal_voice,
                boundaries=minimal_boundaries,
                goals=minimal_goals,
            )

            response = await identity_service.create_identity(request)

            assert response.is_valid is False
            assert response.validation_errors == ["Error"]
            assert response.validation_warnings == ["Warning"]

    class TestGetIdentity:
        """Test get_identity."""

        @pytest.mark.asyncio
        async def test_get_identity_found(self, identity_service, mock_repo, sample_identity):
            mock_repo.get.return_value = sample_identity

            response = await identity_service.get_identity("id_1")

            assert response is not None
            assert response.id == "id_1"
            assert response.companion_id == "comp_123"
            mock_repo.get.assert_called_once_with("id_1")

        @pytest.mark.asyncio
        async def test_get_identity_not_found(self, identity_service, mock_repo):
            mock_repo.get.return_value = None

            response = await identity_service.get_identity("nonexistent")

            assert response is None
            mock_repo.get.assert_called_once_with("nonexistent")

    class TestGetActiveIdentity:
        """Test get_active_identity / get_identity_by_companion."""

        @pytest.mark.asyncio
        async def test_get_active_identity(self, identity_service, mock_repo, sample_identity):
            sample_identity.status = IdentityStatus.ACTIVE
            mock_repo.get_active.return_value = sample_identity

            response = await identity_service.get_identity_by_companion("comp_123")

            assert response is not None
            assert response.status == IdentityStatus.ACTIVE
            mock_repo.get_active.assert_called_once_with("comp_123")

        @pytest.mark.asyncio
        async def test_get_active_identity_not_found(self, identity_service, mock_repo):
            mock_repo.get_active.return_value = None

            response = await identity_service.get_identity_by_companion("comp_123")

            assert response is None

        @pytest.mark.asyncio
        async def test_get_specific_version(self, identity_service, mock_repo, sample_identity):
            sample_identity.version = 2
            mock_repo.get_version.return_value = sample_identity

            response = await identity_service.get_identity_by_companion("comp_123", version=2)

            assert response is not None
            assert response.version == 2
            mock_repo.get_version.assert_called_once_with("comp_123", 2)

    class TestUpdateIdentity:
        """Test update_identity."""

        @pytest.mark.asyncio
        async def test_update_identity(self, identity_service, mock_repo, mock_fingerprint_service, mock_validation_service, sample_identity):
            mock_repo.get.return_value = sample_identity
            mock_repo.save.return_value = None
            mock_repo.save_version.return_value = None
            mock_validation_service.validate_identity.return_value = (True, [], [])

            request = IdentityRequest(
                companion_id="comp_123",
                name="Updated Name",
                description="Updated description",
            )

            response = await identity_service.update_identity("id_1", request)

            assert response.name == "Updated Name"
            assert response.description == "Updated description"
            assert response.version == 2  # Version incremented
            assert response.parent_version_id == "id_1"
            mock_repo.save.assert_called_once()
            mock_repo.save_version.assert_called_once()
            mock_fingerprint_service.compute_fingerprint.assert_called_once()

        @pytest.mark.asyncio
        async def test_update_identity_not_found(self, identity_service, mock_repo):
            mock_repo.get.return_value = None

            with pytest.raises(ValueError, match="Identity not found"):
                await identity_service.update_identity("nonexistent", IdentityRequest(companion_id="comp_123", name="Test"))

    class TestActivateIdentity:
        """Test activate_identity."""

        @pytest.mark.asyncio
        async def test_activate_identity(self, identity_service, mock_repo, mock_fingerprint_service, sample_identity):
            sample_identity.status = IdentityStatus.DRAFT
            sample_identity.is_valid = True
            mock_repo.get.return_value = sample_identity
            mock_repo.get_active.return_value = None
            mock_repo.save.return_value = None
            mock_repo.deactivate_companion_identities.return_value = None
            mock_repo.save_version.return_value = None

            response = await identity_service.activate_identity("id_1", activated_by="user_123")

            assert response.status == IdentityStatus.ACTIVE
            assert response.activated_at is not None
            mock_repo.save.assert_called_once()
            mock_repo.save_version.assert_called_once()

        @pytest.mark.asyncio
        async def test_activate_identity_deactivates_existing(self, identity_service, mock_repo, mock_fingerprint_service, sample_identity):
            existing_active = IdentityConfig(
                id="id_old", companion_id="comp_123",
                personality=sample_identity.personality, values=sample_identity.values,
                voice=sample_identity.voice, boundaries=sample_identity.boundaries,
                goals=sample_identity.goals, version=1, name="Old", status=IdentityStatus.ACTIVE,
            )
            sample_identity.status = IdentityStatus.DRAFT
            sample_identity.is_valid = True
            mock_repo.get.return_value = sample_identity
            mock_repo.get_active.return_value = existing_active
            mock_repo.save.return_value = None
            mock_repo.deactivate_companion_identities.return_value = None
            mock_repo.save_version.return_value = None

            response = await identity_service.activate_identity("id_1")

            assert response.status == IdentityStatus.ACTIVE
            mock_repo.deactivate_companion_identities.assert_called_once_with("comp_123")

        @pytest.mark.asyncio
        async def test_activate_invalid_identity_raises(self, identity_service, mock_repo, sample_identity):
            sample_identity.status = IdentityStatus.DRAFT
            sample_identity.is_valid = False
            sample_identity.validation_errors = ["Error"]
            mock_repo.get.return_value = sample_identity

            with pytest.raises(ValueError, match="Cannot activate invalid identity"):
                await identity_service.activate_identity("id_1")

    class TestDeactivateIdentity:
        """Test deactivate_identity."""

        @pytest.mark.asyncio
        async def test_deactivate_identity(self, identity_service, mock_repo, mock_fingerprint_service, sample_identity):
            sample_identity.status = IdentityStatus.ACTIVE
            mock_repo.get.return_value = sample_identity
            mock_repo.save.return_value = None
            mock_repo.save_version.return_value = None

            response = await identity_service.deactivate_identity("id_1", deactivated_by="user_123")

            assert response.status == IdentityStatus.DEPRECATED
            mock_repo.save.assert_called_once()
            mock_repo.save_version.assert_called_once()

    class TestListIdentities:
        """Test list_identities."""

        @pytest.mark.asyncio
        async def test_list_identities(self, identity_service, mock_repo, sample_identity):
            mock_repo.list.return_value = [sample_identity]

            responses = await identity_service.list_identities(companion_id="comp_123", status=IdentityStatus.ACTIVE, limit=10, offset=0)

            assert len(responses) == 1
            assert responses[0].id == "id_1"
            mock_repo.list.assert_called_once_with(companion_id="comp_123", status=IdentityStatus.ACTIVE, limit=10, offset=0)

    class TestGetIdentityHistory:
        """Test get_identity_history / get_version_history."""

        @pytest.mark.asyncio
        async def test_get_version_history(self, identity_service, mock_repo, sample_identity):
            versions = [
                IdentityVersion(
                    id="ver_1", identity_id="id_1", companion_id="comp_123", version=1,
                    personality=sample_identity.personality, values=sample_identity.values,
                    voice=sample_identity.voice, boundaries=[], goals=[],
                    change_type="create", change_summary="Initial", changed_fields=[], changed_by="user",
                    created_at=datetime.utcnow(),
                ),
                IdentityVersion(
                    id="ver_2", identity_id="id_1", companion_id="comp_123", version=2,
                    personality=sample_identity.personality, values=sample_identity.values,
                    voice=sample_identity.voice, boundaries=[], goals=[],
                    change_type="update", change_summary="Updated", changed_fields=["name"], changed_by="user",
                    created_at=datetime.utcnow(),
                ),
            ]
            mock_repo.get_version_history.return_value = versions

            history = await identity_service.get_identity_history("comp_123")

            assert len(history) == 2
            assert history[0].version == 1
            assert history[1].version == 2
            mock_repo.get_version_history.assert_called_once_with("comp_123")

    class TestRollbackIdentity:
        """Test rollback_identity."""

        @pytest.mark.asyncio
        async def test_rollback_identity(self, identity_service, mock_repo, mock_fingerprint_service, mock_validation_service, sample_identity):
            target_version = IdentityConfig(
                id="id_1", companion_id="comp_123",
                personality=sample_identity.personality, values=sample_identity.values,
                voice=sample_identity.voice, boundaries=[], goals=[],
                version=1, name="Original", status=IdentityStatus.ACTIVE,
                source=IdentitySource.USER_CREATED, created_by="user",
                created_at="2024-01-01T00:00:00", updated_at="2024-01-01T00:00:00",
            )
            current_identity = IdentityConfig(
                id="id_2", companion_id="comp_123",
                personality=sample_identity.personality, values=sample_identity.values,
                voice=sample_identity.voice, boundaries=[], goals=[],
                version=3, name="Current", status=IdentityStatus.ACTIVE,
                source=IdentitySource.USER_CREATED, created_by="user",
                created_at="2024-01-01T00:00:00", updated_at="2024-01-01T00:00:00",
            )
            
            mock_repo.get.return_value = current_identity
            mock_repo.get_version.return_value = target_version
            mock_repo.save.return_value = None
            mock_repo.save_version.return_value = None
            mock_repo.deactivate_companion_identities.return_value = None
            mock_validation_service.validate_identity.return_value = (True, [], [])

            response = await identity_service.rollback_identity("comp_123", 1, rolled_back_by="user_123")

            assert response.version == 4  # New version (current.version + 1)
            assert response.parent_version_id == target_version.id
            assert response.status == IdentityStatus.ACTIVE
            assert "rollback" in response.description.lower()
            mock_repo.deactivate_companion_identities.assert_called_once()
            mock_repo.save.assert_called_once()
            mock_repo.save_version.assert_called_once()
            mock_fingerprint_service.compute_fingerprint.assert_called_once()

        @pytest.mark.asyncio
        async def test_rollback_version_not_found(self, identity_service, mock_repo, sample_identity):
            current_identity = IdentityConfig(
                id="id_2", companion_id="comp_123",
                personality=sample_identity.personality, values=sample_identity.values,
                voice=sample_identity.voice, boundaries=[], goals=[],
                version=3, name="Current", status=IdentityStatus.ACTIVE,
                source=IdentitySource.USER_CREATED, created_by="user",
                created_at="2024-01-01T00:00:00", updated_at="2024-01-01T00:00:00",
            )
            mock_repo.get.return_value = current_identity
            mock_repo.get_version.return_value = None

            with pytest.raises(ValueError, match="Version 1 not found"):
                await identity_service.rollback_identity("comp_123", 1)

        @pytest.mark.asyncio
        async def test_rollback_no_active_identity(self, identity_service, mock_repo):
            mock_repo.get.return_value = None
            mock_repo.get_version.return_value = IdentityConfig(id="v1", companion_id="comp_123")

            with pytest.raises(ValueError, match="No active identity"):
                await identity_service.rollback_identity("comp_123", 1)
