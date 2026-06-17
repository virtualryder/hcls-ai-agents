# HCLS AI Agent Production Pilot
### Consulting Offering — Scope, Deliverables, and Engagement Structure

---

## Offering Summary

A twelve-to-twenty-week engagement that takes one agent from the POC into a production-ready deployment against live systems of record, with IdP integration, live Bedrock inference, at least one live connector, and a computer-system assurance (CSA) scoping and preparation package. The Pilot produces a validated, operated agent capable of being used by qualified professionals in a defined production context for a specific study, product, or jurisdiction.

The Pilot is the first engagement where the customer's regulated processes touch AI-generated content in a production setting. The SI team manages the infrastructure; the customer performs the validation. Exit from the Pilot is production go-live for the scoped use case.

---

## Scope

### In scope

**One agent in production configuration:**
- Full LangGraph workflow deployed via CloudFormation to the customer's production AWS environment
- Live Bedrock inference (Anthropic Claude model, in-account, customer's AWS account)
- Bedrock Guardrails configured for the customer's product/indication context
- Live PHI masking layer with customer-specific NER configuration

**Platform infrastructure (full stack):**
- AgentCore Gateway + Identity (or API Gateway + Lambda authorizer + Cognito + STS equivalent) with deny-by-default policy and HITL gate
- Append-only DynamoDB audit table with PITR + S3 Object Lock WORM store
- Cognito IdP federation integrated with the customer's enterprise IdP (Okta, Entra, Ping, or SAML 2.0 provider)
- KMS customer-managed encryption key
- CloudWatch observability with HITL queue depth and approval latency alarms
- CloudTrail API-level audit

**Live connector integration (one system of record):**
- Selected based on the agent: Veeva Vault RIM (Agent 01), Argus Safety (Agent 02), Medidata CTMS/eTMF (Agent 03), TrackWise (Agent 05)
- Read connector tested and validated against live system
- Write connector (if in scope for the agent) tested in a validated staging environment before production activation

**Computer-system assurance preparation:**
- Validation scoping document: intended use, risk classification (GAMP 5 category), validation approach (IQ/OQ/PQ)
- Requirements traceability matrix (RTM) mapping platform controls to 21 CFR Part 11 and GxP requirements
- Test protocol templates for OQ (based on eval harness golden cases) and PQ (based on representative customer test cases)
- Customer performs execution; SI provides support

**User acceptance testing (UAT) support:**
- Two sprint cycles of UAT with the functional stakeholder team
- Issue triage and remediation within agreed SLA
- Sign-off checklist aligned to the validation protocol

**Runbook delivery:**
- HITL queue operations runbook (see `runbooks/HITL-QUEUE-OPERATIONS.md`)
- Incident response runbook (see `runbooks/INCIDENT-RESPONSE.md`)
- Model degradation response runbook (see `runbooks/MODEL-DEGRADATION-RESPONSE.md`)

### Out of scope
- Additional agents beyond the single pilot scope
- Full CSV execution (customer responsibility)
- Penetration test execution (deliverable: scope and methodology; execution: SI security practice or customer-nominated tester)
- Change management, training materials, and adoption planning beyond the UAT support above

---

## Duration and Team

**Typical duration:** 12–20 weeks (varies with system-of-record integration complexity and customer validation timeline)

**SI team composition:**
- 1 Engagement Lead / Solution Architect
- 1 Life Sciences Domain Architect
- 1–2 AI/ML Engineers (LangGraph, Bedrock, connector development)
- 1 Security / Compliance Architect (validation scoping, Part 11 controls)
- 1 Infrastructure Engineer (CloudFormation, Cognito, KMS, observability)
- 0.5 Project Manager

**Customer time commitment:** approximately 100–150 hours across the engagement, including IdP configuration, connector access credentials, security review, UAT participation, and validation execution.

---

## Deliverables

1. **Production-deployed agent** — running live in the customer's AWS account, integrated with the enterprise IdP and at least one live system-of-record connector
2. **Operational runbooks** — HITL queue operations, incident response, model degradation response (adapted from the suite templates)
3. **Validation package** — requirements traceability matrix, test protocol templates, IQ completion evidence (installation qualification run by SI); OQ and PQ template with representative test cases
4. **Security review report** — configuration review of the deployed stack (IAM roles, KMS key policy, VPC posture, Guardrail configuration, DynamoDB audit policy)
5. **Penetration test scope document** — methodology, scope, and schedule for the pre-production penetration test (execution is a separate engagement or customer-managed)
6. **Pilot lessons learned and scale recommendation** — findings, issues resolved, and a recommendation for the next two agents in the platform rollout, with adjusted effort estimates

---

## Entry Criteria

- POC completed with accepted output quality and go/no-go approved
- AWS production account available with Bedrock access approved
- Enterprise IdP group-to-role mapping confirmed (customer IdP admin engaged)
- System-of-record API credentials and access available in a staging environment
- Customer validation team (QA/CSA) engaged and validation approach agreed
- Legal/procurement: HIPAA BAA with AWS in place (or in process)

## Exit Criteria

- Agent running in production against live systems with real users (limited rollout, scoped to agreed use case)
- Validation IQ complete; OQ and PQ protocols drafted, reviewed, and signed
- All P1 and P2 issues from UAT resolved or risk-accepted with documented rationale
- Operational runbooks accepted by the customer's IT operations team
- Production go-live approval signed by the customer's sponsor and quality/compliance lead

---

## Pricing Approach

Time-and-materials with a not-to-exceed ceiling, phased by milestone (infrastructure provisioning → IdP/connector integration → UAT → go-live). The not-to-exceed ceiling is recalibrated at the end of the connector integration phase once the actual integration complexity is known.

Infrastructure costs (AWS) are the customer's responsibility and are not included in SI fees. AWS cost modeling is provided in `offerings/COST-ROI-MODEL.md`.

---

## Go-to-Production Gate

The formal production go-live gate requires:

- IT operations acceptance of the deployed infrastructure
- Security acceptance (configuration review clean or risk-accepted)
- Quality/CSA acceptance (IQ complete; OQ and PQ protocols signed)
- Functional stakeholder acceptance (UAT sign-off)
- Runbook training completed for the HITL queue operations team

The SI does not authorize production go-live unilaterally. The customer's sponsor and quality lead hold the go-live authority.
