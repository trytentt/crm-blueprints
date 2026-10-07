"""Regression tests for the independent review's findings (D-24 to D-28).

Each test here failed before its fix: S1 (production confirmation tied to the live account), S2 (HubSpot account
type), S4 (the public "never archive" claim), C1 (a hand-edited plan's payload), C2 (`--target` on Attio).
S3 (a shared stage name) is in `test_end_to_end.py`, next to the Salesforce stage tests.
"""

from __future__ import annotations

import io
import json
import sys
from dataclasses import replace
from functools import partial
from pathlib import Path

import pytest

from tests.attio_stub import FakeAttio
from tests.hubspot_stub import FakeHubSpot, Resp
from tests.salesforce_stub import FakeSf
from tests.test_end_to_end import (
    ATTIO_TOKEN,
    HUBSPOT_TOKEN,
    PORTAL_LABEL,
    SF_ALIAS,
    World,
    _Tty,
    apply_cli,
    clients,  # noqa: F401  (fixture)
    make_world,
    plan_cli,
    start_client,
)
from tools.crm import attio, hubspot, salesforce
from tools.crm.base import Change, Plan
from tools.crm.safety import Mode, SafetyError
from tools.design import REPO_ROOT, load_design

# --- S1: the production confirmation is tied to the live account -------------------------------------


def _world_for(platform: str, monkeypatch: pytest.MonkeyPatch, *, live: bool) -> World:
    """A sandbox-like account for planning (`live=False`) or a different, production account (`live=True`)."""
    if platform == "salesforce":
        sf = FakeSf(sandbox=not live, name="Acme Live Ltd" if live else "Acme Sandbox Ltd")
        return make_world("salesforce", monkeypatch, sf=sf)
    world = make_world(platform, monkeypatch, labelled=not live)
    if platform == "attio":
        world.fake.name = "Acme Live Workspace" if live else world.fake.name
    else:
        world.fake.portal = 222 if live else 111
        if live:
            world.env["HUBSPOT_TARGET"] = PORTAL_LABEL
    return world


@pytest.mark.parametrize("platform", ["attio", "hubspot", "salesforce"])
def test_a_plan_made_on_a_sandbox_cannot_be_applied_to_production_whatever_is_typed(
    platform, monkeypatch, tmp_path, clients, capsys
):
    """The review's scenario: a plan made on sandbox alias `acme-sbx`, applied with --execute --production to the
    production org "Acme Live Ltd". Typing the sandbox alias used to be enough for 57 writes."""
    planned = _world_for(platform, monkeypatch, live=False)
    design_file = start_client("recruitment-agency", clients)
    plan_file = tmp_path / "plan.json"
    plan = plan_cli(planned, design_file, plan_file)
    assert plan.account  # the live identity is stored in the plan

    world = _world_for(platform, monkeypatch, live=True)
    empty = world.state()
    asked: list[str] = []
    typed = {"attio": "Acme Test Workspace", "hubspot": "HubSpot portal 111", "salesforce": SF_ALIAS}[platform]
    monkeypatch.setattr(sys, "stdin", _Tty())
    monkeypatch.setattr("builtins.input", lambda prompt="": asked.append(prompt) or typed)
    capsys.readouterr()
    assert apply_cli(world, plan_file, clients, "--execute", "--production") == 2
    assert "made for the account" in capsys.readouterr().err
    assert asked == []  # refused before anyone is asked to type anything
    assert world.state() == empty and world.writes_since(0) == []


@pytest.mark.parametrize("platform", ["attio", "hubspot", "salesforce"])
def test_the_prompt_asks_for_the_live_name_and_shows_its_details(platform, monkeypatch, tmp_path, clients, capsys):
    world = _world_for(platform, monkeypatch, live=True)
    design_file = start_client("recruitment-agency", clients)
    plan_file = tmp_path / "plan.json"
    plan_cli(world, design_file, plan_file)
    expected_name = {"attio": "Acme Live Workspace", "hubspot": "HubSpot portal 222", "salesforce": "Acme Live Ltd"}[platform]
    expected_detail = {"attio": "workspace id", "hubspot": "portal id 222", "salesforce": "username "}[platform]
    prompts: list[str] = []
    monkeypatch.setattr(sys, "stdin", _Tty())
    monkeypatch.setattr("builtins.input", lambda prompt="": prompts.append(prompt) or "not the name")
    capsys.readouterr()
    assert apply_cli(world, plan_file, clients, "--execute", "--production") == 2
    shown = capsys.readouterr().out + " ".join(prompts)
    assert expected_name in shown and expected_detail in shown
    assert world.writes_since(0) == []


