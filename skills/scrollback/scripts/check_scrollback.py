#!/usr/bin/env python3
"""Check a page against the Scrollback rules, and the palette against its contrast floors.

Usage:
  python3 <skill>/scripts/check_scrollback.py <page.html> [--shots] [--out <dir>] [--allow-tokens]
  python3 <skill>/scripts/check_scrollback.py --palette [<file.css or page.html>]

Page check: reads the HTML, its <style> blocks, style="" attributes and any local stylesheet it
links, and reports FAIL (breaks the system) and WARN lines. It checks the tokens against the
shipped stylesheet, radius, weight, italics, shadows, plain gradients, pure white or black, colour
literals outside the token blocks, the accent budget, emoji, nested frames, signal colours inside a
document, chart text alternatives, animation, lang and viewport.

--shots also renders the page at 1280px and 375px wide (needs playwright; try
`uv run --with playwright python <this script> ...`), fails sideways page scroll, meters that
render empty and multi-line blocks that lost their line breaks, and saves two screenshots to
.scrollback-check/ beside the page (or --out). HTTP requests other than the page's own files are
aborted and host names don't resolve, so the web font is not fetched.

--palette prints WCAG contrast ratios for the screen and paper palettes and fails any floor.
--allow-tokens turns a changed token into a WARN and runs the floors on the page's own values; use
it only when the user asked for a changed palette.

Exit 0 when nothing FAILs, 1 when something does, 2 on bad usage. Standard library only, except
playwright for --shots. It catches slips, not intent: a page can pass and still read badly.
"""
import html.parser
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SHIPPED_CSS = os.path.join(HERE, "..", "assets", "scrollback.css")
SAFE_ARGS = ["--single-process", "--no-zygote"]
# no name resolves, so nothing but the page's own files can load even if a request slips past the route
NO_DNS = ["--host-resolver-rules=MAP * ~NOTFOUND"]

TOKENS = ["--canvas", "--surface", "--rule", "--muted", "--text", "--bright", "--accent",
          "--rule-dim", "--signal-warn", "--signal-fail"]
# (foreground, background, floor, what it protects)
SCREEN_FLOORS = [
    ("--muted", "--canvas", 4.5, "captions on the page"),
    ("--muted", "--surface", 4.5, "captions on a panel"),
    ("--text", "--canvas", 4.5, "body text"),
    ("--text", "--surface", 4.5, "body text on a panel"),
    ("--bright", "--canvas", 4.5, "emphasis"),
    ("--accent", "--canvas", 4.5, "frame titles"),
    ("--accent", "--canvas", 3.0, "focus outline (non-text)"),
    ("--signal-warn", "--canvas", 4.5, "warn word"),
    ("--signal-fail", "--canvas", 4.5, "fail word"),
    ("--muted", "--canvas", 3.0, "field and button edges (non-text)"),
]
PAPER_FLOORS = [
    ("--muted", "--canvas", 4.5, "captions on paper"),
    ("--text", "--canvas", 4.5, "body text on paper"),
    ("--bright", "--canvas", 4.5, "emphasis on paper"),
    ("--accent", "--canvas", 4.5, "frame titles on paper"),
    ("--signal-warn", "--canvas", 4.5, "warn word on paper"),
    ("--signal-fail", "--canvas", 4.5, "fail word on paper"),
]
# Selectors allowed to spend the accent: frame title, data marks (bars, meter fill, sparkline, spec
# brackets, live pill) and focus. Each comma-separated part of a selector must name one of them.
ACCENT_OK = re.compile(r"(\.ttl|\.bars|\.fill|\.k|\.pill\.live|\.spark|:focus(-visible|-within)?)(?![\w-])")
CHART_MARK = re.compile(r"(\.bars|\.spark)(?![\w-])")
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")
FUNC_COLOUR = re.compile(r"\b(rgba?|hsla?|hwb|oklch|oklab|lab|lch|color)\(", re.I)
# every CSS named colour (CSS Color 4), so `tomato` or `aqua` can't slip past
NAMED_LIST = """aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue blueviolet brown
burlywood cadetblue chartreuse chocolate coral cornflowerblue cornsilk crimson cyan darkblue darkcyan darkgoldenrod
darkgray darkgreen darkgrey darkkhaki darkmagenta darkolivegreen darkorange darkorchid darkred darksalmon
darkseagreen darkslateblue darkslategray darkslategrey darkturquoise darkviolet deeppink deepskyblue dimgray dimgrey
dodgerblue firebrick floralwhite forestgreen fuchsia gainsboro ghostwhite gold goldenrod gray green greenyellow grey
honeydew hotpink indianred indigo ivory khaki lavender lavenderblush lawngreen lemonchiffon lightblue lightcoral
lightcyan lightgoldenrodyellow lightgray lightgreen lightgrey lightpink lightsalmon lightseagreen lightskyblue
lightslategray lightslategrey lightsteelblue lightyellow lime limegreen linen magenta maroon mediumaquamarine
mediumblue mediumorchid mediumpurple mediumseagreen mediumslateblue mediumspringgreen mediumturquoise
mediumvioletred midnightblue mintcream mistyrose moccasin navajowhite navy oldlace olive olivedrab orange orangered
orchid palegoldenrod palegreen paleturquoise palevioletred papayawhip peachpuff peru pink plum powderblue purple
rebeccapurple red rosybrown royalblue saddlebrown salmon sandybrown seagreen seashell sienna silver skyblue
slateblue slategray slategrey snow springgreen steelblue tan teal thistle tomato turquoise violet wheat white
whitesmoke yellow yellowgreen""".split()
NAMED = re.compile(r"(?<![-\w.#])(" + "|".join(NAMED_LIST) + r")(?![-\w])", re.I)
COLOUR_PROPS = re.compile(r"^(color|background(-color)?|border(-(top|right|bottom|left))?(-color)?|outline(-color)?|"
                          r"text-decoration(-color)?|fill|stroke|caret-color|column-rule(-color)?|accent-color|"
                          r"box-shadow|text-shadow|stop-color|flood-color|lighting-color)$")
