#!/usr/bin/env python3
"""Hold a fix-until-it-passes loop to a real check, a fixed number of attempts and untouched tests.

Usage:
  python3 loop_gate.py init --check CMD [--budget N] [--guard PATH ...] [--state FILE]
                            [--repo DIR] [--timeout SECONDS]
      Record the check, the budget and a fingerprint of every guarded path, before attempt 1.
  python3 loop_gate.py step [--state FILE] [--repo DIR] [--hook]
      Call after each attempt. Runs the check itself and decides: keep going, passed, or stop.
  python3 loop_gate.py status [--state FILE] [--repo DIR]
      Print where the loop stands. Runs nothing.

Defaults: --state .automation/loop/state.json under --repo (jobs pass
automation/<job>/state/loop.json), --repo the current folder (with --hook and no --repo, the
`cwd` from the hook's input), --budget 3, --timeout 600.

"Changed" ignores the gate's own state folder, every automation/<job>/state/ folder, common build
and coverage folders, and any --ignore PATH given at init (for a check that writes a report file).
Guarded paths that are unreadable count as changed.

What `step` does, in order:
  1. A guarded path (a test file, the check's own script) changed since init: stop, cause
     guard_changed. A check that can be made to pass by editing the check proves nothing.
  2. Nothing in the project changed since the last attempt: the first time, say so and keep going;
     the second time in a row, stop, cause no_progress. Unchanged work does not use up an attempt.
  3. Run the check (bash -o pipefail, in --repo, with the timeout).
     exit 0: PASS.  exit 126 or 127: stop, cause check_broken (the check cannot run, so looping
     cannot help).  Anything else: a failed attempt. On a timeout the check's whole process group
     is killed. Only the last 1 MB of output is kept.
  4. A failed attempt that reaches the budget: stop, cause budget_spent.
On a stop it writes ESCALATION.md next to the state file: the check, every attempt, the last
failing output word for word, and the cause. A stopped or passed loop stays that way; a new
budget is a new `init` (the old state is kept as state.json.<time>).

Exit codes without --hook: 0 PASS, 3 keep going (fix and call step again), 4 stopped (show
ESCALATION.md to the user, then stop), 1 setup error.
With --hook (a Claude Code Stop hook): exit 2 with the reason on stderr keeps the agent working;
exit 0 lets it stop. A stop blocks once more so the agent shows ESCALATION.md, then releases.
Setup errors exit 1, which Claude Code shows but does not block on, so a broken gate can't trap a
session.

What it can't catch: a change outside the guarded paths that games the check (a skipped test in a
new file, a mocked call). Guard every file the check reads to decide. A symlinked folder inside a
guarded folder counts by where it points, not by what is in it. The state file sits in the
project, so an agent that edits it can reset the count; it catches slips, not intent.
Standard library only; Python 3.9 or later.
"""
import argparse
import datetime
import glob
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache",
             ".ruff_cache", ".tox", "dist", "build", ".next", ".automation", "htmlcov", "coverage",
             ".nyc_output", "target"}
MAX_FILES = 50000
TAIL_LINES = 60
TAIL_CHARS = 6000
LINE_MAX = 300
CAPTURE_MAX = 1 << 20  # keep the last 1 MB of a check's output


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


class SetupError(Exception):
    pass


def hash_path(path, skip=frozenset()):
    """Fingerprint a file or a folder tree (names and contents). Missing paths hash as MISSING.
    `skip` holds absolute paths whose contents never count (state, logs, ignored folders)."""
    h = hashlib.sha256()
    if not os.path.lexists(path):
        return "MISSING"
    if os.path.isfile(path):
        h.update(b"F")
        try:
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(1 << 16), b""):
                    h.update(chunk)
        except OSError:
            return "UNREADABLE"
        return h.hexdigest()
    count = 0
    for root, dirs, files in os.walk(path):
        kept = []
        for d in sorted(dirs):
            full = os.path.join(root, d)
            if d in SKIP_DIRS or os.path.abspath(full) in skip:
                continue
            if os.path.islink(full):
                # Not followed (loops); its target path counts, so relinking shows.
                h.update(b"D" + os.path.relpath(full, path).encode("utf-8", errors="replace")
                         + b"->" + os.readlink(full).encode("utf-8", errors="replace") + b"\0")
                continue
            kept.append(d)
        dirs[:] = kept
        for name in sorted(files):
            full = os.path.join(root, name)
            if os.path.abspath(full) in skip:
                continue
            count += 1
            if count > MAX_FILES:
                raise SetupError("more than %d files under %s; pass a smaller --repo" % (MAX_FILES, path))
            h.update(os.path.relpath(full, path).encode("utf-8", errors="replace") + b"\0")
            try:
                if os.path.islink(full):
                    h.update(b"L" + os.readlink(full).encode("utf-8", errors="replace"))
                else:
                    with open(full, "rb") as f:
                        for chunk in iter(lambda: f.read(1 << 16), b""):
                            h.update(chunk)
            except OSError:
                h.update(b"UNREADABLE")
            h.update(b"\0")
    return h.hexdigest()


