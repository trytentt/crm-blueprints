"""Generate HubSpot request payloads, a build sheet, manual steps and plan requirements from a design.

Files written to `<out_dir>` (normally `blueprints/<name>/hubspot/`):

- `schemas.json`, `property-groups.json`, `properties.json`, `associations.json`, `pipelines.json`:
  ordered API requests. Each file is
  `{"api_version", "order", "source", "placeholders", "requests": [...]}` and each request is
  `{"method", "path", "body"}` (plus an optional `note`). Run the files in `order`: schemas (1),
  property groups (2), properties (3), associations (4), pipelines (5). This follows the order of
  operations in `platforms/hubspot/reference/api-coverage.md`, with one change: a custom object's
  property group can only be created once the schema exists, so groups come after schemas.
- `build-sheet.md`: the human checklist, through `build_sheet.render_build_sheet`.
- `manual-steps.md`: everything the HubSpot API cannot do, each with a UI path and a reason.
- `plan-requirements.md`: the HubSpot features the blueprint uses, the minimum tier for each, and the
  source page, all taken from the research notes.

The API version is held once, in `API_VERSION`. A custom object has no `objectTypeId` until HubSpot
creates it, so its requests carry a placeholder such as `{objectTypeId.subscription}`. The `placeholders`
key of each file says how to resolve every placeholder that file uses. An object whose design override
sets `object_type_id` is taken to exist already: no schema is sent and the ID is used in the paths.

Payload shapes come from `platforms/hubspot/reference/`. Output is deterministic: fixed key order,
no timestamps.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from tools.design import Design, FieldDef, ObjectDef, Pipeline, RelationshipDef, Stage
from tools.generators.build_sheet import BuildSheetHooks, render_build_sheet

PLATFORM = "hubspot"
API_VERSION = "2026-09"

_REF = "https://developers.hubspot.com/docs/api-reference/latest/crm"
SRC_PROPERTIES = f"{_REF}/properties/guide.md"
SRC_PROPERTY_GROUPS = f"{_REF}/properties/property-groups/create-property.md"
SRC_SCHEMAS = f"{_REF}/objects/schemas/guide.md"
SRC_CREATE_SCHEMA = f"{_REF}/objects/schemas/create-schema.md"
SRC_PIPELINES = f"{_REF}/pipelines/guide.md"
SRC_PIPELINE_RULES = f"{_REF}/pipelines/rules/guide.md"
SRC_ASSOCIATIONS = f"{_REF}/associations/associations-schema/guide.md"
SRC_ASSOC_LABEL_KB = "https://knowledge.hubspot.com/object-settings/create-and-use-association-labels"
SRC_ASSOC_LIMIT_KB = "https://knowledge.hubspot.com/object-settings/set-limits-for-record-associations"
SRC_CUSTOM_OBJECT_KB = "https://knowledge.hubspot.com/object-settings/create-custom-objects"
SRC_PIPELINE_KB = "https://knowledge.hubspot.com/object-settings/set-up-and-customize-pipelines"
SRC_VIEWS_KB = "https://knowledge.hubspot.com/records/create-and-manage-saved-views"
SRC_WORKFLOWS_KB = "https://knowledge.hubspot.com/workflows/create-workflows"
SRC_CATALOG = "https://legal.hubspot.com/hubspot-product-and-services-catalog"
SRC_LIMITS = f"{_REF}/limits-tracking/guide.md"

# canonical type -> (type, fieldType, extra property keys)
TYPE_MAP: dict[str, tuple[str, str, dict[str, Any]]] = {
    "text": ("string", "text", {}),
    "long_text": ("string", "textarea", {}),
    "select": ("enumeration", "select", {}),
    "multi_select": ("enumeration", "checkbox", {}),
    "number": ("number", "number", {"numberDisplayHint": "formatted"}),
    "currency": ("number", "number", {"showCurrencySymbol": True}),
    "percent": ("number", "number", {"numberDisplayHint": "percentage"}),
    "date": ("date", "date", {}),
    "datetime": ("datetime", "date", {}),
    "checkbox": ("bool", "booleancheckbox", {}),
    "url": ("string", "text", {}),
    "email": ("string", "text", {"textDisplayHint": "email"}),
    "phone": ("string", "phonenumber", {}),
    "user": ("enumeration", "select", {"externalOptions": True, "referencedObjectType": "OWNER"}),
}

# Types where HubSpot keeps less than the canonical meaning (platforms/hubspot/reference/fields.md).
LOSSY_TYPES: dict[str, str] = {
    "currency": "carries no currency code: the symbol is a display choice",
    "percent": "the stored value (0.2 or 20) is unconfirmed (open question OQ-5)",
    "url": "is plain text: HubSpot has no URL type or URL validation",
    "email": "is plain text with a display hint: HubSpot does not validate it",
    "phone": "has display formatting only, with no validation",
    "user": "holds the HubSpot owner ID, so only users of the account can be chosen",
}

LOSSY_NOTES: dict[str, str] = {"url": "Full web address. HubSpot has no URL type, so it is stored as text."}

# Standard objects: HubSpot path name -> objectTypeId (platforms/hubspot/reference/objects.md).
STANDARD_TYPE_IDS: dict[str, str] = {"contacts": "0-1", "companies": "0-2", "deals": "0-3"}

# Property groups HubSpot ships. A design override naming one of these is not created.
BUILTIN_GROUPS: frozenset[str] = frozenset(
    {"contactinformation", "companyinformation", "dealinformation", "ticketinformation"}
)

ORDER: dict[str, int] = {
    "schemas.json": 1,
    "property-groups.json": 2,
    "properties.json": 3,
    "associations.json": 4,
    "pipelines.json": 5,
}


# --- naming and overrides --------------------------------------------------------------------


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _overrides(design: Design) -> dict[str, Any]:
    value = design.platform_overrides.get(PLATFORM, {})
    return value if isinstance(value, dict) else {}


def _override(design: Design, section: str, target: str, key: str) -> str | None:
    entry = _overrides(design).get(section, {})
    entry = entry.get(target, {}) if isinstance(entry, dict) else {}
    value = entry.get(key) if isinstance(entry, dict) else None
    return value if isinstance(value, str) and value else None


def design_group(design: Design) -> str:
    """The property group name for the design's own properties."""
    return _slugify(design.name) or "blueprint"


