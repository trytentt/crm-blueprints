# Manual steps: Agency, marketing and creative (hubspot)

Generated from `design.yaml`. Do not edit by hand. The HubSpot API cannot do any of this.
Sources: https://developers.hubspot.com/docs/api-reference/latest/crm/pipelines/guide.md, https://knowledge.hubspot.com/records/create-and-manage-saved-views, https://knowledge.hubspot.com/workflows/create-workflows, `platforms/hubspot/reference/api-coverage.md`.

## Before and during the build

### 1. Create a service key and test in a developer test account first

- [ ] Where: Development > Keys > Service keys > Create service key (scopes in platforms/hubspot/reference/auth-and-setup.md)
- Why it is manual: Keys are made in the account by a super admin. A developer test account carries a 90-day Enterprise trial, so it can test custom objects before the client account is touched.
- Done when: `GET /crm/properties/2026-09/contacts` returns 200 with the key.

### 2. Confirm the account is Enterprise before creating custom objects

- [ ] Where: Settings > Account Management > Account defaults, and GET /crm/limits/2026-09/custom-object-types
- Why it is manual: Custom objects need Enterprise and there is no workaround on a lower tier. A client is typically limited to 10 definitions (OQ-3); this blueprint creates 1.
- Done when: the tier is written in the client notes and the limits call allows 1 custom object(s) (Engagement).

## Required fields on standard objects

### 3. Make Company Name required

- [ ] Where: Settings > Data Management > Objects > Companies > Properties tab > Name, or a workflow that flags it when empty
- Why it is manual: HubSpot has no API setting for required properties on standard objects (OQ-9).
- Done when: a company record cannot be saved, or is flagged, when Name is empty.

### 4. Make Person Last name required

- [ ] Where: Settings > Data Management > Objects > Contacts > Properties tab > Last name, or a workflow that flags it when empty
- Why it is manual: HubSpot has no API setting for required properties on standard objects (OQ-9).
- Done when: a person record cannot be saved, or is flagged, when Last name is empty.

### 5. Make Deal Name required

- [ ] Where: Settings > Data Management > Objects > Deals > Properties tab > Name, or a workflow that flags it when empty
- Why it is manual: HubSpot has no API setting for required properties on standard objects (OQ-9).
- Done when: a deal record cannot be saved, or is flagged, when Name is empty.

## Pipelines

### 6. Check closed stages of Delivery

