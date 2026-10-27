# Full mode: building with Hyperframes

Hyperframes is an open-source command-line tool (Apache-2.0) that renders HTML compositions to MP4.
It is not part of this skill and changes often, so let its own documentation decide the details.

## What was checked, and when

Checked on 2026-10-27 against the npm page of `hyperframes` 0.8.209
(https://www.npmjs.com/package/hyperframes) and its CLI docs
(https://hyperframes.heygen.com/packages/cli):

- Needs Node.js 22 or later and FFmpeg; uses its own Chrome.
- Commands listed there: `init`, `preview`, `lint` (validates the HTML, `--json` for counts),
  `render -o <file>` (renders the project folder's `index.html`, or `-c <file>`), `doctor` (checks
  Node, FFmpeg and Chrome), `audio` (measures where sounds land), `info`, `docs`, `upgrade`, and
  `publish` (uploads the project to a hosted URL).
- Earlier versions of the old brag workflow also used `check`, `snapshot`, `beats` and `tts`. The
  README above doesn't list them; use them only if `npx hyperframes --help` does.

## Steps

1. **Ask first.** `npx hyperframes` downloads the package on first use. Tell the user that, and ask
   before the first `npx hyperframes` call in a run. If they decline, or the download is refused,
   switch to light mode or stop with the brief and the commands.
2. `npx hyperframes doctor`. If Node, FFmpeg or Chrome fails, name what is missing and stop.
3. `npx hyperframes --help` and `npx hyperframes info`: note the version and the commands in the
   plan's audio or brief section, so a later session knows what was used.
4. If the Hyperframes skills are available to you (`hyperframes-core`, `hyperframes-animation`,
   `hyperframes-creative`, `hyperframes-keyframes`, `hyperframes-cli`), read them and build
   `<output>/composition/` to their contract from the brief. Skip their own intake interview and
   their generic promo workflow: the plan and brief already answer those questions. If they are not
   available, follow `npx hyperframes docs` or the CLI docs page above.
5. Copy the chosen music and effects into `composition/assets/` before building; refer to them by
   relative paths. Absolute paths fail in the renderer.
6. Validate with `npx hyperframes lint .` from `composition/` (and `check` if `--help` lists it).
   Fix every error, including contrast. After three failed rounds, stop and hand back the errors.
7. Look at stills (see `compose.md`), then render from `composition/`:
   `npx hyperframes render -o ../brag.mp4`. A draft-quality render first is fine if the CLI offers
   one.

## Voice-over (only when asked)

If the user asked for narration and the CLI offers a text-to-speech command, write the script in
the plan under `## Voice-over`, keep it inside the same 15 to 25 seconds, generate the audio into
`composition/assets/`, measure its length, and adjust scene lengths to it. If no voice tool is
available, say so and stop; don't render a silent version instead.

## Never

- `npx hyperframes publish`, `auth` or anything that uploads. Sharing is the user's step.
- Install Hyperframes globally (`npm install -g`) unless the user asks for it.
- Turn usage reporting on or off for the user without asking; tell them Hyperframes may send
  anonymous usage data and that its docs say how to turn that off.
