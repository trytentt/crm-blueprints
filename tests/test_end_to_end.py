"""End to end: every blueprint on Attio, HubSpot and Salesforce, through the real CLI entry points.

BRIEF section 12: pull, plan, apply, drift and diff tools work; amending a blueprint produces the right
changes with the removal marked destructive; the safety rules hold. Nothing here touches the network:
the in-memory simulators (`FakeAttio`, `FakeHubSpot`, and `FakeSf` standing in for the `sf` CLI) answer every call. The CLIs are driven through
their `main(argv)` functions, with the adapters built by the real registry from the real `make_adapter`
(only the HTTP session, or for Salesforce the `sf` runner, is swapped for a simulator).
"""

from __future__ import annotations

import copy
import io
import json
import sys
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.attio_stub import FakeAttio, attr_obj
from tests.hubspot_stub import FakeHubSpot
from tests.salesforce_stub import FakeSf, fixture as sf_fixture
from tools import crm_apply, crm_drift, crm_plan, diff_design, new_client, validate
from tools.crm import attio, hubspot, salesforce
from tools.crm.base import Plan
from tools.crm.planner import BUILD_RANK
from tools.crm.registry import get_adapter
from tools.design import REPO_ROOT, load_design

BLUEPRINTS = sorted(p.name for p in (REPO_ROOT / "blueprints").iterdir() if (p / "design.yaml").is_file())
PLATFORM_LIST = ["attio", "hubspot", "salesforce"]
LABELLED_LIST = ["attio", "hubspot"]  # platforms whose production gate is a missing *_TARGET label

ATTIO_TOKEN = "atk_e2e_0123456789abcdef"
HUBSPOT_TOKEN = "pat-eu1-00000000-aaaa-bbbb-cccc-111111111111"
WORKSPACE = "Acme Test Workspace"  # what Attio's /v2/self reports; deliberately not the ATTIO_TARGET label
PORTAL_LABEL = "acme sandbox"
SF_ALIAS = "acme-sbx"
SF_SECRET = "TEST-ONLY-NOT-A-TOKEN"  # the placeholder access token inside the org_display fixtures

ADDED_FIELD = "e2e_added_field"
ADDED_OPTION = "e2e_added_option"
ADDED_STAGE = "e2e_added_stage"


def test_there_are_fifteen_blueprints():
    assert len(BLUEPRINTS) == 15


# --- a simulated workspace and the way the CLIs reach it ------------------------------------------


@dataclass
class World:
    """One simulated CRM account plus the environment and monkeypatching that point the CLIs at it."""

    platform: str
    fake: Any
    env: dict[str, str] = field(default_factory=dict)

    # -- what the simulator holds, and what has been sent to it
    def state(self) -> Any:
        f = self.fake
        if self.platform == "attio":
            return copy.deepcopy((f.objects, f.attrs, f.subs, f.lists))
        if self.platform == "salesforce":
            return copy.deepcopy((f.objects, f.stages, f.processes, f.rt_process, f.rules))
        return copy.deepcopy((f.schemas, f.props, f.groups, f.pipelines, f.labels, f.limits))

    def calls(self) -> list[str]:
        if self.platform == "attio":
            return [f"{m} {p}" for m, p, _a, _b in self.fake.calls]
        if self.platform == "salesforce":
            # `sf` calls: a check-only deploy saves nothing, a real deploy is the only write
            return [
                ("CHECK " if "--dry-run" in a else "POST ") + "deploy" if a[1:3] == ["project", "deploy"]
                else "GET " + " ".join(a[1:3])
                for a in self.fake.calls
            ]
        return [f"{m} {p}" for m, p in self.fake.calls]

    def writes_since(self, mark: int) -> list[str]:
        return [c for c in self.calls()[mark:] if not c.startswith(("GET ", "CHECK "))]

    def live_fields(self, design: Any) -> set[tuple[str, str]]:
        """(object, key) of every field the real adapter reads back, mapped to `design`'s keys."""
        adapter = get_adapter(self.platform, self.env, None, False)
        state = adapter.read_state() if self.platform == "hubspot" else adapter.read_state(design)
        return {(f.object, f.key) for f in state.fields}

    # -- how to call the CLIs
    def client_env(self, **extra: str) -> dict[str, str]:
        return {**self.env, **extra}


