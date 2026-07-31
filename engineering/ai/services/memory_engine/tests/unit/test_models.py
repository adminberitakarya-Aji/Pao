"""Unit tests for memory engine models."""

import pytest
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
    ConsolidationCandidate,
    ConsistencyCheck,
    ConsistencyReport,
    ConsistencyIssue,
    ConsistencyIssueType,
    ConsistencySeverity,
    ExportRequest,
    ExportResult,
    ExportFormat,
)


class TestMemoryType:
    """Test MemoryType enum."""

    def test_memory_types_exist(self):
        """Test all memory types are defined."""
        assert MemoryType.EPISODIC.value == "episodic"
        assert MemoryType.SEMANTIC.value == "semantic"
        assert MemoryType.EMOTIONAL.value == "emotional"
        assert MemoryType.RELATIONSHIP.value == "relationship"
        assert MemoryType.TIMELINE.value == "timeline"
        assert MemoryType.PREFERENCE.value == "preference"

    def test_memory_type_from_string(self):
        """Test creating MemoryType from string."""
        assert MemoryType("episodic") == MemoryType.EPISODIC
        assert MemoryType("semantic") == MemoryType.SEMANTIC


class TestMemoryWrite:
    """Test MemoryWrite model."""

    def test_memory_write_creation(self):
        """Test creating a MemoryWrite."""
        write = MemoryWrite(
            companion_id="comp_123",
            user_id="user_456",
            type=MemoryType.EPISODIC,
            content={"event": "User said hello", "timestamp": "2024-01-01T10:00:00Z"},
            importance=0.8,
            tags=["greeting", "first_meeting"],
        )
        assert write.companion_id == "comp_123"
        assert write.user_id == "user_456"
        assert write.type == MemoryType.EPISODIC
        assert write.importance == 0.8
        assert write.tags == ["greeting", "first_meeting"]

    def test_memory_write_defaults(self):
        """Test MemoryWrite defaults."""
        write = MemoryWrite(
            companion_id="comp_123",
            user_id="user_456",
            type=MemoryType.SEMANTIC,
            content={"fact": "User likes cats"},
        )
        assert write.importance == 0.5
        assert write.tags == []
        assert write.ttl_days is None
        assert write.metadata == {}

    def test_memory_write_validation(self):
        """Test MemoryWrite validation."""
        with pytest.raises(ValueError):
            MemoryWrite(
                companion_id="comp_123",
                user_id="user_456",
                type=MemoryType.EPISODIC,
                content={"event": "test"},
                importance=1.5,  # Invalid: > 1.0
            )

        with pytest.raises(ValueError):
            MemoryWrite(
                companion_id="comp_123",
                user_id="user_456",
                type=MemoryType.EPISODIC,
                content={"event": "test"},
                importance=-0.1,  # Invalid: < 0
            )


class TestMemoryRead:
    """Test MemoryRead model."""

    def test_memory_read_creation(self):
        """Test creating a MemoryRead."""
        read = MemoryRead(
            companion_id="comp_123",
            user_id="user_456",
            query="What did we talk about?",
            types=[MemoryType.EPISODIC, MemoryType.SEMANTIC],
            limit=20,
            min_importance=0.3,
        )
        assert read.companion_id == "comp_123"
        assert read.query == "What did we talk about?"
        assert read.limit == 20
        assert read.min_importance == 0.3

    def test_memory_read_defaults(self):
        """Test MemoryRead defaults."""
        read = MemoryRead(
            companion_id="comp_123",
            user_id="user_456",
            query="test",
        )
        assert read.limit == 10
        assert read.min_importance == 0.0
        assert read.types is None
        assert read.filters == {}


class TestMemoryResponse:
    """Test MemoryResponse model."""

    def test_memory_response_creation(self):
        """Test creating a MemoryResponse."""
        response = MemoryResponse(
            id="mem_123",
            companion_id="comp_123",
            user_id="user_456",
            type=MemoryType.EPISODIC,
            content={"event": "User said hello"},
            importance=0.8,
            created_at=datetime.now(timezone.utc),
            tags=["greeting"],
        )
        assert response.id == "mem_123"
        assert response.type == MemoryType.EPISODIC
        assert response.importance == 0.8

    def test_memory_response_optional_fields(self):
        """Test MemoryResponse optional fields."""
        response = MemoryResponse(
            id="mem_123",
            companion_id="comp_123",
            user_id="user_456",
            type=MemoryType.SEMANTIC,
            content={"fact": "User likes cats"},
            importance=0.5,
            created_at=datetime.now(timezone.utc),
        )
        assert response.updated_at is None
        assert response.version == 1
        assert response.consolidated is False
        assert response.consolidated_into is None
        assert response.embedding is None


