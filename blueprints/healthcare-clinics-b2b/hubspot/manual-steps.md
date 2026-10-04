# Manual steps: Healthcare clinics, B2B (hubspot)

Generated from `design.yaml`. Do not edit by hand. The HubSpot API cannot do any of this.
Sources: https://developers.hubspot.com/docs/api-reference/latest/crm/pipelines/guide.md, https://knowledge.hubspot.com/records/create-and-manage-saved-views, https://knowledge.hubspot.com/workflows/create-workflows, `platforms/hubspot/reference/api-coverage.md`.

## Before and during the build

### 1. Create a service key and test in a developer test account first

- [ ] Where: Development > Keys > Service keys > Create service key (scopes in platforms/hubspot/reference/auth-and-setup.md)
- Why it is manual: Keys are made in the account by a super admin. A developer test account carries a 90-day Enterprise trial, so it can test custom objects before the client account is touched.
- Done when: `GET /crm/properties/2026-09/contacts` returns 200 with the key.

### 2. Confirm the account is Enterprise before creating custom objects

- [ ] Where: Settings > Account Management > Account defaults, and GET /crm/limits/2026-09/custom-object-types
- Why it is manual: Custom objects need Enterprise and there is no workaround on a lower tier. A client is typically limited to 10 definitions (OQ-3); this blueprint creates 3.
- Done when: the tier is written in the client notes and the limits call allows 3 custom object(s) (Service, Service contract, Referral agreement).

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

### 6. Check closed stages of Referral partners

