# Manual steps: B2B SaaS, sales-led (hubspot)

Generated from `design.yaml`. Do not edit by hand. The HubSpot API cannot do any of this.
Sources: https://developers.hubspot.com/docs/api-reference/latest/crm/pipelines/guide.md, https://knowledge.hubspot.com/records/create-and-manage-saved-views, https://knowledge.hubspot.com/workflows/create-workflows, `platforms/hubspot/reference/api-coverage.md`.

## Before and during the build

### 1. Create a service key and test in a developer test account first

- [ ] Where: Development > Keys > Service keys > Create service key (scopes in platforms/hubspot/reference/auth-and-setup.md)
- Why it is manual: Keys are made in the account by a super admin. A developer test account carries a 90-day Enterprise trial, so it can test custom objects before the client account is touched.
- Done when: `GET /crm/properties/2026-09/contacts` returns 200 with the key.

### 2. Confirm the account is Enterprise before creating custom objects

- [ ] Where: Settings > Account Management > Account defaults, and GET /crm/limits/2026-09/custom-object-types
- Why it is manual: Custom objects need Enterprise and there is no workaround on a lower tier. A client is typically limited to 10 definitions (OQ-3); this blueprint creates 2.
- Done when: the tier is written in the client notes and the limits call allows 2 custom object(s) (Subscription, Onboarding).

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

## Stage gates and lost reasons

### 6. Require Next step date to enter Qualified (New business)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New business > stage row for Qualified > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Qualified asks for Next step date.

### 7. Require Next step date to enter Discovery (New business)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New business > stage row for Discovery > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Discovery asks for Next step date.

### 8. Require Pain summary, Next step date to enter Solution fit (New business)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New business > stage row for Solution fit > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Solution fit asks for Pain summary, Next step date.

### 9. Require Decision process, Next step date to enter Technical validation (New business)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New business > stage row for Technical validation > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Technical validation asks for Decision process, Next step date.

### 10. Require Budget confirmed, Amount, Contract term (months) to enter Proposal (New business)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New business > stage row for Proposal > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Proposal asks for Budget confirmed, Amount, Contract term (months).

### 11. Require Amount, Close date, Security review to enter Negotiation (New business)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New business > stage row for Negotiation > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Negotiation asks for Amount, Close date, Security review.

### 12. Require Amount, Close date, Contract term (months) to enter Contract out (New business)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New business > stage row for Contract out > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Contract out asks for Amount, Close date, Contract term (months).

### 13. Require Amount, Close date to enter Closed won (New business)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New business > stage row for Closed won > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Closed won asks for Amount, Close date.

### 14. Require Lost reason to enter Closed lost (New business)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New business > stage row for Closed lost > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Closed lost asks for Lost reason.

### 15. Require Renewal type to enter Upcoming (Renewals and expansion)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Renewals and expansion > stage row for Upcoming > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Upcoming asks for Renewal type.

### 16. Require Renewal risk, Next step date to enter Outreach (Renewals and expansion)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Renewals and expansion > stage row for Outreach > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Outreach asks for Renewal risk, Next step date.

### 17. Require Amount, Contract term (months) to enter Proposal sent (Renewals and expansion)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Renewals and expansion > stage row for Proposal sent > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Proposal sent asks for Amount, Contract term (months).

### 18. Require Amount, Close date to enter Negotiation (Renewals and expansion)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Renewals and expansion > stage row for Negotiation > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Negotiation asks for Amount, Close date.

### 19. Require Amount, Close date, Contract term (months) to enter Awaiting signature (Renewals and expansion)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Renewals and expansion > stage row for Awaiting signature > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Awaiting signature asks for Amount, Close date, Contract term (months).

### 20. Require Amount, Close date to enter Renewed (Renewals and expansion)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Renewals and expansion > stage row for Renewed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Renewed asks for Amount, Close date.

### 21. Require Lost reason to enter Churned (Renewals and expansion)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Renewals and expansion > stage row for Churned > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Churned asks for Lost reason.

## Decisions where the HubSpot mapping is lossy

### 22. Check the association limit for subscription_company

- [ ] Where: Settings > Data Management > Objects > Subscriptions > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 23. Check the association limit for deal_subscription

- [ ] Where: Settings > Data Management > Objects > Deals > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 24. Check the association limit for onboarding_subscription

- [ ] Where: Settings > Data Management > Objects > Onboardings > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 25. Accept that currency fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property carries no currency code: the symbol is a display choice.
- Done when: the client has agreed in the client notes. Fields: subscription.arr.

### 26. Accept that user fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property holds the HubSpot owner ID, so only users of the account can be chosen.
- Done when: the client has agreed in the client notes. Fields: subscription.success_owner, onboarding.owner.

## Workflows

### 27. Workflow: Create subscription on closed won

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A deal in the new business pipeline moves to closed won.'; action 'Create a subscription from the deal's amount, term and close date, link it to the deal and the company, and set the company's customer status to customer.'

### 28. Workflow: Start onboarding

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A subscription is created with status pending start.'; action 'Create an onboarding record linked to the subscription and assign it to customer success.'

### 29. Workflow: Open renewal deal

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A subscription's renewal date is 90 days away and its status is active.'; action 'Create a deal in the renewals and expansion pipeline at upcoming, linked to the subscription, and set the subscription status to in renewal.'

### 30. Workflow: Flag stalled deals

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'An open deal has no next step date, or the date is more than 7 days past.'; action 'Notify the deal owner and add the deal to the stalled deals view.'

### 31. Workflow: Mark churn

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A deal in the renewals and expansion pipeline moves to churned.'; action 'Set the subscription status to churned and the company's customer status to former customer.'

## Saved views

### 32. Saved view: My open deals

- [ ] Where: CRM > Deals > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view My open deals shows on the Deals index with filter 'Owner is me and stage is open.' and sort 'Close date, soonest first.'.

### 33. Saved view: Stalled deals

- [ ] Where: CRM > Deals > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Stalled deals shows on the Deals index with filter 'Stage is open and next step date is empty or in the past.' and sort 'Next step date, oldest first.'.

### 34. Saved view: Renewals in the next 90 days

- [ ] Where: CRM > Subscriptions > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Renewals in the next 90 days shows on the Subscriptions index with filter 'Status is active or in renewal and renewal date is within 90 days.' and sort 'Renewal date, soonest first.'.

### 35. Saved view: Onboarding in flight

- [ ] Where: CRM > Onboardings > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Onboarding in flight shows on the Onboardings index with filter 'Status is not live.' and sort 'Kickoff date, oldest first.'.

### 36. Saved view: Customers

- [ ] Where: CRM > Companies > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Customers shows on the Companies index with filter 'Customer status is customer.' and sort 'Name, A to Z.'.

## Permissions

### 37. Set roles and access

- [ ] Where: Settings > Users & Teams (menu name not verified against a page in the research)
- Why it is manual: No permission-set API was found. Only pipeline stage edit permissions have one, and this blueprint does not use it.
- Done when: a non-admin test user sees and edits what their role needs and nothing more.
