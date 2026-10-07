"""Salesforce adapter: reading, planning, applying. No `sf` binary: an in-memory org answers every call."""

from __future__ import annotations

import ast
import copy
import json
import os
import shutil
from dataclasses import replace
from pathlib import Path

import pytest

from tests.salesforce_stub import FakeSf, fixture, result_of
from tools.crm import salesforce as sfa
from tools.crm.base import Change, Plan
from tools.crm.registry import RegistryError, get_adapter
from tools.crm.safety import Mode, SafetyError, check_gates
from tools.design import REPO_ROOT, load_design
from tools.generators import salesforce as gen

BLUEPRINT = REPO_ROOT / "blueprints" / "b2b-saas-sales-led"
TOKEN = "TEST-ONLY-NOT-A-TOKEN"  # the placeholder in the org_display fixtures


@pytest.fixture(scope="module")
def design():
    return load_design(BLUEPRINT)


@pytest.fixture
def sf() -> FakeSf:
    return FakeSf()


def make(sf: FakeSf, *, production: bool = False, review: bool = False, org: str = "example-sbx", build_dir=None):
    ad = sfa.make_adapter({"SF_TARGET_ORG": org}, target=None, production=production, runner=sf, build_dir=build_dir)
    ad.mode = Mode(dry_run=False, production=production, allow_review=review)
    return ad


def make_plan(ad, design):
    return ad.plan(design, ad.read_state())


def build_all(sf: FakeSf, design, **kw):
    ad = make(sf, **kw)
    plan = make_plan(ad, design)
    return ad, plan, ad.apply(plan, dry_run=False)


def seed_from_generator(sf: FakeSf, design, tmp_path: Path) -> None:
    """Put the org in the state a perfect build is in, using the generator's folder and not the adapter."""
    gen.generate(design, tmp_path)
    base = tmp_path / gen.BASE
    files = sorted(p.relative_to(base).as_posix() for p in base.rglob("*") if p.is_file())
    failures, _ = sf._apply_files(tmp_path, files)
    assert not failures, failures


def all_flags(sf: FakeSf) -> list[str]:
    return [a for call in sf.calls for a in call]


# --- the environment -------------------------------------------------------------------------


def test_make_adapter_reads_the_org_through_get_credential():
    ad = sfa.make_adapter({"SF_TARGET_ORG": "client-sbx"}, target=None, production=False)
    assert (ad.target, ad.api_version, ad.cli) == ("client-sbx", "67.0", "sf")
    ad = sfa.make_adapter({"SF_TARGET_ORG": "a", "SF_API_VERSION": "66.0", "SF_CLI": "/opt/sf"}, target="given", production=False)
    assert (ad.target, ad.api_version, ad.cli) == ("given", "66.0", "/opt/sf")
    with pytest.raises(SafetyError, match="SF_TARGET_ORG"):
        sfa.make_adapter({}, target=None, production=False)
    with pytest.raises(SafetyError, match="SF_API_VERSION"):
        sfa.make_adapter({"SF_TARGET_ORG": "a", "SF_API_VERSION": "latest"}, target=None, production=False)


def test_registry_builds_the_adapter_and_names_a_missing_org():
    assert isinstance(get_adapter("salesforce", {"SF_TARGET_ORG": "x"}), sfa.SalesforceAdapter)
    with pytest.raises(RegistryError, match="SF_TARGET_ORG"):
        get_adapter("salesforce", {})


def test_missing_cli_is_a_clear_error():
    ad = sfa.make_adapter({"SF_TARGET_ORG": "x", "SF_CLI": "no-such-sf-binary-xyz"}, target=None, production=False)
    with pytest.raises(sfa.SalesforceError, match="not found"):
        ad.read_org()


# --- reading ---------------------------------------------------------------------------------


