# crm-blueprints

An open toolkit for anyone building CRMs for clients: GTM engineers, RevOps consultants and agencies.
It holds ready-made CRM designs for 15 company types, tools that turn a design into platform files,
and tools that read, plan and change a live CRM through its API. The platforms are Attio, HubSpot and
Salesforce.

You, the builder, run it, usually through Claude Code. Your client does not need to.

## How it works

1. A blueprint is a `design.yaml`: objects, fields, relationships, pipelines, stages, decisions,
   automations and views. It does not name a platform. The format is in [model/schema.md](model/schema.md).
2. `tools.generate` turns a design into each platform's own files (API payloads, SFDX metadata), a
   build sheet and a list of manual steps.
3. `tools.crm_plan` compares a design with a live CRM and saves a plan. `tools.crm_apply` applies a
   saved plan. It is a dry run unless told otherwise, and it never deletes anything.
4. `design.yaml` is the source of truth. The platform files and the live CRM follow it.

Judgement calls made while building are in [DECISIONS.md](DECISIONS.md). The brief is in [BRIEF.md](BRIEF.md).

## Blueprints

| Folder | Company type | In one line |
|---|---|---|
| `b2b-saas-sales-led` | Sales-led SaaS, annual contracts | New business and renewals pipelines, with subscription and onboarding records. |
| `b2b-saas-product-led` | Product-led SaaS with sales assist | Workspace usage fields, a product-qualified-lead stage, an expansion pipeline. |
| `agency-marketing` | Marketing, creative and GTM agencies | Engagement records, retainer renewals and a delivery pipeline. |
| `consultancy-professional-services` | Consultancies, law and accountancy firms | Matters, a conflict-check step and a stated billing model. |
| `recruitment-agency` | Contingent and retained recruitment | Searches (roles), candidates as People with a type, a placement pipeline. |
| `executive-search` | Retained executive search | Mandate stages, longlist and shortlist tracking, fee stages. |
| `manufacturing-distribution` | B2B manufacturers and distributors | Quotes and RFQs, account tiers, reorders and repeat business. |
| `wholesale-ecommerce-b2b` | Brands selling wholesale to retailers | Retailer accounts, orders and reorders, territory and rep. |
| `real-estate-commercial` | Commercial property and leasing | Properties, landlord and tenant roles, a lease pipeline. |
| `financial-advisers` | IFAs and wealth managers | Client households, regulated fields flagged for data protection, a review cycle. |
| `investor-vc` | VC and angel deal flow | Deal-flow pipeline, portfolio records, co-investors. |
| `education-training` | Training providers, B2B learning | Programmes and cohorts, an enrolment pipeline. |
| `construction-trades` | Contractors and specialist trades | Projects and sites, a tender and estimate pipeline. |
| `healthcare-clinics-b2b` | Private clinics selling to organisations | Referral partners, services, sensitive-data rules. |
| `events-sponsorship` | Event organisers | Sponsor and exhibitor pipelines, event records. |

Each folder has a `README.md` (who it is for, the sales motion, design choices, plan-dependent
features and fallbacks), a `design.yaml`, and generated `attio/`, `hubspot/` and `salesforce/` folders.

## Layout

```
model/            core model (Company, Person, Deal) and the design file format
blueprints/       one folder per company type
platforms/        research notes per platform, with sources and dates
tools/            validate, generate, the CRM adapters and CLI tools
clients/          one folder per engagement (see clients/README.md)
docs/             principles, discovery questions, naming, migration, comparison, automated builds
checklists/       go-live QA and monthly data quality
skills/           the Claude Code skill for the whole workflow
tests/            pytest; no live calls by default
```

## Quickstart

