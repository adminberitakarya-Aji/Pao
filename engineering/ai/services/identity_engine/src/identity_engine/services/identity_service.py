"""Identity Service - Core service for managing companion identities."""

from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import structlog

from pao_shared.config import get_settings
from pao_shared.observability import setup_tracing, setup_metrics, setup_logging

from ..models import (
    IdentityConfig, IdentityRequest, IdentityResponse, IdentityVersion,
    IdentityStatus, IdentitySource, PersonalityConfig, ValuesConfig,
    VoiceProfile, Boundary, Goal, BoundaryScope, GoalStatus,
)

logger = structlog.get_logger(__name__)


class IdentityService:
    """Core service for identity management."""
    
    def __init__(self, repository=None, fingerprint_service=None, validation_service=None):
        self.repository = repository
        self.fingerprint_service = fingerprint_service
        self.validation_service = validation_service
        self._tracer = setup_tracing("identity-engine", "identity-service")
        self._meter = setup_metrics("identity-engine", "identity-service")
        
        # Metrics
        self._identity_created = self._meter.create_counter(
            "identity_created_total", "Total identities created"
        )
        self._identity_updated = self._meter.create_counter(
            "identity_updated_total", "Total identities updated"
        )
        self._identity_activated = self._meter.create_counter(
            "identity_activated_total", "Total identities activated"
        )
        self._validation_duration = self._meter.create_histogram(
            "identity_validation_duration_seconds", "Validation duration"
        )
    
    async def create_identity(self, request: IdentityRequest) -> IdentityResponse:
        """Create a new identity configuration."""
        with self._tracer.start_as_current_span("create_identity") as span:
            span.set_attribute("companion_id", request.companion_id)
            
            # Generate ID
            identity_id = f"id_{request.companion_id}_{uuid.uuid4().hex[:8]}"
            now = datetime.utcnow().isoformat()
            
            # Build identity config
            identity = await self._build_identity_config(
                identity_id=identity_id,
                request=request,
                version=1,
                now=now,
            )
            
            # Validate if not skipped
            if not request.skip_validation and self.validation_service:
                is_valid, errors, warnings = await self.validation_service.validate_identity(identity)
                identity.is_valid = is_valid
                identity.validation_errors = errors
                identity.validation_warnings = warnings
            
            # Auto-activate if requested and valid
            if request.auto_activate and identity.is_valid:
                identity.status = IdentityStatus.ACTIVE
                identity.activated_at = now
            
            # Save to repository
            if self.repository:
                await self.repository.save(identity)
            
            # Create initial version snapshot
            version = identity.create_version(
                change_type="create",
                change_summary=f"Initial identity creation: {request.name}",
                changed_fields=["all"],
                changed_by=request.created_by or "system",
            )
            if self.repository:
                await self.repository.save_version(version)
            
            # Compute fingerprint
            if self.fingerprint_service:
                await self.fingerprint_service.compute_fingerprint(identity)
            
            self._identity_created.add(1, {"companion_id": request.companion_id})
            
            logger.info("Identity created", identity_id=identity_id, companion_id=request.companion_id)
            
            return self._to_response(identity)
    
    async def get_identity(self, identity_id: str) -> Optional[IdentityResponse]:
        """Get an identity by ID."""
        if not self.repository:
            return None
        
        identity = await self.repository.get(identity_id)
        if identity:
            return self._to_response(identity)
        return None
    
    async def get_identity_by_companion(self, companion_id: str, version: Optional[int] = None) -> Optional[IdentityResponse]:
        """Get the active identity for a companion, optionally at a specific version."""
        if not self.repository:
            return None
        
        if version:
            identity = await self.repository.get_version(companion_id, version)
        else:
            identity = await self.repository.get_active(companion_id)
        
        if identity:
            return self._to_response(identity)
        return None
    
    async def update_identity(self, identity_id: str, request: IdentityRequest) -> IdentityResponse:
        """Update an existing identity."""
        with self._tracer.start_as_current_span("update_identity") as span:
            span.set_attribute("identity_id", identity_id)
            
            if not self.repository:
                raise ValueError("Repository not configured")
            
            identity = await self.repository.get(identity_id)
            if not identity:
                raise ValueError(f"Identity not found: {identity_id}")
            
            # Track changed fields
            changed_fields = []
            now = datetime.utcnow().isoformat()
            
            # Update components if provided
            if request.personality is not None:
                identity.personality = request.personality
                changed_fields.append("personality")
            if request.values is not None:
                identity.values = request.values
                changed_fields.append("values")
            if request.voice is not None:
                identity.voice = request.voice
                changed_fields.append("voice")
            if request.boundaries:
                identity.boundaries = request.boundaries
                changed_fields.append("boundaries")
            if request.goals:
                identity.goals = request.goals
                changed_fields.append("goals")
            
            # Update metadata
            identity.name = request.name
            identity.description = request.description
            identity.tags = request.tags
            identity.metadata = request.metadata
            identity.updated_at = now
            identity.version += 1
            
            # Re-validate
            if not request.skip_validation and self.validation_service:
                is_valid, errors, warnings = await self.validation_service.validate_identity(identity)
                identity.is_valid = is_valid
                identity.validation_errors = errors
                identity.validation_warnings = warnings
            
            # Save updated identity
            await self.repository.save(identity)
            
            # Create version snapshot
            version = identity.create_version(
                change_type="update",
                change_summary=f"Updated identity: {', '.join(changed_fields)}",
                changed_fields=changed_fields,
                changed_by=request.created_by or "system",
            )
            await self.repository.save_version(version)
            
            # Recompute fingerprint
            if self.fingerprint_service:
                await self.fingerprint_service.compute_fingerprint(identity)
            
            self._identity_updated.add(1, {"identity_id": identity_id})
            
            logger.info("Identity updated", identity_id=identity_id, changed_fields=changed_fields)
            
            return self._to_response(identity)
    
    async def activate_identity(self, identity_id: str, activated_by: str = "system") -> IdentityResponse:
        """Activate an identity (make it the current active version)."""
        with self._tracer.start_as_current_span("activate_identity") as span:
            span.set_attribute("identity_id", identity_id)
            
            if not self.repository:
                raise ValueError("Repository not configured")
            
            identity = await self.repository.get(identity_id)
            if not identity:
                raise ValueError(f"Identity not found: {identity_id}")
            
            if not identity.is_valid:
                raise ValueError(f"Cannot activate invalid identity: {identity.validation_errors}")
            
            # Deactivate other identities for this companion
            await self.repository.deactivate_companion_identities(identity.companion_id)
            
            # Activate this one
            identity.status = IdentityStatus.ACTIVE
            identity.activated_at = datetime.utcnow().isoformat()
            identity.updated_at = datetime.utcnow().isoformat()
            
            await self.repository.save(identity)
            
            # Create version snapshot
            version = identity.create_version(
                change_type="update",
                change_summary="Identity activated",
                changed_fields=["status", "activated_at"],
                changed_by=activated_by,
            )
            await self.repository.save_version(version)
            
            self._identity_activated.add(1, {"companion_id": identity.companion_id})
            
            logger.info("Identity activated", identity_id=identity_id, companion_id=identity.companion_id)
            
            return self._to_response(identity)
    
    async def deactivate_identity(self, identity_id: str, deactivated_by: str = "system") -> IdentityResponse:
        """Deactivate an identity."""
        if not self.repository:
            raise ValueError("Repository not configured")
        
        identity = await self.repository.get(identity_id)
        if not identity:
            raise ValueError(f"Identity not found: {identity_id}")
        
        identity.status = IdentityStatus.DEPRECATED
        identity.updated_at = datetime.utcnow().isoformat()
        
        await self.repository.save(identity)
        
        version = identity.create_version(
            change_type="update",
            change_summary="Identity deactivated",
            changed_fields=["status"],
            changed_by=deactivated_by,
        )
        await self.repository.save_version(version)
        
        logger.info("Identity deactivated", identity_id=identity_id)
        
        return self._to_response(identity)
    
    async def list_identities(
        self, 
        companion_id: Optional[str] = None,
        status: Optional[IdentityStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[IdentityResponse]:
        """List identities with optional filters."""
        if not self.repository:
            return []
        
        identities = await self.repository.list(
            companion_id=companion_id,
            status=status,
            limit=limit,
            offset=offset
        )
        return [self._to_response(i) for i in identities]
    
    async def get_identity_history(self, companion_id: str) -> List[IdentityVersion]:
        """Get version history for a companion's identity."""
        if not self.repository:
            return []
        return await self.repository.get_version_history(companion_id)
    
    async def rollback_identity(self, companion_id: str, target_version: int, rolled_back_by: str = "system") -> IdentityResponse:
        """Rollback to a previous version."""
        with self._tracer.start_as_current_span("rollback_identity") as span:
            span.set_attribute("companion_id", companion_id)
            span.set_attribute("target_version", target_version)
            
            if not self.repository:
                raise ValueError("Repository not configured")
            
            # Get target version
            target = await self.repository.get_version(companion_id, target_version)
            if not target:
                raise ValueError(f"Version {target_version} not found for companion {companion_id}")
            
            # Get current active identity
            current = await self.repository.get_active(companion_id)
            if not current:
                raise ValueError(f"No active identity for companion {companion_id}")
            
            # Create new identity from target version
            new_identity = IdentityConfig(
                id=f"id_{companion_id}_{uuid.uuid4().hex[:8]}",
                companion_id=companion_id,
                personality=target.personality,
                values=target.values,
                voice=target.voice,
                boundaries=target.boundaries,
                goals=target.goals,
                version=current.version + 1,
                name=f"{target.name} (rollback from v{target_version})",
                description=f"Rolled back from version {current.version} to {target_version}",
                status=IdentityStatus.ACTIVE,
                source=IdentitySource.EVOLVED,
                parent_version_id=target.id,
                created_by=rolled_back_by,
            )
            
            # Validate
            if self.validation_service:
                is_valid, errors, warnings = await self.validation_service.validate_identity(new_identity)
                new_identity.is_valid = is_valid
                new_identity.validation_errors = errors
                new_identity.validation_warnings = warnings
            
            # Deactivate current, activate new
            await self.repository.deactivate_companion_identities(companion_id)
            new_identity.activated_at = datetime.utcnow().isoformat()
            await self.repository.save(new_identity)
            
            # Create version
            version = new_identity.create_version(
                change_type="rollback",
                change_summary=f"Rolled back from v{current.version} to v{target_version}",
                changed_fields=["all"],
                changed_by=rolled_back_by,
            )
            await self.repository.save_version(version)
            
            # Fingerprint
            if self.fingerprint_service:
                await self.fingerprint_service.compute_fingerprint(new_identity)
            
            logger.info("Identity rolled back", companion_id=companion_id, from_version=current.version, to_version=target_version)
            
            return self._to_response(new_identity)
    
    async def _build_identity_config(
        self,
        identity_id: str,
        request: IdentityRequest,
        version: int,
        now: str
    ) -> IdentityConfig:
        """Build IdentityConfig from request."""
        # Use provided configs or create defaults
        personality = request.personality or PersonalityConfig.create_default(request.companion_id)
        values = request.values or ValuesConfig.create_default(request.companion_id)
        voice = request.voice or VoiceProfile.create_default(request.companion_id)
        boundaries = request.boundaries or Boundary.get_default_boundaries(request.companion_id)
        goals = request.goals or Goal.get_default_goals(request.companion_id)
        
        return IdentityConfig(
            id=identity_id,
            companion_id=request.companion_id,
            personality=personality,
            values=values,
            voice=voice,
            boundaries=boundaries,
            goals=goals,
            version=version,
            name=request.name,
            description=request.description,
            status=IdentityStatus.DRAFT,
            source=request.source,
            created_by=request.created_by or "system",
            tags=request.tags,
            metadata=request.metadata,
            created_at=now,
            updated_at=now,
        )
    
    def _to_response(self, identity: IdentityConfig) -> IdentityResponse:
        """Convert IdentityConfig to IdentityResponse."""
        return IdentityResponse(
            id=identity.id,
            companion_id=identity.companion_id,
            version=identity.version,
            personality=identity.personality,
            values=identity.values,
            voice=identity.voice,
            boundaries=identity.boundaries,
            goals=identity.goals,
            status=identity.status,
            source=identity.source,
            is_valid=identity.is_valid,
            validation_errors=identity.validation_errors,
            validation_warnings=identity.validation_warnings,
            name=identity.name,
            description=identity.description,
            tags=identity.tags,
            metadata=identity.metadata,
            created_at=identity.created_at,
            updated_at=identity.updated_at,
            activated_at=identity.activated_at,
            created_by=identity.created_by,
        )