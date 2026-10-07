# Handoff

Status at 2026-10-07. Everything described here is built and tested against in-memory simulators.
**No live CRM has been exercised.** Every API shape was taken from vendor documentation, so the first
live run on each platform is the real acceptance test. Section 6 says how to do it.

Contents: 1 What was built. 2 Automated and manual, per platform. 3 Plan- and edition-dependent
features. 4 Open questions. 5 How it was tested. 6 Recommended next steps. 7 Definition of done.

## 1. What was built

| Part | Where | What it is |
|---|---|---|
| Platform research | `platforms/<crm>/reference/` | Ten files per platform (objects, fields, relationships, pipelines, views, automation, auth, limits, `api-coverage.md`, `open-questions.md`). Each has sources and a "Last verified" date. |
| Core model and design format | `model/` | `core-model.yaml` (shared objects and fields) and `schema.md` (the design file format). |
| 15 blueprints | `blueprints/<name>/` | A `design.yaml` and README each, plus the generated `attio/`, `hubspot/` and `salesforce/` folders (45 generated folders). |
| Design tools | `tools/design.py`, `validate.py`, `new_client.py`, `diff_design.py` | Load and merge a design, validate it (`--strict` makes warnings fail), start a client from a blueprint, and compare two designs with risk classes. |
| Generators | `tools/generators/{attio,hubspot,salesforce}.py`, `tools/generate.py` | Turn a design into API payloads (Attio, HubSpot) or SFDX source with `package.xml` (Salesforce), a `build-sheet.md` and a `manual-steps.md`. `--check` fails if committed output is stale. |
| Adapters | `tools/crm/{attio,hubspot,salesforce}.py` | Read live state, plan against a design, apply. One interface (`tools/crm/base.py`), one planner (`planner.py`), one safety module (`safety.py`). |
| CRM tools | `tools/crm_pull.py`, `crm_plan.py`, `crm_apply.py`, `crm_drift.py` | Pull state, plan, apply (dry run by default), and drift. |
| Docs and skill | `README.md`, `CLAUDE.md`, `docs/`, `checklists/`, `skills/crm-builder/` | Workflow, principles, discovery questions, naming, build sequence, migration playbook, platform comparison, automated builds, go-live and monthly checklists. |
| Tests and CI | `tests/`, `.github/workflows/ci.yml` | 566 tests (section 5). CI runs validate, generate `--check` and pytest. |
| Decisions | `DECISIONS.md` | D-1 to D-23: every judgement call, with why and what would change it. Read D-19 (Salesforce adapter) and D-21 to D-23 first. |

Public use (D-16): no real company, person or account data, and no internal names or local paths.
`tests/test_public_safe.py` scans for them. The licence is MIT (`LICENSE`).

## 2. Automated and manual, per platform

"Automated" means a plan change that `crm_apply` makes. "Manual" means a step in the plan and in the
generated `manual-steps.md`, with a UI path and a "done when". Detail: each `api-coverage.md`.

