# Scrollback rulings

Why the system is the way it is. Every ratio here is printed by
`python3 <skill>/scripts/check_scrollback.py --palette`; rerun it rather than trusting this page.

## Contents

- Palette
- Accent: three uses
- Accessibility floors
- Precedence
- Bugs this system tends to produce
- Token contract and amendments
- Lineage and what it refuses

## Palette

Core, seven tokens, and it stays seven:

| Token | Value | On canvas | Job |
| :--- | :--- | :--- | :--- |
| `--canvas` | `#11110F` | ground | Page background, a warm near-black |
| `--surface` | `#171715` | 1.05:1 | Raised panels only (document, command block, field well) |
| `--rule` | `#494844` | 2.06:1 | Frames, separators, leaders, decorative glyphs. Never text (except a disabled control), never meaning |
| `--muted` | `#8A8781` | 5.28:1 | Captions, labels, field and button edges |
| `--text` | `#B7B4AD` | 9.13:1 | Body and data |
| `--bright` | `#E9E7E1` | 15.29:1 | Emphasis, success, totals |
| `--accent` | `#2E8EFF` | 5.79:1 | Frame titles, data marks, focus |

Extensions, each with a fixed scope:

- `--rule-dim` `#2B2B29`: separators inside a `--surface` panel, where `--rule` is too strong.
  Decorative only.
- `--signal-warn` `#E5A13A` (8.54:1) and `--signal-fail` `#F26A5A` (6.29:1): system state only
  (logs, validation, alerts, service state). Never on a document, an invoice, marketing or a chart.

There is **no success colour**. In a system whose normal state is fine, "ok" is the absence of a
signal, so it gets `--bright`. Leaving green out also keeps warn and fail apart for readers with a
red-green deficiency, and the word always comes before the colour.

**Paper** is the only other palette, under `@media print`. There is no light theme for screens and
the system ignores `prefers-color-scheme`. On paper the accent darkens to `#1660C8` (5.24:1),
because `#2E8EFF` on paper measures 2.89:1. That is why every SVG mark takes `var()` colours.
Browsers drop backgrounds when printing by default, and the frame rules, bars, meter fills and
panels are backgrounds, so the print block sets `print-color-adjust: exact`.

## Accent: three uses

1. The bracketed frame title.
2. Data marks: bars, meter fills, the sparkline's last point, spec-diagram brackets, a running pill.
3. The keyboard focus outline.

Never a link colour, button fill, border, hover state, highlight (text selection uses `--bright`)
or syntax colour. Interaction runs
on the brightness ramp instead: `--rule`, `--muted`, `--text`, `--bright`, one step per change of
state. Focus is the third use because nothing else passes: `--rule` measures 2.06:1, under the 3:1
that WCAG 1.4.11 needs for a non-text indicator.

## Accessibility floors

- `--muted` is the smallest text colour and never goes under 13px. Log timestamps, tree lines and
  placeholders are `--muted` (rev 1.1; they were `--rule` before, under the floor).
- `--rule` is text only on a disabled control, which WCAG exempts from contrast floors because it
  is inactive.
- `--rule` carries no meaning. A boundary that tells the user something (a field, a button edge, a
  note's left rule) is `--muted` or brighter. (rev 1.1: field underline, button edge and note rule
  moved from `--rule` to `--muted`, because 2.06:1 fails 1.4.11 for a control's boundary.)
- Status is a word before it is a colour.
- Decorative glyphs (frame corners, flow arrows, leaders) take `aria-hidden="true"`. Tree glyphs
  are content and stay readable.
- Every chart, meter and sparkline takes `role="img"` and an `aria-label` with shape, range and
  endpoint (meters print their value as text instead).
- Prose measure 72ch. Layouts must survive 200% zoom with no sideways page scroll, because a single
  mono face at 15px reads smaller than a 15px sans.
- `prefers-reduced-motion` turns the 120ms transitions off.

## Precedence

1. The user's own words.
2. A project's own design system or brand (`.agents/brand/`, a design-tokens file, an existing
   stylesheet), unless the user asked for Scrollback by name or the project already is Scrollback.
3. Inside a Scrollback surface, this skill decides chart colour and legends: one accent, no legend,
   no second series colour. A general chart guide would allocate a series palette, and the second
   hue is where the system stops reading as instrumentation. Its answer to many series is small
   multiples. Still applied from general chart practice: picking the right form for the question,
   contrast floors, never colour alone.
4. General page guidance still applies (real content, no sideways scroll, visible focus, reduced
   motion), except "design both light and dark": Scrollback is one theme plus paper. Paint the
   background and every colour explicitly so it holds on any host.

## Bugs this system tends to produce

Each shipped at least once and none shows in a code read; `check_scrollback.py --shots` catches the
first three.

- A % width on an inline `<span>` computes to 0: meter track and fill must be blocks.
- A multi-line block that isn't `pre` collapses its newlines.
- A `nowrap` value pushes the page sideways on a phone: stack the pair instead.
- Token names break after the leading `--`: put `.nw` on cells that hold them.
- SVG colour literals look right on screen and vanish on paper.

## Token contract and amendments

The token names are an API: pages, CLI themes and generated documents bind to them.

- v1 exports: core `--canvas --surface --rule --muted --text --bright --accent`; extensions
  `--rule-dim --signal-warn --signal-fail`; layout `--mono --u --measure`.
- Renaming or removing one is a breaking change: bump the major revision and update every page
  that uses it. Core stays at seven; anything new is an extension with a stated scope.
- A new accent use needs a written reason and the measured alternative that was rejected (as focus
  above).
- Revisions are `SB-01 rev N.M`; a change that breaks an existing page increments N.
- A page that changes a token on a user's request runs the checker with `--allow-tokens`, which
  checks the changed palette against the same floors.

## Lineage and what it refuses

Scrollback draws on the density and steady palette of financial terminals, the datasheet posture of
technical-drawing type, the character grid of monospace-web experiments (relaxed to an 8px grid),
and the numbered, ornament-free sections of man pages and RFCs, its closest ancestor.

Refused by name, because each is standard in the terminal-aesthetic genre and someone will add it
as a helpful improvement: phosphor green, CRT scanlines and curvature, text glow, blinking cursors,
typewriter reveals, ASCII-art wordmarks, inverse video in running text, a hard 80-column page.
