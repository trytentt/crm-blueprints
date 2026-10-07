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
- Industry reasoning in blueprint READMEs is general knowledge, not cited research (owner instruction, 2026-10-04: "these are just CRM builds").

## D-12. Blueprint batches one and three judgement calls (2026-10-04)

- Delivery, placement and enrolment pipelines sit on custom objects where the business delivers through them (engagement, matter, search, submission, enrolment, project, referral agreement). Each README gives a deal-pipeline fallback for plans that cannot put pipelines on custom objects.
- Delivery pipelines may hold open stages at probability 100: the sale is already won, so the figure is not weighted revenue. Generators decide whether a platform needs probability on non-deal pipelines.
- Recruitment and executive search mark people with a multi-select `person_type`, so a person who is both candidate and client contact stays one record (principle 2).
- Recruitment fee revenue sits on the submission; the recruitment deal is the client agreement and is won at "terms signed".
- Conflict checks are a custom object for the audit trail, with the latest result copied to the deal to gate the proposal stage.
- Healthcare blueprint stores no patient or health data anywhere; counts are aggregate only.
- Stage keys may repeat across pipelines in one design (`proposal`, `placed`). Generators must scope stage identifiers to their pipeline.

## D-13. HubSpot generator judgement calls (2026-10-04)

- Payload files are `{api_version, order, source, placeholders, requests}`, like the Attio files. Run order: schemas, property groups, properties, associations, pipelines. Groups follow schemas because a custom object's group needs its `objectTypeId`.
- A custom object has no ID until HubSpot creates it, so requests carry `{objectTypeId.<key>}` and `{typeId.<relationship>.<from>_to_<to>}` placeholders, each explained in the file's `placeholders` key. A design `object_type_id` override means the object exists: no schema is sent.
- The schema carries only the display property (a design text field, preferably `name`, else a generated `name`), in HubSpot's default group. Other properties are created afterwards in the design's group, and extra required properties are added by one PATCH of `requiredProperties`.
- `associatedObjects` lists the other end of each non-native relationship; another custom object is listed only if created earlier. Each relationship is one paired label (`from_label`, `to_label`). A cardinality cap is a limit of 1 on the labelled type only; the unlabelled type's ID is unknown until read, so a manual step asks for a check.
- Deal stages carry probability. Custom-object stages carry `isClosed` only (OQ-1), so design probabilities and the won or lost split are not sent there, and the manual steps and plan requirements say so (D-12). Pipelines on companies or people are not sent: HubSpot has none.
- `stageId` is `<pipeline_key>__<stage_key>`. `pipelineId` is the key, prefixed with the object only when two objects share a key.
- Property groups HubSpot ships (`contactinformation`, `companyinformation`, `dealinformation`, `ticketinformation`) are not created when an override names them. Only the first two names beyond `dealinformation`/`contactinformation` are unverified in the research.

## D-14. Adapter discovery and CLI behaviour (2026-10-04)

- Each platform module `tools/crm/<platform>.py` exposes `make_adapter(env: Mapping[str, str], *, target: str | None, production: bool) -> Adapter`. It reads credentials from `env` through `safety.get_credential` and raises `SafetyError` when one is missing.
- `tools/crm/registry.py` `get_adapter(platform, env, target, production)` imports the module lazily and raises `RegistryError` for an unknown platform, a missing module, a missing `make_adapter`, or missing credentials. One platform's broken module never affects the others.
- Every CLI's `main()` takes `adapter_factory` and `env` for tests. `.env` is read by a small loader (`tools/cli_common.py`); a variable already in the environment wins over the file.
- `crm_apply` does the gating itself (`check_gates`, production prompt) and passes an adapter only changes it has cleared, one at a time. If the adapter has a `mode` attribute, the CLI sets it from the flags so the adapter's own gate agrees. An adapter's own gate is a second line of defence and must not re-hold a change the CLI has cleared.
- "Already satisfied" before each change: with `--design`, the CLI re-plans and skips any change no longer in the plan. Without it, additive changes (`add_object`, `add_relationship`, `add_pipeline`, `add_stage`, `add_field`, `add_option`) are checked against the fresh `read_state` by target; other kinds are always attempted.
- `--execute` needs `--client` so every real run is logged. A dry run logs too when `--client` is given. Exit codes: 0 done, 1 a change failed or (drift) drift found, 2 refused or error.
- Held `needs_review` changes are reported, not treated as failure.
- `crm_drift` counts every change and every destructive manual step (extras in live, type changes) as drift. Safe manual steps (automations, views) are not drift because `State` cannot see them.
- `diff_design` treats the old design as the live state and runs the planner, so risk classes match plans. `<git ref>:<path>` is read with `git show` from the repo root.
- `crm_pull --to-design` leaves core objects, fields and links to `extends`, writes `TODO` descriptions, and `tools.validate` now rejects a description starting with `TODO`. Exit-criteria TODOs already fail the "Entered when" rule.

