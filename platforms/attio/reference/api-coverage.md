# Attio: API coverage

> Sources: https://api.attio.com/openapi/api (every path read), https://docs.attio.com/llms.txt, https://docs.attio.com/rest-api/endpoint-reference/ pages cited in the other reference files
> Last verified: 2026-10-04

Base URL `https://api.attio.com`. "Automated" means the toolkit can do it with the stable `/v2` API. Nothing here is beta.

| Design concept | Status | Endpoint and URL, or UI path and reason |
|---|---|---|
| Standard objects People, Companies | Native | Always present. Read with `GET /v2/objects` (https://docs.attio.com/rest-api/endpoint-reference/objects/list-objects.md). |
| Enable Deals, Users, Workspaces objects | Manual | UI: Workspace settings, Objects, enable the object. Reason: no enable endpoint in the spec. |
| Custom object | Automated | `POST /v2/objects` (https://docs.attio.com/rest-api/endpoint-reference/objects/create-an-object.md). |
| Rename object | Automated, review | `PATCH /v2/objects/{object}`. |
| Delete object | Manual | `DELETE /v2/objects/{object}` exists but the toolkit never calls it (safety rule). UI: Workspace settings, Objects. |
| Field: text, long_text, url | Automated | `POST /v2/{target}/{identifier}/attributes` type `text`. long_text and url are lossy. |
| Field: number, percent | Automated | type `number`. percent is lossy. |
| Field: currency | Automated | type `currency` with `config.currency`. |
| Field: date | Automated | type `date`. |
| Field: datetime | Automated | type `timestamp`. |
| Field: checkbox | Automated | type `checkbox`. |
| Field: select, multi_select | Automated | type `select`, `is_multiselect` false or true. |
| Field: email | Automated | type `email-address`. |
| Field: phone | Automated | type `phone-number`. |
| Field: user | Automated | type `actor-reference`. |
| Field: record reference | Automated | type `record-reference` with `relationship` (see relationship row). |
| Field title or description change | Automated | `PATCH /v2/{target}/{identifier}/attributes/{attribute}`. |
| Field type or multiselect change | Manual | Cannot change in place. Create a new attribute, migrate data, archive the old one. |
| Field archive | Automated, destructive | `PATCH` with `is_archived: true`. Toolkit treats it as a destructive manual step. |
| Field delete | Manual | No delete endpoint. UI: object settings, Attributes, archive. |
| Field required or unique | Automated, review | `PATCH` `is_required` / `is_unique`; new data only. |
| Field default value | Automated | `default_value` on create or `PATCH`. |
| Select option: add | Automated | `POST /v2/{target}/{identifier}/attributes/{attribute}/options` (https://docs.attio.com/rest-api/endpoint-reference/attributes/create-a-select-option.md). |
| Select option: rename or archive | Automated, review | `PATCH .../options/{option}` (title, is_archived). |
| Select option: delete or reorder | Manual | No delete, no order control. UI: attribute settings. |
| Relationship (both sides, cardinality) | Automated | `POST /v2/objects/{object}/attributes` type `record-reference` plus `relationship` object. |
| Relationship change | Manual | `relationship` not editable. |
| Pipeline | Automated | `POST /v2/lists` (parent object) plus `POST /v2/lists/{list}/attributes` type `status`. See pipelines.md. |
| Stage | Automated | `POST /v2/{target}/{identifier}/attributes/{attribute}/statuses` (https://docs.attio.com/rest-api/endpoint-reference/attributes/create-a-status.md). |
| Stage rename or archive | Automated, review | `PATCH .../statuses/{status}`. |
| Stage reorder or delete | Manual | No order control, no delete. UI: list or board, edit stages. |
| Stage type won / lost | Manual or convention | No flag. Name the statuses Won and Lost; `celebration_enabled` on Won. Reporting by title. |
| Probability | Convention | No field on statuses. Create a number attribute `probability` on the list; value set by hand or workflow. |
| Exit criteria | Documentation only | Stored in attribute description and build sheet. |
| Required field per stage | Manual | No stage-conditional validation. UI: Workflows, or a saved view of gaps. |
| Lost reason | Automated (as select) | select attribute on the list; cannot be required only when lost. |
| List | Automated | `POST /v2/lists` (https://docs.attio.com/rest-api/endpoint-reference/lists/create-a-list.md). |
| List attribute | Automated | `POST /v2/lists/{list}/attributes`. |
| List entry (seed) | Automated | `POST /v2/lists/{list}/entries`, `PUT` to upsert by parent. |
| Record seed or upsert | Automated | `PUT /v2/objects/{object}/records?matching_attribute=<unique_slug>`. |
| View (saved table or board) | Manual | UI: open the object or list, **+ New view**, set filter, sort, group. Reason: views are read-only in the API (`GET .../views`). |
| Automation / workflow | Manual | UI: Workflows, Create workflow. Reason: no workflow endpoint. |
| Webhook | Automated | `POST /v2/webhooks`. Not part of v1 builds. |
| Permission: workspace roles, object or field access | Manual | UI: Workspace settings, Members. No API. |
| Permission: list access | Automated | `workspace_access` and `workspace_member_access` on `POST /v2/lists`. |
| Token and workspace check | Automated | `GET /v2/self`. |
| Reading state | Automated | `GET /v2/objects`, `GET /v2/lists`, `GET .../attributes?show_archived=true`, `.../options`, `.../statuses`, `GET .../views`. |
