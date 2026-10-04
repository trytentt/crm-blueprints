> Sources: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/sfdx_dev.pdf (Salesforce DX Developer Guide v68.0: "Authorization", "Authorize an Org Using the JWT Flow", "Create an External Client App in Your Org", "Salesforce DX Project Configuration", "Enable Source Tracking in Sandboxes", "Select and Enable a Dev Hub Org"); https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/api_meta.pdf (Metadata API Developer Guide v68.0: "Supported Salesforce Editions", "Metadata API Edit Access", "DeployOptions", "Sample package.xml Manifest Files", "Settings"); https://raw.githubusercontent.com/salesforcecli/plugin-auth/main/messages/web.login.md; https://raw.githubusercontent.com/salesforcecli/plugin-auth/main/messages/jwt.grant.md; https://raw.githubusercontent.com/salesforcecli/plugin-auth/main/messages/accesstoken.store.md; https://raw.githubusercontent.com/salesforcecli/plugin-auth/main/messages/sfdxurl.store.md; https://raw.githubusercontent.com/salesforcecli/plugin-org/main/messages/create.sandbox.md; https://raw.githubusercontent.com/salesforcecli/plugin-org/main/messages/create_scratch.md; https://raw.githubusercontent.com/salesforcecli/plugin-org/main/messages/list.metadata.md; https://raw.githubusercontent.com/salesforcecli/plugin-deploy-retrieve/main/messages/deploy.metadata.md; https://raw.githubusercontent.com/salesforcecli/plugin-deploy-retrieve/main/messages/deploy.metadata.validate.md; https://raw.githubusercontent.com/salesforcecli/plugin-deploy-retrieve/main/messages/retrieve.start.md; https://raw.githubusercontent.com/salesforcecli/plugin-deploy-retrieve/main/src/commands/project/deploy/start.ts; https://raw.githubusercontent.com/salesforcecli/plugin-deploy-retrieve/main/src/commands/project/retrieve/start.ts; https://raw.githubusercontent.com/forcedotcom/schemas/main/sfdx-project.schema.json; https://raw.githubusercontent.com/forcedotcom/salesforcedx-templates/main/src/utils/constants.ts and src/templates/project/ (standard Manifest.xml, ScratchDef.json, sfdx-project.json); https://raw.githubusercontent.com/salesforcecli/plugin-limits/main/src/commands/org/list/limits.ts; web search snippets for the build-user permission pair (secondary)
> Last verified: 2026-10-04

# Salesforce auth and setup

The `sf` CLI is not installed on the build machine (DECISIONS D-2). Everything below was read from the CLI's source and message files, not run. Command and flag names are exact as of the files read on 2026-10-04.

## Credentials for agency work

| Method | Command | Use for | Secret handling |
|---|---|---|---|
| Web login (browser) | `sf org login web --alias <alias> --instance-url <url>` | A person at a keyboard. Default for sandboxes. | Tokens go to the CLI's own store under the home directory. Nothing in our `.env`. |
| JWT bearer | `sf org login jwt --client-id <consumer key> --jwt-key-file <path> --username <user> --alias <alias> --instance-url <url>` | Unattended runs and CI. | Private key file path from an environment variable. Never commit the key. |
| Access token | `SF_ACCESS_TOKEN=<token> sf org login access-token --instance-url <url> --no-prompt` | One-off runs when a client hands over a session token. | Token in the environment variable only. Short-lived. |
| SFDX auth URL | `sf org login sfdx-url --sfdx-url-file <file>` | Moving an already authorised org between machines. | The URL holds a refresh token. Treat as a secret. Web-flow orgs only (not JWT). |

Guidance for engagements:

1. Use `sf org login web` for the first sandbox. Always set `--alias client-sandbox`. The adapter takes the alias from an environment variable (`SF_TARGET_ORG` is the CLI's own variable; the repo's `.env.example` should list one alias variable, name to be chosen by the adapter worker).
2. By default the web flow uses Salesforce's global "Salesforce CLI" connected app. The DX guide says the org needs either an external client app (preferred) or a connected app, and the default app works until you need more control (IP ranges, refresh-token timeout). Pass `--client-id <consumer key>` to use the client's own app.
3. JWT needs an external client app with the certificate uploaded, or a connected app if the same login will create scratch orgs or sandboxes (DX guide, JWT section). JWT cannot be used if the org uses high-assurance (stepped-up) authentication.
4. For a sandbox the login URL is `https://<MyDomain>--<SandboxName>.sandbox.my.salesforce.com` (CLI example). For production it is the My Domain URL ending `my.salesforce.com`, not the `lightning.force.com` URL. Setting `sfdcLoginUrl` in `sfdx-project.json` changes the default.
5. Credentials never go in our repo. The CLI keeps them itself. The repo stores only the alias. The adapter must never print `sfdxAuthUrl`, access tokens or key paths (safety rule 9).

