#!/usr/bin/env python3
"""Render a light-mode brag composition (index.html + brag.json) to MP4.

Usage:
  python3 render_light.py <composition> --dry-run          check everything, render nothing
  python3 render_light.py <composition> --stills 1.5,3.2   write stills to <output>/work/stills/
  python3 render_light.py <composition> [--out <file>]     render <output>/brag.mp4

<output> is the composition folder's parent. The page must define window.seek(t) and draw each
frame as a pure function of t. Capturing needs Playwright with Chromium; mixing and encoding need
ffmpeg. --dry-run needs neither. Nothing is downloaded or installed by this script.
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys

REMOTE = re.compile(r"""(?:src|href|poster|srcset|data)\s*=\s*["'][^"']*?(?:https?:)?//|url\(\s*["']?(?:https?:)?//|"""
                    r"""@import\s+(?:url\()?\s*["'](?:https?:)?//|(?:fetch|import)\s*\(\s*["'`](?:https?:)?//|new\s+(?:WebSocket|EventSource)\s*\(""", re.I)
ABSOLUTE = re.compile(r"""file://|["'(]\s*/(?:Users|home|private|tmp|var|opt|Volumes|mnt|srv|root)/|["'(]\s*[A-Za-z]:[\\/]""")
REF = re.compile(r"""(?:src|href|poster|data)\s*=\s*["']([^"'#?]+)|url\(\s*["']?([^"')#?]+)|srcset\s*=\s*["']([^"']+)""", re.I)
IMPURE = re.compile(r"setTimeout|setInterval|requestAnimationFrame|Date\.now|performance\.now|new Date\(|Math\.random|"
                    r"animation\s*:|animation-name\s*:|transition\s*:|<video[^>]*autoplay", re.I)
SEEK = re.compile(r"window\.seek\s*=|function\s+seek\s*\(|seek\s*:\s*(async\s*)?\(?", re.I)


def num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def inside(comp, rel):
    if not isinstance(rel, str) or not rel or os.path.isabs(rel) or rel.startswith(("~", "file:")):
        return None
    full = os.path.realpath(os.path.join(comp, rel))
    root = os.path.realpath(comp)
    return full if full.startswith(root + os.sep) else None


