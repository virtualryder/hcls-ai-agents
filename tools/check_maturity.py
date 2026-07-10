#!/usr/bin/env python3
"""check_maturity — drift-checker for MATURITY.yaml's declared test count.

MATURITY.yaml is the single source of truth for this repo's maturity claims.
One of those is `tests.offline_total`: the number of automated tests that pass
offline. This tool closes the loop by running the repo's own harness
(scripts/run_all_tests.sh — each of the nine agents reuses the `agent`/`tools`
package names, so they must run in separate processes) and comparing the ACTUAL
green total to the DECLARED `offline_total`.

Usage:
    python tools/check_maturity.py            # verify; exit 1 on drift
    python tools/check_maturity.py --update   # rewrite offline_total to actual

Stdlib-only. Resolves the repo root as the parent of tools/, and runs the suite
with the interpreter that invoked it (sys.executable) so it honours the venv.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATURITY = os.path.join(REPO_ROOT, "MATURITY.yaml")
RUNNER = os.path.join(REPO_ROOT, "scripts", "run_all_tests.sh")

_OFFLINE_TOTAL_RE = re.compile(r"^(\s*offline_total:\s*)(\d+)(.*)$", re.MULTILINE)
# run_all_tests.sh prints:  "✅ ALL GREEN — 575 tests passed across N suites ..."
_TOTAL_RE = re.compile(r"(\d+)\s+tests\s+passed", re.I)


def read_maturity() -> str:
    with open(MATURITY, encoding="utf-8") as fh:
        return fh.read()


def declared_total(text: str) -> int:
    m = _OFFLINE_TOTAL_RE.search(text)
    if not m:
        raise SystemExit("check_maturity: could not find `offline_total:` in MATURITY.yaml")
    return int(m.group(2))


def actual_total() -> int:
    env = dict(os.environ, PYTHON=sys.executable)
    proc = subprocess.run(
        ["bash", RUNNER], cwd=REPO_ROOT, env=env,
        capture_output=True, text=True,
    )
    out = proc.stdout + proc.stderr
    m = _TOTAL_RE.search(out)
    if not m:
        sys.stderr.write(out)
        raise SystemExit("check_maturity: could not parse a '<N> tests passed' total from run_all_tests.sh")
    if proc.returncode != 0:
        sys.stderr.write(out)
        raise SystemExit("check_maturity: the suite did not pass cleanly (see output above)")
    return int(m.group(1))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--update", action="store_true", help="rewrite offline_total to the actual count")
    args = ap.parse_args()

    text = read_maturity()
    declared = declared_total(text)
    actual = actual_total()

    print(f"MATURITY.yaml offline_total (declared): {declared}")
    print(f"run_all_tests.sh green total (actual):  {actual}")

    if declared == actual:
        print("OK: declared test count matches the passing suite.")
        return 0

    if args.update:
        new = _OFFLINE_TOTAL_RE.sub(lambda m: f"{m.group(1)}{actual}{m.group(3)}", text, count=1)
        with open(MATURITY, "w", encoding="utf-8") as fh:
            fh.write(new)
        print(f"UPDATED offline_total {declared} -> {actual} in MATURITY.yaml")
        return 0

    print(f"DRIFT: MATURITY.yaml says {declared} but the suite has {actual}. "
          f"Run `python tools/check_maturity.py --update` (and align docs).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
