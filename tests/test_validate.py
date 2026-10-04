"""Every validator rule has a passing case (the base design) and a failing case."""

from __future__ import annotations

import pytest

from tools.validate import main, validate_file


def issues(write_design, data):
    return validate_file(write_design(data))


def errors(write_design, data):
    return [i for i in issues(write_design, data) if i.severity == "error"]


def warnings(write_design, data):
    return [i for i in issues(write_design, data) if i.severity == "warning"]


def has(found, severity, fragment):
    return any(i.severity == severity and fragment in f"{i.path} {i.message}" for i in found)


def test_base_design_is_clean(write_design, design_dict):
    assert issues(write_design, design_dict) == []


def field(d, obj, key):
    return next(f for f in d["add_fields"] if f["object"] == obj and f["key"] == key)


def stage(d, key):
    return next(s for s in d["pipelines"][0]["stages"] if s["key"] == key)


# Each case: (id, mutate(design), expected severity, fragment of path/message)
def _bad_type(d): field(d, "deal", "next_step_date")["type"] = "datetimez"
def _select_no_options(d): field(d, "deal", "lost_reason")["options"] = {}
def _text_with_options(d): field(d, "deal", "next_step_date")["options"] = {"a": "A"}
def _field_bad_key(d): field(d, "deal", "next_step_date")["key"] = "NextStep"
def _field_dup(d): d["add_fields"].append(dict(field(d, "deal", "next_step_date")))
def _object_bad_key(d): d["add_objects"][0]["key"] = "Project-X"
def _object_dup(d): d["add_objects"].append(dict(d["add_objects"][0]))
def _option_bad_key(d): field(d, "deal", "lost_reason")["options"] = {"Bad Key": "Bad"}
def _field_no_desc(d): field(d, "deal", "next_step_date")["description"] = ""
def _object_no_desc(d): d["add_objects"][0]["description"] = ""
def _field_unknown_object(d): field(d, "deal", "next_step_date")["object"] = "ghost"
def _rel_bad_end(d): d["add_relationships"][0]["to"] = "ghost"
def _rel_bad_cardinality(d): d["add_relationships"][0]["cardinality"] = "lots"
def _rel_dup(d): d["add_relationships"].append(dict(d["add_relationships"][0]))
def _pipeline_bad_object(d): d["pipelines"][0]["object"] = "ghost"
def _required_field_missing(d): stage(d, "discovery")["required_fields"] = ["ghost_field"]
def _view_bad_object(d): d["views"][0]["object"] = "ghost"
def _too_many_open(d):
    base = stage(d, "discovery")
    d["pipelines"][0]["stages"] = [
        {**base, "key": f"s{i}", "label": f"S{i}"} for i in range(9)
    ] + [s for s in d["pipelines"][0]["stages"] if s["type"] != "open"]
def _no_won(d): d["pipelines"][0]["stages"] = [s for s in d["pipelines"][0]["stages"] if s["type"] != "won"]
def _no_lost(d): d["pipelines"][0]["stages"] = [s for s in d["pipelines"][0]["stages"] if s["type"] != "lost"]
def _lost_no_reason(d): stage(d, "lost")["required_fields"] = []
def _lost_reason_not_select(d): stage(d, "lost")["required_fields"] = ["next_step_date"]
def _prob_high(d): stage(d, "discovery")["probability"] = 120
def _prob_negative(d): stage(d, "discovery")["probability"] = -1
def _prob_missing(d): del stage(d, "discovery")["probability"]
def _won_not_100(d): stage(d, "won")["probability"] = 90
def _lost_not_0(d): stage(d, "lost")["probability"] = 5
def _exit_wrong(d): stage(d, "discovery")["exit_criteria"] = "When a call has happened."
def _exit_missing(d): stage(d, "won")["exit_criteria"] = ""
def _bad_stage_type(d): stage(d, "discovery")["type"] = "pending"
def _stage_dup(d): d["pipelines"][0]["stages"].append(dict(stage(d, "discovery")))
def _override_bad_key(d): d["platform_overrides"] = {"hubspot": {"fields": {"deal.lost_reason": {"api_slug": "x"}}}}
def _override_bad_platform(d): d["platform_overrides"] = {"pipedrive": {}}
def _override_missing_target(d): d["platform_overrides"] = {"salesforce": {"objects": {"ghost": {"api_name": "G__c"}}}}
def _override_missing_field(d): d["platform_overrides"] = {"hubspot": {"fields": {"deal.ghost": {"property_group": "g"}}}}
def _override_not_mapping(d): d["platform_overrides"] = {"attio": "slug"}
def _name_missing(d): d["name"] = ""

