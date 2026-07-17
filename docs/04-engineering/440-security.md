# PAO Security Engineering Guide

**Version:** 1.0
**Status:** Draft
**Owner:** PAO Security Team

---

## Overview

This document defines the security engineering practices, standards, and implementation guidelines for PAO.

> **Security Principle:** Security is everyone's responsibility. Defense in depth, zero trust, privacy by design, secure by default.

---

## Security Architecture

### Zero Trust Model

```
┌─────────────────────────────────────────────────────────────────┐
│                    ZERO TRUST ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   IDENTITY  │    │   DEVICE    │    │   NETWORK   │         │
│  │  PROVIDER   │    │  TRUST      │    │  SEGMENTATION│        │
│  │  (OIDC/OAuth)│   │  (MDM/TPM)  │    │  (Istio mTLS)│        │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘         │
│         │                  │                  │                 │
│         └──────────────────┼──────────────────┘                 │
│                            ▼                                    │
│                   ┌─────────────────┐                           │
│                   │  POLICY ENGINE  │                           │
│                   │  (OPA/Rego)     │                           │
│                   └────────┬────────┘                           │
│                            │                                    │
│         ┌──────────────────┼──────────────────┐                │
│         ▼                  ▼                  ▼                │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │   DATA      │    │  WORKLOAD   │    │  VISIBILITY │        │
│  │  PROTECTION │    │  PROTECTION │    │  & AUDIT    │        │
│  │  (Encryption│    │  (Runtime   │    │  (SIEM/     │        │
│  │   DLP)      │    │   Security) │    │   Audit)    │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

### Trust Boundaries

| Boundary | Controls |
|----------|----------|
| **Internet → Edge** | WAF, DDoS protection, Rate limiting, TLS 1.3 |
| **Edge → Services** | mTLS (Istio), JWT validation, Rate limiting |
| **Service → Service** | mTLS, Service identity (SPIFFE), Authorization (OPA) |
| **Service → Data** | Encryption at rest, Column-level encryption, IAM |
| **Admin → Systems** | Bastion hosts, MFA, Just-in-time access, Audit logging |

---

## Identity & Access Management

### Authentication

```yaml
# Primary: OAuth2/OIDC with PKCE
authentication:
  providers:
    - name: "google"
      type: "oidc"
      config:
        client_id: "${GOOGLE_CLIENT_ID}"
        client_secret: "${GOOGLE_CLIENT_SECRET}"
        scopes: ["openid", "email", "profile"]
    
    - name: "apple"
      type: "oidc"
      config:
        client_id: "${APPLE_CLIENT_ID}"
        team_id: "${APPLE_TEAM_ID}"
        key_id: "${APPLE_KEY_ID}"
        private_key: "${APPLE_PRIVATE_KEY}"
        scopes: ["name", "email"]
    
    - name: "email_password"
      type: "credentials"
      config:
        argon2_params:
          memory: 65536
          iterations: 3
          parallelism: 4
        max_attempts: 5
        lockout_duration: "15m"
  
  # Session management
  session:
    access_token_ttl: "15m"
    refresh_token_ttl: "30d"
    refresh_token_rotation: true
    refresh_token_reuse_detection: true
    device_fingerprinting: true
  
  # MFA
  mfa:
    required_for: ["admin", "sensitive_operations"]
    methods: ["totp", "webauthn", "sms"]
    backup_codes: 10
```

### Authorization (OPA/Rego)

```rego
# policies/authorization.rego
package pao.authz

import future.keywords.if
import future.keywords.in

# Default deny
default allow := false

# Allow if user owns the companion
allow if {
    input.action == "companion:read"
    input.resource.companion_id == input.user.id
}

allow if {
    input.action == "companion:write"
    input.resource.companion_id == input.user.id
    not input.resource.is_deleted
}

# Allow if user is admin
allow if {
    input.user.roles contains "admin"
}

# Allow if user has specific permission
allow if {
    permission := sprintf("%s:%s", [input.resource.type, input.action])
    permission in input.user.permissions
}

# Service-to-service (internal)
allow if {
    input.source.type == "service"
    input.source.name in data.allowed_service_calls[input.resource.service]
}

# Rate limiting check
allow if {
    not rate_limited(input.user.id, input.action)
}

# Safety override (always allow safety engine)
allow if {
    input.source.name == "safety-engine"
    input.action in ["safety:check", "safety:intervene"]
}
```

### Service Identity (SPIFFE)

```yaml
# SPIFFE IDs for services
service_identities:
  - spiffe://pao.app/ns/pao-production/sa/conversation-engine
  - spiffe://pao.app/ns/pao-production/sa/memory-engine
  - spiffe://pao.app/ns/pao-production/sa/safety-engine
  - spiffe://pao.app/ns/pao-production/sa/voice-engine

