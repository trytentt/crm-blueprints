"""HubSpot adapter: reading, planning, applying. No network: an in-memory HubSpot answers every call."""

from __future__ import annotations

import os
from dataclasses import replace

import pytest

from tests.hubspot_stub import V, FakeHubSpot, Resp, fixture
from tools.crm import hubspot as hsa
from tools.crm.base import Plan
from tools.crm.design_state import state_from_design
from tools.crm.planner import BUILD_RANK
from tools.crm.safety import Mode, SafetyError
from tools.design import REPO_ROOT, load_design
from tools.generators import hubspot as gen

TOKEN = "pat-eu1-00000000-aaaa-bbbb-cccc-111111111111"
BLUEPRINT = REPO_ROOT / "blueprints" / "b2b-saas-sales-led"


@pytest.fixture(scope="module")
def design():
    return load_design(BLUEPRINT)


@pytest.fixture
def hub() -> FakeHubSpot:
    return FakeHubSpot()


def make(hub: FakeHubSpot, *, production: bool = False, review: bool = False) -> hsa.HubSpotAdapter:
    ad = hsa.make_adapter(
        {"HUBSPOT_ACCESS_TOKEN": TOKEN, "HUBSPOT_TARGET": "test account"},
        target=None, production=production, session=hub, sleep=hub.sleeps.append,
    )
    ad.mode = Mode(dry_run=False, production=production, allow_review=review)
    return ad


def build(ad: hsa.HubSpotAdapter, design, **kw):
    plan = ad.plan(design, ad.read_state())
    return plan, ad.apply(plan, dry_run=False, **kw)


# --- reading ---------------------------------------------------------------------------------


def test_read_state_maps_native_and_core_names(hub):
    state = make(hub).read_state()
    objs = {o.key: o for o in state.objects}
    assert {k: objs[k].native for k in ("company", "person", "deal")} == {"company": True, "person": True, "deal": True}
    fields = {(f.object, f.key): f for f in state.fields}
    # HubSpot names come back as design keys, with the core model's type, and are marked native.
    for key in [("company", "name"), ("company", "employee_count"), ("person", "job_title"), ("deal", "name"), ("deal", "close_date")]:
        assert fields[key].native
    assert fields[("company", "employee_count")].type == "number"
    assert ("company", "numberofemployees") not in fields
    # the default pipeline exists on every account and is not offered for removal
    assert state.pipelines == ()


def test_read_state_after_build_has_design_keys(hub, design):
    ad = make(hub)
    build(ad, design)
    state = ad.read_state()
    fields = {(f.object, f.key): f for f in state.fields}
    assert fields[("subscription", "arr")].type == "currency"
    assert fields[("deal", "lost_reason")].type == "select"
    assert {k for k, _ in fields[("deal", "lost_reason")].options} == {o.key for o in design.get_field("deal", "lost_reason").options}
    assert {(p.object, p.key) for p in state.pipelines} == {(p.object, p.key) for p in design.pipelines}
    new = next(p for p in state.pipelines if p.key == "new_business")
    assert [s.key for s in new.stages][-2:] == ["closed_won", "closed_lost"]
    assert [s.type for s in new.stages][-2:] == ["won", "lost"]
    assert new.stages[1].probability == 20.0


@pytest.mark.parametrize("ftype", sorted(gen.TYPE_MAP))
def test_canonical_type_inverts_the_generator(ftype, design):
    from tools.design import FieldDef

    f = FieldDef("deal", "x", "X", ftype, "A field.", options=design.get_field("deal", "lost_reason").options
                 if ftype in ("select", "multi_select") else ())
    body = gen.property_body(design, f, group="g")
    assert hsa.canonical_type(body) == ftype


# --- planning --------------------------------------------------------------------------------


def test_empty_account_gives_ordered_creates(hub, design):
    ad = make(hub)
    plan = ad.plan(design, ad.read_state())
    ranks = [BUILD_RANK[c.kind] for c in plan.changes]
    assert ranks == sorted(ranks)
    kinds = [c.kind for c in plan.changes]
    assert kinds.count("add_object") == 2 and kinds.index("add_object") == 0
    assert "add_relationship" in kinds and "add_pipeline" in kinds and "add_field" in kinds
    assert all(c.risk == "safe" and c.source_url.startswith("https://") for c in plan.changes)
    # stage gates, views and workflows cannot go through the API
    titles = " ".join(m.title for m in plan.manual_steps)
    assert "Saved view" in titles and "Workflow" in titles
    assert not any("service key" in m.title for m in plan.manual_steps)


