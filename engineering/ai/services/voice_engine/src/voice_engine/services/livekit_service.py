"""LiveKit Service for WebRTC voice calls."""

import asyncio
import logging
import uuid
from typing import Optional, Dict, Any, List

from voice_engine.config import settings
from voice_engine.models.requests import (
    CallSetupRequest,
    CallEndRequest,
    RecordingRequest,
)
from voice_engine.models.responses import (
    CallSetupResponse,
    CallEndResponse,
    RecordingResponse,
)

logger = logging.getLogger(__name__)


class LiveKitService:
    """Service for managing LiveKit voice calls."""
    
    def __init__(self):
        self.livekit_url = settings.livekit_url
        self.api_key = settings.livekit_api_key
        self.api_secret = settings.livekit_api_secret
        self.rooms: Dict[str, Dict[str, Any]] = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize LiveKit connection."""
        logger.info("Initializing LiveKit service")
        self._initialized = True
    
    async def setup_call(self, request: CallSetupRequest) -> CallSetupResponse:
        """Set up a new voice call room."""
        import livekit
        
        # Create room
        room_name = request.room_name or f"pao-call-{uuid.uuid4().hex[:8]}"
        
        # Generate access token
        token = livekit.AccessToken(
            self.api_key,
            self.api_secret,
        ).with_identity(request.participant_identity).with_name(
            request.participant_name or request.participant_identity
        ).with_grants(
            livekit.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        ).to_jwt()
        
        # Store room info
        self.rooms[room_name] = {
            "user_id": str(request.user_id),
            "companion_id": str(request.companion_id),
            "participants": {},
            "recording": False,
            "egress_id": None,
            "created_at": asyncio.get_event_loop().time(),
            "metadata": request.metadata or {},
        }
        
        # Start recording if requested
        egress_id = None
        if request.recording_enabled:
            egress_id = await self.start_recording(
                RecordingRequest(
                    room_name=room_name,
                    action="start",
                    output_format="mp4",
                    audio_only=request.audio_only,
                )
            )
        
        return CallSetupResponse(
            room_name=room_name,
            token=token,
            url=self.livekit_url,
            participant_identity=request.participant_identity,
            recording_started=request.recording_enabled,
            egress_id=egress_id,
        )
    
    async def end_call(self, request: CallEndRequest) -> CallEndResponse:
        """End a voice call."""
        import livekit
        
        room_name = request.room_name
        room_info = self.rooms.get(room_name)
        
        if not room_info:
            return CallEndResponse(
                room_name=room_name,
                status="error",
                duration_seconds=0,
                message="Room not found",
            )
        
        # Stop recording if active
        if room_info["recording"] and room_info["egress_id"]:
            await self.stop_recording(RecordingRequest(
                room_name=room_name,
                action="stop",
            ))
        
        # Calculate duration
        duration = asyncio.get_event_loop().time() - room_info["created_at"]
        
        # Clean up
        del self.rooms[room_name]
        
        return CallEndResponse(
            room_name=room_name,
            status=request.reason,
            duration_seconds=duration,
            recording_url=room_info.get("recording_url"),
            message="Call ended",
        )
    
    async def start_recording(self, request: RecordingRequest) -> Optional[str]:
        """Start recording a room."""
        import livekit
        
        room_name = request.room_name
        
        # Configure egress
        egress = livekit.RoomEgress(
            room_name=room_name,
            audio_only=request.audio_only,
            file_output=livekit.FileOutput(
                filepath=f"recordings/{room_name}/{uuid.uuid4().hex}.{request.output_format}",
                s3=livekit.S3Upload(
                    access_key=settings.livekit_s3_access_key,
                    secret=settings.livekit_s3_secret,
                    region=settings.livekit_s3_region,
                    bucket=settings.livekit_egress_bucket,
                ),
            ),
        )
        
        # In a real implementation, this would call LiveKit API
        # egress_id = await livekit_api.room.start_egress(egress)
        
        # Mock egress ID for now
        egress_id = f"egress-{uuid.uuid4().hex[:8]}"
        
        if room_name in self.rooms:
            self.rooms[room_name]["recording"] = True
            self.rooms[room_name]["egress_id"] = egress_id
        
        logger.info("Recording started", room=room_name, egress_id=egress_id)
        return egress_id
    
    async def stop_recording(self, request: RecordingRequest) -> RecordingResponse:
        """Stop recording a room."""
        room_name = request.room_name
        room_info = self.rooms.get(room_name)
        
        if not room_info or not room_info["recording"]:
            return RecordingResponse(
                room_name=room_name,
                action="failed",
                message="No active recording",
            )
        
        # In a real implementation:
        # await livekit_api.room.stop_egress(room_info["egress_id"])
        
        egress_id = room_info["egress_id"]
        room_info["recording"] = False
        room_info["egress_id"] = None
        
        # Mock recording URL
        recording_url = f"s3://{settings.livekit_egress_bucket}/recordings/{room_name}/{egress_id}.mp4"
        room_info["recording_url"] = recording_url
        
        logger.info("Recording stopped", room=room_name, egress_id=egress_id)
        
        return RecordingResponse(
            room_name=room_name,
            action="stopped",
            egress_id=egress_id,
            output_url=recording_url,
        )
    
    async def get_room_info(self, room_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a room."""
        return self.rooms.get(room_name)
    
    async def list_active_rooms(self) -> List[Dict[str, Any]]:
        """List all active rooms."""
        return [
            {
                "room_name": name,
                "user_id": info["user_id"],
                "companion_id": info["companion_id"],
                "participant_count": len(info["participants"]),
                "recording": info["recording"],
                "duration": asyncio.get_event_loop().time() - info["created_at"],
            }
            for name, info in self.rooms.items()
        ]
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for LiveKit service."""
        return {
            "connected": self._initialized,
            "livekit_url": self.livekit_url,
            "active_rooms": len(self.rooms),
        }
    
    async def close(self) -> None:
        """Cleanup resources."""
        self.rooms.clear()
        self._initialized = False
        logger.info("LiveKit service closed")


# Singleton instance
_livekit_service: Optional[LiveKitService] = None


async def get_livekit_service() -> LiveKitService:
    """Get or create LiveKit service singleton."""
    global _livekit_service
    if _livekit_service is None:
        _livekit_service = LiveKitService()
        await _livekit_service.initialize()
    return _livekit_service


async def close_livekit_service() -> None:
    """Close LiveKit service."""
    global _livekit_service
    if _livekit_service:
        await _livekit_service.close()
        _livekit_service = None