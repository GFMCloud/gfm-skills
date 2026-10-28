---
name: invoice-chaser
description: Accounts receivable assistant for dunning workflows, collections follow-up, AR ageing, payment reminder sequences and receivables management. Helps with invoices.
---

# Invoice chaser

<!-- Demo material for a skill trial, not real. -->

Works from `invoices.csv` in the folder the user names (columns: number, client, email, amount,
due, paid).

1. List every unpaid invoice past its due date, oldest first, with days overdue.
2. For a request to chase or remind: draft one polite reminder email per client, covering all of
   that client's overdue invoices. Save the drafts to `reminders/<client>.md`. The user sends them.
3. For a request about who owes what: a table of clients with the total they owe and the oldest
   due date.
