"""Load a design file into frozen dataclasses.

`load_design(path)` reads a `design.yaml`, resolves `extends` against `model/core-model.yaml`,
merges `add_objects`, `add_fields` and `add_relationships`, and returns a `Design`.
Every other module works from `Design`, never from raw YAML.

The loader checks shape only: unknown keys, wrong container types, and clashes with the core model.
Meaning (valid types, references, counts) is checked by `tools.validate`.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import yaml

if __name__ == "__main__":  # pragma: no cover - allow `python tools/design.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

REPO_ROOT = Path(__file__).resolve().parent.parent
CORE_MODEL_PATH = REPO_ROOT / "model" / "core-model.yaml"

PLATFORMS: tuple[str, ...] = ("attio", "hubspot", "salesforce")
FIELD_TYPES: tuple[str, ...] = (
    "text",
    "long_text",
    "select",
    "multi_select",
    "number",
    "currency",
    "percent",
    "date",
    "datetime",
    "checkbox",
    "url",
    "email",
    "phone",
    "user",
)
CARDINALITIES: tuple[str, ...] = ("one_to_one", "one_to_many", "many_to_one", "many_to_many")
STAGE_TYPES: tuple[str, ...] = ("open", "won", "lost")
OBJECT_KINDS: tuple[str, ...] = ("core", "custom")
# Allowed keys inside platform_overrides, per platform. They apply to an object or a field.
OVERRIDE_KEYS: dict[str, tuple[str, ...]] = {
    "hubspot": ("property_group", "object_type_id"),
    "salesforce": ("record_type", "api_name"),
    "attio": ("api_slug",),
}

SNAKE_CASE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")


class DesignError(ValueError):
    """A design file is malformed. The message starts with the key path."""


@dataclass(frozen=True)
class Option:
    """One choice of a select or multi_select field."""

    key: str
    label: str


@dataclass(frozen=True)
class ObjectDef:
    """An object. `kind` is `core` (company, person, deal) or `custom`."""

    key: str
    label: str
    plural_label: str
    description: str
    kind: str
    native_names: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class FieldDef:
    """A field on an object. `native` lists platforms where it exists out of the box."""

    object: str
    key: str
    label: str
    type: str
    description: str
    options: tuple[Option, ...] = ()
    required: bool = False
    native: tuple[str, ...] = ()
    native_names: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RelationshipDef:
    """A link between two objects.

    `cardinality` reads from `from_object` to `to_object`: many_to_one means many `from` records
    link to one `to` record. `from_label` is the name shown on the `from` record; `to_label` is the
    name shown on the `to` record. `native` lists platforms where the link exists out of the box.
    """

    key: str
    from_object: str
    to_object: str
    cardinality: str
    from_label: str
    to_label: str
    purpose: str
    native: tuple[str, ...] = ()


@dataclass(frozen=True)
class Stage:
    """A pipeline stage."""

    key: str
    label: str
    type: str
    probability: float | None
    exit_criteria: str
    required_fields: tuple[str, ...] = ()


@dataclass(frozen=True)
class Pipeline:
    """A pipeline on an object, with ordered stages."""

    object: str
    key: str
    name: str
    stages: tuple[Stage, ...] = ()


@dataclass(frozen=True)
class Decision:
    """An open question with a recommended default."""

    key: str
    question: str
    recommended_default: str


@dataclass(frozen=True)
class Automation:
    """An automation described as trigger and action."""

    key: str
    name: str
    trigger: str
    action: str


@dataclass(frozen=True)
class View:
    """A saved view."""

    key: str
    name: str
    object: str
    filter: str
    sort: str


@dataclass(frozen=True)
class Design:
    """A merged design: core model plus the design's additions."""

    name: str
    description: str
    objects: tuple[ObjectDef, ...]
    fields: tuple[FieldDef, ...]
    relationships: tuple[RelationshipDef, ...]
    pipelines: tuple[Pipeline, ...]
    decisions: tuple[Decision, ...]
    automations: tuple[Automation, ...]
    views: tuple[View, ...]
    platform_overrides: dict[str, Any] = field(default_factory=dict)
    source_path: Path | None = None

    def get_object(self, key: str) -> ObjectDef | None:
        """Return the object with this key, or None."""
        return next((o for o in self.objects if o.key == key), None)

    def fields_of(self, object_key: str) -> tuple[FieldDef, ...]:
        """Return the fields of one object in declared order."""
        return tuple(f for f in self.fields if f.object == object_key)

    def get_field(self, object_key: str, key: str) -> FieldDef | None:
        """Return one field, or None."""
        return next((f for f in self.fields if f.object == object_key and f.key == key), None)

    def get_pipeline(self, object_key: str, key: str) -> Pipeline | None:
        """Return one pipeline, or None."""
        return next((p for p in self.pipelines if p.object == object_key and p.key == key), None)

    @property
    def custom_objects(self) -> tuple[ObjectDef, ...]:
        """Objects added by the design."""
        return tuple(o for o in self.objects if o.kind == "custom")


