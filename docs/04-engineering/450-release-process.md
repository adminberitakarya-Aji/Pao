# PAO Release Process

**Version:** 1.0
**Status:** Draft
**Owner:** PAO Release Engineering Team

---

## Overview

This document defines the release process, versioning strategy, and deployment procedures for PAO.

> **Release Principle:** Automated, safe, and predictable releases. Progressive delivery with instant rollback.

---

## Versioning Strategy

### Semantic Versioning (SemVer)

```
MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]

Examples:
- 1.0.0           # Major release
- 1.1.0           # Minor release (backward compatible features)
- 1.1.1           # Patch release (bug fixes)
- 1.2.0-rc.1      # Release candidate
- 1.2.0-beta.3    # Beta release
- 1.2.0+build.123 # Build metadata
```

### Version Assignment

| Trigger | Version Bump | Example |
|---------|--------------|---------|
| Breaking API changes | MAJOR | 1.2.0 → 2.0.0 |
| New features (backward compatible) | MINOR | 1.2.0 → 1.3.0 |
| Bug fixes | PATCH | 1.2.0 → 1.2.1 |
| Security patches | PATCH + hotfix branch | 1.2.0 → 1.2.1 |
| Pre-releases | -rc.N, -beta.N | 1.3.0-rc.1 |

### Release Branches

```
main (continuous delivery)
  │
  ├── release/v1.x (stabilization for v1.x)
  │     │
  │     ├── hotfix/v1.2.1 (critical fixes)
  │     │
  │     └── v1.2.1 (tag)
  │
  ├── release/v2.x
  │
  └── v2.0.0 (tag)
```

---

## Release Types

### 1. Continuous Delivery (Main Branch)

Every merge to `main` produces a release candidate.

```yaml
# Trigger: Push to main
# Output: Docker images tagged with SHA
# Deploy: Automatic to staging
# Promote: Manual to production via canary
```

### 2. Minor/Major Releases (Release Branch)

```yaml
# Trigger: Create release/vX.Y branch from main
# Process:
#   1. Branch cut from main
#   2. Stabilization period (1 week)
#   3. Only bug fixes allowed
#   4. Version bump in branch
#   5. Tag release (vX.Y.0)
#   6. Merge back to main
```

### 3. Hotfix Releases

```yaml
# Trigger: Critical production issue
# Process:
#   1. Create hotfix/vX.Y.Z from release/vX.Y
#   2. Apply minimal fix
#   3. Fast-track testing
#   4. Tag release (vX.Y.Z)
#   5. Cherry-pick to main and release branch
```

---

## Release Pipeline

### CI Pipeline (Every Commit)

```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [main, release/**]
  pull_request:
    branches: [main, release/**]

jobs:
  # 1. Code Quality
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - checkout
      - setup-go
      - run: make lint          # golangci-lint, buf lint
      - run: make test-unit     # Unit tests
      - run: make test-component # Component tests
      - run: make security-scan  # SAST, secrets, deps
  
  # 2. Container Build
  build-images:
    needs: lint-and-test
    strategy:
      matrix:
        service: [all-services]
    steps:
      - checkout
      - run: make build-image SERVICE=${{matrix.service}}
      - run: make scan-image IMAGE=ghcr.io/pao/${{matrix.service}}:${{github.sha}}
      - run: make sign-image IMAGE=ghcr.io/pao/${{matrix.service}}:${{github.sha}}
      - run: make generate-sbom IMAGE=ghcr.io/pao/${{matrix.service}}:${{github.sha}}
  
  # 3. Integration Tests
  integration-tests:
    needs: build-images
    steps:
      - deploy to staging (ArgoCD)
      - run: make test-integration
      - run: make test-contract
  
  # 4. Staging Deploy
  deploy-staging:
    needs: integration-tests
    environment: staging
    steps:
      - run: argocd app sync pao-staging --prune
      - run: make smoke-test ENV=staging
      - run: make canary-analysis DURATION=30m  # If canary enabled
```

### CD Pipeline (Release Tags)

