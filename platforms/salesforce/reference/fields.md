> Sources: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/api_meta.pdf (Metadata API Developer Guide v68.0, "CustomField", "Metadata Field Types", "ValueSet", "GlobalValueSet", "StandardValueSet"); https://raw.githubusercontent.com/forcedotcom/source-deploy-retrieve/main/test/snapshot/sampleProjects/customObjects-and-children/__snapshots__/verify-source-files.expected/force-app/main/default/objects/Property__c/fields/ (real field files); https://github.com/SalesforceFoundation/NPSP (real Checkbox, Percent, DateTime, MasterDetail, MultiselectPicklist, global value set files); https://raw.githubusercontent.com/jsforce/jsforce/main/src/api/metadata/schema.ts (element names, API v47 snapshot, structure only); web search snippets for length limits and conversion rules (secondary, flagged below)
> Last verified: 2026-10-04

# Salesforce fields

## Where a field lives

Source format, one file per field:

```
force-app/main/default/objects/<Object>/fields/<FieldApiName>.field-meta.xml
```

- `<Object>` is `Opportunity` for a standard object or `Engagement__c` for a custom one.
- The file name is the field API name, for example `Renewal_date__c`.
- The root element is `<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">`.
- Standard objects need no object file. Ship only the `fields/` child files. The registry treats each child as its own component (`customfield` is a child of `customobject`).
- Manifest member: `Opportunity.Renewal_date__c` under type `CustomField`.

## Elements that appear on every field we generate

| Element | Meaning | Note |
|---|---|---|
| `fullName` | API name, ends `__c` | Must match the file name. |
| `label` | UI label | Sentence case. |
| `type` | A `FieldType` value | See the table below. |
| `description` | What the field is for | Our principle 3. Always set it. |
| `inlineHelpText` | Help bubble | Optional. |
| `externalId` | `false` unless the design says otherwise | Only valid on auto number, email, number and text. |
| `required` | Always required on every save | Avoid. Gate by stage with validation rules instead (see pipelines.md). |
| `trackHistory` | Field history | Needs `enableHistory` on the object. Optional. |

Valid `FieldType` values in API 68.0 (guide, "Metadata Field Types"): Address, AutoNumber, Lookup, MasterDetail, MetadataRelationship, Checkbox, Currency, Date, DateTime, Email, EncryptedText, ExternalLookup, IndirectLookup, Number, Percent, Phone, Picklist, MultiselectPicklist, Summary, Text, TextArea, LongTextArea, Url, Hierarchy, File, Html, Location, Time, Array, Integer, Long.

## Canonical type map (our 14 types)

| Canonical | Salesforce `type` | Required type elements | Defaults we use |
|---|---|---|---|
| `text` | `Text` | `length` | 255. Text holds up to 255 characters (secondary source). |
| `long_text` | `LongTextArea` | `length`, `visibleLines` | `length` 32768, `visibleLines` 6. Maximum 131072 (secondary source). |
| `select` | `Picklist` | `valueSet` | `restricted` true. |
| `multi_select` | `MultiselectPicklist` | `valueSet`, `visibleLines` | `visibleLines` 4. |
| `number` | `Number` | `precision`, `scale` | 18 and 0. Total digits of 18 or fewer (secondary source). |
| `currency` | `Currency` | `precision`, `scale` | 18 and 2. |
| `percent` | `Percent` | `precision`, `scale` | 5 and 2 (NPSP uses this). |
| `date` | `Date` | none | |
| `datetime` | `DateTime` | none | |
| `checkbox` | `Checkbox` | `defaultValue` | `false`. Every real Checkbox file read carries it. Treat as required. |
| `url` | `Url` | none | |
| `email` | `Email` | none | |
| `phone` | `Phone` | none | |
| `user` | `Lookup` to `User` | `referenceTo`, `relationshipName`, `relationshipLabel`, `deleteConstraint` | `deleteConstraint` `SetNull`. |

"Required type elements" is what the real files carry. The guide does not publish a per-type required list. A check-only deploy (`--dry-run`) is the proof. The first sandbox run must deploy one field of every type.

## Minimal XML per type

All shapes below come from real files (SDR fixtures from the Dreamhouse sample, NPSP). Only the labels and names are ours.

