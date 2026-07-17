# PAO Development Guide

**Version:** 1.0
**Status:** Draft
**Owner:** PAO Engineering Team

---

## Overview

This guide covers the development workflow, tooling, standards, and best practices for contributing to PAO.

> **Development Principle:** Developer experience is a first-class concern. Fast feedback loops, clear conventions, and automated quality gates.

---

## Getting Started

### Prerequisites

```bash
# Required tools
- Docker Desktop / Podman
- kubectl >= 1.28
- helm >= 3.12
- kind >= 0.22 (for local Kubernetes)
- tilt >= 0.33 (for local development)
- go >= 1.22
- node >= 20 (LTS)
- python >= 3.11
- protoc >= 25
- buf >= 1.28
- golangci-lint >= 1.56
- pre-commit >= 3.6

# Optional but recommended
- direnv (for .envrc)
- gh (GitHub CLI)
- argocd CLI
- istioctl
- k9s
- stern
```

### Quick Start (Local Development)

```bash
# 1. Clone repository
git clone https://github.com/pao/pao.git
cd pao

# 2. Start local cluster (Kind)
make kind-create

# 3. Install dependencies
make install-tools

# 4. Start development environment (Tilt)
tilt up

# 5. Access services
# API: http://api.local.pao.app
# GraphQL Playground: http://api.local.pao.app/graphql
# Grafana: http://grafana.local.pao.app
# Jaeger: http://jaeger.local.pao.app
```

### Repository Structure

```
pao/
├── .github/                    # GitHub Actions workflows
├── .vscode/                    # VS Code settings
├── api/                        # Protobuf/GraphQL definitions
│   ├── proto/                  # Protocol Buffers
│   └── graphql/                # GraphQL schemas
├── cmd/                        # Service entry points
│   ├── api-gateway/
│   ├── companion-api/
│   ├── identity-engine/
│   ├── conversation-engine/
│   ├── memory-engine/
│   ├── relationship-engine/
│   ├── emotion-engine/
│   ├── voice-engine/
│   ├── proactive-engine/
│   ├── safety-engine/
│   └── evaluation-engine/
├── internal/                   # Private Go packages
│   ├── auth/
│   ├── config/
│   ├── database/
│   ├── messaging/
│   ├── observability/
│   └── validation/
├── pkg/                        # Public Go packages
│   ├── models/
│   ├── clients/
│   └── middleware/
├── services/                   # Service-specific code
│   ├── companion-api/
│   ├── conversation-engine/
│   └── ...
├── deployments/                # Kubernetes manifests
│   ├── base/
│   └── overlays/
├── scripts/                    # Operational scripts
├── docs/                       # Documentation (this repo)
├── tests/                      # Integration/E2E tests
├── Makefile
├── go.work                     # Go workspace
├── tiltfile                    # Tilt configuration
├── docker-compose.yml          # Local dependencies
└── README.md
```

---

## Development Workflow

### Branch Strategy

```
main (protected)
  │
  ├── release/v1.x (protected, long-lived)
  │
  ├── feature/xxx (short-lived, from main)
  ├── fix/xxx (short-lived, from main)
  ├── hotfix/xxx (from release branch)
  └── chore/xxx (maintenance)
```

### Commit Convention

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, no code change
- `refactor`: Code restructuring
- `perf`: Performance improvement
- `test`: Adding tests
- `chore`: Maintenance
- `security`: Security fix

**Examples:**
```
feat(memory): add episodic memory consolidation

Implements the nightly consolidation job that converts
episodic memories to semantic memories based on access patterns.

Closes #1234

---

fix(voice): handle WebRTC ICE restart correctly

The ICE agent was not properly handling network changes
during active calls, causing audio drops.

Fixes #5678
```

### Pull Request Process

