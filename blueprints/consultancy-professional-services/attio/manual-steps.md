# Manual steps: Consultancy and professional services (attio)

Generated from `design.yaml`. Do not edit by hand. The Attio API cannot do any of this.
Sources: https://docs.attio.com/llms.txt, https://api.attio.com/openapi/api, `platforms/attio/reference/api-coverage.md`.

## Before and during the build

### 1. Confirm the client's Attio plan allows the objects below

- [ ] Where: Workspace settings, then Billing, and https://attio.com/pricing
- Why it is manual: Object limits depend on the plan (3, 5, 12 or unlimited) and Attio does not say whether standard objects count. A create past the limit fails with 400 quota_exceeded.
- Done when: the plan is written in the client notes and allows 2 custom object(s) (Matter, Conflict check).

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
- Done when: each of these objects has a Name attribute: Matter, Conflict check. If one does not, add a text attribute with slug `name`.

## Pipelines

### 6. Hide the native Deal stage for New work

- [ ] Where: Deals object, then the table or board view, then hide the Stage column
- Why it is manual: Deals require a native stage. The working pipeline is the list `new_work`, so the native stage would show a second, unused set (Q8).
- Done when: new deals get the first native stage by default and the Deals views use the list's Stage.

### 7. Check the stage order of New work

- [ ] Where: Lists in the left sidebar, then New work, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Enquiry then Qualified then Conflict check then Proposal then Proposal sent then Terms agreed then Engagement letter out then Closed won then Closed lost.

### 8. Stage probability for New work

- [ ] Where: Lists in the left sidebar, then New work, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Enquiry 5%; Qualified 15%; Conflict check 25%; Proposal 45%; Proposal sent 60%; Terms agreed 80%; Engagement letter out 90%; Closed won 100%; Closed lost 0%) and forecast reports multiply by it.

### 9. Won and lost in New work

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Closed won for won and Closed lost for lost.

### 10. Check the stage order of Matter delivery

- [ ] Where: Lists in the left sidebar, then Matter delivery, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Opening then Cleared to start then In progress then Awaiting client then Final billing then Closed then Withdrawn.

### 11. Stage probability for Matter delivery

- [ ] Where: Lists in the left sidebar, then Matter delivery, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Opening 100%; Cleared to start 100%; In progress 100%; Awaiting client 100%; Final billing 100%; Closed 100%; Withdrawn 0%) and forecast reports multiply by it.

### 12. Won and lost in Matter delivery

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Closed for won and Withdrawn for lost.

## Stage gates and lost reasons

### 13. Stage gate (stage gate): New work, Enquiry

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New work where Stage is Enquiry
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Enquiry with any of these empty are flagged or sent back: Service area, Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 14. Stage gate (stage gate): New work, Qualified

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New work where Stage is Qualified
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Qualified with any of these empty are flagged or sent back: Lead partner, Scope summary. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 15. Stage gate (stage gate): New work, Conflict check

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New work where Stage is Conflict check
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Conflict check with any of these empty are flagged or sent back: Conflict check result. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 16. Stage gate (stage gate): New work, Proposal

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New work where Stage is Proposal
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Proposal with any of these empty are flagged or sent back: Conflict check result, Billing model, Amount. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 17. Stage gate (stage gate): New work, Proposal sent

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New work where Stage is Proposal sent
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Proposal sent with any of these empty are flagged or sent back: Amount, Close date, Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 18. Stage gate (stage gate): New work, Terms agreed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New work where Stage is Terms agreed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Terms agreed with any of these empty are flagged or sent back: Amount, Billing model, Close date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 19. Stage gate (stage gate): New work, Engagement letter out

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New work where Stage is Engagement letter out
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Engagement letter out with any of these empty are flagged or sent back: Engagement letter status, Conflict check result. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 20. Stage gate (stage gate): New work, Closed won

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New work where Stage is Closed won
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Closed won with any of these empty are flagged or sent back: Amount, Close date, Engagement letter status. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 21. Stage gate (lost reason): New work, Closed lost

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New work where Stage is Closed lost
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Closed lost with any of these empty are flagged or sent back: Lost reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 22. Stage gate (stage gate): Matter delivery, Opening

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Matter delivery where Stage is Opening
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Opening with any of these empty are flagged or sent back: Responsible partner, Matter manager. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 23. Stage gate (stage gate): Matter delivery, Cleared to start

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Matter delivery where Stage is Cleared to start
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Cleared to start with any of these empty are flagged or sent back: Engagement letter signed date, AML check status. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 24. Stage gate (stage gate): Matter delivery, In progress

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Matter delivery where Stage is In progress
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering In progress with any of these empty are flagged or sent back: Start date, Target end date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 25. Stage gate (stage gate): Matter delivery, Awaiting client

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Matter delivery where Stage is Awaiting client
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Awaiting client with any of these empty are flagged or sent back: Target end date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 26. Stage gate (stage gate): Matter delivery, Final billing

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Matter delivery where Stage is Final billing
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Final billing with any of these empty are flagged or sent back: Billing model, Fee estimate. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 27. Stage gate (stage gate): Matter delivery, Closed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Matter delivery where Stage is Closed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Closed with any of these empty are flagged or sent back: Target end date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 28. Stage gate (lost reason): Matter delivery, Withdrawn

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Matter delivery where Stage is Withdrawn
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Withdrawn with any of these empty are flagged or sent back: Close reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

