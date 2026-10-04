# Manual steps: Education and training providers, B2B (hubspot)

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
- Done when: the tier is written in the client notes and the limits call allows 3 custom object(s) (Programme, Cohort, Enrolment).

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

### 6. Check closed stages of Delegate enrolment

- [ ] Where: Settings > Data Management > Objects > Enrolments > Pipelines tab > Delegate enrolment
- Why it is manual: HubSpot has open or closed on custom object stages, not won or lost, and no probability (the design's probabilities are not sent). The API key for closed is unconfirmed (OQ-1).
- Done when: closed stages (Enrolled, Withdrawn) show as Closed. Set them by hand if the read-back says otherwise.

## Stage gates and lost reasons

### 7. Require Training need, Next step date to enter Enquiry qualified (Corporate training)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Corporate training > stage row for Enquiry qualified > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Enquiry qualified asks for Training need, Next step date.

### 8. Require Needs summary, Delegate count, Next step date to enter Needs analysis (Corporate training)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Corporate training > stage row for Needs analysis > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Needs analysis asks for Needs summary, Delegate count, Next step date.

### 9. Require Delivery format, Amount, Funding source to enter Proposal sent (Corporate training)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Corporate training > stage row for Proposal sent > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Proposal sent asks for Delivery format, Amount, Funding source.

### 10. Require Budget confirmed, Next step date to enter Stakeholder review (Corporate training)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Corporate training > stage row for Stakeholder review > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Stakeholder review asks for Budget confirmed, Next step date.

### 11. Require Amount, Proposed start date, Delegate count to enter Terms agreed (Corporate training)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Corporate training > stage row for Terms agreed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Terms agreed asks for Amount, Proposed start date, Delegate count.

### 12. Require Amount, Close date, Purchase order received to enter Booked (Corporate training)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Corporate training > stage row for Booked > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Booked asks for Amount, Close date, Purchase order received.

### 13. Require Lost reason to enter Closed lost (Corporate training)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Corporate training > stage row for Closed lost > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Closed lost asks for Lost reason.

### 14. Require Application date to enter Applied (Delegate enrolment)

- [ ] Where: Settings > Data Management > Objects > Enrolments > Pipelines tab > Delegate enrolment > stage row for Applied > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test enrolment into Applied asks for Application date.

### 15. Require Price, Funding source to enter Place offered (Delegate enrolment)

- [ ] Where: Settings > Data Management > Objects > Enrolments > Pipelines tab > Delegate enrolment > stage row for Place offered > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test enrolment into Place offered asks for Price, Funding source.

### 16. Require Price, Payment status to enter Awaiting payment (Delegate enrolment)

- [ ] Where: Settings > Data Management > Objects > Enrolments > Pipelines tab > Delegate enrolment > stage row for Awaiting payment > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test enrolment into Awaiting payment asks for Price, Payment status.

### 17. Require Price, Payment status to enter Enrolled (Delegate enrolment)

- [ ] Where: Settings > Data Management > Objects > Enrolments > Pipelines tab > Delegate enrolment > stage row for Enrolled > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test enrolment into Enrolled asks for Price, Payment status.

### 18. Require Withdrawal reason to enter Withdrawn (Delegate enrolment)

- [ ] Where: Settings > Data Management > Objects > Enrolments > Pipelines tab > Delegate enrolment > stage row for Withdrawn > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test enrolment into Withdrawn asks for Withdrawal reason.

## Decisions where the HubSpot mapping is lossy

### 19. Check the association limit for cohort_programme

- [ ] Where: Settings > Data Management > Objects > Cohorts > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 20. Check the association limit for cohort_company

- [ ] Where: Settings > Data Management > Objects > Cohorts > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 21. Check the association limit for enrolment_cohort

- [ ] Where: Settings > Data Management > Objects > Enrolments > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 22. Check the association limit for enrolment_person

- [ ] Where: Settings > Data Management > Objects > Enrolments > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 23. Check the association limit for enrolment_company

- [ ] Where: Settings > Data Management > Objects > Enrolments > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 24. Check the association limit for enrolment_deal

- [ ] Where: Settings > Data Management > Objects > Enrolments > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 25. Accept that currency fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property carries no currency code: the symbol is a display choice.
- Done when: the client has agreed in the client notes. Fields: programme.list_price, enrolment.price.

### 26. Accept that user fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property holds the HubSpot owner ID, so only users of the account can be chosen.
- Done when: the client has agreed in the client notes. Fields: cohort.trainer.

## Workflows

### 27. Workflow: Create cohort on booking

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A corporate training deal with delivery format in-house moves to booked.'; action 'Create a cohort of type in-house linked to the client and the programme, copy the proposed start date and delegate count, and assign it to the course administrator.'

### 28. Workflow: Update confirmed places

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'An enrolment moves to enrolled or withdrawn.'; action 'Recalculate the cohort's confirmed places from enrolments at the enrolled stage. Set the cohort to full when it reaches capacity.'

### 29. Workflow: Review cohort viability

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'An open cohort is 21 days from its start date and confirmed places are below the minimum to run.'; action 'Notify the head of delivery and the owning salesperson to decide between pushing sales and cancelling.'

### 30. Workflow: Rebooking follow-up

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A cohort is marked completed.'; action 'Create a task for the account owner of each paying employer to ask about a next cohort within 14 days, and set the company's customer status to active customer.'

### 31. Workflow: Flag stalled deals

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'An open deal has no next step date, or the date is more than 7 days past.'; action 'Notify the deal owner and add the deal to the stalled deals view.'

## Saved views

### 32. Saved view: My open deals

- [ ] Where: CRM > Deals > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view My open deals shows on the Deals index with filter 'Owner is me and stage is open.' and sort 'Close date, soonest first.'.

### 33. Saved view: Stalled deals

- [ ] Where: CRM > Deals > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Stalled deals shows on the Deals index with filter 'Stage is open and next step date is empty or in the past.' and sort 'Next step date, oldest first.'.

### 34. Saved view: Cohorts with places

- [ ] Where: CRM > Cohorts > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Cohorts with places shows on the Cohorts index with filter 'Status is open for enrolment and start date is in the future.' and sort 'Start date, soonest first.'.

### 35. Saved view: Cohorts at risk

- [ ] Where: CRM > Cohorts > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Cohorts at risk shows on the Cohorts index with filter 'Status is open for enrolment and start date is within 28 days and confirmed places are below the minimum.' and sort 'Start date, soonest first.'.

### 36. Saved view: Enrolments awaiting payment

- [ ] Where: CRM > Enrolments > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Enrolments awaiting payment shows on the Enrolments index with filter 'Stage is awaiting payment.' and sort 'Application date, oldest first.'.

### 37. Saved view: Lapsed customers

- [ ] Where: CRM > Companies > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Lapsed customers shows on the Companies index with filter 'Customer status is lapsed.' and sort 'Name, A to Z.'.

## Permissions

### 38. Set roles and access

- [ ] Where: Settings > Users & Teams (menu name not verified against a page in the research)
- Why it is manual: No permission-set API was found. Only pipeline stage edit permissions have one, and this blueprint does not use it.
- Done when: a non-admin test user sees and edits what their role needs and nothing more.