```yaml
# .github/pull_request_template.md
## Description
<!-- Describe the changes -->

## Type
- [ ] Feature
- [ ] Bug Fix
- [ ] Documentation
- [ ] Refactor
- [ ] Performance
- [ ] Security

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing done

## Checklist
- [ ] Code follows style guide
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No breaking changes (or migration included)
- [ ] Security implications considered

## Screenshots/Recordings
<!-- If UI changes -->
```

### PR Requirements

| Requirement | Enforcement |
|-------------|-------------|
| CI passes | Required (branch protection) |
| 1 approval | Required (branch protection) |
| No merge conflicts | Required |
| Linear history | Rebase & merge |
| Conventional commits | Linted |
| DCO signed | Required |

---

## Local Development with Tilt

### Tiltfile Overview

```python
# Tiltfile
load('ext://docker_build', 'docker_build')
load('ext://k8s_yaml', 'k8s_yaml')
load('ext://k8s_resource', 'k8s_resource')
load('ext://local_resource', 'local_resource')

# Settings
default_registry('local.pao.dev')
k8s_context('kind-pao')

# Build all services
services = [
    'api-gateway',
    'companion-api',
    'identity-engine',
    'conversation-engine',
    'memory-engine',
    'relationship-engine',
    'emotion-engine',
    'voice-engine',
    'proactive-engine',
    'safety-engine',
    'evaluation-engine',
]

for svc in services:
    docker_build(f'cmd/{svc}', f'local.pao.dev/{svc}', live_update=[
        sync('./cmd/{svc}/', '/app/'),
        run('go build -o /app/main .', trigger=['go.mod', 'go.sum', '*.go']),
    ])
    k8s_yaml(f'deployments/base/{svc}.yaml')
    k8s_resource(f'{svc}', port_forwards=8080, new_name=f'{svc}-dev')

# Local dependencies (PostgreSQL, Redis, Kafka, etc.)
local_resource('postgres', 'docker-compose up postgres', serve=True)
local_resource('redis', 'docker-compose up redis', serve=True)
local_resource('kafka', 'docker-compose up kafka', serve=True)
local_resource('qdrant', 'docker-compose up qdrant', serve=True)
local_resource('kuzu', 'docker-compose up kuzu', serve=True)

# Tilt UI extensions
k8s_resource('grafana', port_forwards=3000)
k8s_resource('jaeger', port_forwards=16686)
k8s_resource('prometheus', port_forwards=9090)
```

### Live Reload

```go
// main.go - Development mode detection
func main() {
    isDev := os.Getenv("TILT_DEV") == "true"
    
    if isDev {
        // Enable hot reload for templates, config
        go watchConfig()
        go watchTemplates()
    }
    
    // ... rest of main
}
```

---

## Code Standards

### Go Standards

```go
// 1. Package structure
package conversation

// 2. Imports grouped (stdlib, third-party, local)
import (
    "context"
    "errors"
    "fmt"
    "time"
    
    "github.com/google/uuid"
    "github.com/jackc/pgx/v5/pgxpool"
    "go.uber.org/zap"
    
    "github.com/pao/internal/auth"
    "github.com/pao/internal/database"
    "github.com/pao/pkg/models"
)

// 3. Constants first
const (
    DefaultMaxRecallLimit = 50
    DefaultContextWindow  = 8192
)

// 4. Types
type ConversationEngine struct {
    db     *pgxpool.Pool
    logger *zap.Logger
    config Config
}

// 5. Constructor
func NewConversationEngine(db *pgxpool.Pool, logger *zap.Logger, config Config) (*ConversationEngine, error) {
    if db == nil {
        return nil, errors.New("database pool is required")
    }
    return &ConversationEngine{db: db, logger: logger, config: config}, nil
}

// 6. Public methods (alphabetical)
func (e *ConversationEngine) ProcessMessage(ctx context.Context, req *ProcessMessageRequest) (*ProcessMessageResponse, error) {
    // Implementation
}

// 7. Private methods
func (e *ConversationEngine) loadContext(ctx context.Context, companionID uuid.UUID) (*Context, error) {
    // Implementation
}

// 8. Error handling - use custom errors
var (
    ErrCompanionNotFound = errors.New("companion not found")
    ErrInvalidMessage    = errors.New("invalid message")
)

func (e *ConversationEngine) validateMessage(msg string) error {
    if len(msg) == 0 {
        return ErrInvalidMessage
    }
    if len(msg) > e.config.MaxMessageLength {
        return fmt.Errorf("%w: exceeds %d characters", ErrInvalidMessage, e.config.MaxMessageLength)
    }
    return nil
}
```

