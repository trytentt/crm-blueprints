# Attio: auth and setup

> Sources: https://docs.attio.com/rest-api/guides/authentication.md, https://api.attio.com/openapi/api (the published OpenAPI 3.1 spec, read in full), https://attio.com/help/apps/other-apps/generating-an-api-key, https://docs.attio.com/rest-api/endpoint-reference/meta/identify.md
> Last verified: 2026-10-04

## Credential types

| Type | Use it for | Notes |
|---|---|---|
| Workspace access token ("API key") | Agency work on one client workspace | Created by a workspace admin. Workspace level. No expiry (`exp` is always null). Scopes chosen at creation and editable later. |
| OAuth 2.0 access token | A public app used across many workspaces | Authorization code flow. Authorize at `https://app.attio.com/authorize`, token at `https://app.attio.com/oauth/token`. Needs a Developer Console app (build.attio.com). |
| User-level OAuth token | Acting as one member | Needs PKCE and admin approval. Most config endpoints accept `workspace` and `user` levels. Webhook endpoints are workspace level only. |

Recommendation for the toolkit: one workspace access token per client workspace, read from an environment variable (`ATTIO_ACCESS_TOKEN`). OAuth adds nothing for single-client build work.

## Making a request

- Base URL: `https://api.attio.com`. Paths start `/v2/`.
- Header: `Authorization: Bearer <token>`. HTTP Basic (token as username, blank password) also works.
- Bodies are JSON and wrapped in `{"data": {...}}`. Responses are `{"data": ...}`.

## Creating the token (client admin does this)

1. Click the menu beside the workspace name, then **Workspace settings**.
2. Open the **Developers** tab.
3. Click **+ New access token**.
4. Name it (for example `crm-blueprints read-only`).
5. Tick the scopes below.
6. Copy the token once and store it in `.env` as `ATTIO_ACCESS_TOKEN`.

Only workspace admins can create tokens. Tokens can be edited or deleted later.

## Scopes

Every scope comes as `<name>:read` or `<name>:read-write` (read-write includes read).

| Task | Scopes |
|---|---|
| Read-only pull (objects, attributes, options, statuses, lists, views) | `object_configuration:read`, `list_configuration:read` |
| Build (create objects, attributes, options, statuses, lists) | `object_configuration:read-write`, `list_configuration:read-write` |
| Seed or assert records | add `record_permission:read-write`; `list_entry:read-write` for list entries |
| Delete a custom object (not used by this toolkit) | `object_configuration:read-write` plus `record_permission:read-write` |
| Webhooks (optional) | `webhook:read-write` |

The build token needs no note, task, meeting, comment or file scopes.

## Check the token

`GET /v2/self` needs no scope. An active token returns `active: true`, `scope` (space separated), `token_level`, `workspace_id`, `workspace_name`, `workspace_slug`. An unknown or revoked token returns `200` with `{"active": false}`, so check the field, not the status code.

The adapter should call this first, print the workspace name and slug, and require the user to confirm it matches the client. That is the "naming the account" step for the production confirmation.

## Sandbox and test environments

There is no sandbox, no developer-account type and no API version header in the documentation. The only version marker is the `/v2` path prefix. Handling: use a separate, free workspace as the test target. See open-questions.md (Q1).

## Version pinning

Pin `/v2` in the base path. The spec reports `version: 2.0.0`. Nothing else to pin.

## Beta and alpha

Custom activities (`/v2/activities...`) are marked alpha in the spec and need a billing feature. The toolkit ignores them.
