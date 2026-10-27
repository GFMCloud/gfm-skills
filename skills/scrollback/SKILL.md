---
name: scrollback
description: Builds, restyles, checks or edits pages (charts included) in Scrollback, a dark monospace terminal-style design system for dashboards, status pages, docs, invoices and logs. Use for "make it look like a terminal", "monospace look" or "Scrollback". Not for brand sites, decks or standalone charts.
metadata:
  status: draft
  codex-check: "pending: not yet tried in Codex; must pass before stable"
---

# Scrollback

Scrollback (designator SB-01) is one fixed design system for pages that report on machines: the
page is a terminal buffer, typeset well. One monospace face at one weight, an 8px grid, square
corners, chrome drawn only from characters a terminal can print, and one blue accent spent in three
places. It reports; it does not persuade.

This skill's files are part of using it: `assets/` (the stylesheet and starter page), `scripts/`
(page starter and checker) and `references/`. Run its scripts by their path in this skill's folder
(written `<skill>/` below) with the user's project as the working directory. What you build goes in
the project; nothing else is written there except the checker's screenshots.

| The user wants | Job |
| :--- | :--- |
| A new page in this look (status page, dashboard, changelog, invoice, docs, report) | **Build** |
| An existing page turned into this look ("make it look like a terminal") | **Restyle** |
| A change to a page that is already Scrollback (a new chart, section or table) | **Edit**: as Build, inside the existing page; charts follow components.md, pattern 5 |
| "Does this follow Scrollback?" or "what's off?" | **Check**: run the checker, report, change nothing |
| design, decks or diagrams to use Scrollback colours | **Export**: see "Using it elsewhere" |

## 1. Fit check (before any file)

Scrollback fits a page that **reports state or fact**: docs, specs, dashboards, invoices, receipts,
logs, changelogs, status pages, internal tools, technical write-ups.

It does not fit persuasion or storytelling, consumer marketing, or anything built around photos or
illustration. It also loses to a project's own brand or design system (`.agents/brand/`, a tokens
file, an established stylesheet) unless the user asked for Scrollback by name. In those cases say
so in one or two sentences, point to the `design` skill for branded or marketing pages, and stop
unless the user has already told you to go ahead anyway. Never bend Scrollback into another look:
no photos inside frames, no second accent, no rounded "friendly" version.

## 2. Start from the stylesheet, never from memory

`assets/scrollback.css` is the system. Never retype its tokens or invent values.

- **Single self-contained page** (one HTML file, an artifact, an email preview):
  `python3 <skill>/scripts/new_page.py <page.html> --title "<title>"` writes the starter with the
  stylesheet inlined. Build inside it.
- **Project with a build or several pages**: copy `assets/scrollback.css` into the project's styles
  folder and link it. That copy is generated: fixes belong in the skill's file.
  Copy the starter's first comment and its `generator` meta tag into each page, so the next agent to
  edit the page knows it is Scrollback.
- **Restyle**: first read the page and list what it does. Keep every piece of content, number,
  link, form field, name, id, route and script; change only how it looks. Replace its styling with
  the stylesheet (inline or linked) and map its parts onto the components. If something looks
  functionally wrong, report it; don't fix it silently.

Read [references/components.md](references/components.md) before building, and
[references/rulings.md](references/rulings.md) before changing a token, adding a pattern or styling
a chart.

## 3. The rules that make it Scrollback

| | Rule |
| :--- | :--- |
| Type | One monospace family (`var(--mono)`) for every role, weight 400 everywhere, no italics. |
| Emphasis | A step up the brightness ramp (`--rule`, `--muted`, `--text`, `--bright`), never bold or size. |
| Corners | Radius 0, everywhere. |
| Accent | `--accent` in exactly three places: frame titles, data marks, the focus outline. Never links, button fills, borders, hover or highlights. |
| Colour | Only tokens, never literals. No pure white or black. Signal colours (`--signal-warn`, `--signal-fail`) only for system state, never on a document or chart. No green: ok is `--bright`. |
| Frames | One idea per frame. Frames never nest. |
| Numbers | Tabular figures; numbers right-aligned; the unit stays with the number (`16m`, `112 seats`). |
| Space | 8px grid; content in one 880px column; leave the empty space empty. |
| Motion | 120ms linear on colour only. No animation. |
| Charts | One series, no legend, no second colour. Many series become small multiples with a shared scale. |

Never: gradients (the dashed rules are the only exception), shadows, glows, blur, glass, icons or
emoji (the glyph set is `+ - | [ ] ▸ ◂ · ├ │ └ ─`), phosphor green, scanlines, text glow, blinking
cursors, typewriter reveals, ASCII-art wordmarks, inverse video in running text, a light theme for
screens (paper is print-only).

## 4. Content and voice

- Use the user's real content and data. Where something is missing, write
  `[NEEDS YOUR INPUT: ...]`. Never lorem ipsum, invented customers, numbers, logos or quotes.
  Chart heights and meter widths come from the data: compute them.
- Sentence case; uppercase only for frame titles, eyebrows and pills. Labels are plain nouns.
- Mark estimates (`~50m`). Errors say what happened and what to do, with no apology or exclamation
  mark. A control names its action, and the result names it done ("Issue", then "Issued").
- Cut any sentence that exists to make the reader feel something.

## 5. Check, then look

From the project folder:

```
python3 <skill>/scripts/check_scrollback.py <page.html> --shots
```

`--shots` needs playwright; without it try
`uv run --with playwright python <skill>/scripts/check_scrollback.py <page.html> --shots`. The
checker aborts every HTTP request that is not the page's own files (so the web font is not fetched)
and falls back to Chromium's `--single-process --no-zygote` flags
inside a sandbox; never turn a sandbox off to run it. If the render can't run, say the visual check
did not run.

Fix every FAIL and run it again until `result: pass`. Then open both screenshots
(`.scrollback-check/<page>-desktop.png` and `-phone.png`, beside the page) and name one thing you
checked in each. Tell the user the folder is there to delete. For a **Check** job, pass
`--out "$(mktemp -d)"` so nothing is written to their project.

The checker catches slips, not taste, and reads only CSS it can see (inline, `<style>`, local
stylesheets and their local `@import`s); a remote stylesheet other than the font is reported as
unchecked. Still on you: a passing page can still put two ideas in one frame or bury
the number that matters. Read the page once as its reader would.

## 6. Hand over

The files written or changed; the components used; the checker's `result:` line and any WARN
lines; one thing you saw in each screenshot; every `[NEEDS YOUR INPUT]` left; and anything you bent
because the user asked (a changed token, a pattern outside the catalogue). A changed token is
checked with `--allow-tokens`, which runs the contrast floors on the new values.

## Using it elsewhere

- **design, decks, diagrams**: these read brand tokens. If the user wants them in Scrollback colours,
  copy `references/brand/tokens.json` and `references/brand/guidelines.md` into the project's
  `.agents/brand/` (ask before overwriting one that exists). Say plainly that this carries the
  palette and font and the guidelines as preferences only; the full system (frames, components,
  checker) lives here.
- **Command-line output**: apply the voice, the glyph set, the brightness ramp and the three-use
  accent, using the token hex values as truecolor; there is no checker for terminal output.
