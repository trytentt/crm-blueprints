# Attio: objects

> Sources: https://docs.attio.com/rest-api/endpoint-reference/objects/create-an-object.md, https://docs.attio.com/rest-api/endpoint-reference/objects/list-objects.md, https://docs.attio.com/rest-api/endpoint-reference/objects/update-an-object.md, https://docs.attio.com/rest-api/endpoint-reference/objects/delete-an-object.md, https://docs.attio.com/docs/objects-and-lists, https://docs.attio.com/rest-api/attribute-types/attribute-types-record-reference.md, https://api.attio.com/openapi/api, https://attio.com/pricing
> Last verified: 2026-10-04

## Standard objects

- Always present: `people`, `companies`.
- Optional, enabled in the UI by an admin: `deals`, `users`, `workspaces`. They are off by default. No API call to enable them was found, so enabling Deals is a manual step (Workspace settings, Objects). See open-questions.md (Q3).
- Custom objects: created through the API or the UI.

## List objects (state reading)

`GET /v2/objects`. Scope `object_configuration:read`. No pagination parameters.

```json
{"data": [{
  "id": {"workspace_id": "14beef7a-...", "object_id": "97052eb9-..."},
  "api_slug": "people", "singular_noun": "Person", "plural_noun": "People",
  "created_at": "2022-11-21T13:22:49.061281000Z"}]}
```

`GET /v2/objects/{object}` returns one object, same shape. `{object}` is the slug or the UUID.

## Create a custom object

`POST /v2/objects`. Scope `object_configuration:read-write`.

```json
{"data": {"api_slug": "engagements", "singular_noun": "Engagement", "plural_noun": "Engagements"}}
```

All three fields are required. `api_slug` is snake_case and unique. Response is `200` with `{"data": <object>}` as above.

Errors:

| Status | `type` | `code` | Meaning |
|---|---|---|---|
| 400 | `invalid_request_error` | `quota_exceeded` | Plan object limit reached |
| 403 | `auth_error` | `unauthorized` | Token lacks the scope |
| 409 | `invalid_request_error` | `slug_conflict` | Slug or names already used |

For idempotency read `GET /v2/objects` first, match on `api_slug`, and treat a 409 `slug_conflict` as "already exists".

## Update an object

`PATCH /v2/objects/{object}` with any of `api_slug`, `singular_noun`, `plural_noun`. Empty payload is 400 `validation_type`. Slug clash is 409 `slug_conflict`. Renaming `api_slug` changes every URL that uses it, so treat it as `needs_review`.

## Delete an object

`DELETE /v2/objects/{object}` exists. It only works on custom objects and removes all their records. Needs `object_configuration:read-write` and `record_permission:read-write`. The toolkit must never call it (safety rule 3). It is a destructive manual step.

## Limits and plan needs

- Creating beyond the plan limit returns 400 `quota_exceeded`.
- The pricing page says "Up to 3" objects on Free, "Up to 5" on Plus, "Up to 12" on Pro, "Unlimited objects" on Enterprise. All plans list custom objects as included.
- It does not say whether the standard objects count towards that number. See open-questions.md (Q2).
- API and webhook access is listed on every plan.

Practical rule for the generator: count design objects that are not People or Company, compare with the live object count, and warn before creating. Treat `quota_exceeded` as a stop-and-explain, not a retry.

## Views

`GET /v2/objects/{object}/views` lists saved views (id and title only). There is no create or update. See views-and-lists.md.