def make_world(platform: str, monkeypatch: pytest.MonkeyPatch, *, labelled: bool = True, sf: FakeSf | None = None) -> World:
    """Build a World and patch the platform module's `make_adapter` to use the simulator as its session.

    Salesforce has no label: the org is always named by `SF_TARGET_ORG`, and what makes it production is the org
    itself (pass `sf=FakeSf(sandbox=False)`).
    """
    if platform == "salesforce":
        sfake = sf if sf is not None else FakeSf()
        sf_real = salesforce.make_adapter
        monkeypatch.setattr(salesforce, "make_adapter", partial(sf_real, runner=sfake))
        return World(platform, sfake, {"SF_TARGET_ORG": SF_ALIAS})
    if platform == "attio":
        fake: Any = FakeAttio(name=WORKSPACE, slug="acme-test")
        env = {"ATTIO_ACCESS_TOKEN": ATTIO_TOKEN}
        if labelled:
            env["ATTIO_TARGET"] = "sandbox"
        module = attio
    else:
        fake = FakeHubSpot()
        env = {"HUBSPOT_ACCESS_TOKEN": HUBSPOT_TOKEN}
        if labelled:
            env["HUBSPOT_TARGET"] = PORTAL_LABEL
        module = hubspot
    real = module.make_adapter
    monkeypatch.setattr(module, "make_adapter", partial(real, session=fake, sleep=lambda _s: None))
    return World(platform, fake, env)


class _Tty(io.StringIO):
    def isatty(self) -> bool:
        return True


@pytest.fixture
def clients(tmp_path: Path) -> Path:
    return tmp_path / "clients"


def start_client(blueprint: str, clients: Path, client: str = "acme") -> Path:
    """Run `new_client` and return the client's design.yaml."""
    rc = new_client.main([blueprint, client, "--name", "Acme Ltd", "--clients-dir", str(clients)])
    assert rc == 0
    return clients / client / "design.yaml"


def plan_cli(world: World, design: Path, out: Path) -> Plan:
    rc = crm_plan.main([str(design), "--platform", world.platform, "--out", str(out)], env=world.env)
    assert rc == 0
    return Plan.from_json(out.read_text(encoding="utf-8"))


def apply_cli(world: World, plan_file: Path, clients: Path, *flags: str, env: dict[str, str] | None = None) -> int:
    argv = [str(plan_file), "--clients-dir", str(clients), "--client", "acme", *flags]
    return crm_apply.main(argv, env=env if env is not None else world.env)


def build(world: World, design: Path, clients: Path, tmp_path: Path) -> Plan:
    plan = plan_cli(world, design, tmp_path / "build-plan.json")
    assert apply_cli(world, tmp_path / "build-plan.json", clients, "--execute") == 0
    return plan


# --- editing a client's design ---------------------------------------------------------------------


def _option_keys(options: Any) -> list[str]:
    if isinstance(options, dict):
        return list(options)
    return [o if isinstance(o, str) else o["key"] for o in options]


def _add_option(options: Any, key: str, label: str) -> Any:
    if isinstance(options, dict):
        return {**options, key: label}
    return [*options, key if isinstance(options[0], str) else {"key": key, "label": label}]


def amend_design(path: Path, *, salesforce_org: bool = False) -> dict[str, str]:
    """Add a field, add an option to an existing select, add a stage to an existing pipeline, remove a field.

    Returns the keys touched. The file is rewritten as plain YAML.
    """
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    required = {r for p in data["pipelines"] for s in p["stages"] for r in s.get("required_fields", [])}

    fields = data["add_fields"]
    # not an object's name (every platform creates it with the object), not native, not gating a stage
    # On Salesforce a custom object's `owner` is the standard Owner (D-17), so removing it from the design leaves
    # nothing to remove from the org; the removed field must be one the org really holds.
    never = {"name", "owner"} if salesforce_org else {"name"}
    removable = [f for f in fields if f["key"] not in required and f["key"] not in never and not f.get("native")]
    removed = removable[-1]
    fields.remove(removed)

    select = next(f for f in fields if f["type"] == "select" and f.get("options") and f["key"] not in required)
    select["options"] = _add_option(select["options"], ADDED_OPTION, "E2E added option")

    fields.append(
        {
            "object": "deal",
            "key": ADDED_FIELD,
            "label": "E2E added field",
            "type": "text",
            "description": "A field added by the end-to-end amendment test.",
        }
    )

    # The pipeline with the fewest open stages keeps the design under the eight-open-stage limit.
    # On Salesforce, prefer a pipeline on the deal: only an Opportunity's stage order can be read back (the
    # business process); a custom object's stage picklist is read as the design's order (D-19).
    candidates = data["pipelines"]
    if salesforce_org:
        on_deal = [p for p in candidates if p["object"] == "deal" and sum(x["type"] == "open" for x in p["stages"]) < 8]
        candidates = on_deal or candidates
    pipeline = min(candidates, key=lambda p: sum(1 for s in p["stages"] if s["type"] == "open"))
    first_closed = next(i for i, s in enumerate(pipeline["stages"]) if s["type"] != "open")
    pipeline["stages"].insert(
        first_closed,
        {
            "key": ADDED_STAGE,
            "label": "E2E added stage",
            "type": "open",
            "probability": pipeline["stages"][first_closed - 1].get("probability", 50),
            "exit_criteria": "Entered when the end-to-end amendment test says so.",
        },
    )
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=1000), encoding="utf-8")
    return {
        "removed_object": removed["object"],
        "removed_field": removed["key"],
        "select_field": select["key"],
        "pipeline": pipeline["key"],
        "pipeline_object": pipeline["object"],
    }