def test_plan_json_round_trips(hub, design):
    ad = make(hub)
    plan = ad.plan(design, ad.read_state())
    assert Plan.from_json(plan.to_json()) == plan


def test_matching_state_gives_zero_changes(hub, design):
    ad = make(hub)
    build(ad, design)
    again = ad.plan(design, ad.read_state())
    assert again.changes == ()
    assert not [m for m in again.manual_steps if m.risk == "destructive"]


def test_design_shaped_state_gives_zero_changes(hub, design):
    ad = make(hub)
    plan = ad.plan(design, state_from_design(design, "hubspot"))
    assert plan.changes == ()


def test_removed_option_is_hidden_never_deleted(hub, design):
    ad = make(hub, review=True)
    build(ad, design)
    d = design.get_field("deal", "lost_reason")
    smaller = replace(design, fields=tuple(
        replace(f, options=f.options[:-1]) if (f.object, f.key) == ("deal", "lost_reason") else f for f in design.fields))
    plan = ad.plan(smaller, ad.read_state())
    assert [c.kind for c in plan.changes] == ["remove_option"]
    assert plan.changes[0].risk == "needs_review"
    result = ad.apply(plan, dry_run=False)
    assert result.ok and len(result.applied) == 1
    live = hub.props["0-3"]["lost_reason"]["options"]
    assert [o["value"] for o in live if o["hidden"]] == [d.options[-1].key]
    assert not [c for c in hub.calls if c[0] == "DELETE"]
    assert ad.plan(smaller, ad.read_state()).changes == ()


def test_review_changes_are_held_without_allow_review(hub, design):
    ad = make(hub, review=False)
    build(ad, design)
    smaller = replace(design, fields=tuple(
        replace(f, options=f.options[:-1]) if (f.object, f.key) == ("deal", "lost_reason") else f for f in design.fields))
    plan = ad.plan(smaller, ad.read_state())
    result = ad.apply(plan, dry_run=False)
    assert result.applied == () and len(result.remaining) == 1


def test_stage_removal_becomes_manual_step(hub, design):
    ad = make(hub, review=True)
    build(ad, design)
    pl = design.get_pipeline("deal", "new_business")
    trimmed = replace(pl, stages=pl.stages[:1] + pl.stages[2:])
    changed = replace(design, pipelines=tuple(trimmed if p is pl else p for p in design.pipelines))
    plan = ad.plan(changed, ad.read_state())
    assert not [c for c in plan.changes if c.kind == "remove_stage"]
    assert any(m.title.startswith("Retire stage") and m.risk == "destructive" for m in plan.manual_steps)


def test_missing_custom_object_entitlement_becomes_manual_steps(design):
    hub = FakeHubSpot(enterprise=False)
    ad = make(hub)
    plan = ad.plan(design, ad.read_state())
    custom = {o.key for o in design.custom_objects}
    assert "add_object" not in [c.kind for c in plan.changes]
    for c in plan.changes:
        assert c.target.split(".")[0] not in custom
    steps = [m for m in plan.manual_steps if m.title.startswith("Custom object")]
    assert len(steps) == len(custom)
    assert all("plan-requirements.md" in m.reason and "b2b-saas-sales-led" in m.reason for m in steps)
    result = ad.apply(plan, dry_run=False)
    assert result.ok
    assert not hub.schemas


def test_limit_of_one_object_blocks_the_second(design):
    hub = FakeHubSpot(max_objects=1)
    ad = make(hub)
    plan = ad.plan(design, ad.read_state())
    assert [c.kind for c in plan.changes].count("add_object") == 1
    assert len([m for m in plan.manual_steps if m.title.startswith("Custom object")]) == 1


def test_missing_scope_on_limits_read_leaves_entitlement_unknown(design):
    hub = FakeHubSpot()
    hub.reply_once("GET", r"/crm/limits/", Resp(403, {"status": "error", "context": {"missingScopes": ["x.read"]}}))
    ad = make(hub)
    plan = ad.plan(design, ad.read_state())
    assert ad.entitlement.allowed is None
    assert "add_object" in [c.kind for c in plan.changes]