def group_for(design: Design, f: FieldDef) -> str:
    """Property group of a field: field override, else object override, else the design's group."""
    return (
        _override(design, "fields", f"{f.object}.{f.key}", "property_group")
        or _override(design, "objects", f.object, "property_group")
        or design_group(design)
    )


def is_existing(design: Design, obj: ObjectDef) -> bool:
    """True for a standard object, or a custom one whose `object_type_id` override says it exists."""
    return obj.kind == "core" or _override(design, "objects", obj.key, "object_type_id") is not None


def type_id_placeholder(key: str) -> str:
    """The placeholder for a custom object's objectTypeId, known only after the schema is created."""
    return "{objectTypeId." + key + "}"


def object_ref(design: Design, obj: ObjectDef) -> str:
    """What goes in a path for this object: path name, override ID, or a placeholder."""
    if obj.kind == "core":
        return obj.native_names.get(PLATFORM, obj.plural_label.lower())
    return _override(design, "objects", obj.key, "object_type_id") or type_id_placeholder(obj.key)


def object_ref_for(design: Design, key: str) -> str:
    obj = design.get_object(key)
    return object_ref(design, obj) if obj else key


def object_type_id(design: Design, obj: ObjectDef) -> str:
    """The objectTypeId used in `associatedObjects`: the fixed ID, or a placeholder."""
    if obj.kind == "core":
        return STANDARD_TYPE_IDS.get(object_ref(design, obj), object_ref(design, obj))
    return object_ref(design, obj)


def object_ui_name(design: Design, obj: ObjectDef) -> str:
    """The name HubSpot shows in Settings for this object."""
    return obj.plural_label if obj.kind == "custom" else {
        "companies": "Companies",
        "contacts": "Contacts",
        "deals": "Deals",
    }.get(object_ref(design, obj), obj.plural_label)


# --- properties ------------------------------------------------------------------------------


def _description(f: FieldDef) -> str:
    note = LOSSY_NOTES.get(f.type)
    return f"{f.description} {note}" if note else f.description


def _options(f: FieldDef) -> list[dict[str, Any]]:
    return [
        {"label": o.label, "value": o.key, "displayOrder": i, "hidden": False}
        for i, o in enumerate(f.options)
    ]


def property_body(design: Design, f: FieldDef, *, group: str | None, in_schema: bool = False) -> dict[str, Any]:
    """One property definition. `group` is None for a property sent inside a schema."""
    hs_type, field_type, extra = TYPE_MAP[f.type]
    body: dict[str, Any] = {}
    if group is not None:
        body["groupName"] = group
    body["name"] = f.key
    body["label"] = f.label
    body["type"] = hs_type
    body["fieldType"] = field_type
    body["description"] = _description(f)
    for key, value in extra.items():
        if in_schema and key == "referencedObjectType":
            key = "externalOptionsReferenceType"
        body[key] = value
    if f.type in ("select", "multi_select"):
        body["options"] = _options(f)
    return body


def primary_field(design: Design, obj: ObjectDef) -> FieldDef | None:
    """The design field that names each record of a custom object, or None to add a `name` property."""
    fields = [f for f in design.fields_of(obj.key) if f.type == "text"]
    named = [f for f in fields if f.key == "name"]
    if named:
        return named[0]
    required = [f for f in fields if f.required]
    return (required or fields or [None])[0]  # type: ignore[list-item]


