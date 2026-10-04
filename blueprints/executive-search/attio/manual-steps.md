# Manual steps: Executive search (attio)

Generated from `design.yaml`. Do not edit by hand. The Attio API cannot do any of this.
Sources: https://docs.attio.com/llms.txt, https://api.attio.com/openapi/api, `platforms/attio/reference/api-coverage.md`.

## Before and during the build

### 1. Confirm the client's Attio plan allows the objects below

- [ ] Where: Workspace settings, then Billing, and https://attio.com/pricing
- Why it is manual: Object limits depend on the plan (3, 5, 12 or unlimited) and Attio does not say whether standard objects count. A create past the limit fails with 400 quota_exceeded.
- Done when: the plan is written in the client notes and allows 3 custom object(s) (Search, Search candidate, Fee instalment).

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
- Done when: each of these objects has a Name attribute: Search, Search candidate, Fee instalment. If one does not, add a text attribute with slug `name`.

## Pipelines

### 6. Hide the native Deal stage for Mandate acquisition

- [ ] Where: Deals object, then the table or board view, then hide the Stage column
- Why it is manual: Deals require a native stage. The working pipeline is the list `mandate_acquisition`, so the native stage would show a second, unused set (Q8).
- Done when: new deals get the first native stage by default and the Deals views use the list's Stage.

### 7. Check the stage order of Mandate acquisition

- [ ] Where: Lists in the left sidebar, then Mandate acquisition, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Target then Introduction then Brief then Proposal sent then Pitch or finalist then Terms agreed then Mandate won then Mandate lost.

### 8. Stage probability for Mandate acquisition

- [ ] Where: Lists in the left sidebar, then Mandate acquisition, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Target 5%; Introduction 15%; Brief 30%; Proposal sent 50%; Pitch or finalist 65%; Terms agreed 85%; Mandate won 100%; Mandate lost 0%) and forecast reports multiply by it.

### 9. Won and lost in Mandate acquisition

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Mandate won for won and Mandate lost for lost.

### 10. Check the stage order of Search delivery

- [ ] Where: Lists in the left sidebar, then Search delivery, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Position specification then Market mapping then Longlist then Shortlist then Client interviews then Offer and references then Placed then Closed without placement.

### 11. Stage probability for Search delivery

- [ ] Where: Lists in the left sidebar, then Search delivery, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Position specification 100%; Market mapping 100%; Longlist 100%; Shortlist 100%; Client interviews 100%; Offer and references 100%; Placed 100%; Closed without placement 0%) and forecast reports multiply by it.

### 12. Won and lost in Search delivery

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Placed for won and Closed without placement for lost.

### 13. Check the stage order of Candidate progress

- [ ] Where: Lists in the left sidebar, then Candidate progress, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Identified then Approached then Engaged then Assessed then Shortlisted then Client interview then Offer then Placed then Out.

### 14. Stage probability for Candidate progress

- [ ] Where: Lists in the left sidebar, then Candidate progress, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Identified 5%; Approached 15%; Engaged 30%; Assessed 45%; Shortlisted 60%; Client interview 75%; Offer 90%; Placed 100%; Out 0%) and forecast reports multiply by it.

### 15. Won and lost in Candidate progress

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Placed for won and Out for lost.

### 16. Check the stage order of Fee collection

- [ ] Where: Lists in the left sidebar, then Fee collection, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Scheduled then Due then Invoiced then Paid then Waived.

### 17. Stage probability for Fee collection

- [ ] Where: Lists in the left sidebar, then Fee collection, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Scheduled 80%; Due 90%; Invoiced 95%; Paid 100%; Waived 0%) and forecast reports multiply by it.

### 18. Won and lost in Fee collection

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Paid for won and Waived for lost.

## Stage gates and lost reasons

