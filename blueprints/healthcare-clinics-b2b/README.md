# Healthcare clinics, B2B

## Who it is for

A private clinic or health-services provider that sells to organisations only: employers buying
occupational health or workplace health services, insurers and intermediaries, and referral partners such
as brokers or other providers. A small business development team and account managers.

It is not for patient management, bookings or clinical records.

## Sensitive data rules

**This CRM stores no patient or health data. Not one field, note, email or call may contain it.**

- Health information is special category data under UK GDPR. It belongs in the clinical system.
- A patient is never a Person record. Person records are business contacts at employers, insurers and
  partners.
- Counts such as covered headcount and referrals last quarter are aggregate numbers supplied by the
  organisation. They are never a list of named people.
- Free-text fields are kept to a minimum. Where one exists, its description says not to enter personal
  information.
- Do not sync clinical mailboxes or shared inboxes that receive patient emails. Switch off email body
  capture and call recording or transcription on any inbox or line that may carry patient detail.
- Restrict access to commercial staff. Do not put web forms on the CRM that ask for health detail.
- A data processing agreement is a gate: a service contract cannot go active without one.
- Referral fees between healthcare providers can be restricted. Anything other than "no fee" goes to
  legal and the clinical lead first.

Ask the client's data protection lead to review the design before the build.

## The sales motion

1. A prospect (HR lead, benefits manager or health and safety lead) is found by outbound work, an event,
   a broker or a referral partner, or enquires.
2. Discovery establishes sites, headcount covered and services wanted. The finance lead and procurement
   join at pricing, and an insurer or broker may sit between the clinic and the employer.
3. A proposal sets out services and a pricing model (per appointment, per employee per month, retainer).
4. The buyer runs a data protection and clinical governance review. A short pilot is common.
5. A contract is signed. The account manager runs the service, holds regular service reviews and opens a
   renewal about 90 days before the term ends.
6. In parallel the clinic builds referral partnerships, each with governance checks and an agreement.

## Design choices

- **Three pipelines.** Employer and insurer contracts (deal), contract renewals (deal) and referral
  partners (on the referral agreement object).
- **Service contract is the delivery object** (principle 8). It holds term, pricing basis, data
  processing agreement and renewal date. The deal ends at closed won.
- **Governance is a stage.** Governance review and pilot are explicit stages because that is where
  these deals stall.
- **Referral partners are not deals.** A partnership has no sale value but has governance checks.
- **Services are a catalogue object** linked to deals and contracts, so demand and revenue by service can
  be reported.
- **Selects for reporting.** Account type, sector, headcount band, pricing model, service interest
  and lost reason are selects.

## Objects

| Object | Native | Purpose |
|---|---|---|
| Company | yes | Employer, insurer, broker or partner organisation |
| Person | yes | Business contact only, never a patient |
| Deal | yes | One contract sale or renewal |
| Service | custom | A service line in the catalogue |
| Service contract | custom | The agreement with one customer |
| Referral agreement | custom | The arrangement with one referral partner |

## Pipelines

- **Employer and insurer contracts** (deal): qualified, discovery, proposal, governance review, pilot,
  contract out, closed won, closed lost.
- **Contract renewals** (deal): upcoming, review meeting, terms proposed, awaiting signature, renewed,
  not renewed.
- **Referral partners** (referral agreement): identified, intro meeting, governance check, agreement sent,
  active, declined.

## Design reasoning

Clinics selling to businesses look like any other contract service seller: the buyer is an HR, benefits or
safety lead, the sale is a recurring contract and the account is reviewed regularly. What differs is risk.
Buyers want assurance on data protection and clinical governance before they commit, so governance and
pilot are first-class stages and a signed data processing agreement gates start of service. Brokers and
insurers introduce a large share of employer work, so partners get their own pipeline and deals credit the
source partner. The strict rule of no patient data keeps the CRM out of the clinical records regime, and
the design enforces it by modelling only organisations, business contacts, contracts and aggregate counts.
This reasoning is from general knowledge of how occupational health and similar providers sell, not cited
sources, and should be checked in discovery.

## Decisions

See `decisions` in `design.yaml`. In short: no patient data, delivery on a service contract, a separate
referral partner pipeline, referral fees reviewed by legal, access restricted to commercial staff, and a
fallback if custom objects are unavailable.

## Plan-dependent features

- **Custom objects** (service, service contract, referral agreement). Attio limits the number of objects
  on some plans, and HubSpot may need a higher tier for custom objects. Fallback: the
  `custom_objects_plan` decision, the referral partners as a deal pipeline and contract fields on the company.
- **A pipeline on a custom object** (referral partners). Fallback: a deal pipeline for partners.
- **Field and record permissions.** Restricting who sees records or fields may need a higher tier on some
  platforms. If it is unavailable, restrict by keeping the CRM to commercial staff and record it in the
  client notes.
- **Several pipelines, required fields per stage and automations.** These may depend on plan tier.
  Fallback: record gates and automations as manual steps and checks in the build sheet.

Exact tiers: see hubspot/plan-requirements.md once generated.