Text:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Contract_reference__c</fullName>
    <description>Reference printed on the signed contract.</description>
    <externalId>false</externalId>
    <label>Contract reference</label>
    <length>100</length>
    <required>false</required>
    <type>Text</type>
    <unique>false</unique>
</CustomField>
```

LongTextArea:

```xml
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Notes__c</fullName>
    <description>Free-text notes from discovery.</description>
    <label>Notes</label>
    <length>32768</length>
    <type>LongTextArea</type>
    <visibleLines>6</visibleLines>
</CustomField>
```

Picklist with an inline value set:

```xml
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Segment__c</fullName>
    <description>Customer size band, used in pipeline reports.</description>
    <label>Segment</label>
    <required>false</required>
    <type>Picklist</type>
    <valueSet>
        <restricted>true</restricted>
        <valueSetDefinition>
            <sorted>false</sorted>
            <value>
                <fullName>smb</fullName>
                <default>false</default>
                <label>SMB</label>
            </value>
            <value>
                <fullName>enterprise</fullName>
                <default>false</default>
                <label>Enterprise</label>
            </value>
        </valueSetDefinition>
    </valueSet>
</CustomField>
```

Picklist from a global value set (the `valueSetName` form; do not also give a `valueSetDefinition`, the guide says never both):

```xml
    <type>Picklist</type>
    <valueSet>
        <restricted>true</restricted>
        <valueSetName>Payment_ACH_Code</valueSetName>
    </valueSet>
```

MultiselectPicklist (same `valueSet` as a picklist, plus `visibleLines`):

```xml
    <type>MultiselectPicklist</type>
    <valueSet> ...same as Picklist... </valueSet>
    <visibleLines>4</visibleLines>
```

Number, Currency, Percent (only `precision` and `scale` differ):

```xml
    <precision>18</precision>
    <scale>2</scale>
    <type>Currency</type>
```

Date and DateTime:

```xml
    <label>Renewal date</label>
    <required>false</required>
    <type>Date</type>
```

Checkbox:

```xml
    <defaultValue>false</defaultValue>
    <label>Executive sponsor engaged</label>
    <type>Checkbox</type>
```

Url, Email, Phone: the basic elements plus `<type>Url</type>`, `<type>Email</type>` or `<type>Phone</type>`. `Email` and `Text` accept `unique`.

Lookup (to a custom or standard object):

```xml
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Broker__c</fullName>
    <deleteConstraint>SetNull</deleteConstraint>
    <externalId>false</externalId>
    <label>Broker</label>
    <referenceTo>Broker__c</referenceTo>
    <relationshipLabel>Properties</relationshipLabel>
    <relationshipName>Properties</relationshipName>
    <required>false</required>
    <type>Lookup</type>
</CustomField>
```

`user` (Lookup to User):

```xml
    <fullName>Account_manager__c</fullName>
    <deleteConstraint>SetNull</deleteConstraint>
    <label>Account manager</label>
    <referenceTo>User</referenceTo>
    <relationshipLabel>Accounts managed</relationshipLabel>
    <relationshipName>Accounts_managed</relationshipName>
    <type>Lookup</type>
```

`relationshipName` is the plural API name seen from the parent. Salesforce adds `__r` itself. Because many objects point at `User`, two lookups to `User` from different objects cannot share a `relationshipName` (not confirmed in the guide pages read; make it `<Object>_<Field>` to be safe).

MasterDetail (real NPSP file; note there is no `required` and no `deleteConstraint`):

```xml
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Opportunity__c</fullName>
    <label>Opportunity</label>
    <referenceTo>Opportunity</referenceTo>
    <relationshipLabel>Account Soft Credits</relationshipLabel>
    <relationshipName>Account_Soft_Credits</relationshipName>
    <relationshipOrder>0</relationshipOrder>
    <reparentableMasterDetail>false</reparentableMasterDetail>
    <type>MasterDetail</type>
    <writeRequiresMasterRead>false</writeRequiresMasterRead>
