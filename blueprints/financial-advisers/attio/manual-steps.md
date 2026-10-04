# Manual steps: Financial advisers, client households (attio)

Generated from `design.yaml`. Do not edit by hand. The Attio API cannot do any of this.
Sources: https://docs.attio.com/llms.txt, https://api.attio.com/openapi/api, `platforms/attio/reference/api-coverage.md`.

## Before and during the build

### 1. Confirm the client's Attio plan allows the objects below

- [ ] Where: Workspace settings, then Billing, and https://attio.com/pricing
- Why it is manual: Object limits depend on the plan (3, 5, 12 or unlimited) and Attio does not say whether standard objects count. A create past the limit fails with 400 quota_exceeded.
- Done when: the plan is written in the client notes and allows 3 custom object(s) (Household, Advice case, Review).

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
- Done when: each of these objects has a Name attribute: Household, Advice case, Review. If one does not, add a text attribute with slug `name`.

## Pipelines

### 6. Hide the native Deal stage for New client

- [ ] Where: Deals object, then the table or board view, then hide the Stage column
- Why it is manual: Deals require a native stage. The working pipeline is the list `new_client`, so the native stage would show a second, unused set (Q8).
- Done when: new deals get the first native stage by default and the Deals views use the list's Stage.

### 7. Check the stage order of New client

- [ ] Where: Lists in the left sidebar, then New client, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Enquiry then Initial meeting booked then Initial meeting held then Fee proposal then Agreement out then Client won then Lost.

### 8. Stage probability for New client

- [ ] Where: Lists in the left sidebar, then New client, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Enquiry 10%; Initial meeting booked 25%; Initial meeting held 40%; Fee proposal 60%; Agreement out 80%; Client won 100%; Lost 0%) and forecast reports multiply by it.

### 9. Won and lost in New client

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Client won for won and Lost for lost.

### 10. Check the stage order of Advice delivery

- [ ] Where: Lists in the left sidebar, then Advice delivery, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Fact find then Analysis then Report drafted then Report issued then Accepted then Completed then Closed without advice.

### 11. Stage probability for Advice delivery

- [ ] Where: Lists in the left sidebar, then Advice delivery, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Fact find 20%; Analysis 40%; Report drafted 60%; Report issued 75%; Accepted 90%; Completed 100%; Closed without advice 0%) and forecast reports multiply by it.

### 12. Won and lost in Advice delivery

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Completed for won and Closed without advice for lost.

### 13. Check the stage order of Review cycle

- [ ] Where: Lists in the left sidebar, then Review cycle, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Due then Invited then Booked then Meeting held then Review completed then Not completed.

### 14. Stage probability for Review cycle

- [ ] Where: Lists in the left sidebar, then Review cycle, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Due 20%; Invited 40%; Booked 60%; Meeting held 80%; Review completed 100%; Not completed 0%) and forecast reports multiply by it.

### 15. Won and lost in Review cycle

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Review completed for won and Not completed for lost.

## Stage gates and lost reasons

### 16. Stage gate (stage gate): New client, Enquiry

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New client where Stage is Enquiry
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Enquiry with any of these empty are flagged or sent back: Referral source. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 17. Stage gate (stage gate): New client, Initial meeting booked

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New client where Stage is Initial meeting booked
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Initial meeting booked with any of these empty are flagged or sent back: Service interest, Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 18. Stage gate (stage gate): New client, Initial meeting held

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New client where Stage is Initial meeting held
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Initial meeting held with any of these empty are flagged or sent back: Initial meeting held, Expected investable assets. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 19. Stage gate (stage gate): New client, Fee proposal

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New client where Stage is Fee proposal
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Fee proposal with any of these empty are flagged or sent back: Fee basis agreed, Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 20. Stage gate (stage gate): New client, Agreement out

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New client where Stage is Agreement out
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Agreement out with any of these empty are flagged or sent back: Fee basis agreed, Amount, Close date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 21. Stage gate (stage gate): New client, Client won

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New client where Stage is Client won
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Client won with any of these empty are flagged or sent back: Client agreement signed, Close date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 22. Stage gate (lost reason): New client, Lost

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New client where Stage is Lost
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Lost with any of these empty are flagged or sent back: Lost reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 23. Stage gate (stage gate): Advice delivery, Fact find

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Advice delivery where Stage is Fact find
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Fact find with any of these empty are flagged or sent back: Adviser, Advice topic. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 24. Stage gate (stage gate): Advice delivery, Analysis

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Advice delivery where Stage is Analysis
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Analysis with any of these empty are flagged or sent back: Fact find complete, Paraplanner. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 25. Stage gate (stage gate): Advice delivery, Report drafted

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Advice delivery where Stage is Report drafted
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Report drafted with any of these empty are flagged or sent back: Compliance check. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 26. Stage gate (stage gate): Advice delivery, Report issued

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Advice delivery where Stage is Report issued
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Report issued with any of these empty are flagged or sent back: Report issued date, Compliance check. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 27. Stage gate (stage gate): Advice delivery, Accepted

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Advice delivery where Stage is Accepted
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Accepted with any of these empty are flagged or sent back: Client decision. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 28. Stage gate (stage gate): Advice delivery, Completed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Advice delivery where Stage is Completed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Completed with any of these empty are flagged or sent back: Applications submitted, Completion date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 29. Stage gate (lost reason): Advice delivery, Closed without advice

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Advice delivery where Stage is Closed without advice
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Closed without advice with any of these empty are flagged or sent back: Closure reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 30. Stage gate (stage gate): Review cycle, Due

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Review cycle where Stage is Due
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Due with any of these empty are flagged or sent back: Review type, Due date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 31. Stage gate (stage gate): Review cycle, Invited

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Review cycle where Stage is Invited
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Invited with any of these empty are flagged or sent back: Adviser. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 32. Stage gate (stage gate): Review cycle, Booked

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Review cycle where Stage is Booked
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Booked with any of these empty are flagged or sent back: Meeting date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 33. Stage gate (stage gate): Review cycle, Meeting held

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Review cycle where Stage is Meeting held
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Meeting held with any of these empty are flagged or sent back: Circumstances changed, Risk profile reconfirmed. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 34. Stage gate (stage gate): Review cycle, Review completed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Review cycle where Stage is Review completed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Review completed with any of these empty are flagged or sent back: Outcome, Risk profile reconfirmed. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 35. Stage gate (lost reason): Review cycle, Not completed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Review cycle where Stage is Not completed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Not completed with any of these empty are flagged or sent back: Missed reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

