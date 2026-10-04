# Manual steps: Executive search (salesforce)

Generated from `design.yaml`. Do not edit by hand. The metadata deploy cannot do any of this, or the research has not proven it. Setup paths come from general platform knowledge and labels move between releases.
Sources: `platforms/salesforce/reference/` (api-coverage.md, open-questions.md, automation.md).

## Before and during the build

### 1. Check the Salesforce edition

- [ ] Where: Setup, Company Information, Organization Edition
- Why it is manual: The Metadata API deploys only on Enterprise, Unlimited, Performance and Developer Edition. Professional and Essentials cannot deploy this folder: build by hand from build-sheet.md instead (Professional allows about 50 custom objects and 100 custom fields per object; Essentials allows no custom objects). This blueprint needs 4 custom objects (including 1 junction) and up to 13 custom fields on one object. Allowances are secondary-source figures, so confirm them on the Company Information page.
- Done when: the edition is one of the four, or the by-hand fallback is agreed with the client.

### 2. Run a check-only deploy, then deploy

- [ ] Where: Terminal, in this folder
- Why it is manual: Run `sf project deploy start --dry-run --manifest package.xml --target-org <alias> --api-version 67.0 --wait 30`. Read every error. Then run the same command without `--dry-run`. Use a sandbox first. Never pass `--ignore-errors`, `--ignore-conflicts` or `--ignore-warnings`.
- Done when: the dry run passes and the real deploy lists every file as Created or Unchanged.

### 3. Confirm the deploying user's permissions

- [ ] Where: Setup, Users, Profiles or Permission Sets
- Why it is manual: The user needs API Enabled plus Modify Metadata Through Metadata API Functions or Modify All Data.
- Done when: a check-only deploy starts without a permissions error.

## Check on the first deploy (unverified in the research)

### 4. Deploy one field of each type first

- [ ] Where: Terminal
- Why it is manual: Minimal files for Checkbox, Lookup, MasterDetail and LongTextArea, and the precision and scale limits, are taken from real files but not proven for API 67.0 (research E1). A required Lookup is never emitted.
- Done when: the dry run accepts every field type this blueprint uses.

### 5. Check record type picklist values

- [ ] Where: Setup, Object Manager, the object, Record Types
- Why it is manual: Each record type lists every value of every picklist. Whether omitting a picklist hides its values is unconfirmed (research E4).
- Done when: each record type shows the full list of values for each picklist.

### 6. Check picklist values that contain a comma

- [ ] Where: Setup, Object Manager, the object, Record Types
- Why it is manual: Salesforce may URL-encode a comma inside a record type's picklist value. Values affected: Opportunity.Fee_structure__c: Half on engagement, half on placement; Opportunity.Fee_structure__c: Thirds on engagement, shortlist and placement. Retrieve a record type once and copy the encoding it uses if the deploy rejects these.
- Done when: the values deploy and appear on the record type.

### 7. Check the sales process minimum

- [ ] Where: Setup, Feature Settings, Sales, Sales Processes
- Why it is manual: Each sales process has one open, one won and one lost stage, but the minimum is not stated in the guide (research E9).
- Done when: every sales process saves and shows its stages.

### 8. Check the paths

- [ ] Where: Setup, User Interface, Path Settings
- Why it is manual: A path names its record type. Path preference is on by default only in Enterprise Edition. The `recordTypeName` form is unverified for objects with no record type (research E11).
- Done when: each path shows its stages with the guidance text, for a user of that record type.

### 9. Check the junction objects' sharing

- [ ] Where: Setup, Object Manager, each junction object
- Why it is manual: A junction object is the detail of two master-detail fields, so its sharing is set to Controlled By Parent. The guide lists the value but not the rule (research E7).
- Done when: the junction deploys and its records show on both parent records.

### 10. Check the list views

- [ ] Where: Setup, Object Manager, the object, List Views, or the list controls
- Why it is manual: The share target (`allInternalUsers`), the stage filter token `OPPORTUNITY.STAGE_NAME`, blank tests (`equals` with an empty value) and date literals (`TODAY`, `NEXT_N_DAYS:n`) are unverified (research E12). Retrieve a hand-made view to compare.
- Done when: each generated view is visible to internal users and filters as designed.

### 11. Check the permission set

- [ ] Where: Setup, Users, Permission Sets
- Why it is manual: The set grants object access with the field access because a field permission may need object read in the same file (research E16). Required fields and master-detail fields are left out; they follow the object.
- Done when: a test user with the set sees and edits every custom field that is not required.

### 12. Check the data classification elements

