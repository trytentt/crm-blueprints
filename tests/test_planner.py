"""Planner behaviour: idempotency, ordering, every risk class, destructive removals."""

from __future__ import annotations

from dataclasses import replace

import pytest

from tests.fake_adapter import PLATFORM, FakeAdapter, build_payload, state_matching
from tools.crm.base import ManualStep, Plan, StateField, StateObject, StatePipeline, StateRelationship, StateStage
from tools.crm.planner import BUILD_RANK, RISK_BY_KIND, plan_changes
from tools.design import load_design


@pytest.fixture
def design(write_design, design_dict):
    return load_design(write_design(design_dict))


def plan_for(design, state, **kw):
    return plan_changes(design, state, build_payload, target="sandbox", **kw)


def kinds(plan):
    return [c.kind for c in plan.changes]


def drop_field(state, obj, key):
    return replace(state, fields=tuple(f for f in state.fields if (f.object, f.key) != (obj, key)))


def edit_field(state, obj, key, **changes):
    return replace(
        state,
        fields=tuple(replace(f, **changes) if (f.object, f.key) == (obj, key) else f for f in state.fields),
    )


# --- idempotency -------------------------------------------------------------------------------


def test_matching_state_gives_zero_changes(design):
    plan = plan_for(design, state_matching(design))
    assert plan.changes == () and plan.manual_steps == () and plan.is_empty


def test_reference_blueprint_matching_state_gives_zero_changes():
    d = load_design("blueprints/b2b-saas-sales-led")
    for platform in ("attio", "hubspot", "salesforce"):
        assert plan_for(d, state_matching(d, platform)).is_empty


def test_replanning_after_fake_apply_is_noop(design):
    empty = replace(state_matching(design), objects=tuple(o for o in state_matching(design).objects if o.native),
                    fields=tuple(f for f in state_matching(design).fields if f.native), pipelines=(),
                    relationships=tuple(r for r in state_matching(design).relationships if r.native))
    adapter = FakeAdapter(empty)
    plan = adapter.plan(design, empty)
    assert plan.changes
    result = adapter.apply(plan, dry_run=False)
    assert result.ok and len(result.applied) == len(plan.changes)
    # The "live" state after applying equals a perfect build, so the next plan is empty.
    assert adapter.plan(design, state_matching(design)).is_empty


# --- additions are safe and ordered ------------------------------------------------------------


def test_empty_account_builds_in_order(design):
    s = state_matching(design)
    empty = replace(
        s,
        objects=tuple(o for o in s.objects if o.native),
        fields=tuple(f for f in s.fields if f.native),
        relationships=tuple(r for r in s.relationships if r.native),
        pipelines=(),
    )
    plan = plan_for(design, empty)
    assert kinds(plan)[0] == "add_object"
    ranks = [BUILD_RANK[k] for k in kinds(plan)]
    assert ranks == sorted(ranks)
    ks = kinds(plan)
    assert ks[:3] == ["add_object", "add_relationship", "add_pipeline"]
    assert set(ks[3:]) == {"add_field"}
    # core fields that are not native on this platform are built as custom fields
    assert {"project.status", "deal.lost_reason", "deal.next_step_date"} <= {c.target for c in plan.changes}
    assert all(c.risk == "safe" for c in plan.changes)
    assert plan.manual_steps == ()


def test_add_object_precedes_its_fields_even_if_listed_last(design):
    s = state_matching(design)
    s = replace(s, objects=tuple(o for o in s.objects if o.native), fields=tuple(f for f in s.fields if f.native))
    plan = plan_for(design, s)
    first_field = next(i for i, k in enumerate(kinds(plan)) if k == "add_field")
    assert kinds(plan).index("add_object") < first_field


def test_add_field_is_safe(design):
    plan = plan_for(design, drop_field(state_matching(design), "deal", "next_step_date"))
    assert kinds(plan) == ["add_field"]
    assert plan.changes[0].risk == "safe" and plan.changes[0].target == "deal.next_step_date"


def test_native_field_missing_from_state_is_not_added(design):
    plan = plan_for(design, drop_field(state_matching(design), "deal", "amount"))
    assert plan.is_empty


def test_add_option_is_safe(design):
    s = edit_field(state_matching(design), "deal", "lost_reason", options=(("price", "Price"),))
    plan = plan_for(design, s)
    assert kinds(plan) == ["add_option"]
    assert plan.changes[0].risk == "safe" and plan.changes[0].target == "deal.lost_reason.timing"


