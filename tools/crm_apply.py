"""Apply a saved plan to a CRM. A dry run unless you pass --execute.

    uv run python -m tools.crm_apply plan.json --client acme
    uv run python -m tools.crm_apply plan.json --client acme --execute
    uv run python -m tools.crm_apply plan.json --client acme --execute --allow-review
    uv run python -m tools.crm_apply plan.json --client acme --execute --production

Safety: needs_review changes are held unless --allow-review; destructive changes never run;
--production needs --execute and typing the account name. Before each change the live state is
read again and a change already in place is skipped. The run stops at the first failure and
reports applied, failed and remaining. Every run is logged, redacted, to
clients/<client>/build/apply-log/<timestamp>.json.
Exit codes: 0 done, 1 a change failed, 2 refused or error.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

if __name__ == "__main__":  # pragma: no cover - allow `python tools/crm_apply.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.cli_common import AdapterFactory, default_factory, load_env, secret_values
from tools.crm.base import Adapter, Change, Failure, Plan, State
from tools.crm.registry import RegistryError
from tools.crm.safety import (
    Mode,
    SafetyError,
    check_gates,
    confirm_production,
    redact,
    redact_data,
    resolve_mode,
    write_apply_log,
)
from tools.design import PLATFORMS, REPO_ROOT, DesignError, load_design


def is_satisfied(change: Change, state: State) -> bool:
    """True when live state already shows an additive change. Other kinds return False.

    Rename, update, reorder and remove kinds cannot be judged from the target alone; pass
    `--design` to `crm_apply` to re-plan instead.
    """
    parts = change.target.split(".")
    if change.kind == "add_object":
        return any(o.key == change.target for o in state.objects)
    if change.kind == "add_relationship":
        return any(r.key == change.target for r in state.relationships)
    if change.kind == "add_pipeline" and len(parts) == 2:
        return any((p.object, p.key) == (parts[0], parts[1]) for p in state.pipelines)
    if change.kind == "add_stage" and len(parts) == 3:
        return any(
            (p.object, p.key) == (parts[0], parts[1]) and any(s.key == parts[2] for s in p.stages)
            for p in state.pipelines
        )
    if change.kind == "add_field" and len(parts) == 2:
        return any((f.object, f.key) == (parts[0], parts[1]) for f in state.fields)
    if change.kind == "add_option" and len(parts) == 3:
        return any(
            (f.object, f.key) == (parts[0], parts[1]) and any(k == parts[2] for k, _ in f.options)
            for f in state.fields
        )
    return False


@dataclass
class Report:
    """What an apply run did."""

    dry_run: bool
    applied: list[Change] = field(default_factory=list)
    skipped: list[Change] = field(default_factory=list)
    failed: list[Failure] = field(default_factory=list)
    remaining: list[Change] = field(default_factory=list)
    held: list[Change] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Plain dict for the log."""
        from dataclasses import asdict

        return {
            "dry_run": self.dry_run,
            "applied": [asdict(c) for c in self.applied],
            "already_satisfied": [asdict(c) for c in self.skipped],
            "failed": [{"change": asdict(f.change), "error": f.error} for f in self.failed],
            "remaining": [asdict(c) for c in self.remaining],
            "held_for_review": [asdict(c) for c in self.held],
        }


def run_plan(
    plan: Plan,
    adapter: Adapter,
    mode: Mode,
    *,
    confirm: Callable[[str], None] | None = None,
    design_path: Path | None = None,
) -> Report:
    """Apply `plan` through `adapter` under `mode`. Raises `SafetyError` when a gate refuses."""
    runnable, held = check_gates(plan, mode, confirm=confirm)
    report = Report(dry_run=mode.dry_run, held=list(held))
    if hasattr(adapter, "mode"):  # the CLI has already cleared these changes
        adapter.mode = replace(adapter.mode, dry_run=mode.dry_run, allow_review=mode.allow_review)

    def pending(change: Change, state: State) -> bool:
        if design_path is not None:
            design = load_design(design_path)
            replanned = {(c.kind, c.target) for c in adapter.plan(design, state).changes}
            return (change.kind, change.target) in replanned
        return not is_satisfied(change, state)

    if mode.dry_run:
        state = adapter.read_state()
        todo = []
        for change in runnable:
            (todo if pending(change, state) else report.skipped).append(change)
        result = adapter.apply(Plan(plan.platform, plan.target, tuple(todo)), dry_run=True)
        if result.failed:
            report.failed = list(result.failed)
        report.remaining = list(todo)
        return report

    for i, change in enumerate(runnable):
        state = adapter.read_state()  # re-check live state before every change
        if not pending(change, state):
            report.skipped.append(change)
            continue
        result = adapter.apply(Plan(plan.platform, plan.target, (change,)), dry_run=False)
        if result.failed:
            report.failed = list(result.failed)
            report.remaining = list(runnable[i + 1 :])
            return report
        # An adapter that found the change already in place reports it in `skipped`; do not log it as applied.
        if change in getattr(adapter, "skipped", ()):
            report.skipped.append(change)
        else:
            report.applied.append(change)
    return report


