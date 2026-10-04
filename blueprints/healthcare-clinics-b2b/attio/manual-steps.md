# Manual steps: Healthcare clinics, B2B (attio)

Generated from `design.yaml`. Do not edit by hand. The Attio API cannot do any of this.
Sources: https://docs.attio.com/llms.txt, https://api.attio.com/openapi/api, `platforms/attio/reference/api-coverage.md`.

## Before and during the build

### 1. Confirm the client's Attio plan allows the objects below

- [ ] Where: Workspace settings, then Billing, and https://attio.com/pricing
- Why it is manual: Object limits depend on the plan (3, 5, 12 or unlimited) and Attio does not say whether standard objects count. A create past the limit fails with 400 quota_exceeded.
- Done when: the plan is written in the client notes and allows 3 custom object(s) (Service, Service contract, Referral agreement).

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
- Done when: each of these objects has a Name attribute: Service, Service contract, Referral agreement. If one does not, add a text attribute with slug `name`.

## Pipelines

### 6. Hide the native Deal stage for Employer and insurer contracts

- [ ] Where: Deals object, then the table or board view, then hide the Stage column
- Why it is manual: Deals require a native stage. The working pipeline is the list `employer_insurer_contracts`, so the native stage would show a second, unused set (Q8).
- Done when: new deals get the first native stage by default and the Deals views use the list's Stage.

### 7. Check the stage order of Employer and insurer contracts

- [ ] Where: Lists in the left sidebar, then Employer and insurer contracts, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Qualified then Discovery then Proposal then Governance review then Pilot then Contract out then Closed won then Closed lost.

### 8. Stage probability for Employer and insurer contracts

- [ ] Where: Lists in the left sidebar, then Employer and insurer contracts, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Qualified 10%; Discovery 25%; Proposal 45%; Governance review 65%; Pilot 75%; Contract out 90%; Closed won 100%; Closed lost 0%) and forecast reports multiply by it.

### 9. Won and lost in Employer and insurer contracts

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Closed won for won and Closed lost for lost.

### 10. Hide the native Deal stage for Contract renewals

- [ ] Where: Deals object, then the table or board view, then hide the Stage column
- Why it is manual: Deals require a native stage. The working pipeline is the list `contract_renewals`, so the native stage would show a second, unused set (Q8).
- Done when: new deals get the first native stage by default and the Deals views use the list's Stage.

### 11. Check the stage order of Contract renewals

- [ ] Where: Lists in the left sidebar, then Contract renewals, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Upcoming then Review meeting then Terms proposed then Awaiting signature then Renewed then Not renewed.

### 12. Stage probability for Contract renewals

- [ ] Where: Lists in the left sidebar, then Contract renewals, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Upcoming 60%; Review meeting 70%; Terms proposed 80%; Awaiting signature 95%; Renewed 100%; Not renewed 0%) and forecast reports multiply by it.

### 13. Won and lost in Contract renewals

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Renewed for won and Not renewed for lost.

### 14. Check the stage order of Referral partners

- [ ] Where: Lists in the left sidebar, then Referral partners, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Identified then Intro meeting then Governance check then Agreement sent then Active then Declined.

### 15. Stage probability for Referral partners

- [ ] Where: Lists in the left sidebar, then Referral partners, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Identified 10%; Intro meeting 30%; Governance check 55%; Agreement sent 80%; Active 100%; Declined 0%) and forecast reports multiply by it.

### 16. Won and lost in Referral partners

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Active for won and Declined for lost.

## Stage gates and lost reasons

### 17. Stage gate (stage gate): Employer and insurer contracts, Qualified

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Employer and insurer contracts where Stage is Qualified
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Qualified with any of these empty are flagged or sent back: Service interest, Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 18. Stage gate (stage gate): Employer and insurer contracts, Discovery

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Employer and insurer contracts where Stage is Discovery
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Discovery with any of these empty are flagged or sent back: Covered headcount, Sites covered, Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 19. Stage gate (stage gate): Employer and insurer contracts, Proposal

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Employer and insurer contracts where Stage is Proposal
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Proposal with any of these empty are flagged or sent back: Amount, Pricing model, Contract term (months). A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 20. Stage gate (stage gate): Employer and insurer contracts, Governance review

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Employer and insurer contracts where Stage is Governance review
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Governance review with any of these empty are flagged or sent back: Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 21. Stage gate (stage gate): Employer and insurer contracts, Pilot

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Employer and insurer contracts where Stage is Pilot
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Pilot with any of these empty are flagged or sent back: Pilot agreed, Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 22. Stage gate (stage gate): Employer and insurer contracts, Contract out

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Employer and insurer contracts where Stage is Contract out
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Contract out with any of these empty are flagged or sent back: Amount, Close date, Governance review passed. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 23. Stage gate (stage gate): Employer and insurer contracts, Closed won

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Employer and insurer contracts where Stage is Closed won
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Closed won with any of these empty are flagged or sent back: Amount, Close date, Governance review passed. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 24. Stage gate (lost reason): Employer and insurer contracts, Closed lost

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Employer and insurer contracts where Stage is Closed lost
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Closed lost with any of these empty are flagged or sent back: Lost reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 25. Stage gate (stage gate): Contract renewals, Upcoming

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Contract renewals where Stage is Upcoming
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Upcoming with any of these empty are flagged or sent back: Renewal risk. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 26. Stage gate (stage gate): Contract renewals, Review meeting

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Contract renewals where Stage is Review meeting
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Review meeting with any of these empty are flagged or sent back: Renewal risk, Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 27. Stage gate (stage gate): Contract renewals, Terms proposed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Contract renewals where Stage is Terms proposed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Terms proposed with any of these empty are flagged or sent back: Amount, Pricing model, Contract term (months). A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 28. Stage gate (stage gate): Contract renewals, Awaiting signature

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Contract renewals where Stage is Awaiting signature
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Awaiting signature with any of these empty are flagged or sent back: Amount, Close date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 29. Stage gate (stage gate): Contract renewals, Renewed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Contract renewals where Stage is Renewed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Renewed with any of these empty are flagged or sent back: Amount, Close date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 30. Stage gate (lost reason): Contract renewals, Not renewed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Contract renewals where Stage is Not renewed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Not renewed with any of these empty are flagged or sent back: Lost reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 31. Stage gate (stage gate): Referral partners, Identified

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Referral partners where Stage is Identified
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Identified with any of these empty are flagged or sent back: Agreement type. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 32. Stage gate (stage gate): Referral partners, Intro meeting

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Referral partners where Stage is Intro meeting
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Intro meeting with any of these empty are flagged or sent back: Fee basis. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 33. Stage gate (stage gate): Referral partners, Governance check

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Referral partners where Stage is Governance check
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Governance check with any of these empty are flagged or sent back: Fee basis. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 34. Stage gate (stage gate): Referral partners, Agreement sent

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Referral partners where Stage is Agreement sent
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Agreement sent with any of these empty are flagged or sent back: Governance checked. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 35. Stage gate (stage gate): Referral partners, Active

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Referral partners where Stage is Active
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Active with any of these empty are flagged or sent back: Signed date, Review date, Governance checked. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 36. Stage gate (lost reason): Referral partners, Declined

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Referral partners where Stage is Declined
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Declined with any of these empty are flagged or sent back: Decline reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

