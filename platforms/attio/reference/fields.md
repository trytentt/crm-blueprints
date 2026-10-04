# Attio: fields (attributes)

> Sources: https://api.attio.com/openapi/api (create, update, list attribute and option/status endpoints, attribute schema), https://docs.attio.com/rest-api/endpoint-reference/attributes/create-an-attribute.md, https://docs.attio.com/rest-api/endpoint-reference/attributes/update-an-attribute.md, https://docs.attio.com/rest-api/attribute-types/attribute-types.md and the per-type pages (text, number, currency, rating, date, timestamp, checkbox, domain, email-address, phone-number, actor-reference, select, status, record-reference)
> Last verified: 2026-10-04

Attio calls fields "attributes". They live on an object or on a list.

## Create an attribute

`POST /v2/{target}/{identifier}/attributes`

- `target` is `objects` or `lists`. `identifier` is the object or list slug (or UUID).
- Scope: `object_configuration:read-write` for objects, `list_configuration:read-write` for lists.

Request body (all of `title`, `description`, `api_slug`, `type`, `is_required`, `is_unique`, `is_multiselect`, `config` are required; send them all):

```json
{"data": {
  "title": "Contract value",
  "description": "Total contract value agreed at signature",
  "api_slug": "contract_value",
  "type": "currency",
  "is_required": false,
  "is_unique": false,
  "is_multiselect": false,
  "config": {"currency": {"default_currency_code": "GBP", "display_type": "symbol"}}
}}
```

Optional: `default_value` and `relationship`. Response `200`: `{"data": <attribute>}`.

For types with no config send `"config": {}`.

## Type strings accepted on create

Exactly these 15, with hyphens (not underscores):

`text`, `number`, `checkbox`, `currency`, `date`, `timestamp`, `rating`, `status`, `select`, `record-reference`, `actor-reference`, `location`, `domain`, `email-address`, `phone-number`

`personal-name` and `interaction` appear when reading (they are system attributes) but cannot be created through the API. A formula attribute is also not creatable; the spec only says formula attributes read as `is_writable: false`.

The prose page "attribute types" shows underscores (`record_reference`). Use the OpenAPI spelling above; it is what the create endpoint validates.

## Config shapes

| Type | Create `config` | Notes |
|---|---|---|
| `currency` | `{"currency": {"default_currency_code": "GBP", "display_type": "symbol"}}` | Both keys required. `display_type`: `code`, `name`, `narrowSymbol`, `symbol`. One currency per attribute; cannot override per record. Up to 4 decimal places. The code list has 46 currencies (includes GBP, EUR, USD). |
| `record-reference` | `{"record_reference": {"allowed_objects": ["companies"]}}` | Request uses `allowed_objects` (slugs or UUIDs). The attribute read returns `allowed_object_ids` (UUIDs). With a `relationship`, the list must contain only that object. |
| everything else | `{}` | No other config. |

On read, `config` always has both `currency` and `record_reference` keys; the unused one holds nulls.

## Per-type behaviour

| Type | Write value | Multi? | Notes |
|---|---|---|---|
| `text` | `"abc"` or `[{"value":"abc"}]` | No | One text type. Max 10 MB. No short and long split in the API. |
| `number` | `12.5` or `{"value":12.5}` | No | Up to 4 decimals. |
| `checkbox` | `true`, `"true"`, `[{"value":true}]` | No | Never null. |
| `currency` | `4200` or `{"currency_value":4200}` | Not stated | Currency comes from the attribute. |
| `date` | `"2026-10-04"` | No | Calendar date, no timezone. Partial dates are padded. |
| `timestamp` | `"2026-10-04T09:30:00Z"` | No | Returned in UTC, nanosecond precision. |
| `rating` | integer 0 to 5 | No | Stars. |
| `select` | option title or id | Yes (`is_multiselect`) | Cannot create options on write. |
| `status` | `[{"status":"Lead"}]` | No | Cannot create statuses on write. |
| `record-reference` | `{"target_object":"companies","target_record_id":"<uuid>"}` | Yes | Can also match by a unique attribute, for example `domains`. |
| `actor-reference` | `"person@co.com"` or `{"referenced_actor_type":"workspace-member","referenced_actor_id":"<uuid>"}` | Yes | Only workspace members can be written. |
| `domain` | `"acme.com"` | Yes | Stores domains only; paths and queries are trimmed. Not for URLs. |
| `email-address` | `"a@b.com"` | Yes | Strictly validated. |
| `phone-number` | `"+447700900123"` | Yes | E.164 with `+` prefix, or `{original_phone_number, country_code}`. |
| `location` | object | Yes | Not used in our mapping. |

Whether `is_multiselect: true` is accepted on every type is not documented per type. Only send it as `true` for `select`, `record-reference`, `actor-reference`, `domain`, `email-address`, `phone-number`. Always send `false` otherwise.

## Mapping our 14 canonical types

