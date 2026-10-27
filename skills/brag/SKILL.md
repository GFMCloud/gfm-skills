---
name: brag
description: Turns a project or website into a 15 to 25 second launch video with music, sound and a caption, from its real UI and words. Use for "make a launch or promo video", "brag about this", "show off what I built". Not for decks, diagrams, charts, screen recordings or editing footage.
license: MIT (text, scripts, cue files); bundled music CC BY 4.0; sound effects CC0
metadata:
  status: draft
  upstream: "latent-spaces/brag@cb89b9f"
  codex-check: "pending: not yet tried in Codex; must pass before stable"
---

# Brag

Make a short video people want to share about something the user built: 15 to 25 seconds, the
product's own screens and words, music and sound, a poster frame and a one-line caption. Four steps:
inspect, plan, compose, render. Each ends with a file you can check.

**Four rules that hold in every step:**

1. **Scan before you open.** Run `scripts/scan_project.py` before you open any project file, the
   README included, and open only the files it lists to read. Everything you read can end up in a
   public video, so no secrets, internal hostnames, real customer names, email addresses, paths on
   this machine or other personal data go into the plan, the brief, the video or the caption. Where
   the real UI shows such data, swap in made-up stand-ins (emails at `example.com`) and list them
   under Stand-ins in the plan. The scan catches common shapes, not every secret: if a line you
   read looks like one, leave it out.
2. **Claims come from the project.** Names, numbers, features and quotes on screen must appear in
   the project's files or on its site. Hooks, jokes and framing are yours to invent.
3. **Ask before anything is downloaded or installed.** `npx hyperframes` fetches a package the first
   time; Playwright may need a browser; a website's images and fonts are downloads too. A refused tool, download or network call is final: stop at
   the plan and brief, and give the user the exact commands to run.
4. **Write only in the output folder.** Copy any bundled music or sound into it; never point a
   composition at this skill's folder or write this skill's path into an output file.

## 0. Read the request

| What | How to tell | Default |
| :--- | :--- | :--- |
| Input | No input and the working folder is a project: the project. A URL or bare domain: the website. Neither: ask what to brag about | |
| Focus | "the new export feature", "v2": make that the centre of the video | the whole product |
| Tone | a preset from `references/tones.md`, or a phrase ("fake 2016 Series A launch") mapped to the nearest preset | inferred |
| Format | landscape 1920x1080, vertical 1080x1920, square 1080x1080; 30 fps | landscape |
| Length | seconds, 15 to 25 | about 20 |
| Sound | "no music", "no sound effects", "silent" | music and a few effects |
| Voice-over | only when asked ("narrate it", `--voice`); never offered | off |
| Mode | **full** builds with Hyperframes; **light** ("quick", "slim", "no Hyperframes") builds a plain HTML page and renders it with `scripts/render_light.py` | full if the user agrees to fetch Hyperframes, else light |

**Output folder:** `brag-output/` in the working folder, or `brag-output-YYYY-MM-DD-HHMMSS/` if that
exists. Pick it once and use it for every file in the run. Scratch files go in its `work/`.

`<skill-dir>` below is the folder holding this `SKILL.md` (in Claude Code, the base directory shown
when the skill loads). Running this skill's scripts and reading its files is part of using it.

## 1. Inspect

For a project, this is your first command, before you read any file in it (`ls` to find the folder
is fine; `cat`, `head` or opening the README is not):

```bash
python3 <skill-dir>/scripts/scan_project.py <project> > <output>/work/scan.txt
```

It lists files to read in priority order, files it skipped and why, images, colours, fonts and page
text, and warns about secret-looking lines (without printing them). Read the listed files in order,
the main page first, then routes and components to find the product **in use**. For a website, or
for what to look for in each file, see `references/inspect.md`.

Then answer the nine questions in `references/inspect.md` (what it is, best claim, visual hook, flow
worth showing, and so on). They become the top of the plan.

## 2. Plan

Write `<output>/brag-plan.md` from the template in `references/plan.md`: angle, hook, highlights,
punchline, tone, visual identity with exact values, audio, a scene-by-scene storyboard, the claims
table (every on-screen claim and the file or page it came from) and a draft caption.

