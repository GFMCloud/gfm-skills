#!/usr/bin/env python3
"""Check a designed page before handing it over.

Usage: python3 scripts/check_page.py <page.html | http://localhost:...> [--shots] [--out <folder>] [--screen]

For a file, it checks the source:
  - complete (ends with </html>), has lang, a <title> and a viewport meta tag
  - the brand block from scripts/brand.py is in the page's CSS or a local stylesheet it links, and a
    var(--brand-...) uses it (with only the default brand, the comment alone is a warning)
  - no placeholder text or placeholder-image services; every <img> has alt; every field has a label
  - focus outlines are not removed without a :focus or :focus-visible rule that draws one
  Warnings: more than 8 font sizes, things loaded from outside the file, open [NEEDS YOUR INPUT], TBD,
  and elements marked data-sample (sample content to confirm before launch).
--shots renders the page (file or URL) with playwright at 1280px and 390px wide, writes full-page
<name>-desktop.png and <name>-phone.png into .design-check/ beside the file (or --out), and fails on
horizontal scroll at either width, on script errors and on text contrast under 3:1. At phone width
it warns about text under 14px, tap targets under 44px and contrast under 4.5:1 (3:1 for large
text). If screenshots were asked for and not written, that is a FAIL, never a skip.
--shots also measures the frame at both widths and fails on unequal outer margins, a section whose
content huddles on one side of a wide screen, a stretch over half a screen tall with nothing in it, no
h1 on the first screen, a section of running text with no heading, and a page or section title (the
h1, or a section's h2) over two lines.
--screen is for forms, components and app screens: the frame checks become warnings there.

Standard library only (playwright only for --shots). Exit code 1 on any FAIL.
"""
import pathlib
import re
import sys
import urllib.parse

PLACEHOLDER_TEXT = re.compile(r"lorem ipsum|dolor sit amet|your (headline|tagline|text) here|\bTODO\b", re.I)
PLACEHOLDER_IMG = re.compile(r"placehold\.co|placeholder\.com|picsum\.photos|placekitten|dummyimage\.com|source\.unsplash\.com", re.I)
# An attribute value in double quotes, single quotes or none.
VAL = r"""\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'=<>`]+))"""
CSS_RULE = re.compile(r"([^{}]+)\{([^{}]*)\}")
NO_OUTLINE = re.compile(r"outline(-style)?\s*:\s*(none|0(px|rem|em)?)\s*(!important)?\s*(;|$)", re.I)


def attr(tag, name):
    m = re.search(r"(?<![\w-])" + name + VAL, tag, re.I)
    return next((g for g in m.groups() if g is not None), "") if m else None


def tags(html, name):
    return re.findall(r"<" + name + r"\b[^>]*>", html, re.I)


def strip_comments(raw):
    return re.sub(r"<!--.*?-->", "", raw, flags=re.S)


