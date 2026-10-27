#!/usr/bin/env python3
"""Prove a real read and a real write to every system a project needs, before work starts.

Usage:
  python3 preflight.py preflight.json                 run every check, print a Markdown report
  python3 preflight.py preflight.json --check         validate the file only; run nothing
  python3 preflight.py preflight.json --allow-shared  also run writes marked "shared" (only after
                                                      the user has said yes to them)

For each system, in this order: the control (must fail), the read, then the write. A write is
skipped when its control did not fail, or when it is shared and --allow-shared was not given.
Every system is tried; all problems print together under BLOCKERS.

Commands run with `bash -eu -o pipefail -c` in the folder that holds the file, so relative paths
are the project's, a failure anywhere in a command or pipeline counts, and an unset variable is an
error rather than an empty path. A control that fails only because its command doesn't exist or
doesn't parse proves nothing, so it is a blocker too.

Exit codes: 0 every system proven, 1 something is not proven (see BLOCKERS), 2 the file was
rejected and nothing ran. Standard library only; Python 3.9 or later.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys

# Constructs that let a command report success without having checked anything.
MASKING = [
    (re.compile(r"\|\|"), "`||` can turn a failure into a success"),
    (re.compile(r";\s*(true|:)\s*($|;|\))"), "`; true` throws away the real exit code"),
    (re.compile(r"&&\s*(true|:)\s*($|;|\))"), "`&& true` hides which command's status counts"),
    (re.compile(r"set\s+\+e"), "`set +e` stops failures from counting"),
    (re.compile(r"\bexit\s+0\b"), "`exit 0` forces success"),
    (re.compile(r"^\s*!"), "a leading `!` turns success into failure"),
]
# Token shapes: a command containing one is rejected (use an environment variable instead).
SECRET = re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{16,}|sk-[A-Za-z0-9_-]{16,}|xox[abposr]-[A-Za-z0-9-]{10,}"
                    r"|AKIA[0-9A-Z]{16})\b|(?i:bearer\s+[A-Za-z0-9._~+/-]{12,})")
# Wider net for output, which the report may paste into STATE.md.
REDACT = [SECRET,
          re.compile(r"(?i)\b(password|passwd|pwd|token|secret|api[_-]?key|access[_-]?key)(\w*)(\s*[:=]\s*)\S+"),
          re.compile(r"\b[A-Za-z0-9_-]{40,}\b")]
HASH = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
EXPECT = re.compile(r"^(nonempty|contains:\s*\S.*|number>=\d+)$")
# Exit codes and messages that mean "the command never ran", not "access was refused".
NOT_RUN = re.compile(r"command not found|syntax error|unbound variable|No such file or directory: 'bash'")
EXCERPT = 300


def redact(text):
    text = REDACT[0].sub("[redacted]", text)
    text = REDACT[1].sub(lambda m: m.group(1) + m.group(2) + m.group(3) + "[redacted]", text)
    return REDACT[2].sub(lambda m: m.group(0) if HASH.match(m.group(0)) else "[redacted]", text)


def excerpt(text):
    flat = " ".join(redact(text).split())
    if len(flat) <= EXCERPT:
        return flat
    head, tail = EXCERPT * 2 // 3, EXCERPT // 3
    return "%s [... %d characters cut ...] %s" % (flat[:head], len(flat) - head - tail, flat[-tail:])


def validate(data):
    """Return a list of problems; empty means the file is usable."""
    errs = []
    if not isinstance(data, dict) or not isinstance(data.get("systems"), list) or not data["systems"]:
        return ['the file needs a non-empty "systems" list']
    names = set()
    for i, s in enumerate(data["systems"], 1):
        where = "system %d" % i
        if not isinstance(s, dict):
            errs.append("%s: not an object" % where)
            continue
        name = s.get("name")
        if not name or not isinstance(name, str):
            errs.append('%s: needs a "name"' % where)
        else:
            where = '"%s"' % name
            if name in names:
                errs.append("%s: name used twice" % where)
            names.add(name)
        for key in ("covers", "fix"):
            if not isinstance(s.get(key), str) or not s[key].strip():
                errs.append('%s: needs "%s" (%s)' % (where, key, "what the proof covers and leaves out"
                                                     if key == "covers" else "one line: what the user does if it fails"))
        cmds = []
        if "shared" in s and not isinstance(s["shared"], bool):
            errs.append('%s: "shared" must be true or false (no quotes)' % where)
        if "unreachable" in s:
            u = s["unreachable"]
            if not isinstance(u, dict) or not isinstance(u.get("why"), str) or not isinstance(u.get("probe"), str):
                errs.append('%s: "unreachable" needs "why" and "probe" (a command that fails while it is unreachable)' % where)
            else:
                cmds.append(("unreachable probe", u["probe"]))
        else:
            for part in ("read", "write"):
                p = s.get(part)
                if part == "write" and isinstance(p, str) and p.lower().startswith("not needed"):
                    continue
                if (not isinstance(p, dict) or not isinstance(p.get("run"), str) or not p["run"].strip()
                        or not isinstance(p.get("expect"), str)):
                    hint = ' (or "write": "not needed: <why>")' if part == "write" else ""
                    errs.append('%s: "%s" needs "run" and "expect"%s' % (where, part, hint))
                    continue
                if not EXPECT.match(str(p["expect"])):
                    errs.append('%s: %s expect "%s" is not nonempty, contains:TEXT or number>=N' % (where, part, p["expect"]))
                cmds.append((part, p["run"]))
            c = s.get("control")
            if not isinstance(c, dict) or not isinstance(c.get("run"), str) or not c["run"].strip() or not c.get("why"):
                errs.append('%s: needs a "control" with "run" (the same access, deprived of what is being proven, '
                            'which must fail) and "why"' % where)
            else:
                cmds.append(("control", c["run"]))
        for part, cmd in cmds:
            for pat, why in MASKING:
                if pat.search(cmd):
                    errs.append("%s: %s command rejected: %s" % (where, part, why))
            if SECRET.search(cmd):
                errs.append("%s: %s command contains what looks like a secret; use an environment variable" % (where, part))
    return errs


def run(cmd, cwd, timeout):
    try:
        p = subprocess.run(["bash", "-eu", "-o", "pipefail", "-c", cmd], cwd=cwd, capture_output=True,
                           text=True, errors="replace", timeout=timeout)
        return p.returncode, p.stdout + p.stderr
    except subprocess.TimeoutExpired:
        return 124, "timed out after %ds; a write may have left its probe file behind" % timeout


def did_not_run(code, out):
    """True when a failure means the command never ran, rather than that access was refused."""
    return code in (124, 126, 127) or bool(NOT_RUN.search(out))


def meets(rule, out):
    if rule == "nonempty":
        return bool(out.strip())
    if rule.startswith("contains:"):
        return rule[len("contains:"):] in out
    m = re.search(r"-?\d+", out)
    return bool(m) and int(m.group(0)) >= int(rule.split(">=")[1])


def probe(spec, cwd, timeout):
    """Run a read or write. Returns (verdict, detail)."""
    code, out = run(spec["run"], cwd, timeout)
    if code != 0:
        return "FAILED", "exit %d: %s" % (code, excerpt(out) or "(no output)")
    if not meets(spec["expect"], out):
        return "NO EVIDENCE", "exit 0 but output does not meet %s: %s" % (spec["expect"], excerpt(out) or "(no output)")
    return "PROVEN", excerpt(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("manifest")
    ap.add_argument("--check", action="store_true", help="validate the file only")
    ap.add_argument("--allow-shared", action="store_true", help="run writes marked shared (user said yes)")
    ap.add_argument("--timeout", type=int, default=30, help="seconds per command (default 30)")
    a = ap.parse_args()

    try:
        with open(a.manifest) as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        print("REJECTED: cannot read %s: %s" % (a.manifest, e))
        return 2
    errs = validate(data)
    if errs:
        print("REJECTED: nothing ran. Fix these and run again:")
        for e in errs:
            print("- " + e)
        return 2
    if a.check:
        print("OK: %d systems, file is valid. Nothing was run." % len(data["systems"]))
        return 0

    cwd = os.path.dirname(os.path.abspath(a.manifest))
    now = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    lines = ["## Preflight: %s" % data.get("project", os.path.basename(cwd)), "",
             "Run %s in `%s`." % (now, os.path.basename(cwd)), ""]
    blockers = []
    for s in data["systems"]:
        lines.append("### %s" % s["name"])
        lines.append("Covers: %s" % s["covers"])
        if "unreachable" in s:
            code, out = run(s["unreachable"]["probe"], cwd, a.timeout)
            if code == 0:
                lines.append("- UNREACHABLE CLAIM IS WRONG: the probe succeeded: %s" % (excerpt(out) or "(no output)"))
                blockers.append((s, "declared unreachable, but the probe reached it; plan with it instead"))
            elif did_not_run(code, out):
                lines.append("- unreachable claim NOT CHECKED: the probe did not run (exit %d): %s"
                             % (code, excerpt(out) or "(no output)"))
                blockers.append((s, "the unreachable probe did not run; fix the probe command"))
            else:
                lines.append("- unreachable, confirmed (probe exit %d); planned around: %s" % (code, s["unreachable"]["why"]))
            lines.append("")
            continue
        code, out = run(s["control"]["run"], cwd, a.timeout)
        control_ok = code != 0 and not did_not_run(code, out)
        if control_ok:
            lines.append("- control: failed as it must (exit %d)" % code)
        elif code != 0:
            lines.append("- control: NOT A CONTROL: it failed because the command did not run (exit %d): %s"
                         % (code, excerpt(out) or "(no output)"))
            blockers.append((s, "the control failed for the wrong reason (missing command, syntax error, "
                                "unset variable or timeout); make it the read command with one thing taken away"))
        else:
            lines.append("- control: DID NOT FAIL, so these checks prove nothing: %s" % (excerpt(out) or "(no output)"))
            blockers.append((s, "the control succeeded (%s); fix the checks before trusting them" % s["control"]["why"]))
        verdict, detail = probe(s["read"], cwd, a.timeout)
        if verdict == "PROVEN" and not control_ok:
            verdict = "NOT TRUSTED (no valid control)"
        lines.append("- read: %s: %s" % (verdict, detail))
        if verdict != "PROVEN":
            blockers.append((s, "read %s" % verdict.lower()))
        w = s["write"]
        if isinstance(w, str):
            lines.append("- write: %s" % w)
        elif not control_ok:
            lines.append("- write: NOT RUN (no valid control)")
        elif s.get("shared") and not a.allow_shared:
            lines.append("- write: NOT RUN: shared system; ask the user, then rerun with --allow-shared")
            blockers.append((s, "write to a shared system needs the user's yes"))
        else:
            verdict, detail = probe(w, cwd, a.timeout)
            lines.append("- write: %s: %s" % (verdict, detail))
            if verdict != "PROVEN":
                blockers.append((s, "write %s" % verdict.lower()))
        lines.append("")

    if blockers:
        lines += ["## BLOCKERS: do not start the work", ""]
        for s, why in blockers:
            lines.append("- %s: %s. Fix: %s" % (s["name"], why, s["fix"]))
        lines.append("")
    else:
        lines += ["All %d systems proven." % len(data["systems"]), ""]
    lines.append("This proves only the systems listed above, as they were at %s. Rerun it when the plan "
                 "touches a new system or a session resumes later." % now)
    print("\n".join(lines))
    return 1 if blockers else 0


if __name__ == "__main__":
    sys.exit(main())
