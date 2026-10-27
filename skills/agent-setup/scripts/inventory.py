#!/usr/bin/env python3
"""List what Claude Code and Codex load for one project, and flag setup problems.

Read only: it never writes, and never prints a setting's value, an env entry or an
allow rule (they can hold secrets), only counts and the flagged broad rules.

Usage:
  python3 inventory.py [--home DIR] [--project DIR]
  python3 inventory.py --selftest

--home points at a stand-in home folder (for a trial or a test); it replaces ~ for both
agents and ignores CODEX_HOME and CLAUDE_CONFIG_DIR. Default: the real home, with
CODEX_HOME (in place of ~/.codex) and CLAUDE_CONFIG_DIR (in place of ~/.claude) used when
set. --project defaults to the current folder.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ImportError:  # pragma: no cover
    tomllib = None

DESC_WARN = 300
DESC_FAIL = 1024
CODEX_LIST_BUDGET = 8000  # OpenAI Codex skills docs, read 2026-10-25
CODEX_DOC_MAX = 32 * 1024  # project_doc_max_bytes default, Codex AGENTS.md docs, read 2026-10-26
OVERLAP = 0.35
STOP = set("""about after also and any are because been before being both but can each
every for from have into its just like make more most must need only other over same
should some such than that the their them then there these they this those through use
used uses using very want what when where which while who will with without would your
skill skills user users asked asks when does not""".split())

flags = []
HOME_SHOWN = [None]


def short(path):
    """Show paths under the home in use as ~/..., so stand-in homes read like real ones."""
    s = str(path)
    h = HOME_SHOWN[0]
    if h and (s == h or s.startswith(h + os.sep)):
        return "~" + s[len(h):]
    return s


def flag(level, where, msg):
    flags.append((level, short(where), msg))


def git_root(path):
    try:
        out = subprocess.run(["git", "-C", str(path), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    return Path(out.stdout.strip()).resolve()


def chain(project):
    """Folders from the repo root down to the project (just the project outside git)."""
    root = git_root(project)
    project = project.resolve()
    if root is None or root not in [project, *project.parents]:
        return [project]
    dirs = [project]
    while dirs[-1] != root:
        dirs.append(dirs[-1].parent)
    return list(reversed(dirs))


def frontmatter(text):
    text = text.lstrip("\ufeff")
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end < 0:
        return None
    block = text[3:end]
    data, key = {}, None
    for line in block.splitlines():
        m = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val in (">", ">-", "|", "|-", ">+", "|+"):
                val = ""
            data[key] = val.strip("'\"")
        elif key and line.startswith((" ", "\t")):
            data[key] = (data[key] + " " + line.strip()).strip()
    return data


def toml_keys(text):
    """Read the few top-level keys this script needs when tomllib is missing (Python < 3.11)."""
    data = {}
    for line in text.splitlines():
        if line.lstrip().startswith("["):
            break  # top-level keys only
        m = re.match(r'^\s*(approval_policy|sandbox_mode|project_doc_max_bytes)\s*=\s*"?([^"#\s]+)"?', line)
        if m:
            data[m.group(1)] = int(m.group(2)) if m.group(2).isdigit() else m.group(2)
    return data


def words(text):
    return {w for w in re.findall(r"[a-z]{4,}", text.lower()) if w not in STOP}


def read_text(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def show_instructions(label, files):
    print(f"  {label}:")
    if not files:
        print("    (none)")
    for f in files:
        size = f.stat().st_size if f.exists() else 0
        print(f"    {short(f)}  ({size} bytes)")


def claude_instructions(claude_home, dirs):
    """Files Claude Code loads, and whether it reads AGENTS.md directly (no CLAUDE.md at or above)."""
    files = []
    g = claude_home / "CLAUDE.md"
    if g.is_file():
        files.append(g)
    if (claude_home / "rules").is_dir():
        files.extend(sorted((claude_home / "rules").glob("*.md")))
    project_claude = False
    for d in dirs:
        for name in ("CLAUDE.md", ".claude/CLAUDE.md", "CLAUDE.local.md"):
            p = d / name
            if p.is_file():
                files.append(p)
                project_claude = True
        rules = d / ".claude" / "rules"
        if rules.is_dir():
            files.extend(sorted(rules.glob("*.md")))
    agents_direct = False
    if not project_claude:
        for d in dirs:
            for name in ("AGENTS.md", ".claude/AGENTS.md"):
                p = d / name
                if p.is_file():
                    files.append(p)
                    agents_direct = True
    for f in list(files):
        text = read_text(f) or ""
        for m in re.finditer(r"(?:^|\s)@((?:~|\.{1,2})?/?[\w.~/-]+\.md)\b", text):
            ref = m.group(1)
            target = Path(os.path.expanduser(ref)) if ref.startswith("~") else (f.parent / ref)
            if target.is_file():
                if target not in files:
                    files.append(target)
            else:
                flag("WARN", f, f"imports @{ref}, which does not exist")
    return files, agents_direct


def codex_instructions(codex_home, dirs):
    files = []
    for name in ("AGENTS.override.md", "AGENTS.md"):
        p = codex_home / name
        if p.is_file() and p.stat().st_size > 0:
            files.append(p)
            break
    for d in dirs:
        for name in ("AGENTS.override.md", "AGENTS.md"):
            p = d / name
            if p.is_file() and p.stat().st_size > 0:
                files.append(p)
                break
    return files


def skill_dirs(home, claude_home, codex_home, dirs):
    claude = [("user", claude_home / "skills")]
    codex = [("user", home / ".agents" / "skills")]
    if (codex_home / "skills").is_dir():
        codex.append(("codex-home (older location; check your Codex version)", codex_home / "skills"))
    for d in reversed(dirs):
        claude.append(("project", d / ".claude" / "skills"))
        codex.append(("project", d / ".agents" / "skills"))
    return {"Claude Code": claude, "Codex": codex}


def scan_skills(agent, places):
    found = {}
    total = 0
    for scope, base in places:
        if not base.is_dir():
            continue
        print(f"  {agent} {scope}: {short(base)}")
        for entry in sorted(base.iterdir()):
            if entry.name.startswith("."):
                continue
            if entry.is_symlink() and not entry.exists():
                flag("FAIL", entry, f"broken link to {os.readlink(entry)}")
                print(f"    {entry.name}  BROKEN LINK")
                continue
            if not entry.is_dir():
                continue
            sk = entry / "SKILL.md"
            if not sk.exists():
                flag("WARN", entry, "folder has no SKILL.md, so it is not a skill")
                continue
            text = read_text(sk) if sk.is_file() else None
            if text is None:
                flag("FAIL", sk, "SKILL.md could not be read (not a file, or no permission)")
                continue
            fm = frontmatter(text)
            if not fm or "name" not in fm or "description" not in fm:
                flag("FAIL", sk, "frontmatter missing or lacks name/description")
                continue
            name, desc = fm["name"], fm["description"]
            total += len(desc)
            link = f" -> {os.readlink(entry)}" if entry.is_symlink() else ""
            print(f"    {name}  ({len(desc)} chars){link}")
            if name != entry.name:
                flag("FAIL", sk, f"name '{name}' does not match folder '{entry.name}'")
            if len(desc) > DESC_FAIL:
                flag("FAIL", sk, f"description is {len(desc)} characters (spec limit {DESC_FAIL})")
            elif len(desc) > DESC_WARN:
                flag("WARN", sk, f"description is {len(desc)} characters (aim for about 250)")
            if "not for" not in desc.lower():
                flag("NOTE", sk, "description has no 'Not for' line naming its neighbours")
            if name in found:
                flag("WARN", sk, f"{agent}: name '{name}' also at {found[name]['path']}; one hides the other or both are listed")
            else:
                found[name] = {"path": sk, "desc": desc}
    return found, total


def overlaps(skills):
    items = sorted(skills.items())
    for i, (a, da) in enumerate(items):
        for b, db in items[i + 1:]:
            wa, wb = words(da["desc"]), words(db["desc"])
            if not wa or not wb:
                continue
            j = len(wa & wb) / len(wa | wb)
            if j >= OVERLAP:
                flag("WARN", f"{a} / {b}", f"descriptions overlap ({j:.2f}): they may compete for the same requests")


def claude_settings(claude_home, dirs):
    files = [claude_home / "settings.json"]
    for d in dirs:
        files += [d / ".claude" / "settings.json", d / ".claude" / "settings.local.json"]
    for f in files:
        if not f.is_file():
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            flag("FAIL", f, f"not valid JSON ({type(e).__name__}); Claude Code skips it")
            print(f"  {short(f)}: INVALID JSON")
            continue
        if not isinstance(data, dict):
            flag("FAIL", f, "top level is not a JSON object; Claude Code can't use it")
            print(f"  {short(f)}: not a JSON object")
            continue
        perms = data.get("permissions") or {}
        if not isinstance(perms, dict):
            flag("FAIL", f, "permissions is not an object")
            perms = {}
        lists = {}
        for k in ("allow", "ask", "deny"):
            v = perms.get(k) or []
            if not isinstance(v, list):
                flag("FAIL", f, f"permissions.{k} is not a list")
                v = []
            bad = [r for r in v if not isinstance(r, str)]
            if bad:
                flag("FAIL", f, f"permissions.{k} has {len(bad)} entries that are not strings")
            lists[k] = [r for r in v if isinstance(r, str)]
        counts = {k: len(v) for k, v in lists.items()}
        hk = data.get("hooks") or {}
        if not isinstance(hk, dict):
            flag("FAIL", f, "hooks is not an object")
            hk = {}
        hooks = sorted(str(k) for k in hk.keys())
        print(f"  {short(f)}: allow {counts['allow']}, ask {counts['ask']}, deny {counts['deny']}; hooks: {', '.join(hooks) or 'none'}")
        if perms.get("defaultMode") == "bypassPermissions":
            flag("WARN", f, "defaultMode is bypassPermissions: nothing asks before running")
        for rule in lists["allow"]:
            if rule in ("Bash", "Bash(*)", "Bash(**)", "Write", "Edit", "Write(*)", "Edit(*)") or rule.startswith("Bash(sudo"):
                flag("WARN", f, f"broad allow rule {rule}")


def codex_config(codex_home, dirs):
    files = [codex_home / "config.toml"] + [d / ".codex" / "config.toml" for d in dirs]
    for f in files:
        if not f.is_file():
            continue
        text = read_text(f) or ""
        if tomllib is None:
            data = toml_keys(text)
            note = " (read without a full TOML parse: Python 3.11+ checks the syntax)"
        else:
            try:
                data = tomllib.loads(text)
            except ValueError as e:
                flag("FAIL", f, f"not valid TOML ({type(e).__name__})")
                print(f"  {short(f)}: INVALID TOML")
                continue
            note = ""
        ap, sm = data.get("approval_policy"), data.get("sandbox_mode")
        if isinstance(ap, dict):
            ap = "granular"
        mx = data.get("project_doc_max_bytes")
        print(f"  {short(f)}: approval_policy={ap or 'default'}, sandbox_mode={sm or 'default'}"
              + (f", project_doc_max_bytes={mx}" if mx else "") + note)
        if sm == "danger-full-access":
            flag("WARN", f, "sandbox_mode is danger-full-access: no sandbox")
        if ap == "never" and sm == "danger-full-access":
            flag("WARN", f, "approval_policy never with no sandbox: nothing is checked before it runs")
    for base in [codex_home] + [d / ".codex" for d in dirs]:
        rules = sorted((base / "rules").glob("*.rules")) if (base / "rules").is_dir() else []
        for r in rules:
            print(f"  rules file: {short(r)}")
        if (base / "hooks.json").is_file():
            print(f"  hooks file: {short(base / 'hooks.json')}")


def run(home_arg, project):
    note = ""
    if home_arg:
        home = Path(home_arg).resolve()
        claude_home = home / ".claude"
        codex_home = home / ".codex"
    else:
        home = Path.home()
        codex_home = Path(os.environ.get("CODEX_HOME") or home / ".codex")
        claude_home = Path(os.environ.get("CLAUDE_CONFIG_DIR") or home / ".claude")
        for var in ("CLAUDE_CONFIG_DIR", "CODEX_HOME"):
            if os.environ.get(var):
                note += f"\n{var}={os.environ[var]} is set and used in place of the default folder"
    project = Path(project).resolve()
    dirs = chain(project)
    HOME_SHOWN[0] = str(home.resolve())
    print(f"Home: {home}  (shown as ~ below){note}")
    print(f"Project: {project}  (folders checked: {dirs[0]} down to {dirs[-1]})")

    print("\nInstructions that load from here")
    cl, agents_direct = claude_instructions(claude_home, dirs)
    show_instructions("Claude Code" + (" (reads AGENTS.md directly: no CLAUDE.md here or above; needs v2.1.277 or later)" if agents_direct else ""), cl)
    cx = codex_instructions(codex_home, dirs)
    show_instructions("Codex", cx)
    size = sum(f.stat().st_size for f in cx if f.parent != codex_home)
    if size > CODEX_DOC_MAX:
        flag("WARN", project, f"project AGENTS.md files total {size} bytes; Codex stops adding them at {CODEX_DOC_MAX} by default")
    agents = [f for f in cx if f.name in ("AGENTS.md", "AGENTS.override.md") and f.parent != codex_home]
    imported = any(re.search(r"@(\./)?AGENTS\.md\b", read_text(f) or "") for f in cl)
    if agents and not agents_direct and not imported:
        flag("NOTE", project, "a CLAUDE.md or CLAUDE.local.md here or above does not import @AGENTS.md, so Claude Code reads only the CLAUDE files: the two agents get different rules")
    if agents_direct:
        flag("NOTE", project, "Claude Code reads AGENTS.md directly (v2.1.277 or later). Adding a CLAUDE.md or CLAUDE.local.md without an @AGENTS.md line would stop that")
    if any(f.name == "AGENTS.override.md" for f in agents):
        flag("NOTE", project, "AGENTS.override.md is in use: Codex reads it instead of the AGENTS.md beside it")

    print("\nSkills")
    found = {}
    for agent, places in skill_dirs(home, claude_home, codex_home, dirs).items():
        found[agent], total = scan_skills(agent, places)
        overlaps(found[agent])
        if agent == "Codex" and total > CODEX_LIST_BUDGET:
            flag("WARN", "Codex skills", f"descriptions total {total} characters; Codex may list only about {CODEX_LIST_BUDGET} when it doesn't know the context size")
    c, x = set(found["Claude Code"]), set(found["Codex"])
    if c and x:
        for n in sorted(c - x):
            flag("NOTE", n, "installed for Claude Code only")
        for n in sorted(x - c):
            flag("NOTE", n, "installed for Codex only")

    print("\nSettings")
    claude_settings(claude_home, dirs)
    codex_config(codex_home, dirs)

    print("\nFlags")
    if not flags:
        print("  none")
    order = {"FAIL": 0, "WARN": 1, "NOTE": 2}
    for level, where, msg in sorted(flags, key=lambda t: order[t[0]]):
        print(f"  {level} {where}: {msg}")
    print("\nThis lists what is on disk. It does not show plugins, managed settings or what a running session loaded; check those with the agent itself.")


def selftest():
    tmp = Path(tempfile.mkdtemp(prefix="inventory-selftest-"))
    h = tmp / "home"
    p = tmp / "proj"

    def skill(base, folder, name, desc):
        d = base / folder
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {desc}\n---\n\nbody\n")

    cs, xs = h / ".claude" / "skills", h / ".agents" / "skills"
    skill(cs, "notes-to-tasks", "notes-to-tasks", "Turns meeting notes into action items with owners and due dates. Not for minutes.")
    skill(cs, "action-items", "action-items", "Extracts action items with owners and due dates from meeting notes.")
    skill(cs, "wrong", "other-name", "Does a thing. Not for other things.")
    skill(cs, "long", "long", "x " * 400 + "Not for y.")
    (cs / "gone").symlink_to(tmp / "nowhere")
    skill(xs, "notes-to-tasks", "notes-to-tasks", "Turns meeting notes into action items with owners and due dates. Not for minutes.")
    (h / ".claude" / "settings.json").write_text('{"permissions": {"allow": ["Bash(*)"], "defaultMode": "bypassPermissions"}}')
    (h / ".codex").mkdir()
    (h / ".codex" / "config.toml").write_text('sandbox_mode = "danger-full-access"\napproval_policy = "never"\n')
    p.mkdir()
    (p / "AGENTS.md").write_text("# Rules\n- Run make check.\n")
    (p / "CLAUDE.md").write_text("# Notes\nSee @docs/missing.md\n")
    (p / ".claude").mkdir()
    (p / ".claude" / "settings.json").write_text("{not json")

    import io
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run(str(h), str(p))
    out = buf.getvalue()
    checks = [
        ("broken link", "broken link"),
        ("name mismatch", "does not match folder 'wrong'"),
        ("long description", "description is 8"),
        ("missing Not for", "no 'Not for' line"),
        ("overlap", "descriptions overlap"),
        ("Claude only", "installed for Claude Code only"),
        ("bypass", "bypassPermissions"),
        ("broad allow", "broad allow rule Bash(*)"),
        ("bad JSON", "not valid JSON"),
        ("missing import", "imports @docs/missing.md"),
        ("AGENTS not imported", "does not import @AGENTS.md"),
    ]
    checks.append(("no sandbox", "sandbox_mode is danger-full-access"))
    bad = [n for n, s in checks if s not in out]
    for n, s in checks:
        print(f"{'ok ' if n not in bad else 'FAIL'} {n}")

    def case(name, setup, want, env=None):
        """Run against a fresh stand-in home; pass when no crash and every wanted text appears."""
        flags.clear()
        root = Path(tempfile.mkdtemp(dir=tmp))
        home_, proj = root / "home", root / "proj"
        (home_ / ".claude").mkdir(parents=True)
        proj.mkdir()
        setup(home_, proj, root)
        buf = io.StringIO()
        saved = {k: os.environ.get(k) for k in ("HOME", "CLAUDE_CONFIG_DIR", "CODEX_HOME")}
        try:
            if env:
                for k, v in env(home_, root).items():
                    os.environ[k] = v
            with contextlib.redirect_stdout(buf):
                run(None if env else str(home_), str(proj))
            got = buf.getvalue()
            ok = all(w in got for w in want)
        except Exception as e:  # a crash is a failure
            ok, got = False, repr(e)
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        print(f"{'ok ' if ok else 'FAIL'} {name}")
        if not ok:
            bad.append(name)

    for body, want in (("[]", "not a JSON object"), ("null", "not a JSON object"),
                       ('{"permissions": "x"}', "permissions is not an object"),
                       ('{"permissions": {"allow": [1, null, "Bash(*)"]}}', "entries that are not strings"),
                       ('{"hooks": "x"}', "hooks is not an object")):
        case(f"settings {body} does not crash", lambda h, p_, r, b=body: (h / ".claude" / "settings.json").write_text(b), [want])

    def agents_only(h, p_, r):
        (p_ / "AGENTS.md").write_text("# Rules\n")
    case("AGENTS.md alone is read by Claude Code", agents_only, ["reads AGENTS.md directly"])

    def dot_import(h, p_, r):
        (p_ / "AGENTS.md").write_text("# Rules\n")
        (p_ / "CLAUDE.md").write_text("@./AGENTS.md\n")
    case("@./AGENTS.md counts as an import", dot_import, ["Flags\n  none"])

    def big_agents(h, p_, r):
        (p_ / "AGENTS.md").write_text("x" * 40000)
        (p_ / "CLAUDE.md").write_text("@AGENTS.md\n")
    case("project AGENTS.md over 32 KiB without a global file", big_agents, ["Codex stops adding them"])

    def config_dir(h, p_, r):
        skill(r / "cfg" / "skills", "only-here", "only-here", "Lives in the config dir. Not for tests.")
    case("CLAUDE_CONFIG_DIR is used", config_dir, ["only-here"],
         env=lambda h, r: {"HOME": str(h), "CLAUDE_CONFIG_DIR": str(r / "cfg"), "CODEX_HOME": str(h / ".codex")})

    def bom(h, p_, r):
        d = h / ".claude" / "skills" / "bom"
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text("\ufeff---\nname: bom\ndescription: Has a BOM. Not for tests.\n---\n", encoding="utf-8")
    case("byte-order mark before frontmatter", bom, ["bom  ("])
    # A clean setup must give no FAIL or WARN.
    flags.clear()
    clean = tmp / "clean"
    skill(clean / "home" / ".claude" / "skills", "solo", "solo", "Does one job. Not for anything else.")
    (clean / "p").mkdir()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run(str(clean / "home"), str(clean / "p"))
    noisy = [f for f in flags if f[0] in ("FAIL", "WARN")]
    print(f"{'ok ' if not noisy else 'FAIL'} clean setup has no FAIL or WARN")
    if noisy:
        bad.append("clean")
        print(noisy)
    print("RESULT:", "PASS" if not bad else "FAIL " + ", ".join(bad))
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    return 0 if not bad else 1


def main(argv):
    home, project = None, "."
    args = list(argv)
    if "--selftest" in args:
        return selftest()
    while args:
        a = args.pop(0)
        if a == "--home" and args:
            home = args.pop(0)
        elif a == "--project" and args:
            project = args.pop(0)
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        else:
            print(f"unknown argument: {a}\n{__doc__}", file=sys.stderr)
            return 2
    if home and not Path(home).is_dir():
        print(f"no such folder: {home}", file=sys.stderr)
        return 2
    if not Path(project).is_dir():
        print(f"no such folder: {project}", file=sys.stderr)
        return 2
    run(home, project)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
