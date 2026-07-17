# ADR-005: Security Architecture & Zero Trust

**Status:** Accepted
**Date:** 2025-01-15
**Deciders:** CTO, CISO, VP Engineering, Security Lead
**Consulted:** All Engineering Leads, Legal, Privacy, Compliance

---

## Context

PAO handles highly sensitive user data: intimate conversations, voice recordings, emotional states, memories, and inferred psychological profiles. Security is not a feature—it's the foundation of user trust.

### Threat Model (STRIDE)

| Threat | Likelihood | Impact | Mitigation Priority |
|--------|------------|--------|---------------------|
| **Spoofing** (Identity theft) | High | Critical | P0 |
| **Tampering** (Data integrity) | Medium | Critical | P0 |
| **Repudiation** (Audit gaps) | Low | High | P1 |
| **Information Disclosure** (PII leak) | High | Critical | P0 |
| **Denial of Service** | Medium | High | P1 |
| **Elevation of Privilege** | Medium | Critical | P0 |

### Regulatory Requirements
- **GDPR**: Art 32 (Security of processing), Art 33-34 (Breach notification)
- **SOC 2**: CC6.1-CC6.8 (Logical/Physical access)
- **ISO 27001**: A.9 (Access control), A.10 (Cryptography), A.12 (Operations)
- **HIPAA**: 164.308-312 (Administrative/Physical/Technical safeguards)
- **AI Act**: High-risk AI system requirements

---

## Decision

**Implement Zero Trust Architecture with Defense in Depth across all layers.**

