"""Unit tests for memory engine services."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from uuid import uuid4

from memory_engine.models import (
    MemoryType,
    MemoryWrite,
    MemoryRead,
    MemoryResponse,
    MemoryFilter,
    MemoryUpdate,
    ConsolidationJob,
    ConsolidationReport,
    ExportRequest,
    ExportResult,
    ExportFormat,
)
from memory_engine.services.memory_service import MemoryService
from memory_engine.services.consolidation_service import ConsolidationService
from memory_engine.services.recall_service import RecallService
from memory_engine.services.consistency_service import ConsistencyService
from memory_engine.services.export_service import ExportService


class TestMemoryService:
    """Test MemoryService."""

    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories."""
        return {
            "postgres": AsyncMock(),
            "qdrant": AsyncMock(),
            "kuzu": AsyncMock(),
            "redis": AsyncMock(),
        }

    @pytest.fixture
    def memory_service(self, mock_repositories):
        """Create MemoryService with mock repositories."""
        with patch("memory_engine.services.memory_service.PostgresRepository") as mock_pg, \
             patch("memory_engine.services.memory_service.QdrantRepository") as mock_qdrant, \
             patch("memory_engine.services.memory_service.KuzuRepository") as mock_kuzu, \
             patch("memory_engine.services.memory_service.RedisRepository") as mock_redis:
            
            mock_pg.return_value = mock_repositories["postgres"]
            mock_qdrant.return_value = mock_repositories["qdrant"]
            mock_kuzu.return_value = mock_repositories["kuzu"]
            mock_redis.return_value = mock_repositories["redis"]
            
            service = MemoryService(
                postgres_repo=mock_repositories["postgres"],
                qdrant_repo=mock_repositories["qdrant"],
                kuzu_repo=mock_repositories["kuzu"],
                redis_repo=mock_repositories["redis"],
            )
            return service

    @pytest.mark.asyncio
    async def test_write_memory(self, memory_service, mock_repositories):
        """Test writing a memory."""
        # Setup
        mock_repositories["postgres"].create.return_value = MemoryResponse(
            id="mem_123",
            companion_id="comp_123",
            user_id="user_456",
            type=MemoryType.EPISODIC,
            content={"event": "User said hello"},
            importance=0.8,
            created_at=datetime.now(timezone.utc),
        )
        mock_repositories["qdrant"].upsert.return_value = True
        mock_repositories["redis"].set.return_value = True

        # Execute
        write_request = MemoryWrite(
            companion_id="comp_123",
            user_id="user_456",
            type=MemoryType.EPISODIC,
            content={"event": "User said hello"},
            importance=0.8,
        )
        result = await memory_service.write(write_request)

        # Verify
        assert result.id == "mem_123"
        assert result.type == MemoryType.EPISODIC
        mock_repositories["postgres"].create.assert_called_once()
        mock_repositories["qdrant"].upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_read_memory(self, memory_service, mock_repositories):
        """Test reading a memory."""
        # Setup
        mock_repositories["postgres"].get.return_value = MemoryResponse(
            id="mem_123",
            companion_id="comp_123",
            user_id="user_456",
            type=MemoryType.EPISODIC,
            content={"event": "User said hello"},
            importance=0.8,
            created_at=datetime.now(timezone.utc),
        )

        # Execute
        result = await memory_service.read("mem_123", "comp_123")

        # Verify
        assert result is not None
        assert result.id == "mem_123"
        mock_repositories["postgres"].get.assert_called_once_with("mem_123", "comp_123")

    @pytest.mark.asyncio
    async def test_read_memory_not_found(self, memory_service, mock_repositories):
        """Test reading a non-existent memory."""
        mock_repositories["postgres"].get.return_value = None

        result = await memory_service.read("mem_999", "comp_123")
        assert result is None

    @pytest.mark.asyncio
    async def test_query_memories(self, memory_service, mock_repositories):
        """Test querying memories."""
        mock_repositories["postgres"].query.return_value = [
            MemoryResponse(
                id=f"mem_{i}",
                companion_id="comp_123",
                user_id="user_456",
                type=MemoryType.EPISODIC,
                content={"event": f"Event {i}"},
                importance=0.5,
                created_at=datetime.now(timezone.utc),
            )
            for i in range(5)
        ]

        filter = MemoryFilter(companion_id="comp_123", limit=10)
        results = await memory_service.query(filter)

        assert len(results) == 5
        mock_repositories["postgres"].query.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_memory(self, memory_service, mock_repositories):
        """Test deleting a memory."""
        mock_repositories["postgres"].delete.return_value = True
        mock_repositories["qdrant"].delete.return_value = True
        mock_repositories["redis"].delete.return_value = True

        result = await memory_service.delete("mem_123", "comp_123")

        assert result is True
        mock_repositories["postgres"].delete.assert_called_once_with("mem_123", "comp_123")
        mock_repositories["qdrant"].delete.assert_called_once_with("mem_123")
        mock_repositories["redis"].delete.assert_called_once_with("mem_123")

    @pytest.mark.asyncio
    async def test_update_memory(self, memory_service, mock_repositories):
        """Test updating a memory."""
        mock_repositories["postgres"].update.return_value = MemoryResponse(
            id="mem_123",
            companion_id="comp_123",
            user_id="user_456",
            type=MemoryType.EPISODIC,
            content={"event": "User said hello"},
            importance=0.9,
            created_at=datetime.now(timezone.utc),
        )
        mock_repositories["qdrant"].update.return_value = True

        update = MemoryUpdate(id="mem_123", importance=0.9)
        result = await memory_service.update(update, "comp_123")

        assert result.importance == 0.9
        mock_repositories["postgres"].update.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_consolidation_candidates(self, memory_service, mock_repositories):
        """Test getting consolidation candidates."""
        from memory_engine.models import ConsolidationCandidate
        mock_repositories["postgres"].get_consolidation_candidates.return_value = [
            ConsolidationCandidate(
                memory_id=f"mem_{i}",
                content={"event": f"Event {i}"},
                importance=0.5 + i * 0.1,
                created_at=datetime.now(timezone.utc),
                topics=["topic1"],
                entities=[{"type": "entity", "value": "value"}],
            )
            for i in range(10)
        ]

        candidates = await memory_service.get_consolidation_candidates("comp_123")

        assert len(candidates) == 10
        mock_repositories["postgres"].get_consolidation_candidates.assert_called_once_with("comp_123")

    @pytest.mark.asyncio
    async def test_mark_consolidated(self, memory_service, mock_repositories):
        """Test marking memories as consolidated."""
        mock_repositories["postgres"].mark_consolidated.return_value = True

        result = await memory_service.mark_consolidated(
            source_ids=["mem_1", "mem_2"],
            semantic_ids=["sem_1", "sem_2"],
        )

        assert result is True
        mock_repositories["postgres"].mark_consolidated.assert_called_once_with(
            ["mem_1", "mem_2"], ["sem_1", "sem_2"]
        )