SAFE_TRANSITION = {"color", "background-color", "border-color", "text-decoration-color", "outline-color", "fill",
                   "stroke", "border-top-color", "border-right-color", "border-bottom-color", "border-left-color"}
SKIP_AT = ("@keyframes", "@-webkit-keyframes", "@font-face", "@page", "@property", "@counter-style",
           "@font-feature-values")
EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u26FF\u2700-\u27BF\u2B50\u2B55\uFE0F]")
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


# ---------- CSS ----------

def strip_comments(css):
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


STRING = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'')


def mask_strings(css):
    """Same text with the inside of every quoted string blanked, so braces in strings don't count."""
    return STRING.sub(lambda m: m.group(0)[0] + "_" * (len(m.group(0)) - 2) + m.group(0)[-1], css)


def rules(css, context=""):
    """Yield (context, selector, declarations) for every rule, walking into every block at-rule
    (@media, @supports, @layer, @container, @scope ...) except keyframes, font-face and page."""
    css = strip_comments(css)
    masked = mask_strings(css)
    i, n = 0, len(css)
    while i < n:
        j = masked.find("{", i)
        if j < 0:
            return
        head = css[i:j].strip()
        depth, k = 1, j + 1
        while k < n and depth:
            if masked[k] == "{":
                depth += 1
            elif masked[k] == "}":
                depth -= 1
            k += 1
        body = css[j + 1:k - 1]
        # a statement at-rule (@import ...;) can sit in front of the head
        head = head.split(";")[-1].strip()
        if head.startswith(("@keyframes", "@-webkit-keyframes")):
            yield (head, head, "")
        elif head.startswith(SKIP_AT):
            pass
        elif head.startswith("@"):
            yield from rules(body, (context + " " + head).strip())
        else:
            yield (context, head, body)
        i = k


def decls(body):
    out = []
    masked = mask_strings(body)
    parts, start = [], 0
    for m in re.finditer(";", masked):
        parts.append(body[start:m.start()])
        start = m.end()
    parts.append(body[start:])
    for part in parts:
        if ":" in part:
            p, v = part.split(":", 1)
            out.append((p.strip().lower(), v.strip()))
    return out


def tokens_from(css, print_only=False):
    found = {}
    for ctx, sel, body in rules(css):
        if sel.strip() != ":root":
            continue
        if ("print" in ctx) != print_only:
            continue
        for p, v in decls(body):
            if p in TOKENS:
                found[p] = v.upper()
    return found


# ---------- contrast ----------

def lum(hexv):
    h = hexv.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        return None
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * out[0] + 0.7152 * out[1] + 0.0722 * out[2]