def local_css(path, html):
    out = ""
    for link in tags(html, "link"):
        href = attr(link, "href")
        if not href or "stylesheet" not in (attr(link, "rel") or "").lower() or re.match(r"(https?:)?//", href):
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
    if not any((attr(m, "name") or "").lower() == "viewport" for m in tags(html, "meta")):
        problems.append("no viewport meta tag; the page will render zoomed out on phones")
    src = re.search(r"brand-source:\s*([\w-]+)", styles)
    if not src:
        problems.append("brand block not found in the page's CSS; run brand.py and paste its :root block "
                        "(or, for a redesign that keeps the page's own colours, its brand-source comment)")
    elif "var(--brand-" not in styles + html:
        if src.group(1) == "default":
            warnings.append("brand: default, and no --brand-* variable is used; fine only for a redesign that "
                            "keeps the page's own colours")
        else:
            problems.append(f"brand block ({src.group(1)}) is pasted but no var(--brand-...) uses it")
    body = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", body)
    m = PLACEHOLDER_TEXT.search(text)
    if m:
        problems.append(f"placeholder text left in: {m.group(0)!r}")
    if re.search(r"\bTBD\b", text):
        warnings.append("'TBD' in the visible text; fine if the page means it, otherwise ask for the real value")
    m = PLACEHOLDER_IMG.search(html)
    if m:
        problems.append(f"placeholder image service used: {m.group(0)}")
    for img in tags(html, "img"):
        if attr(img, "alt") is None:
            problems.append(f"image without alt: {img[:80]}")
    labelled = {attr(lab, "for") for lab in tags(html, "label")}
    wrapped = " ".join(re.findall(r"<label\b.*?</label>", html, re.S | re.I))
    for field in re.findall(r"<(?:input|select|textarea)\b[^>]*>", html, re.I):
        if (attr(field, "type") or "").lower() in ("hidden", "submit", "button", "reset", "image"):
            continue
        fid = attr(field, "id")
        if (fid and fid in labelled) or field in wrapped or re.search(r"aria-label(ledby)?\s*=", field, re.I):
            continue
        problems.append(f"field without a label: {field[:80]}")
    rules = CSS_RULE.findall(re.sub(r"/\*.*?\*/", "", styles, flags=re.S))
    removed = any(NO_OUTLINE.search(b) for _, b in rules)
    shown = any(":focus" in sel and (re.search(r"outline\s*:", b) and not NO_OUTLINE.search(b)
                                     or re.search(r"(box-shadow|border(-\w+)?)\s*:(?!\s*(none|0)\b)|background", b))
                for sel, b in rules)
    if removed and not shown:
        problems.append("focus outline removed and no :focus or :focus-visible rule draws a visible focus style")
    sizes = set(re.findall(r"font-size\s*:\s*([^;}\n]+)", styles))
    if len(sizes) > 8:
        warnings.append(f"{len(sizes)} different font-size values; aim for five or fewer from one scale")
    for t in tags(html, "script") + tags(html, "link") + tags(html, "img") + tags(html, "iframe"):
        url = attr(t, "src") or attr(t, "href") or ""
        if re.match(r"(https?:)?//", url) and "fonts.googleapis.com" not in url and "fonts.gstatic.com" not in url:
            warnings.append(f"loads from outside the file: {url}")
    n = raw.count("NEEDS YOUR INPUT")
    if n:
        warnings.append(f"{n} open [NEEDS YOUR INPUT] marker(s) for the author")
    n = len(re.findall(r"<[a-z][^>]*\bdata-sample\b", html, re.I))
    if n:
        warnings.append(f"{n} element(s) marked data-sample: sample content to confirm or replace before launch")
    return problems, warnings


# Some agent sandboxes (on macOS among others) stop Chromium's helper processes from starting.
# Running it as one process avoids that, so try the normal launch first and then that.
SAFE_ARGS = ["--single-process", "--no-zygote"]

MEASURE = """() => {
  const doc = document.documentElement, vis = e => { const r = e.getBoundingClientRect(), s = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  const rgba = c => { if (!/^rgba?\\(/.test(c)) return null; const m = c.match(/[\\d.]+/g); return m ? [+m[0], +m[1], +m[2], m[3] === undefined ? 1 : +m[3]] : null; };
  const over = (a, b) => [0, 1, 2].map(i => a[i] * a[3] + b[i] * (1 - a[3])).concat(1);
  const lum = c => { const l = c.slice(0, 3).map(x => { x /= 255; return x <= 0.04045 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4; });
    return 0.2126 * l[0] + 0.7152 * l[1] + 0.0722 * l[2]; };
  // The colour behind an element: its own and its ancestors' backgrounds over white; null over an image.
  const behind = e => { const layers = [];
    for (let n = e; n; n = n.parentElement) { const s = getComputedStyle(n);
      if (s.backgroundImage !== 'none') return null;
      const c = rgba(s.backgroundColor); if (!c) return null; if (c[3] > 0) { layers.push(c); if (c[3] >= 1) break; } }
    return layers.reverse().reduce((acc, c) => over(c, acc), [255, 255, 255, 1]); };
  let small = 0, tiny = [], low = [];
  for (const e of document.querySelectorAll('body *')) {
    const own = [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (!own || !vis(e)) continue;
    const s = getComputedStyle(e), size = parseFloat(s.fontSize);
    if (size < 14) small++;
    const bg = behind(e), fg = rgba(s.color);
    if (!bg || !fg) continue;
    const f = over(fg, bg), [hi, lo] = [lum(f), lum(bg)].sort((a, b) => b - a), ratio = (hi + 0.05) / (lo + 0.05);
    const large = size >= 24 || (size >= 18.66 && +s.fontWeight >= 700), need = large ? 3 : 4.5;
    if (ratio < need) low.push({ text: e.innerText.trim().slice(0, 30), ratio: Math.round(ratio * 10) / 10, need });
  }
  for (const e of document.querySelectorAll('a[href], button, input:not([type=hidden]), select, textarea, [role=button]')) {
    // A checkbox or radio is tapped through its label, so measure that when there is one.
    const lab = /^(checkbox|radio)$/.test(e.type) && (e.closest('label') || (e.id && document.querySelector(`label[for="${e.id}"]`)));
    const r = (lab || e).getBoundingClientRect(), b = e.getBoundingClientRect();
    const onScreen = b.right > 0 && b.left < window.innerWidth && b.bottom > -window.scrollY;  // skip links sit off-screen
    // A link inside a sentence is exempt; a link that is the whole list item (a nav menu) is not.
    const host = e.closest('p, li'), inline = host && host.innerText.trim().length > (e.innerText || '').trim().length + 20;
    if (vis(e) && onScreen && (r.height < 44 || r.width < 44) && !inline) tiny.push((e.innerText || e.name || e.tagName).replace(/\\s+/g, ' ').trim().slice(0, 30));
  }
  return { over: doc.scrollWidth - window.innerWidth, small, tiny, low };
}"""

