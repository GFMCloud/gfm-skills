#!/usr/bin/env python3
"""Check a designed page before handing it over.

Usage: python3 scripts/check_page.py <page.html | http://localhost:...> [--shots] [--out <folder>]

For a file, it checks the source:
  - complete (ends with </html>), has lang, a <title> and a viewport meta tag
  - the brand block from scripts/brand.py is in the page or a local stylesheet it links
  - no placeholder text or placeholder-image services; every <img> has alt; every field has a label
  - focus outlines are not removed without a :focus-visible style
  Warnings: more than 8 font sizes, things loaded from outside the file, open [NEEDS YOUR INPUT].
--shots renders the page (file or URL) with playwright at 1280px and 390px wide, writes full-page
<name>-desktop.png and <name>-phone.png into .design-check/ beside the file (or --out), and fails on horizontal
scroll at either width or on script errors. It warns about text under 14px and tap targets under
44px at phone width. If screenshots were asked for and not written, that is a FAIL, never a skip.

Standard library only (playwright only for --shots). Exit code 1 on any FAIL.
"""
import pathlib
import re
import sys
import urllib.parse

PLACEHOLDER_TEXT = re.compile(r"lorem ipsum|dolor sit amet|your (headline|tagline|text) here|\bTODO\b|\bTBD\b", re.I)
PLACEHOLDER_IMG = re.compile(r"placehold\.co|placeholder\.com|picsum\.photos|placekitten|dummyimage\.com|source\.unsplash\.com", re.I)


def strip_comments(raw):
    return re.sub(r"<!--.*?-->", "", raw, flags=re.S)


def local_css(path, html):
    out = ""
    for href in re.findall(r'<link[^>]+rel="?stylesheet"?[^>]*href="([^"]+)"', html, re.I) + \
            re.findall(r'<link[^>]+href="([^"]+)"[^>]*rel="?stylesheet"?', html, re.I):
        if re.match(r"(https?:)?//", href):
            continue
        f = (path.parent / urllib.parse.unquote(href.split("?")[0])).resolve()
        if f.is_file():
            out += f.read_text(encoding="utf-8", errors="replace")
    return out


def source_checks(path):
    raw = path.read_text(encoding="utf-8", errors="replace")
    problems, warnings = [], []
    if not raw.rstrip().lower().endswith("</html>"):
        problems.append("file does not end with </html>; it was probably cut off while being written")
    html = strip_comments(raw)
    css = local_css(path, html)
    styles = "".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S | re.I)) + css
    if not re.search(r"<html[^>]*\blang=", html, re.I):
        problems.append("<html> has no lang attribute")
    t = re.search(r"<title>(.*?)</title>", html, re.S | re.I)
    if not t or not t.group(1).strip():
        problems.append("no <title>, or it is empty")
    if not re.search(r'<meta[^>]+name="viewport"', html, re.I):
        problems.append("no viewport meta tag; the page will render zoomed out on phones")
    if "brand-source:" not in raw + css:
        problems.append("brand block not found; run python3 scripts/brand.py and paste its :root block into the CSS")
    body = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.S | re.I)
    m = PLACEHOLDER_TEXT.search(re.sub(r"<[^>]+>", " ", body))
    if m:
        problems.append(f"placeholder text left in: {m.group(0)!r}")
    m = PLACEHOLDER_IMG.search(html)
    if m:
        problems.append(f"placeholder image service used: {m.group(0)}")
    for img in re.findall(r"<img\b[^>]*>", html, re.I):
        if not re.search(r"\balt=", img, re.I):
            problems.append(f"image without alt: {img[:80]}")
    labelled = set(re.findall(r'<label[^>]+for="([^"]+)"', html, re.I))
    wrapped = " ".join(re.findall(r"<label\b.*?</label>", html, re.S | re.I))
    for field in re.findall(r"<(?:input|select|textarea)\b[^>]*>", html, re.I):
        if re.search(r'type="?(hidden|submit|button|reset|image)"?', field, re.I):
            continue
        fid = re.search(r'\bid="([^"]+)"', field)
        if (fid and fid.group(1) in labelled) or field in wrapped or re.search(r"aria-label(ledby)?=", field, re.I):
            continue
        problems.append(f"field without a label: {field[:80]}")
    if re.search(r"outline\s*:\s*(none|0)\b", styles) and ":focus-visible" not in styles:
        problems.append("focus outline removed and no :focus-visible style replaces it")
    sizes = set(re.findall(r"font-size\s*:\s*([^;}\n]+)", styles))
    if len(sizes) > 8:
        warnings.append(f"{len(sizes)} different font-size values; aim for five or fewer from one scale")
    for url in re.findall(r'<(?:script|link|img|iframe)[^>]+(?:src|href)="((?:https?:)?//[^"]+)"', html, re.I):
        if "fonts.googleapis.com" not in url and "fonts.gstatic.com" not in url:
            warnings.append(f"loads from outside the file: {url}")
    n = raw.count("NEEDS YOUR INPUT")
    if n:
        warnings.append(f"{n} open [NEEDS YOUR INPUT] marker(s) for the author")
    return problems, warnings


