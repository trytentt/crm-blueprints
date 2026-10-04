# Manual steps: Consultancy and professional services (hubspot)

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
- Done when: the tier is written in the client notes and the limits call allows 2 custom object(s) (Matter, Conflict check).

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

### 6. Check closed stages of Matter delivery

- [ ] Where: Settings > Data Management > Objects > Matters > Pipelines tab > Matter delivery
- Why it is manual: HubSpot has open or closed on custom object stages, not won or lost, and no probability (the design's probabilities are not sent). The API key for closed is unconfirmed (OQ-1).
- Done when: closed stages (Closed, Withdrawn) show as Closed. Set them by hand if the read-back says otherwise.

## Stage gates and lost reasons

### 7. Require Service area, Next step date to enter Enquiry (New work)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New work > stage row for Enquiry > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Enquiry asks for Service area, Next step date.

### 8. Require Lead partner, Scope summary to enter Qualified (New work)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New work > stage row for Qualified > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Qualified asks for Lead partner, Scope summary.

### 9. Require Conflict check result to enter Conflict check (New work)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New work > stage row for Conflict check > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Conflict check asks for Conflict check result.

### 10. Require Conflict check result, Billing model, Amount to enter Proposal (New work)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New work > stage row for Proposal > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Proposal asks for Conflict check result, Billing model, Amount.

### 11. Require Amount, Close date, Next step date to enter Proposal sent (New work)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New work > stage row for Proposal sent > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Proposal sent asks for Amount, Close date, Next step date.

### 12. Require Amount, Billing model, Close date to enter Terms agreed (New work)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New work > stage row for Terms agreed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Terms agreed asks for Amount, Billing model, Close date.

### 13. Require Engagement letter status, Conflict check result to enter Engagement letter out (New work)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New work > stage row for Engagement letter out > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Engagement letter out asks for Engagement letter status, Conflict check result.

### 14. Require Amount, Close date, Engagement letter status to enter Closed won (New work)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New work > stage row for Closed won > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Closed won asks for Amount, Close date, Engagement letter status.

### 15. Require Lost reason to enter Closed lost (New work)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New work > stage row for Closed lost > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Closed lost asks for Lost reason.

### 16. Require Responsible partner, Matter manager to enter Opening (Matter delivery)

- [ ] Where: Settings > Data Management > Objects > Matters > Pipelines tab > Matter delivery > stage row for Opening > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test matter into Opening asks for Responsible partner, Matter manager.

### 17. Require Engagement letter signed date, AML check status to enter Cleared to start (Matter delivery)

- [ ] Where: Settings > Data Management > Objects > Matters > Pipelines tab > Matter delivery > stage row for Cleared to start > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test matter into Cleared to start asks for Engagement letter signed date, AML check status.

### 18. Require Start date, Target end date to enter In progress (Matter delivery)

- [ ] Where: Settings > Data Management > Objects > Matters > Pipelines tab > Matter delivery > stage row for In progress > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test matter into In progress asks for Start date, Target end date.

### 19. Require Target end date to enter Awaiting client (Matter delivery)

- [ ] Where: Settings > Data Management > Objects > Matters > Pipelines tab > Matter delivery > stage row for Awaiting client > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test matter into Awaiting client asks for Target end date.

### 20. Require Billing model, Fee estimate to enter Final billing (Matter delivery)

- [ ] Where: Settings > Data Management > Objects > Matters > Pipelines tab > Matter delivery > stage row for Final billing > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test matter into Final billing asks for Billing model, Fee estimate.

### 21. Require Target end date to enter Closed (Matter delivery)

- [ ] Where: Settings > Data Management > Objects > Matters > Pipelines tab > Matter delivery > stage row for Closed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test matter into Closed asks for Target end date.

### 22. Require Close reason to enter Withdrawn (Matter delivery)

- [ ] Where: Settings > Data Management > Objects > Matters > Pipelines tab > Matter delivery > stage row for Withdrawn > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test matter into Withdrawn asks for Close reason.

## Decisions where the HubSpot mapping is lossy

### 23. Check the association limit for matter_company

- [ ] Where: Settings > Data Management > Objects > Matters > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 24. Check the association limit for deal_matter

- [ ] Where: Settings > Data Management > Objects > Deals > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 25. Check the association limit for conflict_check_deal

- [ ] Where: Settings > Data Management > Objects > Conflict checks > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 26. Check the association limit for conflict_check_company

- [ ] Where: Settings > Data Management > Objects > Conflict checks > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 27. Accept that currency fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property carries no currency code: the symbol is a display choice.
- Done when: the client has agreed in the client notes. Fields: matter.fee_estimate.

### 28. Accept that user fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property holds the HubSpot owner ID, so only users of the account can be chosen.
- Done when: the client has agreed in the client notes. Fields: deal.lead_partner, conflict_check.cleared_by, matter.responsible_partner, matter.matter_manager.

## Workflows

### 29. Workflow: Request conflict check

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A deal moves to the conflict check stage.'; action 'Create a conflict check record with result pending, link it to the deal and company, and notify risk or compliance.'

### 30. Workflow: Copy conflict result to deal

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A conflict check result changes.'; action 'Set the linked deal's conflict check result to match, and notify the lead partner.'

### 31. Workflow: Return conflicted deals

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A conflict check result is conflicted.'; action 'Move the deal back to qualified, notify the lead partner and risk, and prompt closed lost with conflict as the reason if the conflict cannot be waived.'

### 32. Workflow: Create matter on closed won

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A deal in the new work pipeline moves to closed won.'; action 'Create a matter from the deal's service area, billing model and amount, link it to the deal and company, and set the company's client status to active client.'

### 33. Workflow: Flag stalled deals

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'An open deal has no next step date, or the date is more than 7 days past.'; action 'Notify the deal owner and add the deal to the stalled deals view.'

### 34. Workflow: Flag work before engagement letter

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A matter is in progress and has no engagement letter signed date.'; action 'Notify the responsible partner and compliance.'

## Saved views

### 35. Saved view: My open deals

- [ ] Where: CRM > Deals > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view My open deals shows on the Deals index with filter 'Owner is me and stage is open.' and sort 'Close date, soonest first.'.

### 36. Saved view: Conflict checks awaiting clearance

- [ ] Where: CRM > Conflict checks > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Conflict checks awaiting clearance shows on the Conflict checks index with filter 'Result is pending.' and sort 'Check date, oldest first.'.

### 37. Saved view: Stalled deals

- [ ] Where: CRM > Deals > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Stalled deals shows on the Deals index with filter 'Stage is open and next step date is empty or in the past.' and sort 'Next step date, oldest first.'.

### 38. Saved view: Active matters

- [ ] Where: CRM > Matters > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Active matters shows on the Matters index with filter 'Stage is open.' and sort 'Target end date, soonest first.'.

### 39. Saved view: Matters without a signed letter

- [ ] Where: CRM > Matters > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Matters without a signed letter shows on the Matters index with filter 'Stage is in progress and engagement letter signed date is empty.' and sort 'Start date, oldest first.'.

### 40. Saved view: Matters ready to bill

- [ ] Where: CRM > Matters > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Matters ready to bill shows on the Matters index with filter 'Stage is final billing.' and sort 'Target end date, oldest first.'.

## Permissions

### 41. Set roles and access

- [ ] Where: Settings > Users & Teams (menu name not verified against a page in the research)
- Why it is manual: No permission-set API was found. Only pipeline stage edit permissions have one, and this blueprint does not use it.
- Done when: a non-admin test user sees and edits what their role needs and nothing more.
