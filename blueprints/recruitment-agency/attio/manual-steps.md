# Manual steps: Recruitment agency (attio)

Generated from `design.yaml`. Do not edit by hand. The Attio API cannot do any of this.
Sources: https://docs.attio.com/llms.txt, https://api.attio.com/openapi/api, `platforms/attio/reference/api-coverage.md`.

## Before and during the build

### 1. Confirm the client's Attio plan allows the objects below

- [ ] Where: Workspace settings, then Billing, and https://attio.com/pricing
- Why it is manual: Object limits depend on the plan (3, 5, 12 or unlimited) and Attio does not say whether standard objects count. A create past the limit fails with 400 quota_exceeded.
- Done when: the plan is written in the client notes and allows 2 custom object(s) (Role, Submission).

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
- Done when: each of these objects has a Name attribute: Role, Submission. If one does not, add a text attribute with slug `name`.

## Pipelines

### 6. Hide the native Deal stage for Client development

- [ ] Where: Deals object, then the table or board view, then hide the Stage column
- Why it is manual: Deals require a native stage. The working pipeline is the list `client_development`, so the native stage would show a second, unused set (Q8).
- Done when: new deals get the first native stage by default and the Deals views use the list's Stage.

### 7. Check the stage order of Client development

- [ ] Where: Lists in the left sidebar, then Client development, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Target then Conversation then Terms discussed then Terms sent then Terms signed then Not won.

### 8. Stage probability for Client development

- [ ] Where: Lists in the left sidebar, then Client development, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Target 5%; Conversation 15%; Terms discussed 40%; Terms sent 60%; Terms signed 100%; Not won 0%) and forecast reports multiply by it.

### 9. Won and lost in Client development

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Terms signed for won and Not won for lost.

### 10. Check the stage order of Placement

- [ ] Where: Lists in the left sidebar, then Placement, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Sourced then Screened then Submitted then Interviewing then Offer then Offer accepted then Placed then Rejected.

### 11. Stage probability for Placement

- [ ] Where: Lists in the left sidebar, then Placement, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Sourced 10%; Screened 25%; Submitted 40%; Interviewing 60%; Offer 80%; Offer accepted 90%; Placed 100%; Rejected 0%) and forecast reports multiply by it.

### 12. Won and lost in Placement

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Placed for won and Rejected for lost.

## Stage gates and lost reasons

### 13. Stage gate (stage gate): Client development, Target

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Client development where Stage is Target
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Target with any of these empty are flagged or sent back: Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 14. Stage gate (stage gate): Client development, Conversation

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Client development where Stage is Conversation
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Conversation with any of these empty are flagged or sent back: Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 15. Stage gate (stage gate): Client development, Terms discussed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Client development where Stage is Terms discussed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Terms discussed with any of these empty are flagged or sent back: Search model, Fee percent. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 16. Stage gate (stage gate): Client development, Terms sent

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Client development where Stage is Terms sent
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Terms sent with any of these empty are flagged or sent back: Search model, Fee percent, Exclusivity. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 17. Stage gate (stage gate): Client development, Terms signed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Client development where Stage is Terms signed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Terms signed with any of these empty are flagged or sent back: Search model, Fee percent. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 18. Stage gate (lost reason): Client development, Not won

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Client development where Stage is Not won
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Not won with any of these empty are flagged or sent back: Lost reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 19. Stage gate (stage gate): Placement, Sourced

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Placement where Stage is Sourced
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Sourced with any of these empty are flagged or sent back: Source. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 20. Stage gate (stage gate): Placement, Screened

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Placement where Stage is Screened
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Screened with any of these empty are flagged or sent back: Salary expected. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 21. Stage gate (stage gate): Placement, Submitted

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Placement where Stage is Submitted
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Submitted with any of these empty are flagged or sent back: CV sent date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 22. Stage gate (stage gate): Placement, Interviewing

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Placement where Stage is Interviewing
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Interviewing with any of these empty are flagged or sent back: Interview date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 23. Stage gate (stage gate): Placement, Offer

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Placement where Stage is Offer
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Offer with any of these empty are flagged or sent back: Agreed salary. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 24. Stage gate (stage gate): Placement, Offer accepted

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Placement where Stage is Offer accepted
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Offer accepted with any of these empty are flagged or sent back: Agreed salary, Start date, Checks complete. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 25. Stage gate (stage gate): Placement, Placed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Placement where Stage is Placed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Placed with any of these empty are flagged or sent back: Start date, Fee amount. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 26. Stage gate (lost reason): Placement, Rejected

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Placement where Stage is Rejected
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Rejected with any of these empty are flagged or sent back: Rejection reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

