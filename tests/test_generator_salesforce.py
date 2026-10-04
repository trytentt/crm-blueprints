"""The Salesforce generator: metadata shapes, stage flags, validation rules, manifest, determinism, --check."""

from __future__ import annotations

import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from tools import generate
from tools.design import load_design
from tools.generators import salesforce as sf

NS = "{http://soap.sforce.com/2006/04/metadata}"
BASE = "force-app/main/default"
REPO = Path(__file__).resolve().parent.parent

ALL_TYPES = [
    "text", "long_text", "select", "multi_select", "number", "currency", "percent", "date",
    "datetime", "checkbox", "url", "email", "phone", "user",
]
# canonical type -> (Salesforce type, extra elements that must be present)
EXPECTED = {
    "text": ("Text", {"length": "255"}),
    "long_text": ("LongTextArea", {"length": "32768", "visibleLines": "6"}),
    "select": ("Picklist", {}),
    "multi_select": ("MultiselectPicklist", {"visibleLines": "4"}),
    "number": ("Number", {"precision": "18", "scale": "0"}),
    "currency": ("Currency", {"precision": "18", "scale": "2"}),
    "percent": ("Percent", {"precision": "5", "scale": "2"}),
    "date": ("Date", {}),
    "datetime": ("DateTime", {}),
    "checkbox": ("Checkbox", {"defaultValue": "false"}),
    "url": ("Url", {}),
    "email": ("Email", {}),
    "phone": ("Phone", {}),
    "user": ("Lookup", {"referenceTo": "User", "deleteConstraint": "SetNull"}),
}


def _field(ftype: str) -> dict:
    f = {"object": "project", "key": f"f_{ftype}", "label": f"F {ftype}", "type": ftype, "description": f"A {ftype}."}
    if ftype in ("select", "multi_select"):
        f["options"] = {"a_one": "A one", "b_two": "B two"}
    return f


@pytest.fixture
def design(design_dict, write_design):
    design_dict["add_fields"] += [_field(t) for t in ALL_TYPES]
    return load_design(write_design(design_dict))


@pytest.fixture
def out(design, tmp_path):
    sf.generate(design, tmp_path / "salesforce")
    return tmp_path / "salesforce"


def parse(path: Path) -> ET.Element:
    return ET.parse(path).getroot()


def child(root: ET.Element, tag: str) -> str | None:
    el = root.find(NS + tag)
    return None if el is None else (el.text or "")


def field_root(out: Path, obj: str, api: str) -> ET.Element:
    return parse(out / BASE / "objects" / obj / "fields" / f"{api}.field-meta.xml")


def test_every_xml_file_parses_and_has_the_house_format(out):
    files = [p for p in out.rglob("*.xml")]
    assert files
    for p in files:
        parse(p)
        text = p.read_text(encoding="utf-8")
        assert text.startswith('<?xml version="1.0" encoding="UTF-8"?>\n'), p
        assert text.endswith("</" + text.split("\n")[1].split()[0][1:] + ">\n"), p
        for line in text.splitlines():
            assert (len(line) - len(line.lstrip(" "))) % 4 == 0, (p, line)
        assert "\t" not in text


@pytest.mark.parametrize("ftype", ALL_TYPES)
def test_field_xml_per_canonical_type(out, ftype):
    root = field_root(out, "Project__c", f"F_{ftype}__c")
    sf_type, extras = EXPECTED[ftype]
    assert child(root, "type") == sf_type
    assert child(root, "fullName") == f"F_{ftype}__c"
    assert child(root, "description") == f"A {ftype}."
    for tag, value in extras.items():
        assert child(root, tag) == value, tag
    if ftype in ("select", "multi_select"):
        vs = root.find(NS + "valueSet")
        assert child(vs, "restricted") == "true"
        values = [child(v, "fullName") for v in vs.iter(NS + "value")]
        assert values == ["A one", "B two"]
    if ftype in ("checkbox", "user"):
        assert root.find(NS + "required") is None