def test_read_state_maps_describe_and_query_output(design):
    sf = FakeSf()
    sf.objects["Subscription__c"] = result_of("describe_subscription.json")
    state = make(sf).read_state(design)
    objs = {o.key: o for o in state.objects}
    assert objs["company"].native and objs["deal"].native and not objs["subscription"].native
    fields = {(f.object, f.key): f for f in state.fields}
    # custom fields come back as design keys, with canonical types
    assert fields[("subscription", "arr")].type == "currency"
    assert fields[("subscription", "seats")].type == "number"
    assert fields[("subscription", "success_owner")].type == "user"
    # the inactive picklist value is absent, the active ones keep the design's labels
    status = dict(fields[("subscription", "status")].options)
    assert set(status) == {"pending_start", "active", "in_renewal", "churned"}
    assert status["pending_start"] == "Pending start"
    # a field the design does not know is reported, a managed-package field is native
    assert fields[("subscription", "contract_code")].native is False
    assert fields[("subscription", "acme__tier")].native is True
    # design-native fields are marked native and carry the design's type
    assert fields[("company", "employee_count")].native and fields[("company", "employee_count")].type == "number"
    assert fields[("deal", "next_step")].native
    # the name field of a custom object exists with it
    assert fields[("subscription", "name")].native
    # the lookup to Account is a relationship, not a field
    assert ("subscription", "company") not in fields
    assert any(r.key == "subscription_company" for r in state.relationships)


def test_read_state_without_a_design_guesses_keys_and_plan_remaps(design):
    sf = FakeSf()
    sf.objects["Subscription__c"] = result_of("describe_subscription.json")
    ad = make(sf)
    state = ad.read_state()
    assert {o.key for o in state.objects} >= {"company", "person", "deal", "subscription"}
    assert any(f.key == "arr" for f in state.fields)
    assert not any(r.native for r in state.relationships)
    # every sf read used --json and the target org; none passed a flag from the forbidden list
    assert all("--json" in c for c in sf.calls)
    assert all("--target-org" in c for c in sf.calls)
    plan = ad.plan(design, state)
    assert not any(c.kind == "add_field" and c.target == "subscription.arr" for c in plan.changes)


def test_read_state_reads_stages_and_business_processes(design, tmp_path):
    sf = FakeSf()
    seed_from_generator(sf, design, tmp_path)
    state = make(sf).read_state(design)
    pipes = {(p.object, p.key): p for p in state.pipelines}
    new_business = pipes[("deal", "new_business")]
    assert [s.key for s in new_business.stages][:3] == ["qualified", "discovery", "solution_fit"]
    stage = {s.key: s for s in new_business.stages}
    assert stage["qualified"].probability == 10 and stage["qualified"].type == "open"
    assert any(s.type == "won" for s in new_business.stages) and any(s.type == "lost" for s in new_business.stages)
    # the retrieve ran in a project folder with a manifest
    assert any(c[1:3] == ["project", "retrieve"] for c in sf.calls)


def test_retrieve_failure_is_noted_and_stages_follow_the_design(design, tmp_path):
    sf = FakeSf()
    seed_from_generator(sf, design, tmp_path)
    sf.retrieve_fails = True
    ad = make(sf)
    plan = make_plan(ad, design)
    assert plan.changes == ()
    assert any("could not be retrieved" in n for n in ad.notes)


# --- planning --------------------------------------------------------------------------------


def test_empty_org_gives_ordered_changes(design, sf):
    plan = make_plan(make(sf), design)
    kinds = [c.kind for c in plan.changes]
    phases = [sfa.PHASE[k] for k in kinds]
    assert phases == sorted(phases)
    assert kinds[0] == "add_object" and kinds[-1] in ("add_pipeline", "add_stage")
    assert {c.target for c in plan.changes if c.kind == "add_object"} == {"subscription", "onboarding"}
    assert {c.target for c in plan.changes if c.kind == "add_pipeline"} == {"deal.new_business", "deal.renewals_expansion"}
    # name and owner of a custom object come with the object, so no change for them
    assert not any(c.kind == "add_field" and c.target.endswith((".name", ".owner")) for c in plan.changes)
    # every change carries what it deploys; no change is a manual-only kind
    assert all(c.payload["components"] and c.payload["files"] for c in plan.changes)
    assert all(c.risk == "safe" for c in plan.changes)
    assert all(c.source_url.startswith("https://") for c in plan.changes)
    assert plan.target == "example-sbx"
    titles = " ".join(m.title for m in plan.manual_steps)
    assert "permission set" in titles.lower()
    json.loads(plan.to_json())  # a plan file round-trips
    assert Plan.from_json(plan.to_json()) == plan


