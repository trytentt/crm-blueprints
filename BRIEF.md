<!-- The build brief for this repository, as given by David on 2026-10-04 (verbatim below the line).
     Every phase is built against this file. Where the build deviates, the reason is in DECISIONS.md. -->

# Prompt: build the `crm-blueprints` repository

You are building a private GitHub repository called **`crm-blueprints`** for a GTM engineering agency. The repository will hold ready-to-build CRM structures for **Attio, HubSpot and Salesforce**, for **many types of company**, plus the tools to build and amend those CRMs through each platform's API using Claude Code.

Work through this brief end to end. Do not stop to ask for confirmation between phases unless you hit a blocker listed in "When to stop and ask". Commit after each phase.

## 1. What the finished repo must do

A GTM engineer opens this repo in Claude Code and says, for example, "Set up a HubSpot CRM for a recruitment agency" or "Add a renewals pipeline to Acme's Attio". The repo must let Claude:

1. Pick the right **company-type blueprint** (e.g. recruitment, B2B SaaS).
2. Produce the **platform-specific structure** for that blueprint: every object, field, relationship, pipeline, stage, stage rule, view and automation, in the exact format that platform's API or metadata tooling accepts.
3. **Build** it in the client's CRM (sandbox first) through the API, showing a plan before making changes.
4. **Amend** an existing CRM: change the design, see exactly what will change, apply only that.
5. **Read** an existing CRM and compare it with the design.
6. List everything the API can't do as **manual steps** with UI paths.

## 2. Sources: the vendor documentation

Research the official documentation before writing any platform structure or code:

| Platform | Start here |
|---|---|
| Salesforce | https://developer.salesforce.com/docs |
| HubSpot | https://developers.hubspot.com/docs |
| Attio | https://docs.attio.com/docs/overview |

Rules:
- **Fetch and read the pages. Do not rely on memory.** APIs change; your training data may be out of date.
- **Cite sources.** Every reference doc and every function that calls an API lists the URL(s) it relies on and the date checked.
- **Write in your own words.** Summarise with short examples; don't paste large sections of vendor docs.
- **Log uncertainty.** Anything ambiguous, missing or plan-dependent goes in `platforms/<crm>/reference/open-questions.md` with what you found and how you've handled it.
- **Stable APIs only by default.** Beta or preview features go behind a flag that is off by default.

## 3. Repository structure to create

```
crm-blueprints/
├── README.md                      how the repo works, quickstart, engagement workflow
├── CLAUDE.md                      instructions Claude Code follows in this repo
├── .env.example                   every credential/target variable, with scopes needed
├── .gitignore                     .env, raw client exports, logs with personal data
├── model/
│   ├── core-model.yaml            platform-agnostic core: Company, Person, Deal
│   └── schema.md                  the design file format, every key explained
├── blueprints/                    one folder per company type (section 5)
│   └── <company-type>/
│       ├── design.yaml            the platform-agnostic design (source of truth)
│       ├── README.md              who it's for, the sales motion, design choices, decisions
│       ├── attio/                 platform structure (section 6)
│       ├── hubspot/
│       └── salesforce/
├── platforms/
│   └── <crm>/
│       ├── README.md              summary build notes and gotchas
│       └── reference/             research notes (section 4)
├── tools/
│   ├── validate.py                validates any design.yaml
│   ├── generate.py                design.yaml → platform structure + build sheet
│   ├── crm/                       base interface + attio.py, hubspot.py, salesforce.py
│   ├── crm_pull.py                read live CRM state
│   ├── crm_plan.py                design vs live → reviewable plan
│   ├── crm_apply.py               apply a saved plan (dry run by default)
│   ├── crm_drift.py               report design vs live differences
│   ├── diff_design.py             compare two versions of a design
│   └── new_client.py              start a client workspace from a blueprint
├── clients/                       one folder per client engagement (empty + README)
├── docs/                          principles, discovery questions, naming, migration, platform comparison, automated builds
├── checklists/                    go-live QA, monthly data quality
├── skills/crm-builder/SKILL.md    Claude Code skill for the whole workflow
├── tests/                         pytest, with recorded API fixtures
└── .github/workflows/ci.yml       validate all blueprints, run tests
```

