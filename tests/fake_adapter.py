"""A tiny in-memory adapter that exercises the planner and the safety gates."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from tools.crm.base import (
    Adapter,
    Change,
    Failure,
    Plan,
    Result,
    State,
    StateField,
    StateObject,
    StatePipeline,
    StateRelationship,
    StateStage,
)
from tools.crm.planner import plan_changes
from tools.crm.safety import Mode, check_gates
from tools.design import Design

PLATFORM = "attio"


def state_matching(design: Design, platform: str = PLATFORM) -> State:
    """Build the live state a perfect build of `design` would have. Core things are native."""
    objects = tuple(
        StateObject(o.key, o.label, native=o.kind == "core") for o in design.objects
    )
    fields = tuple(
        StateField(
            f.object, f.key, f.type, f.label,
            options=tuple((o.key, o.label) for o in f.options),
            native=platform in f.native,
        )
        for f in design.fields
    )
    rels = tuple(
        StateRelationship(r.key, r.from_object, r.to_object, r.cardinality, native=platform in r.native)
        for r in design.relationships
    )
    pipes = tuple(
        StatePipeline(
            p.object, p.key, p.name,
            tuple(StateStage(s.key, s.label, s.type, s.probability) for s in p.stages),
        )
        for p in design.pipelines
    )
    return State(platform, objects, fields, rels, pipes)


def build_payload(kind: str, target: str, context: dict[str, Any]) -> dict[str, Any]:
    """The fake payload builder: just records what was asked."""
    return {"kind": kind, "target": target}


class FakeAdapter(Adapter):
    """Holds a State in memory. `apply` records calls; set `fail_on` to a target to simulate an API error."""

    platform = PLATFORM

    def __init__(self, state: State, *, mode: Mode | None = None, fail_on: str | None = None) -> None:
        self.state = state
        self.mode = mode or Mode(dry_run=True, production=False, allow_review=False)
        self.fail_on = fail_on
        self.calls: list[Change] = []

    def read_state(self) -> State:
        return self.state

    def plan(self, design: Design, state: State) -> Plan:
        return plan_changes(design, state, build_payload, target="sandbox")

    def apply(self, plan: Plan, *, dry_run: bool = True) -> Result:
        runnable, held = check_gates(plan, replace(self.mode, dry_run=dry_run))
        if dry_run:
            return Result(applied=(), remaining=runnable + held, dry_run=True)
        applied: list[Change] = []
        for i, change in enumerate(runnable):
            if change.target == self.fail_on:
                return Result(
                    tuple(applied), (Failure(change, "400 bad request"),),
                    runnable[i + 1:] + held, dry_run=False,
                )
            self.calls.append(change)
            applied.append(change)
        return Result(tuple(applied), (), held, dry_run=False)
