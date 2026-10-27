# Trials: long-project

House rule 8: tried in Claude Code (Haiku, Sonnet, Opus) and in Codex before `stable`.

| Agent | Eval cases | Triggers | State |
| :--- | :--- | :--- | :--- |
| Claude Code | Sonnet 5 of 5 and Opus 5 of 5. Haiku: set-up cases 6 of 6 on the final description; "carry on" with an existing project 5 of 5 once the project's `AGENTS.md` starts with the load line (2 of 5 before it) | Sonnet 3 of 3 should, 4 of 4 near-miss. Haiku 4 of 4 near-miss; should: wiki and photo plans loaded, "Pick up the recipe cleanup" 5 of 5 with the load line (1 of 2 on the description alone) | done |
| Codex | not run | not run | **pending** |

## How the Haiku resume misses were fixed

On the description alone, Haiku loaded the skill for set-up requests but often not for "carry on"
or "pick up where we left off" with a project already on disk (3 of 7 runs). Every project this
skill makes now starts its `AGENTS.md` with "Start of every session: if a skill named
`long-project` is available, load it before reading on." Both fixtures that stand for a project
made by the skill have that line, so the two resume prompts now measure the line, not the
description. With it, Haiku loaded the skill in 10 of 10 runs, counted from each run's own report
(its `skills=` line), since Haiku often skips writing RESULT.md; two of the ten (both "pick up"
runs) stopped at the missing recipe folder without writing anything, which is the right outcome.
Three later runs on the final script loaded it as well. The reports themselves were returned to the
trial session and graded there (the planning repo's
`research/r8-trials/haiku-review-long-project/`), not kept in the trial folders. The resume
trigger's fixture has no `recipes/` folder, so that prompt tests loading and the blocker path only,
not the per-item work. The description-only result stays on record above. Every run that did not
load the skill still behaved correctly, because the project's own files carry the gate, the rules
and the preflight.

## Fixed after independent reviews

The preflight runs commands with `bash -eu -o pipefail`; treats a control that failed only because
its command was missing, didn't parse, hit an unset variable or timed out as no control; rejects a
control that uses the common file-changing commands (rm, mv, cp, tee, touch, `sed -i`, a redirect),
a lone `&`, a `!` that inverts a result, a probe that creates its target (`mkdir`), a blank
`contains:`, credentials written into a command, and `unreachable` mixed with probes; judges
evidence on standard output only; blanks secret-looking output; and survives non-text output and
wrong field types. Generated projects carry their own copy of the script in `tools/preflight.py`
instead of the skill's path on the author's machine.

## Known limits

- The script trusts the commands it is given. A write probe that writes to `/dev/null` and prints
  "ok" passes, and so does a control unrelated to its read, or an `if ...; then ...; fi` that
  hides a failure. The skill's example writes and reads
  back the same file.
- A write probe cut off by the timeout can leave its probe file behind; the report says so.
- A control can still change files with a command the script doesn't list; keep controls to plain
  reads.
- `||`, `exit 0` or `&` inside a quoted pattern or URL, and a control whose own output says "syntax
  error", are rejected although harmless. Rewrite the command around them.

## Open items (minor, from the last two reviews; not fixed)

- A control written as `API_TOKEN="" cmd` or `API_TOKEN=wrong cmd` is rejected as a secret;
  `API_TOKEN= cmd` and `env -u API_TOKEN cmd` work. SKILL.md could show the working form.
- `fix` and `covers` text is printed without redaction, so a token pasted there reaches STATE.md.
- `rm -f -r <path>` and `rm <glob>` in a write probe are not caught.
- The not-caught lists don't name `test !`, `[ ! ... ]` or `false` as controls that prove nothing.
- `--allow-shared` placed before the manifest swallows it; the usage could say "manifest first".
- A shared system's control runs before `--allow-shared`, so a "required field left out" control
  reaches the shared server (refused by design) before the user's yes; SKILL.md doesn't say so.
- `ls -ld` reads put the local username into the report and STATE.md.
- A short token printed bare is not redacted; long underscored names are redacted as noise.
- A shared git probe that pushes but fails to delete leaves a probe branch, and the report doesn't
  say so.
- The regression script used in review lives outside the repo; the script's guards have no
  committed test.
- SKILL.md says a sweep's `state/<id>.md` is "the one expected hit" of the placeholder grep; there
  are several.

**Still needed before `stable`: a Codex pass** (at minimum `preflight-blocker`,
`finish-gate-resume`, one "should" trigger and one near-miss). Then set `metadata.codex-check` to
`pass` and `status` to `stable`.
