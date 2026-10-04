> Sources: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/api_meta.pdf (Metadata API Developer Guide v68.0: "CustomObject", "Supported Salesforce Editions", "Metadata API Edit Access", "Sample package.xml Manifest Files"); https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/sfdx_dev.pdf (DX Developer Guide v68.0: "Salesforce DX Project Structure and Source Format", "Decomposed Metadata Types"); https://raw.githubusercontent.com/forcedotcom/source-deploy-retrieve/main/src/registry/metadataRegistry.json; https://raw.githubusercontent.com/forcedotcom/source-deploy-retrieve/main/test/snapshot/sampleProjects/customObjects-and-children/__snapshots__/verify-source-files.expected/force-app/main/default/objects/Property__c/Property__c.object-meta.xml; https://github.com/SalesforceFoundation/NPSP (Batch__c object file); https://raw.githubusercontent.com/salesforcecli/plugin-limits/main/src/commands/org/list/limits.ts; https://raw.githubusercontent.com/salesforcecli/plugin-schema/main/messages/list.md; web search snippets for edition object limits (secondary)
> Last verified: 2026-10-04

# Salesforce objects

## Standard objects we use

| Our core object | Salesforce object | Notes |
|---|---|---|
| Company | `Account` | Business accounts. Person Accounts are a separate opt-in feature we do not use. |
| Person | `Contact` | Linked to an `Account`. Pre-qualification people can be `Lead`. |
| Deal | `Opportunity` | Pipelines map to sales processes and record types (see pipelines.md). |
| Task, meeting | `Task`, `Event` | Present on any object with `enableActivities` true. |
| Owner, user | `User` | Target of `user` fields. Not customised by us. |

Other standard objects that blueprints may touch: `Lead`, `Case`, `Campaign`, `Product2`, `Pricebook2`, `Quote`, `Contract`. Each is customised by adding child components (fields, record types, list views). No object file is needed.

Standard objects are addressed in a manifest as members of type `CustomObject`, one by name. There is no wildcard for standard objects (guide, "Standard Objects"). `*` under `CustomObject` returns custom objects only.

## Custom object file

```
force-app/main/default/objects/<Object>__c/<Object>__c.object-meta.xml
force-app/main/default/objects/<Object>__c/fields/<Field>__c.field-meta.xml
force-app/main/default/objects/<Object>__c/validationRules/<Rule>.validationRule-meta.xml
force-app/main/default/objects/<Object>__c/recordTypes/<RT>.recordType-meta.xml
force-app/main/default/objects/<Object>__c/businessProcesses/<BP>.businessProcess-meta.xml
force-app/main/default/objects/<Object>__c/listViews/<LV>.listView-meta.xml
force-app/main/default/objects/<Object>__c/compactLayouts/...   (optional)
```

The source format always splits a custom object like this (DX guide, "Decomposed Metadata Types"). Children that are split out: `businessProcesses`, `compactLayouts`, `fields`, `fieldSets`, `indexes`, `listViews`, `recordTypes`, `sharingReasons`, `validationRules`, `webLinks`. Everything else stays in the `.object-meta.xml` file.

Required elements, from the guide's "Fields" and its sample:

- `label`
- `pluralLabel`
- `nameField` with its own `label` and `type` (`Text` or `AutoNumber`). Required for custom objects.
- `deploymentStatus` `Deployed` (or `InDevelopment`, which hides the object from users).
- `sharingModel`

Minimal file:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <deploymentStatus>Deployed</deploymentStatus>
    <description>One row per recruitment search. Created when a client signs a search.</description>
    <enableActivities>true</enableActivities>
    <enableHistory>false</enableHistory>
    <enableReports>true</enableReports>
    <enableSearch>true</enableSearch>
    <label>Search</label>
    <nameField>
        <label>Search name</label>
        <type>Text</type>
    </nameField>
    <pluralLabel>Searches</pluralLabel>
    <sharingModel>ReadWrite</sharingModel>
    <visibility>Public</visibility>
</CustomObject>
```

The guide's own sample (`MyFirstObject`) uses just `deploymentStatus`, `description`, `label`, `nameField`, `pluralLabel` and `sharingModel`. The `enable*` elements are valid on custom objects (guide, "Fields"). A real Dreamhouse file adds `enableBulkApi`, `enableStreamingApi`, `enableSharing`, `enableFeeds`, `allowInChatterGroups`, `enableLicensing`, `compactLayoutAssignment` and ten `actionOverrides`. We omit those. Salesforce supplies defaults.

Auto number name field (element names from the `CustomField` table: `displayFormat`, `startingNumber`):

```xml
    <nameField>
        <displayFormat>S-{00000}</displayFormat>
        <label>Search number</label>
        <type>AutoNumber</type>
    </nameField>
```

The guide says an auto number field's starting number cannot be retrieved. If the design needs a different start, put `startingNumber` in the file. Our generator uses a `Text` name field unless the design says otherwise.

### Sharing model values

`Private`, `Read`, `ReadWrite`, `ReadWriteTransfer`, `FullAccess`, `ControlledByParent`, `ControlledByCampaign`, `ControlledByLeadOrContact` (guide, `SharingModel`). Which are valid depends on the object. A custom object that is the detail side of a master-detail relationship uses `ControlledByParent`. The guide lists the value but does not state that rule. Confirm in a sandbox.

### What the file cannot do

- The guide says "specify all relevant fields when you create or update a custom object; you can't update a single field on the object." In source format the CLI merges the children, but the object file itself is sent as written. Keep the object file complete in the generated build folder. Do not hand-trim it later.
- External objects (`__x`) and big objects (`__b`) are out of scope.

## Tabs and apps

A custom object is not visible in navigation until it has a tab, and the tab is shown in an app and granted in a permission set (`tabSettings`). The registry gives the paths:

```
force-app/main/default/tabs/<Object>__c.tab-meta.xml
force-app/main/default/applications/<App>.app-meta.xml
```

`CustomTab` has `customObject` (true), `label`, `motif`, `icon` and others. We have not verified a minimal tab file or whether `motif` is required. Open question. Until proven, the build sheet lists "add a tab" as a manual step with a UI path.

## Limits and plan requirements

From the guide:

- The Metadata API works only on Enterprise, Unlimited, Performance and Developer Edition orgs. Professional Edition orgs get it only for ISV partner apps through an API token. Essentials is not listed. See auth-and-setup.md and open-questions.md.
- The user needs API Enabled plus either Modify Metadata Through Metadata API Functions or Modify All Data.

From secondary sources (help article snippets), to confirm in the target org (Setup, Company Information):

| Edition | Custom objects | Custom fields per object |
|---|---|---|
| Essentials | 0 | 100 |
| Professional | 50 | 100 |
| Enterprise | 200 | 500 |
| Unlimited, Performance | 2,000 | 800 |

A hard ceiling of 3,000 custom objects per org is also reported. These numbers change. The planner should read live limits (`sf org list limits` for API allowances; object counts from `sf sobject list --sobject custom`) and warn when a design needs more than 75 percent of the allowance.

## Reading objects

- `sf sobject list --sobject custom --target-org <alias> --json` lists custom objects.
- `sf sobject describe --sobject Opportunity --target-org <alias> --json` returns the describe result (see relationships.md and limits-and-errors.md for the shape).
- `sf project retrieve start --metadata CustomObject:Engagement__c` retrieves the object and its children.
- `sf org list metadata --metadata-type CustomObject --target-org <alias> --json` lists object names (case-sensitive type name).