@pytest.mark.parametrize("platform", ["attio", "hubspot", "salesforce"])
def test_a_plan_with_no_account_identity_is_refused_for_production(platform, monkeypatch, tmp_path, clients, capsys):
    world = _world_for(platform, monkeypatch, live=True)
    design_file = start_client("recruitment-agency", clients)
    plan_file = tmp_path / "plan.json"
    plan_cli(world, design_file, plan_file)
    data = json.loads(plan_file.read_text())
    data["account"] = ""
    plan_file.write_text(json.dumps(data))
    monkeypatch.setattr(sys, "stdin", _Tty())
    monkeypatch.setattr("builtins.input", lambda prompt="": pytest.fail("must not be asked"))
    capsys.readouterr()
    assert apply_cli(world, plan_file, clients, "--execute", "--production") == 2
    assert "no account identity" in capsys.readouterr().err
    assert world.writes_since(0) == []


def test_each_adapter_reads_its_account_from_the_platform(monkeypatch):
    sf = make_world("salesforce", monkeypatch, sf=FakeSf(sandbox=False, name="Acme Live Ltd"))
    acct = salesforce.make_adapter(sf.env, target=None, production=True, runner=sf.fake).read_account()
    assert acct.name == "Acme Live Ltd" and "build-user.live" in acct.detail
    hub = FakeHubSpot(portal=4321, portal_name="Acme Portal")
    acct = hubspot.make_adapter({"HUBSPOT_ACCESS_TOKEN": HUBSPOT_TOKEN, "HUBSPOT_TARGET": "x"}, session=hub).read_account()
    assert acct.name == "Acme Portal" and "4321" in acct.detail
    fake = FakeAttio(name="Acme Workspace")
    acct = attio.make_adapter({"ATTIO_ACCESS_TOKEN": ATTIO_TOKEN}, target=None, production=True, session=fake).read_account()
    assert acct.name == "Acme Workspace"


# --- S2: a HubSpot account is production unless it is a documented test account ----------------------


def _hub_adapter(hub: FakeHubSpot, *, production: bool) -> hubspot.HubSpotAdapter:
    ad = hubspot.make_adapter(
        {"HUBSPOT_ACCESS_TOKEN": HUBSPOT_TOKEN, "HUBSPOT_TARGET": "label"},
        target=None, production=production, session=hub, sleep=lambda _s: None,
    )
    ad.mode = Mode(dry_run=False, production=production, allow_review=False)
    return ad


def _hub_plan(ad: hubspot.HubSpotAdapter) -> Plan:
    design = load_design(REPO_ROOT / "blueprints" / "recruitment-agency")
    return ad.plan(design, ad.read_state())


@pytest.mark.parametrize("account_type", ["STANDARD", "PRODUCTION", "SOMETHING_NEW", "", None])
def test_a_hubspot_account_that_is_not_a_test_account_needs_the_production_flag(account_type):
    hub = FakeHubSpot(account_type=account_type)
    plan = _hub_plan(_hub_adapter(hub, production=False))
    assert plan.changes
    with pytest.raises(SafetyError, match="treated as production"):
        _hub_adapter(hub, production=False).apply(plan, dry_run=False)
    assert hub.writes() == []
    assert _hub_adapter(hub, production=True).apply(plan, dry_run=False).ok  # with --production it goes ahead


@pytest.mark.parametrize("account_type", ["DEVELOPER_TEST", "developer test", "SANDBOX"])
def test_a_documented_test_account_needs_no_production_flag(account_type):
    hub = FakeHubSpot(account_type=account_type)
    plan = _hub_plan(_hub_adapter(hub, production=False))
    assert _hub_adapter(hub, production=False).apply(plan, dry_run=False).ok


def test_an_account_type_that_cannot_be_read_is_production():
    hub = FakeHubSpot(portal=555)
    hub.reply_once("GET", r"/account-info/", Resp(404, {"status": "error"}))
    ident = _hub_adapter(hub, production=False).read_identity()
    assert hubspot.is_production_account(ident.account_type)
    assert hubspot.is_production_account(None) and not hubspot.is_production_account("SANDBOX")


