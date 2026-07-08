# HCLS Agentic AI Suite — Auditor & GRC Assurance Packet

**Cover sheet and curated index for a life-sciences quality/compliance auditor, CISO review, or
GRC / TPRM team.** This packet does not duplicate content — it points to the artifacts already
in this repository, organized under standard assurance headings. Links are relative to the
repository root.

---

## 1. Purpose & scope

Ten healthcare & life-sciences agents (regulatory writing, pharmacovigilance, clinical-trial
ops, quality/CAPA, manufacturing batch review, etc.) on the shared Aegis control plane, built on
AWS. This packet lets a reviewer answer a GxP / 21 CFR Part 11 / HIPAA / vendor-risk
questionnaire directly from repository artifacts.

> **Honesty line.** This suite is a **reference accelerator, not a validated GxP system, not an
> ATO'd product, and not a compliance certification.** It ships control *design* and reference
> IaC. Computer-system validation (CSV), Part 11 qualification, control operation on live
> regulated data, and accountability for compliance are **customer-owned**. See the maturity
> matrix in [`../README.md`](../README.md) for Implemented vs. Configurable (customer-owned).

---

## 2. Architecture & data-flow diagrams

- HCLS GxP data flow — [`../docs/diagrams/hcls-gxp-data-flow.svg`](../docs/diagrams/hcls-gxp-data-flow.svg) ([PNG](../docs/diagrams/hcls-gxp-data-flow.png))
- MCP gateway authorization flow (shared control plane, deny paths) — [`../docs/diagrams/mcp-gateway-auth-flow.svg`](../docs/diagrams/mcp-gateway-auth-flow.svg) ([PNG](../docs/diagrams/mcp-gateway-auth-flow.png))
- Suite architecture (edge-to-data narrative) — [`../docs/SUITE-ARCHITECTURE.md`](../docs/SUITE-ARCHITECTURE.md)
- AWS Well-Architected review — [`../docs/WELL-ARCHITECTED-REVIEW.md`](../docs/WELL-ARCHITECTED-REVIEW.md)

## 3. Threat model & abuse cases

- STRIDE threat model, abuse cases, threat → control → file — [`../docs/THREAT-MODEL.md`](../docs/THREAT-MODEL.md)

## 4. Control mappings (NIST 800-53, NIST AI RMF; GxP / 21 CFR Part 11 / HIPAA)

- NIST 800-53 control matrix — [`../docs/NIST-800-53-CONTROL-MATRIX.md`](../docs/NIST-800-53-CONTROL-MATRIX.md)
- OWASP LLM Top-10 + MITRE ATLAS mapping — [`../docs/OWASP-LLM-ATLAS-MAPPING.md`](../docs/OWASP-LLM-ATLAS-MAPPING.md)
- Per-agent regulatory-compliance notes (GxP / Part 11 / GVP context) — each `../NN-*-agent/docs/regulatory-compliance.md`
- Governance controls & compliance checker (code) — [`../governance/`](../governance/), [`../08-medical-affairs-msl-agent/tools/compliance_checker.py`](../08-medical-affairs-msl-agent/tools/compliance_checker.py)

## 5. Identity, authorization & human-in-the-loop controls

- Deny-by-default MCP gateway; the legally consequential commit is **withheld from every agent** and only a bound human reviewer may commit (enforced by test) — [`../docs/WHY-THE-MCP-LAYER.md`](../docs/WHY-THE-MCP-LAYER.md), [`../SECURITY.md`](../SECURITY.md) §3
- IdP federation runbook — [`../docs/IDP-FEDERATION-RUNBOOK.md`](../docs/IDP-FEDERATION-RUNBOOK.md)
- Red-team scenarios & commit-withholding tests — [`../governance/redteam/`](../governance/redteam/), [`../governance/tests/`](../governance/tests/)

## 6. Data protection (encryption, masking, WORM audit, residency)

