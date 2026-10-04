# Agency, marketing and creative

## Who it is for

A marketing, creative, performance or GTM agency of five to a hundred people, selling monthly retainers
and fixed-scope projects. Usually a founder or partners who sell, an account lead per client, and a
delivery team.

## The sales motion

1. A lead arrives, mostly by referral, content, outbound or a past client returning.
2. Discovery with someone who can name the goal and budget range. A written brief follows.
3. A priced proposal goes to the decision maker, often followed by a pitch or walk-through with several stakeholders. Some are formal competitive pitches.
4. Negotiation of scope, fee and term, then a signed statement of work.
5. Kickoff, access to the client's accounts, first deliverables, then monthly reviews. About 90 days before a retainer ends, a renewal deal opens.

## Design reasoning

Agencies sell time and expertise as scoped work, so the unit of delivery is the engagement, not the
deal. A retainer renews and a project ends, so one engagement object with a type covers both, and
retainers get a renewal pipeline. Delivery has its own pipeline on the engagement because the owners
and dates differ from selling, and because the real risks (lost access, red health, unreviewed scope
creep) show up after the win. The pitch stage matters because agencies often do unpaid work before a
decision, so the competitive-pitch field and decision date let the owner judge pitch cost against win
rate. Hours and invoicing stay in the time tool. Media spend belongs to the client, so the CRM holds
fee only.

## Design choices

- **Engagement is a custom object** with fee, term, notice period, health and named leads.
- **Three pipelines.** New business (deal), retainer renewals (deal), delivery (engagement).
- **Seven open stages in delivery**, including an at-risk stage entered by red health.
- **Required fields gate stages.** Proposal needs an amount, decision date and competitive-pitch flag. Kickoff done needs access received.
- **Service lines as selects**, on the deal as multi-select and on the engagement as the main line.
- **No real company names or data.**

## Objects

| Object | Native | Purpose |
|---|---|---|
| Company | yes | The client or prospect |
| Person | yes | A decision maker, day-to-day lead or finance contact |
| Deal | yes | A new business or renewal opportunity |
| Engagement | custom | One signed retainer or project and its delivery |

## Pipelines

- **New business**: lead, discovery, brief and scope, proposal sent, pitch or review, negotiation, closed won, closed lost.
- **Retainer renewals**: upcoming, review booked, proposal sent, negotiation, awaiting signature, renewed, not renewed.
- **Delivery** (on engagement): onboarding, kickoff done, first deliverables, steady state, at risk, wrapping up, completed, terminated.

## Decisions

See `decisions` in `design.yaml`: delivery on its own object, retainers and projects together, renewals
as deals, where time is tracked, media spend, the custom-object fallback, and pitch policy.

## Sensitive data

Agencies hold client logins and brand assets. Do not store passwords or access tokens in the CRM. Record
only that access was received. Client contact data is business contact data, but keep marketing consent
in view if the agency also markets to those contacts.

## Plan-dependent features

- **HubSpot:** a custom Engagement object and a pipeline on it may need a higher tier. Fallback: the `custom_objects_plan` decision. Model each engagement as a deal in a delivery pipeline.
- **Attio:** custom objects and statuses on them may be limited by plan. Fallback: a list of engagements with a status attribute.
- **Salesforce:** custom object limits depend on edition. Fallback: use Opportunity record types for delivery.
- Automated creation of the engagement and the 90-day renewal deal needs workflow features that may be plan-dependent. Fallback: a weekly view and a manual step.

Exact tiers: see hubspot/plan-requirements.md once generated.
