"""Salesforce adapter: read live structure with the `sf` CLI, plan against a design, deploy additive changes.

Metadata comes from `tools.generators.salesforce` (one naming scheme, one API version, one set of
file shapes), so a build made from the generator's folder and a build made by this adapter are the
same build. Diffing and the safety rules live in `tools.crm.planner` and `tools.crm.safety`. This
module reads, maps, writes the files for exactly the components a change needs, and deploys them.
Research for every call is in `platforms/salesforce/reference/` (auth-and-setup.md,
limits-and-errors.md, open-questions.md).

Rules this adapter keeps:

- Every `sf` call goes through one runner (`Runner`), so tests stub it. Nothing else starts a process.
- Credentials are an `sf` org alias or username already authorised with `sf org login web`. Nothing
  secret is in the environment. `sf org display` prints an access token; only a few named keys of its
  output are ever kept, and the raw output is never logged.
- A deploy is `sf project deploy start --manifest ... --target-org ... --api-version ... --wait 30
  --json`, with `--dry-run` for a check-only run. These are never passed: `--ignore-errors`,
  `--ignore-conflicts`, `--ignore-warnings`, `--purge-on-delete`, the destructive-changes flags and
  `--test-level`. No destructive-changes file is ever written.
- Edition gate: Professional, Essentials and anything else that is not Enterprise, Unlimited,
  Performance or Developer cannot use the Metadata API, so `plan` turns every change into a manual
  step that points at the build sheet. `apply` on such an org changes nothing and does not fail.
- Removing a picklist value is done by deploying it with `isActive` false. Removing an Opportunity
  stage is a manual step, because the research does not show that a source deploy can deactivate one
  (open-questions.md E10). Renames, stage reorders and probability changes are manual steps because
  `fullName` is the identity of a component (gotcha 2).
- Real deploys run in phases (objects, relationships, fields, pipelines) and re-read the org before
  each phase, skipping what is already there. A dry run is one check-only deploy of everything, so
  cross references resolve. The first failure stops the run; the report has applied, failed and
  remaining.
- The permission set and the list views are not deployed by a change (a permission set is
  overwritten whole). A manual step names the generated files for them.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Callable, Mapping, NamedTuple, Sequence

from tools.crm.base import (
    Adapter,
    Change,
    Failure,
    ManualStep,
    Plan,
    Result,
    State,
    StateField,
    StateObject,
    StatePipeline,
    StateRelationship,
    StateStage,
)
from tools.crm.planner import plan_changes
from tools.crm.safety import Mode, SafetyError, check_gates, get_credential, redact
from tools.design import REPO_ROOT, Design
from tools.generators import salesforce as gen
from tools.generators.salesforce import API_VERSION as DEFAULT_API_VERSION
from tools.generators.salesforce import BASE, PLATFORM

TARGET_VAR = "SF_TARGET_ORG"
VERSION_VAR = "SF_API_VERSION"
CLI_VAR = "SF_CLI"
DEFAULT_CLI = "sf"

WAIT_MINUTES = "30"
READ_TIMEOUT = 300
DEPLOY_TIMEOUT = 60 * 45  # the CLI waits 30 minutes; this only stops a hung process

# Source pages per area. The first three are the CLI's own source files; the rest are the guides.
SRC_DEPLOY = "https://raw.githubusercontent.com/salesforcecli/plugin-deploy-retrieve/main/src/commands/project/deploy/start.ts"
SRC_RETRIEVE = "https://raw.githubusercontent.com/salesforcecli/plugin-deploy-retrieve/main/src/commands/project/retrieve/start.ts"
SRC_EXIT_CODES = "https://raw.githubusercontent.com/salesforcecli/plugin-deploy-retrieve/main/src/utils/errorCodes.ts"
SRC_DESCRIBE = "https://raw.githubusercontent.com/salesforcecli/plugin-schema/main/src/commands/sobject/describe.ts"
SRC_SOBJECT_LIST = "https://github.com/salesforcecli/plugin-schema"
SRC_ORG_DISPLAY = "https://github.com/salesforcecli/plugin-org"
SRC_METADATA_GUIDE = "https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/api_meta.pdf"
SRC_OBJECT_REFERENCE = "https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/object_reference.pdf"

SOURCE_URLS: dict[str, str] = {
    "add_object": SRC_METADATA_GUIDE,
    "add_relationship": SRC_METADATA_GUIDE,
    "add_pipeline": SRC_METADATA_GUIDE,
    "add_stage": SRC_METADATA_GUIDE,
    "remove_stage": SRC_METADATA_GUIDE,
    "add_field": SRC_METADATA_GUIDE,
    "add_option": SRC_METADATA_GUIDE,
    "remove_option": SRC_METADATA_GUIDE,
    "rename_object": SRC_METADATA_GUIDE,
    "rename_field": SRC_METADATA_GUIDE,
    "rename_option": SRC_METADATA_GUIDE,
    "rename_stage": SRC_METADATA_GUIDE,
    "update_stage": SRC_METADATA_GUIDE,
    "reorder_stages": SRC_METADATA_GUIDE,
}

_SETUP = "Setup, Object Manager"
UI_PATHS: dict[str, str] = {
    "remove_object": f"{_SETUP}, pick the object, Delete (after the data is exported)",
    "remove_relationship": f"{_SETUP}, pick the child object, Fields & Relationships, the lookup field, Delete",
    "change_relationship": f"{_SETUP}, pick the child object, Fields & Relationships, the lookup field",
    "remove_pipeline": f"{_SETUP}, Opportunity, Record Types and Business Processes (or the object's Record Types)",
    "remove_field": f"{_SETUP}, pick the object, Fields & Relationships, the field, Delete",
    "change_field_type": f"{_SETUP}, pick the object, Fields & Relationships, the field, Change Field Type",
}

# Editions that can use the Metadata API (auth-and-setup.md, "Editions and environments").
METADATA_EDITIONS = ("enterprise", "unlimited", "performance", "developer")
# Secondary-source allowances: (custom objects, custom fields per object). objects.md.
EDITION_LIMITS: dict[str, tuple[int, int]] = {
    "essentials": (0, 100),
    "professional": (50, 100),
    "enterprise": (200, 500),
    "unlimited": (2000, 800),
    "performance": (2000, 800),
}
LIMIT_WARN = 0.75

STANDARD_KEYS: dict[str, str] = {"Account": "company", "Contact": "person", "Opportunity": "deal"}
STANDARD_APIS = tuple(STANDARD_KEYS)

# Build phases for a real run. Rules and record types reference fields, so pipelines come last.
PHASE: dict[str, int] = {
    "add_object": 0,
    "add_relationship": 1,
    "add_field": 2,
    "add_option": 2,
    "remove_option": 2,
    "add_pipeline": 3,
    "add_stage": 3,
    "remove_stage": 3,
}
PHASE_NAMES = ("objects", "relationships", "fields", "pipelines")

_NAMESPACED = re.compile(r"^[A-Za-z][A-Za-z0-9]*__[A-Za-z0-9_]+__c$")
_VERSION = re.compile(r"^\d{2,3}\.0$")
_NS = "http://soap.sforce.com/2006/04/metadata"

FORBIDDEN_FLAGS = (
    "--ignore-errors",
    "--ignore-conflicts",
    "--ignore-warnings",
    "--purge-on-delete",
    "--pre-destructive-changes",
    "--post-destructive-changes",
    "--test-level",
)

_MIGRATION = "Export the data first. Never delete before the data is safe elsewhere."


class SalesforceError(RuntimeError):
    """An `sf` call failed. The message holds the redacted error, never an access token."""


# --- the one runner ---------------------------------------------------------------------------


class RunOutput(NamedTuple):
    """What a finished process gave back."""

    returncode: int
    stdout: str
    stderr: str


# runner(argv, cwd, timeout_seconds) -> RunOutput. `argv[0]` is the CLI name.
Runner = Callable[[Sequence[str], "Path | None", int], RunOutput]


def subprocess_runner(argv: Sequence[str], cwd: Path | None, timeout: int) -> RunOutput:
    """Run one command and capture its output. The only place this module starts a process.

    Source: https://github.com/salesforcecli/cli (the `sf` command line; every argument list is built by the caller).
    """
    try:
        proc = subprocess.run(  # noqa: S603 - argv is a list, never a shell string
            list(argv), cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False
        )
    except FileNotFoundError as exc:
        raise SalesforceError(
            f"The Salesforce CLI {argv[0]!r} was not found. Install @salesforce/cli, or set {CLI_VAR}."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise SalesforceError(f"`{argv[0]} {' '.join(argv[1:3])}` did not finish in {timeout} seconds.") from exc
    return RunOutput(proc.returncode, proc.stdout, proc.stderr)


# --- reading sf output ------------------------------------------------------------------------


@dataclass(frozen=True)
class Reply:
    """An `sf --json` reply: the process exit code and the parsed body."""

    code: int
    body: dict[str, Any]

    @property
    def ok(self) -> bool:
        """True when the process and the envelope both say success."""
        return self.code == 0 and self.body.get("status", 0) == 0

    @property
    def result(self) -> Any:
        """The command's `result` value."""
        return self.body.get("result")


