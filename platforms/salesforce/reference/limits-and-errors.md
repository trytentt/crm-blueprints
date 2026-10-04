> Sources: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/api_meta.pdf (Metadata API Developer Guide v68.0: "Deploying and Retrieving Metadata with the Zip File", "deploy()", "DeployOptions", "deployRecentValidation()", "Error Handling", "upsertMetadata()"); https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf (Developer Limits and Allocations Quick Reference: "API Request Limits and Allocations", "Metadata Limits"); https://raw.githubusercontent.com/salesforcecli/plugin-deploy-retrieve/main/src/commands/project/deploy/start.ts; https://raw.githubusercontent.com/salesforcecli/plugin-deploy-retrieve/main/src/utils/errorCodes.ts; https://raw.githubusercontent.com/salesforcecli/plugin-deploy-retrieve/main/src/utils/types.ts; https://raw.githubusercontent.com/salesforcecli/plugin-deploy-retrieve/main/messages/deploy.metadata.md; https://raw.githubusercontent.com/forcedotcom/source-deploy-retrieve/main/src/client/types.ts; https://raw.githubusercontent.com/salesforcecli/sf-plugins-core/main/src/sfCommand.ts; https://raw.githubusercontent.com/salesforcecli/sf-plugins-core/main/src/SfCommandError.ts; https://raw.githubusercontent.com/salesforcecli/plugin-schema/main/src/commands/sobject/describe.ts; https://raw.githubusercontent.com/jsforce/jsforce/main/src/types/common.ts
> Last verified: 2026-10-04

# Salesforce limits and errors

## Deploy and retrieve limits (guide, "Metadata Limits")

| Limit | Value |
|---|---|
| Files in one deploy or retrieve | 10,000 |
| Compressed zip (SOAP) | about 39 MB (50 MB after base-64 encoding) |
| Uncompressed project | 600 MB (629,145,600 bytes) |
| AppExchange packages | 35,000 files |
| Retrieves using `rootTypesWithDependencies` | 25 a day, 100 components each |
| Deploy wait in the CLI | `--wait` default 33 minutes |
| Validated deploy reusable for quick deploy | 10 days |

"Limits can change without notice" (guide). A blueprint is far below these: a full build is a few hundred small files.

The CLI can deploy over REST instead of SOAP: `sf config set org-metadata-rest-deploy true` (guide, DX section on deploy; the CLI source lists `ConfigVars.ORG_METADATA_REST_DEPLOY`). Only deploys use REST. Retrieves always use SOAP. The 39 MB zip limit is a SOAP limit. File limits apply to both.

## API request limits

From the quick reference.

Concurrent long-running requests (20 seconds or longer): Developer Edition and trial orgs 5; production orgs and sandboxes 25. Exceeding it returns `REQUEST_LIMIT_EXCEEDED`.

REST and SOAP calls time out after 10 minutes (`REQUEST_RUNNING_TOO_LONG` for SOAP, `QUERY_TIMEOUT` for REST).

Total calls in 24 hours (rolling, org-wide, not per user):

| Edition | Allowance |
|---|---|
| Developer Edition | 15,000 |
| Enterprise, and Professional with API access enabled | 100,000 + (licences x per-licence calls) + purchased add-ons. Per licence: Salesforce 1,000, Salesforce Platform 1,000, Platform One App 200 |
| Unlimited, Performance | 100,000 + (licences x calls), Salesforce and Platform licences 5,000 each |
| Full sandbox | 5,000,000 (when not created from a template) |

What counts: REST, SOAP, Bulk, Bulk 2.0 and most Connect REST calls. Metadata API calls are SOAP calls on the org, so they count. A CLI deploy makes a few calls plus status polls. We have not measured the exact number. The adapter should avoid loops that deploy one field at a time. Group changes in one source deploy.

How to read the remaining allowance: `sf org list limits --target-org <alias> --json` (the command lists each limit with its `Max` and `Remaining`; the REST `/limits` resource is the source). The `Sforce-Limit-Info` response header shows usage on REST calls.

Retry advice: there is no documented `Retry-After` header for these limits. On `REQUEST_LIMIT_EXCEEDED` for concurrency, wait and retry with exponential backoff (start at 30 seconds, double, give up after five tries). On a total-allowance error, stop and report; the allowance recovers over the 24-hour window. Never retry a failed deploy blindly: read the failures first.

## CLI exit codes for a deploy

From `errorCodes.ts` and `determineExitCode`:

| `result.status` | Exit code | Meaning |
|---|---|---|
| `Succeeded` | 0 | Done |
| `Failed` | 1 | Rolled back (check `details.componentFailures`) |
| `Canceled` | 1 | Cancelled |
| `SucceededPartial` | 68 | Some components saved. Only possible with `--ignore-errors`. Never use it. |
| `InProgress`, `Pending`, `Canceling` | 69 | Still running (for example when `--wait` ran out) |

