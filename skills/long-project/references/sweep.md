# Sweep

Many items, one treatment, more than one session can track: "convert every page", "check all
repos", "tag every photo". "Am I done?" becomes a count.

## Files

```text
<project>/
├── AGENTS.md          what this is, rules, how to resume, never-do list
├── CLAUDE.md          one line: @AGENTS.md
├── STATE.md           resume point (template in SKILL.md); Progress points to the counts below
├── preflight.json     systems the work touches
├── MANIFEST.tsv       every item, one row each; frozen before work starts
├── WORKER.md          what to do to one item, and how to prove it's done
├── state/             one file per finished or failed item: <id>.md
└── failures.md        failed items to look at once the sweep is through
```

## MANIFEST.tsv

Columns: `id`, `target` (path, URL or name), `planted` (`yes` on the item planted to fail, else
empty). Build it by running the listing command, never by guessing a count, and record that
command and its row count in `STATE.md`. Then freeze it: a list that grows during the sweep never
honestly reaches zero. New items found later go in a second sweep or a new, recorded version.

**Plant one item that must fail** (a missing file, a malformed input) and mark it. The sweep's
done-check is proven only when that item ends up in `failures.md`. If it comes back "done", the
check is broken, not the item.

## WORKER.md

```markdown
# Worker: one item
Input: one id from MANIFEST.tsv. Touch only the item and state/<id>.md.
1. If state/<id>.md says done, stop: already done.
2. <the treatment>
3. Prove it: <command and what its output must show>
4. Write state/<id>.md: status done or failed, the command, its output.
```

Never write to `MANIFEST.tsv`, `failures.md`, `STATE.md` or another item's state file.

## state/<id>.md

```markdown
id: <id>
status: done | failed
check: <command>
output: <the lines that decide it>
```

## Running it

- **What's left** = ids in `MANIFEST.tsv` minus ids with a state file. Nothing else to track, so a
  crashed session resumes by listing `state/`.
- Do items in batches. Parallel workers each get their own ids; the main session alone writes
  `failures.md` and `STATE.md`, and records the counts (done, failed, left) after each batch.
- A failed item doesn't stop the sweep: its state file says failed with the output, it gets a row
  in `failures.md`, and the sweep moves on. Failures are looked at together at the end.
- Finished means: left is 0, the planted item failed, and every other failure is fixed or listed
  under Left over with an owner.
