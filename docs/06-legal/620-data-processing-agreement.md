# PAO Data Processing Agreement (DPA)

**Version:** 1.0
**Effective Date:** January 15, 2025
**Status:** Template for Enterprise Customers

---

## 1. Parties & Scope

### 1.1 Parties
- **Controller**: Customer ("Customer," "you") - the entity using PAO Enterprise
- **Processor**: PAO Technologies, Inc. ("PAO," "we," "Processor")
- **Contact**: privacy@pao.app | dpo@pao.app

### 1.2 Scope
This DPA governs processing of **Customer Personal Data** by PAO on behalf of Customer under the Enterprise Agreement ("Principal Agreement").

### 1.3 Definitions
| Term | Definition |
|------|------------|
| **Customer Personal Data** | Personal data submitted by/for Customer users via Enterprise service |
| **Processing** | Any operation on Customer Personal Data (Art 4 GDPR) |
| **Sub-processor** | Third party engaged by PAO to process Customer Personal Data |
| **Data Subject** | Customer's users, employees, contractors |
| **Supervisory Authority** | GDPR: Lead DPC (Ireland); UK: ICO |

---

## 2. Processing Details

### 2.1 Categories of Data Subjects
- Customer employees, contractors, affiliates
- Customer's end users (if B2C service)
- Customer administrators, support contacts

### 2.2 Categories of Personal Data
| Category | Examples |
|----------|----------|
| **Identity** | Name, email, employee ID, avatar |
| **Authentication** | Hashed passwords, MFA secrets, session tokens |
| **Usage** | Conversations, memories, RHI scores, feature usage |
| **Voice** | Voice recordings, embeddings, timbre profiles |
| **Administrative** | Roles, permissions, audit logs, support tickets |
| **Billing** | Invoice contacts, payment method tokens (Stripe) |

### 2.3 Purposes of Processing
1. **Service Delivery**: Conversations, memory, proactive, voice
2. **Administration**: User management, SSO, provisioning, billing
3. **Security**: Auth, fraud detection, audit, incident response
4. **Support**: Ticket handling, troubleshooting, communications
5. **Analytics**: Aggregated usage (Customer-controlled opt-out)
6. **Compliance**: Legal holds, regulatory requests, exports

### 2.4 Duration
Term of Principal Agreement + 90 days post-termination (for recovery/export).

---

## 3. Processor Obligations

### 3.1 General Obligations
- Process only on documented instructions (this DPA + Principal Agreement)
- Ensure personnel bound by confidentiality
- Implement Article 32 security measures
- Respect Data Subject rights (assist Customer)
- Notify Customer of legally-required disclosures (unless prohibited)
- Delete/return data per Section 7
- Make available information for audits (Section 8)

### 3.2 Security Measures (Minimum)
| Measure | Implementation |
|---------|----------------|
| **Encryption in Transit** | TLS 1.3, mTLS between services |
| **Encryption at Rest** | AES-256 (cloud KMS), column-level for PII |
| **Access Control** | Zero-trust, RBAC, JIT access, quarterly reviews |
| **Network Security** | VPC isolation, WAF, DDoS, network policies |
| **Container Security** | Distroless, non-root, read-only, seccomp, signed images |
| **Secrets Management** | HashiCorp Vault, dynamic creds, automatic rotation |
| **Vulnerability Management** | Weekly scans, 24hr critical patching, annual pen test |
| **Incident Response** | 24/7 on-call, 15min SEV-1, forensic readiness |
| **Logging & Monitoring** | Centralized, tamper-proof, 13-month retention |
| **Business Continuity** | Multi-AZ, RPO < 1hr, RTO < 4hr, annual DR test |

### 3.3 Certifications & Attestations
- SOC 2 Type II (annual)
- ISO 27001 (certified)
- GDPR/UK GDPR compliance program
- HIPAA BAA available (Healthcare Enterprise)
- FedRAMP Moderate (GovCloud Enterprise)

