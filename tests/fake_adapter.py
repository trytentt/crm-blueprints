"""A tiny in-memory adapter that exercises the planner and the safety gates."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from tools.crm.base import (
    Account,
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
from tools.crm.design_state import state_from_design
from tools.crm.planner import plan_changes
from tools.crm.safety import Mode, check_gates
from tools.design import Design

PLATFORM = "attio"
FAKE_ACCOUNT = Account("Fake Sandbox Ltd", "fake id 1")


def state_matching(design: Design, platform: str = PLATFORM) -> State:
    """Build the live state a perfect build of `design` would have. Core things are native."""
    return state_from_design(design, platform)


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
        self.account = FAKE_ACCOUNT

    def read_account(self) -> Account:
        return self.account

    def read_state(self) -> State:
        return self.state

    def plan(self, design: Design, state: State) -> Plan:
        return replace(plan_changes(design, state, build_payload, target="sandbox"), account=self.account.identity)

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


def rich_payload(kind: str, target: str, context: dict[str, Any]) -> dict[str, Any]:
    """A payload that carries enough for `StatefulFakeAdapter` to mutate its state."""
    out: dict[str, Any] = {"kind": kind, "target": target}
    if "object" in context:
        out["label"] = context["object"].label
    if "relationship" in context:
        r = context["relationship"]
        out.update(from_object=r.from_object, to_object=r.to_object, cardinality=r.cardinality)
    if "pipeline" in context:
        p = context["pipeline"]
        out.update(
            pipeline_name=p.name,
            stages=[[s.key, s.label, s.type, s.probability] for s in p.stages],
        )
    if "stage" in context:
        s = context["stage"]
        out["stage"] = [s.key, s.label, s.type, s.probability]
    if "field" in context:
        f = context["field"]
        out.update(
            label=f.label, type=f.type, field_options=[[o.key, o.label] for o in f.options],
        )
    if "option" in context:
        out["option"] = [context["option"].key, context["option"].label]
    return out


class StatefulFakeAdapter(FakeAdapter):
    """Like `FakeAdapter`, but a real apply changes `self.state`, so a re-plan sees the result.

    Handles the additive kinds and `rename_field`. Other kinds are recorded in `calls` only.
    """

    def plan(self, design: Design, state: State) -> Plan:
        return replace(plan_changes(design, state, rich_payload, target="sandbox"), account=self.account.identity)

    def apply(self, plan: Plan, *, dry_run: bool = True) -> Result:
        result = super().apply(plan, dry_run=dry_run)
        for change in result.applied:
            self.state = _mutate(self.state, change)
        return result


def _mutate(state: State, change: Change) -> State:
    p, t = change.payload, change.target
    if change.kind == "add_object":
        return replace(state, objects=state.objects + (StateObject(t, p["label"]),))
    if change.kind == "add_relationship":
        rel = StateRelationship(t, p["from_object"], p["to_object"], p["cardinality"])
        return replace(state, relationships=state.relationships + (rel,))
    if change.kind == "add_pipeline":
        obj, key = t.split(".")
        stages = tuple(StateStage(k, lbl, ty, pr) for k, lbl, ty, pr in p["stages"])
        pipe = StatePipeline(obj, key, p["pipeline_name"], stages)
        return replace(state, pipelines=state.pipelines + (pipe,))
    if change.kind == "add_stage":
        obj, key, _ = t.split(".")
        k, lbl, ty, pr = p["stage"]
        return replace(state, pipelines=tuple(
            replace(pl, stages=pl.stages + (StateStage(k, lbl, ty, pr),))
            if (pl.object, pl.key) == (obj, key) else pl
            for pl in state.pipelines
        ))
    if change.kind == "add_field":
        obj, key = t.split(".")
        fld = StateField(obj, key, p["type"], p["label"], tuple(tuple(o) for o in p["field_options"]))
        return replace(state, fields=state.fields + (fld,))
    if change.kind == "add_option":
        obj, key, _ = t.split(".")
        return replace(state, fields=tuple(
            replace(f, options=f.options + (tuple(p["option"]),))
            if (f.object, f.key) == (obj, key) else f
            for f in state.fields
        ))
    if change.kind == "rename_field":
        obj, key = t.split(".")
        return replace(state, fields=tuple(
            replace(f, label=p["label"]) if (f.object, f.key) == (obj, key) else f
            for f in state.fields
        ))
    return state
