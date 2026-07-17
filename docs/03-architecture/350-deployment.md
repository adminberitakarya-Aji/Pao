# PAO Deployment Specification

**Version:** 1.0
**Status:** Draft
**Owner:** PAO Platform Team

---

## Overview

This document specifies the deployment strategies, procedures, and configurations for PAO services across all environments.

> **Deployment Principle:** Progressive delivery, automated validation, instant rollback, zero-downtime.

---

## Deployment Pipeline

### Environments & Promotion Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   LOCAL     │────▶│   CI/CD     │────▶│  STAGING    │────▶│   CANARY    │────▶│ PRODUCTION  │
│  (Dev)      │     │  (Build)    │     │  (Integration)│   │  (5% → 100%)│   │  (Global)   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                   │                   │                   │                   │
      ▼                   ▼                   ▼                   ▼                   ▼
  - Kind/k3d          - GitHub          - Full stack         - 5% traffic         - All regions
  - Mock services     - Actions         - Real data          - 30 min soak        - Full traffic
  - Hot reload        - Multi-arch      - E2E tests          - Auto-promote       - SLO monitoring
  - Unit tests        - Security scan   - Performance        - Manual gate        - Incident ready
```

### Environment Specifications

| Environment | Purpose | Infrastructure | Data | Access |
|-------------|---------|----------------|------|--------|
| **Local** | Development | Kind/k3d (single node) | Synthetic/Anonymized | Developer laptop |
| **CI** | Build/Test | GitHub Actions runners | Ephemeral test DBs | CI system only |
| **Staging** | Integration | EKS (scaled down) | Anonymized prod subset | Team + stakeholders |
| **Canary** | Progressive rollout | EKS (production) | Production (5%) | Internal users + beta |
| **Production** | Live | EKS (multi-region) | Production | All users |

---

## Service Deployment Configuration

### Base Deployment Template

```yaml
# base/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Values.serviceName }}
  namespace: {{ .Values.namespace }}
  labels:
    app: {{ .Values.serviceName }}
    version: {{ .Chart.AppVersion }}
    managed-by: argocd
spec:
  replicas: {{ .Values.replicas }}
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 0
  selector:
    matchLabels:
      app: {{ .Values.serviceName }}
  template:
    metadata:
      labels:
        app: {{ .Values.serviceName }}
        version: {{ .Chart.AppVersion }}
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "{{ .Values.metricsPort }}"
        prometheus.io/path: "/metrics"
        traffic.sidecar.istio.io/excludeOutboundPorts: "9090,9091"
        sidecar.istio.io/inject: "true"
    spec:
      serviceAccountName: {{ .Values.serviceName }}
      priorityClassName: {{ .Values.priorityClass | default "default-priority" }}
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        runAsGroup: 1000
        fsGroup: 1000
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: {{ .Values.serviceName }}
          image: {{ .Values.image.registry }}/{{ .Values.image.repository }}:{{ .Values.image.tag }}
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: {{ .Values.httpPort }}
              protocol: TCP
            - name: grpc
              containerPort: {{ .Values.grpcPort }}
              protocol: TCP
            - name: metrics
              containerPort: {{ .Values.metricsPort }}
              protocol: TCP
          envFrom:
            - configMapRef:
                name: {{ .Values.serviceName }}-config
            - secretRef:
                name: {{ .Values.serviceName }}-secrets
                optional: true
          env:
            - name: SERVICE_NAME
              value: {{ .Values.serviceName }}
            - name: POD_NAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name
            - name: POD_IP
              valueFrom:
                fieldRef:
                  fieldPath: status.podIP
            - name: NODE_NAME
              valueFrom:
                fieldRef:
                  fieldPath: spec.nodeName
          resources:
            requests:
              cpu: {{ .Values.resources.requests.cpu }}
              memory: {{ .Values.resources.requests.memory }}
            limits:
              cpu: {{ .Values.resources.limits.cpu }}
              memory: {{ .Values.resources.limits.memory }}
          livenessProbe:
            httpGet:
              path: /health/live
              port: http
            initialDelaySeconds: {{ .Values.livenessProbe.initialDelaySeconds }}
            periodSeconds: {{ .Values.livenessProbe.periodSeconds }}
            timeoutSeconds: {{ .Values.livenessProbe.timeoutSeconds }}
            failureThreshold: {{ .Values.livenessProbe.failureThreshold }}
          readinessProbe:
            httpGet:
              path: /health/ready
              port: http
            initialDelaySeconds: {{ .Values.readinessProbe.initialDelaySeconds }}
            periodSeconds: {{ .Values.readinessProbe.periodSeconds }}
            timeoutSeconds: {{ .Values.readinessProbe.timeoutSeconds }}
            failureThreshold: {{ .Values.readinessProbe.failureThreshold }}
          startupProbe:
            httpGet:
              path: /health/live
              port: http
            initialDelaySeconds: 5
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 30
      # Sidecars added via Istio injection
