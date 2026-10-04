"""Readable text for a Plan: changes grouped by risk, then manual steps."""

from __future__ import annotations

from tools.crm.base import Plan

RISK_TITLES = (
    ("safe", "SAFE (applied automatically)"),
    ("needs_review", "NEEDS REVIEW (applied only with --allow-review)"),
    ("destructive", "DESTRUCTIVE (never applied by this tool)"),
)


def render_plan(plan: Plan, heading: str = "Plan") -> str:
    """Render changes grouped by risk, then every manual step with its risk."""
    lines = [f"{heading}: {plan.platform}, target {plan.target or '(default)'}"]
    if plan.is_empty:
        lines.append("Nothing to do.")
        return "\n".join(lines) + "\n"
    for risk, title in RISK_TITLES:
        changes = [c for c in plan.changes if c.risk == risk]
        if not changes:
            continue
        lines += ["", f"{title}: {len(changes)}"]
        for i, c in enumerate(changes, 1):
            lines.append(f"  {i}. [{c.kind}] {c.summary}")
    if plan.manual_steps:
        lines += ["", f"MANUAL STEPS: {len(plan.manual_steps)}"]
        for m in plan.manual_steps:
            tag = "DESTRUCTIVE" if m.risk == "destructive" else m.risk
            lines.append(f"  - [{tag}] {m.title}")
            lines.append(f"      why: {m.reason}")
            lines.append(f"      where: {m.ui_path}")
            lines.append(f"      done when: {m.done_when}")
            if m.instructions:
                lines.append(f"      how: {m.instructions}")
    lines += ["", f"{len(plan.changes)} automatic change(s), {len(plan.manual_steps)} manual step(s)."]
    return "\n".join(lines) + "\n"
