> Sources: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/api_meta.pdf (Metadata API Developer Guide v68.0: "StandardValueSet", "CustomValue/StandardValue", "BusinessProcess", "RecordType", "ValidationRule", "PathAssistant", "PathAssistantSettings", "Picklist (Including Dependent Picklist)"); https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/object_reference.pdf (Object Reference v68.0: "OpportunityStage"); https://github.com/SalesforceFoundation/NPSP (OpportunityStage.standardValueSet, Opportunity.object business processes and record types, Major_Gift_Path.pathAssistant, Target_Required.validationRule-meta.xml); https://raw.githubusercontent.com/forcedotcom/source-deploy-retrieve/main/src/registry/metadataRegistry.json (directories and suffixes)
> Last verified: 2026-10-04

# Salesforce pipelines and stages

Salesforce has one native pipeline model: the `Opportunity` object with the `StageName` picklist. Everything else is built from a picklist field.

| Design concept | Opportunity | Any other object |
|---|---|---|
| Pipeline | Sales process (`BusinessProcess`) plus `RecordType` | One `Picklist` field `Stage__c` (a record type per pipeline if there are several) |
| Stage | Value in the `OpportunityStage` `StandardValueSet` | Value in the picklist |
| Open, won, lost | `closed` and `won` flags on the stage value | No native flags. Use stage names plus a checkbox or formula. |
| Probability | `probability` on the stage value | A percent field |
| Forecast | `forecastCategory` on the stage value | None |
| Exit criteria | Guidance text in `PathAssistant` `info` | Same |
| Required fields per stage | `ValidationRule` formulas | Same |
| Visual | `PathAssistant` | Same, with `entityName` set to the custom object |

## File paths (source format)

```
force-app/main/default/standardValueSets/OpportunityStage.standardValueSet-meta.xml
force-app/main/default/objects/Opportunity/businessProcesses/<Process>.businessProcess-meta.xml
force-app/main/default/objects/Opportunity/recordTypes/<RecordType>.recordType-meta.xml
force-app/main/default/objects/Opportunity/validationRules/<Rule>.validationRule-meta.xml
force-app/main/default/pathAssistants/<Path>.pathAssistant-meta.xml
force-app/main/default/settings/PathAssistant.settings-meta.xml
```

Manifest members: `OpportunityStage` (`StandardValueSet`), `Opportunity.<Process>` (`BusinessProcess`), `Opportunity.<RecordType>` (`RecordType`), `Opportunity.<Rule>` (`ValidationRule`), `<Path>` (`PathAssistant`), `PathAssistant` (`Settings`).

## Stages: the `OpportunityStage` StandardValueSet

The file name carries the set name. The guide's sample puts `<fullName>OpportunityStage</fullName>` inside the file; the real NPSP file omits it. Use the file name.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<StandardValueSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <sorted>false</sorted>
    <standardValue>
        <fullName>Discovery</fullName>
        <default>false</default>
        <label>Discovery</label>
        <closed>false</closed>
        <forecastCategory>Pipeline</forecastCategory>
        <probability>10</probability>
        <won>false</won>
    </standardValue>
    <standardValue>
        <fullName>Closed Won</fullName>
        <default>false</default>
        <label>Closed Won</label>
        <closed>true</closed>
        <forecastCategory>Closed</forecastCategory>
        <probability>100</probability>
        <won>true</won>
    </standardValue>
    <standardValue>
        <fullName>Closed Lost</fullName>
        <default>false</default>
        <label>Closed Lost</label>
        <closed>true</closed>
        <forecastCategory>Omitted</forecastCategory>
        <probability>0</probability>
        <won>false</won>
    </standardValue>