### Go Linting Rules

```yaml
# .golangci.yml
linters:
  enable:
    - errcheck
    - gosimple
    - govet
    - ineffassign
    - staticcheck
    - unused
    - gofmt
    - goimports
    - misspell
    - unparam
    - nakedret
    - prealloc
    - bodyclose
    - rowserrcheck
    - sqlclosecheck
    - noctx
    - nolintlint
    - exhaustive
    - exhaustruct
    - gocritic
    - gosec

linters-settings:
  gocritic:
    enabled-tags:
      - diagnostic
      - experimental
      - opinionated
      - performance
      - style
    disabled-checks:
      - dupImport
      - ifElseChain
  govet:
    check-shadowing: true
  staticcheck:
    checks: ["all", "-ST1000"]
  gosec:
    excludes:
      - G104  # Errors unhandled (we handle explicitly)
      - G115  # Integer overflow (not applicable in Go)

issues:
  exclude-rules:
    - path: "_test\.go"
      linters:
        - gosec
        - errcheck
    - path: "migrations/"
      linters:
        - sqlclosecheck
  max-issues-per-linter: 0
  max-same-issues: 0

run:
  timeout: 5m
  go: "1.22"
```

### Protobuf Standards

```protobuf
// api/proto/conversation/v1/conversation.proto
syntax = "proto3";

package pao.conversation.v1;

option go_package = "github.com/pao/api/gen/go/pao/conversation/v1";
option java_multiple_files = true;
option java_package = "com.pao.conversation.v1";

// Services
service ConversationEngine {
  rpc ProcessMessage(ProcessMessageRequest) returns (ProcessMessageResponse);
  rpc GetHistory(GetHistoryRequest) returns (GetHistoryResponse);
  rpc StreamMessages(StreamMessagesRequest) returns (stream Message);
}

// Messages
message ProcessMessageRequest {
  string companion_id = 1 [(validate.rules.field).uuid = true];
  string user_id = 2 [(validate.rules).string.uuid = true];
  string content = 3 [(validate.rules).string.min_len = 1, (validate.rules).string.max_len = 10000];
  MessageModality modality = 4;
  map<string, string> metadata = 5;
}

message ProcessMessageResponse {
  string message_id = 1 [(validate.rules).string.uuid = true];
  string content = 2;
  EmotionState emotion = 3;
  repeated string memory_references = 4 [(validate.rules).repeated.items.string.uuid = true];
  bool proactive = 5;
  map<string, string> metadata = 6;
}

// Enums
enum MessageModality {
  MESSAGE_MODALITY_UNSPECIFIED = 0;
  MESSAGE_MODALITY_TEXT = 1;
  MESSAGE_MODALITY_VOICE = 2;
  MESSAGE_MODALITY_IMAGE = 3;
}

// Reusable types
message EmotionState {
  string primary_emotion = 1;
  double valence = 2;      // -1 to 1
  double arousal = 3;      // 0 to 1
  map<string, double> emotions = 4;
}
```

### GraphQL Standards