def test_standard_objects_get_child_files_only(out):
    objects = out / BASE / "objects"
    assert not (objects / "Opportunity" / "Opportunity.object-meta.xml").exists()
    assert (objects / "Opportunity" / "fields" / "Next_step_date__c.field-meta.xml").exists()
    assert (objects / "Project__c" / "Project__c.object-meta.xml").exists()


def test_custom_object_file(out):
    root = parse(out / BASE / "objects/Project__c/Project__c.object-meta.xml")
    assert child(root, "label") == "Project"
    assert child(root, "pluralLabel") == "Projects"
    assert child(root, "sharingModel") == "ReadWrite"
    assert child(root, "deploymentStatus") == "Deployed"
    assert child(root.find(NS + "nameField"), "type") == "Text"


def stage_values(out) -> dict[str, dict[str, str]]:
    root = parse(out / BASE / "standardValueSets/OpportunityStage.standardValueSet-meta.xml")
    return {child(v, "fullName"): {c.tag.removeprefix(NS): c.text for c in v} for v in root.findall(NS + "standardValue")}


def test_stage_value_flags(out):
    v = stage_values(out)
    assert list(v) == ["Discovery", "Won", "Lost"]
    assert (v["Discovery"]["closed"], v["Discovery"]["won"], v["Discovery"]["probability"],
            v["Discovery"]["forecastCategory"]) == ("false", "false", "20", "Pipeline")
    assert (v["Won"]["closed"], v["Won"]["won"], v["Won"]["probability"], v["Won"]["forecastCategory"]) == (
        "true", "true", "100", "Closed")
    assert (v["Lost"]["closed"], v["Lost"]["won"], v["Lost"]["probability"], v["Lost"]["forecastCategory"]) == (
        "true", "false", "0", "Omitted")


def rule(out, name) -> ET.Element:
    return parse(out / BASE / "objects/Opportunity/validationRules" / f"{name}.validationRule-meta.xml")


def test_gated_stage_formula_and_lost_reason_rule(out):
    gate = rule(out, "Gate_sales_discovery")
    assert child(gate, "errorConditionFormula") == (
        'AND(RecordType.DeveloperName = "Sales", CASE(StageName, "Discovery", 1, "Won", 2, 0) >= 1, '
        "ISBLANK(Next_step_date__c))"
    )
    assert child(gate, "errorDisplayField") == "Next_step_date__c"
    assert child(gate, "active") == "true"
    lost = rule(out, "Lost_sales_lost")
    assert child(lost, "errorConditionFormula") == (
        'AND(RecordType.DeveloperName = "Sales", ISPICKVAL(StageName, "Lost"), ISBLANK(TEXT(Lost_reason__c)))'
    )
    assert child(lost, "errorMessage")
    assert lost.find(NS + "validationMessage") is None


def test_formula_escapes_in_the_xml_file(out):
    text = (out / BASE / "objects/Opportunity/validationRules/Gate_sales_discovery.validationRule-meta.xml").read_text()
    assert "&gt;= 1" in text and ">= 1" not in text


def test_record_type_references_its_business_process(out):
    rt = parse(out / BASE / "objects/Opportunity/recordTypes/Sales.recordType-meta.xml")
    bp = parse(out / BASE / "objects/Opportunity/businessProcesses/Sales.businessProcess-meta.xml")
    assert child(rt, "businessProcess") == child(bp, "fullName") == "Sales"
    assert child(rt, "active") == "true"
    assert [child(v, "fullName") for v in bp.findall(NS + "values")] == ["Discovery", "Won", "Lost"]
    assert [child(v, "default") for v in bp.findall(NS + "values")] == ["true", "false", "false"]


