> Sources: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/api_meta.pdf (Metadata API Developer Guide v68.0: "ListView", "ListViewFilter", "FilterScope", "PermissionSet", "PermissionSetFieldPermissions", "PermissionSetObjectPermissions", "PermissionSetRecordTypeVisibility", "PermissionSetTabSetting"); https://raw.githubusercontent.com/forcedotcom/source-deploy-retrieve/main/test/snapshot/sampleProjects/customObjects-and-children/__snapshots__/verify-source-files.expected/force-app/main/default/objects/Property__c/listViews/All.listView-meta.xml; https://github.com/SalesforceFoundation/NPSP (Opportunity and Batch__c list views); https://raw.githubusercontent.com/forcedotcom/source-deploy-retrieve/main/test/snapshot/sampleProjects/preset-PermSet/__snapshots__/verify-source-files.expected/force-app/main/default/permissionsets/dreamhouse.permissionset-meta.xml; https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/sfdx_dev.pdf (DX Developer Guide v68.0: "Decomposed Metadata Types")
> Last verified: 2026-10-04

# Salesforce views, lists and field visibility

## List views

A saved view of records on one object.

Path:

```
force-app/main/default/objects/<Object>/listViews/<ViewApiName>.listView-meta.xml
```

Works for standard objects too (`objects/Opportunity/listViews/...`). Manifest member: `Opportunity.My_open_renewals`, type `ListView`.

Minimal file with a filter (real shape from NPSP; field and label names ours):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ListView xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Open_renewals</fullName>
    <booleanFilter>1 AND 2</booleanFilter>
    <columns>OPPORTUNITY.NAME</columns>
    <columns>ACCOUNT.NAME</columns>
    <columns>OPPORTUNITY.AMOUNT</columns>
    <columns>OPPORTUNITY.CLOSE_DATE</columns>
    <columns>OPPORTUNITY.STAGE_NAME</columns>
    <columns>Renewal_date__c</columns>
    <filterScope>Everything</filterScope>
    <filters>
        <field>OPPORTUNITY.RECORDTYPE</field>
        <operation>equals</operation>
        <value>Opportunity.Renewals</value>
    </filters>
    <filters>
        <field>OPPORTUNITY.CLOSED</field>
        <operation>equals</operation>
        <value>0</value>
    </filters>
    <label>Open renewals</label>