```

### Service-Specific Overrides

```yaml
# overlays/production/conversation-engine/values.yaml
serviceName: conversation-engine
namespace: pao-production
replicas: 50
priorityClass: high-priority
image:
  registry: ghcr.io
  repository: pao/conversation-engine
  tag: "v1.2.3"
httpPort: 8080
grpcPort: 9090
metricsPort: 9090
resources:
  requests:
    cpu: "2000m"
    memory: "4Gi"
  limits:
    cpu: "4000m"
    memory: "8Gi"
livenessProbe:
  initialDelaySeconds: 15
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
readinessProbe:
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3

# HPA
hpa:
  enabled: true
  minReplicas: 20
  maxReplicas: 200
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: "1000"

# PDB
pdb:
  enabled: true
  minAvailable: "80%"

# ServiceMonitor
servicemonitor:
  enabled: true
  interval: 15s
  scrapeTimeout: 10s
```

```yaml
# overlays/production/voice-engine/values.yaml
serviceName: voice-engine
namespace: pao-production
replicas: 20
priorityClass: high-priority
image:
  registry: ghcr.io
  repository: pao/voice-engine
  tag: "v1.2.3"
httpPort: 8080
grpcPort: 9090
metricsPort: 9090
resources:
  requests:
    cpu: "2000m"
    memory: "8Gi"
    nvidia.com/gpu: "1"
  limits:
    cpu: "4000m"
    memory: "16Gi"
    nvidia.com/gpu: "1"
nodeSelector:
  workload: ml-inference
tolerations:
  - key: "nvidia.com/gpu"
    operator: "Exists"
    effect: "NoSchedule"

hpa:
  enabled: true
  minReplicas: 10
  maxReplicas: 100
  metrics:
    - type: Resource
      resource:
        name: nvidia.com/gpu
        target:
          type: Utilization
          averageUtilization: 75
```

---

## Deployment Strategies

### Rolling Update (Default)

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 25%
    maxUnavailable: 0
```

**When to use:** Most services, backward-compatible changes.

### Blue-Green (Major Versions)

```yaml
# ArgoCD Application with blue-green
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: conversation-engine-blue-green
spec:
  source:
    repoURL: https://github.com/pao/application-config
    targetRevision: main
    path: services/conversation-engine
    helm:
      parameters:
        - name: deployment.strategy
          value: "blue-green"
        - name: deployment.activeColor
          value: "blue"
  destination:
    server: https://kubernetes.default.svc
    namespace: pao-production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

**When to use:** Breaking API changes, major dependency upgrades.

### Canary (Default for Production)

```yaml
# Canary deployment via Istio VirtualService
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: conversation-engine
spec:
  hosts:
  - conversation-engine.pao-production.svc.cluster.local
  http:
  - match:
    - headers:
        x-canary:
          exact: "true"
    route:
    - destination:
        host: conversation-engine-canary
      weight: 100
  - route:
    - destination:
        host: conversation-engine-stable
      weight: 95
    - destination:
        host: conversation-engine-canary
      weight: 5
