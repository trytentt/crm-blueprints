> Sources: https://developers.hubspot.com/docs/api-reference/latest/crm/objects/schemas/guide.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/properties/guide.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/pipelines/guide.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/associations/associations-schema/guide.md ; https://developers.hubspot.com/docs/api-reference/latest/crm/lists/filters/guide.md ; https://developers.hubspot.com/docs/api-reference/latest/error-handling.md ; https://knowledge.hubspot.com/object-settings/set-up-and-customize-pipelines ; https://knowledge.hubspot.com/object-settings/create-and-use-association-labels ; https://legal.hubspot.com/hubspot-product-and-services-catalog (further pages are listed in the other files in this folder)
> Last verified: 2026-10-04

# HubSpot: open questions

Each item says what I found and how the tooling should behave until it is resolved. Test in a developer test account (Enterprise trial) and update this file with the answer.

## Pages that did not load

- None failed outright. `https://developers.hubspot.com/docs/api-reference/latest/crm/objects/schemas/guide.md` and the other reference pages loaded as raw Markdown. The older URL `/docs/api/crm/crm-custom-objects` returned the custom object *records* guide, not the schema guide, so I used the Schemas API pages instead.
- Raw OpenAPI JSON files under `/docs/specs/...` did not return JSON when fetched directly, so endpoint paths were taken from the OpenAPI blocks embedded in each reference page.
- Knowledge base pages were read as plain text of the rendered HTML. The saved-views article was found through a web search result (the URL I first guessed returned 404).

## OQ-1. Won, lost and closed on non-deal pipelines

- Found: deals take `metadata.probability` (`1.0` won, `0.0` lost). Reading back shows `metadata.isClosed`. Tickets use `ticketState` (`OPEN` or `CLOSED`). The guide says metadata is optional for other objects and shows no custom-object example. The knowledge base asks for Open or Closed per stage in the UI. One audit sample shows a "Closed lost" stage with probability `0.8` and `isClosed` false, which looks like sample noise.
- Unknown: the input key and values for open or closed on custom object stages, and whether `isClosed` can be set directly on deals.
- Handling: deals use probability only. For custom objects send `isClosed` as a string, read back, and raise a manual step if the stage is not closed. Do not claim won versus lost exists outside deals.

## OQ-2. Association label limit: 10 or 50

- Found: the developer page for creating labels says up to 10 labels per object pair. The knowledge base article and the product catalog say up to 50.
- Handling: plan for 10, warn above that, and let the live limits endpoint (`/crm/limits/{V}/associations/labels`) override.

## OQ-3. Custom object limits per hub

- Found: the catalog shows "up to 10 object definitions and 1,000,000 records" under the Enterprise editions of Marketing, Sales, Service and Content Hub, and "up to 20 object definitions and 1,500,000 records" under Data Hub Enterprise. The catalog is one very long page, so I may have mis-paired a table.
- Handling: `plan-requirements.md` should say "Enterprise; typically 10 definitions". The adapter should read `/crm/limits/{V}/custom-object-types` before planning.

## OQ-4. Create-schema body and label immutability

- Found: the OpenAPI schema marks nine fields as required on create (`allowsSensitiveProperties`, `associatedObjects`, `labels`, `name`, `properties`, `requiredProperties`, `searchableProperties`, `secondaryDisplayProperties`, `shouldCreateSameObjectAssociation`). The guide's worked example omits several. The `labels` text says "no way to change this later", yet the PATCH body accepts `labels`.
- Handling: always send all nine fields. Treat labels as fixed; a label change is a `needs_review` manual step.

## OQ-5. Property type changes, naming, currency, percent, phone

- Found: property `name` rules are not stated. The update schema accepts `type` and `fieldType` but not which conversions are allowed. The `type` enum includes `phone_number`, undocumented in the prose. `currencyPropertyName` exists with no explanation. The percent hint is shown without saying whether the stored value is a fraction.
- Handling: generate lowercase snake_case names; never change `type`/`fieldType` (destructive manual step); use `string`/`phonenumber` for phone; for currency set `showCurrencySymbol` and leave the code to the account currency; for percent store the number the user sees and test display in a test account before the first client use.

## OQ-6. Sensitive-data scopes

- Found: the `.sensitive` and `.highly_sensitive` scope variants appear in many security lists, and `allowSensitiveProperties` exists on schemas. Sensitive Data is Enterprise only and needs extra setup.
- Handling: not part of the default scope set. Flag in the build sheet if a design field is marked sensitive.

## OQ-7. First association definition between two existing objects

- Found: `associatedObjects` in the schema creates associations at object creation. The association schema API creates labels. I did not find a call that creates the unlabeled definition between two objects that already exist (for example a custom object and a company that were not linked at creation).
- Handling: for a custom object, always declare `associatedObjects` in the first schema call. For later links, create a label and read back the type IDs; if the read shows no unlabeled type, raise a manual step (Settings > Data Management > Objects > Associations).

## OQ-8. Plan tier for conditional stage properties (required fields per stage)

- Found: UI-only, no API. The knowledge base page for pipelines does not state a tier for this feature on its own. It sits in the same article that lists Professional for cloning and team restriction.
- Handling: tell the user it is a manual step; assume Professional or higher until a client with Starter shows otherwise.

## OQ-9. Required properties on standard objects

- Found: only custom object schemas have `requiredProperties`. I found no API to make a property required on contacts, companies or deals, other than form settings, conditional stage properties (UI) and property validation rules (value format, not presence).
- Handling: design `required: true` on a standard object field becomes a manual step ("Settings > Properties > edit property > rules" or a workflow), or a data-quality check.

## OQ-10. "Already exists" signal

- Found: undocumented (see `limits-and-errors.md`).
- Handling: read-before-write. Confirm in a test account what a duplicate create returns for property, group, schema, pipeline, label and list, then replace the fallback with the real status and category.

## OQ-11. What "deploy to production" from a sandbox covers

- Found: the sandbox article says supported assets can be deployed and links to a list of "supported object configurations" that I did not read.
- Handling: do not rely on sandbox deploy for the build. Use `crm_apply` for both environments.

## OQ-12. Lists: tier limits, operation type casing

- Found: the Lists API reference states Free tier. The catalog limits active lists on lower tiers, but I did not capture counts. The filters guide uses lowercase operation type names in its reference but uppercase in worked examples.
- Handling: lists are optional in v1. If used, test both casings and read the account's list limit before creating.

## OQ-13. Which API version to pin

- Found: dated versions `2026-03` (Supported) and `2026-09` (Current) are GA; legacy v3/v4 still work. Pipeline rules exist only in dated versions. `2026-09` changes delete and replace behaviour for pipelines.
- Handling: pin `2026-09` by default, make it an env setting (`HUBSPOT_API_VERSION`), and keep legacy path notes in `api-coverage.md` as a fallback.

## OQ-14. Required scopes for association label calls

- Found: the label and limit endpoints list many object read and write scopes as alternatives, including read-only ones, even for create.
- Handling: ask for `crm.objects.{contacts,companies,deals}.write` plus `crm.objects.custom.write` on a build key to be safe; verify that a read-scope-only key is refused on create in a test account.
