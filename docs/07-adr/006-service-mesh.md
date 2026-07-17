# ADR-006: Service Mesh Adoption (Istio Ambient)

**Status:** Accepted
**Date:** 2025-01-15
**Deciders:** CTO, VP Engineering, Platform Lead, Security Lead
**Consulted:** SRE Team, Network Team, All Service Owners

---

## Context

As PAO transitions from modular monolith to extracted services (per ADR-001), we need a service mesh to handle:
- Service-to-service encryption (mTLS)
- Traffic management (canary, retry, timeout, circuit breaker)
- Observability (distributed tracing, metrics, access logs)
- Authorization (workload identity, fine-grained policies)
- Multi-cluster/region federation

### Requirements

| Requirement | Priority |
|-------------|----------|
| Zero-trust mTLS (automatic, no code changes) | Critical |
| Sidecar-less (resource efficiency) | High |
| Multi-cluster (active-active across regions) | High |
| IPv6 support | Medium |
| VM/bare-metal workloads | Low (future) |
| Operational simplicity | High |
| CNCF Graduated project | Medium |

### Options Evaluated

| Mesh | Architecture | mTLS | Sidecar | Maturity | Resources |
|------|-------------|------|---------|----------|-----------|
| **Istio Ambient** | ztunnel (node) + waypoint (L7) | ✅ | ❌ | Beta (1.22) | Low |
| **Linkerd** | Sidecar (Rust) | ✅ | ✅ | Graduated | Very Low |
| **Consul Connect** | Sidecar (Go) | ✅ | ✅ | Graduated | Medium |
| **Cilium** | eBPF (kernel) | ✅ | ❌ | Graduated | Low |
| **Kuma/Kong Mesh** | Sidecar (Envoy) | ✅ | ✅ | Graduated | Medium |

---

## Decision

**Adopt Istio Ambient Mesh as the service mesh platform.**

### Why Istio Ambient?

```
┌─────────────────────────────────────────────────────────────────┐
│                    ISTIO AMBIENT ARCHITECTURE                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐                                              │
│  │   Application│                                              │
│  │    Pods      │                                              │
│  │  (No Sidecar)│                                              │
│  └──────┬───────┘                                              │
│         │                                                      │
│    ┌────▼────┐                                                 │
│    │ ztunnel │  (per-node daemon, Rust, eBPF)                 │
│    │  (L4)   │  - mTLS termination                             │
│    └────┬────┘  - Identity (SPIFFE)                            │
│         │      - L4 authorization                               │
│         │                                                      │
│    ┌────▼────┐                                                 │
│    │Waypoint │  (per-namespace/per-service L7 proxy)          │
│    │ Proxy   │  - L7 policies (authz, rate limit, routing)    │
│    │ (L7)    │  - Optional, deployed on demand                │
│    └─────────┘                                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Key Advantages:**
1. **No sidecars** → 50-70% less CPU/memory, faster pod startup
2. **Zero-trust by default** → mTLS enabled cluster-wide automatically
3. **Incremental adoption** → Add L7 waypoints only where needed
4. **eBPF acceleration** → Kernel-level packet processing
5. **CNCF Graduated** → Istio core is graduated, Ambient is beta→stable
6. **Multi-cluster** → Native support for multi-primary

### Deployment Model

```yaml
# Cluster Setup (3 regions)
clusters:
  - name: pao-us-east
    region: us-east-1
    role: primary
  - name: pao-eu-west
    region: eu-west-1
    role: primary
  - name: pao-ap-southeast
    region: ap-southeast-1
    role: primary

# Mesh Configuration
meshConfig:
  # Ambient mode (no sidecars)
  defaultConfig:
    proxy: 
      # No sidecar injection
      autoInject: disabled
  
  # ztunnel (L4) - DaemonSet on every node
  ztunnel:
    enabled: true
    resources:
      requests:
        cpu: "100m"
        memory: "128Mi"
      limits:
        cpu: "500m"
        memory: "512Mi"
  
  # Waypoint (L7) - Deploy per namespace
  waypoint:
    enabled: true
    # Auto-provision for namespaces with L7 policies
    autoProvision: true
    resources:
      requests:
        cpu: "200m"
        memory: "256Mi"
      limits:
        cpu: "1000m"
        memory: "1Gi"
  
  # Multi-cluster
  multiCluster:
    clusterName: ${CLUSTER_NAME}
    network: ${NETWORK_NAME}
```

### Traffic Management Policies

```yaml
# 1. Global mTLS (STRICT mode)
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: istio-system
spec:
  mtls:
    mode: STRICT

---
# 2. Authorization (Zero Trust)
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: memory-engine-authz
  namespace: ai-core
spec:
  selector:
    matchLabels:
      app: memory-engine
  rules:
  - from:
    - source:
        principals:
        - "spiffe://pao.app/ns/user-facing/sa/api-gateway"
        - "spiffe://pao.app/ns/ai-core/sa/conversation-engine"
    to:
    - operation:
        methods: ["POST"]
        paths: ["/v1/memories/*"]
  - to:
    - operation:
        methods: ["GET"]
        paths: ["/v1/memories/*", "/health"]

---
# 3. Traffic Splitting (Canary)
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: inference-gateway
  namespace: ai-core
spec:
  hosts:
  - inference-gateway.ai-core.svc.cluster.local
  http:
  - match:
    - headers:
        x-canary:
          exact: "true"
    route:
    - destination:
        host: inference-gateway
        subset: canary
      weight: 100
  - route:
    - destination:
        host: inference-gateway
        subset: stable
      weight: 90
    - destination:
        host: inference-gateway
        subset: canary
      weight: 10

