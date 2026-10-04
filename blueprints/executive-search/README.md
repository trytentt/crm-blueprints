# Executive search

## Who it is for

A retained executive search firm placing board and senior leaders. Partners win mandates and own the
client relationship, consultants and researchers run searches, and a small finance function invoices
retained fees.

## The sales motion

1. A partner builds a relationship with a sponsor (chair, CEO, investor or HR lead) and is introduced to a specific role.
2. A brief and a proposal follow: approach, timetable, fee (often about a third of first-year total pay) and how it is split into instalments. Often a pitch against other firms.
3. On engagement, the search starts: position specification, market mapping, longlist, outreach to mostly passive people, assessment interviews and a shortlist to the client.
4. The client interviews, chooses, makes an offer, and references are taken. The final instalment falls due on placement.
5. Fees are billed in instalments at defined points. A cancelled search may waive later instalments.

## Design reasoning

A retained search is a project with its own timetable, so it gets its own object and delivery pipeline
and the mandate deal ends when the agreement is signed. Longlist, shortlist and offer are not states of
a person but states of a person on one search, so a search-candidate record carries the stage and one
Person can appear on many searches. The candidate stage pipeline is where the work is visible. Because
fees are paid in staged instalments tied to milestones, each instalment is a record with its own
status. That gives a cash forecast by stage and stops fee tracking living in a spreadsheet. Candidates
are People with a type, because one human is one record. Confidentiality is built in, because many
searches replace an incumbent who must not learn the role is open. Off-limits rules, which stop the
firm approaching a client's own staff, are enforced with dates on the company and restrictions on
the person.

## Design choices

- **Three custom objects**: search, search candidate and fee instalment.
- **Four pipelines**: mandate acquisition (deal), search delivery (search), candidate progress (search candidate), fee collection (fee instalment).
- **Fee stages**: scheduled, due, invoiced, paid, or waived with a reason.
- **Mandate stages** end at a signed agreement. Terms agreed requires exclusivity confirmed.
- **Longlist and shortlist** are stages on both the search and each candidate, so counts per search are views.
- **Person type is a multi-select**, with a contact restriction select checked before outreach.
- **No real company names or data.**

## Objects

| Object | Native | Purpose |
|---|---|---|
| Company | yes | The client, with off-limits date |
| Person | yes | A candidate, client contact, source or investor, by person type |
| Deal | yes | The mandate opportunity |
| Search | custom | One retained mandate and its timetable |
| Search candidate | custom | One person on one search, with their stage |
| Fee instalment | custom | One scheduled payment of the retained fee |

## Pipelines

- **Mandate acquisition**: target, introduction, brief, proposal sent, pitch or finalist, terms agreed, mandate won, mandate lost.
- **Search delivery**: position specification, market mapping, longlist, shortlist, client interviews, offer and references, placed, closed without placement.
- **Candidate progress**: identified, approached, engaged, assessed, shortlisted, client interview, offer, placed, out.
- **Fee collection**: scheduled, due, invoiced, paid, waived.

## Decisions

See `decisions` in `design.yaml`: delivery on the search, candidates as people, instalments on their own
object, confidential searches, off-limits enforcement, the custom-object fallback, and contingent work.

## Sensitive data

Candidate data is personal data. Current total compensation is sensitive, so restrict it to the search
team. For confidential searches use a code name, a confidential flag and permissions limited to the
search team. Never put the incumbent's name in a record name or note. Do not store protected-characteristic
or health data, or copies of identity documents. Record the lawful basis and a data review date on every
candidate. Confirm access rules with the managing partner before go-live.

## Plan-dependent features

- **HubSpot:** three custom objects and a pipeline on each may need a higher tier, and the number of custom objects may be limited. Record-level permissions for confidential searches may also be plan-dependent. Fallback: the `custom_objects_plan` decision. Build Search and Search candidate first and hold fees as properties on Search.
- **Attio:** the number of custom objects and per-record permissions may depend on plan. Fallback: the same order, and a status attribute instead of a pipeline on fee instalments.
- **Salesforce:** custom object limits and sharing rules depend on edition. Fallback: use Opportunity record types for searches.
- Automated fee schedules need workflow features that may be plan-dependent. Fallback: create instalments by hand from a checklist.

Exact tiers: see hubspot/plan-requirements.md once generated.