```graphql
# api/graphql/schema.graphql
type Query {
  """Get a companion by ID"""
  companion(id: ID!): Companion
  
  """Get conversation history"""
  conversationHistory(
    companionId: ID!
    cursor: String
    limit: Int = 50
  ): MessageConnection!
}

type Mutation {
  """Send a message to a companion"""
  sendMessage(input: SendMessageInput!): SendMessagePayload!
  
  """Create a new companion"""
  createCompanion(input: CreateCompanionInput!): CreateCompanionPayload!
}

type Subscription {
  """Real-time message stream"""
  messageReceived(companionId: ID!): Message!
  
  """Proactive message notifications"""
  proactiveGenerated(companionId: ID!): ProactiveMessage!
}

"""Relay-style connection for pagination"""
type MessageConnection {
  edges: [MessageEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type MessageEdge {
  node: Message!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

# Input types with validation directives
input SendMessageInput {
  companionId: ID!
  content: String! @constraint(minLength: 1, maxLength: 10000)
  modality: MessageModality = TEXT
  metadata: JSONObject
}

# Custom scalars
scalar DateTime
scalar JSONObject
scalar ID
```

---

## Testing Strategy

### Test Pyramid

```
        ┌─────────────┐
        │   E2E       │  < 10 tests (critical paths)
        ├─────────────┤
        │ Integration │  ~100 tests (service interactions)
        ├─────────────┤
        │   Unit      │  ~1000+ tests (business logic)
        └─────────────┘
```

### Unit Tests (Go)

```go
// conversation_engine_test.go
package conversation

import (
    "context"
    "testing"
    "time"
    
    "github.com/google/uuid"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
    "github.com/stretchr/testify/require"
    "go.uber.org/zap/zaptest"
    
    "github.com/pao/internal/database"
    "github.com/pao/pkg/models"
)

// Mock implementations
type MockDB struct {
    mock.Mock
}

func (m *MockDB) QueryContext(ctx context.Context, query string, args ...interface{}) (database.Rows, error) {
    ret := m.Called(ctx, query, args)
    return ret.Get(0).(database.Rows), ret.Error(1)
}

func TestConversationEngine_ProcessMessage(t *testing.T) {
    tests := []struct {
        name          string
        setupMock     func(*MockDB)
        request       *ProcessMessageRequest
        expectError   bool
        expectedError error
    }{
        {
            name: "successful text message",
            setupMock: func(m *MockDB) {
                m.On("QueryContext", mock.Anything, mock.Anything, mock.Anything).
                    Return(newMockRows([]map[string]interface{}{
                        {"id": uuid.New(), "content": "Hello!", "role": "companion"},
                    }), nil)
            },
            request: &ProcessMessageRequest{
                CompanionID: uuid.New().String(),
                UserID:      uuid.New().String(),
                Content:     "Hello",
                Modality:    models.MessageModalityText,
            },
            expectError: false,
        },
        {
            name: "empty message returns error",
            request: &ProcessMessageRequest{
                CompanionID: uuid.New().String(),
                UserID:      uuid.New().String(),
                Content:     "",
                Modality:    models.MessageModalityText,
            },
            expectError:   true,
            expectedError: ErrInvalidMessage,
        },
    }
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // Setup
            mockDB := new(MockDB)
            if tt.setupMock != nil {
                tt.setupMock(mockDB)
            }
            
            logger := zaptest.NewLogger(t)
            config := Config{MaxMessageLength: 10000}
            engine, err := NewConversationEngine(mockDB, logger, config)
            require.NoError(t, err)
            
            // Execute
            resp, err := engine.ProcessMessage(context.Background(), tt.request)
            
            // Assert
            if tt.expectError {
                assert.Error(t, err)
                assert.ErrorIs(t, err, tt.expectedError)
                assert.Nil(t, resp)
            } else {
                assert.NoError(t, err)
                assert.NotNil(t, resp)
                assert.NotEmpty(t, resp.MessageID)
            }
            
            mockDB.AssertExpectations(t)
        })
    }
}

// Table-driven test for validation
func TestConversationEngine_ValidateMessage(t *testing.T) {
    testCases := []struct {
        name        string
        message     string
        maxLength   int
        expectError bool
    }{
        {"empty", "", 100, true},
        {"whitespace only", "   ", 100, true},
        {"valid short", "Hello", 100, false},
        {"valid long", strings.Repeat("a", 100), 100, false},
        {"too long", strings.Repeat("a", 101), 100, true},
    }
    
    for _, tc := range testCases {
        t.Run(tc.name, func(t *testing.T) {
            engine := &ConversationEngine{config: Config{MaxMessageLength: tc.maxLength}}
            err := engine.validateMessage(tc.message)
            
            if tc.expectError {
                assert.Error(t, err)
            } else {
                assert.NoError(t, err)
            }
        })
    }
}
```

