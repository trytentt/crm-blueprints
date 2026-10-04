# Manual steps: Wholesale and ecommerce brand, B2B (attio)

Generated from `design.yaml`. Do not edit by hand. The Attio API cannot do any of this.
Sources: https://docs.attio.com/llms.txt, https://api.attio.com/openapi/api, `platforms/attio/reference/api-coverage.md`.

## Before and during the build

### 1. Confirm the client's Attio plan allows the objects below

- [ ] Where: Workspace settings, then Billing, and https://attio.com/pricing
- Why it is manual: Object limits depend on the plan (3, 5, 12 or unlimited) and Attio does not say whether standard objects count. A create past the limit fails with 400 quota_exceeded.
- Done when: the plan is written in the client notes and allows 2 custom object(s) (Territory, Wholesale order).

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
- Done when: each of these objects has a Name attribute: Territory, Wholesale order. If one does not, add a text attribute with slug `name`.

## Pipelines

### 6. Hide the native Deal stage for Retailer acquisition

- [ ] Where: Deals object, then the table or board view, then hide the Stage column
- Why it is manual: Deals require a native stage. The working pipeline is the list `retailer_acquisition`, so the native stage would show a second, unused set (Q8).
- Done when: new deals get the first native stage by default and the Deals views use the list's Stage.

### 7. Check the stage order of Retailer acquisition

- [ ] Where: Lists in the left sidebar, then Retailer acquisition, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Identified then Contacted then Line sheet sent then Range review then Terms discussion then Account setup then Account opened then Closed lost.

### 8. Stage probability for Retailer acquisition

- [ ] Where: Lists in the left sidebar, then Retailer acquisition, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Identified 5%; Contacted 10%; Line sheet sent 25%; Range review 40%; Terms discussion 60%; Account setup 80%; Account opened 100%; Closed lost 0%) and forecast reports multiply by it.

### 9. Won and lost in Retailer acquisition

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Account opened for won and Closed lost for lost.

### 10. Check the stage order of Order status

- [ ] Where: Lists in the left sidebar, then Order status, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Placed then Confirmed then Picking then Shipped then Delivered and paid then Cancelled.

### 11. Stage probability for Order status

- [ ] Where: Lists in the left sidebar, then Order status, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Placed 40%; Confirmed 60%; Picking 75%; Shipped 90%; Delivered and paid 100%; Cancelled 0%) and forecast reports multiply by it.

### 12. Won and lost in Order status

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Delivered and paid for won and Cancelled for lost.

## Stage gates and lost reasons

### 13. Stage gate (stage gate): Retailer acquisition, Identified

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Retailer acquisition where Stage is Identified
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Identified with any of these empty are flagged or sent back: Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 14. Stage gate (stage gate): Retailer acquisition, Contacted

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Retailer acquisition where Stage is Contacted
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Contacted with any of these empty are flagged or sent back: Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 15. Stage gate (stage gate): Retailer acquisition, Line sheet sent

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Retailer acquisition where Stage is Line sheet sent
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Line sheet sent with any of these empty are flagged or sent back: Line sheet sent, Buying season. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 16. Stage gate (stage gate): Retailer acquisition, Range review

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Retailer acquisition where Stage is Range review
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Range review with any of these empty are flagged or sent back: Samples status, Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 17. Stage gate (stage gate): Retailer acquisition, Terms discussion

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Retailer acquisition where Stage is Terms discussion
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Terms discussion with any of these empty are flagged or sent back: Expected first order value, Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 18. Stage gate (stage gate): Retailer acquisition, Account setup

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Retailer acquisition where Stage is Account setup
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Account setup with any of these empty are flagged or sent back: Terms agreed, Account application received. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 19. Stage gate (stage gate): Retailer acquisition, Account opened

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Retailer acquisition where Stage is Account opened
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Account opened with any of these empty are flagged or sent back: Amount, Close date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 20. Stage gate (lost reason): Retailer acquisition, Closed lost

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Retailer acquisition where Stage is Closed lost
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Closed lost with any of these empty are flagged or sent back: Lost reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 21. Stage gate (stage gate): Order status, Placed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Order status where Stage is Placed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Placed with any of these empty are flagged or sent back: Order type, Order channel, Order value. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 22. Stage gate (stage gate): Order status, Confirmed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Order status where Stage is Confirmed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Confirmed with any of these empty are flagged or sent back: Ship date, Units. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 23. Stage gate (stage gate): Order status, Picking

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Order status where Stage is Picking
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Picking with any of these empty are flagged or sent back: Ship date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 24. Stage gate (stage gate): Order status, Shipped

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Order status where Stage is Shipped
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Shipped with any of these empty are flagged or sent back: Ship date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 25. Stage gate (stage gate): Order status, Delivered and paid

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Order status where Stage is Delivered and paid
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Delivered and paid with any of these empty are flagged or sent back: Payment status. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 26. Stage gate (lost reason): Order status, Cancelled

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Order status where Stage is Cancelled
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Cancelled with any of these empty are flagged or sent back: Cancel reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

