# Commercial real estate, leasing

## Who it is for

A commercial property agency, a landlord with a portfolio, or a property manager that lets offices, retail and industrial space. Typical team: lettings agents or surveyors, a lease or property manager, and directors who hold landlord relationships.

## The sales motion

1. An occupier enquires, or the firm markets available space for a landlord. A requirement is qualified on size, budget, area and move date.
2. The agent shortlists space and arranges viewings, usually with a decision maker and sometimes the occupier's own agent.
3. An offer leads to heads of terms, which summarise rent, term, breaks and incentives and are not binding until the lease is signed.
4. Tenant referencing and solicitors on both sides follow. Legals often take longest.
5. The lease completes. The firm or a property manager then tracks rent reviews, breaks and expiry, and opens a renewal conversation up to a year ahead.

## Design reasoning

Leasing is a long, relationship-led sale where the same companies appear in different roles, and where the asset (the space) matters as much as the buyer. So the design puts the building and the lease at the centre, uses a role list on Company, and splits the letting from the long-running lease record. Dates are first-class fields because breaks, reviews and expiries drive the next piece of business. This is written from general knowledge of commercial letting and should be checked in discovery, including local legal terms and whether the firm also does investment sales.

## Design choices

- **Property and Lease are objects.** Property holds availability so enquiries can be matched to space. A lease holds rent and dates that outlive the letting deal.
- **Roles are a multi-select on Company** because one company can be landlord, tenant and investor. The role on a given property or lease comes from the relationship (landlord on property, tenant on lease). One person, one record.
- **Letting pipeline on Deal, renewal pipeline on Lease.** Selling and managing are different jobs with different owners.
- **Seven open stages in letting.** Heads of terms, referencing and legals are separate because each can stall for different reasons.
- **Units stay as text on the lease** for the first build (see the `units_as_objects` decision).

## Objects

| Object | Native | Purpose |
|---|---|---|
| Company | yes | Landlord, tenant, occupier looking for space, agent, solicitor |
| Person | yes | Decision maker, property manager, tenant's agent |
| Deal | yes | One letting |
| Property | custom | A building with availability |
| Lease | custom | One signed lease with dates and rent |

## Pipelines

- **Letting** (deal): enquiry, requirement qualified, viewing, offer, heads of terms, referencing, legals, completed, lost.
- **Lease renewal** (lease): upcoming, tenant contacted, terms discussed, renewal agreed, renewed, not renewed.

## Decisions

See `decisions` in `design.yaml`. They cover the choices above, what to check on the client's plan before the build, and what to do if it falls short.

## Plan-dependent features

Do not assume these are on every plan. Confirm on the client's account before the build.

- **Attio:** the Property and Lease objects may hit a limit on the number of objects on lower plans. Fallback: hold the building as fields on the company or deal, and run renewals as a second deal pipeline with lease dates as deal properties (see `custom_objects_plan`).
- **HubSpot:** custom objects (Property and Lease objects) may need a higher tier, and so may multiple deal pipelines, required properties per stage and workflows. Fallback: hold the building as fields on the company or deal, and run renewals as a second deal pipeline with lease dates as deal properties (see `custom_objects_plan`).
- **Salesforce:** custom objects and record types are available in the main editions, but limits vary by edition. Check the object count and any path or flow limits. Fallback: hold the building as fields on the company or deal, and run renewals as a second deal pipeline with lease dates as deal properties (see `custom_objects_plan`).

Exact tiers: see hubspot/plan-requirements.md once generated.
