#!/usr/bin/env python3
"""Prove each check_page.py --brief check can pass and fail.

Usage: python3 tests/check_page_brief.py

Builds small pages in a temp folder, runs skills/design/scripts/check_page.py --brief on each and
checks the output. Cases marked shots need playwright and its Chromium; without them they print SKIP
and the run exits 1, because a skipped check is not a pass. Standard library only.
"""
# Test text includes CJK on purpose: 600 four-character phrases should count as about 1,200 words.
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CHECK = os.path.join(os.path.dirname(HERE), "skills", "design", "scripts", "check_page.py")

HEAD = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1"><title>Test page</title>'
        '<style>body{font:16px/1.5 system-ui;margin:0;padding:0 16px}main{max-width:720px;margin:0 auto}'
        '.card{border:1px solid #ccc;padding:12px;border-radius:8px}.grid{display:grid;'
        'grid-template-columns:repeat(3,1fr);gap:12px}</style></head><body><main>')
TAIL = "</main></body></html>"
TREE = ('<svg viewBox="0 0 360 120" role="img" aria-label="tree"><rect x="140" y="4" width="80" height="30" fill="#ddd"/>'
        '<rect x="20" y="80" width="80" height="30" fill="#ddd"/><rect x="260" y="80" width="80" height="30" fill="#ddd"/>'
        '<text x="150" y="24" font-size="14">Start</text></svg>')


def words(n, word="word"):
    return " ".join([word] * n)


def page(body):
    return HEAD + '<h1>Test page</h1><p data-answer>Bottom line: ship it after one step.</p>' + body + TAIL


GOOD = page(f'<section data-shape="tree"><h2>Pick</h2>{TREE}</section>'
            f'<section data-shape="table"><h2>Checks</h2><table><tr><th>a</th></tr><tr><td>b</td></tr></table></section>')

