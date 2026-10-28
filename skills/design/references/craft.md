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
- Pages people read
- Juror passes
- Pictures
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

## Pages people read

For the steps marked *Page* in `SKILL.md`. A generated page looks like the average of its category;
these rules make it belong to its subject instead.

**Inventory.** Places to look: where the name comes from; the street outside and what you would see
standing in it; every number the brief gives (a count, a price, a distance, a founding year); the
limit the client works within (a season, a quota, an appointment book); what it is made of; what
happens at fixed times of its day; the paper of its trade (tickets, labels, timetables, menus).
Each item doubles as a search term for pictures.

**Claims before layout.** For each section, what it must prove and what proves it:

```
1. A ferry café open only while the boats run.  -> the timetable, large
2. Everything is baked on the island that day.  -> the oven at six, photographed
3. Coffee and a bun cost 4, cash or card.       -> price, the opening hours
```

If you can't write a claim for a section, it has no job on the page. Ordering the page by its claims
is also what keeps it off the familiar landing-page running order.

**Headlines.** No more than two lines at any width; the checker counts the titles (the page's `h1`
and each section's own `h1` or `h2`) at 1280px and 390px and is the judge for those (count the rest
in the screenshots). As a first estimate, a line holds the line width divided by 0.55 times the font
size, fewer in bold or serif faces: a 44px headline on a phone fits about 14 characters a line, so
keep the main one near 28. Shorten the words before you shrink the type. Section headings run two to
five words. Headlines that could top any page in the category: a fill-in-the-blanks template around
a buzzword, a run of single-word sentences, a denial of being "just" something, a familiar noun plus
"reimagined", a greeting.

**Frame.** `check_page.py --shots` measures these at 1280px and 390px (a huddled section at
1280px only):

- The page's content reaches equally far towards both edges. An off-centre layout is fine inside
  that frame; a frame that is itself lopsided is not.
- No section huddled on one side: a section whose text fills one half of a wide screen puts
  something of its own in the other half (an image, more text, a table) or is centred. A constrained
  text column (45 to 75 characters) sits centred in the page, or beside something.
- No stretch of the page over half a screen tall with nothing in it. A deliberate rest is a placed
  picture, once per page. Colour alone counts as nothing: an empty band, a gradient or a CSS
  shape is blank to the checker, so draw pictures as `img`, `svg`, `canvas`, an element with
  `role="img"` or an element's own `background-image: url(...)`.
- A visitor can read what this is in the `h1` without scrolling. A visually hidden `h1` (the
  screen-reader-only pattern) doesn't count: the title has to be seen.
- A visitor scanning for the menu, the prices or the hours finds each under its own heading (the
  checker catches sections of 30 words or more; check short ones in the screenshots).

## Juror passes

Run each pass on its own, on the screenshots, not the code.

1. **First look.** Close your eyes, open them on the first screen, and name the thing you saw first.
   It should be one thing. Then read it for five seconds as a visitor: can you say what this is,
   whom it serves and the next step?
2. **Blur.** Unfocus until text turns to grey shapes. Two or three shapes of plainly different
   weight means the page leads somewhere; a field of equal shapes means it doesn't.
3. **Competitor.** Put the nearest competitor's name on the first screen. If nothing else needs to
   change, the page has no idea of its own. Check the last sections too: the idea should still be
   there at the footer.
4. **Alignment.** Run your eye down the left edges of the text blocks and count the distinct
   starting positions. A few, reused, reads as designed; many reads as improvised.
5. **Frame.** The checker's five rules above, looked at in the pictures.
6. **Content.** Each section the brief asked for is there in full, at a size people can read.

Write each round down in the same shape, so the next round can be compared with it:

```
Round <n>: first thing seen <...>; idea <sentence>, competitor test <passes or fails, why>
1. <problem>, seen in <desktop or phone shot> -> <fix>
2. ...
3. ...
```

Each problem names a place and a measure ("the hours box sits 24px lower than the menu beside it"),
never a mood.

## Pictures

- Open collections: Wikimedia Commons, Openverse, and the open-access collections of museums and
  libraries. Use public domain, CC0, CC BY or CC BY-SA (share-alike: note it in the credit); not a
  non-commercial licence on a business's page.
- Ask before downloading. Name each picture with its source page and licence; download into the
  project only on a yes, and keep the source and licence beside the file.
- Credit each picture on the page, in a caption or a credit line in the footer: title, creator,
  licence, link to the source page.
- A found picture shows the world around the client (its street, its trade, its material). It is
  never captioned or placed as the client's own product, room, food or people.

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
- A pill badge above the headline ("New", "Beta"), tiny uppercase letter-spaced labels, feature
  cards each topped with an icon, and (more weakly) a small label above a heading.
- A headline that runs to more than two lines, or a full sentence set at display size.

The badge, capitals and icon-card line has numbers behind it. In [taste-skill's
study](https://github.com/Leonxlnx/taste-skill/blob/12af471f627f866411b4bd785b19646d3672784c/skills/taste-skill/references/research.md)
of 247 gallery sites (October 2026; scored by a panel of model reviewers from screenshots, not by
human jurors; 82 sites scored 7.5 or higher and 23 under 6.5 had enough text to measure), the top
sites used icon-topped feature cards 1% of the time against 28% for sites under 6.5, pill badges 14%
against 34% and tiny letter-spaced capitals 16% against 57%. Labels above headings (32% against 45%)
differ by only a few of the weak sites. The same study found monospace labels and 01/02/03 numbering
*more* often on the top sites and thin rules about as often, so none of them is a tell here; a
monospace system such as scrollback uses them on purpose.

## Audit checklist

For a redesign or critique, go through these in order and note each problem with its location:

1. Does it work at 390px wide? Any horizontal scroll, overlap or cut-off text?
2. Can every control be reached and seen with the keyboard? Is every field labelled?
3. Is text readable: size, contrast, line length?
4. Is the main action obvious within a second?
5. How many type sizes, spacing values, colours and corner radii are in use?
6. Are empty, loading and error states designed?
7. Which tells from the list above appear?
8. Frame: equal margins, no section huddled on one side, no blank stretch over half a screen, the
   `h1` on the first screen, a heading on every section.
9. For a page people read: could it belong to the nearest competitor?