# --- applying --------------------------------------------------------------------------------


def test_dry_run_makes_no_http_call(hub, design):
    ad = make(hub)
    plan = ad.plan(design, ad.read_state())
    hub.calls.clear()
    result = ad.apply(plan)  # default is a dry run
    assert hub.calls == []
    assert result.dry_run and result.applied == () and len(result.remaining) == len(plan.changes)


def test_full_build_resolves_placeholders_and_never_deletes(hub, design):
    ad = make(hub)
    plan, result = build(ad, design)
    assert result.ok and not result.remaining and len(result.applied) == len(plan.changes)
    assert not [c for c in hub.calls if c[0] == "DELETE"]
    for method, path, body in hub.bodies:
        assert "{" not in path, path
        assert "{objectTypeId" not in repr(body) and "{typeId" not in repr(body)
    ids = {s["name"]: tid for tid, s in hub.schemas.items()}
    assert ("POST", f"/crm/properties/{V}/{ids['subscription']}") in hub.calls
    assert ("POST", f"/crm/pipelines/{V}/deals") in hub.calls
    # the second schema was created with the first one's real id in associatedObjects
    onboarding = hub.schemas[ids["onboarding"]]
    assert ids["subscription"] in onboarding["associatedObjects"]
    # cardinality limits carry real integer type ids (the stub rejects anything else)
    assert hub.limits
    # required properties were set on the custom object after the properties existed
    assert set(gen._extra_required(design, design.get_object("subscription"))) <= set(hub.schemas[ids["subscription"]]["requiredProperties"])


def test_read_before_write_skips_existing_items(hub, design):
    ad = make(hub)
    plan = ad.plan(design, ad.read_state())
    target = next(c for c in plan.changes if c.target == "deal.next_step_date")
    hub.groups["0-3"]["b2b_saas_sales_led"] = {"name": "b2b_saas_sales_led"}
    hub.props["0-3"]["next_step_date"] = {"name": "next_step_date", "label": "Next step date", "type": "date",
                                          "fieldType": "date", "groupName": "b2b_saas_sales_led"}
    before = len(hub.calls)
    # simulate a plan made a moment ago: the item has appeared since
    result = ad.apply(replace(plan, changes=(target,)), dry_run=False)
    assert result.ok and result.applied == ()
    assert target in ad.skipped
    assert not [c for c in hub.calls[before:] if c[0] != "GET"]
    # a stale add_object is skipped too
    hub2 = FakeHubSpot()
    ad2 = make(hub2)
    plan2 = ad2.plan(design, ad2.read_state())
    first = next(c for c in plan2.changes if c.kind == "add_object")
    ad2.apply(replace(plan2, changes=(first,)), dry_run=False)
    again = ad2.apply(replace(plan2, changes=(first,)), dry_run=False)
    assert again.applied == () and len(hub2.schemas) == 1


def test_429_is_retried_with_backoff(hub, design):
    ad = make(hub)
    plan = ad.plan(design, ad.read_state())
    hub.reply_once("POST", r"/schemas$", Resp(429, fixture("error_429.json")))
    hub.reply_once("POST", r"/schemas$", Resp(429, fixture("error_429.json")))
    result = ad.apply(replace(plan, changes=plan.changes[:1]), dry_run=False)
    assert result.ok and len(result.applied) == 1
    assert hub.sleeps == [1.0, 2.0]
    assert len(hub.schemas) == 1


def test_429_honours_retry_after_and_gives_up(hub, design):
    ad = make(hub)
    plan = ad.plan(design, ad.read_state())
    for _ in range(hsa.MAX_TRIES):
        hub.reply_once("POST", r"/schemas$", Resp(429, fixture("error_429.json"), {"Retry-After": "3"}))
    result = ad.apply(replace(plan, changes=plan.changes[:1]), dry_run=False)
    assert not result.ok and "HTTP 429" in result.failed[0].error
    assert hub.sleeps == [3.0] * (hsa.MAX_TRIES - 1)
    assert not hub.schemas


def test_daily_limit_429_is_not_retried(hub, design):
    ad = make(hub)
    plan = ad.plan(design, ad.read_state())
    body = {**fixture("error_429.json"), "policyName": "DAILY"}
    hub.reply_once("POST", r"/schemas$", Resp(429, body))
    result = ad.apply(replace(plan, changes=plan.changes[:1]), dry_run=False)
    assert not result.ok and hub.sleeps == []


