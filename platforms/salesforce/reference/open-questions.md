> Sources: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/api_meta.pdf; https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/sfdx_dev.pdf; https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/object_reference.pdf; https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf; the GitHub files named in the other reference files in this folder. This file lists what those could not settle.
> Last verified: 2026-10-04

# Salesforce open questions

Each item says what was found, what is unknown, and how the repo handles it until it is settled. Ordered by how much a wrong guess would cost.

## A. Things that could not be read

### A1. The developer.salesforce.com HTML pages would not load

`WebFetch` and `curl` both got HTTP 403 for every page tried on developer.salesforce.com, including `https://developer.salesforce.com/docs`, the Metadata API Developer Guide page for `CustomField`, the Salesforce DX Developer Guide, and the CLI command reference page for `project deploy start`. A third-party archive was blocked by the tool.

What was done instead (all read in full or by section):

- The official PDF editions of the same guides on `resources.docs.salesforce.com`: Metadata API Developer Guide v68.0 (updated 2 October 2026), Salesforce DX Developer Guide v68.0 (25 September 2026), Object Reference v68.0 (2 October 2026), and the Developer Limits and Allocations Quick Reference.
- The `sf` CLI's own source and message files on GitHub (`salesforcecli/plugin-deploy-retrieve`, `plugin-schema`, `plugin-auth`, `plugin-org`, `plugin-limits`, `sf-plugins-core`). The CLI reference web pages are generated from these.
- Real metadata from `forcedotcom/source-deploy-retrieve` test fixtures, `SalesforceFoundation/NPSP`, and `trailheadapps/dreamhouse-lwc`.

Not obtained: the CLI reference pages as rendered (the flags were taken from source, so they are current but may omit help text), and the HTML-only guide pages (for example the field-type conversion rules and the API-name rules, which live in Salesforce Help and not in the PDFs).

Handling: facts from secondary sources are marked "secondary" or "unverified" where they appear. The first sandbox run settles them (see Section G).

### A2. `sf` is not installed on the build machine

DECISIONS D-2. Nothing here was run. JSON shapes were derived from TypeScript types and message files, not captured. Test fixtures for the Salesforce adapter will be authored from those shapes. Mark them "authored from source, not recorded" until a live run replaces them.

## B. Editions and plan

### B1. The Metadata API is not available on Professional or Essentials

Guide: Enterprise, Unlimited, Performance and Developer Edition only. Professional Edition gets it only for ISV apps with an API token. Essentials is not listed. Professional with API access enabled does have the data APIs.

Handling (proposal):

1. `read_state` first calls `sf data query --query "SELECT OrganizationType, IsSandbox FROM Organization" --json`. (Standard `Organization` object; query not run in this research.) If the edition is not Enterprise, Unlimited, Performance or Developer, the adapter does not offer `apply`.
2. In that case the plan is still produced, but every change becomes a `ManualStep` with the Setup path from api-coverage.md. The build sheet is the deliverable.
3. `describe` and `query` still work on Professional with API access, so `read_state` and drift checks can run on describe alone, with reduced detail (no record type or business process names without a metadata retrieve).
4. Blueprint READMEs should say: "Salesforce: needs Enterprise Edition for automated build. On Professional, use the build sheet."

### B2. Custom object and custom field allowances

Secondary sources only (objects.md): Professional 50 custom objects and 100 fields per object, Enterprise 200 and 500, Unlimited 2,000 and 800. Essentials 0 custom objects. A blueprint with many custom objects may not fit a Professional org.

Handling: the planner reads live counts and warns at 75 percent of the allowance. The real limit comes from the client's Company Information page.

### B3. Multi-currency and Person Accounts

If multi-currency is on, every object gets a `CurrencyIsoCode` field and currency amounts convert. We do not turn it on. A client with it already on needs no change to our files, but reports differ. Person Accounts change what `Account` and `Contact` mean and cannot be turned off. The repo assumes business accounts only.

Handling: `read_state` records both flags (`sf sobject describe --sobject Account` shows `IsPersonAccount`; `CurrencyIsoCode` appears in Opportunity describe). If Person Accounts are on, add a `needs_review` note to every plan.