ERROR_CASES = [
    ("invalid type", _bad_type, "type"),
    ("select without options", _select_no_options, "needs options"),
    ("non-select with options", _text_with_options, "must not have options"),
    ("field key not snake_case", _field_bad_key, "snake_case"),
    ("duplicate field", _field_dup, "duplicate field"),
    ("object key not snake_case", _object_bad_key, "snake_case"),
    ("duplicate object", _object_dup, "duplicate object"),
    ("option key not snake_case", _option_bad_key, "snake_case"),
    ("field without description", _field_no_desc, "needs a description"),
    ("object without description", _object_no_desc, "needs a description"),
    ("field on unknown object", _field_unknown_object, "does not exist"),
    ("relationship end missing", _rel_bad_end, "does not exist"),
    ("invalid cardinality", _rel_bad_cardinality, "cardinality"),
    ("duplicate relationship", _rel_dup, "duplicate relationship"),
    ("pipeline object missing", _pipeline_bad_object, "does not exist"),
    ("required field missing", _required_field_missing, "does not exist on object"),
    ("view object missing", _view_bad_object, "does not exist"),
    ("more than 8 open stages", _too_many_open, "9 open stages"),
    ("no won stage", _no_won, "won stage"),
    ("no lost stage", _no_lost, "lost stage"),
    ("lost without reason", _lost_no_reason, "reason field"),
    ("lost reason not a select", _lost_reason_not_select, "reason field"),
    ("probability above 100", _prob_high, "outside 0 to 100"),
    ("probability below 0", _prob_negative, "outside 0 to 100"),
    ("probability missing", _prob_missing, "probability"),
    ("won not 100", _won_not_100, "probability 100"),
    ("lost not 0", _lost_not_0, "probability 0"),
    ("exit criteria wrong start", _exit_wrong, "Entered when"),
    ("exit criteria missing", _exit_missing, "Entered when"),
    ("invalid stage type", _bad_stage_type, "type"),
    ("duplicate stage", _stage_dup, "duplicate stage"),
    ("override key not allowed", _override_bad_key, "allows only"),
    ("override unknown platform", _override_bad_platform, "unknown platform"),
    ("override missing object", _override_missing_target, "does not exist"),
    ("override missing field", _override_missing_field, "does not exist"),
    ("override not a mapping", _override_not_mapping, "mapping"),
    ("name missing", _name_missing, "name"),
]


@pytest.mark.parametrize("mutate,fragment", [(c[1], c[2]) for c in ERROR_CASES], ids=[c[0] for c in ERROR_CASES])
def test_rule_fails(write_design, design_dict, mutate, fragment):
    mutate(design_dict)
    found = errors(write_design, design_dict)
    assert has(found, "error", fragment), [i.format("x") for i in found]


def test_exactly_eight_open_stages_is_fine(write_design, design_dict):
    base = stage(design_dict, "discovery")
    others = [s for s in design_dict["pipelines"][0]["stages"] if s["type"] != "open"]
    design_dict["pipelines"][0]["stages"] = [
        {**base, "key": f"s{i}", "label": f"S{i}"} for i in range(8)
    ] + others
    assert issues(write_design, design_dict) == []


def test_override_valid_cases_pass(write_design, design_dict):
    design_dict["platform_overrides"] = {
        "hubspot": {"fields": {"deal.lost_reason": {"property_group": "dealinformation"}},
                    "objects": {"project": {"object_type_id": "2-1"}}},
        "salesforce": {"objects": {"project": {"api_name": "Project__c", "record_type": "Delivery"}}},
        "attio": {"objects": {"project": {"api_slug": "projects"}}},
    }
    assert issues(write_design, design_dict) == []


