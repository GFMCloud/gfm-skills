#!/usr/bin/env python3
"""Pick a poster frame for a brag video and bake it in as frame 0.

Usage: python3 poster.py <output-folder> <seconds>

Writes <output>/brag.jpg from the frame at <seconds>, then replaces frame 0 of <output>/brag.mp4
with it, so thumbnails everywhere show the poster. Keeps the length, frame count and audio, checks
them afterwards, and leaves brag.mp4 untouched if anything differs. Needs ffmpeg and ffprobe.
"""
import json
import os
import shutil
import subprocess
import sys


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-show_entries",
                        "format=duration:stream=codec_type,nb_read_packets,width,height,r_frame_rate", "-of", "json", path],
                       capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        return None
    d = json.loads(r.stdout or "{}")
    v = [s for s in d.get("streams", []) if s.get("codec_type") == "video"]
    a = [s for s in d.get("streams", []) if s.get("codec_type") == "audio"]
    if not v:
        return None
    num, _, den = str(v[0].get("r_frame_rate", "30/1")).partition("/")
    try:
        fps = float(num) / float(den or 1)
    except (ValueError, ZeroDivisionError):
        fps = 30.0
    return {"duration": float(d.get("format", {}).get("duration", 0)), "frames": int(v[0].get("nb_read_packets", 0)), "fps": fps or 30.0,
            "audio": bool(a), "size": (v[0].get("width"), v[0].get("height"))}


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        print("poster: ffmpeg failed:\n" + r.stderr[-1500:])
        sys.exit(1)


def main():
    if len(sys.argv) != 3:
        print(__doc__.strip().splitlines()[2])
        return 2
    out, t = sys.argv[1], sys.argv[2]
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            print(f"poster: {tool} is missing")
            return 3
    video = os.path.join(out, "brag.mp4")
    if not os.path.isfile(video):
        print(f"poster: no brag.mp4 in {out}")
        return 2
    try:
        t = float(t)
    except ValueError:
        print("poster: seconds must be a number, e.g. 3.2")
        return 2
    before = probe(video)
    if not before:
        print("poster: brag.mp4 has no readable video stream")
        return 1
    if not 0 < t < before["duration"]:
        print(f"poster: {t}s is outside the video (0 to {before['duration']:.2f}s)")
        return 2
    margin = max(0.1, 1.5 / before["fps"])
    if t > before["duration"] - margin:
        print(f"poster: {t}s is in the last frames; pick a settled moment at least {margin:.2f} s before the end")
        return 2
    jpg = os.path.join(out, "brag.jpg")
    run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t}", "-i", video, "-frames:v", "1", "-q:v", "2", jpg])
    tmp = os.path.join(out, "brag.poster.mp4")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", jpg, "-filter_complex",
         "[0:v][1:v]overlay=0:0:enable='eq(n,0)'[v]", "-map", "[v]", "-map", "0:a?", "-c:v", "libx264",
         "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", tmp])
    after = probe(tmp)
    problems = []
    if not after:
        problems.append("the new file has no readable video stream")
    else:
        if after["frames"] != before["frames"]:
            problems.append(f"frame count changed {before['frames']} -> {after['frames']}")
        if abs(after["duration"] - before["duration"]) > 0.05:
            problems.append(f"length changed {before['duration']:.3f}s -> {after['duration']:.3f}s")
        if after["audio"] != before["audio"]:
            problems.append("audio stream lost")
    if problems:
        os.remove(tmp)
        print("poster: brag.mp4 left as it was: " + "; ".join(problems))
        return 1
    os.replace(tmp, video)
    print(f"poster: brag.jpg from {t}s, baked in as frame 0; {after['frames']} frames, "
          f"{after['duration']:.2f}s, audio {'kept' if after['audio'] else 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