# --- the matrix ----------------------------------------------------------------------------------------


@pytest.mark.parametrize("platform", PLATFORM_LIST)
@pytest.mark.parametrize("blueprint", BLUEPRINTS)
def test_blueprint_builds_amends_and_drifts(blueprint, platform, monkeypatch, tmp_path, clients, capsys):
    world = make_world(platform, monkeypatch)
    fake = world.fake

    # a. new_client copies the blueprint
    design_file = start_client(blueprint, clients)
    source = yaml.safe_load((REPO_ROOT / "blueprints" / blueprint / "design.yaml").read_text(encoding="utf-8"))
    copied = yaml.safe_load(design_file.read_text(encoding="utf-8"))
    assert copied.pop("name") == f"Acme Ltd ({source.pop('name')})"
    assert copied == source
    assert (clients / "acme" / "notes.md").is_file() and (clients / "acme" / "CHANGELOG.md").is_file()
    assert (clients / "acme" / "build").is_dir()
    design = load_design(design_file)

    # b. plan against an empty workspace is in build order, then automations and views by hand
    empty = world.state()
    plan_file = tmp_path / "plan.json"
    plan = plan_cli(world, design_file, plan_file)
    assert world.state() == empty and world.writes_since(0) == []
    kinds = [c.kind for c in plan.changes]
    # Salesforce deploys fields before pipelines (a rule or record type names fields), so it has its own order
    rank = salesforce.PHASE if platform == "salesforce" else BUILD_RANK
    ranks = [rank[k] for k in kinds]
    assert ranks == sorted(ranks), f"changes are out of build order: {kinds}"
    assert {"add_object", "add_relationship", "add_pipeline", "add_field"} <= set(kinds) or "add_object" not in kinds
    assert all(c.risk == "safe" for c in plan.changes)
    assert len(kinds) == len(plan.changes) > 20
    titles = [m.title.lower() for m in plan.manual_steps]
    if platform == "salesforce":
        # Flows and list view sorts have no names like "workflow": each automation is a step titled with its
        # name, each view a "Build the view" or "Set the sort on" step, and the automations still come first.
        flows = [titles.index(a.name.lower()) for a in design.automations]
        views = [i for i, t in enumerate(titles) if t.startswith(("build the view ", "set the sort on "))]
        assert all(any(titles[i].endswith(v.name.lower()) for i in views) for v in design.views)
        assert max(flows) < min(views), "automations come before views"
    else:
        assert sum("workflow" in t for t in titles) == len(design.automations)
        assert sum("view" in t and "workflow" not in t for t in titles) >= len(design.views)
        last_workflow = max(i for i, t in enumerate(titles) if "workflow" in t)
        first_view = min(i for i, t in enumerate(titles) if t.startswith(("view:", "saved view:")))
        assert last_workflow < first_view, "automations come before views"
    assert not [m for m in plan.manual_steps if m.risk == "destructive"]

    # c. a dry run changes nothing
    mark = len(world.calls())
    assert apply_cli(world, plan_file, clients) == 0
    out = capsys.readouterr().out
    assert "DRY RUN" in out
    assert world.state() == empty
    assert world.writes_since(mark) == []
    if platform == "salesforce":  # a dry run is a check-only deploy, which the org validates and saves nothing from
        assert [c for c in world.calls()[mark:] if c.endswith("deploy")] == ["CHECK deploy"]

    # d. --execute builds it and writes a redacted log
    assert apply_cli(world, plan_file, clients, "--execute") == 0
    assert "EXECUTED" in capsys.readouterr().out
    built = world.state()
    assert built != empty
    logs = sorted((clients / "acme" / "build" / "apply-log").glob("*.json"))
    assert len(logs) == 2  # the dry run and the real run
    log_text = logs[-1].read_text(encoding="utf-8")
    record = json.loads(log_text)
    assert record["executed"] is True and record["production"] is False and record["platform"] == platform
    assert record["failed"] == [] and record["remaining"] == [] and record["held_for_review"] == []
    assert len(record["applied"]) + len(record["already_satisfied"]) == len(plan.changes)
    assert len(record["applied"]) > 20
    for secret in (ATTIO_TOKEN, HUBSPOT_TOKEN, SF_SECRET):
        assert secret not in log_text

    if platform == "salesforce":
        # every deploy names the org from SF_TARGET_ORG and carries none of the flags that bypass a check
        real = [d for d in fake.deploys if not d["dry_run"]]
        assert 0 < len(real) <= len(plan.changes)
        for d in fake.deploys:
            assert d["argv"][d["argv"].index("--target-org") + 1] == SF_ALIAS
            assert not [a for a in d["argv"] if "ignore" in a or "destructive" in a or a == "--purge-on-delete"]
            assert d["version"] == salesforce.DEFAULT_API_VERSION

    # e. re-plan is empty, and re-applying the same plan is a no-op
    replan = plan_cli(world, design_file, tmp_path / "replan.json")
    assert replan.changes == (), [c.summary for c in replan.changes]
    mark = len(world.calls())
    assert apply_cli(world, plan_file, clients, "--execute") == 0
    assert world.writes_since(mark) == []
    assert world.state() == built
    again = json.loads(sorted((clients / "acme" / "build" / "apply-log").glob("*.json"))[-1].read_text())
    assert again["applied"] == [] and again["failed"] == []
    assert crm_apply.main(
        [str(plan_file), "--clients-dir", str(clients), "--client", "acme", "--execute", "--design", str(design_file)],
        env=world.env,
    ) == 0
    assert world.state() == built

    # g (clean). no drift after a build
    capsys.readouterr()
    assert crm_drift.main([str(design_file), "--platform", platform], env=world.env) == 0
    assert "No drift" in capsys.readouterr().out

    # f. amendment: add a field, add an option, add a stage, remove a field
    old_file = tmp_path / "old-design.yaml"
    old_file.write_text(design_file.read_text(encoding="utf-8"), encoding="utf-8")
    touched = amend_design(design_file, salesforce_org=platform == "salesforce")
    assert validate.main([str(design_file), "--strict"]) == 0
    capsys.readouterr()

    assert diff_design.main([str(old_file), str(design_file)]) == 0
    diff_out = capsys.readouterr().out
    assert "SAFE (applied automatically): 3" in diff_out
    assert diff_out.count("[add_field]") == 1 and diff_out.count("[add_option]") == 1
    assert diff_out.count("[add_stage]") == 1
    assert diff_out.count("[DESTRUCTIVE]") == 1 and "DESTRUCTIVE (never applied" not in diff_out
    assert f"{touched['removed_object']}.{touched['removed_field']}" in diff_out
    assert "3 automatic change(s), 1 manual step(s)." in diff_out
    assert diff_design.main([str(old_file), str(old_file), "--exit-code"]) == 0

    amend_plan_file = tmp_path / "amend-plan.json"
    amend = plan_cli(world, design_file, amend_plan_file)
    assert sorted(c.kind for c in amend.changes) == ["add_field", "add_option", "add_stage"]
    assert {c.risk for c in amend.changes} == {"safe"}
    destructive = [m for m in amend.manual_steps if m.risk == "destructive"]
    assert len(destructive) == 1
    assert touched["removed_field"] in destructive[0].title + destructive[0].reason + destructive[0].done_when
    assert destructive[0].instructions.strip() and "data" in destructive[0].instructions.lower()
    assert world.state() == built  # planning writes nothing

    mark = len(world.calls())
    assert apply_cli(world, amend_plan_file, clients) == 0  # the amendment's dry run saves nothing either
    assert world.state() == built and world.writes_since(mark) == []
    assert apply_cli(world, amend_plan_file, clients, "--execute") == 0  # no --allow-review
    log = json.loads(sorted((clients / "acme" / "build" / "apply-log").glob("*.json"))[-1].read_text())
    assert sorted(c["kind"] for c in log["applied"]) == ["add_field", "add_option", "add_stage"]
    assert log["held_for_review"] == [] and log["failed"] == []
    assert world.state() != built
    # the removal never deleted anything
    assert (touched["removed_object"], touched["removed_field"]) in world.live_fields(load_design(old_file))
    assert (touched["removed_object"], touched["removed_field"]) not in {
        (f.object, f.key) for f in load_design(design_file).fields
    }
    assert not [c for c in world.calls() if c.startswith("DELETE ")]
    # The new stage sits mid-pipeline, but a platform appends it. The re-plan therefore asks for exactly one
    # reorder of that pipeline: a needs_review change on HubSpot, a manual step on Attio (its API cannot reorder)
    # and on Salesforce (D-19: a stage reorder is a manual step).
    final_file = tmp_path / "final.json"
    final = plan_cli(world, design_file, final_file)
    reorders = [c for c in final.changes if c.kind == "reorder_stages"]
    manual_reorders = [m for m in final.manual_steps if m.title.startswith("Reorder stages")]
    assert [c.kind for c in final.changes] == [c.kind for c in reorders]
    if platform == "salesforce" and touched["pipeline_object"] != "deal":
        # a custom object's stage picklist order cannot be read back, so no reorder is ever asked for (D-19)
        assert reorders == [] and manual_reorders == []
    else:
        assert len(reorders) + len(manual_reorders) == 1
    assert all(c.risk == "needs_review" and c.target.endswith(f".{touched['pipeline']}") for c in reorders)
    assert all(touched["pipeline"] in m.title for m in manual_reorders)
    if platform == "hubspot":
        assert apply_cli(world, final_file, clients, "--execute") == 0  # held: no --allow-review
        assert plan_cli(world, design_file, tmp_path / "held.json").changes == final.changes
        assert apply_cli(world, final_file, clients, "--execute", "--allow-review") == 0
        assert plan_cli(world, design_file, tmp_path / "settled.json").changes == ()
    assert len([m for m in final.manual_steps if m.risk == "destructive"]) == 1

    # g (dirty). drift names the leftover field, and an extra added by hand
    capsys.readouterr()
    assert crm_drift.main([str(design_file), "--platform", platform], env=world.env) == 1
    assert touched["removed_field"] in capsys.readouterr().out
    if platform == "attio":
        fake.attrs[("objects", "deals")].append(attr_obj("zz_extra_by_hand", "Zz extra by hand", "text"))
    elif platform == "salesforce":
        fake.objects["Opportunity"]["fields"].append(
            {"name": "Zz_extra_by_hand__c", "label": "Zz extra by hand", "type": "string", "custom": True,
             "length": 255, "picklistValues": [], "referenceTo": [], "nillable": True}
        )
    else:
        fake.props["0-3"]["zz_extra_by_hand"] = {
            "name": "zz_extra_by_hand", "label": "Zz extra by hand", "type": "string", "fieldType": "text",
            "groupName": "dealinformation", "hubspotDefined": False,
            "modificationMetadata": {"readOnlyDefinition": False},
        }
    assert crm_drift.main([str(design_file), "--platform", platform], env=world.env) == 1
    drift_out = capsys.readouterr().out
    assert "zz_extra_by_hand" in drift_out and "DESTRUCTIVE" in drift_out


