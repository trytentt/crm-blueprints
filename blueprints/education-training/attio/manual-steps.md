# Manual steps: Education and training providers, B2B (attio)

Generated from `design.yaml`. Do not edit by hand. The Attio API cannot do any of this.
Sources: https://docs.attio.com/llms.txt, https://api.attio.com/openapi/api, `platforms/attio/reference/api-coverage.md`.

## Before and during the build

### 1. Confirm the client's Attio plan allows the objects below

- [ ] Where: Workspace settings, then Billing, and https://attio.com/pricing
- Why it is manual: Object limits depend on the plan (3, 5, 12 or unlimited) and Attio does not say whether standard objects count. A create past the limit fails with 400 quota_exceeded.
- Done when: the plan is written in the client notes and allows 3 custom object(s) (Programme, Cohort, Enrolment).

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
- Done when: each of these objects has a Name attribute: Programme, Cohort, Enrolment. If one does not, add a text attribute with slug `name`.

## Pipelines

### 6. Hide the native Deal stage for Corporate training

- [ ] Where: Deals object, then the table or board view, then hide the Stage column
- Why it is manual: Deals require a native stage. The working pipeline is the list `corporate_training`, so the native stage would show a second, unused set (Q8).
- Done when: new deals get the first native stage by default and the Deals views use the list's Stage.

### 7. Check the stage order of Corporate training

- [ ] Where: Lists in the left sidebar, then Corporate training, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Enquiry qualified then Needs analysis then Proposal sent then Stakeholder review then Terms agreed then Booked then Closed lost.

### 8. Stage probability for Corporate training

- [ ] Where: Lists in the left sidebar, then Corporate training, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Enquiry qualified 10%; Needs analysis 25%; Proposal sent 50%; Stakeholder review 65%; Terms agreed 85%; Booked 100%; Closed lost 0%) and forecast reports multiply by it.

### 9. Won and lost in Corporate training

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Booked for won and Closed lost for lost.

### 10. Check the stage order of Delegate enrolment

- [ ] Where: Lists in the left sidebar, then Delegate enrolment, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Enquiry then Applied then Place offered then Awaiting payment then Enrolled then Withdrawn.

### 11. Stage probability for Delegate enrolment

- [ ] Where: Lists in the left sidebar, then Delegate enrolment, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Enquiry 10%; Applied 40%; Place offered 70%; Awaiting payment 85%; Enrolled 100%; Withdrawn 0%) and forecast reports multiply by it.

### 12. Won and lost in Delegate enrolment

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Enrolled for won and Withdrawn for lost.

## Stage gates and lost reasons

### 13. Stage gate (stage gate): Corporate training, Enquiry qualified

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Corporate training where Stage is Enquiry qualified
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Enquiry qualified with any of these empty are flagged or sent back: Training need, Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 14. Stage gate (stage gate): Corporate training, Needs analysis

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Corporate training where Stage is Needs analysis
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Needs analysis with any of these empty are flagged or sent back: Needs summary, Delegate count, Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 15. Stage gate (stage gate): Corporate training, Proposal sent

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Corporate training where Stage is Proposal sent
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Proposal sent with any of these empty are flagged or sent back: Delivery format, Amount, Funding source. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 16. Stage gate (stage gate): Corporate training, Stakeholder review

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Corporate training where Stage is Stakeholder review
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Stakeholder review with any of these empty are flagged or sent back: Budget confirmed, Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 17. Stage gate (stage gate): Corporate training, Terms agreed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Corporate training where Stage is Terms agreed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Terms agreed with any of these empty are flagged or sent back: Amount, Proposed start date, Delegate count. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 18. Stage gate (stage gate): Corporate training, Booked

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Corporate training where Stage is Booked
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Booked with any of these empty are flagged or sent back: Amount, Close date, Purchase order received. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 19. Stage gate (lost reason): Corporate training, Closed lost

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Corporate training where Stage is Closed lost
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Closed lost with any of these empty are flagged or sent back: Lost reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 20. Stage gate (stage gate): Delegate enrolment, Applied

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Delegate enrolment where Stage is Applied
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Applied with any of these empty are flagged or sent back: Application date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 21. Stage gate (stage gate): Delegate enrolment, Place offered

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Delegate enrolment where Stage is Place offered
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Place offered with any of these empty are flagged or sent back: Price, Funding source. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 22. Stage gate (stage gate): Delegate enrolment, Awaiting payment

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Delegate enrolment where Stage is Awaiting payment
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Awaiting payment with any of these empty are flagged or sent back: Price, Payment status. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 23. Stage gate (stage gate): Delegate enrolment, Enrolled

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Delegate enrolment where Stage is Enrolled
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Enrolled with any of these empty are flagged or sent back: Price, Payment status. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 24. Stage gate (lost reason): Delegate enrolment, Withdrawn

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Delegate enrolment where Stage is Withdrawn
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Withdrawn with any of these empty are flagged or sent back: Withdrawal reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