```

**Canary Promotion Gates:**

| Gate | Metric | Threshold | Duration |
|------|--------|-----------|----------|
| **Health** | Pod readiness | 100% ready | Immediate |
| **Errors** | HTTP 5xx rate | < 0.1% | 5 min |
| **Latency** | P99 latency | < 1.5x baseline | 10 min |
| **Business** | RHI change | > -0.1 | 30 min |
| **Safety** | Crisis detection recall | 100% | 10 min |

---

## Configuration Management

### ConfigMaps

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ .Values.serviceName }}-config
  namespace: {{ .Values.namespace }}
data:
  # Application config
  LOG_LEVEL: "info"
  LOG_FORMAT: "json"
  METRICS_ENABLED: "true"
  TRACING_ENABLED: "true"
  
  # Feature flags (synced from Redis)
  FEATURE_NEW_MEMORY_ENGINE: "true"
  FEATURE_PROACTIVE_V2: "true"
  FEATURE_VOICE_STREAMING: "true"
  
  # Service discovery
  DATABASE_HOST: "postgresql.pao-data.svc.cluster.local"
  DATABASE_PORT: "5432"
  QDRANT_URL: "http://qdrant.pao-data.svc.cluster.local:6333"
  KUZU_URL: "bolt://kuzu.pao-data.svc.cluster.local:6343"
  REDIS_URL: "redis://redis.pao-data.svc.cluster.local:6379"
  KAFKA_BROKERS: "kafka.pao-data.svc.cluster.local:9092"
  
  # Timeouts
  HTTP_TIMEOUT: "30s"
  GRPC_TIMEOUT: "10s"
  DATABASE_TIMEOUT: "10s"
  CACHE_TTL: "300s"
  
  # Limits
  MAX_MEMORY_SIZE: "100000"
  MAX_RECALL_LIMIT: "50"
  MAX_PROACTIVE_PER_DAY: "10"
```

### Secrets (via Vault + CSI)

```yaml
# SecretProviderClass for CSI Driver
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: {{ .Values.serviceName }}-secrets
  namespace: {{ .Values.namespace }}
spec:
  provider: vault
  parameters:
    vaultAddress: "https://vault.pao-system.svc.cluster.local:8200"
    roleName: "{{ .Values.serviceName }}"
    objects: |
      - objectName: "database/credentials"
        objectKey: "password"
        objectType: "secret"
      - objectName: "redis/credentials"
        objectKey: "password"
        objectType: "secret"
      - objectName: "kafka/credentials"
        objectKey: "password"
        objectType: "secret"
      - objectName: "jwt/signing-key"
        objectKey: "private_key"
        objectType: "secret"
      - objectName: "encryption/{{ .Values.serviceName }}"
        objectKey: "key"
        objectType: "secret"
  secretObjects:
    - secretName: {{ .Values.serviceName }}-secrets
      type: Opaque
      data:
        - objectName: "database/credentials"
          key: DATABASE_PASSWORD
        - objectName: "redis/credentials"
          key: REDIS_PASSWORD
        - objectName: "kafka/credentials"
          key: KAFKA_PASSWORD
        - objectName: "jwt/signing-key"
          key: JWT_PRIVATE_KEY
        - objectName: "encryption/{{ .Values.serviceName }}"
          key: ENCRYPTION_KEY
```

### External Secrets Operator (Alternative)

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: {{ .Values.serviceName }}-secrets
  namespace: {{ .Values.namespace }}
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: ClusterSecretStore
  target:
    name: {{ .Values.serviceName }}-secrets
    creationPolicy: Owner
  data:
    - secretKey: DATABASE_PASSWORD
      remoteRef:
        key: secret/data/pao/production/database
        property: password
    - secretKey: REDIS_PASSWORD
      remoteRef:
        key: secret/data/pao/production/redis
        property: password
    - secretKey: JWT_PRIVATE_KEY
      remoteRef:
        key: secret/data/pao/production/jwt
        property: private_key
```

---

## Database Migrations

### Migration Framework

```python
# migrations/runner.py
class MigrationRunner:
    def __init__(self, db_pool, migrations_dir):
        self.db = db_pool
        self.migrations_dir = migrations_dir
    
    async def run_migrations(self, target_version: Optional[str] = None):
        # 1. Ensure migration table exists
        await self._ensure_migration_table()
        
        # 2. Get applied migrations
        applied = await self._get_applied_migrations()
        
        # 3. Get available migrations
        available = self._get_available_migrations()
        
        # 4. Determine pending
        pending = [m for m in available if m.version not in applied]
        if target_version:
            pending = [m for m in pending if m.version <= target_version]
        
        # 5. Run each migration in transaction
        for migration in pending:
            await self._run_migration(migration)
    
    async def _run_migration(self, migration: Migration):
        async with self.db.acquire() as conn:
            # Advisory lock to prevent concurrent migrations
            await conn.execute("SELECT pg_advisory_xact_lock(123456789)")
            
            try:
                # Run up migration
                await conn.execute(migration.up_sql)
                
                # Record success
                await conn.execute("""
                    INSERT INTO schema_migrations (version, name, applied_at, checksum)
                    VALUES ($1, $2, NOW(), $3)
                """, migration.version, migration.name, migration.checksum)
                
                logger.info(f"Applied migration {migration.version}: {migration.name}")
            except Exception as e:
                logger.error(f"Migration {migration.version} failed: {e}")
                raise MigrationError(f"Failed to apply {migration.version}") from e
