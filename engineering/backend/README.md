# PAO Backend

Backend API and infrastructure for PAO AI Companion.

## Architecture

```
engineering/backend/
├── packages/
│   ├── backend-api/          # Main Fastify API server (TypeScript)
│   └── shared/               # Shared utilities, types, and schemas
├── docker-compose.yml        # Full stack orchestration
├── prometheus.yml            # Prometheus metrics configuration
├── tsconfig.base.json        # Base TypeScript configuration
└── .env.example              # Environment variables template
```

## Services

### Backend API (Port 3000)
- **Framework**: Fastify with TypeScript
- **Database**: PostgreSQL with Drizzle ORM
- **Cache**: Redis (ioredis)
- **Message Queue**: Kafka (kafkajs)
- **Auth**: JWT with refresh token rotation
- **Documentation**: OpenAPI/Swagger at `/docs`
- **Metrics**: Prometheus at `/metrics`
- **Health Checks**: `/health`, `/health/live`, `/health/ready`

### AI Engines (Python/FastAPI)
| Engine | Port | Description |
|--------|------|-------------|
| Inference Gateway | 8000 | LLM inference routing |
| Identity Engine | 8003 | User identity & profiles |
| Memory Engine | 8004 | Vector memory & retrieval |
| Safety Engine | 8005 | Content moderation |
| Relationship Engine | 8006 | Relationship tracking |
| Emotion Engine | 8007 | Emotion analysis |
| Voice Engine | 8008 | STT/TTS & streaming |
| Proactive Engine | 8009 | Proactive suggestions |
| Evaluation Engine | 8010 | A/B testing & metrics |
| Companion Runtime | 8011 | LangGraph orchestration |

### Infrastructure
- **PostgreSQL**: Primary database (port 5432)
- **Redis**: Caching & sessions (port 6379)
- **Kafka**: Event streaming (port 9092)
- **Qdrant**: Vector database (port 6333)
- **Prometheus**: Metrics (port 9091)
- **Grafana**: Dashboards (port 3001)
- **Jaeger**: Distributed tracing (port 16686)

## Quick Start

### Prerequisites
- Node.js 20+
- pnpm 8+
- Docker & Docker Compose
- Python 3.11+ (for AI engines)

### Development

1. **Install dependencies**
```bash
cd engineering/backend
pnpm install
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your values
```

3. **Start infrastructure**
```bash
docker-compose up -d postgres redis kafka qdrant
```

4. **Run database migrations**
```bash
cd packages/backend-api
pnpm db:migrate
```

5. **Start development server**
```bash
pnpm dev
```

Server runs at `http://localhost:3000`
API Docs at `http://localhost:3000/docs`

### Full Stack with Docker
```bash
docker-compose up -d
```

All services will be available at their respective ports.

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout
- `GET /api/v1/auth/me` - Get current user

### Chat
- `POST /api/v1/chat` - Send message to AI
- `GET /api/v1/chat/history` - Get chat history

### User
- `GET /api/v1/users/profile` - Get user profile
- `PATCH /api/v1/users/profile` - Update profile
- `GET /api/v1/users/sessions` - List active sessions
- `DELETE /api/v1/users/sessions/:id` - Revoke session

### Health & Monitoring
- `GET /health` - Full health check
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe
- `GET /metrics` - Prometheus metrics
- `GET /docs` - Swagger UI

## Project Structure

### backend-api/src/
```
├── config.ts          # Configuration (Zod-validated env)
├── database.ts        # Drizzle ORM setup
├── redis.ts           # Redis client
├── kafka.ts           # Kafka producer/consumer
├── main.ts            # Fastify app entry point
├── models/
│   ├── user.ts        # User schema
│   ├── session.ts     # Session schema
│   └── index.ts       # Exports
└── scripts/
    └── seed.ts        # Database seeding
```

### shared/src/
```
├── index.ts           # Main exports
├── zod.ts             # Shared Zod schemas
├── errors.ts          # Error classes & handlers
└── utils.ts           # Utility functions
```

## Database Schema

Managed with Drizzle ORM. Migrations in `packages/backend-api/migrations/`.

Key tables:
- `users` - User accounts
- `sessions` - Refresh token sessions
- `conversations` - Chat conversations
- `messages` - Chat messages

## Environment Variables

See `.env.example` for all required variables.

Key variables:
```bash
# Required
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
KAFKA_BROKERS=localhost:9092
JWT_SECRET=... (min 32 chars)
JWT_REFRESH_SECRET=... (min 32 chars)

# AI Engines
INFERENCE_GATEWAY_URL=http://localhost:8000
IDENTITY_ENGINE_URL=http://localhost:8003
# ... etc

# Optional
STRIPE_SECRET_KEY=
SENDGRID_API_KEY=
LIVEKIT_API_KEY=
```

## Testing

```bash
# Unit tests
pnpm test

# Watch mode
pnpm test:watch

# Coverage
pnpm test --coverage
```

## Linting & Formatting

```bash
# Lint
pnpm lint

# Format
pnpm format

# Type check
pnpm typecheck
```

## Deployment

### Docker
```bash
docker build -t pao-backend-api -f packages/backend-api/Dockerfile .
docker run -p 3000:3000 --env-file .env pao-backend-api
```

### Kubernetes
Helm charts coming soon.

## Observability

- **Logs**: Structured JSON via Pino
- **Metrics**: Prometheus format at `/metrics`
- **Traces**: OpenTelemetry to Jaeger
- **Dashboards**: Grafana (import from `grafana/dashboards/`)

## License

MIT