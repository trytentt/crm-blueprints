# Manual steps: Financial advisers, client households (hubspot)

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
- Done when: the tier is written in the client notes and the limits call allows 3 custom object(s) (Household, Advice case, Review).

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

### 6. Check closed stages of Advice delivery

- [ ] Where: Settings > Data Management > Objects > Advice cases > Pipelines tab > Advice delivery
- Why it is manual: HubSpot has open or closed on custom object stages, not won or lost, and no probability (the design's probabilities are not sent). The API key for closed is unconfirmed (OQ-1).
- Done when: closed stages (Completed, Closed without advice) show as Closed. Set them by hand if the read-back says otherwise.

### 7. Check closed stages of Review cycle

- [ ] Where: Settings > Data Management > Objects > Reviews > Pipelines tab > Review cycle
- Why it is manual: HubSpot has open or closed on custom object stages, not won or lost, and no probability (the design's probabilities are not sent). The API key for closed is unconfirmed (OQ-1).
- Done when: closed stages (Review completed, Not completed) show as Closed. Set them by hand if the read-back says otherwise.

## Stage gates and lost reasons

### 8. Require Referral source to enter Enquiry (New client)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New client > stage row for Enquiry > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Enquiry asks for Referral source.

### 9. Require Service interest, Next step date to enter Initial meeting booked (New client)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New client > stage row for Initial meeting booked > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Initial meeting booked asks for Service interest, Next step date.

### 10. Require Initial meeting held, Expected investable assets to enter Initial meeting held (New client)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New client > stage row for Initial meeting held > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Initial meeting held asks for Initial meeting held, Expected investable assets.

### 11. Require Fee basis agreed, Next step date to enter Fee proposal (New client)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New client > stage row for Fee proposal > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Fee proposal asks for Fee basis agreed, Next step date.

### 12. Require Fee basis agreed, Amount, Close date to enter Agreement out (New client)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New client > stage row for Agreement out > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Agreement out asks for Fee basis agreed, Amount, Close date.

### 13. Require Client agreement signed, Close date to enter Client won (New client)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New client > stage row for Client won > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Client won asks for Client agreement signed, Close date.

### 14. Require Lost reason to enter Lost (New client)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New client > stage row for Lost > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Lost asks for Lost reason.

### 15. Require Adviser, Advice topic to enter Fact find (Advice delivery)

- [ ] Where: Settings > Data Management > Objects > Advice cases > Pipelines tab > Advice delivery > stage row for Fact find > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test advice_case into Fact find asks for Adviser, Advice topic.

### 16. Require Fact find complete, Paraplanner to enter Analysis (Advice delivery)

- [ ] Where: Settings > Data Management > Objects > Advice cases > Pipelines tab > Advice delivery > stage row for Analysis > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test advice_case into Analysis asks for Fact find complete, Paraplanner.

### 17. Require Compliance check to enter Report drafted (Advice delivery)

- [ ] Where: Settings > Data Management > Objects > Advice cases > Pipelines tab > Advice delivery > stage row for Report drafted > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test advice_case into Report drafted asks for Compliance check.

### 18. Require Report issued date, Compliance check to enter Report issued (Advice delivery)

- [ ] Where: Settings > Data Management > Objects > Advice cases > Pipelines tab > Advice delivery > stage row for Report issued > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test advice_case into Report issued asks for Report issued date, Compliance check.

### 19. Require Client decision to enter Accepted (Advice delivery)

- [ ] Where: Settings > Data Management > Objects > Advice cases > Pipelines tab > Advice delivery > stage row for Accepted > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test advice_case into Accepted asks for Client decision.

### 20. Require Applications submitted, Completion date to enter Completed (Advice delivery)

- [ ] Where: Settings > Data Management > Objects > Advice cases > Pipelines tab > Advice delivery > stage row for Completed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test advice_case into Completed asks for Applications submitted, Completion date.

### 21. Require Closure reason to enter Closed without advice (Advice delivery)

- [ ] Where: Settings > Data Management > Objects > Advice cases > Pipelines tab > Advice delivery > stage row for Closed without advice > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test advice_case into Closed without advice asks for Closure reason.

### 22. Require Review type, Due date to enter Due (Review cycle)

- [ ] Where: Settings > Data Management > Objects > Reviews > Pipelines tab > Review cycle > stage row for Due > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test review into Due asks for Review type, Due date.

### 23. Require Adviser to enter Invited (Review cycle)

- [ ] Where: Settings > Data Management > Objects > Reviews > Pipelines tab > Review cycle > stage row for Invited > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test review into Invited asks for Adviser.

### 24. Require Meeting date to enter Booked (Review cycle)

- [ ] Where: Settings > Data Management > Objects > Reviews > Pipelines tab > Review cycle > stage row for Booked > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test review into Booked asks for Meeting date.

### 25. Require Circumstances changed, Risk profile reconfirmed to enter Meeting held (Review cycle)

- [ ] Where: Settings > Data Management > Objects > Reviews > Pipelines tab > Review cycle > stage row for Meeting held > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test review into Meeting held asks for Circumstances changed, Risk profile reconfirmed.

### 26. Require Outcome, Risk profile reconfirmed to enter Review completed (Review cycle)

- [ ] Where: Settings > Data Management > Objects > Reviews > Pipelines tab > Review cycle > stage row for Review completed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test review into Review completed asks for Outcome, Risk profile reconfirmed.

### 27. Require Missed reason to enter Not completed (Review cycle)

- [ ] Where: Settings > Data Management > Objects > Reviews > Pipelines tab > Review cycle > stage row for Not completed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test review into Not completed asks for Missed reason.

## Decisions where the HubSpot mapping is lossy

### 28. Check the association limit for person_household

- [ ] Where: Settings > Data Management > Objects > Contacts > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 29. Check the association limit for deal_household

- [ ] Where: Settings > Data Management > Objects > Deals > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 30. Check the association limit for advice_case_household

- [ ] Where: Settings > Data Management > Objects > Advice cases > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 31. Check the association limit for advice_case_deal

- [ ] Where: Settings > Data Management > Objects > Advice cases > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 32. Check the association limit for review_household

- [ ] Where: Settings > Data Management > Objects > Reviews > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 33. Check the association limit for household_referrer

- [ ] Where: Settings > Data Management > Objects > Households > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 34. Accept that currency fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property carries no currency code: the symbol is a display choice.
- Done when: the client has agreed in the client notes. Fields: deal.expected_investable_assets, household.annual_fee.

### 35. Accept that user fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property holds the HubSpot owner ID, so only users of the account can be chosen.
- Done when: the client has agreed in the client notes. Fields: household.lead_adviser, advice_case.adviser, advice_case.paraplanner, review.adviser.

## Workflows

### 36. Workflow: Start advice case on client won

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A deal in the new client pipeline moves to client won.'; action 'Set the household status to onboarding, set the agreement date, create an advice case at fact find assigned to the lead adviser, and set the next review date from the review frequency.'

### 37. Workflow: Open review

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A household's next review date is 90 days away and its status is ongoing client.'; action 'Create a review at due for the household, assigned to the lead adviser.'

### 38. Workflow: Roll the review cycle forward

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A review moves to review completed.'; action 'Set the household's last review date to the meeting date and its next review date to the date plus its review frequency.'

### 39. Workflow: Chase overdue reviews

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A review is open and its due date has passed.'; action 'Notify the lead adviser and add the review to the overdue reviews view.'

### 40. Workflow: Vulnerability flag alert

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A person's vulnerability flag changes to possible or confirmed.'; action 'Notify the lead adviser and compliance lead to check the service and communication preferences.'

### 41. Workflow: Compliance check request

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'An advice case moves to report drafted.'; action 'Notify the compliance lead and set the compliance check to pending.'

### 42. Workflow: Thank the referrer

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A deal with a professional referral source moves to client won.'; action 'Create a task for the lead adviser to thank the referrer, subject to the referral agreement and client consent.'

## Saved views

### 43. Saved view: Reviews due in 90 days

- [ ] Where: CRM > Households > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Reviews due in 90 days shows on the Households index with filter 'Status is ongoing client and next review date is within 90 days.' and sort 'Next review date, soonest first.'.

### 44. Saved view: Overdue reviews

- [ ] Where: CRM > Reviews > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Overdue reviews shows on the Reviews index with filter 'Review is open and due date is in the past.' and sort 'Due date, oldest first.'.

### 45. Saved view: My advice cases

- [ ] Where: CRM > Advice cases > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view My advice cases shows on the Advice cases index with filter 'Adviser or paraplanner is me and stage is open.' and sort 'Report issued date, oldest first.'.

### 46. Saved view: My prospects

- [ ] Where: CRM > Deals > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view My prospects shows on the Deals index with filter 'Owner is me and stage is open.' and sort 'Next step date, soonest first.'.

### 47. Saved view: Clients with a vulnerability flag

- [ ] Where: CRM > Contacts > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Clients with a vulnerability flag shows on the Contacts index with filter 'Vulnerability flag is possible or confirmed.' and sort 'Last name, A to Z.'.

### 48. Saved view: Households by service tier

- [ ] Where: CRM > Households > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Households by service tier shows on the Households index with filter 'Status is ongoing client.' and sort 'Service tier, then name.'.

## Permissions

### 49. Set roles and access

- [ ] Where: Settings > Users & Teams (menu name not verified against a page in the research)
- Why it is manual: No permission-set API was found. Only pipeline stage edit permissions have one, and this blueprint does not use it.
- Done when: a non-admin test user sees and edits what their role needs and nothing more.
