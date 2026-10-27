---
name: data-matching
description: Use when asked to match or dedupe records whose names or IDs don't line up exactly (two customer lists, invoices against a supplier list, people listed twice under different spellings). Writes a reusable mapping file and lists every leftover. Not for clean-key joins, charts or spreadsheet edits.
compatibility: The script needs Python 3.9 or later, standard library only. Reads CSV, TSV and XLSX.
metadata:
  status: draft
  codex-check: "pending: not yet tried in Codex; must pass before stable"
---

# Data matching

Decides which records mean the same real thing when a plain join can't: "Brindle & Moss Ltd" and
"BRINDLE AND MOSS LTD", a supplier that renamed, a member who signed up twice. The failures this
skill exists to stop: a match decided by eye or on a cut-off nobody agreed, a similarity score
made up rather than computed, three different people merged through a chain of near-misses,
"N/A" matching "N/A", the hard leftovers reported as "97% matched", answers that live only in the
conversation and get worked out again next month, and personal records leaking.

`<skill>` below means the folder this file is in. Running its script is part of using the skill.

**Start the reply with the script's `Records:` and `Limits:` lines, copied as printed** (step 4).
Without a run, say why on one line: `Records: not run (<reason>)`.

## 1. Look before matching

- Read only the files the user named. Given a folder, list it and pick the record files (`.csv`,
  `.tsv`, `.xlsx`) by name; open nothing else in it.
- See the columns without printing any values:
  `python3 <skill>/scripts/match.py --columns <file> [<file>]`. It gives each column's filled and
  distinct counts, which tells you which columns are unique. Read a few rows only if you still can't
  tell what a column holds.
- An `.xls`, `.numbers` or online sheet: ask for a CSV or XLSX export. Never install a package to read
  one.
- Two files: link them. LEFT is the list being matched (an export, invoices), RIGHT the reference (a
  master list, the accounts system). One file: find the records listed more than once.
- Records pasted into the chat: write them to two small CSV files in the working folder and use the
  script anyway. Scores come from the script, never from your own estimate.

## 2. Say what each column means

| The column holds | Flag | What the script does with it |
| :--- | :--- | :--- |
| The record's own ID (row ref, invoice number) | `--key L=R` | Names records in every output. Default: spreadsheet row number |
| The name to compare | `--name L=R` | Compared after normalising (step 4) |
| One value per thing that is never shared: VAT or tax number, company number, account number | `--id L=R` | Equal values match outright, even if the names differ. Different values never match, even if the names are identical |
| A contact detail: email, phone | `--contact L=R` | Equal values match unless the names clearly differ (then review). Different values say nothing: one person has several, and an office or bookkeeper shares one |
| A fact that never changes for one thing: date of birth | `--must-agree L=R` | Different values keep two records apart. Equal values prove nothing |
| Town, postcode, address, category | leave out | Things move. Use them yourself when explaining a review row |

`L=R` names the column in each file; give one name when both files use it. Repeat `--id` and
`--contact` for more columns. Add `--drop-words ltd,limited,inc,llc,co` for legal endings that never
tell two things apart in this data (keep words like "holdings" or "group" that can), and
`--swap-comma` when names are written "Smith, Ada"; for people, titles go in drop words
(`mr,mrs,ms,dr`). Pick these from the data and say which you used. XLSX date cells are read as
`YYYY-MM-DD`, so they compare with dates typed in a CSV.

## 3. Agree the limits before any fuzzy match

A fuzzy match is applied only against two limits: **accept** (at or above, it is the same thing) and
**reject** (below, it is not). Between them goes to review.

- The user gave limits: `--accept <a> --reject <r> --set-by user`.
- The user gave none: run without limits. Every fuzzy candidate goes to `review.csv` with its score,
  nothing fuzzy is applied, and the run's other rules still do their work. Propose limits: start
  from accept 0.92 and reject 0.75 for names, move one only where the listed scores show a clear
  gap, and never propose accept below 0.85. A pair below reject is reported as not the same, so keep
  reject under any pair you think may be the same. Show the three to five pairs nearest each limit
  and ask the user once to agree. Rerun with `--set-by user` after a yes.
- The user told you to choose: choose from the scores, run with `--set-by agent`, and say so.

## 4. Run it

```
python3 <skill>/scripts/match.py <left> <right> --name company=account_name --key crm_id=account_no \
    --contact contact_email=billing_email --drop-words ltd,limited --out matching
python3 <skill>/scripts/match.py <one file> --name full_name --key member_no --contact email \
    --must-agree date_of_birth --accept 0.9 --reject 0.75 --set-by user --out duplicates
```

The script works down a fixed order for each record and stops at the first rule that settles it:

1. **Identifier or contact detail**, exact after removing case, spaces and (except in emails)
   punctuation. Blank values and placeholders (`N/A`, `n.a.`, `none`, `0`, `000`, `unknown`, `-`)
   never match anything.