## Decisions where the Attio mapping is lossy

### 25. Renamed attribute slugs

- [ ] Where: Decide with the client; edit platform_overrides.attio in design.yaml and regenerate
- Why it is manual: These keys are slugs Attio uses on its own objects, so the slug got an object prefix.
- Done when: company.owner -> company_owner; person.owner -> person_owner. Each is accepted or overridden.

### 26. Long text is the same type as text

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that long text fields look like short text fields in Attio. Fields: deal.description, deal.needs_summary.

### 27. Currency fields use GBP

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Confirm the account currency. One currency per attribute: change it before data is loaded, because a later change does not convert values. Fields: programme.list_price, enrolment.price.

### 28. Phone values must be E.164

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Agree that numbers are written with a + and country code, or with a country code field, on import. Fields: company.phone.

### 29. User fields hold workspace members only

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that people outside the workspace cannot be chosen. Fields: company.owner, person.owner, cohort.trainer.

### 30. Checkbox fields cannot be empty

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that unticked and unknown look the same. Fields: deal.budget_confirmed, deal.purchase_order_received, programme.accredited.

## Workflows

### 31. Workflow: Create cohort on booking

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A corporate training deal with delivery format in-house moves to booked.'; action 'Create a cohort of type in-house linked to the client and the programme, copy the proposed start date and delegate count, and assign it to the course administrator.'

### 32. Workflow: Update confirmed places

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'An enrolment moves to enrolled or withdrawn.'; action 'Recalculate the cohort's confirmed places from enrolments at the enrolled stage. Set the cohort to full when it reaches capacity.'

### 33. Workflow: Review cohort viability

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'An open cohort is 21 days from its start date and confirmed places are below the minimum to run.'; action 'Notify the head of delivery and the owning salesperson to decide between pushing sales and cancelling.'

### 34. Workflow: Rebooking follow-up

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A cohort is marked completed.'; action 'Create a task for the account owner of each paying employer to ask about a next cohort within 14 days, and set the company's customer status to active customer.'

### 35. Workflow: Flag stalled deals

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'An open deal has no next step date, or the date is more than 7 days past.'; action 'Notify the deal owner and add the deal to the stalled deals view.'

## Views

### 36. View: My open deals

- [ ] Where: Open Deals in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view My open deals is saved with filter 'Owner is me and stage is open.' and sort 'Close date, soonest first.'.

### 37. View: Stalled deals

- [ ] Where: Open Deals in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Stalled deals is saved with filter 'Stage is open and next step date is empty or in the past.' and sort 'Next step date, oldest first.'.

### 38. View: Cohorts with places

- [ ] Where: Open Cohorts in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Cohorts with places is saved with filter 'Status is open for enrolment and start date is in the future.' and sort 'Start date, soonest first.'.

### 39. View: Cohorts at risk

- [ ] Where: Open Cohorts in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Cohorts at risk is saved with filter 'Status is open for enrolment and start date is within 28 days and confirmed places are below the minimum.' and sort 'Start date, soonest first.'.

### 40. View: Enrolments awaiting payment

- [ ] Where: Open Enrolments in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Enrolments awaiting payment is saved with filter 'Stage is awaiting payment.' and sort 'Application date, oldest first.'.

### 41. View: Lapsed customers

- [ ] Where: Open Companies in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Lapsed customers is saved with filter 'Customer status is lapsed.' and sort 'Name, A to Z.'.

## Permissions

### 42. Set roles and access

- [ ] Where: Workspace settings, then Members
- Why it is manual: Attio has no API for workspace roles or object and field access.
- Done when: a non-admin test member sees and edits what their role needs and nothing more.