def skip_set(repo, state_path, ignores):
    """What never counts as progress: the gate's own state folder, every job's state/ folder
    under automation/, and the --ignore paths."""
    skip = {os.path.dirname(os.path.abspath(state_path))}
    skip.update(os.path.abspath(p) for p in glob.glob(os.path.join(repo, "automation", "*", "state")))
    skip.update(os.path.abspath(os.path.join(repo, p)) for p in ignores)
    return frozenset(skip)


def tail(text):
    lines = text.splitlines()
    cut = lines[-TAIL_LINES:]
    out = "\n".join(cut)
    if len(out) > TAIL_CHARS:
        out = out[-TAIL_CHARS:]
    if len(cut) < len(lines) or len(out) < len("\n".join(cut)):
        out = "[last %d lines of %d]\n%s" % (min(len(lines), TAIL_LINES), len(lines), out)
    return out


def load(state_path):
    if not os.path.exists(state_path):
        raise SetupError("no loop state at %s; run `loop_gate.py init --check ...` first" % state_path)
    try:
        with open(state_path, encoding="utf-8") as f:
            state = json.load(f)
    except (OSError, ValueError) as e:
        raise SetupError("loop state %s cannot be read (%s)" % (state_path, e))
    if not isinstance(state, dict) or state.get("loop_gate") != 1:
        raise SetupError("%s is not a loop_gate state file" % state_path)
    return state


def save(state_path, state):
    folder = os.path.dirname(state_path)
    os.makedirs(folder, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".state-", dir=folder)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
        f.write("\n")
    os.replace(tmp, state_path)


def guard_hashes(repo, guards, skip):
    return {g: hash_path(os.path.join(repo, g), skip) for g in guards}


def run_check(cmd, repo, timeout):
    """Run the check in its own process group, output to a temp file (bounded in memory)."""
    with tempfile.TemporaryFile() as buf:
        p = subprocess.Popen(["bash", "-o", "pipefail", "-c", cmd], cwd=repo, stdout=buf,
                             stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                             start_new_session=True)
        timed_out = False
        try:
            code = p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except OSError:
                pass
            p.wait()
            code = 124
        size = buf.seek(0, os.SEEK_END)
        buf.seek(max(0, size - CAPTURE_MAX))
        out = buf.read().decode("utf-8", errors="replace")
        if size > CAPTURE_MAX:
            out = "[output cut to its last %d bytes of %d]\n" % (CAPTURE_MAX, size) + out
    if timed_out:
        out += "\n[check timed out after %ss; its processes were stopped]" % timeout
    return code, out


def write_escalation(state, state_path):
    path = os.path.join(os.path.dirname(state_path), "ESCALATION.md")
    why = {
        "budget_spent": "The check still fails after every attempt the budget allowed.",
        "guard_changed": "A guarded file changed, so a pass would prove nothing. The loop stopped at once.",
        "no_progress": "Two attempts in a row changed nothing in the project.",
        "check_broken": "The check itself cannot run (command missing or not executable), so more attempts cannot help.",
    }[state["cause"]]
    lines = [
        "# Loop stopped: %s" % state["cause"],
        "",
        why,
        "",
        "- Check: `%s` (in `%s`)" % (state["check"], state["repo"]),
        "- Attempts: %d of %d" % (state["attempts_used"], state["budget"]),
        "- Started: %s. Stopped: %s" % (state["started"], state["ended"]),
    ]
    if state.get("guard_changes"):
        lines.append("- Guarded paths changed: %s" % ", ".join("`%s`" % g for g in state["guard_changes"]))
    lines += ["", "## Attempts", "", "| # | Time | Exit | Project fingerprint | Last failing line |",
              "| ---: | :--- | ---: | :--- | :--- |"]
    for a in state["history"]:
        first = a.get("failing_line", "").replace("|", "\\|")[:120]
        lines.append("| %s | %s | %s | %s | %s |" % (a["n"], a["time"], a["exit"], a["fingerprint"][:10], first))
    lines += ["", "## Last check output (word for word)", "", "```", state.get("last_output", "").rstrip(), "```",
              "", "## For the person deciding", "",
              "- Likely cause: (the agent fills this in from the output above, one line)",
              "- Question: (the one decision needed to go on, one line)",
              "- To try again with a new budget, run `loop_gate.py init` again with the same options; "
              "it keeps this state as a dated copy."]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return path