def test_each_change_names_only_its_own_components(design, sf):
    plan = make_plan(make(sf), design)
    by = {(c.kind, c.target): c for c in plan.changes}
    obj = by[("add_object", "subscription")]
    assert obj.payload["components"] == [["CustomObject", "Subscription__c"]]
    assert list(obj.payload["files"]) == ["objects/Subscription__c/Subscription__c.object-meta.xml"]
    fld = by[("add_field", "subscription.arr")]
    assert fld.payload["components"] == [["CustomField", "Subscription__c.Arr__c"]]
    rel = by[("add_relationship", "subscription_company")]
    assert rel.payload["components"] == [["CustomField", "Subscription__c.Company__c"]]
    pipe = by[("add_pipeline", "deal.new_business")]
    kinds = {t for t, _ in pipe.payload["components"]}
    assert {"StandardValueSet", "BusinessProcess", "RecordType", "PathAssistant", "ValidationRule"} <= kinds
    assert ["BusinessProcess", "Opportunity.New_business"] in pipe.payload["components"]
    assert ["BusinessProcess", "Opportunity.Renewals_expansion"] not in pipe.payload["components"]


def test_matching_org_gives_zero_changes(design, sf, tmp_path):
    seed_from_generator(sf, design, tmp_path)
    ad = make(sf)
    plan = make_plan(ad, design)
    assert plan.changes == ()
    assert not [m for m in plan.manual_steps if m.risk == "destructive"]


def test_extras_in_the_org_become_destructive_manual_steps_never_changes(design, sf, tmp_path):
    seed_from_generator(sf, design, tmp_path)
    sf.objects["Subscription__c"]["fields"].append(
        {"name": "Leftover__c", "label": "Leftover", "type": "string", "custom": True, "length": 255,
         "picklistValues": [], "referenceTo": []})
    plan = make_plan(make(sf), design)
    assert plan.changes == ()
    removal = [m for m in plan.manual_steps if m.risk == "destructive"]
    assert [m.title for m in removal] == ["Remove field subscription.leftover"]
    assert "Export" in removal[0].instructions


def test_picklist_value_added_in_the_design_is_one_change(design, sf, tmp_path):
    seed_from_generator(sf, design, tmp_path)
    edited = _edit_options(design, "subscription", "status", lambda opts: opts + (_option("paused", "Paused"),))
    plan = make_plan(make(sf), edited)
    assert [(c.kind, c.target) for c in plan.changes] == [("add_option", "subscription.status.paused")]
    assert plan.changes[0].payload["components"] == [["CustomField", "Subscription__c.Status__c"]]


def _option(key, label):
    from tools.design import Option

    return Option(key, label)


def _edit_options(design, obj, key, fn):
    fields = tuple(
        replace(f, options=fn(f.options)) if (f.object, f.key) == (obj, key) else f for f in design.fields
    )
    return replace(design, fields=fields)


def test_renames_and_stage_changes_become_manual_steps(design, sf, tmp_path):
    seed_from_generator(sf, design, tmp_path)
    renamed = _edit_options(design, "subscription", "status", lambda o: (replace(o[0], label="Waiting to start"), *o[1:]))
    plan = make_plan(make(sf), renamed)
    assert plan.changes == ()
    assert any("Rename option" in m.title for m in plan.manual_steps)
    # a stage that moves from open to won is a manual step too, not a deploy
    pipes = tuple(
        replace(p, stages=tuple(replace(s, probability=(s.probability or 0) + 5) if s.key == "discovery" else s for s in p.stages))
        if p.key == "new_business" else p for p in design.pipelines
    )
    plan = make_plan(make(sf), replace(design, pipelines=pipes))
    assert plan.changes == ()
    assert any(m.title.startswith("Change stage") for m in plan.manual_steps)


