# Manual steps: Construction and trades (attio)

Generated from `design.yaml`. Do not edit by hand. The Attio API cannot do any of this.
Sources: https://docs.attio.com/llms.txt, https://api.attio.com/openapi/api, `platforms/attio/reference/api-coverage.md`.

## Before and during the build

### 1. Confirm the client's Attio plan allows the objects below

- [ ] Where: Workspace settings, then Billing, and https://attio.com/pricing
- Why it is manual: Object limits depend on the plan (3, 5, 12 or unlimited) and Attio does not say whether standard objects count. A create past the limit fails with 400 quota_exceeded.
- Done when: the plan is written in the client notes and allows 3 custom object(s) (Site, Project, Estimate).

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
- Done when: each of these objects has a Name attribute: Site, Project, Estimate. If one does not, add a text attribute with slug `name`.

## Pipelines

### 6. Hide the native Deal stage for Tender and estimate

- [ ] Where: Deals object, then the table or board view, then hide the Stage column
- Why it is manual: Deals require a native stage. The working pipeline is the list `tender_estimate`, so the native stage would show a second, unused set (Q8).
- Done when: new deals get the first native stage by default and the Deals views use the list's Stage.

### 7. Check the stage order of Tender and estimate

- [ ] Where: Lists in the left sidebar, then Tender and estimate, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Opportunity then Go or no-go then Estimating then Bid submitted then Clarification then Preferred bidder then Awarded then Closed lost.

### 8. Stage probability for Tender and estimate

- [ ] Where: Lists in the left sidebar, then Tender and estimate, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Opportunity 5%; Go or no-go 15%; Estimating 25%; Bid submitted 35%; Clarification 55%; Preferred bidder 80%; Awarded 100%; Closed lost 0%) and forecast reports multiply by it.

### 9. Won and lost in Tender and estimate

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Awarded for won and Closed lost for lost.

### 10. Check the stage order of Project delivery

- [ ] Where: Lists in the left sidebar, then Project delivery, then Stage attribute settings
- Why it is manual: The API has no position control for statuses and cannot reorder them. Order follows creation order.
- Done when: the stages read: Pre-start then Mobilising then On site then Snagging then Defects period then Closed out then Cancelled.

### 11. Stage probability for Project delivery

- [ ] Where: Lists in the left sidebar, then Project delivery, then set the Probability column on each entry
- Why it is manual: Attio statuses carry no probability. The list has a Probability number attribute by convention and nothing fills it in or weights a forecast.
- Done when: entries show the probability for their stage (Pre-start 100%; Mobilising 100%; On site 100%; Snagging 100%; Defects period 100%; Closed out 100%; Cancelled 0%) and forecast reports multiply by it.

### 12. Won and lost in Project delivery

- [ ] Where: Reports and dashboards, then filter the list by Stage
- Why it is manual: Attio has no won or lost flag on a status. They are ordinary statuses, so every report that needs closed-won or closed-lost must filter on the status title.
- Done when: reports filter on Stage is Closed out for won and Cancelled for lost.

## Stage gates and lost reasons

### 13. Stage gate (stage gate): Tender and estimate, Opportunity

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Tender and estimate where Stage is Opportunity
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Opportunity with any of these empty are flagged or sent back: Procurement route, Work type. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 14. Stage gate (stage gate): Tender and estimate, Go or no-go

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Tender and estimate where Stage is Go or no-go
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Go or no-go with any of these empty are flagged or sent back: Tender deadline, Go or no-go. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 15. Stage gate (stage gate): Tender and estimate, Estimating

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Tender and estimate where Stage is Estimating
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Estimating with any of these empty are flagged or sent back: Site visit done, Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 16. Stage gate (stage gate): Tender and estimate, Bid submitted

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Tender and estimate where Stage is Bid submitted
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Bid submitted with any of these empty are flagged or sent back: Amount, Estimated margin, Contract form. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 17. Stage gate (stage gate): Tender and estimate, Clarification

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Tender and estimate where Stage is Clarification
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Clarification with any of these empty are flagged or sent back: Next step date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 18. Stage gate (stage gate): Tender and estimate, Preferred bidder

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Tender and estimate where Stage is Preferred bidder
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Preferred bidder with any of these empty are flagged or sent back: Amount, Retention, Expected start date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 19. Stage gate (stage gate): Tender and estimate, Awarded

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Tender and estimate where Stage is Awarded
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Awarded with any of these empty are flagged or sent back: Amount, Close date, Contract form. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 20. Stage gate (lost reason): Tender and estimate, Closed lost

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Tender and estimate where Stage is Closed lost
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Closed lost with any of these empty are flagged or sent back: Lost reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 21. Stage gate (stage gate): Project delivery, Pre-start

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Project delivery where Stage is Pre-start
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Pre-start with any of these empty are flagged or sent back: Contract value. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 22. Stage gate (stage gate): Project delivery, Mobilising

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Project delivery where Stage is Mobilising
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Mobilising with any of these empty are flagged or sent back: Project manager, Planned completion. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 23. Stage gate (stage gate): Project delivery, On site

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Project delivery where Stage is On site
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering On site with any of these empty are flagged or sent back: Start on site, RAMS approved, Insurance verified. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 24. Stage gate (stage gate): Project delivery, Snagging

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Project delivery where Stage is Snagging
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Snagging with any of these empty are flagged or sent back: Planned completion. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 25. Stage gate (stage gate): Project delivery, Defects period

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Project delivery where Stage is Defects period
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Defects period with any of these empty are flagged or sent back: Actual completion, Retention held, Retention release date. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 26. Stage gate (stage gate): Project delivery, Closed out

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Project delivery where Stage is Closed out
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Closed out with any of these empty are flagged or sent back: Final margin. A saved view of entries at this stage with the fields empty is an acceptable alternative.