The CLI sets `rollbackOnError` to true unless `--ignore-errors` is passed. The guide says rollback must be true for production.

## JSON output shape: a deploy

Command: `sf project deploy start --source-dir force-app --target-org <alias> --json`.

The envelope (sf-plugins-core): `{ "status": <exit code>, "result": <command result>, "warnings": [...] }`. For a failed deploy the CLI still prints the result, with `status` set to the exit code (1, 68 or 69). It does not switch to the error envelope. Treat any non-zero `status` as failure and read `result`.

Shape of `result` (from `DeployResultJson` and `MetadataApiDeployStatus`):

```json
{
  "status": 1,
  "result": {
    "id": "0Af...",
    "status": "Failed",
    "success": false,
    "done": true,
    "checkOnly": false,
    "createdDate": "2026-10-04T10:00:00.000Z",
    "numberComponentsTotal": 12,
    "numberComponentsDeployed": 11,
    "numberComponentErrors": 1,
    "numberTestsTotal": 0,
    "rollbackOnError": true,
    "ignoreWarnings": false,
    "errorMessage": "...optional top-level message...",
    "errorStatusCode": "...optional...",
    "details": {
      "componentFailures": {
        "componentType": "ValidationRule",
        "fileName": "objects/Opportunity.object",
        "fullName": "Opportunity.Proposal_requires_decision_maker",
        "problem": "Error text from Salesforce",
        "problemType": "Error",
        "lineNumber": "1",
        "columnNumber": "1",
        "success": "false",
        "created": "false",
        "changed": "false",
        "deleted": "false",
        "createdDate": "2026-10-04T10:00:02.000Z"
      },
      "componentSuccesses": []
    },
    "files": [
      {
        "fullName": "Opportunity.Proposal_requires_decision_maker",
        "type": "ValidationRule",
        "state": "Failed",
        "filePath": "force-app/main/default/objects/Opportunity/validationRules/Proposal_requires_decision_maker.validationRule-meta.xml",
        "error": "Error text from Salesforce (Line: 1, Col: 1)",
        "problemType": "Error",
        "lineNumber": 1,
        "columnNumber": 1
      }
    ]
  },
  "warnings": []
}
```

Parse carefully:

- `details.componentFailures` and `componentSuccesses` are typed `DeployMessage | DeployMessage[]`. One failure may arrive as a single object, many as an array. Normalise to a list.
- `DeployMessage` booleans (`success`, `created`, `changed`, `deleted`) are typed `'true' | 'false' | boolean`. Normalise.
- `lineNumber` and `columnNumber` are strings in `details` and numbers in `files[]`.
- `fileName` in `details` uses metadata format (`objects/Opportunity.object`) even though the source was decomposed. Use `files[].filePath` to find the local file.
- `files[]` is the friendly view. `state` is one of `Created`, `Changed`, `Unchanged`, `Deleted`, `Failed`. Only a `Failed` row has `error`, `problemType`, `lineNumber`, `columnNumber`.
- `problemType` is `Warning` or `Error`. With `ignoreWarnings` false (the default) a warning fails the deploy: `success` becomes false and the warning is treated as an error (guide).
- Async (`--async`) returns a smaller result: `id`, `status` (`Queued` and so on), `files` may be empty.

JSON output for a check-only run is the same shape with `checkOnly` true. The command prints `Dry-run complete.` in text mode.

### Errors outside a deploy result

For failures before a deploy starts (no org, bad flags, no source, auth expired) the CLI uses `SfCommandError`. In `--json` mode it prints roughly this (the values are illustrative; only the field names come from the source):

```json
{
  "name": "ErrorName",
  "message": "human readable text",
  "exitCode": 1,
  "commandName": "DeployMetadata",
  "stack": "...",
  "warnings": [],
  "status": 1,
  "code": "1",
  "context": "DeployMetadata",
  "actions": ["optional suggested fixes"],
  "data": {}
}
```

Fields come from `SfCommandError` (`name`, `message`, `exitCode`, `code`, `commandName`, `data`, `context`, `actions`, `stack`, `status`). Key off `exitCode` and `name`. Do not match on message text. A deploy that times out on the client side raises `error.ClientTimeout`; the deployment keeps running. Use `sf project deploy resume --job-id <id>` or `sf project deploy report --job-id <id>`.