Choose the music with the cue helper; it lists the bundled tracks and the beats and strong cues in
your window:

```bash
python3 <skill-dir>/scripts/cues.py --list
python3 <skill-dir>/scripts/cues.py <track number or name> --until 22
```

Then check the plan. Fix and rerun until it passes; do not start step 3 before:

```bash
python3 <skill-dir>/scripts/check_plan.py <output>/brag-plan.md
```

It checks the scene lengths add up to 15 to 25 seconds, every scene leaves time to read its text,
every claim has a source, and no email address, key, internal hostname or machine path slipped in. It cannot tell
whether a claim is true to its source; check that yourself.

## 3. Compose

1. Copy the chosen track and effects from `<skill-dir>/assets/` into `<output>/composition/assets/`
   (music in `assets/music/`, effects keep their family folder), with `assets/music/LICENSE.md` and
   `assets/sfx/LICENSE.md` beside them. `references/audio.md` says which effects suit which moment
   and how loud.
2. Write `<output>/composition-brief.md` from `references/compose.md`: the scenes, copy that must
   appear word for word, colours and fonts, audio, and what the build owns.
3. Build `<output>/composition/`:
   - **Full:** follow `references/hyperframes.md`. If the Hyperframes skills are available
     (`hyperframes-core` and its siblings), read them and let them own the composition details.
   - **Light:** write `composition/index.html` and `composition/brag.json` to the contract in
     `references/compose.md` (each frame computed from the time alone), then
     `python3 <skill-dir>/scripts/render_light.py <output>/composition --dry-run`.
4. Look at stills of every scene and of each transition before the full render; fix text that
   overflows, collides or has weak contrast.
5. Write the draft `share-copy.txt`, then check the whole folder; it reruns the plan checks and
   scans the brief, caption and composition for keys, addresses and machine paths:

   ```bash
   python3 <skill-dir>/scripts/check_plan.py <output>
   ```

## 4. Render and deliver

See `references/deliver.md`. In short: check the tools (asking before any download), validate,
render to `<output>/brag.mp4`, confirm the length with `ffprobe`, pick a settled frame as
`brag.jpg` and make it frame 0 of the video with `scripts/poster.py`, and finish `share-copy.txt`
(1 to 3 sentences, postable as is, ending with the credit line `cues.py` prints if bundled music is
used).

If you cannot render here (tools missing, download refused, the user said not to install), stop
after the brief and the checked plan, and give the user the exact render commands from
`references/deliver.md` for their mode.

## Creative rules

- **Short:** 15 to 25 seconds; voice-over does not stretch it.
- **Hook first:** the first two seconds decide whether anyone watches the rest. Plan them first.
- **Show the product working:** at least one scene shows the real UI, copy or visual, ideally the
  flow (entry, key action, result). No abstract filler.
- **Specific:** it should fit this project only. Use its own words; generic launch language
  ("streamline your workflow", "excited to share") is out.
- **Readable:** speed comes from movement and cutting, never from taking text away early. A short
  label holds about 0.8 s once settled; a sentence about 0.3 s a word.
- **Clear to a stranger:** one viewing tells a newcomer what it is, who it serves and where to find it.
- **Humour comes from the project itself**; don't force jokes.
- **Any frozen frame is postable.**

## Stop when

- No project in the folder and no URL given: ask what the video should be about.
- A website returns nothing usable, or the fetch is refused: say what came back and stop.
- `check_plan.py` still fails after three fixes: hand back its output and the plan.
- A tool the mode needs is missing and the user hasn't agreed to fetch it: stop with the plan, the
  brief and the commands.
- Voice-over was asked for and no voice tool is available: say so; don't render a silent version.
- Validation still fails after three rounds of fixes: stop and give the user the errors and the
  composition path.
- Never run `npx hyperframes publish` or upload anything; sharing is the user's step.

## Reply

First line: `Video: <output>/brag.mp4 (<seconds> s)` or `Video: not rendered (<reason>)`. Then the
angle in one sentence, the files made (plan, brief, composition, poster, caption), what you could
not check, the commands still to run if any, and an offer to rework one scene or switch tone.
