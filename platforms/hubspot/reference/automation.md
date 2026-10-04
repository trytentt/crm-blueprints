> Sources: https://developers.hubspot.com/docs/api-reference/legacy/automation/workflows/guide.md ; https://developers.hubspot.com/docs/api-reference/2027-03-beta/automation/workflows/guide.md ; https://developers.hubspot.com/docs/_llms/apis/2027-03-beta.md ; https://developers.hubspot.com/docs/_llms/apis/2026-09.md ; https://developers.hubspot.com/docs/api-reference/latest/automation/sequences/guide.md ; https://knowledge.hubspot.com/workflows/create-workflows ; https://developers.hubspot.com/docs/api-reference/latest/crm/pipelines/rules/guide.md
> Last verified: 2026-10-04

# HubSpot: automation

## Summary

| Capability | API status | Verdict for this repo |
|---|---|---|
| Create, read, update, delete workflows | **Beta.** Documented as the "v4 workflows API" at `/automation/v4/flows` and, in the next version track, `/automation/v4/2027-03-beta/flows`. Both pages carry a beta disclaimer. | Off by default. Optional flag `--enable-beta-workflows`. |
| Sequences (create, enroll) | In the 2026-09 reference | Out of scope for structure. |
| Custom workflow actions (definitions for an app) | Stable, `automation` scope | Not a way to build our automations. |
| Email templates | In the 2026-09 reference | Out of scope. |
| Pipeline rules (movement, approvals, stage permissions) | Dated API from 2026-09 | Optional; not workflows. |

The 2026-09 reference has **no** stable workflows endpoint. The only workflow create/update endpoints are beta.

## Workflows API (beta)

- Scope: `automation`. Sensitive-data workflows also need the matching `crm.objects.*.sensitive.write` scope.
- Create: `POST /automation/v4/flows` (beta, legacy track) or `POST /automation/v4/2027-03-beta/flows`. Body is a full workflow specification: `type` (`CONTACT_FLOW` for contact workflows, `PLATFORM_FLOW` for others), enrollment criteria, and an `actions` list. The action and enrollment type reference is a separate beta page.
- Read: `GET /automation/v4/flows` (key fields only) and `GET /automation/v4/flows/{flowId}` (full). Batch read: `POST /automation/v4/flows/batch/read`.
- Update: `PUT` with the current `revisionId` and `type`. Anything missing from the body is removed from the workflow.
- Delete: supported.
- Tier: building workflows in HubSpot needs Professional or Enterprise on Marketing, Sales, Service, Data, Smart CRM or Revenue Hub (knowledge base). Some object types (quotes, contracts) need specific subscriptions. Number of workflows depends on the subscription.
- Caveats: the legacy-track page shows the update path inconsistently (`/automation/v4/flows/{flowId}` versus `/automation/v4/{flowId}`), a sign the page is not settled.

Decision: **do not create workflows by API in v1.** The generator writes a description of each design automation into the build sheet, and the apply step emits a manual step. If a client asks for it later, add a beta adapter behind a flag, with a read-back check.

## Manual alternative (each design automation)

Automations > Workflows > Create workflow > pick object and trigger type > set enrollment trigger (use the design's `trigger`) > add actions (use the design's `action`) > review re-enrollment > Turn on. Needs Professional or Enterprise, the Edit workflows permission, and the Publish permission to turn it on. Note that enrolling a record in workflows in a developer test account or sandbox is capped at 100,000 records a day.

Typical design automations and the native tool:

| Intent | Native HubSpot tool |
|---|---|
| Set a property when a deal moves stage | Workflow with a deal-stage trigger |
| Create a task for the owner | Workflow action "Create task" |
| Block stage movement | Pipeline rule (API, optional) |
| Require approval | Deal approval rule (Sales Hub Enterprise) |
| Force a field to be filled at a stage | Conditional stage property (manual, see `pipelines.md`) |
