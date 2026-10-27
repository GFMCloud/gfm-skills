#!/usr/bin/env python3
"""Run a project's smoke checks against a running site or service. Read-only: GET requests only.

Usage:
  python3 smoke.py <smoke.json> [--base <url>] [--prove <url of a build that should fail>]

smoke.json (keep it in the project, next to this script):
  {
    "base": "https://staging.example.org",
    "checks": [
      {"name": "right build is live", "path": "/version.txt", "equals": "${BUILD_ID}"},
      {"name": "pricing page", "path": "/pricing", "status": 200, "contains": ["£12 a month"],
       "not_contains": ["lorem ipsum"], "max_ms": 3000},
      {"name": "API answers", "path": "/api/health", "header": {"Content-Type": "json"}}
    ]
  }

Each check: "path" (required, starting with "/"); "status" (default 200); "contains" /
"not_contains": text that must or must not be in the body (HTML entities such as &pound; count as
the character they stand for); "equals": the whole body, ignoring surrounding whitespace (use it for
a version file, so "142" doesn't pass for "42"); "header": header name -> text its value must
contain; "max_ms": time limit. ${NAME} in any text is replaced from the environment, so a check can
name the build that should be live; an unset variable is a setup error, never a silent pass.
Redirects are followed by hand and shown; "status" is the status at the end of them.

--base runs the same checks against another address (staging, production, a local server).
--prove <url> runs the checks against the base (all must pass), then against <url>, a build where
they should fail (the old build, a copy with the change reverted). Any check that passes on both is
listed as NEVER SEEN FAILING: it can't tell the two builds apart.

Every line starts PASS, FAIL or SETUP. The last line is "SMOKE PASS: n of n passed",
"SMOKE FAIL: k of n failed" or "SMOKE SETUP", with the base address and time.
Exit codes: 0 all pass, 1 any check failed, 2 setup problem (bad file, unset variable, or the
target did not answer any check): the checks never ran, so this says nothing about the site.
Standard library only.
"""
import datetime
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

TIMEOUT = 15          # seconds per socket read
MAX_BYTES = 5_000_000
UA = "deploy-verify-smoke/1 (read-only)"
VAR = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
REDIRECTS = {301, 302, 303, 307, 308}