- [ ] Where: Setup, Object Manager, the field, Edit
- Why it is manual: Fields flagged as data protection carry `complianceGroup` PII;GDPR and a `securityClassification`. These are labels, not encryption. Shield Platform Encryption is a separate paid feature. Confirm API 67.0 accepts them.
- Done when: the flagged fields deploy and show the compliance categorisation.

## Pipelines and stages

### 13. Deactivate the unused default stages

- [ ] Where: Setup, Object Manager, Opportunity, Fields & Relationships, Stage
- Why it is manual: A deploy only adds stage values. Salesforce's default stages stay in the master list (research E10). The sales processes hide them from users, so this is optional tidying. A stage whose label matches a default (for example Closed won and Closed Won) may update that value instead of adding one.
- Done when: only the stages in this design are active, or the client has agreed to leave the defaults.

### 14. Finish the Search delivery pipeline on Search

- [ ] Where: Setup, Object Manager, Search
- Why it is manual: Search has no native stage machinery. The generator wrote the restricted picklist `Stage__c` and the stage gates. It cannot express won and lost as flags, probability (Position specification 100%, Market mapping 100%, Longlist 100%, Shortlist 100%, Client interviews 100%, Offer and references 100%, Placed 100%, Closed without placement 0%) or forecast categories. Report on the stage values instead, or add a Percent field and a flow to set it. No path is generated for this object: create one under Setup, User Interface, Path Settings, after adding a record type.
- Done when: reports group by stage and the client has said how won, lost and probability are read.

### 15. Finish the Candidate progress pipeline on Search candidate

- [ ] Where: Setup, Object Manager, Search candidate
- Why it is manual: Search candidate has no native stage machinery. The generator wrote the restricted picklist `Stage__c` and the stage gates. It cannot express won and lost as flags, probability (Identified 5%, Approached 15%, Engaged 30%, Assessed 45%, Shortlisted 60%, Client interview 75%, Offer 90%, Placed 100%, Out 0%) or forecast categories. Report on the stage values instead, or add a Percent field and a flow to set it. No path is generated for this object: create one under Setup, User Interface, Path Settings, after adding a record type.
- Done when: reports group by stage and the client has said how won, lost and probability are read.

### 16. Finish the Fee collection pipeline on Fee instalment

- [ ] Where: Setup, Object Manager, Fee instalment
- Why it is manual: Fee instalment has no native stage machinery. The generator wrote the restricted picklist `Stage__c` and the stage gates. It cannot express won and lost as flags, probability (Scheduled 80%, Due 90%, Invoiced 95%, Paid 100%, Waived 0%) or forecast categories. Report on the stage values instead, or add a Percent field and a flow to set it. No path is generated for this object: create one under Setup, User Interface, Path Settings, after adding a record type.
- Done when: reports group by stage and the client has said how won, lost and probability are read.

### 17. Check that every Opportunity user has a record type

- [ ] Where: Setup, Users, Permission Sets
- Why it is manual: A record type binds a user to a sales process. The permission set makes each record type visible; users without it fall back to their profile's default record type.
- Done when: a test user creates a deal in each pipeline and sees only that pipeline's stages.

## Stage gates

### 18. Decide how imports pass the stage gates

- [ ] Where: Setup, Custom Code, Custom Permissions
- Why it is manual: Validation rules also fire on API and bulk writes. A data import of records past a gated stage fails unless the gate has an escape hatch (for example a bypass checkbox or custom permission). Not designed here.
- Done when: the import plan names how gated records are loaded.

## Fields, relationships and objects

### 19. Add Search to a tab and an app

- [ ] Where: Setup, User Interface, Tabs; Setup, Apps, App Manager
- Why it is manual: A custom object is not in the navigation until it has a tab in an app. The minimal tab file is unproven, so it is not generated (research E6).
- Done when: users find Searches from the app's navigation.

### 20. Add Search candidate to a tab and an app

- [ ] Where: Setup, User Interface, Tabs; Setup, Apps, App Manager
- Why it is manual: A custom object is not in the navigation until it has a tab in an app. The minimal tab file is unproven, so it is not generated (research E6).
- Done when: users find Search candidates from the app's navigation.

### 21. Add Fee instalment to a tab and an app

- [ ] Where: Setup, User Interface, Tabs; Setup, Apps, App Manager
- Why it is manual: A custom object is not in the navigation until it has a tab in an app. The minimal tab file is unproven, so it is not generated (research E6).
- Done when: users find Fee instalments from the app's navigation.

### 22. Put the new fields on the Account page layout

- [ ] Where: Setup, Object Manager, Account, Page Layouts
- Why it is manual: A deploy creates fields but does not place them on a layout, and a deployed layout would replace the whole one (research E5). The permission set grants access; the layout decides what users see.
- Done when: the Account layout shows every field from this blueprint in a sensible section.