@pytest.mark.parametrize("platform", PLATFORM_LIST)
def test_drift_reports_an_unbuilt_workspace(platform, monkeypatch, tmp_path, clients, capsys):
    world = make_world(platform, monkeypatch)
    design_file = start_client("recruitment-agency", clients)
    assert crm_drift.main([str(design_file), "--platform", platform], env=world.env) == 1  # nothing built yet
    capsys.readouterr()
    build(world, design_file, clients, tmp_path)
    assert crm_drift.main([str(design_file), "--platform", platform], env=world.env) == 0
    assert world.writes_since(0) != []


# --- h. the production gate -----------------------------------------------------------------------------


@pytest.mark.parametrize("platform", LABELLED_LIST)
@pytest.mark.parametrize("blueprint", BLUEPRINTS)
def test_production_gate(blueprint, platform, monkeypatch, tmp_path, clients, capsys):
    # Plan and build through a labelled (test) account first so a plan file exists; then use an unlabelled one.
    labelled = make_world(platform, monkeypatch)
    design_file = start_client(blueprint, clients)
    plan_file = tmp_path / "plan.json"
    plan_cli(labelled, design_file, plan_file)

    world = make_world(platform, monkeypatch, labelled=False)
    empty = world.state()
    capsys.readouterr()

    # --production without --execute is refused outright
    assert apply_cli(world, plan_file, clients, "--production") == 2
    assert "--production needs --execute" in capsys.readouterr().err

    # no target: refused, nothing written
    assert apply_cli(world, plan_file, clients, "--execute") == 2
    err = capsys.readouterr().err
    assert err.startswith("refused:")
    assert "ATTIO_TARGET" in err if platform == "attio" else "HUBSPOT_TARGET" in err
    assert world.state() == empty and world.writes_since(0) == []
    assert ATTIO_TOKEN not in err and HUBSPOT_TOKEN not in err

    # HubSpot needs a label even for production; give both platforms a name to confirm against
    if platform == "hubspot":
        world.env["HUBSPOT_TARGET"] = PORTAL_LABEL
    name = PORTAL_LABEL if platform == "hubspot" else WORKSPACE
    flags = ("--execute", "--production")

    # no terminal: refused
    monkeypatch.setattr(sys, "stdin", io.StringIO())
    monkeypatch.setattr("builtins.input", lambda prompt="": name)
    assert apply_cli(world, plan_file, clients, *flags) == 2
    assert "interactive terminal" in capsys.readouterr().err
    assert world.state() == empty and world.writes_since(0) == []

    # wrong name: aborts
    monkeypatch.setattr(sys, "stdin", _Tty())
    monkeypatch.setattr("builtins.input", lambda prompt="": "some other account")
    assert apply_cli(world, plan_file, clients, *flags) == 2
    assert "did not match" in capsys.readouterr().err
    assert world.state() == empty and world.writes_since(0) == []

    # the right name goes through, and the log says production
    monkeypatch.setattr("builtins.input", lambda prompt="": name)
    assert apply_cli(world, plan_file, clients, *flags) == 0
    assert world.state() != empty
    record = json.loads(sorted((clients / "acme" / "build" / "apply-log").glob("*.json"))[-1].read_text())
    assert record["production"] is True and record["executed"] is True and record["failed"] == []


