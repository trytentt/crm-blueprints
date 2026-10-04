# Platform comparison

How Attio, HubSpot and Salesforce differ for the things a design describes. Everything here comes
from the research notes in `platforms/<crm>/reference/`, last verified 2026-10-04. Cited files
are named in each section and listed at the end. Vendor APIs change, so re-check a row before
promising it to a client. Where the research could not settle a point, the row says so and points to
the platform's `open-questions.md`.

"Automated" means the toolkit can do it through the platform's stable API or metadata tooling.
"Manual" means it appears in the client's `manual-steps.md` with a UI path.

## At a glance

| | Attio | HubSpot | Salesforce |
|---|---|---|---|
| How the toolkit builds | REST API `/v2` | REST API, dated version `2026-09` | SFDX source-format metadata, `sf project deploy start`, API 67.0 |
| Credential | Workspace access token | Service key (fallback: legacy private app) | `sf` CLI login: web, JWT, access token or auth URL |
| Sandbox | None. Use a separate workspace | Developer test account (free, 90-day Enterprise trial). Standard sandbox needs Enterprise | Sandbox, or Developer Edition org |
| Plan or edition gate | Object count limit by plan (unclear what counts) | Custom objects: Enterprise. Association labels and limits: Professional or Enterprise | Metadata API: Enterprise, Unlimited, Performance or Developer edition |
| Read live state | Yes | Yes | Yes, via `sf sobject describe`, retrieve and queries |
| Idempotency | Read first; `409 slug_conflict` on a duplicate | Read first; no documented duplicate error | A deploy is create-or-update; unchanged files report `Unchanged` |

## Objects

| | Attio | HubSpot | Salesforce |
|---|---|---|---|
| Core Company, Person, Deal | `companies`, `people`, `deals` | Companies, Contacts, Deals | Account, Contact, Opportunity |
| Deals | Off by default. An admin enables them in the UI (manual) | Built in | Built in |
| Custom objects | Automated. `POST /v2/objects` | Automated, **Enterprise only**. Typically up to 10 definitions | Automated. Allowances by edition (Enterprise: 200 objects, 500 fields per object) |
| After creation | `api_slug` can be patched but renaming is risky | Name and labels are fixed | `fullName` is the identity; a rename is a new component |
| Plan requirement | Plan-dependent object limit (3, 5, 12 or unlimited) | Enterprise | Edition, above |

Research: `attio/reference/objects.md`, `hubspot/reference/objects.md`, `salesforce/reference/objects.md`.

## Fields

All 14 canonical types map on every platform. Several are lossy.

| Canonical | Attio | HubSpot | Salesforce |
|---|---|---|---|
| text | `text` | `string` / `text` | `Text` + length |
| long_text | `text` (lossy) | `string` / `textarea` | `LongTextArea` |
| select | `select` | `enumeration` / `select` | `Picklist` |
| multi_select | `select`, multiselect | `enumeration` / `checkbox` | `MultiselectPicklist` |
| number | `number` | `number` | `Number` |
| currency | `currency` | `number` with currency symbol (lossy; no code on the field) | `Currency` |
| percent | `number` (lossy) | `number` with percentage hint (storage convention unconfirmed) | `Percent` |
| date | `date` | `date` | `Date` |
| datetime | `timestamp` | `datetime` | `DateTime` |
| checkbox | `checkbox` | `bool` | `Checkbox` |
| url | `text` (lossy) | `string` / `text` (no validation) | `Url` |
| email | `email-address` | `string` / `text` with email hint | `Email` |
| phone | `phone-number` | `string` / `phonenumber` | `Phone` |
| user | `actor-reference` | `enumeration` with owner reference | `Lookup` to `User` |

| | Attio | HubSpot | Salesforce |
|---|---|---|---|
| Type change in place | Not possible | Never done by the toolkit | Never done by the toolkit; many conversions blocked |
| Delete a field | Archive only (no delete) | Not done by the toolkit | Manual in Setup |
| Required field | `is_required`, applied after create; default off | Custom objects only (`requiredProperties`). Standard objects: manual | Field-level required blocks every save; the toolkit uses validation rules instead |
| Fixed after creation | Type, `is_multiselect` | Property `name`, `hasUniqueValue` | API name, type conversions limited |
| New fields visible | Yes | Yes | **No.** Needs a permission set (generated) and a page layout (manual) |

Research: `*/reference/fields.md`, and the type tables in each `api-coverage.md`.

## Relationships

| | Attio | HubSpot | Salesforce |
|---|---|---|---|
| Mechanism | `record-reference` attribute with a `relationship` object. One call makes both sides | Association labels, paired or single. Object links declared in the schema for custom objects | `Lookup` or `MasterDetail` field on the child object |
| Cardinality | Set through `is_multiselect` on each side | Association limits (`maxToObjectIds`), Professional or Enterprise | Many-to-one by field side; one-to-one has no native form (duplicate or validation rule) |
| Many-to-many | Both sides multiselect | Default for associations | Junction object with two master-detail fields |
| Labels | Title on each side | `label` and `inverseLabel` | `relationshipLabel` and `relationshipName` |
| Change later | Not possible; `relationship` is not editable | Labels: Professional or Enterprise; 10 or 50 per pair (sources disagree) | Lookup to master-detail purges child records |

Research: `*/reference/relationships.md`; `hubspot/reference/open-questions.md` (OQ-2, OQ-7).

## Pipelines and stages

