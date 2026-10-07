# crm-blueprints: instructions for Claude Code

This repo builds and amends client CRMs (Attio, HubSpot, Salesforce) from platform-neutral designs.
Read [README.md](README.md) for the workflow and [skills/crm-builder/SKILL.md](skills/crm-builder/SKILL.md)
for the end-to-end steps. Use British English and short sentences.

## Rules

1. **`design.yaml` is the source of truth.** Never hand-edit generated files (`attio/`, `hubspot/`,
   `salesforce/` inside a blueprint or client folder). Change the design, then regenerate.
2. **Always show the plan before applying.** Run `crm_plan`, show the user the plan (changes by risk,
   and the manual steps), and wait for them to agree.
3. **Never pass `--execute` unless the user explicitly asks for it in this conversation.** Every apply
   starts as a dry run. A general request such as "set up the CRM" is not permission to execute.
4. **Never pass `--production`.** Production runs are done by the engineer at their own keyboard, who
   must type the account name.
5. **Never pass `--allow-review`** unless the user has read the `needs_review` changes and asked for them.
6. **Flag plan-dependent features as decisions.** Custom objects on HubSpot (Enterprise), the
   Salesforce edition, Attio object limits and the like go in the design's `decisions` list with a
   recommended default, and in the client's `notes.md`.
7. **Do not invent stages, fields or objects the client did not describe.** If you add something to
   fill a gap, mark it as an assumption in `clients/<client>/notes.md` under "Assumptions" and say so
   to the user.
8. **Regenerate and validate after every design edit.** Run `validate --strict`, then `generate`.
   Commit the design and its generated output together.
9. **Credentials come only from `.env`** (git-ignored) or the environment. Never read a credential
   into the conversation, a file, a log, a commit or an error message. Never write one into
   `.env.example`. Use sandbox or test accounts for routine work.
10. **Nothing is ever deleted.** Removals of options and stages hide, archive or deactivate them (the data
    is kept) and run only with `--allow-review`. Removals of objects, fields, relationships and pipelines,
    and any change of a field's type, are manual steps. Hand the steps to the user with the data-migration
    instructions; do not do them through the API yourself.
11. **Do not touch raw client data.** `clients/*/raw/` and `clients/*/build/apply-log/` are git-ignored
    because they can hold personal data. Do not commit them or paste them into chat.
12. **Do not use beta or preview APIs.** They are off by default.

## Commands

All run with `uv run`. Add `--help` to any tool.

```bash
uv sync                                                        # install
uv run pytest                                                  # tests, no network
uv run python -m tools.validate --all --strict                 # every blueprint; CI uses this
uv run python -m tools.validate clients/acme/design.yaml --strict
uv run python -m tools.generate --all --check                  # fail if committed output is stale
uv run python -m tools.generate clients/acme/design.yaml       # write platform files and build sheet
uv run python -m tools.new_client <blueprint> <client> --name "Client Ltd"
uv run python -m tools.crm_pull  --platform <attio|hubspot|salesforce> [--out state.json] [--to-design draft.yaml]
uv run python -m tools.crm_plan  clients/acme/design.yaml --platform <p> --out clients/acme/build/plan.json
uv run python -m tools.crm_apply clients/acme/build/plan.json --client acme              # dry run
uv run python -m tools.crm_apply clients/acme/build/plan.json --client acme --execute    # only if asked
uv run python -m tools.crm_drift clients/acme/design.yaml --platform <p>                 # exit 1 = drift
uv run python -m tools.diff_design <old> <new>                 # path or <git ref>:<path>
```

`--target` selects the sandbox or org. Leave it at the default unless the user names one.

## Where things are

- Design format: [model/schema.md](model/schema.md). Core model: `model/core-model.yaml`.
- Blueprints: `blueprints/<name>/` (`design.yaml`, `README.md`, generated platform folders).
- Platform research and gotchas: `platforms/<crm>/README.md` and `platforms/<crm>/reference/`.
  Unresolved questions: `platforms/<crm>/reference/open-questions.md`.
- Safety code: `tools/crm/safety.py` (gates, confirmation, redaction) and `tools/crm/planner.py` (risk).
- Docs: `docs/`. Checklists: `checklists/`. Judgement calls: [DECISIONS.md](DECISIONS.md).

## Working in a client folder

- Edit only `clients/<client>/design.yaml`, `notes.md` and `CHANGELOG.md` by hand.
- Record every amendment in `CHANGELOG.md`, newest first: date, what changed, why, and who asked.
- Before an amendment, run `diff_design` against the last sign-off tag and show the output.
- If the plan has destructive manual steps, show them to the user and stop. Do not work around them.
- If a tool refuses a run, report the refusal as it was printed. Do not look for a flag that gets
  past it.

## Changing the toolkit itself

- A change to the design format goes in `model/schema.md`, `tools/design.py` and `tools/validate.py`
  together, with tests.
- A new judgement call goes in `DECISIONS.md` first.
- Before finishing: `validate --all --strict`, `generate --all --check` and `pytest` all pass.
- Do not edit generated files to fix a generator. Fix the generator and regenerate.
