# OWASP Top-10 for LLM Applications + MITRE ATLAS — HCLS Mapping

> How the suite mitigates each OWASP LLM risk and the relevant MITRE ATLAS adversary techniques, with
> the control and the test that proves it. The recurring theme: **controls are enforced in the gateway,
> outside the model**, so model-layer attacks cannot disable authorization, masking, approval, or audit.

## OWASP Top-10 for LLM Applications (2025)

| ID | Risk | Mitigation in this suite | Proof |
|---|---|---|---|
| **LLM01** | Prompt Injection | Authorization/approval/masking live **outside** the model (gateway); deny-by-default; Guardrails; consequential commits withheld from agents | `governance/redteam/` (injection denied), `policy.py` |
| **LLM02** | Sensitive Information Disclosure | PHI masking **before** any model call or audit write; private-connectivity Bedrock via VPC endpoint (PrivateOnly = no NAT route); Guardrails PII filters | `phi.py`, `tests/.../test_pii*`, `llm_factory.py` |
| **LLM03** | Supply Chain | Pinned deps vendored deterministically into Lambda zips; CI compile + 583 tests gate every change | `scripts/build_lambdas.sh`, CI |
| **LLM04** | Data & Model Poisoning | Grounding verification rejects ungrounded claims; approved-corpus RAG; prompt hash-pinning | `governance/grounding.py`, `prompt_registry.py` |
| **LLM05** | Improper Output Handling | Outputs are decision-support drafts; a human gate + grounding/quality checks precede any consequential use | per-agent `quality_checker.py`, HITL gate |
| **LLM06** | Excessive Agency | Least-privilege intersection; **consequential commits withheld from agents**; bound human approval on writes | `policy.py::CONSEQUENTIAL_COMMITS`, `approvals.py` |
| **LLM07** | System Prompt Leakage | No secrets in prompts; secrets via Secrets Manager + scoped tokens; prompts are reviewed/hash-pinned | `secrets.py`, `tokens.py` |
| **LLM08** | Vector/Embedding Weaknesses | RAG over an approved corpus only; grounding ties claims to retrieved source | `governance/grounding.py` |
| **LLM09** | Misinformation | Grounding fails closed on unsourced figures; vendor/modeled stats flagged; human owns the decision | `grounding.py`, `gtm/HCLS-DECK-SOURCES.md` |
| **LLM10** | Unbounded Consumption | WAF rate limiting; scoped per-call tokens; Budgets + Cost Anomaly Detection (customer) | `edge.yaml`, prereqs |

## MITRE ATLAS technique coverage (selected)

| ATLAS technique | How it's addressed |
|---|---|
| **AML.T0051 LLM Prompt Injection** | Gateway-enforced authorization outside the model; red-team test denies injection-driven over-action |
| **AML.T0057 LLM Data Leakage** | PHI masked pre-model; private-connectivity inference; Guardrails; append-only audit detects attempts |
| **AML.T0054 LLM Jailbreak** | Bedrock Guardrails + grounding + the human gate; the consequential act is not model-reachable |
| **AML.T0048 Societal/again Harm (bias)** | Fairness / four-fifths screen on flag/rank workflows; human review | 
| **AML.T0049 Exfiltration via Inference API** | Endpoint-only (PrivateOnly mode): in-account Bedrock via VPC endpoint; least-privilege connectors |
| **AML.T0043 Craft Adversarial Data** | Grounding rejects ungrounded outputs; deterministic checks precede the human gate |

> **One-line CISO takeaway:** every model-layer attack class is contained because the model has **no
> standing authority** — it can draft and propose, but the gateway (deny-by-default, withheld commits,
> bound approval, masking, audit) decides what actually happens, and a human signs the consequential act.
