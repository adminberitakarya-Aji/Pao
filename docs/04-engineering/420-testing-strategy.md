# PAO Testing Strategy

**Version:** 1.0
**Status:** Draft
**Owner:** PAO Quality Engineering Team

---

## Overview

This document defines the comprehensive testing strategy for PAO, covering all test types, tools, processes, and quality gates.

> **Testing Principle:** Quality is built in, not tested in. Fast feedback at every layer, automated quality gates, production-like environments.

---

## Testing Pyramid

```
                    ┌─────────────────┐
                    │  E2E / Journey  │  ███ < 50 tests
                    │   (Critical)    │
                    ├─────────────────┤
                    │  Contract Tests │  ███ ~100 tests
                    ├─────────────────┤
              ┌─────│ Integration     │  █████ ~500 tests
              │     │ (Service)       │
              │     ├─────────────────┤
Unit  ███████████████│  Component      │  ██████████ ~2000 tests
Tests ███████████████│  (Module)       │
              │     ├─────────────────┤
              └─────│  Static Analysis │  ██████████ Continuous
                    └─────────────────┘
```

### Test Distribution Targets

| Layer | Count | Execution Time | Frequency | Environment |
|-------|-------|----------------|-----------|-------------|
| Static Analysis | Continuous | < 1 min | Every commit | Local/CI |
| Unit Tests | ~2000 | < 5 min | Every commit | Local/CI |
| Component Tests | ~500 | < 10 min | Every PR | CI |
| Integration Tests | ~500 | < 15 min | Every PR | Staging |
| Contract Tests | ~100 | < 5 min | Every PR | CI |
| E2E Tests | < 50 | < 30 min | Nightly/Release | Staging/Production |
| Load Tests | ~20 | < 1 hour | Weekly | Staging |
| Chaos Tests | ~10 | < 2 hours | Monthly | Staging |

---

## Test Types & Implementation

### 1. Static Analysis

```yaml
# Tools & Configuration
tools:
  go:
    - golangci-lint (comprehensive)
    - govulncheck (vulnerabilities)
    - go vet (stdlib)
    - staticcheck (advanced)
    - gosec (security)
    - errcheck (error handling)
    - unused (dead code)
  
  protobuf:
    - buf lint (style, breaking changes)
    - buf breaking (compatibility)
  
  yaml:
    - yamllint
    - kubeconform (Kubernetes manifests)
  
  docker:
    - hadolint
    - trivy (vulnerabilities)
  
  secrets:
    - trufflehog
    - gitleaks
  
  licenses:
    - fossa
    - go-licenses

ci_integration:
  - Runs on every push
  - Blocks merge on failures
  - SARIF upload to GitHub Security
```

### 2. Unit Tests

```go
// Standards
// - Test pure functions, business logic
// - No external dependencies (mock everything)
// - Fast (< 10ms per test)
// - Deterministic
// - Table-driven for multiple cases

// Example: Memory Engine - Consolidation Logic
func TestConsolidationEngine_ShouldConsolidate(t *testing.T) {
    testCases := []struct {
        name           string
        memory         *models.Memory
        accessCount    int
        lastAccessed   time.Time
        expectedResult bool
    }{
        {
            name: "high access recent memory consolidates",
            memory: &models.Memory{
                Type:        models.MemoryTypeEpisodic,
                AccessCount: 10,
                LastAccessed: time.Now().Add(-1 * time.Hour),
            },
            expectedResult: true,
        },
        {
            name: "low access old memory doesn't consolidate",
            memory: &models.Memory{
                Type:        models.MemoryTypeEpisodic,
                AccessCount: 1,
                LastAccessed: time.Now().Add(-30 * 24 * time.Hour),
            },
            expectedResult: false,
        },
        {
            name: "semantic memories never consolidate",
            memory: &models.Memory{
                Type:        models.MemoryTypeSemantic,
                AccessCount: 100,
                LastAccessed: time.Now(),
            },
            expectedResult: false,
        },
    }
    
    for _, tc := range testCases {
        t.Run(tc.name, func(t *testing.T) {
            engine := NewConsolidationEngine(DefaultConsolidationConfig())
            result := engine.ShouldConsolidate(tc.memory)
            assert.Equal(t, tc.expectedResult, result)
        })
    }
}

// Mock generation
//go:generate mockgen -source=./storage.go -destination=./mocks/storage_mock.go -package=mocks Storage
```

