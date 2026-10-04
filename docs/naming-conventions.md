# Naming conventions

Rules for names in designs, client folders and the live CRMs. The design format rules are in
[../model/schema.md](../model/schema.md). The validator rejects keys that break them.

## In a design

| Thing | Rule | Example |
|---|---|---|
| Keys (objects, fields, options, stages, pipelines, relationships, decisions, automations, views) | `snake_case`, unique in their scope. Lowercase letters, digits and underscores, starting with a letter. | `renewal_date`, `closed_won` |
| Labels | Sentence case. Capital for the first word only, plus proper nouns. | `Renewal date`, not `Renewal Date` |
| Object key | Singular noun. | `subscription` |
| Object plural label | Plural of the label. | `Subscriptions` |
| Relationship key | `<from>_<to>`, matching the direction in `from` and `to`. | `subscription_company` |
| Relationship labels | `from_label` is what a record of the `from` object shows. `to_label` is what a record of the `to` object shows. | `Company` and `Subscriptions` |
| Pipeline key | The motion, not the tool. | `new_business`, `renewals` |
| Stage key | The state reached, in the past or as a noun. Keep `closed_won` and `closed_lost` for the end states. | `proposal_sent`, `closed_won` |
| Exit criteria | Start "Entered when". Describe a fact. | `Entered when the signed contract is received.` |
| Select options | Keys are `snake_case`. Labels are short and sentence case. | `no_budget: No budget` |
| Field descriptions | One or two sentences: what it holds, who uses it, and for what. | |
| Booleans | Name the true state. | `is_decision_maker`, not `decision_maker_flag` |
| Dates and times | End the key in `_date` or `_at`. | `next_step_date`, `signed_at` |
| Money | Say what the amount is. | `annual_contract_value` |
| Decisions | Phrase `question` as a question. Give a `recommended_default`. | |

British English throughout: organisation, programme, cheque, licence (noun).

Do not use real company or person names in a blueprint. Client designs may use client names
where the client's data needs them. Do not put personal data in a design at all.

## Keys that do not change

A key is the identity the planner matches on. Changing `renewal_date` to `renewal_on` in a design
reads as "remove one field and add another". The old field becomes a destructive manual step.
Pick keys carefully and rename only with `diff_design` open.

A label can change. The planner treats a label change as a `needs_review` rename.

## On each platform

Generators derive platform names from design keys. Override only when the client's CRM already has
a name you must match. Overrides go in `platform_overrides` (see the schema).

| Platform | What gets a name | Rule |
|---|---|---|
| Attio | Object and attribute `api_slug` | snake_case, starts with a letter, 50 characters at most. Avoid system slugs such as `name`, `stage`, `owner`, `domains`, `email_addresses`, `created_at`. Slugs are permanent in practice: renaming changes every URL that uses them. Override key: `api_slug`. Source: `platforms/attio/reference/open-questions.md` (Q12). |
| HubSpot | Property `name`, property group, custom object `name` | Lowercase snake_case. Property `name`, custom object `name` and `hasUniqueValue` cannot change after creation. Override keys: `property_group`, `object_type_id`. Source: `platforms/hubspot/README.md`, `reference/open-questions.md` (OQ-4, OQ-5). |
| Salesforce | Custom object and field API names | Custom objects and fields end `__c`. API names use letters, digits and single underscores. `fullName` is the identity, so a rename is a new component. Override keys: `api_name`, `record_type`. Source: `platforms/salesforce/README.md`. <!-- confirm once adapters land: how the Salesforce generator derives API names from keys --> |

## Client folders and tags

| Thing | Rule | Example |
|---|---|---|
| Client folder | Lowercase letters, digits and hyphens. `new_client` enforces it. | `acme`, `north-star-legal` |
| Sign-off tag | `<client>-v<major>.<minor>` | `acme-v1.0` |
| Plan files | `clients/<client>/build/plan-<platform>-<yyyymmdd>.json` | `plan-hubspot-20261104.json` |
| Branches for a client change | `<client>/<short-description>` | `acme/add-renewals-pipeline` |
| Changelog entries | Date in ISO form, newest first. | `2026-11-04` |
