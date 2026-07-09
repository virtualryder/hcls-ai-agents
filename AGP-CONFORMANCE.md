# AGP v1.0 Conformance — HCLS / Life Sciences

**This pack conforms to the Aegis Governance Pattern (AGP) v1.0.** AGP is the governance *contract*
(8 controls, each fail-closed and negative-tested) that every suite implements once in its
`platform_core`, so agents inherit identity, authorization, audit, masking, approval, budget, and
grounding without re-deriving them. The canonical, versioned contract lives in the Aegis repo:
`docs/14-GOVERNANCE-PATTERN-VERSIONING.md`.

- **Contract version implemented:** AGP **1.0**
- **Implementation package:** `hcls-agent-platform` (version declared in `MATURITY.yaml` / `pyproject.toml`)
- **Machine-readable claim:** `import hcls_agent_platform; hcls_agent_platform.AEGIS_GOVERNANCE_PATTERN_VERSION == "1.0"`

*Two versions are distinct: the **pattern** (AGP 1.0 — what a CISO reviews once) and this pack's
**implementation** (early 0.x). A reviewer approves the pattern once; each suite then shows it conforms.*

## The 8 required controls — implemented and proven here

| AGP v1.0 control | Implemented by | Proven by |
|---|---|---|
| 1. Identity (authN) — verified RS256/JWKS JWT; alg-confusion guarded; identity only from a verified claim | `auth.py` (verify_jwt RS256/JWKS) | `test_auth_walkthrough.py`; negative-demo #1–2 |
| 2. MCP / tool authorization gateway — deny-by-default; unregistered tool → deny | `mcp_gateway/gateway.py` + `policy.TOOL_REGISTRY` | negative-demo #4 (unregistered tool) |
| 3. Least-privilege intersection — effective = agent grant ∩ user entitlement | `mcp_gateway/policy.py` (`decide`) | `test_auth_walkthrough.py`; negative-demo #3 |
| 4. Human approval (SoD, single-use) — consequential acts withheld in code; bound, single-use, approver ≠ requester | `mcp_gateway/approvals.py` + `policy.CONSEQUENTIAL_COMMITS` | negative-demo #5–7; withholding test |
| 5. PII/PHI/regulated-data masking — fail-closed at every log/audit boundary | `phi.py` + `mcp_gateway/audit.py` | negative-demo #8 (masker down → fail-closed) |
| 6. Audit (append-only + WORM) — every decision recorded; IAM deny on mutate; S3 Object Lock | `mcp_gateway/audit.py` + `infra/cloudformation/data.yaml` | negative-demo #9; clean-account run |
| 7. Token budgets — per-agent hard cap enforced before spend | `budget.py` | `platform_core/tests/test_budget.py`; negative-demo #10 |
| 8. Model gateway + grounding — brokered model access; grounding / output-schema checks | `llm_factory.py` + `governance/grounding.py` | `make eval-agent02` (grounding metric) |

Hero: Agent 02 (Pharmacovigilance).

> Conformance is about the **control being present, fail-closed, and negative-tested** — not about
> production-readiness. See [`NOT-CLAIMS.md`](NOT-CLAIMS.md) for what this pack does not claim, and
> [`MATURITY.yaml`](MATURITY.yaml) for per-agent maturity and deployment evidence.
