"""Platform-neutral diff of a Design against a State.

The planner owns the safety rules about *what* may change:

- Adding an object, field, option, stage, relationship or pipeline is `safe`.
- Renaming, reordering stages, changing a stage's type or probability, and removing an option or
  stage are `needs_review`. Adapters must archive or hide on removal, never delete.
- Removing a field, object, relationship or pipeline is never a Change. It becomes a destructive
  ManualStep with data-migration instructions.
- Changing a field's type, or a relationship's cardinality, is never a Change. It becomes a
  destructive ManualStep describing a migration to a new field.
- When the state already matches the design the plan is empty.

Adapters pass a `payload_builder` callback that turns a change into an API payload, and optional
maps of source URLs and UI paths. Changes are ordered by the build order: objects, relationships,
pipelines, fields. Automations and views are not in `State`, so adapters add them as manual steps.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping, Sequence

from tools.crm.base import (
    Change,
    ManualStep,
    Plan,
    State,
    StateField,
    StatePipeline,
)
from tools.design import Design, FieldDef, ObjectDef, Pipeline, RelationshipDef, Stage

# payload_builder(kind, target, context) -> payload dict. `context` holds the design records the
# change is about, under keys such as "object", "field", "relationship", "pipeline", "stage".
PayloadBuilder = Callable[[str, str, dict[str, Any]], dict[str, Any]]

RISK_BY_KIND: dict[str, str] = {
    "add_object": "safe",
    "add_relationship": "safe",
    "add_pipeline": "safe",
    "add_stage": "safe",
    "add_field": "safe",
    "add_option": "safe",
    "rename_object": "needs_review",
    "rename_field": "needs_review",
    "rename_option": "needs_review",
    "rename_stage": "needs_review",
    "update_stage": "needs_review",
    "reorder_stages": "needs_review",
    "remove_option": "needs_review",
    "remove_stage": "needs_review",
}

# Build order: objects, relationships, pipelines, fields.
BUILD_RANK: dict[str, int] = {
    "add_object": 0,
    "rename_object": 0,
    "add_relationship": 1,
    "add_pipeline": 2,
    "add_stage": 2,
    "rename_stage": 2,
    "update_stage": 2,
    "reorder_stages": 2,
    "remove_stage": 2,
    "add_field": 3,
    "add_option": 3,
    "rename_field": 3,
    "rename_option": 3,
    "remove_option": 3,
}

MIGRATION_HINT = (
    "Export the data first. Never delete before the data is safe elsewhere."
)


class _Builder:
    def __init__(
        self,
        design: Design,
        state: State,
        payload_builder: PayloadBuilder,
        source_urls: Mapping[str, str],
        ui_paths: Mapping[str, str],
    ) -> None:
        self.design = design
        self.state = state
        self.payload_builder = payload_builder
        self.source_urls = source_urls
        self.ui_paths = ui_paths
        self.platform = state.platform
        self.changes: list[Change] = []
        self.manual: list[ManualStep] = []

    # -- records ---------------------------------------------------------------------------

    def change(self, kind: str, target: str, summary: str, **context: Any) -> None:
        payload = self.payload_builder(kind, target, {"design": self.design, **context})
        self.changes.append(
            Change(
                kind=kind,
                target=target,
                payload=payload,
                risk=RISK_BY_KIND[kind],
                source_url=self.source_urls.get(kind, ""),
                summary=summary,
            )
        )

    def step(self, kind: str, title: str, reason: str, done_when: str, instructions: str) -> None:
        self.manual.append(
            ManualStep(
                title=title,
                reason=reason,
                ui_path=self.ui_paths.get(kind, "Open the object's settings in the CRM admin area."),
                done_when=done_when,
                risk="destructive",
                instructions=instructions,
            )
        )

    # -- objects ---------------------------------------------------------------------------

    def objects(self) -> None:
        live = {o.key: o for o in self.state.objects}
        for obj in self.design.objects:
            if obj.kind == "core":
                continue
            found = live.get(obj.key)
            if found is None:
                self.change("add_object", obj.key, f"Add object {obj.label}", object=obj)
            elif found.label and found.label != obj.label:
                self.change(
                    "rename_object", obj.key,
                    f"Rename object {found.label!r} to {obj.label!r}", object=obj,
                )
        design_keys = {o.key for o in self.design.objects}
        for key, found in live.items():
            if key not in design_keys and not found.native:
                self.step(
                    "remove_object",
                    f"Remove object {key}",
                    "The design no longer contains this object. This tool never deletes objects.",
                    f"The records are migrated or exported, the object {key} is archived or "
                    "deleted in the CRM, and re-planning shows no difference.",
                    f"1. Export every record of {key}. 2. Decide where the data goes and move it. "
                    f"3. Remove or archive {key} views, automations and integrations. "
                    f"4. Delete or archive the object. {MIGRATION_HINT}",
                )

    # -- relationships ---------------------------------------------------------------------

    def _match_relationship(self, rel: RelationshipDef) -> Any:
        by_key = {r.key: r for r in self.state.relationships}
        if rel.key in by_key:
            return by_key[rel.key]
        if self.platform in rel.native:
            for r in self.state.relationships:
                if (r.from_object, r.to_object) == (rel.from_object, rel.to_object):
                    return r
        return None

    def relationships(self) -> None:
        matched: set[str] = set()
        for rel in self.design.relationships:
            found = self._match_relationship(rel)
            if found is None:
                if self.platform in rel.native:
                    continue  # native by definition
                self.change(
                    "add_relationship", rel.key,
                    f"Add relationship {rel.from_object} to {rel.to_object} ({rel.cardinality})",
                    relationship=rel,
                )
                continue
            matched.add(found.key)
            if found.cardinality != rel.cardinality:
                self.step(
                    "change_relationship",
                    f"Change cardinality of relationship {rel.key}",
                    f"Live is {found.cardinality}; the design says {rel.cardinality}. "
                    "Cardinality is never changed in place.",
                    f"Relationship {rel.key} is {rel.cardinality} in the CRM and re-planning "
                    "shows no difference.",
                    f"1. Create a new relationship {rel.key}_new with the design's cardinality. "
                    "2. Copy the links across. 3. Repoint views and automations. "
                    f"4. Archive the old relationship. {MIGRATION_HINT}",
                )
        for r in self.state.relationships:
            if r.key not in matched and not r.native:
                self.step(
                    "remove_relationship",
                    f"Remove relationship {r.key}",
                    "The design no longer contains this relationship. This tool never deletes relationships.",
                    f"The links are exported, the relationship {r.key} is removed in the CRM, and "
                    "re-planning shows no difference.",
                    f"1. Export the links between {r.from_object} and {r.to_object}. "
                    f"2. Remove the relationship from views and automations. 3. Delete or archive it. "
                    f"{MIGRATION_HINT}",
                )

    # -- pipelines -------------------------------------------------------------------------

    def pipelines(self) -> None:
        live = {(p.object, p.key): p for p in self.state.pipelines}
        for pl in self.design.pipelines:
            found = live.get((pl.object, pl.key))
            target = f"{pl.object}.{pl.key}"
            if found is None:
                self.change(
                    "add_pipeline", target,
                    f"Add pipeline {pl.name} on {pl.object} with {len(pl.stages)} stages",
                    pipeline=pl,
                )
            else:
                self._stages(pl, found)
        design_ids = {(p.object, p.key) for p in self.design.pipelines}
        for (obj, key), found in live.items():
            if (obj, key) not in design_ids:
                self.step(
                    "remove_pipeline",
                    f"Remove pipeline {obj}.{key}",
                    "The design no longer contains this pipeline. This tool never deletes pipelines.",
                    f"Records are moved to another pipeline, pipeline {key} is archived in the "
                    "CRM, and re-planning shows no difference.",
                    f"1. Export the records in pipeline {key}. 2. Move open records to the "
                    f"replacement pipeline and map each stage. 3. Archive the pipeline. {MIGRATION_HINT}",
                )

    def _stages(self, pl: Pipeline, live: StatePipeline) -> None:
        target = f"{pl.object}.{pl.key}"
        live_by_key = {s.key: s for s in live.stages}
        design_keys = [s.key for s in pl.stages]
        for stage in pl.stages:
            found = live_by_key.get(stage.key)
            st = f"{target}.{stage.key}"
            if found is None:
                self.change(
                    "add_stage", st, f"Add stage {stage.label} to {pl.name}",
                    pipeline=pl, stage=stage,
                )
                continue
            if found.label and found.label != stage.label:
                self.change(
                    "rename_stage", st, f"Rename stage {found.label!r} to {stage.label!r}",
                    pipeline=pl, stage=stage,
                )
            if _stage_differs(found.type, found.probability, stage):
                self.change(
                    "update_stage", st,
                    f"Change stage {stage.label} to type {stage.type}, probability {stage.probability}",
                    pipeline=pl, stage=stage,
                )
        for key, found in live_by_key.items():
            if key not in design_keys:
                self.change(
                    "remove_stage", f"{target}.{key}",
                    f"Remove stage {found.label or key} from {pl.name}. Archive it; do not delete.",
                    pipeline=pl, live_stage=found,
                )
        common_live = [s.key for s in live.stages if s.key in design_keys]
        common_design = [k for k in design_keys if k in live_by_key]
        if common_live != common_design:
            self.change(
                "reorder_stages", target,
                f"Reorder stages of {pl.name} to {', '.join(design_keys)}", pipeline=pl,
            )

    # -- fields ----------------------------------------------------------------------------

    def fields(self) -> None:
        live = {(f.object, f.key): f for f in self.state.fields}
        object_keys = {o.key for o in self.design.objects}
        for fld in self.design.fields:
            found = live.get((fld.object, fld.key))
            target = f"{fld.object}.{fld.key}"
            if found is None:
                if self.platform in fld.native:
                    continue  # native by definition
                self.change("add_field", target, f"Add {fld.type} field {fld.label} to {fld.object}", field=fld)
                continue
            self._existing_field(fld, found, target)
        design_ids = {(f.object, f.key) for f in self.design.fields}
        for (obj, key), found in live.items():
            if (obj, key) in design_ids or found.native or obj not in object_keys:
                continue
            self.step(
                "remove_field",
                f"Remove field {obj}.{key}",
                "The design no longer contains this field. This tool never deletes fields.",
                f"The data in {obj}.{key} is migrated or exported, the field is archived or "
                "deleted in the CRM, and re-planning shows no difference.",
                f"1. Export {obj}.{key} with the record id. 2. Decide whether the data moves to "
                f"another field or is retired. 3. Remove it from views, forms and automations. "
                f"4. Archive or delete the field. {MIGRATION_HINT}",
            )

    def _existing_field(self, fld: FieldDef, found: StateField, target: str) -> None:
        if found.type != fld.type:
            self.step(
                "change_field_type",
                f"Change type of {target} from {found.type} to {fld.type}",
                "Field types are never changed in place; the data may not convert.",
                f"{target} has type {fld.type} in the CRM, existing data is checked, and "
                "re-planning shows no difference.",
                f"1. Create a new field {fld.key}_new of type {fld.type}. 2. Copy values across "
                "with an export/import or a script, mapping any values that do not convert. "
                f"3. Repoint views, automations and integrations. 4. Archive the old field and "
                f"rename the new one. {MIGRATION_HINT}",
            )
            return
        if found.label and found.label != fld.label:
            self.change("rename_field", target, f"Rename field {found.label!r} to {fld.label!r}", field=fld)
        if fld.type in ("select", "multi_select"):
            live_opts = dict(found.options)
            for opt in fld.options:
                if opt.key not in live_opts:
                    self.change(
                        "add_option", f"{target}.{opt.key}", f"Add option {opt.label} to {target}",
                        field=fld, option=opt,
                    )
                elif live_opts[opt.key] and live_opts[opt.key] != opt.label:
                    self.change(
                        "rename_option", f"{target}.{opt.key}",
                        f"Rename option {live_opts[opt.key]!r} to {opt.label!r} on {target}",
                        field=fld, option=opt,
                    )
            design_opts = {o.key for o in fld.options}
            for key, label in found.options:
                if key not in design_opts:
                    self.change(
                        "remove_option", f"{target}.{key}",
                        f"Remove option {label or key} from {target}. Archive it; do not delete.",
                        field=fld, live_option=(key, label),
                    )


def _stage_differs(live_type: str, live_probability: float | None, stage: Stage) -> bool:
    if live_type != stage.type:
        return True
    return live_probability is not None and live_probability != stage.probability


def plan_changes(
    design: Design,
    state: State,
    payload_builder: PayloadBuilder,
    *,
    target: str = "",
    source_urls: Mapping[str, str] | None = None,
    ui_paths: Mapping[str, str] | None = None,
    extra_manual_steps: Sequence[ManualStep] = (),
) -> Plan:
    """Diff `design` against `state` and return an ordered `Plan`.

    `payload_builder(kind, target, context)` returns the API payload for a change.
    `source_urls` maps a change kind to the documentation URL it relies on. `ui_paths` maps a
    manual-step kind (`remove_field`, `change_field_type`, `remove_object`, `remove_relationship`,
    `change_relationship`, `remove_pipeline`) to the platform's UI path.
    `extra_manual_steps` are appended after the planner's own, for example automations and views.
    """
    b = _Builder(design, state, payload_builder, source_urls or {}, ui_paths or {})
    # Build order: the four passes run in this order, so changes come out ordered.
    b.objects()
    b.relationships()
    b.pipelines()
    b.fields()
    return Plan(
        platform=state.platform,
        target=target,
        changes=tuple(b.changes),
        manual_steps=tuple(b.manual) + tuple(extra_manual_steps),
    )
