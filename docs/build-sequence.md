# Build sequence

The order of work for a build. It is principle 9 in [design-principles.md](design-principles.md).
The planner applies changes in this order. The generated `build-sheet.md` lists tasks in this order.

Each step needs the one before it. Skipping ahead causes rework or a half-built CRM.

| # | Step | Why here | Done when |
|---|---|---|---|
| 0 | Decisions | Plan-dependent choices (edition, custom objects, native Deals) change everything after them. | Every `decisions` entry has an answer recorded in `notes.md`. |
| 1 | Objects | Everything else attaches to an object. | Each custom object exists with its plural name. |
| 2 | Relationships | A link needs both objects. Pipelines and fields may reference linked records. | Each link exists, with the right cardinality and a label on each side. |
| 3 | Pipelines and stage rules | Stages need their object. Stage rules name fields, which step 4 creates, so a stage rule is only complete once step 4 is done. | Each pipeline exists with its stages in order, won and lost marked as far as the platform allows. |
| 4 | Fields | Fields need their object. Select fields need their options. | Each field exists with the right type, options and description. |
| 5 | Automations | Triggers and actions refer to objects, fields and stages. | Each automation exists, is tested on a dummy record and is switched on. |
| 6 | Views | Views filter and sort on fields and stages. | Each view exists and shows the expected dummy records. |
| 7 | QA and go-live | Proves the whole build. | [../checklists/go-live-qa.md](../checklists/go-live-qa.md) is complete. |

About step 3: the planner's passes run objects, relationships, pipelines, then fields, as the
tests require (DECISIONS D-8). A platform that checks stage-rule fields at creation time handles the
ordering inside its adapter or generator. <!-- confirm once adapters land: how the Salesforce generator orders stage-gating validation rules against fields -->

## What is automated and what is by hand

| Step | Attio | HubSpot | Salesforce |
|---|---|---|---|
| Objects | Automated | Automated; custom objects need Enterprise | Automated |
| Relationships | Automated | Automated; labels need Professional or Enterprise | Automated |
| Pipelines | Automated (list plus status) | Automated | Automated |
| Stage rules | Manual | Manual | Automated (validation rules) |
| Fields | Automated | Automated | Automated |
| Automations | Manual | Manual | Manual |
| Views | Manual | Manual | Automated (list views, no sort) |
| Permissions | Manual | Manual | Permission set automated; assignment manual |

Sources: each platform's `reference/api-coverage.md`. Manual work is listed with UI paths in the
client's generated `manual-steps.md`.

## During a build

1. Work in the sandbox or test account.
2. Dry run, read the plan, then execute. See [automated-builds.md](automated-builds.md).
3. Do the manual steps in order. Tick them off in `build-sheet.md`.
4. Re-run `crm_plan`. The plan should contain no changes. If it does, find out why before going on.
5. Seed a few dummy records to test stages, required fields, automations and views.
6. Remove the dummy records before go-live.

## During an amendment

1. `diff_design` the old and new designs. Read the risk of each change.
2. Validate, generate, plan against the live CRM, show the plan, then apply.
3. Complete the manual steps the plan lists, especially destructive ones. See
   [migration-playbook.md](migration-playbook.md).
4. Re-plan until it is empty. Add an entry to `CHANGELOG.md`.
