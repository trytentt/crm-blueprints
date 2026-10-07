# Automated builds

How the tools read, plan and change a live CRM, what stops them doing harm, and how to set up
credentials. For the order of work see [build-sequence.md](build-sequence.md). For platform
differences see [platform-comparison.md](platform-comparison.md).

All three adapters (Attio, HubSpot, Salesforce) and all three generators are built and tested against
in-memory simulators. **No live CRM has been exercised yet**, so every API shape is taken from the
platforms' documentation; the points a first live run must confirm are listed in
[../HANDOFF.md](../HANDOFF.md). Decisions behind the behaviour are in [../DECISIONS.md](../DECISIONS.md).

## How it works

```
design.yaml ──load──> Design ──┐
                               ├─> planner (platform-neutral diff) ──> Plan ──save──> plan.json
live CRM ──adapter.read_state─> State ─┘                                              │
                                                                  crm_apply <─────────┘
                                                      (gates, re-check, adapter.apply, log)
```

1. **Adapter** (`tools/crm/<platform>.py`). One per platform, behind one interface in
   `tools/crm/base.py`: `read_state()`, `plan(design, state)` and `apply(plan, dry_run=True)`. The
   adapter knows the platform's API: how to read it, how to build a payload, and how to wording
   manual steps. Attio and HubSpot call REST APIs (HubSpot pins API version `2026-09`). Salesforce writes
   the files for exactly the components a change needs into a temporary project folder and calls the `sf`
   CLI (`sf project deploy start`; a dry run is one `--dry-run` check-only deploy, a real run deploys in
   four phases: objects, relationships, fields, pipelines). Every `sf` call goes through one runner, and
   the adapter refuses flags that bypass checks (`--ignore-errors`, `--ignore-conflicts`,
   `--ignore-warnings`, `--purge-on-delete`, the destructive-changes flags and `--test-level`).
2. **State.** The live CRM in canonical terms: objects, fields with type and options, relationships,
   pipelines with ordered stages. The adapter maps live names back to design keys. Items that come with
   the platform are marked `native`, so the planner never proposes removing them.
3. **Planner** (`tools/crm/planner.py`). The same code for every platform. It diffs a design against
   a state and produces ordered `Change` records and `ManualStep` records. It holds the risk rules,
   so they are written and tested once. Order is objects, relationships, pipelines, fields.
4. **Plan.** `crm_plan` saves it as JSON. A change has a kind, target, payload, risk (`safe`,
   `needs_review` or `destructive`), source URL and summary. A manual step has a title, reason, UI
   path, done-when and, for destructive ones, data-migration instructions.
5. **Apply.** `crm_apply` reads the saved plan, checks the safety gates, then hands changes to the
   adapter one at a time, re-reading live state before each.
6. **Automations and views** are not in `State`. Adapters add them to the plan as manual steps.
7. **Drift.** `crm_drift` plans the design against live and reports any change, plus things in the
   live CRM that the design does not contain. Exit 0 means none, 1 means drift.

### What each tool does

| Tool | Reads CRM | Writes CRM | Output |
|---|---|---|---|
| `crm_pull` | Yes | No | State as JSON (`--out`), or a draft design (`--to-design`). A draft has TODO descriptions, so it fails `validate` until a person fills them in. |
| `crm_plan` | Yes | **No** | A plan on screen and, with `--out`, as JSON |
| `crm_apply` | Yes | Only with `--execute` | A report of applied, skipped, held, failed and remaining changes, plus a log file |
| `crm_drift` | Yes | No | The differences |
| `diff_design` | No | No | The differences between two design files, with plan-style risk classes |

## Safety model

Nine rules. Each is enforced in code and covered by a test. Run the tests with `uv run pytest`.

