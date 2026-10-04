> Sources: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/api_meta.pdf (Metadata API Developer Guide v68.0: "Flow", "FlowStart" `triggerType` and `recordTriggerType`, "FlowDefinition", "ValidationRule", "LeadConvertSettings", "Settings"); https://raw.githubusercontent.com/forcedotcom/source-deploy-retrieve/main/src/registry/metadataRegistry.json (flow paths); https://dev.to/tdrnk/salesforce-flow-deactivation-using-metadata-api-5dn4 (secondary: a real record-triggered `<start>` block and FlowDefinition); https://raw.githubusercontent.com/trailheadapps/dreamhouse-lwc/main/force-app/main/default/flows/Create_property.flow-meta.xml (real flow file, a screen flow, for the `recordCreates` shape)
> Last verified: 2026-10-04

# Salesforce automation

## What can be created through the Metadata API

| Design `automation` | Salesforce mechanism | Deployable? | v1 decision |
|---|---|---|---|
| Block a save unless data is present | Validation rule | Yes | Generate (see pipelines.md) |
| Do something when a record changes (create task, update field, notify) | Record-triggered Flow | Yes, as `Flow` metadata | **Manual step by default.** Optional skeleton behind a flag. |
| Run on a schedule | Scheduled-triggered Flow | Yes | Manual |
| Approval chain | Approval process | Yes (`ApprovalProcess`) | Manual |
| Copy custom fields when a Lead converts | `LeadConvertSettings` | Yes | Generate (see below) |
| Assignment, escalation | Assignment rules, escalation rules | Yes | Manual |
| Workflow rules, Process Builder | Legacy | Workflow deployable; Process Builder retired | Never generate |
| Apex triggers | Code | Yes | Out of scope |

The guide's `Flow` type page lists the limits that shape the choice:

- Flows are stored under `flows/` with the extension `.flow` (source: `.flow-meta.xml`).
- A flow file name must not contain spaces.
- You can deploy changes to an active flow in a sandbox or scratch org. In production you must first enable the Deploy processes and flows as active preference. Without it a production deploy lands the flow inactive. That preference is a Setup page.
- A flow version with paused interviews cannot be deleted.
- Do not hand-edit retrieved Process Builder processes.
- If a deploy includes a `FlowDefinition`, its `activeVersionNumber` overrides the flow's `status`. Use `activeVersionNumber` 0 to deactivate. Leave `FlowDefinition` out; use `status` in the flow.

## Should the repo generate record-triggered flows?

Recommendation: no, not as a default.

Reasons:

1. A usable flow is a graph: a start node, one or more action nodes, and connectors with canvas coordinates. The shape depends on what the action is. We have verified only the start node and the `recordCreates` node from real files. We have not deployed a record-triggered flow anywhere.
2. A flow runs on every save and on every API write. A wrong flow can corrupt data in bulk. The review step we want (a human reading a plan) is hard to do on flow XML.
3. A flow cannot be deleted from source. Removal is manual. Each deploy to a sandbox adds a version.
4. Production needs a Setup preference to even activate one.
5. The blueprints' automations are short sentences ("when a deal reaches Closed Won, create a delivery record"). They are better reviewed as a manual build instruction with a Setup path and a done-when line.

So: `automation` entries produce a manual step with a ready-to-follow description, a Setup path, and the design's trigger and action text. Quote the trigger object, the entry condition, and the action. Flow Builder path: Setup, Flows, New Flow, Record-Triggered Flow.

For teams that want a head start, the generator can write a Draft skeleton under a flag (off by default), one per simple automation, with `status` `Draft` so nothing runs until a human opens it in Flow Builder and activates it.

### Skeleton (not tested against an org)

Assembled from the guide's enumerations, the real `<start>` block quoted in the secondary source, and the real `recordCreates` shape in the Dreamhouse flow. The element order follows what Salesforce writes (alphabetical by element name at the top level). Proof needed: a check-only deploy.