def last_failing_line(out):
    hits = [l.strip() for l in out.splitlines()
            if any(w in l.lower() for w in ("fail", "error", "assert", "not found"))]
    if hits:
        return hits[-1][:LINE_MAX]
    lines = [l for l in out.splitlines() if l.strip()]
    return lines[-1].strip()[:LINE_MAX] if lines else ""


def stop(state, state_path, cause, out=None):
    state["status"] = "stopped"
    state["cause"] = cause
    state["ended"] = now()
    if out is not None:
        state["last_output"] = tail(out)
    state["escalation_shown"] = False
    path = write_escalation(state, state_path)
    save(state_path, state)
    return path


def cmd_init(a):
    repo = os.path.abspath(a.repo or os.getcwd())
    state_path = os.path.abspath(a.state or os.path.join(repo, ".automation", "loop", "state.json"))
    if a.budget < 1:
        raise SetupError("--budget must be at least 1")
    if not a.check.strip():
        raise SetupError("--check must not be empty")
    if any(not g.strip() for g in a.guard + a.ignore):
        raise SetupError("--guard and --ignore paths must not be empty")
    for g in a.guard + a.ignore:
        if os.path.isabs(g) or g.startswith(".."):
            raise SetupError("--guard and --ignore paths are relative to --repo and inside it: %s" % g)
        if g in a.guard and not os.path.exists(os.path.join(repo, g)):
            raise SetupError("guarded path %s does not exist" % g)
    if os.path.exists(state_path):
        keep = state_path + "." + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        shutil.move(state_path, keep)
        print("Kept the previous loop state as %s" % keep)
    state = {
        "loop_gate": 1, "check": a.check, "repo": repo, "budget": a.budget, "timeout": a.timeout,
        "guards": guard_hashes(repo, a.guard, skip_set(repo, state_path, a.ignore)),
        "ignore": a.ignore, "started": now(),
        "status": "running", "attempts_used": 0, "idle_in_a_row": 0, "history": [],
        "last_fingerprint": hash_path(repo, skip_set(repo, state_path, a.ignore)),
    }
    save(state_path, state)
    print("Loop ready: check `%s`, budget %d, guarding %s. State: %s"
          % (a.check, a.budget, ", ".join(a.guard) or "nothing", state_path))
    if not a.guard:
        print("WARN no --guard given: an edit to the tests could make the check pass. "
              "Guard every file the check reads to decide.")
    return 0


def hook_input():
    if sys.stdin is None or sys.stdin.isatty():
        return {}
    try:
        data = sys.stdin.read()
        return json.loads(data) if data.strip() else {}
    except ValueError:
        return {}


