#!/usr/bin/env python3
"""List what brag may read in a project, in priority order, before anything is opened.

Usage: python3 scan_project.py <project-folder> [--max-files N]

Files are classified by name and location first. Only files classed as safe are opened, and only
to pull colours, fonts, page text and secret-looking lines (reported by line number, never shown).
Standard library only.
"""
import argparse
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import leaks  # noqa: E402

SKIP_DIRS = {".git", "node_modules", "dist", "build", "out", ".next", ".nuxt", ".svelte-kit",
             "coverage", ".venv", "venv", "env", "__pycache__", ".cache", "vendor", "target",
             ".turbo", ".parcel-cache", ".idea", ".vscode"}
SECRET_DIRS = {"secrets", "secret", "credentials", ".ssh", ".aws", ".gnupg", "private"}
DATA_DIRS = {"seed", "seeds", "fixtures", "migrations", "dumps", "exports", "backups", "data"}
SECRET_NAME = re.compile(
    r"(^\.env($|\.)|\.pem$|\.key$|\.p12$|\.pfx$|\.keystore$|\.jks$|^id_(rsa|dsa|ecdsa|ed25519)|"
    r"credential|secret|service[-_]?account|(auth|access|api|refresh|bearer)[-_]?tokens?|password|passwd|^\.npmrc$|^\.pypirc$|^\.netrc$|"
    r"^\.htpasswd$|\.tfstate|\.kdbx$|\.local\.)", re.I)
# Name-based secret skipping doesn't apply to pages and components (password-reset.jsx is UI)
UI_EXT = re.compile(r"\.(html?|css|scss|sass|less|jsx|tsx|vue|svelte|astro)$", re.I)
DATA_NAME = re.compile(r"\.(sqlite3?|db|csv|tsv|xlsx?|parquet|jsonl|ndjson|sql|dump|bak|log|mbox|eml)$", re.I)
CONFIG_NAME = re.compile(r"(\.(ya?ml|toml|ini|conf|cfg|properties|tf|tfvars)$|^docker-compose|^dockerfile|"
                         r"^(db|database|seed|users|customers|accounts|orders|dump|export|backup)[\w-]*\.json$)", re.I)
LOCK_NAME = re.compile(r"(^package-lock\.json$|^yarn\.lock$|^pnpm-lock\.yaml$|^bun\.lockb?$|"
                       r"^poetry\.lock$|^uv\.lock$|^Cargo\.lock$|^Gemfile\.lock$|^composer\.lock$|\.min\.(js|css)$|\.map$)", re.I)
IMAGE = re.compile(r"\.(png|jpe?g|gif|svg|webp|avif|ico)$", re.I)
MEDIA = re.compile(r"\.(mp4|webm|mov|mp3|wav|ogg|m4a|woff2?|ttf|otf)$", re.I)
TEXT = re.compile(r"\.(html?|css|scss|sass|less|md|mdx|txt|json|js|jsx|ts|tsx|vue|svelte|astro|py|rb|go|rs|php|erb|njk|liquid)$", re.I)
KEEP_CONFIG = {"package.json", "manifest.json", "site.webmanifest", "tokens.json", "theme.json", "pyproject.toml"}
COLOUR_VAR = re.compile(r"(--[A-Za-z0-9_-]+)\s*:\s*(#[0-9a-fA-F]{3,8}\b|(?:rgb|rgba|hsl|hsla|oklch|oklab|lab|lch)\([^)]*\))")
FONT_VAR = re.compile(r"(--[A-Za-z0-9_-]*font[A-Za-z0-9_-]*)\s*:\s*([^;}{]+)", re.I)
FONT_FAMILY = re.compile(r"font-family\s*:\s*([^;}{]+)", re.I)
GOOGLE_FONT = re.compile(r"fonts\.googleapis\.com/css2?\?([^\"'>\s]+)", re.I)
TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
META_DESC = re.compile(r"<meta[^>]+name=[\"']description[\"'][^>]+content=[\"']([^\"']+)", re.I)
HEADING = re.compile(r"<h([1-3])[^>]*>(.*?)</h\1>", re.I | re.S)
TAG = re.compile(r"<[^>]+>")
MAX_BYTES = 512 * 1024