## 4. Phase 1: platform research

For each platform, write these files in `platforms/<crm>/reference/`, each starting with `> Sources:` and `> Last verified: YYYY-MM-DD`:

| File | Must cover |
|---|---|
| `auth-and-setup.md` | Credential types for agency work on client accounts; scopes for read-only vs build; step-by-step credential creation; sandbox/test environments; API version pinning |
| `objects.md` | Standard objects; custom object creation; limits; plan requirements |
| `fields.md` | Every field/attribute/property type; mapping to our canonical types; naming rules; what can't change after creation |
| `relationships.md` | How links are created; cardinality; labels/roles; many-to-many |
| `pipelines.md` | Pipelines and stages; won/lost representation; probabilities; required fields per stage |
| `views-and-lists.md` | Saved views, lists, list views: what's creatable via API |
| `automation.md` | What automation can be created via API, and the manual alternative |
| `limits-and-errors.md` | Rate limits; retry/backoff; error formats; detecting "already exists" for idempotency |
| `api-coverage.md` | Table: every design concept → automated (endpoint/metadata type + URL) or manual (UI path + reason) |
| `open-questions.md` | Ambiguities and proposed handling |

Platform-specific points to confirm in the docs:
- **Attio:** objects, attributes (all types), select and status options, record-reference relationships (reverse side, cardinality), lists, records/upsert by matching attribute, whether workflows are API-creatable.
- **HubSpot:** custom object schemas and plan requirements, properties and property groups, pipelines and stage metadata, associations (types, labels, limits), whether required-properties-per-stage is API-configurable, private app vs OAuth scopes, sandboxes and developer test accounts.
- **Salesforce:** use **Salesforce DX source-format metadata deployed with the `sf` CLI** (validate this choice against the docs). Cover CustomObject, CustomField (incl. Lookup, MasterDetail), picklist value sets, the OpportunityStage StandardValueSet, BusinessProcess, RecordType, ValidationRule, PathAssistant, ListView, PermissionSet (field visibility), record-triggered Flow, junction objects, check-only deploys, retrieve/describe for reading state, and lead-conversion field mapping.

Then write `platforms/<crm>/README.md` (a short practical summary) and `docs/platform-comparison.md` from what you found.

## 5. Phase 2: core model and company-type blueprints

### 5.1 Design format

Create `model/core-model.yaml` (Company, Person, Deal with core fields and native relationships) and a design format documented in `model/schema.md`. Each design supports:

- `extends` (the core model), `name`, `description`
- `add_objects`, `add_fields`, `add_relationships` (from, to, cardinality, both side labels, purpose)
- `pipelines` (object, name, stages with `type` open/won/lost, `probability`, `exit_criteria` written as "entered when…", `required_fields`)
- `decisions` (open question + recommended default)
- `automations` (name, trigger, action), `views` (name, object, filter, sort)
- optional `platform_overrides` per platform (e.g. HubSpot property group, Salesforce record type)
- canonical field types: `text, long_text, select, multi_select, number, currency, percent, date, datetime, checkbox, url, email, phone, user`
- per field: `native` platforms and `native_names` where the field already exists out of the box

### 5.2 Design principles every blueprint must follow

1. Model the business, not the tool. 2. One human, one record. 3. Every custom field has a stated use (description). 4. Selects over free text for anything reported on. 5. Stages are commitments with exit criteria; at most 8 open stages. 6. Every pipeline has won and lost stages; lost requires a reason. 7. Gate stages with required fields. 8. Separate selling (deals) from delivery (its own object). 9. Build order: objects → relationships → pipelines → fields → automations → views → QA.

### 5.3 Company types to build

Create a full blueprint for each. Research how each type actually sells (sales motion, buying roles, typical stages, delivery after the sale) and design accordingly; record your reasoning in the blueprint's `README.md`.

