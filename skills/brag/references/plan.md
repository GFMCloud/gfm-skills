# Step 2: the plan

## Contents

- The template (the headings `check_plan.py` reads)
- Scene count and length
- Reading time
- What to show
- Audio in the plan

The plan is the contract for the build. It says what the video must get across and which project
material it must use. It does not prescribe animation code; the build decides that.

## The template

Keep these headings and the scene line format exactly; `scripts/check_plan.py` parses them.

```markdown
# Brag plan: <product>

## What it is
<one sentence>

## Nine questions
<the answers from step 1, numbered>

## Angle
<the premise: the joke, the claim, why this video fits only this project>

## Hook
<the first two or three seconds>

## Highlights
- <two or three specific moments, e.g. "the progress bar filling as the file uploads">

## Punchline
<the last line before the name>

## Tone
Preset: <default | polished | yc-parody | chaotic | deadpan | cinematic | app-store>
Direction: <a short phrase>

## Format
<landscape | vertical | square> <width>x<height>, 30 fps

## Duration
<target seconds>

## Visual identity
- Background: <exact value>
- Text: <exact value>
- Accent: <exact value>
- Display font: <name>
- Body font: <name>
- Reuse from the project: <components, images, the screen to recreate>

## Audio
Music: <file name from cues.py, or none (why)>
Cues: <one to three strong-cue times you aim major moments at, and the beat spacing>
Effects: <sparse | moderate | dense>, <the moments that get sound>
Restraint: <what the sound must not do>

## Storyboard

### Scene 1: <name> (<seconds>s)
On screen: "<every line a viewer must read, each in double quotes>"
Shows: <what is on screen; the product material it uses>
Motion: <items that arrive in sequence, or a simulated click, swipe or keystroke; or none>
Sound: <intent, e.g. soft click on each card>
Transition: <cut | crossfade | slide | wipe | flash>

### Scene 2: <name> (<seconds>s)
...

## Claims
| On screen | Source |
| :--- | :--- |
| "<a claim about the product>" | <file and line, or page URL> |

## Stand-ins
<made-up names or data used in place of real ones, or "none". Made-up emails use example.com>

## Share copy
<one to three sentences>
```

The Claims table holds claims about the product only. A joke, a hook or a connecting line asserts
nothing, so it stays out of the table; `check_plan.py` fails a row whose source is "joke" or
"invented". A product claim you can't source gets cut, not labelled.

Lines in `On screen` that are pure decoration (a filename on a mock window, a button label in a
recreated UI) can go under `Shows` instead; they then don't count toward reading time.

## Scene count and length

| Tone | Scenes | Feel |
| :--- | :--- | :--- |
| default | 4 to 5 | room to breathe |
| polished | 3 to 4 | long holds, restraint |
| yc-parody | 4 to 5 | one claim per scene, delivered straight |
| chaotic | 6 to 8 | some scenes under 2 s |
| deadpan | 3 to 4 | long holds, empty space |
| cinematic | 4 to 5 | large type, sweeping reveals |
| app-store | 4 to 6 | clean feature cards |

The usual shape is hook (2 to 3 s), reveal (2 to 4 s), two or three highlights, punchline and name
(2 to 4 s). Change it when the project calls for it. Scene lengths must add up to 15 to 25 seconds;
18 to 22 suits most videos.

## Reading time

Each line the viewer has to read needs settled time on screen, counted from when it has fully arrived
to when it starts to leave: about 0.8 s for one to three words, and 0.3 s a word (at least 1.2 s)
for anything longer. Entrances and transitions stay quick (0.3 to 0.6 s). Text may arrive fast as long
as it then stays put.

If a scene has more text than its length allows, cut words or split the scene; never speed the
text up. When items appear one after another on the beat, a fast tempo can put them half a second
apart, which outruns reading: use every other beat, or bring them in quickly and leave the whole group up.

## What to show

In order of preference:

1. **The working app**: the upload, the result, the dashboard with believable content, rebuilt
   from the project's own components and styles.
2. **One UI element**: a card, a meter, a swipe stack, when there is no flow.
3. **The core idea animated**, grounded in the product's own concept.
4. **The copy as the visual**: giant type, when the product is mostly words.

A headline block or stat row can frame the flow once; it doesn't replace it. Write sequences
and simulated clicks, swipes or typing into the storyboard explicitly: they show the product
working, and the sound follows them.

## Audio in the plan

Pick the track and the posture; leave exact effect files and times to the build, which knows when
things move. Name one to three strong cues from `cues.py` for the biggest moments. For `deadpan`
and `yc-parody`, keep sound sparse and quiet rather than absent.