def priority(rel):
    low = rel.lower()
    base = os.path.basename(low)
    depth = low.count("/")
    if base in ("index.html", "index.htm") and depth <= 1:
        return 0
    if base.endswith((".html", ".htm")) and depth <= 1:
        return 1
    if base.endswith((".css", ".scss", ".sass", ".less")) or base in ("tailwind.config.js", "tailwind.config.ts"):
        return 2
    if base.startswith("readme"):
        return 3
    if base in ("package.json", "pyproject.toml", "manifest.json", "site.webmanifest"):
        return 4
    if re.search(r"(^|/)(app|pages|routes|src/app|src/pages|src/routes|src/views|views)/", low):
        return 5
    if re.search(r"(^|/)(components|src/components|features|src/features)/", low):
        return 6
    if base.endswith((".html", ".htm", ".md", ".mdx")):
        return 7
    return 8


def ignored_by_git(root, rels):
    if not rels:
        return set()
    try:
        r = subprocess.run(["git", "-C", root, "check-ignore", "--stdin"], input="\n".join(rels),
                           capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return set()
    return set(l.strip() for l in r.stdout.splitlines() if l.strip())


def classify(root, max_files):
    read, skipped, images, media = [], [], [], []
    candidates = []
    for dp, dns, fns in os.walk(root):
        rel_dir = os.path.relpath(dp, root)
        keep = []
        for d in sorted(dns):
            rd = os.path.normpath(os.path.join(rel_dir, d))
            if d in SKIP_DIRS or d.startswith("brag-output"):
                skipped.append((rd + "/", "build output, dependencies or tooling"))
            elif d.lower() in SECRET_DIRS:
                skipped.append((rd + "/", "folder name suggests secrets"))
            elif d.lower() in DATA_DIRS:
                skipped.append((rd + "/", "data folder: may hold real records"))
            else:
                keep.append(d)
        dns[:] = keep
        for f in sorted(fns):
            rel = os.path.normpath(os.path.join(rel_dir, f))
            full = os.path.join(dp, f)
            if os.path.islink(full):
                skipped.append((rel, "symbolic link"))
            elif SECRET_NAME.search(f) and not UI_EXT.search(f):
                skipped.append((rel, "name suggests secrets or keys"))
            elif DATA_NAME.search(f):
                skipped.append((rel, "data or log file: may hold real records"))
            elif CONFIG_NAME.search(f) and f.lower() not in KEEP_CONFIG:
                skipped.append((rel, "config or data file: not video material; may hold secrets or records"))
            elif LOCK_NAME.search(f):
                skipped.append((rel, "lock file or minified build output"))
            elif IMAGE.search(f):
                images.append(rel)
            elif MEDIA.search(f):
                media.append(rel)
            elif TEXT.search(f):
                candidates.append(rel)
            else:
                skipped.append((rel, "not a text type brag reads"))
    ign = ignored_by_git(root, candidates + images)
    for rel in candidates:
        if rel in ign:
            skipped.append((rel, "ignored by git"))
        elif os.path.getsize(os.path.join(root, rel)) > MAX_BYTES:
            skipped.append((rel, "larger than 512 KB"))
        else:
            read.append(rel)
    images = [i for i in images if i not in ign]
    read.sort(key=lambda r: (priority(r), r.count("/"), r))
    return read[:max_files], read[max_files:], skipped, images, media


def clean(text):
    return re.sub(r"\s+", " ", TAG.sub(" ", text)).strip()


def extract(root, files):
    colours, fonts, text, warns, demoted = {}, [], [], [], []
    for rel in files:
        try:
            with open(os.path.join(root, rel), encoding="utf-8", errors="replace") as fh:
                body = fh.read()
        except OSError:
            continue
        lines = body.splitlines()
        secret_lines = [i for i, line in enumerate(lines, 1) if "a key, token or password" in leaks.find(line)]
        if secret_lines and priority(rel) > 4:
            demoted.append((rel, f"has a key, token or password at line {secret_lines[0]}; not needed for a video"))
            continue
        for i in secret_lines:
            warns.append(f"{rel}:{i}: looks like a key, token or password (not shown); keep it out of every output")
        for i, line in enumerate(lines, 1):
            if leaks.INTERNAL.search(line) or leaks.PRIVATE_IP.search(line):
                warns.append(f"{rel}:{i}: internal hostname or private address (not shown); keep it off screen")
        found = sorted(set(e for line in lines for e in leaks.emails(line)))
        if found:
            warns.append(f"{rel}: {len(found)} email address(es) (not shown); use made-up stand-ins on screen")
        if rel.lower().endswith((".css", ".scss", ".sass", ".less", ".html", ".htm", ".vue", ".svelte", ".astro", ".jsx", ".tsx")):
            for name, val in COLOUR_VAR.findall(body):
                colours.setdefault(name, (val, rel))
            for name, fam in FONT_VAR.findall(body):
                fonts.append((f"{fam.strip()} [{name}]", rel))
            for fam in FONT_FAMILY.findall(body):
                fam = fam.strip()
                if fam and (fam, rel) not in fonts and not fam.startswith("var("):
                    fonts.append((fam, rel))
            for q in GOOGLE_FONT.findall(body):
                for fam in re.findall(r"family=([^&:]+)", q):
                    fonts.append((fam.replace("+", " ") + " (Google Fonts link)", rel))
        if rel.lower().endswith((".html", ".htm")):
            found_text = []
            for m in TITLE.findall(body)[:1]:
                found_text.append(f"{rel}: title: {clean(m)}")
            for m in META_DESC.findall(body)[:1]:
                found_text.append(f"{rel}: description: {clean(m)}")
            for lvl, m in HEADING.findall(body)[:12]:
                t = clean(m)
                if t:
                    found_text.append(f"{rel}: h{lvl}: {t}")
            for t in found_text:
                text.append(t if not leaks.find(t) else f"{rel}: (a heading with an address or key, not shown)")
    return colours, fonts, text, warns, demoted


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("project")
    ap.add_argument("--max-files", type=int, default=40)
    a = ap.parse_args()
    root = os.path.abspath(a.project)
    if not os.path.isdir(root):
        print(f"scan_project: not a folder: {a.project}")
        return 2
    read, more, skipped, images, media = classify(root, a.max_files)
    if not read and not images:
        print("scan_project: nothing brag can read here; is this the project folder?")
        return 1
    colours, fonts, text, warns, demoted = extract(root, read)
    gone = {r for r, _ in demoted}
    read = [r for r in read if r not in gone]
    skipped += demoted
    print(f"Project: {os.path.basename(root)}  ({len(read)} to read, {len(skipped)} skipped, {len(images)} images)")
    print("\nREAD, in this order:")
    for r in read:
        print(f"  {r}")
    if more:
        print(f"  ... {len(more)} more lower-priority files; read them only if the plan needs them")
    print("\nSKIPPED (do not open):")
    for r, why in skipped[:60]:
        print(f"  {r}  [{why}]")
    if len(skipped) > 60:
        print(f"  ... {len(skipped) - 60} more")
    print("\nIMAGES:")
    for i in images[:40]:
        print(f"  {i}")
    if media:
        print("\nOTHER MEDIA (fonts, video, audio):")
        for m in media[:20]:
            print(f"  {m}")
    print("\nCOLOURS (custom properties):")
    for name, (val, rel) in list(colours.items())[:30]:
        print(f"  {name}: {val}  ({rel})")
    if not colours:
        print("  none found; read the stylesheet for the most-used background, text and accent colours")
    print("\nFONTS:")
    for fam, rel in fonts[:15]:
        print(f"  {fam}  ({rel})")
    print("\nPAGE TEXT:")
    for t in text[:30]:
        print(f"  {t}")
    if warns:
        print("\nWARN:")
        for w in warns:
            print(f"  {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