# Workload attestation via Istio
istio:
  peer_authentication:
    mtls: "STRICT"
  authorization_policy:
    - name: "conversation-engine-egress"
      rules:
        - to:
            - principals:
              - "spiffe://pao.app/ns/pao-production/sa/memory-engine"
              - "spiffe://pao.app/ns/pao-production/sa/relationship-engine"
          ports:
            - number: 9090
              protocol: "grpc"
```

---

## Data Protection

### Encryption Standards

| Data State | Algorithm | Key Management |
|------------|-----------|----------------|
| **In Transit** | TLS 1.3 (AES-256-GCM) | Istio mTLS, cert-manager |
| **At Rest (DB)** | AES-256-GCM | Vault transit engine, per-column keys |
| **At Rest (Object)** | AES-256 | S3 SSE-KMS, customer-managed keys |
| **In Memory** | Process isolation, no plaintext secrets | Enclave (future) |
| **Backups** | AES-256-GCM | Separate backup encryption keys |

### Column-Level Encryption

```sql
-- PostgreSQL with pgcrypto
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypted columns
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    companion_id UUID NOT NULL,
    -- Encrypted content (AES-256)
    content_encrypted BYTEA NOT NULL,
    -- Encryption key reference
    encryption_key_id VARCHAR(64) NOT NULL,
    -- Searchable hash for deduplication
    content_hash BYTEA GENERATED ALWAYS AS (
        digest(content_encrypted, 'sha256')
    ) STORED,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Encryption function
CREATE OR REPLACE FUNCTION encrypt_content(plaintext TEXT, key_id TEXT)
RETURNS BYTEA AS $$
DECLARE
    key BYTEA := get_encryption_key(key_id);
    iv BYTEA := gen_random_bytes(12);
    ciphertext BYTEA;
BEGIN
    ciphertext := encrypt_iv(plaintext::bytea, key, iv, 'aes-256-gcm');
    return iv || ciphertext;  -- Prepend IV
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Decryption function
CREATE OR REPLACE FUNCTION decrypt_content(encrypted BYTEA, key_id TEXT)
RETURNS TEXT AS $$
DECLARE
    key BYTEA := get_encryption_key(key_id);
    iv BYTEA := substring(encrypted FROM 1 FOR 12);
    ciphertext BYTEA := substring(encrypted FROM 13);
    plaintext BYTEA;
BEGIN
    plaintext := decrypt_iv(ciphertext, key, iv, 'aes-256-gcm');
    return plaintext::text;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

### Application-Level Encryption

```go
// crypto/encryption.go
package crypto

import (
    "crypto/aes"
    "crypto/cipher"
    "crypto/rand"
    "errors"
    "github.com/hashicorp/vault/api"
)

type EncryptionService struct {
    vault *api.Client
    keyCache map[string][]byte
}

func (e *EncryptionService) Encrypt(ctx context.Context, plaintext []byte, keyID string) ([]byte, error) {
    key, err := e.getKey(ctx, keyID)
    if err != nil {
        return nil, err
    }
    
    block, err := aes.NewCipher(key)
    if err != nil {
        return nil, err
    }
    
    gcm, err := cipher.NewGCM(block)
    if err != nil {
        return nil, err
    }
    
    nonce := make([]byte, gcm.NonceSize())
    if _, err := rand.Read(nonce); err != nil {
        return nil, err
    }
    
    ciphertext := gcm.Seal(nonce, nonce, plaintext, nil)
    return ciphertext, nil
}

func (e *EncryptionService) Decrypt(ctx context.Context, ciphertext []byte, keyID string) ([]byte, error) {
    key, err := e.getKey(ctx, keyID)
    if err != nil {
        return nil, err
    }
    
    block, err := aes.NewCipher(key)
    if err != nil {
        return nil, err
    }
    
    gcm, err := cipher.NewGCM(block)
    if err != nil {
        return nil, err
    }
    
    nonceSize := gcm.NonceSize()
    if len(ciphertext) < nonceSize {
        return nil, errors.New("ciphertext too short")
    }
    
    nonce, ciphertext := ciphertext[:nonceSize], ciphertext[nonceSize:]
    plaintext, err := gcm.Open(nil, nonce, ciphertext, nil)
    if err != nil {
        return nil, errors.New("decryption failed: integrity check failed")
    }
    
    return plaintext, nil
}

func (e *EncryptionService) getKey(ctx context.Context, keyID string) ([]byte, error) {
    if key, ok := e.keyCache[keyID]; ok {
        return key, nil
    }
    
    // Fetch from Vault transit engine
    secret, err := e.vault.Logical().ReadWithContext(ctx, "transit/keys/"+keyID)
    if err != nil {
        return nil, err
    }
    
    // Key derivation from Vault
    key := deriveKey(secret.Data["key"])
    e.keyCache[keyID] = key
    return key, nil
}
```

