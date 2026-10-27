#!/usr/bin/env python3
"""Find what must not go into a repo's first commit (or any later one).

Usage:
  python3 secret_scan.py FOLDER            before git exists: what is in the folder
  python3 secret_scan.py --git FOLDER      what `git add -A` would add right now
  python3 secret_scan.py --staged FOLDER   what is staged (the pre-commit hook uses this)
  python3 secret_scan.py --history FOLDER  every commit reachable from any branch or tag
  python3 secret_scan.py --selftest        prove each check can fail, in a temp folder

Options: --max-mb N (default 50) sets the large-file limit.

Prints one line per finding as KIND path[:line] detail, never the secret itself, then a RESULT
line. Exit 0 = nothing blocks, 2 = something blocks, 1 = bad usage or not a git repo.
Standard library only, Python 3.9+. Pattern checks catch common slips, not every secret.
"""
import math
import os
import re
import subprocess
import sys
import tempfile

SECRET_FILE_NAMES = {
    ".env", ".netrc", ".pgpass", "credentials", "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519",
    "terraform.tfstate", "terraform.tfstate.backup", ".git-credentials", "secrets.yml", "secrets.yaml",
    "secrets.json", ".secrets",
}
SECRET_FILE_SUFFIXES = (".pem", ".key", ".p12", ".pfx", ".jks", ".keystore", ".kdbx", ".tfvars",
                        ".tfstate", ".tfstate.backup", ".ovpn")
SAFE_SUFFIXES = (".example", ".sample", ".template", ".dist", ".pub")
# Dependency and cache folders: never scanned in folder mode (they can be huge); they belong in .gitignore.
GENERATED_DIRS = {"node_modules", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache",
                  ".ruff_cache", ".terraform", ".parcel-cache", ".tox"}
# Build output: often rebuildable, but some projects publish it, so it is always scanned.
OUTPUT_DIRS = {"dist", "build", "target", ".next", "out"}
JUNK_FILES = {".DS_Store", "Thumbs.db", "desktop.ini"}