def test_stops_on_first_failure_and_reports(hub, design):
    ad = make(hub)
    plan = ad.plan(design, ad.read_state())
    n = len(plan.changes)
    # fail the third change: the first property POST that is not the group
    hub.reply_once("POST", rf"/crm/properties/{V}/[^/]+$", Resp(400, fixture("error_400.json")))
    result = ad.apply(plan, dry_run=False)
    assert not result.ok and len(result.failed) == 1
    failure = result.failed[0]
    assert "VALIDATION_ERROR" in failure.error and "discount was not a valid number" in failure.error
    assert failure.change.kind == "add_field"
    assert len(result.applied) + len(result.failed) + len(result.remaining) + len(ad.skipped) == n
    assert list(result.applied) == list(plan.changes[: len(result.applied)])
    assert list(result.remaining) == list(plan.changes[len(result.applied) + 1 :])
    # nothing after the failure was sent
    std = {"company": "0-2", "person": "0-1", "deal": "0-3"}
    for change in result.remaining:
        obj, _, name = change.target.partition(".")
        if change.kind == "add_field" and obj in std:
            assert name not in hub.props[std[obj]], change.target
    obj, _, name = failure.change.target.partition(".")
    if obj in std:
        assert name not in hub.props[std[obj]]


def test_token_is_never_in_an_error(hub, design):
    ad = make(hub)
    plan = ad.plan(design, ad.read_state())
    hub.reply_once("POST", r"/schemas$", Resp(400, {"status": "error", "message": f"bad token {TOKEN}"}))
    result = ad.apply(replace(plan, changes=plan.changes[:1]), dry_run=False)
    assert TOKEN not in result.failed[0].error


def test_destructive_change_is_refused(hub, design):
    from tools.crm.base import Change
    from tools.crm.safety import SafetyError

    bad = Change("add_field", "deal.x", {}, "destructive", "u", "s")
    with pytest.raises(SafetyError):
        make(hub).apply(Plan("hubspot", "t", (bad,)), dry_run=False)


# --- identity and set-up ---------------------------------------------------------------------


def test_production_plan_names_the_portal(hub, design):
    ad = make(hub, production=True)
    plan = ad.plan(design, ad.read_state())
    assert plan.target == "test account (HubSpot portal 12345678)"


def test_identity_falls_back_to_schema_portal_id(design):
    hub = FakeHubSpot(portal=777)
    ad = make(hub)
    build(ad, design)
    hub.reply_once("GET", r"/account-info/", Resp(404, {"status": "error"}))
    ident = make(hub).read_identity()
    assert (ident.portal_id, ident.source) == ("777", "schema fullyQualifiedName")


def test_make_adapter_needs_both_variables():
    with pytest.raises(SafetyError) as e:
        hsa.make_adapter({"HUBSPOT_TARGET": "x"}, target=None, production=False)
    assert "HUBSPOT_ACCESS_TOKEN" in str(e.value) and TOKEN not in str(e.value)
    with pytest.raises(SafetyError, match="HUBSPOT_TARGET"):
        hsa.make_adapter({"HUBSPOT_ACCESS_TOKEN": TOKEN}, target=None, production=False)
    assert hsa.make_adapter({"HUBSPOT_ACCESS_TOKEN": TOKEN}, target="given", production=False).target == "given"


# --- live ------------------------------------------------------------------------------------


@pytest.mark.live
@pytest.mark.skipif(
    not (os.environ.get("HUBSPOT_ACCESS_TOKEN") and os.environ.get("HUBSPOT_TARGET")),
    reason="needs HUBSPOT_ACCESS_TOKEN and HUBSPOT_TARGET (a developer test account)",
)
def test_live_pull_plan_apply_replan(design):
    ad = hsa.make_adapter(os.environ, target=None, production=False)
    ad.mode = Mode(dry_run=False, production=False, allow_review=False)
    plan = ad.plan(design, ad.read_state())
    result = ad.apply(plan, dry_run=False)
    assert result.ok, [f.error for f in result.failed]
    assert not result.remaining
    assert ad.plan(design, ad.read_state()).changes == ()
