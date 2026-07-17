# PAO Observability Guide

**Version:** 1.0
**Status:** Draft
**Owner:** PAO Platform Team

---

## Overview

This document defines the observability strategy, standards, and implementation for PAO across metrics, logs, traces, and profiling.

> **Observability Principle:** You can't improve what you can't measure. Comprehensive, correlated, and actionable telemetry.

---

## Four Pillars of Observability

```
┌─────────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY STACK                          │
├─────────────────┬─────────────────┬─────────────────┬───────────┤
│     METRICS     │      LOGS       │     TRACES      │ PROFILING │
├─────────────────┼─────────────────┼─────────────────┼───────────┤
│ Prometheus      │ Loki            │ Tempo           │ Pyroscope │
│ Grafana         │ Grafana         │ Grafana         │ Grafana   │
│ Alertmanager    │ LogQL           │ TraceQL         │           │
└─────────────────┴─────────────────┴─────────────────┴───────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   CORRELATION   │
                    │  (Trace ID,     │
                    │   Span ID,      │
                    │   Exemplars)    │
                    └─────────────────┘
```

---

## Metrics

### Metric Types & Naming

```prometheus
# Counter - monotonically increasing
http_requests_total{service="conversation-engine",method="POST",path="/v1/messages",status="200"}

# Gauge - instantaneous value
memory_usage_bytes{service="memory-engine",type="heap"}

# Histogram - distribution with buckets
http_request_duration_seconds_bucket{service="api-gateway",le="0.5"}

# Summary - quantiles calculated client-side
grpc_request_duration_seconds{service="conversation-engine",quantile="0.99"}
```

### Naming Convention

```
<namespace>_<subsystem>_<name>_<unit>

Examples:
- pao_http_requests_total
- pao_memory_memories_recalled_total
- pao_relationship_rhi_score
- pao_voice_call_duration_seconds
- pao_safety_crisis_detected_total
- pao_proactive_generated_total
- pao_evaluation_score
```

### Standard Labels

```yaml
# Required on all metrics
service: "conversation-engine"          # Service name
environment: "production"               # Environment
version: "1.2.3"                        # App version
region: "us-east-1"                     # Deployment region

# Recommended
instance: "pod-name"                    # Pod identifier
job: "kubernetes-pods"                  # Scrape job

# Business context (cardinality controlled)
companion_type: "friend|partner|mentor" # Low cardinality
user_tier: "free|pro|premium"           # Low cardinality
```

### Key Metrics by Domain

#### API Gateway
```prometheus
# RED Metrics
pao_http_requests_total{service,method,path,status}
pao_http_request_duration_seconds{service,method,path}
pao_http_request_size_bytes{service,method,path}
pao_http_response_size_bytes{service,method,path}

# Rate limiting
pao_rate_limit_exceeded_total{service,client_ip}
pao_rate_limit_remaining{service,client_ip}
```

#### Conversation Engine
```prometheus
# Business metrics
pao_messages_processed_total{service,modality,status}
pao_message_processing_duration_seconds{service,modality}
pao_context_window_utilization{service}
pao_llm_token_usage_total{service,model,type}  # prompt, completion
pao_llm_cost_usd_total{service,model}
```

#### Memory Engine
```prometheus
pao_memories_stored_total{service,type}
pao_memories_recalled_total{service,type}
pao_memory_recall_duration_seconds{service,type}
pao_memory_consolidation_duration_seconds{service}
pao_memory_vector_index_size{service,collection}
pao_memory_embedding_generation_duration_seconds{service}
```

#### Relationship Engine
```prometheus
pao_relationship_rhi_score{service,companion_id}
pao_relationship_dimension{service,dimension,companion_id}  # trust, closeness, etc.
pao_milestones_achieved_total{service,type}
pao_diary_entries_total{service}
```

#### Proactive Engine
```prometheus
pao_proactive_generated_total{service,trigger_category}
pao_proactive_sent_total{service,trigger_category}
pao_proactive_dismissed_total{service,reason}
pao_proactive_feedback_total{service,rating}
pao_proactive_relevance_score{service}
```

#### Safety Engine
```prometheus
pao_safety_events_total{service,type,risk_level}
pao_safety_interventions_total{service,level}
pao_crisis_detection_latency_seconds{service}
pao_safety_false_positive_rate{service}
pao_appeals_total{service,status}
```

