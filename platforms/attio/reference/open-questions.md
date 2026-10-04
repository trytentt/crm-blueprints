# Attio: open questions

> Sources: https://api.attio.com/openapi/api, https://docs.attio.com/ pages cited in the other reference files, https://attio.com/pricing, https://attio.com/help/reference/automations/workflows/create-a-workflow
> Last verified: 2026-10-04

Nothing below could be settled from the documentation alone. Each says what was found and the proposed handling.

## Pages that would not load

- https://docs.attio.com/docs/standard-objects-deals returned 404. The working page is https://docs.attio.com/docs/standard-objects/standard-objects-deals.
- https://attio.com/help/reference/managing-your-data/objects/create-custom-objects returned 404. Not needed; the API reference covers creation.
- https://attio.com/help/reference/managing-your-data/attributes/attribute-types returned 404. The attribute type facts come from the API reference pages and the OpenAPI spec.
- Several docs pages gave only summaries through the page reader (the limits shown were taken from the OpenAPI spec where possible). The OpenAPI spec at https://api.attio.com/openapi/api is the primary source for payload shapes.

## Questions

**Q1. Sandbox.** The docs describe no sandbox, test mode or developer account type. A search found third-party posts saying developer access is by request to support, or a free workspace seeded by hand. Handling: treat "sandbox" as a separate workspace chosen by the user. The adapter reads `GET /v2/self`, prints `workspace_name` and `workspace_slug`, and demands `--production` plus a typed confirmation of the slug when the target is not flagged as a test workspace. A test workspace is flagged by the user in config (`ATTIO_TARGET=sandbox`). The toolkit cannot detect it.

**Q2. Object limits.** The pricing page says Free "Up to 3", Plus "Up to 5", Pro "Up to 12", Enterprise "Unlimited objects". It does not say if People, Companies and Deals count. One third-party source reads the same numbers as custom objects only. Handling: the planner counts live objects, warns when design objects would exceed the lowest figure that fits, and stops on 400 `quota_exceeded` with the message. State the limit as "plan dependent, check pricing" in blueprint READMEs. Add a manual step: confirm the client's plan before building.

**Q3. Enabling Deals.** Deals are off by default and an admin enables them in the UI. No API for this was found. Handling: the adapter checks for `deals` in `GET /v2/objects`; if absent it emits a manual step and skips deal-dependent changes (the plan marks them blocked). Designs that avoid native Deals can use a custom object instead; decide per blueprint.

**Q4. Status attribute on a custom object.** The status docs say status attributes were built for lists but work on objects. Not tested on a custom object. Handling: pipelines use lists (see pipelines.md), so the question does not block v1.

**Q5. Required attributes and defaults.** The attribute read schema says `is_default_value_enabled` "must be true when `is_required` is `true`", yet create accepts `is_required` without a default. Unclear if a required attribute without a default is rejected or accepted. Handling: create all attributes with `is_required: false`, and apply `is_required: true` afterwards via PATCH only when the design says so; on a 400, report and leave not-required with a manual step. Also, required attributes can break record creation from other tools, so default to false and say so.

**Q6. Default statuses on a new status attribute.** Not documented whether a new status attribute starts empty or with defaults. Handling: after creating the attribute, list its statuses. Create the design's stages that are missing. If extra default statuses exist, do not archive; add a `needs_review` note listing them. The planner compares by title and ignores archived statuses.

**Q7. Cardinality labels.** The spec's description of `is_multiselect` pairs uses "many-to-one" and "one-to-many" in a way that does not obviously match the flag semantics. Handling: relationships.md maps by what each flag does on its own side. Before the first production use, create one test relationship in a throwaway workspace, read it back and confirm the reverse attribute's `is_multiselect`. Record the result in this file.

**Q8. Deals native stage versus a list stage.** Deals require a `stage`. Pipelines built as lists leave the native stage in place. Handling: recommend lists; add a manual step to hide or ignore the native `stage` on the Deals views, and default new deals to the first native stage. Alternative: for single-pipeline designs use the native stage (add statuses to it). Needs a decision from the design owner; default is lists.

**Q9. Archived names.** Not documented whether an archived attribute, option or status still blocks its slug or title. Handling: assume it does; read with `show_archived=true`; report an archived match and make restoring a `needs_review` change.

**Q10. Status and option order.** No position control. Order seems to follow creation order. Handling: always create stages in design order; the plan compares order from the read response and reports a mismatch as a manual step (reorder in the UI).

**Q11. `is_multiselect` by type.** The docs do not list which types accept it. Handling: send true only for select, record-reference, actor-reference, domain, email-address and phone-number; the 400 response will show if one is refused.

**Q12. Slug rules.** The docs say snake_case and unique. No length cap or reserved word list. Handling: validate `^[a-z][a-z0-9_]*$`, cap at 50 characters, and avoid system slugs (`name`, `stage`, `owner`, `domains`, `email_addresses`, `created_at`). Treat 409 `slug_conflict` on a new attribute as a collision to report if the live attribute differs from the design.

**Q13. Retry-After format.** The docs call it a "reset datetime". Handling: accept seconds or an HTTP date.

**Q14. Probability and forecasting.** No stage probability in the API or on statuses. Handling: a `probability` number attribute on the pipeline list as a convention; weighted forecasting is a manual or reporting task.

**Q15. Plan needs for views, workflows and private lists.** Workflows are on all plans (credit limits vary). Private lists appear under Plus on the pricing page; the API can return 403 `billing_error` for member-level list access. Handling: always create lists with `workspace_access: "full-access"`.

**Q16. Beta features.** Custom activities (`/v2/activities`) are alpha and billing-gated. Not used. Attio MCP and SQL (`POST /v2/sql`) exist but are not needed for structure.