- [ ] Where: Settings > Data Management > Objects > Engagements > Pipelines tab > Delivery
- Why it is manual: HubSpot has open or closed on custom object stages, not won or lost, and no probability (the design's probabilities are not sent). The API key for closed is unconfirmed (OQ-1).
- Done when: closed stages (Completed, Terminated) show as Closed. Set them by hand if the read-back says otherwise.

## Stage gates and lost reasons

### 7. Require Next step date to enter Lead (New business)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New business > stage row for Lead > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Lead asks for Next step date.

### 8. Require Next step date, Budget range to enter Discovery (New business)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New business > stage row for Discovery > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Discovery asks for Next step date, Budget range.

### 9. Require Brief received, Service lines, Engagement type to enter Brief and scope (New business)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New business > stage row for Brief and scope > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Brief and scope asks for Brief received, Service lines, Engagement type.

### 10. Require Amount, Decision date, Competitive pitch to enter Proposal sent (New business)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New business > stage row for Proposal sent > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Proposal sent asks for Amount, Decision date, Competitive pitch.

### 11. Require Decision date, Next step date to enter Pitch or review (New business)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New business > stage row for Pitch or review > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Pitch or review asks for Decision date, Next step date.

### 12. Require Amount, Close date to enter Negotiation (New business)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New business > stage row for Negotiation > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Negotiation asks for Amount, Close date.

### 13. Require Amount, Close date, Engagement type to enter Closed won (New business)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New business > stage row for Closed won > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Closed won asks for Amount, Close date, Engagement type.

### 14. Require Lost reason to enter Closed lost (New business)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New business > stage row for Closed lost > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Closed lost asks for Lost reason.

### 15. Require Renewal type to enter Upcoming (Retainer renewals)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Retainer renewals > stage row for Upcoming > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Upcoming asks for Renewal type.

### 16. Require Renewal risk, Next step date to enter Review booked (Retainer renewals)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Retainer renewals > stage row for Review booked > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Review booked asks for Renewal risk, Next step date.

### 17. Require Amount to enter Proposal sent (Retainer renewals)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Retainer renewals > stage row for Proposal sent > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Proposal sent asks for Amount.

### 18. Require Amount, Close date to enter Negotiation (Retainer renewals)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Retainer renewals > stage row for Negotiation > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Negotiation asks for Amount, Close date.

### 19. Require Amount, Close date to enter Awaiting signature (Retainer renewals)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Retainer renewals > stage row for Awaiting signature > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Awaiting signature asks for Amount, Close date.

### 20. Require Amount, Close date to enter Renewed (Retainer renewals)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Retainer renewals > stage row for Renewed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Renewed asks for Amount, Close date.

### 21. Require Lost reason to enter Not renewed (Retainer renewals)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Retainer renewals > stage row for Not renewed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Not renewed asks for Lost reason.

### 22. Require Account lead, Delivery lead to enter Onboarding (Delivery)

- [ ] Where: Settings > Data Management > Objects > Engagements > Pipelines tab > Delivery > stage row for Onboarding > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test engagement into Onboarding asks for Account lead, Delivery lead.

### 23. Require Access received, Scope summary to enter Kickoff done (Delivery)

- [ ] Where: Settings > Data Management > Objects > Engagements > Pipelines tab > Delivery > stage row for Kickoff done > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test engagement into Kickoff done asks for Access received, Scope summary.

### 24. Require Next review date to enter First deliverables (Delivery)

- [ ] Where: Settings > Data Management > Objects > Engagements > Pipelines tab > Delivery > stage row for First deliverables > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test engagement into First deliverables asks for Next review date.

### 25. Require Health, Next review date to enter Steady state (Delivery)

- [ ] Where: Settings > Data Management > Objects > Engagements > Pipelines tab > Delivery > stage row for Steady state > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test engagement into Steady state asks for Health, Next review date.

### 26. Require Health, Next review date to enter At risk (Delivery)

- [ ] Where: Settings > Data Management > Objects > Engagements > Pipelines tab > Delivery > stage row for At risk > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test engagement into At risk asks for Health, Next review date.

### 27. Require End date to enter Wrapping up (Delivery)

- [ ] Where: Settings > Data Management > Objects > Engagements > Pipelines tab > Delivery > stage row for Wrapping up > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test engagement into Wrapping up asks for End date.

### 28. Require End date to enter Completed (Delivery)

- [ ] Where: Settings > Data Management > Objects > Engagements > Pipelines tab > Delivery > stage row for Completed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test engagement into Completed asks for End date.

### 29. Require End reason to enter Terminated (Delivery)

- [ ] Where: Settings > Data Management > Objects > Engagements > Pipelines tab > Delivery > stage row for Terminated > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test engagement into Terminated asks for End reason.

## Decisions where the HubSpot mapping is lossy

### 30. Check the association limit for engagement_company

- [ ] Where: Settings > Data Management > Objects > Engagements > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 31. Check the association limit for deal_engagement

- [ ] Where: Settings > Data Management > Objects > Deals > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 32. Accept that currency fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property carries no currency code: the symbol is a display choice.
- Done when: the client has agreed in the client notes. Fields: engagement.monthly_fee, engagement.project_fee.

### 33. Accept that user fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property holds the HubSpot owner ID, so only users of the account can be chosen.
- Done when: the client has agreed in the client notes. Fields: engagement.account_lead, engagement.delivery_lead.

## Workflows

### 34. Workflow: Create engagement on closed won

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A deal in the new business pipeline moves to closed won.'; action 'Create an engagement from the deal's engagement type, amount, service lines and close date, link it to the deal and company, set it to onboarding, and set the company's client status to active client.'

### 35. Workflow: Notify delivery team

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'An engagement is created.'; action 'Notify the delivery lead and account lead with the scope summary and the signed agreement link.'

### 36. Workflow: Open renewal deal

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A retainer engagement has an end date 90 days away and is not terminated.'; action 'Create a deal in the retainer renewals pipeline at upcoming, linked to the engagement.'

### 37. Workflow: Flag red health

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'An engagement's health is set to red.'; action 'Move it to at risk and notify the account lead and the head of delivery.'

### 38. Workflow: Flag stalled deals

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'An open deal has no next step date, or the date is more than 7 days past.'; action 'Notify the deal owner and add the deal to the stalled deals view.'

### 39. Workflow: Mark past client

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A company's last active engagement moves to completed or terminated and it has no open engagement.'; action 'Set the company's client status to past client.'

## Saved views

### 40. Saved view: My open deals

- [ ] Where: CRM > Deals > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view My open deals shows on the Deals index with filter 'Owner is me and stage is open.' and sort 'Close date, soonest first.'.

### 41. Saved view: Stalled deals

- [ ] Where: CRM > Deals > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Stalled deals shows on the Deals index with filter 'Stage is open and next step date is empty or in the past.' and sort 'Next step date, oldest first.'.

### 42. Saved view: Pitches deciding soon

- [ ] Where: CRM > Deals > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Pitches deciding soon shows on the Deals index with filter 'Pipeline is new business, stage is open and decision date is within 14 days.' and sort 'Decision date, soonest first.'.

### 43. Saved view: Active engagements

- [ ] Where: CRM > Engagements > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Active engagements shows on the Engagements index with filter 'Stage is open.' and sort 'Health, red first, then end date.'.

### 44. Saved view: Retainers ending in 90 days

- [ ] Where: CRM > Engagements > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Retainers ending in 90 days shows on the Engagements index with filter 'Engagement type is retainer, stage is open and end date is within 90 days.' and sort 'End date, soonest first.'.

### 45. Saved view: Reviews overdue

- [ ] Where: CRM > Engagements > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Reviews overdue shows on the Engagements index with filter 'Stage is open and next review date is empty or in the past.' and sort 'Next review date, oldest first.'.

## Permissions

### 46. Set roles and access

- [ ] Where: Settings > Users & Teams (menu name not verified against a page in the research)
- Why it is manual: No permission-set API was found. Only pipeline stage edit permissions have one, and this blueprint does not use it.
- Done when: a non-admin test user sees and edits what their role needs and nothing more.
