# Manual steps: Recruitment agency (hubspot)

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
- Done when: the tier is written in the client notes and the limits call allows 2 custom object(s) (Role, Submission).

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

### 6. Check closed stages of Placement

- [ ] Where: Settings > Data Management > Objects > Submissions > Pipelines tab > Placement
- Why it is manual: HubSpot has open or closed on custom object stages, not won or lost, and no probability (the design's probabilities are not sent). The API key for closed is unconfirmed (OQ-1).
- Done when: closed stages (Placed, Rejected) show as Closed. Set them by hand if the read-back says otherwise.

## Stage gates and lost reasons

### 7. Require Next step date to enter Target (Client development)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Client development > stage row for Target > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Target asks for Next step date.

### 8. Require Next step date to enter Conversation (Client development)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Client development > stage row for Conversation > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Conversation asks for Next step date.

### 9. Require Search model, Fee percent to enter Terms discussed (Client development)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Client development > stage row for Terms discussed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Terms discussed asks for Search model, Fee percent.

### 10. Require Search model, Fee percent, Exclusivity to enter Terms sent (Client development)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Client development > stage row for Terms sent > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Terms sent asks for Search model, Fee percent, Exclusivity.

### 11. Require Search model, Fee percent to enter Terms signed (Client development)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Client development > stage row for Terms signed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Terms signed asks for Search model, Fee percent.

### 12. Require Lost reason to enter Not won (Client development)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Client development > stage row for Not won > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Not won asks for Lost reason.

### 13. Require Source to enter Sourced (Placement)

- [ ] Where: Settings > Data Management > Objects > Submissions > Pipelines tab > Placement > stage row for Sourced > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test submission into Sourced asks for Source.

### 14. Require Salary expected to enter Screened (Placement)

- [ ] Where: Settings > Data Management > Objects > Submissions > Pipelines tab > Placement > stage row for Screened > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test submission into Screened asks for Salary expected.

### 15. Require CV sent date to enter Submitted (Placement)

- [ ] Where: Settings > Data Management > Objects > Submissions > Pipelines tab > Placement > stage row for Submitted > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test submission into Submitted asks for CV sent date.

### 16. Require Interview date to enter Interviewing (Placement)

- [ ] Where: Settings > Data Management > Objects > Submissions > Pipelines tab > Placement > stage row for Interviewing > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test submission into Interviewing asks for Interview date.

### 17. Require Agreed salary to enter Offer (Placement)

- [ ] Where: Settings > Data Management > Objects > Submissions > Pipelines tab > Placement > stage row for Offer > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test submission into Offer asks for Agreed salary.

### 18. Require Agreed salary, Start date, Checks complete to enter Offer accepted (Placement)

- [ ] Where: Settings > Data Management > Objects > Submissions > Pipelines tab > Placement > stage row for Offer accepted > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test submission into Offer accepted asks for Agreed salary, Start date, Checks complete.

### 19. Require Start date, Fee amount to enter Placed (Placement)

- [ ] Where: Settings > Data Management > Objects > Submissions > Pipelines tab > Placement > stage row for Placed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test submission into Placed asks for Start date, Fee amount.

### 20. Require Rejection reason to enter Rejected (Placement)

- [ ] Where: Settings > Data Management > Objects > Submissions > Pipelines tab > Placement > stage row for Rejected > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test submission into Rejected asks for Rejection reason.

## Decisions where the HubSpot mapping is lossy

### 21. Check the association limit for role_company

- [ ] Where: Settings > Data Management > Objects > Roles > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 22. Check the association limit for role_contact

- [ ] Where: Settings > Data Management > Objects > Roles > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 23. Check the association limit for role_deal

- [ ] Where: Settings > Data Management > Objects > Roles > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 24. Check the association limit for submission_role

- [ ] Where: Settings > Data Management > Objects > Submissions > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 25. Check the association limit for submission_candidate

- [ ] Where: Settings > Data Management > Objects > Submissions > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 26. Accept that currency fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property carries no currency code: the symbol is a display choice.
- Done when: the client has agreed in the client notes. Fields: person.desired_salary, role.salary_min, role.salary_max, role.fee_estimate, submission.salary_expected, submission.agreed_salary, submission.fee_amount.

### 27. Accept that percent fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property the stored value (0.2 or 20) is unconfirmed (open question OQ-5).
- Done when: the client has agreed in the client notes. Fields: company.default_fee_percent, deal.fee_percent, role.fee_percent.

### 28. Accept that user fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property holds the HubSpot owner ID, so only users of the account can be chosen.
- Done when: the client has agreed in the client notes. Fields: role.consultant, submission.consultant.

## Workflows

### 29. Workflow: Block submissions without terms

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A submission is created for a role whose client has terms status other than signed.'; action 'Notify the consultant and the desk manager that the client has no signed terms, and flag the submission.'

### 30. Workflow: Calculate fee

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A submission has an agreed salary set.'; action 'Set fee amount from the agreed salary and the fee percent on the role.'

### 31. Workflow: Mark role filled

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A submission moves to placed and the role's openings are all filled.'; action 'Set the role status to filled by us and close other open submissions on the role as rejected with role filled elsewhere.'

### 32. Workflow: Rebate period reminder

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A placed submission's start date plus the client's rebate period is 14 days away.'; action 'Notify the consultant to check in with the client and the new starter.'

### 33. Workflow: Mark dormant client

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'An active client has had no new role for 6 months.'; action 'Set client status to dormant client and add the company to the reactivation view.'

### 34. Workflow: Review candidate data

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A person of type candidate has a data review date in 30 days.'; action 'Notify the owner to confirm consent or delete the record.'

### 35. Workflow: Flag stalled deals

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'An open deal has no next step date, or the date is more than 7 days past.'; action 'Notify the deal owner and add the deal to the stalled deals view.'

## Saved views

### 36. Saved view: Open roles

- [ ] Where: CRM > Roles > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Open roles shows on the Roles index with filter 'Status is open or offer stage.' and sort 'Target fill date, soonest first.'.

### 37. Saved view: My candidates in process

- [ ] Where: CRM > Submissions > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view My candidates in process shows on the Submissions index with filter 'Consultant is me and stage is open.' and sort 'Interview date, soonest first.'.

### 38. Saved view: Offers to close

- [ ] Where: CRM > Submissions > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Offers to close shows on the Submissions index with filter 'Stage is offer or offer accepted.' and sort 'Start date, soonest first.'.

### 39. Saved view: Placements to invoice

- [ ] Where: CRM > Submissions > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Placements to invoice shows on the Submissions index with filter 'Stage is placed and invoice status is to invoice.' and sort 'Start date, oldest first.'.

### 40. Saved view: Candidates due for data review

- [ ] Where: CRM > Contacts > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Candidates due for data review shows on the Contacts index with filter 'Person type includes candidate and data review date is within 30 days.' and sort 'Data review date, soonest first.'.

### 41. Saved view: Stalled deals

- [ ] Where: CRM > Deals > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Stalled deals shows on the Deals index with filter 'Stage is open and next step date is empty or in the past.' and sort 'Next step date, oldest first.'.

## Permissions

### 42. Set roles and access

- [ ] Where: Settings > Users & Teams (menu name not verified against a page in the research)
- Why it is manual: No permission-set API was found. Only pipeline stage edit permissions have one, and this blueprint does not use it.
- Done when: a non-admin test user sees and edits what their role needs and nothing more.
