#!/usr/bin/env python3
"""Deal art directions from references/directions.json, for a page with no brand to follow.

Usage:
  python3 scripts/deal.py --sector <sector> [--tone <tone>] [--have <assets>] [--avoid <ids>] [--seed N] [--count 3]
      deals --count directions (default 3) that suit the sector, the tone and the assets you have
  python3 scripts/deal.py --direction <id> [--keep palette,type] [--avoid <ids>] [--seed N]
      prints that direction in full, with a type system and a palette dealt to suit it
  python3 scripts/deal.py --list sectors|tones|directions

--have lists the pictures that really exist, comma-separated: photography (the project's own photographs),
product-photo, product-ui (real screenshots), illustration, video. Leave it out when there are none.
--keep palette,type deals neither (the brand supplies them). --avoid skips any direction, type or palette
id, which is how one part is dealt again. The same --seed and arguments always deal the same result.
Without photographs, picture-led directions are left out where enough others remain (architecture and
real-estate have too few, so theirs stay in and are marked "Needs: many pictures").

Prints data only. Standard library only. Exit code 2 on bad arguments.
"""
import json
import pathlib
import random
import sys

LIB = pathlib.Path(__file__).resolve().parent.parent / "references" / "directions.json"
ASSETS = {"photography", "product-photo", "product-ui", "illustration", "video"}


def args_of(argv):
    out, i = {}, 0
    while i < len(argv):
        a = argv[i]
        if not a.startswith("--"):
            print(f"unexpected argument: {a}\n\n{__doc__}", file=sys.stderr)
            sys.exit(2)
        val = argv[i + 1] if i + 1 < len(argv) and not argv[i + 1].startswith("--") else ""
        out[a[2:]] = val
        i += 2 if val else 1
    return out


def ids(v):
    return [x.strip() for x in v.split(",") if x.strip()]


def first(text, n=2):
    parts = text.replace("\n", " ").split(". ")
    return ". ".join(parts[:n]).rstrip(".") + "."


def direction_pool(lib, sector, tone, have, avoid):
    pool = [d for d in lib["directions"] if (sector in d["sectors"] or "*" in d["sectors"]) and d["id"] not in avoid]
    feasible = [d for d in pool if all(n in have for n in d.get("needs", []))]
    pool = feasible or pool
    # Without photographs of its own, a page can't carry a picture-led direction (no stock photos here).
    if not ({"photography", "product-photo"} & have):
        plain = [d for d in pool if not d.get("needsPictures")]
        pool = plain if len(plain) >= 3 else pool
    tone_used = False
    if tone:
        toned = [d for d in pool if tone in d.get("tones", [])]
        tone_used = len(toned) >= 2
        pool = toned if tone_used else pool
    return pool, tone_used


def css_block(p, t, label):
    lines = [f":root {{ /* dealt: {label} */"]
    for k in ("bg", "surface", "ink", "muted", "accent", "accentInk") if p else ():
        lines.append(f"  --deal-{k.replace('accentInk', 'accent-ink')}: {p[k]};")
    for i, f in enumerate(p.get("fields", []) if p else [], 1):
        lines.append(f"  --deal-field{i}-bg: {f['bg']};")
        lines.append(f"  --deal-field{i}-ink: {f['ink']};")
    if t:
        serif = t["class"].startswith(("serif", "slab"))
        fall = "Georgia, serif" if serif else "system-ui, sans-serif"
        text_fall = "Georgia, serif" if t["text"]["family"] == t["display"]["family"] and serif else "system-ui, sans-serif"
        lines.append(f"  --deal-font-display: \"{t['display']['family']}\", {fall};")
        lines.append(f"  --deal-font-text: \"{t['text']['family']}\", {text_fall};")
        for k, v in t.get("scale", {}).items():
            lines.append(f"  --deal-{k}: {v};")
    lines.append("}")
    return "\n".join(lines)


