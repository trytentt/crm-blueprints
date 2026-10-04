> Sources: https://developers.hubspot.com/docs/api-reference/latest/crm/associations/associations-schema/guide.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/associations/associate-records/guide.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/associations/overview.md ; https://developers.hubspot.com/docs/api-reference/legacy/crm/associations/associations-schema/labels/create-associations-label.md ; https://developers.hubspot.com/docs/api-reference/legacy/crm/associations/associations-schema/limits/create-associations-limits.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/objects/schemas/guide.md ; https://knowledge.hubspot.com/object-settings/create-and-use-association-labels ; https://knowledge.hubspot.com/object-settings/set-limits-for-record-associations ; https://legal.hubspot.com/hubspot-product-and-services-catalog ; https://developers.hubspot.com/docs/api-reference/latest/crm/limits-tracking/guide.md
> Last verified: 2026-10-04

# HubSpot: relationships (associations)

HubSpot links records with **associations**. Two layers matter:

1. The **definition** (association type) between two object types. It has a numeric `typeId` and a `category`.
2. The **instance**: a link between two records, optionally carrying labels.

`{V}` is the pinned API version (`2026-09`). Legacy v4 paths are `/crm/associations/v4/...` and `/crm/v4/associations/...`.

## Cardinality

HubSpot has no one-to-one or one-to-many setting as such. Every association is many-to-many by default. You can cap it with **association limits** (Professional and Enterprise): "at most N associated records per type", for example one company per deal. Defaults: a contact can link to up to 50,000 companies.

| Our cardinality | HubSpot handling |
|---|---|
| `many_to_many` | Default. Nothing to configure. |
| `one_to_many` / `many_to_one` | Add an association limit of 1 on the "one" side. |
| `one_to_one` | Limit of 1 on both directions. |

Limits are Professional or Enterprise (knowledge base). On Starter the cap is a manual convention, so record it as a warning.

## Labels (roles)

A label names the role, for example "Decision maker". Two kinds:
- **Single**: one word for both sides (Friend).
- **Paired**: a word for each side (Manager / Employee). Needs `inverseLabel`.

Plan and counts:
- Association labels need Professional or Enterprise (knowledge base article, hubs listed).
- The developer page says up to **10** labels per object pair; the knowledge base and product catalog say up to **50** (OQ-2). Plan for 10.
- HubSpot-defined types: the unlabeled default, and "Primary" for company associations. They cannot be deleted.

### Create a label

`POST https://api.hubapi.com/crm/associations/{V}/{fromObjectType}/{toObjectType}/labels`

Body: `name` (internal; no hyphens; not starting with a digit), `label` (shown), `inverseLabel` (paired only).

```json
{ "name": "manager_employee", "label": "Manager", "inverseLabel": "Employee" }
```

Response: `results[]` of `{ "category": "USER_DEFINED", "typeId": 144, "label": "Manager" }`, one entry per direction for a paired label. Keep both IDs: the ID depends on direction.

Legacy: `POST /crm/associations/v4/{fromObjectType}/{toObjectType}/labels`.

### Read labels

`GET /crm/associations/{V}/{fromObjectType}/{toObjectType}/labels` returns `results[]` with `category` (`HUBSPOT_DEFINED` or `USER_DEFINED`), `typeId` and `label` (`null` for the unlabeled type).

Read in both directions to see both sides of a pair, for example contacts to companies and companies to contacts.

### Update and delete a label

- `PUT .../labels` with `{ "associationTypeId": 32, "label": "Contract worker" }`. Only `label` (and `inverseLabel`) change. The internal `name` and `typeId` are fixed.
- `DELETE .../labels/{associationTypeId}`. A label in use must first be removed from the records that carry it.

### Limits on a definition

- `POST /crm/associations/{V}/definitions/configurations/{from}/{to}/batch/create` (and `/batch/update`) with `inputs: [{ "category": "USER_DEFINED", "typeId": 35, "maxToObjectIds": 1 }]`.
- `GET /crm/associations/{V}/definitions/configurations/{from}/{to}` and `.../all` to read.
- `POST .../batch/purge` with `category` and `typeId` to remove a limit.
- Max configurable value in the UI is 10,000. Super Admin is needed in the UI.

## Associating custom objects

At schema creation, list target object type IDs in `associatedObjects`. That creates the definition and a default unlabeled association type. To add a relationship from or to an existing object, create a label with the endpoint above (the reference does not show a separate "create unlabeled association definition" call; OQ-7). Associations to activities (notes, calls, tasks, meetings, emails) exist automatically for custom objects.

An object-to-itself relationship (for example parent company) needs `shouldCreateSameObjectAssociation: true` on a custom schema; for companies HubSpot already has parent/child types (`13`, `14`).

## Record-level associations (for seed data and tests)

| Action | Request |
|---|---|
| Unlabeled (default) | `PUT /crm/objects/{V}/{fromObjectType}/{fromId}/associations/default/{toObjectType}/{toId}` |
| Labeled | `PUT /crm/objects/{V}/{fromObjectType}/{fromId}/associations/{toObjectType}/{toId}` with body `[ { "associationCategory": "USER_DEFINED", "associationTypeId": 36 } ]` |
| Read | `GET /crm/objects/{V}/{fromObjectType}/{id}/associations/{toObjectType}` |
| Batch | `POST /crm/associations/{V}/{from}/{to}/batch/create`, `.../batch/associate/default`, `.../batch/read` (up to 1,000 IDs) |

HubSpot-defined type IDs (selection): contact to company `279`, contact to primary company `1`, company to contact `280`, company to primary contact `2`, contact to deal `4`, company to deal `342`, primary company to deal `6`, company to company `450`, parent to child company `13`, child to parent `14`. Use the full table in the associate-records guide for others.

## Record usage limits

A record can hold a bounded number of associations (for example 50,000 companies per contact). The Limits Tracking API reports records near the limit: `GET /crm/limits/{V}/associations/records/from`. Label counts: `GET /crm/limits/{V}/associations/labels`.

## Mapping from our design

| Design | HubSpot |
|---|---|
| `relationship` between two objects | association definition (exists for standard pairs; created for custom objects) |
| `from_label` / `to_label` | a paired label (`label`, `inverseLabel`) |
| single role label | single label |
| `cardinality` | association limit |
| `purpose` | not stored; keep in docs |

Where the plan is Starter, the apply step can still associate records but cannot create labels: emit a manual-or-upgrade step.

## Manual alternative

Settings > Data Management > Objects > object > Associations tab > Create association label (Super Admin). The "View API details" action there shows the type ID.