# Some agent sandboxes (on macOS among others) stop Chromium's helper processes from starting.
# Running it as one process avoids that, so try the normal launch first and then that.
SAFE_ARGS = ["--single-process", "--no-zygote"]

MEASURE = """() => {
  const doc = document.documentElement, vis = e => { const r = e.getBoundingClientRect(), s = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  let small = 0, tiny = [];
  for (const e of document.querySelectorAll('body *')) {
    const own = [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (own && vis(e) && parseFloat(getComputedStyle(e).fontSize) < 14) small++;
  }
  for (const e of document.querySelectorAll('a[href], button, input:not([type=hidden]), select, textarea, [role=button]')) {
    // A checkbox or radio is tapped through its label, so measure that when there is one.
    const lab = /^(checkbox|radio)$/.test(e.type) && (e.closest('label') || (e.id && document.querySelector(`label[for="${e.id}"]`)));
    const r = (lab || e).getBoundingClientRect(), b = e.getBoundingClientRect();
    const onScreen = b.right > 0 && b.left < window.innerWidth && b.bottom > -window.scrollY;  // skip links sit off-screen
    if (vis(e) && onScreen && (r.height < 44 || r.width < 44) && !e.closest('p, li')) tiny.push((e.innerText || e.name || e.tagName).trim().slice(0, 30));
  }
  return { over: doc.scrollWidth - window.innerWidth, small, tiny };
}"""


def launch(pw):
    try:
        return pw.chromium.launch()
    except Exception as first:
        if "Executable doesn't exist" in str(first):
            raise RuntimeError("playwright's Chromium is missing or doesn't match this playwright version; "
                               "install it with: python3 -m playwright install chromium "
                               "(use the same Python that runs this script)") from None
        return pw.chromium.launch(args=SAFE_ARGS)


def shots(target, out, stem):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return ["--shots asked for but playwright is not installed; no screenshots were taken"], []
    problems, warnings, written = [], [], []
    try:
        with sync_playwright() as pw:
            b = launch(pw)
            # One page, resized: in single-process mode, closing a page can close the browser.
            page = b.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e).splitlines()[0] if str(e) else "error"))
            for label, w, h in (("desktop", 1280, 800), ("phone", 390, 844)):
                errors.clear()
                page.set_viewport_size({"width": w, "height": h})
                page.goto(target)
                page.wait_for_timeout(400)
                m = page.evaluate(MEASURE)
                if m["over"] > 1:
                    problems.append(f"{label} ({w}px): page scrolls sideways by {m['over']}px")
                for e in errors:
                    problems.append(f"{label}: script error: {e}")
                if label == "phone":
                    if m["small"]:
                        warnings.append(f"phone: {m['small']} text element(s) under 14px")
                    if m["tiny"]:
                        warnings.append(f"phone: tap targets under 44px: {', '.join(m['tiny'][:6])}")
                png = out / f"{stem}-{label}.png"
                page.screenshot(path=str(png), full_page=True)
                written.append(png)
            b.close()
    except Exception as e:
        return [f"--shots asked for but the capture failed: {type(e).__name__}: {str(e).splitlines()[0] if str(e) else ''}"], []
    if len(written) != 2 or any(p.stat().st_size == 0 for p in written):
        problems.append("not every screenshot was written")
    else:
        print(f"  wrote {written[0]} and {written[1]}; open both and look before handing over")
    return problems, warnings


def main():
    args = sys.argv[1:]
    out = None
    if "--out" in args:
        i = args.index("--out")
        if i + 1 >= len(args):
            print(__doc__)
            sys.exit(2)
        out = pathlib.Path(args[i + 1])
        del args[i:i + 2]
    targets = [a for a in args if not a.startswith("--")]
    if len(targets) != 1:
        print(__doc__)
        sys.exit(2)
    target = targets[0]
    print(target)
    problems, warnings = [], []
    if re.match(r"https?://", target):
        url, stem = target, re.sub(r"\W+", "-", urllib.parse.urlparse(target).netloc + urllib.parse.urlparse(target).path).strip("-") or "page"
        out = out or pathlib.Path.cwd() / ".design-check"
        if "--shots" not in args:
            print("  FAIL  a URL can only be checked with --shots")
            sys.exit(1)
    else:
        path = pathlib.Path(target)
        if not path.is_file():
            print(f"  FAIL  no such file: {target}")
            sys.exit(1)
        problems, warnings = source_checks(path)
        url, stem = path.resolve().as_uri(), path.stem
        out = out or path.parent / ".design-check"
    if "--shots" in args:
        out.mkdir(parents=True, exist_ok=True)
        p, w = shots(url, out, stem)
        problems += p
        warnings += w
    for w in warnings:
        print(f"  warn  {w}")
    for p in problems:
        print(f"  FAIL  {p}")
    if not problems:
        print("  pass  " + ("source checks" if not re.match(r"https?://", target) else "") +
              (" and no sideways scroll at 1280px or 390px" if "--shots" in args else ""))
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
