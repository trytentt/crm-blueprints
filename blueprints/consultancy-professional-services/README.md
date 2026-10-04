# Consultancy and professional services

## Who it is for

A consultancy, law firm, accountancy or similar firm where partners or directors sell and teams deliver
chargeable work. Typically ten to several hundred staff, a risk or compliance function, and a practice
management or billing system that is the official record of time and invoices.

## The sales motion

1. An enquiry arrives by referral, a professional introducer, inbound or an existing client.
2. A partner decides whether the work is in scope and there is capacity.
3. The parties go to risk or compliance for a conflict check. Nothing is proposed or advised before it clears.
4. A scoped proposal names the billing model: hourly, fixed, capped, retainer, success fee or a mix.
5. Terms are agreed and the engagement letter is signed. Work does not start before it is. Identity and anti-money-laundering checks are completed where the work requires them.
6. The matter is delivered, billed and closed. Follow-on work comes through the same pipeline.

## Design reasoning

In regulated professional services the order matters. Conflict clearance and a signed engagement letter
come before work and often before advice, so they are gates, not tasks. The conflict check is its own
object because compliance needs an audit trail of who was checked, the result and who cleared it, and a
deal field alone loses that. The deal carries a copy of the latest result so stage rules can use it.
The matter is the delivery object: it has the responsible partner, manager, billing model and dates,
and it ends in closed or withdrawn. The billing model is a select on both deal and matter because
margin risk differs sharply between fixed fee and hourly. Time, invoices and write-offs stay in the
billing system.

## Design choices

- **Matter and conflict check are custom objects.**
- **Conflict check is a named stage** before the proposal, and the proposal stage requires a result.
- **Engagement letter out** is the last open stage and requires a cleared result.
- **Matter delivery pipeline** with a cleared-to-start stage requiring the signed-letter date and AML status.
- **Billing model, fee estimate and budget hours** on the matter. Billing frequency is a select.
- **No real company names or data.**

## Objects

| Object | Native | Purpose |
|---|---|---|
| Company | yes | The client, prospect, referrer or related party |
| Person | yes | An instructing contact, sponsor or finance contact |
| Deal | yes | One opportunity to win a piece of work |
| Matter | custom | One piece of client work under one engagement letter |
| Conflict check | custom | The audit record of one conflict check |

## Pipelines

- **New work**: enquiry, qualified, conflict check, proposal, proposal sent, terms agreed, engagement letter out, closed won, closed lost.
- **Matter delivery** (on matter): opening, cleared to start, in progress, awaiting client, final billing, closed, withdrawn.

## Decisions

See `decisions` in `design.yaml`: delivery on matters, the conflict check gate, billing scope, how much
matter detail is allowed, the custom-object fallback, and follow-on work.

## Sensitive data

This blueprint touches regulated and confidential data. Client confidentiality and legal professional
privilege: keep matter names neutral, hold no privileged advice or case facts in the CRM, and restrict
confidential matters by permission and ethical walls. Anti-money-laundering: store check status and risk
rating only, never copies of identity documents. Conflict checks hold party names, which is personal data
when the party is an individual. Confirm all of this with the firm's compliance officer before go-live.
The CRM does not replace the firm's official conflict register unless the firm decides it does.

## Plan-dependent features

- **HubSpot:** custom objects (Matter, Conflict check) and pipelines on them may need a higher tier, and so may record-level permissions for confidential matters. Fallback: the `custom_objects_plan` decision. Hold matters as deals in a delivery pipeline and the conflict result as a select.
- **Attio:** the number of custom objects and permission controls may depend on plan. Fallback: fold Conflict check into a field and note on Deal.
- **Salesforce:** sharing rules and custom object limits depend on edition. Fallback: use record types on Opportunity.
- Automations that block stage moves may need workflow or validation features that are plan-dependent. Fallback: a view of deals past conflict check without a cleared result.

Exact tiers: see hubspot/plan-requirements.md once generated.