```yaml
# .github/workflows/release.yml
name: Release Pipeline

on:
  push:
    tags:
      - 'v*'  # SemVer tags

jobs:
  # 1. Create Release
  create-release:
    runs-on: ubuntu-latest
    steps:
      - checkout
      - run: make generate-changelog TAG=${{github.ref_name}}
      - run: gh release create ${{github.ref_name}} --notes-file CHANGELOG.md
  
  # 2. Build Release Images
  build-release-images:
    needs: create-release
    strategy:
      matrix:
        service: [all-services]
    steps:
      - checkout
      - run: make build-release-image SERVICE=${{matrix.service}} VERSION=${{github.ref_name}}
      - run: make scan-image IMAGE=ghcr.io/pao/${{matrix.service}}:${{github.ref_name}}
      - run: make sign-image IMAGE=ghcr.io/pao/${{matrix.service}}:${{github.ref_name}}
      - run: make attest-sbom IMAGE=ghcr.io/pao/${{matrix.service}}:${{github.ref_name}}
  
  # 3. Production Canary
  deploy-canary:
    needs: build-release-images
    environment: production
    steps:
      - run: argocd app set pao-production --parameter image.tag=${{github.ref_name}}
      - run: argocd app sync pao-production --selector canary=true
      - run: make canary-analysis DURATION=60m
      - run: make canary-promote  # Manual approval gate
  
  # 4. Full Production Rollout
  deploy-production:
    needs: deploy-canary
    environment: production
    steps:
      - run: argocd app sync pao-production --prune
      - run: make post-deploy-check
      - run: make update-status-page
  
  # 5. Post-Release
  post-release:
    needs: deploy-production
    steps:
      - run: make notify-release CHANNEL=#releases VERSION=${{github.ref_name}}
      - run: make update-docs VERSION=${{github.ref_name}}
      - run: make cleanup-old-images RETENTION=30d
```

---

## Pre-Release Checklist

### Code Complete

- [ ] All features merged to main
- [ ] No open critical/high vulnerabilities
- [ ] All tests passing (unit, component, integration, contract)
- [ ] Performance benchmarks within thresholds
- [ ] Security review completed
- [ ] Documentation updated

### Release Branch Cut

- [ ] Create `release/vX.Y` branch from main
- [ ] Update version in `version.go` and `Chart.yaml` files
- [ ] Update `CHANGELOG.md` with release notes
- [ ] Freeze features (only bug fixes allowed)
- [ ] Run full test suite on release branch

### Stabilization Period (1 week)

- [ ] Daily test runs on release branch
- [ ] Staging deployment validated
- [ ] Load testing completed
- [ ] Chaos engineering experiments passed
- [ ] Security scan on release images
- [ ] All SEV-1/2 bugs fixed
- [ ] Release notes finalized

### Release Approval

- [ ] Engineering lead approval
- [ ] Product lead approval
- [ ] Security lead approval (for major releases)
- [ ] Legal/compliance approval (if data changes)
- [ ] Create and push tag `vX.Y.0`

---

## Release Artifacts

### Docker Images

```bash
# Tagging strategy
ghcr.io/pao/conversation-engine:v1.2.0        # Release tag
ghcr.io/pao/conversation-engine:v1.2.0-abc123 # SHA tag (CI)
ghcr.io/pao/conversation-engine:latest        # Latest stable (updated on release)
ghcr.io/pao/conversation-engine:main-abc123   # Main branch (CI)
```

### Helm Charts

```bash
# Chart version = App version
pao/conversation-engine-1.2.0.tgz

# Published to OCI registry
oci://ghcr.io/pao/charts/conversation-engine:1.2.0
```

### SBOM (Software Bill of Materials)

```bash
# Format: SPDX-JSON
pao-conversation-engine-v1.2.0-sbom.spdx.json

# Includes:
# - All direct/transitive dependencies
# - Licenses
# - Vulnerabilities (if known)
# - Build provenance (SLSA)
```

### Release Notes