### 3. Component Tests

```go
// Test a module with its internal dependencies but external dependencies mocked
// Example: Conversation Engine with mocked Memory, Relationship, Safety

func TestConversationEngine_ProcessMessage_Component(t *testing.T) {
    // Setup real engine with mocked dependencies
    mockMemory := mocks.NewMemoryClient(t)
    mockRelationship := mocks.NewRelationshipClient(t)
    mockSafety := mocks.NewSafetyClient(t)
    mockLLM := mocks.NewLLMClient(t)
    
    engine := conversation.NewEngine(
        conversation.WithMemoryClient(mockMemory),
        conversation.WithRelationshipClient(mockRelationship),
        conversation.WithSafetyClient(mockSafety),
        conversation.WithLLMClient(mockLLM),
    )
    
    // Test happy path
    t.Run("successful conversation turn", func(t *testing.T) {
        companionID := uuid.New()
        userID := uuid.New()
        
        // Setup mocks
        mockMemory.On("RecallMemories", mock.Anything, mock.Anything).
            Return([]*models.Memory{{Content: "User likes cats"}}, nil)
        
        mockRelationship.On("GetState", mock.Anything, companionID).
            Return(&models.RelationshipState{Trust: 7.5}, nil)
        
        mockSafety.On("Check", mock.Anything, mock.Anything).
            Return(&safety.CheckResult{Allowed: true}, nil)
        
        mockLLM.On("Generate", mock.Anything, mock.Anything).
            Return("That's wonderful! Cats are great companions.", nil)
        
        // Execute
        resp, err := engine.ProcessMessage(context.Background(), &ProcessMessageRequest{
            CompanionID: companionID.String(),
            UserID:      userID.String(),
            Content:     "I love my cat!",
        })
        
        // Assert
        assert.NoError(t, err)
        assert.Contains(t, resp.Content, "cat")
        
        // Verify memory was stored
        mockMemory.AssertCalled(t, "StoreMemory", mock.Anything, mock.MatchedBy(
            func(m *models.Memory) bool {
                return m.Type == models.MemoryTypeEpisodic
            },
        ))
    })
}
```

### 4. Integration Tests

```go
// Test service interactions with REAL infrastructure
// Run against testcontainers or staging namespace

func TestConversationEngine_Integration(t *testing.T) {
    if testing.Short() {
        t.Skip("Skipping integration test")
    }
    
    // Start test infrastructure
    ctx := context.Background()
    
    // PostgreSQL
    pgContainer := startPostgreSQL(ctx, t)
    defer pgContainer.Terminate(ctx)
    
    // Redis
    redisContainer := startRedis(ctx, t)
    defer redisContainer.Terminate(ctx)
    
    // Qdrant
    qdrantContainer := startQdrant(ctx, t)
    defer qdrantContainer.Terminate(ctx)
    
    // Run migrations
    runMigrations(t, pgContainer.ConnectionString())
    
    // Create engine with REAL clients
    engine := createIntegrationEngine(t, pgContainer, redisContainer, qdrantContainer)
    
    // Test full flow
    t.Run("full message processing with memory recall", func(t *testing.T) {
        companionID := createTestCompanion(t, engine.DB())
        userID := uuid.New()
        
        // Send first message
        resp1, err := engine.ProcessMessage(ctx, &ProcessMessageRequest{
            CompanionID: companionID.String(),
            UserID:      userID.String(),
            Content:     "My name is Alex and I'm a software engineer.",
        })
        require.NoError(t, err)
        
        // Send second message - should recall name
        resp2, err := engine.ProcessMessage(ctx, &ProcessMessageRequest{
            CompanionID: companionID.String(),
            UserID:      userID.String(),
            Content:     "What's my name?",
        })
        require.NoError(t, err)
        assert.Contains(t, strings.ToLower(resp2.Content), "alex")
        
        // Verify memory was created and recalled
        memories := getMemories(t, engine.DB(), companionID)
        assert.Contains(t, memories, "Alex")
        assert.Contains(t, memories, "software engineer")
    })
}
```

### 5. Contract Tests

