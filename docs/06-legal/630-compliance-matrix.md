# PAO Compliance Matrix

**Version:** 1.0
**Status:** Draft
**Owner:** PAO Legal & Compliance
**Classification:** Internal - Confidential

---

## Overview

This document maps PAO's compliance posture across applicable regulations, standards, and contractual obligations. It serves as the single source of truth for compliance status, evidence, and gaps.

> **Compliance Principle:** Compliance is a byproduct of good engineering and privacy-by-design, not a checkbox exercise.

---

## Regulatory Landscape

### Applicable Regulations by Jurisdiction

| Regulation | Jurisdiction | Applicability | Status | Evidence |
|------------|--------------|---------------|--------|----------|
| **GDPR** | EU/EEA | Controller + Processor | ✅ Compliant | DPIA, SCCs, DPO, RoPA |
| **UK GDPR** | UK | Controller + Processor | ✅ Compliant | UK Rep, DPIA, DPA |
| **CCPA/CPRA** | California, US | Business | ✅ Compliant | Privacy Policy, Do Not Sell, Rights |
| **LGPD** | Brazil | Controller + Processor | ✅ Compliant | DPO (Encarregado), LGPD Addendum |
| **PIPEDA** | Canada | Commercial Activity | ✅ Compliant | Privacy Policy, Consent |
| **Quebec Law 25** | Quebec, Canada | Enterprise | 🟡 In Progress | Privacy Officer, PIA, Consent |
| **APPI** | Japan | Business | 🟡 In Progress | Privacy Policy, Localization |
| **PIPA** | South Korea | Business | 🟡 Planned | Privacy Policy, Consent |
| **PDPA** | Singapore | Business | 🟡 Planned | Privacy Policy, DPO |
| **HIPAA** | US Healthcare | Business Associate | ✅ Available | BAA, Risk Analysis, Safeguards |
| **FERPA** | US Education | School Official | 🟡 Planned | BAA-equivalent, Consent |
| **COPPA** | US Children | Not Applicable | ⚪ N/A | Age gate 13+, no child data |
| **ePrivacy** | EU/EEA | Electronic Comms | ✅ Compliant | Cookie Consent, Confidentiality |
| **AI Act** | EU | High-Risk AI System | 🟡 Preparing | Conformity Assessment, QMS |

---

## Standards & Certifications

### Current Certifications

| Standard | Scope | Status | Auditor | Next Audit | Certificate |
|----------|-------|--------|---------|------------|-------------|
| **SOC 2 Type II** | Security, Availability, Confidentiality | ✅ Certified | AICPA Firm | Oct 2025 | [Link] |
| **ISO 27001** | ISMS (all operations) | ✅ Certified | Accredited Registrar | Jan 2026 | [Link] |
| **ISO 27701** | PIMS (Privacy extension) | 🟡 In Progress | Same as 27001 | Target Q2 2025 | - |
| **ISO 42001** | AI Management System | 🟡 Planned | TBD | Target 2026 | - |

### Target Certifications (Roadmap)

| Standard | Target | Rationale | Owner |
|----------|--------|-----------|-------|
| **HIPAA BAA** | Q1 2025 | Healthcare Enterprise | Legal/Eng |
| **FedRAMP Moderate** | 2026 | US Government | Eng/Sec |
| **ISO 27018** | Q2 2025 | Cloud Privacy | Sec/Privacy |
| **CSA STAR** | 2025 | Cloud Security | Sec |
| **SOC 3** | Q3 2025 | Public Trust | Sec/Marketing |

---

## GDPR Compliance Detail

### Lawful Basis Mapping

| Processing Activity | Lawful Basis (Art 6) | Special Category (Art 9) | DPIA Required |
|---------------------|---------------------|-------------------------|---------------|
| Account creation/auth | Contract (6.1.b) | - | No |
| Conversations (core) | Contract (6.1.b) | Health data (9.2.a - consent) | Yes ✅ |
| Memory extraction | Contract (6.1.b) | Health data (9.2.a - consent) | Yes ✅ |
| RHI calculation | Contract (6.1.b) | Health inferences (9.2.a - consent) | Yes ✅ |
| Proactive messages | Legitimate Interest (6.1.f) | - | Yes ✅ |
| Crisis detection | Vital Interests (6.1.d) | Health (9.2.c - vital interests) | Yes ✅ |
| Analytics (aggregated) | Legitimate Interest (6.1.f) | - | No |
| ML training (opt-in) | Consent (6.1.a) | Health (9.2.a - explicit consent) | Yes ✅ |
| Marketing email | Consent (6.1.a) | - | No |
| Fraud prevention | Legitimate Interest (6.1.f) | - | No |
| Legal requests | Legal Obligation (6.1.c) | As required | No |