```

### Migration Naming & Structure

```
migrations/
├── V1.0.0__initial_schema.sql
├── V1.1.0__add_proactive_feedback.sql
├── V1.2.0__add_voice_timbre_verification.sql
├── V1.3.0__add_safety_interventions.sql
└── V1.4.0__add_evaluation_dimensions.sql
```

Each migration file:
```sql
-- V1.1.0__add_proactive_feedback.sql
-- Up migration
BEGIN;

ALTER TABLE proactive_messages 
ADD COLUMN user_feedback JSONB;

CREATE INDEX idx_proactive_feedback 
ON proactive_messages ((user_feedback->>'rating')) 
WHERE user_feedback IS NOT NULL;

COMMIT;

-- Down migration (for rollback)
-- BEGIN;
-- ALTER TABLE proactive_messages DROP COLUMN user_feedback;
-- DROP INDEX IF EXISTS idx_proactive_feedback;
-- COMMIT;
```

### Migration Job (Kubernetes)

```yaml
# migration-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ .Values.serviceName }}-migration-{{ .Chart.AppVersion }}
  namespace: {{ .Values.namespace }}
  annotations:
    "helm.sh/hook": pre-install,pre-upgrade
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": hook-succeeded,hook-failed
spec:
  template:
    spec:
      serviceAccountName: {{ .Values.serviceName }}-migration
      restartPolicy: OnFailure
      containers:
        - name: migration
          image: {{ .Values.image.registry }}/{{ .Values.image.repository }}:{{ .Values.image.tag }}
          command: ["python", "-m", "migrations.runner"]
          envFrom:
            - configMapRef:
                name: {{ .Values.serviceName }}-config
            - secretRef:
                name: {{ .Values.serviceName }}-secrets
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
```

---

## Health Checks & Readiness

### Health Endpoint Implementation

```python
# health.py
class HealthChecker:
    def __init__(self, service_name: str, dependencies: List[Dependency]):
        self.service_name = service_name
        self.dependencies = dependencies
    
    async def liveness(self) -> HealthResponse:
        """Kubernetes liveness - is process alive?"""
        return HealthResponse(
            status="alive",
            service=self.service_name,
            timestamp=datetime.utcnow()
        )
    
    async def readiness(self) -> HealthResponse:
        """Kubernetes readiness - can serve traffic?"""
        checks = []
        overall_ready = True
        
        for dep in self.dependencies:
            check = await dep.check()
            checks.append(check)
            if not check.healthy:
                overall_ready = False
        
        # Additional service-specific checks
        checks.append(await self._check_internal_state())
        
        return HealthResponse(
            status="ready" if overall_ready else "not_ready",
            service=self.service_name,
            timestamp=datetime.utcnow(),
            checks=checks
        )
    
    async def startup(self) -> HealthResponse:
        """Kubernetes startup - is initialization complete?"""
        # Same as readiness but with longer timeout
        return await self.readiness()

class Dependency:
    async def check(self) -> DependencyCheck:
        raise NotImplementedError()

class DatabaseDependency(Dependency):
    async def check(self) -> DependencyCheck:
        try:
            await self.pool.execute("SELECT 1")
            return DependencyCheck(name="database", healthy=True, latency_ms=...)
        except Exception as e:
            return DependencyCheck(name="database", healthy=False, error=str(e))

class CacheDependency(Dependency):
    async def check(self) -> DependencyCheck:
        try:
            await self.redis.ping()
            return DependencyCheck(name="cache", healthy=True, latency_ms=...)
        except Exception as e:
            return DependencyCheck(name="cache", healthy=False, error=str(e))

