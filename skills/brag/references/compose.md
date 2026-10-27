# Step 3: compose

## Contents

- The composition brief
- Light mode: the page contract
- Light mode: brag.json
- Before rendering everything
- Grounding check

## The composition brief

Write `<output>/composition-brief.md` before building. It is the hand-over from the plan to the
build, so a fresh session (or the Hyperframes skills) could build the video from it alone.

```markdown
# Composition brief: <product>

## Output
- Composition: <output>/composition/
- Video: <output>/brag.mp4
- Mode: full | light
- Format: <format> <width>x<height>, 30 fps
- Length: <seconds>

## Source
- Project: <the project folder's name, or the site's URL>; never a full path on this machine
- Files read: <paths relative to the project>
- Copy that must appear word for word:
  - "<line>"
- UI to rebuild: <component or screen, with the file it comes from>
- Images to reuse: <files copied into composition/assets/>

## Direction
- Tone: <preset>, <direction>
- Angle: <from the plan>
- Hook: <first seconds>
- Punchline: <last line>
- Avoid: generic launch language, abstract filler, redesigning the product

## Look
- Background, text, accent: <exact values>
- Display and body font: <names, and the fallback if the font isn't available offline>

## Scenes
<one line per scene: name, seconds, what must be seen and read>

## Audio
- Music: assets/music/<file>, volume <n>, fade out over the last <n> s; credit line from cues.py
- Strong cues aimed at: <times and what lands there>
- Effects: <moment: family>, exact files chosen once the motion exists
- Voice-over: off | on (script in the plan)

## The build owns
Animation timing and easing, structure, effect files and their exact times, and the render
settings. It must keep the copy, the scene order, the lengths within half a second, the colours
and the audio posture.
```

## Light mode: the page contract

`composition/index.html` is one self-contained page at the video's exact width and height:

- It defines `window.seek = (t) => { ... }` that draws the frame for time `t` in seconds. It may
  return a promise; `render_light.py` waits for it.
- **Every frame is a pure function of `t`.** No `setTimeout`, no CSS animations or transitions
  left running, no `requestAnimationFrame` loops, no `Date.now()`. Compute each element's position,
  opacity and text from `t`, with your own easing functions.
- All assets are local and relative (`assets/...`). No remote fonts, scripts or images: download
  what you need into `assets/` first, with the user's agreement if it means fetching anything.
  Prefer system fonts or font files the project already has.
- Rebuild the product's UI with its own markup and styles where you can (copy the CSS you need
  into the page); don't pan over a flat screenshot.
- Typed text: reveal `Math.floor(chars_per_second * (t - start))` characters.
- Busy layouts: don't crossfade two of them into a muddy double exposure; move the old one out,
  then bring the new one in, or pass through a plain background frame.

## Light mode: brag.json

```json
{
  "width": 1920,
  "height": 1080,
  "fps": 30,
  "duration": 20,
  "music": {"file": "assets/music/<track>.mp3", "volume": 0.35, "from": 0, "fade_out": 1.5},
  "sfx": [
    {"file": "assets/sfx/impact/impactSoft_medium_001.ogg", "at": 2.4, "volume": 0.7}
  ]
}
```

`music` may be `null`; `from` is where in the track to start. Every `at` must fall inside the
video. Run `render_light.py <composition> --dry-run` after writing it: it checks the files exist,
paths are relative and inside the composition, values are in range, and the page defines
`window.seek` and loads nothing remote, then prints the frame count and the ffmpeg command it
would run.

## Before rendering everything

Look at stills: one settled frame per scene and one in the middle of each transition. In light
mode, `render_light.py <composition> --stills 1.5,3.2,...` writes them to `<output>/work/stills/`.
In full mode use the Hyperframes preview or still command. Fix overflow, text that collides with
other elements, low contrast, and anything that reads badly mid-transition.

## Grounding check

Validation checks structure, not truth. Before the render, read every line of on-screen text
against the claims table: names, numbers, features and quotes must come from the project; reworded,
trimmed or split is fine, invented is not. Jokes, hooks and connecting lines that claim nothing
about the product are free. When a line you want isn't grounded, quote what the project actually
says instead.