### 23. Put the new fields on the Opportunity page layout

- [ ] Where: Setup, Object Manager, Opportunity, Page Layouts
- Why it is manual: A deploy creates fields but does not place them on a layout, and a deployed layout would replace the whole one (research E5). The permission set grants access; the layout decides what users see.
- Done when: the Opportunity layout shows every field from this blueprint in a sensible section.

### 24. Put the new fields on the Fee instalment page layout

- [ ] Where: Setup, Object Manager, Fee instalment, Page Layouts
- Why it is manual: A deploy creates fields but does not place them on a layout, and a deployed layout would replace the whole one (research E5). The permission set grants access; the layout decides what users see.
- Done when: the Fee instalment layout shows every field from this blueprint in a sensible section.

### 25. Put the new fields on the Contact page layout

- [ ] Where: Setup, Object Manager, Contact, Page Layouts
- Why it is manual: A deploy creates fields but does not place them on a layout, and a deployed layout would replace the whole one (research E5). The permission set grants access; the layout decides what users see.
- Done when: the Contact layout shows every field from this blueprint in a sensible section.

### 26. Put the new fields on the Search page layout

- [ ] Where: Setup, Object Manager, Search, Page Layouts
- Why it is manual: A deploy creates fields but does not place them on a layout, and a deployed layout would replace the whole one (research E5). The permission set grants access; the layout decides what users see.
- Done when: the Search layout shows every field from this blueprint in a sensible section.

### 27. Put the new fields on the Search candidate page layout

- [ ] Where: Setup, Object Manager, Search candidate, Page Layouts
- Why it is manual: A deploy creates fields but does not place them on a layout, and a deployed layout would replace the whole one (research E5). The permission set grants access; the layout decides what users see.
- Done when: the Search candidate layout shows every field from this blueprint in a sensible section.

### 28. Decide master-detail or lookup for the many-to-many links

- [ ] Where: Setup, Object Manager, each junction object
- Why it is manual: Many-to-many links are junction objects with two master-detail fields. Changing a master-detail field later deletes child records, so settle this before any data is loaded.
- Done when: the client has agreed the junction design.

### 29. Map lead fields if the client uses Leads

- [ ] Where: Setup, Object Manager, Lead, Fields & Relationships, Map Lead Fields
- Why it is manual: Only custom fields can be mapped, and the metadata path for the mapping file is unverified (research E14). Map any custom Lead field to its Account, Contact or Opportunity field from this blueprint. Standard mappings are fixed.
- Done when: a test lead converts and the custom values carry over, or the client does not use Leads.

## Flows

### 30. Create search on mandate won

- [ ] Where: Setup, Process Automation, Flows, New Flow, Record-Triggered Flow
- Why it is manual: Flows are not generated: a wrong flow runs on every save and cannot be removed from source. Trigger: A deal in the mandate acquisition pipeline moves to mandate won. Action: Create a search from the deal's role title, compensation and fee terms, link it to the deal and company, set it to position specification, and set the company's client status to active client. In production, a flow deploys inactive unless Setup, Process Automation, Process Automation Settings has 'Deploy processes and flows as active' on.
- Done when: the flow runs once on a test record and does nothing else.

### 31. Create fee schedule

- [ ] Where: Setup, Process Automation, Flows, New Flow, Record-Triggered Flow
- Why it is manual: Flows are not generated: a wrong flow runs on every save and cannot be removed from source. Trigger: A search is created with a total fee and a fee structure on its deal. Action: Create the fee instalments in the fee collection pipeline at scheduled, with trigger and amount from the fee structure. In production, a flow deploys inactive unless Setup, Process Automation, Process Automation Settings has 'Deploy processes and flows as active' on.
- Done when: the flow runs once on a test record and does nothing else.

### 32. Make instalments due

- [ ] Where: Setup, Process Automation, Flows, New Flow, Record-Triggered Flow
- Why it is manual: Flows are not generated: a wrong flow runs on every save and cannot be removed from source. Trigger: A search reaches the shortlist stage or placed, or an instalment's set date arrives. Action: Move the matching instalment to due, set its due date and notify finance. In production, a flow deploys inactive unless Setup, Process Automation, Process Automation Settings has 'Deploy processes and flows as active' on.
- Done when: the flow runs once on a test record and does nothing else.

### 33. Set off-limits on signing

