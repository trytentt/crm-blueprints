> Sources: https://developers.hubspot.com/docs/apps/developer-platform/build-apps/authentication/overview.md ; https://developers.hubspot.com/docs/apps/developer-platform/build-apps/authentication/account-service-keys.md ; https://developers.hubspot.com/docs/apps/legacy-apps/private-apps/overview.md ; https://developers.hubspot.com/docs/developer-tooling/platform/versioning.md ; https://developers.hubspot.com/docs/api-reference/latest/overview.md ; https://developers.hubspot.com/docs/getting-started/account-types.md ; https://developers.hubspot.com/docs/developer-tooling/local-development/configurable-test-accounts.md ; https://knowledge.hubspot.com/account-management/set-up-a-hubspot-standard-sandbox-account ; https://developers.hubspot.com/docs/api-reference/latest/crm/objects/schemas/guide.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/properties/guide.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/pipelines/guide.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/pipelines/rules/guide.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/lists/guide.md
> Last verified: 2026-10-04

# HubSpot: authentication and setup

## Credential types for agency work on client accounts

HubSpot has three ways to call the API with a bearer token. All use `Authorization: Bearer <token>` against `https://api.hubapi.com`.

| Credential | Fits | Notes |
|---|---|---|
| Service key | One client account, our build tooling | Created in the client account. Scoped. Can be rotated. Same rate limits as a privately distributed app. Simplest option. |
| Private app, static auth token (new developer platform, `auth.type: static`, `distribution: private`) | One client account | Needs the HubSpot CLI and a project. Token shown in the app settings. |
| Legacy private app | One client account | Still works. Marked "legacy" in the docs. Super admin creates it. Max 20 per account. |
| OAuth app (`auth.type: oauth`, distribution `private` or `marketplace`) | Many accounts | Needs a hosted OAuth backend. A private-distribution OAuth app installs in at most 10 accounts. Overkill for a one-off build. |

Recommendation: a **service key** per client account, created by the client's super admin (or a user with the "Developer tools access" permission), for the CLI tools in this repo. Fall back to a legacy private app if service keys are not shown. Move to OAuth only if we ever need to act in many accounts without a client admin.

The same docs say service keys and private apps lose scopes if the account is downgraded, and a legacy private app breaks for some calls if its creating user is removed (`USER_DOES_NOT_HAVE_PERMISSIONS`).

## Scopes

Scopes are chosen when the key or app is created. Names below are taken from the 2026-09 reference pages.

**Read-only (for `crm_pull` and `crm_drift`)**

| Need | Scope |
|---|---|
| Read properties and property groups, contacts/companies/deals | `crm.schemas.contacts.read`, `crm.schemas.companies.read`, `crm.schemas.deals.read` |
| Read custom object schemas and their properties | `crm.schemas.custom.read` |
| Read pipelines and stages (deals and custom objects) | `crm.schemas.deals.read`, `crm.schemas.custom.read` |
| Read pipeline rules | `crm.pipelines.governance.read`, `crm.pipelines.stage_permissions.read` |
| Read association labels and limits | any one of the `crm.objects.*.read` scopes, for example `crm.objects.contacts.read`, `crm.objects.companies.read`, `crm.objects.deals.read`, `crm.objects.custom.read` (the reference lists these as alternatives) |
| Read lists (segments) | `crm.lists.read` |
| Read workflows (beta) | `automation` |

**Build (for `crm_apply`)**

| Need | Scope |
|---|---|
| Create or change properties and groups on contacts/companies/deals | `crm.schemas.contacts.write`, `crm.schemas.companies.write`, `crm.schemas.deals.write` |
| Create custom object schemas; create properties and pipelines on them | `crm.schemas.custom.write` |
| Create pipelines and stages | `crm.schemas.deals.write` (deals), `crm.schemas.custom.write` (custom objects) |
| Set pipeline rules (optional) | `crm.pipelines.governance.write`, `crm.pipelines.stage_permissions.write` |
| Create association labels and limits | `crm.objects.contacts.write`, `crm.objects.companies.write`, `crm.objects.deals.write`, `crm.objects.custom.write` to be safe. The reference lists read and write object scopes as alternatives, so read scopes may be enough (OQ-14). |
| Create lists (segments) | `crm.lists.write` |
| Create workflows (beta, optional) | `automation` |

The `.sensitive` and `.highly_sensitive` scope variants are only needed if the client uses Sensitive Data properties. See OQ-6 in `open-questions.md`.

## Step by step: service key

1. Sign in to the client account as a super admin (or a user with "Developer tools access").
2. Open **Development** in the main navigation, then **Keys > Service keys**.
3. Click **Create service key**, name it (for example `crm-blueprints build`).
4. Click **Add new scope** and tick the scopes from the tables above. Use the read-only set for a pull-only key.
5. Click **Create** and confirm. Open the key and use **Show** then **Copy**.
6. Store the token in `.env` as `HUBSPOT_ACCESS_TOKEN`. Never commit it.
7. Check it: `GET https://api.hubapi.com/crm/properties/2026-09/contacts` should return 200.

To rotate, use **Rotate** on the key details page. The old key then expires.

## Step by step: legacy private app (fallback)

1. Super admin: **Development > Legacy apps > Create legacy app > Private**.
2. Fill in Basic Info. Open the **Scopes** tab, **Add new scope**, tick scopes. Click **Create app**.
3. On the **Auth** tab, **Show token**, copy it. Same header as above.
4. To inspect a token's scopes: `POST /oauth/v2/private-apps/get/access-token-info` with the token in the body.

## API version pinning

HubSpot moved to date-based API versions on 30 March 2026. A new GA version appears every March and September.

- Current: `2026-09`. Supported: `2026-03`. A version is unsupported 18 months after its GA date.
- Beta versions carry `-beta` in the path (for example `/2027-03-beta/`). Do not use them by default.
- Legacy semantic versions (v1 to v4) still work at their old URLs.

Decision for the adapter: pin one dated version in one constant (`HUBSPOT_API_VERSION = "2026-09"`) and build every path from it. All paths in these notes use `{V}` for that value. Legacy equivalents (`/crm/v3/...`, `/crm-object-schemas/v3/...`, `/crm/associations/v4/...`) are listed in `api-coverage.md` as a fallback. The pipeline rules API exists only in the dated versions.

Behaviour change to know about: from `2026-09`, deleting or replacing a pipeline or stage is **blocked by default** when records or other tools reference it. See `pipelines.md`.

## Sandboxes and test accounts

| Environment | Who gets it | Use here |
|---|---|---|
| Developer test account | Any standard HubSpot account can create up to 10. Free, with a 90-day trial of many Enterprise features. Cannot sync with other accounts. Trials can be renewed. | Best place to test custom objects and the whole apply flow. Created at **Development > Testing > Test Accounts**. |
| Configurable test account | Platform version 2025.2 or later, CLI 8.3.0 or later. Simulates chosen subscription tiers. Can be created from a config file for CI. | Useful to prove behaviour per tier. |
| Standard sandbox | Needs an **Enterprise** subscription on the production account. Copies the structure of production. Supports "deploy to production" of supported assets (up to 300 changes per deploy). Legacy standard sandboxes ended 30 April 2026. | Good for a client that already has Enterprise: build in the sandbox, then deploy. Record IDs differ between sandbox and production. |
| Development sandbox | Enterprise, CLI only. | Not needed. |
| CMS sandbox | Free, CMS only. | Not relevant. |

Which parts of a CRM data model the "deploy to production" feature supports was not confirmed. See OQ-11.

Our rule: run `crm_apply` against a developer test account first. Never run it against a client production account without `--execute` and the production gate.
