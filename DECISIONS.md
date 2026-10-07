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

- **Account identity.** The research has no account-info page. `read_identity` tries `GET /account-info/v3/details` (HubSpot's Account Information API; the endpoint and its response shape are not confirmed in this repo, and the live smoke test is what checks them). If that gives no portal id it takes the id from a documented response, the `p{HubId}_` prefix of a custom object's `fullyQualifiedName`. With neither, production confirmation names only `HUBSPOT_TARGET`. In production the plan target is `<label> (HubSpot portal <id>)`. **Corrected by D-24:** the portal id and name are the account identity stored in the plan and typed at apply time, and with no portal id a production apply is refused rather than falling back to the label.
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
- **`crm_apply` passes the adapter only the `--target` the user typed**, never the plan's target. The plan's target is a display name (Attio: the workspace name from `/v2/self`), so passing it made every `crm_apply` without `--target` fail against a real `ATTIO_TARGET` label. **Corrected by D-24:** the plan's target is not what the confirmation asks for; the live account name is.
- **`crm_apply` logs a change an adapter found already in place as "already in place", not "applied"**, using the adapter's `skipped` list. Before, re-applying a plan on Attio logged every change as applied while sending nothing.
- **The planner no longer matches a native relationship to a custom one between the same two objects.** Investor VC has `deal_company` (native) and `deal_co_investors` (custom, many-to-many) joining the same pair; the old endpoint fallback paired them and reported false cardinality drift on both platforms.
- **Adding a stage in the middle of a pipeline needs a follow-up reorder.** The add is safe and applies on its own, but both platforms append the new stage, so the next plan holds one `reorder_stages` (`needs_review`, applied with `--allow-review` on HubSpot) or a manual step (Attio cannot reorder through the API). The amendment test asserts exactly this, rather than hiding it by appending the stage last.
- **The amendment test never removes an object's `name` field or a field that gates a stage**, because every platform creates `name` with the object and a stage-gating field is referenced elsewhere. Both would make "remove a field" mean something else.
- **`tests/test_public_safe.py` scans tracked files and untracked files that are not ignored**, so a new file is checked before it is committed. Deliberate fixtures (dummy tokens in tests) are allow-listed by path and kind with a reason, and a stale allow-list entry fails the test. Two sample addresses on real-looking domains (in a test and in the Attio field reference) were changed to `example.com`.
- **CI needed no new step.** `ci.yml` already runs validate --strict, generate --check and pytest, which now includes the public-safety scan.

## D-19. Salesforce adapter judgement calls (2026-10-07)

- **Login and target.** `SF_TARGET_ORG` is an `sf` org alias or username already authorised with `sf org login web`, so the environment holds no secret. `SF_API_VERSION` (default 67.0, also written into `package.xml` and `sfdx-project.json`) and `SF_CLI` (default `sf`) are optional. `sf org display --json` prints an access token, so only the username and instance URL are kept from it and the raw reply is never stored, logged or put in an error.
- **One runner.** Every `sf` call goes through one injectable `Runner` (`subprocess_runner` is the only place a process starts). The adapter refuses to run any argument list containing `--ignore-errors`, `--ignore-conflicts`, `--ignore-warnings`, `--purge-on-delete`, the destructive-changes flags or `--test-level`, and refuses to write a file with `destructive` in its path.
- **Production.** An org is production unless `Organization.IsSandbox` is true, `sf org display` shows scratch signals (`devHubId`, `expirationDate`) or the instance URL has `.sandbox.` or `.scratch.`. A Developer Edition org that is not a sandbox counts as production, because the safe side is to ask for `--production`. When the org is production the plan's target is `<Organization.Name> (<alias>)`, so a plan shows which org it was made for. **Corrected by D-24:** what is typed is the org's name read live, not `<name> (<alias>)`, and the plan stores the org name and username as its account identity. A real apply on a production org without `--production` raises; a check-only run is allowed.
- **Edition gate.** The Metadata API is assumed only for editions whose `OrganizationType` contains enterprise, unlimited, performance or developer. Professional, Essentials and any edition not in that list make `plan` return no changes and one manual step per change, naming the blueprint's `build-sheet.md`. `apply` on such an org changes nothing and does not fail. A near-limit warning (75 percent of the secondary-source custom object and field allowances in `objects.md`) is a manual step.
- **`read_state` takes an optional design.** The CLIs call it with none, so it then describes Account, Contact, Opportunity and every non-managed custom object and guesses design keys from API names (`Foo_bar__c` is `foo_bar`). `plan` re-maps the same reads with the design, using the generator's own naming (`build_model`), when it is handed the state `read_state` just returned (identity check). Any other `State` is used as given.
- **What state holds.** Custom objects, custom fields (type from the describe `type`; `textarea` is long_text; a reference to User is `user`), active picklist values only, lookups as relationships, managed-package (`ns__X__c`) fields as native, design-native and Name/Owner fields as native with the design's type. Junction objects appear only as relationships. A value or label the generator would have written is reported with the design's wording, so a freshly built org compares equal. Opportunity pipelines come from record types in the describe, stages from `OpportunityStage` (type from IsClosed and IsWon, probability from DefaultProbability) and the member order of each business process from a `sf project retrieve start` with wildcard `BusinessProcess` and `RecordType` members. Open question: whether that wildcard retrieve works is unverified (research E14-style; a business process wildcard is documented only alongside a record type wildcard). If the retrieve fails the plan notes it and assumes the design's stages that exist. Custom-object pipelines read the generated `Stage__c` picklist; with several pipelines on one object, stage membership per pipeline cannot be told apart, so extra stages are only detected for a single pipeline.
- **Plan order.** The planner's order is objects, relationships, pipelines, fields. For Salesforce the adapter reorders to objects, relationships, fields, pipelines, because validation rules and record types name fields and a deploy fails if they do not exist yet. `apply` runs in the same four phases, one deploy per phase (research E18), re-reading the org before each.
- **Which components a change deploys.** `add_object` its object file; `add_field` and `add_option` the field file; `add_relationship` the lookup field, or the junction object and its two master-detail fields; `add_pipeline` and `add_stage` the stage value set, business process, record type, path and the pipeline's validation rules (Opportunity) or the stage picklist, record type and rules (other objects). The files are the generator's, taken from `build_model`; two small additive attributes on the generator's `Build` (`component_paths`, `rel_components`) record which file belongs to which component, with no change to any generated file. The `OpportunityStage` and picklist files are deployed whole, so a change can add sibling values another pending change would add; they are all additive. A change's files are stored in its payload, so a saved plan applies without the design.
- **Not deployed by a change.** The permission set (overwritten whole, and it names every field) and list views (they name columns). A manual step points at the generated `package.xml` for them. Name and Owner of a custom object need no change: they come with the object.
- **Removals.** Removing a picklist value (and a stage on a custom object) is `needs_review` and deploys the field file with that value added as `isActive` false; nothing is removed, and `--allow-review` is needed. Removing an Opportunity stage is a manual step, because the research says deactivation through source is unknown (E10). Removing a value another pipeline on the same object still uses is also a manual step.
- **Manual instead of deployed.** Renames (full name is identity), stage reorders, and stage type or probability changes become manual steps at plan time, as do add or remove on a field with no metadata file (a standard field).
- **Check-only is one deploy.** A dry run is one `--dry-run` deploy of every pending change, so cross references resolve, since a check-only run saves nothing for a later phase to depend on. Re-reading before it still skips what is in place.
- **Failure reporting.** A deploy is all or nothing (rollback on error), so a failed phase applies nothing; `applied` holds earlier phases, `failed` holds the change that owns the first failed component (matched by full name or file path, else the first in the phase) with the redacted component errors, and `remaining` holds everything else including held changes. Exit code 69 is a failure that tells the person to check the job with `sf project deploy report`; it is never retried.
- **Working folders.** Each deploy and retrieve uses a temporary project folder (under `build_dir` when given, else the system temp directory). It is removed afterwards, except that a failed deploy is kept when `build_dir` is set.
- **Fixtures.** `tests/fixtures/salesforce/` is authored from the documented shapes, not recorded (D-2); `tests/salesforce_stub.py` is a stateful stand-in for `sf` that checks the manifest against the files written and cross references (a record type or rule naming a missing field fails), so phase order is tested.

## D-20. Licence and the finishing pass (2026-10-07)

- **Licence.** The owner chose MIT. `LICENSE` names the holder "crm-blueprints contributors" and the year 2026, and the README says so. This settles the question D-16 left open. Whether the repository is made public is still the owner's call.
- **Markers.** Every adapters-land confirmation marker (an HTML comment) was resolved against the code. The variable names are `ATTIO_ACCESS_TOKEN` and `ATTIO_TARGET`, `HUBSPOT_ACCESS_TOKEN` and `HUBSPOT_TARGET`, `SF_TARGET_ORG` with optional `SF_API_VERSION` and `SF_CLI`; `.env.example` already matched. The docs now say plainly that no live CRM has been exercised.
- **Where generated files go.** `tools.generate` writes platform folders next to the design (`clients/<client>/<platform>/`, `blueprints/<name>/<platform>/`). `clients/README.md` said `build/`; the docs now match the code. `build/` holds what a run leaves behind: `apply-log/`, any plan or state file saved there with `--out`, and Salesforce deploy staging.
- **Salesforce deploy staging moved under `build/`.** The adapter supported a `build_dir` (D-19) but no CLI set it, so staging always went to the system temp folder and a failed deploy could not be inspected. `crm_apply` now sets it to `clients/<client>/build/salesforce/` when `--client` is given. A successful deploy still removes its own folder; a failed one is left. The folder is git-ignored. The alternative, documenting that staging is temporary, was rejected because a failed deploy is exactly when the files are wanted.

## D-21. Bugs the Salesforce end-to-end run found (2026-10-07)

- **`crm_apply` logged a change as applied when the adapter did nothing.** On an edition without the Metadata API the Salesforce adapter returns nothing applied and nothing failed (D-19). The CLI appended every such change to `applied`, so a Professional org's log claimed dozens of builds that never happened. A change now counts as applied only if the adapter's result says so; otherwise it stays in `remaining`. The adapter's `notes` are printed ("Note: ...") and written to the log. Regression: `tests/test_cli_apply.py::test_a_change_the_adapter_declined_is_not_logged_as_applied`, and the Professional case in `tests/test_end_to_end.py`.
- **`crm_drift` said "No drift" for an unbuilt Professional org.** On such an org every change is a manual step, and drift counted only changes and destructive steps. `ManualStep` gains `drift: bool = False` (additive, default false, so saved plans still load), the Salesforce adapter sets it on every manual step that stands for a difference it could not close (edition, renames, reorders, fields with no file), and `crm_drift` counts those. Routine hand work such as building a flow is still not drift. Regression: `tests/test_cli_read_only.py::test_drift_counts_a_manual_step_that_stands_for_a_difference` and the Professional case.

## D-22. Salesforce end-to-end allowances (2026-10-07)

The Salesforce matrix runs the same journey as the other two platforms with these differences, each from D-17 or D-19 and none weakening an assertion:

- **Build order** is the adapter's (objects, relationships, fields, pipelines), not the planner's.
- **Automations and views** are found by name ("Build the view ...", "Set the sort on ..."), because Salesforce steps are titled after the flow or view, not "workflow".
- **The removed field** is never an `owner` field. A custom object's `owner` is the standard Owner (D-17), so removing it from the design leaves nothing to remove in the org.
- **The added stage** goes on a deal pipeline with room for it (investor VC's is at the eight-open-stage limit and uses another). A deal pipeline's order is read from its business process, so the follow-up reorder appears as exactly one manual step, as on Attio. For a pipeline on a custom object the order cannot be read back, so no reorder is asked for.
- **A separate test removes a deal stage** and asserts it is a destructive manual step, no change, nothing deployed.
- **Production** is the org itself. The gate test uses a Developer Edition org that is not a sandbox, which counts as production, and checks every refusal (no org named, no `--production`, no terminal, wrong name) before the right name goes through. A check-only run on production is allowed.
- **A Professional edition org** gets only manual steps pointing at the build sheet and nothing is deployed, applying an Enterprise-made plan to it changes nothing, and drift is reported.
- **A refused deploy** stops the run, reports applied, failed and remaining, and the same plan resumes to a zero-change re-plan.

## D-23. Found and left open (2026-10-07)

These were seen while testing Salesforce. They are recorded rather than fixed because each is a design decision, not a slip.

- **A stage value two pipelines share is renamed when only one keeps it.** *(Fixed by D-26.)* Values with the same label and different type or probability are named "label (pipeline name)" (D-17). Remove the stage from one pipeline and the other's value is named plainly, so the next plan asks to add a stage the org holds under the old name. Measured on `agency-marketing`: `Negotiation (Retainer renewals)` becomes `Negotiation`. Naming from the whole design is what makes this happen; stable names would need a stored mapping. The end-to-end stage-removal test picks a label no other pipeline uses.
- **A custom object's stage order is not read back**, so a stage added mid-pipeline there is never flagged for reordering. Whether a deploy of the field file puts the value in the right place is one of the points a live run must settle (HANDOFF.md).
- **Manual steps on Attio and HubSpot are not counted as drift** (a reorder on Attio, for example). Only the Salesforce adapter sets `ManualStep.drift` so far.
- **Applying a plan to a Professional edition org prints "Would apply: N" in a dry run**, followed by the adapter's note that nothing can be deployed. The adapter cannot tell the CLI which of the two it means; the note is the signal.

## D-24. Production confirmation is tied to the live account (2026-10-07, review finding S1)

- **The problem.** The typed confirmation was checked against `plan.target`, a string taken from the plan file or `--target`, and `crm_plan` always built the adapter with `production=False`. A plan made on Salesforce sandbox alias `acme-sbx` and applied with `--execute --production` to the production org "Acme Live Ltd" passed when the person typed the alias: 57 writes to production. Attio's adapter-level `_check_target` already compared the workspace; HubSpot and Salesforce did not.
- **The rule.** Every adapter has `read_account()`, which reads the account identity from the platform, never from a flag or the plan: the Salesforce org name (`Organization.Name`) with the `sf` login's username, the HubSpot portal name (when the account-information response has one, else `HubSpot portal <id>`) with the portal id, the Attio workspace name with its id. `Plan.account` stores `Account.identity` (`name [detail]`) at plan time, for all three adapters.
- **At apply time, for a real production run,** `run_plan` reads the account live, refuses a plan whose stored `account` differs (or is empty, which covers plan files made before this change: re-plan), shows the live name and details, and requires the live **name** to be typed exactly. The refusal comes before any prompt. The plan's `target` and `--target` are labels and are never what is typed. `check_gates` no longer confirms; it only splits changes by risk and refuses destructive ones.
- **Typed name.** Salesforce: the org's name, not `<name> (<alias>)`. HubSpot: the portal name, or `HubSpot portal <id>` where the account-information response has no name (its shape is unconfirmed until a live run). If no portal id can be read, a HubSpot production apply is refused. Attio: the workspace name.
- **A dry run and a sandbox run** do not compare the account and do not prompt. The identity is still stored in a plan made on a sandbox, so it can never be reused for production.
- **Unchanged:** the adapters' own production checks (Attio's missing `ATTIO_TARGET`, Salesforce's non-sandbox org without `--production`).

## D-25. A HubSpot account is production unless it is a documented test account (2026-10-07, review finding S2)

- `read_identity` read `accountType` and never used it, so production was only the `--production` flag. Now a real apply without `--production` is refused unless `accountType` is `DEVELOPER_TEST` or `SANDBOX` (compared after upper-casing and turning spaces and hyphens into underscores). Any other value, a missing value, or an identity that could only be taken from a schema name is production, and so needs `--production` and the typed live name.
- The two accepted values are from HubSpot's Account Information API as understood, and **are not confirmed against a live account**; the wrong guess costs an extra `--production`, never a silent write. `HUBSPOT_TARGET` stays a label only. The README, `docs/automated-builds.md` and HANDOFF's live-run list say the values are unconfirmed.

## D-26. Stage value names no longer change a pipeline that was not edited (2026-10-07, review finding S3; settles D-23 item 1)

- **The probe.** On `agency-marketing`, removing `negotiation` from `new_business` alone changed the generated value of `retainer_renewals`' Negotiation from "Negotiation (Retainer renewals)" to "Negotiation". The plan then held a "safe" `add_stage` for `retainer_renewals` and a Retire-stage step for the old name, and applying without `--allow-review` added a second Negotiation to the Retainer renewals process.
- **Fix, in two layers.** (1) *Names kept from the org:* the generator still names a value from the whole design (changing it would rewrite every generated file), but the adapter now treats a live value that is another spelling of a design stage's value (plain label, `label (pipeline name)`, `label (stage key)`) as that stage. The stage is therefore present, no add or remove is planned, and the difference shows as a manual "rename stage by hand" step. (2) *Backstop:* any stage change (`add_pipeline`, `add_stage`, `remove_stage`, and the rest) on an object where some live stage value is spelt differently from what the design now generates becomes a manual step, never a change, because the object's stage files share one value set. Nothing is deployed for it.
- **Not settled by this.** Whether a real `BusinessProcess` deploy merges or replaces the values it lists is unverified (the simulator merges); whether Salesforce deactivates, keeps or rejects live picklist values missing from a deployed field file is unverified. Both are on HANDOFF's live-run list. The layers above do not depend on either answer: they deploy nothing in the cases where the answer would matter.
- The shared-name end-to-end test that avoided this (removing a label no other pipeline uses) stays; two new tests cover the probe and the backstop.

## D-27. A hand-edited plan's payload is checked at apply time (2026-10-07, review finding C1)

- Plan files are editable and the adapters ran their payloads as written (Attio's requests, HubSpot's paths and bodies, Salesforce's file text). Now each change is checked against its kind before anything is sent, in dry runs too.
- **Attio:** each request must use a method and path pattern the kind allows (for example `add_field` may POST attribute and option creates only), a PATCH may set only the keys its kind sets (`rename_field`: `title`; `remove_option` and `remove_stage`: exactly `is_archived: true`), and no other kind may carry `is_archived`.
- **HubSpot:** each path the handler will use must match its kind's pattern for the pinned API version, the method and PATCH body keys must match (a rename sets only `label`), option changes carry only a path, a value and a label, and only `remove_option` may hide.
- **Salesforce:** the components must be metadata types the kind deploys, the files must be exactly those components' files, only `remove_option` and `remove_stage` may write an inactive value, and a field file whose `<type>` differs from the live field's type is refused (types are never changed in place). The type check uses a table of metadata types to describe types; a type outside the table is not judged.
- A mismatch raises a `SafetyError` that names the change and the rule, and nothing is sent. Payloads are checked rather than rebuilt from the design because `apply` has no design (the design is optional on `crm_apply`).
- Not covered: a request body for a create (a field's own properties) is not checked beyond its method, path and the archive flag.

## D-28. `--target` is a label, and the public claims are corrected (2026-10-07, review findings C2, C3, C5, S4)

- **`--target` (C2).** `crm_apply` used to replace the plan's target with `--target`, so on Attio a label equal to `ATTIO_TARGET` was then compared with the workspace name and refused. It no longer touches the plan: `--target` goes to the adapter as a label (Attio checks it against `ATTIO_TARGET`, Salesforce uses it as the org alias) and which account is reached is checked separately and live (D-24). The README says so. The apply log records the label typed, and the plan's account identity.
- **The "never delete or archive" claim (S4).** It was wrong: with `--allow-review` Attio archives options and statuses, HubSpot hides options and Salesforce deactivates picklist values. README, `CLAUDE.md` rule 10, `docs/automated-builds.md` rule 3 and the migration playbook now say: nothing is ever deleted; removals of options and stages hide, archive or deactivate them (data kept) and only with `--allow-review`; removals of objects, fields, relationships and pipelines are manual steps. A test fails if the old wording returns.
- **Client work in public (C3).** The README (step 9) and `clients/README.md` tell public users to keep client work in a private repository or fork, and `.gitignore` now excludes `clients/*/build/*.json` (saved state and plans).
- **Drift (C5).** The README no longer says exit 0 means no drift; detection is partial on Attio and HubSpot (D-23 item 3).
- Review finding S5 (git history and author metadata) is the owner's decision and was not touched.

