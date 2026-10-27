# Risky changes

Read this when step 1 sizes a change as risky. The list shows where damage usually hides; it is
not complete. The test stays the same: if this goes wrong, does a test catch it, or does an
alert, a customer or a bill tell you?

## What counts as risky

| Area | Examples |
| :--- | :--- |
| Infrastructure state | Infrastructure-as-code files and their state; moving, importing or removing resources from state; changing how many copies of a resource exist or how they are keyed (re-keying can destroy and recreate them all); deletion-protection flags; provider or module upgrades |
| Access | Access policies and role trust; wildcards in what is allowed or on what; firewall and network rules, above all anything open to the whole internet; storage made public; encryption key policies; sign-in and single sign-on settings |
| Data and schema | Migrations that remove or retype columns or add a required column to a full table; a delete or update whose filter took thought; database engine upgrades; changes to keys or indexes |
| Deletion and retention | Expiry and lifecycle rules, versioning switched off, log retention, backup schedules and pruning, any cleanup script whose success means files are gone |
| Network, DNS and mail | Routing, gateways, peering; DNS records at the domain root, name-server and mail records (the failure is "mail stops" or "the site vanishes"); reverse proxies and certificates |
| Secrets | Anything that reads, writes or rotates secrets; anything that could leak one into state files, logs or command history |
| Self-hosted services | Container volume and mount paths (a changed path quietly starts an empty service instead of failing); always-on service definitions; storage pools, snapshots and disk resizes; the box that runs DNS, the proxy or the backups, which takes everything else down with it |
| Money and people | Billing, payments, pricing; anything that sends messages, invoices or notices to other people |

## Extra checks for a risky plan

- **Which one are you pointed at.** Name the account, environment, workspace, cluster, database or
  machine the investigation read, and how you know (the command that printed it).
- **Show the drift.** Compare what the repo declares with what is running, using the system's own
  read-only commands (a dry-run or "what would change" mode, a describe or list command, the live
  config). Anything running that the repo doesn't know about goes in the Risk section.
- **Count the blast radius from the real system.** List what a delete or expiry would reach today,
  by name or by count, not by estimate. Say what gets replaced (destroyed and recreated) and what
  is changed in place.
- **Undo path.** For each risky step: how to roll it back, how long that takes, and what can't
  come back (deleted data, sent mail, a published record). "No undo" goes in plain words.
- **One risky thing per step.** Don't bundle a deletion with an unrelated change; each risky step
  gets its own gate and its own check.
- **Prefer the reversible route** where one exists: disable before delete, copy before move, a
  dry run before the real run, a short expiry tried on a test prefix before the real one.
