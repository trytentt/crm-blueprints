# Financial advisers, client households

## Who it is for

An independent financial adviser or small wealth management practice. Typical team: one or more advisers, a paraplanner who drafts reports, administrators, and a compliance lead. Clients are households. A separate planning system and document system usually hold the detailed fact find and evidence.

## The sales motion

1. Most new clients arrive by introduction from existing clients or from professionals such as accountants and solicitors.
2. A free initial meeting explains services and fees. A written proposal follows, and the client signs an agreement and completes identity checks.
3. Advice work starts: a fact find, analysis, a written recommendation checked internally, a meeting, and placing products for the parts the client accepts.
4. Ongoing clients are reviewed on a schedule, often yearly, with circumstances and risk checked again.
5. Fees are usually initial plus ongoing, so the review cycle protects recurring income.

## Design reasoning

Advice firms sell trust and keep clients for years, so the sales pipeline is short and the lasting value is in the household record and the review cycle. Households matter because partners and families are advised together. Personal financial data is sensitive, so the design keeps the CRM light, flags the fields that need restricted access, and leaves detail in specialist systems. The firm's regulatory duties are for its compliance lead. This is written from general knowledge and must be confirmed with the client in discovery.

## Design choices

- **Household is an object.** Advice, fees and reviews are agreed per household. Each human keeps one person record, linked to the household.
- **Three records, three jobs.** The deal wins the client. The advice case delivers advice. The review keeps the relationship going. Each has its own pipeline and owner.
- **Review cycle is built in.** Next review date, review frequency, a review pipeline and automations that open and roll reviews forward.
- **Regulated and sensitive data is flagged.** Fields holding personal financial data, health-related flags or identity status start their description with DATA PROTECTION. They use bands and yes/no values where possible. Detail stays in the planning and document systems.
- **Regulatory wording is general.** This blueprint does not encode rules for any regulator. The firm's compliance lead decides what extra required fields and approval steps to add.

## Objects

| Object | Native | Purpose |
|---|---|---|
| Company | yes | Referrers, employers, product providers |
| Person | yes | Each human, linked to a household |
| Deal | yes | Winning a new client |
| Household | custom | A client unit with service terms and review dates |
| Advice case | custom | One piece of advice from fact find to completion |
| Review | custom | One scheduled review |

## Pipelines

- **New client** (deal): enquiry, initial meeting booked, initial meeting held, fee proposal, agreement out, client won, lost.
- **Advice delivery** (advice case): fact find, analysis, report drafted, report issued, accepted, completed, closed without advice.
- **Review cycle** (review): due, invited, booked, meeting held, review completed, not completed.

## Decisions

See `decisions` in `design.yaml`. They cover the choices above, what to check on the client's plan before the build, and what to do if it falls short.

## Plan-dependent features

Do not assume these are on every plan. Confirm on the client's account before the build.

- **Attio:** the Household, Advice case and Review objects may hit a limit on the number of objects on lower plans. Fallback: use Company as the household and deal pipelines for advice cases and reviews (see `custom_objects_plan`). Field-level or record-level permissions, needed to restrict the DATA PROTECTION fields, may also depend on the plan; the `field_level_access` decision covers the fallback of keeping those fields in the planning system.
- **HubSpot:** custom objects (Household, Advice case and Review objects) may need a higher tier, and so may multiple deal pipelines, required properties per stage and workflows. Fallback: use Company as the household and deal pipelines for advice cases and reviews (see `custom_objects_plan`). Field-level or record-level permissions, needed to restrict the DATA PROTECTION fields, may also depend on the plan; the `field_level_access` decision covers the fallback of keeping those fields in the planning system.
- **Salesforce:** custom objects and record types are available in the main editions, but limits vary by edition. Check the object count and any path or flow limits. Fallback: use Company as the household and deal pipelines for advice cases and reviews (see `custom_objects_plan`). Field-level or record-level permissions, needed to restrict the DATA PROTECTION fields, may also depend on the plan; the `field_level_access` decision covers the fallback of keeping those fields in the planning system.

**Compliance note.** Fields flagged DATA PROTECTION need restricted access, a stated legal basis and a retention rule agreed with the client before go-live. This blueprint does not make regulatory claims.

Exact tiers: see hubspot/plan-requirements.md once generated.