---
# 4. Resilience (Retry, Timeout, Circuit Breaker)
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: memory-engine
  namespace: ai-core
spec:
  host: memory-engine.ai-core.svc.cluster.local
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 1000
      http:
        h2UpgradePolicy: UPGRADE
        http1MaxPendingRequests: 1000
        http2MaxRequests: 1000
    loadBalancer:
      simple: LEAST_REQUEST
    circuitBreaker:
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
```

### Observability Integration

```yaml
# Telemetry (built-in, no code changes)
telemetry:
  v2:
    prometheus:
      enabled: true
      # Custom metrics
      overrides:
      - match:
          metric: ISTIO_REQUESTS_TOTAL
        tagOverrides:
          destination_canonical_service:
            value: "%{DESTINATION_WORKLOAD}"
    accessLogging:
      - providers:
        - name: otel
        format: JSON
        # Structured logs for SIEM
    tracing:
      - providers:
        - name: otel
        randomSamplingPercentage: 10.0
        # 100% for errors
        customTags:
          error:
            literal: "true"
        match:
          - condition: response.code >= 500
```

---

## Multi-Cluster Federation

```yaml
# East-West Gateway (per cluster)
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  profile: ambient
  components:
    ingressGateways:
    - name: istio-eastwestgateway
      enabled: true
      label:
        topology.istio.io/network: network-${REGION}
      k8s:
        service:
          type: LoadBalancer
          ports:
          - port: 15443
            name: tls
          - port: 15017
            name: hb

---
# Service Export (make visible across clusters)
apiVersion: networking.istio.io/v1beta1
kind: ServiceExport
metadata:
  name: memory-engine
  namespace: ai-core

---
# Service Import (consume from other clusters)
apiVersion: networking.istio.io/v1beta1
kind: ServiceImport
metadata:
  name: memory-engine
  namespace: ai-core
spec:
  type: ClusterSetIP
  ports:
  - port: 8080
    protocol: TCP
```

---

## Migration Strategy (from Modular Monolith)

### Phase 1: Foundation (Month 1-2)
- [ ] Deploy Istio Ambient in staging (single cluster)
- [ ] Enable mTLS STRICT mode
- [ ] Configure ztunnel + waypoint for 1 namespace
- [ ] Validate: latency overhead < 2ms P99

### Phase 2: First Extraction (Month 3-4)
- [ ] Extract Inference Gateway as first service
- [ ] Deploy waypoint for ai-core namespace
- [ ] Configure AuthorizationPolicies
- [ ] Load test: 10k RPS, P99 < 200ms

### Phase 3: Multi-Cluster (Month 5-6)
- [ ] Deploy in 3 regions (US, EU, APAC)
- [ ] Configure multi-cluster mesh
- [ ] Test failover (chaos engineering)
- [ ] Validate data residency (EU traffic stays in EU)

### Phase 4: Full Adoption (Month 6-12)
- [ ] Migrate Voice Pipeline, Safety Engine
- [ ] Enable L7 policies for all extracted services
- [ ] Implement global traffic management
- [ ] Deprecate modular monolith communication paths

---

## Consequences

### Positive
- **Zero-trust by default**: All traffic encrypted, authenticated, authorized
- **No sidecars**: 50-70% resource savings, simpler operations
- **Rich traffic management**: Canary, mirroring, fault injection without code
- **Observability**: Automatic metrics, traces, logs for all services
- **Multi-cluster**: Active-active across regions, data residency
- **Standards-based**: SPIFFE, xDS, OpenTelemetry

### Negative
- **Complexity**: New control plane, CRDs, debugging tools
- **Learning curve**: Teams need Istio expertise
- **Control plane HA**: Must run highly available (3+ replicas)
- **Upgrade risk**: Mesh upgrades affect entire cluster
- **IPv6**: Limited support in Ambient (improving)

### Mitigations
- **Platform team owns mesh**: Upgrades, config, troubleshooting
- **Golden paths**: Helm charts, templates, validated patterns
- **Staging mirror**: Full mesh in staging, test upgrades there first
- **Rollback procedure**: Canary control plane upgrades
- **Training**: Istio certification for platform engineers

---

## Resource Requirements

| Component | Replicas | CPU (req/lim) | Memory (req/lim) | Notes |
|-----------|----------|---------------|------------------|-------|
| **istiod** (control plane) | 3 | 500m/2000m | 1Gi/4Gi | HA, leader election |
| **ztunnel** (per node) | 1/node | 100m/500m | 128Mi/512Mi | DaemonSet, Rust/eBPF |
| **waypoint** (per ns) | 2+ | 200m/1000m | 256Mi/1Gi | HPA based on CPU |
| **eastwest gateway** | 2/cluster | 200m/1000m | 256Mi/1Gi | Multi-cluster |

---

## Related Decisions

- ADR-001: Modular Monolith → Service Extraction
- ADR-002: API Protocol (gRPC/Connect over mesh)
- ADR-003: Event-Driven (Kafka over mesh)
- ADR-005: Security Model (Zero Trust enforcement)

---

## References

- [Istio Ambient Mesh](https://istio.io/latest/docs/ambient/)
- [Istio Multi-Cluster](https://istio.io/latest/docs/setup/install/multicluster/)
- [Zero Trust with Istio](https://istio.io/latest/blog/2023/zero-trust/)
- [Ambient Performance](https://istio.io/latest/blog/2023/ambient-performance/)
- [SPIFFE/SPIRE Integration](https://spiffe.io/docs/latest/istio-workload-identity/)

---

**Approval:**
- CTO: _________________ Date: __________
- VP Engineering: _________________ Date: __________
- Platform Lead: _________________ Date: __________
- Security Lead: _________________ Date: __________