# The frame of the page: what a reader notices first when a page looks wrong.
FRAME = """() => {
  const W = window.innerWidth, H = window.innerHeight, SY = window.scrollY;
  const vis = e => { const r = e.getBoundingClientRect(), s = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  // Seen, not only present: a visually hidden or transparent heading does not count.
  const opaque = e => { for (let n = e; n && n.nodeType === 1; n = n.parentElement) if (parseFloat(getComputedStyle(n).opacity) === 0) return false; return true; };
  // A heading the scroll pass saw opaque counts, though a reveal may have hidden it again since.
  const seen = e => { const r = e.getBoundingClientRect(); return vis(e) && r.width >= 20 && r.height >= 8 && (opaque(e) || e.dataset.dcSeen === '1'); };
  // Content inside a box that scrolls sideways (a wide table, a card row) is measured at the box's edges.
  const clip = e => { let l = -Infinity, r = Infinity;
    for (let n = e.parentElement; n && n !== document.body; n = n.parentElement) {
      if (getComputedStyle(n).overflowX !== 'visible') { const b = n.getBoundingClientRect(); l = Math.max(l, b.left); r = Math.min(r, b.right); } }
    return [l, r]; };
  const MEDIA = /^(IMG|VIDEO|CANVAS|PICTURE|IFRAME|SVG|INPUT|SELECT|TEXTAREA|BUTTON)$/i;
  // Content units: elements with their own text, pictures (an element with role="img" included),
  // controls and background pictures. A colour or a gradient alone is not content.
  const units = [];
  for (const e of document.querySelectorAll('body *')) {
    if (!vis(e) || e.closest('svg') && e.tagName.toLowerCase() !== 'svg' || e.closest('[aria-hidden="true"]')) continue;
    const own = [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    const media = MEDIA.test(e.tagName) || e.getAttribute('role') === 'img' ||
      [null, '::before', '::after'].some(p => getComputedStyle(e, p).backgroundImage.includes('url('));
    if (!own && !media) continue;
    // Two extents: the box (l, r: where the layout puts it, for the margins) and the reach (il, ir:
    // what it fills across the width). A heading reaches as far as its letters, since its box spans the
    // column however short it is; other text reaches as far as its box (a narrow column stays narrow,
    // a short address line in a wide column doesn't make the section look huddled).
    const r = e.getBoundingClientRect(), [cl, cr] = clip(e);
    const ink = { left: r.left, right: r.right, top: r.top, bottom: r.bottom }, rg = document.createRange(), bs = [];
    if (!media) for (const n of e.childNodes) if (n.nodeType === 3 && n.textContent.trim()) { rg.selectNodeContents(n); bs.push(...[...rg.getClientRects()].filter(b => b.width > 0)); }
    if (bs.length) { ink.top = Math.min(...bs.map(b => b.top)); ink.bottom = Math.max(...bs.map(b => b.bottom));
      if (e.matches('h1, h2, h3, h4, h5, h6, [role=heading]')) { ink.left = Math.min(...bs.map(b => b.left)); ink.right = Math.max(...bs.map(b => b.right)); } }
    if (Math.min(r.right, cr, W) <= Math.max(r.left, cl, 0)) continue;  // scrolled out of its box
    units.push({ e, scrolled: r.right > cr + 1 || r.left < cl - 1, l: Math.max(r.left, cl, 0), r: Math.min(r.right, cr, W), il: Math.max(ink.left, cl, 0), ir: Math.min(ink.right, cr, W),
                 t: ink.top + SY, b: ink.bottom + SY, media,
                 words: own ? [...e.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join(' ').split(/\\s+/).filter(Boolean).length : 0 });
  }
  // Blank stretches: gaps down the page, from its top, with no content unit in them.
  const spans = units.map(u => [u.t, u.b]).sort((a, b) => a[0] - b[0]);
  const gaps = []; let end = 0;
  for (const [t, b] of spans) { if (t - end > H * 0.5) gaps.push({ top: Math.round(end), height: Math.round(t - end) }); end = Math.max(end, b); }
  // Sections: the outermost section and article elements (a card or column inside a section belongs to
  // it), else the containers directly under main (or body); a paragraph or list is not a section. A
  // section taller than one and a half screens that holds two or more sections stands for those instead.
  let all = [...document.querySelectorAll('section, article')];
  // A page wrapped in one app root (div#root > div > ...) is read from the first level with siblings.
  let box = document.querySelector('main') || document.body;
  const kidsOf = e => [...e.children].filter(c => !/^(SCRIPT|STYLE|NOSCRIPT|TEMPLATE|LINK)$/.test(c.tagName));
  while (kidsOf(box).length === 1 && /^(DIV|MAIN)$/.test(kidsOf(box)[0].tagName)) box = kidsOf(box)[0];
  if (!all.length) all = kidsOf(box).filter(e => /^(DIV|SECTION|ARTICLE|ASIDE|MAIN)$/.test(e.tagName) &&
    !/(^|[\\s_-])(footer|nav|header|navbar|masthead)([\\s_-]|$)/i.test(e.id + ' ' + (typeof e.className === 'string' ? e.className : '')));
  all = all.filter(e => vis(e) && !/^(HEADER|NAV|FOOTER|SCRIPT|STYLE)$/.test(e.tagName) && !e.closest('footer, nav'));
  const parentOf = e => all.find(o => o !== e && o.contains(e) && !all.some(m => m !== o && m !== e && o.contains(m) && m.contains(e)));
  const kids = e => all.filter(o => parentOf(o) === e);
  const cands = all.filter(e => !parentOf(e)).flatMap(e => e.getBoundingClientRect().height > H * 1.5 && kids(e).length >= 2 ? kids(e) : [e]);
  // The block that holds the h1 (a hero in a header or a plain div) is a section too.
  const firstH1 = [...document.querySelectorAll('h1')].find(seen);
  if (firstH1 && !cands.some(c => c.contains(firstH1))) {
    let a = firstH1;
    while (a.parentElement && a.parentElement !== box && a.parentElement !== document.body && !cands.some(c => a.parentElement.contains(c))) a = a.parentElement;
    cands.unshift(a);
  }
  // A stand-in laid out by a grid or flex parent, or sharing its rows with a sibling, is a card in a
  // wider layout (the last card of an odd row included), not a section of its own.
  const besides = e => { const r = e.getBoundingClientRect(), p = parentOf(e), up = e.parentElement;
    const cs = up && getComputedStyle(up);
    const rowed = cs && ((/grid/.test(cs.display) && cs.gridTemplateColumns.trim().split(/\\s+/).length >= 2) ||
                         (/flex/.test(cs.display) && /row/.test(cs.flexDirection)));
    // A grid lays out cards when its children sit beside each other or start at two or more columns
    // (the last card of an odd row included); a grid that stacks every section in one column doesn't.
    const side = o => (b => b.top < r.bottom - 1 && r.top < b.bottom - 1)(o.getBoundingClientRect());
    const cols = rowed && new Set(kidsOf(up).map(o => Math.round(o.getBoundingClientRect().left))).size;
    if (rowed && (cols >= 2 || kidsOf(up).some(o => o !== e && side(o)))) return true;
    if (!p) return false;
    return cands.some(o => o !== e && parentOf(o) === p && (b => b.top < r.bottom - 1 && r.top < b.bottom - 1)(o.getBoundingClientRect())); };
  const headOf = e => [...e.querySelectorAll('h1, h2, h3, h4, h5, h6, [role=heading]')].find(seen);
  const sections = cands.map(e => {
    // Navigation sharing a block with the hero (a header holding both) is not the hero's content.
    const r = e.getBoundingClientRect(), inside = units.filter(u => e.contains(u.e) && !(u.e.closest('nav') && !e.closest('nav')));
    const words = inside.reduce((n, u) => n + u.words, 0);
    // A statement set as one quotation is not running text that needs a heading.
    const prose = inside.filter(u => !u.e.closest('blockquote')).reduce((n, u) => n + u.words, 0);
    const left = inside.length ? Math.min(...inside.map(u => u.il)) : null, right = inside.length ? Math.max(...inside.map(u => u.ir)) : null;
    // A section standing in for its parent (a card in a tall grid) is titled by the parent's heading;
    // a heading set just before the section, as its previous sibling, titles it too.
    const prev = e.previousElementSibling;
    const head = headOf(e) || (parentOf(e) && headOf(parentOf(e))) || (prev && /^H[1-6]$/.test(prev.tagName) && seen(prev) && prev);
    const name = (head ? head.innerText : e.id ? '#' + e.id : typeof e.className === 'string' && e.className.trim() ? e.tagName.toLowerCase() + '.' + e.className.trim().split(/\\s+/)[0]
      : e.tagName.toLowerCase() + ' "' + (e.innerText || '').trim().split(/\\s+/).slice(0, 6).join(' ') + '"').trim().slice(0, 48);
    const top = inside.length ? Math.min(...inside.map(u => u.t)) : r.top + SY, bottom = inside.length ? Math.max(...inside.map(u => u.b)) : r.bottom + SY;
    return { name, head: head || null, top: Math.round(top), bottom: Math.round(bottom), height: Math.round(r.height), words, prose, left, right, heading: !!head, inRow: besides(e) };
  });
  // The outer margins, read row by row: each section, header and footer whose content crosses the middle
  // of the screen gives a pair of margins, and the page's frame is the outermost reach on each side.
  // A row with a picture bleeding off an edge is left out: the bleed is a decision, not a margin.
  const rows = [...new Set([...cands, ...document.querySelectorAll('body > header, body > footer, main > header, main > footer, body > aside, main > aside')])].filter(vis).map(e => {
    const inside = units.filter(u => e.contains(u.e) && u.r - u.l < W * 0.97);
    if (!inside.length || inside.some(u => (u.media || u.scrolled) && (u.l <= 1 || u.r >= W - 1))) return null;
    const l = Math.min(...inside.map(u => u.l)), r = Math.max(...inside.map(u => u.r));
    return l < W / 2 && r > W / 2 ? [l, W - r] : null;
  }).filter(Boolean);
  // No row across the middle: the outermost content of the sections stands in.
  if (!rows.length) { const us = units.filter(u => cands.some(c => c.contains(u.e)) && !(u.media && (u.l <= 1 || u.r >= W - 1)));
    if (us.length) rows.push([Math.min(...us.map(u => u.l)), W - Math.max(...us.map(u => u.r))]); }
  const L = rows.length ? Math.min(...rows.map(x => x[0])) : null, R = rows.length ? Math.min(...rows.map(x => x[1])) : null;
  // Huddled: all of a section's content within one side of a wide screen, and nothing else on the page
  // beside it (a sibling figure or an aside fills the other side; a fixed or sticky bar does not).
  const pinned = e => { for (let n = e; n && n.nodeType === 1; n = n.parentElement) { const p = getComputedStyle(n).position;
    if (p === 'fixed' || (p === 'sticky' && n.getBoundingClientRect().width >= W * 0.9)) return true; } return false; };
  const beside = (s, onRight) => units.some(u => u.t < s.bottom - 1 && u.b > s.top + 1 && (onRight ? u.ir > W * 0.58 : u.il < W * 0.42) && !pinned(u.e));
  const huddled = W >= 900 ? sections.filter(s => !s.inRow && s.left != null && s.words >= 20 && s.height >= 120 &&
    ((s.right <= W * 0.58 && !beside(s, true)) || (s.left >= W * 0.42 && !beside(s, false))))
    .map(s => ({ name: s.name, empty: Math.round(s.right <= W * 0.58 ? W - s.right : s.left), side: s.right <= W * 0.58 ? 'right' : 'left' })).slice(0, 4) : [];
  const untitled = sections.filter(s => !s.heading && s.prose >= 30 && s.height >= 80).map(s => s.name);
  const h1 = [...document.querySelectorAll('h1')].filter(seen)[0];
  const h1top = h1 ? Math.round(h1.getBoundingClientRect().top + SY) : null;
  // Lines in the page's h1 and in each section's own h1 or h2 (a title in a card or a list is content,
  // not a headline): the boxes of its text, grouped by line (a box whose middle sits above the line's
  // bottom belongs to it), so a smaller inline word on the same line is not a line of its own.
  const long = [];
  // Cards standing in for a tall grid (articles, divs) keep their titles out; a section counts, but not
  // when its only heading is the title of a card inside it.
  const inCard = (h, e) => { for (let a = h; a && a !== e; a = a.parentElement) { const up = a.parentElement, cs = up && getComputedStyle(up);
    if (cs && kidsOf(up).length >= 2 && ((/grid/.test(cs.display) && cs.gridTemplateColumns.trim().split(/\\s+/).length >= 2) || (/flex/.test(cs.display) && /row/.test(cs.flexDirection)))) return true; } return false; };
  const titled = cands.filter(e => !parentOf(e) || e.tagName === 'SECTION').map(e => sections[cands.indexOf(e)].head).filter((h, i) => h && !inCard(h, cands.filter(e => !parentOf(e) || e.tagName === 'SECTION')[i]));
  const titles = new Set([firstH1, ...titled].filter(h => h && /^H[12]$/.test(h.tagName)));
  for (const h of titles) {
    if (!seen(h)) continue;
    const rg = document.createRange(); rg.selectNodeContents(h);
    const boxes = [...rg.getClientRects()].filter(b => b.width > 1 && b.height > 1).sort((a, b) => a.top - b.top);
    const lines = [];
    for (const b of boxes) { const last = lines[lines.length - 1]; if (last && (b.top + b.bottom) / 2 < last.bottom) last.bottom = Math.max(last.bottom, b.bottom); else lines.push({ bottom: b.bottom }); }
    if (lines.length > 2) long.push({ text: h.innerText.replace(/\\s+/g, ' ').trim().slice(0, 40), lines: lines.length });
  }
  return { W, H, L: L == null ? null : Math.max(0, Math.round(L)), R: R == null ? null : Math.max(0, Math.round(R)), gaps, huddled, untitled, h1top, long };
}"""