### Zero Trust Principles

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ZERO TRUST ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │
│  │   Identity   │    │   Device     │    │   Network    │         │
│  │   (AuthZ/AuthN)│   │   (Health)   │    │  (Micro-seg) │         │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘         │
│         │                   │                   │                 │
│         └───────────────────┼───────────────────┘                 │
│                             ▼                                     │
│              ┌──────────────────────────────┐                    │
│              │      Policy Decision Point   │                    │
│              │  (OPA + SPIRE + Certificates)│                    │
│              └──────────────┬───────────────┘                    │
│                             │                                     │
│         ┌───────────────────┼───────────────────┐                │
│         ▼                   ▼                   ▼                │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │  Data       │    │  Application│    │ Infrastructure│       │
│  │  (Encrypt,  │    │  (WAF, RASP,│    │  (mTLS,     │         │
│  │   Tokenize, │    │   CSP,      │    │   SBOM,      │         │
│  │   DLP)      │    │   Supply    │    │   Hardening) │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              Visibility & Analytics (SIEM/SOAR)             │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 1. Identity & Access (Control Plane)

#### Authentication
```yaml
Primary: OIDC/OAuth 2.1 with PKCE
Providers:
  - PAO Identity (first-party)
  - Google, Apple, Microsoft (social)
  - Enterprise: SAML 2.0, OIDC (Okta, Entra ID, Ping)
  - Passkeys (WebAuthn Level 2) - preferred for consumers

Tokens:
  - Access: JWT (RS256), 15 min, JWKS rotation
  - Refresh: Opaque, rotating, 30 days, revocable
  - Device-bound: Hardware-backed where available

MFA:
  - Required for: Admin, Support, Billing, Safety roles
  - Methods: TOTP, Passkey, Push (Duo/Authenticator)
  - Adaptive: Risk-based challenge (impossible travel, new device)
```

#### Authorization (Fine-Grained)
```yaml
Model: Google Zanzibar-inspired (Relation Tuples)
Engine: Open Policy Agent (OPA) + SpiceDB

Tuples:
  user:alice  -> viewer -> companion:c123
  user:bob    -> editor -> companion:c123
  team:support -> viewer -> user:* (with justification)

Policies (Rego):
  package pao.authz
  
  allow(user, action, resource) {
    # Companion owner has full access
    data.tuples[user, "owner", resource]
    action in ["read", "write", "delete", "export"]
  }
  
  allow(user, "read", resource) {
    # Support with active ticket
    data.tuples[user, "support_viewer", resource]
    data.active_tickets[user, resource.user_id]
  }

Enforcement:
  - Sidecar (Envoy) for network-level
  - Middleware for application-level
  - Row-level security (PostgreSQL RLS) for data-level
```

#### Machine Identity (SPIFFE/SPIRE)
```yaml
Workload Identity:
  - Every service gets SPIFFE ID: spiffe://pao.app/ns/prod/sa/memory-engine
  - X.509 SVIDs (short-lived, auto-rotated)
  - JWT SVIDs for external calls
  
mTLS:
  - All service-to-service: mandatory
  - Istio ambient mode (no sidecar overhead)
  - Certificate rotation: 24h (X.509), 1h (JWT)
```

### 2. Device Trust

```yaml
Consumer Devices:
  - Attestation: Apple DeviceCheck, Android Play Integrity
  - Risk signals: Root/jailbreak, emulator, VPN, proxy
  - Action: Block high-risk, challenge medium-risk

Corporate Devices (Enterprise):
  - MDM enrollment required (Intune, Jamf, Kandji)
  - Certificate-based auth (machine + user)
  - Compliance checks: Disk encryption, OS version, EDR

Device Registration:
  - Trust score computed per device
  - Binding: User + Device + Credential
  - Revocation: Immediate on risk change
```

### 3. Network Security (Micro-Segmentation)

```yaml
Service Mesh: Istio Ambient (ztunnel + waypoint proxies)

Segmentation:
  ┌─────────────────────────────────────────────────────────────┐
  │                     NAMESPACES                              │
  ├──────────────┬──────────────┬──────────────┬──────────────┤
  │  user-facing │   ai-core    │  data-layer  │  platform    │
  │  (gateway,   │  (inference, │  (postgres,  │  (istio,     │
  │   web, api)  │   memory,    │   qdrant,    │   monitoring,│
  │              │   voice)     │   clickhouse)│   logging)   │
  └──────────────┴──────────────┴──────────────┴──────────────┘
          │             │              │             │
          └─────────────┴──────────────┴─────────────┘
                            │
                   ┌────────▼────────┐
                   │  Authorization  │
                   │    Policies     │
                   └─────────────────┘

Policies (AuthorizationPolicy):
  - user-facing → ai-core: ALLOW (valid JWT, scope: inference)
  - ai-core → data-layer: ALLOW (mTLS, workload identity)
  - data-layer → *: DENY (egress only to S3, model registry)
  - platform → *: ALLOW (observability, control plane)
```

### 4. Application Security

```yaml
Secure SDLC:
  - Threat modeling: Every feature (STRIDE)
  - SAST: Semgrep (CI), CodeQL (weekly)
  - DAST: OWASP ZAP (staging, weekly)
  - SCA: Dependabot + OSV scanner (every PR)
  - Container: Trivy (critical=block, high=warn)
  - Secrets: TruffleHog (git history), GitLeaks (pre-commit)

Runtime Protection:
  - WAF: ModSecurity (OWASP CRS 4.0) at edge
  - RASP: Datadog ASM / custom eBPF probes
  - CSP: Strict (nonce-based, no unsafe-inline)
  - HSTS: Preload, 1 year
  - COOP/COEP: Cross-origin isolation
  - Permissions-Policy: Minimal features

Supply Chain:
  - SLSA Level 3 (provenance, reproducibility)
  - Sigstore cosign (image signing)
  - SBOM: SPDX (syft) for every release
  - Dependency pinning: Renovate (auto-merge patch)
```

### 5. Data Protection

```yaml
Encryption at Rest:
  - PostgreSQL: TDE (AWS KMS / GCP CMEK), column-level (pgcrypto) for PII
  - Qdrant: Volume encryption (LUKS) + payload encryption
  - ClickHouse: Disk encryption (AES-256)
  - Redis: TLS + Redis Enterprise encryption
  - Backups: AES-256-GCM, separate key hierarchy

Encryption in Transit:
  - External: TLS 1.3 only (TLS 1.2 disabled)
  - Internal: mTLS (SPIRE), no plaintext
  - Database: TLS 1.3 with certificate verification
  - Message Queue: TLS + SASL

Key Management:
  - Hierarchy: Root (HSM) → Service Keys → Data Keys
  - Rotation: 90 days (service), 1 year (root)
  - HSM: AWS CloudHSM / GCP Cloud HSM (FIPS 140-2 L3)
  - Envelope encryption for large objects

Tokenization:
  - PII fields: Tokenized via Vault (format-preserving)
  - SSN, credit card, government ID → tokens
  - Original stored in Vault (HSM-backed)
  - Detokenization: Audit logged, rate limited

Data Minimization:
  - Collect only what's needed (Privacy by Design)
  - Auto-delete: Conversations (configurable, default 2yrs)
  - Pseudonymization: Analytics use hashed IDs
  - Synthetic data: For ML training (opt-in only)
```

### 6. Secrets Management

```yaml
Platform: HashiCorp Vault (HA, 3 clusters)

Secrets Types:
  - Static: Database passwords, API keys (rotated 90 days)
  - Dynamic: Database creds (TTL 1h), Cloud creds (TTL 4h)
  - PKI: Certificate issuance (TTL 24h)
  - K/V v2: Application config (versioned, audit)

Access:
  - Kubernetes: Vault Agent Injector (annotated pods)
  - CI/CD: OIDC auth (GitHub Actions → Vault role)
  - Apps: AppRole (wrapped secret ID, CIDR bound)
  - Humans: LDAP/OIDC + MFA (UI/CLI)

Rotation:
  - Automated: Dynamic secrets, certs
  - Scheduled: Static secrets (90 days, with overlap)
  - Emergency: One-click revocation + reissue
```

---

## Security Operations

### Monitoring & Detection
```yaml
SIEM: Datadog Security + Custom Rules
SOAR: Cortex XSOAR (playbooks)

Key Detections:
  - Impossible travel (auth)
  - Credential stuffing (failed login patterns)
  - Data exfiltration (egress volume, unusual queries)
  - Privilege escalation (role changes, sudo)
  - Container escape (syscall anomalies)
  - Model extraction (inference API abuse)

Response:
  - SEV-1: Auto-contain (revoke session, isolate pod)
  - SEV-2: Page on-call, 15min acknowledgement
  - SEV-3: Ticket, 4hr response
```

### Incident Response
```yaml
Plan: NIST 800-61 aligned
Phases:
  1. Preparation: Runbooks, war rooms, comms templates
  2. Detection: Alerting, enrichment, triage
  3. Containment: Short-term (isolate), Long-term (patch)
  4. Eradication: Root cause, remove artifacts
  5. Recovery: Restore, verify, monitor
  6. Lessons Learned: Postmortem (blameless), action items

Breach Notification:
  - GDPR: 72 hours to DPA
  - CCPA: Without unreasonable delay
  - Customers: As required by contract/law
  - Regulators: Per jurisdiction
```

### Compliance Automation
```yaml
Continuous Compliance:
  - Drift detection: AWS Config / GCP Policy Controller
  - Evidence collection: Automated (daily)
  - Control mapping: OSCAL (NIST 800-53, ISO 27001)
  - Audit readiness: Always-on

Attestations:
  - SOC 2 Type II: Annual (Q4)
  - ISO 27001: Surveillance (annual), Recert (3yr)
  - HIPAA: BAA execution, Risk Analysis (annual)
  - AI Act: Conformity Assessment (pre-market)
```

---

## Consequences

### Positive
- **Defense in Depth**: Multiple layers, no single point of failure
- **Zero Trust**: No implicit trust, continuous verification
- **Compliance Ready**: Built for SOC2, ISO27001, GDPR, HIPAA, AI Act
- **Scalable**: Patterns work from 10 to 10,000 engineers
- **Observable**: Full visibility into trust decisions

### Negative
- **Complexity**: Many moving parts (SPIRE, OPA, Vault, Istio)
- **Latency**: mTLS, policy checks add ~2-5ms per hop
- **Operational Burden**: Certificate rotation, policy authoring
- **Learning Curve**: Teams need security engineering skills
- **Cost**: HSM, Vault, Istio, tooling licenses

### Mitigations
- **Platform Team**: Owns security infrastructure, provides paved roads
- **Defaults Secure**: Secure by default, opt-out requires approval
- **Developer Experience**: CLI tools, IDE plugins, golden paths
- **Automation**: Certificate rotation, policy testing, compliance evidence
- **Training**: Security champions program, regular workshops

---

## Implementation Roadmap

### Phase 1: Foundation (Months 1-3)
- [ ] SPIRE deployment (control plane)
- [ ] Vault cluster (3 regions, HA)
- [ ] OPA/SpiceDB for authorization
- [ ] mTLS everywhere (Istio ambient)
- [ ] Basic WAF + CSP

### Phase 2: Identity & Data (Months 3-6)
- [ ] OIDC provider (PAO Identity)
- [ ] Passkey support (WebAuthn)
  - Enterprise SSO (SAML/OIDC)
  - Device trust (DeviceCheck/Play Integrity)
  - Column-level encryption (PII)
  - Tokenization (Vault transform)

### Phase 3: Advanced (Months 6-12)
- [ ] RASP deployment
- [ ] SLSA Level 3 supply chain
- [ ] Automated compliance evidence
- [ ] AI-specific: Model extraction detection
- [ ] Red team exercises (quarterly)

---

## Related Decisions

- ADR-001: Modular Monolith (security boundaries)
- ADR-002: API Protocol (mTLS, auth)
- ADR-003: Event-Driven (message encryption)
- ADR-004: Database per Module (encryption per DB)
- ADR-006: Service Mesh (Istio config)

---

## References

- [NIST Zero Trust Architecture (SP 800-207)](https://csrc.nist.gov/publications/detail/sp/800-207/final)
- [Google BeyondCorp](https://beyondcorp.google.com/)
- [SPIFFE/SPIRE](https://spiffe.io/)
- [Open Policy Agent](https://www.openpolicyagent.org/)
- [HashiCorp Vault](https://www.vaultproject.io/)
- [Istio Ambient Mesh](https://istio.io/latest/blog/2022/ambient-mesh/)
- [SLSA Framework](https://slsa.dev/)

---

**Approval:**
- CTO: _________________ Date: __________
- CISO: _________________ Date: __________
- VP Engineering: _________________ Date: __________
- Security Lead: _________________ Date: __________