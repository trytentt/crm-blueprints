# Monthly data-quality checklist

Run once a month for each live client, and keep a dated copy in `clients/<client>/notes.md`. It takes
about an hour. The aim is to catch drift, decay and misuse before the client notices.

Client: ______________  Platform: ______________  Month: ______________  Checked by: ______________

## 1. Structure drift

- [ ] `uv run python -m tools.crm_drift clients/<client>/design.yaml --platform <p>` has been run.
- [ ] Exit 0, or every difference is explained below.
- [ ] New fields, options or stages added by users in the CRM are listed. For each, decide: add it to the design (with a description) or ask the client to stop using it.
- [ ] Anything in the design that has gone from the CRM is investigated.
- [ ] Any amendments made in the CRM by hand are recorded in `CHANGELOG.md`.

Notes:

## 2. Duplicates

- [ ] People: no two records share an email address. Merge any that do.
- [ ] Companies: no two records share a domain or a company number. Merge any that do.
- [ ] Look for near-duplicates: same name with different spelling or a trailing "Ltd".
- [ ] Count of duplicates found: ____ . Count merged: ____ .

## 3. Completeness

- [ ] Open deals with no amount: ____ .
- [ ] Open deals with no expected close date, or a date in the past: ____ .
- [ ] Open deals with no next step or no next step date: ____ .
- [ ] Open deals with no owner: ____ .
- [ ] People with no email address: ____ .
- [ ] Companies with no domain: ____ .
- [ ] Fields the design lists as required that are empty on open records: ____ .

## 4. Pipeline health

- [ ] Open deals that have sat in one stage longer than the client's usual time: ____ . Ask the owner to move or close them.
- [ ] Deals closed lost with no reason: ____ . Fill them in.
- [ ] Deals closed won with no amount or no follow-on record (subscription, project, matter): ____ .
- [ ] Records moved backwards through stages: look at a sample for a pattern.
- [ ] Any stage that is never used. Raise it with the client as a candidate for removal (a destructive manual step; see [../docs/migration-playbook.md](../docs/migration-playbook.md)).
- [ ] Lost-reason mix: if "other" or one option dominates, the list needs work.

## 5. Field usage

- [ ] For each custom field, the share of records with a value. Fields below about 20 percent on records where they apply: ____ .
- [ ] Select fields: options never used in the last quarter: ____ .
- [ ] Free-text fields where users are typing values that should be a select option.
- [ ] Fields users ask about that do not exist (a sign the design is missing something). Record as requests; do not add them without the client's say.

## 6. Automation and integrations

- [ ] Each automation ran this month and did what it should. Failed runs: ____ .
- [ ] Integrations (email, calendar, billing, forms) are connected and syncing.
- [ ] Any new automation built in the CRM by hand is documented.

## 7. Access and security

- [ ] Leavers are removed and joiners have the right roles.
- [ ] Nobody has more access than they need.
- [ ] Sensitive fields (flagged "DATA PROTECTION", or per the blueprint README) are visible only to agreed roles.
- [ ] API tokens and keys: list those in use. Rotate any older than the client's policy. Remove any not needed.
- [ ] No exports of personal data left on shared drives.

## 8. Platform limits and plan

- [ ] Object, pipeline and custom-property counts against the plan's limits.
- [ ] API usage against allowances (especially HubSpot daily limits and Salesforce API calls).
- [ ] Any platform change notices that touch the build (API version end-of-life, edition changes).

## 9. Report to the client

- [ ] Send a short note: what was checked, what was fixed, what needs their decision.
- [ ] Log decisions in `notes.md` and design changes in `CHANGELOG.md`.
- [ ] Set the date of the next check.

Findings and actions:
