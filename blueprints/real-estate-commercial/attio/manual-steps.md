# Manual steps: Commercial real estate, leasing (attio)

Generated from `design.yaml`. Do not edit by hand. The Attio API cannot do any of this.
Sources: https://docs.attio.com/llms.txt, https://api.attio.com/openapi/api, `platforms/attio/reference/api-coverage.md`.

## Before and during the build

### 1. Confirm the client's Attio plan allows the objects below

- [ ] Where: Workspace settings, then Billing, and https://attio.com/pricing
- Why it is manual: Object limits depend on the plan (3, 5, 12 or unlimited) and Attio does not say whether standard objects count. A create past the limit fails with 400 quota_exceeded.
- Done when: the plan is written in the client notes and allows 2 custom object(s) (Property, Lease).

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
- Done when: each of these objects has a Name attribute: Property, Lease. If one does not, add a text attribute with slug `name`.

## Pipelines

### 6. Hide the native Deal stage for Letting

- [ ] Where: Deals object, then the table or board view, then hide the Stage column
- Why it is manual: Deals require a native stage. The working pipeline is the list `letting`, so the native stage would show a second, unused set (Q8).
- Done when: new deals get the first native stage by default and the Deals views use the list's Stage.

### 7. Check the stage order of Letting

- [ ] Where: Lists in the left sidebar, then Letting, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Enquiry then Requirement qualified then Viewing then Offer then Heads of terms then Referencing then Legals then Completed then Lost.

### 8. Stage probability for Letting

- [ ] Where: Lists in the left sidebar, then Letting, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Enquiry 5%; Requirement qualified 15%; Viewing 30%; Offer 50%; Heads of terms 65%; Referencing 75%; Legals 85%; Completed 100%; Lost 0%) and forecast reports multiply by it.

### 9. Won and lost in Letting

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Completed for won and Lost for lost.

### 10. Check the stage order of Lease renewal

- [ ] Where: Lists in the left sidebar, then Lease renewal, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Upcoming then Tenant contacted then Terms discussed then Renewal agreed then Renewed then Not renewed.

### 11. Stage probability for Lease renewal

- [ ] Where: Lists in the left sidebar, then Lease renewal, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Upcoming 40%; Tenant contacted 50%; Terms discussed 70%; Renewal agreed 90%; Renewed 100%; Not renewed 0%) and forecast reports multiply by it.

### 12. Won and lost in Lease renewal

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Renewed for won and Not renewed for lost.

## Stage gates and lost reasons

### 13. Stage gate (stage gate): Letting, Enquiry

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Letting where Stage is Enquiry
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Enquiry with any of these empty are flagged or sent back: Instruction type. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 14. Stage gate (stage gate): Letting, Requirement qualified

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Letting where Stage is Requirement qualified
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Requirement qualified with any of these empty are flagged or sent back: Size required (sq ft), Target move date, Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 15. Stage gate (stage gate): Letting, Viewing

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Letting where Stage is Viewing
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Viewing with any of these empty are flagged or sent back: Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 16. Stage gate (stage gate): Letting, Offer

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Letting where Stage is Offer
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Offer with any of these empty are flagged or sent back: Viewing held, Headline rent (per year). A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 17. Stage gate (stage gate): Letting, Heads of terms

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Letting where Stage is Heads of terms
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Heads of terms with any of these empty are flagged or sent back: Heads of terms status, Headline rent (per year). A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 18. Stage gate (stage gate): Letting, Referencing

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Letting where Stage is Referencing
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Referencing with any of these empty are flagged or sent back: Referencing status. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 19. Stage gate (stage gate): Letting, Legals

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Letting where Stage is Legals
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Legals with any of these empty are flagged or sent back: Referencing status, Solicitors instructed, Close date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 20. Stage gate (stage gate): Letting, Completed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Letting where Stage is Completed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Completed with any of these empty are flagged or sent back: Headline rent (per year), Close date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 21. Stage gate (lost reason): Letting, Lost

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Letting where Stage is Lost
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Lost with any of these empty are flagged or sent back: Lost reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 22. Stage gate (stage gate): Lease renewal, Upcoming

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Lease renewal where Stage is Upcoming
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Upcoming with any of these empty are flagged or sent back: Expiry date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 23. Stage gate (stage gate): Lease renewal, Tenant contacted

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Lease renewal where Stage is Tenant contacted
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Tenant contacted with any of these empty are flagged or sent back: Lease manager. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 24. Stage gate (stage gate): Lease renewal, Terms discussed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Lease renewal where Stage is Terms discussed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Terms discussed with any of these empty are flagged or sent back: Annual rent, Inside security of tenure. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 25. Stage gate (stage gate): Lease renewal, Renewal agreed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Lease renewal where Stage is Renewal agreed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Renewal agreed with any of these empty are flagged or sent back: Annual rent, Expiry date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 26. Stage gate (stage gate): Lease renewal, Renewed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Lease renewal where Stage is Renewed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Renewed with any of these empty are flagged or sent back: Annual rent, Expiry date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 27. Stage gate (lost reason): Lease renewal, Not renewed

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Lease renewal where Stage is Not renewed
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Not renewed with any of these empty are flagged or sent back: Outcome reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