| # | Rule | Enforced in | Tests |
|---|---|---|---|
| 1 | **Dry run unless `--execute`.** | `resolve_mode` in `tools/crm/safety.py` turns no flag into `dry_run=True`. `run_plan` in `tools/crm_apply.py` calls `adapter.apply(..., dry_run=True)` in that mode. The Attio and HubSpot adapters send no HTTP write at all in a dry run. The Salesforce adapter makes one check-only deploy, which the org validates and saves nothing from. | `tests/test_safety.py::test_default_is_dry_run`; `tests/test_cli_apply.py::test_dry_run_is_the_default` |
| 2 | **Sandbox by default. Production needs `--execute --production` and a typed account name.** | `resolve_mode` refuses `--production` without `--execute`. `confirm_production` makes the user type the account or org name exactly, and refuses to run when stdin is not a terminal. `check_gates` calls it for production execute runs. The Attio adapter also treats a workspace as production unless `ATTIO_TARGET` marks it as a test workspace. The HubSpot adapter refuses to run without `HUBSPOT_TARGET`. The Salesforce adapter reads the org itself: anything that is not a sandbox or scratch org, a Developer Edition org included, is production, a real deploy there is refused without `--production`, and the typed name is `<org name> (<alias>)`. | `tests/test_safety.py::test_production_without_execute_is_refused`, `test_confirm_*`, `test_production_execute_calls_confirmation_with_target`; `tests/test_cli_apply.py::test_production_*` |
| 3 | **Never delete or archive objects, fields, options, stages or records.** Removals become destructive manual steps with data-migration instructions. | `tools/crm/planner.py`: removal of an object, field, relationship or pipeline is a `ManualStep` with risk `destructive`, never a `Change`. `check_gates` raises on any destructive `Change`, in case a plan file was edited by hand. The Attio adapter's request helper refuses the `DELETE` method. Option and stage removals are `needs_review` changes that adapters carry out by hiding, archiving or deactivating, which keeps the data: Attio archives the option or status, HubSpot hides the option, Salesforce deploys the picklist value as inactive. Where the platform documents no such step (a HubSpot stage, a Salesforce Opportunity stage) the adapter turns the removal into a destructive manual step. The Salesforce adapter never writes a destructive-changes file and refuses any `sf` argument that names one. | `tests/test_planner.py::test_field_removal_is_destructive_manual_step`, `test_object_removal_*`, `test_no_change_is_ever_destructive`; `tests/test_cli_apply.py::test_destructive_change_in_plan_is_refused`; `tests/test_safety.py::test_destructive_change_always_refused` |
| 4 | **Never change a field type in place.** A manual migration step is produced. | `_existing_field` in `tools/crm/planner.py`. A type mismatch (including select to multi-select) produces a destructive manual step to create `<key>_new`, copy, repoint and archive. The same goes for a relationship's cardinality. | `tests/test_planner.py::test_type_change_is_manual_step_never_a_change`, `test_select_to_multi_select_is_a_type_change`, `test_cardinality_change_is_manual_step` |
| 5 | **Add options and stages automatically. Renames, removals and reorders are `needs_review` and need `--allow-review`.** | `RISK_BY_KIND` in the planner sets the risk of each kind. `check_gates` holds `needs_review` changes unless `allow_review` is set. | `tests/test_planner.py::test_add_option_is_safe`, `test_add_stage_is_safe`, `test_renames_are_needs_review`, `test_reorder_stages_is_needs_review`; `tests/test_safety.py::test_review_changes_held_without_allow_review`; `tests/test_cli_apply.py::test_execute_applies_safe_and_holds_review` |
| 6 | **Idempotent.** Re-running a plan is a no-op. The live state is re-checked before each change. | The planner returns an empty plan when state matches the design. `run_plan` reads state before every change and skips one already in place (`is_satisfied`), or re-plans against `--design` when given. Attio treats `409 slug_conflict` as "already exists" and checks the live item. Salesforce deploys are create-or-update. | `tests/test_planner.py::test_matching_state_gives_zero_changes`, `test_replanning_after_fake_apply_is_noop`; `tests/test_cli_apply.py::test_reapplying_the_same_plan_changes_nothing`, `test_skips_a_change_made_by_someone_else_meanwhile` |
| 7 | **Stop on first failure and report applied, failed (with the API error) and remaining.** | `run_plan` returns at the first failed change with the rest in `remaining`. `render_report` prints the three lists. The process exits 1. | `tests/test_cli_apply.py::test_stops_at_the_first_failure_and_reports`; `tests/test_safety.py::test_fake_adapter_stops_on_first_failure` |
| 8 | **Log every apply to `clients/<client>/build/apply-log/` with tokens and personal data redacted.** | `main` in `tools/crm_apply.py` writes one JSON file per run through `write_apply_log` and `redact_data`. `--execute` without `--client` is refused so no run goes unlogged. The folder is git-ignored. Redaction removes bearer tokens, key-named values, known secret values from the environment, emails and phone numbers. It is best effort. | `tests/test_cli_apply.py::test_log_is_written_and_redacted`, `test_execute_needs_a_client_for_the_log`; `tests/test_safety.py::test_redact_*` |
| 9 | **Credentials only from environment variables** (`.env`, git-ignored). | `get_credential` in `tools/crm/safety.py` reads them and names the variable, never the value, in its error. `load_env` in `tools/cli_common.py` merges `.env` with the environment. `.gitignore` excludes `.env`. Every error that is printed goes through `redact`. | `tests/test_safety.py::test_get_credential`, `test_redact_known_secret_values` |

