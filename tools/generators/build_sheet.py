"""Render `build-sheet.md`: a checklist a person can follow in the CRM.

Sections follow the build order: decisions, objects and relationships, pipelines and stage rules,
fields, automations, views, QA and go-live. Every task has a checkbox and a "Done when" line.
Each platform passes a `BuildSheetHooks` subclass for UI paths and manual-step text.
The output is deterministic: no timestamps, stable ordering.
"""

from __future__ import annotations

from tools.design import (
    Automation,
    Design,
    FieldDef,
    ObjectDef,
    Pipeline,
    RelationshipDef,
    Stage,
    View,
)


class BuildSheetHooks:
    """Platform-specific wording for the build sheet. Override what differs."""

    platform_label = "the CRM"

    def object_path(self, obj: ObjectDef) -> str:
        """UI path for creating a custom object."""
        return f"Open {self.platform_label} settings, then objects, then create a new object."

    def relationship_path(self, rel: RelationshipDef) -> str:
        """UI path for creating a relationship."""
        return f"Open the {rel.from_object} object settings, then add a relationship."

    def pipeline_path(self, pipeline: Pipeline) -> str:
        """UI path for creating a pipeline."""
        return f"Open pipeline settings for {pipeline.object}, then create a pipeline."

    def stage_rule(self, pipeline: Pipeline, stage: Stage) -> str:
        """Text describing how to enforce the stage's required fields. Empty if there are none."""
        if not stage.required_fields:
            return ""
        return "Require before entering this stage: " + ", ".join(stage.required_fields) + "."

    def field_path(self, field: FieldDef) -> str:
        """UI path for creating a field."""
        return f"Open the {field.object} object settings, then fields, then add a field."

    def automation_path(self, automation: Automation) -> str:
        """UI path for building an automation."""
        return f"Open the automation builder in {self.platform_label}."

    def view_path(self, view: View) -> str:
        """UI path for saving a view."""
        return f"Open the {view.object} list, apply the filter and sort, then save the view."

    def manual_steps(self) -> list[str]:
        """Platform limits that need a person, shown in the QA section."""
        return []


def _task(lines: list[str], title: str, path: str, done_when: str, *, extra: list[str] | None = None) -> None:
    lines.append(f"- [ ] **{title}**")
    if path:
        lines.append(f"  - Where: {path}")
    for e in extra or []:
        lines.append(f"  - {e}")
    lines.append(f"  - Done when: {done_when}")


def render_build_sheet(design: Design, platform: str, hooks: BuildSheetHooks) -> str:
    """Return the build sheet as Markdown for one platform."""
    L: list[str] = []
    L.append(f"# Build sheet: {design.name} ({platform})")
    L.append("")
    L.append(design.description)
    L.append("")
    L.append(
        "Generated from `design.yaml`. Do not edit by hand: change the design and regenerate. "
        "Work top to bottom. Build in a sandbox first."
    )
    L.append("")

    L.append("## 1. Decisions")
    L.append("")
    for d in design.decisions:
        _task(
            L,
            f"Decide: {d.question}",
            "",
            "the answer is written in the client notes, and `design.yaml` is changed if it differs from the default.",
            extra=[f"Recommended default: {d.recommended_default}"],
        )
    if not design.decisions:
        L.append("No open decisions.")
    L.append("")

    L.append("## 2. Objects and relationships")
    L.append("")
    for o in design.objects:
        if o.kind == "core":
            native = o.native_names.get(platform, o.label)
            _task(L, f"Confirm standard object {o.label} (`{native}`) is enabled", "",
                  f"{o.label} records can be created and listed.")
        else:
            _task(L, f"Create object {o.label}", hooks.object_path(o),
                  f"the object {o.label} exists with plural name {o.plural_label}.",
                  extra=[f"Purpose: {o.description}"])
    for rel in design.relationships:
        if platform in rel.native:
            continue
        _task(
            L,
            f"Create relationship {rel.from_object} to {rel.to_object} ({rel.cardinality})",
            hooks.relationship_path(rel),
            f"a {rel.from_object} record shows the link as '{rel.from_label}' and a "
            f"{rel.to_object} record shows it as '{rel.to_label}'.",
            extra=[f"Purpose: {rel.purpose}"] if rel.purpose else None,
        )
    L.append("")

    L.append("## 3. Pipelines and stage rules")
    L.append("")
    for pl in design.pipelines:
        _task(L, f"Create pipeline {pl.name} on {pl.object}", hooks.pipeline_path(pl),
              f"the pipeline {pl.name} exists with {len(pl.stages)} stages in the order below.")
        for i, s in enumerate(pl.stages, 1):
            extra = [f"Type: {s.type}. Probability: {_pct(s.probability)}.", s.exit_criteria]
            rule = hooks.stage_rule(pl, s)
            if rule:
                extra.append(rule)
            _task(L, f"Stage {i}: {s.label}", "", f"the stage {s.label} is in position {i} and its rule is in place.",
                  extra=extra)
    if not design.pipelines:
        L.append("No pipelines.")
    L.append("")

    L.append("## 4. Fields")
    L.append("")
    for o in design.objects:
        fields = design.fields_of(o.key)
        custom = [f for f in fields if platform not in f.native]
        native = [f for f in fields if platform in f.native]
        if not fields:
            continue
        L.append(f"### {o.label}")
        L.append("")
        for f in custom:
            extra = [f"Purpose: {f.description}"]
            if f.options:
                extra.append("Options: " + ", ".join(opt.label for opt in f.options))
            _task(L, f"Create field {f.label} ({f.type}{', required' if f.required else ''})",
                  hooks.field_path(f), f"{o.label} records show {f.label} and it accepts the right values.",
                  extra=extra)
        for f in native:
            name = f.native_names.get(platform, f.key)
            _task(L, f"Confirm standard field {f.label} (`{name}`) exists", "",
                  f"{f.label} is visible on {o.label} records.")
        L.append("")

    L.append("## 5. Automations")
    L.append("")
    for a in design.automations:
        _task(L, a.name, hooks.automation_path(a),
              f"the automation runs on a test record and the result matches: {a.action}",
              extra=[f"Trigger: {a.trigger}", f"Action: {a.action}"])
    if not design.automations:
        L.append("No automations.")
    L.append("")

    L.append("## 6. Views")
    L.append("")
    for v in design.views:
        _task(L, v.name, hooks.view_path(v), f"the view {v.name} is saved and shows the expected records.",
              extra=[f"Object: {v.object}", f"Filter: {v.filter}", f"Sort: {v.sort}"])
    if not design.views:
        L.append("No views.")
    L.append("")

    L.append("## 7. QA and go-live")
    L.append("")
    _task(L, "Create a test record of each custom object and move a test deal through every stage", "",
          "each stage's required fields block entry when empty, and a lost deal needs a reason.")
    _task(L, "Check the relationships from both sides", "",
          "a linked record shows on both records with the right labels.")
    _task(L, "Run every automation once on test data", "", "each one fires once and does nothing else.")
    _task(L, "Check permissions with a non-admin test user", "",
          "the user can see and edit what their role needs and nothing more.")
    _task(L, "Import a small sample and check for duplicates", "",
          "one person has one record, matched by email, and companies are matched by domain.")
    for text in hooks.manual_steps():
        _task(L, f"Manual step: {text}", "", "a person has done it and written down who and when.")
    _task(L, "Delete test records and sign off", "",
          "the client has approved the build and the sign-off tag is on the design in git.")
    L.append("")
    return "\n".join(L)


def _pct(value: float | None) -> str:
    if value is None:
        return "not set"
    return f"{value:g}%"