def test_add_stage_is_safe(design):
    s = state_matching(design)
    pipe = s.pipelines[0]
    s = replace(s, pipelines=(replace(pipe, stages=tuple(x for x in pipe.stages if x.key != "discovery")),))
    plan = plan_for(design, s)
    assert kinds(plan) == ["add_stage"] and plan.changes[0].risk == "safe"
    assert plan.changes[0].target == "deal.sales.discovery"


def test_add_relationship_and_pipeline_are_safe(design):
    s = state_matching(design)
    s = replace(s, pipelines=(), relationships=tuple(r for r in s.relationships if r.native))
    plan = plan_for(design, s)
    assert kinds(plan) == ["add_relationship", "add_pipeline"]
    assert [c.risk for c in plan.changes] == ["safe", "safe"]


def test_native_relationship_matched_by_endpoints_not_key(design):
    s = state_matching(design)
    s = replace(s, relationships=tuple(
        replace(r, key="attio_company_link") if r.key == "person_company" else r for r in s.relationships))
    assert plan_for(design, s).is_empty


def test_native_relationship_is_not_matched_to_a_custom_one_between_the_same_objects(design_dict, write_design):
    """Regression: deal-to-company (native) and a co-investor link (custom, many_to_many) join the same pair."""
    design_dict["add_relationships"].append({
        "key": "deal_co_investors", "from": "deal", "to": "company", "cardinality": "many_to_many",
        "from_label": "Co-investors", "to_label": "Co-invested deals", "purpose": "Other funds in the round.",
    })
    design = load_design(write_design(design_dict))
    s = state_matching(design)
    # Live has the custom link but no native deal_company: the native one must not be matched to it.
    s = replace(s, relationships=tuple(r for r in s.relationships if r.key != "deal_company"))
    plan = plan_for(design, s)
    assert plan.is_empty, [m.title for m in plan.manual_steps]


# --- needs_review ------------------------------------------------------------------------------


def test_renames_are_needs_review(design):
    s = state_matching(design)
    s = edit_field(s, "deal", "next_step_date", label="Old label")
    s = edit_field(s, "deal", "lost_reason", options=(("price", "Cost"), ("timing", "Timing")))
    s = replace(s, objects=tuple(replace(o, label="Old project") if o.key == "project" else o for o in s.objects))
    pipe = s.pipelines[0]
    s = replace(s, pipelines=(replace(pipe, stages=tuple(
        replace(x, label="Old stage") if x.key == "won" else x for x in pipe.stages)),))
    plan = plan_for(design, s)
    assert sorted(kinds(plan)) == sorted(["rename_object", "rename_field", "rename_option", "rename_stage"])
    assert {c.risk for c in plan.changes} == {"needs_review"}
    assert plan.manual_steps == ()


def test_reorder_stages_is_needs_review(design):
    s = state_matching(design)
    pipe = s.pipelines[0]
    s = replace(s, pipelines=(replace(pipe, stages=tuple(reversed(pipe.stages))),))
    plan = plan_for(design, s)
    assert kinds(plan) == ["reorder_stages"] and plan.changes[0].risk == "needs_review"


def test_adding_a_stage_is_not_a_reorder(design):
    s = state_matching(design)
    pipe = s.pipelines[0]
    s = replace(s, pipelines=(replace(pipe, stages=tuple(x for x in pipe.stages if x.key == "won" or x.key == "lost")),))
    assert kinds(plan_for(design, s)) == ["add_stage"]


def test_option_removal_is_needs_review_not_destructive_step(design):
    s = edit_field(state_matching(design), "deal", "lost_reason",
                   options=(("price", "Price"), ("timing", "Timing"), ("old", "Old")))
    plan = plan_for(design, s)
    assert kinds(plan) == ["remove_option"]
    assert plan.changes[0].risk == "needs_review" and plan.manual_steps == ()


def test_stage_removal_is_needs_review(design):
    s = state_matching(design)
    pipe = s.pipelines[0]
    extra = StateStage("legacy", "Legacy", "open", 10)
    s = replace(s, pipelines=(replace(pipe, stages=pipe.stages + (extra,)),))
    plan = plan_for(design, s)
    assert kinds(plan) == ["remove_stage"] and plan.changes[0].risk == "needs_review"
    assert plan.manual_steps == ()


def test_stage_probability_or_type_change_is_needs_review(design):
    s = state_matching(design)
    pipe = s.pipelines[0]
    s = replace(s, pipelines=(replace(pipe, stages=tuple(
        replace(x, probability=50) if x.key == "discovery" else x for x in pipe.stages)),))
    plan = plan_for(design, s)
    assert kinds(plan) == ["update_stage"] and plan.changes[0].risk == "needs_review"


def test_stage_unknown_probability_is_not_a_difference(design):
    s = state_matching(design)
    pipe = s.pipelines[0]
    s = replace(s, pipelines=(replace(pipe, stages=tuple(replace(x, probability=None) for x in pipe.stages)),))
    assert plan_for(design, s).is_empty