def main():
    a = args_of(sys.argv[1:])
    lib = json.loads(LIB.read_text(encoding="utf-8"))
    sectors = sorted({s for d in lib["directions"] for s in d["sectors"]} - {"*"})
    tones = sorted({t for d in lib["directions"] for t in d.get("tones", [])})
    if "list" in a:
        what = a["list"]
        if what == "sectors":
            print("\n".join(sectors))
        elif what == "tones":
            print("\n".join(tones))
        elif what == "directions":
            for d in lib["directions"]:
                print(f"{d['id']:<24} {d['name']}")
        else:
            print("--list takes sectors, tones or directions", file=sys.stderr)
            sys.exit(2)
        return
    for flag, allowed in (("have", ASSETS), ("keep", {"palette", "type"})):
        bad = set(ids(a.get(flag, ""))) - allowed
        if bad:
            print(f"--{flag}: unknown {', '.join(sorted(bad))}; allowed: {', '.join(sorted(allowed))}", file=sys.stderr)
            sys.exit(2)
    if "seed" in a and not a["seed"].isdigit():
        print("--seed takes a whole number", file=sys.stderr)
        sys.exit(2)
    if "count" in a and not (a["count"].isdigit() and 1 <= int(a["count"]) <= 5):
        print("--count takes a whole number from 1 to 5", file=sys.stderr)
        sys.exit(2)
    seed = int(a["seed"]) if a.get("seed") else random.randrange(1, 2**31)
    rnd = random.Random(seed)
    avoid = set(ids(a.get("avoid", "")))
    have = set(ids(a.get("have", "")))
    if "direction" in a:
        d = next((x for x in lib["directions"] if x["id"] == a["direction"]), None)
        if not d:
            print(f"no direction {a['direction']!r}; see --list directions", file=sys.stderr)
            sys.exit(2)
        keep = set(ids(a.get("keep", "")))
        tpool = [t for t in lib["type"] if t["class"] in d.get("typeClasses", []) and t["id"] not in avoid]
        ppool = [p for p in lib["palettes"] if set(p["tags"]) & set(d.get("paletteTags", [])) and p["id"] not in avoid]
        t = None if "type" in keep else rnd.choice(tpool or [x for x in lib["type"] if x["id"] not in avoid])
        p = None if "palette" in keep else rnd.choice(ppool or [x for x in lib["palettes"] if x["id"] not in avoid])
        print(f"# Direction {d['id']}: {d['name']}  (seed {seed})\n")
        for k in ("idea", "composition", "typography", "colour", "imagery", "richness", "pitfalls"):
            if d.get(k):
                print(f"{k.capitalize()}: {d[k]}\n")
        if t:
            print(f"# Type {t['id']}: {t['name']} ({t['class']})\n")
            print(f"Display: {t['display']['family']} ({t['display']['source']}), {t['display'].get('settings', '')}")
            print(f"Text: {t['text']['family']} ({t['text']['source']}), {t['text'].get('settings', '')}")
            print(f"Note: {t['note']}")
            for link in t.get("links", []):
                print(f"Font stylesheet: {link}")
            print()
        if p:
            print(f"# Palette {p['id']}: {p['name']}\n")
            print(f"Note: {p['note']}\n")
        if p or t:
            label = " ".join(x for x in (d["id"], t and t["id"], p and p["id"], f"seed {seed}") if x)
            print(css_block(p, t, label))
        return
    sector = a.get("sector", "")
    if sector not in sectors:
        print("--sector is required, one of: " + ", ".join(sectors), file=sys.stderr)
        sys.exit(2)
    tone = a.get("tone") or None
    if tone and tone not in tones:
        print("--tone must be one of: " + ", ".join(tones), file=sys.stderr)
        sys.exit(2)
    pool, tone_used = direction_pool(lib, sector, tone, have, avoid)
    if not pool:
        print("no direction left after --avoid", file=sys.stderr)
        sys.exit(2)
    n = int(a.get("count") or 3)
    toned = f", tone {tone}" if tone_used else f" (tone {tone}: too few matches, ignored)" if tone else ""
    print(f"# {min(n, len(pool))} directions for sector {sector}{toned}  (seed {seed})\n")
    for d in rnd.sample(pool, min(n, len(pool))):
        print(f"## {d['id']}: {d['name']}")
        print(f"Idea: {first(d['idea'])}")
        print(f"Composition: {first(d['composition'])}")
        if d.get("needsPictures"):
            print("Needs: many pictures")
        print()


if __name__ == "__main__":
    main()