Other CLI errors to expect (from the plugin's message file):

- `error.nothingToDeploy`: "No local changes to deploy". Happens with no flags on a source-tracked org. We always pass `--source-dir` or `--manifest`, so we do not hit it.
- `error.Conflicts`: org changes conflict with local ones (tracked orgs only). Never pass `--ignore-conflicts`.
- `error.NoTestsSpecified`: `--test-level RunSpecifiedTests` needs `--tests`.

## Metadata API errors (guide, "Error Handling")

- SOAP faults carry an `ExceptionCode`. `INVALID_SESSION_ID` means the session expired (default two hours); log in again.
- `deploy()` errors: read `problem` and `success` on each `DeployMessage`.
- Synchronous CRUD calls (`createMetadata`, `upsertMetadata`): a `statusCode` on each error in the result.
- Asynchronous CRUD: `statusCode` in the `AsyncResult`.
- `retrieve()` errors: `problem` on the `RetrieveMessage`.

## "Already exists": source deploys are upserts

The guide labels `deploy()` as "create or update" (API 29.0 and later). `upsertMetadata()` is described the same way: it updates a component if one with that `fullName` exists, otherwise it creates it. The CLI deploys through `deploy()`.

Consequences for idempotency (safety rule 6):

- There is no "already exists" error from a source deploy. Re-deploying the same files succeeds. Each file's `state` is `Unchanged`, `Changed` or `Created`.
- `fullName` is the identity. A file with a new name creates a new component. It does not rename.
- To make a re-run a no-op we do not rely on the deploy. The plan compares the design with live state first (retrieve and describe), and only writes files that differ.
- A re-run that reports any `Created` or `Changed` file means the plan and the live state disagreed. Treat that as a test failure in the live smoke test.
- The create-only CRUD calls do raise a duplicate-name status code, but the guide pages read do not name it. We do not use those calls.

Do not rely on `--dry-run` alone to show what would change. Its result lists components checked. We have not proved whether `created` and `changed` are meaningful in a check-only result. Use retrieve and compare for the plan; use `--dry-run` as the proof that Salesforce accepts the files.

## Check-only and validate

See auth-and-setup.md for the exact commands. Key limits:

- `--dry-run` runs the same validations as a real deploy and rolls back. It also runs Apex tests if the test level calls for it. In sandboxes the default is `NoTestRun`. In production the default is `RunLocalTests` when the package contains Apex, otherwise none are needed (CLI help). We deploy no Apex, so no tests run.
- A change between `Lookup` and `MasterDetail` cannot be checked with `--dry-run` (it fails). Validate in a full deployment to a sandbox.
- `sf project deploy validate` is meant for production. It requires tests, returns a job ID, and the job ID works with `sf project deploy quick` for 10 days (the CLI help says `--use-most-recent` only finds IDs from the last 3 days). We do not use it in v1.

## Retrieve and describe output

`sf project retrieve start --metadata <names> --json` returns `{ status, result: { ...retrieve status fields..., files: [ {fullName, type, state, filePath} ] }, warnings }` (`RetrieveResultJson`: the Metadata API retrieve status with `zipFile` removed and `files` added; the exact status fields were not read). Files land in the package directory. With `--target-metadata-dir` it writes a zip in metadata format instead.

`sf sobject describe --sobject <name> --json` returns `{ status: 0, result: <DescribeSObjectResult>, warnings: [] }`. Useful parts (jsforce types):

- Top level: `name`, `label`, `labelPlural`, `custom`, `keyPrefix`, `createable`, `updateable`, `deletable`, `queryable`, `searchable`, `fields[]`, `childRelationships[]`, `recordTypeInfos[]`, `namedLayoutInfos[]`, `actionOverrides[]`.
- Per field: `name`, `label`, `type` (`string`, `textarea`, `picklist`, `multipicklist`, `double`, `currency`, `percent`, `date`, `datetime`, `boolean`, `url`, `email`, `phone`, `reference`, `id`, and so on), `length`, `precision`, `scale`, `digits`, `nillable`, `custom`, `unique`, `externalId`, `calculated`, `defaultValue`, `inlineHelpText`, `picklistValues[]` (each with `value`, `label`, `active`, `defaultValue`), `restrictedPicklist`, `referenceTo[]`, `relationshipName`, `relationshipOrder`, `cascadeDelete`, `restrictedDelete`, `writeRequiresMasterRead`, `createable`, `updateable`, `controllerName`, `dependentPicklist`.
- `type` is the REST type, not the metadata type. `Text` and `Url`, for example, are `string` and `url`. A long text area is `textarea` with a large `length`. Describe cannot distinguish `Text` (255 or fewer) from `TextArea`, nor `Lookup` from `MasterDetail` with certainty. Use retrieve for exact types.
- `describe` shows only what the running user can see. A field the user has no access to is missing from the result. Always read as a user who has the permission set, or as an admin.