#### Voice Engine
```prometheus
pao_voice_calls_total{service,status}  # started, connected, ended, failed
pao_voice_call_duration_seconds{service}
pao_voice_stream_latency_ms{service,direction}  # ingress, egress
pao_voice_timbre_verification_duration_seconds{service}
pao_voice_timbre_match_score{service}
```

#### Evaluation Engine
```prometheus
pao_evaluation_runs_total{service,type,status}
pao_evaluation_score{service,dimension}
pao_evaluation_duration_seconds{service,type}
pao_heuristic_failures_total{service,heuristic}
```

### SLO Metrics (SLI Definitions)

```prometheus
# Availability
pao_sli_availability: 
  - numerator: sum(rate(pao_http_requests_total{status!~"5.."}[5m]))
  - denominator: sum(rate(pao_http_requests_total[5m]))
  - target: 99.9%

# Latency
pao_sli_latency_p99:
  - numerator: sum(rate(pao_http_request_duration_seconds_bucket{le="1.0"}[5m]))
  - denominator: sum(rate(pao_http_request_duration_seconds_count[5m]))
  - target: 99%

# Quality (Business SLO)
pao_sli_rhi_quality:
  - numerator: sum(pao_relationship_rhi_score > 5)
  - denominator: count(pao_relationship_rhi_score)
  - target: 80%

# Safety
pao_sli_safety_recall:
  - numerator: sum(pao_safety_crisis_detected_total{detected="true"})
  - denominator: sum(pao_safety_crisis_detected_total)
  - target: 99.9%
```

### Recording Rules

```yaml
# Recording rules for common queries
groups:
  - name: pao-recording-rules
    interval: 30s
    rules:
      # Service-level RED
      - expr: |
          sum by (service) (rate(pao_http_requests_total[5m]))
        record: pao:service:request_rate:5m
      
      - expr: |
          sum by (service) (rate(pao_http_requests_total{status=~"5.."}[5m])) 
          / sum by (service) (rate(pao_http_requests_total[5m]))
        record: pao:service:error_rate:5m
      
      - expr: |
          histogram_quantile(0.99, sum by (service, le) (rate(pao_http_request_duration_seconds_bucket[5m])))
        record: pao:service:latency_p99:5m
      
      # Business metrics
      - expr: |
          sum by (companion_type) (pao_messages_processed_total)
        record: pao:business:messages_by_companion_type
      
      - expr: |
          avg by (companion_type) (pao_relationship_rhi_score)
        record: pao:business:avg_rhi_by_companion_type
```

---

## Logging

### Log Format (JSON)

```json
{
  "timestamp": "2025-01-15T10:30:00.123Z",
  "level": "info",
  "service": "conversation-engine",
  "version": "1.2.3",
  "environment": "production",
  "trace_id": "0123456789abcdef0123456789abcdef",
  "span_id": "0123456789abcdef",
  "message": "Processing user message",
  "fields": {
    "companion_id": "uuid",
    "user_id": "uuid",
    "message_id": "uuid",
    "modality": "text",
    "content_length": 150,
    "memory_recall_count": 5,
    "llm_model": "gpt-4-turbo",
    "llm_tokens_prompt": 1200,
    "llm_tokens_completion": 300,
    "duration_ms": 850
  }
}
```

### Log Levels

| Level | Use Case | Sampling |
|-------|----------|----------|
| `debug` | Detailed diagnostic info | Development only |
| `info` | General operational events | 100% |
| `warn` | Unexpected but handled | 100% |
| `error` | Failed operations, requires attention | 100% |
| `critical` | System-level failures, immediate action | 100% |

### Structured Logging Standards

