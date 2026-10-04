# Manual steps: B2B SaaS, product-led (attio)

Generated from `design.yaml`. Do not edit by hand. The Attio API cannot do any of this.
Sources: https://docs.attio.com/llms.txt, https://api.attio.com/openapi/api, `platforms/attio/reference/api-coverage.md`.

## Before and during the build

### 1. Confirm the client's Attio plan allows the objects below

- [ ] Where: Workspace settings, then Billing, and https://attio.com/pricing
- Why it is manual: Object limits depend on the plan (3, 5, 12 or unlimited) and Attio does not say whether standard objects count. A create past the limit fails with 400 quota_exceeded.
- Done when: the plan is written in the client notes and allows 2 custom object(s) (Workspace, Adoption plan).

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

### 5. Mark Product workspace ID on workspace as required

- [ ] Where: Workspace settings, then Objects, then workspace, then Attributes, then Product workspace ID, then Required
- Why it is manual: Attributes are created not required. Attio may demand a default for a required attribute, and a required attribute can break record creation from other tools (Q5).
- Done when: Product workspace ID is required and a test record without it is refused.

### 6. Confirm the Name attribute on custom objects

- [ ] Where: Workspace settings, then Objects, then each custom object, then Attributes
- Why it is manual: A design field called name is not created, because Attio gives a custom object its own name and the slug would clash. The research did not confirm this by a live test.
- Done when: each of these objects has a Name attribute: Workspace, Adoption plan. If one does not, add a text attribute with slug `name`.

## Pipelines

### 7. Hide the native Deal stage for Sales assist

- [ ] Where: Deals object, then the table or board view, then hide the Stage column
- Why it is manual: Deals require a native stage. The working pipeline is the list `sales_assist`, so the native stage would show a second, unused set (Q8).
- Done when: new deals get the first native stage by default and the Deals views use the list's Stage.

### 8. Check the stage order of Sales assist

- [ ] Where: Lists in the left sidebar, then Sales assist, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Product-qualified lead then Conversation then Need confirmed then Proposal then Negotiation then Closed won then Closed lost.

### 9. Stage probability for Sales assist

- [ ] Where: Lists in the left sidebar, then Sales assist, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Product-qualified lead 10%; Conversation 25%; Need confirmed 45%; Proposal 65%; Negotiation 80%; Closed won 100%; Closed lost 0%) and forecast reports multiply by it.

### 10. Won and lost in Sales assist

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Closed won for won and Closed lost for lost.

### 11. Hide the native Deal stage for Expansion

- [ ] Where: Deals object, then the table or board view, then hide the Stage column
- Why it is manual: Deals require a native stage. The working pipeline is the list `expansion`, so the native stage would show a second, unused set (Q8).
- Done when: new deals get the first native stage by default and the Deals views use the list's Stage.

### 12. Check the stage order of Expansion

- [ ] Where: Lists in the left sidebar, then Expansion, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Expansion signal then Outreach then Proposal then Negotiation then Expanded then Declined.

### 13. Stage probability for Expansion

- [ ] Where: Lists in the left sidebar, then Expansion, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Expansion signal 20%; Outreach 35%; Proposal 60%; Negotiation 80%; Expanded 100%; Declined 0%) and forecast reports multiply by it.

### 14. Won and lost in Expansion

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Expanded for won and Declined for lost.

## Stage gates and lost reasons

### 15. Stage gate (stage gate): Sales assist, Product-qualified lead

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Sales assist where Stage is Product-qualified lead
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Product-qualified lead with any of these empty are flagged or sent back: PQL trigger. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 16. Stage gate (stage gate): Sales assist, Conversation

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Sales assist where Stage is Conversation
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Conversation with any of these empty are flagged or sent back: Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 17. Stage gate (stage gate): Sales assist, Need confirmed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Sales assist where Stage is Need confirmed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Need confirmed with any of these empty are flagged or sent back: Need summary, Expected seats, Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 18. Stage gate (stage gate): Sales assist, Proposal

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Sales assist where Stage is Proposal
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Proposal with any of these empty are flagged or sent back: Amount, Target plan, Expected seats, Billing term. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 19. Stage gate (stage gate): Sales assist, Negotiation

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Sales assist where Stage is Negotiation
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Negotiation with any of these empty are flagged or sent back: Amount, Close date, Security review. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 20. Stage gate (stage gate): Sales assist, Closed won

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Sales assist where Stage is Closed won
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Closed won with any of these empty are flagged or sent back: Amount, Close date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 21. Stage gate (lost reason): Sales assist, Closed lost

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Sales assist where Stage is Closed lost
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Closed lost with any of these empty are flagged or sent back: Lost reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 22. Stage gate (stage gate): Expansion, Expansion signal

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Expansion where Stage is Expansion signal
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Expansion signal with any of these empty are flagged or sent back: Expansion type. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 23. Stage gate (stage gate): Expansion, Outreach

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Expansion where Stage is Outreach
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Outreach with any of these empty are flagged or sent back: Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 24. Stage gate (stage gate): Expansion, Proposal

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Expansion where Stage is Proposal
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Proposal with any of these empty are flagged or sent back: Amount, Expected seats, Target plan. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 25. Stage gate (stage gate): Expansion, Negotiation

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Expansion where Stage is Negotiation
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Negotiation with any of these empty are flagged or sent back: Amount, Close date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 26. Stage gate (stage gate): Expansion, Expanded

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Expansion where Stage is Expanded
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Expanded with any of these empty are flagged or sent back: Amount, Close date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 27. Stage gate (lost reason): Expansion, Declined

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Expansion where Stage is Declined
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Declined with any of these empty are flagged or sent back: Lost reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

