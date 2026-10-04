# Manual steps: Wholesale and ecommerce brand, B2B (hubspot)

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
- Done when: the tier is written in the client notes and the limits call allows 2 custom object(s) (Territory, Wholesale order).

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

### 6. Check closed stages of Order status

- [ ] Where: Settings > Data Management > Objects > Wholesale orders > Pipelines tab > Order status
- Why it is manual: HubSpot has open or closed on custom object stages, not won or lost, and no probability (the design's probabilities are not sent). The API key for closed is unconfirmed (OQ-1).
- Done when: closed stages (Delivered and paid, Cancelled) show as Closed. Set them by hand if the read-back says otherwise.

## Stage gates and lost reasons

### 7. Require Next step date to enter Identified (Retailer acquisition)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Retailer acquisition > stage row for Identified > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Identified asks for Next step date.

### 8. Require Next step date to enter Contacted (Retailer acquisition)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Retailer acquisition > stage row for Contacted > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Contacted asks for Next step date.

### 9. Require Line sheet sent, Buying season to enter Line sheet sent (Retailer acquisition)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Retailer acquisition > stage row for Line sheet sent > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Line sheet sent asks for Line sheet sent, Buying season.

### 10. Require Samples status, Next step date to enter Range review (Retailer acquisition)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Retailer acquisition > stage row for Range review > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Range review asks for Samples status, Next step date.

### 11. Require Expected first order value, Next step date to enter Terms discussion (Retailer acquisition)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Retailer acquisition > stage row for Terms discussion > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Terms discussion asks for Expected first order value, Next step date.

### 12. Require Terms agreed, Account application received to enter Account setup (Retailer acquisition)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Retailer acquisition > stage row for Account setup > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Account setup asks for Terms agreed, Account application received.

### 13. Require Amount, Close date to enter Account opened (Retailer acquisition)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Retailer acquisition > stage row for Account opened > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Account opened asks for Amount, Close date.

### 14. Require Lost reason to enter Closed lost (Retailer acquisition)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Retailer acquisition > stage row for Closed lost > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Closed lost asks for Lost reason.

### 15. Require Order type, Order channel, Order value to enter Placed (Order status)

- [ ] Where: Settings > Data Management > Objects > Wholesale orders > Pipelines tab > Order status > stage row for Placed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test wholesale_order into Placed asks for Order type, Order channel, Order value.

### 16. Require Ship date, Units to enter Confirmed (Order status)

- [ ] Where: Settings > Data Management > Objects > Wholesale orders > Pipelines tab > Order status > stage row for Confirmed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test wholesale_order into Confirmed asks for Ship date, Units.

### 17. Require Ship date to enter Picking (Order status)

- [ ] Where: Settings > Data Management > Objects > Wholesale orders > Pipelines tab > Order status > stage row for Picking > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test wholesale_order into Picking asks for Ship date.

### 18. Require Ship date to enter Shipped (Order status)

- [ ] Where: Settings > Data Management > Objects > Wholesale orders > Pipelines tab > Order status > stage row for Shipped > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test wholesale_order into Shipped asks for Ship date.

### 19. Require Payment status to enter Delivered and paid (Order status)

- [ ] Where: Settings > Data Management > Objects > Wholesale orders > Pipelines tab > Order status > stage row for Delivered and paid > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test wholesale_order into Delivered and paid asks for Payment status.

### 20. Require Cancel reason to enter Cancelled (Order status)

- [ ] Where: Settings > Data Management > Objects > Wholesale orders > Pipelines tab > Order status > stage row for Cancelled > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test wholesale_order into Cancelled asks for Cancel reason.

## Decisions where the HubSpot mapping is lossy

### 21. Check the association limit for company_territory

- [ ] Where: Settings > Data Management > Objects > Companies > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 22. Check the association limit for wholesale_order_company

- [ ] Where: Settings > Data Management > Objects > Wholesale orders > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 23. Check the association limit for wholesale_order_person

- [ ] Where: Settings > Data Management > Objects > Wholesale orders > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 24. Check the association limit for wholesale_order_deal

- [ ] Where: Settings > Data Management > Objects > Wholesale orders > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 25. Accept that currency fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property carries no currency code: the symbol is a display choice.
- Done when: the client has agreed in the client notes. Fields: company.credit_limit, deal.first_order_expected, territory.annual_target, wholesale_order.order_value.

### 26. Accept that user fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property holds the HubSpot owner ID, so only users of the account can be chosen.
- Done when: the client has agreed in the client notes. Fields: company.territory_owner, territory.rep, wholesale_order.owner.

## Workflows

### 27. Workflow: Update retailer on order

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A wholesale order is created.'; action 'Set the company's last order date, add one to its order count, set first order date if empty, and set its account status to active.'

### 28. Workflow: Close deal on first order

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A first order linked to an account-acquisition deal moves to confirmed.'; action 'Move the deal to account opened and set the company account status to onboarding.'

### 29. Workflow: Reorder nudge

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'Days since the last order exceed the retailer's reorder cycle and the account is active.'; action 'Create a task for the account rep to contact the buyer and set the account status to at risk.'

### 30. Workflow: Second order check

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A retailer's first order was delivered 45 days ago and its order count is 1.'; action 'Create a task for the account rep to ask for feedback and a reorder.'

### 31. Workflow: Mark lapsed

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A retailer has no order for twice its reorder cycle.'; action 'Set the account status to lapsed and notify the territory rep.'

### 32. Workflow: Vacant territory alert

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A territory status changes to vacant.'; action 'Notify the sales manager and reassign its open deals to the manager.'

## Saved views

### 33. Saved view: My retailers

- [ ] Where: CRM > Companies > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view My retailers shows on the Companies index with filter 'Account rep is me and account status is active, onboarding or at risk.' and sort 'Last order date, oldest first.'.

### 34. Saved view: Reorders overdue

- [ ] Where: CRM > Companies > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Reorders overdue shows on the Companies index with filter 'Account status is active or at risk and last order date is older than the reorder cycle.' and sort 'Last order date, oldest first.'.

### 35. Saved view: One-order retailers

- [ ] Where: CRM > Companies > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view One-order retailers shows on the Companies index with filter 'Orders to date is 1 and first order date is more than 45 days ago.' and sort 'First order date, oldest first.'.

### 36. Saved view: Open orders

- [ ] Where: CRM > Wholesale orders > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Open orders shows on the Wholesale orders index with filter 'Status is not delivered or cancelled.' and sort 'Ship date, soonest first.'.

### 37. Saved view: Territory overview

- [ ] Where: CRM > Territories > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Territory overview shows on the Territories index with filter 'Status is covered or vacant.' and sort 'Name, A to Z.'.

### 38. Saved view: My retailer pipeline

- [ ] Where: CRM > Deals > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view My retailer pipeline shows on the Deals index with filter 'Owner is me and stage is open.' and sort 'Next step date, soonest first.'.

## Permissions

### 39. Set roles and access

- [ ] Where: Settings > Users & Teams (menu name not verified against a page in the research)
- Why it is manual: No permission-set API was found. Only pipeline stage edit permissions have one, and this blueprint does not use it.
- Done when: a non-admin test user sees and edits what their role needs and nothing more.
