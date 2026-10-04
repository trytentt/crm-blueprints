> Sources: https://developers.hubspot.com/docs/api-reference/latest/crm/pipelines/guide.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/pipelines/create-pipeline.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/pipelines/stages/create-pipeline-stage.md ; https://developers.hubspot.com/docs/api-reference/legacy/crm/pipelines/guide.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/pipelines/rules/guide.md ; https://knowledge.hubspot.com/object-settings/set-up-and-customize-pipelines ; https://developers.hubspot.com/docs/api-reference/latest/crm/limits-tracking/guide.md
> Last verified: 2026-10-04

# HubSpot: pipelines and stages

Pipelines exist for deals, tickets, leads, custom objects and several other objects. All use the same endpoints. `{V}` is the pinned API version (`2026-09`). `{objectType}` is `deals`, `tickets`, or an object type ID such as `0-3` or `2-3465404`.

## Endpoints

| Action | Request |
|---|---|
| Create pipeline | `POST /crm/pipelines/{V}/{objectType}` |
| List pipelines | `GET /crm/pipelines/{V}/{objectType}` |
| Read one | `GET /crm/pipelines/{V}/{objectType}/{pipelineId}` |
| Replace | `PUT /crm/pipelines/{V}/{objectType}/{pipelineId}` |
| Update (partial) | `PATCH /crm/pipelines/{V}/{objectType}/{pipelineId}` |
| Delete | `DELETE /crm/pipelines/{V}/{objectType}/{pipelineId}` |
| Create stage | `POST /crm/pipelines/{V}/{objectType}/{pipelineId}/stages` |
| List / read stage | `GET .../stages` and `GET .../stages/{stageId}` |
| Replace / update / delete stage | `PUT`, `PATCH`, `DELETE .../stages/{stageId}` |
| Audit | `GET .../{pipelineId}/audit` and `.../stages/{stageId}/audit` |

Scopes: `crm.schemas.deals.write` for deals, `crm.schemas.custom.write` for custom objects; `.read` versions for reads. Legacy path: `/crm/v3/pipelines/{objectType}...`.

## Create a pipeline (with stages)

Body fields: `label` (required), `displayOrder` (required), `stages` (required array), `pipelineId` (optional internal ID).

Each stage: `label` (required, unique in the pipeline), `displayOrder` (required), `metadata` (required object of string values, `{}` if none), `stageId` (optional internal name, unique; defaults to a numeric ID).

Deal pipeline example:

```json
{
  "label": "New business",
  "displayOrder": 1,
  "pipelineId": "new_business",
  "stages": [
    { "label": "Qualified",   "displayOrder": 0, "stageId": "qualified",  "metadata": { "probability": "0.2" } },
    { "label": "Proposal",    "displayOrder": 1, "stageId": "proposal",   "metadata": { "probability": "0.6" } },
    { "label": "Closed won",  "displayOrder": 2, "stageId": "closed_won", "metadata": { "probability": "1.0" } },
    { "label": "Closed lost", "displayOrder": 3, "stageId": "closed_lost","metadata": { "probability": "0.0" } }
  ]
}
```

Response (pipeline): `id`, `label`, `displayOrder`, `stages[]` (each with `id`, `label`, `displayOrder`, `metadata`, `writePermissions`, `archived`, `createdAt`, `updatedAt`), `createdAt`, `updatedAt`, `archived`.

Add one stage later: `POST .../{pipelineId}/stages` with `{ "label": "Contract signed", "displayOrder": 4, "metadata": { "probability": "0.8" } }`.

## Won, lost, probability