### 27. Stage gate (lost reason): Project delivery, Cancelled

- [ ] Where: Workflows in the left sidebar, then Create workflow, trigger: list entry updated on Project delivery where Stage is Cancelled
- Why it is manual: Attio cannot require fields per stage. is_required is global to an attribute. The attributes exist and are not required.
- Done when: entries entering Cancelled with any of these empty are flagged or sent back: Cancellation reason. A saved view of entries at this stage with the fields empty is an acceptable alternative.

## Decisions where the Attio mapping is lossy

### 28. Renamed attribute slugs

- [ ] Where: Decide with the client; edit platform_overrides.attio in design.yaml and regenerate
- Why it is manual: These keys are slugs Attio uses on its own objects, so the slug got an object prefix.
- Done when: company.owner -> company_owner; person.owner -> person_owner. Each is accepted or overridden.

### 29. Percent fields are plain numbers

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Decide whether percentages are stored as 0 to 100 or 0 to 1. The generated description says 0 to 100. Fields: deal.estimated_margin, deal.retention_percent, project.final_margin, estimate.margin.

### 30. Long text is the same type as text

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that long text fields look like short text fields in Attio. Fields: deal.description, site.access_notes.

### 31. Currency fields use GBP

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Confirm the account currency. One currency per attribute: change it before data is loaded, because a later change does not convert values. Fields: project.contract_value, project.retention_held, estimate.price.

### 32. Phone values must be E.164

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Agree that numbers are written with a + and country code, or with a country code field, on import. Fields: company.phone.

### 33. User fields hold workspace members only

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that people outside the workspace cannot be chosen. Fields: company.owner, person.owner, project.project_manager, estimate.estimator.

### 34. Checkbox fields cannot be empty

- [ ] Where: Client decision, written in the client notes
- Why it is manual: The Attio type does not match the canonical type exactly.
- Done when: Accept that unticked and unknown look the same. Fields: deal.site_visit_done, site.induction_required, project.rams_approved, project.insurance_verified.

## Workflows

### 35. Workflow: Create project on award

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A deal in the tender and estimate pipeline moves to awarded.'; action 'Create a project linked to the deal, site and client, copy the contract value and work type, and set the company's relationship status to active client.'

### 36. Workflow: Tender deadline reminder

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A deal at estimating or go or no-go has a tender deadline within 3 days.'; action 'Notify the deal owner and the estimator daily until the deal reaches bid submitted.'

### 37. Workflow: Retention release reminder

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'A project in the defects period has a retention release date within 30 days.'; action 'Create a task for the project manager and finance to invoice the retention release.'

### 38. Workflow: Supersede old estimates

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'An estimate is set to issued.'; action 'Set earlier estimates on the same deal to superseded and update the deal amount and estimated margin.'

### 39. Workflow: Flag stalled bids

- [ ] Where: Workflows in the left sidebar, then Create workflow
- Why it is manual: The Attio API has no workflow endpoint.
- Done when: a test run matches: trigger 'An open deal has no next step date, or the date is more than 7 days past.'; action 'Notify the deal owner and add the deal to the stalled bids view.'

## Views

### 40. View: Bids due

- [ ] Where: Open Deals in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Bids due is saved with filter 'Stage is go or no-go or estimating and tender deadline is within 14 days.' and sort 'Tender deadline, soonest first.'.

### 41. View: My open bids

- [ ] Where: Open Deals in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view My open bids is saved with filter 'Owner is me and stage is open.' and sort 'Close date, soonest first.'.

### 42. View: Stalled bids

- [ ] Where: Open Deals in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Stalled bids is saved with filter 'Stage is open and next step date is empty or in the past.' and sort 'Next step date, oldest first.'.

### 43. View: Projects on site

- [ ] Where: Open Projects in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Projects on site is saved with filter 'Stage is on site or snagging.' and sort 'Planned completion, soonest first.'.

### 44. View: Retention due

- [ ] Where: Open Projects in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Retention due is saved with filter 'Stage is defects period and retention release date is within 60 days.' and sort 'Retention release date, soonest first.'.

### 45. View: Dormant clients

- [ ] Where: Open Companies in the left sidebar, then + New view
- Why it is manual: Views are read-only in the Attio API.
- Done when: the view Dormant clients is saved with filter 'Relationship status is dormant.' and sort 'Name, A to Z.'.

## Permissions

### 46. Set roles and access

- [ ] Where: Workspace settings, then Members
- Why it is manual: Attio has no API for workspace roles or object and field access.
- Done when: a non-admin test member sees and edits what their role needs and nothing more.