@pytest.mark.parametrize("platform", PLATFORM_LIST)
def test_a_labelled_account_needs_no_confirmation(platform, monkeypatch, tmp_path, clients):
    world = make_world(platform, monkeypatch)
    design_file = start_client("recruitment-agency", clients)
    monkeypatch.setattr("builtins.input", lambda prompt="": pytest.fail("a test account must not prompt"))
    build(world, design_file, clients, tmp_path)
    assert world.writes_since(0)


def test_apply_does_not_pass_the_plans_display_name_as_the_target(monkeypatch, tmp_path, clients):
    """Regression: the plan's target is Attio's workspace name; passing it on as --target clashed with ATTIO_TARGET."""
    world = make_world("attio", monkeypatch)
    assert world.env["ATTIO_TARGET"] != WORKSPACE
    design_file = start_client("recruitment-agency", clients)
    plan = plan_cli(world, design_file, tmp_path / "p.json")
    assert plan.target == WORKSPACE
    assert apply_cli(world, tmp_path / "p.json", clients, "--execute") == 0
    assert world.writes_since(0)


# --- Salesforce: where it differs (D-19) ------------------------------------------------------------------


def _production_world(monkeypatch: pytest.MonkeyPatch, edition: str = "Developer Edition") -> World:
    """An org that is not a sandbox. A Developer Edition org counts as production: the safe side is to ask."""
    return make_world("salesforce", monkeypatch, sf=FakeSf(edition=edition, sandbox=False, name="Acme Live Ltd"))


