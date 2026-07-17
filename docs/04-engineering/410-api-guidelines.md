# PAO API Guidelines

**Version:** 1.0
**Status:** Draft
**Owner:** PAO Platform Team

---

## Overview

This document defines the API design standards, patterns, and best practices for all PAO services.

> **API Principle:** Consistent, predictable, and developer-friendly APIs that evolve gracefully.

---

## API Styles

### REST (Primary for External)

```yaml
# Use for: Public API, Webhooks, Simple CRUD
base_url: "https://api.pao.app/v1"
format: "JSON"
auth: "Bearer Token (OAuth2)"
versioning: "URL path (/v1, /v2)"
```

### GraphQL (Primary for Complex Queries)

```yaml
# Use for: Complex nested queries, Real-time subscriptions, Mobile optimization
endpoint: "https://api.pao.app/graphql"
auth: "Bearer Token (OAuth2)"
versioning: "Schema evolution (no breaking changes)"
```

### gRPC (Internal Service-to-Service)

```yaml
# Use for: High-performance internal communication, Streaming
protocol: "HTTP/2 + Protobuf"
auth: "mTLS (Istio) + JWT"
versioning: "Package versioning (pao.service.v1)"
```

---

## REST API Standards

### Resource Naming

| Resource | Collection | Singleton |
|----------|------------|-----------|
| Companions | `/companions` | `/companions/{id}` |
| Messages | `/companions/{id}/messages` | `/companions/{id}/messages/{msgId}` |
| Memories | `/companions/{id}/memories` | `/companions/{id}/memories/{memId}` |
| Proactive | `/companions/{id}/proactive` | `/companions/{id}/proactive/{provId}` |
| Relationship | `/companions/{id}/relationship` | N/A (singleton) |

### HTTP Methods

| Method | Use Case | Idempotent |
|--------|----------|------------|
| GET | Retrieve resource | Yes |
| POST | Create resource, Actions | No |
| PUT | Full replace | Yes |
| PATCH | Partial update | Yes |
| DELETE | Remove resource | Yes |

### Status Codes

| Code | Meaning | When to Use |
|------|---------|-------------|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST (return resource) |
| 202 | Accepted | Async operation started |
| 204 | No Content | Successful DELETE, no body |
| 400 | Bad Request | Invalid input, validation errors |
| 401 | Unauthorized | Missing/invalid auth |
| 403 | Forbidden | Auth valid but insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource conflict (e.g., duplicate) |
| 422 | Unprocessable Entity | Valid syntax but semantic error |
| 429 | Too Many Requests | Rate limited |
| 500 | Internal Server Error | Unexpected server error |
| 503 | Service Unavailable | Temporary overload/maintenance |

### Request/Response Format

```json
// Success Response (single resource)
{
  "data": {
    "id": "uuid",
    "type": "companion",
    "attributes": {
      "name": "Alex",
      "type": "friend",
      "created_at": "2025-01-15T10:30:00Z"
    },
    "relationships": {
      "memories": {
        "links": {
          "related": "/v1/companions/uuid/memories"
        }
      }
    }
  },
  "meta": {
    "request_id": "uuid",
    "version": "1.0"
  }
}

// Success Response (collection)
{
  "data": [
    { "id": "uuid1", "type": "companion", "attributes": {...} },
    { "id": "uuid2", "type": "companion", "attributes": {...} }
  ],
  "links": {
    "first": "/v1/companions?page=1",
    "next": "/v1/companions?page=2",
    "last": "/v1/companions?page=10"
  },
  "meta": {
    "total_count": 100,
    "page": 1,
    "per_page": 10,
    "request_id": "uuid"
  }
}

// Error Response
{
  "errors": [
    {
      "id": "uuid",
      "status": "422",
      "code": "VALIDATION_ERROR",
      "title": "Validation failed",
      "detail": "Content must be between 1 and 10000 characters",
      "source": {
        "pointer": "/data/attributes/content"
      },
      "meta": {
        "field": "content",
        "rejected_value": ""
      }
    }
  ],
  "meta": {
    "request_id": "uuid"
  }
}
```