| Canonical | Attio `type` | `is_multiselect` | Config | Lossy? |
|---|---|---|---|---|
| `text` | `text` | false | `{}` | No |
| `long_text` | `text` | false | `{}` | Yes. Same type as `text`; the 10 MB limit applies to both. The long-text intent is only kept in the description. |
| `select` | `select` | false | `{}` | No. Options added after creation. |
| `multi_select` | `select` | true | `{}` | No |
| `number` | `number` | false | `{}` | No. 4 decimals max. |
| `currency` | `currency` | false | currency block (default GBP, `symbol`) | Minor. One currency per attribute. |
| `percent` | `number` | false | `{}` | Yes. No percent type or format. Store 0 to 100 (or 0 to 1) as a number and say which in the description. |
| `date` | `date` | false | `{}` | No |
| `datetime` | `timestamp` | false | `{}` | Minor. Always UTC. |
| `checkbox` | `checkbox` | false | `{}` | No. Cannot be empty. |
| `url` | `text` | false | `{}` | Yes. `domain` drops paths, so a full URL must be plain text. No URL validation. |
| `email` | `email-address` | false | `{}` | No. Use `is_multiselect: false` unless the design says many. |
| `phone` | `phone-number` | false | `{}` | Minor. Values must be E.164 or carry a country code. |
| `user` | `actor-reference` | false | `{}` | Minor. Only workspace members. |

A `rating` type exists but has no canonical type. Do not map to it unless a design adds one.

## Naming rules

- `api_slug`: snake_case, unique per object or list. Required on create.
- `title`: free text, shown in the UI.
- Not documented: maximum lengths and the exact reserved slug list. System slugs on standard objects (for example `name`, `domains`, `email_addresses`, `stage`) will collide. A clash returns 409 `slug_conflict`.

## What can change after creation

`PATCH /v2/{target}/{identifier}/attributes/{attribute}` accepts only: `title`, `description`, `api_slug`, `is_required`, `is_unique`, `default_value`, `config`, `is_archived`.

| Property | After creation |
|---|---|
| `type` | Cannot change. Needs a new attribute and a data migration (manual step). |
| `is_multiselect` | Cannot change. Same handling. |
| The object or list it belongs to | Cannot change. |
| `relationship` (the reverse side) | Not in the update body. Treat as fixed. |
| `title`, `description` | Safe to change. |
| `api_slug` | Changeable, but breaks anything that uses the old slug. `needs_review`. |
| `is_required`, `is_unique` | Changeable. They apply to new data only. Existing rows are not backfilled or checked. |
| `config` (currency code or display, allowed objects) | Changeable per the update schema. Changing the currency does not convert values. `needs_review`. |
| `is_archived` | Archive or restore. There is no delete for attributes. |
| System attributes | Cannot be updated (400 `system_edit_unauthorized`). |

`is_required: true` needs a default value: the read schema says `is_default_value_enabled` "must be true when `is_required` is `true`". Not tested. See open-questions.md (Q5).

## Reading attributes (state)

`GET /v2/{target}/{identifier}/attributes?limit=&offset=&show_archived=true`. Scope `*_configuration:read`.

```json
{"data": [{
  "id": {"workspace_id": "...", "object_id": "...", "attribute_id": "..."},
  "title": "Company", "description": "...", "api_slug": "company",
  "type": "record-reference",
  "is_system_attribute": false, "is_writable": true,
  "is_required": false, "is_unique": false, "is_multiselect": false,
  "is_default_value_enabled": false, "is_archived": false,
  "default_value": null, "created_at": "2021-11-21T13:22:49.061Z",
  "config": {"currency": {"default_currency_code": null, "display_type": null},
             "record_reference": {"allowed_object_ids": ["<uuid>"]}},
  "relationship": {"id": {"...": "..."}, "object_slug": "companies", "title": "Team members",
                   "api_slug": "team_members", "is_multiselect": true}
}]}
```

Pass `show_archived=true` or archived attributes will look missing. `GET .../attributes/{attribute}` returns one in `{"data": ...}`.

## Select options

Add: `POST /v2/{target}/{identifier}/attributes/{attribute}/options`

```json
{"data": {"title": "Referral"}}
```

Only `title` (min length 1). No colour, no order, no description. Response `{"data": {"id": {"workspace_id","object_id","attribute_id","option_id"}, "title": "Referral", "is_archived": false}}`.

Read: `GET .../options?show_archived=true` returns `{"data": [<option>...]}`.

Rename or archive: `PATCH .../options/{option}` with `title` and/or `is_archived`. `{option}` is the option id or title. Options cannot be deleted. Errors: 409 `slug_conflict` (title already used), 400 `validation_type` ("This attribute is not a select attribute"), 400 `value_not_found`.

## Status options

Add: `POST /v2/{target}/{identifier}/attributes/{attribute}/statuses`

```json
{"data": {"title": "Proposal sent", "celebration_enabled": false, "target_time_in_status": "P14D"}}
```

`title` required. `celebration_enabled` (default false) and `target_time_in_status` (ISO 8601 duration or null) are optional. Response `{"data": {"id": {..., "status_id"}, "title", "is_archived", "celebration_enabled", "target_time_in_status"}}`.

Read: `GET .../statuses?show_archived=true`. Update: `PATCH .../statuses/{status}` with `title`, `celebration_enabled`, `target_time_in_status`, `is_archived`. Statuses cannot be deleted.

There is no field for order, for won/lost, or for probability. See pipelines.md.

## Creating the first options

`POST .../attributes` cannot take options. Create the attribute, then post each option or status. A freshly created status attribute may arrive with default statuses; the docs do not say. See open-questions.md (Q6).
