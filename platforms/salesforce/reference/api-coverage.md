> Sources: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/api_meta.pdf (Metadata API Developer Guide v68.0; every type below was read in this edition); https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/sfdx_dev.pdf (DX Developer Guide v68.0); https://raw.githubusercontent.com/forcedotcom/source-deploy-retrieve/main/src/registry/metadataRegistry.json (directory and suffix of each type); the other files in this folder. The HTML versions of the Metadata API pages (developer.salesforce.com) returned HTTP 403 from this machine, so the "Doc page" links are the canonical page names that match the PDF section titles and were not opened.
> Last verified: 2026-10-04

# Salesforce API coverage

One table per mode. Every design concept in `model/schema.md` (objects, fields, relationships, pipelines, stage rules, automations, views, overrides) appears once.

Conventions:

- Path = source-format path under `force-app/main/default/`.
- Doc page = `https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/<page>`. Use as `Change.source_url`.
- Setup paths in the manual table come from general platform knowledge, not from the PDFs read. Confirm the wording in a current sandbox when writing a build sheet. Labels move between releases.
- "Edition" = the Metadata API needs Enterprise, Unlimited, Performance or Developer Edition. On other editions every automated row becomes manual (open-questions.md).

## Automated (deploy with `sf project deploy start`)

| Design concept | Metadata type (manifest `<name>`) | Path | Doc page | Notes |
|---|---|---|---|---|
| Custom object | `CustomObject` | `objects/<Obj>__c/<Obj>__c.object-meta.xml` | `customobject.htm` | `nameField`, `label`, `pluralLabel`, `sharingModel`, `deploymentStatus` required. See objects.md. |
| Core object customised (Company, Person, Deal) | `CustomObject` children only | `objects/Account/fields/...` | `customobject.htm` | Ship children only, never the standard object file. |
| Field: text, long_text, select, multi_select, number, currency, percent, date, datetime, checkbox, url, email, phone | `CustomField` | `objects/<Obj>/fields/<Field>__c.field-meta.xml` | `customfield.htm` | One file each. Type map in fields.md. |
| Field: user | `CustomField` (`Lookup` to `User`) | same | `customfield.htm` | Unique `relationshipName`. |
| Field description | `CustomField.description` | same | `customfield.htm` | Always set. |
| Field help text | `CustomField.inlineHelpText` | same | `customfield.htm` | Optional. |
| Field on a standard object (add) | `CustomField` | `objects/Opportunity/fields/...` | `customfield.htm` | Member `Opportunity.Name__c`. |
| Field marked `native` | none | none | none | Exists already. Planner checks it in live describe and skips. |
| Select options (add) | inline `valueSetDefinition` or `GlobalValueSet` | field file or `globalValueSets/<Name>.globalValueSet-meta.xml` | `customfield.htm`, `globalvalueset.htm` | Adding is safe. Removing is manual. |
| Select options shared by many fields | `GlobalValueSet` | as above | `globalvalueset.htm` | New sets get a `__gvs` suffix (API 57+). |
| Relationship many_to_one / one_to_many | `CustomField` (`Lookup`) | child object's `fields/` | `customfield.htm` | Field lives on the "many" side. |
| Relationship with child-owned lifecycle | `CustomField` (`MasterDetail`) | child object's `fields/` | `customfield.htm` | Only if the design asks. Child must be custom. |
| Relationship many_to_many | Junction `CustomObject` plus two `MasterDetail` `CustomField`s | `objects/<Junction>__c/...` | `customobject.htm`, `customfield.htm` | `relationshipOrder` 0 and 1. |
| Relationship labels (`from_label`, `to_label`) | `label`, `relationshipLabel`, `relationshipName` | field file | `customfield.htm` | |
| Pipeline stages (Opportunity) | `StandardValueSet` `OpportunityStage` | `standardValueSets/OpportunityStage.standardValueSet-meta.xml` | `standardvalueset.htm` | Add only. |
| Stage type open, won, lost | `StandardValue.closed` and `.won` | same | `standardvalueset.htm` | Mapping in pipelines.md. |
| Stage probability | `StandardValue.probability` | same | `standardvalueset.htm` | Integer percent. |
| Stage forecast category | `StandardValue.forecastCategory` | same | `standardvalueset.htm` | Via `platform_overrides`. |
| Pipeline (Opportunity) | `BusinessProcess` + `RecordType` | `objects/Opportunity/businessProcesses/...`, `objects/Opportunity/recordTypes/...` | `businessprocess.htm`, `recordtype.htm` | One pair per pipeline. |
| Pipeline (other object) | `CustomField` picklist `Stage__c` (+ `RecordType` for several pipelines) | field file | `customfield.htm`, `recordtype.htm` | No native probability or won flag. |
| Record-type picklist values | `RecordType.picklistValues` | record type file | `recordtype.htm` | List every allowed value. |
| Required fields per stage | `ValidationRule` | `objects/<Obj>/validationRules/<Rule>.validationRule-meta.xml` | `validationrule.htm` | Stage-gating formulas in pipelines.md. |
| Lost requires a reason | `ValidationRule` + a `Closed_lost_reason__c` picklist field | as above | `validationrule.htm` | |
| Stage exit criteria text | `PathAssistant.pathAssistantSteps.info` | `pathAssistants/<Path>.pathAssistant-meta.xml` | `pathassistant.htm` | One path per record type per object. |
| Path switched on | `PathAssistantSettings` (via `Settings`) | `settings/PathAssistant.settings-meta.xml` | `pathassistantsettings.htm` | Default on in Enterprise only. |
| Lead conversion field mapping (custom fields) | `LeadConvertSettings` | `LeadConvertSettings/LeadConvertSettings.LeadConvertSetting-meta.xml` | `leadconvertsettings.htm` | Custom fields only. Path form unverified. |
| View (list) with filters and columns | `ListView` | `objects/<Obj>/listViews/<View>.listView-meta.xml` | `listview.htm` | No sort. Share it with `sharedTo`. |
| Field access | `PermissionSet.fieldPermissions` | `permissionsets/<Name>.permissionset-meta.xml` | `permissionset.htm` | Whole file each time. |
| Object access, record type access, tabs | `PermissionSet` | same | `permissionset.htm` | |
| Read state: objects, fields, relationships | `sf sobject describe`, `sf project retrieve start` | n/a | `sforce_api_calls_describesobjects_describesobjectresult.htm` | See limits-and-errors.md for shapes. |
| Read state: pipelines | `OpportunityStage` query, `retrieve` of `BusinessProcess`, `RecordType` | n/a | Object Reference, `OpportunityStage` | |
| Check-only (dry run) | `sf project deploy start --dry-run` | n/a | `meta_deploy.htm` (deploy and `checkOnly`) | |
| Apply | `sf project deploy start` | n/a | same | Upsert; idempotent. |

