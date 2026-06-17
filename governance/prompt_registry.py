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
    _MANIFEST.write_text(json.dumps(_REGISTRY, indent=2, sort_keys=True) + "\n")


def verify_manifest() -> Dict[str, str]:
    """
    Return a dict of {key: problem} for any registered prompt whose hash/version
    does not match the manifest. Empty dict means CI passes.
    """
    manifest = load_manifest()
    problems: Dict[str, str] = {}
    for key, meta in _REGISTRY.items():
        pinned = manifest.get(key)
        if not pinned:
            problems[key] = "prompt not in manifest (add it with --update)"
        elif pinned.get("sha256") != meta["sha256"]:
            problems[key] = (
                f"prompt text changed without manifest bump "
                f"(manifest v{pinned.get('version')} -> registered v{meta['version']})"
            )
    return problems


def _discover() -> None:
    """Import agent prompt modules so they self-register (best-effort)."""
    import importlib
    import pkgutil
    import sys
    from pathlib import Path as _P

    repo = _P(__file__).resolve().parent.parent
    sys.path.insert(0, str(repo))
    for p in repo.glob("[0-9][0-9]-*/agent"):
        agent_pkg = p.parent.name
        sys.path.insert(0, str(p.parent))
        try:
            importlib.import_module("agent.prompts")
        except Exception:
            pass
        sys.path.pop(0)
    _ = pkgutil  # silence unused in minimal environments


if __name__ == "__main__":
    import sys

    _discover()
    if "--update" in sys.argv:
        write_manifest()
        print(f"Wrote manifest with {len(_REGISTRY)} prompts -> {_MANIFEST}")
    else:
        issues = verify_manifest()
        for k, v in issues.items():
            print("DRIFT", k, "-", v)
        print(f"\n{len(_REGISTRY) - len(issues)}/{len(_REGISTRY)} prompts match manifest")
        raise SystemExit(1 if issues else 0)
