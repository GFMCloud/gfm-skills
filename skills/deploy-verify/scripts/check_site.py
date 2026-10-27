#!/usr/bin/env python3
"""Check a running site the way a visitor meets it. Read-only: GET and HEAD requests only.

Usage:
  python3 check_site.py <base-url> [--pages N] [--external] [--compare <other-base-url>]
                        [--shots] [--out <folder>]

Crawls same-site pages from <base-url> (up to N, default 30) and reports:
  FAIL  broken links, images, scripts and stylesheets on this site (4xx, 5xx, no answer),
        a start page that isn't HTML or redirects in a loop, a "not found" path that answers 200
        (soft 404), placeholder text (lorem ipsum, TODO, "your text here"), missing <title>,
        http:// resources on an https page
  WARN  missing meta description, viewport tag, lang or image alt text; a copyright year
        before this year; no robots.txt, sitemap.xml or favicon; a page cut off at 5 MB
If the start page redirects to another host (http://example.org -> https://www.example.org), the
crawl follows it and says so. Links whose address looks like it changes something when opened
(logout, delete, unsubscribe ...) are never fetched; the summary counts them.
--external also checks links to other sites (HEAD, then GET); off by default.
--compare fetches every page and file found here from a second base URL too, and fails on any
        whose status, final address or bytes differ. For a host move, crawl the OLD host and
        compare it with the new one, so every old page is looked for.
--shots renders each page found (at most 5) with playwright at 375px and 1280px, light and dark,
        writes PNGs to --out (default .deploy-check/ in the current folder), and fails on sideways
        scrolling at 375px. If playwright or its browser is missing it says NOT RUN; it never
        reports a pass it didn't make.

Redirects are followed by hand (301, 302, 303, 307, 308) and shown, so a 308 "pretty URL"
redirect is not mistaken for a broken page. Each response is read for at most 30 seconds and 5 MB.

Exit codes: 0 no FAIL, 1 at least one FAIL, 2 setup problem (the base URL did not answer at all,
or bad arguments): no check ran, so this says nothing about the site.
Standard library only (playwright only for --shots).
"""
import datetime
import hashlib
import html.parser
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

TIMEOUT = 15          # seconds per socket read
DEADLINE = 30         # seconds per response, in total
MAX_BYTES = 5_000_000
UA = "deploy-verify-check/1 (read-only)"
PLACEHOLDER = re.compile(r"lorem ipsum|dolor sit amet|your (?:headline|tagline|text|content) here", re.I)
PLACEHOLDER_CAPS = re.compile(r"\b(?:TODO|TBD|FIXME)\b")
DEFAULT_TITLES = {"", "document", "untitled", "react app", "vite app", "index", "home page"}
REDIRECTS = {301, 302, 303, 307, 308}
RISKY_LINK = re.compile(r"(?:^|[/_.?=&-])(?:log-?out|sign-?out|delete|remove|unsubscribe|destroy)(?:[/_.?=&-]|$)", re.I)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def read_capped(resp):
    """Read a response for at most DEADLINE seconds and MAX_BYTES. Returns (bytes, cut_off)."""
    chunks, size, start = [], 0, time.monotonic()
    while True:
        chunk = resp.read(65536)
        if not chunk:
            return b"".join(chunks), False
        chunks.append(chunk)
        size += len(chunk)
        if size >= MAX_BYTES or time.monotonic() - start > DEADLINE:
            return b"".join(chunks)[:MAX_BYTES], True


def safe_url(url):
    """Percent-encode spaces and other characters a browser would encode."""
    return urllib.parse.quote(url, safe=":/?#[]@!$&'()*+,;=%~")


def fetch(url, method="GET"):
    """Return a dict: status, headers, body, final, chain, error, cut."""
    chain = []
    seen = {url}
    for _ in range(10):
        req = urllib.request.Request(safe_url(url), method=method, headers={"User-Agent": UA})
        cut = False
        try:
            resp = OPENER.open(req, timeout=TIMEOUT)
            status, headers = resp.status, resp.headers
            body, cut = read_capped(resp) if method == "GET" else (b"", False)
        except urllib.error.HTTPError as e:
            status, headers = e.code, e.headers
            body, cut = read_capped(e) if method == "GET" else (b"", False)
        except Exception as e:  # DNS, refused, TLS, timeout
            return {"status": None, "headers": {}, "body": b"", "final": url, "chain": chain,
                    "error": f"{type(e).__name__}: {e}", "cut": False}
        if status in REDIRECTS and headers.get("Location"):
            nxt = urllib.parse.urljoin(url, headers["Location"])
            chain.append(f"{status} {url} -> {nxt}")
            if nxt in seen:
                return {"status": status, "headers": headers, "body": b"", "final": nxt, "chain": chain,
                        "error": "redirect loop", "cut": False}
            seen.add(nxt)
            url = nxt
            continue
        return {"status": status, "headers": headers, "body": body, "final": url, "chain": chain,
                "error": None, "cut": cut}
    return {"status": None, "headers": {}, "body": b"", "final": url, "chain": chain,
            "error": "redirect loop (more than 10 redirects)", "cut": False}