### Integration Tests

```go
// integration/conversation_integration_test.go
package integration

import (
    "context"
    "testing"
    "time"
    
    "github.com/google/uuid"
    "github.com/jackc/pgx/v5/pgxpool"
    "github.com/stretchr/testify/require"
    "go.uber.org/zap/zaptest"
    
    "github.com/pao/cmd/conversation-engine"
    "github.com/pao/internal/database"
    "github.com/pao/pkg/models"
)

func TestConversationEngine_Integration(t *testing.T) {
    // Requires testcontainers or test database
    if testing.Short() {
        t.Skip("Skipping integration test in short mode")
    }
    
    // Setup test database
    pool := setupTestDB(t)
    defer pool.Close()
    
    // Run migrations
    runMigrations(t, pool)
    
    // Create engine
    logger := zaptest.NewLogger(t)
    config := conversation.Config{
        Database: pool,
        MaxMessageLength: 10000,
    }
    engine, err := conversation.New(config, logger)
    require.NoError(t, err)
    
    // Test data
    companionID := uuid.New()
    userID := uuid.New()
    createTestCompanion(t, pool, companionID, userID)
    
    t.Run("full conversation flow", func(t *testing.T) {
        // Send message
        resp, err := engine.ProcessMessage(context.Background(), &models.ProcessMessageRequest{
            CompanionID: companionID.String(),
            UserID:      userID.String(),
            Content:     "Hello, how are you?",
            Modality:    models.MessageModalityText,
        })
        require.NoError(t, err)
        require.NotEmpty(t, resp.MessageID)
        require.NotEmpty(t, resp.Content)
        
        // Verify message stored
        messages := getMessages(t, pool, companionID)
        require.Len(t, messages, 2) // User + Companion
        assert.Equal(t, "user", messages[0].Role)
        assert.Equal(t, "companion", messages[1].Role)
        
        // Get history
        history, err := engine.GetHistory(context.Background(), &models.GetHistoryRequest{
            CompanionID: companionID.String(),
            Limit:       10,
        })
        require.NoError(t, err)
        require.Len(t, history.Messages, 2)
    })
}
```

### Contract Tests (API)

```go
// contract/api_contract_test.go
package contract

import (
    "testing"
    
    "github.com/pact-foundation/pact-go/v2"
    "github.com/stretchr/testify/require"
)

func TestConversationAPI_Contract(t *testing.T) {
    // Provider test (run against running service)
    if testing.Short() {
        t.Skip("Skipping contract test in short mode")
    }
    
    pact := pact.NewProviderPact(t, pact.ProviderPactOptions{
        Provider: "ConversationEngine",
        ProviderVersion: "1.2.3",
        PactURLs: []string{"https://pact-broker.pao.app/pacts/provider/ConversationEngine/consumer/API-Gateway/latest"},
        BrokerURL: "https://pact-broker.pao.app",
        BrokerToken: os.Getenv("PACT_BROKER_TOKEN"),
        PublishResults: true,
    })
    
    pact.VerifyProvider(t, pact.VerifyProviderOptions{
        ProviderBaseURL: "http://conversation-engine:8080",
        Handlers: map[string]pact.Handler{
            "POST /v1/messages": func(w http.ResponseWriter, r *http.Request) {
                // Provider state setup
                setupProviderState(r.Context(), "a companion exists")
                // Service handles request normally
            },
        },
    })
}
```