## Decisions where the Attio mapping is lossy

### 27. Renamed attribute slugs

- [ ] Where: Decide with the client; edit platform_overrides.attio in design.yaml and regenerate
- Why it is manual: These keys are slugs Attio uses on its own objects, so the slug got an object prefix.
- Done when: company.owner -> company_owner; person.owner -> person_owner. Each is accepted or overridden.

### 28. Percent fields are plain numbers

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Decide whether percentages are stored as 0 to 100 or 0 to 1. The generated description says 0 to 100. Fields: company.default_fee_percent, deal.fee_percent, role.fee_percent.

### 29. Long text is the same type as text

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that long text fields look like short text fields in Attio. Fields: deal.description.

### 30. Currency fields use GBP

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Confirm the account currency. One currency per attribute: change it before data is loaded, because a later change does not convert values. Fields: person.desired_salary, role.salary_min, role.salary_max, role.fee_estimate, submission.salary_expected, submission.agreed_salary, submission.fee_amount.

### 31. Phone values must be E.164

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Agree that numbers are written with a + and country code, or with a country code field, on import. Fields: company.phone.

### 32. User fields hold workspace members only

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that people outside the workspace cannot be chosen. Fields: company.owner, person.owner, role.consultant, submission.consultant.

### 33. Checkbox fields cannot be empty

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that unticked and unknown look the same. Fields: submission.checks_complete.

### 34. Select options cannot be reordered or deleted

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Order follows creation order, so options are sent in design order. Removing one means archiving it. Fields: person.person_type, person.sector_experience.

## Workflows

### 35. Workflow: Block submissions without terms

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A submission is created for a role whose client has terms status other than signed.'; action 'Notify the consultant and the desk manager that the client has no signed terms, and flag the submission.'

### 36. Workflow: Calculate fee

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A submission has an agreed salary set.'; action 'Set fee amount from the agreed salary and the fee percent on the role.'

### 37. Workflow: Mark role filled

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A submission moves to placed and the role's openings are all filled.'; action 'Set the role status to filled by us and close other open submissions on the role as rejected with role filled elsewhere.'

### 38. Workflow: Rebate period reminder

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A placed submission's start date plus the client's rebate period is 14 days away.'; action 'Notify the consultant to check in with the client and the new starter.'

### 39. Workflow: Mark dormant client

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'An active client has had no new role for 6 months.'; action 'Set client status to dormant client and add the company to the reactivation view.'

### 40. Workflow: Review candidate data

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A person of type candidate has a data review date in 30 days.'; action 'Notify the owner to confirm consent or delete the record.'

### 41. Workflow: Flag stalled deals

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'An open deal has no next step date, or the date is more than 7 days past.'; action 'Notify the deal owner and add the deal to the stalled deals view.'

## Views

### 42. View: Open roles

- [ ] Where: Open Roles in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Open roles is saved with filter 'Status is open or offer stage.' and sort 'Target fill date, soonest first.'.

### 43. View: My candidates in process

- [ ] Where: Open Submissions in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view My candidates in process is saved with filter 'Consultant is me and stage is open.' and sort 'Interview date, soonest first.'.

### 44. View: Offers to close

- [ ] Where: Open Submissions in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Offers to close is saved with filter 'Stage is offer or offer accepted.' and sort 'Start date, soonest first.'.

### 45. View: Placements to invoice

- [ ] Where: Open Submissions in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Placements to invoice is saved with filter 'Stage is placed and invoice status is to invoice.' and sort 'Start date, oldest first.'.

### 46. View: Candidates due for data review

- [ ] Where: Open People in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Candidates due for data review is saved with filter 'Person type includes candidate and data review date is within 30 days.' and sort 'Data review date, soonest first.'.

### 47. View: Stalled deals

- [ ] Where: Open Deals in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Stalled deals is saved with filter 'Stage is open and next step date is empty or in the past.' and sort 'Next step date, oldest first.'.

## Permissions

### 48. Set roles and access

- [ ] Where: Workspace settings, then Members
- Why it is manual: Attio has no API for workspace roles or object and field access.
- Done when: a non-admin test member sees and edits what their role needs and nothing more.
