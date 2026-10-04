# Manual steps: B2B SaaS, sales-led (attio)

Generated from `design.yaml`. Do not edit by hand. The Attio API cannot do any of this.
Sources: https://docs.attio.com/llms.txt, https://api.attio.com/openapi/api, `platforms/attio/reference/api-coverage.md`.

## Before and during the build

### 1. Confirm the client's Attio plan allows the objects below

- [ ] Where: Workspace settings, then Billing, and https://attio.com/pricing
- Why it is manual: Object limits depend on the plan (3, 5, 12 or unlimited) and Attio does not say whether standard objects count. A create past the limit fails with 400 quota_exceeded.
- Done when: the plan is written in the client notes and allows 2 custom object(s) (Subscription, Onboarding).

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
- Done when: each of these objects has a Name attribute: Subscription, Onboarding. If one does not, add a text attribute with slug `name`.

## Pipelines

### 6. Hide the native Deal stage for New business

- [ ] Where: Deals object, then the table or board view, then hide the Stage column
- Why it is manual: Deals require a native stage. The working pipeline is the list `new_business`, so the native stage would show a second, unused set (Q8).
- Done when: new deals get the first native stage by default and the Deals views use the list's Stage.

### 7. Check the stage order of New business

- [ ] Where: Lists in the left sidebar, then New business, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Qualified then Discovery then Solution fit then Technical validation then Proposal then Negotiation then Contract out then Closed won then Closed lost.

### 8. Stage probability for New business

- [ ] Where: Lists in the left sidebar, then New business, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Qualified 10%; Discovery 20%; Solution fit 35%; Technical validation 50%; Proposal 65%; Negotiation 80%; Contract out 90%; Closed won 100%; Closed lost 0%) and forecast reports multiply by it.

### 9. Won and lost in New business

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Closed won for won and Closed lost for lost.

### 10. Hide the native Deal stage for Renewals and expansion

- [ ] Where: Deals object, then the table or board view, then hide the Stage column
- Why it is manual: Deals require a native stage. The working pipeline is the list `renewals_expansion`, so the native stage would show a second, unused set (Q8).
- Done when: new deals get the first native stage by default and the Deals views use the list's Stage.

### 11. Check the stage order of Renewals and expansion

- [ ] Where: Lists in the left sidebar, then Renewals and expansion, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Upcoming then Outreach then Proposal sent then Negotiation then Awaiting signature then Renewed then Churned.

### 12. Stage probability for Renewals and expansion

- [ ] Where: Lists in the left sidebar, then Renewals and expansion, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Upcoming 60%; Outreach 65%; Proposal sent 75%; Negotiation 85%; Awaiting signature 95%; Renewed 100%; Churned 0%) and forecast reports multiply by it.

### 13. Won and lost in Renewals and expansion

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Renewed for won and Churned for lost.

## Stage gates and lost reasons

### 14. Stage gate (stage gate): New business, Qualified

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New business where Stage is Qualified
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Qualified with any of these empty are flagged or sent back: Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 15. Stage gate (stage gate): New business, Discovery

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New business where Stage is Discovery
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Discovery with any of these empty are flagged or sent back: Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 16. Stage gate (stage gate): New business, Solution fit

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New business where Stage is Solution fit
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Solution fit with any of these empty are flagged or sent back: Pain summary, Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 17. Stage gate (stage gate): New business, Technical validation

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New business where Stage is Technical validation
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Technical validation with any of these empty are flagged or sent back: Decision process, Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 18. Stage gate (stage gate): New business, Proposal

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New business where Stage is Proposal
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Proposal with any of these empty are flagged or sent back: Budget confirmed, Amount, Contract term (months). A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 19. Stage gate (stage gate): New business, Negotiation

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New business where Stage is Negotiation
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Negotiation with any of these empty are flagged or sent back: Amount, Close date, Security review. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 20. Stage gate (stage gate): New business, Contract out

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New business where Stage is Contract out
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Contract out with any of these empty are flagged or sent back: Amount, Close date, Contract term (months). A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 21. Stage gate (stage gate): New business, Closed won

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New business where Stage is Closed won
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Closed won with any of these empty are flagged or sent back: Amount, Close date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 22. Stage gate (lost reason): New business, Closed lost

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on New business where Stage is Closed lost
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Closed lost with any of these empty are flagged or sent back: Lost reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 23. Stage gate (stage gate): Renewals and expansion, Upcoming

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Renewals and expansion where Stage is Upcoming
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Upcoming with any of these empty are flagged or sent back: Renewal type. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 24. Stage gate (stage gate): Renewals and expansion, Outreach

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Renewals and expansion where Stage is Outreach
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Outreach with any of these empty are flagged or sent back: Renewal risk, Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 25. Stage gate (stage gate): Renewals and expansion, Proposal sent

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Renewals and expansion where Stage is Proposal sent
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Proposal sent with any of these empty are flagged or sent back: Amount, Contract term (months). A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 26. Stage gate (stage gate): Renewals and expansion, Negotiation

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Renewals and expansion where Stage is Negotiation
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Negotiation with any of these empty are flagged or sent back: Amount, Close date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 27. Stage gate (stage gate): Renewals and expansion, Awaiting signature

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Renewals and expansion where Stage is Awaiting signature
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Awaiting signature with any of these empty are flagged or sent back: Amount, Close date, Contract term (months). A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 28. Stage gate (stage gate): Renewals and expansion, Renewed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Renewals and expansion where Stage is Renewed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Renewed with any of these empty are flagged or sent back: Amount, Close date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 29. Stage gate (lost reason): Renewals and expansion, Churned

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Renewals and expansion where Stage is Churned
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Churned with any of these empty are flagged or sent back: Lost reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