- [ ] Where: Settings > Data Management > Objects > Referral agreements > Pipelines tab > Referral partners
- Why it is manual: HubSpot has open or closed on custom object stages, not won or lost, and no probability (the design's probabilities are not sent). The API key for closed is unconfirmed (OQ-1).
- Done when: closed stages (Active, Declined) show as Closed. Set them by hand if the read-back says otherwise.

## Stage gates and lost reasons

### 7. Require Service interest, Next step date to enter Qualified (Employer and insurer contracts)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Employer and insurer contracts > stage row for Qualified > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Qualified asks for Service interest, Next step date.

### 8. Require Covered headcount, Sites covered, Next step date to enter Discovery (Employer and insurer contracts)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Employer and insurer contracts > stage row for Discovery > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Discovery asks for Covered headcount, Sites covered, Next step date.

### 9. Require Amount, Pricing model, Contract term (months) to enter Proposal (Employer and insurer contracts)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Employer and insurer contracts > stage row for Proposal > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Proposal asks for Amount, Pricing model, Contract term (months).

### 10. Require Next step date to enter Governance review (Employer and insurer contracts)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Employer and insurer contracts > stage row for Governance review > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Governance review asks for Next step date.

### 11. Require Pilot agreed, Next step date to enter Pilot (Employer and insurer contracts)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Employer and insurer contracts > stage row for Pilot > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Pilot asks for Pilot agreed, Next step date.

### 12. Require Amount, Close date, Governance review passed to enter Contract out (Employer and insurer contracts)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Employer and insurer contracts > stage row for Contract out > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Contract out asks for Amount, Close date, Governance review passed.

### 13. Require Amount, Close date, Governance review passed to enter Closed won (Employer and insurer contracts)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Employer and insurer contracts > stage row for Closed won > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Closed won asks for Amount, Close date, Governance review passed.

### 14. Require Lost reason to enter Closed lost (Employer and insurer contracts)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Employer and insurer contracts > stage row for Closed lost > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Closed lost asks for Lost reason.

### 15. Require Renewal risk to enter Upcoming (Contract renewals)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Contract renewals > stage row for Upcoming > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Upcoming asks for Renewal risk.

### 16. Require Renewal risk, Next step date to enter Review meeting (Contract renewals)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Contract renewals > stage row for Review meeting > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Review meeting asks for Renewal risk, Next step date.

### 17. Require Amount, Pricing model, Contract term (months) to enter Terms proposed (Contract renewals)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Contract renewals > stage row for Terms proposed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Terms proposed asks for Amount, Pricing model, Contract term (months).

### 18. Require Amount, Close date to enter Awaiting signature (Contract renewals)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Contract renewals > stage row for Awaiting signature > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Awaiting signature asks for Amount, Close date.

### 19. Require Amount, Close date to enter Renewed (Contract renewals)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Contract renewals > stage row for Renewed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Renewed asks for Amount, Close date.

### 20. Require Lost reason to enter Not renewed (Contract renewals)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Contract renewals > stage row for Not renewed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Not renewed asks for Lost reason.

### 21. Require Agreement type to enter Identified (Referral partners)

- [ ] Where: Settings > Data Management > Objects > Referral agreements > Pipelines tab > Referral partners > stage row for Identified > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test referral_agreement into Identified asks for Agreement type.

### 22. Require Fee basis to enter Intro meeting (Referral partners)

- [ ] Where: Settings > Data Management > Objects > Referral agreements > Pipelines tab > Referral partners > stage row for Intro meeting > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test referral_agreement into Intro meeting asks for Fee basis.

### 23. Require Fee basis to enter Governance check (Referral partners)

- [ ] Where: Settings > Data Management > Objects > Referral agreements > Pipelines tab > Referral partners > stage row for Governance check > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test referral_agreement into Governance check asks for Fee basis.

### 24. Require Governance checked to enter Agreement sent (Referral partners)

- [ ] Where: Settings > Data Management > Objects > Referral agreements > Pipelines tab > Referral partners > stage row for Agreement sent > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test referral_agreement into Agreement sent asks for Governance checked.

### 25. Require Signed date, Review date, Governance checked to enter Active (Referral partners)

- [ ] Where: Settings > Data Management > Objects > Referral agreements > Pipelines tab > Referral partners > stage row for Active > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test referral_agreement into Active asks for Signed date, Review date, Governance checked.

### 26. Require Decline reason to enter Declined (Referral partners)

- [ ] Where: Settings > Data Management > Objects > Referral agreements > Pipelines tab > Referral partners > stage row for Declined > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test referral_agreement into Declined asks for Decline reason.

## Decisions where the HubSpot mapping is lossy

### 27. Check the association limit for service_contract_company

- [ ] Where: Settings > Data Management > Objects > Service contracts > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 28. Check the association limit for service_contract_deal

- [ ] Where: Settings > Data Management > Objects > Service contracts > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 29. Check the association limit for referral_agreement_company

- [ ] Where: Settings > Data Management > Objects > Referral agreements > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 30. Check the association limit for referral_agreement_person

- [ ] Where: Settings > Data Management > Objects > Referral agreements > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 31. Check the association limit for deal_referral_agreement

- [ ] Where: Settings > Data Management > Objects > Deals > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 32. Accept that currency fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property carries no currency code: the symbol is a display choice.
- Done when: the client has agreed in the client notes. Fields: service.list_price, service_contract.annual_value.

### 33. Accept that user fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property holds the HubSpot owner ID, so only users of the account can be chosen.
- Done when: the client has agreed in the client notes. Fields: service_contract.account_manager.

## Workflows

### 34. Workflow: Create service contract on win

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A deal in the employer and insurer contracts pipeline moves to closed won.'; action 'Create a service contract with the deal's amount, term and services, link it to the deal and the company, set status to pending start and the customer status to active customer.'

### 35. Workflow: Block start without data processing agreement

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A service contract is set to active and the data processing agreement signed box is empty.'; action 'Set the status back to pending start and notify the account manager and the data protection lead.'

### 36. Workflow: Open renewal deal

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A service contract's renewal date is 90 days away and its status is active.'; action 'Create a deal in the contract renewals pipeline at upcoming, linked to the contract, and set the contract status to in renewal.'

### 37. Workflow: Partner review reminder

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'An active referral agreement has a review date within 30 days.'; action 'Create a task for the partnerships owner to hold the review and update the quarterly referral count.'

### 38. Workflow: Flag stalled deals

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'An open deal has no next step date, or the date is more than 7 days past.'; action 'Notify the deal owner and add the deal to the stalled deals view.'

## Saved views

### 39. Saved view: My open deals

- [ ] Where: CRM > Deals > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view My open deals shows on the Deals index with filter 'Owner is me and stage is open.' and sort 'Close date, soonest first.'.

### 40. Saved view: Stalled deals

- [ ] Where: CRM > Deals > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Stalled deals shows on the Deals index with filter 'Stage is open and next step date is empty or in the past.' and sort 'Next step date, oldest first.'.

### 41. Saved view: Deals in governance review

- [ ] Where: CRM > Deals > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Deals in governance review shows on the Deals index with filter 'Stage is governance review or pilot.' and sort 'Next step date, soonest first.'.

### 42. Saved view: Renewals in the next 90 days

- [ ] Where: CRM > Service contracts > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Renewals in the next 90 days shows on the Service contracts index with filter 'Status is active or in renewal and renewal date is within 90 days.' and sort 'Renewal date, soonest first.'.

### 43. Saved view: Partners due review

- [ ] Where: CRM > Referral agreements > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Partners due review shows on the Referral agreements index with filter 'Stage is active and review date is within 60 days.' and sort 'Review date, soonest first.'.

### 44. Saved view: Brokers and insurers

- [ ] Where: CRM > Companies > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Brokers and insurers shows on the Companies index with filter 'Account type is insurer or broker.' and sort 'Name, A to Z.'.

## Permissions

### 45. Set roles and access

- [ ] Where: Settings > Users & Teams (menu name not verified against a page in the research)
- Why it is manual: No permission-set API was found. Only pipeline stage edit permissions have one, and this blueprint does not use it.
- Done when: a non-admin test user sees and edits what their role needs and nothing more.