def decode(r):
    m = re.search(r"charset=([\w-]+)", r["headers"].get("Content-Type") or "", re.I)
    if not m:
        m = re.search(rb"<meta[^>]+charset=[\"']?([\w-]+)", r["body"][:2048], re.I)
    enc = m.group(1) if m else "utf-8"
    enc = enc.decode() if isinstance(enc, bytes) else enc
    try:
        return r["body"].decode(enc, errors="replace")
    except LookupError:
        return r["body"].decode("utf-8", errors="replace")


class Page(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self.assets, self.text = [], [], []
        self.title, self.in_title, self.in_skip = None, False, 0
        self.meta, self.lang, self.imgs_no_alt, self.icon = {}, None, 0, False

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "html":
            self.lang = a.get("lang")
        elif tag == "title":
            self.in_title, self.title = True, self.title or ""
        elif tag in ("script", "style"):
            self.in_skip += 1
            if tag == "script" and a.get("src"):
                self.assets.append(a["src"])
        elif tag == "a" and a.get("href"):
            self.links.append(a["href"])
        elif tag == "img":
            if a.get("src"):
                self.assets.append(a["src"])
            if "alt" not in a:
                self.imgs_no_alt += 1
        elif tag == "link" and a.get("href"):
            rel = a.get("rel", "").lower()
            if "icon" in rel:
                self.icon = True
            if "stylesheet" in rel or "icon" in rel:
                self.assets.append(a["href"])
        elif tag == "meta":
            key = (a.get("name") or a.get("property") or "").lower()
            if key:
                self.meta[key] = a.get("content", "")

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag in ("script", "style") and self.in_skip:
            self.in_skip -= 1

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        elif not self.in_skip:
            self.text.append(data)


def norm(url):
    p = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((p.scheme, p.netloc, p.path or "/", p.query, ""))


def same_site(url, base):
    return urllib.parse.urlsplit(url).netloc == urllib.parse.urlsplit(base).netloc


def is_html(r):
    return "html" in (r["headers"].get("Content-Type") or "").lower()


def placeholder(text):
    m = PLACEHOLDER.search(text) or PLACEHOLDER_CAPS.search(text)
    return m.group(0) if m else None


def shots(pages, out):
    """Phone and dark-mode screenshots with playwright. Returns (fails, notes)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return [], ["NOT RUN  screenshots: playwright is not installed (try: uv run --with playwright python3 check_site.py ... --shots)"]
    out.mkdir(parents=True, exist_ok=True)
    fails, notes = [], []
    try:
        with sync_playwright() as pw:
            try:
                browser = pw.chromium.launch()
            except Exception:
                # Some agent sandboxes stop Chromium's helper processes; this mode starts inside them.
                browser = pw.chromium.launch(args=["--single-process", "--no-zygote"])
            page = browser.new_page()
            for url in pages[:5]:
                slug = re.sub(r"[^a-z0-9]+", "-", urllib.parse.urlsplit(url).path.lower()).strip("-") or "home"
                for width, height in ((375, 812), (1280, 900)):
                    for scheme in ("light", "dark"):
                        page.set_viewport_size({"width": width, "height": height})
                        page.emulate_media(color_scheme=scheme)
                        page.goto(url, wait_until="load", timeout=TIMEOUT * 1000)
                        name = f"{slug}-{width}-{scheme}.png"
                        page.screenshot(path=str(out / name), full_page=True)
                        if width == 375 and scheme == "light":
                            sw = page.evaluate("document.documentElement.scrollWidth")
                            if sw > width + 1:
                                fails.append(f"FAIL  {url}: scrolls sideways at 375px (content is {sw}px wide)")
                notes.append(f"shots {url}: {out}/{slug}-*.png (look at them; dark is prefers-color-scheme only)")
            browser.close()
    except Exception as e:
        return [], [f"NOT RUN  screenshots: {type(e).__name__}: {str(e).splitlines()[0]}"
                    " (if the browser is missing: python3 -m playwright install chromium; ask first)"]
    return fails, notes


def main():
    args = sys.argv[1:]
    opts = {"--pages": "30", "--compare": None, "--out": ".deploy-check"}
    flags, pos = set(), []
    i = 0
    while i < len(args):
        a = args[i]
        if a in opts:
            if i + 1 >= len(args):
                print(f"{a} needs a value", file=sys.stderr)
                return 2
            opts[a] = args[i + 1]
            i += 2
            continue
        if a in ("--external", "--shots"):
            flags.add(a)
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        elif a.startswith("-"):
            print(f"unknown option {a}", file=sys.stderr)
            return 2
        else:
            pos.append(a)
        i += 1
    if len(pos) != 1 or not re.match(r"https?://", pos[0]):
        print("usage: check_site.py <http(s)://base-url> [--pages N] [--external] [--compare URL] [--shots] [--out DIR]", file=sys.stderr)
        return 2
    try:
        max_pages = int(opts["--pages"])
    except ValueError:
        max_pages = 0
    if max_pages < 1:
        print("--pages needs a whole number of at least 1", file=sys.stderr)
        return 2
    base = norm(pos[0])
    now = datetime.datetime.now().astimezone()
    print(f"Checking {base} at {now:%Y-%m-%d %H:%M %Z} (read-only)")

    fails, warns, notes = [], [], []
    start = fetch(base)
    for c in start["chain"]:
        notes.append(f"redirect {c}")
    if start["error"] and start["status"] is None and not start["chain"]:
        print(f"SETUP  {base} did not answer: {start['error']}")
        print("No check ran. This says nothing about the site: check the address, VPN, sign-in or that it is running.")
        return 2
    if start["error"]:
        print(f"FAIL  {base}: the start page never settles ({start['error']}: {' | '.join(start['chain'])})")
        return 1
    if not same_site(start["final"], base):
        base = norm(urllib.parse.urljoin(start["final"], "/"))
        print(f"note  the start page moved to another host; now checking {base}")
    if start["status"] != 200:
        fails.append(f"FAIL  {start['final']}: the start page answers {start['status']}")
    elif not is_html(start):
        print(f"FAIL  {start['final']}: the start page is not an HTML page "
              f"(Content-Type {start['headers'].get('Content-Type')!r}); no pages were checked")
        return 1

    cache = {}

    def get(url):
        if url not in cache:
            cache[url] = fetch(url)
        return cache[url]

    cache[norm(start["final"])] = start
    queue, seen_pages, seen_bodies, skipped = [norm(start["final"])], [], set(), set()
    year = now.year
    while queue and len(seen_pages) < max_pages:
        url = queue.pop(0)
        if url in seen_pages:
            continue
        r = get(url)
        if r["error"] or r["status"] != 200 or not is_html(r) or not same_site(r["final"], base):
            continue
        digest = hashlib.sha256(r["body"]).digest()
        if digest in seen_bodies:  # "/" and "/index.html" are one page
            continue
        seen_bodies.add(digest)
        seen_pages.append(url)
        if r["cut"]:
            warns.append(f"WARN  {url}: cut off after 5 MB or 30 seconds; only that part was checked")
        p = Page()
        p.feed(decode(r))
        text = " ".join(" ".join(p.text).split())
        title = (p.title or "").strip()
        if title.lower() in DEFAULT_TITLES:
            fails.append(f"FAIL  {url}: missing or default <title> ({title!r})")
        for where, value in (("text", text), ("<title>", title), ("meta description", p.meta.get("description", ""))):
            found = placeholder(value)
            if found:
                fails.append(f"FAIL  {url}: placeholder {where} {found!r}")
        if not p.meta.get("description"):
            warns.append(f"WARN  {url}: no meta description")
        if "viewport" not in p.meta:
            warns.append(f"WARN  {url}: no viewport meta tag (phones will zoom out)")
        if not p.lang:
            warns.append(f"WARN  {url}: <html> has no lang")
        if p.imgs_no_alt:
            warns.append(f"WARN  {url}: {p.imgs_no_alt} image(s) without alt")
        years = [int(y) for y in re.findall(r"(?:©|&copy;|copyright)\s*(?:\d{4}\s*[-–]\s*)?(\d{4})", text, re.I)]
        if years and max(years) < year:
            warns.append(f"WARN  {url}: copyright year {max(years)}")
        for ref in p.links + p.assets:
            target = urllib.parse.urljoin(r["final"], ref.strip())
            if not target.startswith(("http://", "https://")):
                continue
            target = norm(target)
            if r["final"].startswith("https://") and target.startswith("http://") and ref in p.assets:
                fails.append(f"FAIL  {url}: loads {target} over http (mixed content)")
            if same_site(target, base):
                if RISKY_LINK.search(urllib.parse.urlsplit(target).path + "?" + urllib.parse.urlsplit(target).query):
                    skipped.add(target)
                    continue
                if ref in p.links and target not in seen_pages and target not in queue:
                    queue.append(target)
                t = get(target)
                if t["error"] or (t["status"] and t["status"] >= 400):
                    fails.append(f"FAIL  {url}: broken link {target} ({t['error'] or t['status']})")
            elif "--external" in flags:
                if target not in cache:
                    t = fetch(target, "HEAD")
                    if t["error"] or (t["status"] and t["status"] >= 400):
                        t = fetch(target)
                    cache[target] = t
                t = cache[target]
                if t["error"] or (t["status"] and t["status"] >= 400):
                    fails.append(f"FAIL  {url}: broken external link {target} ({t['error'] or t['status']})")
        if not p.icon and url == norm(start["final"]):
            t = fetch(urllib.parse.urljoin(base, "/favicon.ico"))
            if t["error"] or t["status"] != 200:
                warns.append(f"WARN  no favicon (no <link rel=icon>, /favicon.ico answers {t['error'] or t['status']})")

    if not seen_pages:
        fails.append(f"FAIL  no HTML page could be checked from {base}")

    missing_path = urllib.parse.urljoin(base, f"/deploy-verify-missing-{uuid.uuid4().hex[:8]}")
    t = fetch(missing_path)
    if t["status"] == 200:
        fails.append(f"FAIL  {missing_path} answers 200: a missing page should answer 404 (soft 404)")
    elif t["status"] == 404:
        notes.append("missing page answers 404 (look at it: is it the site's own page or the host's default?)")
    for path in ("/robots.txt", "/sitemap.xml"):
        t = fetch(urllib.parse.urljoin(base, path))
        if t["status"] != 200:
            warns.append(f"WARN  {path} answers {t['error'] or t['status']}")
        elif path == "/robots.txt" and re.search(r"(?im)^\s*disallow:\s*/\s*$", decode(t)):
            warns.append("WARN  robots.txt blocks the whole site (Disallow: /); fine on staging, not on production")
    if skipped:
        notes.append(f"not fetched: {len(skipped)} link(s) that may change something when opened "
                     f"({', '.join(sorted(skipped)[:3])}{' ...' if len(skipped) > 3 else ''})")
    if "--external" not in flags:
        notes.append("links to other sites were not checked (add --external)")

    if opts["--compare"]:
        other = norm(opts["--compare"])
        diffs = 0
        here = seen_pages + [u for u in cache if u not in seen_pages and same_site(u, base)]
        for url in here:
            path = urllib.parse.urlsplit(url)
            rel = urllib.parse.urlunsplit(("", "", path.path, path.query, ""))
            a = get(url)
            b = fetch(urllib.parse.urljoin(other, rel))
            if b["error"] and b["status"] is None and not a["error"]:
                fails.append(f"FAIL  compare {rel}: {other} did not answer ({b['error']})")
                diffs += 1
                continue
            a_final = urllib.parse.urlsplit(a["final"]).path
            b_final = urllib.parse.urlsplit(b["final"]).path
            if a["status"] != b["status"] or a_final != b_final:
                fails.append(f"FAIL  compare {rel}: {a['status']} at {a_final} here, {b['status']} at {b_final} on {other}")
                diffs += 1
            elif hashlib.sha256(a["body"]).digest() != hashlib.sha256(b["body"]).digest():
                fails.append(f"FAIL  compare {rel}: same status, different bytes ({len(a['body'])} vs {len(b['body'])})")
                diffs += 1
        notes.append(f"compared {len(here)} address(es) found here with {other}: {diffs} differ "
                     "(only what this crawl found; pages only the other host has are not looked for)")

    if "--shots" in flags:
        f, n = shots(seen_pages, pathlib.Path(opts["--out"]))
        fails += f
        notes += n
    else:
        notes.append("NOT RUN  phone width and dark mode (add --shots, or look in a browser)")

    for line in sorted(set(fails)) + sorted(set(warns)):
        print(line)
    for n in notes:
        print(f"note  {n}")
    print(f"Summary: {len(seen_pages)} page(s), {len(cache)} address(es) fetched, "
          f"{len(set(fails))} FAIL, {len(set(warns))} WARN")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
