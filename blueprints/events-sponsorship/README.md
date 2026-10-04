# Events and sponsorship

## Who it is for

An event organiser, running conferences, trade shows or summits, that makes much of its revenue from
sponsors and exhibitors as well as tickets. A small sales team, an operations team and an event lead.
Ticket sales and attendee registration stay in the ticketing platform and are out of scope.

## The sales motion

1. **Sponsors** are sold by relationship. A salesperson finds a brand with budget and an interest in the
   audience, meets the marketing lead to learn the goals, then sends a proposal built around them (tier,
   speaking slot, branding). Negotiation and a contract follow.
2. **Exhibitors** are sold more like inventory. An enquiry, a conversation about stand size and goals, a
   stand held for a few days at a stated price, then a booking form and a deposit. Buyers are usually
   sales or events people rather than marketing.
3. After signature the operations team delivers: asset deadlines, passes, stand allocation, speaking
   slots, on-site support.
4. After the event a wrap-up report goes to each partner and the renewal conversation for the next
   edition begins.

## Design choices

- **Two pipelines on Deal.** Sponsor sales (five open stages) and exhibitor sales (four). They have
  different stages and buyers but share one revenue report per event.
- **Event is an object.** One record per edition holds dates, targets and total stand space. Every deal links to one.
- **Package is the inventory.** Tiers, stand blocks and add-ons have a price and a quantity, so sell-through
  and availability are visible.
- **Fulfilment is the delivery object** (principle 8). It holds assets, passes, stand number and renewal
  intent, and is owned by operations. Both pipelines end at signed or confirmed.
- **Gates.** A proposal needs a tier and amount. Exhibitor confirmed needs a signed date and deposit.
- **Renewals.** Past participants are a company status and a deal checkbox, and finishing an event
  starts next-edition deals for those who will renew or are undecided.

## Objects

| Object | Native | Purpose |
|---|---|---|
| Company | yes | Sponsor, exhibitor, agency or media partner |
| Person | yes | Marketing lead, event manager, signatory |
| Deal | yes | One sponsor or exhibitor sale |
| Event | custom | One edition of an event |
| Package | custom | Sponsor tier, stand space or add-on for sale |
| Fulfilment | custom | Delivery of what one partner bought |

## Pipelines

- **Sponsor sales** (deal): prospect, meeting held, proposal sent, negotiating, contract out, signed, closed lost.
- **Exhibitor sales** (deal): enquiry, qualified, space held, contract sent, confirmed, closed lost.

## Design reasoning

Event revenue is sold against a fixed date and finite inventory, so the design models both: the event
gives the deadline and the target, and packages give the stock. Sponsors buy visibility and want proof of
return, so goals are captured early and drive the proposal and the wrap-up report. Exhibitors buy
a place to meet buyers and move faster once space is held, so that stage has a clock. A booking is
only worth what is delivered and renewed, which is why fulfilment is separate and why the renewal conversation
starts from the delivery record. This reasoning is from general knowledge of how event organisers sell
sponsorship and stands, not cited sources, and should be checked in discovery.

## Decisions

See `decisions` in `design.yaml`. In short: delivery on a fulfilment object, two pipelines on one object,
one event record per edition, renewals as new deals on the next edition, a fallback if custom objects are
unavailable, and category exclusivity checked by hand.

## Plan-dependent features

- **Custom objects** (event, package, fulfilment). Attio limits the number of objects on some plans, and
  HubSpot may need a higher tier for custom objects. Fallback: the `custom_objects_plan` decision, event
  and package details held on the deal, with fulfilment as a task checklist.
- **Several deal pipelines.** The number of pipelines per object may depend on plan tier. Fallback: one
  pipeline with a deal type select, and stage gates recorded as checks in the build sheet.
- **Required fields per stage and automations.** These may depend on plan tier. Fallback: record them
  as manual steps in the build sheet.

Exact tiers: see hubspot/plan-requirements.md once generated.
