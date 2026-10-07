"""An in-memory Salesforce org behind a stand-in for the `sf` CLI runner.

`FakeSf` is a `tools.crm.salesforce.Runner`: call it with `(argv, cwd, timeout)` and it answers the commands
the adapter uses, with JSON shaped like `tests/fixtures/salesforce/`. It holds mutable org state seeded from
those fixtures. A deploy reads the manifest and the files in the working folder, checks that they match each
other, applies them to a copy of the org (objects, fields, stage values, business processes, record types,
validation rules, paths) and checks cross references, so ordering mistakes fail here as they would in an org.
Every call is recorded in `calls`; every deploy in `deploys`. There is no network and no `sf` binary.
"""

from __future__ import annotations

import copy
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Sequence

from tools.crm.salesforce import RunOutput

FIXTURES = Path(__file__).parent / "fixtures" / "salesforce"
NS = "{http://soap.sforce.com/2006/04/metadata}"
BASE = "force-app/main/default"


def fixture(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def result_of(name: str) -> Any:
    return fixture(name)["result"]


def _text(node: ET.Element, tag: str, default: str = "") -> str:
    return node.findtext(NS + tag) or default


def _bool(text: str, default: bool = False) -> bool:
    return text.strip().lower() == "true" if text else default


FIELD_TYPES = {
    "Text": "string", "LongTextArea": "textarea", "Picklist": "picklist", "MultiselectPicklist": "multipicklist",
    "Number": "double", "Currency": "currency", "Percent": "percent", "Date": "date", "DateTime": "datetime",
    "Checkbox": "boolean", "Url": "url", "Email": "email", "Phone": "phone", "Lookup": "reference",
    "MasterDetail": "reference",
}

SUFFIXES = {
    ".object-meta.xml": "CustomObject",
    ".field-meta.xml": "CustomField",
    ".standardValueSet-meta.xml": "StandardValueSet",
    ".businessProcess-meta.xml": "BusinessProcess",
    ".recordType-meta.xml": "RecordType",
    ".validationRule-meta.xml": "ValidationRule",
    ".pathAssistant-meta.xml": "PathAssistant",
    ".settings-meta.xml": "Settings",
    ".permissionset-meta.xml": "PermissionSet",
    ".listView-meta.xml": "ListView",
}


def member_of(rel: str) -> tuple[str, str]:
    """(type, member) for a path under force-app/main/default."""
    parts = rel.split("/")
    name = parts[-1]
    suffix = next(s for s in SUFFIXES if name.endswith(s))
    stem = name[: -len(suffix)]
    ctype = SUFFIXES[suffix]
    if ctype in ("CustomField", "ValidationRule", "BusinessProcess", "RecordType", "ListView"):
        return ctype, f"{parts[1]}.{stem}"
    if ctype == "Settings":
        return ctype, stem
    return ctype, stem


class FakeSf:
    """The org and the runner. `edition` and `sandbox` set what the Organization query says."""

    def __init__(
        self,
        *,
        edition: str = "Enterprise Edition",
        sandbox: bool = True,
        scratch: bool = False,
        name: str = "Example Trading Ltd",
        standard: bool = True,
    ) -> None:
        self.edition = edition
        self.sandbox = sandbox
        self.scratch = scratch
        self.org_name = name
        self.calls: list[list[str]] = []
        self.deploys: list[dict[str, Any]] = []
        self.retrieve_fails = False
        self.script: list[dict[str, Any] | None] = []  # canned replies for real deploys, consumed in order
        self.objects: dict[str, dict[str, Any]] = {}
        self.stages: dict[str, dict[str, Any]] = {}
        self.processes: dict[str, list[str]] = {}
        self.rt_process: dict[str, str] = {}
        self.rules: dict[str, str] = {}
        if standard:
            for api, fx in (("Account", "describe_account.json"), ("Contact", "describe_contact.json"),
                            ("Opportunity", "describe_opportunity.json")):
                self.objects[api] = result_of(fx)
            for row in result_of("query_opportunity_stage.json")["records"]:
                self.stages[row["ApiName"]] = row

    # -- the runner ---------------------------------------------------------------------------

    def __call__(self, argv: Sequence[str], cwd: Path | None, timeout: int) -> RunOutput:
        args = list(argv)
        self.calls.append(args)
        head = args[1:3]
        if head == ["org", "display"]:
            key = "scratch" if self.scratch else "sandbox" if self.sandbox else "production"
            return self._ok(fixture(f"org_display_{key}.json"))
        if head == ["data", "query"]:
            query = args[args.index("--query") + 1]
            if "FROM Organization" in query:
                body = fixture("query_organization_enterprise_sandbox.json")
                rec = body["result"]["records"][0]
                rec.update(Name=self.org_name, OrganizationType=self.edition, IsSandbox=self.sandbox or self.scratch)
                return self._ok(body)
            if "FROM OpportunityStage" in query:
                rows = list(self.stages.values())
                return self._ok({"status": 0, "result": {"totalSize": len(rows), "done": True, "records": rows}, "warnings": []})
            raise AssertionError(f"unexpected query {query!r}")
        if head == ["sobject", "list"]:
            names = [a for a, o in self.objects.items() if o.get("custom")] + ["acme__Thing__c", "Reading__mdt"]
            return self._ok({"status": 0, "result": names, "warnings": []})
        if head == ["sobject", "describe"]:
            api = args[args.index("--sobject") + 1]
            if api not in self.objects:
                return self._err("NOT_FOUND", "The requested resource does not exist")
            return self._ok({"status": 0, "result": copy.deepcopy(self.objects[api]), "warnings": []})
        if head == ["project", "retrieve"]:
            return self._retrieve(cwd)
        if head == ["project", "deploy"]:
            return self._deploy(args, cwd)
        raise AssertionError(f"unexpected sf command {args}")

    @staticmethod
    def _ok(body: Any) -> RunOutput:
        return RunOutput(0, json.dumps(body), "")

    @staticmethod
    def _err(name: str, message: str) -> RunOutput:
        body = {"name": name, "message": message, "exitCode": 1, "status": 1, "warnings": [], "actions": []}
        return RunOutput(1, json.dumps(body), "")

    # -- retrieve -----------------------------------------------------------------------------

    def _retrieve(self, cwd: Path | None) -> RunOutput:
        assert cwd is not None and (cwd / "sfdx-project.json").exists(), "retrieve must run inside a project"
        if self.retrieve_fails:
            return self._err("InsufficientAccess", "You need Modify Metadata Through Metadata API Functions.")
        base = cwd / BASE / "objects" / "Opportunity"
        for name, values in self.processes.items():
            path = base / "businessProcesses" / f"{name}.businessProcess-meta.xml"
            path.parent.mkdir(parents=True, exist_ok=True)
            vals = "".join(f"<values><fullName>{v}</fullName><default>false</default></values>" for v in values)
            path.write_text(f'<BusinessProcess xmlns="{NS[1:-1]}"><fullName>{name}</fullName>{vals}</BusinessProcess>')
        for rt, process in self.rt_process.items():
            path = base / "recordTypes" / f"{rt}.recordType-meta.xml"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f'<RecordType xmlns="{NS[1:-1]}"><fullName>{rt}</fullName><businessProcess>{process}</businessProcess></RecordType>')
        return self._ok({"status": 0, "result": {"status": "Succeeded", "success": True, "files": []}, "warnings": []})

    # -- deploy -------------------------------------------------------------------------------

    def _deploy(self, args: list[str], cwd: Path | None) -> RunOutput:
        assert cwd is not None and (cwd / "sfdx-project.json").exists(), "deploy must run inside a project"
        dry = "--dry-run" in args
        files = sorted(p.relative_to(cwd / BASE).as_posix() for p in (cwd / BASE).rglob("*") if p.is_file())
        manifest = ET.parse(cwd / "package.xml").getroot()
        listed = {
            (t.findtext(NS + "name") or "", m.text or "")
            for t in manifest.findall(NS + "types") for m in t.findall(NS + "members")
        }
        record = {
            "argv": args, "dry_run": dry, "files": files, "listed": sorted(listed),
            "listing": sorted(p.relative_to(cwd).as_posix() for p in cwd.rglob("*") if p.is_file()),
            "version": manifest.findtext(NS + "version"),
        }
        self.deploys.append(record)
        assert {member_of(f) for f in files} == listed, "package.xml must list exactly the files written"
        if self.script and not dry:
            reply = self.script.pop(0)
            if reply is not None:  # None means: behave like a real org for this deploy
                return RunOutput(reply["status"], json.dumps(reply), "")
        work = copy.deepcopy((self.objects, self.stages, self.processes, self.rt_process, self.rules))
        failures, states = self._apply_files(cwd, files)
        if failures:
            self.objects, self.stages, self.processes, self.rt_process, self.rules = work
            return RunOutput(1, json.dumps(self._failure_body(failures, states)), "")
        if dry:
            self.objects, self.stages, self.processes, self.rt_process, self.rules = work
        body = self._success_body(states, dry)
        return RunOutput(0, json.dumps(body), "")

    def _success_body(self, states: list[dict[str, str]], dry: bool) -> dict[str, Any]:
        res = result_of("deploy_success.json")
        res.update(checkOnly=dry, files=states, numberComponentsTotal=len(states), numberComponentsDeployed=len(states))
        return {"status": 0, "result": res, "warnings": []}

    def _failure_body(self, failures: list[dict[str, Any]], states: list[dict[str, str]]) -> dict[str, Any]:
        res = result_of("deploy_success.json")
        rows = [
            {"fullName": f["fullName"], "type": f["type"], "state": "Failed", "filePath": f["path"],
             "error": f["problem"] + " (Line: 1, Col: 1)", "problemType": "Error", "lineNumber": 1, "columnNumber": 1}
            for f in failures
        ]
        msgs = [
            {"componentType": f["type"], "fileName": f["path"], "fullName": f["fullName"], "problem": f["problem"],
             "problemType": "Error", "lineNumber": "1", "columnNumber": "1", "success": "false", "created": "false",
             "changed": "false", "deleted": "false"}
            for f in failures
        ]
        res.update(
            status="Failed", success=False, numberComponentErrors=len(rows), numberComponentsDeployed=0,
            details={"componentFailures": msgs[0] if len(msgs) == 1 else msgs, "componentSuccesses": []}, files=rows,
        )
        return {"status": 1, "result": res, "warnings": []}

    def _apply_files(self, cwd: Path, files: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
        roots = {f: ET.parse(cwd / BASE / f).getroot() for f in files}
        order = ["CustomObject", "CustomField", "StandardValueSet", "BusinessProcess", "RecordType", "ValidationRule", "PathAssistant", "Settings"]
        failures: list[dict[str, Any]] = []
        states: list[dict[str, str]] = []

        def fail(rel: str, problem: str) -> None:
            ctype, member = member_of(rel)
            failures.append({"type": ctype, "fullName": member, "problem": problem, "path": f"{BASE}/{rel}"})

        for ctype in order:
            for rel in files:
                t, member = member_of(rel)
                if t != ctype:
                    continue
                root = roots[rel]
                before = len(failures)
                state = getattr(self, f"_apply_{ctype}", lambda *a: "Created")(rel, member, root, fail)
                if len(failures) == before:
                    states.append({"fullName": member, "type": ctype, "state": state, "filePath": f"{BASE}/{rel}"})
        return failures, states

    def _apply_CustomObject(self, rel: str, member: str, root: ET.Element, fail: Any) -> str:
        label = _text(root, "label", member)
        name_field = root.find(NS + "nameField")
        existing = member in self.objects
        self.objects[member] = self.objects.get(member) or {
            "name": member, "label": label, "labelPlural": _text(root, "pluralLabel", label), "custom": True,
            "queryable": True, "createable": True, "recordTypeInfos": [],
            "fields": [
                {"name": "Id", "label": "Record ID", "type": "id", "custom": False, "picklistValues": [], "referenceTo": []},
                {"name": "Name", "label": _text(name_field, "label", "Name") if name_field is not None else "Name",
                 "type": "string", "custom": False, "picklistValues": [], "referenceTo": []},
                {"name": "OwnerId", "label": "Owner ID", "type": "reference", "custom": False, "picklistValues": [],
                 "referenceTo": ["User"]},
            ],
        }
        self.objects[member]["label"] = label
        return "Unchanged" if existing else "Created"

    def _apply_CustomField(self, rel: str, member: str, root: ET.Element, fail: Any) -> str:
        obj, _, api = member.partition(".")
        if obj not in self.objects:
            fail(rel, f"In field: object {obj} does not exist (INVALID_CROSS_REFERENCE_KEY)")
            return ""
        ftype = _text(root, "type")
        target = _text(root, "referenceTo")
        if target and target not in self.objects and target != "User":
            fail(rel, f"Field {api}: referenceTo object {target} does not exist")
            return ""
        values: list[dict[str, Any]] = []
        for v in root.findall(f".//{NS}valueSetDefinition/{NS}value"):
            values.append({"value": _text(v, "fullName"), "label": _text(v, "label"),
                           "active": _bool(_text(v, "isActive"), True), "defaultValue": False})
        new = {
            "name": api, "label": _text(root, "label"), "type": FIELD_TYPES.get(ftype, ftype), "custom": True,
            "length": int(_text(root, "length", "0") or 0), "picklistValues": values,
            "referenceTo": [target] if target else [], "nillable": True,
        }
        fields: list[dict[str, Any]] = self.objects[obj]["fields"]
        old = next((f for f in fields if f["name"] == api), None)
        if old is None:
            fields.append(new)
            return "Created"
        merged = {v["value"]: v for v in old.get("picklistValues", [])}
        for v in values:  # a deploy adds values and can switch isActive; it removes none
            merged[v["value"]] = v
        new["picklistValues"] = list(merged.values())
        same = new == old
        old.clear()
        old.update(new)
        return "Unchanged" if same else "Changed"

    def _apply_StandardValueSet(self, rel: str, member: str, root: ET.Element, fail: Any) -> str:
        changed = "Unchanged"
        for sv in root.findall(NS + "standardValue"):
            value = _text(sv, "fullName")
            row = {
                "ApiName": value, "MasterLabel": _text(sv, "label", value), "IsActive": _bool(_text(sv, "isActive"), True),
                "IsClosed": _bool(_text(sv, "closed")), "IsWon": _bool(_text(sv, "won")),
                "DefaultProbability": int(_text(sv, "probability", "0") or 0),
                "SortOrder": self.stages.get(value, {}).get("SortOrder", len(self.stages) + 1),
            }
            if self.stages.get(value) != row:
                changed = "Changed"
            self.stages[value] = row
        return changed

    def _apply_BusinessProcess(self, rel: str, member: str, root: ET.Element, fail: Any) -> str:
        name = member.partition(".")[2]
        values = [_text(v, "fullName") for v in root.findall(NS + "values")]
        missing = [v for v in values if v not in self.stages]
        if missing:
            fail(rel, f"Stage value {missing[0]} does not exist")
            return ""
        had = name in self.processes
        merged = list(self.processes.get(name, []))
        merged += [v for v in values if v not in merged]
        self.processes[name] = merged
        return "Changed" if had else "Created"

    def _apply_RecordType(self, rel: str, member: str, root: ET.Element, fail: Any) -> str:
        obj, _, name = member.partition(".")
        if obj not in self.objects:
            fail(rel, f"Object {obj} does not exist")
            return ""
        process = _text(root, "businessProcess")
        if process and process not in self.processes:
            fail(rel, f"Business process {process} does not exist")
            return ""
        fields = {f["name"] for f in self.objects[obj]["fields"]}
        for pl in root.findall(NS + "picklistValues"):
            if _text(pl, "picklist") not in fields:
                fail(rel, f"Picklist {_text(pl, 'picklist')} does not exist on {obj}")
                return ""
        infos: list[dict[str, Any]] = self.objects[obj].setdefault("recordTypeInfos", [])
        if not any(i.get("master") for i in infos):
            infos.append({"active": True, "available": True, "developerName": "Master", "master": True, "name": "Master"})
        existing = next((i for i in infos if i["developerName"] == name), None)
        row = {"active": _bool(_text(root, "active"), True), "available": True, "developerName": name,
               "master": False, "name": _text(root, "label", name)}
        if existing is None:
            infos.append(row)
        else:
            existing.update(row)
        if process:
            self.rt_process[name] = process
        return "Changed" if existing else "Created"

    def _apply_ValidationRule(self, rel: str, member: str, root: ET.Element, fail: Any) -> str:
        obj, _, name = member.partition(".")
        if obj not in self.objects:
            fail(rel, f"Object {obj} does not exist")
            return ""
        fields = {f["name"] for f in self.objects[obj]["fields"]}
        formula = _text(root, "errorConditionFormula")
        for token in set(re.findall(r"\b[A-Za-z][A-Za-z0-9_]*__c\b", formula)):
            if token not in fields:
                fail(rel, f"Field {token} does not exist. Check spelling.")
                return ""
        had = member in self.rules
        self.rules[member] = formula
        return "Changed" if had else "Created"

    def _apply_PathAssistant(self, rel: str, member: str, root: ET.Element, fail: Any) -> str:
        for step in root.findall(NS + "pathAssistantSteps"):
            if _text(step, "picklistValueName") not in self.stages:
                fail(rel, f"Stage value {_text(step, 'picklistValueName')} does not exist")
                return ""
        return "Created"
