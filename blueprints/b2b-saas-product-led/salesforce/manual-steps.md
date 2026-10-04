# Manual steps: B2B SaaS, product-led (salesforce)

Generated from `design.yaml`. Do not edit by hand. The metadata deploy cannot do any of this, or the research has not proven it. Setup paths come from general platform knowledge and labels move between releases.
Sources: `platforms/salesforce/reference/` (api-coverage.md, open-questions.md, automation.md).

## Before and during the build

### 1. Check the Salesforce edition

- [ ] Where: Setup, Company Information, Organization Edition
- Why it is manual: The Metadata API deploys only on Enterprise, Unlimited, Performance and Developer Edition. Professional and Essentials cannot deploy this folder: build by hand from build-sheet.md instead (Professional allows about 50 custom objects and 100 custom fields per object; Essentials allows no custom objects). This blueprint needs 3 custom objects (including 1 junction) and up to 15 custom fields on one object. Allowances are secondary-source figures, so confirm them on the Company Information page.
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

### 6. Check the sales process minimum

- [ ] Where: Setup, Feature Settings, Sales, Sales Processes
- Why it is manual: Each sales process has one open, one won and one lost stage, but the minimum is not stated in the guide (research E9).
- Done when: every sales process saves and shows its stages.

### 7. Check the paths

- [ ] Where: Setup, User Interface, Path Settings
- Why it is manual: A path names its record type. Path preference is on by default only in Enterprise Edition. The `recordTypeName` form is unverified for objects with no record type (research E11).
- Done when: each path shows its stages with the guidance text, for a user of that record type.

### 8. Check the junction objects' sharing

- [ ] Where: Setup, Object Manager, each junction object
- Why it is manual: A junction object is the detail of two master-detail fields, so its sharing is set to Controlled By Parent. The guide lists the value but not the rule (research E7).
- Done when: the junction deploys and its records show on both parent records.

### 9. Check the list views

- [ ] Where: Setup, Object Manager, the object, List Views, or the list controls
- Why it is manual: The share target (`allInternalUsers`), the stage filter token `OPPORTUNITY.STAGE_NAME`, blank tests (`equals` with an empty value) and date literals (`TODAY`, `NEXT_N_DAYS:n`) are unverified (research E12). Retrieve a hand-made view to compare.
- Done when: each generated view is visible to internal users and filters as designed.

### 10. Check the permission set

- [ ] Where: Setup, Users, Permission Sets
- Why it is manual: The set grants object access with the field access because a field permission may need object read in the same file (research E16). Required fields and master-detail fields are left out; they follow the object.
- Done when: a test user with the set sees and edits every custom field that is not required.

## Pipelines and stages

### 11. Deactivate the unused default stages

- [ ] Where: Setup, Object Manager, Opportunity, Fields & Relationships, Stage
- Why it is manual: A deploy only adds stage values. Salesforce's default stages stay in the master list (research E10). The sales processes hide them from users, so this is optional tidying. A stage whose label matches a default (for example Closed won and Closed Won) may update that value instead of adding one.
- Done when: only the stages in this design are active, or the client has agreed to leave the defaults.

### 12. Check that every Opportunity user has a record type

- [ ] Where: Setup, Users, Permission Sets
- Why it is manual: A record type binds a user to a sales process. The permission set makes each record type visible; users without it fall back to their profile's default record type.
- Done when: a test user creates a deal in each pipeline and sees only that pipeline's stages.

## Stage gates

### 13. Decide how imports pass the stage gates

- [ ] Where: Setup, Custom Code, Custom Permissions
- Why it is manual: Validation rules also fire on API and bulk writes. A data import of records past a gated stage fails unless the gate has an escape hatch (for example a bypass checkbox or custom permission). Not designed here.
- Done when: the import plan names how gated records are loaded.

## Fields, relationships and objects

### 14. Add Workspace to a tab and an app

- [ ] Where: Setup, User Interface, Tabs; Setup, Apps, App Manager
- Why it is manual: A custom object is not in the navigation until it has a tab in an app. The minimal tab file is unproven, so it is not generated (research E6).
- Done when: users find Workspaces from the app's navigation.

### 15. Add Adoption plan to a tab and an app

