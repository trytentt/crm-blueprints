# Manual steps: Commercial real estate, leasing (hubspot)

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
- Done when: the tier is written in the client notes and the limits call allows 2 custom object(s) (Property, Lease).

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

### 6. Check closed stages of Lease renewal

- [ ] Where: Settings > Data Management > Objects > Leases > Pipelines tab > Lease renewal
- Why it is manual: HubSpot has open or closed on custom object stages, not won or lost, and no probability (the design's probabilities are not sent). The API key for closed is unconfirmed (OQ-1).
- Done when: closed stages (Renewed, Not renewed) show as Closed. Set them by hand if the read-back says otherwise.

## Stage gates and lost reasons

### 7. Require Instruction type to enter Enquiry (Letting)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Letting > stage row for Enquiry > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Enquiry asks for Instruction type.

### 8. Require Size required (sq ft), Target move date, Next step date to enter Requirement qualified (Letting)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Letting > stage row for Requirement qualified > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Requirement qualified asks for Size required (sq ft), Target move date, Next step date.

### 9. Require Next step date to enter Viewing (Letting)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Letting > stage row for Viewing > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Viewing asks for Next step date.

### 10. Require Viewing held, Headline rent (per year) to enter Offer (Letting)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Letting > stage row for Offer > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Offer asks for Viewing held, Headline rent (per year).

### 11. Require Heads of terms status, Headline rent (per year) to enter Heads of terms (Letting)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Letting > stage row for Heads of terms > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Heads of terms asks for Heads of terms status, Headline rent (per year).

### 12. Require Referencing status to enter Referencing (Letting)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Letting > stage row for Referencing > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Referencing asks for Referencing status.

### 13. Require Referencing status, Solicitors instructed, Close date to enter Legals (Letting)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Letting > stage row for Legals > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Legals asks for Referencing status, Solicitors instructed, Close date.

### 14. Require Headline rent (per year), Close date to enter Completed (Letting)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Letting > stage row for Completed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Completed asks for Headline rent (per year), Close date.

### 15. Require Lost reason to enter Lost (Letting)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Letting > stage row for Lost > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Lost asks for Lost reason.

### 16. Require Expiry date to enter Upcoming (Lease renewal)

- [ ] Where: Settings > Data Management > Objects > Leases > Pipelines tab > Lease renewal > stage row for Upcoming > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test lease into Upcoming asks for Expiry date.

### 17. Require Lease manager to enter Tenant contacted (Lease renewal)

- [ ] Where: Settings > Data Management > Objects > Leases > Pipelines tab > Lease renewal > stage row for Tenant contacted > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test lease into Tenant contacted asks for Lease manager.

### 18. Require Annual rent, Inside security of tenure to enter Terms discussed (Lease renewal)

- [ ] Where: Settings > Data Management > Objects > Leases > Pipelines tab > Lease renewal > stage row for Terms discussed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test lease into Terms discussed asks for Annual rent, Inside security of tenure.

### 19. Require Annual rent, Expiry date to enter Renewal agreed (Lease renewal)

- [ ] Where: Settings > Data Management > Objects > Leases > Pipelines tab > Lease renewal > stage row for Renewal agreed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test lease into Renewal agreed asks for Annual rent, Expiry date.

### 20. Require Annual rent, Expiry date to enter Renewed (Lease renewal)

- [ ] Where: Settings > Data Management > Objects > Leases > Pipelines tab > Lease renewal > stage row for Renewed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test lease into Renewed asks for Annual rent, Expiry date.

### 21. Require Outcome reason to enter Not renewed (Lease renewal)

- [ ] Where: Settings > Data Management > Objects > Leases > Pipelines tab > Lease renewal > stage row for Not renewed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test lease into Not renewed asks for Outcome reason.

## Decisions where the HubSpot mapping is lossy

### 22. Check the association limit for deal_property

- [ ] Where: Settings > Data Management > Objects > Deals > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 23. Check the association limit for property_landlord

- [ ] Where: Settings > Data Management > Objects > Properties > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 24. Check the association limit for lease_property

- [ ] Where: Settings > Data Management > Objects > Leases > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 25. Check the association limit for lease_tenant

- [ ] Where: Settings > Data Management > Objects > Leases > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 26. Check the association limit for lease_deal

- [ ] Where: Settings > Data Management > Objects > Leases > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 27. Accept that currency fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property carries no currency code: the symbol is a display choice.
- Done when: the client has agreed in the client notes. Fields: deal.headline_rent, property.asking_rent_psf, lease.annual_rent.

### 28. Accept that user fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property holds the HubSpot owner ID, so only users of the account can be chosen.
- Done when: the client has agreed in the client notes. Fields: lease.managing_owner.

## Workflows

### 29. Workflow: Create lease on completion

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A deal in the letting pipeline moves to completed.'; action 'Create a lease from the deal's rent and dates, link it to the property and the tenant, set the company's relationship status to current tenant and reduce the property's available area.'

### 30. Workflow: Open renewal

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A lease is 12 months from its expiry or break date and its status is active.'; action 'Move the lease to upcoming in the renewal pipeline and notify the lease manager.'

### 31. Workflow: Rent review reminder

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A lease's next rent review is 6 months away.'; action 'Create a task for the lease manager to prepare the rent review.'

### 32. Workflow: Flag stalled lettings

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'An open letting deal has no next step date, or the date is more than 7 days past.'; action 'Notify the deal owner and add the deal to the stalled lettings view.'

### 33. Workflow: Match requirement to space

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A deal reaches requirement qualified.'; action 'Create a task to list properties with available area and market area that fit the requirement.'

### 34. Workflow: Free the space

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A lease moves to not renewed.'; action 'Set its status to ended and create a task to update the property's availability.'

## Saved views

### 35. Saved view: Available space

- [ ] Where: CRM > Properties > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Available space shows on the Properties index with filter 'Availability is part available or fully available.' and sort 'Available area, largest first.'.

### 36. Saved view: Open lettings

- [ ] Where: CRM > Deals > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Open lettings shows on the Deals index with filter 'Owner is me and stage is open.' and sort 'Close date, soonest first.'.

### 37. Saved view: Stalled lettings

- [ ] Where: CRM > Deals > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Stalled lettings shows on the Deals index with filter 'Stage is open and next step date is empty or in the past.' and sort 'Next step date, oldest first.'.

### 38. Saved view: Expiries and breaks in 18 months

- [ ] Where: CRM > Leases > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Expiries and breaks in 18 months shows on the Leases index with filter 'Status is active and expiry date or break date is within 18 months.' and sort 'Expiry date, soonest first.'.

### 39. Saved view: Rent reviews due

- [ ] Where: CRM > Leases > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Rent reviews due shows on the Leases index with filter 'Status is active and next rent review is within 6 months.' and sort 'Next rent review, soonest first.'.

### 40. Saved view: Active requirements

- [ ] Where: CRM > Companies > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Active requirements shows on the Companies index with filter 'Relationship status is active requirement.' and sort 'Name, A to Z.'.

## Permissions

### 41. Set roles and access

- [ ] Where: Settings > Users & Teams (menu name not verified against a page in the research)
- Why it is manual: No permission-set API was found. Only pipeline stage edit permissions have one, and this blueprint does not use it.
- Done when: a non-admin test user sees and edits what their role needs and nothing more.
