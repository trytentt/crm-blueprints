# Salesforce test fixtures

Shapes follow the research in `platforms/salesforce/reference/` (`limits-and-errors.md` for deploy replies and
describe, `pipelines.md` for the `OpportunityStage` query, `open-questions.md` B1 for the `Organization` query).
They are authored from the documented shapes, not recorded from a live org (DECISIONS D-2), and every name,
id and URL is invented. Replace them with recordings after the first live run (open-questions.md G).

- `org_display_*.json`: `sf org display --json`. `accessToken` is a placeholder; the adapter must drop it.
- `query_organization_*.json`: `SELECT Name, OrganizationType, IsSandbox FROM Organization`.
- `sobject_list_custom_*.json`: `sf sobject list --sobject custom --json` (a list of API names, with managed and metadata noise).
- `describe_*.json`: `sf sobject describe --json` for the three standard objects (a subset of their fields)
  and for a hand-built custom object with an inactive picklist value, a user lookup and a managed field.
- `query_opportunity_stage.json`: `SELECT ApiName, MasterLabel, IsActive, IsClosed, IsWon, DefaultProbability, SortOrder FROM OpportunityStage`.
- `deploy_*.json`: `sf project deploy start --json`. A failure with `componentFailures` as one object, one with a list
  and string booleans, exit codes 68 (partial) and 69 (still running). `error_no_org.json` is an error envelope.
