# Manual steps: Manufacturing and distribution, B2B (attio)

Generated from `design.yaml`. Do not edit by hand. The Attio API cannot do any of this.
Sources: https://docs.attio.com/llms.txt, https://api.attio.com/openapi/api, `platforms/attio/reference/api-coverage.md`.

## Before and during the build

### 1. Confirm the client's Attio plan allows the objects below

- [ ] Where: Workspace settings, then Billing, and https://attio.com/pricing
- Why it is manual: Object limits depend on the plan (3, 5, 12 or unlimited) and Attio does not say whether standard objects count. A create past the limit fails with 400 quota_exceeded.
- Done when: the plan is written in the client notes and allows 2 custom object(s) (Quote, Order).

### 2. Enable the Deals object

- [ ] Where: Workspace settings, then Objects, then enable Deals
- Why it is manual: Deals are off by default and the API has no call to enable them.
- Done when: Deals appears in the sidebar and `GET /v2/objects` lists `deals`. Do this before running relationships.json, lists.json or attributes.json.

### 3. Test the first relationship from both sides

- [ ] Where: Create the first entry of relationships.json, then open both objects
- Why it is manual: Attio's description of the cardinality flags is ambiguous (platforms/attio/reference/open-questions.md, Q7).
- Done when: the reverse attribute's is_multiselect matches the cardinality in build-sheet.md. If it is reversed, swap the two flags in relationships.json and regenerate.

### 4. Check default statuses on each new Stage attribute

- [ ] Where: Lists in the left sidebar, then the list, then the Stage attribute settings
- Why it is manual: Attio does not document whether a new status attribute starts empty (Q6). The API cannot delete a status.
- Done when: only the stages named in build-sheet.md are active. Archive any extra default status by hand.

### 5. Confirm the Name attribute on custom objects

- [ ] Where: Workspace settings, then Objects, then each custom object, then Attributes
- Why it is manual: A design field called name is not created, because Attio gives a custom object its own name and the slug would clash. The research did not confirm this by a live test.
- Done when: each of these objects has a Name attribute: Quote, Order. If one does not, add a text attribute with slug `name`.

## Pipelines

### 6. Hide the native Deal stage for New accounts

- [ ] Where: Deals object, then the table or board view, then hide the Stage column
- Why it is manual: Deals require a native stage. The working pipeline is the list `new_accounts`, so the native stage would show a second, unused set (Q8).
- Done when: new deals get the first native stage by default and the Deals views use the list's Stage.

### 7. Check the stage order of New accounts

- [ ] Where: Lists in the left sidebar, then New accounts, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Identified then First contact then Needs confirmed then Sample or trial then Quote issued then Terms agreed then Closed won then Closed lost.

### 8. Stage probability for New accounts

- [ ] Where: Lists in the left sidebar, then New accounts, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Identified 5%; First contact 10%; Needs confirmed 25%; Sample or trial 40%; Quote issued 55%; Terms agreed 80%; Closed won 100%; Closed lost 0%) and forecast reports multiply by it.

### 9. Won and lost in New accounts

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Closed won for won and Closed lost for lost.

### 10. Check the stage order of RFQ handling

- [ ] Where: Lists in the left sidebar, then RFQ handling, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Received then Qualified then Pricing then Approval then Sent then Follow-up then Accepted then Declined.

### 11. Stage probability for RFQ handling

- [ ] Where: Lists in the left sidebar, then RFQ handling, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Received 20%; Qualified 30%; Pricing 40%; Approval 45%; Sent 50%; Follow-up 60%; Accepted 100%; Declined 0%) and forecast reports multiply by it.

### 12. Won and lost in RFQ handling

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Accepted for won and Declined for lost.

## Stage gates and lost reasons

### 13. Stage gate (stage gate): New accounts, Identified

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New accounts where Stage is Identified
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Identified with any of these empty are flagged or sent back: Opportunity type. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 14. Stage gate (stage gate): New accounts, First contact

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New accounts where Stage is First contact
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering First contact with any of these empty are flagged or sent back: Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 15. Stage gate (stage gate): New accounts, Needs confirmed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New accounts where Stage is Needs confirmed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Needs confirmed with any of these empty are flagged or sent back: Specification confirmed, Annual volume estimate, Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 16. Stage gate (stage gate): New accounts, Sample or trial

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New accounts where Stage is Sample or trial
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Sample or trial with any of these empty are flagged or sent back: Sample status, Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 17. Stage gate (stage gate): New accounts, Quote issued

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New accounts where Stage is Quote issued
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Quote issued with any of these empty are flagged or sent back: Amount, Specification confirmed, Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 18. Stage gate (stage gate): New accounts, Terms agreed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New accounts where Stage is Terms agreed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Terms agreed with any of these empty are flagged or sent back: Amount, Close date, Credit approved. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 19. Stage gate (stage gate): New accounts, Closed won

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New accounts where Stage is Closed won
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Closed won with any of these empty are flagged or sent back: Amount, Close date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 20. Stage gate (lost reason): New accounts, Closed lost

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New accounts where Stage is Closed lost
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Closed lost with any of these empty are flagged or sent back: Lost reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 21. Stage gate (stage gate): RFQ handling, Received

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on RFQ handling where Stage is Received
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Received with any of these empty are flagged or sent back: Received date, RFQ source. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 22. Stage gate (stage gate): RFQ handling, Qualified

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on RFQ handling where Stage is Qualified
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Qualified with any of these empty are flagged or sent back: Product family, Quote due date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 23. Stage gate (stage gate): RFQ handling, Pricing

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on RFQ handling where Stage is Pricing
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Pricing with any of these empty are flagged or sent back: Stock checked, Lead time (days). A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 24. Stage gate (stage gate): RFQ handling, Approval

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on RFQ handling where Stage is Approval
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Approval with any of these empty are flagged or sent back: Quote value, Margin, Approval needed. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 25. Stage gate (stage gate): RFQ handling, Sent

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on RFQ handling where Stage is Sent
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Sent with any of these empty are flagged or sent back: Quote value, Valid until, Lead time (days). A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 26. Stage gate (stage gate): RFQ handling, Follow-up

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on RFQ handling where Stage is Follow-up
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Follow-up with any of these empty are flagged or sent back: Quote value, Valid until. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 27. Stage gate (stage gate): RFQ handling, Accepted

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on RFQ handling where Stage is Accepted
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Accepted with any of these empty are flagged or sent back: Quote value. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 28. Stage gate (lost reason): RFQ handling, Declined

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on RFQ handling where Stage is Declined
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Declined with any of these empty are flagged or sent back: Decline reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