### Pagination

```yaml
# Cursor-based (preferred for large datasets)
GET /v1/companions/{id}/messages?cursor=eyJpZCI6InV1aWQifQ&limit=20

# Response includes next cursor
{
  "data": [...],
  "links": {
    "next": "/v1/companions/{id}/messages?cursor=eyJpZCI6InV1aWQyIn0&limit=20"
  },
  "meta": {
    "has_more": true
  }
}

# Offset-based (for simple lists)
GET /v1/companions?page=2&per_page=20
```

### Filtering & Sorting

```yaml
# Filtering
GET /v1/companions/{id}/memories?type=episodic&since=2025-01-01&topic=career

# Sorting
GET /v1/companions/{id}/memories?sort=-created_at,relevance

# Field selection
GET /v1/companions/{id}?fields=name,type,avatar_url
GET /v1/companions/{id}/messages?include=emotion,memory_references
```

---

## GraphQL API Standards

### Schema Design Principles

```graphql
# 1. Use Relay-style connections for pagination
type Query {
  companion(id: ID!): Companion
  companions(first: Int, after: String, filter: CompanionFilter): CompanionConnection!
}

# 2. Explicit nullability
type Companion {
  id: ID!
  name: String!
  type: CompanionType!
  description: String  # Nullable
  avatarUrl: String
  isActive: Boolean!
  createdAt: DateTime!
  updatedAt: DateTime!
  
  # Relationships
  memories(first: Int, after: String, filter: MemoryFilter): MemoryConnection!
  relationship: Relationship!
  proactiveMessages(first: Int, after: String): ProactiveMessageConnection!
}

# 3. Input types for mutations
input CreateCompanionInput {
  name: String! @constraint(minLength: 1, maxLength: 255)
  type: CompanionType!
  description: String
  identityConfig: IdentityConfigInput
}

type CreateCompanionPayload {
  companion: Companion
  errors: [UserError!]!
}

# 4. Subscriptions for real-time
type Subscription {
  messageReceived(companionId: ID!): Message!
  proactiveGenerated(companionId: ID!): ProactiveMessage!
  relationshipChanged(companionId: ID!): Relationship!
}
```

### Error Handling

```graphql
# User-facing errors (expected)
type UserError {
  code: String!
  message: String!
  field: String
  path: [String!]
}

# Payload pattern for mutations
type SendMessagePayload {
  message: Message
  errors: [UserError!]!
}

# Usage in resolver
func (r *mutationResolver) SendMessage(ctx context.Context, input SendMessageInput) (*SendMessagePayload, error) {
    msg, err := r.service.ProcessMessage(ctx, input)
    if err != nil {
        // Convert to user errors
        return &SendMessagePayload{
            Errors: []*UserError{{Code: "VALIDATION_ERROR", Message: err.Error()}},
        }, nil
    }
    return &SendMessagePayload{Message: msg}, nil
}
```

### Complexity Limiting

```go
// Query complexity analysis
var complexityLimit = 1000

func complexityLimitPlugin() graphql.Plugin {
    return graphql.Plugin{
        Name: "complexity_limit",
        OnOperation: func(ctx context.Context, op *graphql.Operation) error {
            complexity := calculateComplexity(op)
            if complexity > complexityLimit {
                return fmt.Errorf("query complexity %d exceeds limit %d", complexity, complexityLimit)
            }
            return nil
        },
    }
}
```

---

## gRPC API Standards

### Protobuf Structure