</ListView>
```

- Required (guide): `fullName`, `filterScope`, `label`.
- `columns`: custom fields by API name. Standard fields use internal tokens, not API names. Real examples: `NAME`, `LAST_UPDATE`, `OPPORTUNITY.NAME`, `OPPORTUNITY.AMOUNT`, `OPPORTUNITY.CLOSE_DATE`, `OPPORTUNITY.STAGE_NAME`, `ACCOUNT.NAME`. The guide warns that column names do not always match API names. The `OPPORTUNITY.RECORDTYPE` and `OPPORTUNITY.CLOSED` filter tokens above are from memory and unverified. To learn the right token for any standard field, create one view by hand in a sandbox and retrieve it. Then reuse the token.
- `filters`: each has `field`, `operation`, `value`. Operations (guide): `equals`, `notEqual`, `lessThan`, `greaterThan`, `lessOrEqual`, `greaterOrEqual`, `contains`, `notContain`, `startsWith`, `includes`, `excludes`, `within`.
- A multi-value `equals` uses a comma list in `value` (real NPSP file: `To Be Acknowledged,Email Acknowledgment Not Sent`).
- `booleanFilter` combines the numbered filters, for example `(1 AND 2) OR 3`.
- `filterScope` values: `Everything`, `Mine`, `MineAndMyGroups`, `AssignedToMe` (service appointments only), `Queue`, `Delegated`, `MyTerritory`, `MyTeamTerritory`, `Team`, `SalesTeam`, `ScopingRule`. Our views use `Everything` or `Mine`.
- `sharedTo` controls who sees the view. Child elements include `allInternalUsers`, `group`, `role`, `roleAndSubordinates`, `queue`. Without it the view is not shared as intended. List views with "Visible only to me" are not reachable through the Metadata API at all (guide). Always share the generated views. The exact `sharedTo` XML is unverified. Open question; test in a sandbox.
- `language` is only needed when you use `startsWith` or `contains` on a Translation Workbench org.

### Sort order is not in the metadata

`ListView` has no sort element in the guide's field list. Our design `View.sort` therefore cannot be applied by deploy. The build sheet must list it as a manual step ("sort by column in the list view controls and save"), and the planner records it as a known gap.

### What we do not generate

- Kanban display, charts, split view: UI settings on the list view, not in the metadata.
- Reports and dashboards: separate metadata types (`Report`, `Dashboard`). Out of v1.
- Search layouts, compact layouts, page layouts. See open-questions.md.

## Field visibility: permission sets

Visibility is a separate question from existence. A new field is invisible to everyone but System Administrators until a profile or permission set grants it. The generated build ships one permission set per blueprint.

Path (permission sets are not decomposed by default; decomposition is a beta option the CLI turns on with `sf project convert source-behavior`):

```
force-app/main/default/permissionsets/<Name>.permissionset-meta.xml
```

Manifest: type `PermissionSet`, wildcard supported.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Day-to-day access to the recruitment blueprint objects and fields.</description>
    <hasActivationRequired>false</hasActivationRequired>
    <label>Recruitment blueprint user</label>
    <fieldPermissions>
        <editable>true</editable>
        <field>Search__c.Stage__c</field>
        <readable>true</readable>
    </fieldPermissions>
    <fieldPermissions>
        <editable>false</editable>
        <field>Opportunity.Renewal_date__c</field>
        <readable>true</readable>
    </fieldPermissions>
    <objectPermissions>
        <allowCreate>true</allowCreate>
        <allowDelete>false</allowDelete>
        <allowEdit>true</allowEdit>
        <allowRead>true</allowRead>
        <modifyAllRecords>false</modifyAllRecords>
        <object>Search__c</object>
        <viewAllRecords>false</viewAllRecords>
    </objectPermissions>
    <recordTypeVisibilities>
        <recordType>Opportunity.Renewals</recordType>
        <visible>true</visible>
    </recordTypeVisibilities>
    <tabSettings>
        <tab>Search__c</tab>
        <visibility>Visible</visibility>
    </tabSettings>
</PermissionSet>
```

Shapes verified against the real Dreamhouse permission set and the guide.

Rules:

- `label` is required. `fieldPermissions` need `field` (`Object.Field`) and `editable`. `readable` is optional.
- Permissions for fields that are required cannot be retrieved or deployed (guide, API 30.0 and later). That covers a field with `required` true, a master-detail field, and the object `Name` field. Leave these out of `fieldPermissions`. They are visible whenever the object is.
- With the View All Fields object permission on, individual fields are not listed (guide, API 54.0 and later).
- A permission set can grant access, never deny it.
- "When you deploy a permission set, you must include all of its metadata to avoid accidentally overwriting the permission set's contents" (guide, API 40.0 and later). The generator therefore writes the whole file every time and never patches it. When an engagement adds a field later, regenerate the whole file from the design and from a fresh retrieve. Merge by hand if the client has added their own entries.
- Object access should be granted in the same file. Field permissions depend on read access to the object. This dependency is from experience and is not stated in the pages read; the first dry run will show it.
- Record type visibility for the record types created by the pipelines.
- Reading access to the file needs View Setup and Configuration, Manage Profiles and Permission Sets, Assign Permission Sets, or Manage Session Permission Set Activations (guide, "Special Access Rules").
- Assigning the permission set to a user is a data operation, not metadata: `sf org assign permset --name <Name> --target-org <alias>` (command not read; confirm) or Setup, Users, Permission Sets, Manage Assignments. Manual step in v1.
- Profiles also carry field and object permissions, but a deploy of a profile overwrites far more. We never ship profiles.

## Reading view and permission state

- `sf project retrieve start --metadata "ListView:Opportunity.*" --json` (wildcard needs quotes; the CLI help shows `'ListView:Case*'`).
- `sf project retrieve start --metadata PermissionSet:<Name> --json`.
- `sf data query --query "SELECT Id, Name, SobjectType FROM ListView WHERE SobjectType = 'Opportunity'" --json` lists views without downloading them (standard `ListView` sObject; query not run in this research).