- For **deals**, `metadata.probability` is required, as a string from `"0.0"` to `"1.0"`. The docs say `0.0` is Closed Lost and `1.0` is Closed Won.
- Reading a deal stage back shows `metadata.isClosed` (`"true"` or `"false"`) next to `probability`. The pages read show `isClosed` only in audit output examples, not as a documented input. So: **won = `isClosed` true and probability `1.0`; lost = `isClosed` true and probability `0.0`** (inferred; OQ-1).
- The knowledge base says every deal pipeline should have both a Won and a Lost stage so sales reports work.
- For **tickets**, `metadata.ticketState` is `OPEN` or `CLOSED`.
- For **custom objects** and other objects, the knowledge base UI asks for Open or Closed per stage. The API pages say metadata is optional and show no custom-object example. The exact key is not documented (OQ-1). Proposed handling: send `{ "isClosed": "false" }` for open stages and `{ "isClosed": "true" }` for closed ones, read back after create, and if the stage does not show as closed, record a manual step.
- Our design has stage `type` of `open`, `won` or `lost`. Mapping for deals: open stages get their design probability; `won` gets `"1.0"`; `lost` gets `"0.0"`. For non-deal pipelines HubSpot has only open and closed, no won/lost split (lossy; the stage label carries the meaning).

## Limits

- Stages per pipeline: deal, ticket and custom object pipelines up to 100; appointment, course, listing, lead, order and service pipelines up to 30.
- Custom pipelines per account are counted across all objects and exclude each object's default pipeline. Knowledge base figures:
  - Seat-based pricing: Free tools 0, Starter 15, Professional 100, Enterprise 350.
  - Flexible Seats and Credits portals: Free 0, Starter 15, Professional 350, Enterprise 350.
- Plan gates (knowledge base): creating a custom pipeline needs Starter or higher; custom object pipelines need Enterprise; lead pipelines need Professional or higher; cloning a pipeline needs Professional or higher; restricting a pipeline by team needs Professional or higher.
- Live usage: `GET /crm/limits/{V}/pipelines`.

## Deleting and replacing (2026-09 behaviour)

From `2026-09`, `DELETE` of a pipeline or stage, and `PUT` or `PATCH` of a pipeline, validate references first. If records or other tools use it, the call fails with `category: VALIDATION_ERROR`, `subCategory: PipelineError.STAGE_ID_IN_USE` and the offending IDs in `context`. Passing `validateDealStageUsagesBeforeDelete=false` (deals) or `validateReferencesBeforeDelete=false` (other objects) skips the check. The planner must never pass these flags; stage removals are destructive manual steps anyway.

## Required properties per stage ("stage requirements")

**Not available through the API.** HubSpot calls this *conditional stage properties*. It lives in the UI only.

What I checked: the 2026-09 CRM reference index (635 pages), including the Pipelines API, the Pipeline Rules API and the Property Validations API, and the 2027-03 beta list. None sets properties that must be filled when a record enters a stage.

What the Pipeline Rules API (`/crm/pipelines-rules/{V}/{objectTypeId}/{pipelineId}`) does cover instead:
- `noBackwardsMovementRule`, `noSkippingStagesRule`, `objectCreationRule` (which stages new records may start in);
- deal approval rules (Sales Hub Enterprise);
- stage edit permissions (`.../stage-edit-permissions`, `OPEN` or `RESTRICTED` per stage).

Methods: `GET`, `PUT` (replace), `PATCH` (individual rules), `DELETE`. Scopes: `crm.pipelines.governance.read/write`, `crm.pipelines.stage_permissions.read/write`. The reference page lists Professional as the product tier. These rules are optional extras; none of our blueprints needs them.

Manual path for required fields per stage (knowledge base; needs Edit property settings permission):
Settings > Data Management > Objects > pick the object > Pipelines tab > open the pipeline > in the stage row, hover **Conditional logic rules** > **Add rule** > choose operator and stage(s) > **Add property** under Dependent properties > tick **Required** > **Save logic**. Create the properties first. Read-only properties (scores, calculations) cannot be used. The tier for this feature was not stated on the page (OQ-8).

The plan step must emit one manual step per design stage that has `required_fields`, listing the stage, the properties and which are required.

## Manual alternative for everything else

Settings > Data Management > Objects > object > Pipelines tab > Create pipeline > Create from scratch; add stages with **+ Add stage**; deals show a **Deal probability** dropdown with Won and Lost; other objects show Open or Closed.
