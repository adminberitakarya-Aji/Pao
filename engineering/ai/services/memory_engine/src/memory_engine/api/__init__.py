"""Memory Engine API package."""

from .routes import router as memory_router
from .dependencies import (
    initialize_repositories,
    close_repositories,
    get_memory_service,
    get_consolidation_service,
    get_recall_service,
    get_consistency_service,
    get_export_service,
)

__all__ = [
    "memory_router",
    "initialize_repositories",
    "close_repositories",
    "get_memory_service",
    "get_consolidation_service",
    "get_recall_service",
    "get_consistency_service",
    "get_export_service",
]