> Sources: https://developers.hubspot.com/docs/api-reference/latest/crm/lists/guide.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/lists/create-list.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/lists/filters/guide.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/exports/guide.md ; https://developers.hubspot.com/docs/_llms/apis/2026-09/crm.md ; https://knowledge.hubspot.com/records/create-and-manage-saved-views ; https://legal.hubspot.com/hubspot-product-and-services-catalog
> Last verified: 2026-10-04

# HubSpot: saved views and lists

HubSpot has two different things that people call "views".

| Thing | What it is | API? |
|---|---|---|
| **Saved view** | A saved set of filters, sort order, columns and view type (table, board, and so on) on a record index page such as Contacts or Deals | **No create or edit endpoint found** |
| **List / segment** | A group of records, either fixed or rule-driven | **Yes**, the Segments (Lists) API |

## Saved views

I searched the 2026-09 API index (CRM, 635 pages), the legacy CRM index and the 2027-03 beta index. There is no endpoint to create, read, update or delete saved index-page views. The Exports API can export "records in views or lists" but does not define a view. Treat saved views as **manual**.

Manual steps (knowledge base, "Create and manage saved views", available on all products and plans):
1. CRM > pick the object (for example Deals).
2. Click the **+ add view** icon and pick a view type (table, board, gantt).
3. Name the view and confirm.
4. Set advanced or quick filters. Edit columns with the edit columns icon (tick properties, drag to order).
5. Choose the sort property in the view's settings panel.
6. Click **Publish**.
7. Sharing: view settings > **Manage sharing** > Private, Team, Everyone or Custom. New views are private to the creator and Super Admins by default.

For the design file's `views` list (name, object, filter, sort), emit one manual step per view with those details. The step is done when the view tab shows on the index page for the users in scope.

## Lists (segments)

Creatable and readable by API. Scopes: `crm.lists.read`, `crm.lists.write`. The reference page states Free tier for the API; the catalog limits active lists on lower tiers (Free tools and Starter allow a small number of active lists, with more static ones). The exact counts per tier were not captured (OQ-12).

### Create

`POST https://api.hubapi.com/crm/lists/{V}/`

Required: `name` (unique in the account), `objectTypeId` (for example `0-1`), `processingType`.

| `processingType` | Meaning |
|---|---|
| `MANUAL` | Static. Members added and removed by hand or API only. |
| `DYNAMIC` | Active. Filters decide membership; HubSpot keeps it current. |
| `SNAPSHOT` | Filters are applied once at creation, then it behaves as static. |

Static example:

```json
{ "name": "Priority accounts", "objectTypeId": "0-2", "processingType": "MANUAL" }
```

Dynamic example (`filterBranch` must be a root `OR` branch containing `AND` branches):

```json
{
  "name": "Open enterprise deals",
  "objectTypeId": "0-3",
  "processingType": "DYNAMIC",
  "filterBranch": {
    "filterBranchType": "OR",
    "filters": [],
    "filterBranches": [
      {
        "filterBranchType": "AND",
        "filters": [
          {
            "filterType": "PROPERTY",
            "property": "dealstage",
            "operation": { "operationType": "enumeration", "operator": "IS_ANY_OF", "values": ["qualified", "proposal"] }
          }
        ],
        "filterBranches": []
      }
    ]
  }
}
```

The filters guide lists lowercase operation types (`alltypes`, `string`, `enumeration`, `bool`, `datetime`, ...) but its worked examples use uppercase names such as `MULTISTRING`. The example above follows the reference list. Test both forms against a test account before generating dynamic lists (OQ-12).

Response: `{ "list": { "listId": "611", "listVersion": 1, "processingType": "MANUAL", "objectTypeId": "0-1", "name": "...", "processingStatus": "COMPLETE", ... } }`.

### Other calls

| Action | Request |
|---|---|
| Read by ID | `GET /crm/lists/{V}/{listId}` (add `includeFilters=true`) |
| Read by name | `GET /crm/lists/{V}/object-type-id/{objectTypeId}/name/{listName}` |
| Search / list all | `POST /crm/lists/{V}/all` (cursor `after`, up to 500 per page) |
| Rename | `PUT /crm/lists/{V}/{listId}/update-list-name?listName=...` |
| Change filters | `PUT /crm/lists/{V}/{listId}/update-list-filters` |
| Delete | `DELETE /crm/lists/{V}/{listId}` |
| Restore | `PUT /crm/lists/{V}/{listId}/restore` |
| Create folder | `POST /crm/lists/{V}/folders` (rename, move and delete folder also exist) |
| Members | `PUT /crm/lists/{V}/{listId}/memberships/add` and `.../memberships/remove` |

Legacy path: `/crm/v3/lists`.

### Idempotency

List names must be unique within the account. Create by first reading by name; create only if absent.

## Manual alternative

Contacts (or the object) > Segments > Create segment. Needs a tier that allows the list type you want.