---

## 4. Sub-processors

### 4.1 General Authorization
Customer grants general written authorization for Sub-processors listed in **Annex A**.

### 4.2 Sub-processor Obligations
- Written agreement with equivalent data protection obligations
- PAO liable for Sub-processor acts/omissions
- Flow-down of all DPA terms

### 4.3 Notification of Changes
- **New Sub-processors**: 30 days written notice before engagement
- **Objection Right**: Customer may object within 14 days (material change)
- **Remediation**: If objection not resolved, Customer may terminate (pro-rated refund)

### 4.4 Current Sub-processors (Annex A)
| Sub-processor | Purpose | Location | Safeguards |
|---------------|---------|----------|------------|
| AWS / GCP / Azure | Cloud infrastructure | Per Customer region | SOC2, ISO27001, DPA |
| OpenAI / Anthropic / Google | LLM inference | US, EU | Zero-retention, DPA, SCCs |
| Deepgram / ElevenLabs | Voice AI | US, EU | DPA, no training |
| Qdrant / Kuzu / PostgreSQL | Databases | Self-hosted (Customer VPC) | Encryption, RBAC |
| Stripe | Payments | Global | PCI DSS L1, DPA |
| Segment / Amplitude | Analytics | US, EU | DPA, IP anonymization |
| Sentry / Datadog | Observability | US, EU | DPA, PII scrubbing |
| HashiCorp Vault | Secrets | Self-hosted | Encryption, audit |

---

## 5. International Data Transfers

### 5.1 Transfer Mechanism
| Transfer | Mechanism |
|----------|-----------|
| **EU/UK → US Processors** | SCCs (2021/914) + Supplementary Measures |
| **EU/UK → PAO (US entity)** | SCCs + Employee confidentiality + Access controls |
| **Customer Region → Other** | Regional data centers (data stays in region) |

### 5.2 Supplementary Measures (Technical)
- Encryption in transit (TLS 1.3) and at rest (AES-256)
- Customer-held encryption keys (Enterprise Key Management)
- Pseudonymization before cross-region processing
- No Processor access to unencrypted Customer Personal Data

### 5.3 Supplementary Measures (Organizational)
- US: No FISA 702/EO 12333 bulk collection (warrant canary)
- Employee access: Background checks, NDAs, least privilege
- Legal challenge: Notify Customer, challenge requests, transparency

### 5.4 Regional Data Residency
- **Standard**: Customer chooses primary region (US-East, EU-West, APAC-Singapore)
- **Strict**: All processing/storage in chosen region (no cross-region)
- **Dedicated**: Single-tenant deployment in Customer VPC (GovCloud/Enterprise)

---

## 6. Data Subject Rights Assistance

### 6.1 Processor Assistance
PAO shall assist Customer with Data Subject requests:
- **Access**: Self-serve export + API for automated requests
- **Rectification**: Admin tools + API for corrections
- **Erasure**: Admin delete + API, 30-day grace, 90-day hard delete
- **Portability**: Structured export (JSON, CSV, PDF)
- **Restriction**: Processing flags, API controls
- **Objection**: Analytics/profiling opt-out flags

### 6.2 Response Times
- **Standard**: PAO assists within 10 business days
- **Urgent**: 3 business days (safety, legal)
- **API**: Real-time for automated workflows

### 6.3 Costs
- Included in Enterprise subscription (reasonable volume)
- Excessive requests: Mutual agreement on costs

---

## 7. Personal Data Breach

### 7.1 Notification
- **To Customer**: Without undue delay, max 24 hours after discovery
- **Content**: Nature, categories, approximate numbers, consequences, measures taken
- **Channel**: Encrypted email to Customer DPO + security contact + in-app alert

### 7.2 Cooperation
- Joint investigation, regulatory notification support
- Customer controls regulatory notification timing/content
- PAO provides all necessary information

### 7.3 Costs
- PAO bears breach response costs (forensics, notification, credit monitoring)
- Customer bears regulatory fines (unless PAO gross negligence)

