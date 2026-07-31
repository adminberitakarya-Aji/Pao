"""Memory Engine API Routes."""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field

from ..models import (
    MemoryType,
    MemoryWrite,
    MemoryRead,
    MemoryUpdate,
    MemoryDelete,
    MemoryResponse,
    MemoryFilter,
    RecallQuery,
    RecallResponse,
    RecallContext,
    ConsolidationReport,
    ConsolidationCandidate,
    ConsistencyReport,
)
from .dependencies import (
    get_memory_service,
    get_consolidation_service,
    get_recall_service,
    get_consistency_service,
    get_export_service,
)
from ..services import (
    MemoryService,
    ConsolidationService,
    RecallService,
    ConsistencyService,
    ExportService,
)

router = APIRouter(prefix="/api/v1/memory", tags=["memory"])


# Request/Response models
class WriteMemoryRequest(BaseModel):
    companion_id: str = Field(..., description="Companion ID")
    user_id: str = Field(..., description="User ID")
    type: MemoryType = Field(..., description="Memory type")
    content: dict = Field(..., description="Memory content")
    source_message_ids: Optional[List[str]] = Field(default=None)
    metadata: Optional[dict] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)
    importance: float = Field(default=0.5, ge=0, le=1)


class RecallRequest(BaseModel):
    companion_id: str = Field(..., description="Companion ID")
    user_id: Optional[str] = Field(default=None)
    query: str = Field(..., description="Natural language query")
    context: Optional[RecallContext] = Field(default=None)
    filters: Optional[MemoryFilter] = Field(default=None)
    limit: int = Field(default=10, ge=1, le=100)
    diversify: bool = Field(default=True)


class UpdateMemoryRequest(BaseModel):
    memory_id: str = Field(..., description="Memory ID")
    companion_id: str = Field(..., description="Companion ID")
    updates: dict = Field(..., description="Fields to update")
    reason: str = Field(..., description="Reason for update")


class DeleteMemoryRequest(BaseModel):
    memory_id: str = Field(..., description="Memory ID")
    companion_id: str = Field(..., description="Companion ID")
    verification: str = Field(default="full")
    confirm: bool = Field(default=False)


class BulkDeleteRequest(BaseModel):
    companion_id: str = Field(..., description="Companion ID")
    scope: dict = Field(..., description="Deletion scope (types, date_range, topics, tags)")
    confirm: bool = Field(default=False)


class ExportRequest(BaseModel):
    companion_id: str = Field(..., description="Companion ID")
    user_id: str = Field(..., description="User ID")
    formats: List[str] = Field(..., description="Export formats: json-ld, json, timeline, pdf, audio, audit_log")
    include_types: Optional[List[MemoryType]] = Field(default=None)
    encryption_key: Optional[str] = Field(default=None)


class ConsolidationRequest(BaseModel):
    companion_id: str = Field(..., description="Companion ID")
    user_id: str = Field(..., description="User ID")


# Memory CRUD endpoints
@router.post("/write", response_model=MemoryResponse, summary="Write a new memory")
async def write_memory(
    request: WriteMemoryRequest,
    memory_service: MemoryService = Depends(get_memory_service),
):
    """Write a new memory to the appropriate storage backends."""
    write_request = MemoryWrite(
        companion_id=request.companion_id,
        user_id=request.user_id,
        type=request.type,
        content=request.content,
        source_message_ids=request.source_message_ids,
        metadata=request.metadata,
        tags=request.tags,
        importance=request.importance,
    )
    return await memory_service.write(write_request)


@router.post("/read", response_model=Optional[MemoryResponse], summary="Read a memory by ID")
async def read_memory(
    companion_id: str = Query(..., description="Companion ID"),
    memory_id: str = Query(..., description="Memory ID"),
    memory_type: MemoryType = Query(..., description="Memory type"),
    memory_service: MemoryService = Depends(get_memory_service),
):
    """Read a memory by ID with caching."""
    read_request = MemoryRead(
        memory_id=memory_id,
        companion_id=companion_id,
        type=memory_type,
    )
    result = await memory_service.read(read_request)
    if not result:
        raise HTTPException(status_code=404, detail="Memory not found")
    return result


@router.post("/recall", response_model=RecallResponse, summary="Context-aware memory recall")
async def recall_memory(
    request: RecallRequest,
    recall_service: RecallService = Depends(get_recall_service),
):
    """Perform context-aware memory recall with multi-strategy retrieval and reranking."""
    query = RecallQuery(
        companion_id=request.companion_id,
        user_id=request.user_id,
        query=request.query,
        context=request.context,
        filters=request.filters,
        limit=request.limit,
        diversify=request.diversify,
    )
    return await recall_service.recall(query)