def check(comp):
    fails, warns = [], []
    page = os.path.join(comp, "index.html")
    manifest = os.path.join(comp, "brag.json")
    cfg = {}
    if not os.path.isfile(page):
        fails.append("no index.html in the composition folder")
    if not os.path.isfile(manifest):
        fails.append("no brag.json in the composition folder")
    else:
        try:
            with open(manifest, encoding="utf-8") as f:
                cfg = json.load(f)
            if not isinstance(cfg, dict):
                fails.append("brag.json must be a JSON object")
                cfg = {}
        except ValueError as e:
            fails.append(f"brag.json is not valid JSON: {e}")
    for key in ("width", "height"):
        v = cfg.get(key)
        if not (isinstance(v, int) and not isinstance(v, bool) and 16 <= v <= 4096 and v % 2 == 0):
            fails.append(f"brag.json '{key}' must be an even whole number of pixels (got {v!r})")
    fps = cfg.get("fps")
    if not (isinstance(fps, int) and not isinstance(fps, bool) and 1 <= fps <= 60):
        fails.append(f"brag.json 'fps' must be a whole number 1 to 60 (got {fps!r})")
    dur = cfg.get("duration")
    if not num(dur) or dur <= 0:
        fails.append(f"brag.json 'duration' must be a number of seconds (got {dur!r})")
        dur = None
    elif not 15 <= dur <= 25:
        fails.append(f"duration {dur}s is outside 15 to 25 s")
    music = cfg.get("music")
    if music is not None:
        if not isinstance(music, dict):
            fails.append("'music' must be an object or null")
            music = None
        else:
            if not inside(comp, music.get("file")):
                fails.append(f"music file must be a relative path inside the composition (got {music.get('file')!r})")
            elif not os.path.isfile(inside(comp, music["file"])):
                fails.append(f"music file not found: {music['file']} (copy it into the composition first)")
            v = music.get("volume", 0.35)
            if not num(v) or not 0 <= v <= 1:
                fails.append(f"music volume must be 0 to 1 (got {v!r})")
            elif v > 0.5:
                warns.append(f"music volume {v} is above 0.5; beds sit at 0.3 to 0.4")
            for k in ("from", "fade_out"):
                if k in music and (not num(music[k]) or music[k] < 0):
                    fails.append(f"music '{k}' must be a number of seconds, 0 or more")
            if dur and num(music.get("fade_out", 0)) and music.get("fade_out", 0) > dur:
                fails.append("music fade_out is longer than the video")
            full = inside(comp, music.get("file"))
            if full and os.path.isfile(full) and shutil.which("ffprobe") and num(music.get("from", 0)):
                r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", full],
                                   capture_output=True, text=True)
                try:
                    length = float(r.stdout.strip())
                    if music.get("from", 0) >= length:
                        fails.append(f"music 'from' {music['from']}s is past the end of the track ({length:.1f}s)")
                    elif dur and music.get("from", 0) + dur > length:
                        warns.append(f"the track ends {music.get('from', 0) + dur - length:.1f}s before the video does")
                except ValueError:
                    pass
    sfx = cfg.get("sfx", [])
    if not isinstance(sfx, list):
        fails.append("'sfx' must be a list")
        sfx = []
    for i, s in enumerate(sfx, 1):
        if not isinstance(s, dict):
            fails.append(f"sfx {i} must be an object")
            continue
        full = inside(comp, s.get("file"))
        if not full:
            fails.append(f"sfx {i}: file must be a relative path inside the composition (got {s.get('file')!r})")
        elif not os.path.isfile(full):
            fails.append(f"sfx {i}: not found: {s['file']}")
        at = s.get("at")
        if not num(at) or at < 0 or (dur and at >= dur):
            fails.append(f"sfx {i}: 'at' must be a time inside the video (got {at!r})")
        v = s.get("volume", 0.7)
        if not num(v) or not 0 <= v <= 1:
            fails.append(f"sfx {i}: volume must be 0 to 1 (got {v!r})")
    if os.path.isfile(page):
        with open(page, encoding="utf-8", errors="replace") as f:
            html = f.read()
        for i, line in enumerate(html.splitlines(), 1):
            if REMOTE.search(line):
                fails.append(f"index.html:{i}: loads something remote; download it into assets/ (with the user's agreement) and use a relative path")
            if ABSOLUTE.search(line):
                fails.append(f"index.html:{i}: absolute or file:// path; use a path relative to the composition")
            m = IMPURE.search(line)
            if m:
                warns.append(f"index.html:{i}: '{m.group(0)}' can make frames depend on wall-clock time; draw from t only")
        if not SEEK.search(html):
            warns.append("index.html: no 'window.seek =' found; the render needs window.seek(t) to exist")
        for m in REF.finditer(html):
            refs = [m.group(1) or m.group(2)] if not m.group(3) else [p.strip().split()[0] for p in m.group(3).split(",") if p.strip()]
            for ref in refs:
                if not ref or re.match(r"^(?:[a-z]+:|//)", ref, re.I):
                    continue
                full = os.path.realpath(os.path.join(comp, ref))
                if not full.startswith(os.path.realpath(comp) + os.sep):
                    fails.append(f"index.html refers to '{ref}', outside the composition; copy it into assets/ and use that path")
    return cfg, fails, warns


def ffmpeg_cmd(comp, cfg, frames_dir, out):
    fps, dur = cfg["fps"], float(cfg["duration"])
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", os.path.join(frames_dir, "f_%05d.png")]
    chains, labels, idx = [], [], 1
    music = cfg.get("music")
    if music:
        cmd += ["-ss", str(music.get("from", 0)), "-i", inside(comp, music["file"])]
        fade = float(music.get("fade_out", 1.5))
        chain = f"[{idx}:a]atrim=0:{dur},asetpts=PTS-STARTPTS,volume={music.get('volume', 0.35)}"
        if fade > 0:
            chain += f",afade=t=out:st={max(0.0, dur - fade):.3f}:d={fade}"
        chains.append(chain + "[m]")
        labels.append("[m]")
        idx += 1
    for k, s in enumerate(cfg.get("sfx", []), 1):
        cmd += ["-i", inside(comp, s["file"])]
        ms = int(round(float(s["at"]) * 1000))
        chains.append(f"[{idx}:a]adelay={ms}:all=1,volume={s.get('volume', 0.7)}[s{k}]")
        labels.append(f"[s{k}]")
        idx += 1
    if labels:
        chains.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=longest,"
                      f"alimiter=limit=0.95,atrim=0:{dur}[a]")
        cmd += ["-filter_complex", ";".join(chains), "-map", "0:v", "-map", "[a]", "-c:a", "aac", "-b:a", "192k"]
    else:
        cmd += ["-map", "0:v"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium", "-r", str(fps),
            "-t", f"{dur}", "-movflags", "+faststart", out]
    return cmd


def launch(p):
    try:
        return p.chromium.launch(headless=True)
    except Exception as first:  # sandboxed machines refuse Chromium's default process model
        try:
            return p.chromium.launch(headless=True, args=["--single-process", "--no-zygote"])
        except Exception:
            raise first