## Decisions where the Attio mapping is lossy

### 27. Renamed attribute slugs

- [ ] Where: Decide with the client; edit platform_overrides.attio in design.yaml and regenerate
- Why it is manual: These keys are slugs Attio uses on its own objects, so the slug got an object prefix.
- Done when: company.owner -> company_owner; person.owner -> person_owner; wholesale_order.owner -> wholesale_order_owner. Each is accepted or overridden.

### 28. Long text is the same type as text

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that long text fields look like short text fields in Attio. Fields: deal.description.

### 29. Currency fields use GBP

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Confirm the account currency. One currency per attribute: change it before data is loaded, because a later change does not convert values. Fields: company.credit_limit, deal.first_order_expected, territory.annual_target, wholesale_order.order_value.

### 30. Phone values must be E.164

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Agree that numbers are written with a + and country code, or with a country code field, on import. Fields: company.phone.

### 31. User fields hold workspace members only

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that people outside the workspace cannot be chosen. Fields: company.owner, person.owner, company.territory_owner, territory.rep, wholesale_order.owner.

### 32. Checkbox fields cannot be empty

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that unticked and unknown look the same. Fields: deal.line_sheet_sent, deal.terms_agreed, deal.account_application_received.

## Workflows

### 33. Workflow: Update retailer on order

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A wholesale order is created.'; action 'Set the company's last order date, add one to its order count, set first order date if empty, and set its account status to active.'

### 34. Workflow: Close deal on first order

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A first order linked to an account-acquisition deal moves to confirmed.'; action 'Move the deal to account opened and set the company account status to onboarding.'

### 35. Workflow: Reorder nudge

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'Days since the last order exceed the retailer's reorder cycle and the account is active.'; action 'Create a task for the account rep to contact the buyer and set the account status to at risk.'

### 36. Workflow: Second order check

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A retailer's first order was delivered 45 days ago and its order count is 1.'; action 'Create a task for the account rep to ask for feedback and a reorder.'

### 37. Workflow: Mark lapsed

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A retailer has no order for twice its reorder cycle.'; action 'Set the account status to lapsed and notify the territory rep.'

### 38. Workflow: Vacant territory alert

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A territory status changes to vacant.'; action 'Notify the sales manager and reassign its open deals to the manager.'

## Views

### 39. View: My retailers

- [ ] Where: Open Companies in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view My retailers is saved with filter 'Account rep is me and account status is active, onboarding or at risk.' and sort 'Last order date, oldest first.'.

### 40. View: Reorders overdue

- [ ] Where: Open Companies in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Reorders overdue is saved with filter 'Account status is active or at risk and last order date is older than the reorder cycle.' and sort 'Last order date, oldest first.'.

### 41. View: One-order retailers

- [ ] Where: Open Companies in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view One-order retailers is saved with filter 'Orders to date is 1 and first order date is more than 45 days ago.' and sort 'First order date, oldest first.'.

### 42. View: Open orders

- [ ] Where: Open Wholesale orders in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Open orders is saved with filter 'Status is not delivered or cancelled.' and sort 'Ship date, soonest first.'.

### 43. View: Territory overview

- [ ] Where: Open Territories in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Territory overview is saved with filter 'Status is covered or vacant.' and sort 'Name, A to Z.'.

### 44. View: My retailer pipeline

- [ ] Where: Open Deals in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view My retailer pipeline is saved with filter 'Owner is me and stage is open.' and sort 'Next step date, soonest first.'.

## Permissions

### 45. Set roles and access

- [ ] Where: Workspace settings, then Members
- Why it is manual: Attio has no API for workspace roles or object and field access.
- Done when: a non-admin test member sees and edits what their role needs and nothing more.