### Key Rotation

```yaml
# Key rotation schedule
key_rotation:
  # Data encryption keys (DEKs)
  data_encryption_keys:
    rotation_period: "90d"
    process: "automated"
    overlap_period: "7d"  # Both old and new keys work
  
  # Key encryption keys (KEKs) - Vault managed
  key_encryption_keys:
    rotation_period: "365d"
    process: "manual_approval"
    hsm_backed: true
  
  # TLS certificates
  tls_certificates:
    rotation_period: "24h"  # cert-manager auto-renewal
    process: "automated"
  
  # JWT signing keys
  jwt_signing_keys:
    rotation_period: "90d"
    process: "automated"
    jwks_endpoint: "https://auth.pao.app/.well-known/jwks.json"
```

### Data Loss Prevention (DLP)

```go
// dlp/scanner.go
package dlp

import (
    "context"
    "regexp"
    
    dlppb "cloud.google.com/go/dlp/apiv2/dlppb"
)

type DLPScanner struct {
    client *dlp.Client
    inspectionConfig *dlppb.InspectConfig
}

func (d *DLPScanner) ScanContent(ctx context.Context, content string) (*DLPResult, error) {
    // Custom info types for PAO
    customInfoTypes := []*dlppb.CustomInfoType{
        {InfoType: &dlppb.InfoType{Name: "PAO_COMPANION_ID"}, 
         Regex: &dlppb.Regex{Pattern: "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"}},
        {InfoType: &dlppb.InfoType{Name: "PAO_USER_ID"},
         Regex: &dlppb.Regex{Pattern: "user_[0-9a-f]{24}"}},
    }
    
    req := &dlppb.InspectContentRequest{
        Parent: "projects/pao-dlp/locations/global",
        Item: &dlppb.ContentItem{
            DataItem: &dlppb.ContentItem_Value{Value: content},
        },
        InspectConfig: &dlppb.InspectConfig{
            InfoTypes: defaultInfoTypes(),
            CustomInfoTypes: customInfoTypes,
            MinLikelihood: dlppb.Likelihood_POSSIBLE,
            Limits: &dlppb.InspectConfig_FindingLimits{MaxFindingsPerItem: 100},
        },
    }
    
    resp, err := d.client.InspectContent(ctx, req)
    if err != nil {
        return nil, err
    }
    
    return &DLPResult{
        Findings: resp.Result.Findings,
        RiskScore: calculateRiskScore(resp.Result.Findings),
    }, nil
}

// Block PII in proactive messages
func (p *ProactiveEngine) GenerateSafeMessage(ctx context.Context, req *GenerateRequest) (*ProactiveMessage, error) {
    msg, err := p.generateMessage(ctx, req)
    if err != nil {
        return nil, err
    }
    
    dlpResult, err := p.dlpScanner.ScanContent(ctx, msg.Content)
    if err != nil {
        return nil, err
    }
    
    if dlpResult.RiskScore > 0.7 {
        // Redact or regenerate
        msg.Content = p.redactPII(msg.Content, dlpResult.Findings)
    }
    
    return msg, nil
}
```

---

## Application Security

### Secure Coding Practices

