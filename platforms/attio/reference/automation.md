# Attio: automation

> Sources: https://docs.attio.com/sdk/workflow-blocks/overview, https://attio.com/help/reference/automations/workflows/create-a-workflow, https://api.attio.com/openapi/api (full path list read; no workflow path exists), https://docs.attio.com/llms.txt (documentation index; no workflow endpoint listed), https://docs.attio.com/rest-api/endpoint-reference/webhooks/create-a-webhook.md
> Last verified: 2026-10-04

## Can workflows be created through the API?

No. The REST API has no workflow endpoint. I read every path in the OpenAPI spec and the documentation index; none creates, edits, lists or runs a workflow. The SDK docs describe "workflow blocks", which let an installed app add trigger and step blocks to the workflow builder. That extends the builder; it does not create workflows.

So every automation in a design is a manual step.

## Manual route

1. In Attio, click **Workflows** in the left sidebar.
2. Click **Create workflow** (top right), or duplicate an existing one.
3. Choose a trigger (for example "Record created", or a list entry event), then add steps and conditions.

Workflows are available on all plans; the number of credits depends on the plan. Workflows can also be drafted by describing the goal in plain language ("Ask Attio"), which uses credits.

## What the API can still do

- Webhooks: `POST /v2/webhooks` (scope `webhook:read-write`, workspace token only) lets an outside service react to events such as `record.created`, `record.updated`, `list-entry.created`, `list-entry.updated`, `object-attribute.created`. The target URL must be `https://`. Duplicate target, event and filter combinations return 409. This is a route for custom code, not a replacement for workflows, and it needs a server the client owns. Not used by the toolkit in v1.
- Default values on attributes (`default_value`, static or dynamic such as `current-user` or an ISO duration) cover a few small "auto-set" automations.
- `target_time_in_status` on a status stores a target duration; it does not trigger anything on its own.

## Generator handling

For each design `automation` (name, trigger, action): emit a manual step titled with the name, UI path above, "Done when" the workflow is on and a test record behaves as described. Reason: "Attio has no API to create workflows."
