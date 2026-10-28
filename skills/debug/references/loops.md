# Loop recipes

A loop exits non-zero while the fault is there and zero once it is fixed, so it can drive
`git bisect run` and later become the regression test. Keep scripts in `.debug/`; write outputs
there too, never over the project's real output files.

## Wrong or empty output

Run the program's own command on the same input the user used (or a copy of it), with the output
sent to `.debug/`, then check the symptom itself:

```sh
python3 export.py --out .debug/out.csv && test "$(wc -l < .debug/out.csv)" -gt 1
```

When you know a good answer (an earlier commit's output, a hand-checked row), diff against it.
"Exit code 0" is not a check on wrong output.

## Crash or error

Call the smallest piece of code that raises it and check for the error the user saw, not any
error. Run a script in `.debug/` from the project root with the project on the import path (a
folder starting with a dot can't be imported as a test package, so `-m unittest .debug/...` fails):

```sh
PYTHONPATH=. python3 .debug/repro.py
```

If the repro will become the regression test, write it straight into the project's test folder
instead and run it the project's usual way.

## Broke since a date, a commit or "my last change"

1. Find the last good commit: `git log --oneline --since='<date> 00:00'`, or
   `git rev-list -1 --before='<date> 00:00' HEAD`. Give the time: with a bare date git fills in the
   current time of day, which can land after the bad commit.
2. Check the loop really passes there, in a separate worktree:
   `git worktree add .debug/wt <good>` and run the loop with `.debug/wt` as the project.
3. Bisect in that worktree with the loop as the test. Keep the loop script outside the worktree
   (in `.debug/`), since bisect changes every tracked file. The loop runs with the worktree as its
   working folder, so it writes outputs by absolute path or to `../`. Exit 0 good, 1 to 124 bad,
   125 for a commit that can't be tested.

```sh
cd .debug/wt && git bisect start <bad> <good> && git bisect run sh ../loop.sh; git bisect reset
```

Read the first bad commit's whole diff; the cause is often a line the commit message doesn't mention.

## Broke by a change not yet committed

The loop is red in the user's tree and green at `HEAD`: check that with a worktree at `HEAD`
(`git worktree add .debug/wt HEAD`), then read `git diff` (and `git diff --cached`) in the user's
tree for the cause. Don't stash or reset the user's changes to test.

## Intermittent ("fails about one run in five")

1. Measure the rate, so you know when you've changed it:

   ```sh
   fails=0; for i in $(seq 50); do <command> >/dev/null 2>&1 || fails=$((fails+1)); done; echo "$fails/50"
   ```

2. Find what varies between runs and pin it, one thing at a time: random seeds, hash ordering
   (`PYTHONHASHSEED=<n>` in Python), the clock and time zone, test order, parallel workers,
   file-listing order, network calls, state left by an earlier test. When a pinned value fails
   every time, that command is your loop: deterministic and red.
3. Below about one failure in twenty, raise the rate first (more repetitions, run in parallel,
   add load, all on this machine) before you rank hypotheses.

## Slow ("got really slow after my last commit")

1. Same input, same command, at the last good state and now. Time each three times and take the
   middle: `/usr/bin/time -p <command>` (or the shell's own `time` where that isn't installed). Run
   the last good state in a worktree, never by checking it out in the user's tree.
2. Make the loop red on a threshold set from those numbers (fail above three times the good time,
   say), so it turns green when the speed comes back.
3. Check the shape: time at the full input, half and a quarter. Time that quadruples when the
   input doubles points at work repeated per item (a lookup, query or scan inside a loop).
4. Then profile (`python3 -m cProfile -s cumtime <script>`, `EXPLAIN QUERY PLAN` in SQLite, your
   database's `EXPLAIN`, the language's profiler) before changing anything.

## Seen only in production

Reproduce locally from what production captured: a request body, an event, a file, a log line.

- Save the captured input into `.debug/` with secrets replaced by `[REDACTED]`.
- Feed it to the code's own entry point (the handler function, the job's main) on this machine.
  If requests are signed, set a test key in an environment variable and sign the replay with it.
- Never send a replay to the production address, and never call a live payment, email or
  messaging service from a loop.
- If nothing was captured, stop and ask for one redacted example (step 1, "If you can't build
  one").

## Only a person can trigger it

A click in an app, a device, a hardware step. Look for a script first (a headless browser against
a local dev server, a test client, the app's own CLI). If none works, stop and ask for the exact
steps and what the person sees, rather than guessing.