def frame_findings(f, label, screen):
    """Turn one width's frame measurements into problems and warnings."""
    problems, warnings = [], []
    page = warnings if screen else problems
    W, phone = f["W"], f["W"] < 600
    if f["L"] is not None and f["R"] is not None:
        diff, wide = abs(f["L"] - f["R"]), max(f["L"], f["R"])
        if diff >= max(14 if phone else 40, W * 0.045) and wide >= (28 if phone else W * 0.07):
            page.append(f"{label}: unequal outer margins, {f['L']}px on the left and {f['R']}px on the right; "
                            "give the page one pair of equal margins")
        elif diff >= (12 if phone else 16):
            warnings.append(f"{label}: margins differ, {f['L']}px left and {f['R']}px right")
    for s in f["huddled"]:
        page.append(f"{label}: section {s['name']!r} keeps its content on one side and leaves {s['empty']}px on the "
                    f"{s['side']} empty; fill that side with its picture, a second column or a figure, or centre it")
    for g in f["gaps"][:4]:
        page.append(f"{label}: {g['height']}px with nothing in it at {g['top']}px down (over half a screen)")
    if f["h1top"] is None:
        page.append(f"{label}: no visible h1; the first screen needs a title that says what this is")
    elif f["h1top"] >= f["H"] * 0.95:
        page.append(f"{label}: the h1 starts {f['h1top']}px down, below the first screen")
    if f["untitled"]:
        page.append(f"{label}: section(s) of running text with no heading: " + ", ".join(repr(n) for n in f["untitled"][:4]))
    for h in f["long"][:4]:
        page.append(f"{label}: heading {h['text']!r} runs to {h['lines']} lines; cut it to two")
    return problems, warnings


