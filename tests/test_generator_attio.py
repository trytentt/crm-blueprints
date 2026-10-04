"""The Attio generator: payload shapes, relationships, pipelines, manual steps, determinism, --check."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import generate
from tools.design import load_design
from tools.generators import attio

ALL_TYPES = [
    "text", "long_text", "select", "multi_select", "number", "currency", "percent", "date",
    "datetime", "checkbox", "url", "email", "phone", "user",
]
EXPECTED = {
    "text": ("text", False),
    "long_text": ("text", False),
    "select": ("select", False),
    "multi_select": ("select", True),
    "number": ("number", False),
    "currency": ("currency", False),
    "percent": ("number", False),
    "date": ("date", False),
    "datetime": ("timestamp", False),
    "checkbox": ("checkbox", False),
    "url": ("text", False),
    "email": ("email-address", False),
    "phone": ("phone-number", False),
    "user": ("actor-reference", False),
}


def _write(data, directory: Path) -> Path:
    import yaml

    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "design.yaml"
    path.write_text(yaml.safe_dump(data))
    return path


@pytest.fixture
def design_with_all_types(design_dict, write_design):
    for t in ALL_TYPES:
        field = {"object": "project", "key": f"f_{t}", "label": f"F {t}", "type": t, "description": f"A {t}."}
        if t in ("select", "multi_select"):
            field["options"] = {"a": "Option A", "b": "Option B"}
        design_dict["add_fields"].append(field)
    return load_design(write_design(design_dict))


@pytest.fixture
def design(design_dict, write_design):
    return load_design(write_design(design_dict))


def payloads(d):
    return attio.build_payloads(d)


def requests_for(d, name):
    return payloads(d)[name]["requests"]


def test_every_canonical_type_has_the_researched_attio_shape(design_with_all_types):
    reqs = requests_for(design_with_all_types, "attributes.json")
    by_slug = {r["body"]["data"]["api_slug"]: r for r in reqs if r["path"].endswith("/attributes")}
    for t, (attio_type, multi) in EXPECTED.items():
        req = by_slug[f"f_{t}"]
        assert req["method"] == "POST"
        assert req["path"] == "/v2/objects/projects/attributes"
        data = req["body"]["data"]
        assert data["type"] == attio_type
        assert data["is_multiselect"] is multi
        # The API wants every one of these keys on every create.
        for key in ("title", "description", "api_slug", "type", "is_required", "is_unique",
                    "is_multiselect", "config"):
            assert key in data
        assert data["is_required"] is False
        if t == "currency":
            assert data["config"] == {"currency": {"default_currency_code": "GBP", "display_type": "symbol"}}
        else:
            assert data["config"] == {}


def test_select_options_follow_their_attribute(design_with_all_types):
    reqs = requests_for(design_with_all_types, "attributes.json")
    paths = [r["path"] for r in reqs]
    i = paths.index("/v2/objects/projects/attributes/f_select/options")
    assert reqs[i]["body"] == {"data": {"title": "Option A"}}
    assert reqs[i + 1]["body"] == {"data": {"title": "Option B"}}
    attr_index = next(n for n, r in enumerate(reqs) if r["body"]["data"].get("api_slug") == "f_select")
    assert attr_index < i


def test_lossy_types_say_so_in_the_description(design_with_all_types):
    reqs = requests_for(design_with_all_types, "attributes.json")
    desc = {r["body"]["data"]["api_slug"]: r["body"]["data"]["description"] for r in reqs
            if r["path"].endswith("/attributes")}
    assert "0 to 100" in desc["f_percent"]
    assert "no URL type" in desc["f_url"]


def test_native_fields_and_objects_are_skipped(design):
    d = payloads(design)
    object_slugs = [r["body"]["data"]["api_slug"] for r in d["objects.json"]["requests"]]
    assert object_slugs == ["projects"]
    slugs = [r["body"]["data"].get("api_slug") for r in d["attributes.json"]["requests"]]
    # company.name, person.email, deal.amount and similar are standard attributes.
    for native in ("domains", "email_addresses", "value"):
        assert native not in slugs
    assert "next_step_date" in slugs


def test_reserved_slug_gets_object_prefix(design):
    slugs = [r["body"]["data"].get("api_slug") for r in requests_for(design, "attributes.json")]
    assert "company_owner" in slugs
    assert "owner" not in slugs


def test_object_override_drives_slug_everywhere(design_dict, write_design):
    design_dict["platform_overrides"] = {"attio": {"objects": {"project": {"api_slug": "delivery_projects"}}}}
    d = load_design(write_design(design_dict))
    p = payloads(d)
    assert p["objects.json"]["requests"][0]["body"]["data"]["api_slug"] == "delivery_projects"
    assert any(r["path"].startswith("/v2/objects/delivery_projects/attributes")
               for r in p["attributes.json"]["requests"])
    assert p["relationships.json"]["requests"][0]["path"] == "/v2/objects/delivery_projects/attributes"


def test_field_override_drives_slug(design_dict, write_design):
    design_dict["platform_overrides"] = {"attio": {"fields": {"deal.next_step_date": {"api_slug": "nsd"}}}}
    d = load_design(write_design(design_dict))
    slugs = [r["body"]["data"].get("api_slug") for r in requests_for(d, "attributes.json")]
    assert "nsd" in slugs and "next_step_date" not in slugs


@pytest.mark.parametrize(
    "cardinality, parent, reverse",
    [
        ("one_to_one", False, False),
        ("one_to_many", True, False),
        ("many_to_one", False, True),
        ("many_to_many", True, True),
    ],
)
def test_relationship_cardinality_mapping(design_dict, write_design, cardinality, parent, reverse):
    design_dict["add_relationships"][0]["cardinality"] = cardinality
    d = load_design(write_design(design_dict))
    reqs = requests_for(d, "relationships.json")
    assert len(reqs) == 1  # one call makes both sides; native links are skipped
    req = reqs[0]
    assert req["method"] == "POST"
    assert req["path"] == "/v2/objects/projects/attributes"
    data = req["body"]["data"]
    assert data["type"] == "record-reference"
    assert data["is_multiselect"] is parent
    assert data["config"] == {"record_reference": {"allowed_objects": ["companies"]}}
    assert data["relationship"] == {
        "object": "companies", "title": "Projects", "api_slug": "projects", "is_multiselect": reverse,
    }
    assert data["title"] == "Company" and data["api_slug"] == "company"


def test_pipeline_becomes_list_with_stage_attribute(design):
    reqs = requests_for(design, "lists.json")
    assert reqs[0] == {
        "method": "POST",
        "path": "/v2/lists",
        "body": {"data": {
            "name": "Sales", "api_slug": "sales", "parent_object": "deals",
            "workspace_access": "full-access", "workspace_member_access": [],
        }},
    }
    stage = reqs[1]
    assert stage["path"] == "/v2/lists/sales/attributes"
    assert stage["body"]["data"]["type"] == "status"
    assert stage["body"]["data"]["api_slug"] == "stage"
    assert stage["body"]["data"]["config"] == {}
    assert "Entered when a call has happened." in stage["body"]["data"]["description"]
    prob = reqs[2]["body"]["data"]
    assert (prob["api_slug"], prob["type"]) == ("probability", "number")
    lost = [r for r in reqs if r["body"]["data"].get("api_slug") == "lost_reason"]
    assert len(lost) == 1 and lost[0]["body"]["data"]["type"] == "select"
    options = [r["body"]["data"]["title"] for r in reqs if r["path"].endswith("/lost_reason/options")]
    assert options == ["Price", "Timing"]


def test_statuses_in_order_with_won_and_lost(design):
    reqs = requests_for(design, "statuses.json")
    assert [r["body"]["data"]["title"] for r in reqs] == ["Discovery", "Won", "Lost"]
    assert all(r["path"] == "/v2/lists/sales/attributes/stage/statuses" for r in reqs)
    celebrations = {r["body"]["data"]["title"]: r["body"]["data"]["celebration_enabled"] for r in reqs}
    assert celebrations == {"Discovery": False, "Won": True, "Lost": False}


def test_files_are_ordered_and_cite_sources(design):
    p = payloads(design)
    assert [p[n]["order"] for n in
            ("objects.json", "relationships.json", "lists.json", "statuses.json", "attributes.json")] == [1, 2, 3, 4, 5]
    for doc in p.values():
        assert doc["source"] and all(s.startswith("https://") for s in doc["source"])


def test_manual_steps_cover_what_the_api_cannot_do(design, tmp_path):
    attio.generate(design, tmp_path)
    text = (tmp_path / "manual-steps.md").read_text()
    for needle in (
        "Enable the Deals object",
        "Stage probability for Sales",
        "Stage gate (stage gate): Sales, Discovery",
        "Stage gate (lost reason): Sales, Lost",
        "Won and lost in Sales",
        "Workflow: Auto 0",
        "View: View 0",
        "Set roles and access",
        "Workspace settings, then Members",
    ):
        assert needle in text, needle
    # Each step names a UI path and a reason.
    assert text.count("- [ ] Where:") == text.count("- Why it is manual:") == text.count("- Done when:")


def test_lossy_decisions_only_for_types_used(design_with_all_types, tmp_path):
    from tests.conftest import base_design

    small_design = load_design(_write(base_design(), tmp_path / "small"))
    a, b = tmp_path / "a", tmp_path / "b"
    attio.generate(design_with_all_types, a)
    attio.generate(small_design, b)
    full = (a / "manual-steps.md").read_text()
    small = (b / "manual-steps.md").read_text()
    assert "Percent fields are plain numbers" in full
    assert "Percent fields are plain numbers" not in small


def test_generate_writes_the_seven_files(design, tmp_path):
    out = tmp_path / "out"
    written = attio.generate(design, out)
    assert sorted(p.name for p in written) == sorted(
        ["objects.json", "attributes.json", "relationships.json", "statuses.json", "lists.json",
         "build-sheet.md", "manual-steps.md"])
    assert sorted(p.name for p in out.iterdir()) == sorted(p.name for p in written)
    for p in written:
        if p.suffix == ".json":
            assert p.read_text().endswith("}\n")
            json.loads(p.read_text())
    assert "Workspace settings, then Objects, then New object" in (out / "build-sheet.md").read_text()


def test_generation_is_deterministic(design, tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    attio.generate(design, a)
    attio.generate(design, b)
    assert len(list(a.iterdir())) == 7
    for f in sorted(a.iterdir()):
        assert f.read_bytes() == (b / f.name).read_bytes()


@pytest.fixture
def blueprint(tmp_path, write_design, design_dict) -> Path:
    bp = tmp_path / "bp"
    bp.mkdir()
    (bp / "design.yaml").write_text(write_design(design_dict).read_text())
    return bp


def test_check_detects_staleness_for_attio(blueprint, capsys):
    argv = [str(blueprint), "--platform", "attio"]
    assert generate.main(argv) == 0
    assert generate.main(argv + ["--check"]) == 0
    assert "up to date" in capsys.readouterr().out
    target = blueprint / "attio" / "statuses.json"
    target.write_text(target.read_text().replace("Won", "Wonn"))
    assert generate.main(argv + ["--check"]) == 1
    assert "changed: statuses.json" in capsys.readouterr().out
    target.unlink()
    assert generate.main(argv + ["--check"]) == 1
    assert "missing: statuses.json" in capsys.readouterr().out


def test_committed_blueprints_are_current():
    repo = Path(__file__).resolve().parent.parent
    for design_file in sorted((repo / "blueprints").glob("*/design.yaml")):
        bp = design_file.parent
        if not (bp / "attio").is_dir():
            continue
        ok, messages = generate.generate_blueprint(bp, ["attio"], check=True)
        assert ok, messages
