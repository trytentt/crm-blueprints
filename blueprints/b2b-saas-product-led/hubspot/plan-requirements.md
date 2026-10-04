# Plan requirements: B2B SaaS, product-led (hubspot)

Generated from `design.yaml` and `platforms/hubspot/reference/`. Do not edit by hand. Tiers are as the research recorded them (last verified 2026-10-04); check the account's own limits before building.

**Minimum tier: Enterprise.** The custom objects need it, and the research found no workaround on a lower tier. Without Enterprise the custom objects, and any pipeline on them, cannot be created: the build turns them into a blocked item and the client must upgrade or drop the design's custom objects.

| Feature | Used for | Minimum tier | Source |
|---|---|---|---|
| Custom properties and property groups | 37 custom properties | Free tools allow 10 custom properties in total. Starter, Professional and Enterprise allow 1,000 per object. | https://legal.hubspot.com/hubspot-product-and-services-catalog |
| Custom objects | 2 custom object(s): Workspace, Adoption plan | Enterprise. Typically up to 10 definitions (OQ-3: check GET /crm/limits/2026-09/custom-object-types). | https://developers.hubspot.com/docs/api-reference/latest/crm/objects/schemas/guide.md ; https://knowledge.hubspot.com/object-settings/create-custom-objects |
| Custom pipelines | 2 pipeline(s): Sales assist, Expansion | Starter or higher. Limit of custom pipelines across all objects: Starter 15, Professional 100 or 350, Enterprise 350. | https://knowledge.hubspot.com/object-settings/set-up-and-customize-pipelines |
| Association labels | 4 paired label(s), one per non-standard relationship | Professional or Enterprise. Plan for 10 labels per object pair (the developer page says 10, the knowledge base says 50: OQ-2). | https://knowledge.hubspot.com/object-settings/create-and-use-association-labels ; https://developers.hubspot.com/docs/api-reference/latest/crm/associations/associations-schema/guide.md |
| Association limits (cardinality) | 3 relationship(s) capped at one: workspace_company, deal_workspace, adoption_plan_workspace | Professional or Enterprise. On Starter the cap is a convention only. | https://knowledge.hubspot.com/object-settings/set-limits-for-record-associations |
| Conditional stage properties (required fields per stage) | 13 stage(s), set by hand in the UI | Not stated on the page. Assume Professional or higher (OQ-8). | https://knowledge.hubspot.com/object-settings/set-up-and-customize-pipelines |
| Workflows | 6 automation(s), built by hand | Professional or Enterprise | https://knowledge.hubspot.com/workflows/create-workflows |
| Saved views | 6 view(s), built by hand | All products and plans | https://knowledge.hubspot.com/records/create-and-manage-saved-views |
