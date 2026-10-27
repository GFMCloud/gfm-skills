#!/usr/bin/env python3
"""Fill, list and re-run the checks in a handoff file.

Usage:
  check_claims.py fill <handoff.md> [--project DIR] [--allow N[,N...]]
  check_claims.py list <handoff.md>
  check_claims.py run  <handoff.md> [--project DIR] [--allow N[,N...]]
  check_claims.py take <handoff.md> [--by NAME]
  check_claims.py --selftest

The checks are the first fenced block after a "## Checks" heading, written as JSON:
  {"written_at": "...", "checks": [{"claim": "...", "run": "<command>"}], "unchecked": [...]}

fill  runs each check from the project folder (default: the handoff's own folder), writes its real
      output and exit code into "expect" and "exit", and sets written_at to now. A check with
      "match": "contains" keeps its written "expect" and is checked against the output instead.
list  prints every check and what this script would do with it. Runs nothing.
run   re-runs every check, compares with what fill recorded, and lists project files changed
      after written_at.
take  writes <handoff>.taken beside the file, and fails if one is already there.

Only known read-only commands run, joined by | at most. A redirect into a file, ;, &, $,
backticks, a subshell, a known writing command, an option that writes or sends a file (long options
are matched by their abbreviations too), and any argument naming a secret-type file (.env, keys,
~/.ssh, credentials) is refused and never runs. Any other command
"needs a yes": it runs only when its number is passed to --allow, after the user agreed to it.
These guards catch slips, not intent: read a stranger's checks before running them.

Exit codes: 0 every check filled (fill) or matched (run); 1 something to report; 2 bad input.
Standard library only.
"""
import datetime as dt
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

TIMEOUT = 20
MAX_KEEP = 2000
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".mypy_cache", ".pytest_cache"}

READ_ONLY = {"cat", "head", "tail", "wc", "ls", "grep", "egrep", "fgrep", "rg", "shasum", "sha256sum",
             "sha1sum", "md5", "md5sum", "stat", "test", "[", "cut", "tr", "jq", "basename",
             "dirname", "realpath", "readlink", "du", "diff", "cmp", "comm", "pwd", "column"}
SPECIAL = {"git", "gh", "curl", "find", "sort", "uniq"}
WRITERS = {"rm", "rmdir", "mv", "cp", "ln", "chmod", "chown", "chgrp", "touch", "mkdir", "tee", "dd",
           "truncate", "sudo", "su", "doas", "kill", "killall", "pkill", "shutdown", "reboot",
           "launchctl", "crontab", "sh", "bash", "zsh", "fish", "dash", "ksh", "csh", "tcsh", "eval",
           "exec", "source", ".", "xargs", "env", "nohup", "osascript", "open", "install", "rsync",
           "scp", "ssh", "sftp", "ftp", "nc", "ncat", "wget", "brew", "apt", "apt-get", "yum", "dnf",
           "port", "sed", "awk", "perl", "patch", "unzip", "tar", "zip", "split", "shred", "srm",
           "trash", "defaults", "security", "pbcopy", "at", "batch", "watch", "time", "timeout"}

GIT_READ = {"status", "log", "show", "diff", "rev-parse", "rev-list", "ls-files", "ls-tree",
            "ls-remote", "merge-base", "describe", "cat-file", "for-each-ref", "shortlog", "blame",
            "count-objects", "name-rev", "cherry", "show-ref", "grep"}
GIT_BAD_ARGS = ("--output", "--output-directory", "--open-files-in-pager", "--ext-diff", "--upload-pack",
                "--exec", "--receive-pack")
BRANCH_LIST = {"--list", "-l", "--contains", "--no-contains", "--merged", "--no-merged", "--points-at"}
BRANCH_OK = BRANCH_LIST | {"--show-current", "-a", "--all", "-r", "--remotes", "-v", "-vv",
                           "--verbose", "--no-color", "--color", "--column", "--no-column", "-i",
                           "--ignore-case"}