</StandardValueSet>
```

What the flags mean (guide, `StandardValue`; Object Reference, `OpportunityStage`):

- `probability`: integer, the default win percentage for the stage.
- `closed`: this stage ends the deal. Several stages can be closed.
- `won`: this closed stage is a win. Several stages can be won.
- `forecastCategory`: metadata values are `Omitted`, `Pipeline`, `BestCase`, `Forecast`, `Closed`. (The queryable `OpportunityStage` object shows display names such as `Best Case` and `Commit`.)
- `sorted` is required. `false` keeps our order.
- The deploy needs at least one `standardValue`, or it errors.

Mapping from design `Stage.type`:

| Design `type` | `closed` | `won` | `forecastCategory` | `probability` |
|---|---|---|---|---|
| `open` | false | false | `Pipeline` unless an override says otherwise | the design's value |
| `won` | true | true | `Closed` | 100 |
| `lost` | true | false | `Omitted` | 0 |

The 100 and 0 are convention (real NPSP file). The guide does not enforce them.

Important behaviour:

- A deploy only adds stage values ("picklist values are added as needed"). It never removes the stages every org already has. A new org starts with default stages such as `Prospecting` and `Closed Won`. Removing or deactivating defaults is a manual step. The sales process (below) decides which stages a record type offers, so the leftovers are hidden from users of that process.
- A stage's `fullName` is its stored API value. The label can differ. Renaming a stage's `fullName` in a deploy adds a new value. It does not rename. The planner must treat a design rename as `needs_review` and manual.
- New picklist values do not automatically show on record types. The guide (StandardValueSet note) says to edit each record type and add the new value. Our record type files therefore list their `picklistValues` (see below).
- The `OpportunityStage` object (SOQL: `SELECT ApiName, MasterLabel, IsActive, IsClosed, IsWon, DefaultProbability, ForecastCategoryName, SortOrder FROM OpportunityStage`) is the way to read live stages. It supports `describeSObjects`, `query` and `retrieve` only. Use `sf data query --query "..." --json`.

## Sales process: `BusinessProcess`

A business process (called a sales process in the UI) is a subset of the stage values, with its own default. One per Opportunity pipeline.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<BusinessProcess xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Renewals</fullName>
    <description>Annual renewal conversations.</description>
    <isActive>true</isActive>
    <values>
        <fullName>Renewal due</fullName>
        <default>true</default>
    </values>
    <values>
        <fullName>Closed Won</fullName>
        <default>false</default>
    </values>
    <values>
        <fullName>Closed Lost</fullName>
        <default>false</default>
    </values>
</BusinessProcess>
```

- `fullName` inside an object's folder is the bare process name. The object-qualified form (`Opportunity.Renewals`) is only for manifest members (guide).
- Every `values/fullName` must exist in the stage value set. Deploy the stage set in the same deployment. The CLI orders them.
- Access needs the View Setup and Configuration permission.
- Business processes support `*` in a manifest only when `RecordType` is also specified.
- We have not found, in the pages read, a rule on the minimum content of a sales process (for example one open, one won and one lost stage). Include at least one stage of each type.

## Record type

A record type is required for an Opportunity pipeline because it is what binds a sales process to users.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<RecordType xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Renewals</fullName>
    <active>true</active>
    <businessProcess>Renewals</businessProcess>
    <description>Renewal deals for existing customers.</description>
    <label>Renewals</label>
    <picklistValues>
        <picklist>Segment__c</picklist>
        <values>
            <fullName>smb</fullName>
            <default>false</default>
        </values>
        <values>
            <fullName>enterprise</fullName>
            <default>false</default>
        </values>
    </picklistValues>
</RecordType>
```

Rules from the guide:

- `active` and `label` are required.
- `businessProcess` is required for Lead, Opportunity, Solution and Case record types, and not allowed on others. Give the bare process name.
- `fullName` has letters, digits and underscores only, starts with a letter, no spaces, no trailing underscore, no double underscore.
- `description` is at most 255 characters.
- Record types are not access control. Profile (or permission set) assignment grants create and edit access. Everyone with object access can read all record types.
- Retrieving a record type brings in the profiles and permission sets that mention it.

Assigning a record type to users is a permission set or profile setting (`recordTypeVisibilities` on `PermissionSet`). See objects.md and views-and-lists.md for the permission set shape. Add a `recordTypeVisibilities` block per record type.

Picklist values per record type: list every value you want available. The generator emits one `picklistValues` block per picklist field on the object for each record type (to confirm in a sandbox; if a field is omitted it may show no values).

## Stage gating: `ValidationRule`

One rule per gated stage. The rule fires when the formula is true. It blocks the save and shows the message.

File (real shape from NPSP, with our names):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ValidationRule xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Proposal_requires_decision_maker</fullName>
    <active>true</active>
    <description>Gate: Proposal and later stages need a decision maker.</description>
    <errorConditionFormula>AND(
  CASE(StageName, "Proposal", 1, "Negotiation", 2, "Closed Won", 3, 0) &gt;= 1,
  ISBLANK(Decision_maker__c)
)</errorConditionFormula>
    <errorDisplayField>Decision_maker__c</errorDisplayField>
    <errorMessage>Add the decision maker before moving to Proposal.</errorMessage>
</ValidationRule>
```

Required elements (guide): `active`, `errorConditionFormula`, `errorMessage` (255 characters or fewer). `description` and `errorDisplayField` are optional. `errorDisplayField` is the API name of a field. If it is not on the page layout, the message goes to the top of the page. The guide's own sample shows `validationMessage`, which is a typo in the guide. The real element is `errorMessage`.

