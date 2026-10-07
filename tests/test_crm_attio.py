"""Attio adapter: state mapping, planning, applying, safety. No network except the `live` test."""

from __future__ import annotations

import os
from dataclasses import replace

import pytest

from tests.attio_stub import FakeAttio, FixtureSession, Resp, error, load_fixture
from tools.crm import attio as mod
from tools.crm.attio import AttioAdapter, make_adapter
from tools.crm.base import Plan
from tools.crm.safety import SafetyError
from tools.design import load_design

TOKEN = "atk_test_0123456789abcdef"


@pytest.fixture
def design(write_design, design_dict):
    return load_design(write_design(design_dict))


def adapter(session, **kw) -> AttioAdapter:
    kw.setdefault("production", False)
    kw.setdefault("sleep", lambda s: None)
    return AttioAdapter(TOKEN, session=session, label="sandbox", **kw)


def fixture_adapter(**kw) -> AttioAdapter:
    return adapter(FixtureSession(load_fixture("workspace_basic.json")), **kw)


def kinds(plan):
    return [c.kind for c in plan.changes]


# --- read_state --------------------------------------------------------------------------------


def test_read_state_without_design_uses_slugs():
    a = fixture_adapter()
    state = a.read_state()
    assert a.workspace.name == "Example Test Workspace" and a.workspace.slug == "example-test"
    assert {o.key for o in state.objects} == {"people", "companies", "deals", "projects"}
    natives = {o.key for o in state.objects if o.native}
    assert natives == {"people", "companies", "deals"}
    assert {p.key for p in state.pipelines} == {"sales"}


def test_read_state_maps_to_design_keys(design):
    state = fixture_adapter().read_state(design)
    assert {o.key for o in state.objects} == {"person", "company", "deal", "project"}
    fields = {(f.object, f.key): f for f in state.fields}
    assert fields[("deal", "next_step_date")].type == "date"
    assert fields[("deal", "amount")].native  # attio slug `value`
    assert ("project", "old_field") not in fields  # archived is not live
    status = fields[("project", "status")]
    assert status.options == (("not_started", "Not started"), ("live", "Live"))
    assert ("deal", "lost_reason") in fields and fields[("deal", "lost_reason")].options == (
        ("price", "Price"), ("timing", "Timing"))  # archived option left out
    (rel,) = state.relationships
    assert (rel.key, rel.from_object, rel.to_object, rel.cardinality) == (
        "project_company", "project", "company", "many_to_one")
    (pl,) = state.pipelines
    assert (pl.object, pl.key) == ("deal", "sales")
    assert [(s.key, s.type) for s in pl.stages] == [("discovery", "open"), ("won", "won"), ("lost", "lost")]
    assert [s.probability for s in pl.stages] == [None] * 3


def test_inactive_token_is_refused():
    a = adapter(FixtureSession({"GET /v2/self": {"active": False}}))
    with pytest.raises(SafetyError, match="not active"):
        a.read_state()


def test_read_state_uses_show_archived_and_sends_bearer_only_in_header():
    s = FixtureSession(load_fixture("workspace_basic.json"))
    a = adapter(s)
    a.read_state()
    attr_calls = [c for c in s.calls if c[1].endswith("/attributes")]
    assert attr_calls and all(c[2]["show_archived"] == "true" for c in attr_calls)
    assert all(TOKEN not in str(c) for c in s.calls)


# --- plan --------------------------------------------------------------------------------------


def test_plan_matching_state_has_zero_changes(design):
    a = fixture_adapter()
    plan = a.plan(design, a.read_state())
    assert plan.changes == ()
    assert plan.target == "Example Test Workspace"