```go
// Consumer-Driven Contracts with Pact
// Provider: Conversation Engine
// Consumers: API Gateway, Mobile App, Web App

// pact/conversation_engine_test.go
func TestConversationEngine_PactProvider(t *testing.T) {
    // Verify provider against published contracts
    pact.VerifyProvider(t, pact.VerifyProviderOptions{
        Provider:         "ConversationEngine",
        ProviderVersion:  version.Version,
        PactURLs: []string{
            "https://pact-broker.pao.app/pacts/provider/ConversationEngine/consumer/API-Gateway/latest",
            "https://pact-broker.pao.app/pacts/provider/ConversationEngine/consumer/Mobile-App/latest",
        },
        BrokerURL:      "https://pact-broker.pao.app",
        BrokerToken:    os.Getenv("PACT_BROKER_TOKEN"),
        PublishResults: true,
        
        // Provider state setup
        StateHandlers: map[string]pact.StateHandler{
            "a companion exists": func(ctx context.Context, params map[string]interface{}) error {
                return setupCompanion(ctx, params)
            },
            "a companion has memories": func(ctx context.Context, params map[string]interface{}) error {
                return setupMemories(ctx, params)
            },
            "safety check passes": func(ctx context.Context, params map[string]interface{}) error {
                return setupSafetyPass(ctx, params)
            },
        },
    })
}

// Consumer test example (in API Gateway repo)
func TestAPIGateway_SendMessage_Contract(t *testing.T) {
    pact := pact.NewConsumerPact(t, pact.ConsumerPactOptions{
        Consumer: "API-Gateway",
        Provider: "ConversationEngine",
    })
    
    pact.
        AddInteraction().
        Given("a companion exists").
        UponReceiving("a request to send a message").
        WithRequest(pact.Request{
            Method: "POST",
            Path:   "/v1/messages",
            Headers: map[string]string{
                "Content-Type": "application/json",
            },
            Body: map[string]interface{}{
                "companion_id": "uuid",
                "content":      "Hello",
                "modality":     "text",
            },
        }).
        WillRespondWith(pact.Response{
            Status: 200,
            Headers: map[string]string{
                "Content-Type": "application/json",
            },
            Body: map[string]interface{}{
                "message_id": "uuid",
                "content":    "Hello! How can I help?",
            },
        }).
        ExecuteTest(t, func(config pact.MockServerConfig) error {
            // Test against mock server
            client := NewConversationClient(config.URL)
            resp, err := client.SendMessage(context.Background(), SendMessageRequest{
                CompanionID: "uuid",
                Content:     "Hello",
            })
            assert.NoError(t, err)
            assert.NotEmpty(t, resp.MessageID)
            return nil
        })
}
```

### 6. E2E Tests

```go
// Critical user journeys only
// Run against staging environment

func TestE2E_NewUserJourney(t *testing.T) {
    if testing.Short() {
        t.Skip("Skipping E2E test")
    }
    
    client := NewE2EClient("https://api-staging.pao.app")
    
    t.Run("complete new user onboarding", func(t *testing.T) {
        // 1. Sign up
        user := client.SignUp(t, SignUpRequest{
            Email:    fmt.Sprintf("e2e-%s@pao.test", uuid.New()),
            Password: "SecurePass123!",
            Name:     "E2E Test User",
        })
        assert.NotEmpty(t, user.ID)
        
        // 2. Create companion
        companion := client.CreateCompanion(t, user.Token, CreateCompanionRequest{
            Name: "Alex",
            Type: "friend",
            IdentityConfig: IdentityConfig{
                Personality: "warm, curious, supportive",
            },
        })
        assert.NotEmpty(t, companion.ID)
        
        // 3. First conversation
        resp := client.SendMessage(t, user.Token, companion.ID, SendMessageRequest{
            Content:  "Hi! I'm new here.",
            Modality: "text",
        })
        assert.NotEmpty(t, resp.MessageID)
        assert.Contains(t, strings.ToLower(resp.Content), "welcome")
        
        // 4. Check relationship state
        rel := client.GetRelationship(t, user.Token, companion.ID)
        assert.Greater(t, rel.Trust, 0.0)
        
        // 5. Trigger proactive
        proactive := client.WaitForProactive(t, user.Token, companion.ID, 30*time.Second)
        assert.NotNil(t, proactive)
    })
}
```

### 7. Load Tests

