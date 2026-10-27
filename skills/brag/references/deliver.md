# Step 4: render and deliver

## Tools

| Mode | Needs | How to check without installing |
| :--- | :--- | :--- |
| Full | Node 22+, FFmpeg, the Hyperframes package (fetched by `npx`, ask first) | `node --version`, `ffmpeg -version`, then `npx hyperframes doctor` after the user agrees |
| Light | Python 3, FFmpeg, ffprobe, Playwright with Chromium | `ffmpeg -version`, `ffprobe -version`, `python3 -c "import playwright"` or `uv run --offline --with playwright python -c "import playwright"` |

If anything is missing, name it and ask. Never install a package, a browser or a tool without a yes.
Never turn off a sandbox to make a browser start; `render_light.py` already retries Chromium with
`--single-process --no-zygote`, which works inside one.

## Render

- **Full:** see `hyperframes.md`. From `composition/`: `npx hyperframes render -o ../brag.mp4`.
- **Light:** `python3 <skill-dir>/scripts/render_light.py <output>/composition`, or with
  `uv run --with playwright python <skill-dir>/scripts/render_light.py <output>/composition`
  when Playwright isn't installed for the system Python (this may download it: ask first). It
  captures every frame, mixes the audio from `brag.json`, and writes `<output>/brag.mp4`.

Then confirm the length:

```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 <output>/brag.mp4
```

It must be within 15 to 25 seconds and within half a second of the plan.

## Poster

Pick the strongest settled moment (text fully in, nothing mid-transition), usually the hook line,
the main reveal or the final name, from the storyboard times. Then:

```bash
python3 <skill-dir>/scripts/poster.py <output> <seconds>
```

It writes `<output>/brag.jpg` from that frame and replaces frame 0 of `brag.mp4` with it, so every
platform's thumbnail shows the poster. It keeps the length, frame count and audio, and checks both
afterwards. If the frame lands mid-motion, move a few tenths of a second and run it again.

## Share copy

Write `<output>/share-copy.txt`: one to three sentences, postable as is, in the video's tone,
specific to the project, with no "excited to share". Use the caption shape for the tone in
`tones.md`. If a bundled track is used, end with the credit line `cues.py` prints for it. One
caption only; variants, if wanted, go in `share-copy-variants.md`. Then run
`check_plan.py <output>` once more; it fails a caption that lacks the credit or carries an address.

## Done

`<output>/` holds `brag.mp4`, `brag.jpg`, `brag-plan.md`, `composition-brief.md`,
`share-copy.txt` and `composition/`. Tell the user where they are; nothing is posted or uploaded.

## If you can't render here

Stop after the checked plan and the brief (and the composition, if you could write it), and give
the user the commands for their mode, in order, with the real output path. For full mode:

```bash
cd <output>/composition && npx hyperframes doctor && npx hyperframes lint . && npx hyperframes render -o ../brag.mp4
```

For light mode:

```bash
uv run --with playwright python <skill-dir>/scripts/render_light.py <output>/composition
```

Then the `ffprobe` and `poster.py` lines above.
