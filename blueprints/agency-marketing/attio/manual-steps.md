# Manual steps: Agency, marketing and creative (attio)

Generated from `design.yaml`. Do not edit by hand. The Attio API cannot do any of this.
Sources: https://docs.attio.com/llms.txt, https://api.attio.com/openapi/api, `platforms/attio/reference/api-coverage.md`.

## Before and during the build

### 1. Confirm the client's Attio plan allows the objects below

- [ ] Where: Workspace settings, then Billing, and https://attio.com/pricing
- Why it is manual: Object limits depend on the plan (3, 5, 12 or unlimited) and Attio does not say whether standard objects count. A create past the limit fails with 400 quota_exceeded.
- Done when: the plan is written in the client notes and allows 1 custom object(s) (Engagement).

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
- Done when: each of these objects has a Name attribute: Engagement. If one does not, add a text attribute with slug `name`.

## Pipelines

### 6. Hide the native Deal stage for New business

- [ ] Where: Deals object, then the table or board view, then hide the Stage column
- Why it is manual: Deals require a native stage. The working pipeline is the list `new_business`, so the native stage would show a second, unused set (Q8).
- Done when: new deals get the first native stage by default and the Deals views use the list's Stage.

### 7. Check the stage order of New business

- [ ] Where: Lists in the left sidebar, then New business, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Lead then Discovery then Brief and scope then Proposal sent then Pitch or review then Negotiation then Closed won then Closed lost.

### 8. Stage probability for New business

- [ ] Where: Lists in the left sidebar, then New business, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Lead 5%; Discovery 20%; Brief and scope 35%; Proposal sent 50%; Pitch or review 65%; Negotiation 80%; Closed won 100%; Closed lost 0%) and forecast reports multiply by it.

### 9. Won and lost in New business

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Closed won for won and Closed lost for lost.

### 10. Hide the native Deal stage for Retainer renewals

- [ ] Where: Deals object, then the table or board view, then hide the Stage column
- Why it is manual: Deals require a native stage. The working pipeline is the list `retainer_renewals`, so the native stage would show a second, unused set (Q8).
- Done when: new deals get the first native stage by default and the Deals views use the list's Stage.

### 11. Check the stage order of Retainer renewals

- [ ] Where: Lists in the left sidebar, then Retainer renewals, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Upcoming then Review booked then Proposal sent then Negotiation then Awaiting signature then Renewed then Not renewed.

### 12. Stage probability for Retainer renewals

- [ ] Where: Lists in the left sidebar, then Retainer renewals, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Upcoming 60%; Review booked 65%; Proposal sent 75%; Negotiation 85%; Awaiting signature 95%; Renewed 100%; Not renewed 0%) and forecast reports multiply by it.

### 13. Won and lost in Retainer renewals

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Renewed for won and Not renewed for lost.

### 14. Check the stage order of Delivery

- [ ] Where: Lists in the left sidebar, then Delivery, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Onboarding then Kickoff done then First deliverables then Steady state then At risk then Wrapping up then Completed then Terminated.

### 15. Stage probability for Delivery

- [ ] Where: Lists in the left sidebar, then Delivery, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Onboarding 100%; Kickoff done 100%; First deliverables 100%; Steady state 100%; At risk 100%; Wrapping up 100%; Completed 100%; Terminated 0%) and forecast reports multiply by it.

### 16. Won and lost in Delivery

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Completed for won and Terminated for lost.

## Stage gates and lost reasons

### 17. Stage gate (stage gate): New business, Lead

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New business where Stage is Lead
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Lead with any of these empty are flagged or sent back: Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 18. Stage gate (stage gate): New business, Discovery

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New business where Stage is Discovery
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Discovery with any of these empty are flagged or sent back: Next step date, Budget range. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 19. Stage gate (stage gate): New business, Brief and scope

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New business where Stage is Brief and scope
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Brief and scope with any of these empty are flagged or sent back: Brief received, Service lines, Engagement type. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 20. Stage gate (stage gate): New business, Proposal sent

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New business where Stage is Proposal sent
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Proposal sent with any of these empty are flagged or sent back: Amount, Decision date, Competitive pitch. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 21. Stage gate (stage gate): New business, Pitch or review

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New business where Stage is Pitch or review
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Pitch or review with any of these empty are flagged or sent back: Decision date, Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 22. Stage gate (stage gate): New business, Negotiation

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New business where Stage is Negotiation
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Negotiation with any of these empty are flagged or sent back: Amount, Close date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 23. Stage gate (stage gate): New business, Closed won

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New business where Stage is Closed won
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Closed won with any of these empty are flagged or sent back: Amount, Close date, Engagement type. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 24. Stage gate (lost reason): New business, Closed lost

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New business where Stage is Closed lost
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Closed lost with any of these empty are flagged or sent back: Lost reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 25. Stage gate (stage gate): Retainer renewals, Upcoming

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Retainer renewals where Stage is Upcoming
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Upcoming with any of these empty are flagged or sent back: Renewal type. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 26. Stage gate (stage gate): Retainer renewals, Review booked

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Retainer renewals where Stage is Review booked
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Review booked with any of these empty are flagged or sent back: Renewal risk, Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 27. Stage gate (stage gate): Retainer renewals, Proposal sent

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Retainer renewals where Stage is Proposal sent
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Proposal sent with any of these empty are flagged or sent back: Amount. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 28. Stage gate (stage gate): Retainer renewals, Negotiation

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Retainer renewals where Stage is Negotiation
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Negotiation with any of these empty are flagged or sent back: Amount, Close date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 29. Stage gate (stage gate): Retainer renewals, Awaiting signature

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Retainer renewals where Stage is Awaiting signature
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Awaiting signature with any of these empty are flagged or sent back: Amount, Close date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 30. Stage gate (stage gate): Retainer renewals, Renewed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Retainer renewals where Stage is Renewed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Renewed with any of these empty are flagged or sent back: Amount, Close date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 31. Stage gate (lost reason): Retainer renewals, Not renewed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Retainer renewals where Stage is Not renewed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Not renewed with any of these empty are flagged or sent back: Lost reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 32. Stage gate (stage gate): Delivery, Onboarding

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Delivery where Stage is Onboarding
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Onboarding with any of these empty are flagged or sent back: Account lead, Delivery lead. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 33. Stage gate (stage gate): Delivery, Kickoff done

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Delivery where Stage is Kickoff done
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Kickoff done with any of these empty are flagged or sent back: Access received, Scope summary. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 34. Stage gate (stage gate): Delivery, First deliverables

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Delivery where Stage is First deliverables
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering First deliverables with any of these empty are flagged or sent back: Next review date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 35. Stage gate (stage gate): Delivery, Steady state

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Delivery where Stage is Steady state
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Steady state with any of these empty are flagged or sent back: Health, Next review date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 36. Stage gate (stage gate): Delivery, At risk

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Delivery where Stage is At risk
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering At risk with any of these empty are flagged or sent back: Health, Next review date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 37. Stage gate (stage gate): Delivery, Wrapping up

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Delivery where Stage is Wrapping up
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Wrapping up with any of these empty are flagged or sent back: End date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 38. Stage gate (stage gate): Delivery, Completed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Delivery where Stage is Completed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Completed with any of these empty are flagged or sent back: End date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 39. Stage gate (lost reason): Delivery, Terminated

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Delivery where Stage is Terminated
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Terminated with any of these empty are flagged or sent back: End reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

