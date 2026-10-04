# Construction and trades

## Who it is for

A contractor or specialist trade (mechanical, electrical, groundworks, fit-out, maintenance) that sells
to main contractors, developers, housing providers, public bodies and commercial clients. An estimator or
two, a bid manager or director, and project managers. Domestic work for homeowners is out of scope.

## The sales motion

1. Work arrives as an invitation to tender, a framework call-off, a negotiated quote or a repeat client
   asking for another job.
2. The team makes a go or no-go decision. Bids cost estimating time, so many are declined.
3. An estimator visits the site or reviews drawings, then prices the job. Several revisions are common.
4. The bid goes in by the deadline. The client's quantity surveyor, project manager or procurement team
   ask for clarifications, a lower price or a revised programme.
5. A preferred bidder is told. A contract, subcontract or order follows.
6. A project manager runs the job: mobilisation, work on site, snagging, practical completion, then a
   defects period during which the client holds retention.

## Design choices

- **Tender and estimate pipeline on Deal.** Six open stages, with a go or no-go gate before estimating
  so effort is not spent on bids the firm would not take.
- **Project is its own object with its own pipeline** (principle 8). Delivery has a different owner,
  months of activity, retention and a final margin. Its pipeline runs from pre-start to closed out.
- **Site is an object.** A client has many sites, and a site is revisited. Access notes live there.
- **Estimates are records.** Each priced revision keeps its margin and status, so the deal amount is just
  the latest issued price.
- **Selects for reporting.** Procurement route, work type, contract form, lost reason and cancellation
  reason are selects. Estimated margin on the deal and final margin on the project can be compared.
- **Project stages carry 100 per cent.** The sale is already won, so probability is not a forecast there.
- **Supplier approval on Company.** Many clients will not accept a bid until the supplier is approved.

## Objects

| Object | Native | Purpose |
|---|---|---|
| Company | yes | Client, main contractor or partner |
| Person | yes | Client contact, quantity surveyor, designer, site contact |
| Deal | yes | One tender or quote |
| Site | custom | A place where work is done |
| Project | custom | One awarded job |
| Estimate | custom | One priced revision of a bid |

## Pipelines

- **Tender and estimate** (deal): opportunity, go or no-go, estimating, bid submitted, clarification,
  preferred bidder, awarded, closed lost.
- **Project delivery** (project): pre-start, mobilising, on site, snagging, defects period, closed out,
  cancelled.

## Design reasoning

Contractors sell by competing on price and programme, and the buying group is a mix of commercial and
technical people with a formal process, so the sales pipeline is built around the tender: a deadline, a
bid decision, estimating effort, then clarification. Winning starts a long delivery phase run by different
people, so project, site and estimate are separate objects and the deal stops at award. The project
pipeline matters because money arrives late (retention is held until defects are cleared) and a CRM that
forgets the job after award misses repeat work and retention release. This reasoning is from general
knowledge of how construction firms bid and deliver, not cited sources, and should be checked in discovery.

## Decisions

See `decisions` in `design.yaml`. In short: delivery on a project object, estimates as records, domestic
customers out of scope, a fallback if custom objects are unavailable, and tender portals kept outside the CRM.

## Plan-dependent features

- **Custom objects** (site, project, estimate). Attio limits the number of objects on some plans, and
  HubSpot may need a higher tier for custom objects. Fallback: the `custom_objects_plan` decision, the
  project as a second deal pipeline with project fields on the deal.
- **A pipeline on a custom object** (project delivery). Fallback: the same second deal pipeline.
- **Several pipelines, required fields per stage and automations.** The number of pipelines and the
  workflow features available may depend on plan tier. Fallback: record gates and automations as manual
  steps and checks in the build sheet.

Exact tiers: see hubspot/plan-requirements.md once generated.
