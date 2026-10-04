# Manual steps: Executive search (hubspot)

Generated from `design.yaml`. Do not edit by hand. The HubSpot API cannot do any of this.
Sources: https://developers.hubspot.com/docs/api-reference/latest/crm/pipelines/guide.md, https://knowledge.hubspot.com/records/create-and-manage-saved-views, https://knowledge.hubspot.com/workflows/create-workflows, `platforms/hubspot/reference/api-coverage.md`.

## Before and during the build

### 1. Create a service key and test in a developer test account first

- [ ] Where: Development > Keys > Service keys > Create service key (scopes in platforms/hubspot/reference/auth-and-setup.md)
- Why it is manual: Keys are made in the account by a super admin. A developer test account carries a 90-day Enterprise trial, so it can test custom objects before the client account is touched.
- Done when: `GET /crm/properties/2026-09/contacts` returns 200 with the key.

### 2. Confirm the account is Enterprise before creating custom objects

- [ ] Where: Settings > Account Management > Account defaults, and GET /crm/limits/2026-09/custom-object-types
- Why it is manual: Custom objects need Enterprise and there is no workaround on a lower tier. A client is typically limited to 10 definitions (OQ-3); this blueprint creates 3.
- Done when: the tier is written in the client notes and the limits call allows 3 custom object(s) (Search, Search candidate, Fee instalment).

## Required fields on standard objects

### 3. Make Company Name required

- [ ] Where: Settings > Data Management > Objects > Companies > Properties tab > Name, or a workflow that flags it when empty
- Why it is manual: HubSpot has no API setting for required properties on standard objects (OQ-9).
- Done when: a company record cannot be saved, or is flagged, when Name is empty.

### 4. Make Person Last name required

- [ ] Where: Settings > Data Management > Objects > Contacts > Properties tab > Last name, or a workflow that flags it when empty
- Why it is manual: HubSpot has no API setting for required properties on standard objects (OQ-9).
- Done when: a person record cannot be saved, or is flagged, when Last name is empty.

### 5. Make Deal Name required

- [ ] Where: Settings > Data Management > Objects > Deals > Properties tab > Name, or a workflow that flags it when empty
- Why it is manual: HubSpot has no API setting for required properties on standard objects (OQ-9).
- Done when: a deal record cannot be saved, or is flagged, when Name is empty.

## Pipelines

### 6. Check closed stages of Search delivery