## Decisions where the Attio mapping is lossy

### 37. Renamed attribute slugs

- [ ] Where: Decide with the client; edit platform_overrides.attio in design.yaml and regenerate
- Why it is manual: These keys are slugs Attio uses on its own objects, so the slug got an object prefix.
- Done when: company.owner -> company_owner; person.owner -> person_owner. Each is accepted or overridden.

### 38. Long text is the same type as text

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that long text fields look like short text fields in Attio. Fields: deal.description.

### 39. Currency fields use GBP

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Confirm the account currency. One currency per attribute: change it before data is loaded, because a later change does not convert values. Fields: service.list_price, service_contract.annual_value.

### 40. Phone values must be E.164

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Agree that numbers are written with a + and country code, or with a country code field, on import. Fields: company.phone.

### 41. User fields hold workspace members only

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that people outside the workspace cannot be chosen. Fields: company.owner, person.owner, service_contract.account_manager.

### 42. Checkbox fields cannot be empty

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that unticked and unknown look the same. Fields: deal.governance_review_passed, deal.pilot_agreed, service.active, service.regulated, service_contract.dpa_signed, referral_agreement.governance_checked.

### 43. Select options cannot be reordered or deleted

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Order follows creation order, so options are sent in design order. Removing one means archiving it. Fields: deal.service_interest.

## Workflows

### 44. Workflow: Create service contract on win

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A deal in the employer and insurer contracts pipeline moves to closed won.'; action 'Create a service contract with the deal's amount, term and services, link it to the deal and the company, set status to pending start and the customer status to active customer.'

### 45. Workflow: Block start without data processing agreement

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A service contract is set to active and the data processing agreement signed box is empty.'; action 'Set the status back to pending start and notify the account manager and the data protection lead.'

### 46. Workflow: Open renewal deal

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A service contract's renewal date is 90 days away and its status is active.'; action 'Create a deal in the contract renewals pipeline at upcoming, linked to the contract, and set the contract status to in renewal.'

### 47. Workflow: Partner review reminder

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'An active referral agreement has a review date within 30 days.'; action 'Create a task for the partnerships owner to hold the review and update the quarterly referral count.'

### 48. Workflow: Flag stalled deals

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'An open deal has no next step date, or the date is more than 7 days past.'; action 'Notify the deal owner and add the deal to the stalled deals view.'

## Views

### 49. View: My open deals

- [ ] Where: Open Deals in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view My open deals is saved with filter 'Owner is me and stage is open.' and sort 'Close date, soonest first.'.

### 50. View: Stalled deals

- [ ] Where: Open Deals in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Stalled deals is saved with filter 'Stage is open and next step date is empty or in the past.' and sort 'Next step date, oldest first.'.

### 51. View: Deals in governance review

- [ ] Where: Open Deals in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Deals in governance review is saved with filter 'Stage is governance review or pilot.' and sort 'Next step date, soonest first.'.

### 52. View: Renewals in the next 90 days

- [ ] Where: Open Service contracts in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Renewals in the next 90 days is saved with filter 'Status is active or in renewal and renewal date is within 90 days.' and sort 'Renewal date, soonest first.'.

### 53. View: Partners due review

- [ ] Where: Open Referral agreements in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Partners due review is saved with filter 'Stage is active and review date is within 60 days.' and sort 'Review date, soonest first.'.

### 54. View: Brokers and insurers

- [ ] Where: Open Companies in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Brokers and insurers is saved with filter 'Account type is insurer or broker.' and sort 'Name, A to Z.'.

## Permissions

### 55. Set roles and access

- [ ] Where: Workspace settings, then Members
- Why it is manual: Attio has no API for workspace roles or object and field access.
- Done when: a non-admin test member sees and edits what their role needs and nothing more.
