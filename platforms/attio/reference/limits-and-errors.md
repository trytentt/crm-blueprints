# Attio: limits and errors

> Sources: https://docs.attio.com/rest-api/guides/rate-limiting.md, https://docs.attio.com/rest-api/guides/pagination.md, https://api.attio.com/openapi/api (error schemas on every endpoint used), https://attio.com/pricing
> Last verified: 2026-10-04

## Rate limits

- Reads: 100 requests per second.
- Writes: 25 requests per second.
- List-style endpoints (records, entries) also have a score-based limit over a 10-second sliding window. Heavy queries can trigger 429 even under the request limits.
- A 429 request is not processed, so retrying is safe. The `Retry-After` header holds the reset time (the docs say "datetime"; parse both a number of seconds and an HTTP date). Resets usually come within the next clock second.

429 body:

```json
{"status_code": 429, "type": "rate_limit_error", "code": "rate_limit_exceeded",
 "message": "Rate limit exceeded, please try again later"}
```

Retry plan: on 429 wait for `Retry-After` (minimum 1 s), then retry up to 5 times with exponential backoff and jitter (1, 2, 4, 8, 16 s). Build calls are few and sequential, so 25 writes a second is never reached; pace at no more than 10 writes a second anyway. Do not retry 4xx other than 429. Retry 5xx up to 3 times with backoff; for POST create calls re-read state first, because a timed-out create may have succeeded.

## Error body

Every error uses one shape:

```json
{"status_code": 409, "type": "invalid_request_error", "code": "slug_conflict",
 "message": "An attribute with the same API slug already exists on this list. Please choose a different API slug."}
```

`type` values seen: `invalid_request_error`, `auth_error`, `rate_limit_error`. Never log the Authorization header.

## Codes the toolkit meets

| Status | `code` | Where | Meaning and handling |
|---|---|---|---|
| 400 | `quota_exceeded` | create object | Plan object limit. Stop; tell the user to upgrade or remove an object. |
| 400 | `validation_type` | create attribute, option, status; update object | Bad body, or "This attribute is not a select attribute". Stop and show the message. |
| 400 | `value_not_found` | records, entries, option and status patch, create list | Named value, status, option or object missing. |
| 400 | `system_edit_unauthorized` | update attribute | Tried to edit a system attribute. Skip it. |
| 400 | `particle_gate_violation` | records | Seen on record writes; not documented. Report. |
| 403 | `unauthorized` | any write | Token lacks scope. Say which scope. |
| 403 | `billing_error` | create or update list | Plan does not support the access mode. Use `full-access`. |
| 404 | `not_found` | any with a slug path | Object, list, attribute or option missing. |
| 409 | `slug_conflict` | create object, list, attribute, option, status | Already exists. See below. |
| 409 | `concurrent_write_conflict` | records | Retry the write once. |
| 429 | `rate_limit_exceeded` | any | Back off as above. |

## "Already exists" for idempotency

The signal is **HTTP 409 with `type: "invalid_request_error"` and `code: "slug_conflict"`**. The same code is used for objects, lists, attributes, select options and statuses. For options and statuses the clash is on the title ("There is already another select option with the title ...").

Do not rely on the 409 alone. Idempotent pattern:

1. Read first: list objects, lists, attributes (with `show_archived=true`), options, statuses.
2. Match by `api_slug` (objects, lists, attributes) or by title (options, statuses).
3. If found and identical: no change. If found but different: plan a change or a manual step. If found but archived: report it; restoring is `needs_review`.
4. If not found, create. If the create still returns `slug_conflict` (another session raced), re-read and treat as present.

Archived attributes, options and statuses probably still hold their slug or title, so a create against an archived name would return 409. This is inferred, not documented (open-questions.md, Q9). The planner must read with `show_archived=true` to avoid mistaking archived items for missing ones.

## Pagination

`limit` and `offset` on attribute lists, and cursor (`pagination.next_cursor`) on query endpoints. The defaults are documented per endpoint and were not stated on the pages read. Objects and lists endpoints take no paging parameters. For attributes always page until fewer than `limit` results come back; an object can have many attributes.

## Limits on structure

- Objects per plan: 3, 5, 12, unlimited (pricing page). See open-questions.md (Q2).
- Records per plan: 50,000, 250,000, 1,000,000 or custom.
- Attribute count, option count and slug length limits: not documented.