## C. Auth and permissions

### C1. Is "Customize Application" required to deploy?

A secondary source gives "Modify Metadata Through Metadata API Functions plus Customize Application" as the build identity. The Metadata API guide pages read name only the first. Handling: document both; test with a profile that has only the first. The result goes into auth-and-setup.md.

### C2. There is no read-only metadata permission

Retrieve and list calls need the same Modify Metadata Through Metadata API Functions (or Modify All Data) as deploy. A "read-only" integration user can therefore also deploy metadata. Handling: the safety is in our tooling (dry run by default, sandbox only, no `--execute` without the user). For clients who object, offer describe-only reads (API Enabled only), which cover objects, fields, picklists and relationships but not record types, business processes, validation rules or paths. Those need a retrieve.

### C3. Connected app versus external client app

The DX guide calls external client apps "preferred", but says a connected app is needed when the same login creates scratch orgs or sandboxes. We did not find whether creating new connected apps is blocked in new orgs. Handling: default to `sf org login web` with the global app for sandboxes; ask the client's admin to make an external client app only when JWT or IP restrictions are needed.

## D. API version

### D1. 67.0 or 68.0

The guides are 68.0 (Winter '27). The CLI template default is 67.0. Orgs on the earlier release reject the newer version. Handling: pin 67.0 everywhere (auth-and-setup.md). Re-check when a client org is on Winter '27.

## E. Metadata behaviour that must be confirmed

### E1. Required elements per field type

Only real files and the guide's field list were used. Specifically unconfirmed:

- `Checkbox` without `defaultValue`.
- `LongTextArea` length bounds (32768 default, 131072 maximum per secondary sources).
- `Number`, `Currency`, `Percent` precision and scale bounds (18 digits total per secondary sources).
- `required` true on a `Lookup` with `SetNull`.
- Whether `Lookup` accepts `required` at all.
- Whether `Text` needs `length` (every real file has it, so we always set it).

Handling: the first live run deploys one field of each of the 14 canonical types in a sandbox with `--dry-run`, then for real. The error text is recorded here.

### E2. Field type conversions

The conversion matrix (which type can become which) is Help-only. fields.md lists the secondary-source version. Handling: the repo never changes a type, so it does not need the matrix. The manual step text should link to the Help page "Considerations for Converting the Field Type of a Custom Field".

### E3. Deleting picklist values by deploy

The guide says only "picklist values are added as needed" for standard picklists. Behaviour for custom picklists and global sets on removal is not stated. Handling: removal is a manual `destructive` step. Re-deploying a field file with fewer values may or may not remove values; the adapter must not rely on either.

### E4. Record type picklist values

The `StandardValueSet` note says new values do not show on record types until added. If a record type file omits a picklist, the values may not show. Handling: emit all `picklistValues` for every picklist on the object, per record type. Confirm that omitting one is harmful.

### E5. Page layouts

Common experience (not in the pages read) is that deploying a field does not add it to a page layout. Users then see nothing until a layout is edited. Deploying a standard layout replaces the whole layout. Proposal:

1. v1: manual step per object, "add fields to the layout", with the field list.
2. v1.1: generate a new layout for custom objects only (`layouts/<Object>-<Object> Layout.layout-meta.xml`), and for standard objects leave it manual. Layout assignment per profile lives in `Profile.layoutAssignments`, which we never ship, so a new layout would not be assigned automatically.

Alternative worth testing: Lightning record pages with Dynamic Forms (`FlexiPage`). More work, not v1.

### E6. Tab and app for a custom object

Not verified (objects.md). Proposal: manual in v1; revisit once a minimal `CustomTab` is proven.

### E7. Sharing model on a junction or detail object

The guide lists `ControlledByParent` but not the rule that a master-detail child must use it. Confirm. Also confirm that a custom object with a master-detail field accepts `sharingModel` omitted.

### E8. `__gvs` on new global value sets

New sets get the suffix (guide). We do not know whether a source deploy of `Segment_values.globalValueSet-meta.xml` stores `Segment_values__gvs` or the plain name, nor how a field's `valueSetName` should then refer to it. Handling: the generator uses inline value sets by default and global sets only when the design shares one set across two or more fields. First live run settles it.

### E9. Sales process minimum

Does a sales process need at least one open, one won and one lost stage? The pages read do not say. We always include one of each.

### E10. Default stages stay

A deploy of `OpportunityStage` adds values and keeps Salesforce's defaults (for example `Prospecting`). The sales process hides unused stages for record types that use it, but the master list is unchanged. Whether the default stage values can be made inactive through source is unknown. Handling: manual step "deactivate unused default stages", marked optional.

### E11. Path record type name for no record type

The guide mentions the `__Master__` record type for paths. The value to put in `recordTypeName` is unconfirmed (`Master`?). It matters for custom-object pipelines with no record type. Handling: always create a record type for any object that gets a path.

### E12. List view `sharedTo` and standard-field tokens

- The `sharedTo` XML for "all internal users" is unverified (the WSDL element is `allInternalUsers`; the body is probably empty).
- `OPPORTUNITY.RECORDTYPE` and `OPPORTUNITY.CLOSED` as filter fields are from memory. Real column tokens (`OPPORTUNITY.NAME` and others) were read.

Handling: retrieve a hand-made view from a sandbox to learn the tokens for each standard field a blueprint uses.

### E13. Sort order of list views

Not in the metadata. Manual. If this is unacceptable, ask whether the UI API could set it. Not researched.

### E14. LeadConvertSettings path and manifest form

The CLI registry has directory `LeadConvertSettings`, suffix `LeadConvertSetting`. The guide says settings types are addressed through `Settings` and files live in `settings/`. Do a retrieve first and copy the shape it returns.

### E15. Flow shape

The record-triggered skeleton (automation.md) was assembled, not tested. Guide text on `recordTriggerType` says it applies only to before-save flows, but a real after-save file uses it. Handling: flows remain manual in v1.

### E16. Permission set requirements

- Does a field permission need an object permission in the same file?
- Is a field-level `required` field really rejected, or ignored?
- Is `hasActivationRequired` needed?

Handling: write object, field, record type and tab permissions together. List field permissions only for non-required fields.

### E17. Overwrite risk when deploying a partial object file

The guide: "Specify all relevant fields when you create or update a custom object. You can't update a single field on the object." For custom objects we regenerate the whole object file. For standard objects we never ship one.

### E18. Number of API calls per deploy

A deploy plus polling uses an unmeasured number of calls. Handling: one deploy per phase (objects and fields, then pipelines, then views and permissions), not one per component. Measure with `sf org list limits` before and after the first live run.

### E19. A lookup to `User` and `relationshipName` collisions

Not confirmed that names must be unique on `User` across objects. Handling: prefix with the object name.

## F. Design-to-platform gaps

- `View.sort`: no metadata (E13).
- `automations`: manual (E15).
- `one_to_one`: no unique lookup.
- Stage `required_fields`: validation rules fire on API writes too; bulk loads need an escape hatch (for example a custom permission or a checkbox "bypass" field). Not designed. Raise it as a design decision in blueprints that import data.
- Regulated and sensitive fields (financial advisers, healthcare blueprints): the `CustomField` type has `complianceGroup` (CCPA, COPPA, GDPR, HIPAA, PCI, PII), `securityClassification` (Public, Internal, Confidential, Restricted, MissionCritical) and `businessStatus`. These are metadata labels, not encryption. They suit the brief's "flag data protection" need. Shield Platform Encryption is a separate paid feature. Proposal: add `data_protection` to the design's field and map it to these two elements. This is a design-format change, so it is the caller's decision.

## G. First live run checklist

In one Developer Edition or sandbox org, in order:

1. `sf project deploy start --dry-run --manifest package.xml --json` with one field of each canonical type. Record any error text.
2. Real deploy. Re-run. Confirm every file reports `Unchanged`.
3. Pipeline files: stages, sales process, record type, validation rule, path. Check what users see.
4. Retrieve everything back. Diff against what was sent. List elements Salesforce added or dropped. These are the fields the adapter's compare must ignore.
5. Permission set: assign it to a test user and check field access.
6. List view with `sharedTo`.
7. `sf org list limits` before and after.
