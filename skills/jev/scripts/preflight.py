#!/usr/bin/env python3
"""Preflight for the jev skill. Standard library only; makes no network call.

Usage: python3 <skill>/scripts/preflight.py [PROJECT_DIR]

Run it with the project as the working directory (or pass the project folder). Prints these
lines; copy them into the reply as printed:

  Key: present | missing (TYPESAFE_API_KEY is not set in this shell)
  Data rule: <source> (<path>): <first rule line>
  Project rule: <path>: <first rule line>        (only when the project has one)
  SDK: importable | not importable in this Python (<python>)

The key's value is never read beyond an emptiness test and never printed.
"""
import importlib.util
import os
import sys
from pathlib import Path

RULE_FILE = "data-decision.md"
MAX_RULE = 200  # characters of a rule line to print
DEFAULT_RULE = "public data only (no rule file found; this is the skill's default)"


def project_root(start):
    """Nearest folder holding .git, walking up; the start folder if there is none."""
    for d in [start, *start.parents]:
        if (d / ".git").exists():
            return d
    return start


def user_rule_sources():
    """The user's own rule, in lookup order: skill local/, then home."""
    yield "skill local", Path(__file__).resolve().parent.parent / "local" / RULE_FILE
    yield "home", Path.home() / ".agents" / "jev" / RULE_FILE


def project_rule(project):
    """Nearest .agents/jev/data-decision.md from the project up to its repository root.
    A project's file can come from anyone who wrote the repo, so it may only narrow the
    user's rule, never widen it. A file reached through a symlink is never read: it could
    be anywhere on the machine, and its first line would be printed."""
    root = project_root(project).resolve()
    for d in [project, *project.parents]:
        path = d / ".agents" / "jev" / RULE_FILE
        if path.is_symlink() or path.is_file():
            # Reached through a symlink (the file, .agents or .agents/jev): never read it.
            if path.is_symlink() or root not in path.resolve().parents:
                return path, "ignored: it is reached through a symlink; treat the project as having no rule"
            return path, None
        if d == root:
            return None, None
    return None, None


def show(path):
    """A path for the reply, with the home folder written as ~."""
    home = str(Path.home())
    s = str(path)
    return "~" + s[len(home):] if home and home != "/" and s.startswith(home + os.sep) else s


def first_rule_line(path):
    """First list item outside code fences: the newest rule, by the file's own convention.
    Printed only up to MAX_RULE characters; read the file itself for the rest."""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            fenced = False
            for line in f:
                s = line.strip()
                if s.startswith(("```", "~~~")):
                    fenced = not fenced
                    continue
                if not fenced and s.startswith(("- ", "* ")):
                    rule = " ".join(s[2:].split())
                    return rule if len(rule) <= MAX_RULE else rule[:MAX_RULE] + " [...cut; read the file]"
    except OSError as e:
        return f"unreadable ({e.__class__.__name__}); treat as public data only"
    return "no rule line found (expected a '- ' list item); treat as public data only"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    try:
        project = Path(args[0] if args else os.getcwd()).expanduser().resolve()
    except OSError as e:
        print(f"preflight: can't read the working folder ({e.__class__.__name__}); pass the project folder", file=sys.stderr)
        return 2
    if not project.is_dir():
        print(f"preflight: {project} is not a folder", file=sys.stderr)
        return 2
    skill_dir = Path(__file__).resolve().parent.parent
    if project == skill_dir or skill_dir in project.parents:
        print("preflight: warning: run this from the project, not from inside the skill folder", file=sys.stderr)

    key = os.environ.get("TYPESAFE_API_KEY", "")
    print("Key: present" if key.strip() else "Key: missing (TYPESAFE_API_KEY is not set in this shell)")

    for source, path in user_rule_sources():
        if path.is_file():
            print(f"Data rule: {source} ({show(path)}): {first_rule_line(path)}")
            break
    else:
        print(f"Data rule: default: {DEFAULT_RULE}")
    proj, why_ignored = project_rule(project)
    if proj and why_ignored:
        print(f"Project rule: {show(proj)}: {why_ignored}")
    elif proj:
        print(f"Project rule: {show(proj)}: {first_rule_line(proj)} (may narrow the data rule, never widen it)")

    sdk = importlib.util.find_spec("typesafe_sdk") is not None
    print("SDK: importable" if sdk else
          f"SDK: not importable in this Python ({show(sys.executable)}); run preflight with the project's own Python to be sure")
    return 0


if __name__ == "__main__":
    sys.exit(main())
