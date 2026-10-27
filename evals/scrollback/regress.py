#!/usr/bin/env python3
"""Regression checks for skills/scrollback/scripts (check_scrollback.py, new_page.py).

Usage: python3 evals/scrollback/regress.py [--shots]   (exits 1 on any failure)
Starts from regress/good.html (a demo specimen using every component), plants one violation per
case in a temp copy, and checks the checker FAILs with the expected words. --shots adds the
render cases (needs playwright; run with `uv run --with playwright python ...`).
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.join(HERE, "..", "..", "skills", "scrollback")
CHECK = os.path.join(SKILL, "scripts", "check_scrollback.py")
NEW = os.path.join(SKILL, "scripts", "new_page.py")
GOOD = open(os.path.join(HERE, "regress", "good.html"), encoding="utf-8").read()
fails = []

# (name, old text, new text, expected words in a FAIL line; None means the page must pass)
CASES = [
    ("good specimen passes", None, None, None),
    ("radius", ".pill{", ".pill{border-radius:4px;", "radius must be 0"),
    ("radius zero is fine", ".pill{", ".pill{border-radius:0;", None),
    ("bold", ".cap{", ".cap{font-weight:700;", "weight is 400"),
    ("italic", ".cap{", ".cap{font-style:italic;", "no italics"),
    ("second font", ".cap{", ".cap{font-family:Georgia,serif;", "one monospace family"),
    ("shadow", ".doc{", ".doc{box-shadow:0 2px 8px var(--canvas);", "no shadows"),
    ("glow", ".ttl{", ".ttl{text-shadow:0 0 4px var(--accent);", "no shadows"),
    ("blur", ".doc{", ".doc{backdrop-filter:blur(4px);", "no blur"),
    ("plain gradient", ".doc{", ".doc{background-image:linear-gradient(var(--surface),var(--canvas));", "no gradients"),
    ("pure white", ".cap{", ".cap{color:#fff;", "pure white or black"),
    ("colour literal", ".cap{", ".cap{color:#33ff66;", "colour literal"),
    ("named colour", ".cap{", ".cap{color:green;", "colour literal"),
    ("literal in a custom property", ".cap{", ".cap{--x:#123456;", "colour literal outside the token block"),
    ("accent on links", "a{color:var(--bright)", "a{color:var(--accent)", "accent outside its three uses"),
    ("accent button fill", ".btn{", ".btn{background:var(--accent);", "accent outside its three uses"),
    ("accent inline on text", '<span class="cap">runs per week</span>', '<span class="cap" style="color:var(--accent)">runs per week</span>', "accent outside its three uses"),
    ("accent inline on a bar is a data mark", '<i style="height:22px">', '<i style="height:22px;background:var(--accent)">', None),
    ("animation", ".cap{", ".cap{animation:blink 1s steps(1) infinite;", "no animation"),
    ("keyframes", "/* layout helpers */", "@keyframes blink{50%{opacity:0}}", "no animation"),
    ("slow transition", "transition:color 120ms linear,border-color 120ms linear", "transition:color 300ms ease", "120ms"),
    ("token changed", "--accent:#2E8EFF;", "--accent:#22CC66;", "token --accent"),
    ("token missing", "--muted:#8A8781;", "", "token --muted is missing"),
    ("no tokens at all", ":root{", "#nothing{", "no Scrollback tokens"),
    ("emoji", "sync started", "sync started ✅", "emoji"),
    ("check mark dingbat", "sync started", "sync started ✓", "emoji"),
    ("lorem", "Rerun after the schema change is mapped.", "Lorem ipsum dolor sit amet.", "lorem ipsum"),
    ("nested frame", '<div class="rows wide">\n      <div class="log">',
     '<div class="rows wide">\n      <section class="frame"><h2 class="ttl">x</h2></section>\n      <div class="log">', "nested frame"),
    ("signal in a document", '<span class="br">Demo Supplies Ltd</span>',
     '<span class="br">Demo Supplies Ltd</span><span class="pill fail">overdue</span>', "signal colour inside a document"),
    ("legend", '<span class="cap">runs per week</span>', '<span class="legend">a b</span>', "legend"),
    ("chart without label", 'role="img" aria-label="Runs per week, 6 weeks, rising from 22 to 88; latest 88"', "", "has no role"),
    ("svg without label", 'role="img" aria-label="Sync latency, 14 days, flat near 8ms then rising to 21ms on the last day"', "", "has no role"),
    ("svg colour literal", 'stroke="var(--muted)"', 'stroke="#8A8781"', "survives the paper palette"),
    ("no lang", '<html lang="en">', "<html>", "lang"),
    ("no viewport", '<meta name="viewport" content="width=device-width,initial-scale=1">', "", "viewport"),
    ("missing linked stylesheet", "</head>", '<link rel="stylesheet" href="styles/missing.css">\n</head>', "not found"),
    # Fable review round 1: false passes
    ("accent on a second selector", "/* layout helpers */", ".ttl,.cta{color:var(--accent)}", "accent outside"),
    ("accent on a class that only starts like an allowed one", "/* layout helpers */", ".marketing-banner{color:var(--accent)}", "accent outside"),
    ("accent on .filler", "/* layout helpers */", ".filler{background:var(--accent)}", "accent outside"),
    ("accent through an alias", "/* layout helpers */", ":root{--blue:var(--accent)} .btn2{background:var(--blue)}", "accent outside"),
    ("accent through a chained alias", "/* layout helpers */", ".x{--a1:var(--accent);--a2:var(--a1)} .y{color:var(--a2)}", "accent outside"),
    ("breaks inside @container", "/* layout helpers */", "@container (min-width:0){.btn2{border-radius:9px;font-weight:700}}", "radius must be 0"),
    ("named colour tomato", ".cap{", ".cap{color:tomato;", "colour literal"),
    ("emoji in CSS content", ".cap{", '.cap{content:"\u2705";', "generated content"),
    ("emoji in aria-label", 'aria-label="Runs per week', 'aria-label="\U0001F680 Runs per week', "emoji or pictograph in aria-label"),
    ("svg blur filter", "<polyline", '<filter id="g"><feGaussianBlur stdDeviation="2"/></filter><polyline', "no blur"),
    ("svg gradient", "<polyline", '<linearGradient id="lg"></linearGradient><polyline', "gradient"),
    ("variable-font weight", ".cap{", '.cap{font-variation-settings:"wght" 700;', "weight is 400"),
    ("non-colour transition", "transition:color 120ms linear,border-color 120ms linear", "transition:opacity 120ms linear", "colour only"),
    ("transition on all", "transition:color 120ms linear,border-color 120ms linear", "transition:120ms linear", "colour only"),
    ("signal colour on a chart bar", '<i style="height:22px">', '<i style="height:22px;background:var(--signal-fail)">', "signal colour on a chart"),
    ("legend by another class name", '<span class="cap">runs per week</span>', '<span class="chart-legend">a b</span>', "legend"),
    ("paper token changed", "--accent:#1660C8", "--accent:#2E8EFF", "paper token --accent"),
    ("print palette removed", "@media print{", "@media speech{", "no @media print palette"),
    # Fable review round 1: false fails
    ("calc(0px) radius is fine", ".pill{", ".pill{border-radius:calc(0px);", None),
    ("120ms written as .12s is fine", "transition:color 120ms linear,border-color 120ms linear", "transition:color .12s linear,border-color 120ms linear 0s", None),
    ("a brace inside a CSS string doesn't hide later rules", "/* layout helpers */", '.q::before{content:"{"} .q{font-weight:700}', "weight is 400"),
]
RENDER = [
    ("wide nowrap pushes the page sideways", '<span class="br">48,200 rows</span>',
     '<span class="br nw">' + "x" * 200 + "</span>", "scrolls sideways"),
    ("inline meter fill renders empty", ".meter .fill{display:block;", ".meter .fill{display:inline;", "render empty"),
    ("command block lost white-space:pre", ".cmd,pre{margin:0;", ".cmd,pre{white-space:normal!important;margin:0;", "lost their line breaks"),
]


def run(*args, cwd=None):
    p = subprocess.run([sys.executable, *args], capture_output=True, text=True, cwd=cwd,
                       env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    return p.returncode, p.stdout + p.stderr


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {detail[:400]}"))
    if not ok:
        fails.append(name)


def page_case(tmp, name, old, new, want, shots=False):
    src = GOOD
    if old is not None:
        if old not in src:
            check(name, False, f"planted text not found: {old[:60]}")
            return
        src = src.replace(old, new, 1)
    path = os.path.join(tmp, "page.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(src)
    args = [CHECK, path] + (["--shots", "--out", os.path.join(tmp, "shots")] if shots else [])
    code, out = run(*args)
    fail_lines = [l for l in out.splitlines() if l.startswith("FAIL")]
    if want is None:
        check(name, code == 0 and not fail_lines, out)
    else:
        check(name, code == 1 and any(want.lower() in l.lower() for l in fail_lines), out)


tmp = tempfile.mkdtemp(prefix="sb-regress-")
try:
    for name, old, new, want in CASES:
        page_case(tmp, name, old, new, want)

    # --allow-tokens: a changed token warns, and the floors run on the new values
    low = GOOD.replace("--muted:#8A8781;", "--muted:#4A4844;", 1)
    p = os.path.join(tmp, "low.html")
    open(p, "w", encoding="utf-8").write(low)
    code, out = run(CHECK, p, "--allow-tokens")
    check("--allow-tokens runs the floors on changed tokens", code == 1 and "WARN token --muted" in out
          and "under 4.5:1" in out, out)

    # palette
    code, out = run(CHECK, "--palette")
    check("shipped palette holds every floor", code == 0 and "all floors held" in out, out)
    css = open(os.path.join(SKILL, "assets", "scrollback.css"), encoding="utf-8").read()
    bad = os.path.join(tmp, "bad.css")
    open(bad, "w", encoding="utf-8").write(css.replace("--accent:#1660C8", "--accent:#2E8EFF", 1))
    code, out = run(CHECK, "--palette", bad)
    check("palette fails the screen accent on paper", code == 1 and "paper --accent" in out, out)

    # local @import is read; a remote non-font stylesheet is reported
    os.makedirs(os.path.join(tmp, "css"), exist_ok=True)
    open(os.path.join(tmp, "css", "extra.css"), "w").write(".z{border-radius:6px}")
    imp = GOOD.replace("/* layout helpers */", '@import url("css/extra.css");', 1)
    p = os.path.join(tmp, "imp.html")
    open(p, "w", encoding="utf-8").write(imp)
    code, out = run(CHECK, p)
    check("a local @import is read", code == 1 and "radius must be 0" in out and "extra.css" in out, out)
    rem = GOOD.replace("</head>", '<link rel="stylesheet" href="https://cdn.example.com/x.css">\n</head>', 1)
    open(p, "w", encoding="utf-8").write(rem)
    code, out = run(CHECK, p)
    check("a remote stylesheet is reported as unchecked", "WARN linked stylesheet https://cdn.example.com/x.css is remote" in out, out)
    code, out = run(CHECK, "--palette", os.path.join(tmp, "nope.css"))
    check("--palette on a missing file exits 2", code == 2, out)

    # the shipped stylesheet keeps --rule off text (only decorative glyphs and a disabled control)
    import re
    rule_text = [m.group(1) for m in re.finditer(r"([^{}]+)\{[^}]*(?<![-\w])color:var\(--rule\)", css)]
    allowed = (".frame > .c", ".mast .wm .bk", ".btn[disabled]")
    check("--rule is text only on glyphs and disabled controls",
          all(x.strip() in allowed for x in rule_text), str(rule_text))
    check("print keeps backgrounds", "print-color-adjust:exact" in css)

    # new_page.py
    np = os.path.join(tmp, "new", "status.html")
    code, out = run(NEW, np, "--title", "Demo <status>")
    made = open(np, encoding="utf-8").read() if os.path.exists(np) else ""
    check("new_page writes an inlined page", code == 0 and "--canvas:#11110F" in made and "Demo &lt;status&gt;" in made, out)
    code, out = run(CHECK, np)
    check("a fresh starter page passes", code == 0, out)
    code, out = run(NEW, np)
    check("new_page refuses to overwrite", code == 1 and "not overwriting" in out, out)

    # brand export parses as design-skill tokens
    import json
    tok = json.load(open(os.path.join(SKILL, "references", "brand", "tokens.json"), encoding="utf-8"))
    check("brand export carries primary and background", tok.get("primary") == "#2E8EFF" and tok.get("background") == "#11110F")

    if "--shots" in sys.argv:
        page_case(tmp, "good specimen passes the render check", None, None, None, shots=True)
        for name, old, new, want in RENDER:
            page_case(tmp, name, old, new, want, shots=True)
        # printing keeps the bars: with print media, a bar still paints its background
        try:
            from playwright.sync_api import sync_playwright
            gp = os.path.join(tmp, "print.html")
            open(gp, "w", encoding="utf-8").write(GOOD)
            with sync_playwright() as pw:
                try:
                    b = pw.chromium.launch()
                except Exception:
                    b = pw.chromium.launch(args=["--single-process", "--no-zygote"])
                pg = b.new_page()
                pg.goto("file://" + gp)
                pg.emulate_media(media="print")
                got = pg.evaluate("""() => { const i = document.querySelector('.bars > i');
                    const cs = getComputedStyle(i); return [cs.printColorAdjust || cs.webkitPrintColorAdjust, cs.backgroundColor]; }""")
                b.close()
            check("print media keeps bar backgrounds (print-color-adjust exact, paper accent)",
                  got[0] == "exact" and got[1] == "rgb(22, 96, 200)", str(got))
        except ImportError:
            check("print render case needs playwright", False)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print(f"\n{'FAILED' if fails else 'all passed'}: {len(fails)} failing")
sys.exit(1 if fails else 0)