### Step by step: first login to a client sandbox

1. Install the CLI (Node-based `@salesforce/cli`; not covered by the pages read).
2. `sf org login web --alias acme-sbx --instance-url https://acme--dev1.sandbox.my.salesforce.com --set-default`
3. A browser opens. The client's admin (or a user they provision) signs in. The user must have the permissions listed below.
4. `sf org display --target-org acme-sbx --json` to confirm the alias, instance URL and API version (command exists in plugin-org; its output was not read).
5. `sf org list limits --target-org acme-sbx --json` to check the API allowance before a run.

### Step by step: JWT for CI

1. Make a private key and a self-signed certificate with OpenSSL (the DX guide gives the commands: RSA 2048, SHA-256, 365 days).
2. In the org: Setup, App Manager, create an external client app (or a connected app). Enable OAuth, upload `server.crt`, add the scopes the guide lists, and approve the user. Note the consumer key.
3. Run `sf org login jwt` as above.
4. Store the key file outside the repo and pass its path through an environment variable.

The DX guide calls external client apps "preferred" and says a connected app is needed only when the same login will create scratch orgs or sandboxes. Whether a given client org still allows connected app creation was not checked. Open question.

## Permissions

A user needs, for any Metadata API use (guide, "Metadata API Edit Access"):

- an edition that supports it (below);
- **API Enabled**;
- **Modify Metadata Through Metadata API Functions**, or **Modify All Data**;
- any permission a metadata type adds (each type's page lists its "Special Access Rules").

The CLI's own help for `org list metadata` and `org list metadata-types` repeats this: "Modify All Data or Modify Metadata Through Metadata API Functions".

| Level | Needs | Can do |
|---|---|---|
| Read state, objects and data only | API Enabled | `sf sobject describe`, `sf sobject list`, `sf data query`. Describe shows only what this user can see, so the user should be able to see every field in the design. |
| Read all metadata | Above, plus Modify Metadata Through Metadata API Functions | `sf project retrieve start`, `sf org list metadata`, `sf project generate manifest --from-org`. The guide gives no read-only metadata permission. Retrieve needs the same permission as deploy. |
| Build | Above, plus **Customize Application** | `sf project deploy start`. The pair "Modify Metadata Through Metadata API Functions" plus "Customize Application" is the one a secondary source gives as the CI deploy identity in place of Modify All Data. The pages read do not list Customize Application by name. Confirm in the first sandbox. |
| Permission sets | Plus **View Setup and Configuration**, and **Manage Profiles and Permission Sets** to change them | The `PermissionSet` page lists these (and Assign Permission Sets, Manage Session Permission Set Activations) for access to the type. |
| Business processes | View Setup and Configuration | `BusinessProcess` page. |
| Flows in production | The "Deploy processes and flows as active" preference | Not a user permission; a Setup preference. |

Build recommendation: a dedicated integration user per client, with a custom profile or permission set holding exactly the rows above. Do not use Modify All Data for build runs, and never use a person's own login for unattended runs.

The Modify Metadata permission is turned on automatically when Deploy Change Sets or Author Apex is selected (guide).

## Editions and environments

From the guide ("Supported Salesforce Editions"): the Metadata API is available only on **Enterprise, Unlimited, Performance and Developer** editions. Professional Edition orgs get Metadata API access only for ISV partner apps that passed AppExchange security review, via an API token. Essentials is not listed. Professional orgs with API access enabled do get the data APIs (the limits sheet lists "Professional Edition with API access enabled"), so describe and query work there, but deploying metadata with our flow does not.

Consequence: for Essentials and Professional clients the build is a manual build. The repo still produces the same plan and the build sheet (open-questions.md, edition handling).

Environments:

| Environment | Use | Notes (DX guide and CLI help) |
|---|---|---|
| Sandbox (Developer, Developer Pro) | Default target for every run | Create with `sf org create sandbox --name <10 chars or fewer> --license-type Developer --target-org <prod alias> --alias <alias>`. Takes time; use `--wait` or `--async`. Source tracking can be enabled in Developer and Developer Pro sandboxes only. |
| Partial Copy, Full sandbox | Rehearsals with data | No source tracking. Full sandbox API allowance is 5,000,000 calls a day. |
| Scratch org | Our own tests of generated output | Needs a Dev Hub (Enterprise, Unlimited or Developer production org with Dev Hub enabled; cannot be enabled in a sandbox). `sf org create scratch --edition enterprise --alias <alias> --target-dev-hub <hub> --duration-days <n>` or with `--definition-file config/project-scratch-def.json`. Expire on their own. |
| Developer Edition | Free personal org for experiments | Signup is on developer.salesforce.com. Supports the Metadata API. 15,000 calls a day. |
| Production | Only after sign-off | Needs `--production` in our tooling plus a typed confirmation (safety rule 2). |

A scratch org definition file for testing generated output (shape from the standard template):

```json
{
  "orgName": "crm-blueprints test",
  "edition": "Enterprise",
  "features": [],
  "settings": {}
}
```

Source tracking: production orgs and scratch orgs created with `--no-track-source` never track. When tracking is on, `sf project deploy start` with no flags deploys only changed local files. We never rely on that: every run names its inputs with `--manifest` or `--source-dir`.

## API version pinning

- The Metadata, DX and Object guides read on 2026-10-04 are all **API version 68.0 (Winter '27)**, last updated 25 September to 2 October 2026.
- The CLI's template default (`DEFAULT_API_VERSION` in `salesforcedx-templates`, read 2026-10-04) is **67.0**.
- An org that has not yet been upgraded to Winter '27 will not accept 68.0. Production upgrades roll out over several weekends.

Decision: pin **67.0** in `sfdx-project.json` (`sourceApiVersion`), in `package.xml` (`<version>`), and in every `sf` call (`--api-version 67.0`). Keep it as one constant in the generator. Raise it when a client org is confirmed on Winter '27 or later. Nothing in this design needs a 68.0 feature.

Notes:

- `sourceApiVersion` is the version the source is written for. The JSON schema lists a default of `48.0`, which is stale. Always set it.
- `sf project deploy start --api-version <v>` overrides the default (the CLI default is "the latest version supported by the CLI"). The `package.xml` `<version>` is also honoured; "use this flag to override the default API version with the API version of your package.xml file".
- A fresh CLI release can move the default version without notice, so never rely on it.
- The deploy command's help lists an org API version config variable (`OrgConfigProperties.ORG_API_VERSION` in `start.ts`). Its exact CLI name was not read, so do not depend on it. Pass `--api-version` instead.

## Project files

### `sfdx-project.json` (minimal)

The schema requires only `packageDirectories`. A source deploy command also requires being run inside a project ("You must run this command from within a project"), so every client build folder holds this file.

```json
{
  "packageDirectories": [
    { "path": "force-app", "default": true }
  ],
  "name": "client-name-crm",
  "namespace": "",
  "sfdcLoginUrl": "https://login.salesforce.com",
  "sourceApiVersion": "67.0"
}
```

Use `https://test.salesforce.com` as `sfdcLoginUrl` for sandbox-first work, or the My Domain URL. Do not add package-specific keys (`packageAliases`, `plugins`, `replacements`).

### `package.xml` for a blueprint

Used with `--manifest`. List members explicitly. Wildcards are unreliable (see the table).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Search__c</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Search__c.Stage__c</members>
        <members>Opportunity.Renewal_date__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Opportunity.Proposal_requires_decision_maker</members>
        <name>ValidationRule</name>
    </types>
    <types>
        <members>Opportunity.Renewals</members>
        <name>BusinessProcess</name>
    </types>
    <types>
        <members>Opportunity.Renewals</members>
        <name>RecordType</name>
    </types>
    <types>
        <members>Opportunity.Open_renewals</members>
        <name>ListView</name>
    </types>
    <types>
        <members>OpportunityStage</members>
        <name>StandardValueSet</name>
    </types>
    <types>
        <members>Segment_values</members>
        <name>GlobalValueSet</name>
    </types>
    <types>
        <members>Renewals_path</members>
        <name>PathAssistant</name>
    </types>
    <types>
        <members>PathAssistant</members>
        <name>Settings</name>
    </types>
    <types>
        <members>Recruitment_blueprint_user</members>
        <name>PermissionSet</name>
    </types>
    <types>
        <members>LeadConvertSettings</members>
        <name>LeadConvertSettings</name>
    </types>
    <version>67.0</version>
</Package>
```

Types and members:

| Type name | Member form | Wildcard (guide) |
|---|---|---|
| `CustomObject` | `Opportunity` (standard) or `Search__c` | `*` returns custom objects only. Standard objects by name only. |
| `CustomField` | `Object.Field__c` | The guide's samples use names. |
| `ValidationRule` | `Object.RuleName` | **Not supported** |
| `BusinessProcess` | `Object.ProcessName` | Only when `RecordType` is also in the manifest |
| `RecordType` | `Object.RecordTypeName` | Supported with a business process |
| `ListView` | `Object.ViewName` | Not stated |
| `StandardValueSet` | `OpportunityStage` (case-sensitive) | **Not supported** |
| `GlobalValueSet` | `Name` (`<Name>__gvs` for sets made at API 57+) | Supported |
| `PathAssistant` | `PathName` | Supported |
| `Settings` | `PathAssistant` (no "Settings" suffix) | Wildcard retrieves all settings |
| `PermissionSet` | `Name` | Supported |
| `LeadConvertSettings` | `LeadConvertSettings` | Unverified |
| `Flow` | `FlowName` | Not read |

Standard `CustomObject` members pull the whole object on retrieve. For deploys from source we name the children instead (`Opportunity.Renewal_date__c`) so only what we generated is touched.

## Commands the adapter uses

All with `--target-org <alias> --api-version 67.0` and run from the client build folder. Flags below are exact (read from `start.ts`, `validate.ts`, `retrieve/start.ts` and the message files).

Check-only (the "dry run"):

```
sf project deploy start --dry-run --manifest package.xml --target-org <alias> --api-version 67.0 --wait 30 --json
```

- `--dry-run`: "Validate deploy and run Apex tests but don't save to the org." This is the flag for the check-only deploy. The Metadata API calls it `checkOnly`.
- `--manifest` (short `-x`), `--source-dir` (`-d`), `--metadata` (`-m`) and `--metadata-dir` are mutually exclusive ways to say what to deploy.
- `--wait` (`-w`) is in minutes; the default is 33. `--async` returns the job ID at once.
- `--test-level`: `NoTestRun`, `RunSpecifiedTests`, `RunLocalTests`, `RunAllTestsInOrg`, `RunRelevantTests` (beta). Leave it out. `NoTestRun` applies only to development environments, and we deploy no Apex.
- `--ignore-warnings`, `--ignore-errors`, `--ignore-conflicts`: never pass any of them. `--ignore-errors` also turns off rollback.
- `--json` for machine output (limits-and-errors.md).

Alternative: `sf project deploy validate`. The CLI says it is "intended to be used on production orgs", requires tests, and returns a job ID that `sf project deploy quick --job-id <id>` deploys later. On a sandbox the CLI help tells you to use `deploy start --dry-run --test-level RunLocalTests` instead. We use `--dry-run`.

Deploy for real:

```
sf project deploy start --manifest package.xml --target-org <alias> --api-version 67.0 --wait 30 --json
```

Preview what would be sent: `sf project deploy preview --manifest package.xml --target-org <alias>` (source-tracked orgs; shows conflicts and ignored files).

Retrieve state (what exists now):

```
sf project retrieve start --manifest package.xml --target-org <alias> --api-version 67.0 --wait 30 --json
sf project retrieve start --metadata CustomObject:Search__c --metadata "ListView:Opportunity.*" --target-org <alias> --json
```

Retrieve flags: `--manifest`, `--metadata`, `--source-dir`, `--package-name`, `--output-dir`, `--target-metadata-dir`, `--unzip`, `--ignore-conflicts` (never), `--api-version`, `--wait`, `--root-type-with-dependencies`.

Describe and list:

```
sf sobject describe --sobject Opportunity --target-org <alias> --json
sf sobject list --sobject custom --target-org <alias> --json
sf org list metadata-types --target-org <alias> --json
sf org list metadata --metadata-type CustomObject --target-org <alias> --json
sf data query --query "SELECT ApiName, IsClosed, IsWon, DefaultProbability FROM OpportunityStage" --target-org <alias> --json
sf project generate manifest --from-org <alias> --metadata CustomObject --name live.xml
```

Notes:

- `sf sobject describe` takes `--use-tooling-api` for Tooling API objects. Output is the standard describe JSON.
- `sf project generate manifest --from-org` builds a manifest from live metadata. It makes many concurrent API calls (the help suggests `SF_LIST_METADATA_BATCH_SIZE`). Use sparingly against client orgs.
- `sf project convert source --output-dir mdapi_out` converts source format to a Metadata API zip layout. `sf project convert mdapi --root-dir <dir>` goes the other way. `sf project deploy start --metadata-dir <dir_or_zip>` deploys metadata format.

## Destructive changes

`--pre-destructive-changes`, `--post-destructive-changes` and `--purge-on-delete` exist, but safety rule 3 forbids deletion. The adapter never passes them. Removals become destructive manual steps.
