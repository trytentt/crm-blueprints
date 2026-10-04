> Sources: https://developers.hubspot.com/docs/api-reference/latest/crm/objects/schemas/guide.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/objects/schemas/create-schema.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/objects/schemas/update-schema.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/objects/schemas/get-schemas.md ; https://developers.hubspot.com/docs/api-reference/legacy/crm/objects/schemas/guide.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/understanding-the-crm.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/objects/custom-objects/guide.md ; https://knowledge.hubspot.com/object-settings/create-custom-objects ; https://legal.hubspot.com/hubspot-product-and-services-catalog ; https://developers.hubspot.com/docs/api-reference/latest/crm/limits-tracking/guide.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/crm-data-model/guide.md
> Last verified: 2026-10-04

# HubSpot: objects

`{V}` is the pinned API version, currently `2026-09` (see `auth-and-setup.md`).

## Standard objects we use

| Our object | HubSpot object | `objectTypeId` | Path name |
|---|---|---|---|
| Company | Companies | `0-2` | `companies` |
| Person | Contacts | `0-1` | `contacts` |
| Deal | Deals | `0-3` | `deals` |
| (tickets, for later) | Tickets | `0-5` | `tickets` |

Paths accept either the type ID or, for contacts, companies, deals, tickets and notes, the plain name. Custom objects always use their own ID (`2-XXXXXXX`) or fully qualified name (`p{HubId}_{name}`).

Other standard objects exist (products, quotes, leads `0-136`, invoices `0-53`, and so on). Some need to be enabled first; `GET /crm/object-library/{V}/enablement` reports which are enabled (Object Activation API). Not needed for the v1 blueprints.

## Custom objects

### Plan requirements

- Creating a custom object schema through the API needs an **Enterprise** subscription on a Marketing, Sales, Service, Content, Data, Revenue Hub or Smart CRM. Source: the "Supported products" panel and OpenAPI tier requirements on the schemas guide, and the knowledge base article "Create and edit custom objects" (Enterprise for every hub listed).
- Free, Starter and Professional accounts cannot create custom objects. The adapter must check this before planning and turn custom objects into a blocked, manual-or-upgrade item.
- A developer test account has a 90-day Enterprise trial, so it can be used to test custom objects.

### Limits

From the HubSpot Products and Services Catalog (feature tables per hub, Enterprise edition):

| Hub (Enterprise) | Custom object definitions | Total custom object records |
|---|---|---|
| Marketing, Sales, Service, Content | up to 10 | 1,000,000 |
| Data Hub | up to 20 | 1,500,000 |

The catalog is a long page with one table per hub, so the pairing of numbers to hubs should be re-checked per client (OQ-3). The Limits Tracking API reports the real numbers for an account: `GET /crm/limits/{V}/custom-object-types` and `GET /crm/limits/{V}/records`.

Other limits that touch objects:
- Custom properties: the catalog lists 1,000 custom properties per object for Smart CRM Starter, Professional and Enterprise, and 10 in total for the free tools.
- Object API batch endpoints take at most 100 inputs per request.
- A schema can only be deleted once all its records, associations and properties are deleted. To reuse a name after deleting, hard delete with `?archived=true`.

### Create a schema

`POST https://api.hubapi.com/crm-object-schemas/{V}/schemas`

Scope: `crm.schemas.custom.write`. Success: `201` with a `Location` header and the full schema.

| Field | Type | Notes |
|---|---|---|
| `name` | string | Internal name. Cannot change later. Letters, numbers and underscores only; first character a letter. |
| `labels.singular`, `labels.plural` | string | Display words. The OpenAPI text says "no way to change this later"; the PATCH schema does accept `labels` (OQ-4). Treat as fixed. |
| `description` | string | Optional. |
| `properties` | object[] | Property definitions (see `fields.md`). Each needs `name`, `label`, `type`, `fieldType`. Type defaults to `string` and fieldType to `text` if omitted. |
| `primaryDisplayProperty` | string | The property that names each record. Must be one of `properties`. |
| `secondaryDisplayProperties` | string[] | Shown under the name on the record. |
| `searchableProperties` | string[] | Indexed for HubSpot search. |
| `requiredProperties` | string[] | Required when creating a record. |
| `associatedObjects` | string[] | `objectTypeId` values the object can associate with, for example `["0-1","0-2"]`. |
| `allowsSensitiveProperties` | boolean | Only for Sensitive Data properties. |
| `shouldCreateSameObjectAssociation` | boolean | Appears in the OpenAPI as part of the create body. |

The OpenAPI schema for the create body marks `allowsSensitiveProperties`, `associatedObjects`, `labels`, `name`, `properties`, `requiredProperties`, `searchableProperties`, `secondaryDisplayProperties` and `shouldCreateSameObjectAssociation` as required, but the guide's example omits several of them. The adapter should send all of them (empty arrays and `false` where there is no value). See OQ-4.

Minimal example:

```json
{
  "name": "subscription",
  "labels": { "singular": "Subscription", "plural": "Subscriptions" },
  "description": "A recurring plan held by a company.",
  "primaryDisplayProperty": "subscription_name",
  "secondaryDisplayProperties": [],
  "searchableProperties": ["subscription_name"],
  "requiredProperties": ["subscription_name"],
  "allowsSensitiveProperties": false,
  "shouldCreateSameObjectAssociation": false,
  "associatedObjects": ["0-2"],
  "properties": [
    { "name": "subscription_name", "label": "Subscription name", "type": "string", "fieldType": "text" }
  ]
}
```

Response (shape, abridged): `id`, `objectTypeId` (for example `2-3465404`), `fullyQualifiedName` (`p{HubId}_subscription`), `name`, `labels`, `properties[]`, `associations[]`, `requiredProperties`, `searchableProperties`, `primaryDisplayProperty`, `secondaryDisplayProperties`, `archived`, `createdAt`, `updatedAt`.

### Rules that bite

- The primary display property and the required and searchable lists must name properties that already exist. When adding them later by PATCH, create the property first.
- Custom objects get associations with calls, emails, meetings, notes, tasks and conversations automatically. Associations to any other object must be declared in `associatedObjects` at creation or added later with association labels (`relationships.md`).
- A custom object's `requiredProperties` is the only API-level "required field" setting. Standard objects have no such setting in the API (OQ-9).

### Read, update, delete

| Action | Request |
|---|---|
| List all schemas | `GET /crm-object-schemas/{V}/schemas` (options exist to include property and association definitions) |
| Read one | `GET /crm-object-schemas/{V}/schemas/{objectTypeId}` or `/{fullyQualifiedName}` |
| Update | `PATCH /crm-object-schemas/{V}/schemas/{objectTypeId}` |
| Delete | `DELETE /crm-object-schemas/{V}/schemas/{objectType}`; add `?archived=true` for a hard delete |

PATCH body fields: `clearDescription` (required boolean), `description`, `labels`, `primaryDisplayProperty`, `requiredProperties`, `searchableProperties`, `secondaryDisplayProperties`, `restorable`, `allowsSensitiveProperties`. `name` cannot be changed by API.

Legacy equivalents use `/crm-object-schemas/v3/schemas`.

### Records

Custom object records use the generic object API: `POST /crm/objects/{V}/{objectTypeId}` with `{ "properties": { ... } }`. Not part of structure building, but needed for tests and seed data.

## Manual alternative

Settings > Data Management > Objects > Create custom object (needs account access permissions and Enterprise). Use this when the account is not Enterprise only to confirm the block; there is no workaround.