class TestConsolidationService:
    """Test ConsolidationService."""

    @pytest.fixture
    def consolidation_service(self):
        """Create ConsolidationService with mocks."""
        mock_memory_service = AsyncMock()
        mock_embedding_client = AsyncMock()
        mock_inference_client = AsyncMock()

        with patch("memory_engine.services.consolidation_service.MemoryService") as mock_ms:
            mock_ms.return_value = mock_memory_service
            service = ConsolidationService(
                memory_service=mock_memory_service,
                embedding_service_url="http://localhost:8001",
                inference_gateway_url="http://localhost:8000",
            )
            return service

    @pytest.mark.asyncio
    async def test_run_consolidation(self, consolidation_service):
        """Test running consolidation."""
        # Setup mocks
        from memory_engine.models import ConsolidationCandidate, ConsolidationReport
        
        consolidation_service.memory_service.get_consolidation_candidates.return_value = [
            ConsolidationCandidate(
                memory_id=f"mem_{i}",
                content={"event": f"Event {i}"},
                importance=0.7,
                created_at=datetime.now(timezone.utc),
                topics=["topic1"],
                entities=[],
            )
            for i in range(5)
        ]

        consolidation_service._generate_embeddings = AsyncMock(return_value=[
            {"memory_id": f"mem_{i}", "embedding": [0.1] * 768}
            for i in range(5)
        ])

        consolidation_service._extract_facts = AsyncMock(return_value=[
            {
                "fact": "User likes cats",
                "confidence": 0.9,
                "category": "preference",
                "entities": [{"type": "animal", "value": "cat"}],
                "source_indices": [0, 1],
            }
        ])

        consolidation_service._write_semantic_memories = AsyncMock(return_value=[
            {"id": "sem_1", "fact": "User likes cats", "confidence": 0.9}
        ])

        consolidation_service._update_knowledge_graph = AsyncMock(return_value={
            "entities_created": 1,
            "relationships_created": 0,
        })

        consolidation_service.memory_service.mark_consolidated.return_value = True

        # Execute
        report = await consolidation_service.run_consolidation("comp_123", "user_456")

        # Verify
        assert isinstance(report, ConsolidationReport)
        assert report.memories_processed == 5
        assert report.facts_extracted == 1
        assert report.semantic_memories_created == 1


