"""
PAO Inference Gateway - LLM Routing & Streaming Service
Routes requests to appropriate models, handles streaming, fallbacks, and cost optimization.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import AsyncGenerator, Optional, List, Dict, Any, Literal
import structlog
import os
from uuid import uuid4

from pao_shared.config import get_settings
from pao_shared.observability import setup_tracing, get_logger
from pao_shared.models import InferenceRequest, InferenceResponse, ModelConfig

logger = structlog.get_logger(__name__)
settings = get_settings()


class ModelRouter:
    """Routes inference requests to optimal models based on task type, cost, latency."""
    
    def __init__(self):
        self.models: Dict[str, ModelConfig] = {}
        self.fallback_chains: Dict[str, List[str]] = {}
    
    async def route_request(self, request: InferenceRequest) -> ModelConfig:
        """Select best model based on request characteristics."""
        # Task-based routing
        if request.task_type == "reasoning":
            return await self._get_best_model("reasoning", request.max_cost_per_token)
        elif request.task_type == "creative":
            return await self._get_best_model("creative", request.max_cost_per_token)
        elif request.task_type == "coding":
            return await self._get_best_model("coding", request.max_cost_per_token)
        elif request.task_type == "embedding":
            return await self._get_best_model("embedding", request.max_cost_per_token)
        
        # Default to balanced model
        return await self._get_best_model("balanced", request.max_cost_per_token)
    
    async def _get_best_model(self, category: str, max_cost: Optional[float]) -> ModelConfig:
        """Get best available model for category within cost budget."""
        candidates = [m for m in self.models.values() if m.category == category]
        if max_cost:
            candidates = [m for m in candidates if m.cost_per_token <= max_cost]
        
        if not candidates:
            # Try fallback chain
            for fallback in self.fallback_chains.get(category, []):
                if fallback in self.models:
                    return self.models[fallback]
            raise HTTPException(503, f"No available models for category: {category}")
        
        # Sort by quality score (descending) then cost (ascending)
        candidates.sort(key=lambda m: (-m.quality_score, m.cost_per_token))
        return candidates[0]
    
    async def stream_inference(
        self, 
        model: ModelConfig, 
        request: InferenceRequest
    ) -> AsyncGenerator[str, None]:
        """Stream inference from selected model."""
        # Implementation would call vLLM, TGI, or external APIs
        # This is a simplified version
        async for chunk in self._call_model(model, request, stream=True):
            yield chunk
    
    async def _call_model(
        self, 
        model: ModelConfig, 
        request: InferenceRequest, 
        stream: bool
    ) -> AsyncGenerator[str, None]:
        """Call underlying model service."""
        # Placeholder for actual model calling logic
        yield f"data: {model.id} response for: {request.prompt[:50]}...\n\n"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    setup_tracing("inference-gateway")
    logger.info("Starting Inference Gateway")
    
    # Initialize model router
    app.state.router = ModelRouter()
    
    # Load model configurations from config service
    await load_model_configs(app.state.router)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Inference Gateway")


app = FastAPI(
    title="PAO Inference Gateway",
    description="LLM Routing, Streaming & Cost Optimization",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def load_model_configs(router: ModelRouter):
    """Load model configurations from config service."""
    # In production, fetch from config service or database
    router.models = {
        "gpt-4-turbo": ModelConfig(
            id="gpt-4-turbo",
            name="GPT-4 Turbo",
            provider="openai",
            category="reasoning",
            quality_score=0.95,
            cost_per_token=0.00003,
            max_tokens=128000,
            supports_streaming=True,
            supports_functions=True,
        ),
        "claude-3-opus": ModelConfig(
            id="claude-3-opus",
            name="Claude 3 Opus",
            provider="anthropic",
            category="reasoning",
            quality_score=0.97,
            cost_per_token=0.000075,
            max_tokens=200000,
            supports_streaming=True,
            supports_functions=True,
        ),
        "mixtral-8x7b": ModelConfig(
            id="mixtral-8x7b",
            name="Mixtral 8x7B",
            provider="local",
            category="balanced",
            quality_score=0.85,
            cost_per_token=0.000001,
            max_tokens=32000,
            supports_streaming=True,
            supports_functions=False,
        ),
        "llama-3-70b": ModelConfig(
            id="llama-3-70b",
            name="Llama 3 70B",
            provider="local",
            category="creative",
            quality_score=0.88,
            cost_per_token=0.000002,
            max_tokens=8000,
            supports_streaming=True,
            supports_functions=False,
        ),
        "bge-large-en": ModelConfig(
            id="bge-large-en",
            name="BGE Large EN",
            provider="local",
            category="embedding",
            quality_score=0.92,
            cost_per_token=0.0000001,
            max_tokens=512,
            supports_streaming=False,
            supports_functions=False,
        ),
    }
    
    router.fallback_chains = {
        "reasoning": ["gpt-4-turbo", "claude-3-opus", "mixtral-8x7b"],
        "creative": ["llama-3-70b", "mixtral-8x7b", "gpt-4-turbo"],
        "coding": ["gpt-4-turbo", "claude-3-opus", "mixtral-8x7b"],
        "balanced": ["mixtral-8x7b", "gpt-4-turbo", "llama-3-70b"],
        "embedding": ["bge-large-en"],
    }
    
    logger.info("Model configs loaded", count=len(router.models))


class StreamRequest(BaseModel):
    """Streaming inference request."""
    prompt: str = Field(..., min_length=1, max_length=100000)
    task_type: Literal["reasoning", "creative", "coding", "balanced", "embedding"] = "balanced"
    max_tokens: int = Field(2048, ge=1, le=128000)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    top_p: float = Field(0.9, ge=0.0, le=1.0)
    max_cost_per_token: Optional[float] = Field(None, ge=0)
    model_preference: Optional[str] = None
    stop_sequences: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


@app.post("/v1/inference/stream")
async def stream_inference(request: StreamRequest):
    """Stream inference from routed model."""
    router: ModelRouter = app.state.router
    
    # Convert to internal request
    internal_request = InferenceRequest(
        prompt=request.prompt,
        task_type=request.task_type,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        top_p=request.top_p,
        max_cost_per_token=request.max_cost_per_token,
        stop_sequences=request.stop_sequences,
        metadata=request.metadata,
    )
    
    # Route to best model
    model = await router.route_request(internal_request)
    logger.info("Model selected", model=model.id, task_type=request.task_type)
    
    async def generate():
        async for chunk in router.stream_inference(model, internal_request):
            yield chunk
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "X-Model-Used": model.id,
            "X-Model-Provider": model.provider,
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.post("/v1/inference", response_model=InferenceResponse)
async def inference(request: StreamRequest):
    """Non-streaming inference."""
    router: ModelRouter = app.state.router
    
    internal_request = InferenceRequest(
        prompt=request.prompt,
        task_type=request.task_type,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        top_p=request.top_p,
        max_cost_per_token=request.max_cost_per_token,
        stop_sequences=request.stop_sequences,
        metadata=request.metadata,
    )
    
    model = await router.route_request(internal_request)
    
    # Collect full response
    full_response = ""
    async for chunk in router.stream_inference(model, internal_request):
        if chunk.startswith("data: "):
            full_response += chunk[6:].strip()
    
    return InferenceResponse(
        text=full_response,
        model_used=model.id,
        provider=model.provider,
        tokens_used=len(full_response.split()),  # Approximate
        cost_estimate=len(full_response.split()) * model.cost_per_token,
    )


@app.get("/v1/models")
async def list_models():
    """List available models."""
    router: ModelRouter = app.state.router
    return {
        "models": [
            {
                "id": m.id,
                "name": m.name,
                "provider": m.provider,
                "category": m.category,
                "quality_score": m.quality_score,
                "cost_per_token": m.cost_per_token,
                "max_tokens": m.max_tokens,
                "supports_streaming": m.supports_streaming,
                "supports_functions": m.supports_functions,
            }
            for m in router.models.values()
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "inference-gateway"}


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
        port=8000,
        reload=settings.environment == "development",
        workers=1 if settings.environment == "development" else 4,
    )