class VectorDBDependency(Dependency):
    async def check(self) -> DependencyCheck:
        try:
            await self.client.get_collections()
            return DependencyCheck(name="vector_db", healthy=True, latency_ms=...)
        except Exception as e:
            return DependencyCheck(name="vector_db", healthy=False, error=str(e))
```

### Health Response Format

```json
{
  "status": "ready",
  "service": "conversation-engine",
  "timestamp": "2025-06-25T10:30:00.123Z",
  "version": "1.2.3",
  "checks": [
    {
      "name": "database",
      "healthy": true,
      "latency_ms": 2.3,
      "details": {"connections": 45, "max": 100}
    },
    {
      "name": "cache",
      "healthy": true,
      "latency_ms": 0.8,
      "details": {"hit_rate": 0.92}
    },
    {
      "name": "vector_db",
      "healthy": true,
      "latency_ms": 15.2,
      "details": {"collections": 4, "points": 1000000}
    },
    {
      "name": "kafka",
      "healthy": true,
      "latency_ms": 5.1,
      "details": {"brokers": 9, "topics": 42}
    },
    {
      "name": "internal_state",
      "healthy": true,
      "details": {"model_loaded": true, "warmup_complete": true}
    }
  ]
}
```

---

## Rollback Procedures

### Automated Rollback Triggers

```yaml
# ArgoCD Rollback Configuration
argocd_rollback:
  # Automatic rollback on health degradation
  automated:
    enabled: true
    condition: "health_degraded"
    window: "10m"
  
  # Manual rollback commands
  manual_triggers:
    - "argocd app rollback conversation-engine <revision>"
    - "argocd app rollback conversation-engine --revision 42"
```

### Rollback Playbook

```markdown
## ROLLBACK-001: Service Rollback

### Automated (ArgoCD)
1. ArgoCD detects health check failures
2. Compares current revision metrics to previous
3. If degradation > threshold, auto-rollback
4. Notification sent to #deployments

### Manual
1. **Identify revision**: `argocd app history conversation-engine`
2. **Rollback**: `argocd app rollback conversation-engine 42`
3. **Verify**: Check pods, health endpoints, metrics
4. **Communicate**: Update #deployments, status page if user-facing

### Database Rollback (if migration applied)
1. **Check migration status**: `SELECT * FROM schema_migrations ORDER BY applied_at DESC LIMIT 5`
2. **Run down migration**: Execute down SQL from migration file
3. **Verify**: Application health, data integrity
4. **Note**: Only if migration is truly reversible

### Canary Rollback
1. **Immediate**: `istioctl virtualservice update conversation-engine --route stable=100`
2. **Or via ArgoCD**: Update VirtualService weight to 0% canary
3. **Verify**: Traffic fully on stable, no errors
```

---

## Deployment Validation

### Pre-Deployment Checks

```yaml
# GitHub Actions pre-deploy job
pre_deploy_checks:
  - name: "Security Scan"
    run: |
      trivy image --severity CRITICAL,HIGH ghcr.io/pao/conversation-engine:v1.2.3
      grype ghcr.io/pao/conversation-engine:v1.2.3
  
  - name: "SBOM Generation"
    run: |
      syft ghcr.io/pao/conversation-engine:v1.2.3 -o spdx-json > sbom.json
  
  - name: "Image Signing"
    run: |
      cosign sign --yes ghcr.io/pao/conversation-engine:v1.2.3
  
  - name: "Provenance Attestation"
    run: |
      slsa-verifier verify-image ghcr.io/pao/conversation-engine:v1.2.3
  
  - name: "Dependency Check"
    run: |
      # Check for vulnerable dependencies
      govulncheck ./...
      npm audit --audit-level high
      pip-audit
  
  - name: "License Compliance"
    run: |
      fossa analyze --fail-on-violation
