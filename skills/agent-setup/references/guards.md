# Permission rules and guard hooks

Read on 2026-10-26 from [Claude Code permissions](https://code.claude.com/docs/en/permissions),
[Claude Code hooks](https://code.claude.com/docs/en/hooks),
[Codex rules](https://learn.chatgpt.com/docs/agent-configuration/rules) and the
[Codex config reference](https://learn.chatgpt.com/docs/config-file/config-reference). Check them
again if the agent is newer.

## Contents

- Which to use
- Claude Code rules
- Claude Code guard hook
- Codex rules
- Codex sandbox and approvals
- Not here

## Which to use

- **A rule** when the thing to stop or allow is a command or tool with a recognisable start
  (`git push --force`, `rm -rf`, reading `.env`). Simplest, no script, both agents have one.
- **A guard hook** when the check needs logic: look at arguments anywhere in the command, at the
  file being written, or at the project state. Claude Code runs it before each matching tool call.
- Blocking a command is narrowing (go ahead once tested). Allowing one, or turning off prompts or the
  sandbox, is widening (ask first, hard rule 2).

## Claude Code rules

In `settings.json` under `permissions`, lists `allow`, `ask`, `deny`:

```json
{ "permissions": { "deny": ["Bash(git push --force *)", "Bash(git push -f *)", "Read(./.env)"] } }
```

- Checked in the order deny, ask, allow; the first match wins and an allow can't carve an exception
  out of a deny.
- `*` matches any text. Put it after the subcommand: `Bash(git log *)` is git log only,
  `Bash(git *)` is every git command. A trailing ` *` also matches the bare command.
- Compound commands (`&&`, `||`, `;`, `|`) are split; a deny matches if any part matches, an allow
  must match every part.
- A deny rule covers the form the agent usually writes, not every way to run the program
  (`git -c x=y push --force`, a script, an alias). It is a guard rail, not a security boundary;
  say so to the user.
- List keys merge across user, project and local files. Allow rules in a committed project file wait
  until each person trusts the folder; deny and ask rules apply at once.

## Claude Code guard hook

In `settings.json`:

```json
{ "hooks": { "PreToolUse": [ { "matcher": "Bash",
    "hooks": [ { "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/no-force-push.py" } ] } ] } }
```

For a user-level hook, keep the script in `~/.claude/hooks/` and give its full path.

The script gets the event as JSON on stdin (`tool_name`, `tool_input`, `cwd`, ...). For Bash,
the command is `tool_input.command`.

- Exit **2** blocks the call; what it prints to stderr is the reason the agent sees.
- Exit **0** with no output decides nothing: the normal permission prompt still applies.
- Any other exit (including 1) is a hook error and **the call goes ahead**. A guard must exit 2.
- A hook can't override a deny or ask rule; rules are checked whatever the hook returns.

Sketch, standard-library Python. It splits the command into words, so extra spaces, `git -C dir`
or `git -c k=v` before `push`, and chained commands don't slip past, and it blocks (exit 2) when
it can't read the event rather than letting the call through:

```python
#!/usr/bin/env python3
import json, re, shlex, sys

def force_push(cmd):
    for part in re.split(r"&&|\|\||;|\||\n", cmd):
        try:
            w = shlex.split(part)
        except ValueError:
            w = part.split()
        if "git" not in [x.rsplit("/", 1)[-1] for x in w] or "push" not in w:
            continue
        for a in w[w.index("push") + 1:]:
            if a.startswith("--force") or a.startswith("+") or ":+" in a or \
               (re.fullmatch(r"-[a-zA-Z]+", a) and "f" in a):
                return True
    return False

try:
    cmd = (json.load(sys.stdin).get("tool_input") or {}).get("command") or ""
except Exception:
    print("Guard hook could not read the event; blocked to be safe.", file=sys.stderr)
    sys.exit(2)
if force_push(str(cmd)):
    print("Blocked: force-push. Push normally, or ask the user to do it.", file=sys.stderr)
    sys.exit(2)
sys.exit(0)
```

It still misses a push inside `sh -c "..."`, a script or an alias; say so.

**Test it before it is live**, with an event it must block and one it must let through:

```sh
printf '%s' '{"tool_name":"Bash","tool_input":{"command":"git push --force origin main"}}' | python3 hook.py; echo "exit $?"
printf '%s' '{"tool_name":"Bash","tool_input":{"command":"git push origin main"}}' | python3 hook.py; echo "exit $?"
```

Expect `exit 2` then `exit 0`. Also feed it an event with no `command` field (exit 0) and one that
isn't JSON (exit 2): any other exit code, such as 1 from a crash, lets the call through. Run it the
way the settings will (`python3 hook.py` or the executable path) and make the script executable.

## Codex rules

`.rules` files in `~/.codex/rules/` (user) or `<repo>/.codex/rules/` (project, loaded only when the
project is trusted). Restart Codex after adding one.

```
prefix_rule(
    pattern = ["git", "push", ["--force", "-f", "--force-with-lease"]],
    decision = "forbidden",
    justification = "No force-push; push normally or ask the user.",
    match = [["git", "push", "--force", "origin", "main"]],
    not_match = [["git", "push", "origin", "main"]],
)
```

- `pattern` matches the start of the command's arguments; a list inside it is a set of
  alternatives. A flag that comes later (`git push origin main --force`) is not matched by a prefix;
  add patterns for the common orders or say what is not covered.
- `decision`: `allow` (runs outside the sandbox without asking), `prompt`, or `forbidden`. When
  several match, the strictest wins.
- An `allow` rule is widening: it takes the command out of the sandbox. With `sandbox_mode =
  "workspace-write"`, most commands already run inside the sandbox without asking, so "stop asking
  me about npm test" usually needs no Codex rule at all. Check what actually prompts before adding one.
- `match` and `not_match` are checked when the file loads: write both.
- Test: `CODEX_HOME=<new empty folder> codex execpolicy check --pretty --rules <file> -- git push
  --force origin main`. Without `CODEX_HOME`, Codex writes runtime files into the real `~/.codex`.
  If `codex` isn't installed here, say so and give the user this command.

## Codex sandbox and approvals

In `config.toml`: `sandbox_mode` (`read-only`, `workspace-write`, `danger-full-access`) and
`approval_policy` (`on-request`, `never`, or a granular table). `danger-full-access` or `never` is
widening. Project `.codex/config.toml` loads only for trusted projects.

Codex hooks exist (`features.hooks`, then `hooks.json` or a `hooks` table) but their format differs
from Claude Code's; read the Codex docs before writing one, and prefer a rule for a command block.

## Not here

A hook that makes the agent keep going until something is true (a Stop hook loop), or a job that
runs on a schedule, belongs to the automation skill. A guard only allows, asks or blocks.
