# Attio: relationships

> Sources: https://api.attio.com/openapi/api (create attribute, `relationship` object), https://docs.attio.com/rest-api/endpoint-reference/attributes/create-an-attribute.md, https://docs.attio.com/rest-api/attribute-types/attribute-types-record-reference.md, https://docs.attio.com/docs/objects-and-lists
> Last verified: 2026-10-04

## How a link is made

A relationship is a `record-reference` attribute. There is no separate relationship endpoint. One call creates both sides:

`POST /v2/objects/{object}/attributes` (scope `object_configuration:read-write`)

```json
{"data": {
  "title": "Company",
  "description": "The client company this engagement is for",
  "api_slug": "company",
  "type": "record-reference",
  "is_required": false,
  "is_unique": false,
  "is_multiselect": false,
  "config": {"record_reference": {"allowed_objects": ["companies"]}},
  "relationship": {
    "object": "companies",
    "title": "Engagements",
    "api_slug": "engagements",
    "is_multiselect": true
  }
}}
```

`{object}` here is the "from" side (`engagements`). `relationship.object` is the "to" side (`companies`). The response is the attribute on the "from" side. The reverse attribute on the "to" side is created automatically with `relationship.title` and `relationship.api_slug`. Both sides then stay in sync.

Rules from the spec:

- `relationship` works only with type `record-reference`.
- `relationship` needs all four keys: `object`, `title`, `api_slug`, `is_multiselect`.
- If `config.record_reference.allowed_objects` is also sent, it must contain only the relationship object.
- Without `relationship`, you get a one-way reference with no reverse attribute. Do not use that for our designs.

## Cardinality

Each side's `is_multiselect` says whether one record on that side can hold many references. The parent attribute lives on the "from" object; `relationship.is_multiselect` is for the reverse attribute on the "to" object.

| Our cardinality | Parent attribute `is_multiselect` (a from-record holds many to-records?) | `relationship.is_multiselect` (a to-record holds many from-records?) |
|---|---|---|
| `one_to_one` | false | false |
| `one_to_many` (one from-record, many to-records) | true | false |
| `many_to_one` (many from-records, one to-record) | false | true |
| `many_to_many` | true | true |

Example: engagements (from) to companies (to) is `many_to_one`. `engagements.company` is single; the reverse `companies.engagements` is multi.

The spec describes the same four combinations as "both false = one-to-one, parent true + related false = many-to-one, parent false + related true = one-to-many, both true = many-to-many". Its "one" and "many" labels read the opposite way round from the table above for the two mixed rows. The table above is built from what each flag does to the attribute it sits on, which is unambiguous. Confirm with one live test before the first build (open-questions.md, Q7).

## Labels and roles

Each side has a `title` (shown in the UI) and an `api_slug`. There is no separate "role" or association label as in HubSpot. If the design needs roles (landlord and tenant), create two attributes, one per role, each with its own reverse attribute.

## Many-to-many

Two ways:

1. Both flags true. Simple. No data on the link itself.
2. A junction custom object with two many-to-one references, when the link needs its own fields (dates, role, share). Attio also offers lists, where a list entry holds its own attributes on a parent record. That fits "a record appears once in a process"; it does not fit true many-to-many.

Recommendation for the generator: use method 1 unless the design gives the link its own fields; then create the junction as a custom object.

## Writing and reading values

Write by id: `{"target_object": "companies", "target_record_id": "<uuid>"}`. Standard objects also take a shorthand: companies by domain, people by email. The target must exist or the write fails.

Read returns `target_object` and `target_record_id`.

## Standard relationships already present

Company: `team`, `associated_deals`, `associated_workspaces`. Person: `company`, `associated_deals`, `associated_users`. Deal: `associated_people`, `associated_company`. User: `person`, `workspace`. Workspace: `users`, `company`. Do not recreate these. Mark such design fields as `native`.

## After creation

`relationship` cannot be edited through `PATCH`. Only `title`, `description`, `api_slug`, `is_required`, `is_unique`, `default_value`, `config` and `is_archived` can change. Changing cardinality needs a new attribute and a manual data move.

## Reading relationships (state)

List the attributes of the object. Those with `type: "record-reference"` carry `relationship` (reverse side: `object_slug`, `title`, `api_slug`, `is_multiselect`) and `config.record_reference.allowed_object_ids`. Match the pair by the reverse slug. Archived ones need `show_archived=true`.