```

### Post-Deployment Validation

```yaml
# ArgoCD Post-Sync Hook
post_deploy_validation:
  - name: "Smoke Tests"
    run: |
      # Health endpoints
      curl -f https://api-staging.pao.app/health/ready
      curl -f https://api-staging.pao.app/health/live
      
      # GraphQL introspection
      curl -X POST https://api-staging.pao.app/graphql \
        -H "Content-Type: application/json" \
        -d '{"query": "{ __schema { types { name } } }"}'
      
      # Critical API paths
      curl -f -H "Authorization: Bearer $TOKEN" \
        https://api-staging.pao.app/v1/companions
  
  - name: "Integration Tests"
    run: |
      pytest tests/integration -k "staging" --tb=short
  
  - name: "Canary Metrics Check"
    run: |
      # Wait for metrics to stabilize
      sleep 300
      
      # Query Prometheus for canary vs stable
      python scripts/canary_analysis.py \
        --service conversation-engine \
        --threshold-error-rate 0.001 \
        --threshold-latency-p99 1.5 \
        --duration 30m
  
  - name: "SLO Verification"
    run: |
      python scripts/slo_check.py \
        --service conversation-engine \
        --window 10m \
        --require-all
```

---

## Deployment Calendar & Windows

### Sync Windows

```yaml
# ArgoCD Sync Windows
sync_windows:
  - name: "Daily Maintenance"
    schedule: "0 2 * * *"  # 2 AM UTC daily
    duration: "4h"
    applications: ["*"]
    manual_sync: true  # Allow manual outside window
  
  - name: "Emergency"
    schedule: "always"
    applications: ["safety-engine", "voice-engine"]
    manual_sync: true
```

### Deployment Freeze Periods

```yaml
deployment_freezes:
  - name: "Holiday Freeze"
    start: "12-20"
    end: "01-05"
    reason: "Reduced staffing, higher risk"
    exceptions: ["critical-security", "safety-hotfix"]
  
  - name: "Black Friday"
    start: "11-24"
    end: "11-28"
    reason: "High traffic period"
    exceptions: ["critical-security"]
  
  - name: "Quarterly Board Week"
    schedule: "First week of Mar, Jun, Sep, Dec"
    reason: "Demo preparation"
    exceptions: ["critical-security", "safety-hotfix"]
```

---

## Disaster Recovery Deployment

### DR Region Deployment

```yaml
# DR Deployment (passive, scaled down)
dr_deployment:
  regions:
    - "us-west-2"  # DR for us-east-1
    - "eu-west-4"  # DR for eu-west-1
    - "asia-northeast1"  # DR for ap-southeast-1
  
  scaling:
    replicas: 10% of production
    hpa_min: 2
    node_groups:
      - "system" (full)
      - "general" (minimal)
  
  data:
    postgresql: "Read replica (async)"
    qdrant: "Snapshot restore (RPO 24h)"
    kuzu: "Snapshot restore (RPO 24h)"
    redis: "Cross-region replica"
    kafka: "MirrorMaker2 (continuous)"
  
  activation:
    trigger: "Cloudflare health check failure"
    automated: true
    runbook: "PLAYBOOK-DR-001"
```

---

## Deployment Metrics & KPIs

### Key Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Deployment Frequency** | 10+/day | Per service |
| **Lead Time** | < 1 hour | Commit to production |
| **Change Failure Rate** | < 5% | Failed deployments / total |
| **MTTR** | < 15 min | Time to restore service |
| **Rollback Rate** | < 10% | Rollbacks / deployments |
| **Canary Promotion Rate** | > 90% | Successful promotions |

### Deployment Dashboard

```yaml
# Grafana Dashboard Panels
deployment_dashboard:
  - title: "Deployment Frequency"
    type: "time_series"
    query: "rate(argocd_application_sync_total[1d])"
  
  - title: "Change Failure Rate"
    type: "stat"
    query: "argocd_application_sync_failed / argocd_application_sync_total"
  
  - title: "Lead Time"
    type: "heatmap"
    query: "histogram_quantile(0.95, rate(deployment_duration_seconds_bucket[1h]))"
  
  - title: "Rollback Rate"
    type: "time_series"
    query: "rate(argocd_application_rollback_total[1d])"
  
  - title: "Canary Success Rate"
    type: "stat"
    query: "canary_promotions_success / canary_promotions_total"
  
  - title: "Deployment by Service"
    type: "table"
    query: "topk(20, sum by (service) (rate(argocd_application_sync_total[1d])))"
```

---

**Aligned With:** `300-system-architecture.md`, `340-infrastructure.md`, `04-engineering/`
**Next Review:** 2026-01-17