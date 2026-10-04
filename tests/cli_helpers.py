"""Shared setup for the CLI tests."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from tests.fake_adapter import StatefulFakeAdapter, state_matching
from tools.crm.base import Plan, State
from tools.design import Design


def behind_state(design: Design) -> State:
    """Live state missing one field, one option and one stage, with one label drifted.

    That gives plan: add_field (safe), add_option (safe), add_stage (safe), rename_field (needs_review).
    """
    s = state_matching(design)
    fields = []
    for f in s.fields:
        if (f.object, f.key) == ("deal", "next_step_date"):
            continue
        if (f.object, f.key) == ("deal", "lost_reason"):
            f = replace(f, options=tuple(o for o in f.options if o[0] != "timing"))
        if (f.object, f.key) == ("project", "status"):
            f = replace(f, label="Old status label")
        fields.append(f)
    pipes = tuple(
        replace(p, stages=tuple(st for st in p.stages if st.key != "lost")) for p in s.pipelines
    )
    return replace(s, fields=tuple(fields), pipelines=pipes)


def factory_for(adapter):
    """An adapter_factory that records how it was called and returns `adapter`."""
    calls: list[tuple] = []

    def factory(platform, env, target, production):
        calls.append((platform, target, production))
        return adapter

    factory.calls = calls  # type: ignore[attr-defined]
    return factory


def make_plan_file(design: Design, tmp_path: Path, state: State | None = None) -> tuple[Path, StatefulFakeAdapter]:
    adapter = StatefulFakeAdapter(state or behind_state(design))
    plan = adapter.plan(design, adapter.read_state())
    path = tmp_path / "plan.json"
    path.write_text(plan.to_json(), encoding="utf-8")
    return path, adapter


def load_plan(path: Path) -> Plan:
    return Plan.from_json(path.read_text(encoding="utf-8"))


def read_logs(clients: Path, client: str) -> list[dict]:
    folder = clients / client / "build" / "apply-log"
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(folder.glob("*.json"))]