```go
// observability/logger.go
package observability

import (
    "context"
    "go.uber.org/zap"
    "go.uber.org/zap/zapcore"
)

type Logger struct {
    *zap.Logger
}

func (l *Logger) WithContext(ctx context.Context) *Logger {
    traceID := trace.SpanFromContext(ctx).SpanContext().TraceID()
    spanID := trace.SpanFromContext(ctx).SpanContext().SpanID()
    
    return &Logger{l.Logger.With(
        zap.String("trace_id", traceID.String()),
        zap.String("span_id", spanID.String()),
    )}
}

// Usage
func (e *ConversationEngine) ProcessMessage(ctx context.Context, req *Request) (*Response, error) {
    logger := observability.WithContext(ctx).With(
        zap.String("companion_id", req.CompanionID),
        zap.String("user_id", req.UserID),
        zap.String("modality", req.Modality.String()),
    )
    
    logger.Info("Processing message", 
        zap.Int("content_length", len(req.Content)),
    )
    
    // ... processing
    
    logger.Info("Message processed",
        zap.String("message_id", resp.MessageID),
        zap.Int("memory_recall_count", len(memories)),
        zap.Duration("duration", time.Since(start)),
    )
    
    return resp, nil
}
```

### Log Queries (LogQL)

```logql
# All errors in last hour
{service="conversation-engine"} |= "error" | json | level="error"

# Slow requests with trace correlation
{service="api-gateway"} | json | duration_ms > 1000 | trace_id != ""

# Safety events
{service="safety-engine"} | json | event_type=~"crisis|self_harm|violence"

# Memory operations
{service="memory-engine"} | json | operation=~"store|recall|consolidate"

# Proactive feedback
{service="proactive-engine"} | json | feedback_rating != ""

# Voice call issues
{service="voice-engine"} | json | (call_status="failed" OR latency_ms > 500)
```

---

## Distributed Tracing

### Trace Context Propagation

```go
// tracing/middleware.go
package tracing

import (
    "context"
    "net/http"
    
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/propagation"
    "go.opentelemetry.io/otel/trace"
)

var propagator = propagation.NewCompositeTextMapPropagator(
    propagation.TraceContext{},
    propagation.Baggage{},
)

// HTTP Middleware
func TracingMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        ctx := propagator.Extract(r.Context(), propagation.HeaderCarrier(r.Header))
        ctx, span := otel.Tracer("api-gateway").Start(ctx, r.URL.Path)
        defer span.End()
        
        // Add common attributes
        span.SetAttributes(
            attribute.String("http.method", r.Method),
            attribute.String("http.route", r.URL.Path),
            attribute.String("http.scheme", r.URL.Scheme),
        )
        
        // Inject trace context into response headers
        propagator.Inject(ctx, propagation.HeaderCarrier(w.Header()))
        
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

// gRPC Interceptor
func GRPCServerInterceptor() grpc.UnaryServerInterceptor {
    return func(ctx context.Context, req interface{}, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (interface{}, error) {
        md, _ := metadata.FromIncomingContext(ctx)
        ctx = propagator.Extract(ctx, metadataCarrier{md})
        
        ctx, span := otel.Tracer("grpc").Start(ctx, info.FullMethod)
        defer span.End()
        
        return handler(ctx, req)
    }
}
```

### Span Attributes Standards

```go
// Standard attributes for all spans
span.SetAttributes(
    // Service
    attribute.String("service.name", "conversation-engine"),
    attribute.String("service.version", "1.2.3"),
    attribute.String("deployment.environment", "production"),
    
    // Business context (low cardinality)
    attribute.String("pao.companion_type", "friend"),
    attribute.String("pao.user_tier", "premium"),
    
    // Request specifics
    attribute.String("pao.companion_id", companionID),
    attribute.String("pao.user_id", userID),
    attribute.String("pao.message_id", messageID),
    attribute.String("pao.modality", "text"),
)

// Memory recall span
ctx, span := tracer.Start(ctx, "memory.recall",
    trace.WithAttributes(
        attribute.String("pao.memory.query", query),
        attribute.Int("pao.memory.limit", limit),
        attribute.StringSlice("pao.memory.types", types),
    ),
)
defer span.End()

memories, err := m.client.Recall(ctx, query, limit)
span.SetAttributes(
    attribute.Int("pao.memory.results", len(memories)),
    attribute.Float64("pao.memory.avg_relevance", avgRelevance),
)
if err != nil {
    span.RecordError(err)
    span.SetStatus(codes.Error, err.Error())
}
```

### Trace Sampling

