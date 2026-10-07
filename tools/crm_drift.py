"""Report differences between a design and a live CRM. Read-only.

    uv run python -m tools.crm_drift clients/acme/design.yaml --platform attio

Exit 0 when live matches the design, 1 when there is drift (missing items, differences, or extras
in live that the design does not have), 2 on an error.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Mapping

if __name__ == "__main__":  # pragma: no cover - allow `python tools/crm_drift.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.cli_common import AdapterFactory, add_platform_args, default_factory, load_env
from tools.crm.base import Plan
from tools.crm.registry import RegistryError
from tools.crm.render import render_plan
from tools.crm.safety import SafetyError, redact
from tools.design import DesignError, load_design


def drift_plan(plan: Plan) -> Plan:
    """Keep only what counts as drift: every change, destructive manual steps (extras in live), and manual steps
    that stand for a difference the adapter could not close itself (`ManualStep.drift`)."""
    return Plan(
        plan.platform, plan.target, plan.changes,
        tuple(m for m in plan.manual_steps if m.risk == "destructive" or m.drift),
    )


def main(
    argv: list[str] | None = None,
    *,
    adapter_factory: AdapterFactory | None = None,
    env: Mapping[str, str] | None = None,
) -> int:
    """CLI entry point. Returns the exit code."""
    parser = argparse.ArgumentParser(prog="crm_drift", description=__doc__.split("\n")[0])
    parser.add_argument("design", type=Path, help="design.yaml or a blueprint folder")
    add_platform_args(parser)
    args = parser.parse_args(argv)
    environment = env if env is not None else load_env()
    try:
        design = load_design(args.design)
        adapter = (adapter_factory or default_factory)(args.platform, environment, args.target, False)
        drift = drift_plan(adapter.plan(design, adapter.read_state()))
    except DesignError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except (RegistryError, SafetyError) as exc:
        print(f"error: {redact(str(exc))}", file=sys.stderr)
        return 2
    if drift.is_empty:
        print(f"No drift: live {args.platform} matches the design.")
        return 0
    print(render_plan(drift, heading="Drift"), end="")
    print("DESTRUCTIVE items are extras in live that the design lacks, or changes that cannot be made in place.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