## Decisions where the Attio mapping is lossy

### 36. Renamed attribute slugs

- [ ] Where: Decide with the client; edit platform_overrides.attio in design.yaml and regenerate
- Why it is manual: These keys are slugs Attio uses on its own objects, so the slug got an object prefix.
- Done when: company.owner -> company_owner; person.owner -> person_owner. Each is accepted or overridden.

### 37. Long text is the same type as text

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that long text fields look like short text fields in Attio. Fields: deal.description.

### 38. Currency fields use GBP

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Confirm the account currency. One currency per attribute: change it before data is loaded, because a later change does not convert values. Fields: deal.expected_investable_assets, household.annual_fee.

### 39. Phone values must be E.164

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Agree that numbers are written with a + and country code, or with a country code field, on import. Fields: company.phone.

### 40. User fields hold workspace members only

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that people outside the workspace cannot be chosen. Fields: company.owner, person.owner, household.lead_adviser, advice_case.adviser, advice_case.paraplanner, review.adviser.

### 41. Date and time fields are stored in UTC

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that Attio shows and stores timestamps in UTC. Fields: review.meeting_date.

### 42. Checkbox fields cannot be empty

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that unticked and unknown look the same. Fields: company.referral_agreement, person.id_verified, deal.initial_meeting_held, deal.engagement_signed, advice_case.fact_find_complete, advice_case.applications_submitted, review.circumstances_changed, review.risk_profile_reconfirmed.

## Workflows

### 43. Workflow: Start advice case on client won

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A deal in the new client pipeline moves to client won.'; action 'Set the household status to onboarding, set the agreement date, create an advice case at fact find assigned to the lead adviser, and set the next review date from the review frequency.'

### 44. Workflow: Open review

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A household's next review date is 90 days away and its status is ongoing client.'; action 'Create a review at due for the household, assigned to the lead adviser.'

### 45. Workflow: Roll the review cycle forward

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A review moves to review completed.'; action 'Set the household's last review date to the meeting date and its next review date to the date plus its review frequency.'

### 46. Workflow: Chase overdue reviews

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A review is open and its due date has passed.'; action 'Notify the lead adviser and add the review to the overdue reviews view.'

### 47. Workflow: Vulnerability flag alert

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A person's vulnerability flag changes to possible or confirmed.'; action 'Notify the lead adviser and compliance lead to check the service and communication preferences.'

### 48. Workflow: Compliance check request

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'An advice case moves to report drafted.'; action 'Notify the compliance lead and set the compliance check to pending.'

### 49. Workflow: Thank the referrer

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A deal with a professional referral source moves to client won.'; action 'Create a task for the lead adviser to thank the referrer, subject to the referral agreement and client consent.'

## Views

### 50. View: Reviews due in 90 days

- [ ] Where: Open Households in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Reviews due in 90 days is saved with filter 'Status is ongoing client and next review date is within 90 days.' and sort 'Next review date, soonest first.'.

### 51. View: Overdue reviews

- [ ] Where: Open Reviews in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Overdue reviews is saved with filter 'Review is open and due date is in the past.' and sort 'Due date, oldest first.'.

### 52. View: My advice cases

- [ ] Where: Open Advice cases in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view My advice cases is saved with filter 'Adviser or paraplanner is me and stage is open.' and sort 'Report issued date, oldest first.'.

### 53. View: My prospects

- [ ] Where: Open Deals in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view My prospects is saved with filter 'Owner is me and stage is open.' and sort 'Next step date, soonest first.'.

### 54. View: Clients with a vulnerability flag

- [ ] Where: Open People in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Clients with a vulnerability flag is saved with filter 'Vulnerability flag is possible or confirmed.' and sort 'Last name, A to Z.'.

### 55. View: Households by service tier

- [ ] Where: Open Households in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Households by service tier is saved with filter 'Status is ongoing client.' and sort 'Service tier, then name.'.

## Permissions

### 56. Set roles and access

- [ ] Where: Workspace settings, then Members
- Why it is manual: Attio has no API for workspace roles or object and field access.
- Done when: a non-admin test member sees and edits what their role needs and nothing more.