# --- applying --------------------------------------------------------------------------------


def test_dry_run_passes_dry_run_and_never_deploys_for_real(design, sf):
    ad = make(sf)
    plan = make_plan(ad, design)
    before = copy.deepcopy(sf.objects)
    result = ad.apply(plan, dry_run=True)
    assert result.ok and result.dry_run and result.applied == ()
    assert len(result.remaining) == len(plan.changes)
    assert len(sf.deploys) == 1 and sf.deploys[0]["dry_run"] is True
    assert "--dry-run" in sf.deploys[0]["argv"]
    assert sf.objects == before  # a check-only deploy saved nothing
    assert not any(not d["dry_run"] for d in sf.deploys)


def test_deploy_command_line_is_exactly_the_documented_one(design, sf):
    ad, plan, result = build_all(sf, design)
    assert result.ok
    for d in sf.deploys:
        argv = d["argv"]
        assert argv[:4] == ["sf", "project", "deploy", "start"]
        assert ["--manifest", "package.xml"] == argv[argv.index("--manifest"):argv.index("--manifest") + 2]
        assert argv[argv.index("--target-org") + 1] == "example-sbx"
        assert argv[argv.index("--api-version") + 1] == "67.0"
        assert argv[argv.index("--wait") + 1] == "30"
        assert "--json" in argv and "--dry-run" not in argv


def test_forbidden_flags_and_destructive_files_never_appear(design, sf):
    ad = make(sf)
    plan = make_plan(ad, design)
    ad.apply(plan, dry_run=True)
    ad.apply(plan, dry_run=False)
    flags = all_flags(sf)
    for bad in ("--ignore-errors", "--ignore-conflicts", "--ignore-warnings", "--purge-on-delete",
                "--pre-destructive-changes", "--post-destructive-changes"):
        assert bad not in flags
    assert not [a for a in flags if "destructive" in a.lower()]
    for deploy in sf.deploys:
        assert not [f for f in deploy["listing"] if "destructive" in f.lower()]
        assert not [f for f in deploy["files"] if "destructive" in f.lower()]


def test_runner_refuses_a_forbidden_flag_and_a_destructive_file(sf, tmp_path):
    ad = make(sf)
    with pytest.raises(SafetyError, match="--ignore-errors"):
        ad._run(["project", "deploy", "start", "--ignore-errors"])
    with pytest.raises(SafetyError, match="destructive"):
        ad._run(["project", "deploy", "start", "--post-destructive-changes", "x"])
    with pytest.raises(SafetyError, match="destructive"):
        ad._write_project(tmp_path, "<Package/>", {"destructiveChanges.xml": "<x/>"})
    assert sf.calls == []  # nothing reached the runner


def test_manifest_lists_only_the_members_of_the_cleared_changes(design, sf):
    ad = make(sf)
    plan = make_plan(ad, design)
    only = Plan(plan.platform, plan.target, tuple(c for c in plan.changes if c.target == "subscription.arr" or c.kind == "add_object"))
    ad.apply(only, dry_run=False)
    listed = {tuple(x) for d in sf.deploys for x in d["listed"]}
    assert ("CustomField", "Subscription__c.Arr__c") in listed
    assert not any(m == "Subscription__c.Plan__c" for _, m in listed)
    assert not any(t in ("RecordType", "BusinessProcess", "ValidationRule", "PermissionSet", "ListView") for t, _ in listed)


def test_api_version_override_reaches_the_command_and_the_manifest(design):
    sf = FakeSf()
    ad = sfa.make_adapter({"SF_TARGET_ORG": "x", "SF_API_VERSION": "66.0"}, target=None, production=False, runner=sf)
    ad.mode = Mode(dry_run=False, production=False, allow_review=False)
    ad.apply(make_plan(ad, design), dry_run=True)
    argv = sf.deploys[0]["argv"]
    assert argv[argv.index("--api-version") + 1] == "66.0" and sf.deploys[0]["version"] == "66.0"


