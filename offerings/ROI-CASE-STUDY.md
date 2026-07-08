# Worked ROI case study — Pharmacovigilance / ICSR Intake (Agent 02)

**What this is.** A fully worked, illustrative ROI example with totals — the value counterpart to
[`TCO-MODEL.md`](TCO-MODEL.md). Illustrative, source-tagged assumptions; not a guarantee or a customer
result. Replace bracketed inputs with the sponsor/CRO's actuals. `[MODEL ASSUMPTION]` marks editable
drivers.

## Scenario: a mid-size pharma / CRO safety operation

| Input | Value | Source |
|---|---|---|
| Individual Case Safety Reports (ICSRs) processed / yr | 120,000 | `[MODEL ASSUMPTION]` |
| Analyst time per case (intake → triage → narrative draft) today | ~45 min | `[INDUSTRY-RESEARCH]` |
| Fully-loaded safety-analyst cost | $75/hr | `[MODEL ASSUMPTION]` |
| Regulatory reporting-timeliness exposure (late/expedited cases) | risk of GVP findings | `[GOV]` GVP obligations |

## The intervention

Agent 02 extracts adverse-event entities and PHI from case narratives (opt-in **Amazon Comprehend
Medical**, fail-closed, wired in the sibling healthcare suite as the live pattern), drafts the ICSR
narrative, and flags seriousness — **case seriousness sign-off and submission are withheld from the
agent; a named human signs** (21 CFR Part 11 e-signature). Lever: cut analyst minutes per case and
improve timeliness.

## Worked value (illustrative)

| Line | Calculation | Annual value |
|---|---|---|
| Time saved per case (45 → 20 min review) | 25 min × 120,000 = 50,000 hrs | — |
| Analyst cost reclaimed | 50,000 hrs × $75 | **$3,750,000** |
| Timeliness/quality (avoided late-case exposure, illustrative) | `[MODEL ASSUMPTION]` | upside, not quantified here |
| **Gross annual benefit (illustrative)** | | **~$3.75M** |

## Cost side (from TCO-MODEL.md)

| Line | Annual |
|---|---|
| AWS run cost (production scale, from TCO-MODEL, ECS/inference-heavy) | ~$78,000/yr |
| Comprehend Medical DetectPHI (opt-in, volume-driven) | `[MODEL ASSUMPTION]` add per case; small vs analyst cost |
| Implementation + CSV/validation (one-time, engagement) | `[MODEL ASSUMPTION]` $300,000–$700,000 (Part 11 CSV is real work) |

## ROI

Analyst-time reclaim (~$3.75M) against ~$78K/yr AWS + a one-time validated build pays back inside the
first year even after the (non-trivial) computer-system-validation cost. For a CIO/QA lead: the AWS
consumption is small; the real gates are **CSV/Part 11 validation and connector integration** — which
is exactly why the human-signed, audit-tamper-evident design matters.

## Honesty rails

- Illustrative model, not a sponsor outcome or guarantee. Case volumes and per-case time vary — use
  actuals; start with a synthetic/de-identified pilot.
- The agent drafts and flags; **a named human signs every consequential safety decision** (Part 11
  e-signature). Value assumes that model, not autonomous case processing.
- Comprehend Medical is HIPAA-eligible, reached via regional API/PrivateLink under the customer BAA;
  PHI is not sent to external AI APIs. The engine is opt-in and fail-closed.
- 21 CFR Part 11 conformance is customer-owned (CSV/CSA); this is a supporting design, not a
  certification. Budget the validation cost — it's the largest one-time line.