2. **Same name after normalising**: accents, case, `&` as "and", punctuation and spacing removed,
   plus your drop words. Records whose `--id` or `--must-agree` values differ are excluded here and
   below.
3. **Known answers** from earlier runs (`--known`, step 7).
4. **Fuzzy**, against the limits. The score is spelling similarity from 0 to 1, the better of the
   names as written and with their words sorted. Two candidates within 0.03 of each other are
   ambiguous and go to review.
5. **Unmatched**, with the reason. Never the most likely answer.

When finding duplicates in one file, a group where some pair links only through other records (A
like B, B like C, A not like C) goes to review as a chain, never merged; a group of three or more
that all match each other is merged but flagged for a look.

It writes into `--out` (default `matching/`) and refuses a folder that already has files: name a new
one per run. Linking writes `mapping.csv`, `review.csv`, `unmatched.csv`, `right-unused.csv` (RIGHT
records nothing matched) and `run.json`; finding duplicates writes `groups.csv`, `review.csv` and
`run.json`. It reads its inputs and never changes them.

## 5. Check before you report

- The `Records:` line must end `(adds up: yes)`. If it says `NO`, stop and report that; don't hand
  over the files.
- Rerun from the original files: `python3 <skill>/scripts/match.py --verify <out>`. Report its line;
  anything but `verify: same output` is not done.
- Read every matched row with a flag, the three fuzzy matches nearest the accept limit, and every
  group of three or more. Say what you read. If one is wrong, don't edit the outputs: mark that pair
  `different` in a copy of `review.csv` (or a row with `left_key,left_name,right_key,decision`) and
  rerun with it as `--known` into a new folder. A pair answer outranks even an identifier match.
- Never delete, merge or rewrite rows in the user's files. If they ask for a cleaned file, write a
  new one beside the original from the merged groups only, and say which rows it dropped.

## 6. Reply

After the `Records:` and `Limits:` lines, using record keys and compared names only (name a column,
never quote its values):

- Matched, by rule (the script's `By rule:` line), and the files written.
- **To review**: every row as key, name, candidate, score and reason. The leftovers are where the
  renames, mergers and shared accounts are, so list them, never just a percentage. Over 20 rows: the
  first 20 and a pointer to `review.csv`.
- **Unmatched**: every record with its reason.
- Flags: identifier matches whose names differ (a rename, or a wrong number), shared mailboxes.
- The proposed limits and your one question, when step 3 needs a yes.
- How to reuse it: next run, pass the filled-in `review.csv` as `--known`, and when linking this
  run's `mapping.csv` too.

## 7. Reusing answers

`--known <file>` (repeatable) takes earlier answers, so a name worked out once never needs working out
again:

- a past `mapping.csv`, or a `review.csv` with its `decision` column filled in (`same` or
  `different`; blank rows are ignored);
- a hand-kept list with columns `alias,canonical[,decision]`, where `canonical` is a RIGHT key (when
  linking) or any group label (when finding duplicates);
- when finding duplicates, a filled `review.csv` (`key_a,key_b,decision`); answers there are about
  pairs of records, so a `different` for duplicates must name both keys.

To make a run repeatable, `run.json` and `--verify` are enough. If the user wants a rerun script in
the project, copy `match.py` into it (for example `tools/match.py`) and call that copy: never write
this skill's own path into a project file, since it breaks on any other machine or agent.

A name-level `different` stops that name matching that record by name or score; an identifier can
still join them. A pair answer (both keys) stops or makes that exact pair, identifiers included. Pair
answers carry the names they were given for, and are ignored if a later export reuses the key for a
record with another name (row numbers do). Nicknames (Bob and Robert), other-language forms (Dafydd and David), abbreviations
(GWP) and old trading names never score high, so they come only from identifiers or known answers.
Suggest adding the ones the user confirms.

## Personal records

Matching is where personal data leaks, so:

- Everything stays on this machine. Never put records into a web search, online tool, API or upload.
  This skill never needs the network.
- Show record keys and the compared name only, in the reply and in any notes. Never print other
  columns (dates of birth, phone numbers, addresses, tax or account numbers) unless the user asks;
  explain a decision by naming the column ("dates of birth differ"), not by quoting values. The
  script's outputs hold keys and names only; `run.json` also records where the input files were,
  relative to the output folder.
- If the working folder is a git repository, say the outputs hold personal data, and don't commit
  them.
- Test or demonstrate with invented records, and label them as invented.

## Where this stops

- Two files that share a clean key (`customer_id` in both) need a plain join, not this skill.
- Checking that an import or load worked (row counts, totals) is the proof-of-work skill's job.
- Charts and summaries of the matched data go to a charting or spreadsheet tool.
- Above a million pairs the script compares only names that share a two-letter word start, and says
  so; a match with no such shared start is not found.
