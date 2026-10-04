# Attio: views and lists

> Sources: https://api.attio.com/openapi/api (list, entry, view endpoints), https://docs.attio.com/rest-api/endpoint-reference/lists/create-a-list.md, https://docs.attio.com/rest-api/endpoint-reference/lists/update-a-list.md, https://docs.attio.com/rest-api/endpoint-reference/entries/upsert-a-list-entry-by-parent.md, https://docs.attio.com/docs/objects-and-lists
> Last verified: 2026-10-04

## Views

Read only. `GET /v2/objects/{object}/views` and `GET /v2/lists/{list}/views` (scopes `object_configuration:read`, `list_configuration:read`) return `{"data": [{"id": {"workspace_id","object_id" or "list_id","view_id"}, "title": "...", "created_at": "..."}]}`.

The view id can be passed as `filter_view_id` when querying records or entries. There is no endpoint to create, edit, filter, sort or delete a view. Every view in a design is a manual step.

## Lists

A list holds entries. Each entry points to one parent record of one object type and can carry its own attributes.

### Create

`POST /v2/lists`. Scope `list_configuration:read-write`.

```json
{"data": {
  "name": "New business",
  "api_slug": "new_business",
  "parent_object": "deals",
  "workspace_access": "full-access",
  "workspace_member_access": []
}}
```

All five fields are required. `workspace_access`: `full-access`, `read-and-write`, `read-only`, or `null` for private. A new list needs `workspace_access: "full-access"` or at least one member with `full-access`. Member-level or private access may return 403 `billing_error` on lower plans, so always use `full-access` for the workspace.

Errors: 409 `slug_conflict` (slug exists), 404 `not_found` (parent object), 400 `value_not_found`, 403 `billing_error`.

### Read

`GET /v2/lists` and `GET /v2/lists/{list}`:

```json
{"data": [{"id": {"workspace_id":"...","list_id":"..."}, "api_slug":"new_business", "name":"New business",
           "parent_object":["deals"], "workspace_access":"full-access", "workspace_member_access":[],
           "created_by_actor":{"type":"api-token","id":"..."}, "created_at":"..."}]}
```

`parent_object` is an array (legacy lists can have several).

### Update

`PATCH /v2/lists/{list}` accepts `name`, `api_slug`, `workspace_access`, `workspace_member_access`. The parent object cannot be changed through the API. There is no delete-list endpoint.

### Attributes on lists

Same endpoints as objects with `target` = `lists`: `POST /v2/lists/{list}/attributes`, options and statuses likewise. Scope `list_configuration:read-write`. All types in fields.md apply.

### Entries

| Action | Method and path | Notes |
|---|---|---|
| Add a record | `POST /v2/lists/{list}/entries` | Body `{"data":{"parent_record_id","parent_object","entry_values":{}}}`. Throws on unique conflicts. A record may be added more than once. |
| Upsert by parent | `PUT /v2/lists/{list}/entries` | Same body. Updates the entry for that parent, or creates one. Returns `MULTIPLE_MATCH_RESULTS` if the parent has several entries. |
| Query | `POST /v2/lists/{list}/entries/query` | Filter and sort body. |
| Get / update / delete | `GET`/`PATCH`/`PUT`/`DELETE /v2/lists/{list}/entries/{entry_id}` | PATCH appends multiselect values; PUT overwrites them. |

Scopes: `list_entry:read-write`, `list_configuration:read`.

Example:

```json
{"data": {"parent_record_id": "<uuid>", "parent_object": "deals",
          "entry_values": {"stage": [{"status": "Lead"}]}}}
```

The toolkit builds structure only, so it does not need entries except for optional seed data.

## Permissions

List access is set at creation (`workspace_access`, `workspace_member_access`). There is no API for object-level, field-level or role permissions.
