# PAO Infrastructure Specification

**Version:** 1.0
**Status:** Draft
**Owner:** PAO Platform Team

---

## Overview

This document specifies the infrastructure architecture, provisioning, and operational procedures for PAO.

> **Infrastructure Principle:** Immutable, declarative, observable, and designed for global scale with regional data residency.

---

## Cloud Provider Strategy

### Multi-Cloud Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      MULTI-CLOUD TOPOLOGY                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────────┐         ┌─────────────────┐              │
│   │   AWS (Primary) │◄───────►│   GCP (Secondary)│              │
│   │   us-east-1     │  Peering │   us-central1   │              │
│   │                 │         │                 │              │
│   │ • EKS (Control) │         │ • GKE (Standby) │              │
│   │ • RDS (Primary) │         │ • Cloud SQL     │              │
│   │ • MSK (Primary) │         │ • Dataflow      │              │
│   │ • S3 (Primary)  │         │ • GCS (Replica) │              │
│   │ • ElastiCache   │         │ • Memorystore   │              │
│   └────────┬────────┘         └────────┬────────┘              │
│            │                           │                        │
│            └───────────────┬───────────┘                        │
│                            ▼                                    │
│                   ┌─────────────────┐                          │
│                   │  Global Services │                          │
│                   │                 │                          │
│                   │ • Cloudflare    │                          │
│                   │   (WAF, CDN,    │                          │
│                   │    DNS, Load    │                          │
│                   │    Balancing)   │                          │
│                   │ • HashiCorp     │                          │
│                   │   Cloud (Vault, │                          │
│                   │    Consul)      │                          │
│                   │ • Datadog/      │                          │
│                   │   Grafana Cloud │                          │
│                   │ • PagerDuty     │                          │
│                   └─────────────────┘                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Region Strategy

| Region | Provider | Purpose | Data Residency |
|--------|----------|---------|----------------|
| **us-east-1** | AWS | Primary (North America) | US |
| **us-central1** | GCP | Failover / Analytics | US |
| **eu-west-1** | AWS | EU Primary | EU (GDPR) |
| **eu-west-4** | GCP | EU Failover | EU |
| **ap-southeast-1** | AWS | APAC Primary | Singapore |
| **asia-northeast1** | GCP | APAC Failover | Tokyo |
| **sa-east-1** | AWS | LATAM | Brazil (LGPD) |

### Data Residency Controls

```yaml
data_residency:
  enforcement: "At infrastructure layer"
  mechanisms:
    - "Separate Kubernetes clusters per region"
    - "Database replication within region only"
    - "Object storage bucket per region"
    - "Kafka clusters per region"
    - "Network policies prevent cross-region data flow"
  user_control: "User selects region at signup, can migrate"
  compliance: "GDPR, CCPA, LGPD, PDPA, PIPL"
```

---

## Kubernetes Infrastructure

### Cluster Architecture

```yaml
# EKS Cluster Configuration (per region)
cluster:
  name: "pao-{environment}-{region}"
  version: "1.28"  # Latest stable
  endpoint_access: "private"  # No public endpoint
  
  vpc:
    cidr: "10.{region_octet}.0.0/16"
    subnets:
      private:
        - "10.{region_octet}.{az}.0/20"  # Workloads
        - "10.{region_octet}.{az}.16/20" # Data
      public:
        - "10.{region_octet}.{az}.32/20" # NAT Gateways
      intra:
        - "10.{region_octet}.{az}.48/20" # Cross-AZ traffic
  
  node_groups:
    - name: "system"
      instance_type: "m6i.xlarge"
      capacity_type: "ON_DEMAND"
      min_size: 3
      max_size: 10
      desired_size: 3
      labels:
        workload: "system"
      taints:
        - key: "CriticalAddonsOnly"
          effect: "NoSchedule"
      iam_role: "pao-system-node-role"
      
    - name: "general"
      instance_type: "m6i.2xlarge"
      capacity_type: "SPOT"  # 70% spot, 30% on-demand
      min_size: 10
      max_size: 500
      desired_size: 20
      labels:
        workload: "general"
      taints: []
      iam_role: "pao-general-node-role"
      
    - name: "ml-inference"
      instance_type: "g5.2xlarge"  # 1x A10G
      capacity_type: "ON_DEMAND"
      min_size: 2
      max_size: 100
      desired_size: 5
      labels:
        workload: "ml-inference"
        nvidia.com/gpu: "true"
      taints:
        - key: "nvidia.com/gpu"
          effect: "NoSchedule"
      iam_role: "pao-ml-node-role"
      
    - name: "ml-training"
      instance_type: "p4d.24xlarge"  # 8x A100
      capacity_type: "SPOT"
      min_size: 0
      max_size: 20
      labels:
        workload: "ml-training"
        nvidia.com/gpu: "true"
      taints:
        - key: "nvidia.com/gpu"
          effect: "NoSchedule"
      iam_role: "pao-ml-node-role"

  addons:
    - vpc-cni: "latest"
    - coredns: "latest"
    - kube-proxy: "latest"
    - aws-ebs-csi-driver: "latest"
    - aws-efs-csi-driver: "latest"
    - cert-manager: "latest"
    - external-dns: "latest"
    - cluster-autoscaler: "latest"
    - metrics-server: "latest"
    - prometheus-operator: "latest"
    - loki: "latest"
    - tempo: "latest"
    - istio: "latest"  # Via IstioOperator
```

