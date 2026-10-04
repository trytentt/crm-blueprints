"""Design loading and merging."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from tools.design import (
    CORE_MODEL_PATH,
    FIELD_TYPES,
    PLATFORMS,
    DesignError,
    Option,
    load_core_model,
    load_design,
)

REPO = Path(__file__).resolve().parent.parent


def test_constants_match_contract():
    assert PLATFORMS == ("attio", "hubspot", "salesforce")
    assert len(FIELD_TYPES) == 14


def test_core_model_has_three_objects_and_native_names():
    core = load_core_model(CORE_MODEL_PATH)
    assert [o.key for o in core.objects] == ["company", "person", "deal"]
    names = {o.key: o.native_names for o in core.objects}
    assert names["company"] == {"attio": "companies", "hubspot": "companies", "salesforce": "Account"}
    assert names["person"]["hubspot"] == "contacts"
    assert names["deal"]["salesforce"] == "Opportunity"
    assert all(o.kind == "core" for o in core.objects)


def test_core_fields_native_names_cover_native_platforms():
    for f in load_core_model().fields:
        for platform in f.native:
            assert platform in f.native_names, f"{f.object}.{f.key} lacks a native name for {platform}"
        assert f.description


def test_core_relationships():
    rels = {r.key: r for r in load_core_model().relationships}
    assert (rels["person_company"].from_object, rels["person_company"].to_object) == ("person", "company")
    assert rels["person_company"].cardinality == "many_to_one"
    assert rels["deal_company"].to_object == "company"
    assert (rels["deal_person"].from_object, rels["deal_person"].to_object) == ("deal", "person")
    assert all(set(r.native) == set(PLATFORMS) for r in rels.values())


def test_merge_core_plus_additions(design_dict, write_design):
    d = load_design(write_design(design_dict))
    assert [o.key for o in d.objects] == ["company", "person", "deal", "project"]
    assert d.get_object("project").kind == "custom"
    assert d.get_object("deal").kind == "core"
    # core fields come first, additions after
    deal_fields = [f.key for f in d.fields_of("deal")]
    assert deal_fields.index("amount") < deal_fields.index("lost_reason")
    assert {r.key for r in d.relationships} >= {"person_company", "project_company"}
    assert d.name == "Test design"


def test_add_fields_may_target_core_and_custom_objects(design_dict, write_design):
    d = load_design(write_design(design_dict))
    assert d.get_field("deal", "lost_reason") is not None
    assert d.get_field("project", "status") is not None


def test_options_three_shapes(design_dict, write_design):
    design_dict["add_fields"].append(
        {"object": "deal", "key": "tier", "type": "select", "description": "x",
         "options": [{"key": "mid_market", "label": "Mid-market"}, "big_one"]}
    )
    d = load_design(write_design(design_dict))
    assert d.get_field("deal", "lost_reason").options == (Option("price", "Price"), Option("timing", "Timing"))
    assert d.get_field("project", "status").options == (Option("not_started", "Not started"), Option("live", "Live"))
    assert d.get_field("deal", "tier").options == (Option("mid_market", "Mid-market"), Option("big_one", "Big one"))


def test_override_of_core_field_is_error(design_dict, write_design):
    design_dict["add_fields"].append(
        {"object": "deal", "key": "amount", "type": "number", "description": "again"}
    )
    with pytest.raises(DesignError, match="core field"):
        load_design(write_design(design_dict))


def test_redefining_core_object_is_error(design_dict, write_design):
    design_dict["add_objects"].append(
        {"key": "company", "label": "Company", "description": "again"}
    )
    with pytest.raises(DesignError, match="core object"):
        load_design(write_design(design_dict))


def test_unknown_key_is_error(design_dict, write_design):
    design_dict["add_field"] = []
    with pytest.raises(DesignError, match="unknown key"):
        load_design(write_design(design_dict))


def test_unsupported_extends_is_error(design_dict, write_design):
    design_dict["extends"] = "other"
    with pytest.raises(DesignError, match="extends"):
        load_design(write_design(design_dict))


def test_wrong_container_type_is_error(design_dict, write_design):
    design_dict["add_fields"] = {"not": "a list"}
    with pytest.raises(DesignError, match="expected a list"):
        load_design(write_design(design_dict))


def test_invalid_yaml_and_missing_file(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("a: [unclosed", encoding="utf-8")
    with pytest.raises(DesignError, match="invalid YAML"):
        load_design(bad)
    with pytest.raises(DesignError, match="cannot read"):
        load_design(tmp_path / "missing.yaml")


def test_directory_path_resolves_design_yaml(design_dict, write_design):
    path = write_design(design_dict)
    assert load_design(path.parent).name == "Test design"


def test_dataclasses_are_frozen(design_dict, write_design):
    d = load_design(write_design(design_dict))
    with pytest.raises(dataclasses.FrozenInstanceError):
        d.name = "x"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        d.objects[0].key = "x"  # type: ignore[misc]


def test_probability_non_number_loads_as_none(design_dict, write_design):
    design_dict["pipelines"][0]["stages"][0]["probability"] = "high"
    d = load_design(write_design(design_dict))
    assert d.pipelines[0].stages[0].probability is None


def test_reference_blueprint_loads():
    d = load_design(REPO / "blueprints" / "b2b-saas-sales-led")
    assert {o.key for o in d.custom_objects} == {"subscription", "onboarding"}
    assert {p.key for p in d.pipelines} == {"new_business", "renewals_expansion"}
