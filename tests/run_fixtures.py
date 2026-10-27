# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6"]
# ///
"""Prove every house-rule check can fail (house rule 10).

Usage: uv run tests/run_fixtures.py

Each case builds a small library in a temp folder from a known-good skill plus one change, runs
tools/check_skills.py on it, and checks the output. Bad content (including invisible characters)
exists only in the temp folder, never in this repo. Exits 1 if any case misbehaves.

Expectations: "PASS" (exit 0, no FAIL), "FAIL R<n>" or "WARN R<n>" (must appear), or "!<text>"
(must not appear).
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CHECK = os.path.join(REPO, "tools", "check_skills.py")
with open(os.path.join(REPO, "tools", "find-brand.sh")) as f:
    FIND_BRAND = f.read()

TERM = "examplecorp"
GOOD_DESC = ("Drafts a short status update from notes. Use when someone asks for a weekly update. "
             "Not for long reports.")
GOOD_BODY = "# Status update\n\n1. Read the notes.\n2. Write three bullet points.\n"
BRAND_BODY = ("# Brand probe\n\nRun `scripts/find-brand.sh`, then read `tokens.json` from the folder it names "
              "(project `.agents/brand/`, `local/`, `~/.agents/brand/`, or `references/`).\n"
              "First line: `Brand: <source> (<folder>) primary=<value>`.\n")
CASES_YAML = ("cases:\n"
              "  - id: one\n    prompt: weekly update from these notes\n    expect: [three bullets]\n"
              "  - id: two\n    prompt: status for the team\n    expect: [three bullets]\n"
              "  - id: three\n    prompt: what did we do this week\n    expect: [three bullets]\n")
TRIGGERS_YAML = ("should: [write my weekly update, status update please, summarise this week for the team]\n"
                 "should_not: [write a long report, update my packages, weekly meal plan]\n")


def skill_md(name="status-update", desc=GOOD_DESC, body=GOOD_BODY, extra="", meta="  status: stable\n"):
    return f"---\nname: {name}\ndescription: {desc}\n{extra}metadata:\n{meta}---\n\n{body}"


def good_files(name="status-update"):
    return {f"skills/{name}/SKILL.md": skill_md(name),
            f"evals/{name}/cases.yaml": CASES_YAML, f"evals/{name}/triggers.yaml": TRIGGERS_YAML}


def brand_files(name="brand-probe", primary="#111111"):
    files = good_files(name)
    files[f"skills/{name}/SKILL.md"] = skill_md(name, body=BRAND_BODY, meta='  status: stable\n  brand: "true"\n')
    files[f"skills/{name}/references/tokens.json"] = '{ "primary": "%s" }\n' % primary
    files[f"skills/{name}/local.example/tokens.json"] = '{ "primary": "#0f766e" }\n'
    files[f"skills/{name}/scripts/find-brand.sh"] = FIND_BRAND
    return files


def without(base, suffix):
    return {k: v for k, v in base.items() if not k.endswith(suffix)}


def case(files, expect, deny="", require_deny=False, git=None, hidden=None, extra_text=None):
    return dict(files=files, expect=expect, deny=deny, require_deny=require_deny, git=git, hidden=hidden,
                extra_text=extra_text)


S = "skills/status-update/SKILL.md"
G = good_files()
UPSTREAM = '  status: stable\n  upstream: "someone/skills@abc1234def"\n'
NOTICE = "| Skill | Upstream |\n| :--- | :--- |\n| status-update | someone/skills at abc1234 |\n"
CASES = {
    "good library passes": case({**G, **brand_files()}, ["PASS"]),
    "R1 extra frontmatter key": case({**G, S: skill_md(extra="model: opus\n")}, ["FAIL R1"]),
    "R1 invalid YAML": case({**G, S: "---\nname: [unclosed\n---\nbody\n"}, ["FAIL R1"]),
    "R1 metadata not strings": case({**G, S: skill_md(meta="  status: stable\n  brand: true\n")}, ["FAIL R1"]),
    "R2 name differs from folder": case({**G, S: skill_md(name="other-name")}, ["FAIL R2"]),
    "R2 reserved word": case(good_files("claude-helper"), ["FAIL R2"]),
    "R2 built-in name": case(good_files("simplify"), ["FAIL R2"]),
    "R2 bad characters": case(good_files("Status_Update"), ["FAIL R2"]),
    "R3 not third person": case({**G, S: skill_md(desc="I draft status updates. Use when asked. Not for reports.")}, ["WARN R3"]),
    "R3 no when-to-use": case({**G, S: skill_md(desc="Drafts a short status update from notes. Not for reports.")}, ["WARN R3"]),
    "R3 no not-for": case({**G, S: skill_md(desc="Drafts a status update. Use when asked for one.")}, ["WARN R3"]),
    "R3 'use it when' is accepted": case({**G, S: skill_md(desc="Drafts a status update. Use it when asked. Not for reports.")}, ["PASS", "!WARN R3"]),
    "R4 over 300 warns": case({**G, S: skill_md(desc=GOOD_DESC + " x" * 120)}, ["WARN R4"]),
    "R4 over 1024 fails": case({**G, S: skill_md(desc=GOOD_DESC + " x" * 500)}, ["FAIL R4"]),
    "R4 missing description": case({**G, S: "---\nname: status-update\nmetadata:\n  status: draft\n---\nbody\n"}, ["FAIL R4"]),
    "R4 XML tag in description": case({**G, S: skill_md(desc="Drafts <b>updates</b>. Use when asked. Not for reports.")}, ["FAIL R4"]),
    "R5 body 500 lines": case({**G, S: skill_md(body="line\n" * 500)}, ["FAIL R5"]),
    "R5 body over 5000 tokens": case({**G, S: skill_md(body=("word " * 20 + "\n") * 220)}, ["WARN R5"]),
    "R6 missing reference": case({**G, S: skill_md(body="See [guide](references/guide.md).\n")}, ["FAIL R6"]),
    "R6 nested reference": case({**G, S: skill_md(body="See [guide](references/guide.md).\n"),
                                 "skills/status-update/references/guide.md": "See [more](more.md).\n",
                                 "skills/status-update/references/more.md": "detail\n"}, ["FAIL R6"]),
    "R6 long reference without contents": case({**G, "skills/status-update/references/big.md": "line\n" * 101}, ["FAIL R6"]),
    "R6 points outside the skill": case({**G, S: skill_md(body="See [x](../other/SKILL.md).\n")}, ["FAIL R6"]),
    "R6 mailto link is accepted": case({**G, S: skill_md(body="Mail [us](mailto:team@example.org).\n")}, ["PASS"]),
    "R7 stable without evals": case({S: skill_md()}, ["FAIL R7"]),
    "R7 draft without evals warns": case({S: skill_md(meta="  status: draft\n")}, ["WARN R7", "PASS"]),
    "R7 bad status": case({**G, S: skill_md(meta="  status: beta\n")}, ["FAIL R7"]),
    "R7 case without expect": case({**G, "evals/status-update/cases.yaml": CASES_YAML.replace("    expect: [three bullets]\n", "", 1)}, ["FAIL R7"]),
    "R7 too few near-miss triggers": case({**G, "evals/status-update/triggers.yaml": "should: [a, b, c]\nshould_not: [d, e]\n"}, ["FAIL R7"]),
    "R7 missing setup file": case({**G, "evals/status-update/cases.yaml": CASES_YAML.replace("  - id: one\n", "  - id: one\n    setup: [files/notes.md]\n")}, ["FAIL R7"]),
    "R9 zero-width space": case(G, ["FAIL R9"], hidden=0x200B),
    "R9 left-to-right mark": case(G, ["FAIL R9"], hidden=0x200E),
    "R9 soft hyphen": case(G, ["FAIL R9"], hidden=0x00AD),
    "R9 variation selector": case(G, ["FAIL R9"], hidden=0xFE0F),
    "R9 tag character": case(G, ["FAIL R9"], hidden=0xE0041),
    "R9 employer term": case({**G, S: skill_md(body=f"Built for {TERM.title()} teams.\n")}, ["FAIL R9", "pattern #1", f"!{TERM}"], deny=TERM),
    "R9 employer term in an svg": case({**G, "skills/status-update/assets/logo.svg": f"<svg><title>{TERM}</title></svg>\n"}, ["FAIL R9"], deny=TERM),
    "R9 employer term in a fixtures folder": case({**G, "skills/status-update/fixtures/leak.md": f"{TERM}\n"}, ["FAIL R9"], deny=TERM),
    "R9 employer term in commit or PR text": case(G, ["FAIL R9"], deny=TERM, extra_text=f"Fix for the {TERM} rollout\n"),
    "R9 employer patterns required": case(G, ["FAIL R9"], require_deny=True),
    "R9 untracked file is scanned": case({**G, "notes.md": f"{TERM}\n"}, ["FAIL R9"], deny=TERM, git="init"),
    "R9 ignored local/ is not scanned": case({**G, ".gitignore": "skills/*/local/\n",
                                               "skills/status-update/local/guidelines.md": f"{TERM}\n"}, ["PASS"], deny=TERM, git="init"),
    "R9 tracked local file": case({**G, "skills/status-update/local/tokens.json": "{}\n"}, ["FAIL R9"], git="commit-all"),
    "R9 borrowed text without licence": case({**G, S: skill_md(extra="license: Apache-2.0\n")}, ["FAIL R9"]),
    "R9 MIT upstream without licence file": case({**G, S: skill_md(meta=UPSTREAM), "THIRD_PARTY_NOTICES.md": NOTICE}, ["FAIL R9"]),
    "R9 MIT upstream with licence and notice": case({**G, S: skill_md(meta=UPSTREAM), "THIRD_PARTY_NOTICES.md": NOTICE,
                                                      "skills/status-update/LICENSE": "MIT License\n"}, ["PASS"]),
    "R9 notice row without the commit": case({**G, S: skill_md(meta=UPSTREAM), "skills/status-update/LICENSE": "MIT\n",
                                              "THIRD_PARTY_NOTICES.md": NOTICE.replace(" at abc1234", "")}, ["FAIL R9"]),
    "R10 no skills": case({"README.md": "empty\n"}, ["FAIL R10"]),
    "R11 date in body": case({**G, S: skill_md(body="Since 2026-10-25 use the new API.\n")}, ["WARN R11"]),
    "R12 brand files missing": case(without(brand_files(), "references/tokens.json"), ["FAIL R12"]),
    "R12 brand script edited": case({**brand_files(), "skills/brand-probe/scripts/find-brand.sh": FIND_BRAND + "# edited\n"}, ["FAIL R12"]),
    "R12 tokens without primary": case({**brand_files(), "skills/brand-probe/references/tokens.json": '{ "accent": "#000" }\n'}, ["FAIL R12"]),
    "R12 token is a name, not a colour": case(brand_files(primary="LOCAL-TEAL"), ["FAIL R12"]),
    "R12 missing Brand: line": case({**brand_files(), "skills/brand-probe/SKILL.md": skill_md(
        "brand-probe", body="Run `scripts/find-brand.sh`.\n", meta='  status: stable\n  brand: "true"\n')}, ["FAIL R12"]),
}


def run_case(title, c):
    tmp = tempfile.mkdtemp(prefix="gfm-skills-fixture-")
    try:
        root = os.path.join(tmp, "lib")
        os.makedirs(os.path.join(root, "skills"), exist_ok=True)
        for rel, content in c["files"].items():
            p = os.path.join(root, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(content)
        if c["hidden"]:
            with open(os.path.join(root, S), "a", encoding="utf-8") as f:
                f.write("hidden" + chr(c["hidden"]) + "note\n")
        # Run from a git hook, GIT_DIR and friends point at the real repo; keep them away from the
        # fixture repo, or `git init` and `commit` act on the real one.
        clean = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        if c["git"]:
            git = ["git", "-C", root, "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid"]
            subprocess.run(git + ["init", "-q"], check=True, env=clean)
            if c["git"] == "commit-all":
                subprocess.run(git + ["add", "-f", "."], check=True, env=clean)
                subprocess.run(git + ["commit", "-qm", "fixture"], check=True, env=clean)
        env = {k: v for k, v in clean.items() if k not in ("GFM_SKILLS_DENY", "GFM_SKILLS_DENY_FILE")}
        env["GFM_SKILLS_DENY"] = c["deny"]
        cmd = [sys.executable, CHECK, "--root", root]
        if c["require_deny"]:
            cmd.append("--require-deny")
        if c["extra_text"]:
            extra = os.path.join(tmp, "extra.txt")
            with open(extra, "w") as f:
                f.write(c["extra_text"])
            cmd += ["--extra-text", extra]
        r = subprocess.run(cmd, capture_output=True, text=True, env=env)
        out = r.stdout + r.stderr
        ok = True
        for e in c["expect"]:
            if e == "PASS":
                ok = ok and r.returncode == 0 and "FAIL" not in out
            elif e.startswith("!"):
                ok = ok and e[1:].lower() not in out.lower()
            else:
                ok = ok and e in out
                if e.startswith("FAIL"):
                    ok = ok and r.returncode == 1
        print(f"{'ok  ' if ok else 'BAD '} {title}")
        if not ok:
            print("     expected:", c["expect"], "exit:", r.returncode)
            print("     " + out.strip().replace("\n", "\n     "))
        return ok
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    results = [run_case(t, c) for t, c in CASES.items()]
    print(f"{sum(results)} of {len(results)} fixture cases behaved as expected")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
