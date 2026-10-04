# B2B SaaS, sales-led

## Who it is for

A software company with a sales team that sells annual (sometimes multi-year) contracts to other
businesses. Typical deal size is a few thousand to a few hundred thousand a year. Usually a founder
or head of sales, a handful of account executives, and a customer success lead.

## The sales motion

1. A lead arrives from inbound, outbound, a partner, an event or a referral.
2. An account executive qualifies it and runs discovery. The buying group is usually an economic
   buyer, a champion, a technical evaluator and sometimes a blocker (security, procurement or legal).
3. The buyer sees a tailored demo, then a technical validation or trial.
4. A proposal, then negotiation and security review, then a contract for signature.
5. On signature, customer success runs onboarding. About 90 days before the term ends, a renewal
   deal opens. Upsell and cross-sell run in the same pipeline.

## Design choices

- **Two deal pipelines, one Deal object.** New business and renewals/expansion have different
  stages, owners and win rates, but finance wants one revenue report. Both are pipelines on Deal.
- **Subscription is its own object.** A contract has a term, ARR and a renewal date that outlive
  the deal that created it. Renewal deals link back to it.
- **Onboarding is its own object** (principle 8). Sales ends at closed won. Delivery has a different
  owner and its own dates.
- **Seven open stages in new business.** Each has an exit criterion written as "Entered when", so a
  stage is a fact about the buyer, not a feeling.
- **Required fields gate the stages.** For example, proposal needs a confirmed budget, an amount and
  a term. Lost always needs a lost reason from a fixed list.
- **Buying role on Person.** It makes single-threaded deals visible.
- **No real company names or data.** The example subscription name is generic.

## Objects

| Object | Native | Purpose |
|---|---|---|
| Company | yes | The customer or prospect |
| Person | yes | A buyer, user or champion |
| Deal | yes | One sales or renewal opportunity |
| Subscription | custom | One customer contract and its renewal date |
| Onboarding | custom | Getting a new subscription live |

## Pipelines

- **New business**: qualified, discovery, solution fit, technical validation, proposal, negotiation,
  contract out, closed won, closed lost.
- **Renewals and expansion**: upcoming, outreach, proposal sent, negotiation, awaiting signature,
  renewed, churned.

## Decisions

See `decisions` in `design.yaml`. In short: renewals as deals on the same object, onboarding on its
own object, a custom-object fallback if the plan does not allow them, one subscription per contract,
and one product until reporting needs more.

## Plan-dependent features

To be completed from the platform research (minimum plan, fallback, source) once it is done.

- **Attio:** TODO
- **HubSpot:** TODO. Custom objects (Subscription, Onboarding) are expected to need a higher tier. Fallback: see the `custom_objects_plan` decision.
- **Salesforce:** TODO