### Namespace Structure

```yaml
namespaces:
  - name: "pao-system"
    labels:
      environment: "production"
      team: "platform"
    quotas:
      cpu: "100"
      memory: "200Gi"
      pods: "200"
    network_policies:
      - "deny-all-default"
      - "allow-dns"
      - "allow-monitoring"
  
  - name: "pao-production"
    labels:
      environment: "production"
      team: "product"
    quotas:
      cpu: "2000"
      memory: "4Ti"
      pods: "2000"
    network_policies:
      - "deny-all-default"
      - "allow-ingress-gateway"
      - "allow-service-mesh"
      - "allow-database"
      - "allow-cache"
      - "allow-kafka"
  
  - name: "pao-staging"
    labels:
      environment: "staging"
      team: "product"
    quotas:
      cpu: "500"
      memory: "1Ti"
      pods: "500"
  
  - name: "pao-monitoring"
    labels:
      environment: "production"
      team: "platform"
    quotas:
      cpu: "100"
      memory: "200Gi"
      pods: "100"
  
  - name: "pao-data"
    labels:
      environment: "production"
      team: "data"
    quotas:
      cpu: "200"
      memory: "500Gi"
      pods: "100"
    network_policies:
      - "deny-all-default"
      - "allow-internal-clients"
  
  - name: "cert-manager"
    labels:
      app: "cert-manager"
  
  - name: "istio-system"
    labels:
      app: "istio"
  
  - name: "ingress-nginx"
    labels:
      app: "ingress-nginx"
```

### Resource Management

```yaml
# LimitRanges (per namespace)
limit_ranges:
  default:
    cpu_request: "100m"
    cpu_limit: "1000m"
    memory_request: "128Mi"
    memory_limit: "1Gi"
  ml-inference:
    cpu_request: "1000m"
    cpu_limit: "4000m"
    memory_request: "4Gi"
    memory_limit: "16Gi"
    nvidia.com/gpu_request: "1"
    nvidia.com/gpu_limit: "1"

# PriorityClasses
priority_classes:
  - name: "system-critical"
    value: 1000000
    global_default: false
    description: "Critical system pods (DNS, CNI, CSI)"
  
  - name: "high-priority"
    value: 10000
    global_default: false
    description: "API services, safety engine"
  
  - name: "default-priority"
    value: 0
    global_default: true
    description: "Standard workloads"
  
  - name: "low-priority"
    value: -10000
    global_default: false
    description: "Batch jobs, training"

# Vertical Pod Autoscaler
vpa:
  enabled: true
  mode: "Auto"  # For non-critical workloads
  excluded_workloads:
    - "conversation-engine"
    - "safety-engine"
    - "voice-engine"
```

---

## Service Mesh (Istio)

### Configuration

```yaml
istio:
  profile: "custom"
  components:
    pilot:
      autoscale_enabled: true
      resources:
        requests:
          cpu: "500m"
          memory: "2Gi"
    ingress_gateways:
      - name: "istio-ingressgateway"
        enabled: true
        ports:
          - port: 80
            target_port: 8080
            name: http2
          - port: 443
            target_port: 8443
            name: https
          - port: 15443
            target_port: 15443
            name: tls
        autoscaling:
          min_replicas: 3
          max_replicas: 50
    egress_gateway:
      enabled: true
      name: "istio-egressgateway"
    cni:
      enabled: true

  mesh_config:
    default_config:
      proxy_metadata:
        ISTIO_META_DNS_CAPTURE: "true"
        ISTIO_META_DNS_AUTO_ALLOCATE: "true"
      tracing:
        sampling: 10  # 10% for success, 100% for errors
        zipkin:
          address: "tempo.pao-monitoring:9411"
      extension_providers:
        - name: "opa"
          envoy_ext_authz_grpc:
            service: "opa.pao-system.svc.cluster.local"
            port: "9191"
    enable_auto_mtls: true
    trust_domain: "pao.cluster.local"
    ca_certificates:
      - pem: "${ROOT_CA_PEM}"
        is_root: true

  authorization_policies:
    - name: "default-deny"
      namespace: "pao-production"
      spec:
        action: DENY
        rules: []
    
    - name: "allow-same-namespace"
      namespace: "pao-production"
      spec:
        action: ALLOW
        rules:
          - from:
              - source:
                  principals: ["cluster.local/ns/pao-production/sa/*"]
    
    - name: "allow-monitoring"
      namespace: "pao-production"
      spec:
        action: ALLOW
        rules:
          - from:
              - source:
                  namespaces: ["pao-monitoring"]
          - to:
              - operation:
                  ports: ["15020", "8080", "9090"]
    
    - name: "allow-ingress"
      namespace: "pao-production"
      spec:
        action: ALLOW
        rules:
          - from:
              - source:
                  principals: ["cluster.local/ns/ingress-nginx/sa/ingress-nginx"]
    
    - name: "engine-to-engine"
      namespace: "pao-production"
      spec:
        action: ALLOW
        rules:
          - from:
              - source:
                  principals: 
                    - "cluster.local/ns/pao-production/sa/conversation-engine"
                    - "cluster.local/ns/pao-production/sa/memory-engine"
                    - "cluster.local/ns/pao-production/sa/relationship-engine"
                    - "cluster.local/ns/pao-production/sa/emotion-engine"
                    - "cluster.local/ns/pao-production/sa/voice-engine"
                    - "cluster.local/ns/pao-production/sa/proactive-engine"
                    - "cluster.local/ns/pao-production/sa/safety-engine"
                    - "cluster.local/ns/pao-production/sa/evaluation-engine"
            to:
              - operation:
                  methods: ["GET", "POST"]
                  paths: ["/api/*", "/grpc/*"]

  peer_authentication:
    - name: "default-mtls"
      namespace: "pao-production"
      spec:
        mtls:
          mode: STRICT
    
    - name: "ingress-permissive"
      namespace: "ingress-nginx"
      spec:
        mtls:
          mode: PERMISSIVE
        selector:
          matchLabels:
            app: ingress-nginx
```

