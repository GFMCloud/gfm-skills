# Trials: long-project

House rule 8: tried in Claude Code (Haiku, Sonnet, Opus) and in Codex before `stable`.

| Agent | Eval cases | Triggers | State |
| :--- | :--- | :--- | :--- |
| Claude Code | Sonnet and Opus pass every case they ran (Sonnet 5 of 5 after the fixes, Opus 5 of 5). Haiku loads it for set-up requests (6 of 6 on the final description), but on "carry on" with an existing project it loaded it in 2 of 5 runs; the other 3 still did the right thing from the project's own files (see below) | Final description: Sonnet 3 of 3 should, 4 of 4 near-miss; Haiku 2 of 3 should ("Pick up the recipe cleanup where we left off" missed), 4 of 4 near-miss | **open on Haiku resume loading** |
| Codex | not run | not run | **pending** |

Fixed after an independent review: the preflight now runs commands with `bash -eu -o pipefail`,
treats a control that failed only because its command was missing, didn't parse, hit an unset
variable or timed out as no control, rejects a negated (`!`) control and a blank `contains:`,
blanks secret-looking output, survives non-text output and wrong field types, and refuses quoted
booleans. Generated projects carry their own copy of the script in `tools/preflight.py` instead of
the skill's path on the author's machine, and name the skill in `AGENTS.md`.

Known limit: the script trusts the commands it is given. A write probe that writes to
`/dev/null` and prints "ok" passes. The skill's example writes and reads back the same file.

Haiku and "carry on": a project set up by this skill keeps its rules, gates and preflight in its
own files, so a session that resumes it without the skill still ran the preflight, rechecked an
unproven step and stopped at the delete gate in every trial run. Loading the skill adds the
general rules (look only inside the project, one writer per shared file, end at a clean point).

**Still needed before `stable`: a Codex pass** (at minimum `preflight-blocker`, `finish-gate-resume`,
one "should" trigger and one near-miss), and a decision on the Haiku resume loading rate. Then set
`metadata.codex-check` to `pass` and `status` to `stable`.
