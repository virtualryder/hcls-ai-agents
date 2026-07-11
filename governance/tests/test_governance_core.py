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


def test_prompt_manifest_pins_all_discovered_prompts():
    # The shipped manifest must match every self-registering agent prompt exactly:
    # discovery finds them, and each is pinned to its real SHA-256 (no placeholders).
    prompt_registry._REGISTRY.clear()
    prompt_registry._discover()
    registered = prompt_registry.current_registry()
    assert registered, "discovery registered no prompts — the gate would be vacuous"
    assert len(registered) == 9, f"expected 9 registered prompts, got {len(registered)}"
    assert prompt_registry.verify_manifest() == {}, "shipped manifest does not match registered prompts"


def test_prompt_registry_flags_placeholder_pin(tmp_path, monkeypatch):
    # A manifest entry that still holds a placeholder (not a real SHA-256) must fail
    # the gate rather than silently passing a vacuous check.
    import json

    manifest = tmp_path / "prompt_manifest.json"
    manifest.write_text(json.dumps({
        "test-agent:p1": {"version": 1, "sha256": "managed-by-prompt_registry --update",
                          "agent": "test-agent", "name": "p1"},
    }))
    monkeypatch.setattr(prompt_registry, "_MANIFEST", manifest)
    prompt_registry._REGISTRY.clear()
    prompt_registry.register("test-agent", "p1", v=1, text="original prompt text")
    problems = prompt_registry.verify_manifest()
    assert "test-agent:p1" in problems
    assert "hash-pinned" in problems["test-agent:p1"]


def test_prompt_registry_fails_on_vacuous_check(tmp_path, monkeypatch):
    # Zero registered prompts is itself a failure: an empty gate checks nothing.
    import json

    manifest = tmp_path / "prompt_manifest.json"
    manifest.write_text(json.dumps({}))
    monkeypatch.setattr(prompt_registry, "_MANIFEST", manifest)
    prompt_registry._REGISTRY.clear()
    problems = prompt_registry.verify_manifest()
    assert problems, "an empty registry must fail the change-control gate"


def test_prompt_registry_detects_tampered_prompt(tmp_path, monkeypatch):
    # A registered prompt whose text drifts from its pin must be flagged.
    import json

    prompt_registry._REGISTRY.clear()
    prompt_registry.register("test-agent", "p1", v=1, text="original prompt text")
    pinned = prompt_registry.current_registry()["test-agent:p1"]["sha256"]
    manifest = tmp_path / "prompt_manifest.json"
    manifest.write_text(json.dumps({
        "test-agent:p1": {"version": 1, "sha256": pinned, "agent": "test-agent", "name": "p1"},
    }))
    monkeypatch.setattr(prompt_registry, "_MANIFEST", manifest)
    assert prompt_registry.verify_manifest() == {}
    # Tamper: same key, changed text -> different SHA-256.
    prompt_registry._REGISTRY.clear()
    prompt_registry.register("test-agent", "p1", v=1, text="TAMPERED prompt text")
    problems = prompt_registry.verify_manifest()
    assert "test-agent:p1" in problems
    assert "changed" in problems["test-agent:p1"]
