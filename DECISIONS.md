# Decisions

Judgement calls made while building this repository, newest last. Each says what was decided, why, and
what would change it. `BRIEF.md` is the brief; where this file and the brief disagree, this file records why.

## D-1. Python 3.12 through uv (2026-10-04)

The brief asks for Python 3.10+. The build machine's system Python is 3.9, so the project pins 3.12 with
`uv` (`pyproject.toml`, `.python-version`). Every command runs as `uv run …`. CI uses `astral-sh/setup-uv`.
Dependencies stay as the brief lists: `pyyaml`, `requests`, `pytest`.

## D-2. No `sf` CLI on the build machine (2026-10-04)

The Salesforce adapter shells out to `sf`. It is not installed where this was built, so Salesforce deploy and
retrieve are tested by stubbing the subprocess call with recorded output taken from documented examples. The
live smoke test skips unless `sf` is on `PATH` and an org alias is set.

## D-3. Shared contracts (2026-10-04)

These are fixed before parallel work starts so separately built parts fit. Change them only by editing this
section first.

### Layout and running

- `tools/` is a Python package (`tools/__init__.py`). Modules import as `tools.design`, `tools.validate`,
  `tools.generators.attio`, `tools.crm.base`, and so on.
- Every CLI script in `tools/` runs both ways: `uv run python -m tools.validate …` and
  `uv run python tools/validate.py …` (scripts add the repo root to `sys.path` when run directly).
- Tests: `uv run pytest`. No network by default. Live tests are marked `live` and skip without credentials.

### The design file (`tools/design.py`)

- `load_design(path) -> Design` reads a `design.yaml`, resolves `extends` against `model/core-model.yaml`,
  merges `add_objects`, `add_fields`, `add_relationships`, and returns frozen dataclasses. Every other module
  works from `Design`, never from raw YAML.
- Dataclasses (all keys snake_case):
  - `Design(name, description, objects, fields, relationships, pipelines, decisions, automations, views,
    platform_overrides, source_path)`
  - `ObjectDef(key, label, plural_label, description, kind)`; `kind` is `core` (Company, Person, Deal) or `custom`.
    Native mapping per platform lives in `native_names: dict[platform, str]`.
  - `FieldDef(object, key, label, type, description, options, required, native, native_names)`; `options` is a
    tuple of `Option(key, label)`; `native` is the platforms where the field exists out of the box.
  - `RelationshipDef(key, from_object, to_object, cardinality, from_label, to_label, purpose)`; cardinality is
    one of `one_to_one`, `one_to_many`, `many_to_one`, `many_to_many`.
  - `Pipeline(object, key, name, stages)`; `Stage(key, label, type, probability, exit_criteria, required_fields)`;
    `type` is `open`, `won` or `lost`.
  - `Decision(key, question, recommended_default)`, `Automation(key, name, trigger, action)`,
    `View(key, name, object, filter, sort)`.
- Platforms are exactly `attio`, `hubspot`, `salesforce`.
- Canonical field types are exactly the brief's 14.

### Generators (`tools/generate.py`, `tools/generators/`)

- One module per platform: `tools/generators/<platform>.py` exposing
  `generate(design: Design, out_dir: Path) -> list[Path]` that writes that platform's files from section 6 of
  the brief and returns the paths written.
- `tools/generators/build_sheet.py` builds `build-sheet.md` in the brief's order. Each platform passes its own
  UI paths and manual steps.
- Output is deterministic so CI can detect stale files: JSON with `indent=2`, keys in a fixed order, a trailing
  newline; no timestamps in generated files; stable ordering everywhere.
- `uv run python -m tools.generate blueprints/<name>` regenerates one blueprint, `--all` regenerates every one,
  and `--check` exits non-zero if any committed file differs from a fresh generation.

### Live CRM tooling (`tools/crm/`)

- `tools/crm/base.py` defines the brief's `Adapter` interface and the records:
  - `State`: live structure in canonical terms (objects, fields with type and options, relationships,
    pipelines with ordered stages), so it can be compared with a `Design`.
  - `Change(kind, target, payload, risk, source_url, summary)`; risk is `safe`, `needs_review` or `destructive`.
  - `ManualStep(title, reason, ui_path, done_when)`.
  - `Plan(platform, target, changes, manual_steps)`; serialises to and from JSON for `crm_plan.py` → `crm_apply.py`.
  - `Result(applied, failed, remaining)`, where `failed` carries the API error.
- `tools/crm/planner.py` holds the platform-neutral diff of `Design` against `State`: ordering by the build
  order, risk classification, the safety rules (no deletes or type changes; removals become destructive manual
  steps; renames, removals and reorders are `needs_review`). Adapters supply only payload building, API calls,
  and the platform's manual-step wording. This keeps the safety rules in one place and tested once.
- `tools/crm/safety.py` holds the execute and production gates, the confirmation prompt, and log redaction.

## D-4. Additive fields on the D-3 dataclasses (2026-10-04)

D-3 names the dataclass fields. These defaulted additions keep every D-3 positional call working:

- `RelationshipDef.native: tuple[str, ...] = ()`. Core links exist on all three platforms, so generators
  and the planner must skip them. Without this flag a build would try to create Person to Company.
- `ManualStep.risk` (`safe` by default, `destructive` for removals and type changes) and
  `ManualStep.instructions` (the data-migration steps). The brief calls these steps "destructive", and
  they need somewhere to carry the instructions.