def test_apply_then_replan_is_zero_and_a_second_apply_is_a_no_op(design, sf):
    ad, plan, result = build_all(sf, design)
    assert result.ok and not result.remaining
    assert len(result.applied) == len(plan.changes)
    assert [d["dry_run"] for d in sf.deploys] == [False] * len(sf.deploys)
    assert len(sf.deploys) == len({sfa.PHASE[c.kind] for c in plan.changes})  # one deploy per phase
    again = make_plan(make(sf), design)
    assert again.changes == ()
    # applying the first plan again finds everything in place and deploys nothing
    deploys = len(sf.deploys)
    ad2 = make(sf)
    rerun = ad2.apply(plan, dry_run=False)
    assert rerun.ok and rerun.applied == () and len(ad2.skipped) == len(plan.changes)
    assert len(sf.deploys) == deploys
    # the org really has the design: stages, a record type per pipeline, a rule per gate
    assert {"New_business", "Renewals_expansion"} <= set(sf.processes)
    assert len(sf.rules) == len(gen.build_model(design).rules)


def test_pipelines_are_deployed_after_fields(design, sf):
    ad = make(sf)
    plan = make_plan(ad, design)
    pipelines_only = Plan(plan.platform, plan.target, tuple(c for c in plan.changes if c.kind == "add_pipeline"))
    result = ad.apply(pipelines_only, dry_run=True)
    # on an empty org the rules and record types name fields that do not exist yet
    assert not result.ok
    assert "does not exist" in result.failed[0].error
    # the full plan's phases put fields first, so it passes
    assert make(FakeSf()).apply(plan, dry_run=True).ok


def test_stop_on_failure_reports_applied_failed_and_remaining(design, sf):
    sf.script = [None, fixture("deploy_failure_object.json")]  # objects deploy, then the relationships deploy fails
    ad = make(sf)
    plan = make_plan(ad, design)
    result = ad.apply(plan, dry_run=False)
    assert not result.ok
    assert [c.kind for c in result.applied] == ["add_object"] * 2
    assert len(result.failed) == 1 and result.failed[0].change.kind == "add_relationship"
    assert "Field Decision_process__c does not exist" in result.failed[0].error
    done = {id(c) for c in result.applied} | {id(result.failed[0].change)}
    assert {id(c) for c in result.remaining} == {id(c) for c in plan.changes} - done
    assert len(sf.deploys) == 2  # nothing was tried after the failure


def test_first_failure_stops_before_any_later_phase(design, sf):
    sf.script = [fixture("deploy_failure_list.json")]
    ad = make(sf)
    plan = make_plan(ad, design)
    result = ad.apply(plan, dry_run=False)
    assert result.applied == () and len(result.failed) == 1
    assert len(result.remaining) == len(plan.changes) - 1
    assert len(sf.deploys) == 1
    assert sf.objects.get("Subscription__c") is None


def test_held_review_changes_are_not_deployed(design, sf, tmp_path):
    seed_from_generator(sf, design, tmp_path)
    removed = _edit_options(design, "subscription", "status", lambda o: o[:-1])
    ad = make(sf)  # allow_review is False
    plan = make_plan(ad, removed)
    assert [(c.kind, c.risk) for c in plan.changes] == [("remove_option", "needs_review")]
    deploys = len(sf.deploys)
    result = ad.apply(plan, dry_run=False)
    assert result.applied == () and len(result.remaining) == 1
    assert len(sf.deploys) == deploys


def test_removing_a_picklist_value_deactivates_it_and_deletes_nothing(design, sf, tmp_path):
    seed_from_generator(sf, design, tmp_path)
    removed = _edit_options(design, "subscription", "status", lambda o: o[:-1])  # drops "churned"
    ad = make(sf, review=True)
    plan = make_plan(ad, removed)
    change = plan.changes[0]
    assert "<isActive>false</isActive>" in change.payload["files"]["objects/Subscription__c/fields/Status__c.field-meta.xml"]
    result = ad.apply(plan, dry_run=False)
    assert result.ok and len(result.applied) == 1
    status = next(f for f in sf.objects["Subscription__c"]["fields"] if f["name"] == "Status__c")
    churned = next(v for v in status["picklistValues"] if v["value"] == "Churned")
    assert churned["active"] is False  # still there, switched off
    assert len(status["picklistValues"]) == 4
    assert make_plan(make(sf), removed).changes == ()


