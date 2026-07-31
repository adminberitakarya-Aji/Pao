"""Engine Clients for communicating with AI engines."""

import logging
import time
from typing import Optional, Dict, Any, List
from uuid import UUID
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from companion_runtime.config import settings

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Simple circuit breaker implementation."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half-open

    def record_success(self):
        self.failure_count = 0
        self.state = "closed"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

    def can_execute(self) -> bool:
        if self.state == "closed":
            return True
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half-open"
                return True
            return False
        # half-open
        return True


class EngineClient:
    """Base client for communicating with an AI engine."""

    def __init__(
        self,
        base_url: str,
        service_name: str,
        timeout: float = 30.0,
        max_connections: int = 100,
        max_keepalive: int = 20,
    ):
        self.base_url = base_url.rstrip("/")
        self.service_name = service_name
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=settings.circuit_breaker_failure_threshold,
            recovery_timeout=settings.circuit_breaker_recovery_timeout,
        )
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout, connect=5.0),
            limits=httpx.Limits(max_connections=max_connections, max_keepalive_connections=max_keepalive),
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        reraise=True,
    )
    async def _request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> httpx.Response:
        """Make HTTP request with circuit breaker and retry logic."""
        if not self.circuit_breaker.can_execute():
            raise ConnectionError(f"Circuit breaker open for {self.service_name}")

        headers = {}
        if request_id:
            headers["X-Request-ID"] = request_id

        try:
            response = await self.client.request(
                method=method,
                url=path,
                json=json,
                params=params,
                headers=headers,
            )
            response.raise_for_status()
            self.circuit_breaker.record_success()
            return response
        except Exception as e:
            self.circuit_breaker.record_failure()
            logger.error(f"{self.service_name} request failed: {e}", extra={"request_id": request_id})
            raise

    async def get(self, path: str, params: Optional[Dict[str, Any]] = None, request_id: Optional[str] = None) -> Dict[str, Any]:
        """GET request."""
        response = await self._request("GET", path, params=params, request_id=request_id)
        return response.json()

    async def post(self, path: str, json: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """POST request."""
        response = await self._request("POST", path, json=json, request_id=request_id)
        return response.json()

    async def patch(self, path: str, json: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """PATCH request."""
        response = await self._request("PATCH", path, json=json, request_id=request_id)
        return response.json()

    async def delete(self, path: str, request_id: Optional[str] = None) -> Dict[str, Any]:
        """DELETE request."""
        response = await self._request("DELETE", path, request_id=request_id)
        return response.json()

    async def health_check(self) -> Dict[str, Any]:
        """Check engine health."""
        try:
            return await self.get("/health/live", request_id="health-check")
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    async def close(self):
        """Close the client."""
        await self.client.aclose()


class IdentityEngineClient(EngineClient):
    """Client for Identity Engine."""

    def __init__(self):
        super().__init__(
            base_url=settings.identity_engine_url,
            service_name="identity-engine",
            timeout=settings.http_timeout,
            max_connections=settings.http_max_connections,
            max_keepalive=settings.http_max_keepalive,
        )

    async def get_context(self, companion_id: UUID, request_id: Optional[str] = None) -> Dict[str, Any]:
        """Get identity context for a companion."""
        return await self.get(f"/api/v1/identity/{companion_id}", request_id=request_id)

    async def get_fingerprint(self, companion_id: UUID, request_id: Optional[str] = None) -> Dict[str, Any]:
        """Get companion fingerprint."""
        return await self.get(f"/api/v1/identity/{companion_id}/fingerprint", request_id=request_id)

    async def evolve_identity(
        self,
        companion_id: UUID,
        evolution_data: Dict[str, Any],
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Evolve companion identity."""
        return await self.post(f"/api/v1/identity/{companion_id}/evolve", json=evolution_data, request_id=request_id)


class MemoryEngineClient(EngineClient):
    """Client for Memory Engine."""

    def __init__(self):
        super().__init__(
            base_url=settings.memory_engine_url,
            service_name="memory-engine",
            timeout=settings.http_timeout,
            max_connections=settings.http_max_connections,
            max_keepalive=settings.http_max_keepalive,
        )

    async def recall(
        self,
        user_id: UUID,
        companion_id: UUID,
        query: str,
        limit: int = 10,
        memory_types: Optional[List[str]] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Recall relevant memories."""
        payload = {
            "user_id": str(user_id),
            "companion_id": str(companion_id),
            "query": query,
            "limit": limit,
            "memory_types": memory_types,
        }
        return await self.post("/api/v1/memory/recall", json=payload, request_id=request_id)

    async def store(
        self,
        user_id: UUID,
        companion_id: UUID,
        content: str,
        memory_type: str,
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Store a memory."""
        payload = {
            "user_id": str(user_id),
            "companion_id": str(companion_id),
            "content": content,
            "memory_type": memory_type,
            "importance": importance,
            "metadata": metadata or {},
        }
        return await self.post("/api/v1/memory/store", json=payload, request_id=request_id)

    async def consolidate(
        self,
        user_id: UUID,
        companion_id: UUID,
        conversation_id: Optional[UUID] = None,
        force: bool = False,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Trigger memory consolidation."""
        payload = {
            "user_id": str(user_id),
            "companion_id": str(companion_id),
            "conversation_id": str(conversation_id) if conversation_id else None,
            "force": force,
        }
        return await self.post("/api/v1/memory/consolidate", json=payload, request_id=request_id)


class SafetyEngineClient(EngineClient):
    """Client for Safety Engine."""

    def __init__(self):
        super().__init__(
            base_url=settings.safety_engine_url,
            service_name="safety-engine",
            timeout=10.0,  # Safety needs to be fast
            max_connections=settings.http_max_connections,
            max_keepalive=settings.http_max_keepalive,
        )

    async def validate_input(
        self,
        content: str,
        user_id: UUID,
        companion_id: UUID,
        conversation_id: UUID,
        metadata: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Validate user input."""
        payload = {
            "content": content,
            "content_type": "user_input",
            "user_id": str(user_id),
            "companion_id": str(companion_id),
            "conversation_id": str(conversation_id),
            "metadata": metadata or {},
        }
        return await self.post("/api/v1/safety/validate-input", json=payload, request_id=request_id)

    async def filter_output(
        self,
        content: str,
        user_id: UUID,
        companion_id: UUID,
        conversation_id: UUID,
        metadata: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Filter model output."""
        payload = {
            "content": content,
            "content_type": "model_output",
            "user_id": str(user_id),
            "companion_id": str(companion_id),
            "conversation_id": str(conversation_id),
            "metadata": metadata or {},
        }
        return await self.post("/api/v1/safety/filter-output", json=payload, request_id=request_id)

    async def check_status(self, request_id: Optional[str] = None) -> Dict[str, Any]:
        """Get safety engine status."""
        return await self.get("/api/v1/safety/status", request_id=request_id)


class RelationshipEngineClient(EngineClient):
    """Client for Relationship Engine."""

    def __init__(self):
        super().__init__(
            base_url=settings.relationship_engine_url,
            service_name="relationship-engine",
            timeout=settings.http_timeout,
            max_connections=settings.http_max_connections,
            max_keepalive=settings.http_max_keepalive,
        )

    async def get_state(
        self,
        user_id: UUID,
        companion_id: UUID,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get relationship state."""
        params = {"user_id": str(user_id), "companion_id": str(companion_id)}
        return await self.get("/api/v1/relationship/state", params=params, request_id=request_id)

    async def update_dimensions(
        self,
        user_id: UUID,
        companion_id: UUID,
        dimension_updates: Dict[str, float],
        trigger: str = "conversation",
        metadata: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update relationship dimensions."""
        payload = {
            "user_id": str(user_id),
            "companion_id": str(companion_id),
            "dimension_updates": dimension_updates,
            "trigger": trigger,
            "metadata": metadata or {},
        }
        return await self.post("/api/v1/relationship/update", json=payload, request_id=request_id)

    async def get_milestones(
        self,
        user_id: UUID,
        companion_id: UUID,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get relationship milestones."""
        params = {"user_id": str(user_id), "companion_id": str(companion_id)}
        return await self.get("/api/v1/relationship/milestones", params=params, request_id=request_id)

    async def add_diary_entry(
        self,
        user_id: UUID,
        companion_id: UUID,
        content: str,
        entry_type: str = "reflection",
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add a diary entry."""
        payload = {
            "user_id": str(user_id),
            "companion_id": str(companion_id),
            "content": content,
            "entry_type": entry_type,
        }
        return await self.post("/api/v1/relationship/diary", json=payload, request_id=request_id)


class EmotionEngineClient(EngineClient):
    """Client for Emotion Engine."""

    def __init__(self):
        super().__init__(
            base_url=settings.emotion_engine_url,
            service_name="emotion-engine",
            timeout=settings.http_timeout,
            max_connections=settings.http_max_connections,
            max_keepalive=settings.http_max_keepalive,
        )

    async def get_state(
        self,
        user_id: UUID,
        companion_id: UUID,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get emotional state."""
        params = {"user_id": str(user_id), "companion_id": str(companion_id)}
        return await self.get("/api/v1/emotion/state", params=params, request_id=request_id)

    async def analyze(
        self,
        user_id: UUID,
        companion_id: UUID,
        text: str,
        context: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze emotion from text."""
        payload = {
            "user_id": str(user_id),
            "companion_id": str(companion_id),
            "text": text,
            "context": context or {},
        }
        return await self.post("/api/v1/emotion/analyze", json=payload, request_id=request_id)

    async def calibrate(
        self,
        user_id: UUID,
        companion_id: UUID,
        calibration_data: Dict[str, Any],
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Calibrate emotion engine."""
        payload = {
            "user_id": str(user_id),
            "companion_id": str(companion_id),
            "calibration_data": calibration_data,
        }
        return await self.post("/api/v1/emotion/calibrate", json=payload, request_id=request_id)


class VoiceEngineClient(EngineClient):
    """Client for Voice Engine."""

    def __init__(self):
        super().__init__(
            base_url=settings.voice_engine_url,
            service_name="voice-engine",
            timeout=settings.http_timeout,
            max_connections=settings.http_max_connections,
            max_keepalive=settings.http_max_keepalive,
        )

    async def transcribe(
        self,
        audio_data: bytes,
        user_id: UUID,
        companion_id: UUID,
        language: str = "en",
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Transcribe audio (multipart upload)."""
        # This would need multipart handling - simplified for now
        payload = {
            "user_id": str(user_id),
            "companion_id": str(companion_id),
            "language": language,
            # audio_data would be sent as multipart
        }
        return await self.post("/api/v1/voice/transcribe", json=payload, request_id=request_id)

    async def synthesize(
        self,
        text: str,
        user_id: UUID,
        companion_id: UUID,
        voice_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Synthesize speech."""
        payload = {
            "text": text,
            "user_id": str(user_id),
            "companion_id": str(companion_id),
            "voice_id": voice_id,
        }
        return await self.post("/api/v1/voice/synthesize", json=payload, request_id=request_id)


class ProactiveEngineClient(EngineClient):
    """Client for Proactive Engine."""

    def __init__(self):
        super().__init__(
            base_url=settings.proactive_engine_url,
            service_name="proactive-engine",
            timeout=settings.http_timeout,
            max_connections=settings.http_max_connections,
            max_keepalive=settings.http_max_keepalive,
        )

    async def check_nudge(
        self,
        user_id: UUID,
        companion_id: UUID,
        conversation_id: UUID,
        last_message: str,
        context: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Check if a proactive nudge should be generated."""
        payload = {
            "user_id": str(user_id),
            "companion_id": str(companion_id),
            "conversation_id": str(conversation_id),
            "last_message": last_message,
            "context": context or {},
        }
        return await self.post("/api/v1/proactive/check", json=payload, request_id=request_id)

    async def get_preferences(
        self,
        user_id: UUID,
        companion_id: UUID,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get proactive preferences."""
        params = {"user_id": str(user_id), "companion_id": str(companion_id)}
        return await self.get("/api/v1/proactive/preferences", params=params, request_id=request_id)

    async def submit_feedback(
        self,
        nudge_id: str,
        user_id: UUID,
        helpful: bool,
        feedback_text: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Submit feedback on a nudge."""
        payload = {
            "nudge_id": nudge_id,
            "user_id": str(user_id),
            "helpful": helpful,
            "feedback_text": feedback_text,
        }
        return await self.post("/api/v1/proactive/feedback", json=payload, request_id=request_id)


class EvaluationEngineClient(EngineClient):
    """Client for Evaluation Engine."""

    def __init__(self):
        super().__init__(
            base_url=settings.evaluation_engine_url,
            service_name="evaluation-engine",
            timeout=settings.http_timeout,
            max_connections=settings.http_max_connections,
            max_keepalive=settings.http_max_keepalive,
        )

    async def compute_rhi(
        self,
        user_id: UUID,
        companion_id: UUID,
        period_days: int = 30,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Compute Relationship Health Index."""
        payload = {
            "user_id": str(user_id),
            "companion_id": str(companion_id),
            "period_days": period_days,
        }
        return await self.post("/api/v1/rhi/compute", json=payload, request_id=request_id)

    async def check_drift(
        self,
        user_id: UUID,
        companion_id: UUID,
        dimensions: Optional[List[str]] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Check for dimension drift."""
        payload = {
            "user_id": str(user_id),
            "companion_id": str(companion_id),
            "dimensions": dimensions,
        }
        return await self.post("/api/v1/drift/check", json=payload, request_id=request_id)

    async def generate_report(
        self,
        user_id: UUID,
        companion_id: UUID,
        report_type: str = "comprehensive",
        period_days: int = 30,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate evaluation report."""
        payload = {
            "user_id": str(user_id),
            "companion_id": str(companion_id),
            "report_type": report_type,
            "period_days": period_days,
        }
        return await self.post("/api/v1/reports", json=payload, request_id=request_id)


class InferenceGatewayClient(EngineClient):
    """Client for Inference Gateway."""

    def __init__(self):
        super().__init__(
            base_url=settings.inference_gateway_url,
            service_name="inference-gateway",
            timeout=60.0,  # LLM inference can take longer
            max_connections=settings.http_max_connections,
            max_keepalive=settings.http_max_keepalive,
        )

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate completion."""
        payload = {
            "messages": messages,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        return await self.post("/api/v1/inference/generate", json=payload, request_id=request_id)

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        request_id: Optional[str] = None,
    ):
        """Generate streaming completion."""
        payload = {
            "messages": messages,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        # For streaming, we need a different approach
        async with self.client.stream(
            "POST",
            "/api/v1/inference/generate",
            json=payload,
            headers={"X-Request-ID": request_id} if request_id else None,
        ) as response:
            async for chunk in response.aiter_bytes():
                yield chunk

    async def list_models(self, request_id: Optional[str] = None) -> Dict[str, Any]:
        """List available models."""
        return await self.get("/api/v1/inference/models", request_id=request_id)

    async def get_model_info(self, model: str, request_id: Optional[str] = None) -> Dict[str, Any]:
        """Get model information."""
        return await self.get(f"/api/v1/inference/models/{model}", request_id=request_id)