> Sources: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/api_meta.pdf (Metadata API Developer Guide v68.0); https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/sfdx_dev.pdf (Salesforce DX Developer Guide v68.0); https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/object_reference.pdf; https://github.com/salesforcecli/plugin-deploy-retrieve; https://github.com/forcedotcom/source-deploy-retrieve. Full lists are in `reference/`.
> Last verified: 2026-10-04

# Salesforce build notes

Research is in [reference/](reference/). This page is the short version.

## Verdict on the chosen approach

The brief's choice is sound: **SFDX source-format metadata, deployed with `sf project deploy start`**.

Why it holds:

- Source format is the supported on-disk layout. Custom objects are always split into one file per field, validation rule, record type, business process and list view (DX guide, "Decomposed Metadata Types"). That makes generated output reviewable, diffable and deterministic.
- `sf project deploy start --dry-run` is a real check-only deploy. Salesforce runs the same checks as a live deploy and saves nothing. The adapter's "dry run by default" rule maps onto it directly.
- A deploy is create-or-update. Re-running unchanged files is safe and reports each file as `Unchanged`. That gives idempotency without an "already exists" error path.
- `sf project retrieve start` and `sf sobject describe` give the read side in the same toolchain, with JSON output.
- The CLI wraps the Metadata API, so every type the brief lists is covered.

Where it is weaker than it looks:

1. **Edition.** The Metadata API works only on Enterprise, Unlimited, Performance and Developer Edition. Professional and Essentials clients cannot be built this way. They get the build sheet.
2. **No read-only metadata permission.** Retrieve needs the same permission as deploy.
3. **`sf` must be installed** and run inside a project folder (`sfdx-project.json`). The adapter owns a per-client build folder and shells out.
4. **Some design concepts have no metadata**: list view sort, tabs and apps (unproven), page layout placement, user assignment.

### Alternatives considered

| Option | What it is | Verdict |
|---|---|---|
| Metadata API zip (`sf project deploy start --metadata-dir`) | The same API, but with the older "metadata format" folder layout (one `.object` file per object). | Works, same limits. Worse to review, no gain. Keep as a fallback for `sf project convert source`. |
| Metadata API REST deploy | Same deploy over REST. Switched on with `sf config set org-metadata-rest-deploy true`. | Not needed. No 39 MB zip cap, but our payloads are small. |
| Metadata API CRUD calls (`createMetadata`, `upsertMetadata`) | Synchronous calls, one component per call. | Needs a SOAP or SDK client. More code, more API calls. Not chosen. |
| Tooling API | REST access to metadata-like objects (`sf sobject describe --use-tooling-api` exists). | Not researched in the primary pages. Fragile for relationships and picklists. Not chosen. |
| Data APIs only (REST or SOAP describe and query) | Read-only for most things. | Used for `read_state` on editions without the Metadata API. Cannot create objects or fields. |

## Facts the generator and adapter workers need

**Pin API version 67.0** (`sfdx-project.json` `sourceApiVersion`, `package.xml` `<version>`, `--api-version 67.0`). The guides read are 68.0, but orgs on the previous release reject it. See [auth-and-setup.md](reference/auth-and-setup.md).

Paths under `force-app/main/default/` (directory and suffix from the SDR registry; XML from real files):

| What | Path |
|---|---|
| Custom object | `objects/<Obj>__c/<Obj>__c.object-meta.xml` |
| Field | `objects/<Obj>/fields/<Field>__c.field-meta.xml` |
| Validation rule | `objects/<Obj>/validationRules/<Rule>.validationRule-meta.xml` |
| Record type | `objects/<Obj>/recordTypes/<Name>.recordType-meta.xml` |
| Sales process | `objects/Opportunity/businessProcesses/<Name>.businessProcess-meta.xml` |
| List view | `objects/<Obj>/listViews/<Name>.listView-meta.xml` |
| Global value set | `globalValueSets/<Name>.globalValueSet-meta.xml` |
| Opportunity stages | `standardValueSets/OpportunityStage.standardValueSet-meta.xml` |
| Path | `pathAssistants/<Name>.pathAssistant-meta.xml` |
| Path preference | `settings/PathAssistant.settings-meta.xml` |
| Permission set | `permissionsets/<Name>.permissionset-meta.xml` |
| Lead conversion mapping | `LeadConvertSettings/LeadConvertSettings.LeadConvertSetting-meta.xml` (unverified) |
| Flow (manual in v1) | `flows/<Name>.flow-meta.xml` |

