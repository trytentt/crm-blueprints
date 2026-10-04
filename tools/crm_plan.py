"""Compare a design with a live CRM and save the plan. Never writes to the CRM.

    uv run python -m tools.crm_plan clients/acme/design.yaml --platform hubspot --out plan.json

Prints the plan grouped by risk, with manual steps. Apply it with `tools.crm_apply`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Mapping

if __name__ == "__main__":  # pragma: no cover - allow `python tools/crm_plan.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.cli_common import AdapterFactory, add_platform_args, default_factory, load_env
from tools.crm.registry import RegistryError
from tools.crm.render import render_plan
from tools.crm.safety import SafetyError, redact
from tools.design import DesignError, load_design


def main(
    argv: list[str] | None = None,
    *,
    adapter_factory: AdapterFactory | None = None,
    env: Mapping[str, str] | None = None,
) -> int:
    """CLI entry point. Returns the exit code."""
    parser = argparse.ArgumentParser(prog="crm_plan", description=__doc__.split("\n")[0])
    parser.add_argument("design", type=Path, help="design.yaml or a blueprint folder")
    add_platform_args(parser)
    parser.add_argument("--out", type=Path, help="save the plan as JSON here")
    args = parser.parse_args(argv)
    environment = env if env is not None else load_env()
    try:
        design = load_design(args.design)
        adapter = (adapter_factory or default_factory)(args.platform, environment, args.target, False)
        plan = adapter.plan(design, adapter.read_state())
    except DesignError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except (RegistryError, SafetyError) as exc:
        print(f"error: {redact(str(exc))}", file=sys.stderr)
        return 2
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(plan.to_json(), encoding="utf-8")
    print(render_plan(plan), end="")
    if args.out:
        print(f"Saved plan to {args.out}. Nothing was changed in the CRM.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