PATTERNS = [
    ("aws-access-key-id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("aws-secret-key", re.compile(r"(?i)aws_?secret_?access_?key\s*[=:]\s*['\"]?[A-Za-z0-9/+=]{40}")),
    ("private-key", re.compile(r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----")),
    ("github-token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,})")),
    ("slack-token", re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}")),
    ("stripe-live-key", re.compile(r"\b[rs]k_live_[A-Za-z0-9]{20,}")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("ai-api-key", re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_-]{32,}")),
    ("npm-token", re.compile(r"\bnpm_[A-Za-z0-9]{36}\b")),
    ("npm-auth", re.compile(r"(?i)_auth(?:Token)?\s*=\s*[^\s$]{8,}")),
    ("bearer-token", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/-]{20,}")),
    ("password-in-url", re.compile(r"\b[a-z][a-z0-9+.-]*://[^/\s:@'\"]+:([^/\s@'\"]{3,})@")),
]
# A name such as DB_PASSWORD, githubToken or client-secret, then = or :, then a value (quoted or not).
ASSIGN = re.compile(r"(?i)(?<![a-z0-9])(?:[a-z0-9]+[_.-])*(?:password|passwd|secret|api[_-]?key|token|"
                    r"private[_-]?key)(?:[_.-][a-z0-9]+)*['\"]?\s*[:=]\s*(['\"]?)([^'\"\s#,;]{8,})\1")
PLACEHOLDER = re.compile(r"(?i)example|changeme|change_me|your[_-]|xxx|\*\*\*|<|\{\{|\$\{|\$\(|%\(|"
                         r"environ|getenv|process\.env|dummy|placeholder|redacted|not[_-]?real|"
                         r"^pass(?:word|wd)?$|^secret$|^token$")
NOT_A_VALUE = re.compile(r"^(?:https?://|/|~|\.{1,2}/)|^[a-z]+(?:-[a-z]+){2,}$|[()\[\]]")


def entropy(s):
    counts = {c: s.count(c) for c in set(s)}
    return -sum(n / len(s) * math.log2(n / len(s)) for n in counts.values())


def is_secret_file(name):
    low = name.lower()
    if low.endswith(SAFE_SUFFIXES):
        return False
    if low in SECRET_FILE_NAMES or low.startswith(".env."):
        return True
    if low.startswith("service-account") and low.endswith(".json"):
        return True
    return low.endswith(SECRET_FILE_SUFFIXES)


def line_findings(text):
    """(line number, kind) for each likely secret in text. Never returns the value."""
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        for kind, pat in PATTERNS:
            m = pat.search(line)
            if not m or "EXAMPLE" in m.group(0):
                continue
            if kind == "password-in-url" and PLACEHOLDER.search(m.group(1)):
                continue
            out.append((n, kind))
        if any(k == n for k, _ in out):
            continue
        for m in ASSIGN.finditer(line):
            value, quoted = m.group(2), bool(m.group(1))
            if PLACEHOLDER.search(value) or NOT_A_VALUE.search(value) or entropy(value) < 3.0:
                continue
            if not quoted and (len(value) < 12 or not (re.search(r"[A-Za-z]", value) and re.search(r"\d", value))):
                continue
            out.append((n, "secret-assignment"))
            break
    return out


def decode(data):
    if b"\0" in data[:8192]:
        return None
    return data.decode("utf-8", errors="replace")


class Scan:
    def __init__(self, mode, max_mb):
        self.mode, self.max_bytes = mode, max_mb * 1024 * 1024
        self.block, self.ignore, self.note = [], [], []
        self.files = 0

    def check_file(self, rel, size, read):
        """read() returns bytes. Secret files are never read. A file that can't be read blocks."""
        self.files += 1
        rel = rel.replace("\n", "\\n")
        name = os.path.basename(rel)
        pre_git = self.mode == "folder"
        if is_secret_file(name):
            if self.mode == "history":
                self.block.append(f"SECRET-FILE {rel} is in git history: rotate what it holds (removing it now "
                                  "doesn't help) before any push")
            else:
                (self.ignore if pre_git else self.block).append(
                    f"SECRET-FILE {rel} whole file holds secrets: keep it out of git (.gitignore)")
            return
        if name in JUNK_FILES:
            (self.ignore if pre_git else self.note).append(f"JUNK {rel} system file: add {name} to .gitignore")
            return
        if size > self.max_bytes:
            (self.ignore if pre_git else self.block).append(
                f"LARGE {rel} {size // (1024 * 1024)} MB: GitHub warns over 50 MB and refuses over 100 MB; "
                "ignore it or use Git LFS")
            return
        try:
            text = decode(read() or b"")
        except (OSError, subprocess.CalledProcessError):
            self.block.append(f"UNREADABLE {rel} can't be read, so it can't be shown clean: fix its permissions "
                              "or leave it out of git")
            return
        if text is None:
            return
        for n, kind in line_findings(text):
            self.block.append(f"EMBEDDED {rel}:{n} {kind}: remove it from the file; if it was ever real, rotate it")

    def report(self, label):
        print(f"secret_scan: {self.mode} {label}: {self.files} files checked")
        for line in self.block:
            print("BLOCK " + line)
        for line in self.ignore:
            print("IGNORE " + line)
        for line in self.note:
            print("NOTE " + line)
        if self.mode == "folder" and self.ignore:
            print("Add to .gitignore before the first commit, then rerun with --git.")
        if self.block:
            print(f"RESULT: BLOCKED ({len(self.block)} to fix before any commit or push)")
            return 2
        print(f"RESULT: PASS ({len(self.ignore)} to ignore, {len(self.note)} notes)")
        return 0


def git(folder, *args):
    return subprocess.run(["git", "-C", folder, *args], capture_output=True, check=True).stdout


def scan_folder(folder, scan):
    for dp, dirs, files in os.walk(folder):
        rel_dir = os.path.relpath(dp, folder)
        keep = []
        for d in sorted(dirs):
            rel = os.path.normpath(os.path.join(rel_dir, d))
            if d == ".git":
                if rel_dir != ".":
                    scan.block.append(f"NESTED-GIT {rel_dir}/ has its own .git: decide submodule, merge or keep apart "
                                      "before the first commit (never delete it unasked)")
            elif d in GENERATED_DIRS:
                scan.ignore.append(f"GENERATED {rel}/ rebuildable folder: add {d}/ to .gitignore")
            else:
                keep.append(d)
        dirs[:] = keep
        for f in sorted(files):
            p = os.path.join(dp, f)
            if os.path.islink(p) or not os.path.isfile(p):
                continue
            rel = os.path.normpath(os.path.join(rel_dir, f))
            out_dir = next((d for d in rel.split(os.sep)[:-1] if d in OUTPUT_DIRS), None)
            if out_dir and f"{out_dir}/" not in " ".join(scan.note):
                scan.note.append(f"OUTPUT {out_dir}/ build output: ignore it unless the project publishes it")
            scan.check_file(rel, os.path.getsize(p), lambda p=p: read_bytes(p))


def scan_git(folder, scan):
    names = git(folder, "ls-files", "-z", "--cached", "--others", "--exclude-standard").decode("utf-8", "replace")
    for rel in sorted(n for n in names.split("\0") if n):
        p = os.path.join(folder, rel)
        if rel.endswith("/") or os.path.isdir(p):
            scan.block.append(f"NESTED-GIT {rel.rstrip('/')}/ has its own .git: git would add it as an empty link")
            continue
        parts = rel.split("/")
        gen = next((d for d in parts[:-1] if d in GENERATED_DIRS | OUTPUT_DIRS), None)
        if gen and f"{gen}/" not in " ".join(scan.note):
            scan.note.append(f"GENERATED {gen}/ is usually rebuildable: add it to .gitignore unless the project "
                             "publishes it (its files are still scanned)")
        if os.path.islink(p) or not os.path.isfile(p):
            continue
        scan.check_file(rel, os.path.getsize(p), lambda p=p: read_bytes(p))


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def scan_staged(folder, scan):
    names = git(folder, "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR").decode("utf-8", "replace")
    for rel in sorted(n for n in names.split("\0") if n):
        entry = git(folder, "ls-files", "-s", "-z", "--", rel).decode("utf-8", "replace").split(" ", 1)[0]
        if entry == "160000":
            scan.block.append(f"NESTED-GIT {rel}/ is staged as a link to another repo: git would store no files")
            continue
        size = int(git(folder, "cat-file", "-s", f":{rel}").strip() or 0)
        scan.check_file(rel, size, lambda rel=rel: git(folder, "show", f":{rel}"))


def scan_history(folder, scan):
    commits = git(folder, "rev-list", "--all").decode().split()
    if not commits:
        raise NoCommits()
    seen = set()
    for c in commits:
        tree = git(folder, "ls-tree", "-r", "-z", "-l", c).decode("utf-8", "replace")
        for entry in (e for e in tree.split("\0") if e):
            meta, rel = entry.split("\t", 1)
            _mode, kind, blob, size = meta.split()
            if kind != "blob" or blob in seen:
                continue
            seen.add(blob)
            before = len(scan.block)
            scan.check_file(rel, int(size) if size.isdigit() else 0, lambda b=blob: git(folder, "cat-file", "blob", b))
            for i in range(before, len(scan.block)):
                scan.block[i] += f" (in commit {c[:7]})"


class NoCommits(Exception):
    pass


def selftest():
    """Builds fake secrets at run time (never stored in any file of the skill) and checks each mode."""
    for k in [k for k in os.environ if k.startswith("GIT_")]:
        del os.environ[k]  # run from a git hook, these would point the temp repos at the real one
    fake_aws = "AKIA" + "Q7WZ" * 4
    fake_gh = "ghp_" + "a1B2c3D4e5" * 4
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        def write(rel, text):
            p = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w") as f:
                f.write(text)

        def run(*args):
            r = subprocess.run([sys.executable, os.path.abspath(__file__), *args, tmp], capture_output=True, text=True)
            return r.returncode, r.stdout

        def expect(label, got, want_code, must=(), must_not=()):
            nonlocal ok
            code, out = got
            good = code == want_code and all(m in out for m in must) and not any(m in out for m in must_not)
            print(("ok   " if good else "FAIL ") + label)
            if not good:
                ok = False
                print(out)

        write("README.md", "# demo\nSee https://example.com and password = os.environ['PW']\n")
        write("notes.txt", "aws key AKIAIOSFODNN7EXAMPLE from the docs\n")
        expect("clean folder passes", run(), 0, ["RESULT: PASS"])
        write(".env", "API_KEY=" + fake_gh + "\n")
        write("node_modules/x/index.js", "x\n")
        expect("secret file and generated dir are listed to ignore, value never shown", run(), 0,
               ["IGNORE SECRET-FILE .env", "IGNORE GENERATED node_modules/"], [fake_gh])
        write("src/config.py", "KEY = '" + fake_aws + "'\n")
        expect("embedded key blocks, value never shown", run(), 2,
               ["BLOCK EMBEDDED src/config.py:1 aws-access-key-id"], [fake_aws])
        os.remove(os.path.join(tmp, "src/config.py"))
        subprocess.run(["git", "-C", tmp, "init", "-q", "-b", "main"], check=True)
        expect("--git blocks an unignored .env", run("--git"), 2, ["BLOCK SECRET-FILE .env"])
        write(".gitignore", ".env\nnode_modules/\n")
        expect("--git passes once .env is ignored", run("--git"), 0, ["RESULT: PASS"], [".env"])
        write("app.js", "const t = '" + fake_gh + "';\n")
        subprocess.run(["git", "-C", tmp, "add", "app.js"], check=True)
        expect("--staged blocks a staged token", run("--staged"), 2, ["BLOCK EMBEDDED app.js:1 github-token"], [fake_gh])
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
                   GIT_COMMITTER_EMAIL="t@t")
        subprocess.run(["git", "-C", tmp, "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "a"], check=True, env=env)
        write("app.js", "const t = process.env.TOKEN;\n")
        subprocess.run(["git", "-C", tmp, "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false", "commit", "-q", "-am", "b"], check=True, env=env)
        expect("--git passes on today's files", run("--git"), 0, ["RESULT: PASS"])
        expect("--history still finds the token in the old commit", run("--history"), 2,
               ["BLOCK EMBEDDED app.js:1 github-token", "(in commit "], [fake_gh])
    fake_pw = "Tr0ub4dor" + "3xyzQQ"
    for label, line, want in [
        ("env-style name with a prefix", "DB_PASSWORD = '" + fake_pw + "'", True),
        ("unquoted shell export", "export GITHUB_TOKEN=" + fake_pw + "9a", True),
        ("unquoted YAML value", "  password: " + fake_pw + "7", True),
        ("npm token", "//registry.npmjs.org/:_authToken=npm_" + "Ab3" * 12, True),
        ("placeholder URL password", "postgres://app:password@localhost/db", False),
        ("a path, not a secret", "private_key = '~/.ssh/id_ed25519'", False),
        ("a vault entry name", "secret = 'the-name-of-the-secret-in-vault'", False),
        ("a function call", "token = get_token(user)", False),
        ("a word containing token", "tokenizer = 'bert-base-uncased-v2'", False),
        ("a count", "max_tokens = 4096", False),
        ("a value from the environment", "API_KEY = os.environ['API_KEY']", False),
    ]:
        found = bool(line_findings(line))
        good = found == want
        ok = ok and good
        print(("ok   " if good else "FAIL ") + f"pattern: {label} ({'blocks' if want else 'passes'})")

    with tempfile.TemporaryDirectory() as tmp:
        def run_in(folder, *args):
            r = subprocess.run([sys.executable, os.path.abspath(__file__), *args, folder], capture_output=True, text=True)
            return r.returncode, r.stdout

        def check(label, got, want_code, must=()):
            nonlocal ok
            code, out = got
            good = code == want_code and all(m in out for m in must)
            ok = ok and good
            print(("ok   " if good else "FAIL ") + label)
            if not good:
                print(out)

        def mk(rel, text):
            p = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w") as f:
                f.write(text)
            return p

        quiet = dict(capture_output=True, check=True)
        empty = os.path.join(tmp, "empty")
        mk("empty/app.py", "k = '" + fake_aws + "'\n")
        subprocess.run(["git", "-C", empty, "init", "-q"], **quiet)
        check("--history on a repo with no commits refuses rather than passing", run_in(empty, "--history"), 1,
              ["no commits"])
        check("--git on that repo still finds the key", run_in(empty, "--git"), 2, ["BLOCK EMBEDDED app.py:1"])
        site = os.path.join(tmp, "site")
        mk("site/dist/bundle.js", "k = '" + fake_aws + "'\n")
        mk("site/.env.example", "API_KEY=\n")
        subprocess.run(["git", "-C", site, "init", "-q"], **quiet)
        check("--git scans build output and lets .env.example through", run_in(site, "--git"), 2,
              ["BLOCK EMBEDDED dist/bundle.js:1", "GENERATED dist/"])
        check("folder mode scans build output too", run_in(site), 2, ["BLOCK EMBEDDED dist/bundle.js:1"])
        nested = os.path.join(tmp, "nested")
        mk("nested/inner/readme.txt", "hi\n")
        subprocess.run(["git", "-C", os.path.join(nested, "inner"), "init", "-q"], **quiet)
        check("a nested repo blocks", run_in(nested), 2, ["BLOCK NESTED-GIT inner/"])
        locked = mk("locked/notes.txt", "hi\n")
        os.chmod(locked, 0)
        if not os.access(locked, os.R_OK):
            check("an unreadable file blocks instead of crashing", run_in(os.path.dirname(locked)), 2,
                  ["BLOCK UNREADABLE notes.txt"])
        os.chmod(locked, 0o644)
    print("selftest: " + ("all checks behave" if ok else "SOME CHECKS MISBEHAVE"))
    return 0 if ok else 2


def main(argv):
    if argv == ["--selftest"]:
        return selftest()
    mode, max_mb, folder = "folder", 50, None
    args = list(argv)
    while args:
        a = args.pop(0)
        if a in ("--git", "--staged", "--history"):
            mode = a[2:]
        elif a == "--max-mb" and args and args[0].isdigit():
            max_mb = int(args.pop(0))
        elif a.startswith("-") or folder:
            print(__doc__)
            return 1
        else:
            folder = a
    if not folder or not os.path.isdir(folder):
        print(__doc__ if not folder else f"secret_scan: not a folder: {folder}")
        return 1
    folder = os.path.abspath(folder)
    scan = Scan(mode, max_mb)
    try:
        {"folder": scan_folder, "git": scan_git, "staged": scan_staged, "history": scan_history}[mode](folder, scan)
    except NoCommits:
        print(f"secret_scan: {folder} has no commits yet, so there is no history to scan: use --git instead")
        return 1
    except subprocess.CalledProcessError as e:
        print(f"secret_scan: git failed ({' '.join(e.cmd[3:5])}): is {folder} a git repo?")
        return 1
    return scan.report(folder)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
