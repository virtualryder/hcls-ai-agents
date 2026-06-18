# Statement of Work — HCLS AI Agent Suite
## [POC / Pilot / Assessment] Engagement
### Fill-in-the-blank shell — complete bracketed fields before execution

---

**STATEMENT OF WORK NO.:** `[SOW-YYYY-NNN]`
**EFFECTIVE DATE:** `[Month DD, YYYY]`
**MASTER SERVICES AGREEMENT:** This SOW is governed by and incorporated into the Master Services Agreement dated `[MSA Date]` between `[SI Legal Entity Name]` ("Service Provider") and `[Customer Legal Entity Name]` ("Customer").

---

## 1. Engagement Overview

**Engagement type:** `[Assessment / POC / Pilot]` *(select one; delete others)*

**Scope summary:** Service Provider will deliver the HCLS AI Agent Suite `[Assessment / POC / Pilot]` engagement as described herein, covering `[Agent Name(s) — e.g., "Agent 02: Pharmacovigilance ICSR Intake"]` on the Customer's AWS account infrastructure. All deliverables are defined in Section 4.

**Primary engagement objective:**
> *[One to two sentences describing the business outcome. Example: "Demonstrate that Agent 02 can process ICSR narratives from Argus Safety intake to draft E2B submission with 21 CFR Part 11-compliant audit trail, completing the end-to-end workflow in a governed demo environment within the POC term."]*

---

## 2. Engagement Term

| Milestone | Target Date |
|---|---|
| Engagement start (kickoff) | `[Month DD, YYYY]` |
| Discovery / requirements complete | `[Month DD, YYYY]` |
| Environment ready (AWS pre-flight complete) | `[Month DD, YYYY]` |
| Demo / user acceptance test | `[Month DD, YYYY]` |
| Final deliverables submitted | `[Month DD, YYYY]` |
| Engagement end | `[Month DD, YYYY]` |

**Total engagement duration:** `[X]` weeks.

**Extension:** Either party may request a one-time extension of up to `[14 / 30]` calendar days by written notice no later than 5 business days before the scheduled end date. Extensions are subject to resource availability and mutual written agreement.

---

## 3. Scope of Services

### 3.1 In Scope

*(Delete rows not applicable to this engagement type)*

**Assessment engagements:**
- [ ] AI readiness workshop (`[X]` hours; remote or on-site)
- [ ] Data and integration landscape review for selected use cases
- [ ] Compliance posture assessment (21 CFR Part 11, HIPAA, GxP alignment)
- [ ] Prioritized agent roadmap (up to `[X]` use cases scored)
- [ ] Business case / ROI estimate for the top-priority use case
- [ ] Final readout presentation and written Assessment Report

**POC engagements:**
- [ ] AWS environment setup and pre-flight verification (per `docs/AWS-ACCOUNT-PREREQUISITES.md`)
- [ ] Deployment of `[Agent Name]` in demo mode (`EXTRACT_MODE=demo`)
- [ ] Integration of fixture connectors for `[System Name(s) — e.g., Argus Safety, Veeva Vault RIM]`
- [ ] End-to-end workflow demonstration with test data (no live PHI)
- [ ] HITL gate demonstration with `[Customer Role]` as approver
- [ ] Audit trail review — append-only log, PHI masking, and QLDB/DynamoDB evidence
- [ ] Security and compliance architecture walkthrough (for CISO / QA audience)
- [ ] AWS Well-Architected Review session (joint with AWS SA)
- [ ] Go/no-go assessment report (criteria defined in Section 6)
- [ ] Knowledge transfer session (`[X]` hours) for Customer cloud/platform team

**Pilot engagements:**
- [ ] All POC deliverables, plus:
- [ ] Live connector integration for `[System Name]` (production or UAT environment)
- [ ] Amazon Cognito federation with Customer IdP (`[Okta / Azure AD / Ping / other]`)
- [ ] Live Bedrock inference (not demo mode)
- [ ] Bedrock Guardrails configuration and validation
- [ ] Computer System Assurance (CSA) scoping document
- [ ] IQ / OQ / PQ test plan and execution (Customer validation team executes; Service Provider provides documentation)
- [ ] Runbook customization for Customer's operational procedures
- [ ] Production go-live support for `[X]` days post-deployment

