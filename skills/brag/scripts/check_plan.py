#!/usr/bin/env python3
"""Check a brag plan before building, and a brag output folder before rendering.

Usage:
  python3 check_plan.py <output>/brag-plan.md   the plan only (step 2)
  python3 check_plan.py <output>                the plan, plus composition-brief.md, share-copy.txt
                                                and composition/index.html, brag.json (step 3)

Plan checks: the template's headings are there; scene lengths under Storyboard add up to 15-25 s
(and match the Duration line); each scene leaves time to read its on-screen lines; every claim has
a source; no stock launch phrases; a bundled track named in Audio exists. Every file checked: no
key, token, password, internal hostname, private address, path on this machine, or real-looking
email address (made-up ones at example.com, .test or .invalid are fine, and so is anything under
## Stand-ins). It cannot tell whether a claim matches its source.
Exit 0 when there are no FAIL lines. Standard library only.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import leaks  # noqa: E402

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUIRED = ["What it is", "Angle", "Hook", "Tone", "Format", "Duration", "Visual identity",
            "Audio", "Storyboard", "Claims", "Share copy"]
SCENE = re.compile(r"^#{3,4}\s*Scene\s*(\d+)\s*[:.\-]?\s*(.*?)\s*\(\s*(\d+(?:\.\d+)?)\s*s(?:ec(?:onds?)?)?\s*\)\s*$", re.I)
SCENE_LOOSE = re.compile(r"^(?:#{3,4}\s*|\*\*\s*)Scene\s*\d", re.I)
ON_SCREEN = re.compile(r"^\s*[-*]?\s*\**\s*On screen\s*\**\s*:\s*\**", re.I)
QUOTED = re.compile(r"\"([^\"]+)\"|“([^”]+)”")
STOCK = ["streamline your workflow", "excited to share", "thrilled to announce", "game-changer",
         "game changer", "revolutionize", "revolutionise", "next-level", "seamless", "unlock the power",
         "supercharge", "cutting-edge", "best-in-class", "take it to the next level"]
NO_SOURCE = re.compile(r"^\s*(|tbd|todo|\?+|-+|n/?a|none|unknown|made up|invented)\s*$", re.I)
NOT_A_CLAIM = re.compile(r"\b(joke|for fun|made up|invented|written for the video|my own|not a claim)\b", re.I)
OTHER_FILES = ["composition-brief.md", "share-copy.txt", os.path.join("composition", "index.html"),
               os.path.join("composition", "brag.json")]


def sections(lines):
    out = {}
    for i, line in enumerate(lines):
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            out.setdefault(m.group(1).strip().lower(), i)
    return out


def section_text(lines, secs, name):
    start = secs.get(name.lower())
    if start is None:
        return []
    body = []
    for line in lines[start + 1:]:
        if re.match(r"^##\s", line):
            break
        body.append(line)
    return body


def read_time(line):
    words = len(line.split())
    return 0.8 if words <= 3 else max(1.2, 0.3 * words)


def leak_lines(label, lines, skip=()):
    out = []
    for i, line in enumerate(lines, 1):
        if i in skip:
            continue
        for kind in leaks.find(line):
            fix = ("write the folder's name or a relative path instead" if "path" in kind
                   else "leave it out" if "key" in kind
                   else "use a made-up stand-in and list it under Stand-ins")
            out.append(f"{label}:{i}: contains {kind}; {fix}")
    return out


def check_plan(path):
    fails, warns, info = [], [], {"scenes": 0, "total": 0.0, "claims": 0}
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
    except OSError as e:
        return [f"cannot read {path}: {e.strerror}"], warns, info
    secs = sections(lines)
    for name in REQUIRED:
        if name.lower() not in secs:
            fails.append(f"missing section '## {name}'")

    # Scenes: only under ## Storyboard
    sb = secs.get("storyboard")
    sb_end = len(lines)
    if sb is not None:
        for j in range(sb + 1, len(lines)):
            if re.match(r"^##\s", lines[j]):
                sb_end = j
                break
    scenes, cur = [], None
    for i in range(len(lines)):
        line = lines[i].strip()
        inside = sb is not None and sb < i < sb_end
        m = SCENE.match(line)
        if m and inside:
            cur = {"n": int(m.group(1)), "name": m.group(2) or f"Scene {m.group(1)}", "sec": float(m.group(3)), "onscreen": []}
            scenes.append(cur)
            continue
        if SCENE_LOOSE.match(line) and inside:
            fails.append(f"line {i + 1}: scene heading not in the form '### Scene N: name (3.5s)'")
            cur = None
            continue
        if not inside:
            cur = None
            continue
        if cur is not None and ON_SCREEN.match(lines[i]):
            for a, b in QUOTED.findall(lines[i]):
                cur["onscreen"].append(a or b)
    total = sum(s["sec"] for s in scenes)
    info.update(scenes=len(scenes), total=total)
    if len(scenes) < 2:
        fails.append(f"found {len(scenes)} scene(s) under ## Storyboard; a brag video needs at least 2 '### Scene' blocks")
    elif not 15 <= total <= 25:
        fails.append(f"scenes add up to {total:g}s; they must add up to 15 to 25 s")
    dur = " ".join(section_text(lines, secs, "Duration"))
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:s\b|sec|second)", dur, re.I) or re.search(r"^\s*(\d+(?:\.\d+)?)\s*$", dur)
    if m and scenes and abs(float(m.group(1)) - total) > 1.0:
        warns.append(f"Duration says {m.group(1)}s but scenes add up to {total:g}s")
    for s in scenes:
        need = sum(read_time(t) for t in s["onscreen"])
        if need and need + 0.4 > s["sec"] + 1e-9:
            fails.append(f"Scene {s['n']} ({s['name']}, {s['sec']:g}s): its on-screen lines need about {need:.1f}s "
                         f"of reading plus transitions; cut words, split the scene or lengthen it")
        if not s["onscreen"] and s["sec"] >= 2:
            warns.append(f"Scene {s['n']}: no 'On screen:' line with text in double quotes; reading time not checked")
    if scenes and scenes[0]["sec"] > 3.5:
        warns.append(f"the hook scene is {scenes[0]['sec']:g}s; the first 2 to 3 s decide whether anyone keeps watching")

    # Claims
    claims = section_text(lines, secs, "Claims")
    rows = [l for l in claims if l.strip().startswith("|") and not re.match(r"^\s*\|\s*:?-", l)]
    rows = rows[1:] if rows and re.search(r"on screen|claim", rows[0], re.I) else rows
    for r in rows:
        cells = [c.strip() for c in r.strip().strip("|").split("|")]
        if len(cells) < 2 or NO_SOURCE.match(cells[1]):
            fails.append(f"claim without a source: {cells[0][:70]}")
        elif NOT_A_CLAIM.search(cells[1]):
            fails.append(f"'{cells[0][:50]}' is sourced as '{cells[1][:30]}': a joke or invented line isn't a claim; "
                         "take it out of the Claims table, and if it states a fact about the product, cut it")
    info["claims"] = len(rows)
    if "claims" in secs and not rows and not re.search(r"\bnone\b", " ".join(claims), re.I):
        warns.append("Claims table is empty; list every on-screen claim about the product with its source")

    # Leaks (the Stand-ins section is exempt) and stock phrases
    st = secs.get("stand-ins")
    skip = set()
    if st is not None:
        skip = {st + 1 + k + 1 for k in range(len(section_text(lines, secs, "Stand-ins")))}
    fails += leak_lines("line", lines, skip)
    for i, line in enumerate(lines, 1):
        if re.search(r"\blocalhost\b|127\.0\.0\.1", line, re.I):
            warns.append(f"line {i}: a local address; fine in notes, never on screen")
        low = line.lower()
        for p in STOCK:
            if p in low:
                warns.append(f"line {i}: stock launch phrase '{p}'; use the project's own words")

    # Music
    audio = " ".join(section_text(lines, secs, "Audio"))
    for mp3 in set(re.findall(r"[\w.-]+\.mp3", audio)):
        if "ende-dot-app" in mp3 and not os.path.isfile(os.path.join(SKILL, "assets", "music", mp3)):
            fails.append(f"Audio names {mp3}, which is not a bundled track; run cues.py --list")
    if "ende-dot-app" in audio and "ende.app" not in " ".join(section_text(lines, secs, "Share copy")):
        warns.append("a bundled track is used: share-copy.txt must end with the credit line cues.py prints")
    return fails, warns, info


def main():
    if len(sys.argv) != 2:
        print(__doc__.strip().splitlines()[2])
        print(__doc__.strip().splitlines()[3])
        return 2
    target = sys.argv[1]
    folder = None
    if os.path.isdir(target):
        folder, target = target, os.path.join(target, "brag-plan.md")
    if not os.path.isfile(target):
        print(f"check_plan: no plan at {target}")
        return 2
    fails, warns, info = check_plan(target)
    checked = ["brag-plan.md"]
    if folder:
        for rel in OTHER_FILES:
            p = os.path.join(folder, rel)
            if not os.path.isfile(p):
                if rel != OTHER_FILES[-1]:
                    warns.append(f"{rel} not written yet")
                continue
            with open(p, encoding="utf-8", errors="replace") as f:
                fails += leak_lines(rel, f.read().splitlines())
            checked.append(rel)
        share = os.path.join(folder, "share-copy.txt")
        brief = os.path.join(folder, "composition-brief.md")
        manifest = os.path.join(folder, "composition", "brag.json")
        music_dir = os.path.join(folder, "composition", "assets", "music")
        uses_music = any(os.path.isfile(p) and "ende-dot-app" in open(p, encoding="utf-8", errors="replace").read()
                         for p in (brief, manifest))
        uses_music = uses_music or (os.path.isdir(music_dir) and any("ende-dot-app" in n for n in os.listdir(music_dir)))
        if os.path.isfile(share) and "ende.app" in open(share, encoding="utf-8", errors="replace").read():
            warns = [w for w in warns if "credit line" not in w]
        if uses_music and os.path.isfile(share) and "ende.app" not in open(share, encoding="utf-8", errors="replace").read():
            fails.append("share-copy.txt has no music credit; end it with the line cues.py prints for the track")
    for w in warns:
        print(f"WARN  {w}")
    for f_ in fails:
        print(f"FAIL  {f_}")
    summary = f"{info['scenes']} scenes, {info['total']:g}s, {info['claims']} claim(s); checked {', '.join(checked)}"
    if fails:
        print(f"check_plan: FAIL ({len(fails)} problem(s); {summary})")
        return 1
    print(f"check_plan: PASS ({summary}; {len(warns)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