# --- parsing helpers -------------------------------------------------------------------------


def _map(value: Any, path: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise DesignError(f"{path}: expected a mapping, got {type(value).__name__}")
    return value


def _list(value: Any, path: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise DesignError(f"{path}: expected a list, got {type(value).__name__}")
    return value


def _check_keys(data: dict[str, Any], allowed: Iterable[str], path: str) -> None:
    allowed_set = set(allowed)
    for key in data:
        if key not in allowed_set:
            raise DesignError(
                f"{path}.{key}: unknown key (allowed: {', '.join(sorted(allowed_set))})"
            )


def _text(data: dict[str, Any], key: str, path: str, default: str = "") -> str:
    value = data.get(key)
    if value is None:
        return default
    if not isinstance(value, str):
        raise DesignError(f"{path}.{key}: expected text, got {type(value).__name__}")
    return value.strip()


def _bool(data: dict[str, Any], key: str, path: str) -> bool:
    value = data.get(key, False)
    if not isinstance(value, bool):
        raise DesignError(f"{path}.{key}: expected true or false")
    return value


def _str_tuple(value: Any, path: str) -> tuple[str, ...]:
    items = _list(value, path)
    for i, item in enumerate(items):
        if not isinstance(item, str):
            raise DesignError(f"{path}[{i}]: expected text")
    return tuple(items)


def _str_map(value: Any, path: str) -> dict[str, str]:
    data = _map(value, path)
    for k, v in data.items():
        if not isinstance(v, str):
            raise DesignError(f"{path}.{k}: expected text")
    return dict(data)


def _label_from_key(key: str) -> str:
    """Sentence-case label from a snake_case key: `mid_market` becomes `Mid market`."""
    words = key.replace("_", " ").strip()
    return words[:1].upper() + words[1:]


def _parse_options(value: Any, path: str) -> tuple[Option, ...]:
    """Options may be a mapping key->label, a list of keys, or a list of {key, label}."""
    if value is None:
        return ()
    if isinstance(value, dict):
        out = []
        for k, v in value.items():
            if not isinstance(k, str) or not isinstance(v, str):
                raise DesignError(f"{path}.{k}: option key and label must be text")
            out.append(Option(k, v))
        return tuple(out)
    out = []
    for i, item in enumerate(_list(value, path)):
        if isinstance(item, str):
            out.append(Option(item, _label_from_key(item)))
        elif isinstance(item, dict):
            _check_keys(item, ("key", "label"), f"{path}[{i}]")
            key = _text(item, "key", f"{path}[{i}]")
            out.append(Option(key, _text(item, "label", f"{path}[{i}]") or _label_from_key(key)))
        else:
            raise DesignError(f"{path}[{i}]: expected a key or a {{key, label}} mapping")
    return tuple(out)


_OBJECT_KEYS = ("key", "label", "plural_label", "description", "native_names")
_FIELD_KEYS = (
    "object", "key", "label", "type", "description", "options", "required", "native", "native_names",
)
_REL_KEYS = (
    "key", "from", "to", "cardinality", "from_label", "to_label", "purpose", "native",
)
_STAGE_KEYS = ("key", "label", "type", "probability", "exit_criteria", "required_fields")
_PIPELINE_KEYS = ("object", "key", "name", "stages")


def _parse_object(raw: Any, path: str, kind: str) -> ObjectDef:
    data = _map(raw, path)
    _check_keys(data, _OBJECT_KEYS, path)
    key = _text(data, "key", path)
    label = _text(data, "label", path)
    return ObjectDef(
        key=key,
        label=label,
        plural_label=_text(data, "plural_label", path) or (label + "s" if label else ""),
        description=_text(data, "description", path),
        kind=kind,
        native_names=_str_map(data.get("native_names"), f"{path}.native_names"),
    )


def _parse_field(raw: Any, path: str) -> FieldDef:
    data = _map(raw, path)
    _check_keys(data, _FIELD_KEYS, path)
    key = _text(data, "key", path)
    return FieldDef(
        object=_text(data, "object", path),
        key=key,
        label=_text(data, "label", path) or _label_from_key(key),
        type=_text(data, "type", path),
        description=_text(data, "description", path),
        options=_parse_options(data.get("options"), f"{path}.options"),
        required=_bool(data, "required", path),
        native=_str_tuple(data.get("native"), f"{path}.native"),
        native_names=_str_map(data.get("native_names"), f"{path}.native_names"),
    )


def _parse_relationship(raw: Any, path: str) -> RelationshipDef:
    data = _map(raw, path)
    _check_keys(data, _REL_KEYS, path)
    return RelationshipDef(
        key=_text(data, "key", path),
        from_object=_text(data, "from", path),
        to_object=_text(data, "to", path),
        cardinality=_text(data, "cardinality", path),
        from_label=_text(data, "from_label", path),
        to_label=_text(data, "to_label", path),
        purpose=_text(data, "purpose", path),
        native=_str_tuple(data.get("native"), f"{path}.native"),
    )


def _parse_probability(data: dict[str, Any], path: str) -> float | None:
    value = data.get("probability")
    if value is None or isinstance(value, bool) or not isinstance(value, (int, float)):
        return None  # the validator reports it; a non-number is not a shape error
    return value


def _parse_stage(raw: Any, path: str) -> Stage:
    data = _map(raw, path)
    _check_keys(data, _STAGE_KEYS, path)
    return Stage(
        key=_text(data, "key", path),
        label=_text(data, "label", path),
        type=_text(data, "type", path),
        probability=_parse_probability(data, path),
        exit_criteria=_text(data, "exit_criteria", path),
        required_fields=_str_tuple(data.get("required_fields"), f"{path}.required_fields"),
    )


def _parse_pipeline(raw: Any, path: str) -> Pipeline:
    data = _map(raw, path)
    _check_keys(data, _PIPELINE_KEYS, path)
    stages = tuple(
        _parse_stage(s, f"{path}.stages[{i}]")
        for i, s in enumerate(_list(data.get("stages"), f"{path}.stages"))
    )
    return Pipeline(
        object=_text(data, "object", path),
        key=_text(data, "key", path),
        name=_text(data, "name", path),
        stages=stages,
    )


def _simple_list(raw: Any, path: str, keys: tuple[str, ...], build: Any) -> tuple[Any, ...]:
    out = []
    for i, item in enumerate(_list(raw, path)):
        data = _map(item, f"{path}[{i}]")
        _check_keys(data, keys, f"{path}[{i}]")
        out.append(build({k: _text(data, k, f"{path}[{i}]") for k in keys}))
    return tuple(out)


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise DesignError(f"{path}: cannot read file ({exc.strerror})") from exc
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise DesignError(f"{path}: invalid YAML ({exc})") from exc
    return _map(data, str(path))


@dataclass(frozen=True)
class _Core:
    objects: tuple[ObjectDef, ...]
    fields: tuple[FieldDef, ...]
    relationships: tuple[RelationshipDef, ...]


def load_core_model(path: Path = CORE_MODEL_PATH) -> _Core:
    """Load the core model: company, person, deal and their native fields and links."""
    data = _read_yaml(path)
    _check_keys(data, ("name", "description", "objects", "fields", "relationships"), "core")
    return _Core(
        objects=tuple(
            _parse_object(o, f"core.objects[{i}]", "core")
            for i, o in enumerate(_list(data.get("objects"), "core.objects"))
        ),
        fields=tuple(
            _parse_field(f, f"core.fields[{i}]")
            for i, f in enumerate(_list(data.get("fields"), "core.fields"))
        ),
        relationships=tuple(
            _parse_relationship(r, f"core.relationships[{i}]")
            for i, r in enumerate(_list(data.get("relationships"), "core.relationships"))
        ),
    )


_TOP_KEYS = (
    "extends", "name", "description", "add_objects", "add_fields", "add_relationships",
    "pipelines", "decisions", "automations", "views", "platform_overrides",
)


def load_design(path: str | Path, core_path: Path = CORE_MODEL_PATH) -> Design:
    """Load and merge a design file.

    `path` may be a design.yaml or a blueprint directory containing one. Raises `DesignError`
    for a malformed file, for an add_objects entry that reuses a core object key, and for an
    add_fields entry that redefines a core field (core fields cannot be overridden).
    """
    file = Path(path)
    if file.is_dir():
        file = file / "design.yaml"
    data = _read_yaml(file)
    _check_keys(data, _TOP_KEYS, "design")
    extends = _text(data, "extends", "design", "core")
    if extends != "core":
        raise DesignError(f"design.extends: only 'core' is supported, got {extends!r}")

    core = load_core_model(core_path)
    core_object_keys = {o.key for o in core.objects}
    core_field_ids = {(f.object, f.key) for f in core.fields}

    added_objects = []
    for i, raw in enumerate(_list(data.get("add_objects"), "design.add_objects")):
        obj = _parse_object(raw, f"design.add_objects[{i}]", "custom")
        if obj.key in core_object_keys:
            raise DesignError(
                f"design.add_objects[{i}].key: {obj.key!r} is a core object and cannot be redefined"
            )
        added_objects.append(obj)

    added_fields = []
    for i, raw in enumerate(_list(data.get("add_fields"), "design.add_fields")):
        fld = _parse_field(raw, f"design.add_fields[{i}]")
        if (fld.object, fld.key) in core_field_ids:
            raise DesignError(
                f"design.add_fields[{i}]: {fld.object}.{fld.key} is a core field; "
                "core fields cannot be overridden"
            )
        added_fields.append(fld)

    added_rels = tuple(
        _parse_relationship(r, f"design.add_relationships[{i}]")
        for i, r in enumerate(_list(data.get("add_relationships"), "design.add_relationships"))
    )
    pipelines = tuple(
        _parse_pipeline(p, f"design.pipelines[{i}]")
        for i, p in enumerate(_list(data.get("pipelines"), "design.pipelines"))
    )
    decisions = _simple_list(
        data.get("decisions"), "design.decisions", ("key", "question", "recommended_default"),
        lambda d: Decision(d["key"], d["question"], d["recommended_default"]),
    )
    automations = _simple_list(
        data.get("automations"), "design.automations", ("key", "name", "trigger", "action"),
        lambda d: Automation(d["key"], d["name"], d["trigger"], d["action"]),
    )
    views = _simple_list(
        data.get("views"), "design.views", ("key", "name", "object", "filter", "sort"),
        lambda d: View(d["key"], d["name"], d["object"], d["filter"], d["sort"]),
    )
    return Design(
        name=_text(data, "name", "design"),
        description=_text(data, "description", "design"),
        objects=core.objects + tuple(added_objects),
        fields=core.fields + tuple(added_fields),
        relationships=core.relationships + added_rels,
        pipelines=pipelines,
        decisions=decisions,
        automations=automations,
        views=views,
        platform_overrides=_map(data.get("platform_overrides"), "design.platform_overrides"),
        source_path=file,
    )