GH_VERBS = {"view", "list", "status", "checks", "diff", "item-list", "field-list"}
CURL_BAD_LONG = {"--output", "--remote-name", "--remote-name-all", "--data", "--data-ascii",
                 "--data-binary", "--data-raw", "--data-urlencode", "--form", "--form-string",
                 "--upload-file", "--request", "--config", "--cookie-jar", "--dump-header", "--user",
                 "--cookie", "--json", "--create-dirs", "--output-dir", "--proxy-user",
                 "--oauth2-bearer", "--netrc", "--netrc-file", "--netrc-optional", "--trace",
                 "--trace-ascii", "--stderr", "--libcurl", "--etag-save", "--hsts", "--alt-svc",
                 "--variable", "--cert", "--key", "--proxy-header", "--aws-sigv4", "--tlsuser",
                 "--tlspassword", "--proxy-cert", "--proxy-key", "--url-query", "--proxy-tlsuser",
                 "--proxy-tlspassword", "--delegation", "--sasl-authzid", "--login-options", "--quote",
                 "--mail-from", "--mail-rcpt", "--mail-auth", "--etag-compare", "--engine", "--proto",
                 "--proto-default", "--proto-redir"}
CURL_BAD_SHORT = set("oOdFTXKcDubnEQ")
CURL_TAKES_VALUE = set("HwAemrxYyzC")

SECRET = re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}|github_pat_\w{20,}|sk-[A-Za-z0-9_-]{20,}|"
                    r"AKIA[0-9A-Z]{16}|xox[abposr]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY|"
                    r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}|"
                    r"(?i:\b\w*(password|passwd|secret|token|api[-_]?key|private[-_]?key)\w*\s*[=:]\s*['\"]?[^\s'\"]{6,})")
CREDENTIAL_HEADER = re.compile(r"authorization|token|api[-_]?key|cookie", re.I)
SECRET_PATH = re.compile(r"(^|[/=~:])\.env(\.[\w-]+)?$|(^|[/=~:])\.(ssh|aws|gnupg|docker|kube|netrc|npmrc|pypirc|"
                         r"git-credentials)(/|$)|\.config/(gh|op|gcloud)(/|$)|id_(rsa|ed25519|ecdsa|dsa)|"
                         r"\.(pem|key|p12|pfx|keychain|keychain-db|kdbx)$|[/=~:]credentials(\.\w+)?$|^credentials\.\w+$|"
                         r"secrets?\.(json|ya?ml|toml|env)$|Keychains|^/proc/|^/dev/fd/", re.I)
DOT_GLOB = re.compile(r"(^|/|~)\.[^/]*[*?\[{]")
PUBLIC_CERT_OPTS = ("--cacert", "--proxy-cacert", "--capath", "--proxy-capath", "--crlfile", "--pinnedpubkey")
SAFE_ENV = re.compile(r"\.env\.(example|sample|template)$", re.I)
JQ_ENV = re.compile(r"(^|[^.\w$])env\b|\$ENV|\$__prog|input_filename")


def long_hits(arg, names):
    """True if arg is one of names or an abbreviation of one: git and GNU tools accept unique prefixes."""
    name = arg.split("=")[0]
    if not name.startswith("--") or len(name) < 3:
        return name in names
    return any(n.startswith("--") and n.startswith(name) for n in names)


# ---------- the guard ----------

def split_pipeline(cmd):
    """Split on unquoted | and reject unsafe shell syntax. Returns (segments, problem)."""
    if "\n" in cmd or "\r" in cmd:
        return None, "more than one line"
    segs, cur, quote, i = [], "", None, 0
    while i < len(cmd):
        c = cmd[i]
        if quote == "'":
            quote = None if c == "'" else quote
            cur += c
        elif quote == '"':
            if c in "$`":
                return None, "$ or backtick inside double quotes"
            if c == "\\" and i + 1 < len(cmd):
                cur += c
                i += 1
                c = cmd[i]
            elif c == '"':
                quote = None
            cur += c
        elif c in "'\"":
            quote = c
            cur += c
        elif c == "\\" and i + 1 < len(cmd):
            cur += c + cmd[i + 1]
            i += 1
        elif c in "$`":
            return None, "$ or backtick"
        elif c in ";&":
            return None, "; or &"
        elif c in "()":
            return None, "subshell"
        elif c == "<":
            return None, "input redirect"
        elif c == ">":
            m = re.match(r">\s*/dev/null(?=\s|\||$)", cmd[i:])
            if not m:
                return None, "redirect into a file"
            if re.search(r"(^|\s)2$", cur):
                cur = cur[:-1]
            i += m.end()
            continue
        elif c == "|":
            if cmd[i + 1:i + 2] == "|":
                return None, "||"
            segs.append(cur)
            cur = ""
        else:
            cur += c
        i += 1
    if quote:
        return None, "unclosed quote"
    segs.append(cur)
    return segs, None