@pytest.mark.parametrize("blueprint", BLUEPRINTS)
def test_production_gate_salesforce(blueprint, monkeypatch, tmp_path, clients, capsys):
    """The gate is the org itself: a non-sandbox org (here a Developer Edition one) needs --production and its typed name."""
    world = _production_world(monkeypatch)
    design_file = start_client(blueprint, clients)
    plan_file = tmp_path / "plan.json"
    plan = plan_cli(world, design_file, plan_file)
    assert plan.target == f"Acme Live Ltd ({SF_ALIAS})"  # what the person must type
    empty = world.state()
    capsys.readouterr()

    # a check-only run on production is allowed and saves nothing
    assert apply_cli(world, plan_file, clients) == 0
    assert "DRY RUN" in capsys.readouterr().out
    assert world.state() == empty and world.writes_since(0) == []

    # --production without --execute is refused outright
    assert apply_cli(world, plan_file, clients, "--production") == 2
    assert "--production needs --execute" in capsys.readouterr().err

    # no org named: refused, naming the variable, and nothing is read or written
    mark = len(world.calls())
    assert apply_cli(world, plan_file, clients, "--execute", env={}) == 2
    err = capsys.readouterr().err
    assert err.startswith("refused:") and "SF_TARGET_ORG" in err
    assert len(world.calls()) == mark

    # a real run on a production org without --production is refused, with nothing deployed
    assert apply_cli(world, plan_file, clients, "--execute") == 2
    assert "--production" in capsys.readouterr().err
    assert world.state() == empty and world.writes_since(0) == []

    flags = ("--execute", "--production")
    # no terminal: refused
    monkeypatch.setattr(sys, "stdin", io.StringIO())
    monkeypatch.setattr("builtins.input", lambda prompt="": plan.target)
    assert apply_cli(world, plan_file, clients, *flags) == 2
    assert "interactive terminal" in capsys.readouterr().err
    assert world.state() == empty and world.writes_since(0) == []

    # the alias alone is not the org's name: aborts
    monkeypatch.setattr(sys, "stdin", _Tty())
    monkeypatch.setattr("builtins.input", lambda prompt="": SF_ALIAS)
    assert apply_cli(world, plan_file, clients, *flags) == 2
    assert "did not match" in capsys.readouterr().err
    assert world.state() == empty and world.writes_since(0) == []

    # the right name goes through, and the log says production
    monkeypatch.setattr("builtins.input", lambda prompt="": plan.target)
    assert apply_cli(world, plan_file, clients, *flags) == 0
    assert world.state() != empty
    record = json.loads(sorted((clients / "acme" / "build" / "apply-log").glob("*.json"))[-1].read_text())
    assert record["production"] is True and record["executed"] is True and record["failed"] == []
    assert SF_SECRET not in json.dumps(record)