| | Attio | HubSpot | Salesforce |
|---|---|---|---|
| Representation | One **list** per pipeline, with a `stage` status attribute | Native pipelines on deals, tickets and custom objects | Opportunity: `OpportunityStage` values, a `BusinessProcess` and a `RecordType` per pipeline. Other objects: a `Stage__c` picklist |
| Won and lost | No flag. By convention, statuses named Won and Lost | Deals only, via probability `1.0` / `0.0`. Other objects: open or closed | Opportunity: `closed` and `won` flags. Other objects: no native flag |
| Probability | Convention: a number attribute on the list | Automated on deals (`metadata.probability`, a string) | Opportunity: `probability` on the stage value |
| Required fields per stage | **Manual** | **Manual** (conditional stage properties, UI only) | **Automated**: validation rules with a `CASE` on the stage |
| Exit criteria | Stored in the attribute description and build sheet | Build sheet only | Path guidance text (`PathAssistant`) |
| Add stage | Automated | Automated | Automated (a deploy only adds) |
| Remove or reorder stage | Manual (no API) | Blocked by default if in use | Manual |
| Limits | Plan-dependent | Custom pipelines: 15 (Starter), 100 or 350 (Professional), 350 (Enterprise); custom object pipelines need Enterprise | Default stages remain and must be hidden by hand |

Research: `*/reference/pipelines.md`; `attio/reference/open-questions.md` (Q4, Q6, Q8, Q10, Q14);
`hubspot/reference/open-questions.md` (OQ-1, OQ-8).

## Views

| | Attio | HubSpot | Salesforce |
|---|---|---|---|
| Create via API | No. Views are read-only | No API found | Yes, `ListView` (filters and columns; **no sort**) |
| Manual path | Open the object or list, **+ New view** | CRM, the object, **+ add view**, then Publish | The list view, controls menu, sort by column |
| Lists and segments | Lists: automated | Lists (static and active): automated | Not applicable |

Research: `*/reference/views-and-lists.md` and the `api-coverage.md` view rows.

## Automation

| | Attio | HubSpot | Salesforce |
|---|---|---|---|
| Create via API | No workflow endpoint | Beta only; off by default | Flows can be deployed, but the toolkit does not, because a wrong flow runs on every save |
| Result | **Manual** (Workflows) | **Manual** (Automations, Workflows). Needs Professional or Enterprise | **Manual** (Setup, Flows). Production flows deploy inactive unless a Setup preference is on |
| Webhooks | Automated, not used in v1 | Not used | Not used |

Research: `*/reference/automation.md`.

## Sandbox and test environments

| | Attio | HubSpot | Salesforce |
|---|---|---|---|
| Option | **None.** A separate free workspace is the test target. The tool cannot tell it from a live one, so the engineer sets `ATTIO_TARGET` | Developer test account: free, up to 10 per account, 90-day Enterprise trial, so custom objects can be tested. Standard sandbox needs Enterprise | Sandbox (Developer, Developer Pro, Partial Copy, Full), scratch org (needs a Dev Hub), Developer Edition org |
| Record IDs | Not applicable | Differ from production | Differ from production |

Research: `*/reference/auth-and-setup.md`; `attio/reference/open-questions.md` (Q1).

## API coverage summary

| Concept | Attio | HubSpot | Salesforce |
|---|---|---|---|
| Objects, fields, options | Automated | Automated | Automated |
| Relationships | Automated | Automated | Automated |
| Pipelines, stages | Automated | Automated | Automated |
| Stage gating | Manual | Manual | Automated |
| Won/lost flag | Convention | Deals only | Opportunity only |
| Views | Manual | Manual | Automated, without sort |
| Automations | Manual | Manual | Manual |
| Permissions | Manual (list access automated) | Manual | Field access automated; assignment manual |
| Deletes and type changes | Never | Never | Never |

Research: `*/reference/api-coverage.md`, the authority on every row.

## Rate limits

| Attio | HubSpot | Salesforce |
|---|---|---|
| 100 reads and 25 writes a second. Retry 429 using `Retry-After`. | 100 calls per 10 seconds (Free, Starter); 190 (Professional, Enterprise). Daily 250,000 to 1,000,000. | Metadata deploy limits are far above a blueprint's size. API allowances differ by edition (Developer Edition 15,000 a day). |

Research: `*/reference/limits-and-errors.md`.

## Choosing a platform for a client

This toolkit does not recommend a platform. The client's choice stands. Use the table to say plainly
what the build will cover, and raise these as decisions:

1. **HubSpot below Enterprise:** custom objects are unavailable. Use the deal-pipeline fallback in the
   blueprint README, or the client upgrades.
2. **Salesforce on Professional or Essentials:** no automated build. The client gets the build sheet
   and a manual build.
3. **Attio:** no sandbox, no workflow or view creation, no won/lost flags. Say so before the
   client expects them.
4. **Any platform:** stage gating by required fields is automated only on Salesforce.

## Sources

Files drawn on for this page (all under `platforms/`):

- `attio/README.md`, `attio/reference/{api-coverage,auth-and-setup,objects,fields,relationships,pipelines,views-and-lists,automation,limits-and-errors,open-questions}.md`
- `hubspot/README.md`, `hubspot/reference/{api-coverage,auth-and-setup,objects,fields,relationships,pipelines,views-and-lists,automation,limits-and-errors,open-questions}.md`
- `salesforce/README.md`, `salesforce/reference/{api-coverage,auth-and-setup,objects,fields,relationships,pipelines,views-and-lists,automation,limits-and-errors,open-questions}.md`

Each of those files lists its own vendor URLs and the date checked.