class TestRecallService:
    """Test RecallService."""

    @pytest.fixture
    def recall_service(self):
        """Create RecallService with mocks."""
        mock_memory_service = AsyncMock()
        mock_embedding_client = AsyncMock()

        with patch("memory_engine.services.recall_service.MemoryService") as mock_ms:
            mock_ms.return_value = mock_memory_service
            service = RecallService(
                memory_service=mock_memory_service,
                embedding_service_url="http://localhost:8001",
            )
            return service

    @pytest.mark.asyncio
    async def test_recall(self, recall_service):
        """Test recall functionality."""
        # Setup
        from memory_engine.models import RecallResult
        
        recall_service.memory_service.query.return_value = [
            MemoryResponse(
                id=f"mem_{i}",
                companion_id="comp_123",
                user_id="user_456",
                type=MemoryType.EPISODIC,
                content={"event": f"Event {i}"},
                importance=0.5 + i * 0.1,
                created_at=datetime.now(timezone.utc),
            )
            for i in range(3)
        ]

        recall_service._generate_query_embedding = AsyncMock(return_value=[0.1] * 768)
        recall_service._score_memories = AsyncMock(return_value=[
            (0.9, "mem_2"),
            (0.7, "mem_1"),
            (0.5, "mem_0"),
        ])

        # Execute
        read_request = MemoryRead(
            companion_id="comp_123",
            user_id="user_456",
            query="What did we talk about?",
            limit=10,
        )
        result = await recall_service.recall(read_request)

        # Verify
        assert isinstance(result, RecallResult)
        assert len(result.memories) == 3
        assert result.memories[0].id == "mem_2"  # Highest score first


class TestConsistencyService:
    """Test ConsistencyService."""

    @pytest.fixture
    def consistency_service(self):
        """Create ConsistencyService with mocks."""
        mock_memory_service = AsyncMock()

        with patch("memory_engine.services.consistency_service.MemoryService") as mock_ms:
            mock_ms.return_value = mock_memory_service
            service = ConsistencyService(memory_service=mock_memory_service)
            return service

    @pytest.mark.asyncio
    async def test_validate_all(self, consistency_service):
        """Test running all consistency checks."""
        # Setup
        consistency_service._check_contradictions = AsyncMock(return_value=[])
        consistency_service._check_duplicates = AsyncMock(return_value=[])
        consistency_service._check_orphaned = AsyncMock(return_value=[])
        consistency_service._check_ttl = AsyncMock(return_value=[])

        # Execute
        report = await consistency_service.validate_all("comp_123")

        # Verify
        assert report.total_issues == 0
        assert len(report.checks_run) == 4


class TestExportService:
    """Test ExportService."""

    @pytest.fixture
    def export_service(self):
        """Create ExportService with mocks."""
        mock_memory_service = AsyncMock()

        with patch("memory_engine.services.export_service.MemoryService") as mock_ms:
            mock_ms.return_value = mock_memory_service
            service = ExportService(
                memory_service=mock_memory_service,
                redis_url="redis://localhost:6379/0",
            )
            return service

    @pytest.mark.asyncio
    async def test_export_all_json(self, export_service):
        """Test exporting all memories as JSON."""
        # Setup
        export_service.memory_service.query.return_value = [
            MemoryResponse(
                id=f"mem_{i}",
                companion_id="comp_123",
                user_id="user_456",
                type=MemoryType.EPISODIC,
                content={"event": f"Event {i}"},
                importance=0.5,
                created_at=datetime.now(timezone.utc),
            )
            for i in range(5)
        ]

        export_service.redis = AsyncMock()
        export_service.redis.setex = AsyncMock(return_value=True)

        # Execute
        request = ExportRequest(
            companion_id="comp_123",
            user_id="user_456",
            formats=[ExportFormat.JSON],
        )
        result = await export_service.export_all(request)

        # Verify
        assert result.format == ExportFormat.JSON
        assert result.memory_count == 5
        assert result.status == "completed"
        export_service.redis.setex.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])