def primary_property(design: Design, obj: ObjectDef) -> tuple[str, dict[str, Any], FieldDef | None]:
    """(name, inline property body, design field or None) for a custom object's display property."""
    f = primary_field(design, obj)
    if f is not None:
        return f.key, property_body(design, f, group=None, in_schema=True), f
    body = {
        "name": "name",
        "label": "Name",
        "type": "string",
        "fieldType": "text",
        "description": f"Name of the {obj.label.lower()}. Added by the generator: the design has no text field to name it.",
    }
    return "name", body, None


def _custom_in_order(design: Design) -> list[ObjectDef]:
    return [o for o in design.custom_objects if not is_existing(design, o)]


# --- schemas ---------------------------------------------------------------------------------


def _associated_objects(design: Design, obj: ObjectDef, built: list[str]) -> tuple[list[str], bool]:
    """(`associatedObjects`, same-object flag) for a schema.

    Declares every non-native relationship end. Another custom object is declared only when it is
    created earlier (`built`), because its ID is unknown before that; the later schema declares it.
    """
    ids: list[str] = []
    same = False
    for rel in design.relationships:
        if PLATFORM in rel.native or obj.key not in (rel.from_object, rel.to_object):
            continue
        other_key = rel.to_object if rel.from_object == obj.key else rel.from_object
        if other_key == obj.key:
            same = True
            continue
        other = design.get_object(other_key)
        if other is None:
            continue
        if other.kind == "custom" and other.key not in built and not is_existing(design, other):
            continue
        ref = object_type_id(design, other)
        if ref not in ids:
            ids.append(ref)
    return ids, same


def schema_requests(design: Design) -> list[dict[str, Any]]:
    """One create-schema request per new custom object, with all nine fields the OpenAPI requires."""
    requests: list[dict[str, Any]] = []
    built: list[str] = []
    for obj in _custom_in_order(design):
        name, prop, field = primary_property(design, obj)
        associated, same = _associated_objects(design, obj, built)
        body = {
            "name": obj.key,
            "labels": {"singular": obj.label, "plural": obj.plural_label},
            "description": obj.description,
            "primaryDisplayProperty": name,
            "secondaryDisplayProperties": [],
            "searchableProperties": [name],
            "requiredProperties": [name],
            "allowsSensitiveProperties": False,
            "shouldCreateSameObjectAssociation": same,
            "associatedObjects": associated,
            "properties": [prop],
        }
        requests.append(
            {
                "method": "POST",
                "path": f"/crm-object-schemas/{API_VERSION}/schemas",
                "body": body,
                "note": (
                    "Needs Enterprise. Save objectTypeId from the response as "
                    f"{type_id_placeholder(obj.key)}."
                ),
            }
        )
        built.append(obj.key)
    return requests


# --- property groups and properties ----------------------------------------------------------


def _emitted_fields(design: Design) -> list[tuple[ObjectDef, FieldDef]]:
    """Design fields that become a create-property request, in design order."""
    out: list[tuple[ObjectDef, FieldDef]] = []
    for obj in design.objects:
        skip = None
        if not is_existing(design, obj):
            _, _, skip = primary_property(design, obj)
        for f in design.fields_of(obj.key):
            if PLATFORM in f.native or f is skip:
                continue
            out.append((obj, f))
    return out


def group_requests(design: Design) -> list[dict[str, Any]]:
    """One create-group request per object and group name that holds an emitted property."""
    requests: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for obj, f in _emitted_fields(design):
        group = group_for(design, f)
        key = (obj.key, group)
        if key in seen or group in BUILTIN_GROUPS:
            continue
        seen.add(key)
        label = design.name if group == design_group(design) else group.replace("_", " ").capitalize()
        requests.append(
            {
                "method": "POST",
                "path": f"/crm/properties/{API_VERSION}/{object_ref(design, obj)}/groups",
                "body": {"name": group, "label": label},
            }
        )
    return requests


def _extra_required(design: Design, obj: ObjectDef) -> list[str]:
    _, _, skip = primary_property(design, obj)
    return [f.key for f in design.fields_of(obj.key) if f.required and f is not skip]


