#!/usr/bin/env python3
"""Maintainer tool for the evals, not part of the skill. Re-inline the current
skills/scrollback/assets/scrollback.css into the demo pages, so the fixtures stay in step with the
stylesheet. Run after any stylesheet change, then run regress.py.

Usage: python3 evals/scrollback/regen_fixtures.py
The check-dashboard page gets its four planted CSS breaks re-applied after the refresh.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CSS = open(os.path.join(HERE, "..", "..", "skills", "scrollback", "assets", "scrollback.css"), encoding="utf-8").read().strip()
PAGES = ["regress/good.html", "files/chart-split/dashboard.html", "files/check-dashboard/dashboard.html"]
PLANTS = [  # check-dashboard only: the stylesheet breaks the check case expects to be found
    (".doc{background:var(--surface);", ".doc{border-radius:8px;background:var(--surface);"),
    ("a{color:var(--bright)", "a{color:var(--accent)"),
    ("tfoot td{color:var(--bright)}", "tfoot td{color:var(--bright);font-weight:700}"),
    (".pill.ok{color:var(--bright)}", ".pill.ok{color:#3FB950}"),
]

bad = 0
for rel in PAGES:
    path = os.path.join(HERE, rel)
    page = open(path, encoding="utf-8").read()
    m = re.search(r"<style>\n(.*?)\n</style>", page, re.S)
    if not m:
        print(f"no <style> block in {rel}")
        bad += 1
        continue
    css = CSS
    if "check-dashboard" in rel:
        for old, new in PLANTS:
            if old not in css:
                print(f"{rel}: plant target not in stylesheet: {old}")
                bad += 1
            css = css.replace(old, new, 1)
    page = page[:m.start(1)] + css + page[m.end(1):]
    open(path, "w", encoding="utf-8").write(page)
    print(f"refreshed {rel}")
sys.exit(1 if bad else 0)