# --- S4: the public claim ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", ["README.md", "CLAUDE.md"])
def test_the_docs_do_not_claim_nothing_is_ever_archived(name):
    text = (REPO_ROOT / name).read_text(encoding="utf-8")
    assert "never delete or archive" not in text.lower()
    assert "nothing is ever deleted" in text.lower()
    assert "--allow-review" in text and "deactivate" in text.lower()


# --- C1: a hand-edited plan's payload does not run as written ----------------------------------------


def _attio_change(requests, kind="add_field", risk="safe") -> Change:
    return Change(kind, "deal.x", {"requests": requests}, risk, "", "Add x")


def test_attio_refuses_a_safe_add_field_that_archives_an_attribute():
    """The review's probe."""
    fake = FakeAttio()
    ad = attio.make_adapter({"ATTIO_ACCESS_TOKEN": ATTIO_TOKEN, "ATTIO_TARGET": "t"}, target=None, production=False,
                            session=fake, sleep=lambda _s: None)
    evil = _attio_change([{"method": "PATCH", "path": "/v2/objects/deals/attributes/amount",
                           "body": {"data": {"is_archived": True}}}])
    with pytest.raises(SafetyError, match="may not"):
        ad.apply(Plan("attio", fake.name, (evil,), account="x"), dry_run=False)
    assert fake.calls == []


@pytest.mark.parametrize("requests,message", [
    ([{"method": "DELETE", "path": "/v2/objects/deals/attributes/amount", "body": {"data": {}}}], "may not"),
    ([{"method": "POST", "path": "/v2/objects/deals/attributes", "body": {"data": {"is_archived": True}}}], "archive"),
    ([{"method": "POST", "path": "/v2/workspace_members", "body": {"data": {}}}], "may not"),
    ([], "no requests"),
])
def test_attio_payloads_must_match_their_kind(requests, message):
    with pytest.raises(SafetyError, match=message):
        attio.check_payload(_attio_change(requests))


def test_attio_only_the_removal_kinds_may_archive_and_only_that():
    ok = _attio_change([{"method": "PATCH", "path": "/v2/lists/sales/attributes/stage/statuses/abc",
                         "body": {"data": {"is_archived": True}}}], kind="remove_stage", risk="needs_review")
    attio.check_payload(ok)
    wider = replace(ok, payload={"requests": [{**ok.payload["requests"][0], "body": {"data": {"is_archived": True, "title": "x"}}}]})
    with pytest.raises(SafetyError):
        attio.check_payload(wider)
    renames_and_archives = replace(ok, kind="rename_stage")
    with pytest.raises(SafetyError):
        attio.check_payload(renames_and_archives)


def _hub_change(kind, payload, risk="safe") -> Change:
    return Change(kind, "deal.x", payload, risk, "", "s")


V = hubspot.V


@pytest.mark.parametrize("change", [
    _hub_change("add_field", {"method": "POST", "path": "/crm/v3/objects/contacts", "body": {"name": "x"}}),
    _hub_change("add_field", {"method": "DELETE", "path": f"/crm/properties/{V}/deals", "body": {"name": "x"}}),
    _hub_change("rename_field", {"method": "PATCH", "path": f"/crm/properties/{V}/deals/amount",
                                 "body": {"label": "x", "archived": True}}),
    _hub_change("rename_field", {"method": "PATCH", "path": f"/crm/properties/{V}/deals/amount",
                                 "body": {"label": "x", "type": "string"}}),
    _hub_change("add_field", {"method": "POST", "path": f"/crm/properties/{V}/deals", "body": {"name": "x", "hidden": True}}),
    _hub_change("add_option", {"path": f"/crm/properties/{V}/deals/x", "value": "a", "label": "A", "extra": 1}),
    _hub_change("add_stage", {"method": "POST", "path": "/crm/v3/owners", "pipeline_path": f"/crm/pipelines/{V}/deals/p",
                              "stage_id": "s", "body": {}}),
    _hub_change("add_object", {"method": "POST", "path": "/settings/v3/users", "body": {}, "object": "x"}),
])
def test_hubspot_payloads_must_match_their_kind(change):
    with pytest.raises(SafetyError):
        hubspot.check_payload(change)


