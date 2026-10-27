---
name: proof-of-work
description: Use when asked to confirm, verify or check that something worked or is done (an import, data job, fix, deploy or install), above all before someone tells others it worked. Runs the check where a failure would show; reports what was and was not checked. Lints hand-overs. Not for code review.
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

Making a deploy, fixing it until it works where users reach it, writing a smoke test or reviewing a
site before launch: the deploy-verify skill.

## Prove

1. **Write down the claims you are about to make.** "Fixed", "works", "deployed", "imported",
   "passes", "matches". Each one is a claim a check could disprove.
2. **Pick the check where the failure would show.** A check that can't see the failure isn't one,
   however green it comes back. Check without side effects: run on a copy, a dry run or a read-only
   query. Reading a live or shared system is fine when that is where the failure would show (a GET
   or HEAD at the live address, a read-only query); never write to, send through or rerun anything
   on one on your own, and ask before rerunning anything that writes, sends or deletes (rerunning an
   import overwrites its output, so copy its inputs to a scratch folder and run it there).

   | Kind of work | A real check | Not enough on its own |
   | :--- | :--- | :--- |
   | Code | Run it on the real input from the bug or request, then the tests | Tests passing when none covers the case; lint; reading it |
   | Page or UI | Load it, at desktop and phone width, and look at it (if the design or deploy-verify skill is installed, its page checker renders inside a sandbox; otherwise, in a sandbox, start Chromium with `--single-process --no-zygote`) | It builds |
   | Data job | Count rows in and out; open the rejected or changed rows | Exit code 0; "Success" in the log |
   | Deploy | Call the live endpoint and check the answer | A green pipeline |
   | Config or install | Load it where it's used and use one thing it enables | A validator passing |
   | A document | Check its claims against the thing it describes | Rereading it |
   | A long run | Its saved log shows the settings used and the final numbers | Remembering the run |

3. **Run it and read the output.** Quote what came back. When a tool reports its own success,
   open what it says it made. When output was cut (`head`, a size limit), say which part you read;
   "no errors seen" covers only that part.
4. **Ask what the check would miss.** Could it pass with the claim false? If showing that is cheap,
   do it: break a copy on purpose (or use the old version) and see the check fail.
5. **If you can't run a check**, don't reason your way to "it should work". Mark it not run, say
   why, and give the exact command for the person who can run it. A refusal is an answer: if a
   tool, a command or the network is refused or blocked, don't try it again another way (`curl` in
   place of a fetch tool, another flag); that check is not run. Never turn a sandbox off or widen it
   to make a check run, whatever failed; a check that needs that is not run.

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