def test_unknown_key_reported_as_error_with_path(write_design, design_dict):
    design_dict["add_field"] = []
    found = issues(write_design, design_dict)
    assert len(found) == 1 and found[0].severity == "error" and "add_field" in found[0].path


def test_core_field_override_reported_as_error(write_design, design_dict):
    design_dict["add_fields"].append({"object": "deal", "key": "amount", "type": "number", "description": "x"})
    found = issues(write_design, design_dict)
    assert has(found, "error", "core field")


@pytest.mark.parametrize("section,label", [("decisions", "decisions"), ("automations", "automations"), ("views", "views")])
def test_fewer_than_three_is_warning(write_design, design_dict, section, label):
    design_dict[section] = design_dict[section][:2]
    assert errors(write_design, design_dict) == []
    assert has(warnings(write_design, design_dict), "warning", label)


def test_delivery_warning_when_no_custom_object(write_design, design_dict):
    design_dict["add_objects"] = []
    design_dict["add_fields"] = [f for f in design_dict["add_fields"] if f["object"] != "project"]
    design_dict["add_relationships"] = []
    found = warnings(write_design, design_dict)
    assert has(found, "warning", "principle 8")


def test_delivery_warning_suppressed_by_decision(write_design, design_dict):
    design_dict["add_objects"] = []
    design_dict["add_fields"] = [f for f in design_dict["add_fields"] if f["object"] != "project"]
    design_dict["add_relationships"] = []
    design_dict["decisions"][0] = {
        "key": "delivery_note", "question": "How is delivery tracked?",
        "recommended_default": "Outside the CRM, in the project tool.",
    }
    assert issues(write_design, design_dict) == []


def test_delivery_stage_on_deal_pipeline_warns(write_design, design_dict):
    d = design_dict
    d["pipelines"][0]["stages"].insert(
        1,
        {"key": "implementation", "label": "Implementation", "type": "open", "probability": 50,
         "exit_criteria": "Entered when work starts."},
    )
    assert has(warnings(write_design, d), "warning", "delivery-type stage")


def test_delivery_stage_on_non_deal_pipeline_is_fine(write_design, design_dict):
    d = design_dict
    d["add_fields"].append(
        {"object": "project", "key": "lost_why", "type": "select", "description": "Why.", "options": ["a"]}
    )
    d["pipelines"].append({
        "object": "project", "key": "delivery", "name": "Delivery",
        "stages": [
            {"key": "implementation", "label": "Implementation", "type": "open", "probability": 50,
             "exit_criteria": "Entered when work starts."},
            {"key": "done", "label": "Done", "type": "won", "probability": 100,
             "exit_criteria": "Entered when handed over."},
            {"key": "cancelled", "label": "Cancelled", "type": "lost", "probability": 0,
             "exit_criteria": "Entered when stopped.", "required_fields": ["lost_why"]},
        ],
    })
    assert issues(write_design, d) == []


def test_relationship_without_purpose_warns(write_design, design_dict):
    design_dict["add_relationships"][0]["purpose"] = ""
    assert has(warnings(write_design, design_dict), "warning", "purpose")


# --- CLI ---------------------------------------------------------------------------------------


def test_cli_exit_codes(write_design, design_dict, capsys):
    ok = write_design(design_dict, "ok.yaml")
    assert main([str(ok)]) == 0
    design_dict["add_fields"][0]["type"] = "nope"
    bad = write_design(design_dict, "bad.yaml")
    assert main([str(bad)]) == 1
    out = capsys.readouterr().out
    assert "bad.yaml: error: fields[deal.lost_reason].type" in out


def test_cli_strict_fails_on_warning_only(write_design, design_dict):
    design_dict["views"] = design_dict["views"][:2]
    path = write_design(design_dict)
    assert main([str(path)]) == 0
    assert main([str(path), "--strict"]) == 1


def test_cli_accepts_directory(write_design, design_dict):
    path = write_design(design_dict)
    assert main([str(path.parent)]) == 0


def test_cli_requires_input():
    with pytest.raises(SystemExit):
        main([])


def test_cli_all_validates_every_blueprint_strictly():
    assert main(["--all", "--strict"]) == 0
