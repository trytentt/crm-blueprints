# Wholesale and ecommerce brand, B2B

## Who it is for

A product brand that sells wholesale to retailers as well as, often, direct to consumers online. Typical team: a founder or head of wholesale, a few field reps with territories, and customer service or an ops person who processes orders. A wholesale portal or ecommerce platform usually takes orders.

## The sales motion

1. Reps and the brand find retailers that fit the range, through trade shows, outreach, showroom visits and inbound enquiries.
2. The buyer receives a line sheet with wholesale prices, opening minimums and terms, and may see samples.
3. Terms and the opening order are agreed. The retailer returns an account application and, for credit, trade references.
4. The first order opens the account. After that the value is in the reorder: seasonal orders placed through the portal, a rep or email.
5. Reps watch which retailers have gone quiet and which have only ever ordered once.

## Design reasoning

A wholesale brand grows by landing the right retailers and then getting them to reorder every season. So the sales pipeline is short and ends when the account opens, and the longer-lived record is the order history on each retailer. Territories matter because reps are paid and judged by area. The portal or ecommerce platform stays the source of truth for orders; the CRM keeps headers so reps can see who is ordering and who is not. This is written from general knowledge of how brands sell wholesale and should be checked in discovery.

## Design choices

- **Territory is an object.** Territories change rep and carry targets, and retailers belong to one.
- **Wholesale order is its own object with a status pipeline** (principle 8). The deal ends when the account opens. Every later order, first or repeat, is an order record, so reorder rate can be reported.
- **Reorders are not deals.** A deal is created only for expansion, such as a new range.
- **Reorder cycle and last order date on Company** drive the nudge and lapse automations. A one-order retailer view finds accounts that never reordered.
- **Seasonal fields.** Buying season and order season are selects, because wholesale demand follows collections.

## Objects

| Object | Native | Purpose |
|---|---|---|
| Company | yes | The retailer, with type, terms and order history fields |
| Person | yes | Buyer, owner, merchandiser, accounts payable |
| Deal | yes | Winning a new retailer account |
| Territory | custom | A sales area with a rep and a target |
| Wholesale order | custom | One retailer order from placement to payment |

## Pipelines

- **Retailer acquisition** (deal): identified, contacted, line sheet sent, range review, terms discussion, account setup, account opened, closed lost.
- **Order status** (wholesale order): placed, confirmed, picking, shipped, delivered and paid, cancelled.

## Decisions

See `decisions` in `design.yaml`. They cover the choices above, what to check on the client's plan before the build, and what to do if it falls short.

## Plan-dependent features

Do not assume these are on every plan. Confirm on the client's account before the build.

- **Attio:** the Territory and Wholesale order objects may hit a limit on the number of objects on lower plans. Fallback: keep orders in the portal, put last order date, order count and reorder cycle on the company, and make territory a select field (see `custom_objects_plan`).
- **HubSpot:** custom objects (Territory and Wholesale order objects) may need a higher tier, and so may multiple deal pipelines, required properties per stage and workflows. Fallback: keep orders in the portal, put last order date, order count and reorder cycle on the company, and make territory a select field (see `custom_objects_plan`).
- **Salesforce:** custom objects and record types are available in the main editions, but limits vary by edition. Check the object count and any path or flow limits. Fallback: keep orders in the portal, put last order date, order count and reorder cycle on the company, and make territory a select field (see `custom_objects_plan`).

Exact tiers: see hubspot/plan-requirements.md once generated.
