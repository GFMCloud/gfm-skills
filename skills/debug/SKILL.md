---
name: debug
description: 'Finds and fixes the cause of a code fault, running one command that shows the failure before any theory and ending with a regression test. Use for "debug this", "X is broken or empty since Y, find out why and fix it", a flaky test or "it got slow". Not for "did it work?", deploys, plans or reviews.'
metadata:
  status: draft
  codex-check: "pending: not yet tried in Codex; must pass before stable"
---

# Debug

A fault is found by a command that shows it, not by reading code until a theory sounds right.

**The gate: before you name any cause, run one command that shows the user's symptom, and put
it in your reply with its output (secrets redacted), as a line starting `Loop:`.** Reading code to
learn how to run the program is fine before that; reading it to explain the fault is not. No
`Loop:` line, no hypotheses and no fix.

**Every finished run ends with this block, in this order:**

```
Loop: <the command>  (before the fix: <symptom as it showed>; after: <passing result>)
Cause: <what was wrong, and the evidence that proved it>
Hypotheses: <each one you ranked in step 3, in that order: held, or ruled out by what>
Fix: <each file changed, one line each>
Regression test: <test name and file> (failed before the fix, passes after) | none: <why no real seam>
Cleanup: <debug tag> 0 hits; <scratch removed or kept, and where>
Not checked: <what this run could not show, or "none" and why>
```

## Rules that hold throughout

- **Loops run here, on copies.** The loop runs on this machine against local copies of data. When
  the fault shows only on a live or shared system, one read to capture an input there (a log line,
  one GET, one read-only query) is fine; the loop then replays that copy here. Never repeat, load
  or write to a live system, and never call a live payment, email or messaging service. A refused
  tool or network call is final: don't retry it another way.
- **Redact.** Before showing any command, output, log line or captured request, replace secrets
  (keys, tokens, passwords, auth headers, cookies, connection strings) with `[REDACTED]`. Show
  only the lines that show the symptom. Loops read credentials from environment variables, never
  from text written into the command or script. Don't print `.env` or key files to look at them.
- **Leave the user's checkout as you found it, plus the fix.** Scratch files go in `.debug/` in
  the project root. Don't commit unless the user asked. If the working tree has changes you didn't
  make, or you need to check out old commits, use a separate worktree in `.debug/`
  (`git worktree add .debug/wt <commit>`), never `git checkout` or `git bisect` in the user's tree.
- **Fix the fault you were asked about.** Other bugs you notice go under "Also noticed" in the
  report, unfixed.
- **Code changes only.** Editing code and tests in the project is the job. Running anything that
  rewrites stored data (a migration, a backfill, a clean-up of a real database) needs the user's
  yes first; planning such a change is the planning skill's job.
- **Asked only what is wrong** ("what's broken?", "why does it fail?"): stop after step 4 and
  report with the `Loop:`, `Cause:` and `Hypotheses:` lines, then offer the fix.

## 1. Build the loop

The loop is one command that goes red on this symptom and green once it is fixed. It must:

- **show the symptom the user reported**, not just "it ran" or "no error" (an empty CSV needs a
  check on the row count, not an exit code);
- **give the same answer every run**, or for an intermittent fault a measured failure rate;
- **take seconds**, and run with no person in the loop.

Pick the cheapest that fits, from `references/loops.md` (recipes for wrong output, crashes,
"broke since X" or an uncommitted change, flaky, slow, and faults seen only in production). Write any script to `.debug/`.
Run it, see it go red, and write the `Loop:` line.

**If you can't build one, stop.** Say what you tried (each command and what it showed) and ask
for the one thing that would make a loop: access to where it fails, a captured input or log
(redacted), the exact steps, or a yes to add temporary logging. Don't offer causes or a fix. If
the user asks for a guess anyway, label it an untested guess.

## 2. Confirm and shrink

1. **Same symptom.** Check the loop fails the way the user described (same wrong output, same
   error, same slowness), not with a nearby failure. Note the exact symptom: the error text, the
   wrong value, the timing.
2. **Shrink.** Cut the input, steps and settings one at a time, rerunning after each cut, until
   removing anything more makes it pass (halve big inputs). The small case narrows the causes and
   becomes the regression test. A fault that needs the full input (a slowdown that grows with
   size) stays full-size; say so.

## 3. Rank 3 to 5 hypotheses

Write them down before testing any (in your reply, or in `.debug/hypotheses.md` when you are
working on your own), most likely first, each with what it predicts. The closing block lists them
again with each result.

> 2. The price cache ignores the currency, so the second lookup gets the first one's price.
>    Predicts: two lookups in one process, GBP then EUR, return the same number; clearing the
>    cache between them turns the loop green.

A hypothesis with no prediction a run could prove wrong is a hunch: sharpen it or drop it. Use
what the user told you ("since yesterday", "after my last commit") to rank, and what the history
shows (`git log` since the last good state). Don't wait for a reply unless the user asked to weigh
in.

## 4. Test them, one change at a time

- Prefer a direct call or a debugger over logs. When you log, tag every line you add with one tag
  for this session, `DBG-` plus four random hex characters (`[DBG-7c1e]`), so cleanup is one grep.
- Put probes at the boundaries that separate your hypotheses. Record each result: held, or ruled
  out by what.
- **Slow:** measure first. Time the loop at the last good state (in a worktree) and now, then profile
  (`python3 -m cProfile -s cumtime`, a query plan, the language's profiler) or bisect the commits;
  no fix before a measurement says where the time goes.
- **Broke since X:** bisect the commits between the last good state and now with the loop as the
  test, in a separate worktree (`git bisect run`), then read the first bad commit's diff.
- If every hypothesis is ruled out, go back to step 2: the loop or the shrunk case may be wrong.
  After a second empty round, report what is ruled out and what you'd try next.

## 5. Fix, with a regression test at a real seam

1. **Find the seam where the fault happens**: the call path the user's symptom took. A test that
   feeds one function hand-built input can pass while the real path fails (the real producer of
   that input has changed shape, or the bug needs two callers and the test has one). If a test
   near the fault already passes, say why it missed the fault.
2. **Write the test first** from the shrunk case and run it: it must fail, for this reason.
3. **Make the smallest change that fixes the cause.** No refactors, renames or tidy-ups. Existing
   tests that encode the old, wrong behaviour are updated to match, and listed under `Fix:`.
4. Run the new test (passes), the project's whole test suite (nothing new fails), and the
   original loop on the full input (green).
5. **No real seam** (the fault only shows with a live service, or the code can't be called below
   the full app): write `Regression test: none` and why. That is a finding to report.

## 6. Clean up

- Remove every tagged line: `grep -rn "DBG-<tag>" .` returns nothing.
- `git bisect reset` if you bisected; `git worktree remove --force .debug/wt` for any worktree you
  added (only your own scratch worktree, never one you didn't make).
- Delete `.debug/` unless the user wants the loop kept; then say where it is.
- `git status` (or a file list) shows only the fix and the tests as changed.

## 7. Report

Bottom line first (one sentence: the cause and that it's fixed), "Also noticed" if any, then the
closing block above. Proving the fix in the real run before telling others is the proof-of-work skill's job; shipping it is deploy-verify's.

## Not this skill

- "Did the import actually work?", checking a claim before telling others: proof-of-work.
- Deploying a fix, or "the deploy didn't take": deploy-verify.
- "Plan how we'd fix it before touching anything": planning (whose plan starts by reproducing the
  fault the same way).
- Reviewing a diff for bugs nobody has reported: a code review.
