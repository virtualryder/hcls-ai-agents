# Pharmacovigilance ICSR Agent — recorded demo transcript

**Self-service artifact.** This is the *actual captured output* of the governed real-connector
demo. It lets a reviewer see exactly what the agent does — a governed read of a real adverse-event
case, fail-closed PHI masking, and the human-authority boundary — without standing up any
environment. To reproduce it yourself, run the commands at the bottom; the offline mode is
deterministic and needs no API key.

> Reference accelerator — not an AWS service, not AWS-supported software, not a compliance
> certification. openFDA is public, de-identified data (no BAA). The PHI-under-BAA variant is
> AWS HealthLake FHIR. A companion visual walkthrough is `demo/demo-walkthrough.html`.

---

## What you are looking at

The agent extracts an Individual Case Safety Report (ICSR) from a real FDA adverse-event record.
Every tool call is routed through the Aegis MCP gateway: **deny-by-default authorization →
least-privilege scoped token → fail-closed PHI masking → append-only audit**. The trust anchor
is the last beat: the agent can *draft*, but it cannot *submit* — that authority stays with a human.

---

## Recorded run (`OPENFDA_OFFLINE=1 python demo/demo_openfda.py`)

```
======================================================================
  PHARMACOVIGILANCE ICSR AGENT — REAL CONNECTOR DEMO (openFDA / FAERS)
======================================================================
  [mode] OFFLINE — serving recorded openFDA cassette (no network)
  [connector] OpenFDASafetyConnector  source=openFDA FAERS (public, de-identified)

1 / 4  Governed read: safety.get_case  (real FAERS data)
  decision=ALLOW  audit_id=4c0fee60  token_scope=['safety.get_case']
  REAL case 18424955 — serious=True ['Hospitalization']
    suspect drug(s): ['METFORMIN']   reactions: ['Lactic acidosis', 'Acute kidney injury']
    demographics   : {'age': '67 year', 'sex': 'Female', 'weight_kg': '72'}   country: US

2 / 4  PHI masking (A3) — fail-closed, runs even on de-identified data
  masked narrative: A female patient, age 67 year, reported from US experienced a SERIOUS
                    adverse event (Hospitalization) following administration of METFORMIN...
  PHI-leak check  : PASS (identifiers redacted, fail-closed)

3 / 4  Governed read: safety.search_duplicates  (real FAERS data)
  decision=ALLOW  audit_id=f4fff6db  candidates=[]

4 / 4  Human authority boundary (the trust anchor)
  safety.write_case_draft (no approval) -> PENDING_APPROVAL (requires_approval=True)
  safety.submit_report                  -> DENY  (approver roles=['PV_PROCESSOR'] not
                                                  entitled to commit 'safety.submit_report')

======================================================================
  DEMO COMPLETE — governed pattern proven against a REAL system of record
======================================================================
  * Real openFDA/FAERS read through deny-by-default gateway (PV_PROCESSOR)
  * Fail-closed PHI masking on ingested text (no identifier leaks)
  * Scoped per-call token + append-only masked audit on every call
  * Draft write requires human approval; ICSR submission WITHHELD from the agent
  * openFDA is public/de-identified -> NO BAA; HealthLake FHIR is the PHI variant
```

## What each beat proves to a reviewer

| Beat | Reviewer question it answers | Evidence |
|---|---|---|
| 1 · Governed read (ALLOW) | Does the pattern work against a *real* system of record, not a mock? | Live case `18424955` from openFDA/FAERS, allowed + scoped + audited |
| 2 · PHI masking (PASS) | Can PHI leak out of an ingested narrative? | Masker runs fail-closed even on de-identified text; leak check passes |
| 3 · Governed search (ALLOW) | Is *every* tool call governed, not just the first? | Second call independently authorized + audited |
| 4 · Human boundary (PENDING / DENY) | Can the agent take a consequential action on its own? | Draft needs human approval; irreversible submission is denied to the agent entirely |

## How we know the *output* is good (scored, CI-gated)

`make eval-agent02` runs a labeled safety benchmark on every push. Latest: **all thresholds pass**,
including the hard gate **PHI-leak rate = 0**. Seriousness recall = 1.0 (≥0.95), entity F1 = 1.0
(≥0.85), duplicate accuracy = 1.0 (≥0.90), grounding = 1.0 (≥0.90), E2B completeness = 1.0 (≥0.95).
Negative-control tests prove the gate actually catches bad data. Full report:
`governance/evals/eval-report.md`.

## Reproduce it yourself

```bash
cd 02-pharmacovigilance-agent

# Offline — deterministic, no network, no API key:
PYTHONPATH=.:../platform_core:.. OPENFDA_OFFLINE=1 python demo/demo_openfda.py

# Live — against the real openFDA API (api.fda.gov):
PYTHONPATH=.:../platform_core:.. python demo/demo_openfda.py

# The scored benchmark:
make eval-agent02
```

**Pointers:** connector `platform_core/hcls_agent_platform/connectors/openfda.py` ·
locked egress `infra/golden-path-02-pharmacovigilance/EGRESS-OPENFDA.md` ·
governed round-trip tests `demo/../tests/test_openfda_connector.py` ·
in-cloud evidence `evidence/CLEAN-ACCOUNT-ACCEPTANCE.md`.
