"""State Manager for Companion Runtime - Handles LangGraph checkpointing with PostgreSQL."""

import logging
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from contextlib import asynccontextmanager

import asyncpg
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.base import Checkpoint, CheckpointMetadata

from companion_runtime.config import settings

logger = logging.getLogger(__name__)


class StateManager:
    """Manages conversation state and LangGraph checkpointing."""

    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None
        self._saver: Optional[PostgresSaver] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize database connection pool and checkpoint saver."""
        logger.info("Initializing State Manager")
        
        # Create connection pool
        self._pool = await asyncpg.create_pool(
            settings.database_url.replace("postgresql+asyncpg://", "postgresql://"),
            min_size=2,
            max_size=settings.database_pool_size,
            command_timeout=60,
        )
        
        # Initialize PostgresSaver for LangGraph checkpointing
        self._saver = PostgresSaver(self._pool)
        await self._saver.setup()
        
        self._initialized = True
        logger.info("State Manager initialized")

    async def close(self) -> None:
        """Close database connections."""
        logger.info("Closing State Manager")
        if self._pool:
            await self._pool.close()
        self._initialized = False
        logger.info("State Manager closed")

    @property
    def saver(self) -> PostgresSaver:
        """Get the LangGraph PostgresSaver instance."""
        if not self._initialized or not self._saver:
            raise RuntimeError("State Manager not initialized")
        return self._saver

    @property
    def pool(self) -> asyncpg.Pool:
        """Get the database connection pool."""
        if not self._initialized or not self._pool:
            raise RuntimeError("State Manager not initialized")
        return self._pool

    # Checkpoint operations
    async def get_checkpoint(
        self,
        thread_id: str,
        checkpoint_id: Optional[str] = None,
    ) -> Optional[Checkpoint]:
        """Get a checkpoint for a thread."""
        config = {"configurable": {"thread_id": thread_id}}
        if checkpoint_id:
            config["configurable"]["checkpoint_id"] = checkpoint_id
        
        return await self._saver.aget(config)

    async def list_checkpoints(
        self,
        thread_id: str,
        limit: int = 10,
    ) -> List[Checkpoint]:
        """List checkpoints for a thread."""
        config = {"configurable": {"thread_id": thread_id}}
        checkpoints = []
        async for checkpoint in self._saver.alist(config, limit=limit):
            checkpoints.append(checkpoint)
        return checkpoints

    async def delete_checkpoints(self, thread_id: str) -> None:
        """Delete all checkpoints for a thread."""
        config = {"configurable": {"thread_id": thread_id}}
        await self._saver.adelete(config)

    # Conversation state operations
    async def get_conversation_state(
        self,
        user_id: UUID,
        companion_id: UUID,
        conversation_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """Get the latest conversation state from checkpoints."""
        thread_id = f"{user_id}:{companion_id}:{conversation_id}"
        checkpoint = await self.get_checkpoint(thread_id)
        
        if checkpoint:
            return checkpoint.get("channel_values", {})
        return None

    async def save_conversation_state(
        self,
        user_id: UUID,
        companion_id: UUID,
        conversation_id: UUID,
        state: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Save conversation state as a checkpoint."""
        thread_id = f"{user_id}:{companion_id}:{conversation_id}"
        config = {"configurable": {"thread_id": thread_id}}
        
        checkpoint_metadata: CheckpointMetadata = {
            "source": "companion_runtime",
            "step": metadata.get("step", 0) if metadata else 0,
            "parents": {},
            "thread_id": thread_id,
        }
        
        if metadata:
            checkpoint_metadata.update(metadata)
        
        checkpoint = Checkpoint(
            v=1,
            ts=datetime.utcnow().isoformat() + "Z",
            channel_values=state,
            channel_versions={},
            versions_seen={},
        )
        
        await self._saver.aput(config, checkpoint, checkpoint_metadata, {})
        return config["configurable"].get("checkpoint_id", "unknown")

    # Utility methods
    async def get_thread_history(
        self,
        user_id: UUID,
        companion_id: UUID,
        conversation_id: UUID,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get conversation history from checkpoints."""
        thread_id = f"{user_id}:{companion_id}:{conversation_id}"
        checkpoints = await self.list_checkpoints(thread_id, limit)
        
        history = []
        for cp in checkpoints:
            history.append({
                "checkpoint_id": cp.config.get("configurable", {}).get("checkpoint_id"),
                "timestamp": cp.ts,
                "state": cp.channel_values,
                "metadata": cp.metadata,
            })
        
        return history

    async def health_check(self) -> Dict[str, Any]:
        """Health check for state manager."""
        try:
            async with self._pool.acquire() as conn:
                await conn.execute("SELECT 1")
            return {
                "initialized": self._initialized,
                "database": "healthy",
                "pool_size": self._pool.get_size() if self._pool else 0,
            }
        except Exception as e:
            return {
                "initialized": self._initialized,
                "database": "unhealthy",
                "error": str(e),
            }


# Global instance
_state_manager: Optional[StateManager] = None


async def get_state_manager() -> StateManager:
    """Get or create StateManager singleton."""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
        await _state_manager.initialize()
    return _state_manager


async def close_state_manager() -> None:
    """Close StateManager."""
    global _state_manager
    if _state_manager:
        await _state_manager.close()
        _state_manager = None