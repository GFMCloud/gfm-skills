# Scrollback components

The frame plus fourteen patterns, each with markup that works against `assets/scrollback.css`. Use a
listed pattern before inventing one. All example content is demo content: replace it with the
user's real material.

## Contents

- The frame
- 1 Data table, 2 Flow, 3 Spec diagram, 4 Document, 5 Chart, 6 Status pill, 7 Log stream
- 8 Command block, 9 Spec sheet, 10 Meter, 11 Sparkline, 12 Note, 13 Tree, 14 Field and button
- States
- A new pattern

## The frame

Every block of content sits in one frame. The frame carries the look; what is inside stays flat.

```html
<section class="frame" aria-labelledby="f-usage">
  <span class="c tl" aria-hidden="true">+</span><span class="c tr" aria-hidden="true">+</span>
  <span class="c bl" aria-hidden="true">+</span><span class="c br" aria-hidden="true">+</span>
  <h2 class="ttl" id="f-usage">02 · Usage</h2>
  ...
</section>
```

- Dashed top and bottom rules (8px dash, 10px gap), sparser vertical ticks, `+` corners in
  `--rule`. The rules are gradients, so the dash rhythm is the same at every width.
- Title: centred on the top rule, uppercase, in `[ ]`, in `--accent` (accent use 1). Keep it short:
  at 375px about 24 characters fit.
- **Frames never nest.** Two ideas are two frames. Inside a frame the only rectangles are the
  `--surface` panel (document, command block) and the spec diagram's corner brackets.
- Frames stack in `.stack`, one 880px column, 80px apart (56px on phones).

## 1 Data table

```html
<div class="scroll"><table>
  <thead><tr><th>Job</th><th class="r">Rows</th><th class="r">Time</th></tr>
    <tr class="sep"><td colspan="3"></td></tr></thead>
  <tbody><tr><td>Nightly import</td><td class="r">48,200</td><td class="r">6m</td></tr>
    <tr class="sep"><td colspan="3"></td></tr></tbody>
  <tfoot><tr><td>Total</td><td class="r">48,200</td><td class="r">~6m</td></tr></tfoot>
</table></div>
```

- Header in `--text`, not muted and not accent. Total row `--bright`. A dashed separator under the
  header and above the total; no zebra rows, cell borders or row hover.
- Numbers right-aligned (`.r`) with tabular figures. The unit lives with the number (`6m`, `€21.04`).
- Mark estimates: `~6m`. Always wrap in `.scroll`: the table scrolls, never the page.

## 2 Flow

```html
<div class="flow">
  <div class="node"><span class="br">48,200 rows</span><span class="cap">raw</span></div>
  <div class="leader" aria-hidden="true"></div><span class="glyph" aria-hidden="true">▸</span>
  <span class="step">dedupe</span>
  <div class="leader" aria-hidden="true"></div><span class="glyph" aria-hidden="true">▸</span>
  <div class="node"><span class="br">47,912 rows</span><span class="cap">clean</span></div>
</div>
```

- Shape: state, leader, `▸`, transform, leader, `▸`, state. Both ends are the same kind of thing at
  different sizes, so the difference reads at a glance. The transform is an unboxed word.
- Under 640px the leaders hide and the flow stacks; order carries the sequence.

## 3 Spec diagram

```html
<div class="spec-box">
  <span class="k tl"></span><span class="k tr"></span><span class="k bl"></span><span class="k br"></span>
  <div>outer&nbsp;&nbsp;16px</div>
</div>
<p class="formula">inner = outer − inset<br><span class="sub">12px = 16px − 4px</span></p>
```

- Four L-shaped corner brackets in `--accent` (accent use 2: they are data), 14px arms, never a
  closed box. Labels are `name  value` with two spaces.
- End with the relationship as a formula, then the same formula with numbers in `--muted`.

## 4 Document (invoice, receipt, statement)

