"""Runtime Service - Main orchestration service for Companion Runtime."""

import logging
from typing import Optional, AsyncGenerator
from uuid import UUID

from companion_runtime.models.requests import ChatRequest, ChatStreamRequest, CompanionContextRequest
from companion_runtime.models.responses import (
    ChatResponse,
    ChatStreamChunk,
    CompanionStateResponse,
    GraphExecutionResponse,
)
from companion_runtime.services.graph_builder import execute_graph, execute_graph_stream
from companion_runtime.services.engine_clients import (
    IdentityEngineClient,
    MemoryEngineClient,
    SafetyEngineClient,
    RelationshipEngineClient,
    EmotionEngineClient,
    VoiceEngineClient,
    ProactiveEngineClient,
    EvaluationEngineClient,
)
from companion_runtime.services.state_manager import StateManager, get_state_manager

logger = logging.getLogger(__name__)


class RuntimeService:
    """Main service for Companion Runtime orchestration."""

    def __init__(self):
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the runtime service."""
        logger.info("Initializing Runtime Service")
        # State manager is initialized lazily via get_state_manager()
        self._initialized = True
        logger.info("Runtime Service initialized")

    async def close(self) -> None:
        """Close the runtime service."""
        logger.info("Closing Runtime Service")
        self._initialized = False
        logger.info("Runtime Service closed")

    async def chat(self, request: ChatRequest) -> GraphExecutionResponse:
        """Process a chat request (non-streaming)."""
        logger.info(
            f"Processing chat request",
            extra={
                "user_id": str(request.user_id),
                "companion_id": str(request.companion_id),
                "conversation_id": str(request.conversation_id),
                "request_id": request.request_id,
            },
        )
        
        return await execute_graph(request)

    async def chat_stream(self, request: ChatStreamRequest) -> AsyncGenerator[ChatStreamChunk, None]:
        """Process a streaming chat request."""
        logger.info(
            f"Processing streaming chat request",
            extra={
                "user_id": str(request.user_id),
                "companion_id": str(request.companion_id),
                "conversation_id": str(request.conversation_id),
                "request_id": request.request_id,
            },
        )
        
        async for chunk in execute_graph_stream(request):
            yield chunk

    async def get_companion_context(self, request: CompanionContextRequest) -> CompanionStateResponse:
        """Get aggregated companion context from all engines."""
        logger.info(
            f"Fetching companion context",
            extra={
                "user_id": str(request.user_id),
                "companion_id": str(request.companion_id),
                "conversation_id": str(request.conversation_id) if request.conversation_id else None,
                "request_id": request.request_id,
            },
        )
        
        # Initialize clients
        identity_client = IdentityEngineClient()
        memory_client = MemoryEngineClient()
        relationship_client = RelationshipEngineClient()
        emotion_client = EmotionEngineClient()
        proactive_client = ProactiveEngineClient()
        
        # Fetch contexts in parallel
        import asyncio
        
        tasks = []
        if request.include_identity:
            tasks.append(("identity", identity_client.get_context(request.companion_id, request.request_id)))
        if request.include_memory:
            tasks.append(("memory", memory_client.recall(
                request.user_id, request.companion_id, "", limit=20, request_id=request.request_id
            )))
        if request.include_relationship:
            tasks.append(("relationship", relationship_client.get_state(
                request.user_id, request.companion_id, request.request_id
            )))
        if request.include_emotion:
            tasks.append(("emotion", emotion_client.get_state(
                request.user_id, request.companion_id, request.request_id
            )))
        
        results = {}
        if tasks:
            names, coros = zip(*tasks)
            task_results = await asyncio.gather(*coros, return_exceptions=True)
            results = dict(zip(names, task_results))
        
        # Fetch proactive nudges
        proactive_pending = None
        if request.conversation_id:
            try:
                proactive_result = await proactive_client.check_nudge(
                    user_id=request.user_id,
                    companion_id=request.companion_id,
                    conversation_id=request.conversation_id,
                    last_message="",  # No specific message for context fetch
                    request_id=request.request_id,
                )
                if proactive_result.get("should_generate"):
                    proactive_pending = [proactive_result.get("nudge")]
            except Exception as e:
                logger.warning(f"Proactive check failed: {e}")
        
        return CompanionStateResponse(
            user_id=request.user_id,
            companion_id=request.companion_id,
            conversation_id=request.conversation_id,
            identity=results.get("identity") if not isinstance(results.get("identity"), Exception) else None,
            memory=results.get("memory") if not isinstance(results.get("memory"), Exception) else None,
            relationship=results.get("relationship") if not isinstance(results.get("relationship"), Exception) else None,
            emotion=results.get("emotion") if not isinstance(results.get("emotion"), Exception) else None,
            proactive_pending=proactive_pending,
            request_id=request.request_id,
        )

    async def health_check(self) -> dict:
        """Comprehensive health check of runtime and all engines."""
        logger.debug("Running health check")
        
        # Check state manager
        state_manager = await get_state_manager()
        state_health = await state_manager.health_check()
        
        # Check all engines
        engine_clients = {
            "identity": IdentityEngineClient(),
            "memory": MemoryEngineClient(),
            "safety": SafetyEngineClient(),
            "relationship": RelationshipEngineClient(),
            "emotion": EmotionEngineClient(),
            "voice": VoiceEngineClient(),
            "proactive": ProactiveEngineClient(),
            "evaluation": EvaluationEngineClient(),
            "inference": InferenceGatewayClient(),
        }
        
        import asyncio
        engine_health = {}
        
        async def check_engine(name: str, client):
            try:
                result = await client.health_check()
                await client.close()
                return name, {"healthy": result.get("healthy", False), "details": result}
            except Exception as e:
                await client.close()
                return name, {"healthy": False, "error": str(e)}
        
        engine_results = await asyncio.gather(*[
            check_engine(name, client) for name, client in engine_clients.items()
        ], return_exceptions=True)
        
        for result in engine_results:
            if isinstance(result, tuple):
                engine_health[result[0]] = result[1]
            else:
                logger.error(f"Engine health check failed: {result}")
        
        # Overall status
        all_healthy = state_health.get("database") == "healthy" and all(
            h.get("healthy", False) for h in engine_health.values()
        )
        
        return {
            "service": "companion-runtime",
            "version": "0.1.0",
            "status": "healthy" if all_healthy else "degraded",
            "state_manager": state_health,
            "engines": engine_health,
            "initialized": self._initialized,
        }

    async def trigger_memory_consolidation(
        self,
        user_id: UUID,
        companion_id: UUID,
        conversation_id: Optional[UUID] = None,
        force: bool = False,
    ) -> dict:
        """Trigger memory consolidation for a user-companion pair."""
        logger.info(f"Triggering memory consolidation", extra={
            "user_id": str(user_id),
            "companion_id": str(companion_id),
            "conversation_id": str(conversation_id) if conversation_id else None,
        })
        
        memory_client = MemoryEngineClient()
        try:
            result = await memory_client.consolidate(
                user_id=user_id,
                companion_id=companion_id,
                conversation_id=conversation_id,
                force=force,
            )
            return {"success": True, "consolidation_id": result.get("consolidation_id"), "message": "Consolidation triggered"}
        except Exception as e:
            logger.error(f"Memory consolidation trigger failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            await memory_client.close()


# Global instance
_runtime_service: Optional[RuntimeService] = None


async def get_runtime_service() -> RuntimeService:
    """Get or create RuntimeService singleton."""
    global _runtime_service
    if _runtime_service is None:
        _runtime_service = RuntimeService()
        await _runtime_service.initialize()
    return _runtime_service


async def close_runtime_service() -> None:
    """Close RuntimeService."""
    global _runtime_service
    if _runtime_service:
        await _runtime_service.close()
        _runtime_service = None