Also enforced: `--allow-review` without `--execute` is harmless (still a dry run), and an adapter
checks that the plan's target matches the account its credentials belong to (Attio compares with
`GET /v2/self`).

What the rules do not cover. Redaction is best effort, so do not paste apply logs into tickets. The
tools cannot tell a client's live account from a test account on Attio, so the engineer must keep
`ATTIO_TARGET` honest. Manual steps are done by people and are not checked until the next plan.

## Credential setup

Credentials live in `.env` (git-ignored) or the shell environment. `.env.example` lists the names.
Use sandbox or test accounts for routine work. Give each client its own credential, and take it
away at the end of the engagement. Never paste a token into a chat, a ticket or a commit.
The variable names below are the ones the adapters read, and `.env.example` lists the same names.

### Attio

Variables: `ATTIO_ACCESS_TOKEN` and `ATTIO_TARGET`.
(Some research notes call the token `ATTIO_API_KEY`; the adapter and `.env.example` use `ATTIO_ACCESS_TOKEN`.)

1. A workspace admin opens the menu beside the workspace name, then **Workspace settings**,
   **Developers**, **+ New access token**.
2. Name it, for example `crm-blueprints read-only`.
3. Tick scopes. Read-only (pull, plan, drift): `object_configuration:read`, `list_configuration:read`.
   Build: `object_configuration:read-write`, `list_configuration:read-write`. To seed records, add
   `record_permission:read-write` (and `list_entry:read-write` for list entries).
4. Copy the token once into `.env`.
5. Set `ATTIO_TARGET` to a label (for example `sandbox`) **only** for a test workspace. Leave it unset
   for a live workspace so the tool treats it as production.

There is **no sandbox**. Create a separate free workspace for testing. `GET /v2/self` shows the
workspace name and slug; the tool prints them so you can confirm the right workspace.
Source: `platforms/attio/reference/auth-and-setup.md`.

### HubSpot

Variables: `HUBSPOT_ACCESS_TOKEN` and `HUBSPOT_TARGET`. The target is a label you choose for a test
account or sandbox (for example `dev-test`); it is not a secret. The adapter refuses to run with
it unset, even for production, so every run names the account it means.

1. A super admin (or a user with "Developer tools access") opens **Development**, **Keys**,
   **Service keys**, **Create service key**.
2. Name it, for example `crm-blueprints build`.
3. **Add new scope** and tick the scopes. Read-only: `crm.schemas.contacts.read`,
   `crm.schemas.companies.read`, `crm.schemas.deals.read`, `crm.schemas.custom.read`, `crm.lists.read`,
   and one `crm.objects.*.read` scope for association labels. Build: the matching `.write` schema
   scopes, plus `crm.lists.write` if lists are used. The full table is in the research note.