@pytest.mark.parametrize("kind", ["sandbox", "scratch"])
def test_a_sandbox_or_scratch_org_needs_no_confirmation(kind, monkeypatch, tmp_path, clients):
    world = make_world("salesforce", monkeypatch, sf=FakeSf(sandbox=kind == "sandbox", scratch=kind == "scratch"))
    design_file = start_client("recruitment-agency", clients)
    monkeypatch.setattr("builtins.input", lambda prompt="": pytest.fail("a test org must not prompt"))
    build(world, design_file, clients, tmp_path)
    assert world.writes_since(0)


@pytest.mark.parametrize("blueprint", BLUEPRINTS)
def test_removing_a_deal_stage_is_a_manual_step_on_salesforce(blueprint, monkeypatch, tmp_path, clients, capsys):
    """D-19: nothing the source deploy can do retires an Opportunity stage, so it is destructive and by hand."""
    world = make_world("salesforce", monkeypatch)
    design_file = start_client(blueprint, clients)
    build(world, design_file, clients, tmp_path)
    data = yaml.safe_load(design_file.read_text(encoding="utf-8"))
    pipeline = next(p for p in data["pipelines"] if p["object"] == "deal")
    # A stage label two pipelines share is one shared value, named differently once only one pipeline keeps it
    # (D-17), so removing a shared stage would rename the other pipeline's value. Remove one only this pipeline has.
    others = {s["label"] for p in data["pipelines"] if p is not pipeline for s in p["stages"]}
    removed = [s for s in pipeline["stages"] if s["type"] == "open" and s["label"] not in others][-1]
    pipeline["stages"].remove(removed)
    design_file.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=1000), encoding="utf-8")
    built = world.state()
    mark = len(world.calls())

    plan = plan_cli(world, design_file, tmp_path / "remove.json")
    assert plan.changes == ()
    destructive = [m for m in plan.manual_steps if m.risk == "destructive"]
    assert len(destructive) == 1 and removed["key"] in destructive[0].title
    assert destructive[0].instructions.strip() and "data" in destructive[0].instructions.lower()
    assert apply_cli(world, tmp_path / "remove.json", clients, "--execute") == 0
    assert world.state() == built and world.writes_since(mark) == []
    assert crm_drift.main([str(design_file), "--platform", "salesforce"], env=world.env) == 1
    capsys.readouterr()