---

## 8. Audits & Inspections

### 8.1 Audit Rights
- **Annual**: Customer may audit (or appoint auditor) once per year
- **Trigger**: Material breach, security incident, regulatory request
- **Scope**: Processing activities, security controls, Sub-processors

### 8.2 Audit Process
- **Notice**: 30 days written notice
- **Standard**: SOC 2 Type II report satisfies (shared under NDA)
- **On-site**: Only if SOC 2 insufficient, max 5 business days
- **Costs**: Customer bears (unless material non-compliance found)

### 8.3 Certifications as Alternative
Current certifications provided annually:
- SOC 2 Type II (AICPA)
- ISO 27001 (accredited registrar)
- Penetration test summary (redacted)
- Sub-processor compliance attestations

---

## 9. Data Return & Deletion

### 9.1 Termination Obligations
Upon Principal Agreement termination:
1. **Export Window**: 90 days for Customer to export all data
2. **Self-Serve**: Admin portal + API exports (full fidelity)
3. **Assisted**: PAO engineering support for bulk export (included)
4. **Deletion**: Secure deletion within 30 days post-export window
5. **Confirmation**: Written deletion certificate

### 9.2 Deletion Standards
- **Production**: Cryptographic erasure (key destruction) + overwrites
- **Backups**: Expire per rotation (max 90 days), no early access
- **Logs**: PII scrubbed immediately, full logs retained 13 months
- **Sub-processors**: Flow-down deletion requirements, confirmations collected

### 9.3 Legal Hold Exception
- Preservation if legal hold notified
- Customer notified, scope minimized
- Resume deletion when hold lifted

---

## 10. Liability & Indemnification

### 10.1 Processor Liability
- Per Principal Agreement liability caps
- DPA-specific: Direct damages for DPA breaches
- Sub-processor acts: PAO fully liable

### 10.2 Indemnification
PAO indemnifies Customer for:
- Third-party claims from PAO's DPA breach
- Regulatory fines from PAO's gross negligence/willful misconduct
- Sub-processor failures (PAO pursues Sub-processor)

Customer indemnifies PAO for:
- Third-party claims from Customer's instructions
- Customer's use violating laws/rights
- Customer Data Subject claims (unless PAO breach)

---

## 11. General Provisions

### 11.1 Term & Termination
- **Term**: Matches Principal Agreement
- **Survival**: Sections 5, 7, 9, 10, 11 survive termination
- **Auto-terminate**: If Principal Agreement terminates

### 11.2 Amendments
- Written, signed by both parties
- Regulatory changes: PAO may update with 30 days notice
- Customer may object (Section 4.3 process)

### 11.3 Governing Law & Jurisdiction
- **US**: Delaware, San Francisco County
- **EU**: Ireland, Dublin
- **UK**: England, London
- **Other**: Delaware, San Francisco County

### 11.4 Notices
- **Email**: Legal contacts on file
- **Portal**: In-app notifications
- **Effective**: Upon receipt (email) or 3 business days (mail)

### 11.5 Entire Agreement
This DPA + Annexes + Principal Agreement = entire understanding on data processing.

---

## Annex A: Approved Sub-processors

*Attached as separate document, updated quarterly.*

## Annex B: Technical & Organizational Measures

*Detailed in PAO Security Whitepaper (pao.app/security-whitepaper)*

## Annex C: Data Processing Description

*Refer to Section 2 above + Principal Agreement Exhibit A*

---

## Execution

**PAO Technologies, Inc.**
- Signature: _________________________
- Name: _________________________
- Title: _________________________
- Date: _________________________

**Customer: [Customer Legal Entity Name]**
- Signature: _________________________
- Name: _________________________
- Title: _________________________
- Date: _________________________

---

**Document Control:**
- Version: 1.0
- Classification: Confidential
- Review Cycle: Annually (or regulatory change)
- Next Review: January 15, 2026