---

## Data Infrastructure

### PostgreSQL (RDS / Cloud SQL)

```yaml
postgresql:
  engine: "PostgreSQL 16"
  instance_class: "db.r6g.4xlarge"  # 16 vCPU, 128 GiB
  multi_az: true
  storage:
    type: "gp3"
    allocated: "2000 GiB"
    max_allocated: "10000 GiB"
    iops: 20000
    throughput: 500
    encryption: "KMS"
  backup:
    retention_days: 35
    window: "03:00-04:00 UTC"
    snapshot_copy_region: "us-west-2"
    point_in_time_recovery: true
  maintenance:
    window: "Sun 04:00-05:00 UTC"
  parameters:
    max_connections: 5000
    shared_buffers: "32GB"
    effective_cache_size: "96GB"
    work_mem: "64MB"
    maintenance_work_mem: "2GB"
    checkpoint_completion_target: 0.9
    wal_buffers: "64MB"
    default_statistics_target: 100
    random_page_cost: 1.1
    effective_io_concurrency: 200
    max_worker_processes: 32
    max_parallel_workers_per_gather: 8
    max_parallel_workers: 16
    pg_stat_statements_track: "all"
    log_min_duration_statement: 1000
    log_statement: "ddl"
    log_lock_waits: "on"
    log_temp_files: 0
  read_replicas:
    - region: "us-west-2"
      instance_class: "db.r6g.2xlarge"
      max_lag: "1s"
    - region: "eu-west-1"
      instance_class: "db.r6g.2xlarge"
      max_lag: "5s"
  monitoring:
    enhanced_monitoring: 60
    performance_insights: true
    retention_days: 731

# Connection Pooling (PgBouncer)
pgbouncer:
  pool_mode: "transaction"
  max_client_conn: 10000
  default_pool_size: 100
  min_pool_size: 20
  reserve_pool_size: 10
  reserve_pool_timeout: 5
  max_db_connections: 200
  max_user_connections: 200
```

### Qdrant (Vector Database)

```yaml
qdrant:
  deployment: "Qdrant Cloud / Self-managed on EKS"
  cluster:
    nodes: 6
    node_type: "r6g.2xlarge"  # 8 vCPU, 64 GiB
    storage_per_node: "1 TiB NVMe"
    replication_factor: 2
  collections:
    - name: "episodic"
      shards: 12
      replication_factor: 2
      write_consistency: "quorum"
    - name: "semantic"
      shards: 6
      replication_factor: 2
    - name: "emotional"
      shards: 6
      replication_factor: 2
    - name: "voice_timbre"
      shards: 3
      replication_factor: 2
  hnsw:
    m: 16
    ef_construct: 100
    full_scan_threshold: 10000
  quantization:
    scalar:
      type: "int8"
      quantile: 0.99
      always_ram: true
  backup:
    schedule: "0 3 * * *"  # Daily 3 AM
    retention: "14d"
    storage: "s3://pao-backups/qdrant"
  monitoring:
    prometheus_endpoint: "/metrics"
    grafana_dashboards: true
```

### Kuzu (Graph Database)

