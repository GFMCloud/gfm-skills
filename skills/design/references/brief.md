# Brief pages

For the **Brief** job in `SKILL.md`: a page an agent hands a person to read (a report, review,
comparison, plan, decision or explainer). It is judged by what the reader knows after the first
phone screen and how little they had to read to get there.

## Contents

- Shapes
- Sketches
- SVG at phone width
- Toggles
- Worked pair
- Tells of reading pages

## Shapes

Pick one shape per section before writing it, and put it on the section as `data-shape`. The shape
shows the relation between the things in the section; the words only label it.

| Shape | Use when | Not when |
| :--- | :--- | :--- |
| `tree` | The reader chooses: the answer depends on their case ("a live URL? then ...") | The options don't depend on each other: use a table |
| `flow` | Steps happen in order: a process, a request's life, before and after | The steps are a checklist with no order: use a list of 3 to 5 |
| `layers` | Parts sit on other parts: a system by level, what wraps what | All parts are at one level |
| `timeline` | Dates matter: freshness, gaps, what happened when | Fewer than three dates |
| `matrix` | A few options against 3 to 5 criteria, where the pattern is the point | More criteria: use a table, with the long tail in a toggle |
| `table` | Independent items with the same fields (checks, a feature grid) | The items lead to each other: that is a flow or tree |
| `text` | A short section that only states something (one or two sentences) | It runs past a short paragraph: find its shape |

Text in boxes is not a shape. Three or more boxes side by side, each holding a paragraph, is a
list dressed as a layout; `check_page.py --brief --shots` fails it. A system map with paths the
reader should click through belongs to the diagrams skill; link to it or embed its file.

## Sketches

Starting points, not components: redraw each for its content (its labels, its count, its one
highlighted item). Colours come from tokens so both themes work.

Tree (a choice):

```html
<svg viewBox="0 0 360 170" role="img" aria-label="Which tool: local folder? Enigma. Live URL? Dembrandt.">
  <rect x="110" y="4" width="140" height="40" rx="8" fill="var(--surface)" stroke="var(--line)"/>
  <text x="180" y="29" text-anchor="middle" font-size="15">Where is it?</text>
  <path d="M180 44 V64 H70 V84 M180 64 H290 V84" fill="none" stroke="var(--muted)"/>
  <rect x="10" y="84" width="120" height="40" rx="8" fill="var(--surface)" stroke="var(--line)"/>
  <text x="70" y="109" text-anchor="middle" font-size="15">Folder or repo</text>
  <rect x="230" y="84" width="120" height="40" rx="8" fill="var(--surface)" stroke="var(--line)"/>
  <text x="290" y="109" text-anchor="middle" font-size="15">Live URL</text>
  <text x="70" y="152" text-anchor="middle" font-size="15" font-weight="700" fill="var(--primary)">Enigma</text>
  <text x="290" y="152" text-anchor="middle" font-size="15" font-weight="700" fill="var(--primary)">Dembrandt</text>
</svg>
```

Flow (steps, or before and after as two lanes):

```html
<svg viewBox="0 0 360 64" role="img" aria-label="Search, answer opens inline: 2 actions">
  <rect x="0" y="12" width="150" height="40" rx="8" fill="var(--surface)" stroke="var(--line)"/>
  <text x="75" y="37" text-anchor="middle" font-size="15">Search</text>
  <path d="M152 32 H204" stroke="var(--muted)" marker-end="url(#arrow)"/>
  <rect x="210" y="12" width="150" height="40" rx="8" fill="var(--primary-soft)" stroke="var(--primary)"/>
  <text x="285" y="37" text-anchor="middle" font-size="15">Answer inline</text>
</svg>
```

Layers: stacked full-width bars, top is what the reader touches, bottom is what it rests on; mark
the layer the section is about. Timeline: one axis, a dot per dated event, the gap that matters
shaded, today as a dashed line. Matrix: options as rows, criteria as columns, filled and empty
marks instead of words, the winning row highlighted.

Define an arrow marker once per page (`<defs><marker id="arrow" ...>`) and reuse it.

## SVG at phone width

- A figure is about 340px wide on a 390px phone after the page's margins. Draw it in a viewBox at
  most 400 units wide with text at least 14 units, or it shrinks below 12px; the checker warns
  under 12px.
- A figure wider than that (a flow of five steps) gets a vertical version for phones: two `<svg>`
  elements, one shown under 480px and one above, or a flow that turns its axis.
- Every label fits inside its box at both widths. Check by eye on the phone shot.
- `role="img"` and an `aria-label` that says what the figure shows, in a sentence.

## Toggles

- `<details>` with a `<summary>` that names what is inside: "20 rulings, with the cost if wrong",
  "How the numbers were measured", not "More" or "Details".
- What never goes in a toggle: the bottom line, the decision or next step, and the tradeoffs the
  decision rests on.
- Sources go in one closing toggle. Only a number the decision turns on carries its source inline,
  once. A tag beside every fact is clutter, and readers mark the page down for it.
- A toggle can hold a long list, a full table, a diff, a method, raw notes. Nothing is deleted to
  meet the 400-word limit; it moves.

## Worked pair

A comparison page listed 20 "pick by need" rows as text cards, each a sentence and a tool name.
Brief version: a `tree` of three questions (where is the design, what do you need from it, do you
already pay for a service) ending in four tool names, drawn as one SVG; the 20 rows went into a
toggle under it, grouped by the first question. Open words fell and every row stayed on the page.

## Tells of reading pages

- A banner of 80 words above the first heading.
- A source tag or badge beside every fact.
- The same checks shown twice (once as a summary, once as a table).
- A grid of paragraph cards.
- A row of eight or more pills or steps.
- The decision below the first phone screen, or inside a toggle.
