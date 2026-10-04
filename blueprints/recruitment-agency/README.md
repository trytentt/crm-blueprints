# Recruitment agency

## Who it is for

A recruitment agency placing permanent, contract or temporary staff for business clients, working
contingent, retained or a mix. Typically consultants organised in desks by specialism, a desk manager
and a small back office that invoices.

## The sales motion

1. Business development: a consultant targets companies with a likely hiring need, speaks to a hiring manager, and gets terms of business signed. Fee percentage, rebate period and exclusivity are the commercial terms.
2. The client gives a role (a job order). The consultant sources candidates from the database, job boards, LinkedIn and referrals.
3. Each candidate is screened, then submitted to the client, then interviewed, offered and, if all goes well, started. The fee is earned on the start date and is refundable for a rebate period.
4. Candidates who are not placed stay in the database. Some later become client contacts.

## Design reasoning

The commercial relationship (terms of business) and the work (roles and candidates) move at different
speeds, so they are different objects. The deal is the client relationship and ends when terms are
signed. A role is a job order. A submission is one candidate on one role, and it carries the placement
pipeline because that is where the volume, the conversion rates and the revenue are. A deal per
placement would flood the pipeline and distort win rate, so the fee sits on the submission. Candidates
are People with a type, never a second person object, because a candidate can become a hiring manager
and one human should be one record. Because candidates are individuals, the person record also carries
the lawful basis, a review date and checks status. Contingent and retained are a select, not a separate
design; the executive search blueprint covers staged retained fees.

## Design choices

- **Role and submission are custom objects.**
- **Person type is a multi-select**, so someone can be a candidate and a client contact.
- **Placement pipeline on submission**: sourced, screened, submitted, interviewing, offer, offer accepted, placed, rejected.
- **Client development pipeline on deal** ending at terms signed.
- **Fee on the submission** with agreed salary, fee amount and invoice status. Forecast from role fee estimate.
- **Rejection reason is a select** and required on the rejected stage.
- **No real company names or data.**

## Objects

| Object | Native | Purpose |
|---|---|---|
| Company | yes | The client, with terms status and default fee |
| Person | yes | A candidate, client contact, referee or referrer, by person type |
| Deal | yes | The client relationship and its terms |
| Role | custom | One vacancy we have been asked to fill |
| Submission | custom | One candidate on one role, with its placement stage and fee |

## Pipelines

- **Client development** (deal): target, conversation, terms discussed, terms sent, terms signed, not won.
- **Placement** (submission): sourced, screened, submitted, interviewing, offer, offer accepted, placed, rejected.

## Decisions

See `decisions` in `design.yaml`: candidates as people, delivery on its own objects, fee on the
submission, contingent and retained together, retention, the custom-object fallback, and data not to
store.

## Sensitive data

Candidate data is personal data under UK GDPR and similar laws. Record the lawful basis and a review
date. Do not store protected-characteristic or diversity data, health data, criminal record detail or
copies of identity documents. Store right-to-work status only. Desired salary is personal data and
should be visible to consultants only. Candidates have deletion and access rights, so keep a documented
process outside the CRM.

## Plan-dependent features

- **HubSpot:** custom objects (Role, Submission) and pipelines on them may need a higher tier, and custom-object limits may apply. Fallback: the `custom_objects_plan` decision. Model each submission as a deal in a placement pipeline.
- **Attio:** the number of custom objects may be limited on lower plans. Fallback: build Submission first and hold role fields on the deal.
- **Salesforce:** custom objects and field-level security depend on edition and permission setup. Fallback: use Opportunity for submissions with a record type.
- Field-level visibility for salary data may be plan-dependent. Fallback: keep salary in the applicant tracking system.
- A high-volume candidate database may need a plan with enough contact records.

Exact tiers: see hubspot/plan-requirements.md once generated.