```yaml
kuzu:
  deployment: "Self-managed on EKS (StatefulSet)"
  cluster:
    nodes: 3  # Single writer, 2 readers
    node_type: "r6g.xlarge"  # 4 vCPU, 32 GiB
    storage_per_node: "500 GiB gp3"
  configuration:
    max_db_size: "100GB"
    buffer_pool_size: "16GB"
    max_num_threads: 8
    enable_compression: true
    checkpoint_interval: "5min"
  replication:
    mode: "async"
    sync_interval: "1s"
  backup:
    schedule: "0 4 * * *"
    retention: "14d"
    storage: "s3://pao-backups/kuzu"
  read_replicas:
    - region: "us-west-2"
      lag: "< 5s"
```

### Redis (ElastiCache / Memorystore)

```yaml
redis:
  engine: "Redis 7.2 (Cluster Mode)"
  cluster:
    node_type: "cache.r6g.2xlarge"  # 8 vCPU, 64 GiB
    num_shards: 10
    replicas_per_shard: 2
    automatic_failover: true
    multi_az: true
  configuration:
    maxmemory_policy: "allkeys-lru"
    timeout: 300
    tcp_keepalive: 60
    lazyfree_lazy_eviction: "yes"
    lazyfree_lazy_expire: "yes"
    lazyfree_lazy_server_del: "yes"
    replica_lazy_flush: "yes"
  backup:
    snapshot_retention: 7
    snapshot_window: "05:00-06:00 UTC"
  monitoring:
    cloudwatch_metrics: true
    slow_log: "enabled"
```

### Kafka (MSK / Confluent Cloud)

```yaml
kafka:
  deployment: "AWS MSK (Provisioned)"
  version: "3.7"
  cluster:
    broker_nodes: 9
    broker_type: "kafka.m7g.large"  # 2 vCPU, 8 GiB
    storage_per_broker: "2000 GiB gp3"
    zones: 3
  topics:
    default_partitions: 50
    default_replication_factor: 3
    min_insync_replicas: 2
    retention:
      default: "7d"
      audit: "2555d"  # 7 years
      compacted: "compact"
  configuration:
    auto_create_topics: false
    delete_topic_enable: true
    log_cleaner_threads: 2
    num_replica_fetchers: 4
    replica_socket_timeout_ms: 30000
    replica_fetch_max_bytes: 1048576
    max_message_bytes: 1048576
    compression_type: "zstd"
  encryption:
    in_transit: "TLS 1.2"
    at_rest: "KMS"
  client_auth: "SASL/SCRAM-SHA-512"
  monitoring:
    prometheus_jmx_exporter: true
    cloudwatch: true
  schema_registry:
    deployment: "Confluent Cloud"
    compatibility: "BACKWARD"
```

---

## Storage Infrastructure

### Object Storage (MinIO / S3 / GCS)

```yaml
minio:
  deployment: "MinIO Operator on EKS (Primary) + S3 Cross-region replication"
  cluster:
    nodes: 4
    drives_per_node: 4
    drive_size: "4 TiB NVMe"
    total_raw: "64 TiB"
    usable: "~48 TiB"  # Erasure coding
  buckets:
    - name: "pao-audio"
      versioning: true
      lifecycle:
        - transition: "30d" -> "IA"
        - transition: "90d" -> "Glacier"
        - expiration: "365d"
      encryption: "SSE-KMS"
      cors:
        - allowed_origins: ["https://app.pao.app"]
          allowed_methods: ["GET", "PUT", "HEAD"]
          allowed_headers: ["*"]
          max_age_seconds: 3600
    - name: "pao-exports"
      versioning: true
      lifecycle:
        - expiration: "7d"
      encryption: "SSE-KMS"
    - name: "pao-backups"
      versioning: true
      lifecycle:
        - transition: "7d" -> "IA"
        - transition: "30d" -> "Glacier"
        - expiration: "2555d"
      encryption: "SSE-KMS"
      replication:
        destination: "s3://pao-backups-dr-us-west-2"
    - name: "pao-ml-artifacts"
      versioning: true
      lifecycle:
        - transition: "30d" -> "IA"
        - expiration: "365d"
      encryption: "SSE-KMS"
    - name: "pao-avatars"
      versioning: false
      public_read: false
      cloudfront: true
      encryption: "SSE-KMS"
  monitoring:
    prometheus_exporter: true
    alerts:
      - "disk_usage > 80%"
      - "node_offline"
      - "replication_lag > 5m"
```

---

## Network Infrastructure

### DNS & CDN (Cloudflare)