```python
# tests/load/locustfile.py
from locust import HttpUser, task, between, constant, events
import uuid
import json
import os

class PAOUser(HttpUser):
    wait_time = between(1, 3)
    host = os.getenv("TARGET_HOST", "https://api-staging.pao.app")
    
    def on_start(self):
        # Authenticate
        email = f"loadtest-{uuid.uuid4()}@pao.test"
        response = self.client.post("/auth/register", json={
            "email": email,
            "password": "LoadTest123!",
            "name": "Load Test User"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create companion
        response = self.client.post("/v1/companions", headers=self.headers, json={
            "name": "Test Companion",
            "type": "friend"
        })
        self.companion_id = response.json()["id"]
    
    @task(50)
    def send_text_message(self):
        self.client.post(f"/v1/companions/{self.companion_id}/messages", 
            headers=self.headers,
            json={"content": "Hello, how are you?", "modality": "text"},
            name="/v1/companions/:id/messages"
        )
    
    @task(10)
    def get_history(self):
        self.client.get(f"/v1/companions/{self.companion_id}/messages",
            headers=self.headers,
            params={"limit": 20},
            name="/v1/companions/:id/messages (GET)"
        )
    
    @task(5)
    def recall_memories(self):
        self.client.post(f"/v1/companions/{self.companion_id}/memories/recall",
            headers=self.headers,
            json={"query": "conversation about work", "limit": 10},
            name="/v1/companions/:id/memories/recall"
        )
    
    @task(1)
    def voice_call_signaling(self):
        # WebRTC signaling only (no media)
        self.client.post(f"/v1/companions/{self.companion_id}/voice/start",
            headers=self.headers,
            json={"codec": "opus"},
            name="/v1/companions/:id/voice/start"
        )

class ProactiveUser(HttpUser):
    """Simulates proactive message generation load"""
    wait_time = constant(30)
    weight = 0.1  # 10% of users
    
    @task
    def trigger_proactive(self):
        self.client.post(f"/v1/companions/{self.companion_id}/proactive/trigger",
            headers=self.headers,
            json={"trigger_type": "milestone", "data": {"days": 30}},
            name="/v1/companions/:id/proactive/trigger"
        )

# Custom load shapes
class StagesShape:
    stages = [
        {"duration": "2m", "users": 10, "spawn_rate": 5},
        {"duration": "5m", "users": 50, "spawn_rate": 10},
        {"duration": "10m", "users": 100, "spawn_rate": 10},
        {"duration": "5m", "users": 200, "spawn_rate": 20},
        {"duration": "10m", "users": 100, "spawn_rate": 10},
        {"duration": "5m", "users": 10, "spawn_rate": 10},
    ]

# Thresholds
# - 99th percentile < 500ms for message send
# - Error rate < 0.1%
# - 95th percentile < 200ms for memory recall
```

### 8. Chaos Engineering

```yaml
# Chaos experiments (Chaos Mesh / Litmus)
experiments:
  - name: "pod-failure"
    description: "Kill random pods, verify self-healing"
    target: "conversation-engine, memory-engine"
    duration: "5m"
    sla: "No 5xx errors, latency < 2x baseline"
  
  - name: "network-latency"
    description: "Add 200ms latency between services"
    target: "all services"
    duration: "10m"
    sla: "P99 < 1s, no timeouts"
  
  - name: "database-failure"
    description: "Fail primary DB, verify replica promotion"
    target: "postgresql"
    duration: "2m"
    sla: "RPO < 1s, RTO < 30s"
  
  - name: "kafka-broker-down"
    description: "Stop one Kafka broker"
    target: "kafka"
    duration: "5m"
    sla: "No message loss, consumer lag < 1000"
  
  - name: "memory-pressure"
    description: "Limit container memory to 50%"
    target: "ml-inference pods"
    duration: "5m"
    sla: "No OOM kills, graceful degradation"
  
  - name: "zone-failure"
    description: "Simulate AZ outage"
    target: "entire cluster"
    duration: "10m"
    sla: "Multi-AZ services stay healthy"
```

---

## Test Infrastructure

### Testcontainers (Local/CI)

