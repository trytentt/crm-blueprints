> Sources: https://developers.hubspot.com/docs/api-reference/latest/crm/properties/guide.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/properties/create-property.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/properties/update-property.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/properties/property-groups/create-property.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/objects/schemas/create-schema.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/objects/schemas/guide.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/property-validations/guide.md ; https://legal.hubspot.com/hubspot-product-and-services-catalog
> Last verified: 2026-10-04

# HubSpot: properties (fields)

HubSpot calls fields **properties**. Every property has a `type` (the data type) and a `fieldType` (how it looks and is edited). Both are required on create.

`{V}` is the pinned API version, currently `2026-09`.

## Create a property

`POST https://api.hubapi.com/crm/properties/{V}/{objectType}`

`{objectType}` is `contacts`, `companies`, `deals`, `tickets`, or a custom object ID or fully qualified name. Success is `201` with the property. Scopes: `crm.schemas.<object>.write` (see `auth-and-setup.md`). Tier: the endpoint itself is free-tier; limits below.

Required body fields: `groupName`, `name`, `label`, `type`, `fieldType`.

```json
{
  "groupName": "deal_qualification",
  "name": "budget_confirmed",
  "label": "Budget confirmed",
  "type": "bool",
  "fieldType": "booleancheckbox",
  "description": "Has the buyer confirmed budget?"
}
```

Select example (enumeration needs `options`):

```json
{
  "groupName": "deal_qualification",
  "name": "lead_source_detail",
  "label": "Lead source detail",
  "type": "enumeration",
  "fieldType": "select",
  "options": [
    { "label": "Referral", "value": "referral", "displayOrder": 0, "hidden": false },
    { "label": "Webinar",  "value": "webinar",  "displayOrder": 1, "hidden": false }
  ]
}
```

Other accepted create fields: `description`, `displayOrder` (lowest first; `-1` means last), `hidden`, `formField`, `hasUniqueValue`, `numberDisplayHint`, `showCurrencySymbol`, `currencyPropertyName`, `textDisplayHint`, `dataSensitivity`, `calculationFormula`, `externalOptions`, `referencedObjectType`.

Inside a custom object schema, the same property objects go in `properties[]`; there the owner reference field is called `externalOptionsReferenceType`.

Other endpoints (all under `/crm/properties/{V}/{objectType}`):

| Action | Request |
|---|---|
| Read all | `GET /crm/properties/{V}/{objectType}` (add `?dataSensitivity=sensitive` for sensitive ones, Enterprise) |
| Read one | `GET .../{propertyName}` |
| Update (partial) | `PATCH .../{propertyName}` |
| Archive | `DELETE .../{propertyName}` (moves to recycle bin) |
| Batch create / read / archive | `POST .../batch/create`, `.../batch/read`, `.../batch/archive` |

Read response shape (per property): `name`, `label`, `type`, `fieldType`, `groupName`, `description`, `options[]` (`label`, `value`, `displayOrder`, `hidden`), `displayOrder`, `calculated`, `externalOptions`, `hasUniqueValue`, `hidden`, `formField`, `archived`, `createdAt`, `updatedAt`, `modificationMetadata` (`archivable`, `readOnlyDefinition`, `readOnlyValue`). Use `modificationMetadata.readOnlyDefinition` to skip HubSpot-owned properties when diffing.

## Property groups

Groups organise properties on the record. Create one before the properties that use it.

`POST /crm/properties/{V}/{objectType}/groups`, body `{ "name": "deal_qualification", "label": "Deal qualification", "displayOrder": 3 }`. `name` and `label` are required. Also: `GET .../groups`, `GET .../groups/{groupName}`, `PATCH .../groups/{groupName}`, `DELETE .../groups/{groupName}`.

HubSpot ships default groups (for example `contactinformation`, `dealinformation`). A custom group makes API-created fields easy to spot.

## `type` and `fieldType` combinations

From the properties guide:

| `type` | Valid `fieldType` |
|---|---|
| `string` | `text`, `textarea`, `phonenumber`, `html`, `file`, `calculation_equation` |
| `number` | `number`, `calculation_equation` |
| `bool` | `booleancheckbox`, `calculation_equation` |
| `enumeration` | `select`, `radio`, `checkbox`, `booleancheckbox`, `calculation_equation` |
| `date` | `date` |
| `datetime` | `date` |
| `object_coordinates`, `json` | `text`; internal only, cannot be created or edited |

The OpenAPI enum for `type` also lists `phone_number`. The guide does not explain it (OQ-5). Use `string` with `phonenumber`.

