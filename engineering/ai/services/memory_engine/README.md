# PAO Memory Engine

The Memory Engine is the core memory management system for PAO AI companions. It provides a hybrid memory architecture combining episodic, semantic, and procedural memory with consolidation, recall, and consistency checking capabilities.

## Architecture

### Memory Types

| Type | Description | Storage | Use Case |
|------|-------------|---------|----------|
| **Episodic** | Event-based memories with temporal context | PostgreSQL + Qdrant | Conversation history, user interactions |
| **Semantic** | Extracted facts and concepts | PostgreSQL + Qdrant + Kuzu | Knowledge graph, user preferences, facts |
| **Procedural** | Learned patterns and skills | Kuzu (graph) | Behavioral patterns, conversation flows |
| **Emotional** | Emotional context and valence | PostgreSQL + Redis | Sentiment tracking, emotional resonance |
| **Relationship** | Relationship dimension scores | PostgreSQL + Kuzu | Trust, intimacy, conflict tracking |
| **Timeline** | Chronological event sequences | PostgreSQL | Life events, milestones |

### Data Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Write API  │────▶│  PostgreSQL  │────▶│  Qdrant (vec)   │
└─────────────┘     │  (metadata)  │     │  Kuzu (graph)   │
                    └──────────────┘     └─────────────────┘
                           │                      │
                           ▼                      ▼
                    ┌──────────────┐     ┌─────────────────┐
                    │   Redis      │     │  Consolidation  │
                    │  (cache/TTL) │     │   (Temporal)    │
                    └──────────────┘     └─────────────────┘
```

### Core Components

| Component | Purpose |
|-----------|---------|
| **MemoryService** | Core CRUD operations for all memory types |
| **RecallService** | Semantic search and relevance scoring |
| **ConsolidationService** | Batch processing: episodic → semantic + graph |
| **ConsistencyService** | Contradiction detection, deduplication, TTL enforcement |
| **ExportService** | GDPR-compliant data export (JSON, JSON-LD, CSV) |

## API Endpoints

### Memory Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/memories` | Write a new memory |
| `GET` | `/api/v1/memories/{memory_id}` | Read a specific memory |
| `PATCH` | `/api/v1/memories/{memory_id}` | Update a memory |
| `DELETE` | `/api/v1/memories/{memory_id}` | Delete a memory |
| `POST` | `/api/v1/memories/query` | Query memories with filters |
| `POST` | `/api/v1/memories/recall` | Semantic recall with query |

### Consolidation & Consistency

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/memories/consolidate` | Trigger consolidation job |
| `GET` | `/api/v1/memories/consolidate/{job_id}` | Get consolidation status |
| `POST` | `/api/v1/memories/consistency/check` | Run consistency checks |
| `GET` | `/api/v1/memories/consistency/report/{check_id}` | Get consistency report |

### Export

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/memories/export` | Request data export |
| `GET` | `/api/v1/memories/export/{export_id}` | Get export status/download |

## Configuration

Environment variables:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/pao_memory
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379/0
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
TEMPORAL_ADDRESS=localhost:7233

# External Services
EMBEDDING_SERVICE_URL=http://localhost:8001
INFERENCE_GATEWAY_URL=http://localhost:8000
SAFETY_ENGINE_URL=http://localhost:8005
IDENTITY_ENGINE_URL=http://localhost:8003

# Auth
API_KEY=your-api-key
INTERNAL_API_KEY=your-internal-key

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## Local Development

```bash
# Start all dependencies
docker-compose up -d

# Run the service
./scripts/dev.sh

# Run tests
./scripts/test.sh
```

## Testing

```bash
# Unit tests
pytest tests/unit/ -v --cov=memory_engine

# Integration tests
pytest tests/integration/ -v

# All tests with coverage
pytest tests/ -v --cov=memory_engine --cov-fail-under=80
```

## Deployment

### Kubernetes

```bash
# Deploy to cluster
kubectl apply -f k8s/

# Check status
kubectl get pods -n ai-services -l app=memory-engine
```

### Docker

```bash
# Build
docker build -t memory-engine .

# Run
docker run -p 8004:8004 \
  -e DATABASE_URL=... \
  -e QDRANT_URL=... \
  memory-engine
```

## Monitoring

- **Health**: `GET /health`
- **Metrics**: `GET /metrics` (Prometheus format)
- **Key Metrics**:
  - `memory_write_latency_seconds`
  - `memory_recall_latency_seconds`
  - `consolidation_job_duration_seconds`
  - `consistency_check_duration_seconds`
  - `memory_count_total`

## Performance Targets

| Operation | P50 | P95 | P99 |
|-----------|-----|-----|-----|
| Write | <50ms | <100ms | <200ms |
| Read | <20ms | <50ms | <100ms |
| Recall | <100ms | <200ms | <400ms |
| Query | <50ms | <150ms | <300ms |

## Security

- All endpoints require API key authentication (`X-API-Key` header)
- Internal service communication uses `INTERNAL_API_KEY`
- Data encryption at rest (PostgreSQL TDE, Qdrant encryption)
- TLS in transit for all external connections
- Field-level encryption for PII

## License

MIT License - See LICENSE file for details.