```yaml
# Sampling configuration
sampling:
  # Default: 10% of traces
  default: 0.10
  
  # 100% for critical paths
  rules:
    - service: "safety-engine"
      rate: 1.0
    - service: "voice-engine"
      rate: 0.5
    - operation: "*.Recall"
      rate: 0.2
    - operation: "*.ProcessMessage"
      rate: 0.15
    - attribute:
        "pao.user_tier": "premium"
      rate: 0.5
  
  # Always sample errors
  parent_based: true
  error_rate: 1.0
```

### Trace Queries (TraceQL)

```traceql
# Find slow traces
{span.duration > 1s AND service.name = "conversation-engine"}

# Safety-related traces
{service.name = "safety-engine" AND span.name =~ "crisis|intervention"}

# Memory recall traces with low results
{service.name = "memory-engine" AND span.name = "recall" AND pao.memory.results < 3}

# Error traces
{span.status = error AND service.name =~ ".*"}

# Voice call traces with high latency
{service.name = "voice-engine" AND span.name = "voice.call" AND span.duration > 500ms}

# Proactive generation traces
{service.name = "proactive-engine" AND span.name = "generate"}
```

---

## Continuous Profiling

### Pyroscope Integration

```go
// profiling/setup.go
package profiling

import (
    "github.com/pyroscope-io/pyroscope/pkg/agent/profiler"
)

func Init(serviceName string) error {
    return profiler.Start(profiler.Config{
        ApplicationName: serviceName,
        ServerAddress:   "http://pyroscope:4040",
        ProfileTypes: []profiler.ProfileType{
            profiler.ProfileCPU,
            profiler.ProfileAllocObjects,
            profiler.ProfileAllocSpace,
            profiler.ProfileInuseObjects,
            profiler.ProfileInuseSpace,
            profiler.ProfileGoroutines,
            profiler.ProfileMutexCount,
            profiler.ProfileMutexDuration,
            profiler.ProfileBlockCount,
            profiler.ProfileBlockDuration,
        },
        Tags: map[string]string{
            "environment": os.Getenv("ENVIRONMENT"),
            "version":     version.Version,
            "region":      os.Getenv("REGION"),
        },
    })
}
```

### Profiling Queries

```pyroscope
# CPU hotspots in conversation engine
{service_name="conversation-engine", profile_type="cpu"}

# Memory allocations in memory engine
{service_name="memory-engine", profile_type="alloc_space"}

# Goroutine leaks
{service_name=~".*", profile_type="goroutines"} | top 10

# Mutex contention
{service_name=~".*", profile_type="mutex_duration"} | top 10

# Compare profiles (before/after deploy)
diff({service_name="conversation-engine", profile_type="cpu", env="production"}, 
     {service_name="conversation-engine", profile_type="cpu", env="staging"})
```

---

## Dashboards

### Standard Dashboard Structure

```
┌────────────────────────────────────────────────────────────────┐
│ SERVICE: conversation-engine                                    │
├──────────────┬──────────────┬──────────────┬──────────────────┤
│   RED        │  BUSINESS    │   DEPENDENCIES │  RESOURCES      │
│              │              │              │                  │
│ ████ RPS     │ ████ Msgs/s  │ ████ DB      │ ████ CPU%        │
│ ████ Errors  │ ████ RHI     │ ████ Redis   │ ████ Mem%        │
│ ████ P99     │ ████ Recalls │ ████ Qdrant  │ ████ Goroutines  │
│              │ ████ Proact. │ ████ Kafka   │ ████ GC pauses   │
└──────────────┴──────────────┴──────────────┴──────────────────┘
```

### Key Dashboards

| Dashboard | Purpose | Key Panels |
|-----------|---------|------------|
| **Service Overview** | Per-service health | RED, Business KPIs, Dependencies |
| **Business Metrics** | Product-level views | DAU, Messages, RHI, Proactive engagement |
| **Safety Dashboard** | Safety system monitoring | Crisis detection, Interventions, Appeals |
| **Voice Dashboard** | Voice-specific metrics | Call quality, Latency, Timbre verification |
| **Capacity Planning** | Resource utilization | CPU, Memory, Disk, Network trends |
| **Cost Dashboard** | LLM/API costs | Token usage, Cost per conversation, per user |
| **SLO Dashboard** | Error budget tracking | Burn rate, Error budget remaining |

### Dashboard JSON (Grafana)