```protobuf
// api/proto/conversation/v1/conversation.proto
syntax = "proto3";

package pao.conversation.v1;

option go_package = "github.com/pao/api/gen/go/pao/conversation/v1";
option java_multiple_files = true;
option java_package = "com.pao.conversation.v1";

// Service definition
service ConversationEngine {
  // Unary RPC
  rpc ProcessMessage(ProcessMessageRequest) returns (ProcessMessageResponse);
  rpc GetHistory(GetHistoryRequest) returns (GetHistoryResponse);
  
  // Server streaming
  rpc StreamMessages(StreamMessagesRequest) returns (stream Message);
  
  // Client streaming
  rpc UploadAudio(stream AudioChunk) returns (UploadAudioResponse);
  
  // Bidirectional streaming
  rpc VoiceCall(stream VoiceFrame) returns (stream VoiceFrame);
}

// Request/Response messages
message ProcessMessageRequest {
  string companion_id = 1 [(validate.rules).string.uuid = true];
  string user_id = 2 [(validate.rules).string.uuid = true];
  string content = 3 [(validate.rules).string.min_len = 1, (validate.rules).string.max_len = 10000];
  MessageModality modality = 4;
  map<string, string> metadata = 5;
}

message ProcessMessageResponse {
  string message_id = 1 [(validate.rules).string.uuid = true];
  string content = 2;
  EmotionState emotion = 3;
  repeated string memory_references = 4;
  bool proactive = 5;
  map<string, string> metadata = 6;
}

// Streaming messages
message StreamMessagesRequest {
  string companion_id = 1;
  string user_id = 2;
  int32 batch_size = 3;
}

message Message {
  string id = 1;
  string companion_id = 2;
  string role = 3;  // user, companion, system
  string content = 4;
  MessageModality modality = 5;
  EmotionState emotion = 6;
  repeated string memory_references = 7;
  google.protobuf.Timestamp created_at = 8;
}

// Voice streaming
message VoiceFrame {
  oneof payload {
    AudioConfig config = 1;
    bytes audio_data = 2;
    VoiceEvent event = 3;
  }
}

message AudioConfig {
  int32 sample_rate = 1;
  int32 channels = 2;
  string encoding = 3;  // opus, pcm
}

message VoiceEvent {
  enum Type {
    TYPE_UNSPECIFIED = 0;
    START = 1;
    END = 2;
    MUTE = 3;
    UNMUTE = 4;
  }
  Type type = 1;
}
```

### Error Handling

```protobuf
// Standard error details
message ErrorDetail {
  string code = 1;
  string message = 2;
  map<string, string> metadata = 3;
}

// Include in response or use gRPC status codes
// gRPC Status Codes mapping:
// OK = 0
// CANCELLED = 1
// UNKNOWN = 2
// INVALID_ARGUMENT = 3
// DEADLINE_EXCEEDED = 4
// NOT_FOUND = 5
// ALREADY_EXISTS = 6
// PERMISSION_DENIED = 7
// UNAUTHENTICATED = 16
// RESOURCE_EXHAUSTED = 8
// FAILED_PRECONDITION = 9
// ABORTED = 10
// OUT_OF_RANGE = 11
// UNIMPLEMENTED = 12
// INTERNAL = 13
// UNAVAILABLE = 14
// DATA_LOSS = 15
```

### Interceptors