def test_path_and_settings(out):
    path = parse(out / BASE / "pathAssistants/Sales_path.pathAssistant-meta.xml")
    assert child(path, "entityName") == "Opportunity"
    assert child(path, "fieldName") == "StageName"
    assert child(path, "recordTypeName") == "Sales"
    steps = path.findall(NS + "pathAssistantSteps")
    assert [child(s, "picklistValueName") for s in steps] == ["Discovery", "Won", "Lost"]
    assert child(steps[0], "info") == "Entered when a call has happened."
    settings = parse(out / BASE / "settings/PathAssistant.settings-meta.xml")
    assert child(settings, "pathAssistantEnabled") == "true"


def member_of(rel: str) -> tuple[str, str] | None:
    """Independent of the generator: derive (type, member) from a source-format path."""
    parts = rel.split("/")
    name = parts[-1]
    if parts[0] == "objects":
        obj = parts[1]
        if len(parts) == 3:
            return "CustomObject", obj
        folder = {"fields": ("CustomField", ".field-meta.xml"), "validationRules": ("ValidationRule", ".validationRule-meta.xml"),
                  "recordTypes": ("RecordType", ".recordType-meta.xml"),
                  "businessProcesses": ("BusinessProcess", ".businessProcess-meta.xml"),
                  "listViews": ("ListView", ".listView-meta.xml")}[parts[2]]
        return folder[0], f"{obj}.{name.removesuffix(folder[1])}"
    table = {"standardValueSets": ("StandardValueSet", ".standardValueSet-meta.xml"),
             "pathAssistants": ("PathAssistant", ".pathAssistant-meta.xml"),
             "permissionsets": ("PermissionSet", ".permissionset-meta.xml"),
             "settings": ("Settings", ".settings-meta.xml")}
    ctype, suffix = table[parts[0]]
    return ctype, name.removesuffix(suffix)


def manifest(out: Path) -> tuple[set[tuple[str, str]], str]:
    root = parse(out / "package.xml")
    members = set()
    for t in root.findall(NS + "types"):
        for m in t.findall(NS + "members"):
            members.add((child(t, "name"), m.text))
    return members, child(root, "version")


def assert_manifest_matches(out: Path) -> None:
    base = out / BASE
    present = {member_of(str(p.relative_to(base))) for p in base.rglob("*") if p.is_file()}
    members, version = manifest(out)
    assert members == present
    assert version == "67.0"


def test_package_xml_lists_exactly_the_files_present(out):
    assert_manifest_matches(out)


def test_project_file_pins_the_api_version(out):
    import json

    data = json.loads((out / "sfdx-project.json").read_text())
    assert data["sourceApiVersion"] == "67.0"
    assert data["packageDirectories"][0]["path"] == "force-app"


def test_data_protection_fields_carry_compliance_elements(design_dict, write_design, tmp_path):
    design_dict["add_fields"] += [
        {"object": "person", "key": "income", "label": "Income", "type": "currency",
         "description": "DATA PROTECTION: personal financial data. Banded."},
        {"object": "person", "key": "plain", "label": "Plain", "type": "text", "description": "Nothing special."},
        {"object": "person", "key": "pay", "label": "Pay", "type": "currency",
         "description": "Pay as told. Sensitive personal data."},
    ]
    sf.generate(load_design(write_design(design_dict)), tmp_path)
    flagged = field_root(tmp_path, "Contact", "Income__c")
    assert child(flagged, "complianceGroup") == "PII;GDPR"
    assert child(flagged, "securityClassification") == "Confidential"
    assert child(field_root(tmp_path, "Contact", "Pay__c"), "securityClassification") == "Restricted"
    plain = field_root(tmp_path, "Contact", "Plain__c")
    assert plain.find(NS + "complianceGroup") is None and plain.find(NS + "securityClassification") is None
    assert "Check the data classification elements" in (tmp_path / "manual-steps.md").read_text()