- `Result.dry_run`, and `Result.failed` is a tuple of `Failure(change, error)`.
- `State` is built from `StateObject`, `StateField`, `StateRelationship`, `StatePipeline` and `StateStage`.
  Each has a `native` flag where it applies. Adapters set it for platform built-ins so the planner never
  proposes removing them, and map live API names back to design keys when they build the state.

## D-5. Design file leniency and strictness (2026-10-04)

The loader rejects wrong shapes (unknown keys, a list where a mapping belongs, a core field redefined,
a core object reused) with a key path. It accepts missing values as empty and leaves meaning to
`tools.validate`, so one run reports many problems. A malformed file shows up as a single error.
Select options can be written as a `key: label` mapping, a list of keys, or a list of `{key, label}`.
`extends` accepts only `core`.

## D-6. Overrides shape (2026-10-04)

`platform_overrides` is `{platform: {objects: {object_key: {...}}, fields: {"object.field": {...}}}}`.
The allowed keys per platform (hubspot: `property_group`, `object_type_id`; salesforce: `record_type`,
`api_name`; attio: `api_slug`) are accepted at either level, as the brief's wording does not split them.
Targets must exist in the design.

## D-7. Principle 8 check (2026-10-04)

The validator warns when (a) the design has no custom object, or (b) a Deal pipeline has a stage whose key
or label contains delivery, kickoff, fulfilment or implementation. Both are silenced by any decision whose
key, question or default mentions "deliver". This is a heuristic. Any blueprint that trips it for a good
reason should say why in a decision.

## D-8. Planner scope and matching rules (2026-10-04)

- The planner diffs objects, relationships, pipelines (with stages), fields and options. Automations and
  views are not in `State`; adapters pass them as `extra_manual_steps` (or Changes of their own).
- Matching is by design key. Live names are mapped to keys by the adapter. Native relationships match by
  their endpoints, not by key.
- A native field missing from `State` is skipped, not added.
- Live items not in the design are removals only if not marked `native`. Fields on a removed object are not
  listed again, because the object step covers them.
- Pipeline removal and relationship cardinality change are treated like field removal and type change:
  destructive manual steps. The brief does not list them; the same rule 3 and 4 logic applies.
- Option and stage removal are `needs_review` Changes, as the brief says. Rule 3 forbids deleting them,
  so an adapter must archive or hide the option or stage and never delete it.
- Stage label rename is `rename_stage`; a stage type or probability change is `update_stage`. Both are
  `needs_review`. A live probability of `None` (platform does not expose it) is not a difference.
- Order is objects, relationships, pipelines, fields (with options), enforced by the order of the passes.
  Tests fail if the passes are reordered.

## D-9. Safety module behaviour (2026-10-04)

- `--production` without `--execute` is refused, not ignored.
- The production prompt refuses to run when stdin is not a terminal, and needs an exact match on the
  account or org name after trimming whitespace (case-sensitive).
- `check_gates` raises on any `destructive` Change, as a guard against a hand-edited plan file.
- Phone redaction only matches numbers that start with `+`, a `0` or a bracketed area code, so ISO dates
  and record ids are left alone. Redaction is best effort, so adapters should also pass known credential
  values in `secrets`.

## D-10. Generator check (2026-10-04)

`generate --check` fails on changed, missing and unexpected files in a platform folder. So a platform
folder must hold only generated files. A platform with no generator module is skipped with a message and
does not fail the check. A missing generator is detected by the module name, so a broken import inside an
existing generator still raises.

## D-11. Blueprint batch two judgement calls (2026-10-04)

- Manufacturing uses custom `Trade_Quote__c` and `Trade_Order__c` on Salesforce (via overrides), because standard Quote and Order exist there with their own rules.
- Delivery or fulfilment pipelines live on non-Deal objects (wholesale order, advice case, review, lease), each with its own won and lost stages and a select reason on the lost stage.
- Financial advisers store sensitive values as bands or yes/no only; detail stays in external planning systems. Fields holding regulated data start their description with "DATA PROTECTION:".
- Real estate: landlord and tenant are a multi-select role on Company, with separate landlord and tenant relationships on lease and property.
- Placeholder select options (market areas, fund names) are generic and marked "edit at build".
- Industry reasoning in blueprint READMEs is general knowledge, not cited research (David, 2026-10-04: "these are just CRM builds").

## D-12. Blueprint batches one and three judgement calls (2026-10-04)

- Delivery, placement and enrolment pipelines sit on custom objects where the business delivers through them (engagement, matter, search, submission, enrolment, project, referral agreement). Each README gives a deal-pipeline fallback for plans that cannot put pipelines on custom objects.
- Delivery pipelines may hold open stages at probability 100: the sale is already won, so the figure is not weighted revenue. Generators decide whether a platform needs probability on non-deal pipelines.
- Recruitment and executive search mark people with a multi-select `person_type`, so a person who is both candidate and client contact stays one record (principle 2).
- Recruitment fee revenue sits on the submission; the recruitment deal is the client agreement and is won at "terms signed".
- Conflict checks are a custom object for the audit trail, with the latest result copied to the deal to gate the proposal stage.
- Healthcare blueprint stores no patient or health data anywhere; counts are aggregate only.
- Stage keys may repeat across pipelines in one design (`proposal`, `placed`). Generators must scope stage identifiers to their pipeline.