def ratio(a, b):
    la, lb = lum(a), lum(b)
    if la is None or lb is None:
        return None
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def palette_report(screen, paper, fails, label=""):
    lines = []
    for name, pal, floors in (("screen", screen, SCREEN_FLOORS), ("paper", paper, PAPER_FLOORS)):
        if not pal:
            continue
        for fg, bg, floor, what in floors:
            if fg not in pal or bg not in pal:
                fails.append(f"palette{label}: {name} palette has no {fg if fg not in pal else bg}")
                continue
            r = ratio(pal[fg], pal[bg])
            if r is None:
                fails.append(f"palette{label}: {fg} or {bg} is not a 3- or 6-digit hex value")
                continue
            ok = r >= floor
            lines.append(f"  {name:6} {fg:14} on {bg:10} {r:5.2f}:1  floor {floor}:1  {'pass' if ok else 'FAIL'}  ({what})")
            if not ok:
                fails.append(f"palette{label}: {name} {fg} on {bg} is {r:.2f}:1, under {floor}:1 ({what})")
    return lines


# ---------- HTML ----------

class Page(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []          # (tag, classes, attrs)
        self.styles, self.links, self.inline = [], [], []
        self.fails, self.warns = [], []
        self.lang = self.viewport = False
        self.text = []
        self.in_style = False
        self.svg_marks = []      # (aria ok, where)

    def classes_above(self):
        return [c for _, cls, _ in self.stack for c in cls]

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        cls = a.get("class", "").split()
        where = f"<{tag}{(' class=' + repr(' '.join(cls))) if cls else ''}>"
        if tag == "html" and a.get("lang"):
            self.lang = True
        if tag == "meta" and a.get("name", "").lower() == "viewport":
            self.viewport = True
        if tag == "link" and "stylesheet" in a.get("rel", "").lower().split():
            self.links.append(a.get("href", ""))
        if tag == "style":
            self.in_style = True
        above = self.classes_above()
        if "frame" in cls and "frame" in above:
            self.fails.append(f"nested frame: {where} sits inside another .frame (one idea per frame; split it)")
        if "doc" in above or "doc" in cls:
            if {"warn", "fail"} & set(cls):
                self.fails.append(f"signal colour inside a document: {where} (an invoice or statement has no severity)")
        if any("legend" in c for c in cls):
            self.fails.append(f"chart legend: {where} (a chart that needs a legend becomes two charts)")
        if "style" in a:
            self.inline.append((where, a["style"], list(above) + cls))
        for attr in ("title", "aria-label", "alt", "placeholder"):
            if EMOJI.search(a.get(attr, "")):
                self.fails.append(f"emoji or pictograph in {attr}=\"{a[attr]}\" on {where}")
        if tag.lower() in ("fegaussianblur", "fedropshadow", "lineargradient", "radialgradient"):
            self.fails.append(f"<{tag}> in an SVG: no blur, glow or gradient, by any route")
        for attr in ("fill", "stroke", "color", "bgcolor", "stop-color"):
            v = a.get(attr, "")
            if HEX.search(v) or FUNC_COLOUR.search(v) or NAMED.search(v):
                self.fails.append(f"colour literal {attr}=\"{v}\" on {where}: use var(--token) so it survives the paper palette")
        if tag == "svg":
            hidden = a.get("aria-hidden") == "true"
            named = a.get("role") == "img" and a.get("aria-label", "").strip()
            if not hidden and not named:
                self.fails.append(f"{where} has no role=\"img\" and aria-label (state shape, range and endpoint)")
        if "bars" in cls and not (a.get("role") == "img" and a.get("aria-label", "").strip()):
            self.fails.append(f"chart {where} has no role=\"img\" and aria-label (state shape, range and endpoint)")
        if tag not in VOID:
            self.stack.append((tag, cls, a))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID and self.stack and self.stack[-1][0] == tag:
            self.stack.pop()

    def handle_endtag(self, tag):
        if tag == "style":
            self.in_style = False
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if self.in_style:
            self.styles.append(data)
        elif not (self.stack and self.stack[-1][0] == "script"):
            self.text.append(data)


def accent_aliases(css):
    """Custom properties that resolve to the accent (--blue: var(--accent)), followed through chains."""
    defs = {}
    for _, _, body in rules(css):
        for p, v in decls(body):
            if p.startswith("--") and p != "--accent":
                defs[p] = v.lower()
    names = {"--accent"}
    changed = True
    while changed:
        changed = False
        for p, v in defs.items():
            if p not in names and any(f"var({n}" in v for n in names):
                names.add(p)
                changed = True
    return names


def uses_accent(value, names):
    return any(re.search(r"var\(\s*" + re.escape(n) + r"\s*[,)]", value) for n in names)


def selector_parts(sel):
    return [x.strip() for x in re.split(r",(?![^(]*\))", sel) if x.strip()]


def durations_ok(value):
    """True when every time in a transition value is 120ms (or a 0 delay)."""
    for num, unit in re.findall(r"(?<![\w.-])(\d*\.?\d+)(ms|s)\b", value):
        ms = float(num) * (1 if unit == "ms" else 1000)
        if ms not in (0.0, 120.0):
            return False
    return True


def transition_props_ok(value):
    for part in value.replace("!important", " ").split(","):
        words = part.split()
        if not words:
            continue
        first = words[0]
        if re.match(r"^(\d|\.)", first) or first in ("linear", "ease", "ease-in", "ease-out", "ease-in-out", "none"):
            return False if first != "none" else True  # no property named means "all"
        if first not in SAFE_TRANSITION:
            return False
    return True


def check_css(css, fails, warns, source, accent_ok=False, chart=False, aliases=("--accent",)):
    for ctx, sel, body in rules(css):
        if sel.startswith("@keyframes") or sel.startswith("@-webkit-keyframes"):
            fails.append(f"{source}: {sel}: no animation (motion is 120ms colour transitions only)")
            continue
        is_token_block = sel.strip() == ":root"
        parts = selector_parts(sel)
        for p, v in decls(body):
            plain = re.sub(r"url\([^)]*\)", "", v)
            low = plain.lower()
            at = f"{source}: {sel[:60]} {{ {p}: {v[:60]} }}"
            if p.startswith("--"):
                if not is_token_block and (HEX.search(plain) or FUNC_COLOUR.search(plain)):
                    fails.append(f"{at}: colour literal outside the token block")
                continue
            if p == "content" and EMOJI.search(v):
                fails.append(f"{at}: emoji or pictograph in generated content")
            if p == "border-radius" or p.endswith("-radius"):
                if re.sub(r"\b0(px|rem|em|%)?\b|calc|[()]|!important|\s", "", low):
                    fails.append(f"{at}: radius must be 0")
            if p == "font-weight" and low.replace("!important", "").strip() not in ("400", "normal", "inherit", "initial"):
                fails.append(f"{at}: weight is 400 everywhere (emphasis is --bright)")
            if p == "font" and re.search(r"\b(bold|bolder|[5-9]00)\b", low):
                fails.append(f"{at}: weight is 400 everywhere (emphasis is --bright)")
            if p == "font-variation-settings" and "wght" in low:
                fails.append(f"{at}: weight is 400 everywhere (emphasis is --bright)")
            if p in ("font-style", "font") and re.search(r"\b(italic|oblique)\b", low):
                fails.append(f"{at}: no italics")
            if p == "font-family" and "var(--mono)" not in low and low not in ("inherit", "monospace"):
                fails.append(f"{at}: one monospace family (var(--mono)) for every role")
            if p in ("box-shadow", "text-shadow") and low not in ("none", "none !important"):
                fails.append(f"{at}: no shadows or glows")
            if p in ("filter", "backdrop-filter") and low not in ("none",):
                fails.append(f"{at}: no blur, glow or filter effects")
            if re.search(r"(?<!repeating-)(linear|radial|conic)-gradient\(", low):
                fails.append(f"{at}: no gradients (repeating dashes for rules are the only exception)")
            if p in ("animation", "animation-name") and low not in ("none",):
                fails.append(f"{at}: no animation")
            if p in ("transition", "transition-duration") and not durations_ok(low):
                fails.append(f"{at}: transitions are 120ms linear")
            if (p == "transition" and not transition_props_ok(low)) or \
                    (p == "transition-property" and not all(x.strip() in SAFE_TRANSITION for x in low.split(","))):
                fails.append(f"{at}: transitions are on colour only")
            if HEX.search(plain) or FUNC_COLOUR.search(plain) or (NAMED.search(plain) and COLOUR_PROPS.match(p)):
                fails.append(f"{at}: colour literal; use a token")
            if "#fff" in low or "#000" in low:
                fails.append(f"{at}: pure white or black is never used")
            if uses_accent(low, aliases) and not accent_ok and not all(ACCENT_OK.search(x) for x in parts):
                fails.append(f"{at}: accent outside its three uses (frame title, data marks, focus)")
            if "var(--signal-" in low and (chart or any(CHART_MARK.search(x) for x in parts)):
                fails.append(f"{at}: signal colour on a chart (one accent, no severity colours on charts)")


def check_page(path, allow_tokens):
    fails, warns = [], []
    with open(path, encoding="utf-8", errors="replace") as f:
        src = f.read()
    pg = Page()
    pg.feed(src)
    fails += pg.fails
    css_parts = [("<style>", s) for s in pg.styles]
    base = os.path.dirname(os.path.abspath(path))
    def add_local(href, rel_to, how):
        if re.match(r"^[a-z]+:", href, re.I) or href.startswith("//"):
            if "fonts.googleapis.com" not in href:
                warns.append(f"{how} {href} is remote and was not checked")
            return
        p = os.path.normpath(os.path.join(rel_to, href.split("?")[0]))
        if os.path.isfile(p):
            with open(p, encoding="utf-8", errors="replace") as f:
                text = f.read()
            css_parts.append((os.path.relpath(p, base), text))
            return p
        fails.append(f"{how} {href} not found")

    for href in pg.links:
        add_local(href, base, "linked stylesheet")
    # local @import, one level deep
    for source, css in list(css_parts):
        rel_to = base if source == "<style>" else os.path.dirname(os.path.join(base, source))
        for m in re.finditer(r"@import\s+(?:url\(\s*)?[\"']?([^\"')\s;]+)", strip_comments(css)):
            add_local(m.group(1), rel_to, "@import")
    all_css = "\n".join(c for _, c in css_parts)
    aliases = accent_aliases(all_css)
    for source, css in css_parts:
        check_css(css, fails, warns, source, aliases=aliases)
    for where, style, classes in pg.inline:
        # data marks (bars, meter fills, sparklines) may carry the accent inline; never a signal colour on a chart
        check_css(f"inline{{{style}}}", fails, warns, f"style on {where}",
                  accent_ok=bool({"bars", "fill", "spark"} & set(classes)),
                  chart=bool({"bars", "spark"} & set(classes)), aliases=aliases)

    shipped_screen = tokens_from(open(SHIPPED_CSS, encoding="utf-8").read())
    page_screen = tokens_from(all_css)
    page_paper = tokens_from(all_css, print_only=True)
    if not page_screen:
        fails.append("no Scrollback tokens found: inline assets/scrollback.css (scripts/new_page.py does it) or link a copy")
    else:
        for t, v in shipped_screen.items():
            if t not in page_screen:
                fails.append(f"token {t} is missing")
            elif page_screen[t] != v:
                msg = f"token {t} is {page_screen[t]}, shipped value is {v}"
                (warns if allow_tokens else fails).append(msg + ("" if allow_tokens else
                    " (tokens are an API; change them only when the user asks, with --allow-tokens)"))
        shipped_paper = tokens_from(open(SHIPPED_CSS, encoding="utf-8").read(), print_only=True)
        if not page_paper:
            fails.append("no @media print palette: the page would print dark-on-dark or vanish on paper")
        for t, v in shipped_paper.items():
            if page_paper and page_paper.get(t) != v:
                msg = f"paper token {t} is {page_paper.get(t, 'missing')}, shipped value is {v}"
                (warns if allow_tokens else fails).append(msg)
        if allow_tokens:
            palette_report(page_screen, page_paper, fails, " (page)")
    if not pg.lang:
        fails.append("<html> has no lang attribute")
    if not pg.viewport:
        fails.append("no viewport meta tag")
    text = "".join(pg.text)
    em = sorted(set(EMOJI.findall(text)))
    if em:
        fails.append(f"emoji or pictograph in text: {' '.join(em)} (the glyph set is + - | [ ] ▸ ◂ · ├ │ └ ─)")
    if "lorem ipsum" in text.lower():
        fails.append("placeholder text 'lorem ipsum' (use real content or [NEEDS YOUR INPUT: ...])")
    left = text.count("[NEEDS YOUR INPUT")
    if left:
        warns.append(f"{left} [NEEDS YOUR INPUT] marker(s) left on the page")
    return fails, warns


# ---------- render ----------

MEASURE = """() => {
  const d = document.documentElement;
  const over = Math.max(d.scrollWidth, document.body.scrollWidth) - d.clientWidth;
  const empty = [...document.querySelectorAll('.meter .fill')].filter(e => {
    const w = parseFloat(e.style.width || '0'); return w > 0 && e.getBoundingClientRect().width < 1; }).length;
  const flat = [...document.querySelectorAll('.cmd, pre, .tree')].filter(e => {
    const ws = getComputedStyle(e).whiteSpace; return e.textContent.includes('\\n') && !ws.startsWith('pre'); }).length;
  return {over, empty, flat};
}"""


def launch(pw):
    try:
        return pw.chromium.launch(args=NO_DNS)
    except Exception as first:
        if "Executable doesn't exist" in str(first):
            raise RuntimeError("playwright's Chromium is missing; install it with: python3 -m playwright install chromium "
                               "(the same Python that runs this script)") from None
        return pw.chromium.launch(args=SAFE_ARGS + NO_DNS)


def shots(path, out):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return ["--shots asked for but playwright is not installed; no render check ran"], [], []
    fails, warns, written = [], [], []
    url = "file://" + os.path.abspath(path)
    try:
        with sync_playwright() as pw:
            b = launch(pw)
            page = b.new_page()
            page.route("**/*", lambda r: r.continue_() if r.request.url.startswith(("file:", "data:")) else r.abort())
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e).splitlines()[0] if str(e) else "error"))
            os.makedirs(out, exist_ok=True)
            stem = os.path.splitext(os.path.basename(path))[0]
            for label, w, h in (("desktop", 1280, 800), ("phone", 375, 812)):
                errors.clear()
                page.set_viewport_size({"width": w, "height": h})
                page.goto(url)
                page.wait_for_timeout(300)
                m = page.evaluate(MEASURE)
                if m["over"] > 1:
                    fails.append(f"{label} ({w}px): page scrolls sideways by {m['over']}px; wide content scrolls inside .scroll")
                if m["empty"]:
                    fails.append(f"{label}: {m['empty']} meter fill(s) render empty (track and fill need display:block)")
                if m["flat"]:
                    fails.append(f"{label}: {m['flat']} multi-line block(s) lost their line breaks (needs white-space:pre)")
                for e in errors:
                    fails.append(f"{label}: script error: {e}")
                shot = os.path.join(out, f"{stem}-{label}.png")
                page.screenshot(path=shot, full_page=True)
                written.append(shot)
            b.close()
    except Exception as e:
        return [f"render check did not run: {str(e).splitlines()[0]}"], [], written
    return fails, warns, written


