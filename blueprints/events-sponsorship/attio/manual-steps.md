# Manual steps: Events and sponsorship (attio)

Generated from `design.yaml`. Do not edit by hand. The Attio API cannot do any of this.
Sources: https://docs.attio.com/llms.txt, https://api.attio.com/openapi/api, `platforms/attio/reference/api-coverage.md`.

## Before and during the build

### 1. Confirm the client's Attio plan allows the objects below

- [ ] Where: Workspace settings, then Billing, and https://attio.com/pricing
- Why it is manual: Object limits depend on the plan (3, 5, 12 or unlimited) and Attio does not say whether standard objects count. A create past the limit fails with 400 quota_exceeded.
- Done when: the plan is written in the client notes and allows 3 custom object(s) (Event, Package, Fulfilment).

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
- Done when: each of these objects has a Name attribute: Event, Package, Fulfilment. If one does not, add a text attribute with slug `name`.

## Pipelines

### 6. Hide the native Deal stage for Sponsor sales

- [ ] Where: Deals object, then the table or board view, then hide the Stage column
- Why it is manual: Deals require a native stage. The working pipeline is the list `sponsor_sales`, so the native stage would show a second, unused set (Q8).
- Done when: new deals get the first native stage by default and the Deals views use the list's Stage.

### 7. Check the stage order of Sponsor sales

- [ ] Where: Lists in the left sidebar, then Sponsor sales, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Prospect then Meeting held then Proposal sent then Negotiating then Contract out then Signed then Closed lost.

### 8. Stage probability for Sponsor sales

- [ ] Where: Lists in the left sidebar, then Sponsor sales, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Prospect 5%; Meeting held 20%; Proposal sent 40%; Negotiating 65%; Contract out 85%; Signed 100%; Closed lost 0%) and forecast reports multiply by it.

### 9. Won and lost in Sponsor sales

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Signed for won and Closed lost for lost.

### 10. Hide the native Deal stage for Exhibitor sales

- [ ] Where: Deals object, then the table or board view, then hide the Stage column
- Why it is manual: Deals require a native stage. The working pipeline is the list `exhibitor_sales`, so the native stage would show a second, unused set (Q8).
- Done when: new deals get the first native stage by default and the Deals views use the list's Stage.

### 11. Check the stage order of Exhibitor sales

- [ ] Where: Lists in the left sidebar, then Exhibitor sales, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Enquiry then Qualified then Space held then Contract sent then Confirmed then Closed lost.

### 12. Stage probability for Exhibitor sales

- [ ] Where: Lists in the left sidebar, then Exhibitor sales, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Enquiry 10%; Qualified 30%; Space held 55%; Contract sent 80%; Confirmed 100%; Closed lost 0%) and forecast reports multiply by it.

### 13. Won and lost in Exhibitor sales

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Confirmed for won and Closed lost for lost.

## Stage gates and lost reasons

### 14. Stage gate (stage gate): Sponsor sales, Prospect

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Sponsor sales where Stage is Prospect
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Prospect with any of these empty are flagged or sent back: Sponsor objectives. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 15. Stage gate (stage gate): Sponsor sales, Meeting held

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Sponsor sales where Stage is Meeting held
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Meeting held with any of these empty are flagged or sent back: Sponsor objectives, Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 16. Stage gate (stage gate): Sponsor sales, Proposal sent

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Sponsor sales where Stage is Proposal sent
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Proposal sent with any of these empty are flagged or sent back: Sponsor tier, Amount. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 17. Stage gate (stage gate): Sponsor sales, Negotiating

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Sponsor sales where Stage is Negotiating
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Negotiating with any of these empty are flagged or sent back: Amount, Payment terms, Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 18. Stage gate (stage gate): Sponsor sales, Contract out

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Sponsor sales where Stage is Contract out
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Contract out with any of these empty are flagged or sent back: Amount, Close date, Payment terms. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 19. Stage gate (stage gate): Sponsor sales, Signed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Sponsor sales where Stage is Signed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Signed with any of these empty are flagged or sent back: Amount, Contract signed date, Sponsor tier. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 20. Stage gate (lost reason): Sponsor sales, Closed lost

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Sponsor sales where Stage is Closed lost
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Closed lost with any of these empty are flagged or sent back: Lost reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 21. Stage gate (stage gate): Exhibitor sales, Enquiry

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Exhibitor sales where Stage is Enquiry
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Enquiry with any of these empty are flagged or sent back: Stand type. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 22. Stage gate (stage gate): Exhibitor sales, Qualified

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Exhibitor sales where Stage is Qualified
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Qualified with any of these empty are flagged or sent back: Stand size (sqm), Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 23. Stage gate (stage gate): Exhibitor sales, Space held

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Exhibitor sales where Stage is Space held
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Space held with any of these empty are flagged or sent back: Stand size (sqm), Amount, Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 24. Stage gate (stage gate): Exhibitor sales, Contract sent

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Exhibitor sales where Stage is Contract sent
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Contract sent with any of these empty are flagged or sent back: Amount, Payment terms, Close date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 25. Stage gate (stage gate): Exhibitor sales, Confirmed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Exhibitor sales where Stage is Confirmed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Confirmed with any of these empty are flagged or sent back: Amount, Stand size (sqm), Contract signed date, Deposit received. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 26. Stage gate (lost reason): Exhibitor sales, Closed lost

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Exhibitor sales where Stage is Closed lost
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Closed lost with any of these empty are flagged or sent back: Lost reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

