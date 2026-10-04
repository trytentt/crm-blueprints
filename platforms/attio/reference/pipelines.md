# Attio: pipelines and stages

> Sources: https://docs.attio.com/rest-api/attribute-types/attribute-types-status.md, https://docs.attio.com/docs/standard-objects/standard-objects-deals, https://docs.attio.com/rest-api/endpoint-reference/deals/create-a-deal-record.md, https://docs.attio.com/docs/objects-and-lists, https://api.attio.com/openapi/api (status schema, list and entry endpoints)
> Last verified: 2026-10-04

## What Attio has

There is no "pipeline" object. A pipeline is a `status` attribute. Its options ("statuses") are the stages. The UI shows records or list entries as a board grouped by that attribute.

Two places can hold the status attribute:

| Place | How | Fit |
|---|---|---|
| An object (for example Deals) | `stage` status attribute on the object. Deals ship with it: required, defaults such as Lead, In Progress, Won, Lost. | One stage set per object. |
| A list | Create a list whose parent is the object, add a `stage` status attribute to the list. Each record in the process becomes an entry. | One list per pipeline. A record can sit in several lists, each at its own stage. |

Attio's own guide says lists "model a particular process", and that list attributes are separate from the parent record's attributes.

## What Attio does not have

- Won and lost flags. A status has only `title`, `is_archived`, `celebration_enabled`, `target_time_in_status`. "Won" and "Lost" are ordinary names.
- Probability per stage. No field and no forecast weighting in the API.
- Required fields per stage. `is_required` is global to the attribute, not conditional on stage.
- Stage order control. The create call has no position. Order appears to follow creation order (not stated). No reorder call.
- Stage entry rules or exit criteria. Not stored.
- Deleting a stage. Only archive.

## Recommendation for the generator

One approach: **one list per design pipeline, with a `stage` status attribute on the list.**

Why this one:

1. Our designs allow several pipelines on one object (new business and renewals both on Deal). An object has one `stage` attribute; lists scale to any number.
2. Stage sets differ per pipeline, and list statuses are independent per list.
3. It matches Attio's own idea of lists as processes.
4. It works the same for a custom object (a recruitment "search") as for Deals.

Build steps per pipeline:

1. `POST /v2/lists` with `parent_object` = the pipeline's object slug.
2. `POST /v2/lists/{list}/attributes` with `type: "status"`, `api_slug: "stage"`, `is_multiselect: false`, `config: {}`.
3. `POST /v2/lists/{list}/attributes/stage/statuses` once per stage, in design order.
4. For a "lost" stage, add a `lost_reason` select attribute on the list (options from the design) and create its options.
5. For probability, add a `probability` number attribute on the list and note that Attio does not enforce it. The stage-to-probability mapping stays in `design.yaml` and in the build sheet.
6. For stage required fields, create the attributes on the list (not required) and list the gate as a manual step (see below).

Keep stage titles clean. Put the "entered when" text in the attribute description of `stage` and in the build sheet.

### The Deals clash

Deals already require a `stage` on the record. If a design pipeline sits on Deal, the record still has its own native stage. Handling: leave the native stage alone, give new-deal creation a sensible default (the first native stage), and record in the build sheet that the list's `stage` is the working pipeline. Alternative for single-pipeline designs: use the native `stage` and add statuses to it. See open-questions.md (Q8).

## Won and lost representation

- Create statuses titled exactly as the design's won and lost stages (for example "Won", "Lost").
- Turn on `celebration_enabled: true` for the won status. It is cosmetic.
- Lost needs a reason. The API cannot make `lost_reason` required only when stage is Lost. Create it as a select, not required, and add a manual step: a workflow (UI) that creates a task, or a saved view that surfaces lost entries with no reason.
- Reports that need "closed won" must filter on the status title. Say so in the build sheet.

## Required fields per stage

Not available. The generator should:

1. Create the gate attributes on the list or object, `is_required: false`.
2. Emit a manual step per gated stage: "In Workflows, add a rule that blocks or flags entry to <stage> when <fields> are empty", or a view of entries at that stage with the fields empty. Reason: no API support for stage-conditional validation.

## Reading pipelines (state)

For each list: `GET /v2/lists`, then `GET /v2/lists/{list}/attributes`, find `type: "status"`, then `GET /v2/lists/{list}/attributes/{slug}/statuses?show_archived=true`. For object pipelines, the same on `/v2/objects/{object}/attributes`.

Status response:

```json
{"data": [{"id": {"workspace_id":"...","object_id":"...","attribute_id":"...","status_id":"..."},
           "title": "Lead", "is_archived": false, "celebration_enabled": false,
           "target_time_in_status": null}]}
```

Compare titles in order. Archived statuses are not stages.

## Writing a stage value

On a record: `"stage": [{"status": "Lead"}]` (title or id). On a list entry, the same under `entry_values`. An unknown title fails with 400 `value_not_found`; Attio never creates a status on write.