## Decisions where the Attio mapping is lossy

### 29. Renamed attribute slugs

- [ ] Where: Decide with the client; edit platform_overrides.attio in design.yaml and regenerate
- Why it is manual: These keys are slugs Attio uses on its own objects, so the slug got an object prefix.
- Done when: company.owner -> company_owner; person.owner -> person_owner. Each is accepted or overridden.

### 30. Long text is the same type as text

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that long text fields look like short text fields in Attio. Fields: deal.description, deal.scope_summary, conflict_check.parties_checked.

### 31. Currency fields use GBP

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Confirm the account currency. One currency per attribute: change it before data is loaded, because a later change does not convert values. Fields: matter.fee_estimate.

### 32. Phone values must be E.164

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Agree that numbers are written with a + and country code, or with a country code field, on import. Fields: company.phone.

### 33. User fields hold workspace members only

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that people outside the workspace cannot be chosen. Fields: company.owner, person.owner, deal.lead_partner, conflict_check.cleared_by, matter.responsible_partner, matter.matter_manager.

### 34. Checkbox fields cannot be empty

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that unticked and unknown look the same. Fields: conflict_check.ethical_wall_needed, matter.confidential.

## Workflows

### 35. Workflow: Request conflict check

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A deal moves to the conflict check stage.'; action 'Create a conflict check record with result pending, link it to the deal and company, and notify risk or compliance.'

### 36. Workflow: Copy conflict result to deal

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A conflict check result changes.'; action 'Set the linked deal's conflict check result to match, and notify the lead partner.'

### 37. Workflow: Return conflicted deals

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A conflict check result is conflicted.'; action 'Move the deal back to qualified, notify the lead partner and risk, and prompt closed lost with conflict as the reason if the conflict cannot be waived.'

### 38. Workflow: Create matter on closed won

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A deal in the new work pipeline moves to closed won.'; action 'Create a matter from the deal's service area, billing model and amount, link it to the deal and company, and set the company's client status to active client.'

### 39. Workflow: Flag stalled deals

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'An open deal has no next step date, or the date is more than 7 days past.'; action 'Notify the deal owner and add the deal to the stalled deals view.'

### 40. Workflow: Flag work before engagement letter

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A matter is in progress and has no engagement letter signed date.'; action 'Notify the responsible partner and compliance.'

## Views

### 41. View: My open deals

- [ ] Where: Open Deals in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view My open deals is saved with filter 'Owner is me and stage is open.' and sort 'Close date, soonest first.'.

### 42. View: Conflict checks awaiting clearance

- [ ] Where: Open Conflict checks in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Conflict checks awaiting clearance is saved with filter 'Result is pending.' and sort 'Check date, oldest first.'.

### 43. View: Stalled deals

- [ ] Where: Open Deals in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Stalled deals is saved with filter 'Stage is open and next step date is empty or in the past.' and sort 'Next step date, oldest first.'.

### 44. View: Active matters

- [ ] Where: Open Matters in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Active matters is saved with filter 'Stage is open.' and sort 'Target end date, soonest first.'.

### 45. View: Matters without a signed letter

- [ ] Where: Open Matters in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Matters without a signed letter is saved with filter 'Stage is in progress and engagement letter signed date is empty.' and sort 'Start date, oldest first.'.

### 46. View: Matters ready to bill

- [ ] Where: Open Matters in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Matters ready to bill is saved with filter 'Stage is final billing.' and sort 'Target end date, oldest first.'.

## Permissions

### 47. Set roles and access

- [ ] Where: Workspace settings, then Members
- Why it is manual: Attio has no API for workspace roles or object and field access.
- Done when: a non-admin test member sees and edits what their role needs and nothing more.