4. Create the key, **Show**, **Copy**, and put it in `.env`.
5. Fallback if service keys are not offered: **Development**, **Legacy apps**, **Create legacy app**,
   **Private**, with the same scopes.

Test in a developer test account (**Development**, **Testing**, **Test Accounts**). It is free and
carries a 90-day Enterprise trial, so custom objects can be tried. The API version is pinned to
`2026-09` in one constant. Source: `platforms/hubspot/reference/auth-and-setup.md`.

### Salesforce

No token goes in `.env`. The `sf` CLI keeps its own credentials. The repo holds only an org alias.
Variables: `SF_TARGET_ORG` (the org alias or username you logged in with), and optionally
`SF_API_VERSION` (default `67.0`) and `SF_CLI` (the program name or path, default `sf`). An org that
is not a sandbox or scratch org counts as production, and so does a Developer Edition org that is not
a sandbox: it needs `--execute --production` and the typed org name.

1. Install the `sf` CLI. Confirm the client's edition is Enterprise, Unlimited, Performance or Developer.
   Professional and Essentials cannot be built this way.
2. Create or request a sandbox (Setup, Environments, Sandboxes), or use a Developer Edition org.
3. Log in: `sf org login web --alias acme-sbx --instance-url https://acme--dev1.sandbox.my.salesforce.com`.
4. The build user needs API Enabled, Modify Metadata Through Metadata API Functions, and (to be
   confirmed in the first sandbox) Customize Application. Use a dedicated integration user, not a
   person's login. Permission sets also need View Setup and Configuration and Manage Profiles and
   Permission Sets.
5. Check the login: `sf org display --target-org acme-sbx --json`.
6. For CI or unattended runs use the JWT flow (`sf org login jwt`). The private key file stays outside
   the repo and its path comes from an environment variable.

API version is pinned to 67.0 in `sfdx-project.json`, `package.xml` and every `sf` call.
Source: `platforms/salesforce/reference/auth-and-setup.md`.

## Worked examples

The commands use a client called `acme` on HubSpot. Replace as needed. Output shapes come from the
tools' renderers; the counts depend on the design and the live CRM.

### Example 1: a new build

The client has an empty sandbox. The design is `clients/acme/design.yaml`, started from
`b2b-saas-sales-led`.

```bash
uv run python -m tools.validate clients/acme/design.yaml --strict
uv run python -m tools.generate clients/acme/design.yaml --platform hubspot
uv run python -m tools.crm_plan clients/acme/design.yaml --platform hubspot \
    --out clients/acme/build/plan.json
```

The plan prints changes grouped by risk, in build order, followed by manual steps:

```
Plan: hubspot, target (default)

SAFE (applied automatically): N
  1. [add_object] Add object Subscription
  2. [add_relationship] Add relationship subscription to company (many_to_one)
  3. [add_pipeline] Add pipeline New business on deal with N stages
  ...
  N. [add_field] Add select field Plan to subscription

MANUAL STEPS: M
  - [safe] ... (views, workflows, required fields per stage)
```

Show the plan to the client or the lead engineer and get agreement. Then a dry run:

```bash
uv run python -m tools.crm_apply clients/acme/build/plan.json --client acme
```

```
DRY RUN: nothing was changed. Pass --execute to apply.
Would apply: N
  - [add_object] Add object Subscription
  ...
Already in place (skipped): 0
Held for review (need --allow-review): 0
Failed: 0
Logged to clients/acme/build/apply-log/<timestamp>.json
```

Only when the user has asked for it:

```bash
uv run python -m tools.crm_apply clients/acme/build/plan.json --client acme --execute
```

Then re-plan. It must list no changes. Manual steps stay listed until a person does them, so a plan may still show them:

```bash
uv run python -m tools.crm_plan clients/acme/design.yaml --platform hubspot
uv run python -m tools.crm_drift clients/acme/design.yaml --platform hubspot
```