def error_text(body: Mapping[str, Any]) -> str:
    """One line from an `sf` error envelope: name, message and the first suggested action.

    Source: https://raw.githubusercontent.com/salesforcecli/sf-plugins-core/main/src/SfCommandError.ts
    (field names `name`, `message`, `exitCode`, `actions`; key off these, not the message text).
    """
    parts = [str(body.get("name") or "").strip(), str(body.get("message") or "").strip()]
    text = ": ".join(p for p in parts if p) or "no error text"
    actions = body.get("actions")
    if isinstance(actions, list) and actions:
        text += f" (suggested: {actions[0]})"
    return redact(text)[:1000]


def _truthy(value: Any) -> bool:
    """`DeployMessage` booleans arrive as `true`, `false`, `"true"` or `"false"`."""
    return value is True or (isinstance(value, str) and value.strip().lower() == "true")


def _as_list(value: Any) -> list[Any]:
    """`componentFailures` is one object for one failure and a list for many."""
    if value is None or value == "":
        return []
    return list(value) if isinstance(value, list) else [value]


@dataclass(frozen=True)
class ComponentFailure:
    """One component the deploy refused."""

    component_type: str
    full_name: str
    problem: str
    problem_type: str = "Error"
    file_path: str = ""
    line: str = ""


@dataclass(frozen=True)
class DeployOutcome:
    """A parsed deploy reply. `states` maps a component's full name to Created, Changed, Unchanged, ..."""

    ok: bool
    exit_code: int
    status: str
    message: str = ""
    failures: tuple[ComponentFailure, ...] = ()
    states: Mapping[str, str] = field(default_factory=dict)
    job_id: str = ""


def parse_deploy(body: Mapping[str, Any], exit_code: int) -> DeployOutcome:
    """Turn the JSON of `sf project deploy start` into a `DeployOutcome`.

    Source: https://raw.githubusercontent.com/salesforcecli/plugin-deploy-retrieve/main/src/utils/errorCodes.ts
    (exit codes: 0 succeeded, 1 failed or cancelled, 68 partial, 69 still running) and
    limits-and-errors.md in the research (shape of `result`). A failed deploy still prints a normal
    `result`, with `status` set to the exit code. `details.componentFailures` is an object or a list,
    its booleans are strings or booleans, and `files[].state` is Created, Changed, Unchanged,
    Deleted or Failed. Only exit code 0 with no failure is ok; 68 and 69 are never ok.
    """
    raw_status = body.get("status")
    code = raw_status if isinstance(raw_status, int) and not isinstance(raw_status, bool) else exit_code
    code = code or exit_code
    result = body.get("result")
    if not isinstance(result, dict) or "status" not in result and "details" not in result and "files" not in result:
        # An error envelope: the deploy never started (no org, bad flag, expired login).
        return DeployOutcome(False, code or 1, "Error", error_text(body))
    status = str(result.get("status") or "")
    details = result.get("details") if isinstance(result.get("details"), dict) else {}
    failures: dict[str, ComponentFailure] = {}
    for item in _as_list(details.get("componentFailures")):
        if not isinstance(item, dict) or "success" in item and _truthy(item.get("success")):
            continue
        full = str(item.get("fullName") or "")
        failures[full] = ComponentFailure(
            str(item.get("componentType") or ""), full, redact(str(item.get("problem") or "")),
            str(item.get("problemType") or "Error"), "", str(item.get("lineNumber") or ""),
        )
    states: dict[str, str] = {}
    for item in _as_list(result.get("files")):
        if not isinstance(item, dict):
            continue
        full, state = str(item.get("fullName") or ""), str(item.get("state") or "")
        states[full] = state
        if state == "Failed":
            earlier = failures.get(full)
            failures[full] = ComponentFailure(
                str(item.get("type") or (earlier.component_type if earlier else "")), full,
                redact(str(item.get("error") or (earlier.problem if earlier else ""))),
                str(item.get("problemType") or (earlier.problem_type if earlier else "Error")),
                str(item.get("filePath") or ""), str(item.get("lineNumber") or ""),
            )
        elif earlier := failures.get(full):
            failures[full] = replace(earlier, file_path=str(item.get("filePath") or ""))
    if "success" in result:
        success = _truthy(result.get("success"))
    else:
        success = status == "Succeeded"
    job = str(result.get("id") or "")
    ok = code == 0 and success and not failures and status in ("Succeeded", "")
    message = redact(str(result.get("errorMessage") or ""))
    if not ok:
        if code == 69 or status in ("InProgress", "Pending", "Canceling", "Queued"):
            message = (
                f"The deploy is still running (job {job or 'unknown'}). Nothing was retried. Check it with "
                f"`sf project deploy report --job-id {job or '<id>'}` before running again."
            )
        elif code == 68 or status == "SucceededPartial":
            message = "Only some components were saved (partial success). This tool never allows that."
        elif failures and not message:
            first = next(iter(failures.values()))
            message = f"{first.component_type} {first.full_name}: {first.problem}"
    return DeployOutcome(ok, code, status, message[:2000], tuple(failures.values()), states, job)


# --- what the org is --------------------------------------------------------------------------


@dataclass(frozen=True)
class OrgInfo:
    """The org this run talks to. Built from `sf org display` and the Organization query."""

    name: str
    edition: str
    is_sandbox: bool
    is_scratch: bool
    username: str = ""
    instance_url: str = ""

    @property
    def production(self) -> bool:
        """True unless the org is a sandbox or a scratch org. A Developer Edition org counts as production."""
        return not (self.is_sandbox or self.is_scratch)

    @property
    def metadata_api(self) -> bool:
        """True when the edition can use the Metadata API."""
        text = self.edition.lower()
        return any(word in text for word in METADATA_EDITIONS)

    @property
    def edition_key(self) -> str:
        """Lower-case edition word used by the limits table, or empty."""
        text = self.edition.lower()
        return next((k for k in (*EDITION_LIMITS, "developer") if k in text), "")


@dataclass
class Snapshot:
    """Raw reads from one org, before they are mapped to design keys."""

    org: OrgInfo
    describes: dict[str, dict[str, Any]] = field(default_factory=dict)  # API name -> describe result
    custom_objects: tuple[str, ...] = ()
    stages: dict[str, dict[str, Any]] = field(default_factory=dict)  # ApiName -> OpportunityStage row
    processes: dict[str, tuple[str, ...]] | None = None  # business process -> values; None = not read
    record_type_process: dict[str, str] = field(default_factory=dict)  # Opportunity record type -> process