def property_requests(design: Design) -> list[dict[str, Any]]:
    """Create-property requests, then option updates on native properties, then schema patches."""
    requests: list[dict[str, Any]] = []
    for obj, f in _emitted_fields(design):
        requests.append(
            {
                "method": "POST",
                "path": f"/crm/properties/{API_VERSION}/{object_ref(design, obj)}",
                "body": property_body(design, f, group=group_for(design, f)),
            }
        )
    for obj in design.objects:
        for f in design.fields_of(obj.key):
            if PLATFORM in f.native and f.options:
                name = f.native_names.get(PLATFORM, f.key)
                requests.append(
                    {
                        "method": "PATCH",
                        "path": f"/crm/properties/{API_VERSION}/{object_ref(design, obj)}/{name}",
                        "body": {"options": _options(f)},
                        "note": (
                            "Standard property: read it first and merge its existing options with these, "
                            "because PATCH replaces the whole list. Hide options instead of removing them."
                        ),
                    }
                )
    for obj in _custom_in_order(design):
        extra = _extra_required(design, obj)
        if not extra:
            continue
        name, _, _ = primary_property(design, obj)
        requests.append(
            {
                "method": "PATCH",
                "path": f"/crm-object-schemas/{API_VERSION}/schemas/{object_ref(design, obj)}",
                "body": {"clearDescription": False, "requiredProperties": [name, *extra]},
                "note": "Run after the properties above exist: requiredProperties can only name existing properties.",
            }
        )
    return requests


# --- associations ----------------------------------------------------------------------------


def type_id_name(rel: RelationshipDef, frm: str, to: str) -> str:
    """Placeholder for the type ID of a relationship's label in the direction frm to to."""
    return "{typeId." + f"{rel.key}.{frm}_to_{to}" + "}"


def association_requests(design: Design) -> list[dict[str, Any]]:
    """A paired label for each non-native relationship, then an association limit for each cap."""
    labels: list[dict[str, Any]] = []
    limits: list[dict[str, Any]] = []
    for rel in design.relationships:
        if PLATFORM in rel.native:
            continue
        frm = object_ref_for(design, rel.from_object)
        to = object_ref_for(design, rel.to_object)
        labels.append(
            {
                "method": "POST",
                "path": f"/crm/associations/{API_VERSION}/{frm}/{to}/labels",
                "body": {"name": rel.key, "label": rel.from_label, "inverseLabel": rel.to_label},
                "note": (
                    "Needs Professional or Enterprise. The response holds one typeId per direction: "
                    f"save them as {type_id_name(rel, rel.from_object, rel.to_object)} and "
                    f"{type_id_name(rel, rel.to_object, rel.from_object)}."
                ),
            }
        )
        caps: list[tuple[str, str]] = []  # (from object key, to object key) to limit to one
        if rel.cardinality in ("many_to_one", "one_to_one"):
            caps.append((rel.from_object, rel.to_object))
        if rel.cardinality in ("one_to_many", "one_to_one"):
            caps.append((rel.to_object, rel.from_object))
        for a, b in caps:
            limits.append(
                {
                    "method": "POST",
                    "path": (
                        f"/crm/associations/{API_VERSION}/definitions/configurations/"
                        f"{object_ref_for(design, a)}/{object_ref_for(design, b)}/batch/create"
                    ),
                    "body": {
                        "inputs": [
                            {
                                "category": "USER_DEFINED",
                                "typeId": type_id_name(rel, a, b),
                                "maxToObjectIds": 1,
                            }
                        ]
                    },
                    "note": f"Needs Professional or Enterprise. A {a} record may link to one {b} record.",
                }
            )
    return labels + limits


# --- pipelines -------------------------------------------------------------------------------


def probability_string(value: float | None) -> str:
    """A 0 to 100 percentage as HubSpot's string from "0.0" to "1.0"."""
    fraction = round((value or 0.0) / 100.0, 4)
    text = f"{fraction:.4f}".rstrip("0")
    return text + "0" if text.endswith(".") else text


def stage_metadata(pipeline: Pipeline, stage: Stage) -> dict[str, str]:
    """Deal stages carry a probability ("1.0" won, "0.0" lost). Other objects get `isClosed` (OQ-1)."""
    if pipeline.object == "deal":
        if stage.type == "won":
            return {"probability": "1.0"}
        if stage.type == "lost":
            return {"probability": "0.0"}
        return {"probability": probability_string(stage.probability)}
    return {"isClosed": "false" if stage.type == "open" else "true"}


def pipeline_supported(design: Design, pipeline: Pipeline) -> bool:
    """HubSpot has pipelines on deals and custom objects. Contacts and companies have none."""
    obj = design.get_object(pipeline.object)
    return obj is not None and (obj.kind == "custom" or pipeline.object == "deal")


def pipeline_id(design: Design, pipeline: Pipeline) -> str:
    """The pipelineId: the pipeline key, prefixed with the object when two objects share the key."""
    clash = any(p.key == pipeline.key and p.object != pipeline.object for p in design.pipelines)
    return f"{pipeline.object}__{pipeline.key}" if clash else pipeline.key


def stage_id(pipeline: Pipeline, stage: Stage) -> str:
    """The stageId, scoped to its pipeline because stage keys repeat across pipelines (D-12)."""
    return f"{pipeline.key}__{stage.key}"


