# Where a job runs

Pick the runner by what the job needs. Platform behaviour changes; the lines marked *(docs, 2026-10)*
were read from the linked page in October 2026. Recheck the page before relying on an edge.

## Contents

- Choosing
- Each runner: what to write, how the user turns it on and off
- Agent steps inside a job

## Choosing

| Needs | Runner | Runs when | Watch out |
| :--- | :--- | :--- | :--- |
| A few checks while the user works, this session only | In-session loop: `/loop` in Claude Code | Only while the session is open and idle | Stops with the session; recurring loops expire after 7 days *(docs, 2026-10, [scheduled tasks](https://code.claude.com/docs/en/scheduled-tasks))*. No catch-up |
| A plain script on this computer | launchd (macOS), a systemd timer (Linux), Task Scheduler (Windows), cron | Computer on and awake | Bare environment (`PATH`, no shell profile, no keychain prompt). cron skips runs missed while asleep; launchd runs a missed calendar job once on wake. cron has no overlap guard |
| Agent judgment, this computer's files, laptop usually on | Claude desktop app scheduled task, or a Codex app automation | App open and computer awake; one late catch-up run on wake *(docs, 2026-10, [desktop tasks](https://code.claude.com/docs/en/desktop-scheduled-tasks))* | A tool needing approval stalls the run until someone answers: click "Run now" once and allow each tool. Hourly at most for custom schedules |
| Agent judgment on a repo, laptop off | Cloud routine (`/schedule` in Claude Code) or a CI schedule | In the cloud, from a fresh clone | No local files. A green run means the session ended, not that the work was done *(docs, 2026-10, [routines](https://code.claude.com/docs/en/routines))*: the job's own report is the success signal. Hourly at most |
| Checks on a repo, no agent needed | CI schedule (for example a GitHub Actions `schedule:` trigger) | In CI, on the default branch | Scheduled CI runs can start late at busy times, and some hosts pause schedules on inactive repos |
| Keep fixing until a check passes | `loop_gate.py` (see `loop.md`): run by hand in the session, as a Stop hook, or in a driver script | Each time the agent tries to finish | A Stop hook that blocks without end gets overridden by the platform; the gate's own budget must stop first |

Default when unsure: a script plus launchd or a systemd timer for local work, a cloud routine for
repo work with the laptop off. Say which and why in the reply.

## Each runner

Write the turn-on and turn-off commands into `install.md`; the user runs them.

**launchd (macOS).** Write `automation/<job>/<reverse-dns-label>.plist` with `ProgramArguments`
(`/bin/bash` and the absolute path of `run.sh`), `StartCalendarInterval` or `StartInterval`,
`StandardOutPath` and `StandardErrorPath` under `state/`, and an `EnvironmentVariables` `PATH`.
Turn on: copy it to `~/Library/LaunchAgents/` and run `launchctl bootstrap gui/$(id -u) <plist>`.
Turn off: `launchctl bootout gui/$(id -u)/<label>` and remove the copy. Is it on:
`launchctl print gui/$(id -u)/<label>`. Check the file with `plutil -lint` (that only reads it).

**systemd timer (Linux).** Write `<job>.service` and `<job>.timer` (with `Persistent=true` if a
missed run should catch up). Turn on: copy both to `~/.config/systemd/user/`, then
`systemctl --user daemon-reload && systemctl --user enable --now <job>.timer`. Turn off:
`systemctl --user disable --now <job>.timer`. Is it on: `systemctl --user list-timers`.

**cron.** Write the one line to add in `install.md`, with absolute paths and output redirected to
`state/cron.log`. Turn on: `crontab -e` and paste it. Turn off: delete the line. On macOS, cron
needs Full Disk Access to read protected folders; prefer launchd there.

**Claude desktop scheduled task.** Write `prompt.md` (the task's instructions) and, in
`install.md`, the values the user enters: name, schedule (a few minutes off the hour), folder,
permission mode, and whether to use a separate worktree per run (yes unless the job must commit to
the working tree). The prompt names `run.sh` and `state/`, says what a late run does, and ends with
writing `state/last-run.txt`. The user creates it in the app; first run with "Run now" while
watching.

**Cloud routine.** Write `prompt.md` and the settings in `install.md` (repo, schedule, network
hosts it needs, connectors). If an outside system triggers it with a payload, the prompt must say
to read the payload and treat it as data. Its report goes to a place the user can see (a repo file
on a branch, an issue comment), since it has no local files.

**CI schedule.** Write the workflow file into `automation/<job>/` (not into `.github/workflows/`):
the user moves it there and pushes. Least permissions (`permissions: contents: read` unless it must
write), secrets from the CI store only.

## Agent steps inside a job

When `run.sh` calls an agent, it must be able to run with nobody there to approve anything.

- **Claude Code:** `claude -p "$(cat automation/<job>/prompt.md)"` with a narrow tool list
  (`--allowedTools` naming each command it may run), a turn cap (`--max-turns`) and a spend cap
  where available (`--max-budget-usd`). Without a permission mode or allowed tools, a headless run
  denies anything that would need approval *(docs, 2026-10, [headless](https://code.claude.com/docs/en/headless))*. Check
  both the exit code and the output: a failure inside the run can print as a result with exit 0.
  A headless run in a folder you didn't write also runs that folder's project hooks; pass
  `--setting-sources user` or run in a clean checkout.
- **Codex:** `codex exec` with `--sandbox workspace-write` (or `read-only` for a report-only job)
  and `--ask-for-approval never`, and `-o state/last-message.md` to keep its final reply
  *(docs, 2026-10, [non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode))*.
- Never use the flags that skip every permission check or sandbox in a scheduled job.
- The agent's reply is not the status. `run.sh` checks the result itself (step 4 of the job) and
  writes the status.