## D-15. HubSpot adapter judgement calls (2026-10-04)

- **Account identity.** The research has no account-info page. `read_identity` tries `GET /account-info/v3/details` (HubSpot's Account Information API; the endpoint and its response shape are not confirmed in this repo, and the live smoke test is what checks them). If that gives no portal id it takes the id from a documented response, the `p{HubId}_` prefix of a custom object's `fullyQualifiedName`. With neither, production confirmation names only `HUBSPOT_TARGET`. In production the plan target is `<label> (HubSpot portal <id>)`.
- **Custom-object limits.** `GET /crm/limits/{V}/custom-object-types` has no documented response, so the adapter reads any `maxLimit`/`limit` and `usage` number in it. 403 or 404 means "no custom objects"; a 403 that lists a missing scope, or a body with no maximum, means unknown and the plan proceeds (the create then fails with HubSpot's own error). Objects beyond the remaining count, and everything depending on them, become manual steps citing the blueprint's `plan-requirements.md`.
- **Read state needs the design for four things, so `plan` finishes them** (the `read_state()` signature stays as the brief has it): relationship keys (HubSpot returns the label text, not our internal `name`; each direction is read as an entry and `plan` folds the two into the design relationship by endpoints and label text), design-defined native properties (HubSpot name to design key), custom-object pipelines (HubSpot has closed; the design's won or lost is taken from the design), and the cardinality (a limit of 1 on the labelled type). If limits cannot be read (a tier without them) the design's cardinality is trusted, so a Starter account does not loop on a cardinality step.
- **HubSpot-owned items are native.** A property is native if `hubspotDefined` or `modificationMetadata.readOnlyDefinition`, if its name starts `hs_`, or if it is a custom object's primary display property. The `default` deal pipeline is left out of state: it exists everywhere and cannot be removed. Options on native properties that the design does not list are left alone, matching the generator's merge note.
- **Hidden options count as absent.** Removing an option hides it (documented, `hidden: true`). Adding an option that is hidden un-hides it.
- **Turned into manual steps at plan time:** stage removal (no documented hide or archive, and delete is blocked in use), custom object rename (OQ-4), and pipelines on contacts or companies (the generator already writes the manual step). The generator's non-set-up manual steps (stage gates, views, workflows, standard-object required properties, permissions, lossy-type and association-limit checks) are the `extra_manual_steps`.
- **Apply.** Dry run makes no HTTP call at all. Skipped (already satisfied) changes are listed in `adapter.skipped`, not in `applied`, `failed` or `remaining`. 429 retries five times with 1 s doubling to 10 s, or `Retry-After`; a `DAILY` policy is not retried. Other statuses are never retried, because a POST may have landed. Property groups are created on demand inside `add_field` because the planner does not see groups. A custom object's extra required properties are set by one PATCH after the property exists. Reorder uses `PATCH .../stages/{id}` with `displayOrder`, which the research lists but does not show a body for.
- **Gates.** The adapter holds `needs_review` unless `mode.allow_review`, refuses destructive changes, and does not prompt for production (D-14: the CLI owns the prompt).
- **Fixtures.** `tests/fixtures/hubspot/` follows the research examples with invented values. The limits and account-info responses are assumed shapes and the README there says so. `tests/hubspot_stub.py` is a small stateful HubSpot used in place of the network.

## D-16. A public toolkit for anyone (2026-10-04)

The repository is for public use by any GTM engineer, RevOps consultant or agency, not one firm's internal
toolkit. This overrides the brief's "internal toolkit" and "private" wording.

- No real company, person, client or account data anywhere: blueprints, fixtures, examples and docs use
  invented, generic names only.
- No internal information: no names of the authors' own company or people, no local machine paths, no
  private URLs, workspace ids, tokens or account numbers.
- Docs speak to "you, the builder" and "your client", not to one agency's team.
- A test (`tests/test_public_safe.py`) scans the repository for local paths, secret-shaped strings and email
  addresses outside an allow-list, so this stays true.
- The repository is created private on GitHub first (as the brief says) so it can be checked before being
  made public; whether and when to make it public, and under which licence, is the owner's call.

## D-17. Salesforce generator judgement calls (2026-10-04)

- **Data protection flag.** A field whose description starts with "DATA PROTECTION:" gets `complianceGroup` `PII;GDPR` and `securityClassification` `Confidential`. A description that also names health, vulnerability, special category or sensitive personal data, or any description containing "sensitive personal data", gets `Restricted`. No change to the design format (the research proposed a `data_protection` key; not adopted). These are labels, not encryption. Standard fields have no file, so a flagged standard field becomes a manual step. User lookups are not labelled.
- **Picklist values are stored as the label.** Salesforce shows the stored value, so `fullName` and `label` both carry the option label, not the snake_case key. A duplicate label gets the key in brackets.
- **Custom object `name` and `owner`.** A text field `name` on a custom object becomes the object's name field (its label is used), and a `user` field `owner` maps to the standard Owner. Neither gets a field file, because a custom field labelled Owner or Name would clash with the standard one.
- **Stage values and scoping.** An Opportunity stage value is the stage label. The same label in two pipelines is one shared value when type and probability agree. If they differ, each gets "label (pipeline name)", because a stage value holds one probability. Rules and record types are scoped by pipeline key, so repeated stage keys never collide.
- **One validation rule per gated stage**, joining several required fields with OR, with the Opportunity record type in the formula so each pipeline is gated alone. The stage order is the position among the pipeline's non-lost stages. A lost stage gets its own rule (`ISPICKVAL`) rather than the research's generic `IsClosed` form, since each pipeline may use a different reason field. Formulas are written on one line so the build sheet and the file show the same text.
- **Custom-object pipelines.** One restricted `Stage__c` picklist (the first free name) holding the union of stages, and gates as above. A record type per pipeline is written only when the object has more than one pipeline. No path, won/lost flag or probability: manual steps say so.
- **`record_type` override** names the record type of an object's only pipeline; with several pipelines it prefixes each pipeline's name. A `api_name` override that Salesforce would refuse raises `SalesforceGenerationError` instead of being repaired.
- **Relationships.** Lookup everywhere, on the many side (one-to-one: on the `from` side, with a manual step). Many-to-many is a junction object named from the relationship key with two master-detail fields and `ControlledByParent`. Relationship names avoid a conservative list of standard child names.
- **List views** are written only when the filter is a plain comparison on a custom field, the stage or the owner (`Owner is me` becomes scope Mine). Standard-field filters, other "me" fields and free-text filters go to manual-steps.md as does every sort. Date phrases use `TODAY` and `NEXT_N_DAYS`; "empty" is `equals` with an empty value. All of these tokens are unverified and listed as checks.
- **Permission set** grants read and edit on every generated non-required custom field, create/read/edit (no delete) on each object that has one, and record type visibility. It includes standard-object permissions because a field permission may need object read in the same file (unverified, research E16).
- **Names.** API names are the key with a capital first letter (`next_step_date` to `Next_step_date__c`), at most 40 characters, case-insensitively unique per object. A long validation rule name keeps its start plus a six-character hash.
- **Nothing is deleted from the output folder.** After a design edit, orphan files are reported as "unexpected" by `--check`; delete the salesforce folder and regenerate.
- **Flows, tabs, apps, page layouts and lead-conversion mapping** are manual steps, as the research recommends.

## D-18. End-to-end and public-safety testing judgement calls (2026-10-07)

- **The end-to-end matrix is 15 blueprints x Attio and HubSpot**, one journey per case in `tests/test_end_to_end.py`: new_client, plan, dry run, execute, re-plan, re-apply, amend, drift. It drives the CLIs' `main(argv)` and the real registry and `make_adapter`; only the HTTP session is replaced by the simulator.
- **`crm_apply` passes the adapter only the `--target` the user typed**, never the plan's target. The plan's target is a display name (Attio: the workspace name from `/v2/self`), so passing it made every `crm_apply` without `--target` fail against a real `ATTIO_TARGET` label. The plan's target is still what the production confirmation asks the user to type.
- **`crm_apply` logs a change an adapter found already in place as "already in place", not "applied"**, using the adapter's `skipped` list. Before, re-applying a plan on Attio logged every change as applied while sending nothing.
- **The planner no longer matches a native relationship to a custom one between the same two objects.** Investor VC has `deal_company` (native) and `deal_co_investors` (custom, many-to-many) joining the same pair; the old endpoint fallback paired them and reported false cardinality drift on both platforms.
- **Adding a stage in the middle of a pipeline needs a follow-up reorder.** The add is safe and applies on its own, but both platforms append the new stage, so the next plan holds one `reorder_stages` (`needs_review`, applied with `--allow-review` on HubSpot) or a manual step (Attio cannot reorder through the API). The amendment test asserts exactly this, rather than hiding it by appending the stage last.
- **The amendment test never removes an object's `name` field or a field that gates a stage**, because every platform creates `name` with the object and a stage-gating field is referenced elsewhere. Both would make "remove a field" mean something else.
- **`tests/test_public_safe.py` scans tracked files and untracked files that are not ignored**, so a new file is checked before it is committed. Deliberate fixtures (dummy tokens in tests) are allow-listed by path and kind with a reason, and a stale allow-list entry fails the test. Two sample addresses on real-looking domains (in a test and in the Attio field reference) were changed to `example.com`.
- **CI needed no new step.** `ci.yml` already runs validate --strict, generate --check and pytest, which now includes the public-safety scan.
