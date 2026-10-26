#!/usr/bin/env python3
"""Lint a message before sending it: a hand-over, instructions or a status report.

Usage: python3 scripts/lint_message.py <draft.md | ->

Flags what would break or mislead the reader:
  placeholder   YOUR_X, {{x}}, <x>, TODO, TBD, xxx left in (ERROR in code, WARN in text)
  language      a code block whose language doesn't match its contents (ERROR)
  folder        a command that depends on the folder it runs in, with no folder given (WARN)
  risky         curl|sh, rm -rf on an unquoted variable or /, force push, sudo, --no-verify,
                chmod 777 (ERROR for the first three, WARN for the rest)
  announced     "I'll push", "I'm going to create": a write promised instead of done (WARN)
  elided        "rest is similar", "... unchanged", "and so on": output left out (ERROR)
  count         "fixed 9 files" with no list, table or command nearby (WARN)
Not checked, and printed every time: whether the message leads with what the reader must do, and
whether it asks for more than one decision.

Exit code 0 clean (warnings allowed), 1 errors, 2 input unreadable. Standard library only.
"""
import re
import sys

FENCE = re.compile(r"^\s*(`{3,}|~{3,})\s*([\w+.-]*)\s*$")
SHELL = {"bash", "sh", "zsh", "shell", "console", "fish"}
PY = {"python", "py", "python3"}
HTML_TAGS = {"br", "b", "i", "u", "em", "strong", "code", "pre", "p", "a", "img", "div", "span", "hr",
             "ul", "ol", "li", "table", "tr", "td", "th", "details", "summary", "sup", "sub", "kbd"}

SLOT = re.compile(r"\bYOUR_[A-Z0-9_]+\b|\{\{[^}]{1,60}\}\}|\bTODO\b|\bTBD\b|\bxxx+\b|\bCHANGEME\b|\bREPLACE_ME\b", re.I)
ANGLE = re.compile(r"<([A-Za-z][\w .-]{0,40})>")
PY_LINE = re.compile(r"^\s*(import \w|from [\w.]+ import|def \w+\(|class \w+[(:]|print\()")
SH_LINE = re.compile(r"^\s*(\$ |cd |ls |git |npm |pip |curl |rm |mkdir |export |sudo |brew |uv )")
NEEDS_DIR = re.compile(r"^\s*(\./|npm |npx |pnpm |yarn |make\b|pytest\b|cargo |go (run|test|build)\b|uv run |"
                       r"python3? (?!-c)[\w./-]+\.py|git (?!-C|clone)\w)")
DIR_GIVEN = re.compile(r"^\s*(cd|pushd)\s+\S")
DIR_PROSE = re.compile(r"\b(in|from|inside|under|at) (the )?(`[^`]+`|~?/\S+|\S+/ folder|the \S+ (folder|directory|repo))", re.I)
RISKY = [
    (re.compile(r"\b(curl|wget)\b[^|\n]*\|\s*(sudo\s+)?(ba|z)?sh\b"), "ERROR", "pipes a download straight into a shell"),
    (re.compile(r"\brm\s+-\w*r\w*f?\w*\s+(\$\w+|\$\{\w+\}|/\s|/$|~/?\s|~/?$)"), "ERROR", "rm -rf on an unquoted variable, / or ~"),
    (re.compile(r"\bgit push\b.*(--force\b|-f\b)(?!-with-lease)"), "ERROR", "force push; use --force-with-lease and never on main"),
    (re.compile(r"^\s*sudo\b"), "WARN", "runs with sudo"),
    (re.compile(r"--no-verify\b"), "WARN", "skips hooks with --no-verify"),
    (re.compile(r"\bchmod\s+(-R\s+)?777\b"), "WARN", "chmod 777"),
]
ANNOUNCED = re.compile(r"\b(I'll|I will|I'm going to|I am going to|we'll|next I'll|I'm now)\s+"
                       r"(create|write|push|commit|deploy|add|update|delete|remove|send|merge|publish|run|fix|install)\b", re.I)
ELIDED = re.compile(r"(rest (is|are) (similar|the same|unchanged)|\b(other|remaining)\b[^.]{0,30}\b(are|is) (similar|the same|unchanged)|"
                    r"\.\.\.\s*\(?(rest|remaining|unchanged|same as above)|// \.\.\.|# \.\.\.|"
                    r"\b(and so on|etc\.)\s*$|\bsimilar(ly)? for the (rest|others)\b|existing code (here|unchanged))", re.I)
COUNT = re.compile(r"\b(\d{1,4}|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+"
                   r"(files|tests|errors|warnings|rows|records|issues|bugs|skills|pages|endpoints|commits|checks|cases)\b", re.I)
