---
name: crm-builder
description: Build, amend and audit a client's CRM (Attio, HubSpot or Salesforce) from a company-type blueprint. Use when asked to set up a CRM for a type of company, add or change a field, stage, pipeline or object in a client's CRM, compare a live CRM with its design, or plan a CRM migration. Covers choosing a blueprint, discovery, editing design.yaml, validate, generate, plan, apply to a sandbox, QA, amendments and drift checks.
---

# CRM builder

Use this skill in the `crm-blueprints` repository. `design.yaml` is the source of truth. Platform
files and live CRMs follow it. Read `CLAUDE.md` first: its rules always apply.

All commands run as `uv run python -m tools.<name>`. Add `--help` for options.

## Hard rules

- Show the plan before applying. Wait for the user to agree.
- Never pass `--execute` unless the user explicitly asks. Never pass `--production`.
- Never pass `--allow-review` until the user has read the `needs_review` changes.
- Never invent stages, fields or objects the client did not describe. Label assumptions.
- Never delete or retype anything through the API. Removals and type changes are manual steps.
- Credentials come only from `.env`. Never print, log or commit them.
- Regenerate and validate after every design edit.

## 1. Understand the request

Work out which of these it is, and say which:

| Request | Go to |
|---|---|
| A new CRM for a new client | steps 2 to 9 |
| A change to an existing client's CRM | step 10 |
| "Is the CRM still as designed?" | step 11 |
| Reverse-engineer a CRM that already exists | step 12 |
| Move data into the CRM | `docs/migration-playbook.md` |

Ask for what is missing: the client's name, the platform, whether a sandbox or test account exists,
and the plan or edition they are on. Do not guess the platform.

## 2. Choose a blueprint

List `blueprints/*/README.md`. Match on the **sales motion and delivery**, not the industry label.
A short list:

| Blueprint | Pick when |
|---|---|
| `b2b-saas-sales-led` | Annual contracts sold by a sales team |
| `b2b-saas-product-led` | Self-serve sign-up with sales assist |
| `agency-marketing` | Retainers and projects for clients |
| `consultancy-professional-services` | Matters or engagements, conflict checks, billing models |
| `recruitment-agency` | Roles, candidates and placements |
| `executive-search` | Retained mandates with longlists and shortlists |
| `manufacturing-distribution` | Quotes, trade accounts, reorders |
| `wholesale-ecommerce-b2b` | Wholesale to retailers, with orders and territories |
| `real-estate-commercial` | Properties, leases, landlord and tenant roles |
| `financial-advisers` | Households, regulated data, review cycles |
| `investor-vc` | Deal flow and a portfolio |
| `education-training` | Programmes, cohorts, enrolments |
| `construction-trades` | Tenders, estimates, projects on sites |
| `healthcare-clinics-b2b` | Clinics selling to organisations; sensitive data rules |
| `events-sponsorship` | Sponsor and exhibitor sales per event |

Read the chosen blueprint's `README.md` and `design.yaml`. If two fit, take the closer and note the
other in `notes.md`. If none fits, take the nearest, and say the fit is partial.

## 3. Start the client workspace

```bash
uv run python -m tools.new_client <blueprint> <client> --name "Client Ltd"
```

The client name is lowercase letters, digits and hyphens. This creates `clients/<client>/` with
`design.yaml`, `notes.md`, `CHANGELOG.md` and `build/`. It refuses to overwrite an existing folder.

## 4. Run discovery

Use `docs/discovery-questions.md`: business, users, data model, pipelines, fields, automation,
migration. Ask the user (who talks to the client) for answers. Write them in
`clients/<client>/notes.md` under "Discovery".

- Only record what was said. If an answer is missing, write "not answered".
- Put plan-dependent choices in "Decisions" with the recommended default from the design.
- Put anything you proceed without in "Assumptions", and tell the user.

## 5. Edit the design

Edit `clients/<client>/design.yaml`. The format is in `model/schema.md`. Follow
`docs/design-principles.md` and `docs/naming-conventions.md`.

- Change only what discovery supports. Keep the blueprint's structure where the client agrees.
- Every custom field needs a `description` that says what it is for.
- Anything reported on is a `select`, with its full option list.
- Every stage has `exit_criteria` starting "Entered when", and every pipeline has won and lost stages.
- Keep delivery separate from selling.
- Add a `decisions` entry for each plan-dependent feature (for example HubSpot custom objects need
  Enterprise; Salesforce needs a supporting edition; Attio object limits depend on plan).
- Do not use real personal data in a design.

## 6. Validate and generate

```bash
uv run python -m tools.validate clients/<client>/design.yaml --strict
uv run python -m tools.generate clients/<client>/design.yaml
```

Fix every error and warning, then generate. Repeat after every design edit. The generator writes a
platform folder per platform, each with a `build-sheet.md` and `manual-steps.md`. Read
`manual-steps.md` to the user: it lists what the API cannot do.

Commit `design.yaml`, `notes.md`, `CHANGELOG.md` and the generated files together.

## 7. Plan