def pipeline_requests(design: Design) -> list[dict[str, Any]]:
    """One create-pipeline request per supported pipeline, stages included."""
    requests: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    for pl in design.pipelines:
        if not pipeline_supported(design, pl):
            continue
        counts[pl.object] = counts.get(pl.object, 0) + 1
        stages = [
            {
                "label": s.label,
                "displayOrder": i,
                "stageId": stage_id(pl, s),
                "metadata": stage_metadata(pl, s),
            }
            for i, s in enumerate(pl.stages)
        ]
        request: dict[str, Any] = {
            "method": "POST",
            "path": f"/crm/pipelines/{API_VERSION}/{object_ref_for(design, pl.object)}",
            "body": {
                "label": pl.name,
                "displayOrder": counts[pl.object],
                "pipelineId": pipeline_id(design, pl),
                "stages": stages,
            },
        }
        if pl.object != "deal":
            request["note"] = (
                "Custom object pipeline: needs Enterprise. HubSpot has open or closed here, not won or lost, "
                "and the key for closed is unconfirmed (OQ-1). Read the pipeline back and check each closed stage."
            )
        requests.append(request)
    return requests


# --- payload files ---------------------------------------------------------------------------


def _used_placeholders(requests: list[dict[str, Any]]) -> list[str]:
    text = json.dumps(requests)
    found: list[str] = []
    for m in re.finditer(r"\{(?:objectTypeId|typeId)\.[a-z0-9_.]+\}", text):
        if m.group(0) not in found:
            found.append(m.group(0))
    return found


def _placeholder_help(name: str) -> str:
    if name.startswith("{objectTypeId."):
        return "objectTypeId in the response of the create-schema request for this object (schemas.json)."
    return (
        "typeId of the label in that direction: GET /crm/associations/"
        f"{API_VERSION}/<from>/<to>/labels after the label is created (associations.json)."
    )


def _document(filename: str, sources: list[str], requests: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "api_version": API_VERSION,
        "order": ORDER[filename],
        "source": sources,
        "placeholders": {p: _placeholder_help(p) for p in _used_placeholders(requests)},
        "requests": requests,
    }


def build_payloads(design: Design) -> dict[str, dict[str, Any]]:
    """The five JSON documents, keyed by file name."""
    return {
        "schemas.json": _document("schemas.json", [SRC_CREATE_SCHEMA, SRC_SCHEMAS], schema_requests(design)),
        "property-groups.json": _document(
            "property-groups.json", [SRC_PROPERTY_GROUPS, SRC_PROPERTIES], group_requests(design)
        ),
        "properties.json": _document(
            "properties.json", [SRC_PROPERTIES, SRC_SCHEMAS], property_requests(design)
        ),
        "associations.json": _document(
            "associations.json", [SRC_ASSOCIATIONS, SRC_ASSOC_LABEL_KB, SRC_ASSOC_LIMIT_KB], association_requests(design)
        ),
        "pipelines.json": _document("pipelines.json", [SRC_PIPELINES, SRC_PIPELINE_KB], pipeline_requests(design)),
    }


# --- build sheet -----------------------------------------------------------------------------

SETTINGS = "Settings > Data Management > Objects"


class HubSpotHooks(BuildSheetHooks):
    """HubSpot UI paths and manual wording for the build sheet."""

    platform_label = "HubSpot"

    def __init__(self, design: Design) -> None:
        self.design = design

    def _ui(self, key: str) -> str:
        obj = self.design.get_object(key)
        return object_ui_name(self.design, obj) if obj else key

    def object_path(self, obj: ObjectDef) -> str:
        return (
            f"{SETTINGS} > Create custom object (needs Enterprise). Singular '{obj.label}', plural "
            f"'{obj.plural_label}', internal name `{obj.key}`. The name cannot be changed later."
        )

    def relationship_path(self, rel: RelationshipDef) -> str:
        return (
            f"{SETTINGS} > {self._ui(rel.from_object)} > Associations tab > Create association label "
            f"(Super Admin; needs Professional or Enterprise). Pair '{rel.from_label}' with '{rel.to_label}' "
            f"for {self._ui(rel.to_object)}."
        )

    def pipeline_path(self, pipeline: Pipeline) -> str:
        return (
            f"{SETTINGS} > {self._ui(pipeline.object)} > Pipelines tab > Create pipeline > Create from scratch, "
            f"then + Add stage for each stage. "
            + (
                "Set the Deal probability dropdown to Won or Lost on the closing stages."
                if pipeline.object == "deal"
                else "Set each stage to Open or Closed."
            )
        )

    def stage_rule(self, pipeline: Pipeline, stage: Stage) -> str:
        parts = []
        if pipeline.object == "deal":
            parts.append(f"Deal probability: {probability_string(stage.probability) if stage.type == 'open' else ('1.0' if stage.type == 'won' else '0.0')}.")
        if stage.required_fields:
            parts.append(
                "HubSpot has no API for required fields per stage. In the pipeline's stage row choose "
                "Conditional logic rules > Add rule > Add property and tick Required for: "
                + ", ".join(stage.required_fields)
                + "."
            )
        return " ".join(parts)

    def field_path(self, field: FieldDef) -> str:
        hs_type, field_type, _ = TYPE_MAP.get(field.type, ("string", "text", {}))
        return (
            f"{SETTINGS} > {self._ui(field.object)} > Properties tab > Create property. Group "
            f"'{group_for(self.design, field)}', type/field type in the UI matching `{hs_type}`/`{field_type}`, "
            f"internal name `{field.key}`."
        )

    def automation_path(self, automation: Any) -> str:
        return "Automations > Workflows > Create workflow (needs Professional or Enterprise)."

    def view_path(self, view: Any) -> str:
        return (
            f"CRM > {self._ui(view.object)} > + add view, then set filters, columns and sort, and click Publish."
        )

    def manual_steps(self) -> list[str]:
        return [s["title"] for s in manual_steps(self.design) if s["group"] == "setup"]


