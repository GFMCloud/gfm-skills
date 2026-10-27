---
name: doc-vs-reality
description: Checks a document's factual claims (counts, paths, commands, versions, status words) against the files or system it describes, with evidence. Use when asked if a README, spec or status note is still accurate. Not for writing docs or outside-world facts.
metadata:
  status: draft
  codex-check: "pending: not yet tried in Codex triggers; must pass before stable"
---

# Doc vs reality

Turn a document into a list of claims a command could disprove, check each one against the real
thing, and report every mismatch with the evidence.

**Report format (one block per defect, all four fields):**

```
CLAIM:  "three scripts in scripts/"   (quote it exactly)
WHERE:  README.md:12
TRUTH:  two scripts: build.sh, test.sh
CHECK:  ls scripts/
```

End with one line: claims found, claims checked, defects, and claims you could not check.
A clean pass still gets that line.

## Steps

1. **Name the ground truth first.** Prefer what is running (a command and its output), then what
   is on disk (files, `git log`). Another document is not ground truth; it is another claim.
2. **Extract claims, not meaning.** Read once and list every statement a command could disprove,
   with its file and line. Skip opinions and intent. A claim about the outside world (a third-party
   release, a support date, a price) is the research skill's job; hand it over, or do both halves if
   asked for both. The usual suspects:

   | Kind | Looks like | Check with |
   | :--- | :--- | :--- |
   | Counts | "18 files", "nine steps" | list them and count |
   | Every / only / all / none | "each skill has a README" | test every member, not one |
   | Status words | "tested", "verified", "done" | find the evidence it implies |
   | Commands | "run `npm install`" | does the tool and file it needs exist? |
   | Paths and names | files, folders, scripts | does it exist, with that name? |
   | Versions and IDs | versions, commit SHAs, sizes | read the real value |
   | Cross-references | "see section 4", "issue 12" | open the target and compare |
   | Arithmetic | totals, "N of M", percentages | add it up |

3. **Run one check per claim.** Execute it; don't infer it or recall it. If a tool reports its own
   success, check the result yourself at the level where the failure would be.
4. **Say what each check cannot see.** A check can pass because its scope never reached the
   problem: validating a top-level folder misses a broken file one level down, and searching every
   copy of a file finds the right bytes even when the copy in use is stale. If the honest answer to
   "what would this check miss?" is "the thing I'm checking for", it isn't a check. Narrow it.
5. **Classify each defect.**
   - Document is wrong, the thing is right: fix the document (or report it, if you were only asked
     to check).
   - The thing is wrong, the document describes the intent: report it as separate work. Never
     change the thing just to make the document true.
   - Two documents disagree: report both locations; don't pick a winner.

## Where this goes wrong

Extraction is the weak step. Claims dressed as narrative get skipped: "the test ran against this
exact version" is a claim about a specific commit. When a sentence says something *happened* or
*is* a certain way, find the identifier or file it implies and check that.

If you wrote the document yourself in this session, say so in the report; a reader who did not
write it catches more. Where your agent offers a fresh subagent or session, use one for the check.
