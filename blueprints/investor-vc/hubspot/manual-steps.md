# Manual steps: Investor, VC and angel deal flow (hubspot)

Generated from `design.yaml`. Do not edit by hand. The HubSpot API cannot do any of this.
Sources: https://developers.hubspot.com/docs/api-reference/latest/crm/pipelines/guide.md, https://knowledge.hubspot.com/records/create-and-manage-saved-views, https://knowledge.hubspot.com/workflows/create-workflows, `platforms/hubspot/reference/api-coverage.md`.

## Before and during the build

### 1. Create a service key and test in a developer test account first

- [ ] Where: Development > Keys > Service keys > Create service key (scopes in platforms/hubspot/reference/auth-and-setup.md)
- Why it is manual: Keys are made in the account by a super admin. A developer test account carries a 90-day Enterprise trial, so it can test custom objects before the client account is touched.
- Done when: `GET /crm/properties/2026-09/contacts` returns 200 with the key.

### 2. Confirm the account is Enterprise before creating custom objects

- [ ] Where: Settings > Account Management > Account defaults, and GET /crm/limits/2026-09/custom-object-types
- Why it is manual: Custom objects need Enterprise and there is no workaround on a lower tier. A client is typically limited to 10 definitions (OQ-3); this blueprint creates 1.
- Done when: the tier is written in the client notes and the limits call allows 1 custom object(s) (Portfolio investment).

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

### 6. Check closed stages of Portfolio outcome