```go
// testcontainers/setup.go
package testcontainers

import (
    "context"
    "testing"
    
    "github.com/testcontainers/testcontainers-go"
    "github.com/testcontainers/testcontainers-go/modules/postgres"
    "github.com/testcontainers/testcontainers-go/modules/redis"
    "github.com/testcontainers/testcontainers-go/modules/kafka"
    "github.com/testcontainers/testcontainers-go/wait"
)

func StartPostgreSQL(ctx context.Context, t *testing.T) *postgres.PostgresContainer {
    t.Helper()
    
    container, err := postgres.Run(ctx,
        "pgvector/pgvector:pg16",
        postgres.WithDatabase("pao_test"),
        postgres.WithUsername("test"),
        postgres.WithPassword("test"),
        testcontainers.WithWaitStrategy(
            wait.ForLog("database system is ready to accept connections").
                WithOccurrence(2).
                WithStartupTimeout(60*time.Second),
        ),
    )
    require.NoError(t, err)
    
    t.Cleanup(func() {
        container.Terminate(ctx)
    })
    
    return container
}

func StartRedis(ctx context.Context, t *testing.T) *redis.RedisContainer {
    t.Helper()
    
    container, err := redis.Run(ctx,
        "redis:7-alpine",
        testcontainers.WithWaitStrategy(
            wait.ForLog("Ready to accept connections").
                WithStartupTimeout(30*time.Second),
        ),
    )
    require.NoError(t, err)
    
    t.Cleanup(func() {
        container.Terminate(ctx)
    })
    
    return container
}

func StartQdrant(ctx context.Context, t *testing.T) *testcontainers.Container {
    t.Helper()
    
    req := testcontainers.ContainerRequest{
        Image:        "qdrant/qdrant:latest",
        ExposedPorts: []string{"6333/tcp", "6334/tcp"},
        WaitingFor:   wait.ForHTTP("/healthz").WithPort("6333"),
    }
    
    container, err := testcontainers.GenericContainer(ctx, testcontainers.GenericContainerRequest{
        ContainerRequest: req,
        Started:          true,
    })
    require.NoError(t, err)
    
    t.Cleanup(func() {
        container.Terminate(ctx)
    })
    
    return container
}
```

### Staging Environment

```yaml
# Staging namespace configuration
staging:
  namespace: pao-staging
  
  # Scaled down production
  replicas:
    api-gateway: 2
    companion-api: 2
    conversation-engine: 3
    memory-engine: 3
    relationship-engine: 2
    emotion-engine: 2
    voice-engine: 2
    proactive-engine: 2
    safety-engine: 3  # Never scale down
    evaluation-engine: 1
  
  # Anonymized production data
  data:
    source: "production-anonymized"
    refresh_schedule: "0 3 * * *"  # Daily
    tables_excluded: ["audit_log", "safety_events", "interventions"]
  
  # External dependencies (mocked or real)
  dependencies:
    postgresql: "staging-rds"
    redis: "staging-elasticache"
    qdrant: "staging-qdrant"
    kafka: "staging-msk"
    llm: "mock-llm-service"  # Deterministic responses
  
  # Feature flags for testing
  feature_flags:
    new_memory_engine: true
    proactive_v2: true
    voice_streaming: true
```

---

## Quality Gates

### CI Pipeline Gates

```yaml
# .github/workflows/ci.yaml
jobs:
  static-analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: make lint
      - run: make security-scan
      - run: make license-check
  
  unit-tests:
    runs-on: ubuntu-latest
    needs: static-analysis
    steps:
      - uses: actions/checkout@v4
      - run: make test-unit
      - uses: codecov/codecov-action@v3
        with:
          flags: unit
          fail_ci_if_error: true
  
  component-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4
      - run: make test-component
  
  integration-tests:
    runs-on: ubuntu-latest
    needs: component-tests
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to staging
        run: |
          kubectl set image deployment/conversation-engine \
            conversation-engine=ghcr.io/pao/conversation-engine:${{ github.sha }}
      - run: make test-integration
  
  contract-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4
      - run: make test-contract
  
  build-images:
    runs-on: ubuntu-latest
    needs: [integration-tests, contract-tests]
    strategy:
      matrix:
        service: [all services]
    steps:
      - uses: actions/checkout@v4
      - run: make build-image SERVICE=${{ matrix.service }}
      - run: make scan-image IMAGE=ghcr.io/pao/${{ matrix.service }}:${{ github.sha }}
      - run: make sign-image IMAGE=ghcr.io/pao/${{ matrix.service }}:${{ github.sha }}
  
  deploy-staging:
    runs-on: ubuntu-latest
    needs: build-images
    environment: staging
    steps:
      - run: argocd app sync pao-staging --prune
      - run: make smoke-test ENV=staging
  
  deploy-canary:
    runs-on: ubuntu-latest
    needs: deploy-staging
    environment: production
    steps:
      - run: argocd app set pao-production --parameter image.tag=${{ github.sha }}
      - run: argocd app sync pao-production --selector canary=true
      - run: make canary-analysis DURATION=30m
  
  deploy-production:
    runs-on: ubuntu-latest
    needs: deploy-canary
    environment: production
    steps:
      - run: argocd app sync pao-production --prune
      - run: make post-deploy-check
```

