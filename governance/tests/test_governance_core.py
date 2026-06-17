"""Core governance tests: grounding flags hallucinated claims; prompt registry drift."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from governance.grounding import verify_grounding
from governance import prompt_registry


def test_grounding_passes_clean_narrative():
    state = {"product": "Cardizem", "dose_mg": 120, "n": 450}
    text = "Cardizem 120 mg was administered to 450 subjects."
    assert verify_grounding(text, state).grounded


def test_grounding_flags_ungrounded_number():
    state = {"product": "Cardizem", "dose_mg": 120}
    text = "Cardizem 999 mg was administered."
    rep = verify_grounding(text, state)
    assert not rep.grounded
    assert any("999" in n for n in rep.ungrounded_numbers)


def test_grounding_flags_ungrounded_entity():
    state = {"product": "Cardizem"}
    text = "The Acme Pharmaceuticals representative confirmed the dose."
    rep = verify_grounding(text, state)
    assert not rep.grounded
    assert any("Acme" in e for e in rep.ungrounded_entities)


def test_grounding_allowlists_regulatory_boilerplate():
    state = {"event": "headache"}
    text = "The Serious Adverse Event was reported to the FDA per ICH guidance."
    rep = verify_grounding(text, state)
    # FDA / ICH / Serious Adverse Event are allow-listed regulatory terms.
    assert "FDA" not in rep.ungrounded_entities


def test_prompt_registry_detects_drift():
    prompt_registry._REGISTRY.clear()
    prompt_registry.register("test-agent", "p1", v=1, text="original prompt text")
    # No manifest entry for test-agent:p1 -> flagged as missing.
    problems = prompt_registry.verify_manifest()
    assert "test-agent:p1" in problems