class SetupError(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def expand(text):
    def sub(m):
        if not os.environ.get(m.group(1)):
            raise SetupError(f"${{{m.group(1)}}} is not set")
        return os.environ[m.group(1)]
    return VAR.sub(sub, str(text))


def is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            spec = json.load(f)
    except (OSError, ValueError) as e:
        raise SetupError(f"can't read {path}: {e}")
    checks = spec.get("checks") if isinstance(spec, dict) else None
    if not isinstance(checks, list) or not checks:
        raise SetupError(f"{path} has no \"checks\" list")
    for i, c in enumerate(checks):
        if not isinstance(c, dict) or not isinstance(c.get("path"), str):
            raise SetupError(f"check {i + 1} needs a \"path\"")
        if not c["path"].startswith("/") or c["path"].startswith("//"):
            raise SetupError(f"check {i + 1}: \"path\" must start with a single \"/\" (got {c['path']!r}); "
                             "the address comes from \"base\" or --base")
        c.setdefault("name", c["path"])
        for key in ("contains", "not_contains"):
            v = c.get(key, [])
            if isinstance(v, str):
                v = [v]
            if not isinstance(v, list) or any(not isinstance(t, str) or not t.strip() for t in v):
                raise SetupError(f"check {c['name']!r}: \"{key}\" must be a list of non-empty text")
            c[key] = v
        if "equals" in c and not isinstance(c["equals"], str):
            raise SetupError(f"check {c['name']!r}: \"equals\" must be text")
        status = c.get("status", 200)
        if not is_int(status) or not 100 <= status <= 599:
            raise SetupError(f"check {c['name']!r}: \"status\" must be a number from 100 to 599 (got {status!r})")
        c["status"] = status
        if "max_ms" in c and (not isinstance(c["max_ms"], (int, float)) or isinstance(c["max_ms"], bool)
                              or c["max_ms"] <= 0):
            raise SetupError(f"check {c['name']!r}: \"max_ms\" must be a positive number (got {c['max_ms']!r})")
        header = c.get("header", {})
        if not isinstance(header, dict) or any(not isinstance(v, str) for v in header.values()):
            raise SetupError(f"check {c['name']!r}: \"header\" must map a header name to text")
    return spec, checks


def fetch(url, timeout):
    """GET with redirects followed by hand. Returns (status, headers, body, chain); raises on no answer."""
    chain, seen = [], {url}
    for _ in range(10):
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Cache-Control": "no-cache"})
        try:
            resp = OPENER.open(req, timeout=timeout)
            status = resp.status
        except urllib.error.HTTPError as e:
            resp, status = e, e.code
        headers, body = resp.headers, resp.read(MAX_BYTES)
        if status in REDIRECTS and headers.get("Location"):
            nxt = urllib.parse.urljoin(url, headers["Location"])
            chain.append(f"{status} -> {urllib.parse.urlsplit(nxt).path or '/'}")
            if nxt in seen:
                return status, headers, body, chain + ["loop"]
            seen.add(nxt)
            url = nxt
            continue
        return status, headers, body, chain
    return status, headers, body, chain + ["too many redirects"]


def run_one(base, c):
    """Return (ok, reached, detail)."""
    url = urllib.parse.urljoin(base.rstrip("/") + "/", expand(c["path"]).lstrip("/"))
    timeout = min(TIMEOUT, max(1.0, c["max_ms"] / 1000 * 2)) if c.get("max_ms") else TIMEOUT
    start = time.monotonic()
    try:
        status, headers, body, chain = fetch(url, timeout)
    except Exception as e:
        return False, False, f"no answer from {url}: {type(e).__name__}: {e}"
    ms = int((time.monotonic() - start) * 1000)
    raw = body.decode("utf-8", errors="replace")
    texts = (raw, html.unescape(raw))
    problems = []
    if chain and chain[-1] in ("loop", "too many redirects"):
        problems.append(f"redirects never settle ({', '.join(chain)})")
    if status != c["status"]:
        problems.append(f"status {status}, wanted {c['status']}")
    for t in c["contains"]:
        t = expand(t)
        if not any(t in x for x in texts):
            problems.append(f"missing {t!r}")
    for t in c["not_contains"]:
        t = expand(t)
        if any(t in x for x in texts):
            problems.append(f"contains {t!r}")
    if "equals" in c:
        want = expand(c["equals"]).strip()
        if want not in (raw.strip(), html.unescape(raw).strip()):
            problems.append(f"body is {raw.strip()[:60]!r}, wanted exactly {want!r}")
    for name, t in c.get("header", {}).items():
        val = headers.get(name) or ""
        if expand(t).lower() not in val.lower():
            problems.append(f"header {name}: {val!r}, wanted {expand(t)!r}")
    if c.get("max_ms") and ms > c["max_ms"]:
        problems.append(f"took {ms} ms, limit {c['max_ms']}")
    via = f" (after {', '.join(chain)})" if chain else ""
    detail = f"{status}{via}, {ms} ms" if not problems else "; ".join(problems) + via
    return not problems, True, detail


def run_all(base, checks, label=""):
    results = []
    for c in checks:
        ok, reached, detail = run_one(base, c)
        results.append((c["name"], ok, reached, detail))
        print(f"{label}{'PASS' if ok else 'FAIL'}  {c['name']}: {detail}")
    return results


def main():
    args = sys.argv[1:]
    opts = {"--base": None, "--prove": None}
    pos = []
    i = 0
    while i < len(args):
        if args[i] in opts:
            if i + 1 >= len(args):
                print(f"{args[i]} needs a value", file=sys.stderr)
                return 2
            opts[args[i]] = args[i + 1]
            i += 2
            continue
        if args[i] in ("-h", "--help"):
            print(__doc__)
            return 0
        pos.append(args[i])
        i += 1
    if len(pos) != 1:
        print("usage: smoke.py <smoke.json> [--base URL] [--prove URL]", file=sys.stderr)
        return 2
    now = datetime.datetime.now().astimezone()
    base = opts["--base"]
    try:
        spec, checks = load(pos[0])
        base = base or spec.get("base")
        if not base or not re.match(r"https?://", str(base)):
            raise SetupError("no http(s) base address (set \"base\" in the file or pass --base)")
        base = expand(base)
        print(f"Smoke checks from {pos[0]} against {base} at {now:%Y-%m-%d %H:%M %Z}")
        results = run_all(base, checks)
    except SetupError as e:
        print(f"SETUP  {e}")
        print(f"SMOKE SETUP: no check ran against {base or 'any address'}; this says nothing about the site")
        return 2
    except Exception as e:  # a bug or an input the checks above missed: never report it as a site failure
        print(f"SETUP  {type(e).__name__}: {e}")
        print(f"SMOKE SETUP: the checks could not run against {base or 'any address'}; "
              "this says nothing about the site")
        return 2
    if not any(r[2] for r in results):
        print(f"SMOKE SETUP: {base} did not answer any check; this says nothing about the site "
              "(check the address, VPN, sign-in or that it is running)")
        return 2
    failed = [r for r in results if not r[1]]
    proof = ""
    if opts["--prove"]:
        if failed:
            print("Can't prove the checks: they must all pass on the base first. Fix the failing checks "
                  "(or the site) and run --prove again.")
            proof = "; proof not run (base failed)"
        else:
            bad = opts["--prove"]
            print(f"Proving against {bad} (should fail):")
            try:
                bad_results = run_all(bad, checks, label="  on bad build: ")
            except SetupError as e:
                print(f"SETUP  {e}")
                return 2
            never = [r[0] for r in bad_results if r[1]]
            for name in never:
                print(f"NEVER SEEN FAILING  {name}: passes on both builds, so it can't tell them apart")
            if not any(r[2] for r in bad_results):
                print(f"PROOF NOT RUN: {bad} did not answer, so no check was seen failing")
                proof = "; proof not run"
            else:
                print(f"Proof: {len(checks) - len(never)} of {len(checks)} checks failed on the bad build")
                proof = f"; {len(never)} never seen failing" if never else "; every check seen failing"
    tally = (f"PASS: {len(results)} of {len(results)} passed" if not failed
             else f"FAIL: {len(failed)} of {len(results)} failed")
    print(f"SMOKE {tally} against {base} at {now:%Y-%m-%d %H:%M %Z}{proof}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