```go
// 1. Input Validation
func (h *Handler) SendMessage(w http.ResponseWriter, r *http.Request) {
    var req SendMessageRequest
    
    // Strict decoding
    dec := json.NewDecoder(r.Body)
    dec.DisallowUnknownFields()
    if err := dec.Decode(&req); err != nil {
        h.respondError(w, ErrInvalidRequest)
        return
    }
    
    // Validate
    if err := h.validator.Struct(req); err != nil {
        h.respondError(w, ErrValidationFailed)
        return
    }
    
    // Sanitize
    req.Content = sanitize.HTML(req.Content)
    req.Content = sanitize.SQL(req.Content)  // Defense in depth
    
    // Process
    resp, err := h.service.ProcessMessage(r.Context(), &req)
}

// 2. Output Encoding
func (h *Handler) GetMessage(w http.ResponseWriter, r *http.Request) {
    msg, err := h.service.GetMessage(r.Context(), id)
    if err != nil {
        h.respondError(w, err)
        return
    }
    
    // HTML escape for web clients
    if acceptsHTML(r) {
        msg.Content = template.HTMLEscapeString(msg.Content)
    }
    
    h.respondJSON(w, msg)
}

// 3. SQL Injection Prevention - Always use parameterized queries
func (r *Repository) GetMessages(ctx context.Context, companionID uuid.UUID, limit int) ([]Message, error) {
    // GOOD: Parameterized
    rows, err := r.db.Query(ctx, `
        SELECT id, content, role, created_at 
        FROM messages 
        WHERE companion_id = $1 
        ORDER BY created_at DESC 
        LIMIT $2
    `, companionID, limit)
    
    // BAD: String interpolation (NEVER DO THIS)
    // query := fmt.Sprintf("SELECT ... WHERE companion_id = '%s'", companionID)
}

// 4. Path Traversal Prevention
func (h *Handler) GetAvatar(w http.ResponseWriter, r *http.Request) {
    filename := r.URL.Query().Get("file")
    
    // Validate filename
    if !avatarFilenameRegex.MatchString(filename) {
        h.respondError(w, ErrInvalidFilename)
        return
    }
    
    // Use secure path joining
    filepath := filepath.Join(h.avatarDir, filename)
    
    // Ensure path stays within avatar directory
    if !strings.HasPrefix(filepath, h.avatarDir) {
        h.respondError(w, ErrInvalidPath)
        return
    }
    
    http.ServeFile(w, r, filepath)
}

// 5. Secure Headers
func SecurityHeadersMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Content-Security-Policy", 
            "default-src 'self'; script-src 'self' 'nonce-{nonce}'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self' wss:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
        w.Header().Set("X-Content-Type-Options", "nosniff")
        w.Header().Set("X-Frame-Options", "DENY")
        w.Header().Set("X-XSS-Protection", "1; mode=block")
        w.Header().Set("Referrer-Policy", "strict-origin-when-cross-origin")
        w.Header().Set("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        w.Header().Set("Strict-Transport-Security", "max-age=31536000; includeSubDomains; preload")
        
        next.ServeHTTP(w, r)
    })
}
```

### Dependency Security

```yaml
# Dependency management
dependency_security:
  # Go modules
  go:
    - command: "govulncheck ./..."
      frequency: "every_build"
      block_on: ["HIGH", "CRITICAL"]
    
    - command: "go mod verify"
      frequency: "every_build"
    
    - command: "nancy sleuth"  # Check for known vulnerabilities
      frequency: "daily"
  
  # Container images
  container:
    - tool: "trivy"
      severity: ["HIGH", "CRITICAL"]
      frequency: "on_build"
      block_on: ["HIGH", "CRITICAL"]
    
    - tool: "grype"
      frequency: "weekly"
    
    - tool: "syft"  # SBOM generation
      frequency: "on_build"
      format: "spdx-json"
  
  # Supply chain
  supply_chain:
    - sigstore_cosign: true  # Sign images
    - slsa_level: 3  # Build provenance
    - sbom_required: true
    - dependency_review: "github_actions"
```

### Secrets Management

```yaml
# Vault integration
vault:
  auth_method: "kubernetes"
  role: "pao-service"
  
  # Secret paths
  paths:
    - "secret/data/pao/production/database"
    - "secret/data/pao/production/redis"
    - "secret/data/pao/production/kafka"
    - "secret/data/pao/production/llm"
    - "secret/data/pao/production/jwt"
    - "secret/data/pao/production/encryption"
  
  # Dynamic secrets
  dynamic_secrets:
    database:
      type: "postgresql"
      ttl: "1h"
      max_ttl: "4h"
    
    kafka:
      type: "kafka"
      ttl: "1h"
  
  # Rotation
  rotation:
    database_password: "24h"
    jwt_keys: "90d"
    encryption_keys: "90d"
```

```go
// secrets/manager.go
package secrets

import (
    "context"
    "github.com/hashicorp/vault/api"
)

type SecretManager struct {
    client *api.Client
}

func (s *SecretManager) GetSecret(ctx context.Context, path string) (map[string]string, error) {
    secret, err := s.client.KVv2("secret").Get(ctx, path)
    if err != nil {
        return nil, err
    }
    
    data := make(map[string]string)
    for k, v := range secret.Data {
        data[k] = v.(string)
    }
    return data, nil
}

func (s *SecretManager) GetDatabaseCredentials(ctx context.Context) (*DBCredentials, error) {
    secret, err := s.GetSecret(ctx, "pao/production/database")
    if err != nil {
        return nil, err
    }
    
    return &DBCredentials{
        Username: secret["username"],
        Password: secret["password"],
        Host:     secret["host"],
        Port:     secret["port"],
        Database: secret["database"],
    }, nil
}
```

---

## Network Security

### Service Mesh (Istio) Configuration