# --- manual steps ----------------------------------------------------------------------------


def manual_steps(design: Design) -> list[dict[str, str]]:
    """Every step the HubSpot API cannot do. Each has group, title, where, why and done_when."""
    steps: list[dict[str, str]] = []

    def add(group: str, title: str, where: str, why: str, done: str) -> None:
        steps.append({"group": group, "title": title, "where": where, "why": why, "done_when": done})

    def ui(key: str) -> str:
        obj = design.get_object(key)
        return object_ui_name(design, obj) if obj else key

    custom = _custom_in_order(design)
    add(
        "setup",
        "Create a service key and test in a developer test account first",
        "Development > Keys > Service keys > Create service key (scopes in platforms/hubspot/reference/auth-and-setup.md)",
        "Keys are made in the account by a super admin. A developer test account carries a 90-day Enterprise "
        "trial, so it can test custom objects before the client account is touched.",
        "`GET /crm/properties/" + API_VERSION + "/contacts` returns 200 with the key.",
    )
    if custom:
        add(
            "setup",
            "Confirm the account is Enterprise before creating custom objects",
            "Settings > Account Management > Account defaults, and GET /crm/limits/" + API_VERSION + "/custom-object-types",
            "Custom objects need Enterprise and there is no workaround on a lower tier. A client is typically "
            f"limited to 10 definitions (OQ-3); this blueprint creates {len(custom)}.",
            "the tier is written in the client notes and the limits call allows "
            f"{len(custom)} custom object(s) ({', '.join(o.label for o in custom)}).",
        )
    for obj in design.custom_objects:
        if is_existing(design, obj):
            add(
                "setup",
                f"Check the existing object {obj.label} is linked to its related objects",
                f"{SETTINGS} > {obj.plural_label} > Associations tab",
                "The design gives this object an existing ID, so no schema is sent and `associatedObjects` "
                "cannot declare its links. The label call needs the link to exist first (OQ-7).",
                f"each related object appears on the {obj.label} Associations tab before associations.json is run.",
            )
    for obj, f in [(o, f) for o in design.objects for f in design.fields_of(o.key)]:
        if f.required and obj.kind == "core":
            add(
                "required",
                f"Make {obj.label} {f.label} required",
                f"{SETTINGS} > {ui(obj.key)} > Properties tab > {f.label}, or a workflow that flags it when empty",
                "HubSpot has no API setting for required properties on standard objects (OQ-9).",
                f"a {obj.label.lower()} record cannot be saved, or is flagged, when {f.label} is empty.",
            )
    for pl in design.pipelines:
        if not pipeline_supported(design, pl):
            add(
                "pipeline",
                f"Model the {pl.name} pipeline without a pipeline",
                f"{SETTINGS} > {ui(pl.object)} > Properties tab > Create property (a select for the stage)",
                f"HubSpot has pipelines on deals and custom objects, not on {ui(pl.object).lower()}.",
                "a select property lists the stages " + ", ".join(s.label for s in pl.stages) + ".",
            )
            continue
        if pl.object != "deal":
            add(
                "pipeline",
                f"Check closed stages of {pl.name}",
                f"{SETTINGS} > {ui(pl.object)} > Pipelines tab > {pl.name}",
                "HubSpot has open or closed on custom object stages, not won or lost, and no probability "
                "(the design's probabilities are not sent). The API key for closed is unconfirmed (OQ-1).",
                "closed stages ("
                + ", ".join(s.label for s in pl.stages if s.type != "open")
                + ") show as Closed. Set them by hand if the read-back says otherwise.",
            )
        for s in pl.stages:
            if not s.required_fields:
                continue
            names = ", ".join(_field_label(design, pl.object, k) for k in s.required_fields)
            add(
                "gate",
                f"Require {names} to enter {s.label} ({pl.name})",
                f"{SETTINGS} > {ui(pl.object)} > Pipelines tab > {pl.name} > stage row for {s.label} > "
                "Conditional logic rules > Add rule > Add property > Required > Save logic",
                "Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create "
                "the properties first; read-only properties cannot be used.",
                f"moving a test {pl.object} into {s.label} asks for {names}.",
            )
    for rel in design.relationships:
        if PLATFORM in rel.native or rel.cardinality == "many_to_many":
            continue
        add(
            "decision",
            f"Check the association limit for {rel.key}",
            f"{SETTINGS} > {ui(rel.from_object)} > Associations tab (Super Admin)",
            "The limit is set on the labelled association type only. The unlabelled default type has an ID "
            "that is known only on read.",
            f"{rel.cardinality.replace('_', ' ')} holds for both labelled and unlabelled links in a test.",
        )
    used = sorted({f.type for f in design.fields if PLATFORM not in f.native and f.type in LOSSY_TYPES})
    for ftype in used:
        names = ", ".join(f"{f.object}.{f.key}" for f in design.fields if f.type == ftype and PLATFORM not in f.native)
        add(
            "decision",
            f"Accept that {ftype} fields are lossy in HubSpot",
            f"{SETTINGS} > Properties tab, then open a record and look at the field",
            f"The HubSpot property {LOSSY_TYPES[ftype]}.",
            f"the client has agreed in the client notes. Fields: {names}.",
        )
    for a in design.automations:
        add(
            "automation",
            f"Workflow: {a.name}",
            "Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on",
            "The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and "
            "the Edit workflows and Publish permissions.",
            f"a test run matches: trigger '{a.trigger}'; action '{a.action}'",
        )
    for v in design.views:
        add(
            "view",
            f"Saved view: {v.name}",
            f"CRM > {ui(v.object)} > + add view > name it > set filters, columns and sort > Publish > Manage sharing",
            "HubSpot has no API to create saved index-page views.",
            f"the view {v.name} shows on the {ui(v.object)} index with filter '{v.filter}' and sort '{v.sort}'.",
        )
    add(
        "permissions",
        "Set roles and access",
        "Settings > Users & Teams (menu name not verified against a page in the research)",
        "No permission-set API was found. Only pipeline stage edit permissions have one, and this blueprint does not use it.",
        "a non-admin test user sees and edits what their role needs and nothing more.",
    )
    return steps


