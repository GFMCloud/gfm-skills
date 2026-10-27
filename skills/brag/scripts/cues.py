#!/usr/bin/env python3
"""List brag's bundled music, or print one track's beats and strong cues inside a time window.

Usage:
  python3 cues.py --list
  python3 cues.py <track number | part of its name> [--from 0] [--until 22]

Standard library only. Reads assets/music/cues/*.music-cues.json beside this script's skill.
"""
import argparse
import glob
import json
import os
import sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MUSIC = os.path.join(SKILL, "assets", "music")
FEEL = {
    "vol-1": "the most energetic; full upbeat track (default, app-store)",
    "vol-9": "mid energy, a little laid back (default, yc-parody)",
    "vol-10": "short punchy loop (default, chaotic)",
    "vol-11": "warm and businesslike (yc-parody, app-store)",
    "vol-12": "steady and clean; quiet enough for deadpan at low volume (polished, cinematic, deadpan)",
}


def tracks():
    out = []
    for mp3 in sorted(glob.glob(os.path.join(MUSIC, "*.mp3")),
                      key=lambda p: int("".join(c for c in os.path.basename(p).split("vol-")[-1].split("-")[0] if c.isdigit()) or 0)):
        stem = os.path.splitext(os.path.basename(mp3))[0]
        cue = os.path.join(MUSIC, "cues", stem + ".music-cues.json")
        data = None
        if os.path.isfile(cue):
            try:
                with open(cue, encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, ValueError):
                data = None
        out.append((stem, mp3, data))
    return out


def credit(stem):
    vol = stem.split("vol-")[-1].split("-")[0] if "vol-" in stem else "?"
    return f'Music: "Happy Beats / Business Moves vol. {vol}" by ende.app (CC BY 4.0)'


def feel(stem):
    for k, v in FEEL.items():
        if f"{k}-" in stem + "-":
            return v
    return ""


def pick(arg, all_tracks):
    if arg.isdigit() and 1 <= int(arg) <= len(all_tracks):
        return all_tracks[int(arg) - 1]
    if arg.isdigit():
        arg = f"vol-{int(arg)}"
    hits = [t for t in all_tracks if arg.lower() in t[0].lower()]
    if len(hits) == 1:
        return hits[0]
    exact = [t for t in all_tracks if t[0].lower().endswith(arg.lower()) or f"{arg.lower()}-" in t[0].lower()]
    return exact[0] if len(exact) == 1 else None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("track", nargs="?")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--from", dest="start", type=float, default=0.0, help="where in the track the video starts")
    ap.add_argument("--until", type=float, default=25.0, help="video length in seconds")
    a = ap.parse_args()
    if a.until <= 0 or a.start < 0:
        print("cues: --until must be above 0 and --from 0 or more")
        return 2
    all_tracks = tracks()
    if not all_tracks:
        print("cues: no bundled music found in assets/music")
        return 1
    if a.list or not a.track:
        print("Bundled music (CC BY 4.0; cues.py <n> prints the credit line to use):")
        for i, (stem, mp3, data) in enumerate(all_tracks, 1):
            dur = f"{data['duration']:.0f}s" if data else "?"
            tempo = f"{data['tempo']:.0f} BPM" if data else "no cue file"
            print(f"  {i}. {os.path.basename(mp3)}  {dur}, {tempo}; {feel(stem)}")
        print("Next: python3 cues.py <number> --until <video seconds>")
        return 0
    t = pick(a.track, all_tracks)
    if not t:
        print(f"cues: no single track matches '{a.track}'; run with --list")
        return 1
    stem, mp3, data = t
    if not data:
        print(f"cues: {stem} has no cue file; time it by ear")
        return 1
    lo, hi = a.start, a.start + a.until
    win = data.get("analysis", {}).get("windowEnd")
    beats = [b for b in data.get("beats", []) if lo <= b["time"] <= hi]
    strong = [c for c in data.get("strongCues", []) if lo <= c["time"] <= hi]
    strong = sorted(sorted(strong, key=lambda c: -c["intensity"])[:6], key=lambda c: c["time"])
    print(f"Track: {os.path.basename(mp3)}")
    print(f"Credit line for share-copy.txt: {credit(stem)}")
    print(f"Tempo: {data['tempo']:.1f} BPM, beat every {60 / data['tempo']:.2f}s; track length {data['duration']:.1f}s")
    print(f"Window: track {lo:.2f}s to {hi:.2f}s (video 0 to {a.until:.2f}s)")
    if win is not None and hi > win:
        print(f"Note: the cue file covers the track only up to {win:.0f}s; later times have no cues.")
    if beats:
        first = beats[0]["time"] - lo
        print(f"First beat in window at video {first:.2f}s (nothing analysed before it may be a quiet intro).")
    print("Strong cues (video time, intensity): " + (", ".join(f"{c['time'] - lo:.2f}s ({c['intensity']:.2f})" for c in strong) or "none in window"))
    print("Beats (video time): " + (", ".join(f"{b['time'] - lo:.2f}" for b in beats) or "none in window"))
    if beats and 60 / data["tempo"] < 0.6:
        print("Beats are under 0.6s apart: too fast for one readable line per beat; use every other beat for text.")
    print("Aim one to three major moments at strong cues (within about 0.15s); let cues go when they hurt reading time.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