def test_removing_an_opportunity_stage_is_a_manual_step(design, sf, tmp_path):
    seed_from_generator(sf, design, tmp_path)
    pipes = tuple(
        replace(p, stages=tuple(s for s in p.stages if s.key != "discovery")) if p.key == "new_business" else p
        for p in design.pipelines
    )
    plan = make_plan(make(sf, review=True), replace(design, pipelines=pipes))
    assert not any(c.kind == "remove_stage" for c in plan.changes)
    step = next(m for m in plan.manual_steps if m.title.startswith("Retire stage"))
    assert step.risk == "destructive" and "Export" in step.instructions


# --- parsing deploy replies ------------------------------------------------------------------


def test_component_failures_as_one_object_and_as_a_list():
    one = fixture("deploy_failure_object.json")
    outcome = sfa.parse_deploy(one, 1)
    assert not outcome.ok and len(outcome.failures) == 1
    f = outcome.failures[0]
    assert (f.component_type, f.full_name) == ("ValidationRule", "Opportunity.Gate_new_business_proposal")
    assert f.file_path.endswith("Gate_new_business_proposal.validationRule-meta.xml")
    many = fixture("deploy_failure_list.json")
    outcome = sfa.parse_deploy(many, 1)
    assert not outcome.ok and [f.full_name for f in outcome.failures] == [
        "Opportunity.Gate_new_business_proposal", "Subscription__c.Status__c"]
    assert outcome.failures[1].problem.startswith("Picklist value is too long.")


def test_string_booleans_and_states_are_normalised():
    body = fixture("deploy_success.json")
    outcome = sfa.parse_deploy(body, 0)
    assert outcome.ok and outcome.states == {"Subscription__c": "Created"}
    body["result"]["success"] = "false"
    assert not sfa.parse_deploy(body, 0).ok
    body["result"]["success"] = "true"
    assert sfa.parse_deploy(body, 0).ok
    # a failure row marked success "true" is not a failure
    body["result"]["details"]["componentFailures"] = {"fullName": "X", "success": "true", "problem": ""}
    assert sfa.parse_deploy(body, 0).ok


def test_exit_codes_68_and_69_and_error_envelopes_are_never_ok():
    partial = sfa.parse_deploy(fixture("deploy_partial_68.json"), 68)
    assert not partial.ok and "partial" in partial.message
    running = sfa.parse_deploy(fixture("deploy_running_69.json"), 69)
    assert not running.ok and "0Af000000000009AAA" in running.message and "deploy report" in running.message
    err = sfa.parse_deploy(fixture("error_no_org.json"), 1)
    assert not err.ok and "NoDefaultEnvError" in err.message and "sf org login web" in err.message


def test_a_failed_deploy_through_apply_blames_the_change_that_owns_the_component(design, sf, tmp_path):
    seed_from_generator(sf, design, tmp_path)
    ad = make(sf)
    edited = _edit_options(design, "subscription", "status", lambda o: o + (_option("paused", "Paused"),))
    plan = make_plan(ad, edited)
    bad = fixture("deploy_failure_list.json")
    sf.script = [bad]
    result = ad.apply(plan, dry_run=False)
    assert result.failed[0].change.kind == "add_option"  # Subscription__c.Status__c is this change's component


# --- through the command line tools ---------------------------------------------------------