def test_permission_set_grants_non_required_custom_fields_only(design_dict, write_design, tmp_path):
    design_dict["add_fields"] += [
        {"object": "project", "key": "name", "label": "Name", "type": "text", "description": "Name.", "required": True},
        {"object": "project", "key": "ref", "label": "Ref", "type": "text", "description": "Ref.", "required": True},
        {"object": "project", "key": "note", "label": "Note", "type": "text", "description": "Note."},
    ]
    sf.generate(load_design(write_design(design_dict)), tmp_path)
    ps = next((tmp_path / BASE / "permissionsets").glob("*.xml"))
    root = parse(ps)
    fields = {child(p, "field"): (child(p, "editable"), child(p, "readable")) for p in root.findall(NS + "fieldPermissions")}
    assert fields["Project__c.Note__c"] == ("true", "true")
    assert "Project__c.Ref__c" not in fields  # required
    assert "Project__c.Name" not in fields
    assert "Opportunity.Next_step_date__c" in fields
    assert "Opportunity.Amount" not in fields  # standard field
    assert [child(r, "recordType") for r in root.findall(NS + "recordTypeVisibilities")] == ["Opportunity.Sales"]


def test_overrides_are_respected(design_dict, write_design, tmp_path):
    design_dict["platform_overrides"] = {"salesforce": {
        "objects": {"project": {"api_name": "Engagement__c"}, "deal": {"record_type": "Main_pipeline"}},
        "fields": {"project.status": {"api_name": "Project_state__c"}},
    }}
    sf.generate(load_design(write_design(design_dict)), tmp_path)
    assert (tmp_path / BASE / "objects/Engagement__c/Engagement__c.object-meta.xml").exists()
    assert (tmp_path / BASE / "objects/Engagement__c/fields/Project_state__c.field-meta.xml").exists()
    assert (tmp_path / BASE / "objects/Opportunity/recordTypes/Main_pipeline.recordType-meta.xml").exists()
    assert 'RecordType.DeveloperName = "Main_pipeline"' in (
        tmp_path / BASE / "objects/Opportunity/validationRules/Gate_sales_discovery.validationRule-meta.xml").read_text()


def test_bad_api_name_override_is_refused(design_dict, write_design, tmp_path):
    design_dict["platform_overrides"] = {"salesforce": {"objects": {"project": {"api_name": "bad name__c"}}}}
    with pytest.raises(sf.SalesforceGenerationError):
        sf.generate(load_design(write_design(design_dict)), tmp_path)


def test_long_names_stay_within_forty_characters_and_unique(design_dict, write_design, tmp_path):
    for i in range(2):
        design_dict["add_fields"].append({
            "object": "project", "key": "a_very_long_field_name_that_goes_on_and_on_and_on_" + str(i),
            "label": f"Long {i}", "type": "text", "description": "Long."})
    sf.generate(load_design(write_design(design_dict)), tmp_path)
    names = [p.name.removesuffix(".field-meta.xml") for p in (tmp_path / BASE / "objects/Project__c/fields").iterdir()]
    assert all(len(n.removesuffix("__c")) <= 40 for n in names)
    assert len({n.lower() for n in names}) == len(names)


def test_repeated_stage_keys_do_not_collide(design_dict, write_design, tmp_path):
    second = {
        "object": "deal", "key": "renewals", "name": "Renewals",
        "stages": [
            {"key": "discovery", "label": "Discovery", "type": "open", "probability": 40,
             "exit_criteria": "Entered when a call has happened."},
            {"key": "won", "label": "Won", "type": "won", "probability": 100, "exit_criteria": "Entered when signed."},
            {"key": "lost", "label": "Lost", "type": "lost", "probability": 0,
             "exit_criteria": "Entered when refused.", "required_fields": ["lost_reason"]},
        ],
    }
    design_dict["pipelines"].append(second)
    sf.generate(load_design(write_design(design_dict)), tmp_path)
    v = stage_values(tmp_path)
    # Same label with a different probability: two values. Identical ones are shared.
    assert "Discovery (Sales)" in v and "Discovery (Renewals)" in v
    assert v["Discovery (Sales)"]["probability"] == "20" and v["Discovery (Renewals)"]["probability"] == "40"
    assert list(v).count("Won") == 1
    assert (tmp_path / BASE / "objects/Opportunity/validationRules/Lost_renewals_lost.validationRule-meta.xml").exists()
    assert_manifest_matches(tmp_path)