def _field_label(design: Design, obj_key: str, key: str) -> str:
    f = design.get_field(obj_key, key)
    return f.label if f else key


GROUP_TITLES: dict[str, str] = {
    "setup": "Before and during the build",
    "required": "Required fields on standard objects",
    "pipeline": "Pipelines",
    "gate": "Stage gates and lost reasons",
    "decision": "Decisions where the HubSpot mapping is lossy",
    "automation": "Workflows",
    "view": "Saved views",
    "permissions": "Permissions",
}


def render_manual_steps(design: Design) -> str:
    """The manual-steps.md text."""
    steps = manual_steps(design)
    L = [
        f"# Manual steps: {design.name} (hubspot)",
        "",
        "Generated from `design.yaml`. Do not edit by hand. The HubSpot API cannot do any of this.",
        "Sources: " + ", ".join([SRC_PIPELINES, SRC_VIEWS_KB, SRC_WORKFLOWS_KB]) + ", "
        "`platforms/hubspot/reference/api-coverage.md`.",
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


# --- plan requirements -----------------------------------------------------------------------


def plan_features(design: Design) -> list[dict[str, str]]:
    """Features the blueprint uses: feature, used for, minimum tier and source. Tiers are from the research."""
    rows: list[dict[str, str]] = []

    def add(feature: str, used: str, tier: str, source: str) -> None:
        rows.append({"feature": feature, "used": used, "tier": tier, "source": source})

    custom = _custom_in_order(design)
    props = [f for f in design.fields if PLATFORM not in f.native]
    if props:
        add(
            "Custom properties and property groups",
            f"{len(props)} custom properties",
            "Free tools allow 10 custom properties in total. Starter, Professional and Enterprise allow 1,000 per object.",
            SRC_CATALOG,
        )
    if custom:
        add(
            "Custom objects",
            f"{len(custom)} custom object(s): {', '.join(o.label for o in custom)}",
            "Enterprise. Typically up to 10 definitions (OQ-3: check GET /crm/limits/" + API_VERSION + "/custom-object-types).",
            f"{SRC_SCHEMAS} ; {SRC_CUSTOM_OBJECT_KB}",
        )
    supported = [p for p in design.pipelines if pipeline_supported(design, p)]
    if supported:
        add(
            "Custom pipelines",
            f"{len(supported)} pipeline(s): {', '.join(p.name for p in supported)}",
            "Starter or higher. Limit of custom pipelines across all objects: Starter 15, Professional 100 or 350, Enterprise 350.",
            SRC_PIPELINE_KB,
        )
    custom_pipes = [p for p in supported if p.object != "deal"]
    if custom_pipes:
        add(
            "Custom object pipelines",
            ", ".join(p.name for p in custom_pipes),
            "Enterprise",
            SRC_PIPELINE_KB,
        )
        add(
            "Not supported on custom object pipelines: probability, won versus lost",
            "Stage probabilities and the won or lost split of "
            + ", ".join(p.name for p in custom_pipes)
            + " are not sent. Stages are open or closed only (OQ-1); the stage label carries the meaning",
            "No tier has them: HubSpot has probability and won or lost on deal pipelines only",
            SRC_PIPELINES,
        )
    unsupported = [p for p in design.pipelines if not pipeline_supported(design, p)]
    if unsupported:
        add(
            "Not supported: pipelines on contacts or companies",
            ", ".join(p.name for p in unsupported) + " (modelled by hand as a select property)",
            "No tier has them: HubSpot pipelines exist for deals, tickets and custom objects",
            SRC_PIPELINES,
        )
    labelled = [r for r in design.relationships if PLATFORM not in r.native]
    if labelled:
        add(
            "Association labels",
            f"{len(labelled)} paired label(s), one per non-standard relationship",
            "Professional or Enterprise. Plan for 10 labels per object pair (the developer page says 10, the knowledge base says 50: OQ-2).",
            f"{SRC_ASSOC_LABEL_KB} ; {SRC_ASSOCIATIONS}",
        )
    capped = [r for r in labelled if r.cardinality != "many_to_many"]
    if capped:
        add(
            "Association limits (cardinality)",
            f"{len(capped)} relationship(s) capped at one: {', '.join(r.key for r in capped)}",
            "Professional or Enterprise. On Starter the cap is a convention only.",
            SRC_ASSOC_LIMIT_KB,
        )
    gated = [(p, s) for p in design.pipelines for s in p.stages if s.required_fields]
    if gated:
        add(
            "Conditional stage properties (required fields per stage)",
            f"{len(gated)} stage(s), set by hand in the UI",
            "Not stated on the page. Assume Professional or higher (OQ-8).",
            SRC_PIPELINE_KB,
        )
    if design.automations:
        add(
            "Workflows",
            f"{len(design.automations)} automation(s), built by hand",
            "Professional or Enterprise",
            SRC_WORKFLOWS_KB,
        )
    if design.views:
        add(
            "Saved views",
            f"{len(design.views)} view(s), built by hand",
            "All products and plans",
            SRC_VIEWS_KB,
        )
    return rows


def render_plan_requirements(design: Design) -> str:
    """The plan-requirements.md text."""
    rows = plan_features(design)
    custom = _custom_in_order(design)
    L = [
        f"# Plan requirements: {design.name} (hubspot)",
        "",
        "Generated from `design.yaml` and `platforms/hubspot/reference/`. Do not edit by hand. "
        "Tiers are as the research recorded them (last verified 2026-10-04); check the account's own "
        "limits before building.",
        "",
    ]
    if custom:
        L.append(
            "**Minimum tier: Enterprise.** The custom objects need it, and the research found no workaround on a "
            "lower tier. Without Enterprise the custom objects, and any pipeline on them, cannot be created: "
            "the build turns them into a blocked item and the client must upgrade or drop the design's custom objects."
        )
    else:
        L.append("**Minimum tier:** the highest tier in the table below.")
    L += [
        "",
        "| Feature | Used for | Minimum tier | Source |",
        "|---|---|---|---|",
    ]
    for r in rows:
        L.append(f"| {r['feature']} | {r['used']} | {r['tier']} | {r['source']} |")
    L.append("")
    return "\n".join(L)


# --- writing ---------------------------------------------------------------------------------


def _dump(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def _write(path: Path, text: str) -> Path:
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    return path


def generate(design: Design, out_dir: Path) -> list[Path]:
    """Write the HubSpot files for a design into `out_dir` and return the paths written."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, data in build_payloads(design).items():
        written.append(_write(out_dir / name, _dump(data)))
    written.append(
        _write(out_dir / "build-sheet.md", render_build_sheet(design, PLATFORM, HubSpotHooks(design)))
    )
    written.append(_write(out_dir / "manual-steps.md", render_manual_steps(design)))
    written.append(_write(out_dir / "plan-requirements.md", render_plan_requirements(design)))
    return written
