# Layout rules for the four slots

## Contents

- Canvas
- Zones
- Nodes and node classes
- Edges and labels
- DETAIL and FLOWS
- Common mistakes

## Canvas

The SVG is `viewBox="0 0 1560 980"`: abstract units, origin top-left, x right, y down. It scales to
any screen.

## Zones

One `<g class="zone" id="z-...">` per group, laid out as columns left to right in the direction data
flows. Title at `x+20, y+30`; optional caption 18 below. Leave 40 to 60 units between columns for
edges and labels. Four columns usually start near x = 40, 390, 800, 1190.

```html
<g class="zone" id="z-api"><rect x="390" y="120" width="360" height="720"/>
  <text class="ztitle" x="410" y="150">API</text><text class="zsub" x="410" y="168">the service we run</text></g>
```

## Nodes and node classes

One `<g class="node" data-k="...">` per component inside a zone. `data-k` is unique and needs a
`DETAIL` entry. Text at `x+20`; title at `y+30`, then a line every 18 to 22 units. A title plus two
to four short lines; anything longer goes in `DETAIL`.

| Class | Use for |
| :--- | :--- |
| (none) | most components |
| `hero` | the single most important component. Once per diagram at most |
| `store` | anything that holds data |
| `entity` | the thing the system produces |
| `ext` | external or third-party components (dashed border) |

Classes combine: `class="node store ext"`. Text classes: `t` title, `m` detail line, `k` one small
highlighted tag (use once).

## Edges and labels

Draw edges after nodes, from source to target. One `<path class="edge" id="e-...">` and one
`<text class="elbl" data-e="e-...">` per connection, with matching ids. Start and end on a node's
border, not its centre. Use a curve (`C`) to route around boxes, never through them. Add `dash` for
dependencies and look-ups that aren't the main path. Labels are one to three words near the
midpoint, nudged off the line.

## DETAIL and FLOWS

```js
const DETAIL = { api: { t:"Upload API", m:"the service we run", b:"One to three sentences. <b>bold</b> and <code>code</code> allowed." } };
const FLOWS = {
  "upload": { name: "Upload a photo", edges: ["e-app-api"], nodes: ["app", "api"], steps: ["First step", "Second step"] }
};
```

Each `FLOWS` key needs a matching chip, `<button class="chip" data-flow="upload">Upload</button>`.
Never define `all`; the engine provides "Everything". Two to five flows, one per distinct path.

## Common mistakes

- A label sitting on a node's text line. Nudge it away.
- Two hero nodes.
- Rewriting the whole file instead of editing slots in a copy, which can cut the engine off.
- Editing the `<style>` block, the engine script, or the theme script in the head.