def test_pipeline_on_custom_object_uses_a_restricted_stage_picklist(design_dict, write_design, tmp_path):
    design_dict["add_fields"].append(_field("date") | {"key": "due", "label": "Due"})
    design_dict["add_fields"].append({"object": "project", "key": "close_reason", "label": "Close reason", "type": "select",
                                      "description": "Why.", "options": ["a", "b"]})
    design_dict["pipelines"].append({
        "object": "project", "key": "delivery", "name": "Delivery",
        "stages": [
            {"key": "live", "label": "Live", "type": "open", "probability": 50,
             "exit_criteria": "Entered when started.", "required_fields": ["due"]},
            {"key": "done", "label": "Done", "type": "won", "probability": 100, "exit_criteria": "Entered when finished."},
            {"key": "dropped", "label": "Dropped", "type": "lost", "probability": 0,
             "exit_criteria": "Entered when stopped.", "required_fields": ["close_reason"]},
        ],
    })
    sf.generate(load_design(write_design(design_dict)), tmp_path)
    stage = field_root(tmp_path, "Project__c", "Stage__c")
    assert child(stage, "type") == "Picklist" and child(stage.find(NS + "valueSet"), "restricted") == "true"
    gate = parse(tmp_path / BASE / "objects/Project__c/validationRules/Gate_delivery_live.validationRule-meta.xml")
    assert child(gate, "errorConditionFormula") == 'AND(CASE(Stage__c, "Live", 1, "Done", 2, 0) >= 1, ISBLANK(Due__c))'
    lost = parse(tmp_path / BASE / "objects/Project__c/validationRules/Lost_delivery_dropped.validationRule-meta.xml")
    assert child(lost, "errorConditionFormula") == 'AND(ISPICKVAL(Stage__c, "Dropped"), ISBLANK(TEXT(Close_reason__c)))'
    assert not (tmp_path / BASE / "pathAssistants" / "Delivery_path.pathAssistant-meta.xml").exists()
    assert "Finish the Delivery pipeline" in (tmp_path / "manual-steps.md").read_text()


def test_many_to_many_makes_a_junction_with_two_master_details(design_dict, write_design, tmp_path):
    design_dict["add_relationships"].append({
        "key": "project_person", "from": "project", "to": "person", "cardinality": "many_to_many",
        "from_label": "Team", "to_label": "Projects", "purpose": "Who is on a project."})
    sf.generate(load_design(write_design(design_dict)), tmp_path)
    obj = parse(tmp_path / BASE / "objects/Project_person__c/Project_person__c.object-meta.xml")
    assert child(obj, "sharingModel") == "ControlledByParent"
    a = field_root(tmp_path, "Project_person__c", "Project__c")
    b = field_root(tmp_path, "Project_person__c", "Person__c")
    assert (child(a, "type"), child(a, "relationshipOrder"), child(a, "referenceTo")) == ("MasterDetail", "0", "Project__c")
    assert (child(b, "type"), child(b, "relationshipOrder"), child(b, "referenceTo")) == ("MasterDetail", "1", "Contact")
    assert child(a, "relationshipName") == "Team"
    assert_manifest_matches(tmp_path)


def test_lookup_for_many_to_one(out):
    root = field_root(out, "Project__c", "Company__c")
    assert child(root, "type") == "Lookup"
    assert child(root, "referenceTo") == "Account"
    assert child(root, "relationshipLabel") == "Projects"
    assert child(root, "relationshipName") == "Projects"