# --- Salesforce: a Professional edition org cannot take a metadata deploy ---------------------------------------


def test_professional_edition_org_gets_only_manual_steps_and_nothing_is_deployed(monkeypatch, tmp_path, clients, capsys):
    """Everything becomes a manual step pointing at the build sheet, and no deploy of any kind is attempted."""
    enterprise = make_world("salesforce", monkeypatch)
    design_file = start_client("recruitment-agency", clients)
    enterprise_plan = plan_cli(enterprise, design_file, tmp_path / "enterprise-plan.json")
    assert enterprise_plan.changes  # the same design on an Enterprise org is automatic

    world = make_world("salesforce", monkeypatch, sf=FakeSf(edition="Professional Edition"))
    empty = world.state()
    plan_file = tmp_path / "pro-plan.json"
    plan = plan_cli(world, design_file, plan_file)
    assert plan.changes == ()
    by_hand = [m for m in plan.manual_steps if "Professional Edition cannot use the Metadata API" in m.reason]
    assert len(by_hand) >= len(enterprise_plan.changes)  # one manual step per change that would have been automatic
    assert all("build-sheet.md" in m.reason for m in by_hand)
    assert {m.title for m in by_hand} >= {c.summary for c in enterprise_plan.changes}
    assert not [m for m in plan.manual_steps if m.risk == "destructive"]

    # applying that plan, dry or real, is a clean no-op: no deploy, no error
    for flags in ((), ("--execute",)):
        assert apply_cli(world, plan_file, clients, *flags) == 0
    assert world.fake.deploys == [] and world.state() == empty

    # applying a plan made for an Enterprise org to a Professional one changes nothing either, and says so
    capsys.readouterr()
    assert apply_cli(world, tmp_path / "enterprise-plan.json", clients, "--execute") == 0
    out = capsys.readouterr().out
    assert world.fake.deploys == [] and world.writes_since(0) == [] and world.state() == empty
    log = json.loads(sorted((clients / "acme" / "build" / "apply-log").glob("*.json"))[-1].read_text())
    assert log["applied"] == [], "nothing was deployed, so nothing was applied"
    assert len(log["remaining"]) == len(enterprise_plan.changes)
    assert "Applied: 0" in out

    # an unbuilt Professional org is not "no drift"
    assert crm_drift.main([str(design_file), "--platform", "salesforce"], env=world.env) == 1
    drift_out = capsys.readouterr().out
    assert "No drift" not in drift_out and "Professional Edition cannot use the Metadata API" in drift_out


def test_a_failed_salesforce_deploy_stops_reports_and_the_same_plan_resumes(monkeypatch, tmp_path, clients, capsys):
    """The org refuses the second deploy: the run stops, names what was applied, failed and left, and re-running finishes."""
    world = make_world("salesforce", monkeypatch)
    fake = world.fake
    design_file = start_client("b2b-saas-sales-led", clients)
    plan_file = tmp_path / "plan.json"
    plan = plan_cli(world, design_file, plan_file)

    fake.script = [None, sf_fixture("deploy_failure_object.json")]  # the first deploy lands, the second is refused
    capsys.readouterr()
    assert apply_cli(world, plan_file, clients, "--execute") == 1
    out = capsys.readouterr().out
    assert "Failed: 1" in out
    record = json.loads(sorted((clients / "acme" / "build" / "apply-log").glob("*.json"))[-1].read_text())
    assert len(record["failed"]) == 1 and record["applied"]
    done = len(record["applied"]) + len(record["already_satisfied"])
    assert done + 1 + len(record["remaining"]) == len(plan.changes)  # nothing is lost between the three lists
    assert len([d for d in fake.deploys if not d["dry_run"]]) == len(record["applied"]) + 1
    # the refused deploy's staging folder is left under the client's build/ to inspect; the passing ones are gone
    kept = sorted(p.name for p in (clients / "acme" / "build" / "salesforce").iterdir())
    assert len(kept) == 1 and kept[0].startswith("sf-deploy-")
    assert world.state() != World("salesforce", FakeSf(), {}).state()  # the first deploy stayed

    # the cause is fixed: the same plan resumes where it stopped and the org ends up exactly as designed
    assert apply_cli(world, plan_file, clients, "--execute") == 0
    assert plan_cli(world, design_file, tmp_path / "again.json").changes == ()
    assert crm_drift.main([str(design_file), "--platform", "salesforce"], env=world.env) == 0
