# Manual steps: Events and sponsorship (hubspot)

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
- Done when: the tier is written in the client notes and the limits call allows 3 custom object(s) (Event, Package, Fulfilment).

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

### 6. Require Sponsor objectives to enter Prospect (Sponsor sales)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Sponsor sales > stage row for Prospect > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Prospect asks for Sponsor objectives.

### 7. Require Sponsor objectives, Next step date to enter Meeting held (Sponsor sales)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Sponsor sales > stage row for Meeting held > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Meeting held asks for Sponsor objectives, Next step date.

### 8. Require Sponsor tier, Amount to enter Proposal sent (Sponsor sales)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Sponsor sales > stage row for Proposal sent > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Proposal sent asks for Sponsor tier, Amount.

### 9. Require Amount, Payment terms, Next step date to enter Negotiating (Sponsor sales)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Sponsor sales > stage row for Negotiating > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Negotiating asks for Amount, Payment terms, Next step date.

### 10. Require Amount, Close date, Payment terms to enter Contract out (Sponsor sales)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Sponsor sales > stage row for Contract out > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Contract out asks for Amount, Close date, Payment terms.

### 11. Require Amount, Contract signed date, Sponsor tier to enter Signed (Sponsor sales)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Sponsor sales > stage row for Signed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Signed asks for Amount, Contract signed date, Sponsor tier.

### 12. Require Lost reason to enter Closed lost (Sponsor sales)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Sponsor sales > stage row for Closed lost > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Closed lost asks for Lost reason.

### 13. Require Stand type to enter Enquiry (Exhibitor sales)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Exhibitor sales > stage row for Enquiry > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Enquiry asks for Stand type.

### 14. Require Stand size (sqm), Next step date to enter Qualified (Exhibitor sales)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Exhibitor sales > stage row for Qualified > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Qualified asks for Stand size (sqm), Next step date.

### 15. Require Stand size (sqm), Amount, Next step date to enter Space held (Exhibitor sales)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Exhibitor sales > stage row for Space held > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Space held asks for Stand size (sqm), Amount, Next step date.

### 16. Require Amount, Payment terms, Close date to enter Contract sent (Exhibitor sales)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Exhibitor sales > stage row for Contract sent > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Contract sent asks for Amount, Payment terms, Close date.

### 17. Require Amount, Stand size (sqm), Contract signed date, Deposit received to enter Confirmed (Exhibitor sales)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Exhibitor sales > stage row for Confirmed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Confirmed asks for Amount, Stand size (sqm), Contract signed date, Deposit received.

### 18. Require Lost reason to enter Closed lost (Exhibitor sales)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Exhibitor sales > stage row for Closed lost > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Closed lost asks for Lost reason.

## Decisions where the HubSpot mapping is lossy

### 19. Check the association limit for deal_event

- [ ] Where: Settings > Data Management > Objects > Deals > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 20. Check the association limit for package_event

- [ ] Where: Settings > Data Management > Objects > Packages > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 21. Check the association limit for fulfilment_deal

- [ ] Where: Settings > Data Management > Objects > Fulfilments > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: one to one holds for both labelled and unlabelled links in a test.

### 22. Check the association limit for fulfilment_event

- [ ] Where: Settings > Data Management > Objects > Fulfilments > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 23. Check the association limit for fulfilment_company

- [ ] Where: Settings > Data Management > Objects > Fulfilments > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 24. Accept that currency fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property carries no currency code: the symbol is a display choice.
- Done when: the client has agreed in the client notes. Fields: event.sponsorship_target, event.exhibition_target, package.price.

### 25. Accept that user fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property holds the HubSpot owner ID, so only users of the account can be chosen.
- Done when: the client has agreed in the client notes. Fields: event.event_lead, fulfilment.delivery_owner.

## Workflows

### 26. Workflow: Create fulfilment on win

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A sponsor deal moves to signed, or an exhibitor deal moves to confirmed.'; action 'Create a fulfilment record linked to the deal, event and company, set status to not started, and assign it to the operations team with the sponsor objectives copied into the notes.'

### 27. Workflow: Update package sales

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A deal is won or reopened.'; action 'Recalculate quantity sold on each linked package from won deals and flag any package that is sold out.'

### 28. Workflow: Request assets

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A fulfilment is 60 days before its assets due date and assets received is empty.'; action 'Email the partner contact an asset request and set the fulfilment status to assets requested.'

### 29. Workflow: Start next edition renewals

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'An event is marked completed.'; action 'For each fulfilment with renewal intent will renew or undecided, create a deal on the next edition's event with prior participant ticked, and set the company status to past participant.'

### 30. Workflow: Flag stalled deals

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'An open deal has no next step date, or the date is more than 7 days past.'; action 'Notify the deal owner and add the deal to the stalled deals view.'

## Saved views

### 31. Saved view: My open deals

- [ ] Where: CRM > Deals > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view My open deals shows on the Deals index with filter 'Owner is me and stage is open.' and sort 'Close date, soonest first.'.

### 32. Saved view: Stalled deals

- [ ] Where: CRM > Deals > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Stalled deals shows on the Deals index with filter 'Stage is open and next step date is empty or in the past.' and sort 'Next step date, oldest first.'.

### 33. Saved view: Held space

- [ ] Where: CRM > Deals > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Held space shows on the Deals index with filter 'Stage is space held in the exhibitor sales pipeline.' and sort 'Next step date, oldest first.'.

### 34. Saved view: Package availability

- [ ] Where: CRM > Packages > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Package availability shows on the Packages index with filter 'Quantity sold is below quantity available.' and sort 'Package type, then price, highest first.'.

### 35. Saved view: Assets overdue

- [ ] Where: CRM > Fulfilments > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Assets overdue shows on the Fulfilments index with filter 'Assets received is empty and assets due date is in the past.' and sort 'Assets due date, oldest first.'.

### 36. Saved view: Lapsed partners

- [ ] Where: CRM > Companies > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Lapsed partners shows on the Companies index with filter 'Participation status is lapsed or past.' and sort 'Name, A to Z.'.

## Permissions

### 37. Set roles and access

- [ ] Where: Settings > Users & Teams (menu name not verified against a page in the research)
- Why it is manual: No permission-set API was found. Only pipeline stage edit permissions have one, and this blueprint does not use it.
- Done when: a non-admin test user sees and edits what their role needs and nothing more.