### 19. Stage gate (stage gate): Mandate acquisition, Target

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Mandate acquisition where Stage is Target
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Target with any of these empty are flagged or sent back: Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 20. Stage gate (stage gate): Mandate acquisition, Introduction

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Mandate acquisition where Stage is Introduction
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Introduction with any of these empty are flagged or sent back: Role title, Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 21. Stage gate (stage gate): Mandate acquisition, Brief

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Mandate acquisition where Stage is Brief
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Brief with any of these empty are flagged or sent back: Role title, Expected total compensation, Competing firms. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 22. Stage gate (stage gate): Mandate acquisition, Proposal sent

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Mandate acquisition where Stage is Proposal sent
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Proposal sent with any of these empty are flagged or sent back: Fee percent, Fee structure, Amount. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 23. Stage gate (stage gate): Mandate acquisition, Pitch or finalist

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Mandate acquisition where Stage is Pitch or finalist
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Pitch or finalist with any of these empty are flagged or sent back: Competing firms, Close date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 24. Stage gate (stage gate): Mandate acquisition, Terms agreed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Mandate acquisition where Stage is Terms agreed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Terms agreed with any of these empty are flagged or sent back: Fee percent, Fee structure, Exclusivity confirmed, Close date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 25. Stage gate (stage gate): Mandate acquisition, Mandate won

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Mandate acquisition where Stage is Mandate won
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Mandate won with any of these empty are flagged or sent back: Amount, Close date, Fee structure. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 26. Stage gate (lost reason): Mandate acquisition, Mandate lost

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Mandate acquisition where Stage is Mandate lost
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Mandate lost with any of these empty are flagged or sent back: Lost reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 27. Stage gate (stage gate): Search delivery, Position specification

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Search delivery where Stage is Position specification
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Position specification with any of these empty are flagged or sent back: Partner, Consultant. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 28. Stage gate (stage gate): Search delivery, Market mapping

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Search delivery where Stage is Market mapping
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Market mapping with any of these empty are flagged or sent back: Engaged date, Target shortlist date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 29. Stage gate (stage gate): Search delivery, Longlist

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Search delivery where Stage is Longlist
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Longlist with any of these empty are flagged or sent back: Longlist size. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 30. Stage gate (stage gate): Search delivery, Shortlist

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Search delivery where Stage is Shortlist
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Shortlist with any of these empty are flagged or sent back: Target placement date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 31. Stage gate (stage gate): Search delivery, Client interviews

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Search delivery where Stage is Client interviews
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Client interviews with any of these empty are flagged or sent back: Target placement date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 32. Stage gate (stage gate): Search delivery, Offer and references

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Search delivery where Stage is Offer and references
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Offer and references with any of these empty are flagged or sent back: Total fee. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 33. Stage gate (stage gate): Search delivery, Placed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Search delivery where Stage is Placed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Placed with any of these empty are flagged or sent back: Total fee. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 34. Stage gate (lost reason): Search delivery, Closed without placement

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Search delivery where Stage is Closed without placement
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Closed without placement with any of these empty are flagged or sent back: Close reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 35. Stage gate (stage gate): Candidate progress, Identified

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Candidate progress where Stage is Identified
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Identified with any of these empty are flagged or sent back: Source. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 36. Stage gate (stage gate): Candidate progress, Approached

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Candidate progress where Stage is Approached
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Approached with any of these empty are flagged or sent back: Outreach date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 37. Stage gate (stage gate): Candidate progress, Engaged

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Candidate progress where Stage is Engaged
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Engaged with any of these empty are flagged or sent back: Motivation. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 38. Stage gate (stage gate): Candidate progress, Assessed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Candidate progress where Stage is Assessed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Assessed with any of these empty are flagged or sent back: Interview date, Assessment rating. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 39. Stage gate (stage gate): Candidate progress, Shortlisted

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Candidate progress where Stage is Shortlisted
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Shortlisted with any of these empty are flagged or sent back: Assessment rating, Client feedback. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 40. Stage gate (stage gate): Candidate progress, Client interview

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Candidate progress where Stage is Client interview
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Client interview with any of these empty are flagged or sent back: Client interview date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 41. Stage gate (stage gate): Candidate progress, Offer

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Candidate progress where Stage is Offer
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Offer with any of these empty are flagged or sent back: Offered compensation. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 42. Stage gate (stage gate): Candidate progress, Placed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Candidate progress where Stage is Placed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Placed with any of these empty are flagged or sent back: Offered compensation, Start date, References complete. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 43. Stage gate (lost reason): Candidate progress, Out

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Candidate progress where Stage is Out
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Out with any of these empty are flagged or sent back: Out reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 44. Stage gate (stage gate): Fee collection, Scheduled

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Fee collection where Stage is Scheduled
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Scheduled with any of these empty are flagged or sent back: Amount, Trigger. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 45. Stage gate (stage gate): Fee collection, Due

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Fee collection where Stage is Due
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Due with any of these empty are flagged or sent back: Due date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 46. Stage gate (stage gate): Fee collection, Invoiced

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Fee collection where Stage is Invoiced
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Invoiced with any of these empty are flagged or sent back: Invoice reference. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 47. Stage gate (stage gate): Fee collection, Paid

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Fee collection where Stage is Paid
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Paid with any of these empty are flagged or sent back: Invoice reference. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 48. Stage gate (lost reason): Fee collection, Waived

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Fee collection where Stage is Waived
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Waived with any of these empty are flagged or sent back: Waiver reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