## Decisions where the Attio mapping is lossy

### 40. Renamed attribute slugs

- [ ] Where: Decide with the client; edit platform_overrides.attio in design.yaml and regenerate
- Why it is manual: These keys are slugs Attio uses on its own objects, so the slug got an object prefix.
- Done when: company.owner -> company_owner; person.owner -> person_owner. Each is accepted or overridden.

### 41. Long text is the same type as text

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that long text fields look like short text fields in Attio. Fields: deal.description, engagement.scope_summary.

### 42. Currency fields use GBP

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Confirm the account currency. One currency per attribute: change it before data is loaded, because a later change does not convert values. Fields: engagement.monthly_fee, engagement.project_fee.

### 43. Phone values must be E.164

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Agree that numbers are written with a + and country code, or with a country code field, on import. Fields: company.phone.

### 44. User fields hold workspace members only

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that people outside the workspace cannot be chosen. Fields: company.owner, person.owner, engagement.account_lead, engagement.delivery_lead.

### 45. Checkbox fields cannot be empty

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that unticked and unknown look the same. Fields: deal.brief_received, deal.competitive_pitch, engagement.access_received.

### 46. Select options cannot be reordered or deleted

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Order follows creation order, so options are sent in design order. Removing one means archiving it. Fields: deal.service_lines.

## Workflows

### 47. Workflow: Create engagement on closed won

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A deal in the new business pipeline moves to closed won.'; action 'Create an engagement from the deal's engagement type, amount, service lines and close date, link it to the deal and company, set it to onboarding, and set the company's client status to active client.'

### 48. Workflow: Notify delivery team

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'An engagement is created.'; action 'Notify the delivery lead and account lead with the scope summary and the signed agreement link.'

### 49. Workflow: Open renewal deal

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A retainer engagement has an end date 90 days away and is not terminated.'; action 'Create a deal in the retainer renewals pipeline at upcoming, linked to the engagement.'

### 50. Workflow: Flag red health

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'An engagement's health is set to red.'; action 'Move it to at risk and notify the account lead and the head of delivery.'

### 51. Workflow: Flag stalled deals

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'An open deal has no next step date, or the date is more than 7 days past.'; action 'Notify the deal owner and add the deal to the stalled deals view.'

### 52. Workflow: Mark past client

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A company's last active engagement moves to completed or terminated and it has no open engagement.'; action 'Set the company's client status to past client.'

## Views

### 53. View: My open deals

- [ ] Where: Open Deals in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view My open deals is saved with filter 'Owner is me and stage is open.' and sort 'Close date, soonest first.'.

### 54. View: Stalled deals

- [ ] Where: Open Deals in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Stalled deals is saved with filter 'Stage is open and next step date is empty or in the past.' and sort 'Next step date, oldest first.'.

### 55. View: Pitches deciding soon

- [ ] Where: Open Deals in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Pitches deciding soon is saved with filter 'Pipeline is new business, stage is open and decision date is within 14 days.' and sort 'Decision date, soonest first.'.

### 56. View: Active engagements

- [ ] Where: Open Engagements in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Active engagements is saved with filter 'Stage is open.' and sort 'Health, red first, then end date.'.

### 57. View: Retainers ending in 90 days

- [ ] Where: Open Engagements in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Retainers ending in 90 days is saved with filter 'Engagement type is retainer, stage is open and end date is within 90 days.' and sort 'End date, soonest first.'.

### 58. View: Reviews overdue

- [ ] Where: Open Engagements in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Reviews overdue is saved with filter 'Stage is open and next review date is empty or in the past.' and sort 'Next review date, oldest first.'.

## Permissions

### 59. Set roles and access

- [ ] Where: Workspace settings, then Members
- Why it is manual: Attio has no API for workspace roles or object and field access.
- Done when: a non-admin test member sees and edits what their role needs and nothing more.