# --- mapping live shapes to canonical terms ---------------------------------------------------

_TYPE_BY_DESCRIBE: dict[str, str] = {
    "string": "text",
    "textarea": "long_text",
    "picklist": "select",
    "multipicklist": "multi_select",
    "double": "number",
    "int": "number",
    "long": "number",
    "currency": "currency",
    "percent": "percent",
    "date": "date",
    "datetime": "datetime",
    "boolean": "checkbox",
    "url": "url",
    "email": "email",
    "phone": "phone",
}


def canonical_type(fld: Mapping[str, Any]) -> str:
    """Map a describe field back to a canonical type, the inverse of the generator's type map.

    Source: https://raw.githubusercontent.com/salesforcecli/plugin-schema/main/src/commands/sobject/describe.ts
    (describe gives the REST type: `string`, `textarea`, `picklist`, `double`, `boolean`, `reference`).
    Describe cannot tell Text from TextArea or Lookup from MasterDetail with certainty
    (limits-and-errors.md); unmapped shapes come back as `unknown:<type>` so they show as a difference.
    A reference to User is `user`; any other reference is `lookup`.
    """
    kind = str(fld.get("type") or "")
    if kind == "reference":
        return "user" if list(fld.get("referenceTo") or []) == ["User"] else "lookup"
    return _TYPE_BY_DESCRIBE.get(kind, f"unknown:{kind}")


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_") or "value"