- [ ] Where: Setup, User Interface, Tabs; Setup, Apps, App Manager
- Why it is manual: A custom object is not in the navigation until it has a tab in an app. The minimal tab file is unproven, so it is not generated (research E6).
- Done when: users find Adoption plans from the app's navigation.

### 16. Put the new fields on the Adoption plan page layout

- [ ] Where: Setup, Object Manager, Adoption plan, Page Layouts
- Why it is manual: A deploy creates fields but does not place them on a layout, and a deployed layout would replace the whole one (research E5). The permission set grants access; the layout decides what users see.
- Done when: the Adoption plan layout shows every field from this blueprint in a sensible section.

### 17. Put the new fields on the Account page layout

- [ ] Where: Setup, Object Manager, Account, Page Layouts
- Why it is manual: A deploy creates fields but does not place them on a layout, and a deployed layout would replace the whole one (research E5). The permission set grants access; the layout decides what users see.
- Done when: the Account layout shows every field from this blueprint in a sensible section.

### 18. Put the new fields on the Opportunity page layout

- [ ] Where: Setup, Object Manager, Opportunity, Page Layouts
- Why it is manual: A deploy creates fields but does not place them on a layout, and a deployed layout would replace the whole one (research E5). The permission set grants access; the layout decides what users see.
- Done when: the Opportunity layout shows every field from this blueprint in a sensible section.

### 19. Put the new fields on the Contact page layout

- [ ] Where: Setup, Object Manager, Contact, Page Layouts
- Why it is manual: A deploy creates fields but does not place them on a layout, and a deployed layout would replace the whole one (research E5). The permission set grants access; the layout decides what users see.
- Done when: the Contact layout shows every field from this blueprint in a sensible section.

### 20. Put the new fields on the Workspace page layout

- [ ] Where: Setup, Object Manager, Workspace, Page Layouts
- Why it is manual: A deploy creates fields but does not place them on a layout, and a deployed layout would replace the whole one (research E5). The permission set grants access; the layout decides what users see.
- Done when: the Workspace layout shows every field from this blueprint in a sensible section.

### 21. Decide master-detail or lookup for the many-to-many links

- [ ] Where: Setup, Object Manager, each junction object
- Why it is manual: Many-to-many links are junction objects with two master-detail fields. Changing a master-detail field later deletes child records, so settle this before any data is loaded.
- Done when: the client has agreed the junction design.

### 22. Map lead fields if the client uses Leads

- [ ] Where: Setup, Object Manager, Lead, Fields & Relationships, Map Lead Fields
- Why it is manual: Only custom fields can be mapped, and the metadata path for the mapping file is unverified (research E14). Map any custom Lead field to its Account, Contact or Opportunity field from this blueprint. Standard mappings are fixed.
- Done when: a test lead converts and the custom values carry over, or the client does not use Leads.

## Flows

### 23. Sync product usage

- [ ] Where: Setup, Process Automation, Flows, New Flow, Record-Triggered Flow
- Why it is manual: Flows are not generated: a wrong flow runs on every save and cannot be removed from source. Trigger: Nightly, and when a workspace is created or its plan changes in the product. Action: Upsert the workspace by product workspace ID with plan, seats, active users, limit used and last active date, and link the people who are members. In production, a flow deploys inactive unless Setup, Process Automation, Process Automation Settings has 'Deploy processes and flows as active' on.
- Done when: the flow runs once on a test record and does nothing else.

### 24. Flag product-qualified lead

- [ ] Where: Setup, Process Automation, Flows, New Flow, Record-Triggered Flow
- Why it is manual: Flows are not generated: a wrong flow runs on every save and cannot be removed from source. Trigger: A workspace meets the PQL rule and its PQL status is not qualified, accepted or rejected. Action: Set PQL status to qualified, notify the sales-assist queue, and create a deal in the sales assist pipeline at product-qualified lead once a rep accepts, with the PQL trigger filled. In production, a flow deploys inactive unless Setup, Process Automation, Process Automation Settings has 'Deploy processes and flows as active' on.
- Done when: the flow runs once on a test record and does nothing else.

### 25. Open expansion deal