- [ ] Where: Settings > Data Management > Objects > Searches > Pipelines tab > Search delivery
- Why it is manual: HubSpot has open or closed on custom object stages, not won or lost, and no probability (the design's probabilities are not sent). The API key for closed is unconfirmed (OQ-1).
- Done when: closed stages (Placed, Closed without placement) show as Closed. Set them by hand if the read-back says otherwise.

### 7. Check closed stages of Candidate progress

- [ ] Where: Settings > Data Management > Objects > Search candidates > Pipelines tab > Candidate progress
- Why it is manual: HubSpot has open or closed on custom object stages, not won or lost, and no probability (the design's probabilities are not sent). The API key for closed is unconfirmed (OQ-1).
- Done when: closed stages (Placed, Out) show as Closed. Set them by hand if the read-back says otherwise.

### 8. Check closed stages of Fee collection

- [ ] Where: Settings > Data Management > Objects > Fee instalments > Pipelines tab > Fee collection
- Why it is manual: HubSpot has open or closed on custom object stages, not won or lost, and no probability (the design's probabilities are not sent). The API key for closed is unconfirmed (OQ-1).
- Done when: closed stages (Paid, Waived) show as Closed. Set them by hand if the read-back says otherwise.

## Stage gates and lost reasons

### 9. Require Next step date to enter Target (Mandate acquisition)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Mandate acquisition > stage row for Target > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Target asks for Next step date.

### 10. Require Role title, Next step date to enter Introduction (Mandate acquisition)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Mandate acquisition > stage row for Introduction > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Introduction asks for Role title, Next step date.

### 11. Require Role title, Expected total compensation, Competing firms to enter Brief (Mandate acquisition)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Mandate acquisition > stage row for Brief > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Brief asks for Role title, Expected total compensation, Competing firms.

### 12. Require Fee percent, Fee structure, Amount to enter Proposal sent (Mandate acquisition)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Mandate acquisition > stage row for Proposal sent > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Proposal sent asks for Fee percent, Fee structure, Amount.

### 13. Require Competing firms, Close date to enter Pitch or finalist (Mandate acquisition)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Mandate acquisition > stage row for Pitch or finalist > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Pitch or finalist asks for Competing firms, Close date.

### 14. Require Fee percent, Fee structure, Exclusivity confirmed, Close date to enter Terms agreed (Mandate acquisition)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Mandate acquisition > stage row for Terms agreed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Terms agreed asks for Fee percent, Fee structure, Exclusivity confirmed, Close date.

### 15. Require Amount, Close date, Fee structure to enter Mandate won (Mandate acquisition)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Mandate acquisition > stage row for Mandate won > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Mandate won asks for Amount, Close date, Fee structure.

### 16. Require Lost reason to enter Mandate lost (Mandate acquisition)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Mandate acquisition > stage row for Mandate lost > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Mandate lost asks for Lost reason.

### 17. Require Partner, Consultant to enter Position specification (Search delivery)

- [ ] Where: Settings > Data Management > Objects > Searches > Pipelines tab > Search delivery > stage row for Position specification > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test search into Position specification asks for Partner, Consultant.

### 18. Require Engaged date, Target shortlist date to enter Market mapping (Search delivery)

- [ ] Where: Settings > Data Management > Objects > Searches > Pipelines tab > Search delivery > stage row for Market mapping > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test search into Market mapping asks for Engaged date, Target shortlist date.

### 19. Require Longlist size to enter Longlist (Search delivery)

- [ ] Where: Settings > Data Management > Objects > Searches > Pipelines tab > Search delivery > stage row for Longlist > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test search into Longlist asks for Longlist size.

### 20. Require Target placement date to enter Shortlist (Search delivery)

- [ ] Where: Settings > Data Management > Objects > Searches > Pipelines tab > Search delivery > stage row for Shortlist > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test search into Shortlist asks for Target placement date.

### 21. Require Target placement date to enter Client interviews (Search delivery)

- [ ] Where: Settings > Data Management > Objects > Searches > Pipelines tab > Search delivery > stage row for Client interviews > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test search into Client interviews asks for Target placement date.

### 22. Require Total fee to enter Offer and references (Search delivery)

- [ ] Where: Settings > Data Management > Objects > Searches > Pipelines tab > Search delivery > stage row for Offer and references > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test search into Offer and references asks for Total fee.

### 23. Require Total fee to enter Placed (Search delivery)

- [ ] Where: Settings > Data Management > Objects > Searches > Pipelines tab > Search delivery > stage row for Placed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test search into Placed asks for Total fee.

### 24. Require Close reason to enter Closed without placement (Search delivery)

- [ ] Where: Settings > Data Management > Objects > Searches > Pipelines tab > Search delivery > stage row for Closed without placement > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test search into Closed without placement asks for Close reason.

### 25. Require Source to enter Identified (Candidate progress)

- [ ] Where: Settings > Data Management > Objects > Search candidates > Pipelines tab > Candidate progress > stage row for Identified > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test search_candidate into Identified asks for Source.

### 26. Require Outreach date to enter Approached (Candidate progress)

- [ ] Where: Settings > Data Management > Objects > Search candidates > Pipelines tab > Candidate progress > stage row for Approached > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test search_candidate into Approached asks for Outreach date.

### 27. Require Motivation to enter Engaged (Candidate progress)

- [ ] Where: Settings > Data Management > Objects > Search candidates > Pipelines tab > Candidate progress > stage row for Engaged > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test search_candidate into Engaged asks for Motivation.

### 28. Require Interview date, Assessment rating to enter Assessed (Candidate progress)

- [ ] Where: Settings > Data Management > Objects > Search candidates > Pipelines tab > Candidate progress > stage row for Assessed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test search_candidate into Assessed asks for Interview date, Assessment rating.

### 29. Require Assessment rating, Client feedback to enter Shortlisted (Candidate progress)

- [ ] Where: Settings > Data Management > Objects > Search candidates > Pipelines tab > Candidate progress > stage row for Shortlisted > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test search_candidate into Shortlisted asks for Assessment rating, Client feedback.

### 30. Require Client interview date to enter Client interview (Candidate progress)

- [ ] Where: Settings > Data Management > Objects > Search candidates > Pipelines tab > Candidate progress > stage row for Client interview > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test search_candidate into Client interview asks for Client interview date.

### 31. Require Offered compensation to enter Offer (Candidate progress)

- [ ] Where: Settings > Data Management > Objects > Search candidates > Pipelines tab > Candidate progress > stage row for Offer > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test search_candidate into Offer asks for Offered compensation.

### 32. Require Offered compensation, Start date, References complete to enter Placed (Candidate progress)

- [ ] Where: Settings > Data Management > Objects > Search candidates > Pipelines tab > Candidate progress > stage row for Placed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test search_candidate into Placed asks for Offered compensation, Start date, References complete.

### 33. Require Out reason to enter Out (Candidate progress)

- [ ] Where: Settings > Data Management > Objects > Search candidates > Pipelines tab > Candidate progress > stage row for Out > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test search_candidate into Out asks for Out reason.

### 34. Require Amount, Trigger to enter Scheduled (Fee collection)

- [ ] Where: Settings > Data Management > Objects > Fee instalments > Pipelines tab > Fee collection > stage row for Scheduled > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test fee_instalment into Scheduled asks for Amount, Trigger.

### 35. Require Due date to enter Due (Fee collection)

- [ ] Where: Settings > Data Management > Objects > Fee instalments > Pipelines tab > Fee collection > stage row for Due > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test fee_instalment into Due asks for Due date.

### 36. Require Invoice reference to enter Invoiced (Fee collection)

- [ ] Where: Settings > Data Management > Objects > Fee instalments > Pipelines tab > Fee collection > stage row for Invoiced > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test fee_instalment into Invoiced asks for Invoice reference.

### 37. Require Invoice reference to enter Paid (Fee collection)

- [ ] Where: Settings > Data Management > Objects > Fee instalments > Pipelines tab > Fee collection > stage row for Paid > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test fee_instalment into Paid asks for Invoice reference.

### 38. Require Waiver reason to enter Waived (Fee collection)

- [ ] Where: Settings > Data Management > Objects > Fee instalments > Pipelines tab > Fee collection > stage row for Waived > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test fee_instalment into Waived asks for Waiver reason.

## Decisions where the HubSpot mapping is lossy

### 39. Check the association limit for search_company

- [ ] Where: Settings > Data Management > Objects > Searches > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 40. Check the association limit for search_deal

- [ ] Where: Settings > Data Management > Objects > Searches > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 41. Check the association limit for search_candidate_search

- [ ] Where: Settings > Data Management > Objects > Search candidates > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 42. Check the association limit for search_candidate_person

- [ ] Where: Settings > Data Management > Objects > Search candidates > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 43. Check the association limit for fee_instalment_search

- [ ] Where: Settings > Data Management > Objects > Fee instalments > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 44. Accept that currency fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property carries no currency code: the symbol is a display choice.
- Done when: the client has agreed in the client notes. Fields: person.current_total_compensation, deal.expected_total_compensation, search.expected_total_compensation, search.total_fee, search_candidate.offered_compensation, fee_instalment.amount.

### 45. Accept that percent fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property the stored value (0.2 or 20) is unconfirmed (open question OQ-5).
- Done when: the client has agreed in the client notes. Fields: deal.fee_percent.

### 46. Accept that user fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property holds the HubSpot owner ID, so only users of the account can be chosen.
- Done when: the client has agreed in the client notes. Fields: search.partner, search.consultant.

## Workflows

### 47. Workflow: Create search on mandate won

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A deal in the mandate acquisition pipeline moves to mandate won.'; action 'Create a search from the deal's role title, compensation and fee terms, link it to the deal and company, set it to position specification, and set the company's client status to active client.'

### 48. Workflow: Create fee schedule

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A search is created with a total fee and a fee structure on its deal.'; action 'Create the fee instalments in the fee collection pipeline at scheduled, with trigger and amount from the fee structure.'

### 49. Workflow: Make instalments due

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A search reaches the shortlist stage or placed, or an instalment's set date arrives.'; action 'Move the matching instalment to due, set its due date and notify finance.'

### 50. Workflow: Set off-limits on signing

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A deal moves to mandate won.'; action 'Set the company's off-limits until date from the agreement and flag its people as off-limits for approaches.'

### 51. Workflow: Shortlist timetable alert

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A search is not yet at shortlist and its target shortlist date is 7 days away.'; action 'Notify the partner and consultant with the number of assessed candidates.'

### 52. Workflow: Close other candidates

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A search candidate moves to placed.'; action 'Move every other open search candidate on the search to out with a reason of client did not proceed, set the search to placed, and prompt the consultant to send candidate courtesy notes.'

### 53. Workflow: Review candidate data

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A person of type candidate has a data review date in 30 days.'; action 'Notify the owner to confirm consent or delete the record.'

## Saved views

### 54. Saved view: Active searches

- [ ] Where: CRM > Searches > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Active searches shows on the Searches index with filter 'Stage is open.' and sort 'Target shortlist date, soonest first.'.

### 55. Saved view: Longlist

- [ ] Where: CRM > Search candidates > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Longlist shows on the Search candidates index with filter 'Search is the chosen search and stage is identified, approached or engaged.' and sort 'Motivation, strongest first.'.

### 56. Saved view: Shortlist

- [ ] Where: CRM > Search candidates > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Shortlist shows on the Search candidates index with filter 'Search is the chosen search and stage is shortlisted, client interview or offer.' and sort 'Assessment rating, strongest first.'.

### 57. Saved view: Instalments to invoice

- [ ] Where: CRM > Fee instalments > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Instalments to invoice shows on the Fee instalments index with filter 'Stage is due.' and sort 'Due date, oldest first.'.

### 58. Saved view: Outstanding fees

- [ ] Where: CRM > Fee instalments > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Outstanding fees shows on the Fee instalments index with filter 'Stage is invoiced.' and sort 'Due date, oldest first.'.

### 59. Saved view: My open mandate deals

- [ ] Where: CRM > Deals > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view My open mandate deals shows on the Deals index with filter 'Owner is me and stage is open.' and sort 'Close date, soonest first.'.

### 60. Saved view: Stalled deals

- [ ] Where: CRM > Deals > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Stalled deals shows on the Deals index with filter 'Stage is open and next step date is empty or in the past.' and sort 'Next step date, oldest first.'.

## Permissions

### 61. Set roles and access

- [ ] Where: Settings > Users & Teams (menu name not verified against a page in the research)
- Why it is manual: No permission-set API was found. Only pipeline stage edit permissions have one, and this blueprint does not use it.
- Done when: a non-admin test user sees and edits what their role needs and nothing more.