def _active_values(fld: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [pv for pv in fld.get("picklistValues") or [] if pv.get("active", True)]


class _Names:
    """API names to design keys. With a design it uses the generator's own naming (`build_model`)."""

    def __init__(self, design: Design | None) -> None:
        self.design = design
        self.build = gen.build_model(design) if design is not None else None
        self.obj_keys: dict[str, str] = {}
        self.junctions: set[str] = set()
        self.fields: dict[tuple[str, str], tuple[str, str, str]] = {}  # (obj api, field api) -> key info
        if self.build is not None:
            for key, api in self.build.obj_api.items():
                if key.startswith("__junction_"):
                    self.junctions.add(api)
                else:
                    self.obj_keys[api] = key
            for (okey, fkey), api in self.build.field_api.items():
                if fkey != "__stage":
                    kind = self.build.field_kind.get((okey, fkey), "custom")
                    self.fields[(self.build.obj_api[okey], api)] = (okey, fkey, kind)

    def object_apis(self) -> list[str]:
        """Every object a design touches, junctions included."""
        if self.build is None:
            return list(STANDARD_APIS)
        return sorted(set(self.build.obj_api.values()))

    def obj_key(self, api: str) -> str:
        return self.obj_keys.get(api) or STANDARD_KEYS.get(api) or api.removesuffix("__c").lower()

    def field_key(self, obj_api: str, api: str) -> str:
        known = self.fields.get((obj_api, api))
        return known[1] if known else api.removesuffix("__c").lower()


def _expected_values(f: Any) -> dict[str, tuple[str, str, str]]:
    """The generator's stored value -> (option key, label it writes, design label)."""
    pairs = gen._values([(o.key, o.label) for o in f.options])
    return {value: (o.key, label, o.label) for (value, label), o in zip(pairs, f.options)}


def _options_for(live: Mapping[str, Any], design_field: Any | None) -> tuple[tuple[str, str], ...]:
    """Live active picklist values as (key, label). Values the generator wrote keep the design label."""
    expected = _expected_values(design_field) if design_field is not None else {}
    out: list[tuple[str, str]] = []
    for pv in _active_values(live):
        value, label = str(pv.get("value") or ""), str(pv.get("label") or "")
        hit = expected.get(value)
        if hit is not None:
            out.append((hit[0], hit[2] if label == hit[1] else label))
        else:
            out.append((_slug(value), value))
    return tuple(out)


def _stage_type(row: Mapping[str, Any]) -> str:
    if not _truthy(row.get("IsClosed")):
        return "open"
    return "won" if _truthy(row.get("IsWon")) else "lost"


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_state(snap: Snapshot, design: Design | None) -> State:
    """Map a snapshot to a `State`. Needs the design to find generated names; without one it guesses from the API names."""
    names = _Names(design)
    build = names.build
    objects: list[StateObject] = []
    fields: list[StateField] = []
    rels: list[StateRelationship] = []
    rel_fields: set[tuple[str, str]] = set()
    if build is not None:
        for comps in build.rel_components.values():
            for ctype, member in comps:
                if ctype == "CustomField":
                    obj_api, _, f_api = member.partition(".")
                    rel_fields.add((obj_api, f_api))
    stage_fields = {(build.obj_api[k], v) for k, v in build.stage_field.items()} if build is not None else set()

    for api, desc in sorted(snap.describes.items()):
        if api in names.junctions:
            continue
        okey = names.obj_key(api)
        d_obj = design.get_object(okey) if design is not None else None
        label = str(desc.get("label") or "")
        if d_obj is not None and label == gen._fit_label(d_obj.label):
            label = d_obj.label
        objects.append(StateObject(okey, label, native=api in STANDARD_KEYS))
        live_by_name = {str(f.get("name")): f for f in desc.get("fields") or []}
        handled: set[str] = set()
        if design is not None:
            for df in design.fields_of(okey):
                info = names.fields.get((api, build.field_api[(okey, df.key)])) if build else None
                kind = info[2] if info else "custom"
                if kind == "custom":
                    continue
                fapi = build.field_api[(okey, df.key)]
                handled.add(fapi)
                if kind == "native" and fapi not in live_by_name:
                    continue  # the planner skips a native field it cannot see
                opts: tuple[tuple[str, str], ...] = ()
                if df.type in ("select", "multi_select") and fapi in live_by_name:
                    opts = _options_for(live_by_name[fapi], df)
                fields.append(StateField(okey, df.key, df.type, df.label, opts, native=True))
        for name, fld in live_by_name.items():
            if name in handled or not fld.get("custom"):
                continue
            if (api, name) in rel_fields or (api, name) in stage_fields:
                continue
            ctype = canonical_type(fld)
            native = bool(_NAMESPACED.match(name))
            if ctype == "lookup":
                target_api = (list(fld.get("referenceTo") or []) or [""])[0]
                rels.append(StateRelationship(
                    f"{okey}_{names.field_key(api, name)}", okey, names.obj_key(target_api), "many_to_one", native=native,
                ))
                continue
            info = names.fields.get((api, name))
            df = design.get_field(info[0], info[1]) if design is not None and info else None
            fkey = names.field_key(api, name)
            flabel = str(fld.get("label") or "")
            if df is not None and flabel == gen._fit_label(df.label):
                flabel = df.label
            opts = _options_for(fld, df) if ctype in ("select", "multi_select") else ()
            fields.append(StateField(okey, fkey, ctype, flabel, opts, native=native))

    if design is not None and build is not None:
        for rel in design.relationships:
            if PLATFORM in rel.native:
                continue
            if _components_live(snap, build.rel_components.get(rel.key, [])):
                rels.append(StateRelationship(rel.key, rel.from_object, rel.to_object, rel.cardinality))

    pipelines = _build_pipelines(snap, names, design)
    return State(PLATFORM, tuple(objects), tuple(fields), tuple(rels), tuple(pipelines))


def _components_live(snap: Snapshot, comps: Sequence[tuple[str, str]]) -> bool:
    """True when every custom object and custom field in `comps` exists in the snapshot."""
    if not comps:
        return False
    for ctype, member in comps:
        if ctype == "CustomObject" and member not in snap.describes:
            return False
        if ctype == "CustomField":
            obj_api, _, f_api = member.partition(".")
            fields = snap.describes.get(obj_api, {}).get("fields") or []
            if not any(f.get("name") == f_api for f in fields):
                return False
    return True


def _stage_from_row(row: Mapping[str, Any], value: str, info: Any | None) -> StateStage:
    """A live Opportunity stage. If it is what the generator would write, report the design's wording."""
    live_label = str(row.get("MasterLabel") or value)
    live_type = _stage_type(row)
    prob = _number(row.get("DefaultProbability"))
    if info is None:
        return StateStage(_slug(value), live_label, live_type, prob)
    st = info.stage
    label = st.label if live_label == info.value else live_label
    expected = 100 if st.type == "won" else 0 if st.type == "lost" else gen._prob(st.probability)
    if prob is not None and int(round(prob)) == expected:
        prob = st.probability
    return StateStage(st.key, label, live_type, prob)


def _build_pipelines(snap: Snapshot, names: _Names, design: Design | None) -> list[StatePipeline]:
    out: list[StatePipeline] = []
    build = names.build
    rows = {k: r for k, r in snap.stages.items() if _truthy(r.get("IsActive", True))}
    opp = snap.describes.get("Opportunity", {})
    rts = {
        str(rt.get("developerName")): rt
        for rt in opp.get("recordTypeInfos") or []
        if not rt.get("master") and rt.get("active", True)
    }
    if build is None:
        for rt_name, process in sorted(snap.record_type_process.items()):
            if rt_name not in rts or snap.processes is None or process not in snap.processes:
                continue
            stages = tuple(
                _stage_from_row(rows[v], v, None) for v in snap.processes[process] if v in rows
            )
            out.append(StatePipeline("deal", rt_name.lower(), rt_name, stages))
        return out
    for p in build.pipes:
        pl = p.pipeline
        if p.is_opp:
            if p.rt not in rts:
                continue
            by_value = {si.value: si for si in p.stages}
            if snap.processes is not None and p.bp in snap.processes:
                values = [v for v in snap.processes[p.bp] if v in rows]
            else:  # the retrieve was not possible: assume the design's stages that exist
                values = [si.value for si in p.stages if si.value in rows]
            stages = tuple(_stage_from_row(rows[v], v, by_value.get(v)) for v in values)
            out.append(StatePipeline(pl.object, pl.key, pl.name, stages))
            continue
        obj_api, f_api = p.obj_api, build.stage_field.get(pl.object, "")
        desc = snap.describes.get(obj_api)
        if desc is None or p.rt and p.rt not in {str(r.get("developerName")) for r in desc.get("recordTypeInfos") or []}:
            continue
        fld = next((f for f in desc.get("fields") or [] if f.get("name") == f_api), None)
        if fld is None:
            continue
        live = {str(pv.get("value")): pv for pv in _active_values(fld)}
        single = sum(1 for q in build.pipes if q.pipeline.object == pl.object) == 1
        design_values = {si.value for si in p.stages}
        stages_list: list[StateStage] = []
        for si in p.stages:
            if si.value in live:
                pv_label = str(live[si.value].get("label") or si.value)
                stages_list.append(StateStage(
                    si.stage.key, si.stage.label if pv_label == si.value else pv_label, si.stage.type, None,
                ))
        if single:
            for value in live:
                if value not in design_values:
                    stages_list.append(StateStage(_slug(value), value, "open", None))
        out.append(StatePipeline(pl.object, pl.key, pl.name, tuple(stages_list)))
    return out


# --- XML helpers ------------------------------------------------------------------------------


def add_inactive_value(xml_text: str, value: str) -> str:
    """Return a picklist field file with `value` added as an inactive value.

    Source: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/api_meta.pdf (Metadata API
    Developer Guide, `CustomValue`: a value may carry `isActive`; the research fields.md lists it).
    Adding the value with `isActive` false deactivates it and removes nothing. Any existing value of
    the same name is left alone.
    """
    ET.register_namespace("", _NS)
    root = ET.fromstring(xml_text)

    def q(tag: str) -> str:
        return f"{{{_NS}}}{tag}"

    definition = root.find(f".//{q('valueSetDefinition')}")
    if definition is None:
        raise SalesforceError("The field file has no value set, so a value cannot be deactivated.")
    for existing in definition.findall(q("value")):
        if (existing.findtext(q("fullName")) or "") == value:
            definition.remove(existing)
    node = ET.SubElement(definition, q("value"))
    for tag, text in (("fullName", value), ("default", "false"), ("isActive", "false"), ("label", value)):
        ET.SubElement(node, q(tag)).text = text
    ET.indent(root, space="    ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"


def parse_process_file(text: str) -> tuple[str, ...]:
    """The `values` full names of a business process file, in order."""
    root = ET.fromstring(text)
    return tuple(
        v.findtext(f"{{{_NS}}}fullName") or "" for v in root.findall(f"{{{_NS}}}values")
    )


def parse_record_type_process(text: str) -> str:
    """The business process a record type file names, or empty."""
    return ET.fromstring(text).findtext(f"{{{_NS}}}businessProcess") or ""


# --- the adapter ------------------------------------------------------------------------------


class SalesforceAdapter(Adapter):
    """Reads and builds Salesforce structure through the `sf` CLI. Build one with `make_adapter`."""

    platform = PLATFORM

    def __init__(
        self,
        org: str,
        *,
        production: bool = False,
        api_version: str = DEFAULT_API_VERSION,
        cli: str = DEFAULT_CLI,
        runner: Runner = subprocess_runner,
        build_dir: Path | None = None,
    ) -> None:
        self.target = org
        self.production = production
        self.api_version = api_version
        self.cli = cli
        self.build_dir = build_dir
        self.mode = Mode(dry_run=True, production=production, allow_review=False)
        self.skipped: list[Change] = []
        self.notes: list[str] = []
        self.last_states: dict[str, str] = {}
        self._runner = runner
        self._org_info: OrgInfo | None = None
        self._last: tuple[State, Snapshot] | None = None

    def __repr__(self) -> str:
        return f"SalesforceAdapter(org={self.target!r}, production={self.production})"

    # -- running sf ----------------------------------------------------------------------------

    def _run(self, args: Sequence[str], *, cwd: Path | None = None, timeout: int = READ_TIMEOUT) -> Reply:
        """Run `sf <args> --json` through the runner and parse the JSON. Every sf call comes through here.

        Source: https://raw.githubusercontent.com/salesforcecli/sf-plugins-core/main/src/sfCommand.ts
        (`--json` prints `{status, result, warnings}` on success and an error envelope on failure, on stdout).
        """
        argv = [self.cli, *args]
        for flag in FORBIDDEN_FLAGS:
            if flag in argv:
                raise SafetyError(f"Refusing to run `sf` with {flag}.")
        if any(a.startswith("--") and "destructive" in a.lower() for a in argv):
            raise SafetyError("Refusing to run `sf` with a destructive-changes option.")
        out = self._runner(argv, cwd, timeout)
        try:
            body = json.loads(out.stdout)
        except ValueError:
            body = None
        if not isinstance(body, dict):
            tail = redact((out.stderr or out.stdout).strip())[:500]
            raise SalesforceError(f"`sf {' '.join(args[:3])}` gave no JSON (exit {out.returncode}): {tail}")
        return Reply(out.returncode, body)

    def _read(self, args: Sequence[str], what: str, *, cwd: Path | None = None) -> Any:
        """Run a read command and return its `result`, or raise with the redacted error.

        Source: https://raw.githubusercontent.com/salesforcecli/sf-plugins-core/main/src/sfCommand.ts (the `--json` envelope).
        """
        reply = self._run(args, cwd=cwd)
        if not reply.ok:
            raise SalesforceError(f"{what} failed: {error_text(reply.body)}")
        return reply.result

    def _target_args(self) -> list[str]:
        return ["--target-org", self.target]

    # -- identity and edition -----------------------------------------------------------------

    def read_org(self) -> OrgInfo:
        """Name the org, its edition and whether it is a sandbox, scratch org or production.

        Source: https://github.com/salesforcecli/plugin-org (`sf org display --json`: username,
        instanceUrl, and for scratch orgs devHubId and expirationDate) and
        platforms/salesforce/reference/open-questions.md B1 (`SELECT OrganizationType, IsSandbox FROM Organization`).
        The access token in the display output is dropped at once and never kept or logged.
        """
        if self._org_info is not None:
            return self._org_info
        shown = self._read(["org", "display", *self._target_args(), "--json"], "sf org display")
        shown = shown if isinstance(shown, dict) else {}
        instance = str(shown.get("instanceUrl") or "")
        scratch = bool(shown.get("devHubId") or shown.get("expirationDate") or _truthy(shown.get("isScratch")))
        scratch = scratch or ".scratch." in instance
        username = str(shown.get("username") or "")
        del shown  # holds an access token
        query = "SELECT Name, OrganizationType, IsSandbox FROM Organization"
        rows = self._read(["data", "query", "--query", query, *self._target_args(), "--json"], "The Organization query")
        records = (rows or {}).get("records") or []
        if not records:
            raise SalesforceError("The Organization query returned no row, so the edition is unknown.")
        rec = records[0]
        sandbox = _truthy(rec.get("IsSandbox")) or ".sandbox." in instance
        self._org_info = OrgInfo(
            name=str(rec.get("Name") or self.target), edition=str(rec.get("OrganizationType") or ""),
            is_sandbox=sandbox, is_scratch=scratch, username=username, instance_url=instance,
        )
        return self._org_info

    def target_label(self) -> str:
        """The name a production confirmation must type: the org's name and the alias."""
        return f"{self.read_org().name} ({self.target})"

    # -- reading ------------------------------------------------------------------------------

    def _list_custom(self) -> tuple[str, ...]:
        """Custom objects in the org, without managed-package ones.

        Source: https://github.com/salesforcecli/plugin-schema (`sf sobject list --sobject custom --json`
        returns a list of API names).
        """
        result = self._read(["sobject", "list", "--sobject", "custom", *self._target_args(), "--json"], "sf sobject list")
        names = [str(n) for n in result or []]
        return tuple(sorted(n for n in names if n.endswith("__c") and n.count("__") == 1))

    def _describe(self, api: str) -> dict[str, Any]:
        """Describe one object. Source: https://raw.githubusercontent.com/salesforcecli/plugin-schema/main/src/commands/sobject/describe.ts"""
        result = self._read(["sobject", "describe", "--sobject", api, *self._target_args(), "--json"], f"sf sobject describe {api}")
        return dict(result or {})

    def _read_stages(self) -> dict[str, dict[str, Any]]:
        """Read Opportunity stage values, active flags and probability.

        Source: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/object_reference.pdf
        (`OpportunityStage` supports query; fields ApiName, MasterLabel, IsActive, IsClosed, IsWon,
        DefaultProbability, SortOrder; see pipelines.md in the research).
        """
        query = (
            "SELECT ApiName, MasterLabel, IsActive, IsClosed, IsWon, DefaultProbability, SortOrder "
            "FROM OpportunityStage"
        )
        result = self._read(["data", "query", "--query", query, *self._target_args(), "--json"], "The OpportunityStage query")
        rows = sorted((result or {}).get("records") or [], key=lambda r: _number(r.get("SortOrder")) or 0)
        return {str(r.get("ApiName")): r for r in rows}

    def _read_processes(self) -> tuple[dict[str, tuple[str, ...]] | None, dict[str, str]]:
        """Read Opportunity business processes and which record type uses which.

        Source: https://raw.githubusercontent.com/salesforcecli/plugin-deploy-retrieve/main/src/commands/project/retrieve/start.ts
        (`sf project retrieve start --manifest`; a wildcard business process needs a wildcard record type
        in the same manifest, auth-and-setup.md). Retrieve needs the same permission as deploy. If it
        fails, the processes are unknown (None) and a note says so; the plan then trusts the design's stages.
        """
        manifest = gen.package_xml({("BusinessProcess", "*"), ("RecordType", "*")})
        root = Path(tempfile.mkdtemp(prefix="sf-read-", dir=self.build_dir if self.build_dir and self.build_dir.is_dir() else None))
        try:
            self._write_project(root, manifest, {})
            reply = self._run(
                ["project", "retrieve", "start", "--manifest", "package.xml", *self._target_args(),
                 "--api-version", self.api_version, "--wait", WAIT_MINUTES, "--json"],
                cwd=root, timeout=DEPLOY_TIMEOUT,
            )
            if not reply.ok:
                self.notes.append(
                    "Business processes could not be retrieved (" + error_text(reply.body) + "). "
                    "Pipeline stages are assumed to match the design."
                )
                return None, {}
            base = root / BASE / "objects" / "Opportunity"
            processes: dict[str, tuple[str, ...]] = {}
            for path in sorted((base / "businessProcesses").glob("*.businessProcess-meta.xml")):
                processes[path.name.split(".")[0]] = parse_process_file(path.read_text(encoding="utf-8"))
            used: dict[str, str] = {}
            for path in sorted((base / "recordTypes").glob("*.recordType-meta.xml")):
                process = parse_record_type_process(path.read_text(encoding="utf-8"))
                if process:
                    used[path.name.split(".")[0]] = process
            return processes, used
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def _snapshot(
        self, design: Design | None = None, *, apis: Sequence[str] | None = None, stages: bool | None = None,
        processes: bool | None = None,
    ) -> Snapshot:
        """Read the org. With a design (or `apis`) only those objects are described; otherwise every custom object is."""
        org = self.read_org()
        custom = self._list_custom()
        if apis is None:
            apis = _Names(design).object_apis() if design is not None else [*STANDARD_APIS, *custom]
        snap = Snapshot(org=org, custom_objects=custom)
        for api in sorted(set(apis)):
            if api in STANDARD_KEYS or api in custom:
                snap.describes[api] = self._describe(api)
        opp = snap.describes.get("Opportunity")
        if stages is None:
            stages = opp is not None
        if stages:
            snap.stages = self._read_stages()
        has_rt = opp is not None and any(
            not rt.get("master") and rt.get("active", True) for rt in opp.get("recordTypeInfos") or []
        )
        if processes is None:
            processes = has_rt
        if processes and has_rt:
            snap.processes, snap.record_type_process = self._read_processes()
        elif processes:
            snap.processes = {}
        return snap

    def read_state(self, design: Design | None = None) -> State:
        """Read live objects, custom fields, relationships and pipelines in canonical terms.

        Uses `sf sobject describe` for each design object (or, with no design, Account, Contact,
        Opportunity and every custom object), a query on OpportunityStage, and a retrieve of business
        processes. Without `design`, API names map to keys by guesswork (`Foo_bar__c` is `foo_bar`);
        `plan` re-maps the same reads with the design, so the two agree. Read-only. Sources are in the
        helpers it calls (`read_org`, `_describe`, `_read_stages`, `_read_processes`).
        """
        snap = self._snapshot(design)
        state = _build_state(snap, design)
        self._last = (state, snap)
        return state

    # -- planning ------------------------------------------------------------------------------

    def plan(self, design: Design, state: State) -> Plan:
        """Diff the design against live state, then fit the result to what Salesforce can take.

        Delegates to `tools.crm.planner.plan_changes`. If `state` is what `read_state` just returned it
        is re-mapped with the design first, so generated names match. Then: changes are reordered
        objects, relationships, fields, pipelines (rules and record types reference fields); renames, stage
        reorders and stage probability changes become manual steps; an Opportunity stage removal becomes a
        manual step; a field with no metadata file becomes a manual step; on an edition without the
        Metadata API every change becomes a manual step pointing at the build sheet.
        """
        org = self.read_org()
        if self._last is not None and self._last[0] is state:
            bound = _build_state(self._last[1], design)
        else:
            bound = state
        b = gen.build_model(design)
        target = self.target_label() if org.production else self.target
        base = plan_changes(
            design, bound, lambda kind, tgt, ctx: _payload(b, kind, tgt, ctx),
            target=target, source_urls=SOURCE_URLS, ui_paths=UI_PATHS,
            extra_manual_steps=_generator_steps(design, b) + _limit_steps(design, b, org) + _deploy_rest_steps(design),
        )
        changes, converted = _fit_changes(design, b, base.changes, org)
        return replace(base, changes=tuple(changes), manual_steps=base.manual_steps + tuple(converted))

    # -- applying ------------------------------------------------------------------------------

    def apply(self, plan: Plan, *, dry_run: bool = True) -> Result:
        """Apply a plan. A dry run is one check-only deploy of everything; a real run deploys in phases.

        Holds `needs_review` changes unless `self.mode.allow_review`, refuses a destructive change,
        refuses a real run on a production org unless `production` was passed, and re-reads the org before
        each phase, skipping satisfied changes (listed in `self.skipped`). On an edition without the
        Metadata API it changes nothing and reports the changes as remaining. It stops at the first
        failure. The production prompt belongs to the caller (D-14). Deploy sources are in `_deploy`.
        """
        runnable, held = check_gates(plan, replace(self.mode, dry_run=dry_run), confirm=lambda _t: None)
        self.skipped = []
        todo = list(runnable)
        org = self.read_org()
        if not todo:
            return Result(applied=(), remaining=held, dry_run=dry_run)
        if not org.metadata_api:
            self.notes.append(
                f"{org.edition or 'This edition'} cannot use the Metadata API. Nothing was deployed; build by hand from the build sheet."
            )
            return Result(applied=(), remaining=tuple(todo) + held, dry_run=dry_run)
        if not dry_run and org.production and not self.production:
            raise SafetyError(
                f"The org {org.name!r} is a production org. Re-run with --production (and confirm the org name)."
            )
        missing = [c for c in todo if not c.payload.get("components") or not c.payload.get("files")]
        if missing:
            return Result((), (Failure(missing[0], f"No Salesforce payload for {missing[0].kind} {missing[0].target}; re-plan with this tool."),),
                          tuple(c for c in todo if c is not missing[0]) + held, dry_run=dry_run)
        if dry_run:
            pending = self._pending(todo)
            if not pending:
                return Result(applied=(), remaining=held, dry_run=True)
            outcome = self._deploy(pending, dry_run=True)
            if outcome.ok:
                return Result(applied=(), remaining=tuple(pending) + held, dry_run=True)
            blamed = _blame(pending, outcome)
            return Result((), (Failure(blamed, _describe_failure(outcome)),),
                          tuple(c for c in pending if c is not blamed) + held, dry_run=True)
        applied: list[Change] = []
        for phase in sorted({PHASE.get(c.kind, 9) for c in todo}):
            batch = [c for c in todo if PHASE.get(c.kind, 9) == phase]
            pending = self._pending(batch)  # re-read the org before every batch
            if not pending:
                continue
            outcome = self._deploy(pending, dry_run=False)
            if outcome.ok:
                applied.extend(pending)
                continue
            blamed = _blame(pending, outcome)
            done = set(map(id, applied)) | set(map(id, self.skipped))
            rest = [c for c in todo if id(c) not in done and c is not blamed]
            return Result(tuple(applied), (Failure(blamed, _describe_failure(outcome)),), tuple(rest) + held, dry_run=False)
        return Result(tuple(applied), (), held, dry_run=False)

    def _pending(self, batch: Sequence[Change]) -> list[Change]:
        """Re-read the org and drop changes that are already in place (they go to `self.skipped`)."""
        checks = [c.payload.get("check") or {} for c in batch]
        apis = {a for chk in checks for a in _check_objects(chk)}
        need_stages = any(chk.get("stage_values") or chk.get("process_values") for chk in checks)
        need_process = any(chk.get("process_values") for chk in checks)
        snap = self._snapshot(apis=sorted(apis), stages=need_stages, processes=need_process)
        pending: list[Change] = []
        for change, chk in zip(batch, checks):
            if _satisfied(chk, snap):
                self.skipped.append(change)
            else:
                pending.append(change)
        return pending

    def _deploy(self, batch: Sequence[Change], *, dry_run: bool) -> DeployOutcome:
        """Write the files for `batch`, then run `sf project deploy start` on a manifest of exactly those members.

        Source: https://raw.githubusercontent.com/salesforcecli/plugin-deploy-retrieve/main/src/commands/project/deploy/start.ts
        (flags `--manifest`, `--target-org`, `--api-version`, `--wait`, `--dry-run`, `--json`). Never passes
        `--ignore-errors`, `--ignore-conflicts`, `--ignore-warnings`, `--purge-on-delete` or a destructive-changes
        flag. Exit codes and the JSON shape are parsed by `parse_deploy`. The folder is removed afterwards unless
        the deploy failed and a `build_dir` was given, so a failed run can be inspected.
        """
        files: dict[str, str] = {}
        members: set[tuple[str, str]] = set()
        for change in batch:
            files.update(change.payload["files"])
            members.update((t, m) for t, m in change.payload["components"])
        manifest = gen.package_xml(members).replace(
            f"<version>{DEFAULT_API_VERSION}</version>", f"<version>{self.api_version}</version>"
        )
        root = Path(tempfile.mkdtemp(prefix="sf-deploy-", dir=self.build_dir if self.build_dir and self.build_dir.is_dir() else None))
        keep = False
        try:
            self._write_project(root, manifest, files)
            args = [
                "project", "deploy", "start", "--manifest", "package.xml", *self._target_args(),
                "--api-version", self.api_version, "--wait", WAIT_MINUTES, "--json",
            ]
            if dry_run:
                args.insert(3, "--dry-run")
            reply = self._run(args, cwd=root, timeout=DEPLOY_TIMEOUT)
            outcome = parse_deploy(reply.body, reply.code)
            self.last_states = dict(outcome.states)
            keep = not outcome.ok and self.build_dir is not None
            return outcome
        finally:
            if not keep:
                shutil.rmtree(root, ignore_errors=True)

    def _write_project(self, root: Path, manifest: str, files: Mapping[str, str]) -> None:
        """Write `sfdx-project.json`, `package.xml` and the metadata files under `force-app/main/default`."""
        project = {
            "name": "crm-blueprints-build",
            "namespace": "",
            "packageDirectories": [{"default": True, "path": "force-app"}],
            "sfdcLoginUrl": "https://login.salesforce.com",
            "sourceApiVersion": self.api_version,
        }
        (root / "sfdx-project.json").write_text(json.dumps(project, indent=2) + "\n", encoding="utf-8")
        (root / "package.xml").write_text(manifest, encoding="utf-8")
        for rel, text in files.items():
            if "destructive" in rel.lower():
                raise SafetyError("Refusing to write a destructive-changes file.")
            path = root / BASE / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")


# --- checks of live state (used before each deploy phase) --------------------------------------


def _check_objects(chk: Mapping[str, Any]) -> set[str]:
    apis = set(chk.get("objects") or [])
    apis.update(o for o, _ in chk.get("fields") or [])
    apis.update(o for o, _, _ in chk.get("options") or [])
    apis.update(o for o, _, _ in chk.get("inactive") or [])
    apis.update(o for o, _ in chk.get("record_types") or [])
    if chk.get("stage_values") or chk.get("process_values"):
        apis.add("Opportunity")
    return apis


def _satisfied(chk: Mapping[str, Any], snap: Snapshot) -> bool:
    """True when the org already holds everything the change would deploy. An empty check is never satisfied."""
    if not chk:
        return False

    def field_of(obj: str, name: str) -> Mapping[str, Any] | None:
        return next((f for f in snap.describes.get(obj, {}).get("fields") or [] if f.get("name") == name), None)

    for obj in chk.get("objects") or []:
        if obj not in snap.describes:
            return False
    for obj, name in chk.get("fields") or []:
        if field_of(obj, name) is None:
            return False
    for obj, name, value in chk.get("options") or []:
        fld = field_of(obj, name)
        if fld is None or value not in {str(pv.get("value")) for pv in _active_values(fld)}:
            return False
    for obj, name, value in chk.get("inactive") or []:
        fld = field_of(obj, name)
        if fld is not None and value in {str(pv.get("value")) for pv in _active_values(fld)}:
            return False
    for obj, rt in chk.get("record_types") or []:
        rts = snap.describes.get(obj, {}).get("recordTypeInfos") or []
        if rt not in {str(r.get("developerName")) for r in rts}:
            return False
    for value in chk.get("stage_values") or []:
        row = snap.stages.get(value)
        if row is None or not _truthy(row.get("IsActive", True)):
            return False
    if snap.processes is not None:
        for process, values in chk.get("process_values") or []:
            if not set(values) <= set(snap.processes.get(process, ())):
                return False
    return True


def _blame(batch: Sequence[Change], outcome: DeployOutcome) -> Change:
    """The change a failed component belongs to; the first change if none matches."""
    for failure in outcome.failures:
        for change in batch:
            members = {m for _, m in change.payload.get("components") or []}
            if failure.full_name in members or any(failure.file_path.endswith(p) for p in change.payload.get("files") or {}):
                return change
    return batch[0]


def _describe_failure(outcome: DeployOutcome) -> str:
    lines = [f"Deploy {outcome.status or 'failed'} (exit {outcome.exit_code})."]
    if outcome.message:
        lines.append(outcome.message)
    for f in outcome.failures[:10]:
        where = f" in {f.file_path}" if f.file_path else ""
        lines.append(f"{f.problem_type} {f.component_type} {f.full_name}{where}: {f.problem}")
    return redact(" ".join(lines))[:3000]


# --- payloads ---------------------------------------------------------------------------------


def _payload(b: gen.Build, kind: str, target: str, ctx: dict[str, Any]) -> dict[str, Any]:
    """Build the payload of one change: the components it deploys, their file text, and a live check.

    The files come from the generator's `Build`, so they are the files `tools.generate` writes. An empty
    payload means the change has no metadata and is turned into a manual step by `_fit_changes`.
    """
    comps: list[tuple[str, str]] = []
    check: dict[str, Any] = {}
    overrides: dict[str, str] = {}

    if kind == "add_object":
        api = b.obj_api[ctx["object"].key]
        comps = [("CustomObject", api)]
        check = {"objects": [api]}
    elif kind == "add_relationship":
        comps = list(b.rel_components.get(ctx["relationship"].key, []))
        check = {
            "objects": [m for t, m in comps if t == "CustomObject"],
            "fields": [list(m.partition(".")[::2]) for t, m in comps if t == "CustomField"],
        }
    elif kind in ("add_field", "add_option", "remove_option"):
        f = ctx["field"]
        fkind = b.field_kind.get((f.object, f.key), "custom")
        if fkind in ("name", "owner"):
            return {"covered_by_object": True}
        if fkind != "custom":
            return {}
        obj_api, api = b.obj_api[f.object], b.field_api[(f.object, f.key)]
        comps = [("CustomField", f"{obj_api}.{api}")]
        if kind == "add_field":
            check = {"fields": [[obj_api, api]]}
        elif kind == "add_option":
            value = gen._values([(o.key, o.label) for o in f.options])[[o.key for o in f.options].index(ctx["option"].key)][0]
            check = {"options": [[obj_api, api, value]]}
        else:
            value = ctx["live_option"][1]
            overrides[b.component_paths[comps[0]]] = add_inactive_value(b.files[b.component_paths[comps[0]]], value)
            check = {"inactive": [[obj_api, api, value]]}
    elif kind in ("add_pipeline", "add_stage", "remove_stage"):
        p = b.pipe(ctx["pipeline"])
        pl = p.pipeline
        values = [si.value for si in p.stages]
        rules = [("ValidationRule", f"{r.obj_api}.{r.name}") for r in b.rules
                 if r.pipeline_key == pl.key and r.obj_api == p.obj_api]
        if p.is_opp:
            if kind == "remove_stage":
                return {}
            if kind == "add_stage":
                one = next(si.value for si in p.stages if si.stage.key == ctx["stage"].key)
                values_check = [one]
            else:
                values_check = values
            comps = [("StandardValueSet", "OpportunityStage"), ("BusinessProcess", f"Opportunity.{p.bp}")]
            if kind == "add_pipeline":
                comps.append(("RecordType", f"Opportunity.{p.rt}"))
            if p.path:
                comps += [("PathAssistant", p.path), ("Settings", "PathAssistant")]
            check = {"stage_values": values_check, "process_values": [[p.bp, values_check]]}
            if kind == "add_pipeline":
                check["record_types"] = [["Opportunity", p.rt]]
        else:
            stage_api = b.stage_field[pl.object]
            field_comp = ("CustomField", f"{p.obj_api}.{stage_api}")
            comps = [field_comp]
            if p.rt and kind != "remove_stage":
                comps.append(("RecordType", f"{p.obj_api}.{p.rt}"))
            if kind == "add_pipeline":
                check = {"fields": [[p.obj_api, stage_api]],
                         "options": [[p.obj_api, stage_api, v] for v in values]}
                if p.rt:
                    check["record_types"] = [[p.obj_api, p.rt]]
            elif kind == "add_stage":
                one = next(si.value for si in p.stages if si.stage.key == ctx["stage"].key)
                check = {"options": [[p.obj_api, stage_api, one]]}
            else:  # remove_stage: deactivate the value
                value = ctx["live_stage"].label
                if value in {si.value for q in b.pipes if q.pipeline.object == pl.object for si in q.stages}:
                    return {}  # another pipeline still uses this value
                path = b.component_paths[field_comp]
                overrides[path] = add_inactive_value(b.files[path], value)
                check = {"inactive": [[p.obj_api, stage_api, value]]}
        if kind != "remove_stage":
            comps += rules
    else:
        return {}  # renames, reorders and probability changes are manual

    files = {b.component_paths[c]: overrides.get(b.component_paths[c], b.files[b.component_paths[c]]) for c in comps}
    return {"components": [list(c) for c in sorted(set(comps))], "files": files, "check": check}


# --- fitting a plan to Salesforce -------------------------------------------------------------

_BY_HAND = {
    "rename_object": ("Rename object {t} by hand", "The component's full name is its identity, so a rename deploys as a new object (gotcha 2)."),
    "rename_field": ("Rename field {t} by hand", "The component's full name is its identity, so a rename deploys as a new field (gotcha 2)."),
    "rename_option": ("Rename option {t} by hand", "A picklist value's full name is its identity, so a rename deploys as a new value (gotcha 2)."),
    "rename_stage": ("Rename stage {t} by hand", "A stage value's full name is its identity, so a rename deploys as a new value (gotcha 2)."),
    "update_stage": ("Change stage {t} by hand", "A deploy is not shown to change the type or probability of an existing stage value."),
    "reorder_stages": ("Reorder stages of {t} by hand", "Stage order is not shown to be changeable by a source deploy."),
}
_ADD_PATHS = {
    "add_object": f"{_SETUP}, Create, Custom Object",
    "add_relationship": f"{_SETUP}, pick the child object, Fields & Relationships, New, Lookup Relationship",
    "add_field": f"{_SETUP}, pick the object, Fields & Relationships, New",
    "add_option": f"{_SETUP}, pick the object, Fields & Relationships, the picklist field, Values, New",
    "remove_option": f"{_SETUP}, pick the object, Fields & Relationships, the picklist field, Values, Deactivate",
    "add_pipeline": f"{_SETUP}, Opportunity (or the object), Record Types, and Setup, Feature Settings, Sales, Sales Processes",
    "add_stage": "Setup, Object Manager, Opportunity (or the object), Fields & Relationships, Stage, Values, New",
    "remove_stage": "Setup, Object Manager, Opportunity, Fields & Relationships, Stage, Values, Deactivate",
}


def _build_sheet_path(design: Design) -> str:
    if design.source_path:
        folder = Path(design.source_path).resolve().parent
        try:
            folder = folder.relative_to(REPO_ROOT)
        except ValueError:
            pass
        return str(folder / PLATFORM / "build-sheet.md")
    return f"blueprints/<name>/{PLATFORM}/build-sheet.md"


def _fit_changes(
    design: Design, b: gen.Build, changes: Sequence[Change], org: OrgInfo
) -> tuple[list[Change], list[ManualStep]]:
    """Reorder, drop, or turn into manual steps the changes the Metadata API cannot take."""
    manual: list[ManualStep] = []
    kept: list[Change] = []
    sheet = _build_sheet_path(design)
    for c in changes:
        if c.payload.get("covered_by_object"):
            continue  # the Name and Owner fields exist with the object
        if c.kind in _BY_HAND:
            title, why = _BY_HAND[c.kind]
            manual.append(ManualStep(
                title=title.format(t=c.target), reason=why + f" Change wanted: {c.summary}.",
                ui_path=_ADD_PATHS.get(c.kind, f"{_SETUP}, pick the object"),
                done_when="The org shows the design's wording and re-planning shows no difference.",
                drift=True,
            ))
            continue
        if not c.payload:
            if c.kind == "remove_stage":
                manual.append(ManualStep(
                    title=f"Retire stage {c.target}",
                    reason=(
                        "The design no longer has this stage. The research does not show that a source deploy can "
                        "deactivate an Opportunity stage value (open-questions.md E10), and this tool never deletes."
                    ),
                    ui_path=_ADD_PATHS["remove_stage"],
                    done_when="No open record uses the stage, it is deactivated in Setup, and re-planning shows no difference.",
                    risk="destructive",
                    instructions=("1. Move every record out of the stage. 2. Remove it from the sales process and paths. "
                                  "3. Deactivate it in the Stage field's values. " + _MIGRATION),
                ))
            else:
                manual.append(ManualStep(
                    title=f"{c.summary} by hand",
                    reason="This item has no metadata file (a standard field or a value shared by another pipeline).",
                    ui_path=_ADD_PATHS.get(c.kind, f"{_SETUP}, pick the object"),
                    done_when="The org shows the design's wording and re-planning shows no difference.",
                    drift=True,
                ))
            continue
        kept.append(c)
    kept = [c for _, c in sorted(enumerate(kept), key=lambda ic: (PHASE.get(ic[1].kind, 9), ic[0]))]
    if not org.metadata_api:
        edition = org.edition or "This edition"
        for c in kept:
            manual.append(ManualStep(
                title=c.summary,
                reason=(f"{edition} cannot use the Metadata API, so this tool does not deploy. "
                        f"Build by hand from {sheet}."),
                ui_path=_ADD_PATHS.get(c.kind, f"{_SETUP}, pick the object"),
                done_when="The org shows the design's wording and re-planning shows no difference.",
                drift=True,
            ))
        kept = []
    return kept, manual


def _generator_steps(design: Design, b: gen.Build) -> list[ManualStep]:
    """The generator's manual steps (flows, page layouts, list view sort, lead mapping...), minus its set-up group."""
    return [
        ManualStep(title=s["title"], reason=s["why"], ui_path=s["where"], done_when=s["done_when"])
        for s in gen.manual_steps(b)
        if s["group"] != "setup"
    ]


def _deploy_rest_steps(design: Design) -> list[ManualStep]:
    folder = _build_sheet_path(design).rsplit("/", 1)[0]
    return [ManualStep(
        title="Deploy the permission set and the list views",
        reason=(
            "A change deploys only its own components. A permission set is overwritten whole and a list view "
            "reads columns that must exist, so neither is deployed by a change. New fields are invisible until "
            "a permission set grants them."
        ),
        ui_path=(f"Terminal, in {folder}: sf project deploy start --dry-run --manifest package.xml, then the same "
                 "without --dry-run, once every field exists. Or build them from the build sheet."),
        done_when="The permission set exists and is assigned, and the list views show in the org.",
    )]


def _limit_steps(design: Design, b: gen.Build, org: OrgInfo) -> list[ManualStep]:
    """Warn when the design is near the edition's custom object or field allowance (secondary figures, objects.md)."""
    limits = EDITION_LIMITS.get(org.edition_key)
    if limits is None:
        return []
    max_objects, max_fields = limits
    n_objects = len(b.custom_objects) + len(b.junctions)
    per_obj: dict[str, int] = {}
    for f in design.fields:
        if b.field_kind[(f.object, f.key)] == "custom":
            per_obj[b.obj_api[f.object]] = per_obj.get(b.obj_api[f.object], 0) + 1
    most = max(per_obj.values(), default=0)
    over_objects = n_objects > max_objects * LIMIT_WARN
    over_fields = most > max_fields * LIMIT_WARN
    if not (over_objects or over_fields):
        return []
    return [ManualStep(
        title="Check the edition limits",
        reason=(
            f"{org.edition} allows about {max_objects} custom objects and {max_fields} custom fields per object "
            f"(secondary-source figures, objects.md). This design needs {n_objects} custom objects and up to "
            f"{most} custom fields on one object, which is over {int(LIMIT_WARN * 100)} percent of an allowance."
        ),
        ui_path="Setup, Company Information, and Setup, Object Manager (the object's field count)",
        done_when="The real allowances are confirmed to fit, or the design is trimmed, and re-planning shows no difference.",
    )]


# --- factory ----------------------------------------------------------------------------------


def make_adapter(
    env: Mapping[str, str],
    *,
    target: str | None = None,
    production: bool = False,
    runner: Runner | None = None,
    build_dir: Path | None = None,
) -> SalesforceAdapter:
    """Build the adapter from environment variables.

    `SF_TARGET_ORG` is an `sf` org alias or username already authorised with `sf org login web`; `target`
    overrides it. There is no secret in the environment. `SF_API_VERSION` (default 67.0) and `SF_CLI`
    (default `sf`) are optional. The environment is read through `safety.get_credential`, so a missing
    org raises `SafetyError` naming the variable. Nothing is run here; the first read calls `sf`.
    `build_dir`, if given, is where deploy folders are made (for example `clients/<client>/build/salesforce`).
    """
    environment = dict(env)
    org = target or get_credential(TARGET_VAR, environment)
    version = environment.get(VERSION_VAR, "") or DEFAULT_API_VERSION
    if not _VERSION.match(version):
        raise SafetyError(f"{VERSION_VAR} must look like 67.0, not {version!r}.")
    cli = environment.get(CLI_VAR, "") or DEFAULT_CLI
    return SalesforceAdapter(
        org, production=production, api_version=version, cli=cli,
        runner=runner or subprocess_runner, build_dir=build_dir,
    )
