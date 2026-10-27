# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6"]
# ///
"""Check every skill against the house rules (docs/house-rules.md).

Usage: uv run tools/check_skills.py [--root DIR] [--require-deny] [--extra-text FILE]

Prints one line per finding, "FAIL R<n> <path>: <message>" or "WARN R<n> ...", then a summary.
Exits 1 if anything failed.

Employer-terms scan (rule 9): patterns come from the GFM_SKILLS_DENY environment variable (one
regular expression per line) or the file named by GFM_SKILLS_DENY_FILE. They are kept outside the
repo. A match prints its location only, never the matched text. With --require-deny, missing
patterns fail the run instead of being skipped.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import unicodedata

import yaml

ALLOWED_KEYS = {"name", "description", "license", "compatibility", "metadata"}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
BOM = chr(0xFEFF)
VARIATION_SELECTORS = ((0xFE00, 0xFE0F), (0xE0100, 0xE01EF))
COLOUR_RE = re.compile(r"^(#[0-9a-fA-F]{3,8}|(rgba?|hsla?|oklch|oklab|lab|lch|color)\(.+\))$")
COLOUR_KEY_RE = re.compile(r"(?i)^(primary|secondary|accent|background|foreground|text)$|colou?r$")


def has_hidden_char(line):
    """True for format, private-use or unassigned characters and variation selectors."""
    for c in line:
        if unicodedata.category(c) in ("Cf", "Co", "Cn"):
            return True
        if any(a <= ord(c) <= b for a, b in VARIATION_SELECTORS):
            return True
    return False


class Report:
    def __init__(self):
        self.fails = 0
        self.warns = 0

    def fail(self, rule, path, msg):
        self.fails += 1
        print(f"FAIL R{rule} {path}: {msg}")

    def warn(self, rule, path, msg):
        self.warns += 1
        print(f"WARN R{rule} {path}: {msg}")


def split_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    return (m.group(1), m.group(2)) if m else (None, text)


def reserved_names(root):
    path = os.path.join(root, "tools", "reserved-names.txt")
    if not os.path.isfile(path):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reserved-names.txt")
    with open(path) as f:
        return {l.strip() for l in f if l.strip() and not l.startswith("#")}


def referenced_paths(body):
    refs = set(re.findall(r"\]\(([^)#\s]+)\)", body))
    refs |= set(re.findall(r"`((?:references|scripts|assets|local\.example)/[\w./-]+)`", body))
    return {r for r in refs if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", r) and not r.startswith("local/")}


def check_skill(root, folder, rep, reserved, seen):
    rel = os.path.relpath(folder, root)
    path = os.path.join(rel, "SKILL.md")
    with open(os.path.join(folder, "SKILL.md"), encoding="utf-8") as f:
        text = f.read()
    raw, body = split_frontmatter(text)
    if raw is None:
        rep.fail(1, path, "no YAML frontmatter between --- lines")
        return
    try:
        fm = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        rep.fail(1, path, f"frontmatter is not valid YAML ({str(e).splitlines()[0]})")
        return
    if not isinstance(fm, dict):
        rep.fail(1, path, "frontmatter is not a mapping")
        return
    extra = sorted(set(fm) - ALLOWED_KEYS)
    if extra:
        rep.fail(1, path, f"frontmatter keys outside the spec set: {', '.join(extra)}")
    meta = fm.get("metadata") or {}
    if not isinstance(meta, dict) or not all(isinstance(v, str) for v in meta.values()):
        rep.fail(1, path, "metadata must map strings to strings (quote values like \"true\")")
        meta = {}
    if "compatibility" in fm and len(str(fm["compatibility"])) > 500:
        rep.fail(1, path, "compatibility is over 500 characters")

    # Rule 2: name
    name = fm.get("name")
    folder_name = os.path.basename(folder)
    if not isinstance(name, str) or not name:
        rep.fail(2, path, "name is missing")
    else:
        if name != folder_name:
            rep.fail(2, path, f"name '{name}' does not match folder '{folder_name}'")
        if len(name) > 64 or not NAME_RE.match(name):
            rep.fail(2, path, "name must be lowercase letters, digits and single hyphens, max 64")
        if re.search(r"claude|anthropic", name):
            rep.fail(2, path, "name contains a reserved word (claude, anthropic)")
        if name in reserved:
            rep.fail(2, path, f"name '{name}' reuses a built-in skill name (tools/reserved-names.txt)")
        if name in seen:
            rep.fail(2, path, f"name '{name}' is used by {seen[name]} too")
        seen[name] = rel

    # Rules 3 and 4: description
    desc = fm.get("description")
    if not isinstance(desc, str) or not desc.strip():
        rep.fail(4, path, "description is missing")
    else:
        desc = " ".join(desc.split())
        if re.search(r"<[^>]+>", desc):
            rep.fail(4, path, "description contains an XML-style tag")
        if len(desc) > 1024:
            rep.fail(4, path, f"description is {len(desc)} characters (limit 1,024)")
        elif len(desc) > 300:
            rep.warn(4, path, f"description is {len(desc)} characters (house limit 300, aim for 250)")
        if re.match(r"(?i)(i|i'm|you|use this skill|this skill)\b", desc):
            rep.warn(3, path, "description should be in the third person ('Drafts...', not 'I/You/This skill')")
        if not re.search(r"(?i)\buse(d)?\b(\s+\w+){0,2}\s+(when|whenever|for|before|after|to)\b", desc):
            rep.warn(3, path, "description should say when to use the skill ('Use when ...')")
        if not re.search(r"(?i)\bnot for\b|\bdon't use\b|\bdo not use\b|\bnot when\b", desc):
            rep.warn(3, path, "description should say what the skill is not for ('Not for ...')")

    # Rule 5: body size
    lines = body.splitlines()
    if len(lines) >= 500:
        rep.fail(5, path, f"body is {len(lines)} lines (limit under 500)")
    if len(body) // 4 > 5000:
        rep.warn(5, path, f"body is about {len(body) // 4} tokens (aim for under 5,000)")

    # Rule 6: references
    for ref in sorted(referenced_paths(body)):
        target = os.path.normpath(os.path.join(folder, ref))
        if not target.startswith(folder + os.sep):
            rep.fail(6, path, f"points outside the skill folder: {ref}")
            continue
        if not os.path.exists(target):
            rep.fail(6, path, f"points to a missing file: {ref}")
            continue
        if target.endswith(".md") and os.path.isfile(target):
            with open(target, encoding="utf-8") as f:
                if re.search(r"\]\((?!https?://)[^)#\s]+\.md\)", f.read()):
                    rep.fail(6, os.path.join(rel, ref), "links to another .md file (keep references one level deep)")
    for dp, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if d != "local"]
        for fn in files:
            if fn.endswith(".md") and not (dp == folder and fn == "SKILL.md"):
                p = os.path.join(dp, fn)
                with open(p, encoding="utf-8") as f:
                    content = f.read().splitlines()
                if len(content) > 100 and not any(l.strip().lower() == "## contents" for l in content[:20]):
                    rep.fail(6, os.path.relpath(p, root), "over 100 lines without a '## Contents' list near the top")

    # Rule 7: evals
    status = meta.get("status", "draft")
    if status not in ("draft", "stable"):
        rep.fail(7, path, f"metadata.status must be draft or stable, not '{status}'")
    for problem in eval_problems(root, folder_name):
        (rep.fail if status == "stable" else rep.warn)(7, f"evals/{folder_name}", problem)

    # Rule 11: time-sensitive content
    # Built-in skill names such as claude-api are not model names.
    unreserved = re.sub(r"\b(" + "|".join(map(re.escape, sorted(reserved))) + r")\b", "", body) if reserved else body
    if re.search(r"\b20\d\d-\d\d(-\d\d)?\b|[$€£]\s?\d|\b(claude|gpt|gemini)-[\w.]+", unreserved, re.I):
        rep.warn(11, path, "body has a date, price or model name; date and link it, or move it to an 'old patterns' section")

    # Rule 12: brand convention
    if meta.get("brand") == "true":
        for need in ("references/tokens.json", "local.example/tokens.json", "scripts/find-brand.sh"):
            if not os.path.isfile(os.path.join(folder, need)):
                rep.fail(12, path, f"brand-aware skill is missing {need}")
        master = os.path.join(root, "tools", "find-brand.sh")
        if not os.path.isfile(master):
            master = os.path.join(os.path.dirname(os.path.abspath(__file__)), "find-brand.sh")
        copy = os.path.join(folder, "scripts", "find-brand.sh")
        if os.path.isfile(master) and os.path.isfile(copy):
            with open(master, "rb") as a, open(copy, "rb") as b:
                if a.read() != b.read():
                    rep.fail(12, os.path.join(rel, "scripts/find-brand.sh"), "differs from tools/find-brand.sh; copy it again")
        if "Brand:" not in body or ".agents/brand" not in body:
            rep.fail(12, path, "brand-aware skill must describe the lookup and the 'Brand:' first line")
        for tj in ("references/tokens.json", "local.example/tokens.json"):
            p = os.path.join(folder, tj)
            if os.path.isfile(p):
                try:
                    with open(p) as f:
                        tokens = json.load(f)
                    if not isinstance(tokens, dict) or "primary" not in tokens:
                        rep.fail(12, os.path.join(rel, tj), "tokens.json needs a 'primary' value")
                    else:
                        for k, v in tokens.items():
                            if COLOUR_KEY_RE.search(k) and not (isinstance(v, str) and COLOUR_RE.match(v.strip())):
                                rep.fail(12, os.path.join(rel, tj), f"'{k}' must be a real colour (#hex or a CSS colour function)")
                except ValueError:
                    rep.fail(12, os.path.join(rel, tj), "tokens.json is not valid JSON")

    # Rule 9: licence beside borrowed text. Any upstream counts, MIT included.
    lic = fm.get("license")
    upstream = meta.get("upstream")
    if upstream or (lic and str(lic).strip().upper() != "MIT"):
        why = f"upstream is '{upstream}'" if upstream else f"license is '{lic}'"
        if not any(f.upper().startswith(("LICENSE", "LICENCE")) for f in os.listdir(folder)):
            rep.fail(9, path, f"{why} but the skill folder has no LICENSE file from the upstream")
        notices = os.path.join(root, "THIRD_PARTY_NOTICES.md")
        text = open(notices, encoding="utf-8").read() if os.path.isfile(notices) else ""
        rows = [l for l in text.splitlines() if l.startswith("|") and folder_name in l]
        if not rows:
            rep.fail(9, path, "borrowed text must have a row in THIRD_PARTY_NOTICES.md")
        elif upstream and "@" in upstream and not any(upstream.split("@", 1)[1][:7] in r for r in rows):
            rep.fail(9, path, "the THIRD_PARTY_NOTICES.md row must name the upstream commit")


def eval_problems(root, name):
    """Problems with evals/<name>/ against docs/evals.md. Empty list means complete."""
    ev = os.path.join(root, "evals", name)
    problems = []
    try:
        with open(os.path.join(ev, "cases.yaml")) as f:
            cases = (yaml.safe_load(f) or {}).get("cases") or []
    except (OSError, yaml.YAMLError, AttributeError):
        cases = None
    if cases is None:
        problems.append("cases.yaml is missing or unreadable")
    else:
        good = [c for c in cases if isinstance(c, dict) and isinstance(c.get("prompt"), str) and c["prompt"].strip()
                and isinstance(c.get("expect"), list) and c["expect"] and all(isinstance(e, str) for e in c["expect"])]
        if len(good) < 3:
            problems.append(f"needs 3+ cases with a prompt and an expect list (has {len(good)} complete)")
        for c in cases:
            for s in (c.get("setup") or []) if isinstance(c, dict) else []:
                if not os.path.isfile(os.path.join(ev, str(s))):
                    problems.append(f"setup file missing: {s}")
    try:
        with open(os.path.join(ev, "triggers.yaml")) as f:
            trig = yaml.safe_load(f) or {}
    except (OSError, yaml.YAMLError):
        trig = None
    if not isinstance(trig, dict):
        problems.append("triggers.yaml is missing or unreadable")
    else:
        for key in ("should", "should_not"):
            items = [t for t in (trig.get(key) or []) if isinstance(t, str) and t.strip()]
            if len(items) < 3:
                problems.append(f"triggers.yaml needs 3+ '{key}' prompts (has {len(items)})")
    return problems


def publishable_files(root):
    """What git would publish: tracked plus untracked-but-not-ignored files. Ignored files (such as
    skills/*/local/) are left out. Outside a git repo, every file except .git and skills/*/local/."""
    try:
        out = subprocess.run(["git", "-C", root, "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
        if os.path.realpath(out.stdout.strip()) != os.path.realpath(root):
            raise ValueError("root is not the top of its own repo")
        names = subprocess.run(["git", "-C", root, "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                               capture_output=True, check=True).stdout.decode("utf-8").split("\0")
        return [os.path.join(root, n) for n in names if n and os.path.isfile(os.path.join(root, n))]
    except (OSError, subprocess.CalledProcessError, ValueError):
        files = []
        for dp, dirs, fs in os.walk(root):
            dirs[:] = [d for d in dirs if d != ".git" and not (d == "local" and os.path.basename(os.path.dirname(dp)) == "skills")]
            files += [os.path.join(dp, f) for f in fs]
        return files


def deny_patterns():
    raw = os.environ.get("GFM_SKILLS_DENY", "")
    path = os.environ.get("GFM_SKILLS_DENY_FILE")
    if not raw and path and os.path.isfile(path):
        with open(path) as f:
            raw = f.read()
    pats = [l.strip() for l in raw.splitlines() if l.strip() and not l.startswith("#")]
    return [re.compile(p, re.I) for p in pats]


def scan_repo(root, rep, require_deny, extra_text):
    pats = deny_patterns()
    if not pats:
        (rep.fail if require_deny else rep.warn)(9, ".", "employer-terms scan has no patterns (set GFM_SKILLS_DENY or GFM_SKILLS_DENY_FILE)")
    files = publishable_files(root)
    if extra_text:
        files.append(extra_text)
    for p in files:
        try:
            with open(p, encoding="utf-8") as f:
                lines = f.read().splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        shown = p if p == extra_text else os.path.relpath(p, root)
        for i, line in enumerate(lines, 1):
            check_line = line[1:] if i == 1 and line.startswith(BOM) else line
            if has_hidden_char(check_line):
                rep.fail(9, f"{shown}:{i}", "invisible or direction-changing character")
            for j, pat in enumerate(pats, 1):
                if pat.search(line):
                    rep.fail(9, f"{shown}:{i}", f"matches employer-terms pattern #{j}")
    try:
        tracked = subprocess.run(["git", "-C", root, "ls-files", "skills/*/local/*"],
                                 capture_output=True, text=True, check=True).stdout.split()
    except (OSError, subprocess.CalledProcessError):
        tracked = []
    for t in tracked:
        rep.fail(9, t, "a local/ file is tracked by git; it must never be committed")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--require-deny", action="store_true")
    ap.add_argument("--extra-text", help="also scan this file (commit messages, PR title and body)")
    args = ap.parse_args()
    root = os.path.abspath(args.root)
    rep = Report()
    skills_dir = os.path.join(root, "skills")
    folders = sorted(os.path.join(skills_dir, d) for d in os.listdir(skills_dir)) if os.path.isdir(skills_dir) else []
    folders = [f for f in folders if os.path.isdir(f)]
    reserved, seen = reserved_names(root), {}
    for folder in folders:
        if not os.path.isfile(os.path.join(folder, "SKILL.md")):
            rep.fail(1, os.path.relpath(folder, root), "skill folder has no SKILL.md")
            continue
        check_skill(root, folder, rep, reserved, seen)
    if not folders:
        rep.fail(10, "skills/", "no skills found; an empty run must not pass")
    scan_repo(root, rep, args.require_deny, args.extra_text)
    print(f"{len(folders)} skills checked: {rep.fails} fail, {rep.warns} warn")
    sys.exit(1 if rep.fails else 0)


if __name__ == "__main__":
    main()