```yaml
cloudflare:
  zone: "pao.app"
  dns_records:
    - name: "api"
      type: "CNAME"
      target: "api.pao.app.edge.cloudflare.net"
      proxy: true
    - name: "ws"
      type: "CNAME"
      target: "ws.pao.app.edge.cloudflare.net"
      proxy: true
    - name: "grpc"
      type: "CNAME"
      target: "grpc.pao.app.edge.cloudflare.net"
      proxy: true
    - name: "app"
      type: "CNAME"
      target: "app.pao.app.pages.cloudflare.net"
      proxy: true
  
  waf_rules:
    - id: "rate_limit_api"
      action: "challenge"
      threshold: "1000/minute"
      scope: "IP"
    - id: "block_tor"
      action: "block"
      list: "tor_exit_nodes"
    - id: "block_known_bots"
      action: "managed_challenge"
      category: "bad_bot"
  
  rate_limiting:
    - name: "api_global"
      threshold: "5000/minute"
      period: "1m"
      action: "block_1h"
    - name: "auth_endpoints"
      threshold: "20/minute"
      period: "1m"
      action: "block_15m"
  
  bot_management:
    enabled: true
    action: "managed_challenge"
  
  ddos:
    enabled: true
    sensitivity: "high"
    action: "block"
  
  ssl_tls:
    encryption_mode: "Full (Strict)"
    minimum_version: "TLS 1.2"
    automatic_https_rewrites: true
    always_use_https: true
  
  workers:
    - name: "geo-routing"
      route: "api/*"
      script: |
        // Route to nearest healthy region
        const region = getNearestRegion(request.cf.country);
        return fetch(`https://api-${region}.pao.app${request.url.pathname}`, request);
    
    - name: "security_headers"
      route: "*"
      script: |
        response.headers.set("X-Content-Type-Options", "nosniff");
        response.headers.set("X-Frame-Options", "DENY");
        response.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
        response.headers.set("Permissions-Policy", "microphone=(), camera=()");
        return response;

  load_balancing:
    - name: "api-lb"
      pools:
        - name: "us-east-1"
          origin: "api-us-east-1.pao.app"
          weight: 1
          health_check: "/health/ready"
        - name: "us-west-2"
          origin: "api-us-west-2.pao.app"
          weight: 1
          health_check: "/health/ready"
        - name: "eu-west-1"
          origin: "api-eu-west-1.pao.app"
          weight: 1
          health_check: "/health/ready"
      steering_policy: "geo"
      session_affinity: "cookie"
```

### VPC Peering / Transit Gateway

```yaml
network_connectivity:
  transit_gateway:
    asn: 64512
    vpc_attachments:
      - vpc: "pao-production-us-east-1"
      - vpc: "pao-production-us-west-2"
      - vpc: "pao-production-eu-west-1"
      - vpc: "pao-production-ap-southeast-1"
    route_tables:
      - name: "production"
        associations: ["all"]
        propagation: ["all"]
        routes:
          - cidr: "10.0.0.0/8"
            attachment: "all"
            blackhole: false
  
  vpc_peering:
    # For cross-cloud (AWS <-> GCP)
    - name: "aws-gcp-us"
      aws_vpc: "pao-production-us-east-1"
      gcp_network: "pao-production-us-central1"
      connection_type: "Partner Interconnect / Cloud VPN"
      bandwidth: "10 Gbps"
      bgp: true
```

---

## CI/CD Infrastructure

### GitOps (ArgoCD)

```yaml
argocd:
  deployment: "Helm on EKS"
  high_availability: true
  replicas: 3
  repositories:
    - url: "https://github.com/pao/infrastructure-config"
      type: "git"
      username: "argocd"
      password_secret: "argocd-git-credentials"
    - url: "https://github.com/pao/application-config"
      type: "git"
  projects:
    - name: "platform"
      source_repos: ["infrastructure-config"]
      destinations:
        - server: "https://kubernetes.default.svc"
          namespace: "pao-system"
      cluster_resource_whitelist:
        - group: ""
          kind: "Namespace"
        - group: "rbac.authorization.k8s.io"
          kind: "ClusterRole"
    - name: "product"
      source_repos: ["application-config"]
      destinations:
        - server: "https://kubernetes.default.svc"
          namespace: "pao-production"
      namespace_resource_whitelist:
        - group: "apps"
          kind: "Deployment"
        - group: ""
          kind: "Service"
        - group: "networking.k8s.io"
          kind: "Ingress"
  sync_windows:
    - kind: "allow"
      schedule: "0 2 * * *"  # Daily 2 AM UTC
      duration: "4h"
      applications: ["*"]
      manual_sync: true  # Outside window
  rbac:
    - role: "admin"
      groups: ["platform-team"]
    - role: "readonly"
      groups: ["security-team", "data-team"]
