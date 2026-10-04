# B2B SaaS, product-led

## Who it is for

A software company where people sign up, try the product and often pay by card without talking to
anyone. A small sales-assist team steps in on accounts that show buying signals. Usually a founder or
head of growth, one to five sales-assist reps, and a customer success lead.

## The sales motion

1. A person signs up (free plan or trial). No sales contact. The workspace record is created from product data.
2. The workspace activates, invites teammates and grows. Usage syncs nightly onto the workspace.
3. When usage and company fit meet the PQL rule, or someone asks for sales, a rep accepts the lead and a deal opens.
4. The rep finds who pays and what they need, then quotes seats, plan and billing term. The step that matters is moving a card payer to an invoiced annual contract.
5. After a sales-assisted win, customer success runs an adoption plan. Later, seats used above seats paid, or a plan limit nearly reached, opens an expansion deal.

Self-serve upgrades by card never create a deal.

## Design reasoning

PLG companies have two engines: the product converts most users, and a few humans convert the
accounts the product cannot close alone. The CRM must show usage next to the commercial record or the
reps are blind, so usage lives on a Workspace object synced from the product. The product-qualified
lead is the first stage of the sales-assist pipeline, because a PQL is a lead a rep has accepted, not
a score. Expansion is a separate pipeline because its trigger is usage, not outreach, and its win rate
is far higher than new business. Adoption after the sale gets its own object (principle 8) and exists
only for sales-assisted customers. A company can have several workspaces, and one human can sit in
several, so those links are many-to-one and many-to-many. A person's workspace role is separate from
their buying role, since the user is rarely the payer.

## Design choices

- **Workspace is a custom object**, matched on the product workspace ID, with plan, seats, active users and plan-limit usage.
- **Two deal pipelines**: sales assist (five open stages, starting at product-qualified lead) and expansion (four open).
- **Self-serve stays out of deals.** Card payments update the workspace plan and MRR only.
- **Adoption plan** is a separate delivery object, not stages on the deal.
- **Selects over free text.** PQL trigger, expansion type, billing term and lost reason are all selects.
- **No real company names or data.**

## Objects

| Object | Native | Purpose |
|---|---|---|
| Company | yes | The organisation, with segment and ICP fit |
| Person | yes | A product user, buyer or champion |
| Deal | yes | One sales-assist or expansion opportunity |
| Workspace | custom | One product account and its usage |
| Adoption plan | custom | Post-sale adoption for assisted customers |

## Pipelines

- **Sales assist**: product-qualified lead, conversation, need confirmed, proposal, negotiation, closed won, closed lost.
- **Expansion**: expansion signal, outreach, proposal, negotiation, expanded, declined.

## Decisions

See `decisions` in `design.yaml`: the PQL rule, self-serve staying out of deals, adoption on its own
object, how usage is synced, the custom-object fallback, and which accounts get a human.

## Sensitive data

Product usage is personal data when it names individuals. Sync workspace-level summaries, not user
events. Sign-up does not always give consent for sales outreach, so the marketing consent field gates
outreach. Confirm the lawful basis with the client before switching on sequences.

## Plan-dependent features

- **HubSpot:** custom objects (Workspace, Adoption plan) and pipelines on them may need a higher tier, and custom-object limits may apply. Fallback: the `custom_objects_plan` decision. Hold usage as properties on Company and treat the company as the workspace.
- **Attio:** the number of custom objects may be limited on lower plans. Fallback: build Workspace first and fold the adoption plan into a Deal pipeline.
- **Salesforce:** custom object and field limits depend on edition. Fallback: use Account fields for usage if Workspace cannot be created.
- Nightly usage sync needs an integration or API access, which may be plan-dependent.
- Pipelines on custom objects may not exist everywhere. The fallback is a status select on the object.

Exact tiers: see hubspot/plan-requirements.md once generated.
