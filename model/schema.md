# Design file format

A design is one YAML file, `blueprints/<name>/design.yaml`. It is the source of truth. Platform
files are generated from it. Check a design with `uv run python -m tools.validate <path>`.

All keys are `snake_case`. Labels are sentence case. Text is British English.

## Top-level keys

```yaml
extends: core            # optional; only "core" is supported
name: B2B SaaS, sales-led
description: One or two sentences on who the design is for.
add_objects: []
add_fields: []
add_relationships: []
pipelines: []
decisions: []
automations: []
views: []
platform_overrides: {}
```

An unknown key is an error, so a typo such as `add_field` cannot pass silently.

## `extends`

Every design starts from `model/core-model.yaml`: three objects (`company`, `person`, `deal`), their
core fields, and three native links (`person_company`, `deal_company`, `deal_person`). The loader
merges your `add_*` keys onto it.

- `add_objects` adds new objects. Reusing `company`, `person` or `deal` is an error.
- `add_fields` may target core or custom objects. Redefining a field that the core model already has
  (same `object` and `key`) is an error: core fields cannot be overridden. Give a new field a new key.
- `add_relationships` adds links. Core links are always present.

## Objects (`add_objects`)

```yaml
add_objects:
  - key: subscription          # snake_case, unique
    label: Subscription        # sentence case
    plural_label: Subscriptions
    description: One customer contract. Required.
```

Every object needs a `description`. Objects added here have `kind: custom`; core ones have `kind: core`.

## Fields (`add_fields`)

```yaml
add_fields:
  - object: deal               # a core or custom object key
    key: lost_reason
    label: Lost reason
    type: select
    description: Why the deal was lost. Required.
    required: false            # optional; true if the field must always be filled
    options:                   # select and multi_select only
      no_budget: No budget
      competitor: Chose a competitor
    native: [hubspot]          # optional; platforms where it exists out of the box
    native_names: {hubspot: some_property}
```

Options can be written three ways: a mapping `key: label` (shown above), a list of keys (labels are
derived: `mid_market` becomes "Mid market"), or a list of `{key, label}` mappings.

`native` and `native_names` are used for the core model. In a design, leave them out unless you are
certain the field exists out of the box. Every field needs a `description`.

### The 14 canonical field types

| Type | Use for |
|---|---|
| `text` | Short single-line text |
| `long_text` | Multi-line notes |
| `select` | One choice from a fixed list (needs `options`) |
| `multi_select` | Several choices from a fixed list (needs `options`) |
| `number` | Counts and quantities |
| `currency` | Money in the account currency |
| `percent` | Percentages |
| `date` | A day |
| `datetime` | A day and time |
| `checkbox` | Yes or no |
| `url` | A web address |
| `email` | An email address |
| `phone` | A phone number |
| `user` | A team member of the CRM account |

Only `select` and `multi_select` take `options`. Option keys are `snake_case` and unique within the field.

## Relationships (`add_relationships`)

```yaml
add_relationships:
  - key: subscription_company
    from: subscription
    to: company
    cardinality: many_to_one
    from_label: Company          # name shown on a subscription record
    to_label: Subscriptions      # name shown on a company record
    purpose: Shows every contract a customer has had.
```

`cardinality` reads from `from` to `to`:

| Value | Meaning |
|---|---|
| `one_to_one` | One `from` record links to one `to` record |
| `one_to_many` | One `from` record links to many `to` records |
| `many_to_one` | Many `from` records link to one `to` record (most common) |
| `many_to_many` | Many on both sides |

Core links carry a `native` list (platforms where the link exists out of the box). Generators skip
native links.

## Pipelines

```yaml
pipelines:
  - object: deal
    key: new_business
    name: New business
    stages:
      - key: discovery
        label: Discovery
        type: open
        probability: 20
        exit_criteria: Entered when the first discovery call has happened.
        required_fields: [next_step_date]   # field keys on the pipeline's object
      - key: closed_won
        label: Closed won
        type: won
        probability: 100
        exit_criteria: Entered when the signed contract is received.
      - key: closed_lost
        label: Closed lost
        type: lost
        probability: 0
        exit_criteria: Entered when the buyer says no.
        required_fields: [lost_reason]
```

Stage types:

| Type | Rules |
|---|---|
| `open` | Work in progress. At most 8 per pipeline. |
| `won` | Probability must be 100. At least one per pipeline. |
| `lost` | Probability must be 0. At least one per pipeline. `required_fields` must include a `select` field (the lost reason). |

Every stage has an `exit_criteria` that starts with "Entered when" and describes a fact, not a feeling.
Probabilities are numbers from 0 to 100. `required_fields` lists the fields that must be filled before
a record can enter the stage. Each must exist on the pipeline's object. Pipelines can sit on any
object, not only Deal.

## Decisions, automations, views

```yaml
decisions:
  - key: renewals_as_deals
    question: Are renewals tracked as deals?
    recommended_default: Yes, in a second pipeline on Deal.
automations:
  - key: start_onboarding
    name: Start onboarding
    trigger: A subscription is created.
    action: Create an onboarding record and assign it.
views:
  - key: stalled_deals
    name: Stalled deals
    object: deal
    filter: Stage is open and next step date is in the past.
    sort: Next step date, oldest first.
```

A design should have at least 3 of each; fewer is a warning. Blueprints are checked with `--strict`,
so a warning fails CI. Use `decisions` for anything plan-dependent or uncertain, with a
recommended default.

## `platform_overrides`

Optional. Sets a platform-specific value for one object or field. The shape is:

```yaml
platform_overrides:
  hubspot:
    objects:
      subscription: {object_type_id: "2-1234567"}
    fields:
      deal.lost_reason: {property_group: dealinformation}   # field targets are object.field
  salesforce:
    objects:
      subscription: {api_name: Subscription__c, record_type: Standard}
  attio:
    objects:
      subscription: {api_slug: subscriptions}
```

Allowed keys per platform, usable on an object or a field:

| Platform | Keys |
|---|---|
| `hubspot` | `property_group`, `object_type_id` |
| `salesforce` | `record_type`, `api_name` |
| `attio` | `api_slug` |

Any other platform, section, key or target that does not exist in the design is an error. Values are
non-empty text.

## Design principles

Every blueprint follows these. The validator enforces what a machine can check.

1. **Model the business, not the tool.** Objects and stages come from how the company sells and delivers.
2. **One human, one record.** A person has a single Person record, matched by email.
3. **Every custom field has a stated use.** The `description` is required, and says what the field is for.
4. **Selects over free text for anything reported on.** If you will filter or count by it, it is a select.
5. **Stages are commitments with exit criteria.** At most 8 open stages. Each exit criterion starts "Entered when".
6. **Every pipeline has won and lost stages; lost requires a reason.** A select field, required on the lost stage.
7. **Gate stages with required fields.** A record cannot enter a stage without the facts that justify it.
8. **Separate selling from delivery.** Deals sell; delivery gets its own object. The validator warns if there is no custom object for delivery and no decision explaining why, or if a Deal pipeline has delivery-type stages.
9. **Build order: objects, relationships, pipelines, fields, automations, views, QA.** Generated build sheets and plans follow this order.