# ---------- main ----------

def main(argv):
    args = list(argv)
    if not args or args[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0 if args else 2
    if "--palette" in args:
        args.remove("--palette")
        if "--shots" in args or "--allow-tokens" in args or len(args) > 1:
            print("--palette takes at most one CSS or HTML file and no other option", file=sys.stderr)
            return 2
        src = args[0] if args else SHIPPED_CSS
        if not os.path.isfile(src):
            print(f"no such file: {src}", file=sys.stderr)
            return 2
        with open(src, encoding="utf-8", errors="replace") as f:
            text = f.read()
        if src.lower().endswith((".html", ".htm")):
            pg = Page()
            pg.feed(text)
            text = "\n".join(pg.styles)
        fails = []
        screen, paper = tokens_from(text), tokens_from(text, print_only=True)
        if not screen:
            print(f"FAIL no Scrollback tokens in {src}")
            return 1
        print(f"palette: {src if src != SHIPPED_CSS else 'shipped assets/scrollback.css'}")
        for line in palette_report(screen, paper, fails):
            print(line)
        for f in fails:
            print("FAIL " + f)
        print("result: " + ("FAIL" if fails else "all floors held"))
        return 1 if fails else 0
    want_shots = "--shots" in args
    allow = "--allow-tokens" in args
    out = None
    rest = []
    while args:
        a = args.pop(0)
        if a == "--out" and args:
            out = args.pop(0)
        elif a in ("--shots", "--allow-tokens"):
            continue
        elif a.startswith("-"):
            print(f"unknown option {a}", file=sys.stderr)
            return 2
        else:
            rest.append(a)
    if len(rest) != 1 or not os.path.isfile(rest[0]):
        print("give one HTML file that exists", file=sys.stderr)
        return 2
    path = rest[0]
    fails, warns = check_page(path, allow)
    written = []
    if want_shots:
        f2, w2, written = shots(path, out or os.path.join(os.path.dirname(os.path.abspath(path)), ".scrollback-check"))
        fails += f2
        warns += w2
    seen = set()
    for f in fails:
        if f not in seen:
            print("FAIL " + f)
            seen.add(f)
    for w in warns:
        print("WARN " + w)
    for s in written:
        print("shot " + s)
    if not want_shots:
        print("note: no render check (add --shots for sideways scroll at 375px and screenshots)")
    print(f"result: {'FAIL' if fails else 'pass'} ({len(seen)} fail, {len(warns)} warn) {path}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