| Step | Attio | HubSpot | Salesforce |
|---|---|---|---|
| Read live state, plan, drift | Automated (REST) | Automated (REST, API version `2026-09`) | Automated (`sf` CLI describe, query, retrieve) |
| Custom objects | Automated | Automated, **Enterprise only** | Automated |
| Fields (14 types) | Automated; percent is lossy | Automated; currency, percent, URL and email are lossy | Automated |
| Select options: add | Automated | Automated | Automated |
| Select options: remove | Archive, needs `--allow-review` | Hide, needs `--allow-review` | Deploy as inactive, needs `--allow-review` |
| Relationships | Automated | Automated; labels and cardinality need Professional or Enterprise | Automated (lookup, master-detail, junction object) |
| Pipelines and stages | Automated, as a list with a status field | Automated; won or lost and probability on deals only | Automated on Opportunity (business process, record type, path); a restricted stage picklist on other objects |
| Stage added mid-pipeline | Add is automatic; the reorder is manual (no order control) | Add is automatic; the reorder is a `needs_review` change | Add is automatic; the reorder is manual |
| Stage removed | Archive, needs `--allow-review` | Manual | Manual on Opportunity; inactive picklist value elsewhere |
| Required fields per stage | Manual | Manual | Automated, as validation rules |
| Automations | Manual | Manual (workflow API is beta) | Manual (flows are not generated) |
| Views | Manual (read-only API) | Manual | List views automated without sort; sort and complex filters manual |
| Permissions | Manual | Manual | Permission set generated for field access; deploying it and assigning it are manual |
| Renames, type changes, reorders | Rename `needs_review` (applied with `--allow-review`); reorder and type change manual | Rename and reorder `needs_review`; type change, custom object rename and stage removal manual | All manual (a file's full name is its identity) |
| Removing an object, field, relationship or pipeline | Destructive manual step, never applied | Same | Same |
| Sandbox | None. A separate workspace, labelled in `ATTIO_TARGET` | Developer test account | Sandbox, scratch org (not production) |

Never automated on any platform: deleting or archiving an object, field, relationship or record,
changing a field type in place, and applying a `destructive` change.

## 3. Plan- and edition-dependent features

Each blueprint's `plan-requirements.md` (HubSpot) and README name what that design needs. Flag these
as decisions in discovery, before the build.

- **Salesforce edition.** The Metadata API works on Enterprise, Unlimited, Performance and Developer
  editions. On Professional or Essentials (or any edition not in that list) `plan` turns every change
  into a manual step that points at the build sheet, and `apply` deploys nothing and does not fail.
  Allowances (custom objects and fields per object) are secondary-source figures; the plan warns at
  75 percent of them.
- **Salesforce production.** An org that is not a sandbox or scratch org is production. A Developer
  Edition org that is not a sandbox counts as production too (D-19).
- **HubSpot tier.** Custom objects need Enterprise (typically 10 object definitions). Association
  labels and cardinality need Professional or Enterprise. Required fields per stage are UI-only
  (assumed Professional or higher). Custom-object stages carry open or closed only, not won or lost
  or probability. Objects beyond the account's limit, and everything depending on them, become manual
  steps.
- **Attio plan.** Object count depends on the plan (Free up to 3, Plus 5, Pro 12, Enterprise
  unlimited, per the pricing page; whether the standard objects count is unknown). Deals must be
  enabled by an admin in the UI. Workflows are on every plan, with credit limits.
- **Attio has no sandbox,** and the tool cannot tell a test workspace from a live one. `ATTIO_TARGET`
  must be set only for a test workspace.
- **Regulated data.** A field described as "DATA PROTECTION:" gets Salesforce compliance labels
  (`PII;GDPR`, `Confidential`, or `Restricted`). These are labels, not encryption. Shield Platform
  Encryption, HubSpot Sensitive Data and Attio's equivalents are separate paid features.

## 4. Open questions

The full lists are in `platforms/<crm>/reference/open-questions.md` and `DECISIONS.md`. These are the
ones that matter, grouped by whether a live run is needed to settle them. **Points marked LIVE need a
first run in a test account or sandbox to confirm.** Record each answer in the open-questions file.

### 4.1 Needs a first live run

**Attio**

- LIVE: whether a new status attribute starts empty or with default statuses (Q6). The adapter lists
  them and never archives extras.
- LIVE: the cardinality flags. Create one test relationship in a throwaway workspace, read it back and
  check the reverse attribute's `is_multiselect` (Q7).
- LIVE: whether a required attribute without a default is accepted (Q5). The adapter creates all
  attributes not required and tightens afterwards.
- LIVE: whether an archived attribute, option or status still blocks its slug or title (Q9). The
  adapter assumes it does and makes restoring a reviewed manual step.
- LIVE: that `409 slug_conflict` and the Retry-After format (seconds or a date) behave as assumed
  (Q12, Q13), and that status order follows creation order (Q10).
- LIVE: Deals enabled or not, and the native `stage` on Deals (Q3, Q8). Pipelines are built as lists.
- Every create body in `tools/generators/attio.py` is from the OpenAPI spec, not recorded output.

**HubSpot**

- LIVE: the account-information call. `GET /account-info/v3/details` and its response shape are not
  confirmed (D-15). Without it the production prompt falls back to the portal id from a custom
  object's `fullyQualifiedName`, and then to `HUBSPOT_TARGET` alone.
- LIVE: the custom-object limits response (`GET /crm/limits/{V}/custom-object-types`) has no
  documented shape. The adapter reads any `maxLimit` or `limit` and `usage` number (D-15).
- LIVE: the "already exists" status and category for property, group, schema, pipeline, label and
  list creates (OQ-10). Until then the adapter reads before it writes.
- LIVE: stage reorder with `PATCH .../stages/{id}` and `displayOrder` (the body is not shown in the
  docs), and `isClosed` on custom-object stages (OQ-1).
- LIVE: whether a first association between two existing objects can be created without a label
  (OQ-7), whether the create-schema body needs all nine fields (OQ-4), and how percent displays (OQ-5).
- LIVE: the association label limit (10 or 50, OQ-2) and the scopes a label call needs (OQ-14).
- LIVE: that `2026-09` is accepted on every path used (OQ-13).

**Salesforce** (every fixture is authored from documented shapes, not recorded, D-2)

- LIVE, first: `sf org display --json`, `sf data query` on `Organization`, `sf sobject list` and
  `describe` return the shapes the adapter reads (`tests/fixtures/salesforce/README.md`).
- LIVE: the wildcard `sf project retrieve start` of `BusinessProcess` and `RecordType` (D-19). If it
  fails, the plan notes it and assumes the design's stages that exist.
- LIVE: one field of each of the 14 types deployed check-only, then for real (E1). Record every error.
- LIVE: a second deploy of the same files reports every component `Unchanged`, and a retrieve back
  differs from what was sent only in elements Salesforce adds (G, steps 2 and 4).
- LIVE: whether a field-file deploy puts a new picklist value mid-order, and whether a business
  process keeps design order (D-23). The adapter reads Opportunity order but not a custom object's.
- LIVE: how `OpportunityStage` behaves on deploy: default stages staying (E10), and whether a source
  deploy can deactivate one. Until known, an Opportunity stage removal is a manual step.
- LIVE: record-type picklist values (E4), the `__Master__` path record type (E11), global value set
  naming (E8), master-detail sharing (E7), the sales-process minimum (E9).
- LIVE: permission-set field and object rules (E16) and list view `sharedTo` and filter tokens (E12).
  The permission set and list views are deployed by hand, never by a change.
- LIVE: deploy API-call cost per phase (E18, `sf org list limits` before and after), and the minimum
  build-user permissions (C1: "Customize Application" or not).

### 4.2 Decisions and limits to know (not live-run questions)

- **Pricing and tier facts are secondary.** HubSpot object limits (OQ-3), Salesforce allowances (B2)
  and Attio object counts (Q2) come from catalogues and third-party sources. Check the client's real
  plan in discovery.
- **API version.** Salesforce is pinned to 67.0 (`SF_API_VERSION` overrides); the guides are 68.0
  (D1). HubSpot is pinned to `2026-09`.
- **No read-only metadata permission on Salesforce** (C2). A build user that can retrieve can also
  deploy. The safety is in the tool (dry run by default, no destructive flags), not the permission.
- **Shared stage names (D-23).** Two Opportunity pipelines that share a stage label get the value
  "label (pipeline name)" when type or probability differ. Remove the stage from one and the other is
  renamed in the design's eyes, so the next plan asks to add a value the org holds under the old name.
- **Drift is partial (D-23).** Only Salesforce marks manual steps that stand for a difference. A
  pending stage reorder on Attio is not reported as drift.
- **Gaps in the design format:** view sort and automations are manual everywhere; `one_to_one` has
  no unique lookup on Salesforce; stage-gating validation rules also fire on API and bulk writes, so
  a data import needs a bypass that is not designed yet (F in the Salesforce open questions).
- **Page layouts, tabs and apps** on Salesforce are manual steps (E5, E6).

## 5. How it was tested

No live CRM has been exercised. Every test runs offline with in-memory simulators:
`tests/attio_stub.py`, `tests/hubspot_stub.py` and `tests/salesforce_stub.py` (a stand-in for the `sf`
CLI that checks the manifest against the files written and cross references, so a record type or rule
naming a missing field fails as it would in an org).

| Suite | Files | Tests |
|---|---|---|
| Unit: design, validation, planner, safety, generators, adapters, CLIs | `test_design`, `test_validate`, `test_planner`, `test_safety`, `test_plan_json`, `test_generate`, `test_generator_*`, `test_crm_*`, `test_cli_*` | 431 (includes 3 live tests, skipped) |
| End to end | `test_end_to_end.py` | 117 |
| Public safety | `test_public_safe.py` | 18 |
| **All** | | **566 collected: 563 passed, 3 skipped** |

The end-to-end suite drives the real command-line entry points (`new_client`, `crm_plan`, `crm_apply`,
`crm_drift`, `diff_design`) with the real registry and adapters; only the HTTP session (Attio,
HubSpot) or the `sf` runner (Salesforce) is a simulator. Every one of the 15 blueprints runs on
all three platforms through: new client, plan in build order, dry run changes nothing, execute builds
with a redacted log, re-plan gives zero changes and re-applying is a no-op, an amendment (add field,
add option, add stage, remove field) makes three safe changes and one destructive manual step that
deletes nothing, drift is clean after a build and names a leftover and an extra added by hand, and the
production gate refuses every unsafe route. Salesforce has extra cases: a Developer Edition org that
is production, a Professional edition org (manual steps only, nothing deployed), a refused deploy that
stops and resumes, and a deal-stage removal.

**The 3 skipped tests are the live smoke tests** (`@pytest.mark.live`), one per platform. Each skips
unless its credentials are set, so a normal run never touches a CRM:

- `tests/test_crm_attio.py`: needs `ATTIO_ACCESS_TOKEN` and `ATTIO_TARGET` (a test workspace).
- `tests/test_crm_hubspot.py`: needs `HUBSPOT_ACCESS_TOKEN` and `HUBSPOT_TARGET` (a developer test account).
- `tests/test_crm_salesforce.py`: needs the `sf` CLI on `PATH` and `SF_TARGET_ORG` (an authorised alias).

Each pulls, plans, applies and checks the re-plan is empty, against a sandbox. The Salesforce one
refuses a production org.

The newest tests were shown to bite by breaking the code, watching them fail and restoring a backup.
Logging a declined change as applied failed the Professional edition test and its unit regression.
Ignoring drift manual steps failed the same Professional test and its unit regression. Removing the
Salesforce adapter's production check failed all 15 `test_production_gate_salesforce` cases.

## 6. Recommended next steps

Do these in order. Use a test account each time, never a client's live one. Each step has three
parts: set up, run the live smoke test, then the same journey by hand through the CLIs. Stop and read
the output after each stage. Fix what differs from the documentation, add a test that reproduces it,
and record the answer in the platform's `open-questions.md`.

Set the variables for the test (they are not read by `pytest` from `.env`):

```bash
cp .env.example .env                    # then fill in the platform's variables
set -a; . ./.env; set +a                # export them for pytest
```

### 6.1 Attio test workspace

Create a separate free workspace (Attio has no sandbox). Create an access token with
`object_configuration:read-write` and `list_configuration:read-write`. In `.env` set
`ATTIO_ACCESS_TOKEN` and `ATTIO_TARGET=sandbox`.

```bash
uv run pytest -m live tests/test_crm_attio.py -rs
uv run python -m tools.new_client b2b-saas-sales-led live-attio --name "Live Attio test"
uv run python -m tools.crm_pull --platform attio --out clients/live-attio/build/state.json
uv run python -m tools.crm_plan clients/live-attio/design.yaml --platform attio --out clients/live-attio/build/plan.json
uv run python -m tools.crm_apply clients/live-attio/build/plan.json --client live-attio             # dry run
uv run python -m tools.crm_apply clients/live-attio/build/plan.json --client live-attio --execute
uv run python -m tools.crm_plan clients/live-attio/design.yaml --platform attio                     # expect no changes
uv run python -m tools.crm_drift clients/live-attio/design.yaml --platform attio                    # expect exit 0
```

Check in the UI: the objects, the pipeline list and its statuses, and the relationship's reverse side
(Q7). Then amend the design (add a field, an option and a stage, remove a field), run
`diff_design`, `crm_plan` and `crm_apply --execute` once more, and confirm nothing was deleted.

### 6.2 HubSpot developer test account

Create a developer test account (Development, Testing, Test Accounts). It carries a 90-day Enterprise
trial, so custom objects work. Create a service key with the schema and object scopes in
`.env.example`. Set `HUBSPOT_ACCESS_TOKEN` and `HUBSPOT_TARGET=dev-test`.

```bash
uv run pytest -m live tests/test_crm_hubspot.py -rs
uv run python -m tools.new_client b2b-saas-sales-led live-hubspot --name "Live HubSpot test"
uv run python -m tools.crm_pull --platform hubspot --out clients/live-hubspot/build/state.json
uv run python -m tools.crm_plan clients/live-hubspot/design.yaml --platform hubspot --out clients/live-hubspot/build/plan.json
uv run python -m tools.crm_apply clients/live-hubspot/build/plan.json --client live-hubspot             # dry run
uv run python -m tools.crm_apply clients/live-hubspot/build/plan.json --client live-hubspot --execute
uv run python -m tools.crm_plan clients/live-hubspot/design.yaml --platform hubspot                     # expect no changes
uv run python -m tools.crm_drift clients/live-hubspot/design.yaml --platform hubspot                    # expect exit 0
```

First read the plan's target: it should show the portal id (D-15). Then check the open points in
4.1: the account-information call, the limits call, duplicate-create responses and stage reorder (the
amendment leaves one `needs_review` reorder; apply it with `--allow-review` once you have read it).

### 6.3 Salesforce scratch org

Install the `sf` CLI (`@salesforce/cli`). Create a scratch org from a Dev Hub, or use a Developer
Edition sandbox. Sign in once: `sf org login web --alias client-sbx` (add `--instance-url` for a
sandbox). Set `SF_TARGET_ORG=client-sbx`. A scratch org is not production; a Developer Edition org
that is not a sandbox is, and needs `--production`.

```bash
sf org display --target-org client-sbx --json                       # check the login (do not paste the output anywhere)
uv run pytest -m live tests/test_crm_salesforce.py -rs
uv run python -m tools.new_client b2b-saas-sales-led live-sf --name "Live Salesforce test"
uv run python -m tools.crm_plan clients/live-sf/design.yaml --platform salesforce --out clients/live-sf/build/plan.json
uv run python -m tools.crm_apply clients/live-sf/build/plan.json --client live-sf             # one check-only deploy
uv run python -m tools.crm_apply clients/live-sf/build/plan.json --client live-sf --execute
uv run python -m tools.crm_plan clients/live-sf/design.yaml --platform salesforce             # expect no changes
uv run python -m tools.crm_drift clients/live-sf/design.yaml --platform salesforce            # expect exit 0
```

Before the full build, run the "first live run checklist" (Section G of
`platforms/salesforce/reference/open-questions.md`) with the generated `package.xml` in
`clients/live-sf/salesforce/`: one field of each type check-only, then for real; deploy again and
expect `Unchanged`; retrieve back and diff. A failed deploy leaves its staging folder under
`clients/live-sf/build/salesforce/`. Then deploy the permission set and list views by hand (the plan
lists the command), assign the permission set to a test user, and check field access.

### 6.4 After the three live runs

1. Replace the authored fixtures in `tests/fixtures/` with recorded ones (remove any token first) and
   update the fixture READMEs.
2. Settle D-23: decide on stable Opportunity stage value names, and on reading a custom object's
   stage order.
3. Make the repository public only after the public-safety test passes on the final tree and the
   owner agrees. It is created private first (BRIEF section 10); there is no remote yet.

## 7. Definition of done

BRIEF section 12, item by item. Commands were run from the repository root on 2026-10-07. "Not a
live result" marks anything proven only against simulators.

- [x] **Reference docs for all three platforms, each with sources and dates; `api-coverage.md`
  covers every design concept.** `ls platforms/*/reference` lists 10 files for each platform;
  `grep -L "Last verified" platforms/*/reference/*.md` prints nothing, so all 30 carry a source block and a
  date. Coverage was checked by reading each table against the design concepts (objects, 14 field
  types, options, relationships, pipelines, stages, stage rules, views, automations, permissions);
  there is no automated check of that.
- [x] **15 blueprints, each validating with zero warnings, each with a README.**
  `uv run python -m tools.validate --all --strict` printed `15 design(s) checked: 0 error(s), 0
  warning(s)`. `ls blueprints | wc -l` is 15 and every folder has a `README.md`.
- [~] **Platform structures generated for all 15 blueprints x 3 platforms, matching documented
  API/metadata formats.** `uv run python -m tools.generate --all --check` exits 0 and reports every
  file up to date; `ls -d blueprints/*/attio blueprints/*/hubspot blueprints/*/salesforce` finds 45
  folders. The formats match the documentation as read; none has been accepted by a real API yet
  (section 4.1). Not a live result.
- [x] **Pull, plan, apply, drift and diff tools working; apply tested against fixtures, and against
  sandboxes if credentials were provided.** The 117 end-to-end tests drive `crm_plan`, `crm_apply`,
  `crm_drift` and `diff_design` for every blueprint on every platform; `test_cli_read_only.py` covers
  `crm_pull`. No credentials were provided, so no sandbox run happened; the three live tests skip.
- [x] **Amending a blueprint (add field, add option, add stage, remove field) produces the right
  changes, with the removal marked destructive.**
  `uv run pytest tests/test_end_to_end.py -k "test_blueprint_builds_amends_and_drifts"` passed 45 of
  45 (15 blueprints x 3 platforms): three safe changes, one destructive manual step, no `DELETE`
  sent, the field still in the org afterwards.
- [x] **All safety rules enforced and tested.** The nine rules and their tests are in
  `docs/automated-builds.md`. `uv run pytest tests/test_safety.py tests/test_cli_apply.py
  tests/test_public_safe.py` passes, and the production gate runs per blueprint per platform
  (`test_production_gate`, `test_production_gate_salesforce`).
- [~] **CI green.** The steps of `.github/workflows/ci.yml` were run locally in order: `uv sync`;
  `uv run python -m tools.validate --all --strict` (0 errors, 0 warnings);
  `uv run python -m tools.generate --all --check` (exit 0); `uv run pytest` (563 passed, 3 skipped).
  GitHub Actions has not run: the repository has no remote yet.
- [x] **Docs, `CLAUDE.md` and skill complete.** a `git grep` for the confirmation marker comments (the ones that began "confirm once", in
  README.md, docs/ and the skill) prints nothing. `README.md`, `CLAUDE.md`, `skills/crm-builder/SKILL.md`, seven files in `docs/` and two in
  `checklists/` exist, and the variable names in them match the adapters (`ATTIO_ACCESS_TOKEN`,
  `ATTIO_TARGET`, `HUBSPOT_ACCESS_TOKEN`, `HUBSPOT_TARGET`, `SF_TARGET_ORG`, `SF_API_VERSION`,
  `SF_CLI`). `uv run pytest tests/test_public_safe.py` passes (18).
- [x] **`HANDOFF.md` at the root.** This file.

Not part of section 12 and not done: Phase 7, publishing (the repository has no remote, and this
round's changes are uncommitted).