### Load Testing

```python
# tests/load/locustfile.py
from locust import HttpUser, task, between, constant
import uuid
import json

class PAOUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Authenticate
        response = self.client.post("/auth/login", json={
            "email": f"loadtest-{uuid.uuid4()}@pao.test",
            "password": "test123"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create companion
        response = self.client.post("/v1/companions", headers=self.headers, json={
            "name": "Test Companion",
            "type": "friend"
        })
        self.companion_id = response.json()["id"]
    
    @task(10)
    def send_message(self):
        self.client.post(f"/v1/companions/{self.companion_id}/messages", 
            headers=self.headers,
            json={
                "content": "Hello, how are you today?",
                "modality": "text"
            }
        )
    
    @task(3)
    def get_history(self):
        self.client.get(f"/v1/companions/{self.companion_id}/messages",
            headers=self.headers,
            params={"limit": 20}
        )
    
    @task(1)
    def trigger_proactive(self):
        self.client.post(f"/v1/companions/{self.companion_id}/proactive/trigger",
            headers=self.headers,
            json={"trigger_type": "milestone", "data": {}}
        )

class VoiceUser(HttpUser):
    wait_time = constant(5)
    
    @task
    def voice_call(self):
        # WebRTC signaling load test
        pass
```

---

## Observability in Development

### Structured Logging

```go
// observability/logger.go
package observability

import (
    "context"
    "go.uber.org/zap"
    "go.uber.org/zap/zapcore"
)

var Logger *zap.Logger

func Init(serviceName, environment string) error {
    config := zap.NewProductionConfig()
    config.ServiceName = serviceName
    config.Environment = environment
    config.Level = zap.NewAtomicLevelAt(zap.InfoLevel)
    config.EncoderConfig.TimeKey = "timestamp"
    config.EncoderConfig.EncodeTime = zapcore.ISO8601TimeEncoder
    config.EncoderConfig.StacktraceKey = "stacktrace"
    
    var err error
    Logger, err = config.Build(
        zap.AddCallerSkip(1),
        zap.AddStacktrace(zap.ErrorLevel),
    )
    return err
}

func WithContext(ctx context.Context, fields ...zap.Field) *zap.Logger {
    return Logger.With(fields...)
}

// Usage
logger := observability.WithContext(ctx, 
    zap.String("companion_id", companionID.String()),
    zap.String("user_id", userID.String()),
    zap.String("trace_id", traceID),
)
logger.Info("Processing message", 
    zap.Int("message_length", len(content)),
    zap.String("modality", modality.String()),
)
```

### Metrics

