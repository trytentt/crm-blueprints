> Sources: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/api_meta.pdf (Metadata API Developer Guide v68.0: "CustomField" fields `referenceTo`, `relationshipName`, `relationshipLabel`, `relationshipOrder`, `deleteConstraint`, `reparentableMasterDetail`, `writeRequiresMasterRead`; "DeployOptions" `checkOnly`; "SharingModel"); https://raw.githubusercontent.com/forcedotcom/source-deploy-retrieve/main/test/snapshot/sampleProjects/customObjects-and-children/__snapshots__/verify-source-files.expected/force-app/main/default/objects/Property__c/fields/Broker__c.field-meta.xml; https://github.com/SalesforceFoundation/NPSP (MasterDetail files); https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf; https://raw.githubusercontent.com/jsforce/jsforce/main/src/types/common.ts (describe result shape)
> Last verified: 2026-10-04

# Salesforce relationships

A relationship is a field on the child object. There is no separate relationship object. One file creates both sides.

## Two kinds

| | Lookup | Master-detail |
|---|---|---|
| `type` | `Lookup` | `MasterDetail` |
| Parent can be | Any object (standard or custom) | Standard or custom |
| Child can be | Any object | Custom objects only (see note) |
| Child without a parent | Allowed, unless `required` | Not allowed |
| Delete behaviour | `deleteConstraint`: `SetNull` (default), `Restrict`, `Cascade` | Child is always deleted with the parent |
| Sharing | Independent | Child inherits the parent (`ControlledByParent`) |
| Roll-up summary on parent | No | Yes (`type` `Summary`) |

Note: the guide's field table does not state "child must be custom". It is long-standing platform behaviour. Confirm with a check-only deploy before relying on it.

## Cardinality mapping

Our `RelationshipDef` has `from_object`, `to_object`, `cardinality`, two labels and a purpose.

| Design cardinality | Salesforce build | Field lives on |
|---|---|---|
| `many_to_one` (many `from` to one `to`) | One `Lookup` | `from_object` |
| `one_to_many` (one `from` to many `to`) | One `Lookup` | `to_object` |
| `one_to_one` | `Lookup`, plus a validation rule or duplicate rule for uniqueness | the side the design names as dependent |
| `many_to_many` | Junction object with two `MasterDetail` fields (or two lookups) | the junction |

Why one-to-one is approximate: Salesforce has no unique constraint on a lookup. We have not found one in the guide. The planner must raise a manual step: "one-to-one is not enforced by the platform".

Default choice between lookup and master-detail: use `Lookup`. Use `MasterDetail` only when the design says the child cannot exist alone and needs roll-ups or parent-controlled sharing. Master-detail is harder to change (see below).

## Labels

- `label` on the field is the name shown on the child's page layout (for example "Broker").
- `relationshipLabel` is the name of the related list shown on the parent (for example "Properties").
- `relationshipName` is the plural API name from the parent's point of view (for example `Properties`). The parent query then reads `Properties__r`. Salesforce appends `__r`; do not write it.

Design mapping: `from_label` is the label of the field on the child. `to_label` is the `relationshipLabel` on the parent. `relationshipName` is `to_label` with spaces replaced by underscores, ASCII only. Name collisions on the parent object are possible; the generator must check the parent's existing relationship names (from `sf sobject describe` `childRelationships`) before it plans a change.

## Minimal Lookup (real file, Dreamhouse sample)

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

Path: `force-app/main/default/objects/Property__c/fields/Broker__c.field-meta.xml`. Manifest member: `Property__c.Broker__c`, type `CustomField`.

## Minimal MasterDetail (real file, NPSP)

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

- `reparentableMasterDetail` default false: children cannot move to another parent.
- `writeRequiresMasterRead` false (default): users need Read/Write on the parent to change children. True is less strict (Read is enough).

## Many-to-many: the junction object

A junction object is a custom object with two master-detail fields (guide, `relationshipOrder`). One parent is primary (`relationshipOrder` 0). The other is secondary (1). The primary parent decides look and feel, record ownership and delete behaviour.

Example: `Placement__c` links `Candidate__c` and `Search__c`.

```
objects/Placement__c/Placement__c.object-meta.xml
objects/Placement__c/fields/Candidate__c.field-meta.xml     (MasterDetail, relationshipOrder 0)
objects/Placement__c/fields/Search__c.field-meta.xml        (MasterDetail, relationshipOrder 1)
```

The object file uses `sharingModel` `ControlledByParent` (to confirm; see objects.md) and an `AutoNumber` name field. Build order: create both parent objects first, then the junction object, then its two fields. In one source deploy the CLI orders components itself, but a first deploy that mixes new parents and the junction is the place a dependency error shows up. Check-only first.

A junction that points at a standard parent (for example `Opportunity`) is allowed as a detail of a custom object. Roll-up summary fields on the parents are possible (`type` `Summary` with `summaryForeignKey`, `summaryOperation`, `summarizedField`). The generator does not emit them in v1.

## The lookup to `User`

`referenceTo` `User`. See fields.md. Each lookup to `User` needs a distinct `relationshipName`.

## Hard limits

- The cheat sheet notes that a custom object allows up to 40 relationships that a single query can reference, and a query can name 55 child-to-parent relationships in total.
- Per-object master-detail limits (two per custom object) are well known but not stated in the pages read. Treat as unverified.
- Edition caps on custom fields apply to relationship fields too (objects.md).

## Changing a relationship later

From the guide (`checkOnly` and `DeployOptions`):

- Lookup to master-detail: every child record must reference a parent, or be soft-deleted first. A successful deploy permanently deletes any child records in the Recycle Bin.
- A new master-detail field on an object that already holds records: soft-delete the records first, or the deploy fails. It then purges them from the Recycle Bin.
- Master-detail to lookup, or the reverse, is not supported by `--dry-run`. The check-only deploy fails with an error. Validate in a full-copy or other sandbox instead.

The adapter treats any change of relationship type as a manual migration step, never an automatic change.

## Reading relationships

`sf sobject describe --sobject Property__c --json` returns `result.fields[]` and `result.childRelationships[]`.

Key reference-field properties (jsforce `Field` type): `type` is `reference`; `referenceTo` is a list of target object names; `relationshipName` is the name without `__r`; `cascadeDelete` and `restrictedDelete` show master-detail and `Restrict`; `writeRequiresMasterRead`; `relationshipOrder`; `nillable` false for master-detail.

`childRelationships[]` entries carry `childSObject`, `field`, `relationshipName`, `cascadeDelete`, `restrictedDelete`, `junctionReferenceTo`.

Describe cannot tell a lookup from a master-detail except by `cascadeDelete` true plus `nillable` false and `writeRequiresMasterRead`. For a reliable answer, retrieve the field file (`sf project retrieve start --metadata CustomField:Property__c.Broker__c`) and read `<type>`.