def judge_git(args):
    i = 0
    while i < len(args) and args[i].startswith("-"):
        if args[i] == "-C" and i + 1 < len(args):
            i += 2
        elif args[i] in ("--no-pager", "-P"):
            i += 1
        else:
            return "refused", f"git option {args[i]}"
    if i >= len(args):
        return "refused", "git with no subcommand"
    sub, rest = args[i], args[i + 1:]
    for a in rest:
        if long_hits(a, GIT_BAD_ARGS) or (a.startswith("-O") and not a.startswith("--")) or (sub == "ls-remote" and a == "-u"):
            return "refused", f"git {sub} {a}"
    if sub in GIT_READ:
        return "runs", ""
    if sub == "branch":
        flags = [a for a in rest if a.startswith("-")]
        positional = [a for a in rest if not a.startswith("-")]
        bad = [f for f in flags if f.split("=")[0] not in BRANCH_OK and not f.startswith(("--format=", "--sort="))]
        if bad:
            return "refused", f"git branch {bad[0]}"
        if positional and not any(f in BRANCH_LIST for f in flags):
            return "refused", "git branch with a name creates a branch"
        return "runs", ""
    if sub == "tag":
        listing = {"-l", "--list", "--contains", "--no-contains", "--points-at", "--merged", "--no-merged"}
        flags = [a for a in rest if a.startswith("-")]
        if not rest or any(f in listing for f in flags) and not any(f in ("-d", "--delete", "-a", "-s", "-f", "-m", "-F") for f in flags):
            return "runs", ""
        return "refused", "git tag that may create or delete a tag"
    if sub == "remote":
        if rest in ([], ["-v"], ["--verbose"]) or (rest and rest[0] in ("get-url", "show")):
            return "runs", ""
        return "refused", "git remote that changes remotes"
    if sub == "config":
        reads = {"--get", "--get-all", "--get-regexp", "--list", "-l", "get", "list"}
        writes = {"--add", "--unset", "--unset-all", "--replace-all", "--edit", "-e", "--rename-section",
                  "--remove-section", "set", "unset", "edit", "rename-section", "remove-section"}
        if any(a in reads for a in rest) and not any(a in writes for a in rest):
            return "runs", ""
        return "refused", "git config that may write"
    if sub in ("worktree", "stash", "notes") and rest[:1] in (["list"], ["show"]):
        return "runs", ""
    return "refused", f"git {sub} is not a read"


def judge_gh(args):
    rest = list(args)
    if rest[:1] in (["-R"], ["--repo"]):
        rest = rest[2:]
    if any(a in ("--web", "-w") for a in rest):
        return "refused", "gh --web"
    if any(a == "--show-token" for a in rest) or (rest[:2] == ["auth", "status"] and "-t" in rest):
        return "refused", "gh printing a token"
    if rest[:2] == ["auth", "status"] or rest[:1] in (["search"], ["status"]):
        return "runs", ""
    if rest[:1] == ["api"]:
        for j, a in enumerate(rest):
            name = a.split("=")[0]
            if name in ("-f", "-F", "--field", "--raw-field", "--input"):
                return "refused", f"gh api {name} sends data"
            if name in ("-X", "--method"):
                val = a.split("=", 1)[1] if "=" in a else (rest[j + 1] if j + 1 < len(rest) else "")
                if val.upper() not in ("GET", "HEAD"):
                    return "refused", "gh api with a writing method"
        return "runs", ""
    if len(rest) >= 2 and rest[1] in GH_VERBS:
        return "runs", ""
    return "refused", "gh command that is not view, list, status, checks or diff"


