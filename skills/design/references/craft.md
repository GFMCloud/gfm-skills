# Craft rules

## Contents

- Hierarchy
- Type
- Space and layout
- Colour
- States
- Motion
- Phone
- Accessibility floor
- Tells of generated design
- Audit checklist

## Hierarchy

- Each screen has one main action. It gets the primary colour and the strongest weight; everything
  else steps back. Two equal buttons side by side means a decision wasn't made.
- Rank by size, weight, colour and space, in that order. Reach for a box, border or shadow last.
- Group by proximity. Related things sit closer to each other than to the next group.
- Cut before you style. A section nobody would miss makes the rest weaker.

## Type

- Two families at most; one is usually enough. System fonts are a fine default.
- Five sizes at most, from a ratio (for example 1.25), not picked one by one.
- Body text 16px or more on screens, line height about 1.5, line length 45 to 75 characters.
- Headings tighter (line height about 1.15), sentence case, no full stop.
- Left-align running text. Centre only short, standalone lines.
- Use weight and size for emphasis; avoid underlines that aren't links and all-caps paragraphs.

## Space and layout

- One spacing scale (for example 4, 8, 12, 16, 24, 32, 48, 64) and nothing off it.
- More space between groups than inside them. Generous outer margins read as confidence.
- Align to a few edges. Every new left edge is visual noise.
- Prefer a single column on phones and a clear grid on wide screens. Constrain text width even
  when the screen is wide.
- Use real content when laying out; placeholder text hides the real lengths.

## Colour

- Build from the brand tokens. Neutrals carry most of the page; the primary colour marks the main
  action and current state; the accent is rare.
- Text contrast at least 4.5:1 (3:1 for text 24px and up, and for icons and field borders).
- Never use colour alone to carry meaning: pair it with text or an icon.
- Tint neutrals slightly toward the brand hue instead of pure grey if it helps them belong.
- Dark mode, if asked for, is its own palette: lower the saturation, don't just invert.

## States

Every interactive element and every data view needs its states designed, not left to defaults:

- Controls: default, hover, focus (visible, not removed), active, disabled.
- Forms: empty, filled, invalid with a message next to the field saying how to fix it, submitting,
  success.
- Data views: loading (skeleton or spinner with words), empty (what it is and the first action to
  take), error (what happened and what to do), partial, and very long content.
- Write the words for each state. "Something went wrong" alone is not a state.

## Motion

- Motion explains a change (where something came from or went). If it explains nothing, drop it.
- Short: 150 to 250 ms for most changes, ease-out for things entering.
- Animate `transform` and `opacity`, not layout properties.
- Respect `prefers-reduced-motion`.

## Phone

- Design at 390px wide first, then widen. No horizontal scroll at any width from 320px up.
- Tap targets at least 44 by 44 px, with space between them.
- Text no smaller than 14px; inputs 16px so phones don't zoom on focus.
- Put the main action where a thumb reaches it, and keep it visible.
- Tables become stacked rows or scroll inside their own box, never the whole page.

## Accessibility floor

- Semantic elements: `button` for actions, `a` for navigation, headings in order, one `h1`.
- Every field has a `label`; every meaningful image has `alt`; decorative images have `alt=""`.
- Keyboard: everything reachable, in a sensible order, with a visible focus style.
- Set `lang` on `html` and a real `title`.

## Tells of generated design

These make a page look machine-made. Avoid them unless the brief asks for one on purpose:

- A purple-to-blue gradient hero, gradient text, glowing blobs.
- Emoji used as icons, or an icon on every heading.
- Everything centred; three identical feature cards in a row; the same section shape repeated.
- Rounded corners and soft shadows on everything, glass panels, borders around every group.
- Copy like "Unlock the power of", "Seamless", "Elevate your"; invented testimonials, logos and
  metrics.
- Many accent colours, each used once.
- Dark background with neon accents as the default look.

## Audit checklist

For a redesign or critique, go through these in order and note each problem with its location:

1. Does it work at 390px wide? Any horizontal scroll, overlap or cut-off text?
2. Can every control be reached and seen with the keyboard? Is every field labelled?
3. Is text readable: size, contrast, line length?
4. Is the main action obvious within a second?
5. How many type sizes, spacing values, colours and corner radii are in use?
6. Are empty, loading and error states designed?
7. Which tells from the list above appear?
