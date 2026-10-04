# Manual steps: Investor, VC and angel deal flow (attio)

Generated from `design.yaml`. Do not edit by hand. The Attio API cannot do any of this.
Sources: https://docs.attio.com/llms.txt, https://api.attio.com/openapi/api, `platforms/attio/reference/api-coverage.md`.

## Before and during the build

### 1. Confirm the client's Attio plan allows the objects below

- [ ] Where: Workspace settings, then Billing, and https://attio.com/pricing
- Why it is manual: Object limits depend on the plan (3, 5, 12 or unlimited) and Attio does not say whether standard objects count. A create past the limit fails with 400 quota_exceeded.
- Done when: the plan is written in the client notes and allows 1 custom object(s) (Portfolio investment).

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
- Done when: each of these objects has a Name attribute: Portfolio investment. If one does not, add a text attribute with slug `name`.

## Pipelines

### 6. Hide the native Deal stage for Deal flow

- [ ] Where: Deals object, then the table or board view, then hide the Stage column
- Why it is manual: Deals require a native stage. The working pipeline is the list `deal_flow`, so the native stage would show a second, unused set (Q8).
- Done when: new deals get the first native stage by default and the Deals views use the list's Stage.

### 7. Check the stage order of Deal flow

- [ ] Where: Lists in the left sidebar, then Deal flow, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Sourced then Screening then First meeting then Deep dive then Partner meeting then Term sheet then Due diligence then Investment committee then Invested then Passed.

### 8. Stage probability for Deal flow

- [ ] Where: Lists in the left sidebar, then Deal flow, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Sourced 2%; Screening 5%; First meeting 10%; Deep dive 20%; Partner meeting 35%; Term sheet 55%; Due diligence 70%; Investment committee 85%; Invested 100%; Passed 0%) and forecast reports multiply by it.

### 9. Won and lost in Deal flow

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Invested for won and Passed for lost.

### 10. Check the stage order of Portfolio outcome

- [ ] Where: Lists in the left sidebar, then Portfolio outcome, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Active then Follow-on review then Exit preparation then Exit process then Exited then Written off.

### 11. Stage probability for Portfolio outcome

- [ ] Where: Lists in the left sidebar, then Portfolio outcome, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Active 30%; Follow-on review 40%; Exit preparation 60%; Exit process 80%; Exited 100%; Written off 0%) and forecast reports multiply by it.

### 12. Won and lost in Portfolio outcome

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Exited for won and Written off for lost.

## Stage gates and lost reasons

### 13. Stage gate (stage gate): Deal flow, Sourced

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Deal flow where Stage is Sourced
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Sourced with any of these empty are flagged or sent back: Deal source. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 14. Stage gate (stage gate): Deal flow, Screening

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Deal flow where Stage is Screening
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Screening with any of these empty are flagged or sent back: Deal lead, Round type. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 15. Stage gate (stage gate): Deal flow, First meeting

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Deal flow where Stage is First meeting
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering First meeting with any of these empty are flagged or sent back: Thesis fit confirmed, Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 16. Stage gate (stage gate): Deal flow, Deep dive

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Deal flow where Stage is Deep dive
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Deep dive with any of these empty are flagged or sent back: Conviction, Round size, Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 17. Stage gate (stage gate): Deal flow, Partner meeting

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Deal flow where Stage is Partner meeting
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Partner meeting with any of these empty are flagged or sent back: Our role, Pre-money valuation, Conviction. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 18. Stage gate (stage gate): Deal flow, Term sheet

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Deal flow where Stage is Term sheet
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Term sheet with any of these empty are flagged or sent back: Term sheet status, Amount, Pre-money valuation. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 19. Stage gate (stage gate): Deal flow, Due diligence

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Deal flow where Stage is Due diligence
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Due diligence with any of these empty are flagged or sent back: Term sheet status, Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 20. Stage gate (stage gate): Deal flow, Investment committee

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Deal flow where Stage is Investment committee
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Investment committee with any of these empty are flagged or sent back: Diligence complete, Amount. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 21. Stage gate (stage gate): Deal flow, Invested

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Deal flow where Stage is Invested
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Invested with any of these empty are flagged or sent back: Investment committee approved, Amount, Close date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 22. Stage gate (lost reason): Deal flow, Passed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Deal flow where Stage is Passed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Passed with any of these empty are flagged or sent back: Pass reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 23. Stage gate (stage gate): Portfolio outcome, Active

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Portfolio outcome where Stage is Active
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Active with any of these empty are flagged or sent back: Amount invested, Ownership, Lead partner. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 24. Stage gate (stage gate): Portfolio outcome, Follow-on review

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Portfolio outcome where Stage is Follow-on review
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Follow-on review with any of these empty are flagged or sent back: Follow-on reserve, Health. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 25. Stage gate (stage gate): Portfolio outcome, Exit preparation

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Portfolio outcome where Stage is Exit preparation
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Exit preparation with any of these empty are flagged or sent back: Latest valuation. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 26. Stage gate (stage gate): Portfolio outcome, Exit process

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Portfolio outcome where Stage is Exit process
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Exit process with any of these empty are flagged or sent back: Latest valuation, Lead partner. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 27. Stage gate (stage gate): Portfolio outcome, Exited

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Portfolio outcome where Stage is Exited
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Exited with any of these empty are flagged or sent back: Exit route. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 28. Stage gate (lost reason): Portfolio outcome, Written off

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Portfolio outcome where Stage is Written off
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Written off with any of these empty are flagged or sent back: Write-off reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

