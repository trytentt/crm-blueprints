# Manual steps: Construction and trades (hubspot)

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
- Done when: the tier is written in the client notes and the limits call allows 3 custom object(s) (Site, Project, Estimate).

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

### 6. Check closed stages of Project delivery

- [ ] Where: Settings > Data Management > Objects > Projects > Pipelines tab > Project delivery
- Why it is manual: HubSpot has open or closed on custom object stages, not won or lost, and no probability (the design's probabilities are not sent). The API key for closed is unconfirmed (OQ-1).
- Done when: closed stages (Closed out, Cancelled) show as Closed. Set them by hand if the read-back says otherwise.

## Stage gates and lost reasons

### 7. Require Procurement route, Work type to enter Opportunity (Tender and estimate)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Tender and estimate > stage row for Opportunity > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Opportunity asks for Procurement route, Work type.

### 8. Require Tender deadline, Go or no-go to enter Go or no-go (Tender and estimate)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Tender and estimate > stage row for Go or no-go > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Go or no-go asks for Tender deadline, Go or no-go.

### 9. Require Site visit done, Next step date to enter Estimating (Tender and estimate)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Tender and estimate > stage row for Estimating > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Estimating asks for Site visit done, Next step date.

### 10. Require Amount, Estimated margin, Contract form to enter Bid submitted (Tender and estimate)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Tender and estimate > stage row for Bid submitted > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Bid submitted asks for Amount, Estimated margin, Contract form.

### 11. Require Next step date to enter Clarification (Tender and estimate)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Tender and estimate > stage row for Clarification > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Clarification asks for Next step date.

### 12. Require Amount, Retention, Expected start date to enter Preferred bidder (Tender and estimate)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Tender and estimate > stage row for Preferred bidder > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Preferred bidder asks for Amount, Retention, Expected start date.

### 13. Require Amount, Close date, Contract form to enter Awarded (Tender and estimate)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Tender and estimate > stage row for Awarded > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Awarded asks for Amount, Close date, Contract form.

### 14. Require Lost reason to enter Closed lost (Tender and estimate)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Tender and estimate > stage row for Closed lost > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Closed lost asks for Lost reason.

### 15. Require Contract value to enter Pre-start (Project delivery)

- [ ] Where: Settings > Data Management > Objects > Projects > Pipelines tab > Project delivery > stage row for Pre-start > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test project into Pre-start asks for Contract value.

### 16. Require Project manager, Planned completion to enter Mobilising (Project delivery)

- [ ] Where: Settings > Data Management > Objects > Projects > Pipelines tab > Project delivery > stage row for Mobilising > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test project into Mobilising asks for Project manager, Planned completion.

### 17. Require Start on site, RAMS approved, Insurance verified to enter On site (Project delivery)

- [ ] Where: Settings > Data Management > Objects > Projects > Pipelines tab > Project delivery > stage row for On site > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test project into On site asks for Start on site, RAMS approved, Insurance verified.

### 18. Require Planned completion to enter Snagging (Project delivery)

- [ ] Where: Settings > Data Management > Objects > Projects > Pipelines tab > Project delivery > stage row for Snagging > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test project into Snagging asks for Planned completion.

### 19. Require Actual completion, Retention held, Retention release date to enter Defects period (Project delivery)

- [ ] Where: Settings > Data Management > Objects > Projects > Pipelines tab > Project delivery > stage row for Defects period > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test project into Defects period asks for Actual completion, Retention held, Retention release date.

### 20. Require Final margin to enter Closed out (Project delivery)

- [ ] Where: Settings > Data Management > Objects > Projects > Pipelines tab > Project delivery > stage row for Closed out > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test project into Closed out asks for Final margin.

### 21. Require Cancellation reason to enter Cancelled (Project delivery)

- [ ] Where: Settings > Data Management > Objects > Projects > Pipelines tab > Project delivery > stage row for Cancelled > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test project into Cancelled asks for Cancellation reason.

## Decisions where the HubSpot mapping is lossy

### 22. Check the association limit for site_company

- [ ] Where: Settings > Data Management > Objects > Sites > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 23. Check the association limit for deal_site

- [ ] Where: Settings > Data Management > Objects > Deals > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 24. Check the association limit for estimate_deal

- [ ] Where: Settings > Data Management > Objects > Estimates > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 25. Check the association limit for project_deal

- [ ] Where: Settings > Data Management > Objects > Projects > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: one to one holds for both labelled and unlabelled links in a test.

### 26. Check the association limit for project_site

- [ ] Where: Settings > Data Management > Objects > Projects > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 27. Check the association limit for project_company

- [ ] Where: Settings > Data Management > Objects > Projects > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 28. Accept that currency fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property carries no currency code: the symbol is a display choice.
- Done when: the client has agreed in the client notes. Fields: project.contract_value, project.retention_held, estimate.price.

### 29. Accept that percent fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property the stored value (0.2 or 20) is unconfirmed (open question OQ-5).
- Done when: the client has agreed in the client notes. Fields: deal.estimated_margin, deal.retention_percent, project.final_margin, estimate.margin.

### 30. Accept that user fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property holds the HubSpot owner ID, so only users of the account can be chosen.
- Done when: the client has agreed in the client notes. Fields: project.project_manager, estimate.estimator.

## Workflows

### 31. Workflow: Create project on award

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A deal in the tender and estimate pipeline moves to awarded.'; action 'Create a project linked to the deal, site and client, copy the contract value and work type, and set the company's relationship status to active client.'

### 32. Workflow: Tender deadline reminder

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A deal at estimating or go or no-go has a tender deadline within 3 days.'; action 'Notify the deal owner and the estimator daily until the deal reaches bid submitted.'

### 33. Workflow: Retention release reminder

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A project in the defects period has a retention release date within 30 days.'; action 'Create a task for the project manager and finance to invoice the retention release.'

### 34. Workflow: Supersede old estimates

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'An estimate is set to issued.'; action 'Set earlier estimates on the same deal to superseded and update the deal amount and estimated margin.'

### 35. Workflow: Flag stalled bids

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'An open deal has no next step date, or the date is more than 7 days past.'; action 'Notify the deal owner and add the deal to the stalled bids view.'

## Saved views

### 36. Saved view: Bids due

- [ ] Where: CRM > Deals > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Bids due shows on the Deals index with filter 'Stage is go or no-go or estimating and tender deadline is within 14 days.' and sort 'Tender deadline, soonest first.'.

### 37. Saved view: My open bids

- [ ] Where: CRM > Deals > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view My open bids shows on the Deals index with filter 'Owner is me and stage is open.' and sort 'Close date, soonest first.'.

### 38. Saved view: Stalled bids

- [ ] Where: CRM > Deals > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Stalled bids shows on the Deals index with filter 'Stage is open and next step date is empty or in the past.' and sort 'Next step date, oldest first.'.

### 39. Saved view: Projects on site

- [ ] Where: CRM > Projects > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Projects on site shows on the Projects index with filter 'Stage is on site or snagging.' and sort 'Planned completion, soonest first.'.

### 40. Saved view: Retention due

- [ ] Where: CRM > Projects > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Retention due shows on the Projects index with filter 'Stage is defects period and retention release date is within 60 days.' and sort 'Retention release date, soonest first.'.

### 41. Saved view: Dormant clients

- [ ] Where: CRM > Companies > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Dormant clients shows on the Companies index with filter 'Relationship status is dormant.' and sort 'Name, A to Z.'.

## Permissions

### 42. Set roles and access

- [ ] Where: Settings > Users & Teams (menu name not verified against a page in the research)
- Why it is manual: No permission-set API was found. Only pipeline stage edit permissions have one, and this blueprint does not use it.
- Done when: a non-admin test user sees and edits what their role needs and nothing more.