def cmd_step(a):
    hook_data = hook_input() if a.hook else {}
    hook_cwd = hook_data.get("cwd") if isinstance(hook_data, dict) else None
    repo = os.path.abspath(a.repo or (hook_cwd if isinstance(hook_cwd, str) else None) or os.getcwd())
    state_path = os.path.abspath(a.state or os.path.join(repo, ".automation", "loop", "state.json"))
    state = load(state_path)
    repo = state["repo"]
    skip = os.path.dirname(state_path)
    esc = os.path.join(skip, "ESCALATION.md")

    def keep_going(msg):
        if a.hook:
            print(msg, file=sys.stderr)
            return 2
        print(msg)
        return 3

    def stopped(msg):
        if a.hook and not state.get("escalation_shown"):
            state["escalation_shown"] = True
            save(state_path, state)
            print(msg + "\nShow the user %s as it is (fill in its two lines at the end), then stop "
                  "working on this loop." % esc, file=sys.stderr)
            return 2
        print(msg)
        return 0 if a.hook else 4

    if state["status"] == "passed":
        print("PASS already recorded at attempt %d; nothing to do." % state["attempts_used"])
        return 0
    if state["status"] == "stopped":
        return stopped("STOPPED (%s) earlier; see %s." % (state["cause"], esc))

    skip_paths = skip_set(repo, state_path, state.get("ignore", []))
    changed = [g for g, h in state["guards"].items() if hash_path(os.path.join(repo, g), skip_paths) != h]
    if changed:
        state["guard_changes"] = changed
        stop(state, state_path, "guard_changed", "Guarded paths changed: " + ", ".join(changed))
        return stopped("STOPPED: guarded path changed (%s). Put it back; don't edit what the check "
                       "reads. See %s." % (", ".join(changed), esc))

    fingerprint = hash_path(repo, skip_paths)
    if fingerprint == state["last_fingerprint"] and state["attempts_used"] > 0:
        state["idle_in_a_row"] += 1
        if state["idle_in_a_row"] >= 2:
            stop(state, state_path, "no_progress")
            return stopped("STOPPED: two attempts in a row changed nothing. See %s." % esc)
        save(state_path, state)
        return keep_going("Nothing in the project changed since attempt %d, and its check failed:\n%s\n"
                          "Change something that addresses the failure, or stop and say why you can't."
                          % (state["attempts_used"], state.get("last_output", "")))

    code, out = run_check(state["check"], repo, state["timeout"])
    state["idle_in_a_row"] = 0
    state["last_fingerprint"] = fingerprint
    if code == 0:
        state["attempts_used"] += 1
        state["status"] = "passed"
        state["ended"] = now()
        state["history"].append({"n": state["attempts_used"], "time": now(), "exit": 0,
                                 "fingerprint": fingerprint, "failing_line": "passed"})
        state["last_output"] = tail(out)
        save(state_path, state)
        print("PASS at attempt %d of %d: `%s`\n%s" % (state["attempts_used"], state["budget"],
                                                   state["check"], tail(out)))
        return 0

    broken = code in (126, 127)
    if broken:
        stop(state, state_path, "check_broken", out)
        return stopped("STOPPED: the check can't run (exit %d). Fix the check command, then init "
                       "again. See %s." % (code, esc))

    state["attempts_used"] += 1
    state["history"].append({"n": state["attempts_used"], "time": now(), "exit": code,
                             "fingerprint": fingerprint, "failing_line": last_failing_line(out)})
    state["last_output"] = tail(out)
    if state["attempts_used"] >= state["budget"]:
        stop(state, state_path, "budget_spent", out)
        return stopped("STOPPED: attempt %d of %d failed; budget spent. See %s."
                       % (state["attempts_used"], state["budget"], esc))
    save(state_path, state)
    return keep_going("Check failed (attempt %d of %d, exit %d): `%s`\n%s\nFix the cause. Don't edit "
                      "guarded files (%s)." % (state["attempts_used"], state["budget"], code,
                                                state["check"], tail(out),
                                                ", ".join(state["guards"]) or "none"))


def cmd_status(a):
    repo = os.path.abspath(a.repo or os.getcwd())
    state_path = os.path.abspath(a.state or os.path.join(repo, ".automation", "loop", "state.json"))
    s = load(state_path)
    print("%s: %d of %d attempts used, check `%s`%s" % (
        s["status"].upper(), s["attempts_used"], s["budget"], s["check"],
        ", cause %s" % s["cause"] if s.get("cause") else ""))
    return 0


def main(argv):
    p = argparse.ArgumentParser(description="Bounded fix-until-it-passes loop gate.")
    sub = p.add_subparsers(dest="cmd")
    i = sub.add_parser("init")
    i.add_argument("--check", required=True)
    i.add_argument("--budget", type=int, default=3)
    i.add_argument("--guard", action="append", default=[])
    i.add_argument("--timeout", type=int, default=600)
    i.add_argument("--ignore", action="append", default=[])
    for sp in (i, sub.add_parser("step"), sub.add_parser("status")):
        sp.add_argument("--state")
        sp.add_argument("--repo")
    sub.choices["step"].add_argument("--hook", action="store_true")
    a = p.parse_args(argv)
    if not a.cmd:
        p.print_help()
        return 1
    try:
        return {"init": cmd_init, "step": cmd_step, "status": cmd_status}[a.cmd](a)
    except SetupError as e:
        print("SETUP ERROR " + str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