Display hints (optional): `numberDisplayHint` = `formatted` (default), `unformatted`, `duration`, `percentage`, `probability`, `currency`; `showCurrencySymbol: true` renders a number as currency; `textDisplayHint` = `unformatted_single_line`, `multi_line`, `domain_name`, `email`, `ip_address`, `phone_number`, `physical_address`, `postal_code`; `dateDisplayHint` = `absolute`, `absolute_with_relative`, `time_since`, `time_until`. The guide's prose only demonstrates `percentage`, `showCurrencySymbol` and `domain_name`; the other values come from the OpenAPI enum.

## Enumeration options

- `options` is an array of `{label, value, displayOrder, hidden, description?}`. `label`, `value`, `displayOrder` and `hidden` are all required by the schema.
- `value` is the internal value used on records. Use a stable snake_case key.
- A multi-select (`checkbox`) value is stored as the selected values joined with semicolons, for example `a;b;c`. To append, start the string with a semicolon.
- To change options use `PATCH` with the full `options` list. Hidden options stay on old records; use `hidden: true` instead of deleting.

## Mapping our 14 canonical types

| Canonical | `type` | `fieldType` | Extra | Lossy? |
|---|---|---|---|---|
| `text` | `string` | `text` | | No. |
| `long_text` | `string` | `textarea` | | No. A string property holds up to 65,536 characters. |
| `select` | `enumeration` | `select` | `options[]` | No. `radio` is the alternative look. |
| `multi_select` | `enumeration` | `checkbox` | `options[]` | No. Values are semicolon-joined. |
| `number` | `number` | `number` | `numberDisplayHint: formatted` | Decimal places are not configurable here. |
| `currency` | `number` | `number` | `showCurrencySymbol: true` (and `numberDisplayHint: currency` is in the enum) | **Lossy.** The number carries no currency code. The symbol is a display choice. `currencyPropertyName` exists in the schema, purpose undocumented (OQ-5). |
| `percent` | `number` | `number` | `numberDisplayHint: percentage` | **Lossy / unclear.** The guide shows the hint, not whether 0.2 or 20 is stored (OQ-5). |
| `date` | `date` | `date` | | No. Send `YYYY-MM-DD` or midnight-UTC epoch ms. |
| `datetime` | `datetime` | `date` | | No. UTC; displayed in the viewer's time zone. |
| `checkbox` | `bool` | `booleancheckbox` | | No. Stored as `true` or `false`. |
| `url` | `string` | `text` | | **Lossy.** No URL type or URL validation. |
| `email` | `string` | `text` | `textDisplayHint: email` | **Lossy.** Free text, optionally hinted. The built-in contact `email` is special. |
| `phone` | `string` | `phonenumber` | | Display formatting only; no validation. |
| `user` | `enumeration` | `select` | `externalOptions: true`, `referencedObjectType: "OWNER"` | Works as an owner picker. Value is the owner `id` from the owners API, not an email. Inside a custom object schema use `externalOptionsReferenceType`. |

Property validation rules (min and max, regex and so on) are a separate API: `/crm/property-validations/{V}/...`. Not used by v1 blueprints.

## Naming rules

- Property `name` rules are **not stated** in the pages read (OQ-5). Examples show lowercase snake_case (`favorite_food`) and one mixed-case name (`VIN`). Proposed handling: generate lowercase snake_case starting with a letter, letters digits underscores only, and keep it unique per object.
- Custom object `name`: letters, numbers, underscores; first character a letter.
- Association label `name`: no hyphens, may not start with a digit.
- Property group `name`: rules not stated; use the same snake_case rule.

## What cannot change after creation

| Thing | Changeable? | Source |
|---|---|---|
| Property `name` | No. It is not in the update schema. | Update schema |
| `hasUniqueValue` | No: "Once set, this can't be changed." | Create schema |
| Property `type` / `fieldType` | The PATCH schema accepts them, but the allowed conversions are not documented. Treat as immutable; changing is a destructive manual step. | Update schema (OQ-5) |
| `label`, `description`, `groupName`, `displayOrder`, `hidden`, `options` | Yes | Update schema |
| Enumeration option `value` | Not documented; treat as fixed. Add a new option and hide the old one. | Inference (OQ-5) |
| Property group `name` | Not in the group PATCH (only label and order) | Group endpoints |
| Custom object `name` | No | Schemas guide |
| Calculation properties created by API | Cannot be edited in the HubSpot UI, only by API | Properties guide |

## Limits

- Up to 10 properties per object may have `hasUniqueValue: true`.
- Catalog: 1,000 custom properties per object on Smart CRM Starter, Professional and Enterprise; 10 in total on free tools. Calculated properties: 40 and 200 for Professional and Enterprise (column order in the catalog inferred). Check live usage with `GET /crm/limits/{V}/custom-properties`.
- Read-only values (score, calculation properties) cannot be used as conditional stage properties.

## Manual alternative

Settings > Data Management > Objects (or Properties) > pick object > Properties tab > Create property. Use it for anything the API refuses, such as a type conversion.
