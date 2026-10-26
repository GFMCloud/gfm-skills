---
name: proof-of-work
description: Confirms work is really done, fixed or working by running it where a failure would show, then reports what was checked, what it returned and what was not. Use when asked to confirm or verify that something worked, before saying "done", or to lint a hand-over. Not for code review.
metadata:
  status: draft
  codex-check: "pending: not yet tried in Codex; must pass before stable"
---

# Proof of work

Work is done when a check you ran says so, not when it looks done. This skill has three parts:
**prove** (run the right check), **report** (say what it returned and what it didn't cover), and
**lint** (catch what would break for the reader before the message goes out).

**Every report ends with a `Not checked` list. If everything was checked, write `Not checked: none`
and say why that's true.** A missing list reads as "everything was checked".

## Prove

1. **Write down the claims you are about to make.** "Fixed", "works", "deployed", "imported",
   "passes", "matches". Each one is a claim a check could disprove.
2. **Pick the check where the failure would show.** A check that can't see the failure isn't one,
   however green it comes back.

   | Kind of work | A real check | Not enough on its own |
   | :--- | :--- | :--- |
   | Code | Run it on the real input from the bug or request, then the tests | Tests passing when none covers the case; lint; reading it |
   | Page or UI | Load it, at desktop and phone width, and look at it | It builds |
   | Data job | Count rows in and out; open the rejected or changed rows | Exit code 0; "Success" in the log |
   | Deploy | Call the live endpoint and check the answer | A green pipeline |
   | Config or install | Load it where it's used and use one thing it enables | A validator passing |
   | A document | Check its claims against the thing it describes | Rereading it |
   | A long run | Its saved log shows the settings used and the final numbers | Remembering the run |

3. **Run it and read the output.** Quote what came back. When a tool reports its own success,
   open what it says it made. When output was cut (`head`, a size limit), say which part you read;
   "no errors seen" covers only that part.
4. **Ask what the check would miss.** Could it pass with the claim false? If showing that is cheap,
   do it: break the thing on purpose (or use the old version) and see the check fail.
5. **If you can't run a check**, don't reason your way to "it should work". Mark it not run, say
   why, and give the exact command for the person who can run it.

## Report

One block per claim:

```
CLAIM:   the resize script handles every photo in uploads/
CHECK:   python3 resize.py uploads/ && ls uploads/*.jpg | wc -l && ls thumbs/ | wc -l
RESULT:  40 (uploads) / 37 (thumbs); the 3 missing are .JPG (upper case)
VERDICT: FAILED. Rules out "it ran, so it worked": 3 photos skipped without a message
```

- **CHECK** is the exact command or action, so someone else can rerun it.
- **RESULT** is what came back, quoted and trimmed to the lines that decide it. Count errors, not
  the tool's adjectives ("passed with warnings" with 3 errors is 3 errors).
- **VERDICT** is `VERIFIED`, `FAILED` or `NOT RUN`, plus what it rules out.
- Name what it ran against: commit, file, row count, URL, time.
- Two fixes measured one at a time don't add up; measure them together or report them apart.

Then the `Not checked` list: each item with the reason, and who can check it. Open with the bottom
line (done or not, and what's left) before the blocks.

## Lint

Before you send a hand-over, instructions or status message, save the draft and run
`python3 scripts/lint_message.py <draft.md>` (or pipe it in with `-`). It flags:

- leftover placeholders (`YOUR_KEY`, `{{name}}`, `<path>`, `TODO`) in commands and text
- a code block whose language doesn't match its contents (Python in a `bash` block)
- commands that depend on the folder they run in with no folder given
- risky commands: `curl ... | sh`, `rm -rf` on an unquoted variable, force pushes, `sudo`,
  `--no-verify`, `chmod 777`
- writes announced instead of done ("I'll push the tag") and elided output ("rest is similar",
  "... unchanged")
- counts with nothing behind them ("fixed 9 files" with no list or command)

Fix every ERROR and run it again; weigh each WARN. The script can't judge whether the message leads
with what the reader must do, or asks for more than one decision. Check those two yourself.