## Decisions where the Attio mapping is lossy

### 30. Renamed attribute slugs

- [ ] Where: Decide with the client; edit platform_overrides.attio in design.yaml and regenerate
- Why it is manual: These keys are slugs Attio uses on its own objects, so the slug got an object prefix.
- Done when: company.owner -> company_owner; person.owner -> person_owner; onboarding.owner -> onboarding_owner. Each is accepted or overridden.

### 31. Long text is the same type as text

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that long text fields look like short text fields in Attio. Fields: deal.description, deal.pain_summary, deal.decision_process.

### 32. Currency fields use GBP

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Confirm the account currency. One currency per attribute: change it before data is loaded, because a later change does not convert values. Fields: subscription.arr.

### 33. Phone values must be E.164

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Agree that numbers are written with a + and country code, or with a country code field, on import. Fields: company.phone.

### 34. User fields hold workspace members only

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that people outside the workspace cannot be chosen. Fields: company.owner, person.owner, subscription.success_owner, onboarding.owner.

### 35. Checkbox fields cannot be empty

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that unticked and unknown look the same. Fields: deal.budget_confirmed, subscription.auto_renews.

## Workflows

### 36. Workflow: Create subscription on closed won

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A deal in the new business pipeline moves to closed won.'; action 'Create a subscription from the deal's amount, term and close date, link it to the deal and the company, and set the company's customer status to customer.'

### 37. Workflow: Start onboarding

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A subscription is created with status pending start.'; action 'Create an onboarding record linked to the subscription and assign it to customer success.'

### 38. Workflow: Open renewal deal

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A subscription's renewal date is 90 days away and its status is active.'; action 'Create a deal in the renewals and expansion pipeline at upcoming, linked to the subscription, and set the subscription status to in renewal.'

### 39. Workflow: Flag stalled deals

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'An open deal has no next step date, or the date is more than 7 days past.'; action 'Notify the deal owner and add the deal to the stalled deals view.'

### 40. Workflow: Mark churn

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A deal in the renewals and expansion pipeline moves to churned.'; action 'Set the subscription status to churned and the company's customer status to former customer.'

## Views

### 41. View: My open deals

- [ ] Where: Open Deals in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view My open deals is saved with filter 'Owner is me and stage is open.' and sort 'Close date, soonest first.'.

### 42. View: Stalled deals

- [ ] Where: Open Deals in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Stalled deals is saved with filter 'Stage is open and next step date is empty or in the past.' and sort 'Next step date, oldest first.'.

### 43. View: Renewals in the next 90 days

- [ ] Where: Open Subscriptions in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Renewals in the next 90 days is saved with filter 'Status is active or in renewal and renewal date is within 90 days.' and sort 'Renewal date, soonest first.'.

### 44. View: Onboarding in flight

- [ ] Where: Open Onboardings in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Onboarding in flight is saved with filter 'Status is not live.' and sort 'Kickoff date, oldest first.'.

### 45. View: Customers

- [ ] Where: Open Companies in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Customers is saved with filter 'Customer status is customer.' and sort 'Name, A to Z.'.

## Permissions

### 46. Set roles and access

- [ ] Where: Workspace settings, then Members
- Why it is manual: Attio has no API for workspace roles or object and field access.
- Done when: a non-admin test member sees and edits what their role needs and nothing more.