def test_plan_against_empty_workspace_is_in_build_order(design):
    fake = FakeAttio()
    a = adapter(fake)
    plan = a.plan(design, a.read_state())
    order = [c.kind for c in plan.changes]
    ranks = [{"add_object": 0, "add_relationship": 1, "add_pipeline": 2, "add_stage": 2, "add_field": 3}[k] for k in order]
    assert ranks == sorted(ranks)
    assert order[0] == "add_object" and "add_relationship" in order and "add_pipeline" in order
    assert plan.manual_steps  # workflows, views, permissions
    titles = [m.title for m in plan.manual_steps]
    assert any("Workflow" in t for t in titles) and any("View" in t for t in titles)
    assert "Set roles and access" in titles
    assert any(c.source_url.startswith("https://") for c in plan.changes)


def test_deals_step_only_when_deals_missing(design):
    a = adapter(FakeAttio(deals=False))
    assert "Enable the Deals object" in [m.title for m in a.plan(design, a.read_state()).manual_steps]
    b = adapter(FakeAttio(deals=True))
    assert "Enable the Deals object" not in [m.title for m in b.plan(design, b.read_state()).manual_steps]


def run(fake, design, *, dry=False):
    a = adapter(fake)
    plan = a.plan(design, a.read_state())
    return a, plan, a.apply(plan, dry_run=dry)


def test_apply_then_replan_is_zero_changes(design):
    fake = FakeAttio()
    a, plan, result = run(fake, design)
    assert result.ok and not result.remaining and len(result.applied) == len(plan.changes) > 0
    assert fake.titles("lists", "sales", "stage", "statuses") == ["Discovery", "Won", "Lost"]
    again = adapter(fake)
    assert again.plan(design, again.read_state()).changes == ()


def test_reference_blueprint_applies_and_replans_to_zero():
    d = load_design("blueprints/b2b-saas-sales-led")
    fake = FakeAttio()
    _, plan, result = run(fake, d)
    assert result.ok, result.failed
    again = adapter(fake)
    assert again.plan(d, again.read_state()).changes == ()


def test_second_apply_of_same_plan_skips_everything(design):
    fake = FakeAttio()
    a, plan, _ = run(fake, design)
    before = len(fake.writes)
    result = a.apply(plan, dry_run=False)
    assert result.ok and len(fake.writes) == before
    assert len(a.skipped) == len(plan.changes)


# --- apply: dry run, errors, retries -------------------------------------------------------------


def test_dry_run_makes_no_http_call_at_all(design):
    fake = FakeAttio()
    a = adapter(fake)
    plan = a.plan(design, a.read_state())
    calls = len(fake.calls)
    result = a.apply(plan)  # default is dry
    assert result.dry_run and result.applied == () and result.remaining == plan.changes
    assert len(fake.calls) == calls


def test_409_slug_conflict_is_treated_as_exists_and_verified(design):
    fake = FakeAttio()
    a = adapter(fake)
    plan = a.plan(design, a.read_state())
    # Another session creates the project object between the pre-check and the POST.
    first = plan.changes[0]
    slug = first.payload["requests"][0]["body"]["data"]["api_slug"]
    other = adapter(fake)
    other.apply(Plan(plan.platform, plan.target, (first,)), dry_run=False)
    original = a._current
    state = {"n": 0}

    def stale_first_read(req):
        state["n"] += 1
        return None if state["n"] == 1 else original(req)

    a._current = stale_first_read
    result = a.apply(Plan(plan.platform, plan.target, (first,)), dry_run=False)
    assert result.ok and result.applied == (first,)
    assert ("POST", "/v2/objects") in [(c[0], c[1]) for c in fake.calls[-4:]] and slug in fake.objects


def test_409_on_archived_item_fails_with_explanation(design):
    fake = FakeAttio()
    a = adapter(fake)
    plan = a.plan(design, a.read_state())
    run_obj = Plan(plan.platform, plan.target, (plan.changes[0],))
    a.apply(run_obj, dry_run=False)
    fake.objects["projects"]["is_archived"] = True
    result = adapter(fake).apply(run_obj, dry_run=False)
    assert not result.ok and "archived" in result.failed[0].error


