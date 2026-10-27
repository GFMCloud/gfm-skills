#!/usr/bin/env python3
"""Regression tests for deploy-verify's scripts, against the DEMO fixtures. Not part of the skill.

Usage: python3 evals/deploy-verify/test_scripts.py   (from the repo root)

Serves the fixture sites on 127.0.0.1 (demo_server.py, free ports) and checks that check_site.py
and smoke.py pass what should pass and fail what should fail. Needs local ports: in an agent
sandbox that blocks them, run it outside the sandbox. Standard library only (--shots not tested).
"""
import http.server
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import threading

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parents[1] / "skills" / "deploy-verify" / "scripts"
FILES = HERE / "files"
sys.path.insert(0, str(HERE))
import demo_server  # noqa: E402

demo_server.QUIET = True


def serve(folder):
    s = http.server.ThreadingHTTPServer(("127.0.0.1", 0), demo_server.handler_for(folder))
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{s.server_address[1]}/"


def run(script, *args, env=None):
    p = subprocess.run([sys.executable, str(SCRIPTS / script), *args], capture_output=True, text=True,
                       env={**os.environ, **(env or {})}, cwd=tempfile.mkdtemp())
    return p.returncode, p.stdout + p.stderr


RESULTS = []


def expect(name, code, out, want_code, must=(), must_not=()):
    ok = code == want_code and all(m in out for m in must) and not any(m in out for m in must_not)
    RESULTS.append(ok)
    print(f"{'ok  ' if ok else 'FAIL'} {name}")
    if not ok:
        print(f"     exit {code} (wanted {want_code})\n" + "\n".join("     " + line for line in out.splitlines()))


