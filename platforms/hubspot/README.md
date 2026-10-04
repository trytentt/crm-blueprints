# HubSpot: practical summary

Research last verified 2026-10-04. Detail and sources are in `reference/`. Plan requirements are generated later from these notes.

## What can be automated

- Property groups, properties (all 14 canonical types, some lossy), select options.
- Custom object schemas (Enterprise only), with display, search and required properties.
- Pipelines and stages for deals and custom objects, including deal probability.
- Association labels (single and paired) and association limits (Professional and Enterprise).
- Lists (static and active), pipeline movement rules.

## What stays manual

- **Required fields per stage** (conditional stage properties). UI only.
- **Saved views** on index pages. No API found.
- **Workflows.** The only API is beta; keep off by default.
- **Permissions** (roles, field-level), other than pipeline stage edit permissions.
- Required fields on standard objects (no API setting).
- Anything destructive: type changes, deletes, stage removal.

## Connect

Use a **service key** (Development > Keys > Service keys) with scopes from `reference/auth-and-setup.md`. Fall back to a legacy private app. Both send `Authorization: Bearer <token>` to `https://api.hubapi.com`. Pin one dated API version, `2026-09`, in one constant. Legacy v3/v4 paths are the fallback.

## Test first

A developer test account is free, holds up to 10 per standard account, and carries a 90-day Enterprise trial, so it can test custom objects. Standard sandboxes need Enterprise.

## Gotchas

1. **Custom objects need Enterprise.** Free, Starter and Professional cannot create them. Typical limit: 10 definitions.
2. **Create order matters:** group, then properties, then schema display lists. The primary display, required and searchable properties must already exist.
3. **Names are permanent:** property `name`, custom object `name`, `hasUniqueValue`. Labels of a custom object are also treated as fixed.
4. **Won and lost exist only on deals**, through `metadata.probability` of `"1.0"` or `"0.0"`. Other objects have open or closed only.
5. **Probability and metadata values are strings,** not numbers.
6. **Enumeration values are stored as text.** Multi-select values are joined with semicolons.
7. **Currency, percent, url, email, phone are display hints** over number or string, not real types.
8. **Owner (user) fields** use `externalOptions: true` with `referencedObjectType: OWNER`; the stored value is the owner ID.
9. **Association labels** need Professional or Enterprise; the 10 versus 50 per pair figures disagree between pages. Paired labels return two type IDs, one per direction.
10. **From 2026-09, deleting or replacing an in-use pipeline or stage is blocked by default.** Never pass the bypass flag.
11. **No documented "already exists" error.** Read before write; match on internal names where possible, on label text for association labels.
12. **Rate limits:** 100 calls per 10 seconds on Free and Starter, 190 on Professional and Enterprise. Daily 250,000 to 1,000,000 per account.
13. **Record IDs differ** between a sandbox and production, so seed data cannot be copied by ID.
14. **Custom pipelines are counted across all objects:** 15 on Starter, 100 or 350 on Professional, 350 on Enterprise.

## Open questions to settle first

See `reference/open-questions.md`. The ones that change code: OQ-1 (closed stages on custom objects), OQ-4 (schema create body), OQ-7 (linking existing objects), OQ-10 (duplicate create response).
