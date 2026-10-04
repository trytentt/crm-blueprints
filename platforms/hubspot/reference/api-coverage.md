> Sources: https://developers.hubspot.com/docs/api-reference/latest/crm/objects/schemas/guide.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/properties/guide.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/pipelines/guide.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/pipelines/rules/guide.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/associations/associations-schema/guide.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/lists/guide.md ; https://developers.hubspot.com/docs/api-reference/legacy/automation/workflows/guide.md ; https://knowledge.hubspot.com/object-settings/set-up-and-customize-pipelines ; https://knowledge.hubspot.com/records/create-and-manage-saved-views ; https://developers.hubspot.com/docs/_llms/apis/2026-09/crm.md
> Last verified: 2026-10-04

# HubSpot: API coverage

Every design concept, mapped to automated (endpoint) or manual (UI path and reason). `{V}` = pinned version, `2026-09`. Base URL `https://api.hubapi.com`. "Legacy" is the semantic-version fallback that still works.

## Table

| Design concept | Mode | Endpoint or UI path | Legacy fallback | Notes |
|---|---|---|---|---|
| Object: Company, Person, Deal | Automated (exists) | Built in. Read: `GET /crm/properties/{V}/companies` etc. | `/crm/v3/properties/...` | Nothing to create. |
| Object: custom | Automated, Enterprise only | `POST /crm-object-schemas/{V}/schemas` | `/crm-object-schemas/v3/schemas` | Not on Free, Starter, Professional: manual-block with upgrade note. Name and labels fixed after create. |
| Object: delete | Manual | Settings > Data Management > Objects | `DELETE .../schemas/{id}` exists | Destructive; we never delete. |
| Property group | Automated | `POST /crm/properties/{V}/{object}/groups` | `/crm/v3/properties/{object}/groups` | Create before properties. |
| Field: text | Automated | `POST /crm/properties/{V}/{object}` with `string`/`text` | `/crm/v3/properties/{object}` | |
| Field: long_text | Automated | same, `string`/`textarea` | same | |
| Field: select | Automated | same, `enumeration`/`select` + `options` | same | |
| Field: multi_select | Automated | same, `enumeration`/`checkbox` + `options` | same | |
| Field: number | Automated | same, `number`/`number` | same | |
| Field: currency | Automated, lossy | same, `number`/`number` + `showCurrencySymbol` | same | No currency code on the field. |
| Field: percent | Automated, lossy | same, `number`/`number` + `numberDisplayHint: percentage` | same | Storage convention unconfirmed (OQ-5). |
| Field: date | Automated | same, `date`/`date` | same | |
| Field: datetime | Automated | same, `datetime`/`date` | same | |
| Field: checkbox | Automated | same, `bool`/`booleancheckbox` | same | |
| Field: url | Automated, lossy | same, `string`/`text` | same | No URL validation. |
| Field: email | Automated, lossy | same, `string`/`text` + `textDisplayHint: email` | same | |
| Field: phone | Automated | same, `string`/`phonenumber` | same | |
| Field: user | Automated | same, `enumeration`/`select`, `externalOptions: true`, `referencedObjectType: OWNER` | same | Value is owner ID. |
| Field inside a custom object | Automated | `properties[]` in the schema create, or the property endpoint after | same | |
| Field: required | Custom objects: Automated | `requiredProperties` in schema create or `PATCH /crm-object-schemas/{V}/schemas/{id}` | `/v3/` | |
| Field: required, standard objects | Manual | Property settings or a workflow; see OQ-9 | | No API setting. |
| Field: unique value | Automated | `hasUniqueValue: true` at create | | Cannot be changed later; max 10 per object. |
| Option (select / multi_select) | Automated | `options[]` on create; `PATCH /crm/properties/{V}/{object}/{name}` to change | `/crm/v3/properties/...` | Hide rather than delete. |
| Primary display property | Automated | `primaryDisplayProperty` in the schema (custom objects only) | | Standard objects have built-in ones. |
| Searchable properties | Automated | `searchableProperties` in the schema (custom objects only) | | |
| Relationship (standard pair) | Automated (exists) | Built in; read with `GET /crm/associations/{V}/{from}/{to}/labels` | `/crm/associations/v4/{from}/{to}/labels` | |
| Relationship (custom object to other) | Automated | `associatedObjects` in schema create; else label call | | See OQ-7 for existing pairs. |
| Relationship label (single or paired) | Automated, Professional+ | `POST /crm/associations/{V}/{from}/{to}/labels` | `POST /crm/associations/v4/{from}/{to}/labels` | `inverseLabel` for pairs. 10 or 50 labels per pair (OQ-2). |
| Relationship label: read | Automated | `GET /crm/associations/{V}/{from}/{to}/labels` | `GET /crm/associations/v4/{from}/{to}/labels` | |
| Relationship cardinality | Automated, Professional+ | `POST /crm/associations/{V}/definitions/configurations/{from}/{to}/batch/create` | `/crm/associations/v4/definitions/configurations/...` | `maxToObjectIds`. |
| Pipeline (deals, custom objects, tickets) | Automated | `POST /crm/pipelines/{V}/{object}` | `/crm/v3/pipelines/{object}` | Custom pipelines: Starter+ (15), Professional (100), Enterprise (350); custom object pipelines Enterprise. |
| Stage | Automated | in pipeline create, or `POST /crm/pipelines/{V}/{object}/{pipelineId}/stages` | `/crm/v3/pipelines/...` | Max 100 per pipeline for deals, tickets, custom. |
| Stage: won / lost (deals) | Automated | `metadata.probability` `"1.0"` / `"0.0"` | same | `isClosed` shows on read. |
| Stage: won / lost (other objects) | Partly | Open or closed only; key unconfirmed (OQ-1) | | No won/lost split outside deals. |
| Probability | Automated (deals) | `metadata.probability` string `"0.0"` to `"1.0"` | same | |
| Required field per stage | **Manual** | Settings > Data Management > Objects > object > Pipelines > pipeline > stage row > Conditional logic rules > Add rule > Add property > Required | | Conditional stage properties have no API. Pipeline Rules API does not cover it. |
| Stage movement rules, creation rules, edit permissions | Automated (optional) | `PUT/PATCH /crm/pipelines-rules/{V}/{objectTypeId}/{pipelineId}` | none | Dated versions only. |
| Deal approvals | Automated (optional) | same `approvalStageRules` | none | Sales Hub Enterprise. |
| View (saved index-page view) | **Manual** | CRM > object > + add view > filters, columns, sort > Publish | | No API found. |
| List / segment | Automated | `POST /crm/lists/{V}/` | `POST /crm/v3/lists` | `MANUAL`, `DYNAMIC`, `SNAPSHOT`. |
| Automation (workflow) | **Manual** by default | Automations > Workflows > Create workflow | beta `/automation/v4/flows` | API is beta; off by default. Professional+. |
| Permission (roles, field-level, team access) | **Manual** | Settings > Users & Teams for roles (menu name not verified against a page I read); field-level permissions are a Smart CRM Enterprise feature in the product catalog | | No permission-set API in the pages read. Pipeline stage edit permissions are the one automated slice (above). |
| Custom object records, seed data | Automated | `POST /crm/objects/{V}/{objectTypeId}`, imports API | `/crm/v3/objects/...` | For tests and demo data only. |

## Order of operations for apply

1. Read limits (`/crm/limits/{V}/...`) and the object library enablement.
2. Property groups.
3. Custom object schemas (with their properties and `associatedObjects`).
4. Properties on standard objects (and any remaining on custom objects).
5. Association labels, then association limits.
6. Pipelines and stages (custom pipelines, then any default-pipeline changes as manual or `needs_review`).
7. Pipeline rules (optional).
8. Lists (optional).
9. Emit manual steps: stage-required fields, saved views, workflows, permissions.

## Safety notes for the planner

- Deleting or changing a pipeline stage that is in use fails by default in `2026-09`. Do not pass the bypass flags.
- Never change a property `type` or `fieldType`, and never archive properties. These become destructive manual steps.
- The default Sales pipeline (`default`) exists on every account. Editing it is `needs_review`, never `safe`.