def test_plan_then_apply_one_change_at_a_time_through_the_cli(design, tmp_path, capsys):
    from tools import crm_apply, crm_plan

    sf = FakeSf()
    factory = lambda platform, env, target, production: make(sf, production=production)  # noqa: E731
    plan_file = tmp_path / "plan.json"
    assert crm_plan.main([str(BLUEPRINT), "--platform", "salesforce", "--out", str(plan_file)],
                         adapter_factory=factory, env={}) == 0
    plan = Plan.from_json(plan_file.read_text(encoding="utf-8"))
    assert plan.changes
    clients = ["--clients-dir", str(tmp_path / "clients")]
    # dry run: one check-only deploy, nothing saved
    assert crm_apply.main([str(plan_file), *clients], adapter_factory=factory, env={}) == 0
    assert sf.deploys and all(d["dry_run"] for d in sf.deploys) and "Subscription__c" not in sf.objects
    # execute: the CLI hands the adapter one change at a time, in plan order, re-reading the org each time
    assert crm_apply.main([str(plan_file), "--execute", "--client", "acme", "--design", str(BLUEPRINT), *clients],
                          adapter_factory=factory, env={}) == 0
    assert "Failed: 0" in capsys.readouterr().out
    real = [d for d in sf.deploys if not d["dry_run"]]
    assert 0 < len(real) <= len(plan.changes)
    again = tmp_path / "again.json"
    assert crm_plan.main([str(BLUEPRINT), "--platform", "salesforce", "--out", str(again)],
                         adapter_factory=factory, env={}) == 0
    assert Plan.from_json(again.read_text(encoding="utf-8")).changes == ()


# --- editions and production -----------------------------------------------------------------


def test_professional_edition_turns_every_change_into_a_manual_step(design):
    sf = FakeSf(edition="Professional Edition")
    ad = make(sf)
    plan = make_plan(ad, design)
    assert plan.changes == ()
    sheet = "blueprints/b2b-saas-sales-led/salesforce/build-sheet.md"
    steps = [m for m in plan.manual_steps if "Professional Edition cannot use the Metadata API" in m.reason]
    assert len(steps) > 20 and all(sheet in m.reason for m in steps)
    assert any(m.title.startswith("Add object") or "Add" in m.title for m in steps)
    assert sf.deploys == []


def test_professional_edition_apply_changes_nothing_and_does_not_fail(design):
    sf = FakeSf()
    plan = make_plan(make(sf), design)  # a plan made against an Enterprise org
    pro = FakeSf(edition="Professional Edition")
    ad = make(pro)
    result = ad.apply(plan, dry_run=False)
    assert result.ok and result.applied == () and len(result.remaining) == len(plan.changes)
    assert pro.deploys == [] and any("Professional" in n for n in ad.notes)


def test_essentials_and_unknown_editions_are_manual_too():
    for edition, ok in (("Essentials", False), ("Unlimited Edition", True), ("Developer Edition", True),
                        ("Performance Edition", True), ("Enterprise Edition", True), ("Mystery Edition", False)):
        org = sfa.OrgInfo("n", edition, True, False)
        assert org.metadata_api is ok, edition


def test_edition_limits_warn_near_the_allowance(design):
    b = gen.build_model(design)
    essentials = sfa._limit_steps(design, b, sfa.OrgInfo("n", "Essentials", True, False))
    assert [m.title for m in essentials] == ["Check the edition limits"]
    assert sfa._limit_steps(design, b, sfa.OrgInfo("n", "Enterprise Edition", True, False)) == []


def test_production_detection_names_the_org(design):
    live = FakeSf(sandbox=False)
    ad = make(live, org="example-live")
    org = ad.read_org()
    assert org.production and org.name == "Example Trading Ltd"
    plan = make_plan(ad, design)
    assert plan.target == "Example Trading Ltd (example-live)"
    seen: list[str] = []
    check_gates(plan, Mode(dry_run=False, production=True, allow_review=False), confirm=seen.append)
    assert seen == ["Example Trading Ltd (example-live)"]
    assert not make(FakeSf(sandbox=True)).read_org().production
    scratch = make(FakeSf(scratch=True)).read_org()
    assert scratch.is_scratch and not scratch.production


def test_a_production_org_needs_the_production_flag_to_deploy(design):
    live = FakeSf(sandbox=False)
    ad = make(live, org="example-live")  # production not passed
    plan = make_plan(ad, design)
    with pytest.raises(SafetyError, match="production org"):
        ad.apply(plan, dry_run=False)
    assert live.deploys == []
    # a check-only run is allowed without the flag, and a real run with it goes ahead
    assert make(live, org="example-live").apply(plan, dry_run=True).ok
    flagged = make(live, production=True, org="example-live")
    assert flagged.apply(plan, dry_run=False).ok


