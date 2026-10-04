# Investor, VC and angel deal flow

## Who it is for

A venture fund, angel syndicate or individual investor. Typical team: a few partners and associates, an operations or platform person, and a fund administrator outside the CRM. The CRM is the shared record of who the team knows and which companies are being looked at.

## The sales motion

1. Deals come from founders, warm introductions, co-investors, accelerators, events and the team's own outreach.
2. Most are screened out quickly against stage, sector, geography and cheque size. A few get a founder meeting and a deeper look.
3. A deal lead presents to the partners. If they agree, a term sheet is issued, due diligence runs, and the investment committee approves.
4. On closing, the company joins the portfolio. The team tracks health, investor updates, follow-on reserves and eventually an exit or write-off.
5. Co-investors matter at every step: who leads, who follows, and who the team likes to back with.

## Design reasoning

Investor CRMs are relationship systems first: the value is knowing who introduced a deal, who else is investing, and how well the team knows the founders. The deal funnel is steep, so the design makes passing cheap and recording the reason mandatory. After investing, the work changes from selection to support, so the portfolio gets its own object and pipeline. Financial records stay with the fund administrator. This is written from general knowledge of venture and angel investing and should be checked in discovery.

## Design choices

- **Deal flow is a funnel with eight open stages**, the maximum, because the committee and diligence steps are separate gates. Early stages carry low probabilities.
- **Portfolio investment is its own object** (principle 8). The investment lasts for years, with its own owner, health, reserves and exit.
- **Co-investors are companies**, linked many-to-many to deals and investments, with their partners as people.
- **Pass reason is a select** so the team can learn from passes. Passed companies can be revisited.
- **Introducers are people** linked to deals, so the team can thank and measure them.
- **Company stands for startups, funds and LPs alike**, told apart by organisation type.

## Objects

| Object | Native | Purpose |
|---|---|---|
| Company | yes | Startup, co-investor, limited partner, accelerator |
| Person | yes | Founder, introducer, co-investor partner |
| Deal | yes | A startup being evaluated for investment |
| Portfolio investment | custom | An investment made, with ownership, health and exit |

## Pipelines

- **Deal flow** (deal): sourced, screening, first meeting, deep dive, partner meeting, term sheet, due diligence, investment committee, invested, passed.
- **Portfolio outcome** (portfolio investment): active, follow-on review, exit preparation, exit process, exited, written off.

## Decisions

See `decisions` in `design.yaml`. They cover the choices above, what to check on the client's plan before the build, and what to do if it falls short.

## Plan-dependent features

Do not assume these are on every plan. Confirm on the client's account before the build.

- **Attio:** the Portfolio investment object may hit a limit on the number of objects on lower plans. Fallback: use a second deal pipeline for the portfolio, with ownership and valuation as deal properties (see `custom_objects_plan`).
- **HubSpot:** custom objects (Portfolio investment object) may need a higher tier, and so may multiple deal pipelines, required properties per stage and workflows. Fallback: use a second deal pipeline for the portfolio, with ownership and valuation as deal properties (see `custom_objects_plan`).
- **Salesforce:** custom objects and record types are available in the main editions, but limits vary by edition. Check the object count and any path or flow limits. Fallback: use a second deal pipeline for the portfolio, with ownership and valuation as deal properties (see `custom_objects_plan`).

Exact tiers: see hubspot/plan-requirements.md once generated.