Needs credentials in `.env` for a **sandbox or test** account. See `docs/automated-builds.md` for
setup per platform. If credentials are missing, stop and tell the user what is needed. Do not ask
for the secret in chat.

```bash
uv run python -m tools.crm_pull --platform <p> --out clients/<client>/build/state.json   # optional
uv run python -m tools.crm_plan clients/<client>/design.yaml --platform <p> \
    --out clients/<client>/build/plan.json
```

`crm_plan` never writes to the CRM. Show the user:

1. **Safe** changes (adds).
2. **Needs review** changes (renames, reorders, hiding options or stages).
3. **Manual steps**, especially anything marked destructive.

Say plainly what is not automated on this platform. See `docs/platform-comparison.md`.

## 8. Apply to the sandbox

Always the dry run first:

```bash
uv run python -m tools.crm_apply clients/<client>/build/plan.json --client <client>
```

Show the result. Only if the user has explicitly asked to execute:

```bash
uv run python -m tools.crm_apply clients/<client>/build/plan.json --client <client> --execute
```

Add `--allow-review` only for `needs_review` changes the user has read and approved. Never add
`--production`.

After an execute run:

- Read the report: applied, skipped, held, failed, remaining.
- On a failure the run has stopped. Report the error, re-plan, and do not retry blindly.
- Re-run `crm_plan`. No changes should remain. Manual steps will.
- Then do the manual steps with the user, using `build-sheet.md` and `manual-steps.md`.

## 9. QA and sign-off

1. Work through `checklists/go-live-qa.md` with dummy records.
2. Run `crm_drift`. Exit 0 means the CRM matches the design.
3. When the client signs off, commit the client folder and tag it: `git tag <client>-v1.0`.
4. Moving to a live account is done by the user, at their own keyboard, who types the account name
   when asked. You do not run it.

## 10. Amend an existing build

The client wants a change to a CRM that is already built.

1. Read `clients/<client>/notes.md` and `CHANGELOG.md`.
2. Edit `design.yaml` for the change only.
3. Validate, then show the diff against the last sign-off tag:

   ```bash
   uv run python -m tools.validate clients/<client>/design.yaml --strict
   uv run python -m tools.diff_design <client>-v1.0:clients/<client>/design.yaml clients/<client>/design.yaml
   ```

4. Read the risks to the user:
   - **Safe:** add field, add option, add stage, add object, add relationship, add pipeline.
   - **Needs review:** renames, reorders, stage type or probability changes, hiding an option or stage.
   - **Destructive (manual):** removing a field, object, relationship or pipeline; changing a field's
     type or a relationship's cardinality. Follow `docs/migration-playbook.md`. Never work around it.
5. Regenerate. Plan against the live CRM. Show the plan. Dry run. Execute only when asked.
6. Re-plan until it is empty. Add a dated entry to `CHANGELOG.md`: what, why, who asked.

A key rename reads as remove-and-add. Check the diff before agreeing to rename a key. Labels can change.

## 11. Audit with drift

```bash
uv run python -m tools.crm_drift clients/<client>/design.yaml --platform <p>
```

Exit 0 means no drift. Exit 1 lists the differences, including things in the CRM that the design
does not have. For each difference, ask the user which is right: update the design, or have the
CRM put back. Do not change the CRM yourself. Pair this with `checklists/monthly-data-quality.md`.

## 12. Read a CRM that has no design

```bash
uv run python -m tools.crm_pull --platform <p> --to-design clients/<client>/draft-design.yaml
```

This writes a draft. Every description is a TODO, so it fails validation until a person writes what each
field is for. Do not make up descriptions. Ask the client, or leave them as TODO and say so.

## Platform reminders

| | Attio | HubSpot | Salesforce |
|---|---|---|---|
| Sandbox | None. Use a separate workspace and set `ATTIO_TARGET` | Developer test account | Sandbox or Developer Edition |
| Needs | Plan with enough objects | Custom objects: Enterprise | Enterprise, Unlimited, Performance or Developer edition to deploy |
| Manual | Workflows, views, won/lost flags, stage rules | Workflows, views, stage rules, permissions | Flows, view sort, permission assignment, page layouts |

<!-- confirm once adapters land: the table above against the HubSpot and Salesforce adapters -->

## Stop and ask when

- The user has not said which platform, or whether an account is a sandbox.
- Credentials are missing, or a tool refuses a run. Report it as printed.
- The plan has a destructive manual step.
- The client's plan or edition cannot support the design.
- You are about to add a stage, field or object the client did not describe.
- Anything seems to need `--production`, `--allow-review` or a hand-edited plan file.

## More detail

- `README.md`: the engagement workflow in one table.
- `docs/automated-builds.md`: how adapters work, the nine safety rules, credentials, worked examples.
- `docs/build-sequence.md`, `docs/migration-playbook.md`, `docs/platform-comparison.md`.
- `docs/discovery-questions.md`, `docs/design-principles.md`, `docs/naming-conventions.md`.
- `platforms/<crm>/README.md` and `reference/`: research, sources and open questions.
- `checklists/`: go-live QA and monthly data quality.
