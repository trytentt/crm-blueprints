# Manual steps: Manufacturing and distribution, B2B (salesforce)

Generated from `design.yaml`. Do not edit by hand. The metadata deploy cannot do any of this, or the research has not proven it. Setup paths come from general platform knowledge and labels move between releases.
Sources: `platforms/salesforce/reference/` (api-coverage.md, open-questions.md, automation.md).

## Before and during the build

### 1. Check the Salesforce edition

- [ ] Where: Setup, Company Information, Organization Edition
- Why it is manual: The Metadata API deploys only on Enterprise, Unlimited, Performance and Developer Edition. Professional and Essentials cannot deploy this folder: build by hand from build-sheet.md instead (Professional allows about 50 custom objects and 100 custom fields per object; Essentials allows no custom objects). This blueprint needs 2 custom objects (including 0 junction) and up to 11 custom fields on one object. Allowances are secondary-source figures, so confirm them on the Company Information page.
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

### 8. Check the list views

- [ ] Where: Setup, Object Manager, the object, List Views, or the list controls
- Why it is manual: The share target (`allInternalUsers`), the stage filter token `OPPORTUNITY.STAGE_NAME`, blank tests (`equals` with an empty value) and date literals (`TODAY`, `NEXT_N_DAYS:n`) are unverified (research E12). Retrieve a hand-made view to compare.
- Done when: each generated view is visible to internal users and filters as designed.

### 9. Check the permission set

- [ ] Where: Setup, Users, Permission Sets
- Why it is manual: The set grants object access with the field access because a field permission may need object read in the same file (research E16). Required fields and master-detail fields are left out; they follow the object.
- Done when: a test user with the set sees and edits every custom field that is not required.

## Pipelines and stages

### 10. Deactivate the unused default stages

- [ ] Where: Setup, Object Manager, Opportunity, Fields & Relationships, Stage
- Why it is manual: A deploy only adds stage values. Salesforce's default stages stay in the master list (research E10). The sales processes hide them from users, so this is optional tidying. A stage whose label matches a default (for example Closed won and Closed Won) may update that value instead of adding one.
- Done when: only the stages in this design are active, or the client has agreed to leave the defaults.

### 11. Finish the RFQ handling pipeline on Quote

- [ ] Where: Setup, Object Manager, Quote
- Why it is manual: Quote has no native stage machinery. The generator wrote the restricted picklist `Stage__c` and the stage gates. It cannot express won and lost as flags, probability (Received 20%, Qualified 30%, Pricing 40%, Approval 45%, Sent 50%, Follow-up 60%, Accepted 100%, Declined 0%) or forecast categories. Report on the stage values instead, or add a Percent field and a flow to set it. No path is generated for this object: create one under Setup, User Interface, Path Settings, after adding a record type.
- Done when: reports group by stage and the client has said how won, lost and probability are read.

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

### 14. Add Quote to a tab and an app

- [ ] Where: Setup, User Interface, Tabs; Setup, Apps, App Manager
- Why it is manual: A custom object is not in the navigation until it has a tab in an app. The minimal tab file is unproven, so it is not generated (research E6).
- Done when: users find Quotes from the app's navigation.

### 15. Add Order to a tab and an app

- [ ] Where: Setup, User Interface, Tabs; Setup, Apps, App Manager
- Why it is manual: A custom object is not in the navigation until it has a tab in an app. The minimal tab file is unproven, so it is not generated (research E6).
- Done when: users find Orders from the app's navigation.

### 16. Put the new fields on the Account page layout

- [ ] Where: Setup, Object Manager, Account, Page Layouts
- Why it is manual: A deploy creates fields but does not place them on a layout, and a deployed layout would replace the whole one (research E5). The permission set grants access; the layout decides what users see.
- Done when: the Account layout shows every field from this blueprint in a sensible section.

### 17. Put the new fields on the Opportunity page layout

- [ ] Where: Setup, Object Manager, Opportunity, Page Layouts
- Why it is manual: A deploy creates fields but does not place them on a layout, and a deployed layout would replace the whole one (research E5). The permission set grants access; the layout decides what users see.
- Done when: the Opportunity layout shows every field from this blueprint in a sensible section.

### 18. Put the new fields on the Order page layout

- [ ] Where: Setup, Object Manager, Order, Page Layouts
- Why it is manual: A deploy creates fields but does not place them on a layout, and a deployed layout would replace the whole one (research E5). The permission set grants access; the layout decides what users see.
- Done when: the Order layout shows every field from this blueprint in a sensible section.

### 19. Put the new fields on the Contact page layout

- [ ] Where: Setup, Object Manager, Contact, Page Layouts
- Why it is manual: A deploy creates fields but does not place them on a layout, and a deployed layout would replace the whole one (research E5). The permission set grants access; the layout decides what users see.
- Done when: the Contact layout shows every field from this blueprint in a sensible section.

### 20. Put the new fields on the Quote page layout

- [ ] Where: Setup, Object Manager, Quote, Page Layouts
- Why it is manual: A deploy creates fields but does not place them on a layout, and a deployed layout would replace the whole one (research E5). The permission set grants access; the layout decides what users see.
- Done when: the Quote layout shows every field from this blueprint in a sensible section.

### 21. Map lead fields if the client uses Leads

- [ ] Where: Setup, Object Manager, Lead, Fields & Relationships, Map Lead Fields
- Why it is manual: Only custom fields can be mapped, and the metadata path for the mapping file is unverified (research E14). Map any custom Lead field to its Account, Contact or Opportunity field from this blueprint. Standard mappings are fixed.
- Done when: a test lead converts and the custom values carry over, or the client does not use Leads.

