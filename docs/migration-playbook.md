# Migration playbook

How to move data into a new or amended CRM safely, and how to do the destructive manual steps that
the planner emits. The tools never delete or retype anything. They archive, hide or deactivate only an option or a
stage, and only with `--allow-review`. A person does these steps, in the sandbox first.

## Rules

1. Take a backup before every step that cannot be undone. Export with record IDs.
2. Rehearse in the sandbox. Record IDs differ between sandbox and production on every platform, so
   never copy IDs across.
3. Structure first, data second. Build and sign off the structure (see [build-sequence.md](build-sequence.md)),
   then load data.
4. Load in a fixed order: companies, people, then records that link to them (deals, custom objects).
5. Match on a stable key. People match on email. Companies match on domain or a client-supplied ID.
   Never load the same human twice (principle 2).
6. Check counts after every load. Compare the source count with the loaded count and sample records.
7. Personal data stays out of this repo. Raw exports go in `clients/<client>/raw/`, which is
   git-ignored. Delete them when the engagement ends, as the contract says.
8. Run no automations during a bulk load unless they are meant to fire. Switch them off, load, switch them on.
9. Validation rules fire on API and bulk loads too. On Salesforce, stage-gating validation rules will
   reject records that lack the required fields. Load with the rules in mind or temporarily relax them
   in the sandbox, and tell the user which you chose.

## Moving data in

1. **Inventory** the source: objects, record counts, fields in use, fields never filled. Use the
   answers to the migration questions in [discovery-questions.md](discovery-questions.md).
2. **Clean** the source: duplicates, blank emails, free text that should be a select option. Decide
   the mapping from old values to option keys, and write it in `notes.md`.
3. **Map** each source field to a design field. Fields with no home are either added to the design (with
   a description, and recorded as a decision) or dropped on purpose. Write down which.
4. **Prepare** the file: one file per object, a header row of design field keys, option keys rather
   than free text, ISO dates.
5. **Load a sample** of 20 records into the sandbox. Check them by eye against the source.
6. **Load everything** into the sandbox. Check counts and spot-check 20 more. Run `crm_drift` to confirm
   structure is unchanged.
7. **Sign off** in the sandbox with the client.
8. **Repeat in production**, engineer at the keyboard, with a fresh backup of anything that already
   exists there.

Platform loading routes (from the research; check the current page before relying on them):

| Platform | Route | Match on |
|---|---|---|
| Attio | `PUT /v2/objects/{object}/records?matching_attribute=<unique_slug>` (assert/upsert), or the CSV import in the UI. Select options and statuses must exist before the record is written. | A unique attribute, such as email or domain |
| HubSpot | The imports API or the import tool in the UI. | Email for people, domain for companies |
| Salesforce | Data Import Wizard or `sf data import bulk` (data, not metadata). | An external ID field, if the design adds one |

Source: each platform's `reference/api-coverage.md` and `reference/objects.md`.

## Destructive manual steps

The planner never applies these. It writes them to the plan as manual steps with the risk
"destructive" and instructions. The wording below matches what the planner prints
(`tools/crm/planner.py`).

| Step | Triggered by | What to do |
|---|---|---|
| Remove field | A field is in the live CRM but not in the design. | 1. Export the field with the record ID. 2. Decide whether the data moves to another field or is retired. 3. Remove the field from views, forms and automations. 4. Archive or delete it in the CRM. |
| Change type of field | A field's type differs from the design. | 1. Create a new field (`<key>_new`) of the new type. 2. Copy values across by export and import, mapping any that do not convert. 3. Point views, automations and integrations at the new field. 4. Archive the old field and rename the new one. |
| Remove object | An object is live but not in the design. | 1. Export every record. 2. Decide where the data goes and move it. 3. Remove its views, automations and integrations. 4. Delete or archive the object. |
| Remove relationship | A link is live but not in the design. | 1. Export the links. 2. Remove it from views and automations. 3. Delete or archive it. |
| Change cardinality of relationship | The cardinality differs from the design. | 1. Create a new relationship with the right cardinality. 2. Copy the links across. 3. Repoint views and automations. 4. Archive the old one. |
| Remove pipeline | A pipeline is live but not in the design. | 1. Export the records in it. 2. Move open records to the replacement pipeline and map each stage. 3. Archive the pipeline. |

Every one ends with: **export the data first, and never delete before the data is safe elsewhere.**
After each step, re-run `crm_plan`. The step is done when the plan no longer lists it.

### Removing an option or a stage

These are `needs_review` changes, not manual steps. The tool archives or hides, and never deletes.
Before approving with `--allow-review`:

1. Find records that use the option or stage.
2. Move them to a different option or stage, or accept that they keep the old value.
3. Read the plan line. It says "Archive it; do not delete".

### Platform notes for destructive steps

- **Attio:** attributes, options and statuses can be archived, not deleted. An archived item may still block its slug or title (open question Q9). Option and stage order cannot be set through the API.
- **HubSpot:** from API version 2026-09, deleting or replacing an in-use pipeline or stage is blocked by default. Never pass the bypass flag. Moving records between stages is a data operation.
- **Salesforce:** a deploy only adds. Deleting a field, picklist value, stage or record type is done in Setup, Object Manager. A rename is a new component, because `fullName` is the identity. Changing lookup to master-detail purges child records and cannot be checked with a dry run.

Sources: `platforms/attio/reference/open-questions.md`, `platforms/hubspot/README.md`, `platforms/salesforce/README.md`.

## After the load

1. Run [../checklists/go-live-qa.md](../checklists/go-live-qa.md).
2. Keep the old system read-only for the agreed period.
3. Schedule the monthly check in [../checklists/monthly-data-quality.md](../checklists/monthly-data-quality.md).