### Quality Gate Thresholds

| Metric | Threshold | Action on Fail |
|--------|-----------|----------------|
| Code Coverage (Unit) | > 80% | Block merge |
| Code Coverage (Integration) | > 60% | Warn |
| Static Analysis Issues | 0 Critical/High | Block merge |
| Vulnerabilities | 0 Critical/High | Block merge |
| Unit Test Pass Rate | 100% | Block merge |
| Integration Test Pass Rate | 100% | Block merge |
| Contract Test Pass Rate | 100% | Block merge |
| Build Time | < 20 min | Warn |
| Deploy Time | < 10 min | Warn |
| Canary Error Rate | < 0.1% | Auto-rollback |
| Canary Latency P99 | < 1.5x baseline | Auto-rollback |

---

## Test Data Management

### Synthetic Data Generation

```go
// testdata/generator.go
package testdata

import (
    "github.com/brianvoe/gofakeit/v7"
    "github.com/google/uuid"
    "github.com/pao/pkg/models"
)

func GenerateCompanion(opts ...CompanionOption) *models.Companion {
    c := &models.Companion{
        ID:        uuid.New(),
        UserID:    uuid.New(),
        Name:      gofakeit.Name(),
        Type:      randomCompanionType(),
        IsActive:  true,
        CreatedAt: gofakeit.DateRange(time.Now().Add(-365*24*time.Hour), time.Now()),
    }
    
    for _, opt := range opts {
        opt(c)
    }
    return c
}

func GenerateMemories(companionID uuid.UUID, count int) []*models.Memory {
    memories := make([]*models.Memory, count)
    for i := 0; i < count; i++ {
        memories[i] = &models.Memory{
            ID:           uuid.New(),
            CompanionID:  companionID,
            Type:         randomMemoryType(),
            Content:      generateMemoryContent(),
            CreatedAt:    gofakeit.DateRange(time.Now().Add(-90*24*time.Hour), time.Now()),
            AccessCount:  gofakeit.Number(0, 50),
        }
    }
    return memories
}

func GenerateConversation(companionID, userID uuid.UUID, turns int) []*models.Message {
    messages := make([]*models.Message, turns*2)
    for i := 0; i < turns; i++ {
        // User message
        messages[i*2] = &models.Message{
            ID:           uuid.New(),
            CompanionID:  companionID,
            Role:         "user",
            Content:      gofakeit.Sentence(10),
            Modality:     models.MessageModalityText,
            CreatedAt:    gofakeit.DateRange(time.Now().Add(-30*24*time.Hour), time.Now()),
        }
        // Companion response
        messages[i*2+1] = &models.Message{
            ID:           uuid.New(),
            CompanionID:  companionID,
            Role:         "companion",
            Content:      gofakeit.Sentence(15),
            Modality:     models.MessageModalityText,
            CreatedAt:    messages[i*2].CreatedAt.Add(time.Second),
        }
    }
    return messages
}
```

### Data Anonymization

