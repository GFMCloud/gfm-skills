#!/usr/bin/env python3
"""Prove a tree is clean before it is handed to someone else.

Usage:
  clean_check.py <tree> --terms <terms-file>
  clean_check.py --selftest

<terms-file> holds the strings that must not travel, one per line: names, emails, phone numbers,
account names, team or client names. Matching ignores case. A line starting with "re:" is a regular
expression; blank lines and lines starting with "#" are skipped. The file must live outside <tree>,
or it would ship the very list it protects.

Checks, all on <tree>:
  terms      every file's name and contents (binary too), and if <tree> has a .git folder, every
             commit's author, committer, message and diff. Prints the term's number, never the term.
  history    a .git folder with more than one commit, or with any remote: the delivered tree should
             start a new history.
  names      files that usually hold secrets (.env, keys, certificates, credential files) fail;
             data files (.db, .sqlite, .csv, .xlsx, .json over 100 KB) are listed to confirm.
  gitleaks   runs gitleaks on the tree when it is installed, and says so when it is not.

Exit codes: 0 clean, 1 a term, secret file, gitleaks finding or old history found, 2 bad input.
Standard library only. A clean result means none of these matched, not that nothing personal is
left: read the tree once yourself.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

SECRET_NAMES = re.compile(r"(^|/)(\.env(\.[\w-]+)?|id_(rsa|ed25519|ecdsa|dsa)|[^/]*\.(pem|key|p12|pfx|keystore|jks|tfvars|ovpn)|"
                          r"credentials[^/]*|\.netrc|\.npmrc|\.pypirc|secrets?\.(json|ya?ml|toml))$", re.I)
SAFE_ENV = re.compile(r"\.env\.(example|sample|template)$", re.I)
DATA_NAMES = re.compile(r"\.(db|sqlite3?|csv|tsv|xlsx?|parquet|mbox|eml|vcf)$", re.I)


def load_terms(path, tree):
    if os.path.realpath(path).startswith(os.path.realpath(tree) + os.sep):
        sys.exit("the terms file is inside the tree; move it outside, or it ships with the tree")
    terms = []
    for line in open(path, encoding="utf-8"):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        try:
            pat = re.compile(s[3:] if s.startswith("re:") else re.escape(s), re.I)
        except re.error as e:
            sys.exit(f"bad pattern on a line of the terms file: {e}")
        terms.append(pat)
    if not terms:
        sys.exit("the terms file has no terms; an empty list proves nothing")
    return terms


def git(tree, *args):
    p = subprocess.run(["git", "-C", tree, *args], capture_output=True)
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def check(tree, terms):
    fails, notes = [], []
    hits = {n: [] for n in range(1, len(terms) + 1)}
    secret_files, data_files = [], []
    for root, dirs, files in os.walk(tree):
        dirs[:] = [d for d in dirs if d != ".git"]
        for f in files:
            p = os.path.join(root, f)
            rel = os.path.relpath(p, tree)
            if SECRET_NAMES.search(rel) and not SAFE_ENV.search(rel):
                secret_files.append(rel)
            if DATA_NAMES.search(rel) or (rel.lower().endswith(".json") and os.path.getsize(p) > 100_000):
                data_files.append(rel)
            try:
                text = open(p, "rb").read().decode("utf-8", errors="replace")
            except OSError:
                fails.append(f"unreadable: {rel} (it would still ship; fix its permissions or remove it, then rerun)")
                continue
            for n, pat in enumerate(terms, 1):
                if pat.search(rel) or pat.search(text):
                    hits[n].append(rel)
    if os.path.isdir(os.path.join(tree, ".git")):
        code, count = git(tree, "rev-list", "--all", "--count")
        if code == 0 and count.strip().isdigit() and int(count) > 1:
            fails.append(f"history: {count.strip()} commits travel with this tree; start a new history")
        _, remotes = git(tree, "remote")
        if remotes.strip():
            fails.append(f"history: the tree has remotes ({', '.join(remotes.split())}); a delivered tree has none")
        _, log = git(tree, "log", "--all", "-p", "--format=%an <%ae>%n%cn <%ce>%n%B")
        for n, pat in enumerate(terms, 1):
            if pat.search(log):
                hits[n].append("(git history: an author, committer, message or diff)")
    for n, files in hits.items():
        if files:
            shown = ", ".join(files[:10]) + (f" and {len(files) - 10} more" if len(files) > 10 else "")
            fails.append(f"term #{n}: found in {len(files)} place(s): {shown}")
    for rel in secret_files:
        fails.append(f"secret-type file: {rel}")
    if shutil.which("gitleaks"):
        p = subprocess.run(["gitleaks", "detect", "--no-git", "--source", tree, "--redact", "--no-banner",
                            "--exit-code", "1"], capture_output=True)
        if p.returncode == 1:
            fails.append("gitleaks: found something (rerun: gitleaks detect --no-git --redact --source <tree>)")
        elif p.returncode != 0:
            notes.append(f"gitleaks: could not run (exit {p.returncode})")
        else:
            notes.append("gitleaks: no findings")
    else:
        notes.append("gitleaks: not installed, not run")
    return fails, notes, data_files


def report(tree, terms, fails, notes, data_files):
    print(f"Tree: {tree}\nTerms checked: {len(terms)}")
    for f in fails:
        print(f"FAIL {f}")
    for d in data_files:
        print(f"CONFIRM data file holds nothing personal: {d}")
    for n in notes:
        print(f"note: {n}")
    print("CLEAN: no term, secret-type file, gitleaks finding or old history." if not fails
          else f"NOT CLEAN: {len(fails)} finding(s). Fix the tree and run this again.")
    print("Not checked: anything personal that is not on the terms list. Read the tree once yourself.")


def selftest():
    d = tempfile.mkdtemp()
    tree, terms = os.path.join(d, "tree"), os.path.join(d, "terms.txt")
    os.makedirs(os.path.join(tree, "data"))
    open(terms, "w").write("# demo terms\nDemo Person\nre:demo\\.person@example\\.com\n")
    open(os.path.join(tree, "app.py"), "w").write("print('hello')\n")
    open(os.path.join(tree, ".env.example"), "w").write("API_KEY=\n")
    t = load_terms(terms, tree)
    results = [("clean tree passes", len(check(tree, t)[0]), 0)]
    open(os.path.join(tree, "data", "roster.csv"), "w").write("name\ndemo person\n")
    fails, _, data = check(tree, t)
    results += [("finds a term regardless of case", sum("term #1" in f for f in fails), 1),
                ("lists the data file", data, ["data/roster.csv"])]
    os.remove(os.path.join(tree, "data", "roster.csv"))
    open(os.path.join(tree, ".env"), "w").write("X=1\n")
    results.append(("flags .env", sum("secret-type" in f for f in check(tree, t)[0]), 1))
    os.remove(os.path.join(tree, ".env"))
    if shutil.which("git"):
        env = dict(os.environ, GIT_AUTHOR_NAME="Demo Person", GIT_AUTHOR_EMAIL="demo.person@example.com",
                   GIT_COMMITTER_NAME="x", GIT_COMMITTER_EMAIL="x@example.com")
        subprocess.run(["git", "-C", tree, "init", "-q"], check=True)
        subprocess.run(["git", "-C", tree, "add", "-A"], check=True)
        subprocess.run(["git", "-C", tree, "-c", "core.hooksPath=/dev/null", "commit", "-q", "-m", "x"], check=True, env=env)
        fails = check(tree, t)[0]
        results.append(("finds a term in commit authors", sum("git history" in f for f in fails), 2))
    locked = os.path.join(tree, "locked.txt")
    open(locked, "w").write("nothing\n")
    os.chmod(locked, 0)
    results.append(("an unreadable file fails", sum("unreadable" in f for f in check(tree, t)[0]), 1))
    os.chmod(locked, 0o600)
    os.remove(locked)
    inside = os.path.join(tree, "terms.txt")
    open(inside, "w").write("x\n")
    try:
        load_terms(inside, tree)
        results.append(("refuses a terms file inside the tree", "accepted", "refused"))
    except SystemExit:
        results.append(("refuses a terms file inside the tree", "refused", "refused"))
    bad = [(n, g, w) for n, g, w in results if g != w]
    for n, g, w in bad:
        print(f"FAIL {n}: got {g!r}, want {w!r}")
    shutil.rmtree(d, ignore_errors=True)
    print(f"selftest: {len(results) - len(bad)} of {len(results)} passed")
    return 1 if bad else 0


def main(argv):
    if argv[:1] == ["--selftest"]:
        return selftest()
    if len(argv) != 3 or argv[1] != "--terms":
        print(__doc__)
        return 2
    tree, terms_path = os.path.abspath(argv[0]), argv[2]
    if not os.path.isdir(tree) or not os.path.isfile(terms_path):
        print(f"need an existing tree and terms file: {tree}, {terms_path}")
        return 2
    terms = load_terms(terms_path, tree)
    fails, notes, data_files = check(tree, terms)
    report(tree, terms, fails, notes, data_files)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