- [ ] Where: Settings > Data Management > Objects > Portfolio investments > Pipelines tab > Portfolio outcome
- Why it is manual: HubSpot has open or closed on custom object stages, not won or lost, and no probability (the design's probabilities are not sent). The API key for closed is unconfirmed (OQ-1).
- Done when: closed stages (Exited, Written off) show as Closed. Set them by hand if the read-back says otherwise.

## Stage gates and lost reasons

### 7. Require Deal source to enter Sourced (Deal flow)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Deal flow > stage row for Sourced > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Sourced asks for Deal source.

### 8. Require Deal lead, Round type to enter Screening (Deal flow)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Deal flow > stage row for Screening > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Screening asks for Deal lead, Round type.

### 9. Require Thesis fit confirmed, Next step date to enter First meeting (Deal flow)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Deal flow > stage row for First meeting > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into First meeting asks for Thesis fit confirmed, Next step date.

### 10. Require Conviction, Round size, Next step date to enter Deep dive (Deal flow)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Deal flow > stage row for Deep dive > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Deep dive asks for Conviction, Round size, Next step date.

### 11. Require Our role, Pre-money valuation, Conviction to enter Partner meeting (Deal flow)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Deal flow > stage row for Partner meeting > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Partner meeting asks for Our role, Pre-money valuation, Conviction.

### 12. Require Term sheet status, Amount, Pre-money valuation to enter Term sheet (Deal flow)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Deal flow > stage row for Term sheet > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Term sheet asks for Term sheet status, Amount, Pre-money valuation.

### 13. Require Term sheet status, Next step date to enter Due diligence (Deal flow)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Deal flow > stage row for Due diligence > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Due diligence asks for Term sheet status, Next step date.

### 14. Require Diligence complete, Amount to enter Investment committee (Deal flow)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Deal flow > stage row for Investment committee > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Investment committee asks for Diligence complete, Amount.

### 15. Require Investment committee approved, Amount, Close date to enter Invested (Deal flow)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Deal flow > stage row for Invested > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Invested asks for Investment committee approved, Amount, Close date.

### 16. Require Pass reason to enter Passed (Deal flow)

- [ ] Where: Settings > Data Management > Objects > Deals > Pipelines tab > Deal flow > stage row for Passed > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test deal into Passed asks for Pass reason.

### 17. Require Amount invested, Ownership, Lead partner to enter Active (Portfolio outcome)

- [ ] Where: Settings > Data Management > Objects > Portfolio investments > Pipelines tab > Portfolio outcome > stage row for Active > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test portfolio_investment into Active asks for Amount invested, Ownership, Lead partner.

### 18. Require Follow-on reserve, Health to enter Follow-on review (Portfolio outcome)

- [ ] Where: Settings > Data Management > Objects > Portfolio investments > Pipelines tab > Portfolio outcome > stage row for Follow-on review > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test portfolio_investment into Follow-on review asks for Follow-on reserve, Health.

### 19. Require Latest valuation to enter Exit preparation (Portfolio outcome)

- [ ] Where: Settings > Data Management > Objects > Portfolio investments > Pipelines tab > Portfolio outcome > stage row for Exit preparation > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test portfolio_investment into Exit preparation asks for Latest valuation.

### 20. Require Latest valuation, Lead partner to enter Exit process (Portfolio outcome)

- [ ] Where: Settings > Data Management > Objects > Portfolio investments > Pipelines tab > Portfolio outcome > stage row for Exit process > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test portfolio_investment into Exit process asks for Latest valuation, Lead partner.

### 21. Require Exit route to enter Exited (Portfolio outcome)

- [ ] Where: Settings > Data Management > Objects > Portfolio investments > Pipelines tab > Portfolio outcome > stage row for Exited > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test portfolio_investment into Exited asks for Exit route.

### 22. Require Write-off reason to enter Written off (Portfolio outcome)

- [ ] Where: Settings > Data Management > Objects > Portfolio investments > Pipelines tab > Portfolio outcome > stage row for Written off > Conditional logic rules > Add rule > Add property > Required > Save logic
- Why it is manual: Conditional stage properties are UI only. The Pipeline Rules API does not cover them. Create the properties first; read-only properties cannot be used.
- Done when: moving a test portfolio_investment into Written off asks for Write-off reason.

## Decisions where the HubSpot mapping is lossy

### 23. Check the association limit for portfolio_investment_company

- [ ] Where: Settings > Data Management > Objects > Portfolio investments > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 24. Check the association limit for portfolio_investment_deal

- [ ] Where: Settings > Data Management > Objects > Portfolio investments > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 25. Check the association limit for deal_introducer

- [ ] Where: Settings > Data Management > Objects > Deals > Associations tab (Super Admin)
- Why it is manual: The limit is set on the labelled association type only. The unlabelled default type has an ID that is known only on read.
- Done when: many to one holds for both labelled and unlabelled links in a test.

### 26. Accept that currency fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property carries no currency code: the symbol is a display choice.
- Done when: the client has agreed in the client notes. Fields: deal.round_size, deal.pre_money_valuation, portfolio_investment.amount_invested, portfolio_investment.latest_valuation, portfolio_investment.follow_on_reserve.

### 27. Accept that percent fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property the stored value (0.2 or 20) is unconfirmed (open question OQ-5).
- Done when: the client has agreed in the client notes. Fields: portfolio_investment.ownership_percent.

### 28. Accept that user fields are lossy in HubSpot

- [ ] Where: Settings > Data Management > Objects > Properties tab, then open a record and look at the field
- Why it is manual: The HubSpot property holds the HubSpot owner ID, so only users of the account can be chosen.
- Done when: the client has agreed in the client notes. Fields: person.relationship_owner, deal.deal_lead, portfolio_investment.lead_partner.

## Workflows

### 29. Workflow: Create investment on invested

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A deal in the deal flow pipeline moves to invested.'; action 'Create a portfolio investment from the deal's amount, valuation and close date, link it to the company and the deal, copy the round co-investors, and set the company's organisation type to startup.'

### 30. Workflow: Flag stalled deals

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'An open deal has no next step date, or the date is more than 7 days past.'; action 'Notify the deal lead and add the deal to the stalled deals view.'

### 31. Workflow: Revisit passed companies

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A deal moves to passed with a pass reason of timing or traction and its next step date arrives.'; action 'Create a task for the deal lead to check progress and reopen the company at sourced if it now fits.'

### 32. Workflow: Investor update reminder

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A portfolio investment's next update due date is 7 days away.'; action 'Create a task for the lead partner to request the update from the founders.'

### 33. Workflow: Follow-on alert

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A portfolio company's funding stage changes or its health changes to needs support.'; action 'Move the investment to follow-on review and notify the lead partner.'

### 34. Workflow: Thank the introducer

- [ ] Where: Automations > Workflows > Create workflow > pick the object and trigger > add actions > Turn on
- Why it is manual: The only workflow API is beta, so this repo does not use it. Needs Professional or Enterprise and the Edit workflows and Publish permissions.
- Done when: a test run matches: trigger 'A deal with an introducer moves to term sheet or invested.'; action 'Create a task for the deal lead to thank the introducer.'

## Saved views

### 35. Saved view: Active deal flow

- [ ] Where: CRM > Deals > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Active deal flow shows on the Deals index with filter 'Stage is open and deal lead is me.' and sort 'Next step date, soonest first.'.

### 36. Saved view: Stalled deals

- [ ] Where: CRM > Deals > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Stalled deals shows on the Deals index with filter 'Stage is open and next step date is empty or in the past.' and sort 'Next step date, oldest first.'.

### 37. Saved view: Passed, to revisit

- [ ] Where: CRM > Deals > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Passed, to revisit shows on the Deals index with filter 'Stage is passed and pass reason is timing or traction.' and sort 'Next step date, soonest first.'.

### 38. Saved view: Portfolio health

- [ ] Where: CRM > Portfolio investments > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Portfolio health shows on the Portfolio investments index with filter 'Status is active or follow-on review.' and sort 'Health, at risk first.'.

### 39. Saved view: Investor updates due

- [ ] Where: CRM > Portfolio investments > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Investor updates due shows on the Portfolio investments index with filter 'Status is active and next update due is within 14 days.' and sort 'Next update due, soonest first.'.

### 40. Saved view: Co-investors

- [ ] Where: CRM > Companies > + add view > name it > set filters, columns and sort > Publish > Manage sharing
- Why it is manual: HubSpot has no API to create saved index-page views.
- Done when: the view Co-investors shows on the Companies index with filter 'Organisation type is co-investor or other fund.' and sort 'Relationship strength, close first.'.

## Permissions

### 41. Set roles and access

- [ ] Where: Settings > Users & Teams (menu name not verified against a page in the research)
- Why it is manual: No permission-set API was found. Only pipeline stage edit permissions have one, and this blueprint does not use it.
- Done when: a non-admin test user sees and edits what their role needs and nothing more.