### Data Subject Rights Implementation

| Right | Implementation | SLA | Automation |
|-------|---------------|-----|------------|
| **Access (Art 15)** | Self-serve export (JSON/PDF/CSV) + API | 30 days | ✅ Fully |
| **Rectification (Art 16)** | Profile edit, memory correction API | 30 days | 🟡 Partial |
| **Erasure (Art 17)** | Account delete + partial delete API | 30 days | ✅ Fully |
| **Restriction (Art 18)** | Processing flags, API controls | 30 days | 🟡 Partial |
| **Portability (Art 20)** | Structured export (JSON/CSV) | 30 days | ✅ Fully |
| **Objection (Art 21)** | Analytics/marketing toggles | Immediate | ✅ Fully |
| **Automated Decision (Art 22)** | Human review available, no solely automated | N/A | ✅ N/A |

### Cross-Border Transfers

| Transfer | Mechanism | Supplementary Measures | Review Date |
|----------|-----------|----------------------|-------------|
| EU → US (OpenAI, Anthropic) | SCCs 2021/914 | Encryption, pseudonymization, no gov access | Quarterly |
| EU → US (PAO personnel) | SCCs + Employee contracts | JIT access, background checks, logging | Quarterly |
| EU → APAC (Customer request) | SCCs + Customer consent | Regional data centers preferred | Per request |
| Sub-processor chain | Flow-down SCCs | Contractual + technical | Quarterly |

---

## CCPA/CPRA Compliance Detail

### Consumer Rights Implementation

