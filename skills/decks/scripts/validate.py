#!/usr/bin/env python3
"""Validate a slide deck built from assets/template.html before handing it over.

Usage: python3 scripts/validate.py <deck.html> [--shots]

Checks, in order:
  1. The file is complete: ends with </html>, script tags balance, the engine is intact.
  2. The brand slot was filled by scripts/apply_brand.py (a brand-source marker is present).
  3. Every slide has exactly one h1 or h2 (a quote slide has a blockquote instead); no template placeholder text is left; a points slide has
     at most five bullets; a chart slide has at most one hero bar and a source line; nothing is
     loaded from outside the file.
  Headlines over 15 words and open [NEEDS YOUR INPUT] markers are listed as warnings.
--shots renders every slide with playwright, writes <name>-NN.png, and fails any slide whose content
overflows it. If screenshots were asked for and not written, that is a FAIL, never a skip.

Standard library only (playwright only for --shots). Exit code 1 on any FAIL.
"""
import pathlib
import re
import sys

ENGINE = ["function go(n)", "function fit()", "</body>"]
PLACEHOLDERS = ["Deck title as a claim", "One sentence the audience should remember", "A claim that the points below",
                "First supporting point", "A claim that compares two things", "What the number means",
                "The chart's takeaway", "A short quotation, exactly as said", "The one thing to do next",
                "DECK TITLE", "Presenter name, date"]


def structural(raw):
    problems = []
    if not raw.rstrip().endswith("</html>"):
        problems.append("file does not end with </html>; it was probably cut off while being written")
    if raw.count("<script") != raw.count("</script>"):
        problems.append("script tags do not balance; the engine block is not closed")
    for s in ENGINE:
        if s not in raw:
            problems.append(f"engine marker missing: {s!r}; copy the template again and edit only the slides")
    return problems


def brand(raw):
    m = re.search(r'<style id="brand">(.*?)</style>', raw, re.S)
    if not m:
        return ["no brand slot; start from assets/template.html"]
    if "brand-source:" not in m.group(1):
        return ["brand slot not filled; run python3 scripts/apply_brand.py on this file"]
    return []


def text(fragment):
    return " ".join(re.sub(r"<[^>]+>", " ", fragment).split())


def slides(raw):
    problems, warnings = [], []
    html = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
    found = re.findall(r'<section class="slide\s*([\w-]*)[^"]*"[^>]*>(.*?)</section>', html, re.S)
    if not found:
        return ["no slides found"], [], 0
    for i, (kind, body) in enumerate(found, 1):
        heads = re.findall(r"<h([12])[^>]*>(.*?)</h\1>", body, re.S)
        if kind == "quote":
            if "<blockquote" not in body or heads:
                problems.append(f"slide {i} (quote): needs one <blockquote> and no headline")
        elif len(heads) != 1:
            problems.append(f"slide {i} ({kind}): has {len(heads)} headlines (h1/h2); it needs exactly one")
        elif len(text(heads[0][1]).split()) > 15:
            warnings.append(f"slide {i}: headline is {len(text(heads[0][1]).split())} words; aim for 15 or fewer")
        if kind == "points" and body.count("<li") > 5:
            problems.append(f"slide {i}: {body.count('<li')} bullets; five at most, or split the slide")
        if kind == "chart":
            if len(re.findall(r'class="bar hero"', body)) > 1:
                problems.append(f"slide {i}: more than one hero bar; give the accent to one bar only")
            if "Source" not in body:
                problems.append(f"slide {i}: chart has no source line")
        if "NEEDS YOUR INPUT" in body:
            warnings.append(f"slide {i}: has a [NEEDS YOUR INPUT] marker for the author")
    for p in PLACEHOLDERS:
        if p in html:
            problems.append(f"template placeholder left in: {p!r}")
    for m in re.findall(r'(?:src|href)\s*=\s*"(https?:[^"]+)"|url\(\s*["\']?(https?:[^)"\']+)', html):
        url = m[0] or m[1]
        if not re.search(r'<a\s[^>]*href="' + re.escape(url), html):
            problems.append(f"loads something from outside the file: {url}")
    return problems, warnings, len(found)


# Some agent sandboxes (on macOS among others) stop Chromium's helper processes from starting.
# Running it as one process avoids that, so try the normal launch first and then that.
SAFE_ARGS = ["--single-process", "--no-zygote"]


def launch(pw):
    try:
        return pw.chromium.launch()
    except Exception as first:
        if "Executable doesn't exist" in str(first):
            raise RuntimeError("playwright's Chromium is missing or doesn't match this playwright version; "
                               "install it with: python3 -m playwright install chromium "
                               "(use the same Python that runs this script)") from None
        return pw.chromium.launch(args=SAFE_ARGS)


def shots(path, count):
    p = pathlib.Path(path)
    for old in p.parent.glob(p.stem + "-[0-9][0-9].png"):
        old.unlink()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return ["--shots asked for but playwright is not installed; no screenshots were taken"]
    problems, written = [], []
    try:
        with sync_playwright() as pw:
            b = launch(pw)
            page = b.new_page(viewport={"width": 1600, "height": 900})
            page.goto(p.resolve().as_uri())
            page.wait_for_timeout(300)
            for i in range(count):
                page.evaluate(f"go({i})")
                page.wait_for_timeout(150)
                over = page.evaluate("""() => { const s = document.querySelector('.slide.active');
                    return s.scrollHeight > s.clientHeight + 2 || s.scrollWidth > s.clientWidth + 2; }""")
                if over:
                    problems.append(f"slide {i + 1}: content overflows the slide; cut text or split it")
                png = p.with_name(f"{p.stem}-{i + 1:02d}.png")
                page.screenshot(path=str(png))
                written.append(png)
            b.close()
    except Exception as e:
        return [f"--shots asked for but the capture failed: {type(e).__name__}: {str(e).splitlines()[0] if str(e) else ''}"]
    if len(written) != count or any(w.stat().st_size == 0 for w in written):
        problems.append("not every slide was captured")
    print(f"  wrote {len(written)} screenshots ({p.stem}-01.png ...); open them and look before handing over")
    return problems


def main():
    paths = [a for a in sys.argv[1:] if not a.startswith("-")]
    if len(paths) != 1:
        print(__doc__)
        sys.exit(2)
    path = paths[0]
    raw = pathlib.Path(path).read_text(encoding="utf-8")
    print(path)
    problems = structural(raw)
    if problems:
        for pr in problems:
            print(f"  FAIL  {pr}")
        sys.exit(1)
    problems = brand(raw)
    more, warnings, count = slides(raw)
    problems += more
    print(f"  {count} slides")
    for w in warnings:
        print(f"  warn  {w}")
    if "--shots" in sys.argv and count:
        problems += shots(path, count)
    for pr in problems:
        print(f"  FAIL  {pr}")
    if not problems:
        print("  pass  complete, branded, one headline per slide, nothing loaded from outside")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