- [ ] Where: Setup, Process Automation, Flows, New Flow, Record-Triggered Flow
- Why it is manual: Flows are not generated: a wrong flow runs on every save and cannot be removed from source. Trigger: Seats used exceed seats paid, or plan limit used passes 80 percent, on a paying workspace with no open expansion deal. Action: Create a deal in the expansion pipeline at expansion signal, linked to the workspace, and assign it to the account owner. In production, a flow deploys inactive unless Setup, Process Automation, Process Automation Settings has 'Deploy processes and flows as active' on.
- Done when: the flow runs once on a test record and does nothing else.

### 26. Start adoption plan

- [ ] Where: Setup, Process Automation, Flows, New Flow, Record-Triggered Flow
- Why it is manual: Flows are not generated: a wrong flow runs on every save and cannot be removed from source. Trigger: A sales-assist deal moves to closed won. Action: Create an adoption plan linked to the workspace, assign it to customer success and set the company to paying. In production, a flow deploys inactive unless Setup, Process Automation, Process Automation Settings has 'Deploy processes and flows as active' on.
- Done when: the flow runs once on a test record and does nothing else.

### 27. Trial ending alert

- [ ] Where: Setup, Process Automation, Flows, New Flow, Record-Triggered Flow
- Why it is manual: Flows are not generated: a wrong flow runs on every save and cannot be removed from source. Trigger: A workspace on a trial has a trial end date in 3 days and is activated. Action: Notify the account owner, or the sales-assist queue if the workspace has no owner. In production, a flow deploys inactive unless Setup, Process Automation, Process Automation Settings has 'Deploy processes and flows as active' on.
- Done when: the flow runs once on a test record and does nothing else.

### 28. Flag stalled deals

- [ ] Where: Setup, Process Automation, Flows, New Flow, Record-Triggered Flow
- Why it is manual: Flows are not generated: a wrong flow runs on every save and cannot be removed from source. Trigger: An open deal has no next step date, or the date is more than 7 days past. Action: Notify the deal owner and add the deal to the stalled deals view. In production, a flow deploys inactive unless Setup, Process Automation, Process Automation Settings has 'Deploy processes and flows as active' on.
- Done when: the flow runs once on a test record and does nothing else.

## List views

### 29. Set the sort on PQL queue

- [ ] Where: Workspaces, the list view `Pql_queue`, List View Controls
- Why it is manual: List views have no sort in the metadata. Sort: PQL score, highest first.
- Done when: the saved view sorts as stated.

### 30. Set the sort on Trials ending soon

- [ ] Where: Workspaces, the list view `Trials_ending`, List View Controls
- Why it is manual: List views have no sort in the metadata. Sort: Trial end date, soonest first.
- Done when: the saved view sorts as stated.

### 31. Build the view Expansion candidates

- [ ] Where: Workspaces, List View Controls, New
- Why it is manual: The filter is not a plain comparison on a custom field, the stage or the owner, so it is not generated. Filter: Lifecycle stage is paying and plan limit used is over 80 percent, or seats used is above seats paid. Sort: Plan limit used, highest first.
- Done when: the saved view shows the expected records in the stated order.

### 32. Set the sort on My open deals

- [ ] Where: Deals, the list view `My_open_deals`, List View Controls
- Why it is manual: List views have no sort in the metadata. Sort: Close date, soonest first.
- Done when: the saved view sorts as stated.

### 33. Set the sort on Stalled deals

- [ ] Where: Deals, the list view `Stalled_deals`, List View Controls
- Why it is manual: List views have no sort in the metadata. Sort: Next step date, oldest first.
- Done when: the saved view sorts as stated.

### 34. Set the sort on Adoption in flight

- [ ] Where: Adoption plans, the list view `Adoption_in_flight`, List View Controls
- Why it is manual: List views have no sort in the metadata. Sort: Target activation date, oldest first.
- Done when: the saved view sorts as stated.

## Permissions and access

### 35. Assign the permission set B2B_SaaS_product_led_user

- [ ] Where: Setup, Users, Permission Sets, Manage Assignments
- Why it is manual: Assigning a permission set is a data operation, not metadata. A new field is invisible until a profile or permission set grants it. Never ship profiles from here: a profile deploy overwrites far more.
- Done when: a non-admin test user sees and edits the blueprint's fields.

### 36. Set sharing for the standard objects

- [ ] Where: Setup, Security, Sharing Settings
- Why it is manual: Sharing for custom objects is set in the object files (public read and write). Standard objects need the org-wide defaults chosen by the client.
- Done when: the client has signed off the org-wide defaults.