## Manual (build sheet / `manual-steps.md`)

| Design concept | Setup path (verify) | Reason |
|---|---|---|
| Record-triggered automation (`automations` entries) | Setup, Process Automation, Flows, New Flow, Record-Triggered Flow | Flows can be deployed, but a wrong flow runs on every save and cannot be removed from source. Reviewed as instructions. Optional Draft skeleton behind a flag (automation.md). |
| Activate flows in production | Setup, Process Automation, Process Automation Settings, "Deploy processes and flows as active" | Setup preference. Not metadata we ship. |
| Scheduled flows, approvals, assignment rules, escalation rules | Setup, Process Automation | Not in v1 blueprints. |
| View sort order | The list view, controls menu, sort by column | `ListView` has no sort element. |
| Kanban board for Opportunity list view | The list view, display as Kanban | UI display setting. |
| Reports and dashboards | Reports tab, New Report | Out of v1. |
| Tab and app for a custom object | Setup, User Interface, Tabs; Setup, Apps, App Manager | Deployable (`CustomTab`, `CustomApplication`) but the minimal file is unverified. Move to automated once proven. |
| Page layout: show new fields to users | Setup, Object Manager, `<Object>`, Page Layouts | A deploy puts a field in the org, not on a layout (to confirm). Deploying a layout replaces the whole layout. |
| Lightning record page, compact layout | Setup, Object Manager, `<Object>`, Lightning Record Pages / Compact Layouts | Out of v1. |
| Assign the permission set to users | Setup, Users, Permission Sets, Manage Assignments | Data operation, not metadata. |
| Profiles | Setup, Users, Profiles | We never ship profiles; a profile deploy overwrites too much. |
| Org-wide default and sharing rules for standard objects | Setup, Security, Sharing Settings | Needs the standard object file. Sharing for custom objects is automated via `sharingModel`. |
| Remove or deactivate the default stages | Object Manager, Opportunity, Fields & Relationships, Stage, Opportunity Stages | A deploy only adds stage values. |
| Delete a field, option, stage, record type or object | Object Manager, `<Object>`, the item, Delete | Safety rule 3. Destructive: move data first. |
| Rename a field, stage or option | Same pages | `fullName` is the identity. A rename is a new component. |
| Change a field type | Object Manager, `<Object>`, Fields & Relationships, the field, Change Field Type | Safety rule 4. Many conversions are blocked or lose data. |
| Lookup to master-detail (or back) | Same | Not checkable with `--dry-run`. Child records are purged. |
| One-to-one uniqueness | Duplicate rule or validation rule | Salesforce has no unique lookup. |
| Mapping to or from standard Lead fields | Object Manager, Lead, Fields & Relationships, Map Lead Fields | Standard mappings are fixed. |
| Enable features (Opportunity Teams, multi-currency, divisions, Person Accounts) | Setup, the feature's settings page | Org-wide features. Some are one-way. |
| Create the sandbox | Setup, Environments, Sandboxes (or `sf org create sandbox`) | Needs the production org. Done by the account holder. |
| Professional or Essentials Edition: any row in the first table | The same Setup pages | The Metadata API is not available. The build sheet carries the full list. |
| Seed data, import of records | Data Import Wizard or `sf data import bulk` | Data, not metadata. Out of scope. |

## Gaps to close in a sandbox

Rows marked "unverified" or "to confirm" in the other files, in the order the first live run should settle them:

1. `Checkbox`, `Lookup`, `MasterDetail` and `LongTextArea` minimal files deploy as written (fields.md).
2. Record type `picklistValues` are needed for new custom picklists (pipelines.md).
3. The `__gvs` suffix on a global value set made through source (fields.md).
4. A minimal `CustomTab` (objects.md).
5. `sharedTo` XML on a list view (views-and-lists.md).
6. Whether `LeadConvertSettings` deploys through its own type or through `Settings` (automation.md).
7. `PathAssistant` `recordTypeName` for objects with no record type (pipelines.md).