## Decisions where the Attio mapping is lossy

### 28. Renamed attribute slugs

- [ ] Where: Decide with the client; edit platform_overrides.attio in design.yaml and regenerate
- Why it is manual: These keys are slugs Attio uses on its own objects, so the slug got an object prefix.
- Done when: company.owner -> company_owner; person.owner -> person_owner; adoption_plan.owner -> adoption_plan_owner. Each is accepted or overridden.

### 29. Percent fields are plain numbers

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Decide whether percentages are stored as 0 to 100 or 0 to 1. The generated description says 0 to 100. Fields: workspace.limit_usage_percent.

### 30. Long text is the same type as text

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that long text fields look like short text fields in Attio. Fields: deal.description, deal.need_summary, adoption_plan.success_criteria.

### 31. Currency fields use GBP

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Confirm the account currency. One currency per attribute: change it before data is loaded, because a later change does not convert values. Fields: workspace.mrr.

### 32. Phone values must be E.164

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Agree that numbers are written with a + and country code, or with a country code field, on import. Fields: company.phone.

### 33. User fields hold workspace members only

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that people outside the workspace cannot be chosen. Fields: company.owner, person.owner, adoption_plan.owner.

### 34. Checkbox fields cannot be empty

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that unticked and unknown look the same. Fields: workspace.activated.

## Workflows

### 35. Workflow: Sync product usage

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'Nightly, and when a workspace is created or its plan changes in the product.'; action 'Upsert the workspace by product workspace ID with plan, seats, active users, limit used and last active date, and link the people who are members.'

### 36. Workflow: Flag product-qualified lead

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A workspace meets the PQL rule and its PQL status is not qualified, accepted or rejected.'; action 'Set PQL status to qualified, notify the sales-assist queue, and create a deal in the sales assist pipeline at product-qualified lead once a rep accepts, with the PQL trigger filled.'

### 37. Workflow: Open expansion deal

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'Seats used exceed seats paid, or plan limit used passes 80 percent, on a paying workspace with no open expansion deal.'; action 'Create a deal in the expansion pipeline at expansion signal, linked to the workspace, and assign it to the account owner.'

### 38. Workflow: Start adoption plan

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A sales-assist deal moves to closed won.'; action 'Create an adoption plan linked to the workspace, assign it to customer success and set the company to paying.'

### 39. Workflow: Trial ending alert

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A workspace on a trial has a trial end date in 3 days and is activated.'; action 'Notify the account owner, or the sales-assist queue if the workspace has no owner.'

### 40. Workflow: Flag stalled deals

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'An open deal has no next step date, or the date is more than 7 days past.'; action 'Notify the deal owner and add the deal to the stalled deals view.'

## Views

### 41. View: PQL queue

- [ ] Where: Open Workspaces in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view PQL queue is saved with filter 'PQL status is qualified.' and sort 'PQL score, highest first.'.

### 42. View: Trials ending soon

- [ ] Where: Open Workspaces in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Trials ending soon is saved with filter 'Lifecycle stage is trialling and trial end date is within 7 days.' and sort 'Trial end date, soonest first.'.

### 43. View: Expansion candidates

- [ ] Where: Open Workspaces in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Expansion candidates is saved with filter 'Lifecycle stage is paying and plan limit used is over 80 percent, or seats used is above seats paid.' and sort 'Plan limit used, highest first.'.

### 44. View: My open deals

- [ ] Where: Open Deals in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view My open deals is saved with filter 'Owner is me and stage is open.' and sort 'Close date, soonest first.'.

### 45. View: Stalled deals

- [ ] Where: Open Deals in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Stalled deals is saved with filter 'Stage is open and next step date is empty or in the past.' and sort 'Next step date, oldest first.'.

### 46. View: Adoption in flight

- [ ] Where: Open Adoption plans in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Adoption in flight is saved with filter 'Status is not complete.' and sort 'Target activation date, oldest first.'.

## Permissions

### 47. Set roles and access

- [ ] Where: Workspace settings, then Members
- Why it is manual: Attio has no API for workspace roles or object and field access.
- Done when: a non-admin test member sees and edits what their role needs and nothing more.
