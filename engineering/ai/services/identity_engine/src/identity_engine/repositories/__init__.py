"""Repository layer for Identity Engine."""

from .base import BaseRepository
from .memory import MemoryRepository
from .postgres import PostgresRepository

__all__ = [
    "BaseRepository",
    "MemoryRepository", 
    "PostgresRepository",
]