def capture(comp, cfg, times, pattern):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("render_light: Playwright is not installed for this Python. With the user's agreement, run:\n"
              f"  uv run --with playwright python {os.path.abspath(__file__)} {comp}\n"
              "Never turn off a sandbox to start the browser.")
        sys.exit(3)
    url = "file://" + os.path.join(os.path.realpath(comp), "index.html")
    with sync_playwright() as p:
        try:
            browser = launch(p)
        except Exception as e:
            print(f"render_light: Chromium did not start: {str(e).splitlines()[0]}\n"
                  "If the browser is missing, ask the user before running: playwright install chromium")
            sys.exit(3)
        page = browser.new_page(viewport={"width": cfg["width"], "height": cfg["height"]}, device_scale_factor=1)
        page.goto(url, wait_until="load")
        try:
            page.wait_for_function("typeof window.seek === 'function'", timeout=10000)
        except Exception:
            browser.close()
            print("render_light: the page never defined window.seek(t)")
            sys.exit(1)
        page.evaluate("""async () => { await document.fonts.ready;
          await Promise.all([...document.images].map(i => i.complete ? 1 : new Promise(r => { i.onload = i.onerror = r; }))); }""")
        for n, t in enumerate(times):
            try:
                page.evaluate("async t => { await window.seek(t); await document.fonts.ready; }", t)
            except Exception as e:
                browser.close()
                print(f"render_light: window.seek({t:.3f}) failed: {str(e).splitlines()[0][:300]}")
                sys.exit(1)
            page.screenshot(path=pattern(n, t), type="png")
            if n and n % 60 == 0:
                print(f"  {n}/{len(times)} frames", flush=True)
        browser.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("composition")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--stills", help="comma-separated times in seconds")
    ap.add_argument("--out")
    a = ap.parse_args()
    comp = os.path.abspath(a.composition)
    if not os.path.isdir(comp):
        print(f"render_light: not a folder: {a.composition}")
        return 2
    output = os.path.dirname(comp)
    cfg, fails, warns = check(comp)
    for w in warns:
        print(f"WARN  {w}")
    for f in fails:
        print(f"FAIL  {f}")
    if fails:
        print(f"render_light: FAIL ({len(fails)} problem(s)); nothing rendered")
        return 1
    frames_dir = os.path.join(output, "work", "frames")
    out = os.path.abspath(a.out) if a.out else os.path.join(output, "brag.mp4")
    n = int(round(float(cfg["duration"]) * cfg["fps"]))
    if a.dry_run:
        print(f"render_light: OK. {cfg['width']}x{cfg['height']} at {cfg['fps']} fps, {cfg['duration']}s = {n} frames, "
              f"{'music' if cfg.get('music') else 'no music'}, {len(cfg.get('sfx', []))} effect(s)")
        print("Would run after capturing frames to work/frames/:")
        print("  " + " ".join(c if re.match(r"^[\w@%+=:,./-]+$", c) else "'" + c + "'" for c in ffmpeg_cmd(comp, cfg, frames_dir, out)))
        print(f"Tools: ffmpeg {'found' if shutil.which('ffmpeg') else 'MISSING'}, "
              f"ffprobe {'found' if shutil.which('ffprobe') else 'MISSING'}")
        return 0
    if a.stills:
        try:
            times = [float(x) for x in a.stills.split(",") if x.strip()]
        except ValueError:
            print("render_light: --stills takes times in seconds, e.g. 1.5,3.2")
            return 2
        bad = [t for t in times if not 0 <= t < float(cfg["duration"])]
        if bad:
            print(f"render_light: still times outside the video: {bad}")
            return 2
        sdir = os.path.join(output, "work", "stills")
        os.makedirs(sdir, exist_ok=True)
        capture(comp, cfg, times, lambda i, t: os.path.join(sdir, f"still_{t:06.2f}s.png"))
        print(f"render_light: {len(times)} still(s) in {sdir}")
        return 0
    if not shutil.which("ffmpeg"):
        print("render_light: ffmpeg is missing; ask the user to install it, then rerun")
        return 3
    os.makedirs(frames_dir, exist_ok=True)
    for old in glob.glob(os.path.join(frames_dir, "f_*.png")):
        os.remove(old)
    print(f"render_light: capturing {n} frames")
    capture(comp, cfg, [i / cfg["fps"] for i in range(n)], lambda i, t: os.path.join(frames_dir, f"f_{i:05d}.png"))
    r = subprocess.run(ffmpeg_cmd(comp, cfg, frames_dir, out), capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        print("render_light: ffmpeg failed:\n" + r.stderr[-2000:])
        return 1
    print(f"render_light: wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