```yaml
# Istio PeerAuthentication - mTLS STRICT
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: pao-production
spec:
  mtls:
    mode: STRICT

---
# Istio AuthorizationPolicy - Default deny
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: default-deny
  namespace: pao-production
spec:
  action: DENY
  rules: []

---
# Conversation Engine - Allow specific callers
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: conversation-engine-ingress
  namespace: pao-production
spec:
  selector:
    matchLabels:
      app: conversation-engine
  action: ALLOW
  rules:
    - from:
      - source:
          principals:
          - "spiffe://pao.app/ns/pao-production/sa/api-gateway"
          - "spiffe://pao.app/ns/pao-production/sa/companion-api"
          - "spiffe://pao.app/ns/pao-production/sa/proactive-engine"
      to:
      - operation:
          ports: ["9090"]
          methods: ["POST"]

---
# Egress - Allow only specific external endpoints
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: conversation-engine-egress
  namespace: pao-production
spec:
  selector:
    matchLabels:
      app: conversation-engine
  action: ALLOW
  rules:
    - to:
      - operation:
          hosts:
          - "memory-engine.pao-production.svc.cluster.local"
          - "relationship-engine.pao-production.svc.cluster.local"
          - "safety-engine.pao-production.svc.cluster.local"
          - "api.openai.com"
          - "api.anthropic.com"
          ports: ["443", "9090"]
```

### Network Policies (Kubernetes)

```yaml
# Default deny all ingress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: pao-production
spec:
  podSelector: {}
  policyTypes:
  - Ingress

---
# Allow ingress to conversation-engine from specific namespaces
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: conversation-engine-ingress
  namespace: pao-production
spec:
  podSelector:
    matchLabels:
      app: conversation-engine
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: pao-system
    - podSelector:
        matchLabels:
          app: api-gateway
    - podSelector:
        matchLabels:
          app: companion-api
    ports:
    - protocol: TCP
      port: 9090

---
# Allow egress to dependencies
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: conversation-engine-egress
  namespace: pao-production
spec:
  podSelector:
    matchLabels:
      app: conversation-engine
  policyTypes:
  - Egress
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgresql
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
  - to:
    - namespaceSelector:
        matchLabels:
          name: pao-data
    ports:
    - protocol: TCP
      port: 6333  # Qdrant
    - protocol: TCP
      port: 6343  # Kuzu
  - to:
    - podSelector:
        matchLabels:
          app: kafka
    ports:
    - protocol: TCP
      port: 9092
```

### WAF Rules (Cloudflare/AWS WAF)

```yaml
waf_rules:
  # Rate limiting
  - name: "api-rate-limit"
    action: "block"
    condition: "rate(5m) > 1000 per IP"
    scope: "/v1/*"
  
  # Bot detection
  - name: "bot-detection"
    action: "challenge"
    condition: "bot_score < 0.3"
  
  # SQL injection
  - name: "sql-injection"
    action: "block"
    condition: "sql_injection_detected"
    scope: "/v1/*"
  
  # XSS
  - name: "xss-protection"
    action: "block"
    condition: "xss_detected"
    scope: "/v1/*"
  
  # Path traversal
  - name: "path-traversal"
    action: "block"
    condition: "path_traversal_detected"
  
  # Known bad IPs
  - name: "ip-reputation"
    action: "block"
    condition: "ip_in_threat_intel_feed"
  
  # API abuse
  - name: "api-abuse"
    action: "rate_limit"
    condition: "errors_5xx > 10% in 1m"
    scope: "/v1/*"
```

---

## Container Security

### Hardened Images

```dockerfile
# Dockerfile.hardened
# Build stage
FROM golang:1.22-alpine AS builder

# Install build dependencies
RUN apk add --no-cache git make protoc

# Set secure build flags
ENV CGO_ENABLED=0
ENV GOOS=linux
ENV GOARCH=amd64
ENV GOPRIVATE=github.com/pao/*

WORKDIR /build

# Copy go.mod first for caching
COPY go.mod go.sum ./
RUN go mod download

# Copy source
COPY . .

# Build with security flags
RUN go build -ldflags="-s -w -extldflags=-static" \
    -tags="netgo,osusergo" \
    -o /app/main ./cmd/conversation-engine

# Final stage - Distroless
FROM gcr.io/distroless/static-debian12:nonroot

# Copy binary
COPY --from=builder /app/main /app/main

# Non-root user (distroless provides nonroot:65532)
USER 65532:65532

# Read-only root filesystem
# No shell, no package manager, minimal attack surface

ENTRYPOINT ["/app/main"]
```

### Container Runtime Security

```yaml
# Kubernetes Security Context
securityContext:
  runAsNonRoot: true
  runAsUser: 65532
  runAsGroup: 65532
  fsGroup: 65532
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop:
    - ALL
  seccompProfile:
    type: RuntimeDefault

# Pod Security Standards (restricted)
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: pao-restricted
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  hostNetwork: false
  hostIPC: false
  hostPID: false
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
  readOnlyRootFilesystem: true
```