def render_report(report: Report) -> str:
    """Readable summary of a run."""
    lines = [("DRY RUN: nothing was changed. Pass --execute to apply." if report.dry_run else "EXECUTED")]
    rows = [
        ("Would apply", report.remaining) if report.dry_run else ("Applied", report.applied),
        ("Already in place (skipped)", report.skipped),
        ("Held for review (need --allow-review)", report.held),
    ]
    if not report.dry_run:
        rows.append(("Remaining (not attempted)", report.remaining))
    for title, items in rows:
        lines.append(f"{title}: {len(items)}")
        lines += [f"  - [{c.kind}] {c.summary}" for c in items]
    lines.append(f"Failed: {len(report.failed)}")
    for f in report.failed:
        lines.append(f"  - [{f.change.kind}] {f.change.summary}")
        lines.append(f"    error: {redact(f.error)}")
    return "\n".join(lines) + "\n"


def main(
    argv: list[str] | None = None,
    *,
    adapter_factory: AdapterFactory | None = None,
    env: Mapping[str, str] | None = None,
) -> int:
    """CLI entry point. Returns the exit code."""
    parser = argparse.ArgumentParser(prog="crm_apply", description=__doc__.split("\n")[0])
    parser.add_argument("plan", type=Path, help="plan JSON saved by crm_plan")
    parser.add_argument("--platform", choices=PLATFORMS, help="default: the platform in the plan")
    parser.add_argument("--target", help="default: the target in the plan")
    parser.add_argument("--execute", action="store_true", help="really make the changes")
    parser.add_argument("--production", action="store_true", help="target a live account (needs --execute)")
    parser.add_argument("--allow-review", action="store_true", help="also apply needs_review changes")
    parser.add_argument("--client", help="client folder name, for the apply log")
    parser.add_argument("--clients-dir", type=Path, default=REPO_ROOT / "clients", help=argparse.SUPPRESS)
    parser.add_argument("--design", type=Path, help="re-plan against this design before each change")
    args = parser.parse_args(argv)

    environment = env if env is not None else load_env()
    secrets = secret_values(environment)
    try:
        plan = Plan.from_json(args.plan.read_text(encoding="utf-8"))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"error: cannot read plan {args.plan}: {type(exc).__name__}", file=sys.stderr)
        return 2
    try:
        mode = resolve_mode(execute=args.execute, production=args.production, allow_review=args.allow_review)
        if args.execute and not args.client:
            raise SafetyError("--execute needs --client so the run can be logged.")
        platform = args.platform or plan.platform
        target = args.target or plan.target
        plan = replace(plan, platform=platform, target=target)
        # Only a target the user typed goes to the adapter. The plan's target is a display name
        # (Attio: the workspace name) and need not equal ATTIO_TARGET or HUBSPOT_TARGET.
        adapter = (adapter_factory or default_factory)(platform, environment, args.target, mode.production)
        report = run_plan(plan, adapter, mode, confirm=confirm_production, design_path=args.design)
    except (SafetyError, RegistryError, DesignError) as exc:
        print(f"refused: {redact(str(exc), secrets)}", file=sys.stderr)
        return 2

    text = redact(render_report(report), secrets)
    print(text, end="")
    if args.client:
        record = {
            "time": datetime.now(timezone.utc).isoformat(),
            "platform": platform,
            "target": target,
            "executed": not mode.dry_run,
            "production": mode.production,
            "allow_review": mode.allow_review,
            "plan_file": str(args.plan),
            **report.to_dict(),
        }
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        log = write_apply_log(
            args.clients_dir / args.client / "build" / "apply-log",
            f"{stamp}.json",
            json.dumps(redact_data(record, secrets), indent=2, ensure_ascii=False) + "\n",
            secrets,
        )
        print(f"Logged to {log}")
    return 1 if report.failed else 0


if __name__ == "__main__":
    sys.exit(main())