## Decisions where the Attio mapping is lossy

### 28. Renamed attribute slugs

- [ ] Where: Decide with the client; edit platform_overrides.attio in design.yaml and regenerate
- Why it is manual: These keys are slugs Attio uses on its own objects, so the slug got an object prefix.
- Done when: company.owner -> company_owner; person.owner -> person_owner. Each is accepted or overridden.

### 29. Long text is the same type as text

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that long text fields look like short text fields in Attio. Fields: deal.description.

### 30. Currency fields use GBP

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Confirm the account currency. One currency per attribute: change it before data is loaded, because a later change does not convert values. Fields: deal.headline_rent, property.asking_rent_psf, lease.annual_rent.

### 31. Phone values must be E.164

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Agree that numbers are written with a + and country code, or with a country code field, on import. Fields: company.phone.

### 32. User fields hold workspace members only

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that people outside the workspace cannot be chosen. Fields: company.owner, person.owner, lease.managing_owner.

### 33. Checkbox fields cannot be empty

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that unticked and unknown look the same. Fields: deal.viewing_held, deal.solicitors_instructed, lease.security_of_tenure.

### 34. Select options cannot be reordered or deleted

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Order follows creation order, so options are sent in design order. Removing one means archiving it. Fields: company.company_roles.

## Workflows

### 35. Workflow: Create lease on completion

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A deal in the letting pipeline moves to completed.'; action 'Create a lease from the deal's rent and dates, link it to the property and the tenant, set the company's relationship status to current tenant and reduce the property's available area.'

### 36. Workflow: Open renewal

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A lease is 12 months from its expiry or break date and its status is active.'; action 'Move the lease to upcoming in the renewal pipeline and notify the lease manager.'

### 37. Workflow: Rent review reminder

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A lease's next rent review is 6 months away.'; action 'Create a task for the lease manager to prepare the rent review.'

### 38. Workflow: Flag stalled lettings

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'An open letting deal has no next step date, or the date is more than 7 days past.'; action 'Notify the deal owner and add the deal to the stalled lettings view.'

### 39. Workflow: Match requirement to space

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A deal reaches requirement qualified.'; action 'Create a task to list properties with available area and market area that fit the requirement.'

### 40. Workflow: Free the space

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A lease moves to not renewed.'; action 'Set its status to ended and create a task to update the property's availability.'

## Views

### 41. View: Available space

- [ ] Where: Open Properties in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Available space is saved with filter 'Availability is part available or fully available.' and sort 'Available area, largest first.'.

### 42. View: Open lettings

- [ ] Where: Open Deals in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Open lettings is saved with filter 'Owner is me and stage is open.' and sort 'Close date, soonest first.'.

### 43. View: Stalled lettings

- [ ] Where: Open Deals in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Stalled lettings is saved with filter 'Stage is open and next step date is empty or in the past.' and sort 'Next step date, oldest first.'.

### 44. View: Expiries and breaks in 18 months

- [ ] Where: Open Leases in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Expiries and breaks in 18 months is saved with filter 'Status is active and expiry date or break date is within 18 months.' and sort 'Expiry date, soonest first.'.

### 45. View: Rent reviews due

- [ ] Where: Open Leases in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Rent reviews due is saved with filter 'Status is active and next rent review is within 6 months.' and sort 'Next rent review, soonest first.'.

### 46. View: Active requirements

- [ ] Where: Open Companies in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Active requirements is saved with filter 'Relationship status is active requirement.' and sort 'Name, A to Z.'.

## Permissions

### 47. Set roles and access

- [ ] Where: Workspace settings, then Members
- Why it is manual: Attio has no API for workspace roles or object and field access.
- Done when: a non-admin test member sees and edits what their role needs and nothing more.
