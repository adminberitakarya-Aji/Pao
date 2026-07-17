# ADR-002: API Protocol Selection

**Status:** Accepted
**Date:** 2025-01-15
**Deciders:** CTO, VP Engineering, API Platform Lead
**Consulted:** Frontend Leads, Mobile Leads, AI Engineers, Security

---

## Context

PAO needs to choose the primary API protocol(s) for:
1. **Client ↔ Backend** (Mobile apps, Web, Third-party)
2. **Service ↔ Service** (Internal, after extraction)
3. **AI Inference** (High-throughput, streaming)
4. **Real-time Voice** (WebRTC, low-latency streaming)

### Requirements

| Requirement | Priority |
|-------------|----------|
| Type safety (end-to-end) | Critical |
| Streaming support (SSE, WebSocket) | Critical |
| Mobile performance (bandwidth, battery) | High |
| Browser compatibility | High |
| Developer experience (tooling, docs) | High |
| Gradual adoption (strangler fig) | High |
| gRPC ecosystem (proxies, mesh) | Medium |
| GraphQL flexibility (mobile) | Medium |

---

## Decision

**Multi-protocol strategy with clear boundaries:**

| Layer | Protocol | Rationale |
|-------|----------|-----------|
| **Client ↔ Backend** | **REST + JSON** (primary), **GraphQL** (mobile), **WebSocket** (realtime) | Universal, cacheable, great tooling, mobile-optimized via GraphQL |
| **Service ↔ Service** | **gRPC/Connect** (protobuf) | Type-safe, streaming, service mesh ready |
| **AI Inference** | **gRPC/Connect** (streaming) | High throughput, binary, model streaming |
| **Voice/Real-time** | **WebRTC** (media) + **gRPC** (signaling) | Sub-100ms, adaptive bitrate, standard |

### Protocol Details

#### 1. REST + JSON (Public API)
```yaml
Style: RESTful, resource-oriented
Versioning: URL path (/v1/, /v2/)
Auth: Bearer tokens (JWT), API keys
Format: JSON (camelCase)
Errors: RFC 9457 (Problem Details)
Pagination: Cursor-based (after/before)
Rate Limits: Header-based (X-RateLimit-*)
Streaming: Server-Sent Events (SSE) for proactive, typing indicators
```

#### 2. GraphQL (Mobile-Optimized)
```yaml
Endpoint: /graphql (single)
Schema: Federated (Apollo Federation v2)
Clients: iOS, Android, React Native
Features:
  - Persisted queries (APQ)
  - @defer/@stream for progressive loading
  - DataLoader for N+1 prevention
  - Complexity limiting (depth, cost)
Auth: Same JWT as REST
```

#### 3. gRPC/Connect (Internal + AI)
```yaml
Protocol: Connect (gRPC + JSON/HTTP fallback)
Codegen: buf (protobuf), connect-es (TypeScript), connect-go, connect-swift
Transport: h2 (HTTP/2) for internal, h2c/HTTP+JSON for edge
Streaming: Bidirectional for voice, server-stream for inference
Interceptors: Auth, tracing, metrics, retries, circuit breaker
Reflection: Enabled for tooling (grpcurl, Evans)
```

#### 4. WebRTC (Voice)
```yaml
Signaling: gRPC (Connect) for offer/answer/ICE
Media: SRTP (encrypted), Opus codec, 48kHz
Transport: UDP (preferred), TCP fallback, TURN/STUN
Latency Target: < 150ms end-to-end (P95)
Adaptive: Bandwidth estimation, packet loss concealment
```

---

## API Gateway Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  API Gateway │────▶│  Services   │
│ (Mobile/Web)│     │   (Envoy)    │     │  (gRPC)     │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │
       │ REST/GraphQL      │ gRPC/Connect
       │ WebSocket/SSE     │ WebRTC Signaling
       ▼                   ▼