## Decisions where the Attio mapping is lossy

### 29. Renamed attribute slugs

- [ ] Where: Decide with the client; edit platform_overrides.attio in design.yaml and regenerate
- Why it is manual: These keys are slugs Attio uses on its own objects, so the slug got an object prefix.
- Done when: company.owner -> company_owner; person.owner -> person_owner; quote.owner -> quote_owner; order.owner -> order_owner. Each is accepted or overridden.

### 30. Percent fields are plain numbers

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Decide whether percentages are stored as 0 to 100 or 0 to 1. The generated description says 0 to 100. Fields: quote.margin_percent.

### 31. Long text is the same type as text

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that long text fields look like short text fields in Attio. Fields: deal.description.

### 32. Currency fields use GBP

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Confirm the account currency. One currency per attribute: change it before data is loaded, because a later change does not convert values. Fields: deal.annual_volume_estimate, quote.value, order.order_value.

### 33. Phone values must be E.164

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Agree that numbers are written with a + and country code, or with a country code field, on import. Fields: company.phone.

### 34. User fields hold workspace members only

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that people outside the workspace cannot be chosen. Fields: company.owner, person.owner, quote.owner, order.owner.

### 35. Checkbox fields cannot be empty

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that unticked and unknown look the same. Fields: deal.spec_confirmed, deal.credit_approved, quote.approval_needed, quote.stock_checked.

## Workflows

### 36. Workflow: Update company on order

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'An order is created or its status moves to received.'; action 'Set the company's last order date and account status to active, and set the order type to first order if the company had no earlier order.'

### 37. Workflow: Flag late quotes

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A quote is open and its due date is today or in the past.'; action 'Notify the quote owner and add the quote to the overdue quotes view.'

### 38. Workflow: Chase sent quotes

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A quote has been in sent for 5 working days.'; action 'Create a task for the owner to chase the buyer and move the quote to follow-up when done.'

### 39. Workflow: Reorder due

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'Days since the company's last order date exceed its expected reorder interval and the account is active.'; action 'Create a task for the account owner to call the buyer and set the account status to dormant after 2 intervals.'

### 40. Workflow: Route quote for approval

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A quote moves to approval.'; action 'Notify the sales manager, who either approves it or sends it back to pricing.'

### 41. Workflow: Quarterly tier review

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'Each quarter, for every active account.'; action 'Compare the account's annual spend band with its tier and list mismatches for the sales manager.'

## Views

### 42. View: Open quotes

- [ ] Where: Open Quotes in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Open quotes is saved with filter 'Quote is not accepted or declined and owner is me.' and sort 'Due date, soonest first.'.

### 43. View: Overdue quotes

- [ ] Where: Open Quotes in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Overdue quotes is saved with filter 'Quote is open and due date is in the past.' and sort 'Due date, oldest first.'.

### 44. View: Reorders due

- [ ] Where: Open Companies in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Reorders due is saved with filter 'Account status is active and last order date is older than the expected reorder interval.' and sort 'Last order date, oldest first.'.

### 45. View: Key and core accounts

- [ ] Where: Open Companies in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Key and core accounts is saved with filter 'Account tier is key account or core.' and sort 'Last order date, oldest first.'.

### 46. View: Orders in flight

- [ ] Where: Open Orders in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Orders in flight is saved with filter 'Status is not delivered, invoiced or cancelled.' and sort 'Promised date, soonest first.'.

### 47. View: My open opportunities

- [ ] Where: Open Deals in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view My open opportunities is saved with filter 'Owner is me and stage is open.' and sort 'Next step date, soonest first.'.

## Permissions

### 48. Set roles and access

- [ ] Where: Workspace settings, then Members
- Why it is manual: Attio has no API for workspace roles or object and field access.
- Done when: a non-admin test member sees and edits what their role needs and nothing more.