def test_429_is_retried_with_retry_after(design):
    fake = FakeAttio()
    waits = []
    a = adapter(fake, sleep=waits.append)
    plan = a.plan(design, a.read_state())
    first = plan.changes[0]
    path = first.payload["requests"][0]["path"]
    body = load_fixture("errors.json")["rate_limit"]
    fake.rate_limit[f"POST {path}"] = [Resp(429, body, {"Retry-After": "3"}), Resp(429, body, {"Retry-After": "2"})]
    result = a.apply(Plan(plan.platform, plan.target, (first,)), dry_run=False)
    assert result.ok and waits == [3.0, 2.0]


def test_429_retries_are_bounded(design):
    fake = FakeAttio()
    waits = []
    a = adapter(fake, sleep=waits.append)
    plan = a.plan(design, a.read_state())
    first = plan.changes[0]
    path = first.payload["requests"][0]["path"]
    body = load_fixture("errors.json")["rate_limit"]
    fake.rate_limit[f"POST {path}"] = [Resp(429, body) for _ in range(20)]
    result = a.apply(Plan(plan.platform, plan.target, (first,)), dry_run=False)
    assert not result.ok and result.failed[0].error.startswith("429")
    assert len(waits) == mod.MAX_RETRIES_429


def test_retry_after_parses_seconds_and_http_dates():
    from datetime import datetime, timezone

    assert mod.parse_retry_after("4") == 4.0
    now = datetime(2026, 10, 4, 12, 0, 0, tzinfo=timezone.utc)
    assert mod.parse_retry_after("Sun, 04 Oct 2026 12:00:07 GMT", now=now) == 7.0
    assert mod.parse_retry_after(None) is None and mod.parse_retry_after("soon") is None


def test_stops_on_first_failure_and_reports_applied_failed_remaining(design):
    fake = FakeAttio()
    a = adapter(fake)
    plan = a.plan(design, a.read_state())
    assert len(plan.changes) > 3
    bad = plan.changes[2]
    path = bad.payload["requests"][0]["path"]
    fake.fail[f"POST {path}"] = error(400, "quota_exceeded", "Object limit reached for this plan.")
    result = a.apply(plan, dry_run=False)
    assert result.applied == plan.changes[:2]
    assert len(result.failed) == 1 and result.failed[0].change == bad
    assert "quota_exceeded" in result.failed[0].error and result.failed[0].error.startswith("400")
    assert result.remaining == plan.changes[3:]
    assert TOKEN not in result.failed[0].error
    sent = [c[1] for c in fake.writes]
    assert sent.count(path) == 1 and sent[-1] == path  # nothing was sent after the failing request
    assert len(sent) == sum(len(c.payload["requests"]) for c in plan.changes[:2]) + 1


def test_no_delete_is_ever_issued(design):
    fake = FakeAttio()
    run(fake, design)
    assert "DELETE" not in fake.methods
    with pytest.raises(ValueError):
        adapter(fake)._call("DELETE", "/v2/objects/projects")
    assert "DELETE" not in fake.methods and "DELETE" not in mod.ALLOWED_METHODS


def test_removals_are_archived_by_patch_never_deleted(design):
    fake = FakeAttio()
    run(fake, design)
    pruned = replace(design, fields=tuple(
        replace(f, options=f.options[:1]) if f.key == "status" else f for f in design.fields))
    a = adapter(fake)
    plan = a.plan(pruned, a.read_state())
    assert [c.kind for c in plan.changes] == ["remove_option"] and plan.changes[0].risk == "needs_review"
    result = a.apply(plan, dry_run=False)
    assert result.ok and "DELETE" not in fake.methods
    assert fake.writes[-1][0] == "PATCH" and fake.writes[-1][3] == {"data": {"is_archived": True}}
    assert fake.titles("objects", "projects", "status", "options", archived=True) == ["Live"]