┌─────────────────────────────────────────┐
│         Protocol Translation Layer      │
│  - REST → gRPC transcoding (Envoy)     │
│  - GraphQL → gRPC resolution            │
│  - Auth termination (JWT → mTLS)        │
│  - Rate limiting, quotas                │
│  - Request/response transformation      │
└─────────────────────────────────────────┘
```

---

## Schema Management

### Protobuf (Source of Truth)
```protobuf
// api/v1/conversation.proto
syntax = "proto3";
package pao.api.v1;

service ConversationService {
  rpc SendMessage(SendMessageRequest) returns (stream MessageResponse);
  rpc GetHistory(GetHistoryRequest) returns (stream Message);
  rpc CreateCompanion(CreateCompanionRequest) returns (Companion);
}

message SendMessageRequest {
  string companion_id = 1;
  string content = 2;
  MessageModality modality = 3;
  map<string, string> metadata = 4;
}
```

### Tooling Pipeline
```
protobuf (.proto)
    │
    ├─▶ buf lint / buf breaking (CI)
    │
    ├─▶ connect-es (TypeScript) ──▶ @pao/api-client (npm)
    ├─go (Go) ──▶ github.com/pao/api/gen/go (go.mod)
    ├─swift (Swift) ──▶ PAOAPI (SPM)
    ├─kotlin (Kotlin) ──▶ com.pao:api (Maven)
    │
    └─▶ OpenAPI v3 (via protoc-gen-openapiv2) ──▶ REST docs, Postman
```

### Versioning Strategy
- **Protobuf**: Package versioning (`pao.api.v1`, `pao.api.v2`)
- **REST**: URL versioning (`/v1/`, `/v2/`)
- **GraphQL**: Schema evolution (deprecate, no breaking changes)
- **Compatibility**: 12-month overlap, automated breaking change detection

---

## Consequences

### Positive
- **Right tool for each job**: REST for simplicity, GraphQL for mobile flexibility, gRPC for performance
- **Type safety everywhere**: Protobuf → generated clients (no drift)
- **Service mesh ready**: gRPC works natively with Istio/Envoy
- **Gradual migration**: REST gateway translates to gRPC internally
- **Mobile optimized**: GraphQL reduces over-fetching on cellular

### Negative
- **Complexity**: Multiple protocols to maintain, test, document
- **Gateway logic**: Translation layer adds latency, failure modes
- **Team expertise**: Need proficiency in REST, GraphQL, gRPC, WebRTC
- **Debugging**: Different tools for each protocol

### Mitigations
- **Gateway as translation layer**: Services only speak gRPC
- **Unified observability**: OpenTelemetry spans across protocols
- **Contract testing**: Pact for REST, protobuf breaking change detection
- **Documentation**: Single source (protobuf) → generated docs for all

---

## Implementation Checklist

- [ ] Define protobuf schemas for all domains
- [ ] Set up buf registry (buf.build/pao)
- [ ] Configure CI: lint, breaking change detection
- [ ] Generate TypeScript/Go/Swift/Kotlin clients
- [ ] Deploy Envoy gateway with gRPC transcoding
- [ ] Implement GraphQL federation gateway
- [ ] WebRTC signaling service (gRPC)
- [ ] Load test each protocol path
- [ ] Document migration guide for clients

---

## Related Decisions

- ADR-001: Microservices vs Modular Monolith
- ADR-003: Event-Driven Architecture
- ADR-006: Service Mesh (Istio)

---

## References

- [Connect Protocol](https://connectrpc.com/)
- [buf: Protobuf tooling](https://buf.build/)
- [Envoy gRPC Transcoding](https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/grpc_json_transcoder_filter)
- [Apollo Federation](https://www.apollographql.com/federation/)
- [WebRTC for the Curious](https://webrtcforthecurious.com/)

---

**Approval:**
- CTO: _________________ Date: __________
- VP Engineering: _________________ Date: __________
- API Platform Lead: _________________ Date: __________