## Decisions where the Attio mapping is lossy

### 49. Renamed attribute slugs

- [ ] Where: Decide with the client; edit platform_overrides.attio in design.yaml and regenerate
- Why it is manual: These keys are slugs Attio uses on its own objects, so the slug got an object prefix.
- Done when: company.owner -> company_owner; person.owner -> person_owner. Each is accepted or overridden.

### 50. Percent fields are plain numbers

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Decide whether percentages are stored as 0 to 100 or 0 to 1. The generated description says 0 to 100. Fields: deal.fee_percent.

### 51. Long text is the same type as text

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that long text fields look like short text fields in Attio. Fields: deal.description.

### 52. Currency fields use GBP

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Confirm the account currency. One currency per attribute: change it before data is loaded, because a later change does not convert values. Fields: person.current_total_compensation, deal.expected_total_compensation, search.expected_total_compensation, search.total_fee, search_candidate.offered_compensation, fee_instalment.amount.

### 53. Phone values must be E.164

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Agree that numbers are written with a + and country code, or with a country code field, on import. Fields: company.phone.

### 54. User fields hold workspace members only

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that people outside the workspace cannot be chosen. Fields: company.owner, person.owner, search.partner, search.consultant.

### 55. Checkbox fields cannot be empty

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that unticked and unknown look the same. Fields: deal.confidential_search, deal.exclusivity_confirmed, search.confidential, search_candidate.references_complete.

### 56. Select options cannot be reordered or deleted

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Order follows creation order, so options are sent in design order. Removing one means archiving it. Fields: person.person_type.

## Workflows

### 57. Workflow: Create search on mandate won

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A deal in the mandate acquisition pipeline moves to mandate won.'; action 'Create a search from the deal's role title, compensation and fee terms, link it to the deal and company, set it to position specification, and set the company's client status to active client.'

### 58. Workflow: Create fee schedule

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A search is created with a total fee and a fee structure on its deal.'; action 'Create the fee instalments in the fee collection pipeline at scheduled, with trigger and amount from the fee structure.'

### 59. Workflow: Make instalments due

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A search reaches the shortlist stage or placed, or an instalment's set date arrives.'; action 'Move the matching instalment to due, set its due date and notify finance.'

### 60. Workflow: Set off-limits on signing

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A deal moves to mandate won.'; action 'Set the company's off-limits until date from the agreement and flag its people as off-limits for approaches.'

### 61. Workflow: Shortlist timetable alert

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A search is not yet at shortlist and its target shortlist date is 7 days away.'; action 'Notify the partner and consultant with the number of assessed candidates.'

### 62. Workflow: Close other candidates

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A search candidate moves to placed.'; action 'Move every other open search candidate on the search to out with a reason of client did not proceed, set the search to placed, and prompt the consultant to send candidate courtesy notes.'

### 63. Workflow: Review candidate data

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A person of type candidate has a data review date in 30 days.'; action 'Notify the owner to confirm consent or delete the record.'

## Views

### 64. View: Active searches

- [ ] Where: Open Searches in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Active searches is saved with filter 'Stage is open.' and sort 'Target shortlist date, soonest first.'.

### 65. View: Longlist

- [ ] Where: Open Search candidates in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Longlist is saved with filter 'Search is the chosen search and stage is identified, approached or engaged.' and sort 'Motivation, strongest first.'.

### 66. View: Shortlist

- [ ] Where: Open Search candidates in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Shortlist is saved with filter 'Search is the chosen search and stage is shortlisted, client interview or offer.' and sort 'Assessment rating, strongest first.'.

### 67. View: Instalments to invoice

- [ ] Where: Open Fee instalments in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Instalments to invoice is saved with filter 'Stage is due.' and sort 'Due date, oldest first.'.

### 68. View: Outstanding fees

- [ ] Where: Open Fee instalments in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Outstanding fees is saved with filter 'Stage is invoiced.' and sort 'Due date, oldest first.'.

### 69. View: My open mandate deals

- [ ] Where: Open Deals in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view My open mandate deals is saved with filter 'Owner is me and stage is open.' and sort 'Close date, soonest first.'.

### 70. View: Stalled deals

- [ ] Where: Open Deals in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Stalled deals is saved with filter 'Stage is open and next step date is empty or in the past.' and sort 'Next step date, oldest first.'.

## Permissions

### 71. Set roles and access

- [ ] Where: Workspace settings, then Members
- Why it is manual: Attio has no API for workspace roles or object and field access.
- Done when: a non-admin test member sees and edits what their role needs and nothing more.