def main():
    site = serve(FILES / "launch-site/site")
    old = serve(FILES / "recipes-move/old-host")
    new = serve(FILES / "recipes-move/new-host")
    cur = serve(FILES / "bakery-smoke/site")
    prev = serve(FILES / "bakery-smoke/previous")
    tmp = pathlib.Path(tempfile.mkdtemp())
    clean = tmp / "clean"
    shutil.copytree(FILES / "bakery-smoke/site", clean)
    (clean / "robots.txt").write_text("User-agent: *\nAllow: /\n")
    (clean / "sitemap.xml").write_text("<urlset/>")
    (clean / "favicon.ico").write_bytes(b"\0")
    clean_url = serve(clean)

    code, out = run("check_site.py", site)
    expect("check_site finds planted problems", code, out, 1,
           must=["broken link http", "img/hero.jpg (404)", "team.html (404)", "placeholder text 'Lorem ipsum'",
                 "copyright year 2024", "no meta description", "/sitemap.xml answers 404", "NOT RUN  phone width"])
    code, out = run("check_site.py", clean_url)
    expect("check_site passes a clean site", code, out, 0, must_not=["FAIL  "])
    code, out = run("check_site.py", new, "--compare", old)
    expect("check_site --compare finds the missing page and the moved address", code, out, 1,
           must=["compare /recipes/soup.html: 404", "compare /about.html: 200 at /about here"])
    code, out = run("check_site.py", old, "--compare", old)
    expect("check_site --compare passes identical hosts", code, out, 0, must=[": 0 differ"])
    code, out = run("check_site.py", "http://127.0.0.1:9/")
    expect("check_site: no answer is a setup problem", code, out, 2, must=["SETUP", "No check ran"])
    code, out = run("check_site.py", "--pages")
    expect("check_site: bad arguments exit 2", code, out, 2)

    spec = tmp / "smoke.json"
    spec.write_text(json.dumps({"base": cur, "checks": [
        {"name": "build", "path": "/version.txt", "contains": ["${BUILD_ID}"]},
        {"name": "hours", "path": "/", "contains": ["Open today 8 to 4"]},
        {"name": "menu", "path": "/menu.html", "contains": ["Sourdough loaf"]},
        {"name": "order page", "path": "/order.html", "contains": ["Send order"]},
    ]}))
    env = {"BUILD_ID": "42"}
    code, out = run("smoke.py", str(spec), env=env)
    expect("smoke passes the current release", code, out, 0, must=["SMOKE PASS: 4 of 4 passed"])
    code, out = run("smoke.py", str(spec), "--base", prev, env=env)
    expect("smoke fails the previous release", code, out, 1, must=["SMOKE FAIL: 3 of 4 failed", "missing '42'"])
    code, out = run("smoke.py", str(spec), "--prove", prev, env=env)
    expect("smoke --prove names the check that can't tell builds apart", code, out, 0,
           must=["NEVER SEEN FAILING  order page", "1 never seen failing"])
    code, out = run("smoke.py", str(spec), env={"BUILD_ID": ""})
    expect("smoke: unset variable is a setup problem", code, out, 2, must=["${BUILD_ID} is not set", "SMOKE SETUP"])
    code, out = run("smoke.py", str(spec), "--base", "http://127.0.0.1:9/", env=env)
    expect("smoke: no answer is a setup problem", code, out, 2, must=["did not answer any check"])
    bad = tmp / "bad.json"
    bad.write_text(json.dumps({"base": cur, "checks": [{"path": "/", "contains": [""]}]}))
    code, out = run("smoke.py", str(bad), env=env)
    expect("smoke rejects empty expected text", code, out, 2, must=["non-empty text"])

    # Review round 1 (Fable): each of these failed before the fix.
    target = serve(FILES / "launch-site/site")
    hop = tmp / "hop"
    hop.mkdir()
    (hop / "_redirects").write_text(f"/ {target} 301\n")
    code, out = run("check_site.py", serve(hop))
    expect("check_site follows a start page that redirects to another host", code, out, 1,
           must=["now checking " + target, "team.html (404)"])
    plain = tmp / "plain"
    plain.mkdir()
    (plain / "notes.txt").write_text("just text")
    (plain / "_redirects").write_text("/ /notes.txt 302\n")
    code, out = run("check_site.py", serve(plain))
    expect("check_site fails a start page that is not HTML", code, out, 1, must=["not an HTML page"])
    code, out = run("check_site.py", site, "--pages", "0")
    expect("check_site never passes zero pages", code, out, 2)
    loop = tmp / "loop"
    loop.mkdir()
    (loop / "_redirects").write_text("/ /a 302\n/a / 302\n")
    code, out = run("check_site.py", serve(loop))
    expect("check_site: a redirect loop is a FAIL, not a setup problem", code, out, 1, must=["redirect"])
    todo = tmp / "todo"
    shutil.copytree(clean, todo)
    (todo / "index.html").write_text((todo / "index.html").read_text().replace("Bread baked", "Todo list and bread baked"))
    code, out = run("check_site.py", serve(todo))
    expect("check_site: the word 'Todo' is not a placeholder", code, out, 0, must_not=["placeholder"])
    code, out = run("check_site.py", old, "--compare", new)
    expect("check_site --compare from the old host lists pages missing on the new one", code, out, 1,
           must=["compare /recipes/soup-tips.html: 200", "compare /recipes/soup.html: 200"])

    risky = tmp / "risky"
    shutil.copytree(clean, risky)
    (risky / "index.html").write_text((risky / "index.html").read_text().replace(
        '<a href="/order.html">Order</a>', '<a href="/order.html">Order</a> <a href="/account/logout">Sign out</a>'))
    code, out = run("check_site.py", serve(risky))
    expect("check_site never opens a logout link", code, out, 0,
           must=["not fetched: 1 link(s) that may change something", "/account/logout"], must_not=["broken link"])

    ent = tmp / "entities.json"
    ent.write_text(json.dumps({"base": cur, "checks": [
        {"name": "menu price", "path": "/menu.html", "contains": ["Sourdough loaf, £4.20"]},
        {"name": "exact build", "path": "/version.txt", "equals": "42"},
    ]}))
    code, out = run("smoke.py", str(ent))
    expect("smoke matches text written as HTML entities, and equals is exact", code, out, 0,
           must=["SMOKE PASS: 2 of 2 passed"])
    ent.write_text(json.dumps({"base": cur, "checks": [{"name": "exact build", "path": "/version.txt", "equals": "4"}]}))
    code, out = run("smoke.py", str(ent))
    expect("smoke equals fails on a partial match", code, out, 1, must=["SMOKE FAIL"])
    red = tmp / "redirect.json"
    red.write_text(json.dumps({"base": new, "checks": [{"name": "about", "path": "/about.html", "contains": ["Nana's notebook"]}]}))
    code, out = run("smoke.py", str(red))
    expect("smoke follows a 308 redirect and shows it", code, out, 0, must=["308", "SMOKE PASS"])
    for bad_check in ({"path": "/", "status": "two hundred"}, {"path": "/", "status": None}, {"path": "/", "max_ms": "fast"},
                      {"path": "/", "status": True}, {"path": "/", "header": {"Content-Type": ["html"]}},
                      {"path": "http://127.0.0.1:9/elsewhere"}, {"path": "/", "equals": 42}):
        bad.write_text(json.dumps({"base": cur, "checks": [bad_check]}))
        code, out = run("smoke.py", str(bad), env=env)
        expect(f"smoke rejects {json.dumps(bad_check)} as a setup problem", code, out, 2, must=["SMOKE SETUP"],
               must_not=["Traceback"])

    print(f"{sum(RESULTS)} of {len(RESULTS)} script tests behaved as expected")
    return 0 if all(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