def launch(pw):
    try:
        return pw.chromium.launch()
    except Exception as first:
        if "Executable doesn't exist" in str(first):
            raise RuntimeError("playwright's Chromium is missing or doesn't match this playwright version; "
                               "install it with: python3 -m playwright install chromium "
                               "(use the same Python that runs this script)") from None
        return pw.chromium.launch(args=SAFE_ARGS)


def shots(target, out, stem, screen=False):
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
                # Scroll through once so reveal-on-scroll content shows, then measure the page as it
                # rests: back at the top, entrance animations finished (an endless one can't be).
                page.evaluate("""async () => { const step = innerHeight * 0.8, wait = (ms = 60) => new Promise(r => setTimeout(r, ms));
                  document.documentElement.style.scrollBehavior = 'auto'; document.body.style.scrollBehavior = 'auto';  // jump, don't glide
                  const mark = () => document.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(h => {
                    for (let n = h; n && n.nodeType === 1; n = n.parentElement) if (parseFloat(getComputedStyle(n).opacity) === 0) return;
                    if (h.getBoundingClientRect().top < innerHeight && h.getBoundingClientRect().bottom > 0) h.dataset.dcSeen = '1'; });
                  const settle = () => document.getAnimations().forEach(a => { try { a.finish(); } catch (e) {} });
                  for (let y = 0; y < document.documentElement.scrollHeight; y += step) { scrollTo(0, y); await wait(); settle(); mark(); }
                  scrollTo(0, 0); await wait(300); }""")
                page.evaluate("() => document.getAnimations().forEach(a => { try { a.finish(); } catch (e) {} })")
                m = page.evaluate(MEASURE)
                if m["over"] > 1:
                    problems.append(f"{label} ({w}px): page scrolls sideways by {m['over']}px")
                for e in errors:
                    problems.append(f"{label}: script error: {e}")
                fp, fw = frame_findings(page.evaluate(FRAME), label, screen)
                problems += fp
                warnings += fw
                if label == "phone":
                    if m["small"]:
                        warnings.append(f"phone: {m['small']} text element(s) under 14px")
                    if m["tiny"]:
                        warnings.append(f"phone: tap targets under 44px: {', '.join(m['tiny'][:6])}")
                    # Contrast doesn't change with width, so it is reported once, from the phone render.
                    bad = [x for x in m["low"] if x["ratio"] < 3]
                    faint = [x for x in m["low"] if x["ratio"] >= 3]
                    if bad:
                        problems.append("text contrast under 3:1: " + "; ".join(
                            f"{x['text']!r} {x['ratio']}:1" for x in bad[:6]))
                    if faint:
                        warnings.append("text contrast under its target (4.5:1, or 3:1 for large text): " + "; ".join(
                            f"{x['text']!r} {x['ratio']}:1" for x in faint[:6]))
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
        p, w = shots(url, out, stem, screen="--screen" in args)
        problems += p
        warnings += w
    for w in warnings:
        print(f"  warn  {w}")
    for p in problems:
        print(f"  FAIL  {p}")
    if not problems:
        frame = "" if "--screen" in args else " and the frame,"
        print("  pass  " + ("source checks" if not re.match(r"https?://", target) else "") +
              (f"{frame} with no sideways scroll at 1280px or 390px" if "--shots" in args else ""))
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
