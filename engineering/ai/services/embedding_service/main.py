"""
PAO Embedding Service - Vector Embedding Generation
Generates embeddings for text using various models (BGE, E5, OpenAI, etc.)
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
import structlog
import time

from pao_shared import (
    get_settings,
    setup_tracing,
    get_logger,
    EmbeddingRequest,
    EmbeddingResponse,
    HealthResponse,
)

settings = get_settings()
logger = get_logger(__name__)
tracer = setup_tracing("embedding-service")


class EmbeddingModel:
    """Embedding model wrapper."""
    
    def __init__(self, model_id: str, name: str, provider: str, dimensions: int, max_tokens: int):
        self.model_id = model_id
        self.name = name
        self.provider = provider
        self.dimensions = dimensions
        self.max_tokens = max_tokens
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts."""
        # Placeholder - in production, call actual embedding model
        # This would use sentence-transformers, vLLM, or external APIs
        return [[0.1] * self.dimensions for _ in texts]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    setup_tracing("embedding-service")
    logger.info("Starting Embedding Service")
    
    # Initialize models
    app.state.models = {
        "bge-large-en": EmbeddingModel(
            model_id="bge-large-en",
            name="BGE Large EN",
            provider="local",
            dimensions=1024,
            max_tokens=512,
        ),
        "e5-large-v2": EmbeddingModel(
            model_id="e5-large-v2",
            name="E5 Large v2",
            provider="local",
            dimensions=1024,
            max_tokens=512,
        ),
        "text-embedding-3-large": EmbeddingModel(
            model_id="text-embedding-3-large",
            name="OpenAI text-embedding-3-large",
            provider="openai",
            dimensions=3072,
            max_tokens=8191,
        ),
        "text-embedding-3-small": EmbeddingModel(
            model_id="text-embedding-3-small",
            name="OpenAI text-embedding-3-small",
            provider="openai",
            dimensions=1536,
            max_tokens=8191,
        ),
    }
    
    yield
    
    logger.info("Shutting down Embedding Service")


app = FastAPI(
    title="PAO Embedding Service",
    description="Vector Embedding Generation for RAG & Semantic Search",
    version="1.0.0",
    lifespan=lifespan,
)


class EmbedRequest(BaseModel):
    """Embedding request."""
    texts: List[str] = Field(..., min_length=1, max_length=100)
    model: Optional[str] = Field(default="bge-large-en")
    dimensions: Optional[int] = Field(default=None, ge=1, le=4096)
    normalize: bool = Field(default=True)


@app.post("/v1/embeddings", response_model=EmbeddingResponse)
async def create_embeddings(request: EmbedRequest):
    """Generate embeddings for input texts."""
    start_time = time.time()
    
    model = app.state.models.get(request.model)
    if not model:
        raise HTTPException(404, f"Model not found: {request.model}")
    
    # Truncate texts if needed
    truncated_texts = [text[:model.max_tokens] for text in request.texts]
    
    # Generate embeddings
    embeddings = await model.embed(truncated_texts)
    
    # Optionally reduce dimensions
    if request.dimensions and request.dimensions < model.dimensions:
        embeddings = [emb[:request.dimensions] for emb in embeddings]
    
    # Normalize if requested
    if request.normalize:
        import math
        embeddings = [
            [v / math.sqrt(sum(x*x for x in emb)) for v in emb]
            for emb in embeddings
        ]
    
    latency_ms = int((time.time() - start_time) * 1000)
    
    return EmbeddingResponse(
        embeddings=embeddings,
        model_used=request.model,
        tokens_used=sum(len(t.split()) for t in truncated_texts),
        cost_estimate=0.0,  # Local models are free
    )


@app.get("/v1/models")
async def list_models():
    """List available embedding models."""
    return {
        "models": [
            {
                "id": m.model_id,
                "name": m.name,
                "provider": m.provider,
                "dimensions": m.dimensions,
                "max_tokens": m.max_tokens,
            }
            for m in app.state.models.values()
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service="embedding-service",
        version="1.0.0",
        checks={"models_loaded": len(app.state.models)},
    )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.environment == "development",
    )