```json
{
  "dashboard": {
    "title": "PAO - Conversation Engine",
    "tags": ["pao", "conversation-engine"],
    "timezone": "utc",
    "panels": [
      {
        "title": "Request Rate",
        "type": "timeseries",
        "targets": [
          {
            "expr": "sum(rate(pao_http_requests_total{service=\"conversation-engine\"}[5m])) by (method)",
            "legendFormat": "{{method}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "timeseries",
        "targets": [
          {
            "expr": "sum(rate(pao_http_requests_total{service=\"conversation-engine\",status=~\"5..\"}[5m])) / sum(rate(pao_http_requests_total{service=\"conversation-engine\"}[5m]))",
            "legendFormat": "Error Rate"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percentunit",
            "thresholds": {
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 0.01},
                {"color": "red", "value": 0.05}
              ]
            }
          }
        }
      }
    ]
  }
}
```

---

## Alerting

### Alert Rules

```yaml
# prometheus/rules/alerts.yaml
groups:
  - name: pao-service-alerts
    interval: 30s
    rules:
      # Critical: Service down
      - alert: ServiceDown
        expr: up{job="kubernetes-pods",service=~"pao-.*"} == 0
        for: 1m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: "Service {{ $labels.service }} is down"
          runbook: "https://runbooks.pao.app/service-down"
      
      # Critical: High error rate
      - alert: HighErrorRate
        expr: |
          sum(rate(pao_http_requests_total{status=~"5.."}[5m])) by (service)
          /
          sum(rate(pao_http_requests_total[5m])) by (service)
          > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate on {{ $labels.service }}"
          description: "Error rate is {{ $value | humanizePercentage }}"
      
      # Warning: High latency
      - alert: HighLatency
        expr: |
          histogram_quantile(0.99, 
            sum(rate(pao_http_request_duration_seconds_bucket[5m])) by (service, le)
          ) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High P99 latency on {{ $labels.service }}"
      
      # Critical: Safety system degraded
      - alert: SafetySystemDegraded
        expr: |
          pao_safety_crisis_detection_latency_seconds > 5
          OR
          pao_safety_crisis_recall < 0.99
        for: 1m
        labels:
          severity: critical
          team: safety
        annotations:
          summary: "Safety system degraded"
          runbook: "https://runbooks.pao.app/safety-degraded"
      
      # Warning: Low memory recall quality
      - alert: LowMemoryRecallQuality
        expr: |
          avg(pao_memory_recall_relevance_score) < 0.6
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Memory recall quality degraded"
      
      # Info: New deployment
      - alert: NewDeployment
        expr: |
          kube_deployment_status_replicas_updated{namespace="pao-production"} 
          != 
          kube_deployment_status_replicas{namespace="pao-production"}
        for: 0m
        labels:
          severity: info
        annotations:
          summary: "New deployment detected for {{ $labels.deployment }}"

  - name: pao-business-alerts
    rules:
      # Warning: RHI dropping
      - alert: RHIDeclining
        expr: |
          (pao_relationship_rhi_score - pao_relationship_rhi_score offset 24h) < -1
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "RHI declining for companion {{ $labels.companion_id }}"
      
      # Critical: Proactive system not generating
      - alert: ProactiveGenerationStalled
        expr: |
          rate(pao_proactive_generated_total[1h]) == 0
        for: 2h
        labels:
          severity: critical
        annotations:
          summary: "Proactive engine not generating messages"
      
      # Warning: High LLM costs
      - alert: HighLLMCosts
        expr: |
          rate(pao_llm_cost_usd_total[1h]) > 1000
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "LLM costs exceeding $1000/hr"
```

### Alert Routing

```yaml
# Alertmanager config
route:
  group_by: ['alertname', 'service', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'critical-pagerduty'
      continue: true
    - match:
        team: safety
      receiver: 'safety-team'
    - match:
        team: ml
      receiver: 'ml-team'

receivers:
  - name: 'default'
    slack_configs:
      - channel: '#alerts'
        send_resolved: true
  
  - name: 'critical-pagerduty'
    pagerduty_configs:
      - service_key: '${PAGERDUTY_CRITICAL_KEY}'
        severity: critical
  
  - name: 'safety-team'
    slack_configs:
      - channel: '#safety-alerts'
        send_resolved: true
    pagerduty_configs:
      - service_key: '${PAGERDUTY_SAFETY_KEY}'
  
  - name: 'ml-team'
    slack_configs:
      - channel: '#ml-alerts'
        send_resolved: true
```

