# Manual steps: Manufacturing and distribution, B2B (hubspot)

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
- Done when: the tier is written in the client notes and the limits call allows 2 custom object(s) (Quote, Order).

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

### 6. Check closed stages of RFQ handling

- [ ] Where: Settings > Data Management > Objects > Quotes > Pipelines tab > RFQ handling
- Why it is manual: HubSpot has open or closed on custom object stages, not won or lost, and no probability (the design's probabilities are not sent). The API key for closed is unconfirmed (OQ-1).
- Done when: closed stages (Accepted, Declined) show as Closed. Set them by hand if the read-back says otherwise.

## Stage gates and lost reasons

### 7. Require Opportunity type to enter Identified (New accounts)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New accounts > stage row for Identified > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Identified asks for Opportunity type.

### 8. Require Next step date to enter First contact (New accounts)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New accounts > stage row for First contact > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into First contact asks for Next step date.

### 9. Require Specification confirmed, Annual volume estimate, Next step date to enter Needs confirmed (New accounts)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New accounts > stage row for Needs confirmed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Needs confirmed asks for Specification confirmed, Annual volume estimate, Next step date.

### 10. Require Sample status, Next step date to enter Sample or trial (New accounts)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New accounts > stage row for Sample or trial > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Sample or trial asks for Sample status, Next step date.

### 11. Require Amount, Specification confirmed, Next step date to enter Quote issued (New accounts)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New accounts > stage row for Quote issued > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Quote issued asks for Amount, Specification confirmed, Next step date.

### 12. Require Amount, Close date, Credit approved to enter Terms agreed (New accounts)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New accounts > stage row for Terms agreed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Terms agreed asks for Amount, Close date, Credit approved.

### 13. Require Amount, Close date to enter Closed won (New accounts)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New accounts > stage row for Closed won > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Closed won asks for Amount, Close date.

### 14. Require Lost reason to enter Closed lost (New accounts)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > New accounts > stage row for Closed lost > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Closed lost asks for Lost reason.

### 15. Require Received date, RFQ source to enter Received (RFQ handling)

- [ ] Where: Settings > Data Management > Objects > Quotes > Pipelines tab > RFQ handling > stage row for Received > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test quote into Received asks for Received date, RFQ source.

### 16. Require Product family, Quote due date to enter Qualified (RFQ handling)

- [ ] Where: Settings > Data Management > Objects > Quotes > Pipelines tab > RFQ handling > stage row for Qualified > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test quote into Qualified asks for Product family, Quote due date.

### 17. Require Stock checked, Lead time (days) to enter Pricing (RFQ handling)

- [ ] Where: Settings > Data Management > Objects > Quotes > Pipelines tab > RFQ handling > stage row for Pricing > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test quote into Pricing asks for Stock checked, Lead time (days).

### 18. Require Quote value, Margin, Approval needed to enter Approval (RFQ handling)

- [ ] Where: Settings > Data Management > Objects > Quotes > Pipelines tab > RFQ handling > stage row for Approval > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test quote into Approval asks for Quote value, Margin, Approval needed.

### 19. Require Quote value, Valid until, Lead time (days) to enter Sent (RFQ handling)

- [ ] Where: Settings > Data Management > Objects > Quotes > Pipelines tab > RFQ handling > stage row for Sent > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test quote into Sent asks for Quote value, Valid until, Lead time (days).

### 20. Require Quote value, Valid until to enter Follow-up (RFQ handling)

- [ ] Where: Settings > Data Management > Objects > Quotes > Pipelines tab > RFQ handling > stage row for Follow-up > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test quote into Follow-up asks for Quote value, Valid until.

### 21. Require Quote value to enter Accepted (RFQ handling)

- [ ] Where: Settings > Data Management > Objects > Quotes > Pipelines tab > RFQ handling > stage row for Accepted > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test quote into Accepted asks for Quote value.

### 22. Require Decline reason to enter Declined (RFQ handling)

- [ ] Where: Settings > Data Management > Objects > Quotes > Pipelines tab > RFQ handling > stage row for Declined > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test quote into Declined asks for Decline reason.

## Decisions where the HubSpot mapping is lossy

### 23. Check the association limit for quote_company

- [ ] Where: Settings > Data Management > Objects > Quotes > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 24. Check the association limit for quote_person

- [ ] Where: Settings > Data Management > Objects > Quotes > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 25. Check the association limit for quote_deal

- [ ] Where: Settings > Data Management > Objects > Quotes > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 26. Check the association limit for order_company

- [ ] Where: Settings > Data Management > Objects > Orders > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 27. Check the association limit for order_quote

- [ ] Where: Settings > Data Management > Objects > Orders > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 28. Accept that currency fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property carries no currency code: the symbol is a display choice.
- Done when: the client has agreed in the client notes. Fields: deal.annual_volume_estimate, quote.value, order.order_value.

### 29. Accept that percent fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property the stored value (0.2 or 20) is unconfirmed (open question OQ-5).
- Done when: the client has agreed in the client notes. Fields: quote.margin_percent.

### 30. Accept that user fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property holds the HubSpot owner ID, so only users of the account can be chosen.
- Done when: the client has agreed in the client notes. Fields: quote.owner, order.owner.

## Workflows

### 31. Workflow: Update company on order

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'An order is created or its status moves to received.'; action 'Set the company's last order date and account status to active, and set the order type to first order if the company had no earlier order.'

### 32. Workflow: Flag late quotes

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A quote is open and its due date is today or in the past.'; action 'Notify the quote owner and add the quote to the overdue quotes view.'

### 33. Workflow: Chase sent quotes

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A quote has been in sent for 5 working days.'; action 'Create a task for the owner to chase the buyer and move the quote to follow-up when done.'

### 34. Workflow: Reorder due

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'Days since the company's last order date exceed its expected reorder interval and the account is active.'; action 'Create a task for the account owner to call the buyer and set the account status to dormant after 2 intervals.'

### 35. Workflow: Route quote for approval

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A quote moves to approval.'; action 'Notify the sales manager, who either approves it or sends it back to pricing.'

### 36. Workflow: Quarterly tier review

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'Each quarter, for every active account.'; action 'Compare the account's annual spend band with its tier and list mismatches for the sales manager.'

## Saved views

### 37. Saved view: Open quotes

- [ ] Where: CRM > Quotes > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Open quotes shows on the Quotes index with filter 'Quote is not accepted or declined and owner is me.' and sort 'Due date, soonest first.'.

### 38. Saved view: Overdue quotes

- [ ] Where: CRM > Quotes > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Overdue quotes shows on the Quotes index with filter 'Quote is open and due date is in the past.' and sort 'Due date, oldest first.'.

### 39. Saved view: Reorders due

- [ ] Where: CRM > Companies > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Reorders due shows on the Companies index with filter 'Account status is active and last order date is older than the expected reorder interval.' and sort 'Last order date, oldest first.'.

### 40. Saved view: Key and core accounts

- [ ] Where: CRM > Companies > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Key and core accounts shows on the Companies index with filter 'Account tier is key account or core.' and sort 'Last order date, oldest first.'.

### 41. Saved view: Orders in flight

- [ ] Where: CRM > Orders > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Orders in flight shows on the Orders index with filter 'Status is not delivered, invoiced or cancelled.' and sort 'Promised date, soonest first.'.

### 42. Saved view: My open opportunities

- [ ] Where: CRM > Deals > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view My open opportunities shows on the Deals index with filter 'Owner is me and stage is open.' and sort 'Next step date, soonest first.'.

## Permissions

### 43. Set roles and access

- [ ] Where: Settings > Users & Teams (menu name not verified against a page in the research)
- Why it is manual: No permission-set API was found. Only pipeline stage edit permissions have one, and this blueprint does not use it.
- Done when: a non-admin test user sees and edits what their role needs and nothing more.
