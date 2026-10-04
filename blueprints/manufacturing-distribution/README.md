# Manufacturing and distribution, B2B

## Who it is for

A manufacturer or distributor that sells products to trade customers: contractors, OEMs, resellers and end users. Typical team: a sales manager, field reps, an inside sales team that handles quotes, and an account manager for the biggest customers. An ERP usually holds stock, prices and invoices.

## The sales motion

1. A new account is found through a rep visit, a trade enquiry, a tender or a referral.
2. The rep confirms the specification, expected volumes and any sample or trial the buyer needs. Buyers include purchasing, an engineer who specifies, and an economic buyer.
3. A quote is priced against stock and lead time, approved if it breaks margin or credit rules, and sent. The buyer often asks several suppliers, so speed to quote matters.
4. The first purchase order wins the account. After that most business is repeat: reorders, call-offs and further quotes, handled by inside sales and an account manager.
5. Accounts are tiered by spend. Key accounts get scheduled reviews, and accounts that stop reordering are chased.

## Design reasoning

Trade sellers win on speed, availability and relationship, and most revenue repeats. So the design separates the rare event (winning a new account) from the frequent one (quoting and reordering), and gives the frequent one its own object and measures: speed to quote, quote-to-order conversion and days since last order. Account tiers decide how much attention an account gets. This is written from general knowledge of how trade manufacturers and distributors sell and should be checked in discovery with the client.

## Design choices

- **Quote is its own object with its own pipeline.** Distributors answer many RFQs a week and most come from existing accounts, so they are not deals. The deal pipeline is for new accounts and projects.
- **Order is its own object** (principle 8). It carries dates and status for delivery and feeds the last order date, so reorder chasing works. The ERP stays the system of record.
- **Account tier, spend band and expected reorder interval on Company.** These are selects and numbers so reports and the reorder view work without free text.
- **Six open stages in new accounts, six in RFQ handling.** The RFQ pipeline has an approval stage for margin and credit rules.
- **Required fields gate stages.** For example, a quote cannot be issued until the specification is confirmed.

## Objects

| Object | Native | Purpose |
|---|---|---|
| Company | yes | Customer or prospect, with tier and reorder fields |
| Person | yes | Purchasing, specifier, economic buyer, end user |
| Deal | yes | A new-account or project opportunity |
| Quote | custom | One RFQ and the quote sent in reply |
| Order | custom | One accepted customer order and its delivery |

## Pipelines

- **New accounts** (deal): identified, first contact, needs confirmed, sample or trial, quote issued, terms agreed, closed won, closed lost.
- **RFQ handling** (quote): received, qualified, pricing, approval, sent, follow-up, accepted, declined.

## Decisions

See `decisions` in `design.yaml`. They cover the choices above, what to check on the client's plan before the build, and what to do if it falls short.

## Plan-dependent features

Do not assume these are on every plan. Confirm on the client's account before the build.

- **Attio:** the Quote and Order objects may hit a limit on the number of objects on lower plans. Fallback: record quotes as deals in a second pipeline, keep orders in the ERP, and put last order date and reorder interval on the company (see the `custom_objects_plan` decision).
- **HubSpot:** custom objects (Quote and Order objects) may need a higher tier, and so may multiple deal pipelines, required properties per stage and workflows. Fallback: record quotes as deals in a second pipeline, keep orders in the ERP, and put last order date and reorder interval on the company (see the `custom_objects_plan` decision).
- **Salesforce:** custom objects and record types are available in the main editions, but limits vary by edition. Check the object count and any path or flow limits. Fallback: record quotes as deals in a second pipeline, keep orders in the ERP, and put last order date and reorder interval on the company (see the `custom_objects_plan` decision).

Salesforce already has standard Quote and Order objects, so the overrides name the custom objects `Trade_Quote__c` and `Trade_Order__c` to avoid a clash.

Exact tiers: see hubspot/plan-requirements.md once generated.