@router.put("/update", response_model=MemoryResponse, summary="Update a memory (reconsolidation)")
async def update_memory(
    request: UpdateMemoryRequest,
    memory_service: MemoryService = Depends(get_memory_service),
):
    """Update a memory with version control (reconsolidation)."""
    update_request = MemoryUpdate(
        memory_id=request.memory_id,
        companion_id=request.companion_id,
        updates=request.updates,
        reason=request.reason,
    )
    return await memory_service.update(update_request)


@router.delete("/delete", summary="Delete a memory with verification")
async def delete_memory(
    request: DeleteMemoryRequest,
    memory_service: MemoryService = Depends(get_memory_service),
):
    """Delete a memory with verification."""
    delete_request = MemoryDelete(
        memory_id=request.memory_id,
        companion_id=request.companion_id,
        verification=request.verification,
        confirm=request.confirm,
    )
    return await memory_service.delete(delete_request)


@router.delete("/bulk", summary="Bulk delete memories by scope")
async def bulk_delete(
    request: BulkDeleteRequest,
    memory_service: MemoryService = Depends(get_memory_service),
):
    """Bulk delete memories by scope (topic, time, type, etc.)."""
    return await memory_service.bulk_delete(
        companion_id=request.companion_id,
        scope=request.scope,
        confirm=request.confirm,
    )


# Consolidation endpoints
@router.post("/consolidate", response_model=ConsolidationReport, summary="Run memory consolidation")
async def run_consolidation(
    request: ConsolidationRequest,
    consolidation_service: ConsolidationService = Depends(get_consolidation_service),
):
    """Run episodic to semantic memory consolidation for a companion."""
    return await consolidation_service.run_consolidation(
        companion_id=request.companion_id,
        user_id=request.user_id,
    )


@router.get("/consolidate/status", summary="Get consolidation status")
async def get_consolidation_status(
    companion_id: str = Query(..., description="Companion ID"),
    consolidation_service: ConsolidationService = Depends(get_consolidation_service),
):
    """Get current consolidation progress/status."""
    return await consolidation_service.get_consolidation_status(companion_id)


@router.get("/consolidate/candidates", response_model=List[ConsolidationCandidate], summary="Get consolidation candidates")
async def get_consolidation_candidates(
    companion_id: str = Query(..., description="Companion ID"),
    memory_service: MemoryService = Depends(get_memory_service),
):
    """Get episodic memories ready for consolidation."""
    return await memory_service.get_consolidation_candidates(companion_id)


# Consistency endpoints
@router.post("/consistency/validate", response_model=ConsistencyReport, summary="Run consistency validation")
async def validate_consistency(
    companion_id: str = Query(..., description="Companion ID"),
    consistency_service: ConsistencyService = Depends(get_consistency_service),
):
    """Run all consistency checks for a companion."""
    return await consistency_service.validate_all(companion_id)


@router.get("/consistency/issues", response_model=List[dict], summary="Get active consistency issues")
async def get_consistency_issues(
    companion_id: str = Query(..., description="Companion ID"),
    severity: Optional[str] = Query(default=None, description="Filter by severity"),
    consistency_service: ConsistencyService = Depends(get_consistency_service),
):
    """Get active consistency issues for a companion."""
    issues = await consistency_service.get_active_issues(companion_id, severity)
    return [issue.model_dump() for issue in issues]


@router.post("/consistency/resolve", summary="Resolve a consistency issue")
async def resolve_consistency_issue(
    issue_id: str = Body(..., embed=True),
    resolution: str = Body(..., embed=True),
    resolved_by: str = Body(..., embed=True),
    consistency_service: ConsistencyService = Depends(get_consistency_service),
):
    """Manually resolve a consistency issue."""
    success = await consistency_service.resolve_issue(issue_id, resolution, resolved_by)
    return {"success": success}


# Export endpoints
@router.post("/export", summary="Export all memories")
async def export_memories(
    request: ExportRequest,
    export_service: ExportService = Depends(get_export_service),
):
    """Export all memories for a companion in specified formats."""
    return await export_service.export_all(
        companion_id=request.companion_id,
        user_id=request.user_id,
        formats=request.formats,
        include_types=request.include_types,
        encryption_key=request.encryption_key,
    )


@router.get("/export/{export_id}/status", summary="Get export status")
async def get_export_status(
    export_id: str,
    export_service: ExportService = Depends(get_export_service),
):
    """Get status of an export job."""
    return await export_service.get_export_status(export_id)


# Stats endpoint
@router.get("/stats", summary="Get memory statistics")
async def get_memory_stats(
    companion_id: str = Query(..., description="Companion ID"),
    memory_service: MemoryService = Depends(get_memory_service),
):
    """Get memory statistics for a companion."""
    return await memory_service.get_memory_stats(companion_id)


# Health check
@router.get("/health", summary="Health check")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "memory-engine"}