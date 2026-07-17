# PAO Engineering Project Structure

This directory contains the implementation code for PAO, organized by technology stack.

## Structure

```
engineering/
├── mobile/                 # Flutter mobile application (iOS/Android)
│   ├── lib/
│   │   ├── core/           # Core utilities, constants, themes
│   │   ├── features/       # Feature modules (clean architecture)
│   │   │   ├── auth/
│   │   │   ├── companion/
│   │   │   ├── conversation/
│   │   │   ├── memory/
│   │   │   ├── proactive/
│   │   │   ├── settings/
│   │   │   └── subscription/
│   │   ├── shared/         # Shared widgets, models, services
│   │   └── main.dart
│   ├── test/
│   ├── pubspec.yaml
│   └── melos.yaml
│
├── backend/                # Node.js/TypeScript backend services
│   ├── packages/
│   │   ├── api-gateway/    # REST/GraphQL API Gateway
│   │   ├── user-service/   # User management, auth
│   │   ├── companion-service/  # Companion CRUD, personality
│   │   ├── conversation-service/  # Messaging, streaming
│   │   ├── memory-service/  # Memory CRUD, retrieval
│   │   ├── proactive-service/  # Proactive generation
│   │   ├── billing-service/  # Subscriptions, entitlements
│   │   ├── safety-service/  # Crisis detection, moderation
│   │   ├── notification-service/  # Push, email, in-app
│   │   ├── shared/         # Shared libraries
│   │   │   ├── config/
│   │   │   ├── database/
│   │   │   ├── events/
│   │   │   ├── auth/
│   │   │   ├── observability/
│   │   │   └── testing/
│   │   └── proto/          # Protobuf definitions (source of truth)
│   ├── turbo.json
│   ├── package.json
│   └── tsconfig.base.json
│
├── ai/                     # Python AI/ML services
│   ├── services/
│   │   ├── inference-gateway/  # LLM routing, streaming
│   │   ├── identity-engine/    # Personality, traits
│   │   ├── conversation-engine/  # Response generation
│   │   ├── memory-engine/      # Embedding, consolidation
│   │   ├── relationship-engine/  # RHI, bonding
│   │   ├── emotion-engine/     # Emotion detection
│   │   ├── voice-engine/       # TTS, STT, voice cloning
│   │   ├── proactive-engine/   # Proactive candidate generation
│   │   ├── safety-engine/      # Crisis, harm, injection detection
│   │   └── evaluation-engine/  # Automated evaluation
│   ├── shared/
│   │   ├── models/       # Model wrappers, inference
│   │   ├── data/         # Datasets, preprocessing
│   │   ├── training/     # Fine-tuning, RLHF
│   │   ├── evaluation/   # Benchmarks, metrics
│   │   └── utils/        # Common utilities
│   ├── pyproject.toml
│   └── uv.lock
│
├── infrastructure/         # Infrastructure as Code
│   ├── terraform/
│   │   ├── modules/
│   │   ├── environments/
│   │   │   ├── dev/
│   │   │   ├── staging/
│   │   │   └── prod/
│   │   └── global/
│   ├── kubernetes/
│   │   ├── base/
│   │   ├── overlays/
│   │   │   ├── dev/
│   │   │   ├── staging/
│   │   │   └── prod/
│   │   └── charts/
│   └── helm/
│
└── docs/                   # Engineering documentation
    ├── architecture/
    ├── api/
    ├── deployment/
    └── runbooks/
```

## Technology Choices

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Mobile** | Flutter 3.x + Dart 3.x | Single codebase, native performance, great tooling |
| **Backend** | Node.js 20 + TypeScript 5.x | Type safety, ecosystem, team familiarity |
| **API** | Connect (gRPC) + REST + GraphQL | Type-safe, streaming, flexible |
| **AI/ML** | Python 3.11 + PyTorch + Transformers | ML ecosystem, model serving |
| **Vector DB** | Qdrant | Performance, filtering, multi-tenancy |
| **Graph DB** | Kuzu | Embedded, fast, Cypher-like |
| **Time-series** | ClickHouse | Analytics, compression |
| **Primary DB** | PostgreSQL 16 | ACID, JSONB, extensions |
| **Cache** | Redis 7 Cluster | Sessions, rate limits, pub/sub |
| **Message Bus** | Redpanda (Kafka-compatible) | Low resource, tiered storage |
| **Service Mesh** | Istio Ambient | Zero-trust, no sidecars |
| **Orchestration** | Kubernetes (EKS/GKE/AKS) | Multi-cloud, GitOps |
| **IaC** | Terraform + Helm | Declarative, modular |
| **Observability** | OpenTelemetry + Datadog | Vendor-neutral, comprehensive |
| **CI/CD** | GitHub Actions + ArgoCD | GitOps, progressive delivery |

## Getting Started

### Prerequisites
- Flutter 3.22+
- Node.js 20+ (via fnm/nvm)
- Python 3.11+ (via uv)
- Docker & Docker Compose
- Kubernetes CLI (kubectl)
- Terraform 1.8+

### Development Setup

```bash
# Clone with submodules
git clone --recurse-submodules https://github.com/pao/app.git

# Backend
cd engineering/backend
pnpm install
pnpm dev

# AI Services
cd engineering/ai
uv sync
uv run python -m services.inference_gateway

# Mobile
cd engineering/mobile
flutter pub get
flutter run

# Infrastructure (local)
cd engineering/infrastructure
docker-compose up -d
```

## Monorepo Management

- **Backend**: Turborepo for Node.js packages
- **AI**: uv workspace for Python packages
- **Mobile**: Melos for Flutter packages
- **Shared Protobuf**: buf for schema registry

## Documentation

- [Architecture Decision Records](../docs/07-adr/)
- [RFCs](../docs/08-rfc/)
- [API Specification](../docs/03-architecture/310-api-specification.md)
- [Development Guide](../docs/04-engineering/400-development-guide.md)
- [Deployment Guide](../docs/03-architecture/350-deployment.md)