ENUMERATED = re.compile(r"`[^`]+`|\bcount(ed)?\b|\benumerat|\blisted\b|\bbelow\b|\bwc -l\b|\bgrep -c\b", re.I)


def blocks_and_prose(lines):
    blocks, prose, cur = [], [], None
    for n, line in enumerate(lines, 1):
        m = FENCE.match(line)
        if cur is None and m:
            cur = {"lang": m.group(2).lower(), "start": n, "lines": [], "fence": m.group(1)}
        elif cur is not None and line.strip().startswith(cur["fence"][:3]) and not line.strip()[3:].strip():
            blocks.append(cur)
            cur = None
        elif cur is not None:
            cur["lines"].append((n, line))
        else:
            prose.append((n, line))
    if cur is not None:
        blocks.append(cur)
    return blocks, prose


def lint(text):
    lines = text.splitlines()
    blocks, prose = blocks_and_prose(lines)
    out = []

    def add(n, sev, rule, msg):
        out.append((n, sev, rule, msg))

    for b in blocks:
        body = b["lines"]
        is_shell = b["lang"] in SHELL or (not b["lang"] and any(SH_LINE.match(l) for _, l in body))
        is_py = b["lang"] in PY
        if b["lang"] in SHELL and any(PY_LINE.match(l) for _, l in body):
            add(b["start"], "ERROR", "language", f"`{b['lang']}` block contains Python; it fails when pasted into a shell")
        if is_py and any(SH_LINE.match(l) for _, l in body) and not any(PY_LINE.match(l) for _, l in body):
            add(b["start"], "ERROR", "language", "`python` block contains shell commands")
        dir_set = any(DIR_GIVEN.match(l) for _, l in body)
        above = " ".join(l for n, l in prose if b["start"] - 3 <= n < b["start"])
        for n, l in body:
            for m in SLOT.finditer(l):
                add(n, "ERROR", "placeholder", f"left in a code block: {m.group(0)}")
            for m in ANGLE.finditer(l):
                if m.group(1).split()[0].lower() not in HTML_TAGS and not re.match(r"<<-?\s*'?\w+", l[m.start() - 2:m.end()]):
                    add(n, "ERROR", "placeholder", f"left in a code block: <{m.group(1)}>")
            if is_shell:
                for rx, sev, msg in RISKY:
                    if rx.search(l):
                        add(n, sev, "risky", msg)
                if NEEDS_DIR.match(l) and not dir_set and not DIR_PROSE.search(above):
                    add(n, "WARN", "folder", f"depends on the folder it runs in; add a cd line or name the folder: {l.strip()[:60]}")
            if ELIDED.search(l):
                add(n, "ERROR", "elided", f"output left out: {l.strip()[:60]}; give it in full")

    for i, (n, l) in enumerate(prose):
        bare = re.sub(r"`[^`]*`", "", l)
        for m in SLOT.finditer(bare):
            add(n, "WARN", "placeholder", f"in the text: {m.group(0)}")
        for m in ANNOUNCED.finditer(bare):
            add(n, "WARN", "announced", f"'{m.group(0)}': do the write, then report it with its result")
        if ELIDED.search(l):
            add(n, "ERROR", "elided", f"output left out: {l.strip()[:60]}; give it in full")
        for code in re.findall(r"`([^`]+)`", l):
            for rx, sev, msg in RISKY:
                if rx.search(code):
                    add(n, sev, "risky", msg)
            for m in SLOT.finditer(code):
                add(n, "ERROR", "placeholder", f"left in a command: {m.group(0)}")
        if not l.lstrip().startswith("|"):
            for m in COUNT.finditer(bare):
                near = " ".join(x for _, x in prose[max(0, i - 1):i + 3])
                nxt = prose[i + 1][1] if i + 1 < len(prose) else ""
                listed = l.rstrip().endswith(":") or re.match(r"\s*([-*]|\d+\.)\s", nxt)
                if not ENUMERATED.search(near) and not listed:
                    add(n, "WARN", "count", f"'{m.group(0)}' with no list or command behind it")
    return sorted(set(out))


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    try:
        text = sys.stdin.read() if sys.argv[1] == "-" else open(sys.argv[1], encoding="utf-8").read()
    except (OSError, UnicodeDecodeError) as e:
        print(f"cannot read input: {e}")
        sys.exit(2)
    found = lint(text)
    for n, sev, rule, msg in found:
        print(f"{sev:5} line {n}  {rule}: {msg}")
    errors = sum(1 for f in found if f[1] == "ERROR")
    warns = len(found) - errors
    print(f"{errors} error(s), {warns} warning(s)")
    print("NOT CHECKED: does it lead with what the reader must do? Does it ask for more than one decision?")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
