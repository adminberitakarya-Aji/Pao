"""API Dependencies for Memory Engine."""

from typing import Optional
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from pao_shared.config import get_settings

from ..repositories import (
    PostgresRepository,
    QdrantRepository,
    KuzuRepository,
    RedisRepository,
)
from ..services import (
    MemoryService,
    ConsolidationService,
    RecallService,
    ConsistencyService,
    ExportService,
)

settings = get_settings()

# Global repository instances (initialized on startup)
_postgres_repo: Optional[PostgresRepository] = None
_qdrant_repo: Optional[QdrantRepository] = None
_kuzu_repo: Optional[KuzuRepository] = None
_redis_repo: Optional[RedisRepository] = None

# Global service instances
_memory_service: Optional[MemoryService] = None
_consolidation_service: Optional[ConsolidationService] = None
_recall_service: Optional[RecallService] = None
_consistency_service: Optional[ConsistencyService] = None
_export_service: Optional[ExportService] = None


async def initialize_repositories() -> None:
    """Initialize all repositories."""
    global _postgres_repo, _qdrant_repo, _kuzu_repo, _redis_repo
    global _memory_service, _consolidation_service, _recall_service
    global _consistency_service, _export_service
    
    # Initialize repositories
    _postgres_repo = PostgresRepository(settings.database_url)
    _qdrant_repo = QdrantRepository(settings.qdrant_url, settings.qdrant_api_key)
    _kuzu_repo = KuzuRepository("/var/lib/kuzu/memory_engine")
    _redis_repo = RedisRepository(settings.redis_url)
    
    await _postgres_repo.initialize()
    await _qdrant_repo.initialize()
    await _kuzu_repo.initialize()
    await _redis_repo.initialize()
    
    # Initialize services
    _memory_service = MemoryService(
        postgres_repo=_postgres_repo,
        qdrant_repo=_qdrant_repo,
        kuzu_repo=_kuzu_repo,
        redis_repo=_redis_repo,
    )
    
    _consolidation_service = ConsolidationService(
        memory_service=_memory_service,
        postgres_repo=_postgres_repo,
        qdrant_repo=_qdrant_repo,
        kuzu_repo=_kuzu_repo,
        redis_repo=_redis_repo,
    )
    
    _recall_service = RecallService(
        qdrant_repo=_qdrant_repo,
        postgres_repo=_postgres_repo,
        kuzu_repo=_kuzu_repo,
        redis_repo=_redis_repo,
    )
    
    _consistency_service = ConsistencyService(
        postgres_repo=_postgres_repo,
        qdrant_repo=_qdrant_repo,
        kuzu_repo=_kuzu_repo,
    )
    
    _export_service = ExportService(
        postgres_repo=_postgres_repo,
        qdrant_repo=_qdrant_repo,
        kuzu_repo=_kuzu_repo,
        redis_repo=_redis_repo,
    )
    
    await _memory_service.initialize()


async def close_repositories() -> None:
    """Close all repositories."""
    if _memory_service:
        await _memory_service.close()
    
    if _postgres_repo:
        await _postgres_repo.close()
    if _qdrant_repo:
        await _qdrant_repo.close()
    if _kuzu_repo:
        await _kuzu_repo.close()
    if _redis_repo:
        await _redis_repo.close()


# Dependency functions
async def get_memory_service() -> MemoryService:
    """Get the memory service instance."""
    if _memory_service is None:
        raise HTTPException(status_code=503, detail="Memory service not initialized")
    return _memory_service


async def get_consolidation_service() -> ConsolidationService:
    """Get the consolidation service instance."""
    if _consolidation_service is None:
        raise HTTPException(status_code=503, detail="Consolidation service not initialized")
    return _consolidation_service


async def get_recall_service() -> RecallService:
    """Get the recall service instance."""
    if _recall_service is None:
        raise HTTPException(status_code=503, detail="Recall service not initialized")
    return _recall_service


async def get_consistency_service() -> ConsistencyService:
    """Get the consistency service instance."""
    if _consistency_service is None:
        raise HTTPException(status_code=503, detail="Consistency service not initialized")
    return _consistency_service


async def get_export_service() -> ExportService:
    """Get the export service instance."""
    if _export_service is None:
        raise HTTPException(status_code=503, detail="Export service not initialized")
    return _export_service


# Repository getters (for internal use)
def get_postgres_repo() -> Optional[PostgresRepository]:
    return _postgres_repo


def get_qdrant_repo() -> Optional[QdrantRepository]:
    return _qdrant_repo


def get_kuzu_repo() -> Optional[KuzuRepository]:
    return _kuzu_repo


def get_redis_repo() -> Optional[RedisRepository]:
    return _redis_repo