```html
<div class="doc">
  <div class="meta"><span class="br">Demo Supplies Ltd</span>
    <dl><dt>Ref</dt><dd>INV-0042</dd><dt>Due</dt><dd>14 Nov · Net 14</dd></dl></div>
  <div class="drule" aria-hidden="true"></div>
  <div class="cols"><div><div class="eyebrow">From</div><div class="br">...</div></div>
    <div><div class="eyebrow">Bill to</div><div class="br">...</div></div></div>
  <div class="drule" aria-hidden="true"></div>
  <div class="scroll"><table>...line items...</table></div>
  <div class="drule" aria-hidden="true"></div>
  <div class="totals"><div class="row"><span class="sub">Subtotal</span><span>€3,975.18</span></div>
    <div class="row"><span class="sub">VAT 20%</span><span>€795.04</span></div>
    <div class="row total"><span>Total due</span><span>€4,770.22</span></div></div>
</div>
```

- A `--surface` panel inside a frame. Separators inside it use `--rule-dim`.
- Metadata top right, values right-aligned in `--bright`. Line items `--text` with a `--muted`
  description under each. Totals in a column no wider than 340px.
- **No signal colours**: a document has no severity. It prints through the paper palette unchanged;
  any logo SVG uses `fill="var(--bright)"`, never a literal.

## 5 Chart

```html
<div class="cols">
  <div class="bars" style="height:88px" role="img"
       aria-label="Runs per week, 8 weeks, rising from 22 to 88; latest week 88">
    <i style="height:22px"></i><i style="height:40px"></i>...<i style="height:88px"></i>
  </div>
  <div class="rows tight"><span class="cap">runs per week</span><span class="br">88 <span class="sub">latest</span></span></div>
</div>
```

- Flat accent bars (accent use 2), square, 16px wide with 3px gaps. No axes, gridlines or tooltips.
- **One series, no legend, no second colour.** A chart that needs a legend becomes two or more
  small charts, one per series, each with its own label and its own `aria-label`. Use the same
  height scale across them so they compare.
- The number that matters sits beside the chart in `--bright`; the bars carry shape, the number
  carries the fact. Heights come from the data: compute them, don't eyeball them.
- Inside a Scrollback page this replaces general chart guidance on colour, legends and palettes
  (see rulings.md, "Precedence"); accessible encoding and choosing the right chart still apply.

## 6 Status pill

```html
<span class="pill ok">ok</span> <span class="pill live">running</span> <span class="pill">idle</span>
<span class="pill warn">degraded</span> <span class="pill fail">failed</span>
```

- A bracketed uppercase word at 13px. No background, border or radius: there is no pill shape.
- The word carries the state first, the colour second: ok `--bright`, idle `--muted`, running
  `--accent`, degraded `--signal-warn`, failed `--signal-fail`. There is no green.
- Running spends accent. With many live rows on one screen, show them as `ok`-bright instead.

## 7 Log stream

```html
<div class="log">
  <div class="ln"><span class="t">09:41:02</span><span class="s">info</span><span class="m">sync started · 48,200 queued</span></div>
  <div class="ln warn"><span class="t">09:41:44</span><span class="s">warn</span><span class="m">rate limit at 82% · backing off 2s</span></div>
  <div class="ln fail"><span class="t">09:42:38</span><span class="s">fail</span><span class="m">batch 6/8 rejected · schema changed on issued_at</span></div>
</div>
```

- Timestamp `--muted` (recedes most), lowercase severity `--text` (or its signal colour), message
  `--text`. Only a failing line's message goes `--bright`, so failures are easy to scan for.
- No row backgrounds, left stripes or icons. Under 640px each line runs inline.

## 8 Command block

```html
<div class="cmd"><span class="p">$ </span><span class="in">sync --dry-run</span>
  48,200 rows read
  288 duplicates
<span class="p">$ </span><span class="in">_</span></div>
```

- `--surface` panel, 13px; prompt `--muted`, typed command `--bright`, output `--text`.
- `white-space:pre` is what keeps the lines (`pre` works too). Reproduce output exactly as the
  program printed it. No syntax highlighting. A trailing `_` cursor is static: it never blinks.

## 9 Spec sheet

