# NIST SP 800-53 Rev. 5 Control Matrix — HCLS AI Agent Suite

> Maps the suite's controls to NIST 800-53 families a CISO / auditor expects. **Reference-implemented**
> = present in this repo's control plane/IaC. **Customer-owned** = the deployer provides it (IdP, CSV,
> pen test, monitoring). HIPAA Security Rule and 21 CFR Part 11 map onto these same controls. This is a
> control *crosswalk*, not an ATO; production substitutes managed AWS services (see
> `PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`).

| Family | Control(s) | How the suite satisfies it | Where | Status |
|---|---|---|---|---|
| **AC — Access Control** | AC-2, AC-3, AC-6 | Deny-by-default authorization; least-privilege intersection (agent grant ∩ user entitlement); consequential commits withheld from agents | `mcp_gateway/policy.py` | Reference |
| | AC-4 | Information-flow enforced at the gateway; no SoR/model access except through it | `mcp_gateway/gateway.py` | Reference |
| **IA — Identification & Auth** | IA-2, IA-5, IA-8 | RS256/JWKS JWT verification; federated IdP; no trusted client roles | `auth.py` | Reference + Customer (IdP) |
| **AU — Audit & Accountability** | AU-2, AU-3, AU-9, AU-10 | Append-only audit of every attempt with full lineage; WORM (S3 Object Lock); non-repudiation via bound reviewer identity | `mcp_gateway/audit*.py`, `data.yaml` | Reference |
| **SC — System & Comms Protection** | SC-7, SC-8, SC-12, SC-13, SC-28 | Per-customer VPC + edge (CloudFront/WAF); TLS 1.3; KMS CMK per data class; in-VPC Bedrock (no egress) | `network.yaml`, `edge.yaml`, `security.yaml` | Reference |
| | SC-23 | Short-lived, per-call scoped tokens; no standing service accounts | `mcp_gateway/tokens.py` | Reference |
| **SI — System & Info Integrity** | SI-4, SI-7, SI-10 | Grounding verification (input/output integrity); PHI masking; Bedrock Guardrails; red-team monitoring | `governance/grounding.py`, `phi.py` | Reference |
| **CM — Configuration Mgmt** | CM-2, CM-3, CM-6 | IaC-defined config; prompt hash-pinning + CI drift gate (model-risk change control) | `infra/`, `governance/prompt_registry.py` | Reference |
| **IR — Incident Response** | IR-4, IR-5, IR-6, IR-8 | IR runbook + audit evidence + notification flow | `INCIDENT-RESPONSE-AND-KEY-MANAGEMENT.md`, `runbooks/INCIDENT-RESPONSE.md` | Reference (process) |
| **CP — Contingency Planning** | CP-9, CP-10 | WORM retention survives stack deletion; DR runbook | `data.yaml`, `runbooks/DR-RUNBOOK.md` | Reference + Customer |
| **RA — Risk Assessment** | RA-3, RA-5 | Threat model; dependency pinning; (pen test customer-owned) | `THREAT-MODEL.md` | Reference + Customer (pen test) |
| **SA — System & Services Acq** | SA-11, SA-15 | 503 automated tests incl. governance/red-team; CI gates every change | `make test`, `.github/workflows/ci.yml` | Reference |
| **PL/PM — Planning / Program** | PL-8, PM-* | Documented architecture, shared-responsibility, production-readiness | `SUITE-ARCHITECTURE.md`, `SHARED-RESPONSIBILITY-MATRIX.md` | Reference |
| **PT/SI (privacy) — PHI** | HIPAA §164.312(a)(c)(e) | Access control, audit, integrity, transmission security; PHI masked before model/audit | `phi.py`, `policy.py`, `data.yaml` | Reference + Customer (BAA) |

## Customer-owned controls (must be completed for production)
IdP entitlement source of truth (AC/IA) · CSV/CSA validation evidence (SA-11 / Part 11) · independent
penetration test (CA-8/RA-5) · continuous monitoring + alarms (SI-4/AU-6) · KMS key custody & rotation
(SC-12) · retention schedules & DR (CP) · BAA and data-residency (privacy). Tracked in
`PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`.
