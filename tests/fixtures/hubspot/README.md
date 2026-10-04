# HubSpot test fixtures

Shapes follow the examples in `platforms/hubspot/reference/` (properties read response, pipeline
response, error bodies in `limits-and-errors.md`). Values are invented: no real portal data.

- `native_properties.json`: the standard properties the core model names, with `hubspotDefined`
  and `modificationMetadata.readOnlyDefinition` set as the research says to read them.
- `default_deal_pipeline.json`: the `default` deal pipeline every account has.
- `error_429.json`, `error_400.json`: error bodies from limits-and-errors.md.
- `limits_custom_object_types.json`: ASSUMED shape. The research does not show this response.
- `account_info.json`: ASSUMED shape. No research page covers the account-info endpoint.