```html
<div class="spec">
  <span class="lbl">Region</span><span class="dots" aria-hidden="true"></span><span class="val">eu-west</span>
  <span class="lbl">Retention</span><span class="dots" aria-hidden="true"></span><span class="val">30 days</span>
</div>
```

- Label `--muted`, dotted `--rule` leader, value `--bright`. For under about ten short flat facts;
  anything compared across rows is a table. Values never wrap. Under 640px the pair stacks.

## 10 Meter

```html
<div class="meter"><span class="label">quota</span>
  <span class="track"><span class="fill" style="width:34%"></span></span><span class="val">34%</span></div>
```

- 8px square track in `--rule-dim`, fill in `--accent` (a data mark). The printed value in
  `--bright` is required: a bar without its number is decoration.
- Fill turns `.warn` above a stated threshold and `.fail` at breach. No animation, rounding or
  label inside the bar. Track and fill are blocks; as inline spans a % width renders empty.

## 11 Sparkline

```html
<div class="spark">
  <svg width="180" height="24" viewBox="0 0 180 24" role="img"
       aria-label="Sync latency, 14 days, flat near 8ms then rising to 21ms on the last day">
    <polyline fill="none" stroke="var(--muted)" stroke-width="1" points="0,16 42,14 84,15 126,10 166,9 176,3"/>
    <rect x="174" y="1" width="4" height="4" fill="var(--accent)"/>
  </svg>
  <span class="br">21ms</span><span class="sub">14d</span>
</div>
```

- 1px `--muted` line, no fill, axis or grid; a 4px `--accent` square on the latest point only.
- Fixed 180 by 24 box so sparklines stack and compare; never stretch one to fill the width.
- Colours as `var()`, never literals, or they break on paper. The `aria-label` states shape, range
  and endpoint. Never a signal colour on a chart; a meter is the one mark that turns warn or fail.

## 12 Note

```html
<div class="note warn"><div class="h">Caution</div><p>Backups paused until the disk is replaced.</p></div>
```

- 1px left rule and a 24px indent; no background, icon or card. A coloured note is a signal use:
  system state only, never to make prose feel important. More than two on a page is too many.

## 13 Tree

```html
<pre class="tree"><span class="d">exports/</span>
<span class="g">├─</span> <span class="d">2026-10/</span>
<span class="g">│  └─</span> ledger.csv      <span class="k">48,200 rows</span>
<span class="g">└─</span> README.md</pre>
```

- Box-drawing characters in `--muted`; folders `--bright` with a trailing slash, files `--text`,
  notes `--muted`. Always a `<pre>`; never nested lists. Here the glyphs are content.

## 14 Field and button

```html
<div class="field"><label for="ref">Reference</label><input id="ref" type="text" placeholder="INV-0042"></div>
<button class="btn" type="button">Issue</button>
```

- The field is a `--surface` well with a single `--muted` underline; no box or radius. Every field
  has a visible label; a placeholder (`--muted`) is never the label.
- Buttons are a 1px `--muted` outline with uppercase `--text`; hover lifts to `--bright`. **Nothing
  is filled**, not even the main action: a filled accent button would be a fourth accent use.
  Order and wording make the main action clear.
- Destructive actions are ordinary buttons behind a confirmation that states the result in
  `--signal-fail`. Disabled drops to `--rule` on purpose: an inactive control is exempt from the
  contrast floor, and the only place `--rule` is text.

## States

| State | Treatment |
| :--- | :--- |
| Link | `--bright`, dashed `--rule` underline; on hover it goes solid `--bright` |
| Focus | 1px `--accent` outline, 2px offset (accent use 3) |
| Hover on a control | one step up the ramp: `--text` to `--bright`, edge `--muted` to `--text` |
| Disabled | `--rule` text, `--rule-dim` edge |
| Selection | `--bright` ground, `--canvas` text (not the accent) |
| Loading | the word "loading" in `--muted`; no spinner, skeleton or shimmer |
| Done | the control's verb in the past tense: "Issue", then "Issued" |

## A new pattern

Only when nothing above fits. Before using it, answer three questions in the reply: which step of the
brightness ramp carries its emphasis, what it does at 375px, and what a screen reader gets.