### Image Scanning Pipeline

```yaml
# .github/workflows/security-scan.yml
name: Security Scan

on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: '0 2 * * *'  # Daily

jobs:
  container-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build image
        run: docker build -t pao/conversation-engine:${{ github.sha }} -f Dockerfile.hardened .
      
      - name: Run Trivy
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'pao/conversation-engine:${{ github.sha }}'
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'
      
      - name: Run Grype
        uses: anchore/grype-action@v1
        with:
          image: 'pao/conversation-engine:${{ github.sha }}'
          fail-build: true
          severity-cutoff: 'high'
      
      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
      
      - name: Sign image
        if: github.ref == 'refs/heads/main'
        run: |
          cosign sign --yes pao/conversation-engine:${{ github.sha }}
      
      - name: Generate SBOM
        run: |
          syft pao/conversation-engine:${{ github.sha }} -o spdx-json > sbom.json
      
      - name: Attest SBOM
        if: github.ref == 'refs/heads/main'
        run: |
          cosign attest --predicate sbom.json --type spdxjson pao/conversation-engine:${{ github.sha }}
```

---

## Incident Response

### Security Incident Classification

| Severity | Definition | Response Time | Examples |
|----------|------------|---------------|----------|
| **SEV-1 (Critical)** | Active breach, data exfiltration, safety system compromise | 15 min | RCE, auth bypass, PII leak, safety bypass |
| **SEV-2 (High)** | Vulnerability being exploited, privilege escalation | 1 hour | SQLi, IDOR, broken access control |
| **SEV-3 (Medium)** | Vulnerability with potential impact, config issues | 4 hours | Missing headers, info disclosure, weak crypto |
| **SEV-4 (Low)** | Security hygiene, best practice violations | 1 week | Outdated deps, missing CSP, weak passwords |

### Incident Response Playbook

```markdown
## SECURITY-INCIDENT-RESPONSE

### 1. Detection & Triage (0-15 min)
- [ ] Alert received (SIEM, bug bounty, internal report)
- [ ] Assign incident commander
- [ ] Classify severity (SEV-1 to SEV-4)
- [ ] Create incident channel (#sec-incident-XXXX)
- [ ] Notify stakeholders (security@, legal@, exec@ for SEV-1)

### 2. Containment (15 min - 2 hours)
- [ ] Isolate affected systems (network policies, revoke tokens)
- [ ] Preserve evidence (logs, memory dumps, disk images)
- [ ] Block attacker IPs (WAF, security groups)
- [ ] Rotate compromised credentials
- [ ] Enable enhanced logging

### 3. Investigation (2 hours - 2 days)
- [ ] Root cause analysis
- [ ] Impact assessment (data accessed, users affected)
- [ ] Timeline reconstruction
- [ ] Identify all affected systems
- [ ] Check for persistence/lateral movement

### 4. Eradication (1-3 days)
- [ ] Patch vulnerabilities
- [ ] Remove malicious artifacts
- [ ] Rebuild compromised systems from clean images
- [ ] Verify no backdoors remain
- [ ] Update detection rules

### 5. Recovery (1-7 days)
- [ ] Restore services from clean state
- [ ] Monitor for recurrence
- [ ] Gradual traffic restoration
- [ ] Validate data integrity
- [ ] User notification (if required)

### 6. Post-Incident (Within 1 week)
- [ ] Post-mortem meeting
- [ ] Write incident report
- [ ] Action items with owners/dates
- [ ] Update runbooks
- [ ] Share learnings (blameless)
```

### Forensic Readiness