def test_reorder_becomes_a_manual_step(design):
    fake = FakeAttio()
    run(fake, design)
    stages = design.pipelines[0].stages
    swapped = replace(design, pipelines=(replace(design.pipelines[0], stages=(stages[1], stages[0], stages[2])),))
    a = adapter(fake)
    plan = a.plan(swapped, a.read_state())
    assert plan.changes == () and any(m.title.startswith("Reorder stages") for m in plan.manual_steps)


def test_destructive_change_is_refused(design):
    from dataclasses import replace as r

    a = adapter(FakeAttio())
    plan = a.plan(design, a.read_state())
    bad = Plan(plan.platform, plan.target, (r(plan.changes[0], risk="destructive"),))
    with pytest.raises(SafetyError):
        a.apply(bad, dry_run=False)


# --- gating ------------------------------------------------------------------------------------


def test_plan_for_another_workspace_is_refused(design):
    fake = FakeAttio()
    a = adapter(fake)
    plan = a.plan(design, a.read_state())
    wrong = Plan(plan.platform, "Someone Else", plan.changes)
    with pytest.raises(SafetyError, match="Someone Else"):
        a.apply(wrong, dry_run=False)
    assert fake.writes == []


def test_make_adapter_production_rules():
    env = {"ATTIO_ACCESS_TOKEN": TOKEN}
    assert make_adapter(env, target=None, production=False).production  # no ATTIO_TARGET
    test_env = {**env, "ATTIO_TARGET": "sandbox"}
    assert not make_adapter(test_env, target=None, production=False).production
    assert make_adapter(test_env, target=None, production=True).production
    with pytest.raises(SafetyError, match="does not match"):
        make_adapter(test_env, target="other", production=False)
    with pytest.raises(SafetyError, match="ATTIO_ACCESS_TOKEN"):
        make_adapter({}, target=None, production=False)
    assert TOKEN not in repr(make_adapter(env, target=None, production=False))


def test_unlabelled_workspace_cannot_be_written_without_production_flag(design):
    fake = FakeAttio()
    a = make_adapter({"ATTIO_ACCESS_TOKEN": TOKEN}, target=None, production=False, session=fake)
    plan = a.plan(design, a.read_state())
    with pytest.raises(SafetyError, match="treated as production"):
        a.apply(plan, dry_run=False)
    assert fake.writes == []
    ok = make_adapter({"ATTIO_ACCESS_TOKEN": TOKEN}, target=None, production=True, session=fake)
    assert ok.apply(plan, dry_run=False).ok


def test_every_api_function_names_its_source_url():
    names = ["_call", "_data", "_get_or_none", "identify", "_attributes", "_sub_items", "fetch_snapshot",
             "read_state", "plan", "_payload", "_current", "_check_existing", "_run_request", "_check_target",
             "apply"]
    for n in names:
        assert "https://" in (getattr(AttioAdapter, n).__doc__ or ""), n


def test_error_report_redacts_token(design):
    fake = FakeAttio()
    a = adapter(fake)
    plan = a.plan(design, a.read_state())
    path = plan.changes[0].payload["requests"][0]["path"]
    fake.fail[f"POST {path}"] = error(400, "validation_type", f"bad request for {TOKEN} by a@example.com")
    result = a.apply(plan, dry_run=False)
    assert TOKEN not in result.failed[0].error and "a@example.com" not in result.failed[0].error


# --- live ----------------------------------------------------------------------------------------


@pytest.mark.live
@pytest.mark.skipif(
    not (os.environ.get("ATTIO_ACCESS_TOKEN") and os.environ.get("ATTIO_TARGET")),
    reason="needs ATTIO_ACCESS_TOKEN and ATTIO_TARGET (a test workspace)",
)
def test_live_pull_plan_apply_replan_is_zero():
    d = load_design("blueprints/b2b-saas-sales-led")
    a = make_adapter(os.environ, target=None, production=False)
    assert not a.production
    plan = a.plan(d, a.read_state())
    result = a.apply(plan, dry_run=False)
    assert result.ok, result.failed
    again = make_adapter(os.environ, target=None, production=False)
    assert again.plan(d, again.read_state()).changes == ()
