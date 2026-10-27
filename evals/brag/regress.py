#!/usr/bin/env python3
"""Regression checks for brag's helper scripts, on made-up DEMO inputs. Standard library only.

Usage: python3 evals/brag/regress.py   (from the repo root; needs ffmpeg for the poster cases)
Prints one line per case and a tally; exit 1 if any case behaves unexpectedly.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(ROOT, "skills", "brag", "scripts")
FILES = os.path.join(ROOT, "evals", "brag", "files")
results = []
# Made-up key-shaped test values, assembled at run time so no secret-shaped literal is committed.
FAKE_LIVE_KEY = "sk_" + "live_" + "DEMO" + "0" * 16
FAKE_TOKEN_LINE = "export TO" + "KEN=" + "abc123" + "def456"


def run(script, *args):
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS, script), *args], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def case(name, ok, detail=""):
    results.append(ok)
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f"  ({detail})" if not ok and detail else ""))


GOOD_PLAN = """# Brag plan: Demo
## What it is
A demo.
## Angle
x
## Hook
x
## Tone
Preset: default
## Format
landscape 1920x1080, 30 fps
## Duration
18
## Visual identity
- Background: #ffffff
## Audio
Music: none (demo)
## Storyboard
### Scene 1: Hook (3s)
On screen: "Cook what you already have."
### Scene 2: Flow (8s)
On screen: "Tell us what's in the cupboard."
### Scene 3: Name (7s)
On screen: "Pantry Pal"
## Claims
| On screen | Source |
| :--- | :--- |
| "Cook what you already have." | index.html h1 |
## Share copy
Demo.
"""


def plan_case(name, text, want_rc, want=None):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "brag-plan.md")
        with open(p, "w") as f:
            f.write(text)
        rc, out = run("check_plan.py", p)
    ok = rc == want_rc and (want is None or want in out)
    case(name, ok, out.strip().splitlines()[-1] if out.strip() else "no output")


def main():
    # scan_project
    rc, out = run("scan_project.py", os.path.join(FILES, "pantry-pal"))
    read = out.split("SKIPPED")[0]
    case("scan: secrets file skipped, never listed to read", rc == 0 and "secrets.local.json  [name" in out and "secrets.local.json" not in read)
    case("scan: customer data folder skipped", "data/  [data folder" in out and "customers.csv" not in out)
    case("scan: index.html read first", read.split("READ, in this order:")[1].split()[0] == "index.html")
    case("scan: internal hostname warned", "internal hostname" in out and "pantrypal.internal" not in out)
    case("scan: colours found", "--tomato: #e4572e" in out)
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, ".env"), "w").write("KEY=DEMO\n")
        open(os.path.join(d, "tokens.css"), "w").write(":root { --brand: #123456; }\n")
        open(os.path.join(d, "id_ed25519"), "w").write("DEMO\n")
        os.makedirs(os.path.join(d, "node_modules", "x"))
        open(os.path.join(d, "node_modules", "x", "index.html"), "w").write("<h1>dep</h1>")
        rc, out = run("scan_project.py", d)
        read = out.split("SKIPPED")[0]
        case("scan: .env and ssh key skipped; design tokens file still read",
             ".env  [" in out and "id_ed25519  [" in out and "tokens.css" in read)
        case("scan: node_modules not walked", "node_modules/  [" in out and "node_modules/x" not in read)
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "config"))
        os.makedirs(os.path.join(d, "seed"))
        os.makedirs(os.path.join(d, "src", "pages"))
        open(os.path.join(d, "index.html"), "w").write("<h1>Demo</h1>\n")
        open(os.path.join(d, "config", "settings.yaml"), "w").write("db: postgres://admin:DemoPass99@db.demo.example/app\n")
        open(os.path.join(d, "docker-compose.yml"), "w").write("POSTGRES_PASSWORD: demodemodemo123\n")
        open(os.path.join(d, "seed", "users.json"), "w").write('[{"email": "demo@gmail.com"}]\n')
        open(os.path.join(d, "notes.txt"), "w").write("stripe " + FAKE_LIVE_KEY + "\n")
        open(os.path.join(d, "src", "pages", "password-reset.jsx"), "w").write("export default () => <h1>Reset</h1>;\n")
        open(os.path.join(d, "src", "app.js"), "w").write("const apiKey = process.env.API_KEY;\n")
        rc, out = run("scan_project.py", d)
        read = out.split("SKIPPED")[0]
        case("scan: yaml config, docker-compose and seed data skipped",
             all(x not in read for x in ("settings.yaml", "docker-compose", "users.json")) and "seed/  [" in out)
        case("scan: file with a live-key line moved to skipped", "notes.txt" not in read and "notes.txt  [has a key" in out)
        case("scan: password-reset.jsx (UI) still read; process.env read not flagged",
             "password-reset.jsx" in read and "src/app.js" in read)
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "src", "components"))
        open(os.path.join(d, "index.html"), "w").write("<h1>Demo</h1>\n")
        open(os.path.join(d, "README.md"), "w").write("Setup: export API_KEY=your-api-key-here\nDemo: " + FAKE_TOKEN_LINE + "\n")
        open(os.path.join(d, "src", "components", "LoginForm.jsx"), "w").write(
            "<label>Password:</label>\n<input type='password' value={password} />\nconst token = request.headers.authorization;\n")
        rc, out = run("scan_project.py", d)
        read = out.split("SKIPPED")[0]
        case("scan: login form UI with a Password label still read", "LoginForm.jsx" in read)
        case("scan: README with a key-like line warned, not dropped", "README.md" in read and "README.md:2: looks like a key" in out)
    with tempfile.TemporaryDirectory() as d:
        rc, out = run("scan_project.py", d)
        case("scan: empty folder says nothing to read", rc == 1 and "nothing brag can read" in out)

    # check_plan
    plan_case("plan: good plan passes", GOOD_PLAN, 0, "PASS")
    plan_case("plan: total under 15 s fails", GOOD_PLAN.replace("(8s)", "(2s)"), 1, "must add up to 15 to 25")
    plan_case("plan: too much text for the scene fails",
              GOOD_PLAN.replace('On screen: "Cook what you already have."', 'On screen: "Cook what you already have." "Tell us what is in the cupboard tonight."'), 1, "reading")
    plan_case("plan: claim without source fails", GOOD_PLAN.replace("| index.html h1 |", "| TBD |"), 1, "without a source")
    plan_case("plan: email address fails", GOOD_PLAN.replace("A demo.", "Contact ada.demo@gmail.com"), 1, "email")
    plan_case("plan: image@2x filename is not an email", GOOD_PLAN.replace("A demo.", "logo@2x.png"), 0, "PASS")
    plan_case("plan: internal hostname fails", GOOD_PLAN.replace("A demo.", "api.pantrypal.internal"), 1, "internal hostname")
    plan_case("plan: missing section fails", GOOD_PLAN.replace("## Claims", "## Sources"), 1, "missing section")
    plan_case("plan: scene without length fails", GOOD_PLAN.replace("### Scene 2: Flow (8s)", "### Scene 2: Flow"), 1, "not in the form")
    plan_case("plan: unknown bundled track fails",
              GOOD_PLAN.replace("Music: none (demo)", "Music: happy-beats-business-moves-vol-99-by-ende-dot-app.mp3"), 1, "not a bundled track")
    plan_case("plan: stock phrase warns", GOOD_PLAN.replace("Demo.\n", "Excited to share this.\n"), 0, "stock launch phrase")
    plan_case("plan: live payment key fails", GOOD_PLAN.replace("A demo.", "key " + FAKE_LIVE_KEY), 1, "key, token")
    plan_case("plan: JWT fails", GOOD_PLAN.replace("A demo.", "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJkZW1vIn0.x"), 1, "key, token")
    plan_case("plan: stand-in email under Stand-ins passes",
              GOOD_PLAN.replace("## Share copy", "## Stand-ins\nShows sam.demo@gmail.com in place of the real user\n## Share copy"), 0, "PASS")
    plan_case("plan: example.com email passes anywhere", GOOD_PLAN.replace("A demo.", "Login shows sam@example.com"), 0, "PASS")
    plan_case("plan: mentioning secrets.local.json is not a hostname", GOOD_PLAN.replace("A demo.", "Skipped secrets.local.json"), 0, "PASS")
    plan_case("plan: joke in the claims table fails",
              GOOD_PLAN.replace("| index.html h1 |", "| my joke |"), 1, "isn't a claim")
    plan_case("plan: scenes outside Storyboard not counted",
              GOOD_PLAN.replace("## Hook\nx", "## Hook\n### Scene 9: Extra (9s)\nx"), 0, "3 scenes, 18s")
    plan_case("plan: bold On screen label is read",
              GOOD_PLAN.replace('On screen: "Cook what you already have."', '**On screen:** "Cook what you already have, every single night of the week."'), 1, "reading")
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "brag-plan.md"), "w").write(GOOD_PLAN)
        open(os.path.join(d, "composition-brief.md"), "w").write("- Project: /Users/demo-person/work/pantry-pal\n- Music: assets/music/happy-beats-business-moves-vol-12-by-ende-dot-app.mp3\n")
        open(os.path.join(d, "share-copy.txt"), "w").write("Pantry Pal. Dinner from the cupboard.\n")
        rc, out = run("check_plan.py", d)
        case("folder: machine path in the brief fails", rc == 1 and "composition-brief.md:1" in out and "path on this machine" in out)
        case("folder: caption without music credit fails", "no music credit" in out)
    plan_case("plan: quoted password with symbols fails", GOOD_PLAN.replace("A demo.", 'password = "P@ssw0rd!2024"'), 1, "key, token")
    plan_case("plan: quoted passphrase without digits fails", GOOD_PLAN.replace("A demo.", 'password: "correcthorsebatterystaple"'), 1, "key, token")
    plan_case("plan: quoted placeholder text is not a secret", GOOD_PLAN.replace("A demo.", 'password: "Your password here"'), 0, "PASS")
    plan_case("plan: a 'Password:' label in a scene is not a secret",
              GOOD_PLAN.replace("A demo.", "Shows the login form, Password: required"), 0, "PASS")
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "composition"))
        open(os.path.join(d, "brag-plan.md"), "w").write(GOOD_PLAN)
        open(os.path.join(d, "composition-brief.md"), "w").write("- Project: pantry-pal\n- Music: vol-9\n")
        open(os.path.join(d, "composition", "brag.json"), "w").write('{"music": {"file": "assets/music/happy-beats-business-moves-vol-9-by-ende-dot-app.mp3"}}')
        open(os.path.join(d, "share-copy.txt"), "w").write("Pantry Pal.\n")
        rc, out = run("check_plan.py", d)
        case("folder: missing credit caught from brag.json when the brief names no file", rc == 1 and "no music credit" in out)
    rc, out = run("check_plan.py", "/nonexistent/brag-plan.md")
    case("plan: missing file exits 2", rc == 2)

    # render_light --dry-run
    music = "happy-beats-business-moves-vol-12-by-ende-dot-app.mp3"
    page = "<html><body><script>window.seek = (t) => { document.body.dataset.t = t; };</script></body></html>"

    def comp(manifest, html=page, copy_music=True):
        d = tempfile.mkdtemp()
        c = os.path.join(d, "composition")
        os.makedirs(os.path.join(c, "assets", "music"))
        if copy_music:
            shutil.copy(os.path.join(ROOT, "skills", "brag", "assets", "music", music), os.path.join(c, "assets", "music"))
        open(os.path.join(c, "index.html"), "w").write(html)
        open(os.path.join(c, "brag.json"), "w").write(manifest if isinstance(manifest, str) else json.dumps(manifest))
        return d, c

    base = {"width": 1080, "height": 1920, "fps": 30, "duration": 18,
            "music": {"file": f"assets/music/{music}", "volume": 0.3, "fade_out": 1.5}, "sfx": []}
    for name, m, html, want_rc, want in [
        ("dry-run: good composition passes", base, page, 0, "540 frames"),
        ("dry-run: odd width fails", {**base, "width": 1081}, page, 1, "even"),
        ("dry-run: 30 s fails", {**base, "duration": 30}, page, 1, "outside 15 to 25"),
        ("dry-run: music outside composition fails", {**base, "music": {"file": "../../etc/passwd"}}, page, 1, "inside the composition"),
        ("dry-run: absolute music path fails", {**base, "music": {"file": "/tmp/x.mp3"}}, page, 1, "relative path"),
        ("dry-run: effect after the end fails", {**base, "sfx": [{"file": f"assets/music/{music}", "at": 19}]}, page, 1, "inside the video"),
        ("dry-run: remote font fails", base, page.replace("<body>", '<head><link href="https://fonts.example.com/x.css" rel="stylesheet"></head><body>'), 1, "remote"),
        ("dry-run: no seek warns (the render itself stops)", base, "<html><body>static</body></html>", 0, "window.seek"),
        ("dry-run: setInterval warns", base, page.replace("</script>", "setInterval(()=>{},1000);</script>"), 0, "wall-clock"),
        ("dry-run: bad JSON fails", "{not json", page, 1, "not valid JSON"),
        ("dry-run: ../ reference escaping the composition fails", base, page.replace("<body>", '<body><img src="../../outside.png">'), 1, "outside the composition"),
        ("dry-run: remote fetch fails", base, page.replace("</script>", "fetch('https://api.demo.example/x');</script>"), 1, "remote"),
        ("dry-run: music start past the end of the track fails", {**base, "music": {"file": f"assets/music/{music}", "from": 500}}, page, 1, "past the end"),
        ("dry-run: string volume fails", {**base, "music": {"file": f"assets/music/{music}", "volume": "loud"}}, page, 1, "volume"),
    ]:
        d, c = comp(m, html)
        rc, out = run("render_light.py", c, "--dry-run")
        shutil.rmtree(d)
        case(name, rc == want_rc and want in out, out.strip().splitlines()[-1] if out.strip() else "no output")

    # cues
    rc, out = run("cues.py", "--list")
    case("cues: lists five tracks", rc == 0 and out.count("ende-dot-app.mp3") == 5)
    rc, out = run("cues.py", "vol-1", "--until", "20")
    case("cues: vol-1 resolves to one track", rc == 0 and "vol-1-by" in out and "Strong cues" in out)
    rc, out = run("cues.py", "12")
    case("cues: a volume number past the list resolves by name", rc == 0 and "vol-12-by" in out)
    rc, out = run("cues.py", "0")
    case("cues: track 0 is not a track", rc == 1)
    rc, out = run("cues.py", "1", "--until", "-5")
    case("cues: negative length refused", rc == 2)
    rc, out = run("cues.py", "nope")
    case("cues: unknown track exits 1", rc == 1)

    # poster (needs ffmpeg)
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        d = tempfile.mkdtemp()
        subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=size=320x240:rate=30:duration=16",
                        "-f", "lavfi", "-i", "sine=frequency=440:duration=16", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-shortest", os.path.join(d, "brag.mp4")], check=True)
        rc, out = run("poster.py", d, "5")
        case("poster: bakes frame 0, keeps frames and audio", rc == 0 and "480 frames" in out and "audio kept" in out and os.path.isfile(os.path.join(d, "brag.jpg")))
        rc, out = run("poster.py", d, "15.99")
        case("poster: time inside the last frames refused", rc == 2 and "last frames" in out)
        rc, out = run("poster.py", d, "99")
        case("poster: time past the end refused", rc == 2 and "outside the video" in out)
        shutil.rmtree(d)
    else:
        print("skip poster cases: ffmpeg or ffprobe missing")

    print(f"{sum(results)} of {len(results)} regression cases behaved as expected")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