Escape XML in formulas: `<` is `&lt;`, `>` is `&gt;`, `&` is `&amp;`. Double quotes are fine inside element text.

"Reaches a stage" means "is at or after it". Salesforce cannot compare picklist order directly. Use `CASE(StageName, <stage>, <ordinal>, ..., 0) >= n`. The generator builds the CASE from the stage order in the design. Closed-lost stages sit outside the open order, so give them a separate rule.

"Required field is empty" by canonical type:

| Canonical | Empty test |
|---|---|
| text, long_text, url, email, phone, number, currency, percent, date, datetime, user | `ISBLANK(Field__c)` |
| select | `ISBLANK(TEXT(Field__c))` |
| multi_select | `ISBLANK(Field__c)` |
| checkbox | `NOT(Field__c)` |

The multi_select form is from memory of the formula reference. Prove it with `--dry-run`: the platform compiles each formula at deploy time, so a bad formula fails the check-only deploy.

Variant that only fires when the stage changes (leaves old records editable):

```
AND(ISCHANGED(StageName), CASE(StageName, "Proposal", 1, "Negotiation", 2, 0) >= 1, ISBLANK(Decision_maker__c))
```

Lost reason, any lost stage, using the standard `IsClosed` and `IsWon` fields:

```
AND(IsClosed, NOT(IsWon), ISBLANK(TEXT(Closed_lost_reason__c)))
```

Or by name: `AND(ISPICKVAL(StageName, "Closed Lost"), ISBLANK(TEXT(Closed_lost_reason__c)))`. `Closed_lost_reason__c` is a custom picklist on Opportunity. There is no standard loss-reason field.

Limits and notes:

- Validation rules cannot use compound fields (addresses, split names, dependent picklists) as of API 20.0.
- A manifest cannot use `*` for `ValidationRule`.
- Rules also run on API writes. Bulk loads and integrations hit them. Warn in the build sheet.

## Path: `PathAssistant`

The chevron bar on a record. One path per record type per object.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PathAssistant xmlns="http://soap.sforce.com/2006/04/metadata">
    <active>true</active>
    <entityName>Opportunity</entityName>
    <fieldName>StageName</fieldName>
    <masterLabel>Renewals path</masterLabel>
    <pathAssistantSteps>
        <fieldNames>Amount</fieldNames>
        <fieldNames>CloseDate</fieldNames>
        <info>Entered when the renewal quote has been sent.</info>
        <picklistValueName>Proposal</picklistValueName>
    </pathAssistantSteps>
    <recordTypeName>Renewals</recordTypeName>
</PathAssistant>
```

- Required: `entityName`, `fieldName`, `masterLabel`, `recordTypeName`, and `picklistValueName` per step. `entityName`, `fieldName` and `recordTypeName` are not updateable.
- `fieldName` is `StageName` for Opportunity (and `Status` for Lead). For a custom object it is the API name of the picklist field.
- `fieldNames` are the key fields shown for the step. `info` is the guidance text (our exit criteria).
- A step missing from the file is simply unconfigured, not absent.
- `recordTypeName` for objects with no record type: the guide mentions the `__Master__` record type. The exact value (`Master`) is unverified. Open question.
- The Path preference: `settings/PathAssistant.settings-meta.xml`

```xml
<PathAssistantSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <pathAssistantEnabled>true</pathAssistantEnabled>
</PathAssistantSettings>
```

  `pathAssistantEnabled` defaults to true in Enterprise Edition and false in other editions (guide). The guide also says the preference need not be on to deploy a path.
- Note: the real NPSP path file used here is an older style (`.pathAssistant` in an `unpackaged` folder) and refers to placeholders. The shape is the same.

## Non-Opportunity pipelines (custom objects)

Example: a `Search__c` object with stages.

- `Stage__c` is a `Picklist` field (fields.md). Values are the stages in order.
- Won and lost are plain stage values. Add `Closed_lost_reason__c` and a validation rule like the one above, written with `ISPICKVAL(Stage__c, "Lost")`.
- Probability and forecast do not exist natively. Add a `Percent` field and set it with a Flow, or leave it out. Reporting by stage works without it.
- For a second pipeline on the same object, add a record type and restrict the picklist values per record type (`picklistValues` in the record type). A business process is not available for custom objects.
- Path works with `entityName` `Search__c` and `fieldName` `Stage__c`.

## Leads

Lead stages are the `LeadStatus` StandardValueSet. A value can carry `converted` true. A Lead sales process (`BusinessProcess` on Lead) and record types follow the same pattern. We do not use Lead pipelines in v1 unless a blueprint asks.
