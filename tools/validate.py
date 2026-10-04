"""Validate design files.

    uv run python -m tools.validate blueprints/b2b-saas-sales-led
    uv run python -m tools.validate --all --strict

Exit code 1 on any error, and on any warning with --strict.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

if __name__ == "__main__":  # pragma: no cover - allow `python tools/validate.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.design import (
    CARDINALITIES,
    FIELD_TYPES,
    OVERRIDE_KEYS,
    PLATFORMS,
    REPO_ROOT,
    SNAKE_CASE,
    STAGE_TYPES,
    Design,
    DesignError,
    load_design,
)

MAX_OPEN_STAGES = 8
MIN_DECISIONS = MIN_AUTOMATIONS = MIN_VIEWS = 3
# Words in a Deal stage that suggest delivery work is being tracked on the sales pipeline.
DELIVERY_WORDS = ("delivery", "kickoff", "kick_off", "fulfilment", "fulfillment", "implementation")


@dataclass(frozen=True)
class Issue:
    """One validation finding. `path` is the key path inside the design."""

    severity: str  # "error" or "warning"
    path: str
    message: str

    def format(self, file: str) -> str:
        """Render as `file: severity: path: message`."""
        return f"{file}: {self.severity}: {self.path}: {self.message}"


class _Report:
    def __init__(self) -> None:
        self.issues: list[Issue] = []

    def error(self, path: str, message: str) -> None:
        self.issues.append(Issue("error", path, message))

    def warn(self, path: str, message: str) -> None:
        self.issues.append(Issue("warning", path, message))


def _check_key(report: _Report, path: str, key: str) -> None:
    if not key:
        report.error(path, "key is missing")
    elif not SNAKE_CASE.match(key):
        report.error(path, f"key {key!r} is not snake_case")


def _check_unique(report: _Report, path: str, keys: Iterable[str], what: str) -> None:
    for key, count in Counter(keys).items():
        if key and count > 1:
            report.error(path, f"duplicate {what} key {key!r}")


def _check_objects(d: Design, r: _Report) -> None:
    for o in d.objects:
        p = f"objects[{o.key}]"
        _check_key(r, p, o.key)
        if not o.label:
            r.error(f"{p}.label", "label is missing")
        if not o.description:
            r.error(f"{p}.description", "every object needs a description")
        for platform in o.native_names:
            if platform not in PLATFORMS:
                r.error(f"{p}.native_names.{platform}", f"unknown platform {platform!r}")
    _check_unique(r, "objects", (o.key for o in d.objects), "object")


def _check_fields(d: Design, r: _Report) -> None:
    object_keys = {o.key for o in d.objects}
    for f in d.fields:
        p = f"fields[{f.object}.{f.key}]"
        _check_key(r, p, f.key)
        if f.object not in object_keys:
            r.error(f"{p}.object", f"object {f.object!r} does not exist")
        if not f.label:
            r.error(f"{p}.label", "label is missing")
        if not f.description:
            r.error(f"{p}.description", "every field needs a description")
        if f.type not in FIELD_TYPES:
            r.error(f"{p}.type", f"type {f.type!r} is not one of {', '.join(FIELD_TYPES)}")
        elif f.type in ("select", "multi_select"):
            if not f.options:
                r.error(f"{p}.options", f"{f.type} field needs options")
        elif f.options:
            r.error(f"{p}.options", f"{f.type} field must not have options")
        for o in f.options:
            _check_key(r, f"{p}.options[{o.key}]", o.key)
            if not o.label:
                r.error(f"{p}.options[{o.key}].label", "option label is missing")
        _check_unique(r, f"{p}.options", (o.key for o in f.options), "option")
        for platform in (*f.native, *f.native_names):
            if platform not in PLATFORMS:
                r.error(f"{p}.native", f"unknown platform {platform!r}")
    _check_unique(r, "fields", (f"{f.object}.{f.key}" for f in d.fields), "field")


def _check_relationships(d: Design, r: _Report) -> None:
    object_keys = {o.key for o in d.objects}
    for rel in d.relationships:
        p = f"relationships[{rel.key}]"
        _check_key(r, p, rel.key)
        for side, value in (("from", rel.from_object), ("to", rel.to_object)):
            if value not in object_keys:
                r.error(f"{p}.{side}", f"object {value!r} does not exist")
        if rel.cardinality not in CARDINALITIES:
            r.error(
                f"{p}.cardinality",
                f"cardinality {rel.cardinality!r} is not one of {', '.join(CARDINALITIES)}",
            )
        if not rel.from_label:
            r.error(f"{p}.from_label", "from_label is missing")
        if not rel.to_label:
            r.error(f"{p}.to_label", "to_label is missing")
        if not rel.purpose:
            r.warn(f"{p}.purpose", "say what the relationship is for")
    _check_unique(r, "relationships", (x.key for x in d.relationships), "relationship")


def _check_pipelines(d: Design, r: _Report) -> None:
    object_keys = {o.key for o in d.objects}
    _check_unique(r, "pipelines", (f"{p.object}.{p.key}" for p in d.pipelines), "pipeline")
    for pl in d.pipelines:
        p = f"pipelines[{pl.key}]"
        _check_key(r, p, pl.key)
        if not pl.name:
            r.error(f"{p}.name", "name is missing")
        if pl.object not in object_keys:
            r.error(f"{p}.object", f"object {pl.object!r} does not exist")
        _check_unique(r, f"{p}.stages", (s.key for s in pl.stages), "stage")
        opens = [s for s in pl.stages if s.type == "open"]
        if len(opens) > MAX_OPEN_STAGES:
            r.error(
                f"{p}.stages",
                f"{len(opens)} open stages; the limit is {MAX_OPEN_STAGES}. Merge or move work to delivery.",
            )
        if not any(s.type == "won" for s in pl.stages):
            r.error(f"{p}.stages", "pipeline needs at least one won stage")
        if not any(s.type == "lost" for s in pl.stages):
            r.error(f"{p}.stages", "pipeline needs at least one lost stage")
        for s in pl.stages:
            sp = f"{p}.stages[{s.key}]"
            _check_key(r, sp, s.key)
            if not s.label:
                r.error(f"{sp}.label", "label is missing")
            if s.type not in STAGE_TYPES:
                r.error(f"{sp}.type", f"type {s.type!r} is not one of {', '.join(STAGE_TYPES)}")
            _check_probability(r, sp, s.type, s.probability)
            if not s.exit_criteria.startswith("Entered when"):
                r.error(f"{sp}.exit_criteria", 'exit_criteria must start with "Entered when"')
            fields_on_object = {f.key: f for f in d.fields_of(pl.object)}
            for rf in s.required_fields:
                if rf not in fields_on_object and pl.object in object_keys:
                    r.error(
                        f"{sp}.required_fields",
                        f"field {rf!r} does not exist on object {pl.object!r}",
                    )
            if s.type == "lost":
                reasons = [fields_on_object.get(rf) for rf in s.required_fields]
                if not any(f is not None and f.type == "select" for f in reasons):
                    r.error(
                        f"{sp}.required_fields",
                        "a lost stage must require a reason field that is a select",
                    )


def _check_probability(r: _Report, path: str, stage_type: str, value: float | None) -> None:
    if value is None:
        r.error(f"{path}.probability", "probability is missing or not a number (0 to 100)")
    elif not 0 <= value <= 100:
        r.error(f"{path}.probability", f"probability {value} is outside 0 to 100")
    elif stage_type == "won" and value != 100:
        r.error(f"{path}.probability", "a won stage must have probability 100")
    elif stage_type == "lost" and value != 0:
        r.error(f"{path}.probability", "a lost stage must have probability 0")


def _check_views(d: Design, r: _Report) -> None:
    object_keys = {o.key for o in d.objects}
    for v in d.views:
        p = f"views[{v.key}]"
        _check_key(r, p, v.key)
        if not v.name:
            r.error(f"{p}.name", "name is missing")
        if v.object not in object_keys:
            r.error(f"{p}.object", f"object {v.object!r} does not exist")
    _check_unique(r, "views", (v.key for v in d.views), "view")


def _check_lists(d: Design, r: _Report) -> None:
    for a in d.automations:
        p = f"automations[{a.key}]"
        _check_key(r, p, a.key)
        for part in ("name", "trigger", "action"):
            if not getattr(a, part):
                r.error(f"{p}.{part}", f"{part} is missing")
    _check_unique(r, "automations", (a.key for a in d.automations), "automation")
    for dec in d.decisions:
        p = f"decisions[{dec.key}]"
        _check_key(r, p, dec.key)
        if not dec.question:
            r.error(f"{p}.question", "question is missing")
        if not dec.recommended_default:
            r.error(f"{p}.recommended_default", "every decision needs a recommended default")
    _check_unique(r, "decisions", (x.key for x in d.decisions), "decision")
    for what, items, minimum in (
        ("decisions", d.decisions, MIN_DECISIONS),
        ("automations", d.automations, MIN_AUTOMATIONS),
        ("views", d.views, MIN_VIEWS),
    ):
        if len(items) < minimum:
            r.warn(what, f"{len(items)} {what}; a blueprint should have at least {minimum}")


def _check_overrides(d: Design, r: _Report) -> None:
    for platform, body in d.platform_overrides.items():
        p = f"platform_overrides.{platform}"
        if platform not in OVERRIDE_KEYS:
            r.error(p, f"unknown platform {platform!r}")
            continue
        if not isinstance(body, dict):
            r.error(p, "expected a mapping with objects and/or fields")
            continue
        for section in body:
            if section not in ("objects", "fields"):
                r.error(f"{p}.{section}", "expected 'objects' or 'fields'")
        for target, values in _override_targets(body, "objects"):
            _check_override_values(r, f"{p}.objects.{target}", platform, values)
            if d.get_object(str(target)) is None:
                r.error(f"{p}.objects.{target}", f"object {target!r} does not exist")
        for target, values in _override_targets(body, "fields"):
            _check_override_values(r, f"{p}.fields.{target}", platform, values)
            obj, _, key = str(target).partition(".")
            if not key or d.get_field(obj, key) is None:
                r.error(f"{p}.fields.{target}", f"field {target!r} does not exist (use object.field)")


def _override_targets(body: dict, section: str) -> list[tuple[str, object]]:
    value = body.get(section)
    return list(value.items()) if isinstance(value, dict) else []


def _check_override_values(r: _Report, path: str, platform: str, values: object) -> None:
    if not isinstance(values, dict):
        r.error(path, "expected a mapping")
        return
    allowed = OVERRIDE_KEYS[platform]
    for k, v in values.items():
        if k not in allowed:
            r.error(f"{path}.{k}", f"{platform} allows only: {', '.join(allowed)}")
        elif not isinstance(v, str) or not v:
            r.error(f"{path}.{k}", "expected non-empty text")


def _check_header(d: Design, r: _Report) -> None:
    if not d.name:
        r.error("name", "name is missing")
    if not d.description:
        r.error("description", "description is missing")


def _check_delivery(d: Design, r: _Report) -> None:
    """Principle 8: delivery gets its own object, not stages on the sales pipeline."""
    explained = any(
        "deliver" in f"{dec.key} {dec.question} {dec.recommended_default}".lower()
        for dec in d.decisions
    )
    if explained:
        return
    if not d.custom_objects:
        r.warn(
            "add_objects",
            "no custom object for delivery (principle 8). Add one, or add a decision that "
            "explains how delivery is tracked.",
        )
    for pl in d.pipelines:
        if pl.object != "deal":
            continue
        for s in pl.stages:
            text = f"{s.key} {s.label}".lower().replace(" ", "_")
            if any(w in text for w in DELIVERY_WORDS):
                r.warn(
                    f"pipelines[{pl.key}].stages[{s.key}]",
                    "delivery-type stage on a Deal pipeline (principle 8). Track delivery on its "
                    "own object, or add a decision that explains why not.",
                )


def validate_design(design: Design) -> list[Issue]:
    """Return every error and warning for a loaded design."""
    report = _Report()
    for check in (
        _check_header, _check_objects, _check_fields, _check_relationships, _check_pipelines,
        _check_views, _check_lists, _check_overrides, _check_delivery,
    ):
        check(design, report)
    return report.issues


def validate_file(path: str | Path) -> list[Issue]:
    """Load and validate one design file. A malformed file is reported as one error."""
    try:
        design = load_design(path)
    except DesignError as exc:
        text = str(exc)
        where, _, message = text.partition(": ")
        return [Issue("error", where, message or text)]
    return validate_design(design)


def find_all_designs(root: Path = REPO_ROOT) -> list[Path]:
    """Every blueprints/*/design.yaml under `root`, sorted."""
    return sorted((root / "blueprints").glob("*/design.yaml"))


def _resolve(arg: str) -> Path:
    p = Path(arg)
    return p / "design.yaml" if p.is_dir() else p


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns the exit code."""
    parser = argparse.ArgumentParser(prog="validate", description=__doc__.split("\n")[0])
    parser.add_argument("paths", nargs="*", help="design.yaml files or blueprint directories")
    parser.add_argument("--all", action="store_true", help="validate every blueprints/*/design.yaml")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    args = parser.parse_args(argv)

    files = [_resolve(p) for p in args.paths]
    if args.all:
        files += find_all_designs()
    if not files:
        parser.error("give a path or --all")

    errors = warnings = 0
    for file in files:
        shown = _display(file)
        for issue in validate_file(file):
            print(issue.format(shown))
            if issue.severity == "error":
                errors += 1
            else:
                warnings += 1
    print(f"{len(files)} design(s) checked: {errors} error(s), {warnings} warning(s)")
    return 1 if errors or (args.strict and warnings) else 0


def _display(file: Path) -> str:
    try:
        return str(file.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(file)


if __name__ == "__main__":
    sys.exit(main())