CASES = [
    # (id, html, extra args, must contain, must not contain, exit code)
    ("good-passes", GOOD, [], ["pass", "brief:"], ["FAIL"], 0),
    ("no-brand-ok", GOOD, [], [], ["brand block not found"], 0),
    ("open-words-over", page(f'<section data-shape="text"><h2>Long</h2><p>{words(450)}</p></section>'), [],
     ["FAIL  brief: ", "open words"], [], 1),
    ("closed-details-not-counted",
     page(f'<section data-shape="text"><h2>Long</h2><p>{words(100)}</p><details><summary>More</summary>'
          f'<p>{words(600)}</p></details></section>'), [], ["pass"], ["open words over"], 0),
    ("open-details-counted",
     page(f'<section data-shape="text"><h2>Long</h2><details open><summary>More</summary><p>{words(450)}</p>'
          f'</details></section>'), [], ["open words"], [], 1),
    ("svg-words-not-counted",
     page('<section data-shape="flow"><h2>Flow</h2><svg viewBox="0 0 360 100">' +
          "".join(f'<text x="4" y="{i * 2}">{words(20)}</text>' for i in range(30)) + '</svg></section>'),
     [], ["pass"], ["open words over"], 0),
    ("drawn-shape-without-svg",
     page(f'<section data-shape="tree"><h2>Pick</h2><ul><li>a</li><li>b</li></ul></section>'), [],
     ["FAIL  brief: ", "data-shape=\"tree\"", "no <svg>"], [], 1),
    ("no-shapes-warns", page('<section><h2>Plain</h2><p>Short.</p></section>'), [],
     ["warn  brief: ", "data-shape"], [], 0),
    ("long-list-warns",
     page('<section data-shape="text"><h2>List</h2><ul>' + "".join(f"<li>item {i}</li>" for i in range(8)) +
          '</ul></section>'), [], ["warn  brief: ", "8 items"], [], 0),
    ("long-list-in-toggle-ok",
     page('<section data-shape="text"><h2>List</h2><details><summary>All</summary><ul>' +
          "".join(f"<li>item {i}</li>" for i in range(8)) + '</ul></details></section>'), [], [], ["8 items"], 0),
    ("text-cards-fail",
     page('<section data-shape="text"><h2>Cards</h2><div class="grid">' +
          "".join(f'<div class="card"><h3>Card {i}</h3><p>{words(40)}</p></div>' for i in range(3)) +
          '</div></section>'), ["--shots"], ["FAIL", "text in cards"], [], 1),
    ("answer-below-fold-fails",
     HEAD + '<h1>Test page</h1>' + f'<section data-shape="tree"><h2>Pick</h2>{TREE}</section>' +
     '<div style="height:1400px"></div><p data-answer>Bottom line far down.</p>' + TAIL,
     ["--shots"], ["FAIL", "data-answer"], [], 1),
    ("small-svg-text-warns",
     page('<section data-shape="flow"><h2>Wide</h2><svg viewBox="0 0 1400 200" style="width:100%">'
          '<rect x="0" y="0" width="200" height="60" fill="#ddd"/><text x="10" y="40" font-size="14">tiny label</text>'
          '<rect x="300" y="0" width="200" height="60" fill="#ddd"/></svg></section>'),
     ["--shots"], ["SVG text", "px"], [], 0),
    ("clipped-by-hidden-overflow-fails",
     HEAD.replace("</style>", "html,body{overflow-x:hidden}</style>") + '<h1>Test page</h1><p data-answer>Bottom line.</p>'
     f'<section data-shape="tree"><h2>Pick</h2>{TREE}</section>'
     '<p style="white-space:nowrap">open -a Safari "/a/very/long/path/that/keeps/going/far/past/the/edge/of/a/phone/screen.html"</p>' + TAIL,
     ["--shots"], ["FAIL", "cut off"], [], 1),
    ("wide-table-in-scroll-box-ok",
     page('<section data-shape="table"><h2>Grid</h2><div style="overflow-x:auto"><table style="min-width:900px">'
          '<tr><td>a</td><td>b</td></tr></table></div></section>'), ["--shots"], [], ["cut off"], 0),
    # Review fixes (each failed before its fix).
    ("no-warnings-under-W-error", GOOD, ["PYW", "--shots"], ["pass"], ["SyntaxError", "Warning"], 0),
    ("shape-on-svg-itself-ok",
     page('<section><h2>Flow</h2><svg data-shape="flow" viewBox="0 0 360 100"><rect x="0" y="0" width="100" height="40" fill="#ddd"/>'
          '<rect x="200" y="0" width="100" height="40" fill="#ddd"/></svg></section>'), [], ["pass"], ["no <svg>"], 0),
    ("icon-svg-is-not-a-figure",
     page('<section data-shape="tree"><h2>Pick</h2><p><svg viewBox="0 0 12 12" width="12" height="12"><circle cx="6" cy="6" r="5" fill="#ddd"/></svg> Start</p></section>'),
     [], ["FAIL  brief: ", "no <svg>"], [], 1),
    ("hidden-text-not-counted",
     page(f'<section data-shape="tree"><h2>Pick</h2>{TREE}</section><template><p>{words(500)}</p></template>'
          f'<div hidden>{words(500)}</div><div aria-hidden="true">{words(500)}</div><div style="display: none">{words(500)}</div>'),
     [], ["pass"], ["open words over", "open words,"], 0),
    ("first-screen-skips-closed-toggle",
     HEAD + '<h1>Test page</h1><p data-answer>Bottom line: ship it.</p>'
     f'<section data-shape="tree"><h2>Pick</h2>{TREE}</section><details><summary>More</summary><p>{words(300)}</p></details>' + TAIL,
     ["--shots"], ["pass"], ["words on the first phone screen"], 0),
    ("li-cards-fail",
     page('<section data-shape="text"><h2>Cards</h2><ul class="grid" style="list-style:none;padding:0">' +
          "".join(f'<li class="card"><b>Card {i}</b> {words(40)}</li>' for i in range(3)) + '</ul></section>'),
     ["--shots"], ["FAIL", "text in cards"], [], 1),
    ("a-cards-fail",
     page('<section data-shape="text"><h2>Cards</h2><div class="grid">' +
          "".join(f'<a class="card" href="#c{i}"><b>Card {i}</b> {words(40)}</a>' for i in range(3)) + '</div></section>'),
     ["--shots"], ["FAIL", "text in cards"], [], 1),
    ("cjk-words-counted",
     page('<section data-shape="text"><h2>Long</h2><p>' + " ".join(["检查页面"] * 600) + '</p></section>'),
     [], ["FAIL  brief: ", "open words"], [], 1),
    ("table-8-body-rows-warns",
     page('<section data-shape="table"><h2>T</h2><table><tr><th>a</th></tr>' + "<tr><td>b</td></tr>" * 8 + '</table></section>'),
     [], ["warn  brief: ", "8 rows"], [], 0),
    ("table-8-rows-no-header-warns",
     page('<section data-shape="table"><h2>T</h2><table>' + "<tr><td>b</td></tr>" * 8 + '</table></section>'),
     [], ["warn  brief: ", "8 rows"], [], 0),
    ("table-7-body-rows-ok",
     page('<section data-shape="table"><h2>T</h2><table><tr><th>a</th></tr>' + "<tr><td>b</td></tr>" * 7 + '</table></section>'),
     [], [], ["rows; split"], 0),
    ("good-passes-shots", GOOD, ["--shots"], ["pass"], ["FAIL"], 0),
]


def have_browser():
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
        return True
    except ImportError:
        return False


def main():
    bad, skipped = 0, 0
    browser = have_browser()
    with tempfile.TemporaryDirectory() as tmp:
        for cid, html, extra, must, must_not, code in CASES:
            if "--shots" in extra and not browser:
                print(f"SKIP  {cid} (playwright not installed)")
                skipped += 1
                continue
            f = os.path.join(tmp, cid + ".html")
            with open(f, "w", encoding="utf-8") as fh:
                fh.write(html)
            py = [sys.executable, "-W", "error"] if "PYW" in extra else [sys.executable]
            args = [x for x in extra if x != "PYW"]
            r = subprocess.run(py + [CHECK, f, "--brief", "--out", os.path.join(tmp, "shots")] + args,
                               capture_output=True, text=True, timeout=180)
            out = r.stdout + r.stderr
            missing = [m for m in must if m not in out]
            present = [m for m in must_not if m in out]
            ok = not missing and not present and r.returncode == code
            print(f"{'ok  ' if ok else 'BAD '}  {cid}" + ("" if ok else
                  f"\n      exit {r.returncode} (want {code}); missing {missing}; unwanted {present}\n"
                  + "\n".join("      | " + line for line in out.splitlines())))
            bad += not ok
    print(f"{len(CASES) - bad - skipped} ok, {bad} bad, {skipped} skipped")
    sys.exit(1 if bad or skipped else 0)


if __name__ == "__main__":
    main()
