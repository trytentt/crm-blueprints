# Clients

One folder per client engagement, made by `uv run python -m tools.new_client <blueprint> <client>`.

```
clients/<client>/
├── design.yaml     the client's design (source of truth for their CRM)
├── notes.md        discovery answers, decisions, assumptions
├── CHANGELOG.md    every amendment, newest first
└── build/          generated structures, saved plans, apply logs
    └── apply-log/  one redacted JSON file per `crm_apply` run (git-ignored)
```

Git ignores `clients/*/raw/` (raw exports from the client's CRM, which hold personal data) and
`clients/*/build/apply-log/` (apply logs). Never commit either. Logs are redacted, but redaction is
best effort.

Commit `design.yaml`, `notes.md` and `CHANGELOG.md` with every change to the client's design.