class TestMemoryFilter:
    """Test MemoryFilter model."""

    def test_memory_filter_creation(self):
        """Test creating a MemoryFilter."""
        filter = MemoryFilter(
            companion_id="comp_123",
            user_id="user_456",
            types=[MemoryType.EPISODIC],
            limit=50,
            offset=10,
        )
        assert filter.companion_id == "comp_123"
        assert filter.limit == 50
        assert filter.offset == 10

    def test_memory_filter_defaults(self):
        """Test MemoryFilter defaults."""
        filter = MemoryFilter(companion_id="comp_123")
        assert filter.limit == 100
        assert filter.offset == 0
        assert filter.types is None
        assert filter.min_importance is None
        assert filter.tags is None
        assert filter.date_from is None
        assert filter.date_to is None


class TestMemoryUpdate:
    """Test MemoryUpdate model."""

    def test_memory_update_creation(self):
        """Test creating a MemoryUpdate."""
        update = MemoryUpdate(
            id="mem_123",
            importance=0.9,
            tags=["updated", "important"],
            metadata={"source": "user_feedback"},
        )
        assert update.id == "mem_123"
        assert update.importance == 0.9
        assert update.tags == ["updated", "important"]
        assert update.metadata == {"source": "user_feedback"}

    def test_memory_update_partial(self):
        """Test partial MemoryUpdate."""
        update = MemoryUpdate(id="mem_123")
        assert update.importance is None
        assert update.tags is None
        assert update.content is None


class TestConsolidationModels:
    """Test consolidation models."""

    def test_consolidation_candidate(self):
        """Test ConsolidationCandidate."""
        candidate = ConsolidationCandidate(
            memory_id="mem_123",
            content={"event": "User mentioned cats"},
            importance=0.7,
            created_at=datetime.now(timezone.utc),
            topics=["pets", "cats"],
            entities=[{"type": "animal", "value": "cat"}],
        )
        assert candidate.memory_id == "mem_123"
        assert candidate.importance == 0.7
        assert "cats" in candidate.topics

    def test_consolidation_job(self):
        """Test ConsolidationJob."""
        job = ConsolidationJob(
            id="consol_123",
            companion_id="comp_123",
            user_id="user_456",
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        assert job.id == "consol_123"
        assert job.status == "running"
        assert job.memories_processed == 0
        assert job.facts_extracted == 0

    def test_consolidation_report(self):
        """Test ConsolidationReport."""
        report = ConsolidationReport(
            job_id="consol_123",
            companion_id="comp_123",
            user_id="user_456",
            memories_processed=100,
            facts_extracted=25,
            semantic_memories_created=20,
            graph_updates=15,
            duration_ms=5000,
            status="completed",
        )
        assert report.memories_processed == 100
        assert report.facts_extracted == 25
        assert report.status == "completed"


class TestConsistencyModels:
    """Test consistency models."""

    def test_consistency_issue(self):
        """Test ConsistencyIssue."""
        issue = ConsistencyIssue(
            id="issue_123",
            type=ConsistencyIssueType.CONTRADICTION,
            severity=ConsistencySeverity.HIGH,
            description="Two memories contradict each other",
            memory_ids=["mem_1", "mem_2"],
            suggested_resolution="Keep the more recent memory",
        )
        assert issue.type == ConsistencyIssueType.CONTRADICTION
        assert issue.severity == ConsistencySeverity.HIGH
        assert len(issue.memory_ids) == 2

    def test_consistency_check(self):
        """Test ConsistencyCheck."""
        check = ConsistencyCheck(
            id="check_123",
            companion_id="comp_123",
            check_type="contradiction_detection",
            status="completed",
            issues_found=3,
        )
        assert check.check_type == "contradiction_detection"
        assert check.issues_found == 3

    def test_consistency_report(self):
        """Test ConsistencyReport."""
        issue = ConsistencyIssue(
            id="issue_1",
            type=ConsistencyIssueType.DUPLICATE,
            severity=ConsistencySeverity.LOW,
            description="Duplicate memory",
            memory_ids=["mem_1", "mem_2"],
        )
        report = ConsistencyReport(
            companion_id="comp_123",
            checked_at=datetime.now(timezone.utc),
            checks_run=["contradiction_detection", "duplicate_detection"],
            total_issues=1,
            auto_resolved=0,
            requires_user_review=1,
            issues=[issue],
            duration_ms=1000,
        )
        assert report.total_issues == 1
        assert len(report.issues) == 1


class TestExportModels:
    """Test export models."""

    def test_export_request(self):
        """Test ExportRequest."""
        request = ExportRequest(
            companion_id="comp_123",
            user_id="user_456",
            formats=[ExportFormat.JSON, ExportFormat.JSON_LD],
            include_types=[MemoryType.EPISODIC, MemoryType.SEMANTIC],
            encryption_key="secret_key",
        )
        assert request.companion_id == "comp_123"
        assert ExportFormat.JSON in request.formats
        assert request.encryption_key == "secret_key"

    def test_export_result(self):
        """Test ExportResult."""
        result = ExportResult(
            export_id="export_123",
            companion_id="comp_123",
            format=ExportFormat.JSON,
            status="completed",
            file_url="https://example.com/export.json",
            memory_count=100,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc),
        )
        assert result.export_id == "export_123"
        assert result.status == "completed"
        assert result.memory_count == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])