Needs [uv](https://docs.astral.sh/uv/). The project pins Python 3.12.

```bash
uv sync                                          # install
cp .env.example .env                             # then fill in sandbox credentials; .env is git-ignored
uv run python -m tools.validate --all --strict   # check every blueprint
uv run python -m tools.generate --all --check    # fail if generated files are stale
uv run pytest                                    # tests; no network
```

Every tool runs as `uv run python -m tools.<name>` and accepts `--help`.

## Engagement workflow

Example: a new HubSpot build for a client called Acme, starting from the sales-led SaaS blueprint.
Work in a sandbox or test account until sign-off. Platform notes are in the table below the steps.

| # | Step | Command or action |
|---|---|---|
| 1 | New client | `uv run python -m tools.new_client b2b-saas-sales-led acme --name "Acme Ltd"` |
| 2 | Discovery | Ask the questions in [docs/discovery-questions.md](docs/discovery-questions.md). Write the answers, decisions and assumptions in `clients/acme/notes.md`. |
| 3 | Design | Edit `clients/acme/design.yaml`. Add only what the client described. Label assumptions in `notes.md`. |
| 4 | Validate | `uv run python -m tools.validate clients/acme/design.yaml --strict` |
| 5 | Generate | `uv run python -m tools.generate clients/acme/design.yaml` writes the platform folders next to the design and the build sheet. Add `--platform hubspot` to limit it. |
| 6 | Plan | `uv run python -m tools.crm_pull --platform hubspot --out clients/acme/build/state.json` (optional: see what is there), then `uv run python -m tools.crm_plan clients/acme/design.yaml --platform hubspot --out clients/acme/build/plan.json` |
| 7 | Apply to sandbox | Dry run first: `uv run python -m tools.crm_apply clients/acme/build/plan.json --client acme`. Then, once the plan has been read and agreed: add `--execute`. Add `--allow-review` only for `needs_review` changes someone has read. |
| 8 | QA | Do the manual steps in `manual-steps.md`. Work through [checklists/go-live-qa.md](checklists/go-live-qa.md). Re-plan; the result must be empty. |
| 9 | Sign-off tag | Commit the client folder, then `git tag acme-v1.0 -m "Acme signed off"`. |
| 10 | Amendment | Edit `design.yaml`. `uv run python -m tools.diff_design acme-v1.0:clients/acme/design.yaml clients/acme/design.yaml` shows what changes and its risk. Then validate, generate, plan, apply, as above. Record it in `clients/acme/CHANGELOG.md`. |
| 11 | Drift check | `uv run python -m tools.crm_drift clients/acme/design.yaml --platform hubspot` (exit 0 means no drift). Run it monthly, with [checklists/monthly-data-quality.md](checklists/monthly-data-quality.md). |

Notes on the steps:

- `--target` names the sandbox or org. The default is the sandbox. `--production` exists, but only the
  engineer at the keyboard uses it, after sign-off, and it asks them to type the account name. See
  [docs/automated-builds.md](docs/automated-builds.md).
- A plan has three kinds of change: `safe` (adds), `needs_review` (renames, reorders, hiding options
  or stages) and manual steps. Removals and type changes are never applied. They appear as destructive
  manual steps with data-migration instructions. See [docs/migration-playbook.md](docs/migration-playbook.md).
- Each apply run writes a redacted log to `clients/acme/build/apply-log/`. Logs are git-ignored.
- A sign-off tag marks the design that was signed off. The diff in step 10 reads it with `<tag>:<path>`.

## Platform support

What the tools do for each platform, honestly. Detail is in `platforms/<crm>/README.md` and
[docs/platform-comparison.md](docs/platform-comparison.md).

| | Attio | HubSpot | Salesforce |
|---|---|---|---|
| Generated files | Yes | Yes | <!-- confirm once adapters land --> Generator in progress |
| Read live state, plan, apply | Yes (REST API) | <!-- confirm once adapters land --> In progress (REST API) | <!-- confirm once adapters land --> In progress (`sf` CLI) |
| Objects, fields, options | Automated | Automated | Automated |
| Relationships | Automated | Automated; labels and limits need Professional or Enterprise | Automated (lookup, master-detail, junction) |
| Pipelines and stages | Automated, as a list with a status field | Automated. Won and lost only on deals | Automated on Opportunity; a stage picklist on other objects |
| Required fields per stage | Manual | Manual | Automated, as validation rules |
| Views | Manual (read-only API) | Manual | Automated as list views, without sort |
| Automations | Manual | Manual (workflow API is beta) | Manual |
| Permissions | Manual | Manual | Field access by permission set; assignment manual |
| Sandbox | **None.** Use a separate workspace | Developer test account; standard sandbox needs Enterprise | Sandbox or Developer Edition org |
| Plan or edition needed | Object limits depend on plan | **Custom objects need Enterprise** | **Deploys need Enterprise, Unlimited, Performance or Developer edition** |

Points to know before quoting a client:

- **Salesforce:** the Metadata API works only on Enterprise, Unlimited, Performance and Developer
  editions. Professional and Essentials clients get the build sheet and a manual build.
- **HubSpot:** custom objects need Enterprise. A design that needs them falls back to Deal pipelines or
  a higher plan; each blueprint README says which. Required fields per stage are set by hand in the UI.
- **Attio:** there is no sandbox. Testing happens in a separate workspace the engineer names in
  `ATTIO_TARGET`; the tool cannot tell a test workspace from a live one. Workflows, views, stage
  probability and won/lost flags cannot be created through the API.
- **All three:** automations and saved views are mostly manual. Every build ends with a
  `manual-steps.md` that lists them with UI paths.

## Safety in one paragraph

Nothing changes a CRM unless `--execute` is passed. Production needs `--execute --production` and a
typed account name. The tools never delete or archive anything and never change a field type in place.
Credentials come only from environment variables. The nine rules and where each is enforced are in
[docs/automated-builds.md](docs/automated-builds.md).

## Licence

<!-- owner to choose licence -->
No licence has been chosen yet.
