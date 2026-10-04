"""HubSpot generator: payload shapes, manual steps, plan requirements, determinism and staleness."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from tools import generate
from tools.design import load_design
from tools.generators import hubspot as hs

ALL_TYPES = {
    "text": ("string", "text"),
    "long_text": ("string", "textarea"),
    "select": ("enumeration", "select"),
    "multi_select": ("enumeration", "checkbox"),
    "number": ("number", "number"),
    "currency": ("number", "number"),
    "percent": ("number", "number"),
    "date": ("date", "date"),
    "datetime": ("datetime", "date"),
    "checkbox": ("bool", "booleancheckbox"),
    "url": ("string", "text"),
    "email": ("string", "text"),
    "phone": ("string", "phonenumber"),
    "user": ("enumeration", "select"),
}


def _field(ftype: str) -> dict:
    f = {"object": "deal", "key": f"f_{ftype}", "label": f"F {ftype}", "type": ftype, "description": f"A {ftype}."}
    if ftype in ("select", "multi_select"):
        f["options"] = {"a_one": "A one", "b_two": "B two"}
    return f


@pytest.fixture
def design(design_dict, write_design):
    design_dict["add_fields"] += [_field(t) for t in ALL_TYPES]
    design_dict["add_fields"].append(
        {"object": "project", "key": "name", "label": "Name", "type": "text", "description": "Project name.", "required": True}
    )
    design_dict["add_fields"].append(
        {"object": "project", "key": "budget", "label": "Budget", "type": "currency", "description": "Money.", "required": True}
    )
    return load_design(write_design(design_dict))


def requests_of(design, builder):
    return builder(design)


def prop(design, name):
    return next(r["body"] for r in hs.property_requests(design) if r["body"].get("name") == name)


@pytest.mark.parametrize("ftype,expected", sorted(ALL_TYPES.items()))
def test_type_and_field_type_per_canonical_type(design, ftype, expected):
    body = prop(design, f"f_{ftype}")
    assert (body["type"], body["fieldType"]) == expected
    assert body["groupName"] == "test_design"


def test_extras_for_lossy_and_special_types(design):
    assert prop(design, "f_currency")["showCurrencySymbol"] is True
    assert prop(design, "f_percent")["numberDisplayHint"] == "percentage"
    assert prop(design, "f_email")["textDisplayHint"] == "email"
    user = prop(design, "f_user")
    assert user["externalOptions"] is True and user["referencedObjectType"] == "OWNER"
    options = prop(design, "f_multi_select")["options"]
    assert options[1] == {"label": "B two", "value": "b_two", "displayOrder": 1, "hidden": False}


def test_native_properties_are_skipped(design):
    names = [r["body"]["name"] for r in hs.property_requests(design) if r["method"] == "POST"]
    assert "dealname" not in names and "amount" not in names and "name" not in [n for n in names if n == "dealname"]
    assert "f_text" in names


def test_schema_sends_all_nine_required_fields(design):
    (req,) = hs.schema_requests(design)
    assert req["method"] == "POST" and req["path"] == f"/crm-object-schemas/{hs.API_VERSION}/schemas"
    body = req["body"]
    nine = {
        "allowsSensitiveProperties", "associatedObjects", "labels", "name", "properties",
        "requiredProperties", "searchableProperties", "secondaryDisplayProperties",
        "shouldCreateSameObjectAssociation",
    }
    assert nine <= set(body)
    assert body["name"] == "project"
    assert body["labels"] == {"singular": "Project", "plural": "Projects"}
    assert body["associatedObjects"] == ["0-2"]  # project_company
    assert body["primaryDisplayProperty"] == "name" == body["properties"][0]["name"]
    assert body["requiredProperties"] == ["name"]
    assert "groupName" not in body["properties"][0]


def test_required_custom_properties_are_patched_after_creation(design):
    patches = [r for r in hs.property_requests(design) if r["method"] == "PATCH"]
    (patch,) = patches
    assert patch["path"].endswith("/schemas/{objectTypeId.project}")
    assert patch["body"] == {"clearDescription": False, "requiredProperties": ["name", "budget"]}
    assert hs.property_requests(design)[-1] == patch


def test_custom_object_requests_use_placeholder(design):
    group = [r for r in hs.group_requests(design) if "project" in r["path"]]
    assert group[0]["path"] == f"/crm/properties/{hs.API_VERSION}/{{objectTypeId.project}}/groups"
    doc = hs.build_payloads(design)["property-groups.json"]
    assert "{objectTypeId.project}" in doc["placeholders"]


def test_property_group_named_after_design_and_override(design_dict, write_design):
    design_dict["platform_overrides"] = {
        "hubspot": {
            "objects": {"project": {"property_group": "delivery"}},
            "fields": {"deal.lost_reason": {"property_group": "dealinformation"}},
        }
    }
    d = load_design(write_design(design_dict))
    assert prop(d, "lost_reason")["groupName"] == "dealinformation"
    assert prop(d, "status")["groupName"] == "delivery"
    assert prop(d, "next_step_date")["groupName"] == "test_design"
    names = [(r["path"].split("/")[-2], r["body"]["name"]) for r in hs.group_requests(d)]
    assert ("deals", "test_design") in names
    assert not any(n == "dealinformation" for _, n in names)  # HubSpot's own group is not created


def test_object_type_id_override_skips_schema(design_dict, write_design):
    design_dict["platform_overrides"] = {"hubspot": {"objects": {"project": {"object_type_id": "2-1234567"}}}}
    d = load_design(write_design(design_dict))
    assert hs.schema_requests(d) == []
    paths = [r["path"] for r in hs.property_requests(d)]
    assert f"/crm/properties/{hs.API_VERSION}/2-1234567" in paths
    assert not any("{objectTypeId" in r["path"] for r in hs.property_requests(d))
    assert any("existing object" in s["title"] for s in hs.manual_steps(d))


def test_native_field_options_become_patch(design_dict, write_design):
    design_dict["add_fields"].append(
        {"object": "deal", "key": "description", "label": "Description", "type": "select", "description": "x"}
    )
    # Redefining a core field is a design error; use the native_names path on a copy of the field instead.
    from dataclasses import replace

    d = load_design(write_design({k: v for k, v in design_dict.items() if k != "add_fields"} | {"add_fields": []}))
    fields = tuple(
        replace(f, type="select", options=(hs_option("a", "A"),)) if (f.object, f.key) == ("deal", "next_step") else f
        for f in d.fields
    )
    d = replace(d, fields=fields)
    patch = next(r for r in hs.property_requests(d) if r["method"] == "PATCH")
    assert patch["path"] == f"/crm/properties/{hs.API_VERSION}/deals/hs_next_step"
    assert patch["body"]["options"][0]["value"] == "a"


def hs_option(key, label):
    from tools.design import Option

    return Option(key, label)


def test_deal_pipeline_probabilities(design):
    (req,) = hs.pipeline_requests(design)
    assert req["path"] == f"/crm/pipelines/{hs.API_VERSION}/deals"
    body = req["body"]
    assert body["label"] == "Sales" and body["pipelineId"] == "sales" and body["displayOrder"] == 1
    metas = {s["stageId"]: s["metadata"] for s in body["stages"]}
    assert metas == {
        "sales__discovery": {"probability": "0.2"},
        "sales__won": {"probability": "1.0"},
        "sales__lost": {"probability": "0.0"},
    }
    assert all(isinstance(m["probability"], str) for m in metas.values())
    assert [s["displayOrder"] for s in body["stages"]] == [0, 1, 2]


@pytest.mark.parametrize("value,text", [(0, "0.0"), (100, "1.0"), (20, "0.2"), (65, "0.65"), (33.3, "0.333"), (None, "0.0")])
def test_probability_string(value, text):
    assert hs.probability_string(value) == text


def test_custom_object_pipeline_uses_is_closed_and_notes_oq1(design_dict, write_design):
    design_dict["add_fields"].append(
        {"object": "project", "key": "lost_why", "label": "Why", "type": "select", "description": "x", "options": ["a"]}
    )
    design_dict["pipelines"].append(
        {
            "object": "project", "key": "delivery", "name": "Delivery",
            "stages": [
                {"key": "live", "label": "Live", "type": "open", "probability": 50, "exit_criteria": "Entered when live."},
                {"key": "done", "label": "Done", "type": "won", "probability": 100, "exit_criteria": "Entered when done."},
                {"key": "dropped", "label": "Dropped", "type": "lost", "probability": 0,
                 "exit_criteria": "Entered when dropped.", "required_fields": ["lost_why"]},
            ],
        }
    )
    d = load_design(write_design(design_dict))
    req = [r for r in hs.pipeline_requests(d) if "project" in r["path"]][0]
    assert req["path"] == f"/crm/pipelines/{hs.API_VERSION}/{{objectTypeId.project}}"
    assert [s["metadata"] for s in req["body"]["stages"]] == [
        {"isClosed": "false"}, {"isClosed": "true"}, {"isClosed": "true"},
    ]
    assert "OQ-1" in req["note"]
    assert req["body"]["stages"][0]["stageId"] == "delivery__live"
    rows = {r["feature"] for r in hs.plan_features(d)}
    assert "Not supported on custom object pipelines: probability, won versus lost" in rows
    assert any("Check closed stages of Delivery" in s["title"] for s in hs.manual_steps(d))


def test_association_labels_and_limits(design_dict, write_design):
    design_dict["add_relationships"].append(
        {"key": "project_deal", "from": "project", "to": "deal", "cardinality": "one_to_many",
         "from_label": "Deals", "to_label": "Project", "purpose": "Links."}
    )
    d = load_design(write_design(design_dict))
    reqs = hs.association_requests(d)
    labels = [r for r in reqs if r["path"].endswith("/labels")]
    assert labels[0]["path"] == f"/crm/associations/{hs.API_VERSION}/{{objectTypeId.project}}/companies/labels"
    assert labels[0]["body"] == {"name": "project_company", "label": "Company", "inverseLabel": "Projects"}
    assert all(r["method"] == "POST" for r in reqs)
    limits = [r for r in reqs if "definitions/configurations" in r["path"]]
    many_to_one = limits[0]
    assert many_to_one["path"].endswith("/configurations/{objectTypeId.project}/companies/batch/create")
    assert many_to_one["body"]["inputs"] == [
        {"category": "USER_DEFINED", "typeId": "{typeId.project_company.project_to_company}", "maxToObjectIds": 1}
    ]
    one_to_many = limits[1]  # the cap sits on the other direction
    assert one_to_many["path"].endswith("/configurations/deals/{objectTypeId.project}/batch/create")
    assert one_to_many["body"]["inputs"][0]["typeId"] == "{typeId.project_deal.deal_to_project}"
    assert "project_company" not in " ".join(r["body"].get("name", "") for r in reqs if "person_company" in r["body"].get("name", ""))


def test_native_relationships_are_not_sent(design):
    names = [r["body"].get("name") for r in hs.association_requests(design)]
    assert "person_company" not in names and "deal_company" not in names and "deal_person" not in names


def test_manual_steps_cover_ui_only_features(design):
    steps = hs.manual_steps(design)
    titles = [s["title"] for s in steps]
    assert any(t == "Require Next step date to enter Discovery (Sales)" for t in titles)
    assert any(t.startswith("Require Lost reason to enter Lost") for t in titles)
    assert sum(t.startswith("Workflow:") for t in titles) == 3
    assert sum(t.startswith("Saved view:") for t in titles) == 3
    assert any(t.startswith("Make Deal Name required") for t in titles)
    assert any(t == "Set roles and access" for t in titles)
    for s in steps:
        assert s["where"] and s["why"] and s["done_when"]
    gate = next(s for s in steps if s["title"].startswith("Require Next step date"))
    assert "Conditional logic rules" in gate["where"] and gate["where"].startswith("Settings > Data Management")
    text = hs.render_manual_steps(design)
    assert "Why it is manual" in text and "Done when" in text


def test_plan_requirements_list_tiers_and_sources(design):
    text = hs.render_plan_requirements(design)
    assert "**Minimum tier: Enterprise.**" in text
    rows = {r["feature"]: r for r in hs.plan_features(design)}
    assert rows["Custom objects"]["tier"].startswith("Enterprise")
    assert rows["Association labels"]["tier"].startswith("Professional or Enterprise")
    assert rows["Workflows"]["tier"] == "Professional or Enterprise"
    assert "Saved views" in rows and "Conditional stage properties (required fields per stage)" in rows
    assert all(r["source"].startswith("https://") for r in rows.values())
    assert "https://knowledge.hubspot.com/object-settings/create-and-use-association-labels" in text
    assert "https://developers.hubspot.com/docs/api-reference/latest/crm/objects/schemas/guide.md" in text


def test_plan_requirements_drop_unused_features(design_dict, write_design):
    design_dict["add_objects"] = []
    design_dict["add_relationships"] = []
    design_dict["add_fields"] = [f for f in design_dict["add_fields"] if f["object"] == "deal"]
    design_dict["automations"] = []
    design_dict["views"] = []
    d = load_design(write_design(design_dict))
    rows = {r["feature"] for r in hs.plan_features(d)}
    assert not rows & {"Custom objects", "Association labels", "Workflows", "Saved views"}
    assert "Minimum tier: Enterprise" not in hs.render_plan_requirements(d)


def test_api_version_held_in_one_constant(design, monkeypatch):
    monkeypatch.setattr(hs, "API_VERSION", "2030-01")
    docs = hs.build_payloads(design)
    for doc in docs.values():
        assert doc["api_version"] == "2030-01"
        assert all("/2030-01/" in r["path"] for r in doc["requests"])


def test_build_sheet_uses_hubspot_ui_paths(design):
    text = hs.render_build_sheet(design, "hubspot", hs.HubSpotHooks(design)) if hasattr(hs, "render_build_sheet") else ""
    assert "Settings > Data Management > Objects > Create custom object (needs Enterprise)" in text
    assert "Pipelines tab > Create pipeline" in text
    assert "Done when:" in text


def test_generate_writes_all_files_and_is_deterministic(design, tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    written = hs.generate(design, a)
    hs.generate(design, b)
    names = sorted(p.name for p in written)
    assert names == sorted(
        ["schemas.json", "property-groups.json", "properties.json", "pipelines.json", "associations.json",
         "build-sheet.md", "manual-steps.md", "plan-requirements.md"]
    )
    for n in names:
        assert (a / n).read_bytes() == (b / n).read_bytes()
        assert (a / n).read_text().endswith("\n")
    for n in names:
        if n.endswith(".json"):
            text = (a / n).read_text()
            assert json.loads(text)["requests"] is not None
            assert text == json.dumps(json.loads(text), indent=2, ensure_ascii=False) + "\n"


def test_check_detects_stale_hubspot_files(design_dict, write_design, tmp_path):
    bp = tmp_path / "bp"
    bp.mkdir()
    shutil.copy(write_design(design_dict), bp / "design.yaml")
    ok, _ = generate.generate_blueprint(bp, ["hubspot"], check=False)
    assert ok
    ok, msgs = generate.generate_blueprint(bp, ["hubspot"], check=True)
    assert ok and any("up to date" in m for m in msgs)
    target = bp / "hubspot" / "pipelines.json"
    original = target.read_text()
    target.write_text(original.replace('"1.0"', '"0.9"'))
    ok, msgs = generate.generate_blueprint(bp, ["hubspot"], check=True)
    assert not ok and "changed: pipelines.json" in "\n".join(msgs)
    target.write_text(original)
    (bp / "hubspot" / "plan-requirements.md").unlink()
    ok, msgs = generate.generate_blueprint(bp, ["hubspot"], check=True)
    assert not ok and "missing: plan-requirements.md" in "\n".join(msgs)


def test_committed_hubspot_output_is_current():
    """Every blueprint that already has a hubspot folder matches a fresh generation."""
    repo = Path(__file__).resolve().parent.parent
    stale = []
    for design_path in sorted((repo / "blueprints").glob("*/design.yaml")):
        bp = design_path.parent
        if not (bp / "hubspot").is_dir():
            continue
        ok, msgs = generate.generate_blueprint(bp, ["hubspot"], check=True)
        if not ok:
            stale.append("\n".join(msgs))
    assert not stale, stale


def test_stage_ids_scoped_to_pipeline_when_keys_repeat(design_dict, write_design):
    stages = lambda: [
        {"key": "proposal", "label": "Proposal", "type": "open", "probability": 40, "exit_criteria": "Entered when sent."},
        {"key": "won", "label": "Won", "type": "won", "probability": 100, "exit_criteria": "Entered when signed."},
        {"key": "lost", "label": "Lost", "type": "lost", "probability": 0, "exit_criteria": "Entered when no.",
         "required_fields": ["lost_reason"]},
    ]
    design_dict["pipelines"][0]["stages"] = stages()
    design_dict["pipelines"].append({"object": "deal", "key": "renewals", "name": "Renewals", "stages": stages()})
    d = load_design(write_design(design_dict))
    ids = [s["stageId"] for r in hs.pipeline_requests(d) for s in r["body"]["stages"]]
    assert len(ids) == len(set(ids)) == 6
    assert "sales__proposal" in ids and "renewals__proposal" in ids