- [ ] Where: Setup, Process Automation, Flows, New Flow, Record-Triggered Flow
- Why it is manual: Flows are not generated: a wrong flow runs on every save and cannot be removed from source. Trigger: A deal moves to mandate won. Action: Set the company's off-limits until date from the agreement and flag its people as off-limits for approaches. In production, a flow deploys inactive unless Setup, Process Automation, Process Automation Settings has 'Deploy processes and flows as active' on.
- Done when: the flow runs once on a test record and does nothing else.

### 34. Shortlist timetable alert

- [ ] Where: Setup, Process Automation, Flows, New Flow, Record-Triggered Flow
- Why it is manual: Flows are not generated: a wrong flow runs on every save and cannot be removed from source. Trigger: A search is not yet at shortlist and its target shortlist date is 7 days away. Action: Notify the partner and consultant with the number of assessed candidates. In production, a flow deploys inactive unless Setup, Process Automation, Process Automation Settings has 'Deploy processes and flows as active' on.
- Done when: the flow runs once on a test record and does nothing else.

### 35. Close other candidates

- [ ] Where: Setup, Process Automation, Flows, New Flow, Record-Triggered Flow
- Why it is manual: Flows are not generated: a wrong flow runs on every save and cannot be removed from source. Trigger: A search candidate moves to placed. Action: Move every other open search candidate on the search to out with a reason of client did not proceed, set the search to placed, and prompt the consultant to send candidate courtesy notes. In production, a flow deploys inactive unless Setup, Process Automation, Process Automation Settings has 'Deploy processes and flows as active' on.
- Done when: the flow runs once on a test record and does nothing else.

### 36. Review candidate data

- [ ] Where: Setup, Process Automation, Flows, New Flow, Record-Triggered Flow
- Why it is manual: Flows are not generated: a wrong flow runs on every save and cannot be removed from source. Trigger: A person of type candidate has a data review date in 30 days. Action: Notify the owner to confirm consent or delete the record. In production, a flow deploys inactive unless Setup, Process Automation, Process Automation Settings has 'Deploy processes and flows as active' on.
- Done when: the flow runs once on a test record and does nothing else.

## List views

### 37. Set the sort on Active searches

- [ ] Where: Searches, the list view `Active_searches`, List View Controls
- Why it is manual: List views have no sort in the metadata. Sort: Target shortlist date, soonest first.
- Done when: the saved view sorts as stated.

### 38. Build the view Longlist

- [ ] Where: Search candidates, List View Controls, New
- Why it is manual: The filter is not a plain comparison on a custom field, the stage or the owner, so it is not generated. Filter: Search is the chosen search and stage is identified, approached or engaged. Sort: Motivation, strongest first.
- Done when: the saved view shows the expected records in the stated order.

### 39. Build the view Shortlist

- [ ] Where: Search candidates, List View Controls, New
- Why it is manual: The filter is not a plain comparison on a custom field, the stage or the owner, so it is not generated. Filter: Search is the chosen search and stage is shortlisted, client interview or offer. Sort: Assessment rating, strongest first.
- Done when: the saved view shows the expected records in the stated order.

### 40. Set the sort on Instalments to invoice

- [ ] Where: Fee instalments, the list view `Instalments_to_invoice`, List View Controls
- Why it is manual: List views have no sort in the metadata. Sort: Due date, oldest first.
- Done when: the saved view sorts as stated.

### 41. Set the sort on Outstanding fees

- [ ] Where: Fee instalments, the list view `Outstanding_fees`, List View Controls
- Why it is manual: List views have no sort in the metadata. Sort: Due date, oldest first.
- Done when: the saved view sorts as stated.

### 42. Set the sort on My open mandate deals

- [ ] Where: Deals, the list view `My_open_mandate_deals`, List View Controls
- Why it is manual: List views have no sort in the metadata. Sort: Close date, soonest first.
- Done when: the saved view sorts as stated.

### 43. Set the sort on Stalled deals

- [ ] Where: Deals, the list view `Stalled_deals`, List View Controls
- Why it is manual: List views have no sort in the metadata. Sort: Next step date, oldest first.
- Done when: the saved view sorts as stated.

## Permissions and access

### 44. Assign the permission set Executive_search_user

- [ ] Where: Setup, Users, Permission Sets, Manage Assignments
- Why it is manual: Assigning a permission set is a data operation, not metadata. A new field is invisible until a profile or permission set grants it. Never ship profiles from here: a profile deploy overwrites far more.
- Done when: a non-admin test user sees and edits the blueprint's fields.

### 45. Set sharing for the standard objects

- [ ] Where: Setup, Security, Sharing Settings
- Why it is manual: Sharing for custom objects is set in the object files (public read and write). Standard objects need the org-wide defaults chosen by the client.
- Done when: the client has signed off the org-wide defaults.