| Blueprint folder | Company type | Must include |
|---|---|---|
| `b2b-saas-sales-led` | Sales-led SaaS, annual contracts | New-business pipeline; renewals/expansion pipeline; subscription object |
| `b2b-saas-product-led` | PLG SaaS with self-serve and sales assist | Workspace/account usage fields; PQL stage; expansion pipeline |
| `agency-marketing` | Marketing / creative / GTM agencies | Engagement object; retainer renewals; delivery pipeline |
| `consultancy-professional-services` | Consultancies, law, accounting | Matter/engagement object; conflict-check step; billing model |
| `recruitment-agency` | Contingent and retained recruitment | Search/role object; candidates as People with type; placement pipeline |
| `executive-search` | Retained search | Mandate stages; longlist/shortlist tracking; fee stages |
| `manufacturing-distribution` | B2B manufacturers, distributors | Quotes/RFQ; account tiers; reorder/repeat business |
| `wholesale-ecommerce-b2b` | Brands selling wholesale to retailers | Retailer accounts; orders/reorders; territory/rep |
| `real-estate-commercial` | Commercial property, leasing | Property object; tenant/landlord roles; lease pipeline |
| `financial-advisers` | IFAs, wealth managers | Client households; regulated fields (flag data protection); review cycle |
| `investor-vc` | VC / angel deal flow | Deal flow pipeline; portfolio object; co-investors |
| `education-training` | Training providers, B2B learning | Programme/cohort object; enrolment pipeline |
| `construction-trades` | Contractors, trades | Project/site object; tender/estimate pipeline |
| `healthcare-clinics-b2b` | Private clinics, B2B health services | Referral partners; services; flag sensitive data rules |
| `events-sponsorship` | Event organisers | Sponsor and exhibitor pipelines; event object |

Each `design.yaml` must validate with zero errors and zero warnings, include at least 3 `decisions`, 3 `automations` and 3 `views`, and use no real company names or data. Note in each README anything that is plan-dependent (e.g. needs HubSpot Enterprise for custom objects) and the fallback.

## 6. Phase 3: platform structures for every blueprint

Write `tools/generate.py` to turn each `design.yaml` into platform structures, then run it for every blueprint × platform and commit the output. For each blueprint:

**`attio/`**
- `objects.json`, `attributes.json`, `relationships.json`, `statuses.json`, `lists.json`: request payloads in the exact shape the Attio API expects (from your research), in creation order
- `build-sheet.md`: human checklist with UI paths and "Done when" per task
- `manual-steps.md`: everything the API can't do

**`hubspot/`**
- `schemas.json` (custom objects), `property-groups.json`, `properties.json`, `pipelines.json`, `associations.json`: API payloads in creation order
- `build-sheet.md`, `manual-steps.md`
- `plan-requirements.md`: features this blueprint needs and the minimum HubSpot tier for each, with sources

**`salesforce/`**
- `force-app/main/default/…`: SFDX source metadata (objects, fields, picklists, OpportunityStage values, business processes, record types, validation rules, paths, list views, a permission set granting field access)
- `sfdx-project.json` and `package.xml`
- `build-sheet.md`, `manual-steps.md`

The generated build sheet follows this order with checkbox tasks and "Done when" lines: decisions → objects & relationships → pipelines & stage rules → fields → automations → views → QA & go-live. Salesforce stage rules include the actual validation rule formulas.

## 7. Phase 4: build and amend tooling

Build the adapters in `tools/crm/` behind one interface:

```python
class Adapter:
    def read_state(self) -> State: ...                  # live objects, fields, relationships, pipelines
    def plan(self, design, state) -> Plan: ...          # ordered Changes + ManualSteps
    def apply(self, plan, *, dry_run=True) -> Result: ...
```

- Attio and HubSpot: REST APIs using the payload formats from Phase 3.
- Salesforce: write metadata into the client's build folder and deploy with `sf project deploy start` (check-only when dry-running); read state with retrieve/describe.
- `Change` records: kind, target, payload, risk (`safe` / `needs_review` / `destructive`), source URL, summary. `ManualStep` records: title, reason, UI path, done-when.
- CLI tools: `crm_pull.py` (with `--to-design` to reverse-engineer a draft design from a live CRM), `crm_plan.py`, `crm_apply.py`, `crm_drift.py`, `diff_design.py`, `new_client.py` (copies a blueprint into `clients/<client>/` with `design.yaml`, `notes.md`, `CHANGELOG.md`, `build/`).
- Dependencies: Python 3.10+, `pyyaml`, `requests`, `pytest`. The Salesforce adapter may call the `sf` CLI.