```python
# scripts/anonymize_production_data.py
import pandas as pd
import hashlib
import uuid

def anonymize_dataframe(df, pii_columns):
    """Anonymize PII columns in dataframe"""
    for col in pii_columns:
        if col in df.columns:
            if df[col].dtype == 'object':
                # Hash emails
                if 'email' in col.lower():
                    df[col] = df[col].apply(lambda x: hash_email(x) if pd.notna(x) else x)
                # Replace names
                elif 'name' in col.lower():
                    df[col] = df[col].apply(lambda x: fake.name() if pd.notna(x) else x)
                # Replace text content
                elif 'content' in col.lower() or 'text' in col.lower():
                    df[col] = df[col].apply(lambda x: fake.paragraph() if pd.notna(x) else x)
    return df

def hash_email(email):
    """Consistent hash for email"""
    return hashlib.sha256(email.encode()).hexdigest()[:16] + "@anonymized.pao"

# Tables to anonymize
TABLES = {
    "users": ["email", "name"],
    "companions": ["name", "description"],
    "messages": ["content"],
    "memories": ["event", "fact", "content", "trigger", "narrative_arc"],
    "diary_entries": ["user_text", "companion_reflection"],
}
```

---

## Monitoring Test Health

### Test Metrics Dashboard

```yaml
# Grafana panels for test health
dashboards:
  - name: "Test Execution"
    panels:
      - title: "Test Pass Rate (24h)"
        query: "sum(rate(test_passed_total[24h])) / sum(rate(test_total_total[24h]))"
        target: "> 0.99"
      
      - title: "Test Duration Trend"
        query: "histogram_quantile(0.95, rate(test_duration_seconds_bucket[1h]))"
        target: "< 300s (unit), < 900s (integration)"
      
      - title: "Flaky Test Rate"
        query: "sum(rate(test_flaky_total[7d])) / sum(rate(test_total_total[7d]))"
        target: "< 0.01"
      
      - title: "Coverage Trend"
        query: "code_coverage_percentage"
        target: "> 80%"
  
  - name: "Test Reliability"
    panels:
      - title: "Top Flaky Tests"
        query: "topk(10, sum by (test_name) (rate(test_flaky_total[7d])))"
      
      - title: "Slowest Tests"
        query: "topk(10, avg by (test_name) (test_duration_seconds))"
      
      - title: "Test Debt (Skipped Tests)"
        query: "sum(test_skipped_total)"
```

### Flaky Test Management

```go
// Automatic flaky test detection
// Quarantine flaky tests, create issue, track fix

func FlakyTestDetector() {
    // Query test results from last 7 days
    // Identify tests that pass/fail non-deterministically
    // Criteria: > 2 flakes in 7 days, > 1% flake rate
    
    // Actions:
    // 1. Add @flaky annotation
    // 2. Create GitHub issue with test name, frequency
    // 3. Exclude from required gates (but still run)
    // 4. Assign to team for fix within 2 weeks
    // 5. Auto-close issue when fixed (0 flakes for 7 days)
}
```

---

## Testing Best Practices

### Do's ✅

- Write tests first (TDD for new features)
- Test behavior, not implementation
- Use table-driven tests for multiple cases
- Mock at interface boundaries
- Use testcontainers for integration tests
- Keep tests fast and deterministic
- Name tests clearly: `Test<Unit>_<Scenario>_<Expected>`
- Test error paths and edge cases
- Use realistic test data
- Clean up test resources

### Don'ts ❌

- Don't test private methods directly
- Don't depend on test execution order
- Don't use sleep/wait for synchronization
- Don't share state between tests
- Don't test framework code
- Don't ignore flaky tests
- Don't skip tests without reason
- Don't test implementation details
- Don't use production data in tests
- Don't write tests that only assert "no error"

---

## Testing Roadmap

### Phase 1 (Current)
- [x] Unit test framework established
- [x] Integration tests with testcontainers
- [x] Contract testing with Pact
- [x] E2E tests for critical journeys
- [x] Load testing with Locust
- [x] Chaos engineering experiments
- [x] CI quality gates

### Phase 2 (6 months)
- [ ] Property-based testing (Rapid)
- [ ] Mutation testing (go-mutesting)
- [ ] Visual regression testing (Chromatic)
- [ ] API fuzzing (go-fuzz)
- [ ] Automated test generation (AI-assisted)
- [ ] Test impact analysis (run only affected tests)

### Phase 3 (12 months)
- [ ] Continuous verification in production
- [ ] Synthetic monitoring as tests
- [ ] Chaos engineering in production (controlled)
- [ ] Self-healing test infrastructure
- [ ] Predictive test selection

---

**Aligned With:** `400-development-guide.md`, `410-api-guidelines.md`, `350-deployment.md`
**Next Review:** 2026-01-17