```go
// Forensic logging for critical operations
func (a *AuditLogger) LogSecurityEvent(ctx context.Context, event SecurityEvent) {
    entry := AuditEntry{
        Timestamp:    time.Now().UTC(),
        EventType:    event.Type,
        Severity:     event.Severity,
        UserID:       getUserID(ctx),
        SessionID:    getSessionID(ctx),
        IPAddress:    getClientIP(ctx),
        UserAgent:    getUserAgent(ctx),
        Resource:     event.Resource,
        Action:       event.Action,
        Result:       event.Result,
        Metadata:     event.Metadata,
        // Cryptographic integrity
        Hash:         calculateHash(event),
        PrevHash:     a.getLastHash(),
    }
    
    // Write to immutable store (append-only)
    a.store.Append(entry)
    
    // Also send to SIEM
    a.siem.Send(entry)
}

// Events to audit
type SecurityEventType string

const (
    // Authentication
    EventLoginSuccess           SecurityEventType = "auth.login.success"
    EventLoginFailure           SecurityEventType = "auth.login.failure"
    EventMFAChallenge           SecurityEventType = "auth.mfa.challenge"
    EventTokenRefresh           SecurityEventType = "auth.token.refresh"
    EventPasswordChange         SecurityEventType = "auth.password.change"
    EventAccountLockout         SecurityEventType = "auth.account.lockout"
    
    // Authorization
    EventAccessGranted          SecurityEventType = "authz.access.granted"
    EventAccessDenied           SecurityEventType = "authz.access.denied"
    EventPrivilegeEscalation    SecurityEventType = "authz.privilege.escalation"
    EventRoleChange             SecurityEventType = "authz.role.change"
    
    // Data
    EventDataAccess             SecurityEventType = "data.access"
    EventDataExport             SecurityEventType = "data.export"
    EventDataDeletion           SecurityEventType = "data.deletion"
    EventEncryptionKeyAccess    SecurityEventType = "data.encryption.key_access"
    
    // Safety
    EventCrisisDetected         SecurityEventType = "safety.crisis.detected"
    EventInterventionTriggered  SecurityEventType = "safety.intervention.triggered"
    EventSafetyOverride         SecurityEventType = "safety.override"
    
    // Admin
    EventConfigChange           SecurityEventType = "admin.config.change"
    EventUserImpersonation      SecurityEventType = "admin.impersonation"
    EventAuditLogAccess         SecurityEventType = "admin.audit.access"
)
```

---

## Compliance & Privacy

### GDPR Compliance

```go
// GDPR Article 17 - Right to Erasure
func (s *UserService) DeleteUserData(ctx context.Context, userID string) error {
    return s.db.Transaction(ctx, func(tx *sql.Tx) error {
        // 1. Anonymize messages (retain for companion continuity)
        _, err := tx.ExecContext(ctx, `
            UPDATE messages 
            SET content = '[deleted]', user_id = '00000000-0000-0000-0000-000000000000'
            WHERE user_id = $1
        `, userID)
        if err != nil {
            return err
        }
        
        // 2. Delete memories containing PII
        _, err = tx.ExecContext(ctx, `
            DELETE FROM memories 
            WHERE companion_id IN (SELECT id FROM companions WHERE user_id = $1)
            AND (content ILIKE '%email%' OR content ILIKE '%phone%' OR content ILIKE '%address%')
        `, userID)
        if err != nil {
            return err
        }
        
        // 3. Delete user record
        _, err = tx.ExecContext(ctx, `DELETE FROM users WHERE id = $1`, userID)
        if err != nil {
            return err
        }
        
        // 4. Delete auth tokens
        _, err = tx.ExecContext(ctx, `DELETE FROM refresh_tokens WHERE user_id = $1`, userID)
        
        // 5. Log for audit
        _, err = tx.ExecContext(ctx, `
            INSERT INTO gdpr_deletion_log (user_id, deleted_at, deleted_by)
            VALUES ($1, NOW(), $2)
        `, userID, getRequesterID(ctx))
        
        return err
    })
}

// GDPR Article 20 - Data Portability
func (s *UserService) ExportUserData(ctx context.Context, userID string) (*UserDataExport, error) {
    export := &UserDataExport{
        User:        s.getUser(ctx, userID),
        Companions:  s.getCompanions(ctx, userID),
        Messages:    s.getMessages(ctx, userID),
        Memories:    s.getMemories(ctx, userID),
        Relationships: s.getRelationships(ctx, userID),
        Proactives:  s.getProactives(ctx, userID),
        Settings:    s.getSettings(ctx, userID),
        ExportedAt:  time.Now(),
    }
    
    // Encrypt export
    encrypted, err := s.crypto.Encrypt(export, "user-export-"+userID)
    if err != nil {
        return nil, err
    }
    
    // Store for download (expires in 7 days)
    url, err := s.storage.StoreEncrypted(encrypted, 7*24*time.Hour)
    if err != nil {
        return nil, err
    }
    
    return &UserDataExport{DownloadURL: url}, nil
}
```

### Data Retention

```yaml
# Data retention policies
retention_policies:
  # User data
  users:
    active: "indefinite"
    deleted: "30d"  # Grace period for recovery
    anonymized: "immediate"
  
  # Conversations
  messages:
    active: "indefinite"  # Core product value
    deleted_user: "90d"   # Anonymized after user deletion
    legal_hold: "indefinite"
  
  # Memories
  memories:
    episodic: "2y"  # Auto-consolidate or delete
    semantic: "indefinite"
    procedural: "indefinite"
    flashbulb: "indefinite"
    deleted_user: "immediate"
  
  # Safety (longer retention for legal)
  safety_events:
    crisis: "7y"
    intervention: "7y"
    appeal: "7y"
    false_positive: "1y"
  
  # Analytics
  analytics_events: "13m"
  evaluation_results: "2y"
  
  # Logs
  audit_logs: "7y"
  access_logs: "1y"
  debug_logs: "30d"
```

