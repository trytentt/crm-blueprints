# Design principles

Every blueprint and every client design follows these nine principles. The validator
(`tools.validate`) checks what a machine can check. The rest is for the person editing the design.
The format itself is in [../model/schema.md](../model/schema.md).

## 1. Model the business, not the tool

**Why.** A CRM shaped like the vendor's defaults forces the client to talk in the vendor's terms.
Reports and pipelines then answer questions nobody asked. Objects and stages should match how the
company sells and delivers. The platform mapping comes later and is the generator's job.

**Example.** A recruitment agency places candidates into roles. The design has a `search` object
for each role and a placement pipeline on it. It does not squeeze roles into a Deal field.
See `blueprints/recruitment-agency/`.

**Checked by the validator?** No. This is a judgement. Ask the discovery questions first.

## 2. One human, one record

**Why.** If the same person sits in the CRM twice, activity is split, emails go out twice and
reports count two people. A single Person record, matched by email, keeps one history.

**Example.** A candidate who later becomes a hiring manager stays one Person. A `type` field
(candidate, contact, both) tells the cases apart. Do not add a separate `candidate` object.

**Checked by the validator?** Partly. The core model has one `person` object and design files may not
redefine it.

## 3. Every custom field has a stated use

**Why.** A field nobody can explain gets filled in badly or not at all, and is expensive to remove.
The `description` says what the field is for and who reads it.

**Example.** `renewal_date`: "The day the current subscription ends. Account managers use it to
start renewal conversations 90 days earlier." A description such as "Renewal date" fails the point.

**Checked by the validator?** Yes: a missing description is an error. Whether it is a good one is
for the reviewer.

## 4. Selects over free text for anything reported on

**Why.** If you will filter, count or group by a value, free text will give you "UK", "U.K." and
"United Kingdom". A select gives you one answer per option.

**Example.** `lost_reason` is a select (`no_budget`, `chose_competitor`, `no_decision`), not a
text box. Keep `long_text` for notes nobody will report on.

**Checked by the validator?** Partly: a lost stage must require a select field. Other choices are a
judgement.

## 5. Stages are commitments with exit criteria

**Why.** A stage is a promise that something has happened. "Proposal sent" is a fact. "Warm" is a
feeling. Facts make forecasts honest and let a new starter move a deal without guessing. More than
eight open stages means people cannot tell them apart.

**Example.** `exit_criteria: Entered when the first discovery call has happened.` Every criterion
starts "Entered when" and describes something that can be checked.

**Checked by the validator?** Yes: at most 8 open stages, and each `exit_criteria` starts "Entered when".

## 6. Every pipeline has won and lost stages, and lost requires a reason

**Why.** A pipeline with no end states piles up dead records. A lost deal with no reason teaches
nothing. The reason must be a select so it can be counted.

**Example.** A `closed_lost` stage with `required_fields: [lost_reason]`, where `lost_reason` is a
select. Won stages have probability 100 and lost stages 0.

**Checked by the validator?** Yes: at least one won and one lost stage, the probabilities, and a
select among the lost stage's required fields.

## 7. Gate stages with required fields

**Why.** If a record can move to "Proposal" without a value or a decision maker, the pipeline
reports activity, not progress. Required fields stop a stage being entered without the facts behind it.

**Example.** `proposal` stage: `required_fields: [amount, expected_close_date, economic_buyer]`.

**Platform note.** Salesforce enforces this as a validation rule, which the generator writes.
HubSpot and Attio cannot set it through the API, so the build sheet lists it as a manual step.
The design still states the rule, so the intent is on record.

**Checked by the validator?** Yes: each required field must exist on the pipeline's object.

## 8. Separate selling from delivery

**Why.** A deal answers "will they buy?". Delivery answers "is the work being done and getting paid?".
Mixing them gives deals with odd stages such as "In delivery", and inflates or hides the real
pipeline. Delivery gets its own object and its own pipeline.

**Example.** A consultancy sells on Deal and delivers on a `matter` object, with stages from
conflict check to final invoice. A won deal creates a matter.

**Checked by the validator?** Yes, as a warning. It warns if the design has no custom object and no
decision explaining why, or if a Deal pipeline has delivery-type stages (delivery, kickoff,
fulfilment, implementation). A `decision` whose text mentions "deliver" silences it. Blueprints run
with `--strict`, so a warning fails CI. See DECISIONS D-7.

## 9. Build in order: objects, relationships, pipelines, fields, automations, views, QA

**Why.** Each step needs the one before it. A relationship needs both objects. A stage rule needs
the field it names. A view needs the fields it filters on. Building in order avoids rework and
half-built states.

**Example.** The planner orders changes objects, relationships, pipelines, fields. Build sheets
follow the full order, with decisions first. See [build-sequence.md](build-sequence.md).

**Checked by the validator?** Not by the validator. The planner and the build sheet generator follow
the order, and the planner's tests fail if the order changes.