Do the manual steps from `clients/acme/hubspot/manual-steps.md`, then go to
[../checklists/go-live-qa.md](../checklists/go-live-qa.md).

### Example 2: an amendment that adds a field, an option and a stage

After sign-off (tag `acme-v1.0`) the client asks for three things: a billing contact email on
subscriptions, a new "Enterprise plus" plan, and a "Legal review" stage in new business. Edit
`clients/acme/design.yaml`, then:

```bash
uv run python -m tools.validate clients/acme/design.yaml --strict
uv run python -m tools.diff_design acme-v1.0:clients/acme/design.yaml clients/acme/design.yaml
```

The diff, as the tool prints it for this change (checked on the sales-led blueprint):

```
Design changes: design, target B2B SaaS, sales-led -> B2B SaaS, sales-led

SAFE (applied automatically): 3
  1. [add_stage] Add stage Legal review to New business
  2. [add_option] Add option Enterprise plus to subscription.plan
  3. [add_field] Add email field Billing contact email to subscription

3 automatic change(s), 0 manual step(s).
```

All three are `safe`: adds only. Regenerate, plan against the live CRM, show the plan, get agreement,
dry run, and apply only when asked:

```bash
uv run python -m tools.generate clients/acme/design.yaml --platform hubspot
uv run python -m tools.crm_plan clients/acme/design.yaml --platform hubspot --out clients/acme/build/plan.json
uv run python -m tools.crm_apply clients/acme/build/plan.json --client acme
```

Because the plan compares the design with live state, it contains only these three changes, even if
the first build was done weeks ago. Add an entry to `clients/acme/CHANGELOG.md`.

If the client also wants the stage's required fields enforced, that is a manual step on HubSpot and
Attio. On Salesforce the validation rule is generated.

### Example 3: a removal that shows as destructive

The client no longer uses the subscription's start date. Remove `start_date` from the design.

```bash
uv run python -m tools.diff_design acme-v1.0:clients/acme/design.yaml clients/acme/design.yaml
```

```
MANUAL STEPS: 1
  - [DESTRUCTIVE] Remove field subscription.start_date
      why: The design no longer contains this field. This tool never deletes fields.
      where: Open the object's settings in the CRM admin area.
      done when: The data in subscription.start_date is migrated or exported, the field is archived or deleted in the CRM, and re-planning shows no difference.
      how: 1. Export subscription.start_date with the record id. 2. Decide whether the data moves to another field or is retired. 3. Remove it from views, forms and automations. 4. Archive or delete the field. Export the data first. Never delete before the data is safe elsewhere.

0 automatic change(s), 1 manual step(s).
```

`crm_plan` shows the same step against the live CRM. `crm_apply` has nothing to apply for it:
it is not a change, and a plan edited by hand to contain one is refused. The engineer follows
[migration-playbook.md](migration-playbook.md): export the data, decide where it goes, remove the
field from views and automations, then archive or delete it in the CRM by hand. Re-run `crm_plan`.
The step disappears when the field is gone.

Until the manual step is done, `crm_drift` reports the field as drift, which is correct: the
design and the CRM disagree.

### Example 4: a rename that needs review

Changing the label of the stage "Proposal" to "Proposal sent" is a `needs_review` change.

```
NEEDS REVIEW (applied only with --allow-review): 1
  1. [rename_stage] Rename stage 'Proposal' to 'Proposal sent'
```

`crm_apply --execute` holds it:
the report lists it under "Held for review (need --allow-review)". Read it, confirm it with the
client, and only if the user asks, add `--allow-review`.

## When something fails

1. Read the report. It says what was applied, what failed with the API error, and what remains.
2. Do not re-run blindly. Re-plan first. The planner sees what has been done and plans only the rest.
3. Check the apply log in `clients/<client>/build/apply-log/`. It is redacted but still private.
4. If the error is a permission or plan-limit problem (403, `quota_exceeded`, an edition message),
   it is a decision for the client, not something to code around. Add it to `notes.md`.
5. If a tool refuses a run, the refusal is the answer. Do not search for a flag that gets past it.
