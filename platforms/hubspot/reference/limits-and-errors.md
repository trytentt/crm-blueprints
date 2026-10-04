> Sources: https://developers.hubspot.com/docs/developer-tooling/platform/usage-guidelines.md ; https://developers.hubspot.com/docs/api-reference/latest/error-handling.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/properties/create-property.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/pipelines/guide.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/limits-tracking/guide.md ; https://developers.hubspot.com/docs/apps/developer-platform/build-apps/authentication/account-service-keys.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/objects/schemas/guide.md
> Last verified: 2026-10-04

# HubSpot: limits, errors and idempotency

## Rate limits

Applies to service keys, legacy private apps, and private-distribution apps on platform 2025.2 and 2026.03 (service keys use the same limits). The burst limit is per app. The daily limit is shared by every app in the account.

| Account tier (any Hub) | Per 10 seconds | Per day |
|---|---|---|
| Free and Starter | 100 per app | 250,000 per account |
| Professional | 190 per app | 625,000 per account |
| Enterprise | 190 per app | 1,000,000 per account |
| With the API Limit Increase add-on (max two) | 250 per app | +1,000,000 per account for each add-on |

Public OAuth apps installed from the marketplace: 110 requests per 10 seconds per installing account, excluding the CRM Search API. Not our case.

The CRM Search API and a few other endpoints have their own limits. Structure building does not use search.

Response headers (not sent on OAuth-authorised calls for the daily pair): `X-HubSpot-RateLimit-Max`, `X-HubSpot-RateLimit-Remaining`, `X-HubSpot-RateLimit-Interval-Milliseconds`, `X-HubSpot-RateLimit-Daily`, `X-HubSpot-RateLimit-Daily-Remaining`.

A structure build is small (tens of calls), so limits matter mostly for `crm_pull` on large models. Set the client to at most 8 calls a second and honour headers.

## Retry and backoff

| Status | Meaning | What to do |
|---|---|---|
| `429` | Over the 10-second or daily limit. Body has `errorType: RATE_LIMIT` and `policyName` (`DAILY` or `TEN_SECONDLY_ROLLING`). | For `TEN_SECONDLY_ROLLING`: wait, honour `Retry-After` if present, else back off from 1 s doubling to 10 s, up to 5 tries. For `DAILY`: stop and report. Error responses should stay under 5 percent of daily calls. |
| `423 Locked` | Heavy sync in a short time | Wait at least 2 seconds, retry. |
| `502`, `503`, `504`, `521`, `523`, `524` | Temporary | Pause a few seconds and retry, up to 5 tries. |
| `477` | Account is being moved between data centres | Wait for `Retry-After` (can be long); fail the run if over a minute. |
| `401` | Bad or expired token | Do not retry. |
| `403` | Missing scope, or tier does not allow it | Do not retry. Read `context.missingScopes` if present and report it. |
| `4xx` otherwise | Request problem | Do not retry. |

Never retry a `POST` after a timeout without first reading back, because the first call may have succeeded.

## Error body

Most endpoints return JSON like this (every field should be treated as optional):

```json
{
  "status": "error",
  "message": "Human readable text.",
  "errors": [
    { "message": "discount was not a valid number", "code": "INVALID_INTEGER", "context": { "propertyName": ["discount"] } }
  ],
  "category": "VALIDATION_ERROR",
  "subCategory": "PipelineError.STAGE_ID_IN_USE",
  "context": { "missingScopes": ["crm.schemas.custom.write"] },
  "correlationId": "a43683b0-5717-4ceb-80b4-104d02915d8c",
  "links": { "knowledge-base": "https://..." }
}
```

The OpenAPI `Error` object lists `category`, `correlationId` and `message` as required, with `context`, `errors[]`, `links` and `subCategory` optional. Rate-limit errors use a different shape: `status`, `message`, `errorType`, `correlationId`, `policyName`, `requestId`. Always log `correlationId`. Never log the token.

Batch create endpoints for objects can return `207 Multi-Status` when each input carries a unique `objectWriteTraceId`.

## "Already exists" and idempotency

**What the docs say:** nothing. None of the create pages I read (properties, property groups, schemas, pipelines, stages, association labels, lists) names a status code or category for "this already exists". The only documented validation subcategory is `PipelineError.STAGE_ID_IN_USE` (delete blocked). See OQ-10.

**What the adapter should do instead (read before write):**

| Resource | Existence check | Key |
|---|---|---|
| Property group | `GET /crm/properties/{V}/{obj}/groups/{name}` | internal `name` |
| Property | `GET /crm/properties/{V}/{obj}/{name}` (404 means absent) | internal `name` |
| Custom object | `GET /crm-object-schemas/{V}/schemas/{fullyQualifiedName}` (`p{HubId}_{name}`) | `name` |
| Pipeline | `GET /crm/pipelines/{V}/{obj}/{pipelineId}` when we set `pipelineId` ourselves; otherwise list and match `label` | `pipelineId`, else label |
| Stage | read the pipeline and match `stageId` (we set it) or `label` | `stageId` |
| Association label | `GET .../labels` both ways; the read returns `typeId`, `category`, `label` but not the internal `name`, so match on `label` | label text |
| Association limit | `GET .../definitions/configurations/{from}/{to}` | `typeId` |
| List | `GET /crm/lists/{V}/object-type-id/{type}/name/{name}` | name |

**Fallback if a create still collides:** treat `409`, or any `4xx` whose message contains "already exists" or "already been", as "exists", then re-read and compare. If the live object matches the design, record `skipped (exists)`; if it differs, record a `needs_review` change. This is a proposed handling, not a documented one. Confirm the real status and category in a developer test account and record them here (OQ-10).

Always set our own `stageId` and `pipelineId` (snake_case) so reruns are deterministic. HubSpot otherwise generates numeric IDs.

## Other limits worth knowing

- Object batch endpoints: 100 inputs per request. Associations batch read: 1,000 IDs.
- Custom objects, properties, pipelines, labels: see `objects.md`, `fields.md`, `pipelines.md`, `relationships.md`. `GET /crm/limits/{V}/...` reports live usage and should be read before a plan that creates many things.
- Legacy private apps: 20 per account. Developer test accounts: 10 per standard account.
- Workflows in a test account or sandbox: 100,000 enrolments a day.