```markdown
# PAO v1.2.0 - "Memory Lane"

## 🎉 Highlights
- New episodic memory consolidation engine
- Proactive v2 with milestone triggers
- Voice timbre verification

## ✨ New Features
- **Memory Engine**: Nightly consolidation job converts episodic→semantic memories
- **Proactive Engine**: Milestone triggers (anniversaries, streaks, achievements)
- **Voice Engine**: Timbre verification for voice calls (anti-spoofing)

## 🐛 Bug Fixes
- Fixed memory recall timeout under high load (#1234)
- Fixed proactive message deduplication (#1235)
- Fixed WebRTC ICE restart handling (#1236)

## 🔒 Security
- Updated Go to 1.22.1 (CVE-2024-XXXX)
- Rotated JWT signing keys
- Hardened container images (distroless)

## ⚠️ Breaking Changes
- Memory API v2: `recall` endpoint now requires `type` parameter
- Proactive config: `triggers` field renamed to `trigger_categories`

## 📦 Upgrade Guide
See [UPGRADE-v1.2.0.md](UPGRADE-v1.2.0.md)

## 📊 Metrics
- 247 commits, 18 contributors
- Test coverage: 84%
- Build time: 12min
- Deploy time: 8min (canary) + 5min (full)
```

---

## Rollback Procedures

### Automated Rollback Triggers

```yaml
# ArgoCD automated rollback
argocd:
  automated_rollback:
    enabled: true
    conditions:
      - metric: "error_rate"
        threshold: "> 5% for 5m"
      - metric: "latency_p99"
        threshold: "> 3x baseline for 10m"
      - metric: "safety_recall"
        threshold: "< 99%"
    max_rollbacks: 3
    cooldown: "30m"
```

### Manual Rollback

```bash
# 1. Identify previous stable revision
argocd app history pao-production

# 2. Rollback to specific revision
argocd app rollback pao-production 42

# 3. Or rollback to previous tag
argocd app set pao-production --parameter image.tag=v1.1.5
argocd app sync pao-production --prune

# 4. Verify
kubectl get pods -n pao-production -l app=conversation-engine
curl -f https://api.pao.app/health/ready
```

### Database Rollback (If Migration Applied)

```bash
# 1. Check migration status
kubectl exec -it postgresql-0 -n pao-data -- psql -U pao -c "
  SELECT version, name, applied_at FROM schema_migrations ORDER BY applied_at DESC LIMIT 5;
"

# 2. Run down migration (if reversible)
kubectl exec -it postgresql-0 -n pao-data -- psql -U pao -c "
  -- Run down migration SQL from migration file
  BEGIN;
  ALTER TABLE proactive_messages DROP COLUMN user_feedback;
  DROP INDEX IF EXISTS idx_proactive_feedback;
  DELETE FROM schema_migrations WHERE version = 'V1.2.0';
  COMMIT;
"

# 3. Verify application health
# 4. Note: Only if migration is truly reversible
```

---

## Release Communication

### Internal

| Channel | Audience | Timing |
|---------|----------|--------|
| `#releases` | All engineering | At release |
| `#releases-announce` | All company | At release |
| Email | Stakeholders | Day of release |
| Release notes PR | Engineering | Before release |

### External

| Channel | Audience | Timing |
|---------|----------|--------|
| GitHub Releases | Developers, users | At release |
| Status page | Users | If user-facing changes |
| Blog post | Public | Major releases only |
| In-app notification | Users | Major features |
| Discord/Community | Community | Major releases |

---

## Release Metrics & KPIs

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Release Frequency** | 2-4 weeks (minor), Daily (patches) | Time between releases |
| **Lead Time** | < 1 day | Commit to production |
| **Change Failure Rate** | < 5% | Failed releases / total |
| **MTTR** | < 15 min | Time to rollback/restore |
| **Rollback Rate** | < 10% | Rollbacks / releases |
| **Canary Promotion Rate** | > 90% | Successful promotions |
| **Release Duration** | < 2 hours | Tag to full production |

---

## Emergency Releases

### Security Hotfix

```yaml
# Bypass normal process for critical security fixes
process:
  1. Create hotfix branch from release/vX.Y or main
  2. Apply minimal fix
  3. Fast-track review (1 approval from security + 1 from engineering)
  4. Run critical tests only (unit + security + smoke)
  5. Build and deploy directly to production (skip canary if SEV-1)
  6. Tag release (vX.Y.Z)
  7. Post-incident review within 48 hours
```