</CustomField>
```

`relationshipOrder` is 0 for a normal detail, and 0 or 1 for the two fields of a junction object (guide, `relationshipOrder`).

## Picklist value sets

Inline (`valueSetDefinition`):

- Each `value` has `fullName` (the stored API value), `default` and `label`.
- `sorted` is required on the definition.
- `restricted` true makes the API reject values not in the list.
- `value` also accepts `isActive`, `color` and `description` (guide, `CustomValue`).

Global (`GlobalValueSet`), file `force-app/main/default/globalValueSets/<Name>.globalValueSet-meta.xml`:

```xml
<GlobalValueSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <customValue>
        <fullName>PPD</fullName>
        <default>false</default>
        <label>Prearranged Payment and Deposit Entry (PPD)</label>
    </customValue>
    <description>The Standard Entry Class code used for this transaction.</description>
    <masterLabel>Payment ACH Code</masterLabel>
    <sorted>false</sorted>
</GlobalValueSet>
```

Rules from the guide:

- `masterLabel` and `sorted` are required. At least one `customValue`. At most 1,000 values including inactive ones.
- A picklist that uses a global set is restricted. Add or remove values only on the global set.
- A global value set created at API 57.0 or later gets `__gvs` appended to its developer name. In the real NPSP file the field references `Payment_ACH_Code` (an older set). For a new set, expect the field to reference `<Name>__gvs`. Confirm in the first sandbox run (open question).
- Manifest: type `GlobalValueSet`, wildcard supported.
- The guide describes `valueSetName` as "the masterLabel of the global value set". The real file shows the API name. Use the API name.

Dependent picklists use `controllingField` on the `valueSet` and `valueSettings`. The guide says dependency values can be added through the API but not removed. We do not generate dependent picklists in v1.

## Standard picklists

`StageName` and other standard picklists are not `CustomField` files. They are `StandardValueSet` files. See pipelines.md.

## Naming rules

From the guide:

- Custom field and custom object names end `__c` (`__x` for external objects, `__gvs` for new global value sets).
- Record type, validation rule and similar names: letters, digits and underscores only, start with a letter, no spaces, no trailing underscore, no two underscores in a row (guide, `RecordType.fullName` and `ValidationRule.fullName`).
- A flow file name must not contain spaces (guide, `Flow`).

From secondary sources, to confirm in a sandbox:

- API name base is at most 40 characters, not counting `__c`.
- Field labels are at most 40 characters (the guide states 40 for translated labels).
- Salesforce builds an API name from a label by replacing spaces and punctuation with underscores. We always set `fullName` ourselves, so this does not apply.

Generator rule: `fullName = Title_case_with_underscores + "__c"`, ASCII only, base 40 characters or fewer, check for collisions after truncation.

## What cannot change after creation

From the guide:

- The field API name (`fullName`) is the identity. A different name is a different field.
- Picklist `StandardValueSet` values are only added by deploy ("picklist values are added as needed").
- On `PathAssistant`: `entityName`, `fieldName` and `recordTypeName` are "not updateable".
- Changing a field between `MasterDetail` and `Lookup` is not supported in a check-only deploy. Going from Lookup to MasterDetail needs every child record to have a parent, and a successful deploy permanently deletes child records in the Recycle Bin. A new MasterDetail field on an object that already has records needs those records soft-deleted first, or the deploy fails.
- A required lookup, a roll-up summary and an auto number field have special rules (below).

From secondary sources (field-type conversion help pages), to confirm in a sandbox:

- Text Area (Long) converts only to Email, Phone, Text, Text Area or Url.
- Multi-select picklist, Checkbox and Formula cannot convert to another type.
- Only Text can convert to Auto Number.
- Text to Picklist and Number to Text are allowed, with data caveats.
- MasterDetail to Lookup has no Change Field Type button.

The adapter must never emit a changed `type` for an existing field. It reports a manual migration step: create a new field, copy data, repoint views and rules, retire the old field. This matches safety rule 4.

## Unverified points the generator must not assume

1. `required` on a Lookup with `deleteConstraint` `SetNull`. We recall Salesforce rejects it. Emit `Restrict` if a required lookup is ever needed. Better: never emit `required` on a lookup.
2. `required` on a Checkbox or MasterDetail. Not valid. Skip it.
3. Whether a deploy that removes picklist values removes them. The guide only says additions happen. Treat removals as manual.
4. New fields are not placed on page layouts by a deploy. Users do not see them until a layout includes them. See open-questions.md.
