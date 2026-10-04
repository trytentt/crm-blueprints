# Manual steps: B2B SaaS, product-led (hubspot)

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
- Done when: the tier is written in the client notes and the limits call allows 2 custom object(s) (Workspace, Adoption plan).

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

### 6. Require PQL trigger to enter Product-qualified lead (Sales assist)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Sales assist > stage row for Product-qualified lead > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Product-qualified lead asks for PQL trigger.

### 7. Require Next step date to enter Conversation (Sales assist)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Sales assist > stage row for Conversation > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Conversation asks for Next step date.

### 8. Require Need summary, Expected seats, Next step date to enter Need confirmed (Sales assist)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Sales assist > stage row for Need confirmed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Need confirmed asks for Need summary, Expected seats, Next step date.

### 9. Require Amount, Target plan, Expected seats, Billing term to enter Proposal (Sales assist)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Sales assist > stage row for Proposal > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Proposal asks for Amount, Target plan, Expected seats, Billing term.

### 10. Require Amount, Close date, Security review to enter Negotiation (Sales assist)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Sales assist > stage row for Negotiation > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Negotiation asks for Amount, Close date, Security review.

### 11. Require Amount, Close date to enter Closed won (Sales assist)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Sales assist > stage row for Closed won > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Closed won asks for Amount, Close date.

### 12. Require Lost reason to enter Closed lost (Sales assist)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Sales assist > stage row for Closed lost > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Closed lost asks for Lost reason.

### 13. Require Expansion type to enter Expansion signal (Expansion)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Expansion > stage row for Expansion signal > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Expansion signal asks for Expansion type.

### 14. Require Next step date to enter Outreach (Expansion)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Expansion > stage row for Outreach > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Outreach asks for Next step date.

### 15. Require Amount, Expected seats, Target plan to enter Proposal (Expansion)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Expansion > stage row for Proposal > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Proposal asks for Amount, Expected seats, Target plan.

### 16. Require Amount, Close date to enter Negotiation (Expansion)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Expansion > stage row for Negotiation > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Negotiation asks for Amount, Close date.

### 17. Require Amount, Close date to enter Expanded (Expansion)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Expansion > stage row for Expanded > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Expanded asks for Amount, Close date.

### 18. Require Lost reason to enter Declined (Expansion)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Expansion > stage row for Declined > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Declined asks for Lost reason.

## Decisions where the HubSpot mapping is lossy

### 19. Check the association limit for workspace_company

- [ ] Where: Settings > Data Management > Objects > Workspaces > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 20. Check the association limit for deal_workspace

- [ ] Where: Settings > Data Management > Objects > Deals > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 21. Check the association limit for adoption_plan_workspace

- [ ] Where: Settings > Data Management > Objects > Adoption plans > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 22. Accept that currency fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property carries no currency code: the symbol is a display choice.
- Done when: the client has agreed in the client notes. Fields: workspace.mrr.

### 23. Accept that percent fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property the stored value (0.2 or 20) is unconfirmed (open question OQ-5).
- Done when: the client has agreed in the client notes. Fields: workspace.limit_usage_percent.

### 24. Accept that user fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property holds the HubSpot owner ID, so only users of the account can be chosen.
- Done when: the client has agreed in the client notes. Fields: adoption_plan.owner.

## Workflows

### 25. Workflow: Sync product usage

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'Nightly, and when a workspace is created or its plan changes in the product.'; action 'Upsert the workspace by product workspace ID with plan, seats, active users, limit used and last active date, and link the people who are members.'

### 26. Workflow: Flag product-qualified lead

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A workspace meets the PQL rule and its PQL status is not qualified, accepted or rejected.'; action 'Set PQL status to qualified, notify the sales-assist queue, and create a deal in the sales assist pipeline at product-qualified lead once a rep accepts, with the PQL trigger filled.'

### 27. Workflow: Open expansion deal

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'Seats used exceed seats paid, or plan limit used passes 80 percent, on a paying workspace with no open expansion deal.'; action 'Create a deal in the expansion pipeline at expansion signal, linked to the workspace, and assign it to the account owner.'

### 28. Workflow: Start adoption plan

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A sales-assist deal moves to closed won.'; action 'Create an adoption plan linked to the workspace, assign it to customer success and set the company to paying.'

### 29. Workflow: Trial ending alert

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A workspace on a trial has a trial end date in 3 days and is activated.'; action 'Notify the account owner, or the sales-assist queue if the workspace has no owner.'

### 30. Workflow: Flag stalled deals

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'An open deal has no next step date, or the date is more than 7 days past.'; action 'Notify the deal owner and add the deal to the stalled deals view.'

## Saved views

### 31. Saved view: PQL queue

- [ ] Where: CRM > Workspaces > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view PQL queue shows on the Workspaces index with filter 'PQL status is qualified.' and sort 'PQL score, highest first.'.

### 32. Saved view: Trials ending soon

- [ ] Where: CRM > Workspaces > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Trials ending soon shows on the Workspaces index with filter 'Lifecycle stage is trialling and trial end date is within 7 days.' and sort 'Trial end date, soonest first.'.

### 33. Saved view: Expansion candidates

- [ ] Where: CRM > Workspaces > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Expansion candidates shows on the Workspaces index with filter 'Lifecycle stage is paying and plan limit used is over 80 percent, or seats used is above seats paid.' and sort 'Plan limit used, highest first.'.

### 34. Saved view: My open deals

- [ ] Where: CRM > Deals > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view My open deals shows on the Deals index with filter 'Owner is me and stage is open.' and sort 'Close date, soonest first.'.

### 35. Saved view: Stalled deals

- [ ] Where: CRM > Deals > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Stalled deals shows on the Deals index with filter 'Stage is open and next step date is empty or in the past.' and sort 'Next step date, oldest first.'.

### 36. Saved view: Adoption in flight

- [ ] Where: CRM > Adoption plans > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Adoption in flight shows on the Adoption plans index with filter 'Status is not complete.' and sort 'Target activation date, oldest first.'.

## Permissions

### 37. Set roles and access

- [ ] Where: Settings > Users & Teams (menu name not verified against a page in the research)
- Why it is manual: No permission-set API was found. Only pipeline stage edit permissions have one, and this blueprint does not use it.
- Done when: a non-admin test user sees and edits what their role needs and nothing more.