def test_views_with_expressible_filters_become_list_views(design_dict, write_design, tmp_path):
    design_dict["views"] = [
        {"key": "mine", "name": "Mine", "object": "deal", "filter": "Owner is me and stage is open.", "sort": "Name."},
        {"key": "odd", "name": "Odd", "object": "deal", "filter": "Weather is nice.", "sort": "Name."},
        {"key": "live", "name": "Live projects", "object": "project", "filter": "Status is live.", "sort": "Name."},
    ]
    sf.generate(load_design(write_design(design_dict)), tmp_path)
    mine = parse(tmp_path / BASE / "objects/Opportunity/listViews/Mine.listView-meta.xml")
    assert child(mine, "filterScope") == "Mine"
    f = mine.find(NS + "filters")
    assert child(f, "field") == "OPPORTUNITY.STAGE_NAME" and child(f, "value") == "Discovery"
    live = parse(tmp_path / BASE / "objects/Project__c/listViews/Live.listView-meta.xml")
    assert child(live.find(NS + "filters"), "value") == "Live"
    assert not (tmp_path / BASE / "objects/Opportunity/listViews/Odd.listView-meta.xml").exists()
    manual = (tmp_path / "manual-steps.md").read_text()
    assert "Build the view Odd" in manual and "Set the sort on Mine" in manual
    assert_manifest_matches(tmp_path)


def test_build_sheet_has_the_actual_formulas_and_manual_steps_the_edition(out):
    sheet = (out / "build-sheet.md").read_text()
    assert "Validation rule `Gate_sales_discovery`" in sheet
    assert 'CASE(StageName, "Discovery", 1, "Won", 2, 0) >= 1' in sheet
    assert "Setup, Object Manager" in sheet
    manual = (out / "manual-steps.md").read_text()
    for needle in ("Enterprise, Unlimited, Performance and Developer", "Professional", "Record-Triggered Flow",
                   "Sort:", "Map lead fields"):
        assert needle in manual


def snapshot(directory: Path) -> dict[str, bytes]:
    return {str(p.relative_to(directory)): p.read_bytes() for p in sorted(directory.rglob("*")) if p.is_file()}


def test_generation_is_deterministic(design, tmp_path):
    sf.generate(design, tmp_path / "a")
    sf.generate(design, tmp_path / "b")
    assert snapshot(tmp_path / "a") == snapshot(tmp_path / "b")


ALL_BLUEPRINTS = sorted(p.parent.name for p in (REPO / "blueprints").glob("*/design.yaml"))


@pytest.mark.parametrize("name", ALL_BLUEPRINTS)
def test_every_blueprint_generates_valid_xml_and_a_matching_manifest(name, tmp_path):
    out = tmp_path / "salesforce"
    sf.generate(load_design(REPO / "blueprints" / name), out)
    for p in out.rglob("*.xml"):
        parse(p)
    assert_manifest_matches(out)
    # public toolkit: nothing from this machine in generated files
    for p in out.rglob("*"):
        if p.is_file():
            assert "/Users/" not in p.read_text(encoding="utf-8")


def test_committed_files_are_current():
    ok_all = True
    for name in ALL_BLUEPRINTS:
        ok, msgs = generate.generate_blueprint(REPO / "blueprints" / name, ["salesforce"], check=True)
        assert ok, msgs
        ok_all = ok_all and ok
    assert ok_all


def test_check_detects_stale_salesforce_files(tmp_path):
    bp = tmp_path / "bp"
    shutil.copytree(REPO / "blueprints" / "b2b-saas-sales-led", bp, ignore=shutil.ignore_patterns("attio", "hubspot"))
    ok, _ = generate.generate_blueprint(bp, ["salesforce"], check=False)
    ok, msgs = generate.generate_blueprint(bp, ["salesforce"], check=True)
    assert ok, msgs
    victim = bp / "salesforce" / BASE / "standardValueSets/OpportunityStage.standardValueSet-meta.xml"
    victim.write_text(victim.read_text().replace("<probability>20</probability>", "<probability>21</probability>"))
    ok, msgs = generate.generate_blueprint(bp, ["salesforce"], check=True)
    assert not ok and any("changed" in m for m in msgs)