# --- destructive: manual steps, never Changes -------------------------------------------------


def test_field_removal_is_destructive_manual_step(design):
    s = state_matching(design)
    s = replace(s, fields=s.fields + (StateField("deal", "legacy_code", "text", "Legacy code"),))
    plan = plan_for(design, s)
    assert plan.changes == ()
    (step,) = plan.manual_steps
    assert isinstance(step, ManualStep) and step.risk == "destructive"
    assert "deal.legacy_code" in step.title
    assert "Export" in step.instructions and "never delete" in step.instructions.lower()
    assert step.done_when and step.ui_path


def test_native_live_field_not_in_design_is_ignored(design):
    s = state_matching(design)
    s = replace(s, fields=s.fields + (StateField("deal", "system_field", "text", native=True),))
    assert plan_for(design, s).is_empty


def test_object_removal_is_destructive_manual_step(design):
    s = state_matching(design)
    s = replace(s, objects=s.objects + (StateObject("old_thing", "Old thing"),),
                fields=s.fields + (StateField("old_thing", "x", "text"),))
    plan = plan_for(design, s)
    assert plan.changes == ()
    assert [m.risk for m in plan.manual_steps] == ["destructive"]
    assert "old_thing" in plan.manual_steps[0].title


def test_relationship_removal_is_destructive_manual_step(design):
    s = state_matching(design)
    s = replace(s, relationships=s.relationships + (StateRelationship("old_link", "deal", "project", "many_to_one"),))
    plan = plan_for(design, s)
    assert plan.changes == () and plan.manual_steps[0].risk == "destructive"
    assert "old_link" in plan.manual_steps[0].title


def test_pipeline_removal_is_destructive_manual_step(design):
    s = state_matching(design)
    s = replace(s, pipelines=s.pipelines + (StatePipeline("deal", "old_pipe", "Old", (StateStage("a"),)),))
    plan = plan_for(design, s)
    assert plan.changes == () and plan.manual_steps[0].risk == "destructive"


def test_type_change_is_manual_step_never_a_change(design):
    s = edit_field(state_matching(design), "deal", "next_step_date", type="text")
    plan = plan_for(design, s)
    assert plan.changes == ()
    (step,) = plan.manual_steps
    assert step.risk == "destructive"
    assert "text to date" in step.title
    assert "new field" in step.instructions.lower() and "Copy values" in step.instructions


def test_select_to_multi_select_is_a_type_change(design):
    s = edit_field(state_matching(design), "deal", "lost_reason", type="multi_select")
    plan = plan_for(design, s)
    assert plan.changes == () and len(plan.manual_steps) == 1


def test_cardinality_change_is_manual_step(design):
    s = state_matching(design)
    s = replace(s, relationships=tuple(
        replace(r, cardinality="many_to_many") if r.key == "project_company" else r for r in s.relationships))
    plan = plan_for(design, s)
    assert plan.changes == () and plan.manual_steps[0].risk == "destructive"


def test_no_change_is_ever_destructive(design):
    s = state_matching(design)
    s = replace(s, fields=s.fields + (StateField("deal", "legacy", "text"),))
    s = edit_field(s, "deal", "next_step_date", type="text")
    assert all(c.risk != "destructive" for c in plan_for(design, s).changes)
    assert "destructive" not in RISK_BY_KIND.values()


# --- plumbing ----------------------------------------------------------------------------------


def test_source_urls_ui_paths_and_extra_steps(design):
    s = state_matching(design)
    s = replace(s, fields=s.fields + (StateField("deal", "legacy", "text"),))
    s = drop_field(s, "deal", "next_step_date")
    extra = ManualStep("Build automation A", "No API", "Settings > Automations", "It runs", )
    plan = plan_for(design, s, source_urls={"add_field": "https://example.test/docs"},
                    ui_paths={"remove_field": "Settings > Objects > Deal"}, extra_manual_steps=[extra])
    assert plan.changes[0].source_url == "https://example.test/docs"
    assert plan.manual_steps[0].ui_path == "Settings > Objects > Deal"
    assert plan.manual_steps[-1] == extra


def test_payload_builder_receives_context(design):
    seen = []

    def builder(kind, target, context):
        seen.append((kind, target, sorted(context)))
        return {"ok": True}

    plan_changes(design, drop_field(state_matching(design), "deal", "next_step_date"), builder)
    assert seen == [("add_field", "deal.next_step_date", ["design", "field"])]


def test_plan_platform_comes_from_state(design):
    assert plan_for(design, state_matching(design)).platform == PLATFORM