```

### Build Pipeline (GitHub Actions)

```yaml
# .github/workflows/build.yaml
build_pipeline:
  triggers:
    - push: [main, release/*]
    - pull_request: [main]
    - schedule: "0 6 * * 1"  # Weekly Monday
  
  jobs:
    lint:
      runs_on: "ubuntu-latest"
      steps:
        - "checkout"
        - "setup: go, node, python, hadolint, shellcheck, sqlfluff"
        - "run: make lint"
    
    test_unit:
      runs_on: "ubuntu-latest"
      services: [postgresql, redis, kafka]
      steps:
        - "checkout"
        - "setup: go, node, python"
        - "run: make test-unit"
        - "upload: coverage"
    
    test_integration:
      runs_on: "ubuntu-latest"
      needs: [test_unit]
      steps:
        - "checkout"
        - "deploy: staging namespace"
        - "run: make test-integration"
    
    build_images:
      runs_on: "ubuntu-latest"
      needs: [test_integration]
      strategy:
        matrix:
          service: [api-gateway, companion-api, identity-engine, conversation-engine, memory-engine, relationship-engine, emotion-engine, voice-engine, proactive-engine, safety-engine, evaluation-engine]
      steps:
        - "checkout"
        - "setup: docker buildx, cosign"
        - "build: multi-arch (amd64, arm64)"
        - "scan: trivy, grype"
        - "sign: cosign"
        - "push: ghcr.io/pao/{service}:{sha}"
        - "attest: SLSA provenance"
    
    deploy_staging:
      runs_on: "ubuntu-latest"
      needs: [build_images]
      environment: "staging"
      steps:
        - "argocd: app sync pao-staging --prune"
        - "wait: health"
        - "test: smoke"
    
    deploy_canary:
      runs_on: "ubuntu-latest"
      needs: [deploy_staging]
      environment: "production"
      steps:
        - "argocd: app set pao-production --parameter image.tag={sha}"
        - "argocd: app sync pao-production --prune --selector canary=true"
        - "wait: health"
        - "monitor: 30m"
        - "promote: manual_approval"
    
    deploy_production:
      runs_on: "ubuntu-latest"
      needs: [deploy_canary]
      environment: "production"
      steps:
        - "argocd: app sync pao-production --prune"
        - "wait: health"
        - "notify: slack, pagerduty"

  security_gates:
    - "no_critical_vulnerabilities"
    - "no_secrets_in_images"
    - "sbom_generated"
    - "image_signed"
    - "provenance_verified"
```

---

## Monitoring Infrastructure

### Prometheus Stack

```yaml
prometheus:
  deployment: "Prometheus Operator (kube-prometheus-stack)"
  retention: "15d"  # Hot
  remote_write:
    - url: "https://prometheus.grafana.cloud/api/prom/push"
      basic_auth:
        username: "${GRAFANA_CLOUD_USER}"
        password: "${GRAFANA_CLOUD_API_KEY}"
  rules:
    - name: "platform.rules"
      groups: ["kubernetes", "node", "pod", "container", "apiserver"]
    - name: "application.rules"
      groups: ["http", "grpc", "database", "cache", "queue", "business"]
    - name: "slo.rules"
      groups: ["latency", "availability", "quality", "safety"]
  alertmanager:
    replicas: 3
    config:
      receivers:
        - name: "critical"
          pagerduty_configs:
            - service_key: "${PAGERDUTY_CRITICAL_KEY}"
              severity: "critical"
        - name: "warning"
          slack_configs:
            - api_url: "${SLACK_WEBHOOK}"
              channel: "#alerts-warning"
        - name: "info"
          slack_configs:
            - api_url: "${SLACK_WEBHOOK}"
              channel: "#alerts-info"
      route:
        group_by: ["alertname", "cluster", "service"]
        group_wait: "30s"
        group_interval: "5m"
        repeat_interval: "4h"
        receiver: "critical"
        routes:
          - match:
              severity: "warning"
            receiver: "warning"
          - match:
              severity: "info"
            receiver: "info"
```

### Logging (Loki)

```yaml
loki:
  deployment: "Loki Stack (Helm)"
  mode: "microservices"
  retention: "30d"  # Hot in SSD, 1y cold in S3
  storage:
    type: "boltdb-shipper"
    bucket: "pao-logs-loki"
    region: "us-east-1"
  limits:
    ingestion_rate_mb: 50
    ingestion_burst_size_mb: 100
    per_stream_rate_limit: 10MB
    per_stream_rate_limit_burst: 20MB
  queries:
    max_entries_limit: 10000
    max_query_parallelism: 32
  compactor:
    retention_enabled: true
    retention_delete_delay: "2h"
```

### Tracing (Tempo/Jaeger)

```yaml
tempo:
  deployment: "Tempo Stack (Helm)"
  mode: "microservices"
  retention: "7d"
  storage:
    type: "s3"
    bucket: "pao-traces-tempo"
    region: "us-east-1"
  traces:
    otlp:
      grpc:
        endpoint: "0.0.0.0:4317"
      http:
        endpoint: "0.0.0.0:4318"
  sampling:
    default: 0.1  # 10%
    policies:
      - service: "safety-engine"
        rate: 1.0  # 100%
      - service: "voice-engine"
        rate: 0.5  # 50%
      - operation: "*.Recall"
        rate: 0.2
```

---

## Disaster Recovery

### Backup Strategy

```yaml
backup_strategy:
  postgresql:
    continuous: "WAL-G to S3 (wal-g)"
    schedule: "Every 5 minutes"
    retention: "35 days"
    cross_region: "us-west-2, eu-west-1"
    pitr: true
    test_restore: "Weekly automated"
  
  qdrant:
    snapshot: "Daily 3:30 AM UTC"
    retention: "14 days"
    storage: "s3://pao-backups/qdrant"
    verification: "Weekly restore to staging"
  
  kuzu:
    snapshot: "Daily 4:00 AM UTC"
    retention: "14 days"
    storage: "s3://pao-backups/kuzu"
  
  redis:
    rdb: "Every 60 minutes (if changes > 1)"
    aof: "Every second"
    retention: "7 days"
    cross_region: "Replica in us-west-2"
  
  kafka:
    mirror_maker_2: "Continuous to DR cluster"
    topics: "all"
    retention: "7 days"
    lag_monitoring: "Alert if > 1000 messages"
  
  minio:
    replication: "Cross-region (us-west-2, eu-west-1)"
    versioning: "Enabled"
    lifecycle: "As defined in bucket config"
  
  etcd:
    snapshot: "Every 30 minutes"
    retention: "7 days"
    storage: "S3"
    encryption: "KMS"
```

### Recovery Procedures

```markdown
## DR Playbooks

### PLAYBOOK-DR-001: Regional Outage (Primary Region Down)
**RTO: < 15 minutes | RPO: < 1 minute**

1. **Detection** (Automated)
   - Cloudflare health checks fail
   - Route53 failover triggers
   - PagerDuty alerts fire

2. **Failover** (Automated via Cloudflare)
   - DNS switches to secondary region
   - Cloudflare Load Balancer routes traffic
   - Global accelerator updates endpoints

3. **Verification** (Automated + Manual)
   - Smoke tests against secondary
   - Database replication lag check
   - Cache warmup (if needed)

4. **Communication**
   - Status page updated
   - Slack #incidents notification
   - Customer notification if > 5 min

5. **Failback** (Planned)
   - Primary region restored
   - Data consistency verified
   - Scheduled failback during low traffic

### PLAYBOOK-DR-002: Database Corruption
**RTO: < 30 minutes | RPO: < 1 second**

1. **Detection**
   - Automated integrity checks fail
   - Application errors spike
   - pg_dump verification fails

2. **Containment**
   - Stop writes to affected DB
   - Promote read replica (if healthy)
   - Or restore from latest clean backup

3. **Recovery**
   - Point-in-time recovery to before corruption
   - Verify data integrity
   - Rebuild read replicas

4. **Validation**
   - Run consistency checks
   - Application smoke tests
   - Monitor for anomalies

### PLAYBOOK-DR-003: Ransomware / Encryption Attack
**RTO: < 4 hours | RPO: < 1 hour**

1. **Detection**
   - Anomalous encryption activity
   - File extension changes
   - Ransom notes

2. **Containment**
   - Isolate affected systems (NetworkPolicy)
   - Revoke compromised credentials
   - Enable maximum WAF rules

3. **Assessment**
   - Identify blast radius
   - Determine last clean backup
   - Check backup integrity (offline)

4. **Recovery**
   - Restore from immutable backups
   - Rebuild infrastructure from IaC
   - Rotate ALL credentials/keys

5. **Post-Incident**
   - Forensic analysis
   - Root cause
   - Improved defenses
```

---

## Cost Optimization

### Strategies

```yaml
cost_optimization:
  compute:
    - "Spot instances for fault-tolerant workloads (70% savings)"
    - "Savings Plans for baseline (30-40% savings)"
    - "Right-sizing via VPA (15-20% savings)"
    - "Scale-to-zero for dev/staging (nights/weekends)"
    - "GPU time-slicing for inference (multi-tenancy)"
  
  storage:
    - "Intelligent tiering for object storage"
    - "gp3 over gp2 (20% cheaper, better performance)"
    - "Delete orphaned snapshots/volumes (automated)"
    - "Compress database backups"
    - "Lifecycle policies for logs/traces"
  
  network:
    - "VPC endpoints for AWS services (no NAT charges)"
    - "Cloudflare for DDoS/WAF (cheaper than ALB)"
    - "Regional traffic stays regional"
    - "Compress API responses (gzip/brotli)"
  
  data_transfer:
    - "Cross-region replication only for DR"
    - "CDN for static assets"
    - "Batch processing during off-peak"
  
  monitoring:
    - "Downsample high-cardinality metrics"
    - "Retention policies per metric importance"
    - "Sampling for traces (10% default)"

### Budget & Alerts

budgets:
  - name: "monthly_total"
    amount: 500000  # USD
    alerts:
      - threshold: 50%
        notify: "finance-team"
      - threshold: 80%
        notify: "platform-team, finance-team"
      - threshold: 100%
        notify: "all-leadership"
        action: "freeze_non_critical_spending"
  
  - name: "compute_monthly"
    amount: 200000
    alerts:
      - threshold: 80%
        notify: "platform-team"
  
  - name: "gpu_monthly"
    amount: 100000
    alerts:
      - threshold: 70%
        notify: "ml-team, platform-team"
```

---

## Infrastructure as Code

### Tooling

```yaml
iac:
  primary: "Terraform (Cloud/Enterprise)"
  modules:
    - "vpc"
    - "eks-cluster"
    - "rds-postgresql"
    - "elasticache-redis"
    - "msk-kafka"
    - "s3-buckets"
    - "iam-roles"
    - "cloudflare"
    - "datadog"
    - "pagerduty"
  
  state_backend:
    type: "S3 + DynamoDB locking"
    bucket: "pao-terraform-state"
    key: "{environment}/{region}/{module}/terraform.tfstate"
    encryption: "KMS"
    dynamodb_table: "terraform-locks"
  
  workflow:
    - "PR: terraform plan (auto-comment)"
    - "Merge: terraform apply (auto-approve for non-prod)"
    - "Prod: Manual approval in Atlantis"
    - "Drift detection: Daily"
  
  testing:
    - "terratest for module validation"
    - "checkov for policy as code"
    - "tfsec for security scanning"
    - "infracost for cost estimation"
```

### GitOps Repository Structure

```
infrastructure-config/
├── clusters/
│   ├── production-us-east-1/
│   │   ├── cluster.yaml
│   │   ├── node-groups.yaml
│   │   ├── addons/
│   │   └── namespaces/
│   ├── production-eu-west-1/
│   └── staging-us-east-1/
├── services/
│   ├── postgresql/
│   ├── qdrant/
│   ├── kuzu/
│   ├── redis/
│   ├── kafka/
│   └── minio/
├── networking/
│   ├── cloudflare/
│   ├── transit-gateway/
│   └── vpc-peering/
├── security/
│   ├── iam/
│   ├── vault/
│   ├── certificates/
│   └── waf/
├── monitoring/
│   ├── prometheus/
│   ├── loki/
│   ├── tempo/
│   └── alertmanager/
└── argocd/
    ├── projects/
    └── applications/

application-config/
├── base/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── hpa.yaml
│   ├── pdb.yaml
│   └── servicemonitor.yaml
├── overlays/
│   ├── production/
│   │   ├── kustomization.yaml
│   │   ├── replicas.yaml
│   │   ├── resources.yaml
│   │   └── secrets.yaml
│   ├── staging/
│   └── canary/
└── services/
    ├── conversation-engine/
    ├── memory-engine/
    └── ...
```

---

## Operational Procedures

### Runbooks

```markdown
## Critical Runbooks

### RUNBOOK-001: Service Deployment
1. Create PR with image tag update in application-config
2. ArgoCD syncs to staging automatically
3. Run smoke tests
4. Promote to canary (5% traffic)
5. Monitor for 30 minutes (SLO dashboards)
6. Manual approval to promote to 100%
7. ArcoCD syncs production
8. Post-deployment verification

### RUNBOOK-002: Database Schema Migration
1. Create migration SQL (up + down)
2. Test on staging copy
3. Schedule during low-traffic window
4. Run via migration job (with lock)
5. Verify application health
6. Monitor error rates
7. Mark migration complete

### RUNBOOK-003: Certificate Rotation
1. Cert-manager auto-renews (30 days before expiry)
2. Verify new cert in staging
3. Monitor for SSL errors
4. Alert if not renewed within 7 days

### RUNBOOK-004: Secret Rotation
1. Vault rotates automatically (90 days)
2. CSI driver updates pod env vars
3. Rolling restart of affected deployments
4. Verify no errors

### RUNBOOK-005: Capacity Scaling
1. Cluster autoscaler handles nodes
2. HPA handles pod replicas
3. VPA handles resource requests
4. Manual intervention only for:
   - New node groups
   - Quota increases
   - GPU allocation

### RUNBOOK-006: Incident Response
1. Acknowledge PagerDuty alert
2. Join incident channel
3. Follow PLAYBOOK-XXX
4. Update status page
5. Postmortem within 5 days
```

---

## Infrastructure Roadmap

### Phase 1 (Current)
- [x] Multi-region EKS/GKE
- [x] Istio service mesh
- [x] GitOps with ArgoCD
- [x] Comprehensive observability
- [x] Automated DR failover
- [x] Terraform for all infrastructure
- [x] Cost optimization (Spot, Savings Plans)

### Phase 2 (6 months)
- [ ] Local-first sync infrastructure
- [ ] Edge computing (Cloudflare Workers)
- [ ] Federated learning infrastructure
- [ ] Advanced capacity planning (ML-based)
- [ ] Chaos engineering automation
- [ ] Supply chain security (SLSA L3)

### Phase 3 (12 months)
- [ ] Custom Kubernetes operator for Companion lifecycle
- [ ] Serverless inference (Knative)
- [ ] Confidential computing (Nitro Enclaves / TDX)
- [ ] Quantum-safe infrastructure
- [ ] Decentralized infrastructure options

---

**Aligned With:** `300-system-architecture.md`, `330-security-model.md`, `04-engineering/`
**Next Review:** 2026-01-17