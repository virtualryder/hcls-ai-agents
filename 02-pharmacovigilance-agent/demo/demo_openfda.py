"""
demo_openfda.py — the "one REAL connector" demo for Agent 02 (Pharmacovigilance).

Pulls a **real** adverse-event case from the public **openFDA** drug-event API
(FAERS) **through the governed MCP gateway**, then shows the whole governance
story against real data:

    real openFDA read  ->  deny-by-default authorization (PV_PROCESSOR)
                       ->  fail-closed PHI masking (A3)
                       ->  scoped per-call token + append-only masked audit
                       ->  human gate: draft requires approval; submission WITHHELD

openFDA is public and **de-identified**, so this needs **no BAA** — yet PHI
masking still runs on the ingested text (the control is exercised, not assumed).
The regulated/PHI variant (AWS HealthLake FHIR `AdverseEvent` under a BAA) is the
same interface behind a different SAFETY_SOURCE.

Usage
-----
    cd 02-pharmacovigilance-agent
    # Live (hits api.fda.gov):
    PYTHONPATH=.:../platform_core:.. python demo/demo_openfda.py
    # Offline / CI (uses the recorded cassette, no network):
    OPENFDA_OFFLINE=1 python demo/demo_openfda.py
    # Pick the drug to search for a real serious case:
    OPENFDA_DRUG=metformin python demo/demo_openfda.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_AGENT = _HERE.parent
_REPO = _AGENT.parent
sys.path.insert(0, str(_AGENT))
sys.path.insert(0, str(_REPO / "platform_core"))
sys.path.insert(0, str(_REPO))

SEP = "=" * 70


def _load_cassette() -> dict:
    p = _AGENT / "tests" / "fixtures" / "openfda_sample.json"
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> None:
    print(f"\n{SEP}\n  PHARMACOVIGILANCE ICSR AGENT — REAL CONNECTOR DEMO (openFDA / FAERS)\n{SEP}")

    # ── Governed, real-connector mode ───────────────────────────────────────
    os.environ["CONNECTOR_MODE"] = "live"
    os.environ["SAFETY_SOURCE"] = "openfda"
    os.environ["DISABLE_SECRETS_MANAGER"] = "1"
    offline = os.getenv("OPENFDA_OFFLINE", "").strip() in ("1", "true", "yes")
    drug = os.getenv("OPENFDA_DRUG", "").strip()

    from hcls_agent_platform.connectors import openfda
    from hcls_agent_platform.connectors.factory import get_connector
    from hcls_agent_platform.mcp_gateway import MCPGateway
    from hcls_agent_platform.phi import mask  # A3: fail-closed masker

    # Offline/CI: serve the recorded real-structure cassette instead of the network.
    if offline:
        cassette = _load_cassette()
        openfda.OpenFDASafetyConnector._get = lambda self, params: cassette
        print("  [mode] OFFLINE — serving recorded openFDA cassette (no network)")
    else:
        print("  [mode] LIVE — calling https://api.fda.gov/drug/event.json")

    conn = get_connector("safety")  # -> OpenFDASafetyConnector (real, read-only)
    print(f"  [connector] {type(conn).__name__}  source={conn.source}")

    gw = MCPGateway()
    processor = {"sub": "demo-pv-processor", "custom:hcls_role": "PV_PROCESSOR"}

    # ── 1. Governed READ of a REAL case ─────────────────────────────────────
    print(f"\n1 / 4  Governed read: safety.get_case  (real FAERS data)")
    args = {"case_id": None, "drug": drug} if drug else {}
    try:
        r = gw.invoke(user_claims=processor, agent_id="02-pharmacovigilance",
                      tool="safety.get_case", args=args)
    except Exception as exc:  # network/API failure -> fail closed, fall back to cassette
        print(f"  [warn] live openFDA call failed ({exc}); falling back to cassette")
        cassette = _load_cassette()
        openfda.OpenFDASafetyConnector._get = lambda self, params: cassette
        r = gw.invoke(user_claims=processor, agent_id="02-pharmacovigilance",
                      tool="safety.get_case", args=args)

    if not r.allowed:
        print(f"  DENIED: {r.reason}"); return
    case = r.result
    print(f"  decision={r.decision}  audit_id={r.audit_id[:8]}  token_scope={r.scope}")
    print(f"  REAL case {case['case_id']} — serious={case['serious']} {case['seriousness_criteria']}")
    print(f"    suspect drug(s): {case['suspect_drugs']}   reactions: {case['reactions']}")
    print(f"    demographics   : {case['demographics']}   country: {case['country']}")

    # ── 2. A3: fail-closed PHI masking on the ingested narrative ────────────
    print(f"\n2 / 4  PHI masking (A3) — fail-closed, runs even on de-identified data")
    raw_narrative = case.get("narrative_text", "")
    # Demonstrate the control catches PHI even if a real feed leaked an identifier:
    stress = raw_narrative + "  [intake note: reporter jane.doe@example.com, SSN 123-45-6789]"
    masked = mask(stress)
    leaked = ("123-45-6789" in masked) or ("jane.doe@example.com" in masked)
    print(f"  masked narrative: {masked[:150]}...")
    print(f"  PHI-leak check  : {'FAIL (leak!)' if leaked else 'PASS (identifiers redacted, fail-closed)'}")
    assert not leaked, "PHI masking must not leak identifiers"

    # ── 3. Governed duplicate search against real data ──────────────────────
    print(f"\n3 / 4  Governed read: safety.search_duplicates  (real FAERS data)")
    crit = {"suspect_drug": (case['suspect_drugs'] or ['']) [0],
            "meddra_pt": (case['reactions'] or ['']) [0],
            "case_id": case['case_id']}
    rd = gw.invoke(user_claims=processor, agent_id="02-pharmacovigilance",
                   tool="safety.search_duplicates", args=crit)
    print(f"  decision={rd.decision}  audit_id={rd.audit_id[:8]}  candidates={rd.result}")

    # ── 4. The human authority boundary ─────────────────────────────────────
    print(f"\n4 / 4  Human authority boundary (the trust anchor)")
    rw = gw.invoke(user_claims=processor, agent_id="02-pharmacovigilance",
                   tool="safety.write_case_draft", args={"case_id": case['case_id']})
    print(f"  safety.write_case_draft (no approval) -> {rw.decision} (requires_approval={rw.requires_approval})")
    rs = gw.invoke(user_claims=processor, agent_id="02-pharmacovigilance",
                   tool="safety.submit_report", args={"case_id": case['case_id']})
    print(f"  safety.submit_report                  -> {rs.decision}  ({rs.reason[:70]})")

    print(f"\n{SEP}\n  DEMO COMPLETE — governed pattern proven against a REAL system of record")
    print(f"{SEP}")
    print("  * Real openFDA/FAERS read through deny-by-default gateway (PV_PROCESSOR)")
    print("  * Fail-closed PHI masking on ingested text (no identifier leaks)")
    print("  * Scoped per-call token + append-only masked audit on every call")
    print("  * Draft write requires human approval; ICSR submission WITHHELD from the agent")
    print("  * openFDA is public/de-identified -> NO BAA; HealthLake FHIR is the PHI variant\n")


if __name__ == "__main__":
    main()