```go
// observability/metrics.go
package observability

import (
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
)

var (
    // HTTP metrics
    HTTPRequestsTotal = promauto.NewCounterVec(prometheus.CounterOpts{
        Name: "http_requests_total",
        Help: "Total number of HTTP requests",
    }, []string{"service", "method", "path", "status"})
    
    HTTPRequestDuration = promauto.NewHistogramVec(prometheus.HistogramOpts{
        Name:    "http_request_duration_seconds",
        Help:    "HTTP request latency in seconds",
        Buckets: []float64{.005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10},
    }, []string{"service", "method", "path"})
    
    // Business metrics
    MessagesProcessed = promauto.NewCounterVec(prometheus.CounterOpts{
        Name: "messages_processed_total",
        Help: "Total messages processed",
    }, []string{"service", "modality", "status"})
    
    MemoriesRecalled = promauto.NewCounterVec(prometheus.CounterOpts{
        Name: "memories_recalled_total",
        Help: "Total memories recalled",
    }, []string{"service", "memory_type"})
    
    RHIScore = promauto.NewGaugeVec(prometheus.GaugeOpts{
        Name: "relationship_health_index",
        Help: "Current RHI score",
    }, []string{"companion_id"})
    
    // Safety metrics
    SafetyEventsTotal = promauto.NewCounterVec(prometheus.CounterOpts{
        Name: "safety_events_total",
        Help: "Total safety events",
    }, []string{"type", "risk_level", "action_taken"})
    
    CrisisDetectionLatency = promauto.NewHistogram(prometheus.HistogramOpts{
        Name:    "crisis_detection_latency_seconds",
        Help:    "Time to detect crisis",
        Buckets: []float64{.01, .025, .05, .1, .25, .5, 1, 2.5, 5},
    })
)

// Usage in middleware
func MetricsMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        
        wrapped := &responseWriter{ResponseWriter: w, statusCode: 200}
        next.ServeHTTP(wrapped, r)
        
        duration := time.Since(start).Seconds()
        HTTPRequestsTotal.WithLabelValues(
            serviceName, r.Method, r.URL.Path, strconv.Itoa(wrapped.statusCode),
        ).Inc()
        HTTPRequestDuration.WithLabelValues(
            serviceName, r.Method, r.URL.Path,
        ).Observe(duration)
    })
}
```

### Tracing

```go
// observability/tracing.go
package observability

import (
    "context"
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
    "go.opentelemetry.io/otel/propagation"
    "go.opentelemetry.io/otel/sdk/resource"
    "go.opentelemetry.io/otel/sdk/trace"
    semconv "go.opentelemetry.io/otel/semconv/v1.21.0"
)

func InitTracing(serviceName, environment string) (*trace.TracerProvider, error) {
    ctx := context.Background()
    
    exporter, err := otlptracegrpc.New(ctx,
        otlptracegrpc.WithEndpoint("tempo:4317"),
        otlptracegrpc.WithInsecure(),
    )
    if err != nil {
        return nil, err
    }
    
    tp := trace.NewTracerProvider(
        trace.WithBatcher(exporter),
        trace.WithResource(resource.NewWithAttributes(
            semconv.SchemaURL,
            semconv.ServiceName(serviceName),
            semconv.DeploymentEnvironment(environment),
        )),
        trace.WithSampler(trace.ParentBased(trace.TraceIDRatioBased(0.1))),
    )
    
    otel.SetTracerProvider(tp)
    otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(
        propagation.TraceContext{},
        propagation.Baggage{},
    ))
    
    return tp, nil
}

// Usage
func (e *ConversationEngine) ProcessMessage(ctx context.Context, req *Request) (*Response, error) {
    ctx, span := otel.Tracer("conversation-engine").Start(ctx, "ProcessMessage")
    defer span.End()
    
    span.SetAttributes(
        attribute.String("companion_id", req.CompanionID),
        attribute.String("modality", req.Modality.String()),
    )
    
    // ... processing
    span.AddEvent("memory_recall_start")
    memories, err := e.recallMemories(ctx, req)
    span.AddEvent("memory_recall_end", attribute.Int("count", len(memories)))
    
    return resp, nil
}
```

---

## Security in Development

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/golangci/golangci-lint
    rev: v1.56.0
    hooks:
      - id: golangci-lint
        args: [--fast]
  
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: detect-private-key
      - id: detect-aws-credentials
  
  - repo: https://github.com/securego/gosec
    rev: v2.18.0
    hooks:
      - id: gosec
        args: [-exclude=G104,G115]
  
  - repo: https://github.com/trufflesecurity/trufflehog
    rev: v3.63.0
    hooks:
      - id: trufflehog
        args: [--no-verification]
  
  - repo: local
    hooks:
      - id: go-test
        name: go test
        entry: go test ./...
        language: system
        pass_filenames: false
        stages: [commit]
      - id: buf-lint
        name: buf lint
        entry: buf lint
        language: system
        pass_filenames: false