---

## Security Testing

### SAST/DAST/IAST

```yaml
security_testing:
  sast:
    tool: "golangci-lint + gosec + semgrep"
    frequency: "every_pr"
    rules:
      - "G101: Hardcoded credentials"
      - "G104: Unchecked errors"
      - "G204: Command injection"
      - "G301: Poor file permissions"
      - "G302: Poor file permissions"
      - "G401: Weak crypto (SHA1, MD5)"
      - "G404: Insecure random"
      - "G505: TLS config"
      - "SQL injection patterns"
      - "XSS patterns"
      - "Path traversal"
  
  dast:
    tool: "OWASP ZAP"
    frequency: "weekly"
    target: "staging"
    config:
      - "Active scan with authentication"
      - "API scan (OpenAPI spec)"
      - "WebSocket testing"
  
  iast:
    tool: "Contrast Security"
    environment: "staging"
    always_on: true
  
  sca:
    tool: "Dependabot + Renovate + govulncheck"
    frequency: "daily"
    auto_pr: true
  
  container:
    tool: "Trivy + Grype"
    frequency: "on_build + weekly"
  
  secrets:
    tool: "TruffleHog + GitLeaks"
    frequency: "every_push"
```

### Penetration Testing

```yaml
pentest:
  frequency: "annual"
  scope:
    - "api.pao.app"
    - "app.pao.app"
    - "Mobile apps (iOS/Android)"
    - "Infrastructure (AWS/GCP)"
    - "Internal networks (via VPN)"
  
  methodology: "OWASP ASVS Level 2"
  
  rules_of_engagement:
    - "No DoS testing"
    - "No social engineering"
    - "No physical security"
    - "Test accounts provided"
    - "Data exfiltration simulated only"
  
  reporting:
    - "Executive summary"
    - "Technical findings with CVSS"
    - "Remediation guidance"
    - "Retest verification"
```

### Bug Bounty

```yaml
bug_bounty:
  platform: "HackerOne"
  scope:
    - "api.pao.app"
    - "app.pao.app"
    - "*.pao.app"
  
  rewards:
    critical: "$10,000 - $50,000"
    high: "$3,000 - $10,000"
    medium: "$1,000 - $3,000"
    low: "$100 - $1,000"
  
  safe_harbor: true
  response_time: "72h"
  triage_team: "security@pao.app"
```

---

## Security Training

### Required Training

| Role | Training | Frequency |
|------|----------|-----------|
| **All Engineers** | Secure Coding (OWASP Top 10) | Annual |
| **All Engineers** | Secrets Management | Annual |
| **All Engineers** | Incident Response | Annual |
| **Backend Engineers** | API Security | Annual |
| **ML Engineers** | Model Security (Poisoning, Extraction) | Annual |
| **DevOps/Platform** | Infrastructure Security | Annual |
| **Security Team** | Advanced Threat Hunting | Quarterly |
| **Managers** | Security Leadership | Annual |

### Security Champions

```yaml
security_champions:
  - team: "conversation-engine"
    champion: "alex@pao.app"
  - team: "memory-engine"
    champion: "sam@pao.app"
  - team: "voice-engine"
    champion: "jordan@pao.app"
  - team: "safety-engine"
    champion: "taylor@pao.app"  # Required
  - team: "mobile"
    champion: "casey@pao.app"
  - team: "platform"
    champion: "riley@pao.app"
  
  responsibilities:
    - "Security review for PRs"
    - "Threat modeling for new features"
    - "Vulnerability triage"
    - "Security training for team"
    - "Liaison with security team"
```

---

## Security Checklist

### For New Features

- [ ] Threat model completed (STRIDE)
- [ ] Data classification identified
- [ ] Authentication/authorization designed
- [ ] Input validation implemented
- [ ] Output encoding implemented
- [ ] Encryption for sensitive data
- [ ] Secrets not in code/config
- [ ] Security headers configured
- [ ] Logging for security events
- [ ] Rate limiting applied
- [ ] Security tests written
- [ ] Dependency scan passed
- [ ] Container scan passed
- [ ] Documentation updated

### For Releases

- [ ] All SEV-1/2 vulnerabilities fixed
- [ ] SAST/DAST scans clean
- [ ] Dependencies updated
- [ ] Container images signed
- [ ] SBOM generated
- [ ] Security regression tests pass
- [ ] Rollback plan tested
- [ ] Incident response contacts current

---

**Aligned With:** `330-security-model.md`, `300-system-architecture.md`, `340-infrastructure.md`, `350-deployment.md`, `06-legal/`
**Next Review:** 2026-01-17