| Right | Implementation | Verification | Opt-Out Signal |
|-------|---------------|--------------|----------------|
| **Know (Access)** | Self-serve download + API | Email + 2FA | - |
| **Delete** | Account deletion + partial API | Email + 2FA | - |
| **Opt-Out of Sale** | N/A (we don't sell) | - | GPC honored |
| **Opt-Out of Sharing** | Analytics toggle + advertising opt-out | Email | GPC honored |
| **Limit Sensitive PI** | Sensitive data controls in settings | Email | - |
| **Non-Discrimination** | No price/service degradation | - | - |
| **Authorized Agent** | Agent portal with signed permission | Agent verification | - |

### "Sale" & "Share" Analysis

| Activity | Sale? | Share? | Justification |
|----------|-------|--------|---------------|
| LLM API calls (OpenAI, etc.) | No | No | Processors, not third parties |
| Analytics (Amplitude) | No | Yes* | Cross-context behavioral advertising |
| Advertising pixels | No | Yes | Opt-out available |
| Sub-processors | No | No | Processors under contract |
| *Sharing for analytics | - | Yes | "Share" per CPRA, opt-out provided |

---

## HIPAA Compliance (Enterprise Healthcare)

### Business Associate Agreement (BAA)

- **Available**: Yes, for Enterprise Healthcare tier
- **Scope**: PHI in conversations, memories, voice
- **Safeguards**: All SOC 2 + HIPAA-specific

### Administrative Safeguards (45 CFR §164.308)

| Standard | Implementation |
|----------|----------------|
| **Security Officer** | CISO designated |
| **Workforce Training** | Annual HIPAA + quarterly phishing |
| **Access Management** | RBAC, JIT, quarterly review |
| **Incident Response** | 24/7, breach notification < 60 days |
| **Contingency Plan** | DR/BCP tested annually |
| **BAA with Sub-processors** | All PHI-touching vendors |

### Physical Safeguards (45 CFR §164.310)

| Standard | Implementation |
|----------|----------------|
| **Facility Access** | Cloud (AWS/GCP/Azure) - provider controlled |
| **Workstation Security** | MDM, encryption, auto-lock, remote wipe |
| **Device/Media Controls** | Encryption, disposal procedures |

### Technical Safeguards (45 CFR §164.312)

| Standard | Implementation |
|----------|----------------|
| **Access Control** | Unique IDs, emergency access, auto-logoff, encryption |
| **Audit Controls** | Immutable logs, 6-year retention, tamper-evident |
| **Integrity** | Checksums, digital signatures, validation |
| **Transmission Security** | TLS 1.3, mTLS, AES-256 at rest |

---

## AI Act Preparation (EU)

### Risk Classification

| AI System | Classification | Requirements |
|-----------|----------------|--------------|
| **Conversation Engine** | High-Risk (Annex III: Emotion recognition, biometric) | Conformity assessment, QMS, CE marking |
| **Memory Engine** | High-Risk (Profiling, automated decision-making) | Risk management, data governance, transparency |
| **Proactive Engine** | High-Risk (Behavioral manipulation potential) | Human oversight, accuracy, robustness |
| **Safety Engine** | High-Risk (Biometric categorization, health) | Post-market monitoring, incident reporting |
| **Voice Engine** | High-Risk (Biometric identification, emotion) | Data quality, documentation, registration |

### Compliance Roadmap

| Milestone | Target | Status |
|-----------|--------|--------|
| **AI Inventory** | Q1 2025 | ✅ Complete |
| **Risk Assessments** | Q1 2025 | 🟡 In Progress |
| **Data Governance** | Q2 2025 | 🟡 In Progress |
| **Technical Documentation** | Q2 2025 | 🟡 Planned |
| **QMS Implementation** | Q3 2025 | 🟡 Planned |
| **Conformity Assessment** | Q4 2025 | 🟡 Planned |
| **CE Marking** | Q1 2026 | 🟡 Planned |
| **Post-Market Monitoring** | Ongoing | 🟡 Planned |

### Key Obligations Mapping

| Obligation (AI Act) | PAO Implementation |
|---------------------|-------------------|
| **Art 9: Risk Management** | Continuous risk assessment per engine |
| **Art 10: Data Governance** | Training data documentation, bias testing |
| **Art 11: Technical Documentation** | Per-engine model cards, architecture docs |
| **Art 12: Record Keeping** | Immutable audit logs, 10-year retention |
| **Art 13: Transparency** | User-facing AI disclosure, capability limits |
| **Art 14: Human Oversight** | Evaluation engine, safety reviewers, appeals |
| **Art 15: Accuracy/Robustness** | Automated eval, red-teaming, monitoring |
| **Art 17: QMS** | ISO 42001 alignment, documented processes |
| **Art 20: Corrective Actions** | Incident response, model rollback capability |
| **Art 26: Fundamental Rights** | DPIA, equity testing, accessibility |

---

## Security Compliance Mapping

### SOC 2 Trust Services Criteria

| Criterion | Control | Evidence | Status |
|-----------|---------|----------|--------|
| **CC1.1** | Code of Conduct | Employee handbook, annual ack | ✅ |
| **CC2.1** | Security Policy | InfoSec policy, annual review | ✅ |
| **CC3.1** | Risk Assessment | Annual + continuous, documented | ✅ |
| **CC4.1** | Monitoring | Datadog, Sentry, SIEM, 24/7 | ✅ |
| **CC5.1** | Access Control | Zero-trust, RBAC, JIT, MFA | ✅ |
| **CC6.1** | Logical Access | IAM, PAM, quarterly certs | ✅ |
| **CC7.1** | System Operations | Runbooks, change mgmt, DR | ✅ |
| **CC8.1** | Change Management | PR review, CI/CD, feature flags | ✅ |
| **CC9.1** | Risk Mitigation | Vendors, BCP, insurance | ✅ |
| **A1.1** | Availability | Multi-AZ, SLA 99.9%, RTO<4hr | ✅ |
| **C1.1** | Confidentiality | Encryption, DLP, classification | ✅ |
| **PI1.1** | Privacy | DPIA, consent, rights, retention | ✅ |

### ISO 27001 Annex A Controls (Key)

| Control | Implementation | Status |
|---------|---------------|--------|
| **A.5.1** Policies | InfoSec, Privacy, Acceptable Use | ✅ |
| **A.6.1** Roles | CISO, DPO, Security Champions | ✅ |
| **A.7.1** HR Security | Background checks, training, offboarding | ✅ |
| **A.8.1** Asset Mgmt | Inventory, classification, disposal | ✅ |
| **A.9.1** Access Control | Zero-trust, RBAC, MFA, PAM | ✅ |
| **A.10.1** Crypto | TLS 1.3, AES-256, KMS, cert mgmt | ✅ |
| **A.11.1** Physical | Cloud provider (shared responsibility) | ✅ |
| **A.12.1** Operations | Backup, logging, monitoring, vuln mgmt | ✅ |
| **A.13.1** Network | VPC, mTLS, WAF, segmentation | ✅ |
| **A.14.1** SDLC | Secure coding, SAST/DAST, threat modeling | ✅ |
| **A.15.1** Supplier | Vendor risk, DPA, continuous monitoring | ✅ |
| **A.16.1** Incident | IR plan, 24/7, comms, lessons learned | ✅ |
| **A.17.1** BCP | DR tested annually, RPO<1hr, RTO<4hr | ✅ |
| **A.18.1** Compliance | Regulatory tracking, audits, legal review | ✅ |

---

## Contractual Obligations

### Customer Contracts (Enterprise)

| Obligation | Source | Frequency | Owner | Status |
|------------|--------|-----------|-------|--------|
| **SLA 99.9%** | MSA | Monthly | Eng/SRE | ✅ |
| **SOC 2 Report** | MSA | Annual | Sec | ✅ |
| **Pen Test Summary** | MSA | Annual | Sec | ✅ |
| **Sub-processor Notice** | DPA | 30 days prior | Legal | ✅ |
| **Breach Notification** | DPA | 24 hours | Sec/Legal | ✅ |
| **Data Export** | DPA | On termination | Eng | ✅ |
| **Deletion Certificate** | DPA | Post-termination | Eng/Legal | ✅ |
| **Audit Rights** | DPA | Annual | Sec/Legal | ✅ |
| **DPIA Sharing** | DPA | On request | Privacy | ✅ |

### Vendor Contracts

| Vendor | Contract Type | Key Terms | Renewal | Status |
|--------|---------------|-----------|---------|--------|
| **OpenAI** | Enterprise API | Zero-retention, DPA, SCCs | Annual | ✅ |
| **Anthropic** | Enterprise API | Zero-retention, DPA, SCCs | Annual | ✅ |
| **AWS** | EDP | Security, compliance, credits | Annual | ✅ |
| **GCP** | Enterprise | Security, compliance, credits | Annual | ✅ |
| **Stripe** | Standard | PCI DSS, DPA, financial | Monthly | ✅ |
| **Segment** | Enterprise | DPA, SCCs, data residency | Annual | ✅ |

---

## Gap Analysis & Remediation

### Current Gaps (As of Jan 2025)

| Gap | Regulation/Standard | Risk | Owner | Target | Status |
|-----|---------------------|------|-------|--------|--------|
| **ISO 27701 Certification** | GDPR/ISO 27001 | Medium | Privacy/Sec | Q2 2025 | 🟡 In Progress |
| **Quebec Law 25 Full Compliance** | Quebec Law 25 | Low | Legal/Privacy | Q3 2025 | 🟡 Planned |
| **AI Act Conformity** | EU AI Act | High | AI/Legal/Eng | Q1 2026 | 🟡 Planned |
| **FedRAMP Moderate** | US Gov | Medium | Eng/Sec | 2026 | 🟡 Planned |
| **HIPAA BAA Execution** | HIPAA | Low | Legal/Sales | Q1 2025 | 🟡 In Progress |
| **Automated DSAR API** | GDPR/CCPA | Low | Eng | Q2 2025 | 🟡 Planned |
| **Real-time Consent Sync** | GDPR/ePrivacy | Low | Eng/Privacy | Q2 2025 | 🟡 Planned |

### Remediation Tracking

```yaml
remediation_process:
  identification: "Quarterly compliance review + continuous monitoring"
  prioritization: "Risk-based (Regulatory > Contractual > Best Practice)"
  ownership: "Single owner per gap (RACI)"
  tracking: "Jira Epic + Compliance Dashboard"
  verification: "Evidence collection + internal audit"
  closure: "Compliance sign-off + evidence archived"
```

---

## Compliance Monitoring

### Continuous Monitoring

| Control | Tool | Frequency | Alert Threshold |
|---------|------|-----------|-----------------|
| **Encryption Coverage** | CSPM (Wiz/Prisma) | Continuous | < 100% |
| **Access Reviews** | IAM (Okta/Entra) | Quarterly | Overdue > 7 days |
| **Vulnerability SLA** | Scanner (Trivy/Qualys) | Continuous | Critical > 24hr |
| **Log Completeness** | SIEM (Datadog) | Daily | Gap > 1 hour |
| **Backup Success** | Backup (Veeam/Restic) | Daily | Any failure |
| **Consent Validity** | CMP (OneTrust) | Daily | Expired > 30 days |
| **Sub-processor Changes** | Vendor Registry | Continuous | Unauthorized change |
| **Data Residency** | CSPM + Custom | Continuous | Cross-region violation |

### Periodic Reviews

| Review | Frequency | Participants | Output |
|--------|-----------|--------------|--------|
| **Compliance Dashboard** | Monthly | CISO, DPO, Legal, Eng Leads | Metrics, gaps, actions |
| **Regulatory Horizon Scan** | Quarterly | Legal, Privacy, Product | New obligations, impact |
| **Internal Audit** | Semi-annual | Internal Audit + Domain Experts | Findings, remediation |
| **External Audit** | Annual | SOC 2, ISO 27001 Auditors | Reports, certifications |
| **Board Compliance Update** | Quarterly | Board, Audit Committee | Risk posture, investments |

---

## Evidence Repository

### Structure

```
📁 Compliance_Evidence_[Year]/
├── 📁 SOC2/
│   ├── Report_[Date].pdf
│   ├── Bridge_Letter_[Date].pdf
│   └── Management_Assertion.pdf
├── 📁 ISO27001/
│   ├── Certificate.pdf
│   ├── Statement_of_Applicability.pdf
│   └── Surveillance_Audit_[Date].pdf
├── 📁 GDPR/
│   ├── DPIA_Conversation_Engine.pdf
│   ├── DPIA_Memory_Engine.pdf
│   ├── DPIA_Proactive_Engine.pdf
│   ├── RoPA_[Version].xlsx
│   ├── SCCs_OpenAI.pdf
│   ├── SCCs_Anthropic.pdf
│   └── DPO_Appointment.pdf
├── 📁 HIPAA/
│   ├── BAA_Template.pdf
│   ├── Risk_Analysis_[Date].pdf
│   └── Training_Records_[Quarter].xlsx
├── 📁 AI_Act/
│   ├── AI_Inventory_[Version].xlsx
│   ├── Risk_Assessment_[Engine].pdf
│   ├── Technical_Documentation_[Engine].pdf
│   └── QMS_Manual.pdf
├── 📁 Contracts/
│   ├── Customer_DPA_Template.pdf
│   ├── Vendor_DPAs/
│   └── Sub_processor_List_[Quarter].xlsx
├── 📁 Audits/
│   ├── Internal_[Date].pdf
│   ├── Pen_Test_Summary_[Date].pdf
│   └── Vendor_Assessments_[Quarter].pdf
└── 📁 Training/
    ├── Security_Training_[Quarter].xlsx
    ├── Privacy_Training_[Quarter].xlsx
    └── Phishing_Results_[Quarter].xlsx
```

---

## Compliance Metrics (KPIs)

| Metric | Target | Current | Trend |
|--------|--------|---------|-------|
| **SOC 2 Findings (Critical/High)** | 0 | 0 | → |
| **ISO 27001 Non-conformities** | 0 | 0 | → |
| **GDPR DSAR Response Time** | < 30 days | 12 days avg | ↓ |
| **Breach Notification Time** | < 24 hours | N/A (no breaches) | → |
| **Vendor Risk Assessments Current** | 100% | 95% | ↑ |
| **Employee Training Completion** | 100% | 98% | ↑ |
| **Encryption Coverage** | 100% | 100% | → |
| **Access Review Completion** | 100% quarterly | 100% | → |
| **Vulnerability SLA Met** | 100% (Critical 24hr) | 98% | ↑ |
| **Backup Test Success** | 100% monthly | 100% | → |
| **Compliance Gap Closure** | < 90 days avg | 67 days | ↓ |
| **Regulatory Change Response** | < 30 days | 14 days avg | → |

---

## Escalation & Reporting

### Compliance Escalation

| Level | Trigger | Response | Owner |
|-------|---------|----------|-------|
| **Level 1** | Single metric miss, minor gap | 5 business days | Domain Owner |
| **Level 2** | Repeated misses, moderate risk | 48 hours | CISO/DPO |
| **Level 3** | Regulatory inquiry, breach, major gap | 4 hours | CEO + Legal |
| **Level 4** | Enforcement action, existential risk | Immediate | CEO + Board |

### Reporting Channels

- **Internal**: #compliance-alerts (Slack), Compliance Dashboard (Grafana)
- **Executive**: Monthly Compliance Review (30 min)
- **Board**: Quarterly Audit Committee, Annual Full Board
- **Regulatory**: As required (breach notifications, annual reports)
- **Customer**: On request (Enterprise), Annual Transparency Report

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Classification** | Confidential - Internal Only |
| **Owner** | General Counsel / CISO / DPO |
| **Review Cycle** | Quarterly (or regulatory change) |
| **Next Review** | April 15, 2025 |
| **Approved By** | CEO, CISO, DPO, General Counsel |
| **Distribution** | Leadership, Security, Legal, Privacy, Engineering Leads |

---

**Aligned With:** `600-privacy-policy.md`, `610-terms-of-service.md`, `620-data-processing-agreement.md`, `330-security-model.md`, `440-security.md`
**Next Review:** April 15, 2025