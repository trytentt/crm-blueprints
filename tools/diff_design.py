"""Compare two versions of a design and print what changed, with the same risk classes as a plan.

    uv run python -m tools.diff_design old/design.yaml new/design.yaml
    uv run python -m tools.diff_design HEAD~1:clients/acme/design.yaml clients/acme/design.yaml

An argument is a path, or `<git ref>:<path>` to read a committed version. Removing a field shows
as DESTRUCTIVE. Exit 0 normally; with --exit-code, 1 when the designs differ.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

if __name__ == "__main__":  # pragma: no cover - allow `python tools/diff_design.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.crm.base import Plan
from tools.crm.design_state import state_from_design
from tools.crm.planner import plan_changes
from tools.crm.render import render_plan
from tools.design import REPO_ROOT, Design, DesignError, load_design


def _payload(kind: str, target: str, context: dict) -> dict:
    return {}


def diff_designs(old: Design, new: Design) -> Plan:
    """The plan that would turn a CRM built from `old` into one built from `new`."""
    return plan_changes(new, state_from_design(old), _payload, target=f"{old.name} -> {new.name}")


def load_version(spec: str) -> Design:
    """Load a design from a path, or from `<git ref>:<path>` (path relative to the repo root)."""
    path = Path(spec)
    if path.exists():
        return load_design(path)
    ref, sep, rel = spec.partition(":")
    if not sep or not ref or not rel:
        raise DesignError(f"{spec}: not a file, and not of the form <git ref>:<path>")
    result = subprocess.run(
        ["git", "show", f"{ref}:{rel}"], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise DesignError(f"{spec}: git could not read it ({result.stderr.strip()})")
    with tempfile.TemporaryDirectory() as tmp:
        file = Path(tmp) / "design.yaml"
        file.write_text(result.stdout, encoding="utf-8")
        return load_design(file)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns the exit code."""
    parser = argparse.ArgumentParser(prog="diff_design", description=__doc__.split("\n")[0])
    parser.add_argument("old", help="older design: a path or <git ref>:<path>")
    parser.add_argument("new", help="newer design: a path or <git ref>:<path>")
    parser.add_argument("--exit-code", action="store_true", help="exit 1 when the designs differ")
    args = parser.parse_args(argv)
    try:
        plan = diff_designs(load_version(args.old), load_version(args.new))
    except DesignError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(render_plan(plan, heading="Design changes"), end="")
    return 1 if args.exit_code and not plan.is_empty else 0


if __name__ == "__main__":
    sys.exit(main())