```go
// grpc/interceptors.go
package grpc

import (
    "context"
    "time"
    
    "google.golang.org/grpc"
    "google.golang.org/grpc/codes"
    "google.golang.org/grpc/metadata"
    "google.golang.org/grpc/status"
    "go.opentelemetry.io/otel/trace"
)

// Tracing interceptor
func TracingInterceptor(tracer trace.Tracer) grpc.UnaryServerInterceptor {
    return func(ctx context.Context, req interface{}, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (interface{}, error) {
        ctx, span := tracer.Start(ctx, info.FullMethod)
        defer span.End()
        
        return handler(ctx, req)
    }
}

// Logging interceptor
func LoggingInterceptor(logger *zap.Logger) grpc.UnaryServerInterceptor {
    return func(ctx context.Context, req interface{}, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (interface{}, error) {
        start := time.Now()
        
        resp, err := handler(ctx, req)
        
        duration := time.Since(start)
        logger.Info("gRPC request",
            zap.String("method", info.FullMethod),
            zap.Duration("duration", duration),
            zap.Error(err),
        )
        
        return resp, err
    }
}

// Auth interceptor
func AuthInterceptor(validator TokenValidator) grpc.UnaryServerInterceptor {
    return func(ctx context.Context, req interface{}, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (interface{}, error) {
        md, ok := metadata.FromIncomingContext(ctx)
        if !ok {
            return nil, status.Error(codes.Unauthenticated, "missing metadata")
        }
        
        token := md.Get("authorization")
        if len(token) == 0 {
            return nil, status.Error(codes.Unauthenticated, "missing token")
        }
        
        claims, err := validator.Validate(ctx, strings.TrimPrefix(token[0], "Bearer "))
        if err != nil {
            return nil, status.Error(codes.Unauthenticated, "invalid token")
        }
        
        // Add claims to context
        ctx = context.WithValue(ctx, claimsKey{}, claims)
        
        return handler(ctx, req)
    }
}

// Rate limiting interceptor
func RateLimitInterceptor(limiter RateLimiter) grpc.UnaryServerInterceptor {
    return func(ctx context.Context, req interface{}, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (interface{}, error) {
        // Extract identifier (user_id, companion_id, IP)
        identifier := extractIdentifier(ctx, req)
        
        allowed, retryAfter := limiter.Allow(ctx, identifier)
        if !allowed {
            return nil, status.Error(codes.ResourceExhausted, "rate limit exceeded").
                WithDetails(&errdetails.RetryInfo{RetryDelay: durationpb.New(retryAfter)})
        }
        
        return handler(ctx, req)
    }
}
```

---

## Versioning Strategy

### REST Versioning

```yaml
# URL versioning (major versions only)
/v1/companions
/v2/companions  # Breaking changes only

# Header versioning (minor/experimental)
Accept: application/vnd.pao.v1+json
Accept: application/vnd.pao.v1.1+json  # Backward compatible additions

# Deprecation
# Response headers
Deprecation: true
Sunset: Sat, 01 Jan 2026 00:00:00 GMT
Link: <https://api.pao.app/v2/companions>; rel="successor-version"
```

### GraphQL Versioning

```graphql
# No versioning in URL - evolve schema
# Rules:
# 1. Never remove fields - deprecate instead
# 2. Never change field types - add new fields
# 3. Use @deprecated directive

type Companion {
  id: ID!
  name: String!
  # Old field
  avatarUrl: String @deprecated(reason: "Use avatar instead")
  # New field
  avatar: Avatar!
}

type Avatar {
  url: String!
  thumbnailUrl: String
  generatedAt: DateTime
}
```

### gRPC Versioning

```protobuf
// Package versioning
package pao.conversation.v1;  // v1, v2, etc.

// Service version in name
service ConversationEngineV1 { ... }
service ConversationEngineV2 { ... }

// Or use google.api.http annotations for REST gateway
```

---

## Authentication & Authorization

### OAuth2 Scopes

```yaml
scopes:
  # Companion management
  companion:read: "Read companion profile and config"
  companion:write: "Create/update companion"
  companion:delete: "Delete companion"
  
  # Conversation
  message:read: "Read conversation history"
  message:write: "Send messages"
  message:stream: "Stream messages (WebSocket)"
  
  # Memory
  memory:read: "Recall memories"
  memory:write: "Create memories (system)"
  memory:delete: "Forget memories"
  
  # Relationship
  relationship:read: "View relationship state"
  relationship:manage: "Configure relationship settings"
  
  # Proactive
  proactive:read: "View proactive messages"
  proactive:manage: "Configure proactive settings"
  proactive:feedback: "Provide feedback on proactives"
  
  # Voice
  voice:call: "Initiate voice calls"
  voice:stream: "Stream audio"
  
  # Export
  export:create: "Create data exports"
  export:read: "Download exports"
  
  # Admin
  admin:read: "Read admin data"
  admin:write: "Modify admin settings"
  admin:moderate: "Moderation actions"
```

### Token Format