- Encryption / key management (KMS CMK), append-only hash-chained audit, WORM — [`../docs/INCIDENT-RESPONSE-AND-KEY-MANAGEMENT.md`](../docs/INCIDENT-RESPONSE-AND-KEY-MANAGEMENT.md)
- PHI/regulated-data masking at every boundary — see [`../docs/SUITE-ARCHITECTURE.md`](../docs/SUITE-ARCHITECTURE.md) and threat model
- Residency: regulated data stays in the customer's AWS account/region; residency guarantees are **customer-owned** (region pinning, PrivateLink endpoint policy).

## 7. Deployment evidence

- Clean-account acceptance run — [`../evidence/CLEAN-ACCOUNT-ACCEPTANCE.md`](../evidence/CLEAN-ACCOUNT-ACCEPTANCE.md)
- Golden-path deploy notes / deployment handbook — [`../docs/GOLDEN-PATH-DEPLOY-NOTES.md`](../docs/GOLDEN-PATH-DEPLOY-NOTES.md), [`../docs/DEPLOYMENT-HANDBOOK.md`](../docs/DEPLOYMENT-HANDBOOK.md)
- No standalone `DEPLOYED-AND-VALIDATED.md` — validation is summarized in [`../README.md`](../README.md) and [`../docs/DEPLOY-QUICKSTART.md`](../docs/DEPLOY-QUICKSTART.md).

## 8. Security testing (pen-test, CI gates, SBOM)

- Pen-test scope: **not present as a standalone doc** — customer-owned; nearest equivalent is the threat model + incident-response docs above.
- CI security gates — [`../.github/`](../.github/) workflows; full test suite (governance + platform + agent) via `make test`.
- SBOM: not present as a static artifact — **customer-owned**, generated per build/release.
- Third-party risk (TPRM) due-diligence packet — [`../offerings/TPRM-DUE-DILIGENCE-PACKET.md`](../offerings/TPRM-DUE-DILIGENCE-PACKET.md)

## 9. Shared-responsibility / RACI

- Production-readiness & shared-responsibility split — [`../docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`](../docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md)
- Shared-responsibility matrix — [`../docs/SHARED-RESPONSIBILITY-MATRIX.md`](../docs/SHARED-RESPONSIBILITY-MATRIX.md)
- Incident response runbook — [`../runbooks/INCIDENT-RESPONSE.md`](../runbooks/INCIDENT-RESPONSE.md)

## 10. Known limitations & maturity

- Capability maturity matrix & maturity ladder — [`../README.md`](../README.md) (§ "Maturity Ladder" / "Capability maturity matrix")
- Suite status — [`../SUITE-STATUS.md`](../SUITE-STATUS.md)

## 11. Contact & reporting

- Vulnerability reporting via **GitHub Security Advisories** (repository *Security* tab →
  *Report a vulnerability*) — see [`../SECURITY.md`](../SECURITY.md). Do not open public issues
  for security reports.
- Per-stakeholder security briefings / talk tracks — [`../docs/STAKEHOLDER-SECURITY-BRIEFINGS.md`](../docs/STAKEHOLDER-SECURITY-BRIEFINGS.md)

---

*Reference accelerator — not an AWS service, not AWS-supported software, not a compliance
certification, and not production-ready for regulated data without customer-specific
engineering, testing, authorization, and operational ownership.*

- **GDPR / EU annex:** [`../docs/GDPR-EU-ANNEX.md`](../docs/GDPR-EU-ANNEX.md) and DPIA template [`../docs/DPIA-TEMPLATE.md`](../docs/DPIA-TEMPLATE.md) — roles, lawful basis, Art. 9 health data, residency/transfers, Art. 22 automated-decision posture.

- **Agent 02 output-quality evidence:** [`../governance/evals/eval-report.md`](../governance/evals/eval-report.md) � scored PV benchmark (seriousness recall, entity F1, duplicate accuracy, grounding, **PHI-leak hard gate = 0**, E2B completeness) with regulatory thresholds gated in CI (`make eval-agent02`).
