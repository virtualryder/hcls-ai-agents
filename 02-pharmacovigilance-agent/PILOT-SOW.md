# Scoped Pilot SOW — Governed Pharmacovigilance ICSR Intake on AWS

*Template statement of work for a time-boxed, low-risk pilot that proves the governed pattern in
the customer's own AWS account. Reference accelerator — not an AWS service, not a certification;
see [`NOT-CLAIMS.md`](../NOT-CLAIMS.md). This is a template for scoping, not a signed agreement or
legal/compliance advice.*

## 1. Objective

Prove, in the customer's AWS account, that an AI agent can **safely** perform PV case-intake work —
parse an adverse-event source record, extract E2B(R3) fields, code MedDRA/WHODrug, assess seriousness
and the reporting clock, and draft a CIOMS narrative — **with a qualified PV medical reviewer
authorizing every submission** and immutable evidence for every step. Deliberately narrow: **one
workflow, one connector path, one approval path, one evidence report.**

## 2. Duration & shape

**6–10 weeks**, three phases: Foundation (weeks 1–3) → Governed pilot (weeks 3–8) → Evidence & readout
(weeks 8–10). Synthetic or de-identified adverse-event data only; no production safety database write.

## 3. Customer prerequisites (before week 1)

- An AWS account (or sandbox OU) with Amazon Bedrock + the required model enabled in a supported Region.
- An identity provider (Okta / Entra / AD) for federated login and the PV role groups (processor, medical reviewer).
- A named **PV medical reviewer** and a business owner empowered to approve go/no-go.
- Security contact for the account (KMS key policy, VPC, Guardrail settings review).
- **Data:** a set of **synthetic or de-identified** AE source records (email/PDF/CSV). No PHI in the pilot unless a BAA and PHI handling are separately agreed.

## 4. Scope — in

- Deploy the Agent 02 golden path (SAM) into the customer account: MCP authorization gateway, Step
  Functions workflow with the `waitForTaskToken` human gate, append-only + WORM audit, PHI masking,
  token budget, Bedrock + Guardrails over PrivateLink.
- **One connector path:** the **tier-3 openFDA/FAERS live reference** read (public), OR a
  **tier-2 local HTTP stand-in** shaped like the customer's safety DB. (Production Argus/Veeva =
  out of scope — see §5.)
- Wire the customer IdP federation and the two PV roles; exercise the human-approval gate with the
  named reviewer.
- Run the governed workflow end-to-end on synthetic cases; produce the immutable audit evidence.
- Run the scored safety eval (`make eval-agent02`) and the 10-point negative demo (`make neg-demo`)
  in the customer account as acceptance gates.

## 5. Scope — out (explicitly)

- **Production connector to Argus / Veeva Safety or HealthLake FHIR PHI (tier-4)** — engagement work
  under a separate SOW and BAA.
- Computer-system validation (CSV/CSA), 21 CFR Part 11 qualification, penetration test, SOC 2 / HITRUST.
- Production monitoring/alerting, DR, and ongoing operations.
- Real ICSR submission to a regulator or a production safety database.

## 6. Success metrics (agreed before week 3)

- **Governance:** 10/10 negative-demo refusals enforced in the customer account; PHI-leak rate = 0 on the scored eval.
- **Human authority:** every draft submission blocks at the reviewer gate; the irreversible submit is never taken by the agent.
- **Quality:** seriousness recall ≥ 0.95 and entity F1 ≥ 0.85 on the labeled set.
- **Throughput (illustrative, to be baselined):** median case-intake handling time vs. the manual baseline.
- **Evidence:** a complete, append-only audit trail for every pilot case, exported as the evidence pack.

## 7. Security gates (must pass to proceed to readout)

Deny-by-default gateway live; bound single-use SoD approvals (`STRICT_APPROVAL=1`); scoped short-lived
tokens; fail-closed PHI masking; append-only + WORM audit; Bedrock reached only over PrivateLink with
no egress to external AI APIs; egress FQDN allow-list if the openFDA path is used. Reviewed against
[`ASSURANCE-PACKET.md`](ASSURANCE-PACKET.md) and [`../docs/THREAT-MODEL.md`](../docs/THREAT-MODEL.md).

## 8. Deployment path

Canonical: the per-agent **SAM golden path** (`infra/golden-path-02-pharmacovigilance/`) — `sam build
&& sam deploy` + smoke test + teardown. Hardened option: the `-secure` variant (in-VPC Lambdas,
PrivateLink, CMK, S3 Object-Lock, CloudFront/WAF). Runbook:
[`docs/aws-deployment-guide.md`](docs/aws-deployment-guide.md).

## 9. Deliverables

1. Deployed governed Agent 02 golden path in the customer account.
2. Evidence pack: clean-account acceptance, the negative-demo result, the scored eval report, and the per-case audit export.
3. A go/no-go readout deck with the success-metric results and a scoped path to production (connector integration, CSV, IdP, monitoring).

## 10. Go / no-go criteria (end of pilot)

**Go** if: all security gates pass, 10/10 refusals enforced, PHI-leak = 0, the human gate held on every
case, and the throughput/quality metrics meet the agreed thresholds. **No-go / iterate** if any
security gate fails or the human-authority boundary is not demonstrably enforced.

## 11. Shared responsibility

Per [`ASSURANCE-PACKET.md` §9](ASSURANCE-PACKET.md) and
[`../docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`](../docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md).
The accelerator provides the governed control plane; the customer owns identity, production connectors,
validation, and operations.
