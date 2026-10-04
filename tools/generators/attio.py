"""Generate Attio request payloads, a build sheet and manual steps from a design.

Files written to `<out_dir>` (normally `blueprints/<name>/attio/`):

- `objects.json`, `relationships.json`, `lists.json`, `statuses.json`, `attributes.json`: ordered
  API requests. Each file is `{"source": [...], "order": n, "requests": [...]}` and each request is
  `{"method", "path", "body"}`. Run the files in `order`: objects (1), relationships (2), lists with
  their own attributes (3), statuses (4), attributes and select options (5). This is the brief's
  build order: objects, relationships, pipelines, fields.
- `build-sheet.md`: the human checklist, through `build_sheet.render_build_sheet`.
- `manual-steps.md`: everything the Attio API cannot do, each with a UI path and a reason.

Payload shapes come from `platforms/attio/reference/`, which was read from Attio's OpenAPI spec.
Output is deterministic: fixed key order, no timestamps.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from tools.design import Design, FieldDef, ObjectDef, Pipeline, RelationshipDef, Stage
from tools.generators.build_sheet import BuildSheetHooks, render_build_sheet

PLATFORM = "attio"

SRC_OPENAPI = "https://api.attio.com/openapi/api"
SRC_CREATE_OBJECT = "https://docs.attio.com/rest-api/endpoint-reference/objects/create-an-object.md"
SRC_CREATE_ATTRIBUTE = "https://docs.attio.com/rest-api/endpoint-reference/attributes/create-an-attribute.md"
SRC_RECORD_REFERENCE = "https://docs.attio.com/rest-api/attribute-types/attribute-types-record-reference.md"
SRC_STATUS = "https://docs.attio.com/rest-api/attribute-types/attribute-types-status.md"
SRC_CREATE_LIST = "https://docs.attio.com/rest-api/endpoint-reference/lists/create-a-list.md"

# Slugs that Attio uses on its own objects. A design field that would take one gets a prefix.
RESERVED_SLUGS: frozenset[str] = frozenset(
    {"name", "stage", "owner", "domains", "email_addresses", "created_at"}
)

# canonical type -> (Attio type, is_multiselect)
TYPE_MAP: dict[str, tuple[str, bool]] = {
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

# Text appended to the description where the Attio type loses the canonical meaning.
LOSSY_NOTES: dict[str, str] = {
    "long_text": "Long text: Attio has one text type.",
    "percent": "Percentage stored as a number from 0 to 100.",
    "url": "Full web address stored as text: Attio has no URL type.",
}


def _slugify(text: str) -> str:
    """snake_case slug from a label."""
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _overrides(design: Design) -> dict[str, Any]:
    value = design.platform_overrides.get(PLATFORM, {})
    return value if isinstance(value, dict) else {}


def _override_slug(design: Design, section: str, target: str) -> str | None:
    entry = _overrides(design).get(section, {})
    entry = entry.get(target, {}) if isinstance(entry, dict) else {}
    slug = entry.get("api_slug") if isinstance(entry, dict) else None
    return slug if isinstance(slug, str) and slug else None


def object_slug(design: Design, obj: ObjectDef) -> str:
    """The Attio slug of an object: native name, override, or the snake_case plural label."""
    if obj.kind == "core":
        return obj.native_names.get(PLATFORM, obj.plural_label.lower())
    return _override_slug(design, "objects", obj.key) or _slugify(obj.plural_label or obj.label + "s")


def object_slug_for(design: Design, key: str) -> str:
    """Slug for an object key. Falls back to the key if the object is unknown."""
    obj = design.get_object(key)
    return object_slug(design, obj) if obj else key


def field_slug(design: Design, f: FieldDef) -> str:
    """The Attio slug of a field: override, else the key, prefixed when it is a reserved slug."""
    override = _override_slug(design, "fields", f"{f.object}.{f.key}")
    if override:
        return override
    if f.key in RESERVED_SLUGS and PLATFORM not in f.native:
        return f"{f.object}_{f.key}"
    return f.key


def _is_object_name_field(design: Design, f: FieldDef) -> bool:
    """A `name` field on a custom object maps to the name Attio gives every object."""
    obj = design.get_object(f.object)
    return bool(obj and obj.kind == "custom" and f.key == "name")


def _currency_config() -> dict[str, Any]:
    return {"currency": {"default_currency_code": "GBP", "display_type": "symbol"}}


def _description(f: FieldDef) -> str:
    note = LOSSY_NOTES.get(f.type)
    return f"{f.description} {note}" if note else f.description


def attribute_request(target: str, parent_slug: str, f: FieldDef, slug: str) -> dict[str, Any]:
    """The create-attribute request for one design field. `target` is `objects` or `lists`."""
    attio_type, multi = TYPE_MAP[f.type]
    config: dict[str, Any] = _currency_config() if attio_type == "currency" else {}
    return {
        "method": "POST",
        "path": f"/v2/{target}/{parent_slug}/attributes",
        "body": {
            "data": {
                "title": f.label,
                "description": _description(f),
                "api_slug": slug,
                "type": attio_type,
                "is_required": False,
                "is_unique": False,
                "is_multiselect": multi,
                "config": config,
            }
        },
    }


def option_requests(target: str, parent_slug: str, slug: str, f: FieldDef) -> list[dict[str, Any]]:
    """One add-option request per option, in design order."""
    return [
        {
            "method": "POST",
            "path": f"/v2/{target}/{parent_slug}/attributes/{slug}/options",
            "body": {"data": {"title": opt.label}},
        }
        for opt in f.options
    ]


def relationship_request(design: Design, rel: RelationshipDef) -> dict[str, Any]:
    """One record-reference attribute that creates both sides of a relationship."""
    from_slug = object_slug_for(design, rel.from_object)
    to_slug = object_slug_for(design, rel.to_object)
    parent_multi = rel.cardinality in ("one_to_many", "many_to_many")
    reverse_multi = rel.cardinality in ("many_to_one", "many_to_many")
    return {
        "method": "POST",
        "path": f"/v2/objects/{from_slug}/attributes",
        "body": {
            "data": {
                "title": rel.from_label,
                "description": rel.purpose,
                "api_slug": _slugify(rel.from_label),
                "type": "record-reference",
                "is_required": False,
                "is_unique": False,
                "is_multiselect": parent_multi,
                "config": {"record_reference": {"allowed_objects": [to_slug]}},
                "relationship": {
                    "object": to_slug,
                    "title": rel.to_label,
                    "api_slug": _slugify(rel.to_label),
                    "is_multiselect": reverse_multi,
                },
            }
        },
    }


def _lost_reason_fields(design: Design, pipeline: Pipeline) -> list[FieldDef]:
    """Select fields required on a lost stage, in first-seen order."""
    seen: list[FieldDef] = []
    for stage in pipeline.stages:
        if stage.type != "lost":
            continue
        for key in stage.required_fields:
            f = design.get_field(pipeline.object, key)
            if f and f.type == "select" and f not in seen:
                seen.append(f)
    return seen


def _stage_description(pipeline: Pipeline) -> str:
    parts = " ".join(f"{s.label}: {s.exit_criteria}" for s in pipeline.stages)
    return f"Stage of the {pipeline.name} pipeline. {parts}"


def list_requests(design: Design, pipeline: Pipeline) -> list[dict[str, Any]]:
    """The list, then its `stage`, `probability` and lost-reason attributes with options."""
    list_slug = pipeline.key
    reqs: list[dict[str, Any]] = [
        {
            "method": "POST",
            "path": "/v2/lists",
            "body": {
                "data": {
                    "name": pipeline.name,
                    "api_slug": list_slug,
                    "parent_object": object_slug_for(design, pipeline.object),
                    "workspace_access": "full-access",
                    "workspace_member_access": [],
                }
            },
        },
        {
            "method": "POST",
            "path": f"/v2/lists/{list_slug}/attributes",
            "body": {
                "data": {
                    "title": "Stage",
                    "description": _stage_description(pipeline),
                    "api_slug": "stage",
                    "type": "status",
                    "is_required": False,
                    "is_unique": False,
                    "is_multiselect": False,
                    "config": {},
                }
            },
        },
        {
            "method": "POST",
            "path": f"/v2/lists/{list_slug}/attributes",
            "body": {
                "data": {
                    "title": "Probability",
                    "description": (
                        "Win probability in percent (0 to 100) for the current stage. "
                        "Attio does not enforce it: set it to match the stage."
                    ),
                    "api_slug": "probability",
                    "type": "number",
                    "is_required": False,
                    "is_unique": False,
                    "is_multiselect": False,
                    "config": {},
                }
            },
        },
    ]
    for f in _lost_reason_fields(design, pipeline):
        slug = f.key
        reqs.append(attribute_request("lists", list_slug, f, slug))
        reqs.extend(option_requests("lists", list_slug, slug, f))
    return reqs


def status_request(pipeline: Pipeline, stage: Stage) -> dict[str, Any]:
    """The create-status request for one stage. Won stages get the celebration flag."""
    return {
        "method": "POST",
        "path": f"/v2/lists/{pipeline.key}/attributes/stage/statuses",
        "body": {"data": {"title": stage.label, "celebration_enabled": stage.type == "won"}},
    }


def status_requests(pipeline: Pipeline) -> list[dict[str, Any]]:
    """One status per stage in design order. Won stages get the celebration flag."""
    return [status_request(pipeline, s) for s in pipeline.stages]


def object_request(design: Design, obj: ObjectDef) -> dict[str, Any]:
    """The create-object request for one custom object."""
    return {
        "method": "POST",
        "path": "/v2/objects",
        "body": {
            "data": {
                "api_slug": object_slug(design, obj),
                "singular_noun": obj.label,
                "plural_noun": obj.plural_label,
            }
        },
    }


def build_payloads(design: Design) -> dict[str, dict[str, Any]]:
    """The five JSON documents, keyed by file name."""
    objects = [object_request(design, obj) for obj in design.custom_objects]

    attributes: list[dict[str, Any]] = []
    for obj in design.objects:
        parent = object_slug(design, obj)
        for f in design.fields_of(obj.key):
            slug = field_slug(design, f)
            if PLATFORM in f.native:
                # A standard attribute: only options the design adds are sent.
                native_slug = f.native_names.get(PLATFORM, slug)
                if f.options:
                    attributes.extend(option_requests("objects", parent, native_slug, f))
                continue
            if _is_object_name_field(design, f):
                continue
            attributes.append(attribute_request("objects", parent, f, slug))
            attributes.extend(option_requests("objects", parent, slug, f))

    relationships = [relationship_request(design, r) for r in design.relationships if PLATFORM not in r.native]

    lists: list[dict[str, Any]] = []
    statuses: list[dict[str, Any]] = []
    for pl in design.pipelines:
        lists.extend(list_requests(design, pl))
        statuses.extend(status_requests(pl))

    def doc(order: int, source: list[str], reqs: list[dict[str, Any]]) -> dict[str, Any]:
        return {"source": source, "order": order, "requests": reqs}

    return {
        "objects.json": doc(1, [SRC_CREATE_OBJECT, SRC_OPENAPI], objects),
        "relationships.json": doc(2, [SRC_CREATE_ATTRIBUTE, SRC_RECORD_REFERENCE, SRC_OPENAPI], relationships),
        "lists.json": doc(3, [SRC_CREATE_LIST, SRC_CREATE_ATTRIBUTE, SRC_OPENAPI], lists),
        "statuses.json": doc(4, [SRC_STATUS, SRC_OPENAPI], statuses),
        "attributes.json": doc(5, [SRC_CREATE_ATTRIBUTE, SRC_OPENAPI], attributes),
    }


# --- build sheet -----------------------------------------------------------------------------


class AttioHooks(BuildSheetHooks):
    """Attio UI paths and manual wording for the build sheet."""

    platform_label = "Attio"

    def __init__(self, design: Design) -> None:
        self.design = design

    def object_path(self, obj: ObjectDef) -> str:
        return (
            f"Workspace settings, then Objects, then New object. Use singular {obj.label}, "
            f"plural {obj.plural_label}, slug `{object_slug(self.design, obj)}`."
        )

    def relationship_path(self, rel: RelationshipDef) -> str:
        frm = self.design.get_object(rel.from_object)
        return (
            f"Workspace settings, then Objects, then {frm.label if frm else rel.from_object}, then "
            f"Attributes, then New attribute. Choose a relationship to {rel.to_object}, name this side "
            f"'{rel.from_label}' and the other side '{rel.to_label}'."
        )

    def pipeline_path(self, pipeline: Pipeline) -> str:
        return (
            f"Lists in the left sidebar, then New list, parent object {pipeline.object}, named "
            f"'{pipeline.name}' (slug `{pipeline.key}`). Add a Status attribute called Stage, a Number "
            "attribute called Probability, and a Select attribute for the lost reason."
        )

    def stage_rule(self, pipeline: Pipeline, stage: Stage) -> str:
        parts = []
        if stage.type == "won":
            parts.append("Won stage: a plain status. Reports filter on this title. Celebration is on.")
        if stage.type == "lost":
            parts.append("Lost stage: a plain status. Reports filter on this title.")
        parts.append(f"Set Probability to {stage.probability:g} on entries at this stage." if stage.probability is not None else "")
        if stage.required_fields:
            parts.append(
                "Attio cannot require fields per stage. Build a Workflow (see manual-steps.md) that flags "
                "entry when these are empty: " + ", ".join(stage.required_fields) + "."
            )
        return " ".join(p for p in parts if p)

    def field_path(self, field: FieldDef) -> str:
        attio_type, multi = TYPE_MAP.get(field.type, ("text", False))
        obj = self.design.get_object(field.object)
        label = obj.label if obj else field.object
        kind = f"{attio_type}{' (allow several)' if multi else ''}"
        return (
            f"Workspace settings, then Objects, then {label}, then Attributes, then New attribute. "
            f"Type {kind}, slug `{field_slug(self.design, field)}`."
        )

    def automation_path(self, automation: Any) -> str:
        return "Workflows in the left sidebar, then Create workflow."

    def view_path(self, view: Any) -> str:
        obj = self.design.get_object(view.object)
        label = obj.plural_label if obj else view.object
        return f"Open {label} in the left sidebar, then + New view, set the filter and sort, and save."

    def manual_steps(self) -> list[str]:
        return [s["title"] for s in manual_steps(self.design) if s["group"] == "setup"]


# --- manual steps ----------------------------------------------------------------------------


def _field_label(design: Design, obj_key: str, key: str) -> str:
    f = design.get_field(obj_key, key)
    return f.label if f else key


def manual_steps(design: Design) -> list[dict[str, str]]:
    """Every step the Attio API cannot do. Each has group, title, where, why and done_when."""
    steps: list[dict[str, str]] = []

    def add(group: str, title: str, where: str, why: str, done: str) -> None:
        steps.append({"group": group, "title": title, "where": where, "why": why, "done_when": done})

    uses_deal = (
        any(p.object == "deal" for p in design.pipelines)
        or any(f.object == "deal" and PLATFORM not in f.native for f in design.fields)
        or any(
            PLATFORM not in r.native and "deal" in (r.from_object, r.to_object)
            for r in design.relationships
        )
    )
    custom = design.custom_objects

    add(
        "setup",
        "Confirm the client's Attio plan allows the objects below",
        "Workspace settings, then Billing, and https://attio.com/pricing",
        "Object limits depend on the plan (3, 5, 12 or unlimited) and Attio does not say whether standard "
        "objects count. A create past the limit fails with 400 quota_exceeded.",
        f"the plan is written in the client notes and allows {len(custom)} custom object(s) "
        f"({', '.join(o.label for o in custom) or 'none'}).",
    )
    if uses_deal:
        add(
            "setup",
            "Enable the Deals object",
            "Workspace settings, then Objects, then enable Deals",
            "Deals are off by default and the API has no call to enable them.",
            "Deals appears in the sidebar and `GET /v2/objects` lists `deals`. Do this before running "
            "relationships.json, lists.json or attributes.json.",
        )
    add(
        "setup",
        "Test the first relationship from both sides",
        "Create the first entry of relationships.json, then open both objects",
        "Attio's description of the cardinality flags is ambiguous (platforms/attio/reference/open-questions.md, Q7).",
        "the reverse attribute's is_multiselect matches the cardinality in build-sheet.md. If it is "
        "reversed, swap the two flags in relationships.json and regenerate.",
    )
    add(
        "setup",
        "Check default statuses on each new Stage attribute",
        "Lists in the left sidebar, then the list, then the Stage attribute settings",
        "Attio does not document whether a new status attribute starts empty (Q6). The API cannot delete a status.",
        "only the stages named in build-sheet.md are active. Archive any extra default status by hand.",
    )

    for pl in design.pipelines:
        order = " then ".join(s.label for s in pl.stages)
        if pl.object == "deal":
            add(
                "pipeline",
                f"Hide the native Deal stage for {pl.name}",
                "Deals object, then the table or board view, then hide the Stage column",
                "Deals require a native stage. The working pipeline is the list `" + pl.key + "`, so the "
                "native stage would show a second, unused set (Q8).",
                "new deals get the first native stage by default and the Deals views use the list's Stage.",
            )
        add(
            "pipeline",
            f"Check the stage order of {pl.name}",
            f"Lists in the left sidebar, then {pl.name}, then Stage attribute settings",
            "The API has no position control for statuses and cannot reorder them. Order follows creation order.",
            f"the stages read: {order}.",
        )
        rows = "; ".join(
            f"{s.label} {s.probability:g}%" for s in pl.stages if s.probability is not None
        )
        add(
            "pipeline",
            f"Stage probability for {pl.name}",
            f"Lists in the left sidebar, then {pl.name}, then set the Probability column on each entry",
            "Attio statuses carry no probability. The list has a Probability number attribute by convention "
            "and nothing fills it in or weights a forecast.",
            f"entries show the probability for their stage ({rows}) and forecast reports multiply by it.",
        )
        won = [s.label for s in pl.stages if s.type == "won"]
        lost = [s.label for s in pl.stages if s.type == "lost"]
        add(
            "pipeline",
            f"Won and lost in {pl.name}",
            f"Reports and dashboards, then filter the list by Stage",
            "Attio has no won or lost flag on a status. They are ordinary statuses, so every report that "
            "needs closed-won or closed-lost must filter on the status title.",
            f"reports filter on Stage is {' or '.join(won)} for won and {' or '.join(lost)} for lost.",
        )
        for s in pl.stages:
            if not s.required_fields:
                continue
            names = ", ".join(_field_label(design, pl.object, k) for k in s.required_fields)
            kind = "lost reason" if s.type == "lost" else "stage gate"
            add(
                "gate",
                f"Stage gate ({kind}): {pl.name}, {s.label}",
                "Workflows in the left sidebar, then Create workflow, trigger: list entry updated on "
                f"{pl.name} where Stage is {s.label}",
                "Attio cannot require fields per stage. is_required is global to an attribute. The "
                "attributes exist and are not required.",
                f"entries entering {s.label} with any of these empty are flagged or sent back: {names}. "
                "A saved view of entries at this stage with the fields empty is an acceptable alternative.",
            )

    required = [f for f in design.fields if f.required and PLATFORM not in f.native and not _is_object_name_field(design, f)]
    for f in required:
        add(
            "setup",
            f"Mark {f.label} on {f.object} as required",
            f"Workspace settings, then Objects, then {f.object}, then Attributes, then {f.label}, then Required",
            "Attributes are created not required. Attio may demand a default for a required attribute, and a "
            "required attribute can break record creation from other tools (Q5).",
            f"{f.label} is required and a test record without it is refused.",
        )

    name_fields = [o for o in custom if design.get_field(o.key, "name") is not None]
    if name_fields:
        add(
            "setup",
            "Confirm the Name attribute on custom objects",
            "Workspace settings, then Objects, then each custom object, then Attributes",
            "A design field called name is not created, because Attio gives a custom object its own name "
            "and the slug would clash. The research did not confirm this by a live test.",
            "each of these objects has a Name attribute: " + ", ".join(o.label for o in name_fields) + ". "
            "If one does not, add a text attribute with slug `name`.",
        )

    renamed = [f for f in design.fields if PLATFORM not in f.native and field_slug(design, f) != f.key
               and not _is_object_name_field(design, f)]
    if renamed:
        add(
            "decision",
            "Renamed attribute slugs",
            "Decide with the client; edit platform_overrides.attio in design.yaml and regenerate",
            "These keys are slugs Attio uses on its own objects, so the slug got an object prefix.",
            "; ".join(f"{f.object}.{f.key} -> {field_slug(design, f)}" for f in renamed) + ". Each is accepted or overridden.",
        )

    # Lossy type mappings the client must decide, only for types this design uses.
    used = {f.type for f in design.fields if PLATFORM not in f.native}
    lossy: list[tuple[str, str, str]] = [
        ("percent", "Percent fields are plain numbers",
         "Decide whether percentages are stored as 0 to 100 or 0 to 1. The generated description says 0 to 100."),
        ("long_text", "Long text is the same type as text",
         "Accept that long text fields look like short text fields in Attio."),
        ("url", "URL fields are plain text",
         "Accept no URL validation. Attio's Domain type drops paths, so it is not used for URLs."),
        ("currency", "Currency fields use GBP",
         "Confirm the account currency. One currency per attribute: change it before data is loaded, because a "
         "later change does not convert values."),
        ("phone", "Phone values must be E.164",
         "Agree that numbers are written with a + and country code, or with a country code field, on import."),
        ("user", "User fields hold workspace members only",
         "Accept that people outside the workspace cannot be chosen."),
        ("datetime", "Date and time fields are stored in UTC",
         "Accept that Attio shows and stores timestamps in UTC."),
        ("checkbox", "Checkbox fields cannot be empty",
         "Accept that unticked and unknown look the same."),
        ("multi_select", "Select options cannot be reordered or deleted",
         "Order follows creation order, so options are sent in design order. Removing one means archiving it."),
    ]
    for ftype, title, decision in lossy:
        if ftype in used:
            names = ", ".join(
                f"{f.object}.{f.key}" for f in design.fields if f.type == ftype and PLATFORM not in f.native
            )
            add("decision", title, "Client decision, written in the client notes",
                "The Attio type does not match the canonical type exactly.", f"{decision} Fields: {names}.")

    for a in design.automations:
        add(
            "automation",
            f"Workflow: {a.name}",
            "Workflows in the left sidebar, then Create workflow",
            "The Attio API has no workflow endpoint.",
            f"a test run matches: trigger '{a.trigger}'; action '{a.action}'",
        )
    for v in design.views:
        obj = design.get_object(v.object)
        label = obj.plural_label if obj else v.object
        add(
            "view",
            f"View: {v.name}",
            f"Open {label} in the left sidebar, then + New view",
            "Views are read-only in the Attio API.",
            f"the view {v.name} is saved with filter '{v.filter}' and sort '{v.sort}'.",
        )
    add(
        "permissions",
        "Set roles and access",
        "Workspace settings, then Members",
        "Attio has no API for workspace roles or object and field access.",
        "a non-admin test member sees and edits what their role needs and nothing more.",
    )
    return steps


GROUP_TITLES: dict[str, str] = {
    "setup": "Before and during the build",
    "pipeline": "Pipelines",
    "gate": "Stage gates and lost reasons",
    "decision": "Decisions where the Attio mapping is lossy",
    "automation": "Workflows",
    "view": "Views",
    "permissions": "Permissions",
}


def render_manual_steps(design: Design) -> str:
    """The manual-steps.md text."""
    steps = manual_steps(design)
    L = [
        f"# Manual steps: {design.name} (attio)",
        "",
        "Generated from `design.yaml`. Do not edit by hand. The Attio API cannot do any of this.",
        "Sources: https://docs.attio.com/llms.txt, https://api.attio.com/openapi/api, "
        "`platforms/attio/reference/api-coverage.md`.",
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


def _dump(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def generate(design: Design, out_dir: Path) -> list[Path]:
    """Write the Attio files for a design into `out_dir` and return the paths written."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, data in build_payloads(design).items():
        path = out_dir / name
        path.write_text(_dump(data), encoding="utf-8")
        written.append(path)
    sheet = render_build_sheet(design, PLATFORM, AttioHooks(design))
    path = out_dir / "build-sheet.md"
    path.write_text(sheet if sheet.endswith("\n") else sheet + "\n", encoding="utf-8")
    written.append(path)
    path = out_dir / "manual-steps.md"
    text = render_manual_steps(design)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    written.append(path)
    return written
