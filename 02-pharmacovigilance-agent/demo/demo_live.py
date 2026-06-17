"""
demo_live.py — Customer-ready live demo for the Pharmacovigilance ICSR agent.

Demonstrates the full live path:
  * LiveSafetyConnector making real HTTP calls to a safety system of record
  * Bedrock (or Anthropic) LLM drafting the ICSR narrative
  * MCP authorization gateway enforcing HITL + audit
  * E2B-style ICSR submission with a verified human approval

Mode selection (in priority order):
  1. LLM_PROVIDER=bedrock + AWS credentials -> Amazon Bedrock (in-account inference)
  2. ANTHROPIC_API_KEY set               -> Anthropic API
  3. Otherwise                           -> EXTRACT_MODE=demo (deterministic, no API key)

Connector:
  * SAFETY_BASE_URL already set -> uses that endpoint
  * Otherwise, starts the local reference safety service on an ephemeral port

Usage
-----
# Full demo (deterministic, no credentials needed):
    cd 02-pharmacovigilance-agent
    PYTHONPATH=.:../platform_core:.. python demo/demo_live.py

# With Anthropic API:
    ANTHROPIC_API_KEY=sk-ant-... python demo/demo_live.py

# With Amazon Bedrock (in-account):
    LLM_PROVIDER=bedrock BEDROCK_REGION=us-east-1 python demo/demo_live.py

# Against your real safety endpoint:
    SAFETY_BASE_URL=https://your-argus-gateway.example.com CONNECTOR_MODE=live python demo/demo_live.py
"""
from __future__ import annotations

import json
import os
import sys
import textwrap
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup — must happen before any local imports
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent          # 02-pharmacovigilance-agent/demo/
_AGENT = _HERE.parent                            # 02-pharmacovigilance-agent/
_REPO = _AGENT.parent                            # repo root
sys.path.insert(0, str(_AGENT))
sys.path.insert(0, str(_REPO / "platform_core"))
sys.path.insert(0, str(_REPO))

# ---------------------------------------------------------------------------
# 1. Start local reference safety service (unless SAFETY_BASE_URL already set)
# ---------------------------------------------------------------------------

_local_service_port: int = 0
_local_service_active: bool = False


def _ensure_safety_service() -> str:
    """Returns the SAFETY_BASE_URL to use, starting a local service if needed."""
    global _local_service_port, _local_service_active

    existing = os.getenv("SAFETY_BASE_URL", "").strip()
    if existing:
        print(f"  [connector] Using external safety endpoint: {existing}")
        return existing

    from demo.reference_safety_service import start_in_background
    _local_service_port = start_in_background(port=0)
    _local_service_active = True
    url = f"http://127.0.0.1:{_local_service_port}"
    os.environ["SAFETY_BASE_URL"] = url
    print(f"  [connector] Started local reference safety service on {url}")
    return url


# ---------------------------------------------------------------------------
# 2. Determine LLM mode
# ---------------------------------------------------------------------------

def _select_llm_mode() -> str:
    """Return 'bedrock', 'anthropic', or 'demo'."""
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    if provider == "bedrock":
        # Validate that boto3 is present and creds look plausible
        try:
            import boto3  # noqa: F401
            return "bedrock"
        except ImportError:
            print("  [llm] LLM_PROVIDER=bedrock but boto3 not installed -> fallback")

    if os.getenv("ANTHROPIC_API_KEY", "").strip():
        return "anthropic"

    return "demo"


# ---------------------------------------------------------------------------
# 3. Sample case (serious, expedited, E2B-reportable)
# ---------------------------------------------------------------------------

_SAMPLE_CASE = {
    "case_id": "ICSR-2026-LIVE-0001",
    "source_type": "CALL_CENTER",
    "raw_source": (
        "Call center intake — caller is Dr. Robert Chen, nephrologist, "
        "Toronto General Hospital, Canada. Patient is a 67 year old male "
        "with hypertension receiving Lisinopril 20 mg once daily by oral "
        "route for hypertension. Patient was hospitalized on 2026-01-15 "
        "with acute renal failure, 21 days after starting Lisinopril. "
        "Creatinine elevated to 4.2 mg/dL. Patient required intensive "
        "care and dialysis. The event is considered an unexpected serious "
        "adverse reaction. Dechallenge: Lisinopril was discontinued; renal "
        "function improved (positive dechallenge). This is a medically "
        "important event requiring expedited reporting."
    ),
    "acting_user_claims": {
        "sub": "demo-pv-reviewer",
        "custom:hcls_role": "PV_MEDICAL_REVIEWER",
    },
}

# ---------------------------------------------------------------------------
# 4. Banner helpers
# ---------------------------------------------------------------------------

SEP = "=" * 70


def _banner(title: str) -> None:
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)


