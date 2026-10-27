#!/usr/bin/env python3
"""Start a self-contained Scrollback page with the stylesheet inlined.

Usage: python3 <skill>/scripts/new_page.py <out.html> [--title "Sync status"]

Writes the starter page (assets/starter.html) with assets/scrollback.css pasted into its <style>
block, so the tokens are never retyped by hand. Refuses to overwrite an existing file.
For a project with its own build, copy assets/scrollback.css into the project and link it instead.
Standard library only.
"""
import html
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")


def main(argv):
    title, out, rest = "Untitled", None, list(argv)
    while rest:
        a = rest.pop(0)
        if a == "--title" and rest:
            title = rest.pop(0)
        elif a.startswith("--title="):
            title = a.split("=", 1)[1]
        elif a in ("-h", "--help"):
            print(__doc__.strip())
            return 0
        elif out is None and not a.startswith("-"):
            out = a
        else:
            print(f"unknown argument: {a}", file=sys.stderr)
            return 2
    if not out:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    if os.path.exists(out):
        print(f"{out} already exists; not overwriting it. Edit it, or pick a new name.", file=sys.stderr)
        return 1
    with open(os.path.join(ASSETS, "starter.html"), encoding="utf-8") as f:
        page = f.read()
    with open(os.path.join(ASSETS, "scrollback.css"), encoding="utf-8") as f:
        css = f.read().strip()
    page = page.replace("/*SCROLLBACK_CSS*/", css).replace("{{TITLE}}", html.escape(title))
    parent = os.path.dirname(os.path.abspath(out))
    os.makedirs(parent, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"wrote {out} (stylesheet inlined, {len(css):,} characters)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
