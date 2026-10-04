# Go-live QA checklist

Use before a CRM goes live for a client, and again after a large amendment. Copy it into
`clients/<client>/notes.md` and tick each line. Do the work in the sandbox or test account first, then
repeat the items marked **(live)** in the live account after the engineer has promoted the build.

Client: ______________  Platform: ______________  Design version / tag: ______________
Tester: ______________  Date: ______________

## 1. Design and tooling

- [ ] `uv run python -m tools.validate clients/<client>/design.yaml --strict` passes.
- [ ] `uv run python -m tools.generate clients/<client>/design.yaml` has been run and the output is committed with the design.
- [ ] Every `decisions` entry has an answer written in `notes.md`.
- [ ] Every assumption is listed in `notes.md` and the client has seen the list.
- [ ] `uv run python -m tools.crm_plan ... --platform <p>` lists no changes. Only manual steps the client has accepted remain.
- [ ] `uv run python -m tools.crm_drift ... --platform <p>` exits 0, or every difference is explained in `notes.md`.
- [ ] The latest apply log is in `clients/<client>/build/apply-log/` and shows no failed change.

## 2. Plan and edition

- [ ] The client's plan or edition supports every feature in the design (HubSpot custom objects: Enterprise; Salesforce Metadata API: Enterprise, Unlimited, Performance or Developer; Attio object limit).
- [ ] The platform's `plan-requirements.md` (HubSpot) or the blueprint README fallback has been read, and any fallback chosen is recorded.

## 3. Manual steps

- [ ] Every item in `manual-steps.md` is done, or has a named owner and date.
- [ ] Workflows and automations from the design exist, are switched on, and have been tested.
- [ ] Saved views exist and are shared with the right users or teams.
- [ ] Stage-required fields are set up (manual on HubSpot and Attio; check the validation rules on Salesforce).
- [ ] Default stages, fields or views that do not belong to the design are hidden or noted.
- [ ] Any destructive manual step from an amendment is done and re-planning no longer lists it.

## 4. Structure

- [ ] Each object has the right name and plural name.
- [ ] Each relationship appears on both records, with a clear label on each side.
- [ ] Each pipeline has the stages in the design's order.
- [ ] Won and lost stages exist. Lost requires a reason.
- [ ] Select fields have the full list of options and no stray extras.
- [ ] Every custom field has a description visible to users where the platform allows it.
- [ ] Fields hold the right type (dates are dates, money is currency, lists are selects).

## 5. Test with dummy records

Create dummy records. Mark them clearly (for example the name starts `ZZ TEST`). Do not use real
people's details.

- [ ] Create a company, a person and a deal. Link them. All links show on all three records.
- [ ] Move the deal through every stage. A stage with required fields refuses the move when they are blank, or the build sheet says why it cannot.
- [ ] Mark the deal lost without a reason. It is refused or flagged.
- [ ] Mark it won. Anything that should be created (a subscription, an onboarding, a matter) is created.
- [ ] Each automation fires once, on the right trigger, and does the right thing.
- [ ] Each saved view shows the dummy records it should, and not others.
- [ ] A user with the least access can see what they need and nothing more.
- [ ] Sensitive fields (flagged "DATA PROTECTION" in descriptions, or in the blueprint README) are visible only to the roles agreed.
- [ ] Delete the dummy records. Check no automation left stray records behind.

## 6. Data (if migrated)

- [ ] Record counts match the source for each object. Differences are explained.
- [ ] 20 sampled records per object match the source field by field.
- [ ] No duplicate people (match on email) or companies (match on domain).
- [ ] Owners are set. No records are owned by the integration user.
- [ ] Required dates and amounts are filled on open deals.
- [ ] Consent and marketing-status flags came across.
- [ ] The raw export is stored in `clients/<client>/raw/` (git-ignored) or deleted, as agreed.

## 7. Access and credentials

- [ ] Users are invited with the right roles and teams.
- [ ] The build token or key is removed or reduced to read-only, as the client wants. Nothing is left in a shared place.
- [ ] No credential is in the repo, a ticket or a chat.

## 8. Training and handover

- [ ] The client's admin has been walked through the pipelines, required fields and views.
- [ ] The client has the list of manual steps still open, with owners.
- [ ] The client knows how to ask for a change (a request that produces a `design.yaml` edit and a plan).
- [ ] The first monthly data-quality check is in the calendar ([monthly-data-quality.md](monthly-data-quality.md)).

## 9. Sign-off

- [ ] The client has signed off in writing.
- [ ] The client folder is committed and tagged: `git tag <client>-v1.0 -m "<Client> signed off"`.
- [ ] `CHANGELOG.md` has the entry for this release.
- [ ] Production changes were made by the engineer at the keyboard, with the account name typed at the prompt. They were not made through an agent.
