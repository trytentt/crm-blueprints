# Attio platform notes

> Sources: https://docs.attio.com/docs/overview, https://docs.attio.com/llms.txt, https://api.attio.com/openapi/api, plus the pages listed in each file under reference/
> Last verified: 2026-10-04

Short guide for anyone building or amending an Attio workspace with this toolkit. Detail is in `reference/`.

## What the API can do

- Create custom objects, attributes (15 types), select options, status options, lists and list attributes.
- Create a relationship in one call, with its reverse side, by adding a `relationship` object to a `record-reference` attribute.
- Read all of that back, including archived items, for drift checks.
- Upsert records with `PUT /v2/objects/{object}/records?matching_attribute=<unique_slug>`.

## What it cannot do (manual steps)

- Create or edit workflows. All automations are manual (UI: Workflows, Create workflow).
- Create, edit or filter views. Read-only.
- Enable Deals, Users or Workspaces objects.
- Delete attributes, options or statuses (archive only). Reorder options or stages.
- Change an attribute's type or `is_multiselect`, or edit a relationship after creation.
- Mark a stage as won or lost, give a stage a probability, or require fields per stage.
- Set object or field level permissions.

## Pipelines

One list per pipeline, with a `stage` status attribute on the list. Won and lost are plain statuses; lost reason is a select attribute. Probability is a number attribute by convention. Stage gates are manual. See `reference/pipelines.md`.

## Gotchas

1. Type strings are hyphenated on create: `record-reference`, `email-address`, `phone-number`, `actor-reference`.
2. Request config uses `allowed_objects`; reads return `allowed_object_ids`.
3. Every create attribute call needs all of `title`, `description`, `api_slug`, `type`, `is_required`, `is_unique`, `is_multiselect`, `config`.
4. Options and statuses cannot be created by writing a record. Create them first or the write fails.
5. Archived items are hidden unless you pass `show_archived=true`.
6. `url` and `long_text` both map to `text`. `percent` maps to `number`. `domain` drops URL paths.
7. Tokens have no sandbox. Use a separate workspace for testing and check `GET /v2/self` before every run.
8. Rate limits: 100 reads and 25 writes a second. Retry 429 using `Retry-After`.
9. "Already exists" is 409 `slug_conflict`. Read state first rather than relying on it.
10. Plan limits on objects (3, 5, 12, unlimited) are unclear about standard objects. Check the plan before building.
11. A newly created status attribute may arrive with default statuses; check before adding stages.

## Credentials

Workspace access token created by a client admin: Workspace settings, Developers, New access token. Build scopes: `object_configuration:read-write`, `list_configuration:read-write` (add `record_permission:read-write` for seeding). Read-only scopes: `object_configuration:read`, `list_configuration:read`. Environment variable: `ATTIO_ACCESS_TOKEN`.