def judge_curl(args):
    for a in args:
        if a.startswith("@") or "=@" in a or (a.startswith("-") and not a.startswith("--") and "@" in a):
            return "refused", "curl reading a local file with @"
        m = re.match(r"^([A-Za-z][\w+.-]*)://([^/]*)", a)
        if m and m.group(1).lower() not in ("http", "https"):
            return "refused", f"curl with a {m.group(1)} address; only http and https reads run"
        if m and "@" in m.group(2):
            return "refused", "a credential written into an address"
    j = 0
    while j < len(args):
        a = args[j]
        nxt = args[j + 1] if j + 1 < len(args) else ""
        if a.startswith("--expand"):
            return "refused", "curl --expand-* can put a file's contents in the request"
        if a.startswith("--"):
            name = a.split("=")[0]
            val = a.split("=", 1)[1] if "=" in a else nxt
            if name == "--output" and val == "/dev/null":
                pass
            elif name == "--request" and val.upper() in ("GET", "HEAD"):
                pass
            elif name == "--dump-header" and val == "-":
                pass
            elif name in CURL_BAD_LONG:
                return "refused", f"curl {name}"
            elif name == "--header" and CREDENTIAL_HEADER.search(val):
                return "refused", "curl header carrying a credential"
        elif a.startswith("-") and len(a) > 1:
            letters = a[1:]
            if letters in ("o", "X", "D"):
                ok = {"o": nxt == "/dev/null", "X": nxt.upper() in ("GET", "HEAD"), "D": nxt == "-"}[letters]
                if not ok:
                    return "refused", f"curl -{letters} {nxt}"
                j += 1
            elif CURL_BAD_SHORT & set(letters):
                return "refused", f"curl {a} (write each flag on its own: -s -o /dev/null)"
            elif letters[-1:] in CURL_TAKES_VALUE:
                if letters[-1] == "H" and CREDENTIAL_HEADER.search(nxt):
                    return "refused", "curl header carrying a credential"
                j += 1
        j += 1
    return "runs", ""


def judge_segment(seg):
    try:
        toks = shlex.split(seg)
    except ValueError as e:
        return "refused", f"cannot parse: {e}"
    if not toks:
        return "refused", "empty command"
    if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", toks[0]):
        return "refused", "variable assignment"
    prog, args = toks[0], toks[1:]
    for n, a in enumerate(toks):
        bare = re.sub(r"/+", "/", a)
        public = toks[n - 1] in PUBLIC_CERT_OPTS if n else False
        if any(a.startswith(o + "=") for o in PUBLIC_CERT_OPTS):
            public = True
        if (SECRET_PATH.search(a) or SECRET_PATH.search(bare)) and not SAFE_ENV.search(a) and not public:
            return "refused", f"names a secret-type file ({a}); its contents would be saved in the handoff"
        unquoted = f"'{a}'" not in seg and f'"{a}"' not in seg
        if DOT_GLOB.search(a) and unquoted and not a.startswith("-") and n:
            return "refused", f"a wildcard that can match hidden files ({a}); name the file instead"
    if "/" in prog:
        return "needs a yes", f"runs a program by path ({prog})"
    if prog in WRITERS:
        return "refused", f"{prog} can write or run other commands"
    if prog in READ_ONLY:
        if prog == "rg" and any(a.startswith(("--pre", "--hostname-bin")) for a in args):
            return "refused", "rg --pre and --hostname-bin run a program"
        if prog == "jq" and any(JQ_ENV.search(a) for a in args):
            return "refused", "jq reading environment variables, which can hold secrets"
        return "runs", ""
    if prog == "git":
        return judge_git(args)
    if prog == "gh":
        return judge_gh(args)
    if prog == "curl":
        return judge_curl(args)
    if prog == "find":
        bad = {"-delete", "-exec", "-execdir", "-ok", "-okdir", "-fprint", "-fprint0", "-fprintf", "-fls"}
        hit = next((a for a in args if a in bad), None)
        return ("refused", f"find {hit}") if hit else ("runs", "")
    if prog == "sort":
        if any(long_hits(a, ("--output", "--compress-program")) or (a.startswith("-") and not a.startswith("--") and "o" in a) for a in args):
            return "refused", "sort -o writes a file; --compress-program runs one"
        return "runs", ""
    if prog == "uniq":
        files, skip = [], False
        for a in args:
            if skip:
                skip = False
            elif a in ("-f", "-s", "-w"):
                skip = True
            elif not a.startswith("-"):
                files.append(a)
        if len(files) > 1:
            return "refused", "uniq with two files writes the second"
        return "runs", ""
    return "needs a yes", f"{prog} is not a known read-only command"


