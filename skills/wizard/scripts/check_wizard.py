#!/usr/bin/env python3
"""Check a wizard script without running it.

Usage: python3 check_wizard.py <wizard.sh> [--ci <workflows folder>]

Runs bash -n and shellcheck, compares the library part with the skill's template, and reads the
stages for secrets handled outside the helpers, a wrong stage count, leftover EXAMPLE text, gates
that would stop the script on "no", bash 4 features the macOS bash lacks, and irreversible steps
without a typed-yes gate. With --ci, every gh_secret name must match a secrets.NAME reference in
the workflows. Prints a stage map, then RESULT: PASS or RESULT: FAIL.
Exit 0 pass, 1 fail, 2 usage. Standard library only. It never runs the wizard itself.
These checks catch slips, not intent: the static trace in the skill's step 5 is still needed.
"""
import os
import re
import shlex
import shutil
import subprocess
import sys

MARKER = "# ===== STAGES"
LAST_LINE = '_wizard_run "$@"'
TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "wizard-template.sh")
TEMPLATE_EXAMPLES = ("EXAMPLE:", "/EXAMPLE", "EXAMPLE_API_KEY", "the EXAMPLE API key")

KEYWORDS = {"if", "elif", "then", "else", "do", "while", "until", "!", "{", "builtin",
            "command", "exec", "time", "local", "export"}
GUARDS = {"if", "elif", "while", "until", "!"}  # keywords that keep a failing test from ending the script
PUNCT = {";", "&&", "||", "|", "&", ";;", "(", ")", "|&"}
ARITY = {"keychain_store": 2, "op_store": 3, "gh_secret": 3, "gh_variable": 3,
         "config_set": 2, "config_remove": 2, "ask": 2}
STORE_HELPERS = ("keychain_store", "op_store")
ACTION_HELPERS = ("keychain_store", "op_store", "gh_secret", "gh_variable", "config_set",
                  "config_remove", "ask")
TEXT_HELPERS = ("step", "say", "pause", "warn", "note")

# Raw-line rules, run with quoted strings blanked out and comments dropped.
RAW_RULES = [
    (r">>?\s*\S*\.env(\.[\w.-]+)?\b", "writes to a .env file: secrets go to the keychain or 1Password"),
    (r"--body\b", "a value passed as a command argument"),
    (r"\bdeclare\s+-[a-zA-Z]*[An]|\blocal\s+-n\b|\$\{[^}]*(,,|\^\^)\}|\bmapfile\b|\breadarray\b"
     r"|\|&|&>>|\bcoproc\b", "bash 4 only: the system bash on macOS is 3.2"),
    (r"\b_fetch\b|\b_v\b|\b_drain\b|\b_need\b", "library internals used in a stage"),
]
IRREVERSIBLE = re.compile(
    r"\b(delete|destroy|revoke|rotate|purge|wipe|downgrade|overwrite)\b"
    r"|\bcancel (the |your |this )?(plan|subscription|account|domain)\b"
    r"|\bclose (the |your )?account\b"
    r"|\btransfer (the |your )?(domain|repo|repository|ownership)\b"
    r"|\b(switch|change|replace|update|point) (the )?(\w+ )?nameservers?\b"
    r"|\bremove (the |old |existing )*(site|record|records|key|keys|domain|zone|user|member|webhook)\b"
    r"|\breplace (the |old |existing )*(key|secret|token|record|records)\b", re.I)
SECRET_VAR = re.compile(r"(^|_)(KEY|KEYS|TOKEN|TOKENS)(_|$)|SECRET|PASSWORD|PRIVATE", re.I)
SECRET_WORD = re.compile(r"\b(secret|token|password|key|private)\b", re.I)
NOT_SECRET = re.compile(r"not (a )?secret|publishable|public", re.I)


def split_library(text):
    i = text.find(MARKER)
    if i < 0:
        return None, None
    return text[:i], text[i:]


def strip_comment(line):
    """The line without a trailing # comment, keeping quoted text."""
    q = None
    for i, c in enumerate(line):
        if q:
            if c == q:
                q = None
        elif c in "'\"":
            q = c
        elif c == "#" and (i == 0 or line[i - 1] in " \t;"):
            return line[:i]
    return line


def blank_quotes(line):
    """The line with the insides of '...' and "..." blanked and any comment dropped."""
    out, q, i = [], None, 0
    while i < len(line):
        c = line[i]
        if q:
            if c == "\\" and q == '"' and i + 1 < len(line):
                out.append("  ")
                i += 2
                continue
            out.append(c if c == q else " ")
            if c == q:
                q = None
        elif c in "'\"":
            q = c
            out.append(c)
        elif c == "#" and (i == 0 or line[i - 1] in " \t;"):
            break
        else:
            out.append(c)
        i += 1
    return "".join(out)