def test_hubspot_refuses_a_hand_edited_plan_before_sending_anything():
    hub = FakeHubSpot()
    ad = _hub_adapter(hub, production=False)
    plan = _hub_plan(ad)
    first = plan.changes[0]
    edited = replace(first, payload={**first.payload, "path": "/crm/v3/objects/contacts"})
    with pytest.raises(SafetyError):
        ad.apply(replace(plan, changes=(edited, *plan.changes[1:])), dry_run=False)
    assert hub.writes() == []


def _sf_plan(monkeypatch, tmp_path, clients_dir) -> tuple[World, Plan]:
    world = make_world("salesforce", monkeypatch)
    design_file = start_client("recruitment-agency", clients_dir)
    return world, plan_cli(world, design_file, tmp_path / "sf.json")


def test_salesforce_refuses_a_change_whose_components_do_not_belong_to_its_kind(monkeypatch, tmp_path, clients):
    world, plan = _sf_plan(monkeypatch, tmp_path, clients)
    field = next(c for c in plan.changes if c.kind == "add_field")
    ad = salesforce.make_adapter(world.env, target=None, production=False, runner=world.fake)
    ad.mode = Mode(dry_run=False, production=False, allow_review=True)
    for payload, message in [
        ({**field.payload, "components": [["PermissionSet", "Everyone"]]}, "may not"),
        ({**field.payload, "components": [["CustomObject", "Foo__c"]]}, "may not"),
        ({**field.payload, "files": {**field.payload["files"], "permissionsets/x.permissionset-meta.xml": "<x/>"}}, "not those"),
        ({**field.payload, "files": {k: v.replace("</CustomField>", "<isActive>false</isActive></CustomField>")
                                     for k, v in field.payload["files"].items()}}, "deactivate"),
    ]:
        with pytest.raises(SafetyError, match=message):
            ad.apply(replace(plan, changes=(replace(field, payload=payload),)), dry_run=False)
    assert world.fake.deploys == []


def test_salesforce_refuses_a_field_file_that_changes_the_live_type(monkeypatch, tmp_path, clients):
    world, plan = _sf_plan(monkeypatch, tmp_path, clients)
    first = Plan(plan.platform, plan.target, tuple(c for c in plan.changes if c.kind in ("add_object", "add_field")), account=plan.account)
    ad = salesforce.make_adapter(world.env, target=None, production=False, runner=world.fake)
    ad.mode = Mode(dry_run=False, production=False, allow_review=True)
    assert ad.apply(first, dry_run=False).ok  # the fields now exist, as Text or Picklist or whatever the design says
    field = next(c for c in first.changes if c.kind == "add_field" and "<type>Text</type>" in "".join(c.payload["files"].values()))
    flipped = {k: v.replace("<type>Text</type>", "<type>Checkbox</type>") for k, v in field.payload["files"].items()}
    deploys = len(world.fake.deploys)
    with pytest.raises(SafetyError, match="Types are never changed"):
        ad.apply(replace(first, changes=(replace(field, payload={**field.payload, "files": flipped}),)), dry_run=False)
    assert len(world.fake.deploys) == deploys


# --- C2: --target is a label ---------------------------------------------------------------------------


def test_apply_target_on_attio_is_a_label_checked_against_attio_target(monkeypatch, tmp_path, clients, capsys):
    world = make_world("attio", monkeypatch)
    design_file = start_client("recruitment-agency", clients)
    plan_file = tmp_path / "plan.json"
    plan_cli(world, design_file, plan_file)
    capsys.readouterr()
    # a label that is not ATTIO_TARGET is refused, whatever the workspace is called
    assert apply_cli(world, plan_file, clients, "--execute", "--target", "something-else") == 2
    assert "does not match ATTIO_TARGET" in capsys.readouterr().err
    assert world.writes_since(0) == []
    # the label itself works even though it differs from the workspace name
    assert apply_cli(world, plan_file, clients, "--execute", "--target", world.env["ATTIO_TARGET"]) == 0
    assert world.writes_since(0)
    # the log keeps the label the person typed and the account identity the plan was made for
    record = json.loads(sorted((clients / "acme" / "build" / "apply-log").glob("*.json"))[-1].read_text())
    assert record["target"] == "sandbox" and "Acme Test Workspace" in record["account"]