Path: `force-app/main/default/flows/Create_delivery_on_closed_won.flow-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <description>When a deal reaches Closed Won, create the delivery record.</description>
    <interviewLabel>Create delivery on closed won {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Create delivery on closed won</label>
    <processType>AutoLaunchedFlow</processType>
    <recordCreates>
        <name>Create_delivery</name>
        <label>Create delivery</label>
        <locationX>176</locationX>
        <locationY>335</locationY>
        <inputAssignments>
            <field>Opportunity__c</field>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </inputAssignments>
        <object>Delivery__c</object>
    </recordCreates>
    <start>
        <locationX>50</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Create_delivery</targetReference>
        </connector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>StageName</field>
            <operator>EqualTo</operator>
            <value>
                <stringValue>Closed Won</stringValue>
            </value>
        </filters>
        <object>Opportunity</object>
        <recordTriggerType>Update</recordTriggerType>
        <triggerType>RecordAfterSave</triggerType>
    </start>
    <status>Draft</status>
</Flow>
```

Notes:

- `triggerType` values from the guide include `RecordAfterSave`, `RecordBeforeSave` and `RecordBeforeDelete`. `recordTriggerType` values are `Create`, `Update`, `CreateAndUpdate`, `Delete`, `None`. The guide text says `recordTriggerType` is "available only when `triggerType` is `RecordBeforeSave` or `DataCloudDataChange`". The secondary source shows `Update` with `RecordAfterSave` in a working file, so the guide text looks incomplete. Another reason to prove it with a dry run.
- `filters` and `filterLogic` on the start node are from the Flow schema (`FlowStart.filters`). The operator spelling `EqualTo` is the one used in the real Dreamhouse and sample flows.
- To fire only when the stage becomes Closed Won (not on every later edit), flows use the `$Record__Prior` global. That needs a decision element. Not in the skeleton. Another reason to leave flows manual.
- `locationX` and `locationY` are canvas positions. Flow Builder re-lays out the canvas.
- Production activation: needs the preference above.

## Lead conversion field mapping

This one is metadata.

`LeadConvertSettings` holds custom field mappings from Lead to Account, Contact and Opportunity, the option to let users change the owner at conversion, and whether the Opportunity box is optional, required or hidden (guide, `LeadConvertSettings`, API 39.0 and later).

Source path (from the registry, `directoryName` `LeadConvertSettings`, suffix `LeadConvertSetting`):

```
force-app/main/default/LeadConvertSettings/LeadConvertSettings.LeadConvertSetting-meta.xml
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LeadConvertSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <allowOwnerChange>false</allowOwnerChange>
    <objectMapping>
        <inputObject>Lead</inputObject>
        <mappingFields>
            <inputField>Source_campaign_note__c</inputField>
            <outputField>Original_source_note__c</outputField>
        </mappingFields>
        <outputObject>Account</outputObject>
    </objectMapping>
    <opportunityCreationOptions>VisibleOptional</opportunityCreationOptions>
</LeadConvertSettings>
```

Rules from the guide:

- Up to three `objectMapping` entries: one each for Account, Contact and Opportunity.
- `inputObject` is always `Lead`.
- Only custom fields can be mapped (`inputField` and `outputField` are described as custom fields). The standard mappings (Company to Account Name, and so on) are fixed by Salesforce and cannot be edited.
- `opportunityCreationOptions`: `VisibleOptional` (default), `VisibleRequired`, `NotVisible`.
- Settings types are normally addressed through type `Settings` with a member without the "Settings" suffix. The `LeadConvertSettings` page says that, but the registry also exposes a standalone `LeadConvertSettings` type and directory. Which package.xml form retrieves it is unverified. Open question.
- Field-compatibility rules (matching data types and lengths between source and target) are a UI rule; not found in the pages read.

What stays manual: nothing in the mapping itself, if only custom fields are involved. Mapping to or from standard fields is not possible. The Setup path for a check: Setup, Object Manager, Lead, Fields and Relationships, Map Lead Fields.

The Lead conversion process itself (the "Convert" button, creating the Account, Contact and Opportunity) is a platform feature, not something we build.

## Approvals and assignment

Not covered by blueprints in v1. Both are deployable metadata types (`ApprovalProcess`, `AssignmentRules`). Add only if a blueprint needs them and a human has designed them. Manifest samples in the guide: `Case` and `Lead` under `AssignmentRules`.

## Reading automation state

- `sf project retrieve start --metadata Flow --json` retrieves all flows (latest version of each).
- `sf data query --use-tooling-api --query "SELECT DeveloperName, ProcessType, TriggerType, ActiveVersionId FROM FlowDefinitionView" --json` lists flows with their active version. `FlowDefinitionView` is not covered in the pages read; treat the query as unverified.
