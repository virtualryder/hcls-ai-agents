"""
Root pytest configuration — lets `pytest` run the ENTIRE suite in one command.

The nine agents (and their aws-native counterparts) each define packages named
`agent`, `tools`, and top-level modules `core` / `_shared`. Python caches modules
in sys.modules, so whichever agent's code imports first would win for the whole
run. This hook purges those cached modules whenever pytest moves to a test file
in a different agent directory, so each agent's tests import their own code.

Result: `pytest -q` from the repo root runs platform_core, governance, all nine
agents, and all nine AWS-native rebuilds together — no per-agent juggling.
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent

# platform_core and the repo root on the path (NOT any specific agent dir).
for p in (_ROOT / "platform_core", _ROOT):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

_AGENT_MODULE_PREFIXES = ("agent", "tools", "core", "_shared")
_NATIVE = _ROOT / "aws-native-reference"
_last_agent_dir: str | None = None


def _agent_dir_for(fspath: str) -> str | None:
    """Return the agent root directory for a test file, or None.

    Matches both `<repo>/0N-...-agent/` and `<repo>/aws-native-reference/0N-.../`.
    """
    p = Path(fspath).resolve()
    for parent in p.parents:
        if parent.name[:1] == "0" and parent.parent in (_ROOT, _NATIVE):
            return str(parent)
    return None


def _flush_and_set(agent_dir: str) -> None:
    global _last_agent_dir
    _last_agent_dir = agent_dir
    to_remove = [k for k in sys.modules
                 if any(k == pfx or k.startswith(pfx + ".") for pfx in _AGENT_MODULE_PREFIXES)]
    for k in to_remove:
        del sys.modules[k]
    # also purge bare native lambda module names (assemble/draft/check/finalize/hitl_notify/strands_agent)
    for k in ("assemble", "draft", "check", "finalize", "hitl_notify", "strands_agent"):
        sys.modules.pop(k, None)
    if agent_dir in sys.path:
        sys.path.remove(agent_dir)
    sys.path.insert(0, agent_dir)


def pytest_collect_file(parent, file_path):
    agent_dir = _agent_dir_for(str(file_path))
    if agent_dir and agent_dir != _last_agent_dir:
        _flush_and_set(agent_dir)


def pytest_runtest_setup(item):
    agent_dir = _agent_dir_for(str(item.fspath))
    if agent_dir and agent_dir != _last_agent_dir:
        _flush_and_set(agent_dir)
