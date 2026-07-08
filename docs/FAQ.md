# HCLS AI Agent Suite — FAQ

Plain answers to the questions customers, AWS account teams, and SI architects ask most.

## What is this, exactly?
A governed, AWS-native **accelerator** — not a certified product. It is nine reference AI
agents for life-sciences workflows that share one governed control plane (MCP authorization
gateway, in-VPC Bedrock + Guardrails, PHI masking, grounding verification, framework-enforced
human-in-the-loop, and a 21 CFR Part 11 append-only audit trail). It gives an SI engagement a
compliant, auditable starting point.

## What is it *not*?
A turnkey SaaS you switch on, a computer-system-validated (CSV/CSA) system, a certified product,
or anything that takes GxP / 21 CFR Part 11 accountability off the sponsor. Production-readiness
(validation, live connectors, IdP integration, penetration test) is the engagement.

## Which agents are included?
01 Regulatory Writing & Intelligence · 02 Pharmacovigilance (ICSR intake) · 03 Clinical Trial Ops
& TMF · 04 Site Selection & Patient Matching · 05 Quality / CAPA & Complaints · 06 Clinical
Protocol Design & Feasibility · 07 Real-World Evidence / HEOR · 08 Medical Affairs / MSL Copilot · 09 Manufacturing Batch-Review (CMC/GxP). A tenth agent — 10 Scientific Intelligence & Target Discovery (R&D) — is at roadmap/Documented maturity (cited deck + design spec).

## Where do we start?
Land-first with **01 / 02 / 03 / 08** — document- and case-centric, measurable, lower decision-risk.
Agent **02** is the best live demo: it ships a real Bedrock + real-connector path you can run
end-to-end. Then expand to 05/06 and scale to the de-identified-RWD agents 04/07.

## Does patient data (PHI) leave our environment?
No. Bedrock inference runs **in-account, inside your VPC** via a VPC endpoint, and the PHI masker
replaces identifiers with stable pseudonyms **before** any prompt or audit record. The LLM factory
also supports a deterministic demo mode with no LLM call at all.

## How is this 21 CFR Part 11 / GxP-defensible?
Every gateway call is logged to an append-only DynamoDB + S3 Object Lock (WORM) audit with full
lineage (actor, timestamp, sources, model + prompt version). Consequential actions block until a
named, correctly-roled reviewer binds their identity — the e-signature linkage. Prompts are
hash-pinned for model-risk change control. See `governance/` and `docs/WELL-ARCHITECTED-REVIEW.md`.

## What does the customer have to provide?
An IdP (Okta / Entra / Ping) with the reviewer roles; network reachability to the systems of record
(Veeva / Argus / Medidata / QMS) via PrivateLink / Direct Connect; approved corpus/KB content; named
reviewers; and a validated AWS account. See `docs/AWS-ACCOUNT-PREREQUISITES.md`.

## Can it run without an AWS account?
Yes — `EXTRACT_MODE=demo` runs every workflow against deterministic fixtures with no API key, which
is how the **503 automated tests** pass and how you demo before any account exists.

## How does it deploy into a brand-new account?
`make build-lambdas` (vendors deps into each zip) then `make deploy` stages to S3 and deploys the
CloudFormation quickstart — connector Lambdas + a dual-mode MCP gateway (portable API Gateway+Cognito
**or** managed AgentCore) + the native/container agent — in any Region. Terraform is provided as a reference skeleton (not at parity — see docs/TERRAFORM-AND-GOVCLOUD-STATUS.md).
Full walkthrough: `docs/DEPLOY-QUICKSTART.md`.

## Which LLM does it use? Are we locked in?
The LLM factory routes to Amazon Bedrock (Claude, in-account) or the Anthropic API, or bypasses the
model in demo mode. Swapping models is a config change, not a re-architecture.

## What are the honest gaps today?
Live connectors run on fixtures (production validation is the engagement); no CSV/CSA package, SOC 2,
or penetration test of its own yet; the reviewer UI is an SI build; AgentCore managed-gateway
registration uses customer-supplied custom-resource placeholders (portable mode is the fallback);
KB-ingestion IaC and per-environment observability are finished during delivery. All of this is on
the `decks/HCLS-CIO-Adoption-Review.pptx` shortfalls + backlog slides.

## Are the deck metrics real?
Yes — every figure traces to `gtm/HCLS-DECK-SOURCES.md` with a source-class tag and URL, and
vendor/modeled/estimate figures are flagged on-slide and never used as the lead claim.

## Who pays for the pilot?
Often AWS funding programs (MAP / PoA / ISV Accelerate) plus SI services. See
`docs/AWS-FUNDING-AND-GTM.md` and `docs/AWS-MARKETPLACE-PATH.md`.

## How do we add another agent?
Follow `docs/CREATE-A-NEW-AGENT.md` — the platform, gateway, governance, and deck system are designed
to be extended without re-architecting.