def _section(title: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print("─" * 60)


def _pretty(obj: object, indent: int = 2) -> str:
    try:
        return json.dumps(obj, indent=indent, default=str)
    except Exception:
        return str(obj)


# ---------------------------------------------------------------------------
# 5. Main demo
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"\n{SEP}")
    print("  PHARMACOVIGILANCE ICSR AGENT — LIVE DEMO")
    print("  Amazon Bedrock AgentCore + Real Safety Connector")
    print(SEP)

    # ── Step 1: connector ──────────────────────────────────────────────────
    _section("1 / 5  Connector setup")
    safety_url = _ensure_safety_service()
    os.environ["CONNECTOR_MODE"] = "live"
    os.environ["DISABLE_SECRETS_MANAGER"] = "1"  # local demo: no AWS secrets
    print(f"  CONNECTOR_MODE : live")
    print(f"  SAFETY_BASE_URL: {safety_url}")
    print("  MedDRA / WHODrug: fixture-backed (licensed API; see integration-guide.md)")

    # ── Step 2: LLM selection ──────────────────────────────────────────────
    _section("2 / 5  LLM provider selection")
    llm_mode = _select_llm_mode()
    if llm_mode == "bedrock":
        region = os.getenv("BEDROCK_REGION", "us-east-1")
        model = os.getenv("BEDROCK_NARRATIVE_MODEL_ID",
                          "anthropic.claude-sonnet-4-6-20260601-v1:0")
        guardrail = os.getenv("BEDROCK_GUARDRAIL_ID", "(not set — dev mode)")
        print(f"  Provider : Amazon Bedrock (in-account; no PHI/IP egress)")
        print(f"  Region   : {region}")
        print(f"  Model    : {model}")
        print(f"  Guardrail: {guardrail}")
        os.environ["LLM_PROVIDER"] = "bedrock"
    elif llm_mode == "anthropic":
        model = os.getenv("CLAUDE_NARRATIVE_MODEL", "claude-sonnet-4-6")
        print(f"  Provider : Anthropic API")
        print(f"  Model    : {model}")
        os.environ["LLM_PROVIDER"] = "anthropic"
    else:
        print("  Provider : DEMO (deterministic; no LLM API key required)")
        os.environ["EXTRACT_MODE"] = "demo"

    # ── Step 3: Verify live connector with a direct call ───────────────────
    _section("3 / 5  Live connector smoke-test (real HTTP)")
    from hcls_agent_platform.connectors.factory import get_connector
    from hcls_agent_platform.connectors.live import LiveSafetyConnector

    conn = get_connector("safety", mode="live")
    connector_type = type(conn).__name__
    print(f"  Connector type : {connector_type}")
    assert isinstance(conn, LiveSafetyConnector), (
        f"Expected LiveSafetyConnector, got {connector_type}"
    )

    # Fetch a known case to prove the HTTP path works
    case_result = conn.get_case(case_id="ICSR-2026-0002")
    print(f"  GET /cases/ICSR-2026-0002 -> HTTP 200")
    print(f"  case_id      : {case_result.get('case_id')}")
    print(f"  suspect_drug : {case_result.get('suspect_drug')}")
    print(f"  is_serious   : {case_result.get('is_serious')}")

    dup_result = conn.search_duplicates(suspect_drug="Lisinopril", meddra_pt="renal failure",
                                        reporter_country="Canada")
    print(f"  POST /cases/search-duplicates -> {len(dup_result)} potential match(es)")
    if dup_result:
        print(f"  Top match: {dup_result[0].get('case_id')} "
              f"(score={dup_result[0].get('match_score')})")

    # ── Step 4: Run the full PV graph ──────────────────────────────────────
    _section("4 / 5  Running ICSR graph (live connector + LLM)")
    print(f"  Input case : {_SAMPLE_CASE['case_id']}")
    print(f"  Source type: {_SAMPLE_CASE['source_type']}")
    print()

    from agent.graph import build_pharmacovigilance_graph

    graph = build_pharmacovigilance_graph(use_memory=False)
    final_state = graph.invoke(_SAMPLE_CASE)

    # ── Step 5: Print results ──────────────────────────────────────────────
    _section("5 / 5  Results")

    print("\n[PROVIDER + CONNECTOR]")
    print(f"  LLM provider  : {llm_mode}")
    print(f"  Connector     : {connector_type} -> {safety_url}")

    print("\n[EXTRACTED FIELDS]")
    print(f"  Patient       : {final_state.get('patient_age')} {final_state.get('patient_sex', '').lower()}")
    print(f"  Reporter      : {final_state.get('reporter_name')} ({final_state.get('reporter_country')})")
    print(f"  Suspect drug  : {final_state.get('suspect_drug')} {final_state.get('suspect_dose')}")
    print(f"  Time to onset : {final_state.get('time_to_onset_days')} days")

    print("\n[MEDDRA + WHODRUG CODING]")
    print(f"  MedDRA PT     : {final_state.get('meddra_pt')} [{final_state.get('meddra_pt_code')}]")
    print(f"  MedDRA SOC    : {final_state.get('meddra_soc')}")
    print(f"  WHODrug name  : {final_state.get('whodrug_name')}")
    print(f"  WHODrug ATC   : {final_state.get('whodrug_atc')}")

    print("\n[SERIOUSNESS + EXPEDITED CLOCK]")
    print(f"  Serious       : {final_state.get('is_serious')}")
    print(f"  Criteria      : {final_state.get('seriousness_criteria')}")
    print(f"  Clock         : {final_state.get('reporting_clock_days')}-day expedited")
    print(f"  Expectedness  : {final_state.get('expectedness')}")
    print(f"  Causality     : {final_state.get('causality_assessment')}")

    print("\n[DRAFTED ICSR NARRATIVE]")
    narrative = final_state.get("narrative_text", "")
    print(f"  Drafted by    : {final_state.get('narrative_drafted_by')}")
    print()
    for line in textwrap.wrap(narrative, width=66):
        print(f"  {line}")

    print("\n[GROUNDING REPORT]")
    grounding = final_state.get("grounding_report", {})
    print(f"  Grounded      : {grounding.get('grounded')}")
    ungrounded_nums = grounding.get("ungrounded_numbers", [])
    ungrounded_ent = grounding.get("ungrounded_entities", [])
    if ungrounded_nums or ungrounded_ent:
        print(f"  Warnings      : numbers={ungrounded_nums} entities={ungrounded_ent}")
    else:
        print("  Warnings      : none")
    print(f"  PHI check     : {'PASS' if final_state.get('phi_check_passed') else 'FAIL'}")
    print(f"  Required elems: {'OK' if final_state.get('required_elements_present') else 'MISSING'}")

    print(f"\n[RECOMMENDED ACTION]")
    action = final_state.get("recommended_action")
    action_str = getattr(action, "value", str(action))
    print(f"  Action        : {action_str}")

    # ── HITL approval + gateway-authorized submit_report ──────────────────
    print("\n[HITL APPROVAL + GATEWAY SUBMIT]")
    from tools.gateway_tools import submit_report as gateway_submit

    # Simulate a verified reviewer approving submission
    reviewer_claims = {
        "sub": "demo-pv-reviewer",
        "custom:hcls_role": "PV_MEDICAL_REVIEWER",
    }
    approval = {
        "approved": True,
        "reviewer": {"sub": "pv-medical-reviewer-01", "name": "Dr. Demo Reviewer"},
        "comment": "Narrative reviewed and approved for E2B submission.",
    }

    submit_res = gateway_submit(
        reviewer_claims,
        {
            "case_id": _SAMPLE_CASE["case_id"],
            "meddra_pt": final_state.get("meddra_pt"),
            "suspect_drug": final_state.get("suspect_drug"),
            "is_serious": final_state.get("is_serious"),
            "narrative_len": len(narrative),
        },
        approval=approval,
    )

    print(f"  Gateway decision: {submit_res.decision}")
    if submit_res.allowed:
        result = submit_res.result or {}
        print(f"  Submission ID   : {result.get('submission_id', result.get('case_id', 'N/A'))}")
        print(f"  Gateway         : {result.get('gateway', 'N/A')}")
        print(f"  Status          : {result.get('status', 'N/A')}")
    else:
        print(f"  Reason          : {submit_res.reason}")
    print(f"  Audit ID        : {submit_res.audit_id}")
    print(f"  Token JTI       : {submit_res.token_jti}")

    print("\n[AUDIT TRAIL]")
    audit = final_state.get("audit_trail", [])
    print(f"  {len(audit)} entries logged")
    for entry in audit:
        node = entry.get("node", "?")
        action_name = entry.get("action", "")[:60]
        ts = entry.get("timestamp", "")[:19]
        actor = entry.get("actor", "")
        print(f"  [{ts}] {actor:<15} {node:<25} {action_name}")

    _banner("DEMO COMPLETE")
    print(f"  LLM provider  : {llm_mode}")
    print(f"  Connector     : {connector_type}")
    print(f"  Safety URL    : {safety_url}")
    if _local_service_active:
        print("  (local reference service was used — swap SAFETY_BASE_URL for Argus/Veeva)")
    print(f"  Case status   : {final_state.get('case_status')}")
    print()
    print("  SECURITY PROPERTIES DEMONSTRATED:")
    print("  * In-account inference (Bedrock) — PHI/IP never leaves the AWS VPC")
    print("  * Scoped bearer token minted per call (no standing service accounts)")
    print("  * Deny-by-default gateway: agent grants ∩ user entitlements")
    print("  * HITL gate: submit_report blocked until verified reviewer approves")
    print("  * PHI-masked, immutable audit trail (21 CFR Part 11 / GVP Module VI)")
    print()


if __name__ == "__main__":
    main()