## Flows

### 22. Update company on order

- [ ] Where: Setup, Process Automation, Flows, New Flow, Record-Triggered Flow
- Why it is manual: Flows are not generated: a wrong flow runs on every save and cannot be removed from source. Trigger: An order is created or its status moves to received. Action: Set the company's last order date and account status to active, and set the order type to first order if the company had no earlier order. In production, a flow deploys inactive unless Setup, Process Automation, Process Automation Settings has 'Deploy processes and flows as active' on.
- Done when: the flow runs once on a test record and does nothing else.

### 23. Flag late quotes

- [ ] Where: Setup, Process Automation, Flows, New Flow, Record-Triggered Flow
- Why it is manual: Flows are not generated: a wrong flow runs on every save and cannot be removed from source. Trigger: A quote is open and its due date is today or in the past. Action: Notify the quote owner and add the quote to the overdue quotes view. In production, a flow deploys inactive unless Setup, Process Automation, Process Automation Settings has 'Deploy processes and flows as active' on.
- Done when: the flow runs once on a test record and does nothing else.

### 24. Chase sent quotes

- [ ] Where: Setup, Process Automation, Flows, New Flow, Record-Triggered Flow
- Why it is manual: Flows are not generated: a wrong flow runs on every save and cannot be removed from source. Trigger: A quote has been in sent for 5 working days. Action: Create a task for the owner to chase the buyer and move the quote to follow-up when done. In production, a flow deploys inactive unless Setup, Process Automation, Process Automation Settings has 'Deploy processes and flows as active' on.
- Done when: the flow runs once on a test record and does nothing else.

### 25. Reorder due

- [ ] Where: Setup, Process Automation, Flows, New Flow, Record-Triggered Flow
- Why it is manual: Flows are not generated: a wrong flow runs on every save and cannot be removed from source. Trigger: Days since the company's last order date exceed its expected reorder interval and the account is active. Action: Create a task for the account owner to call the buyer and set the account status to dormant after 2 intervals. In production, a flow deploys inactive unless Setup, Process Automation, Process Automation Settings has 'Deploy processes and flows as active' on.
- Done when: the flow runs once on a test record and does nothing else.

### 26. Route quote for approval

- [ ] Where: Setup, Process Automation, Flows, New Flow, Record-Triggered Flow
- Why it is manual: Flows are not generated: a wrong flow runs on every save and cannot be removed from source. Trigger: A quote moves to approval. Action: Notify the sales manager, who either approves it or sends it back to pricing. In production, a flow deploys inactive unless Setup, Process Automation, Process Automation Settings has 'Deploy processes and flows as active' on.
- Done when: the flow runs once on a test record and does nothing else.

### 27. Quarterly tier review

- [ ] Where: Setup, Process Automation, Flows, New Flow, Record-Triggered Flow
- Why it is manual: Flows are not generated: a wrong flow runs on every save and cannot be removed from source. Trigger: Each quarter, for every active account. Action: Compare the account's annual spend band with its tier and list mismatches for the sales manager. In production, a flow deploys inactive unless Setup, Process Automation, Process Automation Settings has 'Deploy processes and flows as active' on.
- Done when: the flow runs once on a test record and does nothing else.

## List views

### 28. Build the view Open quotes

- [ ] Where: Quotes, List View Controls, New
- Why it is manual: The filter is not a plain comparison on a custom field, the stage or the owner, so it is not generated. Filter: Quote is not accepted or declined and owner is me. Sort: Due date, soonest first.
- Done when: the saved view shows the expected records in the stated order.

### 29. Build the view Overdue quotes

- [ ] Where: Quotes, List View Controls, New
- Why it is manual: The filter is not a plain comparison on a custom field, the stage or the owner, so it is not generated. Filter: Quote is open and due date is in the past. Sort: Due date, oldest first.
- Done when: the saved view shows the expected records in the stated order.

### 30. Build the view Reorders due

- [ ] Where: Companies, List View Controls, New
- Why it is manual: The filter is not a plain comparison on a custom field, the stage or the owner, so it is not generated. Filter: Account status is active and last order date is older than the expected reorder interval. Sort: Last order date, oldest first.
- Done when: the saved view shows the expected records in the stated order.

### 31. Set the sort on Key and core accounts

- [ ] Where: Companies, the list view `Key_accounts`, List View Controls
- Why it is manual: List views have no sort in the metadata. Sort: Last order date, oldest first.
- Done when: the saved view sorts as stated.

### 32. Set the sort on Orders in flight

- [ ] Where: Orders, the list view `Orders_in_flight`, List View Controls
- Why it is manual: List views have no sort in the metadata. Sort: Promised date, soonest first.
- Done when: the saved view sorts as stated.

### 33. Set the sort on My open opportunities

- [ ] Where: Deals, the list view `My_open_opportunities`, List View Controls
- Why it is manual: List views have no sort in the metadata. Sort: Next step date, soonest first.
- Done when: the saved view sorts as stated.

## Permissions and access

### 34. Assign the permission set Manufacturing_and_distribution_B2B_user

- [ ] Where: Setup, Users, Permission Sets, Manage Assignments
- Why it is manual: Assigning a permission set is a data operation, not metadata. A new field is invisible until a profile or permission set grants it. Never ship profiles from here: a profile deploy overwrites far more.
- Done when: a non-admin test user sees and edits the blueprint's fields.

### 35. Set sharing for the standard objects

- [ ] Where: Setup, Security, Sharing Settings
- Why it is manual: Sharing for custom objects is set in the object files (public read and write). Standard objects need the org-wide defaults chosen by the client.
- Done when: the client has signed off the org-wide defaults.
