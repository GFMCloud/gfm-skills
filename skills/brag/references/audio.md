# Audio

## Contents

- What ships
- Picking music
- Picking effects
- Levels and timing
- Credit

Music and a few well-placed effects beat silence for almost every brag video. Use fewer effects
with better timing rather than many; one coherent set of sounds rather than a grab bag. Skip music
or effects only when the user turned them off or the plan makes silence the joke.

## What ships

All paths are inside `<skill-dir>/assets/`. Copy what you use into `<output>/composition/assets/`
and refer to it by a path relative to `composition/`.

| Folder | What | Licence |
| :--- | :--- | :--- |
| `music/*.mp3` | Five upbeat tracks, 1 to 3 minutes each | CC BY 4.0, credit line from `cues.py` |
| `music/cues/` | Beat grid and strong cues for each track's first 25 s (JSON and a short summary) | MIT |
| `sfx/interface/` | 20: clicks, switches, soft drops, one deep bong, two glitches, two error buzzes | CC0 |
| `sfx/ui/` | 48: clicks, a mouse click, rollovers, 38 switch variants | CC0 |
| `sfx/impact/` | 109: soft, wood, plank, plate, metal, glass, bell and punch hits; footsteps | CC0 |
| `sfx/casino/` | 51: card slides, places, fans and shuffles, chips, dice | CC0 |
| `sfx/keyboard/` | 32 single key presses (`keypress-001.wav` to `-032.wav`) | CC0 |
| `sfx/sfx-analysis.md` | Each effect's length, brightness and high-frequency risk, with safest picks by use | MIT |

## Picking music

`python3 <skill-dir>/scripts/cues.py --list` prints each track with its length, tempo and a feel
note. `cues.py <n> --until <seconds>` prints that track's beat spacing, strong cues and beats inside
your video's length. Aim one to three of the biggest moments (the reveal, the name landing) at
strong cues, within about 0.15 s; small entrances may snap to beats within about 0.1 s. Let cues go
when they would hurt reading time or the story.

For your own track, there is no cue file: time it by ear, or ask the user before installing any
beat-detection tool.

## Picking effects

Read `sfx/sfx-analysis.md` first. Prefer low or medium high-frequency risk for anything repeated or
for calm tones; keep bright, high-risk files for one small accent or a chaotic edit.

| Moment | Families that fit |
| :--- | :--- |
| Cards or items arriving one by one | `casino/card-slide-*`, `card-place-*`, `interface/drop_*`; accent the first and last, not every item |
| Big reveal or the name landing | `impact/impactSoft_medium_*`, `impact/impactBell_heavy_*`, `interface/bong_001` |
| Typed text | a different `keyboard/keypress-*` file for each character, quiet; thin it out for long lines |
| A click, tap, toggle or swipe on screen | `interface/click_*`, `ui/mouseclick1`, `ui/click*`, `interface/switch_*`, `casino/card-slide-*` |
| Success or a number landing | `impact/impactBell_heavy_*`, `casino/chips-collide-*` |
| A comic or chaotic beat | `interface/glitch_*`, `interface/error_*`, `impact/impactPunch_heavy_*`, `casino/dice-throw-*` |

How many, by tone: `polished` and `deadpan` two or three quiet ones; `yc-parody` two or three dry
ones; `default` three to five; `cinematic` two or three big ones; `app-store` one per feature card;
`chaotic` many, sometimes stacked.

## Levels and timing

- Music bed 0.3 to 0.4 (0.12 to 0.2 for deadpan or quiet parody), never above 0.5. Fade it out over
  the last 1 to 2 seconds.
- Effects 0.55 to 0.85, softer for calm tones. They sit under the music, never spiky.
- A click starts with the gesture; a reveal sound lands with the payoff. A pop-in sound starts up
  to 0.1 s before the element appears.
- With a voice-over, lower the music to about 0.12 to 0.15 while the voice speaks.
- Each overlapping sound gets its own track in the composition; never let two share one.

## Credit

If a bundled track is used, the post must credit it. `cues.py <track>` prints the line, for example
`Music: "Happy Beats / Business Moves vol. 12" by ende.app (CC BY 4.0)`; put it on the last line of
`share-copy.txt`. Copy `assets/music/LICENSE.md` into the composition with the track. The effects
need no credit; copy `assets/sfx/LICENSE.md` with them anyway, so the folder says where they came
from.