## Decisions where the Attio mapping is lossy

### 29. Renamed attribute slugs

- [ ] Where: Decide with the client; edit platform_overrides.attio in design.yaml and regenerate
- Why it is manual: These keys are slugs Attio uses on its own objects, so the slug got an object prefix.
- Done when: company.owner -> company_owner; person.owner -> person_owner. Each is accepted or overridden.

### 30. Percent fields are plain numbers

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Decide whether percentages are stored as 0 to 100 or 0 to 1. The generated description says 0 to 100. Fields: portfolio_investment.ownership_percent.

### 31. Long text is the same type as text

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that long text fields look like short text fields in Attio. Fields: deal.description.

### 32. Currency fields use GBP

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Confirm the account currency. One currency per attribute: change it before data is loaded, because a later change does not convert values. Fields: deal.round_size, deal.pre_money_valuation, portfolio_investment.amount_invested, portfolio_investment.latest_valuation, portfolio_investment.follow_on_reserve.

### 33. Phone values must be E.164

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Agree that numbers are written with a + and country code, or with a country code field, on import. Fields: company.phone.

### 34. User fields hold workspace members only

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that people outside the workspace cannot be chosen. Fields: company.owner, person.owner, person.relationship_owner, deal.deal_lead, portfolio_investment.lead_partner.

### 35. Checkbox fields cannot be empty

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that unticked and unknown look the same. Fields: deal.thesis_fit_confirmed, deal.diligence_complete, deal.ic_approved, portfolio_investment.board_seat.

## Workflows

### 36. Workflow: Create investment on invested

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A deal in the deal flow pipeline moves to invested.'; action 'Create a portfolio investment from the deal's amount, valuation and close date, link it to the company and the deal, copy the round co-investors, and set the company's organisation type to startup.'

### 37. Workflow: Flag stalled deals

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'An open deal has no next step date, or the date is more than 7 days past.'; action 'Notify the deal lead and add the deal to the stalled deals view.'

### 38. Workflow: Revisit passed companies

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A deal moves to passed with a pass reason of timing or traction and its next step date arrives.'; action 'Create a task for the deal lead to check progress and reopen the company at sourced if it now fits.'

### 39. Workflow: Investor update reminder

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A portfolio investment's next update due date is 7 days away.'; action 'Create a task for the lead partner to request the update from the founders.'

### 40. Workflow: Follow-on alert

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A portfolio company's funding stage changes or its health changes to needs support.'; action 'Move the investment to follow-on review and notify the lead partner.'

### 41. Workflow: Thank the introducer

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A deal with an introducer moves to term sheet or invested.'; action 'Create a task for the deal lead to thank the introducer.'

## Views

### 42. View: Active deal flow

- [ ] Where: Open Deals in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Active deal flow is saved with filter 'Stage is open and deal lead is me.' and sort 'Next step date, soonest first.'.

### 43. View: Stalled deals

- [ ] Where: Open Deals in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Stalled deals is saved with filter 'Stage is open and next step date is empty or in the past.' and sort 'Next step date, oldest first.'.

### 44. View: Passed, to revisit

- [ ] Where: Open Deals in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Passed, to revisit is saved with filter 'Stage is passed and pass reason is timing or traction.' and sort 'Next step date, soonest first.'.

### 45. View: Portfolio health

- [ ] Where: Open Portfolio investments in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Portfolio health is saved with filter 'Status is active or follow-on review.' and sort 'Health, at risk first.'.

### 46. View: Investor updates due

- [ ] Where: Open Portfolio investments in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Investor updates due is saved with filter 'Status is active and next update due is within 14 days.' and sort 'Next update due, soonest first.'.

### 47. View: Co-investors

- [ ] Where: Open Companies in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Co-investors is saved with filter 'Organisation type is co-investor or other fund.' and sort 'Relationship strength, close first.'.

## Permissions

### 48. Set roles and access

- [ ] Where: Workspace settings, then Members
- Why it is manual: Attio has no API for workspace roles or object and field access.
- Done when: a non-admin test member sees and edits what their role needs and nothing more.