Root element in every file: `<TypeName xmlns="http://soap.sforce.com/2006/04/metadata">`.

Field type map: text `Text`+`length`; long_text `LongTextArea`+`length`+`visibleLines`; select `Picklist`+`valueSet`; multi_select `MultiselectPicklist`+`valueSet`+`visibleLines`; number, currency, percent `Number`/`Currency`/`Percent`+`precision`+`scale`; date `Date`; datetime `DateTime`; checkbox `Checkbox`+`defaultValue`; url `Url`; email `Email`; phone `Phone`; user `Lookup` to `User`. Details in [fields.md](reference/fields.md).

Stage flags: `closed`, `won`, `probability`, `forecastCategory` on each `standardValue`. Won = closed true, won true, 100, `Closed`. Lost = closed true, won false, 0, `Omitted`. See [pipelines.md](reference/pipelines.md).

Commands (all `--json`, all with `--target-org <alias> --api-version 67.0`, run in the build folder):

```
sf project deploy start --dry-run --manifest package.xml --wait 30    # check only
sf project deploy start --manifest package.xml --wait 30              # apply
sf project retrieve start --manifest package.xml --wait 30            # read metadata
sf sobject describe --sobject <Name>                                  # read fields
sf data query --query "SELECT ... FROM OpportunityStage"              # read stages
```

Exit codes: 0 success, 1 failed, 68 partial, 69 still running. Read failures from `result.details.componentFailures` (may be one object or a list) and `result.files[]`. See [limits-and-errors.md](reference/limits-and-errors.md).

Never pass: `--ignore-errors`, `--ignore-conflicts`, `--ignore-warnings`, `--purge-on-delete`, the destructive-changes flags, or `--test-level NoTestRun` on production.

## Gotchas

1. **Deploys only add.** Stage values and picklist values are added, never removed. Salesforce's default stages remain.
2. **`fullName` is identity.** A rename is a new component. Treat renames as manual.
3. **Permission sets are overwritten whole.** Regenerate the full file and merge by hand if the client has edited it.
4. **New fields are invisible** until a permission set grants them, and may not be on any page layout.
5. **Required fields are not for stage gating.** Field-level `required` blocks every save. Stage rules are validation rules with a `CASE` on the stage order.
6. **Validation rules also fire on API and bulk writes.** Warn when a client plans an import.
7. **Master-detail changes are destructive.** Lookup to master-detail purges child records. `--dry-run` cannot check it.
8. **Check XML escaping** in formulas: `<` is `&lt;`, `>` is `&gt;`, `&` is `&amp;`.
9. **Production flows** deploy inactive unless a Setup preference is on.
10. **The guide has a typo**: its validation rule sample shows `validationMessage`. The real element is `errorMessage`.
11. **Describe is permission-filtered.** Read as a user who can see every field.
12. **Dates matter.** A Salesforce release lands three times a year. Re-check the pinned API version each time.

## What to read first for each task

- Generating files: fields.md, objects.md, relationships.md, pipelines.md, views-and-lists.md.
- Writing the adapter: auth-and-setup.md, limits-and-errors.md, api-coverage.md.
- Writing build sheets and manual steps: api-coverage.md (manual table), automation.md, open-questions.md.
- Anything you are unsure of: open-questions.md.