### Safety rules (enforce in code and test them)

1. Dry run unless `--execute`.
2. Sandbox/test targets by default; production needs `--execute --production` plus an interactive confirmation naming the account or org.
3. Never delete or archive objects, fields, options, stages or records. Removals become `destructive` manual steps with data-migration instructions.
4. Never change a field type in place; produce a manual migration step.
5. Add options and stages automatically; renames, removals and reorders are `needs_review` and need `--allow-review`.
6. Idempotent: re-running a plan is a no-op; re-check live state before each change.
7. Stop on first failure and report applied / failed (with API error) / remaining.
8. Log every apply to `clients/<client>/build/apply-log/` with tokens and personal data redacted.
9. Credentials only from environment variables (`.env`, git-ignored).

## 8. Phase 5: tests and CI

- `pytest`, no live calls by default. Unit tests for type mapping, plan ordering, idempotency (matching state → zero changes), risk classification, manual steps, override validation, and validation of every blueprint.
- API response fixtures based on documented examples (scrubbed).
- Live smoke tests per platform, skipped unless credentials are set: pull → plan `b2b-saas-sales-led` → apply to sandbox → re-plan → assert zero changes.
- CI runs validation for every blueprint, regenerates platform structures and fails if committed output is stale, and runs `pytest`.

## 9. Phase 6: documentation and Claude Code integration

- `README.md`: what the repo is (internal toolkit, no marketing), the blueprint list, quickstart, and the engagement workflow: new client → discovery → design → validate → generate → plan → apply (sandbox) → QA → sign-off tag → amendments via diff/plan/apply → drift checks.
- `CLAUDE.md`: commands; `design.yaml` is the source of truth; always show the plan before applying; **never pass `--execute` unless the user explicitly asks, and never pass `--production`**; flag plan-dependent features as decisions; don't invent stages or fields the client didn't describe, label assumptions.
- `skills/crm-builder/SKILL.md`: the end-to-end workflow, including choosing a blueprint, running discovery (`docs/discovery-questions.md`), editing the design, building, amending and auditing.
- `docs/`: design principles, discovery questions (business, users, data model, pipelines, fields, automation, migration), naming conventions, build sequence, migration playbook, platform comparison, automated builds (how adapters work, safety model, credential setup per platform, worked examples).
- `checklists/`: go-live QA and monthly data quality.

## 10. Phase 7: publish

1. Run the full test suite and validation; fix everything.
2. `git init`, commit with clear messages per phase (if not already).
3. Create the GitHub repo as **private**: `gh repo create crm-blueprints --private --source=. --push`. If `gh` isn't authenticated, stop and tell me the command to run.

## 11. When to stop and ask

- A doc contradicts a safety rule or the design format in a way you can't resolve.
- A core capability (e.g. creating custom objects) isn't available through any documented API on a platform; propose the manual alternative and continue elsewhere while waiting.
- You need credentials for a live test or to publish.

Otherwise keep going, and record judgement calls in `DECISIONS.md` at the repo root.

## 12. Definition of done

- [ ] Reference docs for all three platforms, each with sources and dates; `api-coverage.md` covers every design concept.
- [ ] 15 blueprints, each validating with zero warnings, each with a README.
- [ ] Platform structures generated for all 15 blueprints × 3 platforms, matching documented API/metadata formats.
- [ ] Pull, plan, apply, drift and diff tools working; apply tested against fixtures, and against sandboxes if credentials were provided.
- [ ] Amending a blueprint (add field, add option, add stage, remove field) produces the right changes, with the removal marked destructive.
- [ ] All safety rules enforced and tested.
- [ ] CI green.
- [ ] Docs, `CLAUDE.md` and skill complete.
- [ ] `HANDOFF.md` at the root: what was built, automated vs manual per platform, plan-dependent features, open questions, how it was tested, and recommended next steps.

## 13. Style

British English. Short sentences. snake_case keys, sentence-case labels. Docstrings on public functions. No marketing language.