### Criteria for Emergency Release

- Active exploitation (SEV-1)
- Data breach in progress
- Safety system compromise
- Regulatory compliance violation
- Complete service outage

---

## Release Tools

### CLI Tools

```bash
# Release CLI (internal)
pao-release create --version 1.2.0 --notes CHANGELOG.md
pao-release promote --from canary --to production
pao-release rollback --revision 42
pao-release status --service conversation-engine

# ArgoCD
argocd app sync pao-production --prune
argocd app rollback pao-production 42
argocd app history pao-production

# GitHub CLI
gh release create v1.2.0 --notes-file CHANGELOG.md
gh release view v1.2.0
```

### Automation

```python
# scripts/release_automation.py
class ReleaseAutomation:
    def __init__(self):
        self.github = GitHubClient()
        self.argocd = ArgoCDClient()
        self.slack = SlackClient()
    
    def create_release(self, version: str):
        # 1. Validate version format
        # 2. Check all checks pass on main
        # 3. Create release branch
        # 4. Update versions
        # 5. Generate changelog
        # 6. Create PR for release branch
        # 7. On merge: tag and trigger release workflow
        pass
    
    def promote_canary(self, service: str):
        # 1. Check canary metrics
        # 2. If healthy: promote to 100%
        # 3. If unhealthy: auto-rollback
        pass
    
    def emergency_hotfix(self, version: str, fix_branch: str):
        # 1. Build hotfix image
        # 2. Deploy to production directly
        # 3. Notify security team
        # 4. Create tracking issue
        pass
```

---

## Release Calendar

### Regular Schedule

```
Week 1: Feature development (main branch)
Week 2: Feature development (main branch)
Week 3: Release branch cut (release/vX.Y), stabilization starts
Week 4: Stabilization, testing, release (vX.Y.0)

Patch releases: As needed (typically weekly)
```

### Freeze Periods

```yaml
deployment_freezes:
  - name: "Holiday Freeze"
    start: "12-20"
    end: "01-05"
    reason: "Reduced staffing"
    exceptions: ["security-hotfix", "safety-hotfix"]
  
  - name: "Black Friday"
    start: "11-24"
    end: "11-28"
    reason: "High traffic"
    exceptions: ["security-hotfix"]
  
  - name: "Quarterly Board Week"
    schedule: "First week of Mar, Jun, Sep, Dec"
    reason: "Demo preparation"
    exceptions: ["security-hotfix", "safety-hotfix"]
```

---

## Disaster Recovery Release

### DR Region Activation

```yaml
# If primary region fails
dr_release:
  trigger: "Automated (Cloudflare health check) or Manual"
  process:
    1. DNS failover to DR region (Cloudflare)
    2. Scale up DR deployments (HPA)
    3. Promote read replicas to primary
    4. Restore from latest snapshots (RPO < 24h)
    5. Verify critical paths
    6. Notify users via status page
  runbook: "PLAYBOOK-DR-001"
```

---

## Release Retrospective

### Post-Release Review (Every Release)

```markdown
## Release Retrospective - v1.2.0

### What Went Well
- Canary analysis caught memory leak before full rollout
- Automated rollback worked perfectly
- Team communication was clear

### What Could Be Better
- Changelog generation took 2 hours (manual)
- Load test environment not representative
- 3 flaky tests caused CI delays

### Action Items
- [ ] Automate changelog generation (Owner: Release Eng, Due: Next release)
- [ ] Provision dedicated load test env (Owner: Platform, Due: 2 weeks)
- [ ] Fix flaky tests (Owner: QE, Due: 1 week)

### Metrics
- Lead time: 18 hours (target: < 24h) ✅
- Change failure rate: 0% (target: < 5%) ✅
- MTTR: 8 min (target: < 15 min) ✅
- Rollback rate: 0% (target: < 10%) ✅
```

---

**Aligned With:** `350-deployment.md`, `400-development-guide.md`, `420-testing-strategy.md`, `430-observability.md`
**Next Review:** 2026-01-17