# Education and training providers, B2B

## Who it is for

A training provider that sells to employers: in-house programmes, bespoke courses, seats on open
courses and sometimes apprenticeship or accredited routes. A small sales team, a course administration
team and trainers. Not for schools, universities or consumer course sellers.

## The sales motion

1. An enquiry arrives from an employer, a returning delegate, a partner or outbound work.
2. A salesperson runs a needs analysis with the learning lead and the budget holder. The line manager of
   the team to be trained often has a say, and procurement joins for larger orders.
3. A written proposal gives programme, format, dates and price. Funding (company budget, levy funds or a
   grant) shapes what paperwork is needed.
4. The buyer reviews it internally, terms are agreed and a booking form or purchase order comes back.
5. Delivery is a cohort. Delegates enrol onto it, pay or are covered by a purchase order, attend and
   complete. Repeat bookings are common once an employer has a supplier it trusts.

## Design choices

- **Two pipelines.** Corporate training is a deal pipeline (five open stages). Delegate enrolment is a
  separate pipeline on the enrolment object (four open stages), because one corporate deal can create
  many enrolments and an open-course place has no deal at all.
- **Programme, cohort, enrolment are their own objects** (principle 8). The programme is what is sold,
  the cohort is a dated run, the enrolment is one person on one run. Delivery has its own owner and dates.
- **Delegates are People.** One human, one record, matched by work email. Their enrolments are their history.
- **Selects for reporting.** Training need, delivery format, funding source, lost reason, payment status
  and withdrawal reason are selects so demand, funding mix and drop-off can be counted.
- **Gates.** A proposal needs format, amount and funding source. Booked needs a purchase order. An
  enrolment cannot be confirmed without a payment status.
- **No learner records.** Attendance, assessment and certificates stay in the learning platform. The CRM
  holds a completion status only.
- **Delivery probabilities.** All probabilities are sales probabilities; cohort capacity is tracked on
  the cohort, not through stage probability.

## Objects

| Object | Native | Purpose |
|---|---|---|
| Company | yes | Employer, public body, partner or funder |
| Person | yes | Buyer, line manager or delegate |
| Deal | yes | One corporate training sale |
| Programme | custom | A course in the catalogue |
| Cohort | custom | A dated run of a programme |
| Enrolment | custom | One delegate's place on a cohort |

## Pipelines

- **Corporate training** (deal): enquiry qualified, needs analysis, proposal sent, stakeholder review,
  terms agreed, booked, closed lost.
- **Delegate enrolment** (enrolment): enquiry, applied, place offered, awaiting payment, enrolled, withdrawn.

## Design reasoning

Training providers sell a consultative service to a buyer who is rarely the person being trained, so the
design separates the buying group (budget holder, learning lead, line manager, procurement) from the
delegates. The commercial result of a corporate sale is a booking, but the operational result is a
cohort with places to fill, so the sale and the run are different objects. Open courses behave like
small retail sales that need a place, a price and payment, which is why enrolments have their own
pipeline instead of one deal per delegate. Funding source and a purchase order are gates because they are
the usual reasons a booked course falls over late. This reasoning comes from general knowledge of how
training businesses work, not from cited sources, and should be checked in discovery.

## Decisions

See `decisions` in `design.yaml`. In short: delivery on its own objects, delegates as people, every
delegate through the enrolment pipeline, a fallback if custom objects are unavailable, no attendance or
assessment data in the CRM, and one team for open and in-house work.

## Data protection

Delegates are personal data. Keep learner results, special needs and any data about under-18s out of
the CRM. If the client trains young people or runs funded courses with eligibility checks, discuss what
may be stored before the build.

## Plan-dependent features

- **Custom objects** (programme, cohort, enrolment). Attio limits the number of objects on some plans,
  and HubSpot may need a higher tier for custom objects. Fallback: the `custom_objects_plan` decision,
  one deal per delegate in an enrolment deal pipeline with cohort details held on the deal.
- **A pipeline on a custom object** (delegate enrolment). Some plans and platforms only allow pipelines on
  deals. Fallback: the same enrolment deal pipeline.
- **Required fields per stage and automations.** These may depend on plan tier or on workflow features.
  Fallback: record them as manual steps and checks in the build sheet.

Exact tiers: see hubspot/plan-requirements.md once generated.