def tokens(line):
    lex = shlex.shlex(line, posix=True, punctuation_chars=";&|()")
    lex.whitespace_split = True
    lex.commenters = "#"
    try:
        return list(lex)
    except ValueError:
        return line.split()


def commands(line):
    """Yield (name, args, prefix) for each simple command on a line; prefix holds the keywords before it."""
    toks = tokens(line)
    i = 0
    while i < len(toks):
        prefix = []
        while i < len(toks) and (toks[i] in KEYWORDS or toks[i] in PUNCT
                                 or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", toks[i])):
            if toks[i] in KEYWORDS:
                prefix.append(toks[i])
            i += 1
        if i >= len(toks):
            break
        name = toks[i]
        i += 1
        args = []
        while i < len(toks) and toks[i] not in PUNCT:
            args.append(toks[i])
            i += 1
        yield name, args, prefix


def ci_refs(folder):
    secrets, vars_ = set(), set()
    for root, _, files in os.walk(folder):
        for f in files:
            if f.endswith((".yml", ".yaml")):
                with open(os.path.join(root, f), encoding="utf-8", errors="replace") as fh:
                    t = fh.read()
                secrets.update(re.findall(r"secrets\.([A-Za-z_][A-Za-z0-9_]*)", t))
                vars_.update(re.findall(r"vars\.([A-Za-z_][A-Za-z0-9_]*)", t))
    secrets.discard("GITHUB_TOKEN")
    return secrets, vars_


def main(argv):
    args = list(argv)
    ci = None
    if "--ci" in args:
        i = args.index("--ci")
        if i + 1 >= len(args):
            print("usage: check_wizard.py <wizard.sh> [--ci <workflows folder>]")
            return 2
        ci = args[i + 1]
        del args[i:i + 2]
    if len(args) != 1 or not os.path.isfile(args[0]):
        print("usage: check_wizard.py <wizard.sh> [--ci <workflows folder>]")
        return 2
    path = args[0]
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    fails, warns = [], []

    r = subprocess.run(["bash", "-n", path], capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        fails.append("bash -n: " + (r.stderr.strip() or "syntax error"))
    if shutil.which("shellcheck"):
        r = subprocess.run(["shellcheck", "-S", "warning", "-f", "gcc", path],
                           capture_output=True, text=True, errors="replace")
        if r.returncode != 0:
            for line in r.stdout.strip().splitlines()[:10]:
                fails.append("shellcheck: " + line.replace(path, os.path.basename(path)))
    else:
        warns.append("shellcheck not installed, so not run")

    lib, stages = split_library(text)
    if lib is None:
        fails.append("no STAGES line: start from the skill's assets/wizard-template.sh")
        stages = ""
    else:
        with open(TEMPLATE, encoding="utf-8") as fh:
            tlib, _ = split_library(fh.read())
        if lib != tlib:
            fails.append("the library above the STAGES line differs from the template; copy it unchanged")

    code = [l for l in stages.splitlines() if l.strip() and not l.strip().startswith("#")]
    if not code or code[-1].strip() != LAST_LINE:
        fails.append(f"the last command must be {LAST_LINE}")
    if any(e in stages for e in TEMPLATE_EXAMPLES):
        fails.append("EXAMPLE text from the template is still there")
    if "WIZARD_TITLE=" not in stages:
        warns.append("WIZARD_TITLE not set")
    if "/skills/wizard/" in stages:
        fails.append("names the skill's own folder; the wizard must stand alone")

    stage_list = []
    total = None
    func = None  # the shell function the current line is in
    for n, raw in enumerate(stages.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^(function\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*(\(\))?\s*\{?\s*$", line)
        if m and (m.group(1) or m.group(3)):
            func = m.group(2)
            continue
        if raw.startswith("}"):
            func = None
            continue
        m = re.match(r"^TOTAL_STAGES=[\"']?(\d+)[\"']?(\s|$)", line)
        if m:
            total = int(m.group(1))
            continue
        bare = blank_quotes(raw)
        code_part = strip_comment(raw)
        for pat, why in RAW_RULES:
            if re.search(pat, code_part):
                fails.append(f"stages line {n}: {why}: {line[:80]}")
        cur = stage_list[-1] if stage_list else None
        for name, cargs, prefix in commands(raw):
            if name == "read":
                fails.append(f"stages line {n}: read directly: use ask (visible) or keychain_store / op_store (hidden)")
            elif name == "security" and any(a.endswith("-password") for a in cargs):
                fails.append(f"stages line {n}: security directly: use keychain_store / gh_secret")
            elif name == "gh" and cargs[:2] == ["secret", "set"]:
                fails.append(f"stages line {n}: gh secret set directly: use gh_secret (value on standard input)")
            elif name == "op" and any(a in ("item", "document", "read", "inject") for a in cargs):
                fails.append(f"stages line {n}: op item/document/read/inject directly: use op_store / gh_secret")
            elif name == "set" and ("xtrace" in cargs or any(re.match(r"^-[a-zA-Z]*x", a) for a in cargs)):
                fails.append(f"stages line {n}: set -x prints every command, secrets included")
            elif name in ("sed", "tee", "cp", "mv", "dd", "awk", "perl") and \
                    any(re.search(r"(^|/)\.env(\.[\w.-]+)?$", a) for a in cargs):
                fails.append(f"stages line {n}: {name} on a .env file: use config_set / config_remove")
            if name in ("confirm", "confirm_irreversible") and not (set(prefix) & GUARDS) \
                    and "&&" not in bare and "||" not in bare:
                fails.append(f"stages line {n}: a bare {name} stops the whole wizard on 'no' "
                             "(set -e); put it in an if, or use &&")
            if name == "stage":
                if func != "main":
                    fails.append(f"stages line {n}: stage called outside main(), so the stage count can't be checked")
                title = cargs[0] if cargs else ""
                stage_list.append({"title": title, "opens": 0, "actions": [], "gate": False, "text": title})
                cur = stage_list[-1]
                continue
            if name in ARITY:
                need = ARITY[name]
                if len(cargs) < need or any(not a for a in cargs[:need]):
                    fails.append(f"stages line {n}: {name} needs {need} arguments: {line[:80]}")
            if cur is None:
                if name in ACTION_HELPERS or name == "open_url":
                    fails.append(f"stages line {n}: {name} before the first stage")
                continue
            if name in TEXT_HELPERS:
                cur["text"] += " " + " ".join(cargs)
            elif name == "open_url":
                cur["opens"] += 1
            elif name == "confirm_irreversible":
                cur["gate"] = True
            if name == "ask" and len(cargs) >= 2:
                var, prompt = cargs[0], cargs[1]
                if not NOT_SECRET.search(prompt + " " + var) and \
                        (SECRET_WORD.search(prompt) or SECRET_VAR.search(var)):
                    fails.append(f"stages line {n}: ask shows what is typed; a secret needs keychain_store or op_store")
            if name in ("gh_variable", "config_set") and len(cargs) >= 2:
                key = cargs[0] if name == "gh_variable" else cargs[1]
                value = cargs[2] if len(cargs) > 2 else ""
                if SECRET_VAR.search(key) and not NOT_SECRET.search(key) and not value.startswith("op://"):
                    fails.append(f"stages line {n}: {name} {key} looks like a secret; use gh_secret, "
                                 "or an op:// reference in config_set")
            if name in ACTION_HELPERS:
                cur["actions"].append((name, cargs))
                if name in STORE_HELPERS and cur["opens"] == 0:
                    warns.append(f"stage '{cur['title']}': stores a secret before any open_url in that stage")

    if total is None:
        fails.append("TOTAL_STAGES is not set")
    elif total != len(stage_list):
        fails.append(f"TOTAL_STAGES={total} but there are {len(stage_list)} stage calls")
    if not stage_list:
        fails.append("no stages")
    for s in stage_list:
        text = re.sub(r"\b(don't|do not|never|not|without)\s+(\w+\s+){0,2}\w+", " ", s["text"], flags=re.I)
        hit = IRREVERSIBLE.search(text)
        if hit and not s["gate"]:
            warns.append(f"stage '{s['title']}' mentions '{hit.group(0)}' but has no confirm_irreversible; "
                         "add one, or say in the reply why the step can be undone")

    if ci is not None:
        if not os.path.isdir(ci):
            fails.append(f"--ci folder not found: {ci}")
        else:
            want_s, want_v = ci_refs(ci)
            got_s = {a[1][0] for s in stage_list for a in s["actions"] if a[0] == "gh_secret" and a[1]}
            got_v = {a[1][0] for s in stage_list for a in s["actions"] if a[0] == "gh_variable" and a[1]}
            for name in sorted(got_s - want_s):
                fails.append(f"gh_secret {name} matches no secrets.{name} in the workflows")
            for name in sorted(got_v - want_v):
                fails.append(f"gh_variable {name} matches no vars.{name} in the workflows")
            for name in sorted(want_s - got_s):
                warns.append(f"workflows use secrets.{name}, which this wizard never sets")
            for name in sorted(want_v - got_v):
                warns.append(f"workflows use vars.{name}, which this wizard never sets")

    print(f"Stage map ({len(stage_list)} stages):")
    for i, s in enumerate(stage_list, 1):
        acts = "; ".join(f"{c} {' '.join(a[:3])}" for c, a in s["actions"]) or "no stored values"
        gate = ", typed-yes gate" if s["gate"] else ""
        print(f"  {i}. {s['title']}: opens {s['opens']} page(s){gate}; {acts}")
    for w in warns:
        print("WARN " + w)
    for f in fails:
        print("FAIL " + f)
    print("RESULT: PASS" if not fails else f"RESULT: FAIL ({len(fails)})")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