## Decisions where the Attio mapping is lossy

### 27. Renamed attribute slugs

- [ ] Where: Decide with the client; edit platform_overrides.attio in design.yaml and regenerate
- Why it is manual: These keys are slugs Attio uses on its own objects, so the slug got an object prefix.
- Done when: company.owner -> company_owner; person.owner -> person_owner. Each is accepted or overridden.

### 28. Long text is the same type as text

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that long text fields look like short text fields in Attio. Fields: deal.description.

### 29. Currency fields use GBP

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Confirm the account currency. One currency per attribute: change it before data is loaded, because a later change does not convert values. Fields: event.sponsorship_target, event.exhibition_target, package.price.

### 30. Phone values must be E.164

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Agree that numbers are written with a + and country code, or with a country code field, on import. Fields: company.phone.

### 31. User fields hold workspace members only

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that people outside the workspace cannot be chosen. Fields: company.owner, person.owner, event.event_lead, fulfilment.delivery_owner.

### 32. Checkbox fields cannot be empty

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that unticked and unknown look the same. Fields: deal.prior_participant, deal.deposit_received, package.exclusive, fulfilment.assets_received.

### 33. Select options cannot be reordered or deleted

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Order follows creation order, so options are sent in design order. Removing one means archiving it. Fields: deal.sponsor_objectives.

## Workflows

### 34. Workflow: Create fulfilment on win

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A sponsor deal moves to signed, or an exhibitor deal moves to confirmed.'; action 'Create a fulfilment record linked to the deal, event and company, set status to not started, and assign it to the operations team with the sponsor objectives copied into the notes.'

### 35. Workflow: Update package sales

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A deal is won or reopened.'; action 'Recalculate quantity sold on each linked package from won deals and flag any package that is sold out.'

### 36. Workflow: Request assets

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A fulfilment is 60 days before its assets due date and assets received is empty.'; action 'Email the partner contact an asset request and set the fulfilment status to assets requested.'

### 37. Workflow: Start next edition renewals

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'An event is marked completed.'; action 'For each fulfilment with renewal intent will renew or undecided, create a deal on the next edition's event with prior participant ticked, and set the company status to past participant.'

### 38. Workflow: Flag stalled deals

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'An open deal has no next step date, or the date is more than 7 days past.'; action 'Notify the deal owner and add the deal to the stalled deals view.'

## Views

### 39. View: My open deals

- [ ] Where: Open Deals in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view My open deals is saved with filter 'Owner is me and stage is open.' and sort 'Close date, soonest first.'.

### 40. View: Stalled deals

- [ ] Where: Open Deals in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Stalled deals is saved with filter 'Stage is open and next step date is empty or in the past.' and sort 'Next step date, oldest first.'.

### 41. View: Held space

- [ ] Where: Open Deals in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Held space is saved with filter 'Stage is space held in the exhibitor sales pipeline.' and sort 'Next step date, oldest first.'.

### 42. View: Package availability

- [ ] Where: Open Packages in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Package availability is saved with filter 'Quantity sold is below quantity available.' and sort 'Package type, then price, highest first.'.

### 43. View: Assets overdue

- [ ] Where: Open Fulfilments in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Assets overdue is saved with filter 'Assets received is empty and assets due date is in the past.' and sort 'Assets due date, oldest first.'.

### 44. View: Lapsed partners

- [ ] Where: Open Companies in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Lapsed partners is saved with filter 'Participation status is lapsed or past.' and sort 'Name, A to Z.'.

## Permissions

### 45. Set roles and access

- [ ] Where: Workspace settings, then Members
- Why it is manual: Attio has no API for workspace roles or object and field access.
- Done when: a non-admin test member sees and edits what their role needs and nothing more.