```json
// Access Token (JWT)
{
  "iss": "https://auth.pao.app",
  "sub": "user-uuid",
  "aud": "pao-api",
  "exp": 1734567890,
  "iat": 1734564290,
  "scope": "companion:read message:write memory:read",
  "companion_id": "companion-uuid",  // Optional, for companion-scoped tokens
  "permissions": ["read", "write"],   // Fine-grained permissions
  "org_id": "org-uuid"               // For future multi-tenancy
}

// Refresh Token (Opaque)
// Stored in database with rotation
```

---

## Rate Limiting

### Limits

| Tier | Requests/Minute | Burst | Scope |
|------|-----------------|-------|-------|
| Free | 60 | 10 | Per user |
| Pro | 300 | 50 | Per user |
| Premium | 1000 | 100 | Per user |
| Internal | 10000 | 500 | Per service |

### Headers

```http
# Response headers
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 295
X-RateLimit-Reset: 1734567900
Retry-After: 45  # On 429
```

---

## Webhooks

### Configuration

```json
// Webhook registration
POST /v1/webhooks
{
  "url": "https://app.example.com/webhooks/pao",
  "events": [
    "companion.created",
    "message.received",
    "proactive.generated",
    "safety.crisis_detected",
    "relationship.milestone_achieved",
    "export.completed"
  ],
  "secret": "webhook-secret-key"
}

// Webhook payload
{
  "id": "evt-uuid",
  "type": "message.received",
  "created_at": "2025-01-15T10:30:00Z",
  "data": {
    "companion_id": "uuid",
    "message_id": "uuid",
    "user_id": "uuid",
    "content": "Hello!",
    "modality": "text"
  },
  "signature": "sha256=..."
}
```

### Retry Policy

```yaml
retries:
  - delay: 1m
  - delay: 5m
  - delay: 15m
  - delay: 1h
  - delay: 6h
  - delay: 24h
max_retries: 6
timeout: 30s
```

---

## API Documentation

### OpenAPI/Swagger

```yaml
# Generated from code annotations
# Available at: https://api.pao.app/docs
# Spec: https://api.pao.app/openapi.yaml
```

### GraphQL Playground

```yaml
# Available at: https://api.pao.app/graphql
# Introspection enabled in non-production
```

### gRPC Reflection

```yaml
# Enabled in development/staging
# grpcurl -proto api/proto/conversation/v1/conversation.proto \
#   conversation-engine:9090 \
#   pao.conversation.v1.ConversationEngine.ProcessMessage
```

---

## Testing APIs

### Contract Testing

```yaml
# Pact for REST/GraphQL
# Consumer-driven contracts
# Broker: https://pact-broker.pao.app
```

### Integration Testing

```go
// Test against real API
func TestAPI_Integration(t *testing.T) {
    client := NewTestClient("https://api-staging.pao.app")
    
    // Auth
    token := client.Login(t, "test@pao.app", "password")
    
    // Create companion
    companion := client.CreateCompanion(t, token, CreateCompanionRequest{
        Name: "Test",
        Type: "friend",
    })
    
    // Send message
    resp := client.SendMessage(t, token, companion.ID, SendMessageRequest{
        Content: "Hello!",
    })
    
    assert.NotEmpty(t, resp.MessageID)
    assert.Contains(t, resp.Content, "Hello")
}
```

---

## API Checklist

### Before Release

- [ ] OpenAPI spec generated and valid
- [ ] GraphQL schema validated
- [ ] gRPC protobuf linted (buf lint)
- [ ] Breaking changes documented
- [ ] Deprecation notices added
- [ ] Rate limits configured
- [ ] Authentication tested
- [ ] Error responses consistent
- [ ] Pagination works correctly
- [ ] Filtering/sorting tested
- [ ] Webhook signatures verified
- [ ] Load tested
- [ ] Contract tests pass

---

**Aligned With:** `310-api-specification.md`, `300-system-architecture.md`, `400-development-guide.md`
**Next Review:** 2026-01-17