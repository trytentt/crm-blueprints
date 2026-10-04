# Discovery questions

Ask these before editing a design. Write the answers in `clients/<client>/notes.md` under
"Discovery". Where the client does not know, write "not answered" and, if you proceed, add the
assumption under "Assumptions". Do not fill a gap with a guess presented as a fact.

Which blueprint to start from? Pick the one whose sales motion matches the client's, then use
sections 3 to 5 to see where the client differs. If none fits, start from the closest and say so.

## 1. Business

1. What do you sell, and who buys it? (Company types, sizes, sectors.)
2. How do you win a customer today? From first contact to first money, in the order it happens.
3. Is the work sold once, on repeat, or on a contract that renews? How long is a typical contract?
4. What happens after the sale? Who delivers, using which system, and for how long?
5. What is a typical deal worth? How many do you win in a month? How long do they take?
6. Which numbers do you look at every week to know the business is healthy?
7. Which CRM, spreadsheet or tool do you use now? What do you dislike about it?
8. Which CRM do you want to use, and which plan or edition are you on? (Needed for
   plan-dependent features. See [platform-comparison.md](platform-comparison.md).)
9. Is there a sandbox or test account you can give me to build in first? Who can create one?

## 2. Users

1. Who will use the CRM? Roles and numbers.
2. What does each role need to do in it every day?
3. Who owns an account? Who owns a deal? Can they differ?
4. Who must not see what? (For example finance data, candidate details, client-confidential matters.)
5. Who is the admin who can create API credentials and approve changes?
6. Who signs off the build, and how?

## 3. Data model

1. What are the things you keep records of? List them in the client's own words.
2. Which of those are companies, which are people, and which are neither? (A property, a project,
   an event, a fund, a role.)
3. How do they relate? For each pair: can one A have many Bs? Can one B belong to many As?
4. Can one person be linked to several companies? Can a company have several types of relationship
   with you (customer, supplier, partner)?
5. Do you track groups, such as households or buying committees?
6. Which of these live in another system that stays the record of truth (billing, ERP, planning
   software)? What must the CRM hold and what should it only link to?
7. Is any of the data sensitive: health, financial, personal beyond business contact details,
   regulated? Where must it not be stored? Flag these as decisions.

## 4. Pipelines

For each pipeline the client describes (sales, renewal, delivery, recruitment, tender, lease):

1. What is being moved along it: a deal, a project, a candidate?
2. What are the steps, in the client's words, and what has happened by the time a record enters each one?
   (These become `exit_criteria`: "Entered when ...".)
3. What facts must be known before a record can enter a step? (These become `required_fields`.)
4. At what step do you stop counting a record as a loss? What are the reasons records are lost?
5. How likely is a record to close from each step, roughly? Is that a feeling or measured?
6. Can a record skip a step, go backwards or sit in two pipelines?
7. Are selling and delivery separate pipelines? Who works each?

## 5. Fields

1. What do you need to know about each record to do your job?
2. Which values will you filter, count or report on? (These must be selects.) Give the full list of options.
3. Which fields must always be filled in? When?
4. Which fields are filled by a person, which by an integration or form?
5. Money: one currency or several? Net or gross? Per year, per month?
6. Dates: which ones drive work (renewal date, next step date, start date)?
7. For each field, who reads it and what do they do with it? (This is the `description`.)

## 6. Automation

1. What do people do by hand that should happen on its own? (Create a record, assign an owner, send a notice.)
2. What must trigger a task or an alert? (A stalled deal, an approaching renewal.)
3. Which emails or sequences are sent from the CRM, and which from other tools?
4. Which approvals exist (discounts, terms, conflict checks)? Who approves?
5. Which integrations are needed (email, calendar, billing, product data, forms)?
6. Note that most automations are built by hand on all three platforms. See
   [platform-comparison.md](platform-comparison.md). Say so to the client.

## 7. Migration

1. Where does the current data live, and in what format? How many records of each kind?
2. How clean is it? Duplicates, missing emails, free-text where there should be a list?
3. Which records should come across, and which should be left behind (old, dead, never worked)?
4. Who owns the clean-up, and by when?
5. Is there a cut-over date? Can the old system stay read-only afterwards?
6. Do any records carry consent or regulatory flags that must come across?
7. Who checks the migrated data, and against what?

Next steps: [migration-playbook.md](migration-playbook.md) for moving data, and
[build-sequence.md](build-sequence.md) for the order of work.