---

## Correlation & Debugging

### Exemplars (Metrics → Traces)

```go
// Add trace ID to histogram observations
httpRequestDuration.Observe(duration.Seconds(),
    exemplar.TraceID(traceID),
)
```

### Unified Debugging Flow

```
1. Alert fires: HighErrorRate on conversation-engine
2. Click "View in Grafana" → Service Overview dashboard
3. See error rate spike at 10:30
4. Click "Traces" link on error rate panel
5. Tempo shows traces with errors
6. Click trace → See full request flow
7. Span shows: memory.recall took 3s (timeout)
8. Click "Logs" link on span
9. Loki shows: "Qdrant connection pool exhausted"
10. Fix: Increase Qdrant connection pool size
```

### Correlation IDs

```go
// All telemetry includes these IDs
type TelemetryContext struct {
    TraceID    string `json:"trace_id"`
    SpanID     string `json:"span_id"`
    UserID     string `json:"user_id,omitempty"`
    CompanionID string `json:"companion_id,omitempty"`
    RequestID  string `json:"request_id"`
}

// Propagate through all service calls
func (c *Client) Do(ctx context.Context, req *http.Request) (*http.Response, error) {
    tc := TelemetryFromContext(ctx)
    req.Header.Set("X-Trace-ID", tc.TraceID)
    req.Header.Set("X-Span-ID", tc.SpanID)
    req.Header.Set("X-Request-ID", tc.RequestID)
    return c.httpClient.Do(req)
}
```

---

## Cost Optimization

### Metric Cardinality Control

```yaml
# Relabel configs to limit cardinality
metric_relabel_configs:
  # Drop high-cardinality labels
  - action: labeldrop
    regex: "(request_id|user_id|companion_id|message_id|trace_id|span_id)"
  
  # Keep only low-cardinality business labels
  - action: labelkeep
    regex: "(service|environment|version|region|method|path|status|companion_type|user_tier)"
  
  # Hash high-cardinality to buckets
  - action: replace
    source_labels: ["user_id"]
    target_label: "user_bucket"
    replacement: "{{ sha256($1) | mod 100 }}"
    separator: ""
```

### Retention Policies

```yaml
# Prometheus retention
prometheus:
  retention: 15d          # Hot storage
  remote_write:
    - url: "https://prometheus.grafana.cloud/..."
      # Long-term in Grafana Cloud (13 months)

# Loki retention
loki:
  limits_config:
    retention_period: 30d  # Hot
  chunk_store_config:
    max_look_back_period: 0s
  table_manager:
    retention_deletes_enabled: true
    retention_period: 30d

# Tempo retention
tempo:
  retention: 7d  # Traces are large, keep shorter

# Pyroscope retention
pyroscope:
  retention: 30d
```

---

## Observability Checklist

### For New Services

- [ ] Metrics: RED metrics (Rate, Errors, Duration)
- [ ] Metrics: Business KPIs specific to service
- [ ] Metrics: SLO SLIs defined
- [ ] Logs: Structured JSON with trace correlation
- [ ] Logs: Appropriate log levels
- [ ] Traces: All external calls instrumented
- [ ] Traces: Critical internal paths instrumented
- [ ] Traces: Sampling configured
- [ ] Profiling: Pyroscope agent deployed
- [ ] Dashboards: Service overview dashboard
- [ ] Dashboards: Business metrics dashboard
- [ ] Alerts: Critical alerts (down, error rate, latency)
- [ ] Alerts: Business alerts (if applicable)
- [ ] Runbooks: Links in alert annotations
- [ ] Documentation: Key metrics documented

### For Existing Services (Quarterly Review)

- [ ] Review alert noise (reduce false positives)
- [ ] Check dashboard relevance
- [ ] Verify SLO targets still appropriate
- [ ] Update runbooks
- [ ] Cardinality audit
- [ ] Cost review (metrics, logs, traces)
- [ ] Coverage gaps analysis

---

**Aligned With:** `300-system-architecture.md`, `340-infrastructure.md`, `350-deployment.md`, `420-testing-strategy.md`
**Next Review:** 2026-01-17