def judge(cmd):
    """Return (verdict, reason): verdict is 'runs', 'needs a yes' or 'refused'."""
    if not isinstance(cmd, str) or not cmd.strip():
        return "refused", "no command"
    segs, problem = split_pipeline(cmd)
    if problem:
        return "refused", problem
    worst = ("runs", "")
    for seg in segs:
        v, why = judge_segment(seg)
        if v == "refused":
            return v, why
        if v == "needs a yes":
            worst = (v, why)
    return worst


# ---------- the file ----------

def find_block(text):
    lines = text.split("\n")
    start = None
    for n, line in enumerate(lines):
        if re.match(r"^#{2,4}\s+Checks\s*$", line.strip()):
            start = n
            break
    if start is None:
        return None
    for n in range(start + 1, len(lines)):
        m = re.match(r"^\s*(`{3,}|~{3,})", lines[n])
        if m:
            fence = m.group(1)
            for k in range(n + 1, len(lines)):
                if lines[k].strip().startswith(fence):
                    return lines, n + 1, k
            return None
        if lines[n].startswith("#"):
            return None
    return None


def load(path):
    try:
        text = open(path, encoding="utf-8").read()
    except (OSError, UnicodeDecodeError) as e:
        print(f"cannot read {path} as UTF-8 text: {e}")
        sys.exit(2)
    found = find_block(text)
    if not found:
        print("NO CHECKS BLOCK: no ```json block under a '## Checks' heading. Nothing typed to re-run;"
              " check the file's main facts by hand and say so. An empty table proves nothing.")
        sys.exit(2)
    lines, a, b = found
    try:
        data = json.loads("\n".join(lines[a:b]))
    except json.JSONDecodeError as e:
        print(f"BAD CHECKS BLOCK: not valid JSON ({e}). Fix the block; don't guess what it meant.")
        sys.exit(2)
    if not isinstance(data, dict) or not isinstance(data.get("checks", []), list):
        print('BAD CHECKS BLOCK: expected an object with a "checks" list.')
        sys.exit(2)
    for c in data.get("checks", []):
        if not isinstance(c, dict):
            print("BAD CHECKS BLOCK: every check must be an object with claim and run.")
            sys.exit(2)
    return lines, a, b, data


def save(path, lines, a, b, data):
    body = json.dumps(data, indent=2, ensure_ascii=False).split("\n")
    out = lines[:a] + body + lines[b:]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))