def test_the_access_token_is_never_kept_or_printed(design, sf):
    ad = make(sf)
    plan = make_plan(ad, design)
    ad.apply(plan, dry_run=True)
    for text in (repr(ad), repr(ad.read_org()), plan.to_json(), " ".join(ad.notes)):
        assert TOKEN not in text
    # an error from sf is redacted and carries no raw output
    broken = FakeSf()
    broken.__class__ = type("Broken", (FakeSf,), {"__call__": lambda self, a, c, t: sfa.RunOutput(1, json.dumps(
        {"name": "Boom", "message": f"failed with token={TOKEN}", "exitCode": 1, "status": 1}), "")})
    with pytest.raises(sfa.SalesforceError) as err:
        make(broken).read_org()
    assert TOKEN not in str(err.value) and "Boom" in str(err.value)


def test_non_json_output_is_a_clear_error(sf):
    ad = sfa.make_adapter({"SF_TARGET_ORG": "x"}, target=None, production=False,
                          runner=lambda argv, cwd, timeout: sfa.RunOutput(2, "", "sf: command not found: org"))
    with pytest.raises(sfa.SalesforceError, match="gave no JSON"):
        ad.read_org()


# --- the build folder ------------------------------------------------------------------------


def test_deploy_folder_is_removed_unless_a_failure_leaves_it_in_the_build_dir(design, tmp_path):
    ok = FakeSf()
    ad = make(ok, build_dir=tmp_path)
    ad.apply(make_plan(ad, design), dry_run=False)
    assert list(tmp_path.iterdir()) == []
    bad = FakeSf()
    bad.script = [fixture("deploy_failure_object.json")]
    ad = make(bad, build_dir=tmp_path)
    ad.apply(make_plan(ad, design), dry_run=False)
    kept = list(tmp_path.iterdir())
    assert len(kept) == 1 and (kept[0] / "package.xml").exists()
    shutil.rmtree(kept[0])


# --- housekeeping ----------------------------------------------------------------------------


def test_every_function_that_runs_sf_names_its_source_url():
    tree = ast.parse(Path(sfa.__file__).read_text(encoding="utf-8"))
    runners = {"_run", "_read", "_runner", "subprocess_runner"}
    missing = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        calls = {
            n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "")
            for n in ast.walk(node) if isinstance(n, ast.Call)
        }
        if calls & runners or node.name == "subprocess_runner":
            doc = ast.get_docstring(node) or ""
            if "https://" not in doc:
                missing.append(node.name)
    assert missing == []


def test_only_the_runner_starts_a_process():
    text = Path(sfa.__file__).read_text(encoding="utf-8")
    assert text.count("subprocess.run(") == 1 and "os.system" not in text and "Popen" not in text


# --- live ------------------------------------------------------------------------------------


@pytest.mark.live
@pytest.mark.skipif(
    not (shutil.which(os.environ.get("SF_CLI", "sf")) and os.environ.get("SF_TARGET_ORG")),
    reason="needs the sf CLI on PATH and SF_TARGET_ORG (an org alias authorised with `sf org login web`)",
)
def test_live_pull_plan_apply_replan(design):
    ad = sfa.make_adapter(os.environ, target=None, production=False)
    org = ad.read_org()
    if org.production:
        pytest.fail(f"{org.name!r} is not a sandbox or scratch org. This test deploys, so it refuses production.")
    if not org.metadata_api:
        pytest.skip(f"{org.edition} cannot use the Metadata API")
    ad.mode = Mode(dry_run=False, production=False, allow_review=False)
    plan = ad.plan(design, ad.read_state())
    result = ad.apply(plan, dry_run=False)
    assert result.ok, [f.error for f in result.failed]
    assert not result.remaining
    assert ad.plan(design, ad.read_state()).changes == ()
