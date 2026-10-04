"""Generate Salesforce SFDX source metadata, a build sheet and manual steps from a design.

Files written to `<out_dir>` (normally `blueprints/<name>/salesforce/`):

- `force-app/main/default/...`: source-format metadata (API 67.0). Custom objects get an object file.
  Standard objects (Account, Contact, Opportunity) get child files only, never an object file.
- `sfdx-project.json` and `package.xml`: the project file and a manifest listing exactly the members
  generated.
- `build-sheet.md`: the human checklist, through `build_sheet.render_build_sheet`, with the validation
  rule formulas in the stage-rules section.
- `manual-steps.md`: everything the metadata cannot do, and everything the research marks unverified.

Shapes come from `platforms/salesforce/reference/`. Output is deterministic: child elements are
ordered (`fullName` first, then alphabetical), 4-space indentation, an XML declaration, a trailing
newline, and every collection is in design order or sorted. No timestamps.

Judgement calls are in DECISIONS.md. Nothing is deleted from `out_dir`: regenerating after a design
edit can leave orphan files, and `tools.generate --check` reports them as unexpected.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tools.design import Design, FieldDef, ObjectDef, Pipeline, RelationshipDef, Stage, View
from tools.generators.build_sheet import BuildSheetHooks, render_build_sheet

PLATFORM = "salesforce"
API_VERSION = "67.0"
NAMESPACE = "http://soap.sforce.com/2006/04/metadata"
BASE = "force-app/main/default"

NAME_LIMIT = 40
LABEL_LIMIT = 40
DESCRIPTION_LIMIT = 1000
MESSAGE_LIMIT = 255
PATH_FIELD_LIMIT = 5

# Standard child relationship names on the objects we hang lookups from. A custom lookup that reuses
# one of these fails to deploy, so the generator picks another name.
RESERVED_RELATIONSHIP_NAMES: frozenset[str] = frozenset(
    n.lower()
    for n in (
        "Contacts Opportunities Cases Contracts Assets Orders Notes Attachments Tasks Events "
        "ActivityHistories OpenActivities EmailMessages ContactRoles OpportunityLineItems Quotes "
        "Partners AccountPartners Feeds Histories Shares TeamMembers AccountContactRoles "
        "OpportunityContactRoles OpportunityHistories OpportunityFieldHistories OpportunityCompetitors "
        "OpportunityTeamMembers CampaignMembers ContentDocumentLinks AttachedContentNotes "
        "CombinedAttachments ProcessInstances ProcessSteps Solutions Users Owner Account Contact "
        "Opportunity"
    ).split()
)

SPECIAL_CATEGORY = re.compile(r"health|vulnerab|special categor|sensitive personal data", re.I)


class SalesforceGenerationError(ValueError):
    """A design asks for something Salesforce cannot hold (a bad `api_name` override, say)."""


# --- XML --------------------------------------------------------------------------------------


class Ordered(list):
    """A list of (tag, value) pairs that is written in the order given, not sorted."""


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return _esc(str(value))


def _sorted_pairs(pairs: list[tuple[str, Any]]) -> list[tuple[str, Any]]:
    """`fullName` first, then alphabetical by tag. Stable, so repeated tags keep their order."""
    return sorted(pairs, key=lambda p: (0 if p[0] == "fullName" else 1, p[0].lower()))


def _write_children(lines: list[str], pairs: list[tuple[str, Any]], depth: int) -> None:
    ordered = pairs if isinstance(pairs, Ordered) else _sorted_pairs(pairs)
    pad = "    " * depth
    for tag, value in ordered:
        if value is None:
            continue
        if isinstance(value, list):
            lines.append(f"{pad}<{tag}>")
            _write_children(lines, value, depth + 1)
            lines.append(f"{pad}</{tag}>")
        else:
            lines.append(f"{pad}<{tag}>{_scalar(value)}</{tag}>")


def xml_doc(root: str, pairs: list[tuple[str, Any]]) -> str:
    """One metadata file: declaration, root element with the namespace, children, trailing newline."""
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', f'<{root} xmlns="{NAMESPACE}">']
    _write_children(lines, pairs, 1)
    lines.append(f"</{root}>")
    return "\n".join(lines) + "\n"


# --- naming -----------------------------------------------------------------------------------


def _ascii(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def _slug(text: str) -> str:
    """ASCII letters, digits and single underscores, starting with a letter."""
    s = re.sub(r"[^A-Za-z0-9]+", "_", _ascii(text)).strip("_") or "X"
    return s if s[0].isalpha() else "X" + s


def _title(key: str) -> str:
    """`next_step_date` becomes `Next_step_date`."""
    s = _slug(key)
    return s[0].upper() + s[1:]


def _clip(text: str, limit: int) -> str:
    text = " ".join(text.split()) if "\n" not in text else text.strip()
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def _fit_label(text: str) -> str:
    text = text.strip()
    return text if len(text) <= LABEL_LIMIT else text[:LABEL_LIMIT].rstrip()


def _fit_name(base: str, limit: int = NAME_LIMIT) -> str:
    return base[:limit].rstrip("_")


def _hash_name(raw: str, limit: int = NAME_LIMIT) -> str:
    """A name of at most `limit` characters; a long one keeps its start and gains a short hash."""
    if len(raw) <= limit:
        return raw
    return raw[: limit - 7].rstrip("_") + "_" + hashlib.sha1(raw.encode()).hexdigest()[:6]


class Names:
    """Hands out API names that are unique (case-insensitively) within a scope."""

    def __init__(self) -> None:
        self.used: dict[Any, set[str]] = defaultdict(set)

    def reserve(self, scope: Any, name: str) -> bool:
        if name.lower() in self.used[scope]:
            return False
        self.used[scope].add(name.lower())
        return True

    def take(self, scope: Any, candidates: list[str], limit: int = NAME_LIMIT) -> str:
        for cand in candidates:
            name = _fit_name(cand, limit)
            if name and self.reserve(scope, name):
                return name
        n = 2
        while True:
            suffix = f"_{n}"
            name = _fit_name(candidates[0], limit - len(suffix)) + suffix
            if self.reserve(scope, name):
                return name
            n += 1


def _overrides(design: Design) -> dict[str, Any]:
    value = design.platform_overrides.get(PLATFORM, {})
    return value if isinstance(value, dict) else {}


def _override(design: Design, section: str, target: str, key: str) -> str | None:
    entry = _overrides(design).get(section, {})
    entry = entry.get(target, {}) if isinstance(entry, dict) else {}
    value = entry.get(key) if isinstance(entry, dict) else None
    return value if isinstance(value, str) and value else None


API_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)*$")


def _override_api(raw: str, where: str) -> str:
    """An `api_name` override without its `__c`. Raises if Salesforce would refuse it."""
    base = raw[:-3] if raw.endswith("__c") else raw
    if not API_NAME.match(base) or len(base) > NAME_LIMIT:
        raise SalesforceGenerationError(
            f"{where}: api_name {raw!r} is not a valid Salesforce API name "
            f"(letters, digits, single underscores, start with a letter, at most {NAME_LIMIT} characters before __c)"
        )
    return base


def _fstr(text: str) -> str:
    """A formula string literal."""
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _sensitive(f: FieldDef) -> str | None:
    """`Confidential`, `Restricted` or None: how the description flags the field."""
    if f.description.startswith("DATA PROTECTION:"):
        return "Restricted" if SPECIAL_CATEGORY.search(f.description) else "Confidential"
    if re.search(r"sensitive personal data", f.description, re.I):
        return "Restricted"
    return None


def _prob(value: float | None) -> int:
    return int(round(value)) if value is not None else 0


# --- the model --------------------------------------------------------------------------------


@dataclass
class StageInfo:
    stage: Stage
    value: str
    ordinal: int | None  # position among the pipeline's non-lost stages; None for lost


@dataclass
class PipeInfo:
    pipeline: Pipeline
    obj_api: str
    is_opp: bool
    stage_api: str
    stages: list[StageInfo]
    rt: str | None = None
    bp: str | None = None
    path: str | None = None


@dataclass
class Rule:
    name: str
    obj_api: str
    pipeline_key: str
    stage_key: str
    kind: str  # gate or lost
    formula: str
    message: str
    display_field: str | None
    description: str


@dataclass
class ViewFile:
    view: View
    obj_api: str
    name: str
    xml: str


@dataclass
class Junction:
    rel: RelationshipDef
    api: str
    label: str


@dataclass
class Build:
    design: Design
    obj_api: dict[str, str] = field(default_factory=dict)
    custom_objects: list[str] = field(default_factory=list)  # object keys, design order
    field_api: dict[tuple[str, str], str] = field(default_factory=dict)
    field_kind: dict[tuple[str, str], str] = field(default_factory=dict)  # custom native name owner
    name_label: dict[str, str] = field(default_factory=dict)
    files: dict[str, str] = field(default_factory=dict)  # path under BASE -> text
    components: set[tuple[str, str]] = field(default_factory=set)
    field_perms: set[str] = field(default_factory=set)
    object_perms: set[str] = field(default_factory=set)
    rt_vis: set[str] = field(default_factory=set)
    pipes: list[PipeInfo] = field(default_factory=list)
    stage_field: dict[str, str] = field(default_factory=dict)  # object key -> generated stage field
    opp_values: list[tuple[str, Stage]] = field(default_factory=list)
    rules: list[Rule] = field(default_factory=list)
    views: list[ViewFile] = field(default_factory=list)
    unparsed_views: list[View] = field(default_factory=list)
    junctions: list[Junction] = field(default_factory=list)
    rel_fields: dict[str, str] = field(default_factory=dict)  # relationship key -> description of build
    flagged: list[tuple[str, str]] = field(default_factory=list)  # (object api, field api)
    flagged_native: list[FieldDef] = field(default_factory=list)
    comma_options: list[tuple[str, str]] = field(default_factory=list)
    skipped_required: list[FieldDef] = field(default_factory=list)
    multi_blank: bool = False
    names: Names = field(default_factory=Names)

    def add(self, ctype: str, member: str, path: str, text: str) -> None:
        self.components.add((ctype, member))
        self.files[path] = text

    def rules_for(self, pipeline: Pipeline, stage: Stage) -> list[Rule]:
        return [r for r in self.rules if r.pipeline_key == pipeline.key and r.stage_key == stage.key
                and r.obj_api == self.obj_api[pipeline.object]]

    def pipe(self, pipeline: Pipeline) -> PipeInfo:
        return next(p for p in self.pipes if p.pipeline is pipeline)


def _object_api(design: Design, b: Build) -> None:
    custom = [o for o in design.objects if o.kind == "custom"]
    for o in design.objects:
        if o.kind == "core":
            b.obj_api[o.key] = o.native_names.get(PLATFORM, o.label)
    explicit: dict[str, str] = {}
    for o in custom:
        raw = _override(design, "objects", o.key, "api_name")
        if raw:
            base = _override_api(raw, f"platform_overrides.salesforce.objects.{o.key}")
            if not b.names.reserve("objects", base):
                raise SalesforceGenerationError(f"object {o.key}: api_name {raw!r} is used twice")
            explicit[o.key] = base
    for o in custom:
        base = explicit.get(o.key) or b.names.take("objects", [_title(o.key)])
        b.obj_api[o.key] = base + "__c"
        b.custom_objects.append(o.key)


def _field_api(design: Design, b: Build) -> None:
    """Decide the API name of every design field."""
    pending: list[FieldDef] = []
    for f in design.fields:
        key = (f.object, f.key)
        obj = design.get_object(f.object)
        custom_obj = obj is not None and obj.kind == "custom"
        scope = b.obj_api.get(f.object, f.object)
        if PLATFORM in f.native:
            b.field_api[key] = f.native_names.get(PLATFORM, f.key)
            b.field_kind[key] = "native"
        elif custom_obj and f.key == "name" and f.type == "text":
            b.field_api[key] = "Name"
            b.field_kind[key] = "name"
            b.name_label[f.object] = f.label
        elif custom_obj and f.key == "owner" and f.type == "user":
            b.field_api[key] = "OwnerId"
            b.field_kind[key] = "owner"
        else:
            raw = _override(design, "fields", f"{f.object}.{f.key}", "api_name")
            if raw:
                base = _override_api(raw, f"platform_overrides.salesforce.fields.{f.object}.{f.key}")
                if not b.names.reserve(scope, base):
                    raise SalesforceGenerationError(f"field {f.object}.{f.key}: api_name {raw!r} is used twice")
                b.field_api[key] = base + "__c"
                b.field_kind[key] = "custom"
            else:
                pending.append(f)
    for f in pending:
        base = b.names.take(b.obj_api[f.object], [_title(f.key)])
        b.field_api[(f.object, f.key)] = base + "__c"
        b.field_kind[(f.object, f.key)] = "custom"


# --- field XML --------------------------------------------------------------------------------


def _values(options: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """(stored value, label) pairs. The stored value is the label, which is what users see."""
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for key, label in options:
        value = " ".join(label.split()) or key
        if value.lower() in seen:
            value = f"{value} ({key})"
        seen.add(value.lower())
        out.append((value, label.strip() or value))
    return out


def _value_set(options: list[tuple[str, str]]) -> list[tuple[str, Any]]:
    return [
        ("restricted", True),
        ("valueSetDefinition", [
            ("sorted", False),
            *[("value", [("fullName", v), ("default", False), ("label", lab)]) for v, lab in _values(options)],
        ]),
    ]


def _picklist_xml(api: str, label: str, description: str, options: list[tuple[str, str]], *,
                  multi: bool = False, required: bool = False) -> str:
    pairs: list[tuple[str, Any]] = [
        ("fullName", api),
        ("label", _fit_label(label)),
        ("description", _clip(description, DESCRIPTION_LIMIT)),
        ("required", required),
        ("type", "MultiselectPicklist" if multi else "Picklist"),
        ("valueSet", _value_set(options)),
    ]
    if multi:
        pairs.append(("visibleLines", 4))
    return xml_doc("CustomField", pairs)


def _field_xml(b: Build, f: FieldDef, api: str, obj_api: str, flag: str | None) -> tuple[str, bool]:
    """The field file text, and whether the field is required (so the permission set leaves it out)."""
    can_require = f.type not in ("checkbox", "user")
    required = f.required and can_require
    if f.required and not can_require:
        b.skipped_required.append(f)
    pairs: list[tuple[str, Any]] = [
        ("fullName", api),
        ("label", _fit_label(f.label)),
        ("description", _clip(f.description, DESCRIPTION_LIMIT)),
    ]
    if can_require:
        pairs.append(("required", required))
    t = f.type
    if t == "text":
        pairs += [("type", "Text"), ("length", 255), ("externalId", False), ("unique", False)]
    elif t == "long_text":
        pairs += [("type", "LongTextArea"), ("length", 32768), ("visibleLines", 6)]
    elif t in ("select", "multi_select"):
        opts = [(o.key, o.label) for o in f.options]
        multi = t == "multi_select"
        pairs += [("type", "MultiselectPicklist" if multi else "Picklist"), ("valueSet", _value_set(opts))]
        if multi:
            pairs.append(("visibleLines", 4))
        for o in f.options:
            if "," in o.label:
                b.comma_options.append((f"{obj_api}.{api}", o.label))
    elif t in ("number", "currency", "percent"):
        precision, scale = {"number": (18, 0), "currency": (18, 2), "percent": (5, 2)}[t]
        pairs += [("type", t.capitalize()), ("precision", precision), ("scale", scale)]
    elif t == "date":
        pairs.append(("type", "Date"))
    elif t == "datetime":
        pairs.append(("type", "DateTime"))
    elif t == "checkbox":
        pairs += [("type", "Checkbox"), ("defaultValue", False)]
    elif t in ("url", "email", "phone"):
        pairs.append(("type", t.capitalize()))
    elif t == "user":
        obj = b.design.get_object(f.object)
        plural = obj.plural_label if obj else f.object
        rel = b.names.take(("relname", "User"), [f"{obj_api.removesuffix('__c')}_{api.removesuffix('__c')}"])
        pairs += [
            ("type", "Lookup"), ("referenceTo", "User"), ("deleteConstraint", "SetNull"),
            ("relationshipLabel", _clip(f"{plural} {f.label}", 80)), ("relationshipName", rel),
        ]
    else:  # the validator rejects unknown types; keep the generator total
        pairs.append(("type", "Text"))
        pairs.append(("length", 255))
    if flag and t != "user":
        pairs += [("complianceGroup", "PII;GDPR"), ("securityClassification", flag)]
    return xml_doc("CustomField", pairs), required


def _emit_fields(b: Build) -> None:
    design = b.design
    for f in design.fields:
        key = (f.object, f.key)
        flag = _sensitive(f)
        kind = b.field_kind[key]
        if kind != "custom":
            if flag and kind == "native":
                b.flagged_native.append(f)
            continue
        obj_api, api = b.obj_api[f.object], b.field_api[key]
        text, required = _field_xml(b, f, api, obj_api, flag)
        b.add("CustomField", f"{obj_api}.{api}", f"objects/{obj_api}/fields/{api}.field-meta.xml", text)
        if not required:
            b.field_perms.add(f"{obj_api}.{api}")
        b.object_perms.add(obj_api)
        if flag and f.type != "user":
            b.flagged.append((obj_api, api))


# --- relationships ----------------------------------------------------------------------------


def _rel_name(b: Build, parent_api: str, label: str, fallback: str) -> str:
    """A relationship name unique on the parent and not one of the standard child names."""
    cand = _slug(label)
    scope = ("relname", parent_api)
    if cand.lower() not in RESERVED_RELATIONSHIP_NAMES and b.names.reserve(scope, cand):
        return _fit_name(cand)
    return b.names.take(scope, [f"{cand}_{fallback}", f"{cand}_{fallback}_rel"])


def _emit_relationships(b: Build) -> None:
    design = b.design
    for rel in design.relationships:
        if PLATFORM in rel.native:
            continue
        frm, to = design.get_object(rel.from_object), design.get_object(rel.to_object)
        if frm is None or to is None:
            continue
        desc = rel.purpose or f"Link from {frm.label} to {to.label}."
        if rel.cardinality == "many_to_many":
            _emit_junction(b, rel, frm, to, desc)
            continue
        if rel.cardinality == "one_to_many":
            child, parent, child_label, list_label = to, frm, rel.to_label, rel.from_label
        else:  # many_to_one and one_to_one: the field sits on the `from` side
            child, parent, child_label, list_label = frm, to, rel.from_label, rel.to_label
        child_api, parent_api = b.obj_api[child.key], b.obj_api[parent.key]
        base = b.names.take(child_api, [_title(child_label), _title(rel.key)])
        api = base + "__c"
        name = _rel_name(b, parent_api, list_label, base)
        text = xml_doc("CustomField", [
            ("fullName", api), ("label", _fit_label(child_label)), ("description", _clip(desc, DESCRIPTION_LIMIT)),
            ("type", "Lookup"), ("referenceTo", parent_api), ("deleteConstraint", "SetNull"),
            ("externalId", False), ("required", False),
            ("relationshipLabel", _clip(list_label, 80)), ("relationshipName", name),
        ])
        b.add("CustomField", f"{child_api}.{api}", f"objects/{child_api}/fields/{api}.field-meta.xml", text)
        b.field_perms.add(f"{child_api}.{api}")
        b.object_perms.add(child_api)
        b.rel_fields[rel.key] = f"Lookup `{api}` on {child_api} to {parent_api}"


def _emit_junction(b: Build, rel: RelationshipDef, frm: ObjectDef, to: ObjectDef, desc: str) -> None:
    base = b.names.take("objects", [_title(rel.key)])
    api = base + "__c"
    label = _fit_label(f"{frm.label} to {to.label.lower()} link")
    plural = _fit_label(f"{frm.label} to {to.label.lower()} links")
    prefix = "".join(w[0] for w in rel.key.split("_") if w).upper() or "J"
    b.obj_api[f"__junction_{rel.key}"] = api
    b.junctions.append(Junction(rel, api, label))
    text = xml_doc("CustomObject", [
        ("deploymentStatus", "Deployed"), ("description", _clip(desc, DESCRIPTION_LIMIT)),
        ("enableActivities", False), ("enableHistory", False), ("enableReports", True), ("enableSearch", True),
        ("label", label),
        ("nameField", [("displayFormat", f"{prefix}-{{00000}}"), ("label", _fit_label(f"{label} number")),
                       ("type", "AutoNumber")]),
        ("pluralLabel", plural), ("sharingModel", "ControlledByParent"), ("visibility", "Public"),
    ])
    b.add("CustomObject", api, f"objects/{api}/{api}.object-meta.xml", text)
    b.object_perms.add(api)
    same = frm.key == to.key
    sides = [
        (frm, "From_" + _title(frm.key) if same else _title(frm.key), rel.from_label, 0),
        (to, "To_" + _title(to.key) if same else _title(to.key), rel.to_label, 1),
    ]
    for parent, fbase, list_label, order in sides:
        parent_api = b.obj_api[parent.key]
        fapi = b.names.take(api, [fbase]) + "__c"
        name = _rel_name(b, parent_api, list_label, base)
        ftext = xml_doc("CustomField", [
            ("fullName", fapi), ("label", _fit_label(parent.label)),
            ("description", _clip(f"{desc} Master side {order + 1} of the link.", DESCRIPTION_LIMIT)),
            ("type", "MasterDetail"), ("referenceTo", parent_api),
            ("relationshipLabel", _clip(list_label, 80)), ("relationshipName", name),
            ("relationshipOrder", order), ("reparentableMasterDetail", False), ("writeRequiresMasterRead", False),
        ])
        b.add("CustomField", f"{api}.{fapi}", f"objects/{api}/fields/{fapi}.field-meta.xml", ftext)
    b.rel_fields[rel.key] = f"Junction object `{api}` with two master-detail fields"


# --- objects ----------------------------------------------------------------------------------


def _emit_objects(b: Build) -> None:
    for key in b.custom_objects:
        obj = b.design.get_object(key)
        assert obj is not None
        api = b.obj_api[key]
        name_label = b.name_label.get(key) or f"{obj.label} name"
        text = xml_doc("CustomObject", [
            ("deploymentStatus", "Deployed"), ("description", _clip(obj.description, DESCRIPTION_LIMIT)),
            ("enableActivities", True), ("enableHistory", False), ("enableReports", True), ("enableSearch", True),
            ("label", _fit_label(obj.label)),
            ("nameField", [("label", _fit_label(name_label)), ("type", "Text")]),
            ("pluralLabel", _fit_label(obj.plural_label)), ("sharingModel", "ReadWrite"), ("visibility", "Public"),
        ])
        b.add("CustomObject", api, f"objects/{api}/{api}.object-meta.xml", text)
        b.object_perms.add(api)


# --- pipelines --------------------------------------------------------------------------------


def _build_pipes(b: Build) -> None:
    design = b.design
    by_obj: dict[str, list[Pipeline]] = defaultdict(list)
    for pl in design.pipelines:
        by_obj[pl.object].append(pl)
    values: dict[tuple[str, str, str], str] = {}
    for obj_key, pls in by_obj.items():
        is_opp = obj_key == "deal"
        groups: dict[str, list[tuple[Pipeline, Stage]]] = defaultdict(list)
        for pl in pls:
            for s in pl.stages:
                groups[s.label.strip().lower()].append((pl, s))
        owner: dict[str, tuple[str, int, str, str]] = {}
        for pl in pls:
            for s in pl.stages:
                group = groups[s.label.strip().lower()]
                attrs = {(g.type, _prob(g.probability) if is_opp else 0) for _, g in group}
                value = " ".join(s.label.split())
                if len(attrs) > 1:
                    value = f"{value} ({pl.name})"
                mine = (s.type, _prob(s.probability) if is_opp else 0)
                held = owner.get(value.lower())
                if held is not None and held[:2] != mine:
                    value = f"{value} ({s.key})"
                owner.setdefault(value.lower(), (*mine, pl.key, s.key))
                values[(obj_key, pl.key, s.key)] = value
    for pl in design.pipelines:
        obj_api = b.obj_api[pl.object]
        is_opp = pl.object == "deal"
        stages: list[StageInfo] = []
        n = 0
        for s in pl.stages:
            if s.type == "lost":
                stages.append(StageInfo(s, values[(pl.object, pl.key, s.key)], None))
            else:
                n += 1
                stages.append(StageInfo(s, values[(pl.object, pl.key, s.key)], n))
        b.pipes.append(PipeInfo(pl, obj_api, is_opp, "StageName" if is_opp else "", stages))
    for obj_key, pls in by_obj.items():
        infos = [p for p in b.pipes if p.pipeline.object == obj_key]
        obj_api = b.obj_api[obj_key]
        if obj_key == "deal":
            seen: set[str] = set()
            for p in infos:
                for si in p.stages:
                    if si.value.lower() not in seen:
                        seen.add(si.value.lower())
                        b.opp_values.append((si.value, si.stage))
        else:
            api = b.names.take(obj_api, ["Stage", "Pipeline_stage"]) + "__c"
            b.stage_field[obj_key] = api
            b.field_api[(obj_key, "__stage")] = api
            for p in infos:
                p.stage_api = api
        override = _override(b.design, "objects", obj_key, "record_type")
        multi = len(infos) > 1
        for p in infos:
            if obj_key == "deal" or multi:
                if override and not multi:
                    cand = [_slug(override)]
                elif override:
                    cand = [f"{_slug(override)}_{_title(p.pipeline.key)}"]
                else:
                    cand = [_title(p.pipeline.key)]
                p.rt = b.names.take(("rt", obj_api), cand)
            if obj_key == "deal":
                p.bp = p.rt
                p.path = b.names.take("paths", [_title(p.pipeline.key) + "_path"])


def _stage_options(b: Build, obj_key: str) -> list[tuple[str, str]]:
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for p in b.pipes:
        if p.pipeline.object != obj_key:
            continue
        for si in p.stages:
            if si.value.lower() not in seen:
                seen.add(si.value.lower())
                out.append((si.stage.key, si.value))
    return out


def _blank(b: Build, obj_key: str, fkey: str) -> str:
    f = b.design.get_field(obj_key, fkey)
    api = b.field_api.get((obj_key, fkey)) or _title(fkey) + "__c"
    t = f.type if f else "text"
    if t == "select":
        return f"ISBLANK(TEXT({api}))"
    if t == "checkbox":
        return f"NOT({api})"
    if t == "multi_select":
        b.multi_blank = True
    return f"ISBLANK({api})"


def _join_labels(labels: list[str]) -> str:
    if len(labels) <= 1:
        return "".join(labels)
    return ", ".join(labels[:-1]) + " and " + labels[-1]


def _build_rules(b: Build) -> None:
    for p in b.pipes:
        pl = p.pipeline
        order = [si for si in p.stages if si.ordinal is not None]
        case = ", ".join(f"{_fstr(si.value)}, {si.ordinal}" for si in order)
        rt = f'RecordType.DeveloperName = {_fstr(p.rt)}' if p.rt else None
        for si in p.stages:
            s = si.stage
            if not s.required_fields:
                continue
            blanks = [_blank(b, pl.object, k) for k in s.required_fields]
            blank = blanks[0] if len(blanks) == 1 else "OR(" + ", ".join(blanks) + ")"
            labels = []
            for k in s.required_fields:
                f = b.design.get_field(pl.object, k)
                labels.append(f.label if f else k)
            if s.type == "lost":
                kind, prefix = "lost", "Lost"
                cond = f"ISPICKVAL({p.stage_api}, {_fstr(si.value)})"
                msg = f"Fill in {_join_labels(labels)} before closing this as {s.label}."
                desc = f"Lost reason: {pl.name}, {s.label} needs {_join_labels(labels)}."
            else:
                kind, prefix = "gate", "Gate"
                cond = f"CASE({p.stage_api}, {case}, 0) >= {si.ordinal}"
                msg = f"Fill in {_join_labels(labels)} before moving to {s.label}."
                desc = f"Stage gate: {pl.name}, {s.label} and later stages need {_join_labels(labels)}."
            formula = "AND(" + ", ".join([x for x in (rt, cond, blank) if x]) + ")"
            obj_api = p.obj_api
            name = b.names.take(("rule", obj_api), [_hash_name(f"{prefix}_{_slug(pl.key)}_{_slug(s.key)}")])
            display = None
            if len(s.required_fields) == 1:
                display = b.field_api.get((pl.object, s.required_fields[0]))
                if display and b.field_kind.get((pl.object, s.required_fields[0])) == "owner":
                    display = None
            b.rules.append(Rule(name, obj_api, pl.key, s.key, kind, formula, _clip(msg, MESSAGE_LIMIT),
                                display, _clip(desc, DESCRIPTION_LIMIT)))


def _emit_pipelines(b: Build) -> None:
    # Opportunity stages, sales processes, record types, paths
    if b.opp_values:
        std: list[tuple[str, Any]] = []
        for value, s in b.opp_values:
            if s.type == "won":
                flags = (True, True, "Closed", 100)
            elif s.type == "lost":
                flags = (True, False, "Omitted", 0)
            else:
                flags = (False, False, "Pipeline", _prob(s.probability))
            std.append(("standardValue", Ordered([
                ("fullName", value), ("default", False), ("label", value), ("closed", flags[0]),
                ("forecastCategory", flags[2]), ("probability", flags[3]), ("won", flags[1]),
            ])))
        b.add("StandardValueSet", "OpportunityStage", "standardValueSets/OpportunityStage.standardValueSet-meta.xml",
              xml_doc("StandardValueSet", Ordered([("sorted", False), *std])))
        b.object_perms.add("Opportunity")
    for key, api in sorted(b.stage_field.items()):
        obj_api = b.obj_api[key]
        opts = _stage_options(b, key)
        text = _picklist_xml(api, "Stage", "Where the record is in its pipeline. Restricted to the pipeline's stages.",
                             [(k, v) for k, v in opts])
        b.add("CustomField", f"{obj_api}.{api}", f"objects/{obj_api}/fields/{api}.field-meta.xml", text)
        b.field_perms.add(f"{obj_api}.{api}")
        b.object_perms.add(obj_api)
    for p in b.pipes:
        pl = p.pipeline
        if p.rt:
            _emit_record_type(b, p)
        if p.bp:
            vals: list[tuple[str, Any]] = []
            first_open = next((si for si in p.stages if si.stage.type == "open"), p.stages[0])
            for si in p.stages:
                vals.append(("values", [("fullName", si.value), ("default", si is first_open)]))
            b.add("BusinessProcess", f"Opportunity.{p.bp}",
                  f"objects/Opportunity/businessProcesses/{p.bp}.businessProcess-meta.xml",
                  xml_doc("BusinessProcess", [("fullName", p.bp), ("description", _clip(pl.name, 255)),
                                              ("isActive", True), *vals]))
        if p.path:
            steps: list[tuple[str, Any]] = []
            for si in p.stages:
                step: list[tuple[str, Any]] = []
                for k in si.stage.required_fields[:PATH_FIELD_LIMIT]:
                    api = b.field_api.get((pl.object, k))
                    if api:
                        step.append(("fieldNames", api))
                step.append(("info", si.stage.exit_criteria))
                step.append(("picklistValueName", si.value))
                steps.append(("pathAssistantSteps", Ordered(step)))
            b.add("PathAssistant", p.path, f"pathAssistants/{p.path}.pathAssistant-meta.xml",
                  xml_doc("PathAssistant", [
                      ("active", True), ("entityName", "Opportunity"), ("fieldName", "StageName"),
                      ("masterLabel", _clip(f"{pl.name} path", 80)), *steps, ("recordTypeName", p.rt)]))
    if any(p.path for p in b.pipes):
        b.add("Settings", "PathAssistant", "settings/PathAssistant.settings-meta.xml",
              xml_doc("PathAssistantSettings", [("pathAssistantEnabled", True)]))
    for r in b.rules:
        pairs: list[tuple[str, Any]] = [
            ("fullName", r.name), ("active", True), ("description", r.description),
            ("errorConditionFormula", r.formula), ("errorMessage", r.message),
        ]
        if r.display_field:
            pairs.append(("errorDisplayField", r.display_field))
        b.add("ValidationRule", f"{r.obj_api}.{r.name}",
              f"objects/{r.obj_api}/validationRules/{r.name}.validationRule-meta.xml", xml_doc("ValidationRule", pairs))
        b.object_perms.add(r.obj_api)


def _emit_record_type(b: Build, p: PipeInfo) -> None:
    pl = p.pipeline
    obj_api = p.obj_api
    plists: list[tuple[str, list[tuple[str, str]]]] = []
    for f in b.design.fields_of(pl.object):
        if f.type in ("select", "multi_select") and b.field_kind[(f.object, f.key)] == "custom":
            plists.append((b.field_api[(f.object, f.key)], [(o.key, o.label) for o in f.options]))
    if not p.is_opp:
        plists.append((b.stage_field[pl.object], [(si.stage.key, si.value) for si in p.stages]))
    pairs: list[tuple[str, Any]] = [
        ("fullName", p.rt), ("active", True), ("description", _clip(pl.name, 255)), ("label", _fit_label(pl.name)),
    ]
    if p.bp:
        pairs.append(("businessProcess", p.bp))
    for api, opts in sorted(plists, key=lambda x: x[0].lower()):
        vals = [("values", [("fullName", v), ("default", False)]) for v, _ in _values(opts)]
        pairs.append(("picklistValues", Ordered([("picklist", api), *vals])))
    b.add("RecordType", f"{obj_api}.{p.rt}", f"objects/{obj_api}/recordTypes/{p.rt}.recordType-meta.xml",
          xml_doc("RecordType", pairs))
    b.rt_vis.add(f"{obj_api}.{p.rt}")
    b.object_perms.add(obj_api)


# --- list views -------------------------------------------------------------------------------


@dataclass
class _VF:
    kind: str  # field stage owner
    token: str
    type: str
    options: list[tuple[str, list[str]]]  # (label, stored values)
    api: str = ""


@dataclass
class _Clause:
    terms: list[tuple[str, str, str]]
    join: str = "AND"
    mine: bool = False


def _view_fields(b: Build, obj_key: str) -> dict[str, _VF]:
    out: dict[str, _VF] = {}
    for f in b.design.fields_of(obj_key):
        kind = b.field_kind[(f.object, f.key)]
        if kind == "owner" or (kind == "native" and f.key == "owner"):
            out[f.label.lower()] = _VF("owner", "OwnerId", "user", [])
        elif kind == "custom":
            api = b.field_api[(f.object, f.key)]
            opts: list[tuple[str, list[str]]] = []
            if f.type in ("select", "multi_select"):
                stored = _values([(o.key, o.label) for o in f.options])
                opts = [(o.label, [v]) for o, (v, _lab) in zip(f.options, stored)]
            out[f.label.lower()] = _VF("field", api, f.type, opts, api)
    stage_opts: dict[str, list[str]] = {}
    for p in b.pipes:
        if p.pipeline.object == obj_key:
            for si in p.stages:
                stage_opts.setdefault(si.stage.label, [])
                if si.value not in stage_opts[si.stage.label]:
                    stage_opts[si.stage.label].append(si.value)
    if stage_opts and "stage" not in out:
        token = "OPPORTUNITY.STAGE_NAME" if obj_key == "deal" else b.stage_field.get(obj_key, "")
        out["stage"] = _VF("stage", token, "select", list(stage_opts.items()), token)
    return out


def _cover(phrase: str, options: list[tuple[str, list[str]]]) -> list[str] | None:
    """Split 'a or b, c' into option values when every piece is a known label."""
    phrase = phrase.strip()
    if not phrase:
        return []
    for label, vals in sorted(options, key=lambda o: -len(o[0])):
        if not phrase.lower().startswith(label.lower()):
            continue
        rest = phrase[len(label):]
        if not rest:
            return list(vals)
        m = re.match(r"^(?:\s+or\s+|,\s*)(.*)$", rest, re.I)
        if m:
            tail = _cover(m.group(1), options)
            if tail is not None:
                return list(vals) + tail
    return None


def _open_values(b: Build, obj_key: str) -> list[str]:
    out: list[str] = []
    for p in b.pipes:
        if p.pipeline.object == obj_key:
            for si in p.stages:
                if si.stage.type == "open" and si.value not in out:
                    out.append(si.value)
    return out


def _parse_clause(b: Build, obj_key: str, text: str, vfs: dict[str, _VF]) -> _Clause | None:
    text = text.strip()
    for label in sorted(vfs, key=len, reverse=True):
        if not text.lower().startswith(label + " is "):
            continue
        vf = vfs[label]
        rest = text[len(label) + 4:].strip()
        low = rest.lower()
        if vf.kind == "owner":
            return _Clause([], mine=True) if low == "me" else None
        if low == "empty":
            return _Clause([(vf.token, "equals", "")])
        if vf.type in ("date", "datetime"):
            m = re.fullmatch(r"within (\d+) (days|months)", low)
            if low == "in the past":
                return _Clause([(vf.token, "lessThan", "TODAY")])
            if low == "in the future":
                return _Clause([(vf.token, "greaterThan", "TODAY")])
            if low == "empty or in the past":
                return _Clause([(vf.token, "equals", ""), (vf.token, "lessThan", "TODAY")], join="OR")
            if m:
                unit = "DAYS" if m.group(2) == "days" else "MONTHS"
                return _Clause([(vf.token, "greaterOrEqual", "TODAY"),
                                (vf.token, "lessOrEqual", f"NEXT_N_{unit}:{m.group(1)}")])
            return None
        if vf.type in ("select", "multi_select"):
            negate = low.startswith("not ")
            phrase = rest[4:] if negate else rest
            vals = _cover(phrase, vf.options)
            if vals is None and vf.kind == "stage" and phrase.lower() == "open" and not negate:
                vals = _open_values(b, obj_key)
            if not vals or any("," in v for v in vals):
                return None
            if vf.type == "multi_select":
                op = "excludes" if negate else "includes"
            else:
                op = "notEqual" if negate else "equals"
            return _Clause([(vf.token, op, ",".join(vals))])
        return None
    return None


def _parse_and(b: Build, obj_key: str, text: str, vfs: dict[str, _VF]) -> list[_Clause] | None:
    one = _parse_clause(b, obj_key, text, vfs)
    if one is not None:
        return [one]
    for m in re.finditer(r" and ", text):
        left = _parse_clause(b, obj_key, text[:m.start()], vfs)
        if left is None:
            continue
        rest = _parse_and(b, obj_key, text[m.end():], vfs)
        if rest is not None:
            return [left] + rest
    return None


_NAME_COLUMN = {"Account": "ACCOUNT.NAME", "Contact": "FULL_NAME", "Opportunity": "OPPORTUNITY.NAME"}


def _build_views(b: Build) -> None:
    for v in b.design.views:
        obj = b.design.get_object(v.object)
        if obj is None:
            continue
        vfs = _view_fields(b, v.object)
        clauses = _parse_and(b, v.object, v.filter.strip().rstrip("."), vfs)
        if clauses is None:
            b.unparsed_views.append(v)
            continue
        obj_api = b.obj_api[v.object]
        scope = "Mine" if any(c.mine for c in clauses) else "Everything"
        filters: list[tuple[str, str, str]] = []
        parts: list[str] = []
        has_or = False
        for c in clauses:
            if c.mine:
                continue
            start = len(filters) + 1
            filters += c.terms
            idx = [str(i) for i in range(start, len(filters) + 1)]
            if c.join == "OR":
                has_or = True
                parts.append("(" + " OR ".join(idx) + ")")
            else:
                parts.extend(idx)
        columns = [_NAME_COLUMN.get(obj_api, "NAME")]
        if obj_api == "Opportunity":
            columns += ["ACCOUNT.NAME", "OPPORTUNITY.AMOUNT", "OPPORTUNITY.CLOSE_DATE"]
        stage_vf = vfs.get("stage")
        if stage_vf and stage_vf.token:
            columns.append(stage_vf.token)
        sort_head = v.sort.split(",")[0].strip().lower()
        for label, vf in sorted(vfs.items(), key=lambda x: -len(x[0])):
            if vf.kind == "field" and sort_head.startswith(label):
                columns.append(vf.token)
                break
        for tok, _, _ in filters:
            columns.append(tok)
        cols: list[str] = []
        for c in columns:
            if c not in cols and c != "OwnerId":
                cols.append(c)
        name = b.names.take(("view", obj_api), [_title(v.key)])
        pairs: list[tuple[str, Any]] = [("fullName", name)]
        if has_or:
            pairs.append(("booleanFilter", " AND ".join(parts)))
        pairs += [("columns", c) for c in cols]
        pairs.append(("filterScope", scope))
        pairs += [("filters", Ordered([("field", f), ("operation", o), ("value", val)])) for f, o, val in filters]
        pairs.append(("label", _fit_label(v.name)))
        pairs.append(("sharedTo", [("allInternalUsers", "")]))
        text = xml_doc("ListView", Ordered(pairs))  # columns and filters keep their order
        b.add("ListView", f"{obj_api}.{name}", f"objects/{obj_api}/listViews/{name}.listView-meta.xml", text)
        b.views.append(ViewFile(v, obj_api, name, text))


# --- permission set, manifest, project --------------------------------------------------------


def _permset_name(design: Design) -> str:
    return _hash_name(_slug(design.name) + "_user", 70)


def _emit_permission_set(b: Build) -> None:
    design = b.design
    name = _permset_name(design)
    pairs: list[tuple[str, Any]] = [
        ("description", _clip(f"Read and edit access to the custom fields of the {design.name} blueprint.", 255)),
        ("hasActivationRequired", False),
        ("label", _clip(f"{design.name} user", 80)),
    ]
    for f in sorted(b.field_perms):
        pairs.append(("fieldPermissions", Ordered([("editable", True), ("field", f), ("readable", True)])))
    for o in sorted(b.object_perms):
        pairs.append(("objectPermissions", Ordered([
            ("allowCreate", True), ("allowDelete", False), ("allowEdit", True), ("allowRead", True),
            ("modifyAllRecords", False), ("object", o), ("viewAllRecords", False)])))
    for rt in sorted(b.rt_vis):
        pairs.append(("recordTypeVisibilities", Ordered([("recordType", rt), ("visible", True)])))
    b.add("PermissionSet", name, f"permissionsets/{name}.permissionset-meta.xml", xml_doc("PermissionSet", pairs))


def package_xml(components: set[tuple[str, str]]) -> str:
    """The manifest: types sorted by name, members sorted, version pinned."""
    by_type: dict[str, list[str]] = defaultdict(list)
    for ctype, member in components:
        by_type[ctype].append(member)
    pairs: list[tuple[str, Any]] = []
    for ctype in sorted(by_type):
        members = [("members", m) for m in sorted(by_type[ctype])]
        pairs.append(("types", Ordered([*members, ("name", ctype)])))
    pairs.append(("version", API_VERSION))
    return xml_doc("Package", Ordered(pairs))


def sfdx_project(design: Design) -> str:
    """sfdx-project.json: one package directory, source API version pinned."""
    data = {
        "name": _slug(design.name).lower().replace("_", "-"),
        "namespace": "",
        "packageDirectories": [{"default": True, "path": "force-app"}],
        "sfdcLoginUrl": "https://login.salesforce.com",
        "sourceApiVersion": API_VERSION,
    }
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def build_model(design: Design) -> Build:
    """Work out every name and every file for a design."""
    b = Build(design)
    _object_api(design, b)
    _field_api(design, b)
    _build_pipes(b)
    _build_rules(b)
    _emit_objects(b)
    _emit_fields(b)
    _emit_relationships(b)
    _emit_pipelines(b)
    _build_views(b)
    _emit_permission_set(b)
    return b


# --- build sheet ------------------------------------------------------------------------------

SF_TYPE = {
    "text": "Text (255)", "long_text": "Text Area (Long)", "select": "Picklist", "multi_select": "Picklist (Multi-Select)",
    "number": "Number (18, 0)", "currency": "Currency (18, 2)", "percent": "Percent (5, 2)", "date": "Date",
    "datetime": "Date/Time", "checkbox": "Checkbox", "url": "URL", "email": "Email", "phone": "Phone",
    "user": "Lookup Relationship to User",
}


def _objects_label(b: Build, key: str) -> str:
    o = b.design.get_object(key)
    if o is not None and o.kind == "core":
        return b.obj_api[key]  # Setup shows Opportunity, not our word Deal
    return o.label if o else key


class SalesforceHooks(BuildSheetHooks):
    """Setup UI paths and stage-rule wording for the build sheet."""

    platform_label = "Salesforce"

    def __init__(self, b: Build) -> None:
        self.b = b

    def object_path(self, obj: ObjectDef) -> str:
        api = self.b.obj_api[obj.key]
        return (f"Setup, then Object Manager, then Create, then Custom Object. Label {obj.label}, plural "
                f"{obj.plural_label}, API name `{api}`, record name a Text field.")

    def relationship_path(self, rel: RelationshipDef) -> str:
        how = self.b.rel_fields.get(rel.key, "")
        if rel.cardinality == "many_to_many":
            return (f"Setup, then Object Manager, then Create, then Custom Object for the junction, then add two "
                    f"Master-Detail fields (one to {rel.from_object}, one to {rel.to_object}). {how}.")
        return (f"Setup, then Object Manager, then the child object, then Fields & Relationships, then New, "
                f"then Lookup Relationship. {how}.")

    def pipeline_path(self, pipeline: Pipeline) -> str:
        p = self.b.pipe(pipeline)
        if p.is_opp:
            return (f"Add the stage values: Setup, Object Manager, Opportunity, Fields & Relationships, Stage. "
                    f"Sales process `{p.bp}`: Setup, Feature Settings, Sales, Sales Processes, New. "
                    f"Record type `{p.rt}`: Object Manager, Opportunity, Record Types, New, with that sales process. "
                    f"Path: Setup, User Interface, Path Settings, New.")
        extra = f" Record type `{p.rt}` limits the stages." if p.rt else ""
        return (f"Create the restricted picklist field `{p.stage_api}` on {_objects_label(self.b, pipeline.object)}: "
                f"Setup, Object Manager, the object, Fields & Relationships, New.{extra}")

    def stage_rule(self, pipeline: Pipeline, stage: Stage) -> str:
        p = self.b.pipe(pipeline)
        si = next(s for s in p.stages if s.stage is stage)
        parts: list[str] = []
        if p.is_opp:
            closed = stage.type != "open"
            parts.append(
                f"Stage value `{si.value}`: closed {str(closed).lower()}, won {str(stage.type == 'won').lower()}, "
                f"probability {100 if stage.type == 'won' else 0 if stage.type == 'lost' else _prob(stage.probability)}, "
                f"forecast category {'Closed' if stage.type == 'won' else 'Omitted' if stage.type == 'lost' else 'Pipeline'}.")
        for r in self.b.rules_for(pipeline, stage):
            parts.append(f"Validation rule `{r.name}` (Setup, Object Manager, {_objects_label(self.b, pipeline.object)}, "
                         f"Validation Rules, New). Formula: `{r.formula}`. Error message: {r.message}")
        return " ".join(parts)

    def field_path(self, field: FieldDef) -> str:
        kind = self.b.field_kind.get((field.object, field.key), "custom")
        if kind == "name":
            return "The standard Name field of the object, set when the object is created."
        if kind == "owner":
            return "The standard Owner field of the object. Nothing to create."
        api = self.b.field_api[(field.object, field.key)]
        label = _objects_label(self.b, field.object)
        return (f"Setup, Object Manager, {label}, Fields & Relationships, New. Data type {SF_TYPE.get(field.type, field.type)}, "
                f"API name `{api}`{', required' if field.required and field.type not in ('checkbox', 'user') else ''}.")

    def automation_path(self, automation: Any) -> str:
        return "Setup, Process Automation, Flows, New Flow, Record-Triggered Flow."

    def view_path(self, view: View) -> str:
        obj = self.b.design.get_object(view.object)
        label = obj.plural_label if obj else view.object
        gen = next((v for v in self.b.views if v.view is view), None)
        if gen:
            return (f"Generated as list view `{gen.name}`. Open {label}, choose the view, then set the sort "
                    f"({view.sort}) from the list controls and save.")
        return f"Open {label}, then List View Controls, then New. Set the filter and sort by hand and save."

    def manual_steps(self) -> list[str]:
        return [s["title"] for s in manual_steps(self.b) if s["group"] == "setup"]


# --- manual steps -----------------------------------------------------------------------------

GROUP_TITLES: dict[str, str] = {
    "setup": "Before and during the build",
    "verify": "Check on the first deploy (unverified in the research)",
    "pipeline": "Pipelines and stages",
    "gate": "Stage gates",
    "field": "Fields, relationships and objects",
    "automation": "Flows",
    "view": "List views",
    "permissions": "Permissions and access",
}


def manual_steps(b: Build) -> list[dict[str, str]]:
    """Every step the metadata cannot do, plus the checks the research leaves open."""
    d = b.design
    steps: list[dict[str, str]] = []

    def add(group: str, title: str, where: str, why: str, done: str) -> None:
        steps.append({"group": group, "title": title, "where": where, "why": why, "done_when": done})

    per_obj: dict[str, int] = defaultdict(int)
    for f in d.fields:
        if b.field_kind[(f.object, f.key)] == "custom":
            per_obj[b.obj_api[f.object]] += 1
    n_objs = len(b.custom_objects) + len(b.junctions)
    most = max(per_obj.values(), default=0)
    add("setup", "Check the Salesforce edition", "Setup, Company Information, Organization Edition",
        "The Metadata API deploys only on Enterprise, Unlimited, Performance and Developer Edition. Professional "
        "and Essentials cannot deploy this folder: build by hand from build-sheet.md instead (Professional allows "
        f"about 50 custom objects and 100 custom fields per object; Essentials allows no custom objects). This blueprint "
        f"needs {n_objs} custom objects (including {len(b.junctions)} junction) and up to {most} custom fields on one "
        "object. Allowances are secondary-source figures, so confirm them on the Company Information page.",
        "the edition is one of the four, or the by-hand fallback is agreed with the client.")
    add("setup", "Run a check-only deploy, then deploy", "Terminal, in this folder",
        "Run `sf project deploy start --dry-run --manifest package.xml --target-org <alias> --api-version 67.0 --wait 30`. "
        "Read every error. Then run the same command without `--dry-run`. Use a sandbox first. Never pass "
        "`--ignore-errors`, `--ignore-conflicts` or `--ignore-warnings`.",
        "the dry run passes and the real deploy lists every file as Created or Unchanged.")
    add("setup", "Confirm the deploying user's permissions", "Setup, Users, Profiles or Permission Sets",
        "The user needs API Enabled plus Modify Metadata Through Metadata API Functions or Modify All Data.",
        "a check-only deploy starts without a permissions error.")
    # verify
    add("verify", "Deploy one field of each type first", "Terminal",
        "Minimal files for Checkbox, Lookup, MasterDetail and LongTextArea, and the precision and scale limits, are "
        "taken from real files but not proven for API 67.0 (research E1). A required Lookup is never emitted.",
        "the dry run accepts every field type this blueprint uses.")
    if b.rt_vis:
        add("verify", "Check record type picklist values", "Setup, Object Manager, the object, Record Types",
            "Each record type lists every value of every picklist. Whether omitting a picklist hides its values is "
            "unconfirmed (research E4).", "each record type shows the full list of values for each picklist.")
    if b.comma_options and b.rt_vis:
        rows = "; ".join(f"{f}: {v}" for f, v in sorted(set(b.comma_options)))
        add("verify", "Check picklist values that contain a comma", "Setup, Object Manager, the object, Record Types",
            f"Salesforce may URL-encode a comma inside a record type's picklist value. Values affected: {rows}. "
            "Retrieve a record type once and copy the encoding it uses if the deploy rejects these.",
            "the values deploy and appear on the record type.")
    if b.opp_values:
        add("verify", "Check the sales process minimum", "Setup, Feature Settings, Sales, Sales Processes",
            "Each sales process has one open, one won and one lost stage, but the minimum is not stated in the guide "
            "(research E9).", "every sales process saves and shows its stages.")
    if any(p.path for p in b.pipes):
        add("verify", "Check the paths", "Setup, User Interface, Path Settings",
            "A path names its record type. Path preference is on by default only in Enterprise Edition. The "
            "`recordTypeName` form is unverified for objects with no record type (research E11).",
            "each path shows its stages with the guidance text, for a user of that record type.")
    if b.junctions:
        add("verify", "Check the junction objects' sharing", "Setup, Object Manager, each junction object",
            "A junction object is the detail of two master-detail fields, so its sharing is set to Controlled By "
            "Parent. The guide lists the value but not the rule (research E7).",
            "the junction deploys and its records show on both parent records.")
    if b.multi_blank:
        add("verify", "Check the blank test on multi-select picklists", "Setup, Object Manager, Validation Rules",
            "A stage gate tests a multi-select field with `ISBLANK(Field__c)`. That form is from memory of the formula "
            "reference (research, ValidationRule).", "the check-only deploy compiles the rule and a test save is blocked.")
    if b.views:
        add("verify", "Check the list views", "Setup, Object Manager, the object, List Views, or the list controls",
            "The share target (`allInternalUsers`), the stage filter token `OPPORTUNITY.STAGE_NAME`, blank tests "
            "(`equals` with an empty value) and date literals (`TODAY`, `NEXT_N_DAYS:n`) are unverified (research E12). "
            "Retrieve a hand-made view to compare.", "each generated view is visible to internal users and filters as designed.")
    add("verify", "Check the permission set", "Setup, Users, Permission Sets",
        "The set grants object access with the field access because a field permission may need object read in the same "
        "file (research E16). Required fields and master-detail fields are left out; they follow the object.",
        "a test user with the set sees and edits every custom field that is not required.")
    if b.flagged:
        add("verify", "Check the data classification elements", "Setup, Object Manager, the field, Edit",
            "Fields flagged as data protection carry `complianceGroup` PII;GDPR and a `securityClassification`. These are "
            "labels, not encryption. Shield Platform Encryption is a separate paid feature. Confirm API 67.0 accepts them.",
            "the flagged fields deploy and show the compliance categorisation.")
    # pipelines
    if b.opp_values:
        add("pipeline", "Deactivate the unused default stages", "Setup, Object Manager, Opportunity, Fields & Relationships, Stage",
            "A deploy only adds stage values. Salesforce's default stages stay in the master list (research E10). The sales "
            "processes hide them from users, so this is optional tidying. A stage whose label matches a default (for "
            "example Closed won and Closed Won) may update that value instead of adding one.",
            "only the stages in this design are active, or the client has agreed to leave the defaults.")
    for p in b.pipes:
        if p.is_opp:
            continue
        label = _objects_label(b, p.pipeline.object)
        probs = ", ".join(f"{si.value} {_prob(si.stage.probability)}%" for si in p.stages)
        add("pipeline", f"Finish the {p.pipeline.name} pipeline on {label}", f"Setup, Object Manager, {label}",
            f"{label} has no native stage machinery. The generator wrote the restricted picklist `{p.stage_api}` and the "
            f"stage gates. It cannot express won and lost as flags, probability ({probs}) or forecast categories. Report on "
            "the stage values instead, or add a Percent field and a flow to set it. No path is generated for this object: "
            "create one under Setup, User Interface, Path Settings"
            + (", using the record type." if p.rt else ", after adding a record type."),
            "reports group by stage and the client has said how won, lost and probability are read.")
    if b.opp_values:
        add("pipeline", "Check that every Opportunity user has a record type", "Setup, Users, Permission Sets",
            "A record type binds a user to a sales process. The permission set makes each record type visible; users "
            "without it fall back to their profile's default record type.",
            "a test user creates a deal in each pipeline and sees only that pipeline's stages.")
    # gates
    add("gate", "Decide how imports pass the stage gates", "Setup, Custom Code, Custom Permissions",
        "Validation rules also fire on API and bulk writes. A data import of records past a gated stage fails unless the "
        "gate has an escape hatch (for example a bypass checkbox or custom permission). Not designed here.",
        "the import plan names how gated records are loaded.")
    if b.skipped_required:
        names = ", ".join(f"{f.object}.{f.key}" for f in b.skipped_required)
        add("gate", "Make these fields required another way", "Setup, Object Manager, the object, Page Layouts",
            f"Salesforce does not allow a field-level required setting on a checkbox or user lookup: {names}. Mark them "
            "required on the page layout instead.", "the layout marks each field required.")
    # fields and objects
    for key in b.custom_objects:
        o = d.get_object(key)
        assert o is not None
        add("field", f"Add {o.label} to a tab and an app", "Setup, User Interface, Tabs; Setup, Apps, App Manager",
            "A custom object is not in the navigation until it has a tab in an app. The minimal tab file is unproven, so "
            "it is not generated (research E6).", f"users find {o.plural_label} from the app's navigation.")
    for key in sorted({f.object for f in d.fields if b.field_kind[(f.object, f.key)] == "custom"} | set(b.stage_field)):
        label = _objects_label(b, key)
        add("field", f"Put the new fields on the {label} page layout", f"Setup, Object Manager, {label}, Page Layouts",
            "A deploy creates fields but does not place them on a layout, and a deployed layout would replace the whole "
            "one (research E5). The permission set grants access; the layout decides what users see.",
            f"the {label} layout shows every field from this blueprint in a sensible section.")
    for key in (r.key for r in d.relationships if PLATFORM not in r.native and r.cardinality == "one_to_one"):
        rel = next(r for r in d.relationships if r.key == key)
        add("field", f"Enforce one-to-one for {rel.key}", "Setup, Object Manager, the child object, Fields & Relationships",
            "Salesforce has no unique lookup, so the lookup built for this link allows several records. Add a duplicate "
            "rule or a validation rule if the business needs exactly one.", "a second link to the same record is refused.")
    if b.junctions:
        add("field", "Decide master-detail or lookup for the many-to-many links", "Setup, Object Manager, each junction object",
            "Many-to-many links are junction objects with two master-detail fields. Changing a master-detail field later "
            "deletes child records, so settle this before any data is loaded.", "the client has agreed the junction design.")
    if b.flagged_native:
        names = ", ".join(f"{f.object}.{f.key}" for f in b.flagged_native)
        add("field", "Classify the standard fields flagged as data protection", "Setup, Object Manager, the field, Edit",
            f"Standard fields have no file in this folder, so they carry no compliance label: {names}.",
            "each standard field has a data classification set.")
    add("field", "Map lead fields if the client uses Leads", "Setup, Object Manager, Lead, Fields & Relationships, Map Lead Fields",
        "Only custom fields can be mapped, and the metadata path for the mapping file is unverified (research E14). Map any "
        "custom Lead field to its Account, Contact or Opportunity field from this blueprint. Standard mappings are fixed.",
        "a test lead converts and the custom values carry over, or the client does not use Leads.")
    # automations
    for a in d.automations:
        add("automation", a.name, "Setup, Process Automation, Flows, New Flow, Record-Triggered Flow",
            f"Flows are not generated: a wrong flow runs on every save and cannot be removed from source. Trigger: {a.trigger} "
            f"Action: {a.action} In production, a flow deploys inactive unless Setup, Process Automation, Process "
            "Automation Settings has 'Deploy processes and flows as active' on.",
            "the flow runs once on a test record and does nothing else.")
    # views
    for v in d.views:
        obj = d.get_object(v.object)
        label = obj.plural_label if obj else v.object
        gen = next((x for x in b.views if x.view is v), None)
        if gen:
            add("view", f"Set the sort on {v.name}", f"{label}, the list view `{gen.name}`, List View Controls",
                f"List views have no sort in the metadata. Sort: {v.sort}", "the saved view sorts as stated.")
        else:
            add("view", f"Build the view {v.name}", f"{label}, List View Controls, New",
                f"The filter is not a plain comparison on a custom field, the stage or the owner, so it is not generated. "
                f"Filter: {v.filter} Sort: {v.sort}", "the saved view shows the expected records in the stated order.")
    # permissions
    add("permissions", f"Assign the permission set {_permset_name(d)}", "Setup, Users, Permission Sets, Manage Assignments",
        "Assigning a permission set is a data operation, not metadata. A new field is invisible until a profile or "
        "permission set grants it. Never ship profiles from here: a profile deploy overwrites far more.",
        "a non-admin test user sees and edits the blueprint's fields.")
    add("permissions", "Set sharing for the standard objects", "Setup, Security, Sharing Settings",
        "Sharing for custom objects is set in the object files (public read and write). Standard objects need the org-wide "
        "defaults chosen by the client.", "the client has signed off the org-wide defaults.")
    return steps


def render_manual_steps(b: Build) -> str:
    """The manual-steps.md text."""
    steps = manual_steps(b)
    L = [
        f"# Manual steps: {b.design.name} (salesforce)",
        "",
        "Generated from `design.yaml`. Do not edit by hand. The metadata deploy cannot do any of this, or the research has not "
        "proven it. Setup paths come from general platform knowledge and labels move between releases.",
        "Sources: `platforms/salesforce/reference/` (api-coverage.md, open-questions.md, automation.md).",
        "",
    ]
    n = 0
    for group, title in GROUP_TITLES.items():
        items = [s for s in steps if s["group"] == group]
        if not items:
            continue
        L.append(f"## {title}")
        L.append("")
        for s in items:
            n += 1
            L.append(f"### {n}. {s['title']}")
            L.append("")
            L.append(f"- [ ] Where: {s['where']}")
            L.append(f"- Why it is manual: {s['why']}")
            L.append(f"- Done when: {s['done_when']}")
            L.append("")
    return "\n".join(L)


# --- entry point ------------------------------------------------------------------------------


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    return path


def generate(design: Design, out_dir: Path) -> list[Path]:
    """Write the Salesforce files for a design into `out_dir` and return the paths written."""
    out_dir = Path(out_dir)
    b = build_model(design)
    written: list[Path] = []
    for rel in sorted(b.files):
        written.append(_write(out_dir / BASE / rel, b.files[rel]))
    written.append(_write(out_dir / "sfdx-project.json", sfdx_project(design)))
    written.append(_write(out_dir / "package.xml", package_xml(b.components)))
    written.append(_write(out_dir / "build-sheet.md", render_build_sheet(design, PLATFORM, SalesforceHooks(b))))
    written.append(_write(out_dir / "manual-steps.md", render_manual_steps(b)))
    return written