```

### Dependency Management

```bash
# Go modules
go mod tidy
go mod verify
go mod download

# Check for vulnerabilities
govulncheck ./...

# Update dependencies
go get -u ./...
go mod tidy

# License check
go-licenses check ./...
```

---

## Performance Profiling

### CPU Profiling

```bash
# Start pprof server
go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30

# Or in code
import _ "net/http/pprof"

func main() {
    go func() {
        log.Println(http.ListenAndServe("localhost:6060", nil))
    }()
    // ...
}
```

### Memory Profiling

```bash
# Heap profile
go tool pprof http://localhost:6060/debug/pprof/heap

# Allocation profile
go tool pprof http://localhost:6060/debug/pprof/allocs
```

### Benchmarking

```go
// benchmark_test.go
func BenchmarkProcessMessage(b *testing.B) {
    engine := setupBenchmarkEngine(b)
    req := &ProcessMessageRequest{
        CompanionID: uuid.New().String(),
        UserID:      uuid.New().String(),
        Content:     "Hello, how are you today?",
        Modality:    models.MessageModalityText,
    }
    
    b.ResetTimer()
    b.ReportAllocs()
    
    for i := 0; i < b.N; i++ {
        _, err := engine.ProcessMessage(context.Background(), req)
        if err != nil {
            b.Fatal(err)
        }
    }
}

func BenchmarkMemoryRecall(b *testing.B) {
    engine := setupBenchmarkEngine(b)
    companionID := uuid.New()
    
    // Pre-populate memories
    populateMemories(b, engine, companionID, 10000)
    
    b.ResetTimer()
    b.ReportAllocs()
    
    for i := 0; i < b.N; i++ {
        _, err := engine.RecallMemories(context.Background(), &RecallRequest{
            CompanionID: companionID.String(),
            Query:       "memories about childhood",
            Limit:       10,
        })
        if err != nil {
            b.Fatal(err)
        }
    }
}
```

---

## Debugging Tips

### Common Issues

| Issue | Debug Command |
|-------|---------------|
| Pod not starting | `kubectl describe pod <pod>` / `kubectl logs <pod>` |
| Service not reachable | `kubectl exec -it <pod> -- curl localhost:8080/health` |
| Database connection | `kubectl exec -it <pod> -- pg_isready -h postgresql` |
| High memory | `kubectl top pods` / `go tool pprof` |
| Slow queries | `EXPLAIN ANALYZE` in psql |
| Istio issues | `istioctl proxy-config all <pod>` |

### Useful Aliases

```bash
# ~/.bashrc or ~/.zshrc
alias k='kubectl'
alias kg='kubectl get'
alias kd='kubectl describe'
alias kl='kubectl logs'
alias ke='kubectl exec -it'
alias kctx='kubectx'
alias kns='kubens'
alias stern='stern --since 1h'
alias tilt-up='tilt up --stream'
```

---

## Documentation Standards

### Code Comments

```go
// ProcessMessage handles an incoming message from a user to a companion.
// It performs safety checks, recalls relevant memories, generates a response,
// and stores the interaction.
//
// The method returns the companion's response along with any recalled memories
// and emotional state. If safety controls block the message, an error is returned
// with details about the intervention.
//
// Example:
//
//	resp, err := engine.ProcessMessage(ctx, &ProcessMessageRequest{
//	    CompanionID: "uuid",
//	    UserID:      "uuid",
//	    Content:     "Hello!",
//	    Modality:    MessageModalityText,
//	})
func (e *ConversationEngine) ProcessMessage(ctx context.Context, req *ProcessMessageRequest) (*ProcessMessageResponse, error) {
    // ...
}
```

### Architecture Decision Records (ADRs)

See `docs/07-adr/` for template and process.

---

**Aligned With:** `300-system-architecture.md`, `350-deployment.md`, `CONTRIBUTING.md`
**Next Review:** 2026-01-17