### 3.2 Out of Scope

The following items are explicitly excluded from this engagement unless added by a written Change Order:

- Validation / qualification of any Customer-owned regulated system (CSV/GxP validation is Customer's responsibility)
- Integration with systems not listed in Section 3.1
- Training of Customer end users beyond the knowledge transfer session defined above
- Any regulatory submission, filing, or interaction with FDA, EMA, or other regulatory bodies on behalf of Customer
- Customization of agent logic beyond what is required to demonstrate the use case defined in Section 3.1
- Infrastructure management or monitoring after the engagement end date (see `offerings/MANAGED-SERVICE-OFFERING.md` for ongoing operations)
- Procurement, licensing, or administration of third-party software (Veeva, Medidata, Argus Safety, etc.)

---

## 4. Deliverables

| # | Deliverable | Format | Due Date | Acceptance criteria |
|---|---|---|---|---|
| D1 | Kickoff agenda and environment checklist | Document | `[+3 business days from start]` | Customer confirms receipt |
| D2 | Architecture diagram (deployed topology) | Diagram + written description | `[+2 weeks from start]` | Customer cloud architect reviews and acknowledges |
| D3 | `[Assessment Report / POC Demo / Pilot Go-Live]` | `[Written report / Live demo + recording / Production deployment]` | `[Date]` | Acceptance criteria per Section 6 |
| D4 | Audit trail evidence package | PDF export of DynamoDB/QLDB audit records from demo run | `[Date]` | Customer QA/compliance lead reviews and acknowledges |
| D5 | Go/no-go report *(POC only)* | Written report | `[Date]` | Customer receives; no approval required |
| D6 | Knowledge transfer recording | Video recording of knowledge transfer session | `[Date]` | Customer confirms receipt |
| D7 | IQ/OQ/PQ test plan *(Pilot only)* | Document | `[Date]` | Customer validation lead reviews |

---

## 5. Customer Responsibilities

Customer agrees to provide the following, on the dates specified, as a prerequisite for Service Provider to complete its obligations. Delays in Customer responsibilities may extend the engagement timeline at no cost to Service Provider.

| Responsibility | Owner (Customer role) | Required by |
|---|---|---|
| AWS account with prerequisites completed (per `docs/AWS-ACCOUNT-PREREQUISITES.md`) | Cloud Platform / IT | `[+5 business days from start]` |
| Bedrock model access approved in target region | Cloud Platform / IT | `[+5 business days from start]` |
| Cognito User Pool created with custom attributes | Cloud Platform / IT | `[+1 week from start]` |
| Named project sponsor with authority to approve go/no-go | `[VP/Director title]` | Kickoff |
| Named technical point of contact (≥50% dedicated) | Cloud Architect / IT | Kickoff |
| Named domain subject matter expert for `[PV / Regulatory / Clinical Ops / etc.]` (≥25% dedicated) | `[SME title]` | Discovery workshop |
| Access to `[System Name]` UAT/sandbox environment *(Pilot only)* | `[System Admin]` | `[+2 weeks from start]` |
| API credentials for `[System Name]` *(Pilot only)* | `[System Admin]` | `[+2 weeks from start]` |
| Review and approval of deliverables within `[5]` business days of receipt | Project Sponsor | Ongoing |

---

## 6. Go/No-Go Criteria (POC only)

The POC is considered successful ("Go") if all of the following criteria are met by the POC end date. Customer and Service Provider agree to these criteria at kickoff; changes require a written Change Order.

| # | Criterion | How measured | Pass threshold |
|---|---|---|---|
| G1 | End-to-end workflow completes without error in demo mode | Run `EXTRACT_MODE=demo pytest` — all tests pass | 100% pass rate |
| G2 | HITL gate fires and captures qualified reviewer approval | Manual demonstration with named Customer reviewer | Reviewer confirms approval recorded in audit trail |
| G3 | Audit trail captures all tool calls with required fields | Audit log review: session_id, agent_id, tool, decision, user_sub, timestamp | All fields present for ≥95% of records |
| G4 | PHI masking verified — no identifiers in audit log | Automated test: `pytest governance/redteam/` — PHI exfiltration tests pass | 100% pass rate |
| G5 | Customer technical lead can describe the deployment architecture | Knowledge transfer session delivered and acknowledged | Customer lead provides written confirmation |
| G6 | `[Customer-specific criterion — e.g., "ICSR narrative draft reviewed by PV Medical Reviewer and rated acceptable for format"]` | `[Measurement method]` | `[Threshold]` |

---

## 7. Fees and Payment

### 7.1 Fixed Fee (select if applicable)

| Item | Amount |
|---|---|
| `[Assessment / POC / Pilot]` fixed engagement fee | `$[Amount]` |
| **Total** | `$[Amount]` |

**Payment schedule:**
- `[50%]` upon SOW execution: `$[Amount]`
- `[50%]` upon delivery of final deliverable (D`[X]`): `$[Amount]`

### 7.2 Time and Materials (select if applicable)

| Role | Rate | Estimated hours | Estimated fee |
|---|---|---|---|
| Engagement Manager | `$[Rate]`/hr | `[X]` hrs | `$[Amount]` |
| Solutions Architect | `$[Rate]`/hr | `[X]` hrs | `$[Amount]` |
| AI/ML Engineer | `$[Rate]`/hr | `[X]` hrs | `$[Amount]` |
| Compliance Specialist | `$[Rate]`/hr | `[X]` hrs | `$[Amount]` |
| **Not-to-exceed total** | | | `$[Amount]` |

### 7.3 AWS Service Costs

AWS service consumption (Bedrock inference, DynamoDB, Step Functions, etc.) is billed directly by AWS to Customer's AWS account and is **not included in the fees above**. Estimated AWS consumption during the engagement: `$[X,000]–$[X,000]` (see `offerings/TCO-MODEL.md` for basis of estimate).

*If Customer is utilizing MAP or PoA credits toward AWS consumption, Service Provider will assist with the credit application process at no additional charge.*

### 7.4 Expenses

Travel and out-of-pocket expenses (if applicable) are billed at cost with receipts, not to exceed `$[Amount]` without prior written approval.

---

## 8. Intellectual Property

**Pre-existing IP:** Each party retains ownership of its pre-existing IP. The HCLS AI Agent Suite codebase is Service Provider's pre-existing IP licensed to Customer under Apache 2.0 (see `LICENSE`).

**Work product:** Deliverables produced specifically for this engagement (architecture diagrams, configuration files, customizations) are `[owned by Customer / jointly owned / licensed to Customer]` as agreed in the MSA.

**Customer data:** Customer data, including any test data or PHI, remains Customer's property and is not used by Service Provider for any purpose other than the engagement.

---

## 9. Confidentiality

Both parties are bound by the confidentiality terms of the MSA. In addition, Service Provider acknowledges that Customer data accessed during the engagement may be subject to HIPAA and agrees to comply with the AWS Business Associate Agreement and any BAA between Customer and Service Provider.

---

## 10. Limitation of Liability

This engagement is a technology accelerator delivery — not a validated, certified, or FDA-cleared product. Customer is responsible for any validation, qualification, or regulatory submission actions taken based on deliverables. Service Provider's aggregate liability under this SOW shall not exceed the total fees paid hereunder, as specified in the MSA.

---

## 11. Change Order Process

Changes to scope, timeline, or fees require a written Change Order executed by both parties' authorized signatories before work begins. Service Provider will provide a Change Order estimate within 5 business days of a written change request.

---

## 12. Signatures

By signing below, the parties agree to the terms of this Statement of Work.

**SERVICE PROVIDER**

Signature: _____________________________ Date: ___________

Name: _________________________________

Title: __________________________________

Organization: __________________________

**CUSTOMER**

Signature: _____________________________ Date: ___________

Name: _________________________________

Title: __________________________________

Organization: __________________________

---

*Related: `offerings/POC-OFFERING.md`, `offerings/PILOT-OFFERING.md`, `offerings/ASSESSMENT-OFFERING.md`, `offerings/TCO-MODEL.md`, `docs/AWS-ACCOUNT-PREREQUISITES.md`*