def execute(cmd, project):
    try:
        p = subprocess.run(["bash", "-o", "pipefail", "-c", cmd], cwd=project, capture_output=True,
                           timeout=TIMEOUT, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return None, None, f"timed out after {TIMEOUT}s"
    out = p.stdout.decode("utf-8", errors="replace").rstrip()
    err = p.stderr.decode("utf-8", errors="replace").strip()
    if p.returncode in (126, 127) or "command not found" in err:
        return None, None, f"could not run (exit {p.returncode}): {err[:200]}"
    return out, p.returncode, None


def allowed(arg):
    if not arg:
        return set()
    try:
        return {int(x) for x in arg.split(",") if x.strip()}
    except ValueError:
        sys.exit("--allow takes check numbers, for example --allow 3 or --allow 2,5")


def flat(s):
    """Compare ignoring runs of spaces: wc and ls pad differently on macOS and Linux."""
    return " ".join(str(s).split())


def short(s, n=80):
    s = str(s).replace("\n", " / ").replace("|", "\\|")
    return s if len(s) <= n else s[: n - 3] + "..."


def now_iso():
    return dt.datetime.now().astimezone().replace(microsecond=0).isoformat()


def parse_time(s):
    try:
        t = dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.astimezone()


# ---------- commands ----------

def cmd_list(path):
    _, _, _, data = load(path)
    checks = data.get("checks", [])
    print(f"{len(checks)} checks in {path}. Nothing has been run.")
    for n, c in enumerate(checks, 1):
        v, why = judge(c.get("run"))
        print(f"{n}. [{v}{': ' + why if why else ''}] {c.get('claim', '(no claim)')}\n   $ {c.get('run')}")
    for u in data.get("unchecked", []):
        if isinstance(u, dict):
            print(f"not checked by design ({u.get('kind', 'note')}): {u.get('text', '')}")
    return 0


def cmd_fill(path, project, allow):
    lines, a, b, data = load(path)
    checks = data.get("checks", [])
    problems, filled = [], 0
    for n, c in enumerate(checks, 1):
        v, why = judge(c.get("run"))
        if v == "refused":
            problems.append(f"{n}. REFUSED ({why}): {c.get('run')}. Replace it with a read-only check.")
            continue
        if v == "needs a yes" and n not in allow:
            problems.append(f"{n}. NEEDS A YES ({why}): {c.get('run')}. Read it; if it only reads, rerun with --allow {n}."
                            " The resuming session will need the user's yes for it too.")
            continue
        out, code, err = execute(c["run"], project)
        if err:
            problems.append(f"{n}. ERROR: {err}")
            continue
        if SECRET.search(out):
            problems.append(f"{n}. OUTPUT LOOKS LIKE A SECRET: not recorded. Use a check that doesn't print it (a hash, a count).")
            continue
        if c.get("match") == "contains":
            if not str(c.get("expect", "")).strip() or flat(c.get("expect", "")) not in flat(out):
                problems.append(f"{n}. CONTAINS CHECK FAILS NOW: {short(c.get('expect'))!r} is not in the output {short(out)!r}.")
                continue
        else:
            if len(out) > MAX_KEEP:
                problems.append(f"{n}. OUTPUT TOO LONG ({len(out)} chars): pick a narrower command (| wc -l, | head -1, shasum).")
                continue
            c["expect"] = out
            if len(out) > 300:
                print(f"note: check {n} recorded {len(out)} characters; a shorter output is easier to compare.")
        c["exit"] = code
        filled += 1
    data["written_at"] = now_iso()
    data["checks"] = [dict(sorted(c.items(), key=lambda kv: ["claim", "run", "expect", "exit", "match"].index(kv[0])
                                  if kv[0] in ("claim", "run", "expect", "exit", "match") else 9)) for c in checks]
    save(path, lines, a, b, data)
    print(f"{filled} of {len(checks)} checks filled from real output in {project}; written_at {data['written_at']}.")
    if not checks:
        print("0 checks: nothing could be re-checked by command, so everything rests on the unchecked list. Say so in the reply.")
    for p in problems:
        print(p)
    return 1 if problems else 0


def stale_files(project, since, skip):
    hits = []
    for root, dirs, files in os.walk(project):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            p = os.path.join(root, f)
            if os.path.abspath(p) in skip:
                continue
            try:
                if os.path.getmtime(p) > since.timestamp() + 1:
                    hits.append(os.path.relpath(p, project))
            except OSError:
                pass
    return sorted(hits)


def cmd_run(path, project, allow):
    _, _, _, data = load(path)
    checks = data.get("checks", [])
    rows, bad = [], 0
    for n, c in enumerate(checks, 1):
        cmd = c.get("run")
        v, why = judge(cmd)
        if v == "refused":
            rows.append((n, c, "(not run)", f"REFUSED: {why}"))
            bad += 1
            continue
        if v == "needs a yes" and n not in allow:
            rows.append((n, c, "(not run)", f"NEEDS A YES: {why}"))
            bad += 1
            continue
        if "expect" not in c:
            rows.append((n, c, "(not run)", "NO EXPECT: the writer never filled it"))
            bad += 1
            continue
        out, code, err = execute(cmd, project)
        if err:
            rows.append((n, c, "(error)", f"ERROR: {err}"))
            bad += 1
            continue
        shown = "[hidden: looks like a secret]" if SECRET.search(out) else out
        exp = str(c.get("expect"))
        same = (flat(exp) in flat(out)) if c.get("match") == "contains" else (flat(out) == flat(exp))
        if "exit" in c and c["exit"] != code:
            same = False
        if same:
            rows.append((n, c, shown, "match"))
        else:
            detail = f"MISMATCH: expected {short(exp, 60)!r}" + (f" exit {c['exit']}, got exit {code}" if "exit" in c and c["exit"] != code else "")
            rows.append((n, c, shown, detail))
            bad += 1
    since = parse_time(data.get("written_at"))
    print(f"Handoff: {path}\nProject: {project}\nWritten at: {data.get('written_at') or '(missing)'}")
    if since is None:
        print("Changed since: cannot tell (written_at missing or unreadable).")
    else:
        skip = {os.path.abspath(path), os.path.abspath(path) + ".taken"}
        changed = stale_files(project, since, skip)
        if changed:
            more = f" and {len(changed) - 20} more" if len(changed) > 20 else ""
            print(f"Changed since: {len(changed)} file(s): {', '.join(changed[:20])}{more}")
        else:
            print("Changed since: no files in the project changed after written_at.")
    print("\n| # | Claim | Command | Now | Result |\n| ---: | :--- | :--- | :--- | :--- |")
    for n, c, shown, result in rows:
        print(f"| {n} | {short(c.get('claim', ''))} | `{short(c.get('run', ''), 60)}` | {short(shown, 60)} | {result} |")
    unchecked = [u for u in data.get("unchecked", []) if isinstance(u, dict)]
    if unchecked:
        print("\nNot checked by design:")
        for u in unchecked:
            print(f"- ({u.get('kind', 'note')}) {u.get('text', '')}")
    print(f"\n{len(checks) - bad} of {len(checks)} checks match.")
    if not checks:
        print("The file has no checks: nothing here was re-checked.")
    return 1 if bad else 0


def cmd_take(path, by):
    if not os.path.isfile(path):
        sys.exit(f"no such handoff: {path}")
    side = path + ".taken"
    try:
        with open(side, "x", encoding="utf-8") as f:
            f.write(f"taken {now_iso()} by {by}\n")
    except FileExistsError:
        print(f"ALREADY TAKEN: {side} says: {open(side, encoding='utf-8').read().strip()}")
        print("Another session may be on this work. Ask the user before going on.")
        return 1
    print(f"took {path} ({side})")
    return 0


# ---------- self test ----------

def selftest():
    cases = {
        "runs": ["git branch --show-current", "git -C sub rev-parse --short HEAD", "git status --porcelain | wc -l",
                 "shasum -a 256 docs/a.md", "grep -c 'x$' f.txt", "ls dir 2>/dev/null", "git branch --list 'feat*'",
                 "curl -s -o /dev/null -w '%{http_code}' https://example.com", "gh pr view 12 --json state -q .state",
                 "git config --get user.name", "find . -name '*.md'", "git tag", "gh api repos/o/r/pulls",
                 "jq .version package.json", "sort -n f | uniq -c", "gh search repos handoff", "uniq -f 1 a",
                 "cat .env.example", "git log --oneline -5", "grep -c credentials README.md",
                 "ls docs/credentials-policy.md", "curl -s --cacert ca.pem https://example.com", "ls *.md",
                 "jq -r '.[]' x.json", "find . -name '.git*'", "gh pr view 1 -t '{{.body}}'"],
        "needs a yes": ["pytest -q", "python3 -c 'print(1)'", "./check.sh", "npm test | tail -1"],
        "refused": ["rm -rf build", "git push", "cat a > b", "echo $HOME", "ls; rm x", "ls && rm x", "cat `x`",
                    "git branch new-thing", "git branch -D main", "git -c core.pager=x log", "curl -d a=b https://x",
                    "curl -sSo out https://x", "curl -X POST https://x", "find . -delete", "find . -exec rm {} ;",
                    "sort -o out f", "gh pr merge 3", "gh api -X POST repos/o/r/issues", "A=1 ls", "tee f",
                    "git diff --output=f", "xargs rm", "ls || true", "(cd x; ls)", "sh -c ls", "git config user.name x",
                    "uniq a b", "curl -H 'Authorization: Bearer x' https://x", "sed -i s/a/b/ f", "git ls-remote -u x y",
                    "cat \"$(whoami)\"", "ls\nrm x", "git tag -d v1", "git remote add o u", "cat <f",
                    "sort --out x f", "sort --o x f", "sort --compress-program=sh f", "git diff --outp=x",
                    "git grep -Ovim x", "jq -n env.HOME", "jq -n '$ENV'", "cat .env", "grep x ~/.ssh/id_rsa",
                    "cat ~/.aws/credentials", "curl -s --variable v@/etc/hosts --expand-url https://x/{{v}}",
                    "curl -w @/etc/hosts https://x", "curl -H @/etc/hosts https://x", "curl -E cert.pem https://x",
                    "git ls-remote --up=x origin", "cat .e*", "head -2 .env*", "ls -la ~/.ss?", "git show HEAD:.env",
                    "git cat-file -p HEAD:.env", "cat /proc/self/environ", "grep -a . /proc/1/environ",
                    "curl -Q 'DELE x' ftp://h/", "curl --mail-rcpt a@b smtp://h", "curl -x http://u:p@proxy https://x",
                    "gh auth status --show-token", "rg --hostname-bin x y", "cat config/credentials.json",
                    "cat .{env,x} 2>/dev/null", "cat //proc/self/environ", "curl -s --proto-default ftp host/",
                    "gh auth status -t", "ls -d .*/", "cat \".e\"*", "cat '.e'*"],
    }
    fails = 0
    for want, cmds in cases.items():
        for c in cmds:
            got, why = judge(c)
            if got != want:
                fails += 1
                print(f"FAIL guard: {c!r} -> {got} ({why}), want {want}")
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "a.txt"), "w") as f:
        f.write("one\ntwo\n")
    h = os.path.join(d, "handoff.md")
    block = {"written_at": "", "checks": [{"claim": "a has 2 lines", "run": "wc -l a.txt"},
                                          {"claim": "tests", "run": "pytest -q"},
                                          {"claim": "bad", "run": "rm a.txt"}], "unchecked": []}
    with open(h, "w") as f:
        f.write("# Handoff\n\n## Checks\n\n```json\n" + json.dumps(block) + "\n```\n")
    devnull = open(os.devnull, "w")
    real = sys.stdout
    sys.stdout = devnull
    try:
        r_fill = cmd_fill(h, d, set())
        data = load(h)[3]
        r_run_ok = None
        data["checks"] = data["checks"][:1]
        lines, a, b, _ = load(h)
        save(h, lines, a, b, data)
        r_run_ok = cmd_run(h, d, set())
        with open(os.path.join(d, "a.txt"), "a") as f:
            f.write("three\n")
        r_run_bad = cmd_run(h, d, set())
        r_take1, r_take2 = cmd_take(h, "test"), cmd_take(h, "test")
    finally:
        sys.stdout = real
    expect = [("fill reports the needs-a-yes and refused checks", r_fill, 1),
              ("fill recorded real output", data["checks"][0].get("expect", "").split()[0] if data["checks"][0].get("expect") else "", "2"),
              ("refused check left the file alone", os.path.exists(os.path.join(d, "a.txt")), True),
              ("run matches an unchanged project", r_run_ok, 0),
              ("run catches a changed file", r_run_bad, 1),
              ("first take works", r_take1, 0), ("second take is refused", r_take2, 1)]
    for name, got, want in expect:
        if got != want:
            fails += 1
            print(f"FAIL {name}: got {got!r}, want {want!r}")
    total = sum(len(v) for v in cases.values()) + len(expect)
    shutil.rmtree(d, ignore_errors=True)
    print(f"selftest: {total - fails} of {total} passed")
    return 1 if fails else 0


def main(argv):
    if argv[:1] == ["--selftest"]:
        return selftest()
    if len(argv) < 2 or argv[0] not in ("fill", "list", "run", "take"):
        print(__doc__)
        return 2
    mode, path, rest = argv[0], argv[1], argv[2:]
    opts = {}
    j = 0
    while j < len(rest):
        if rest[j] in ("--project", "--allow", "--by") and j + 1 < len(rest):
            opts[rest[j]] = rest[j + 1]
            j += 2
        else:
            print(f"unknown argument: {rest[j]}\n{__doc__}")
            return 2
    project = os.path.abspath(opts.get("--project") or os.path.dirname(os.path.abspath(path)))
    if mode != "take" and not os.path.isdir(project):
        print(f"no such project folder: {project}")
        return 2
    if mode == "list":
        return cmd_list(path)
    if mode == "fill":
        return cmd_fill(path, project, allowed(opts.get("--allow")))
    if mode == "run":
        return cmd_run(path, project, allowed(opts.get("--allow")))
    return cmd_take(path, opts.get("--by", "a session"))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
