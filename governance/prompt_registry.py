"""
Prompt registry — versioned, hash-pinned prompts (no silent prompt drift).

In a GxP / SR-11-7-style model-risk posture, the prompt is part of the model.
A prompt change can change a regulated output, so prompts must be versioned,
hash-pinned, and change-controlled like code. This registry:

  * computes a stable SHA-256 over each registered prompt,
  * checks it against governance/prompt_manifest.json (the pinned versions), and
  * fails CI if a prompt changed without a manifest bump (deliberate, reviewed).

Agents register their prompts at import time:

    from governance.prompt_registry import register
    SAE_NARRATIVE_PROMPT = register("02-pharmacovigilance", "sae_narrative", v=3, text=\"\"\"...\"\"\")

CI runs `verify_manifest()` (governance/tests). Bumping a prompt = update the
text, bump `v`, run `python -m governance.prompt_registry --update`, commit the
manifest diff alongside the prompt diff so the change is auditable.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict

_MANIFEST = Path(__file__).resolve().parent / "prompt_manifest.json"

# In-process registry: key -> {"version", "sha256", "agent", "name"}
_REGISTRY: Dict[str, Dict[str, object]] = {}


def _sha(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def register(agent: str, name: str, v: int, text: str) -> str:
    """Register a prompt and return its text (so call sites assign normally)."""
    key = f"{agent}:{name}"
    _REGISTRY[key] = {"version": v, "sha256": _sha(text), "agent": agent, "name": name}
    return text


def current_registry() -> Dict[str, Dict[str, object]]:
    return dict(_REGISTRY)


def load_manifest() -> Dict[str, Dict[str, object]]:
    if _MANIFEST.exists():
        return json.loads(_MANIFEST.read_text())
    return {}


def write_manifest() -> None:
    existing = load_manifest()
    out: Dict[str, object] = {}
    # Preserve human-authored top-level metadata (e.g. the "_comment" doc string).
    for k, v in existing.items():
        if k.startswith("_"):
            out[k] = v
    for k in sorted(_REGISTRY):
        out[k] = _REGISTRY[k]
    _MANIFEST.write_text(json.dumps(out, indent=2) + "\n")


def is_pinned_sha(value: object) -> bool:
    """True only for a real 64-hex SHA-256 pin. Placeholders / blanks fail."""
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(c in "0123456789abcdef" for c in value.lower())
    )


def verify_manifest() -> Dict[str, str]:
    """
    Return a dict of {key: problem}. Empty dict means the change-control gate passes.

    The gate fails (non-empty) when it would otherwise be VACUOUS — i.e. it must
    actually be checking real, hash-pinned prompts:
      * no prompts registered at all (discovery found nothing);
      * a manifest entry still holds a placeholder instead of a real SHA-256;
      * a registered prompt is missing from the manifest, or its text drifted;
      * a pinned prompt is no longer discovered/registered.
    """
    manifest = load_manifest()
    problems: Dict[str, str] = {}

    # (a) Nothing registered => the gate would check nothing. Fail loudly.
    if not _REGISTRY:
        problems["<no-prompts>"] = (
            "no prompts registered — the change-control gate would check nothing (vacuous)"
        )

    # (b) A placeholder / non-SHA pin in the manifest is an un-pinned (vacuous) gate.
    for key, pinned in manifest.items():
        if key.startswith("_"):
            continue
        if not is_pinned_sha(pinned.get("sha256")):
            problems[key] = "manifest entry is not hash-pinned (placeholder sha256); run --update"

    # (c) Every registered prompt must be present and match its real pin.
    for key, meta in _REGISTRY.items():
        pinned = manifest.get(key)
        if not pinned:
            problems[key] = "prompt not in manifest (add it with --update)"
        elif not is_pinned_sha(pinned.get("sha256")):
            problems.setdefault(
                key, "manifest entry is not hash-pinned (placeholder sha256); run --update"
            )
        elif pinned.get("sha256") != meta["sha256"]:
            problems[key] = (
                f"prompt text changed without manifest bump "
                f"(manifest v{pinned.get('version')} -> registered v{meta['version']})"
            )

    # (d) A real pin whose prompt is no longer discovered is silent-drop drift.
    for key, pinned in manifest.items():
        if key.startswith("_"):
            continue
        if key not in _REGISTRY and is_pinned_sha(pinned.get("sha256")):
            problems[key] = "pinned prompt is not registered — discovery no longer finds it"

    return problems


def _discover() -> None:
    """Import each agent's prompts so they self-register.

    Every agent ships its prompts under the SAME package name (`agent.prompts`),
    so a naive repeated import hits sys.modules' cache and only the FIRST agent
    ever registers. Evict the `agent*` modules around each import so every agent's
    prompts.py actually re-executes and registers.
    """
    import importlib
    import sys
    from pathlib import Path as _P

    def _evict_agent_modules() -> None:
        for name in [m for m in list(sys.modules) if m == "agent" or m.startswith("agent.")]:
            del sys.modules[name]

    repo = _P(__file__).resolve().parent.parent
    for p in sorted(repo.glob("[0-9][0-9]-*/agent")):
        agent_dir = p.parent
        sys.path.insert(0, str(agent_dir))
        _evict_agent_modules()
        try:
            importlib.import_module("agent.prompts")
        except Exception:
            pass
        finally:
            _evict_agent_modules()
            try:
                sys.path.remove(str(agent_dir))
            except ValueError:
                pass


def main(argv=None) -> int:
    import sys

    argv = list(sys.argv[1:] if argv is None else argv)
    # Invoked as `python -m governance.prompt_registry`, THIS file runs as
    # `__main__`, but the agent prompt modules import the registry under its real
    # name (`governance.prompt_registry`) — a DIFFERENT module object with its own
    # _REGISTRY. Drive the canonical module so we read what the prompts registered.
    from governance import prompt_registry as reg

    reg._discover()
    if "--update" in argv:
        reg.write_manifest()
        print(f"Wrote manifest with {len(reg.current_registry())} prompts -> {reg._MANIFEST}")
        return 0
    issues = reg.verify_manifest()
    registry = reg.current_registry()
    matched = sum(1 for k in registry if k not in issues)
    for k, v in sorted(issues.items()):
        print("DRIFT", k, "-", v)
    print(f"\n{matched}/{len(registry)} prompts match manifest")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
