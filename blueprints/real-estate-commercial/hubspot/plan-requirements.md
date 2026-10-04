# Plan requirements: Commercial real estate, leasing (hubspot)

Generated from `design.yaml` and `platforms/hubspot/reference/`. Do not edit by hand. Tiers are as the research recorded them (last verified 2026-10-04); check the account's own limits before building.

**Minimum tier: Enterprise.** The custom objects need it, and the research found no workaround on a lower tier. Without Enterprise the custom objects, and any pipeline on them, cannot be created: the build turns them into a blocked item and the client must upgrade or drop the design's custom objects.

| Feature | Used for | Minimum tier | Source |
|---|---|---|---|
| Custom properties and property groups | 37 custom properties | Free tools allow 10 custom properties in total. Starter, Professional and Enterprise allow 1,000 per object. | https://legal.hubspot.com/hubspot-product-and-services-catalog |
| Custom objects | 2 custom object(s): Property, Lease | Enterprise. Typically up to 10 definitions (OQ-3: check GET /crm/limits/2026-09/custom-object-types). | https://developers.hubspot.com/docs/api-reference/latest/crm/objects/schemas/guide.md ; https://knowledge.hubspot.com/object-settings/create-custom-objects |
| Custom pipelines | 2 pipeline(s): Letting, Lease renewal | Starter or higher. Limit of custom pipelines across all objects: Starter 15, Professional 100 or 350, Enterprise 350. | https://knowledge.hubspot.com/object-settings/set-up-and-customize-pipelines |
| Custom object pipelines | Lease renewal | Enterprise | https://knowledge.hubspot.com/object-settings/set-up-and-customize-pipelines |
| Not supported on custom object pipelines: probability, won versus lost | Stage probabilities and the won or lost split of Lease renewal are not sent. Stages are open or closed only (OQ-1); the stage label carries the meaning | No tier has them: HubSpot has probability and won or lost on deal pipelines only | https://developers.hubspot.com/docs/api-reference/latest/crm/pipelines/guide.md |
| Association labels | 5 paired label(s), one per non-standard relationship | Professional or Enterprise. Plan for 10 labels per object pair (the developer page says 10, the knowledge base says 50: OQ-2). | https://knowledge.hubspot.com/object-settings/create-and-use-association-labels ; https://developers.hubspot.com/docs/api-reference/latest/crm/associations/associations-schema/guide.md |
| Association limits (cardinality) | 5 relationship(s) capped at one: deal_property, property_landlord, lease_property, lease_tenant, lease_deal | Professional or Enterprise. On Starter the cap is a convention only. | https://knowledge.hubspot.com/object-settings/set-limits-for-record-associations |
| Conditional stage properties (required fields per stage) | 15 stage(s), set by hand in the UI | Not stated on the page. Assume Professional or higher (OQ-8). | https://knowledge.hubspot.com/object-settings/set-up-and-customize-pipelines |
| Workflows | 6 automation(s), built by hand | Professional or Enterprise | https://knowledge.hubspot.com/workflows/create-workflows |
| Saved views | 6 view(s), built by hand | All products and plans | https://knowledge.hubspot.com/records/create-and-manage-saved-views |
