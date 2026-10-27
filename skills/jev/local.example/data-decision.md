# What data may go to TypeSafe

Copy this file to `local/data-decision.md` in the skill folder, or to
`~/.agents/jev/data-decision.md`, and edit it. The jev skill reads the first list item as the
current rule, so add new rules at the top with a date. Without this file the skill assumes public
data only.

- <DATE>: Public data only. I haven't read the provider's data agreement. Email, chat logs,
  transcripts, personal or customer records and anything from a private repo stay on this machine.

To change it: read the agreement, then add a new dated line above the old one saying what is now
allowed (for example "public data and my own private repos; still no personal records").
