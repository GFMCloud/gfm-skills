# Step 1: inspect

The goal is material, not a tour: the product's real words, colours, fonts, images, and the two or
three moments of someone using it.

## A project

`scripts/scan_project.py` has already sorted the files. Read what it lists, in its order:

1. **The main page** (`index.html` or the app's entry page): title, headline, tagline, section
   headings, buttons, testimonials, menu items. This is the product's voice.
2. **Styles**: colour custom properties, background, text and accent colours, display and body
   fonts. The scan prints the ones it found; check them against the page.
3. **README and package file**: name, one-line description, features, "how it works".
4. **Routes, pages and feature components**: the form where work goes in, the editing screen,
   the page that shows the result. The strongest material is the product doing its job, not the
   landing page describing it. Name the flow as three beats: entry, key action, result.
5. **Images** in `public/` or `assets/`: logo, icons, screenshots worth reusing.

Never open what the scan skipped. It skips secrets and keys, environment files, files git ignores,
databases and data exports, build output and lock files. If the only copy of something you need is
in a skipped file, describe the gap in the plan instead of opening it.

A `WARN` line means a file the scan listed contains something that looks like a key or token. Read
that file, but leave that line out of everything you write.

## A website

Get the page as a visitor sees it. If a plain fetch returns an almost empty page (built by
JavaScript), load it in a headless browser, but only if one is available without installing
anything; otherwise say what came back and ask. Dismiss cookie banners by declining, and scroll
down in steps: sections that animate on scroll come out empty in a single full-page capture.

Collect: the page title and description, preview-card tags, the headline and tagline, headings
and feature names, button text and customer quotes; colours and fonts from the site's CSS; the
logo, product screenshots and demo videos (ask before downloading them, then fetch only what you
will use, into `work/`); and the entry, action, result flow from demos or "how it works" sections.

A website is someone else's content unless the user says it is theirs. Ask before using another
company's logo or footage in a video meant for posting.

## The nine questions

Answer all nine before planning; they become the top of `brag-plan.md`.

1. **What is it?** One sentence on what it does or claims to do.
2. **Best claim?** The line most likely to make someone react, quoted from the project, with its
   file.
3. **Visual hook?** The strongest visual: a striking colour, one piece of interface, a card, a
   diagram.
4. **What real UI to show?** Which screen or section would look best moving on screen.
5. **Shortest satisfying length?** Would 15 seconds land it, or does it need 22?
6. **Tone?** The user's preset or phrase; otherwise infer a preset and a short direction for this
   project (an absurd product suits `yc-parody`, an earnest one `polished`).
7. **Audio?** The role sound plays (warm bed, sparse accents, dense rhythm, deliberate silence).
   Default to music plus a few effects unless the user turned them off.
8. **Caption?** One draft sentence for `share-copy.txt`.
9. **Flow worth showing?** Entry, key action, result, as a real user goes through it. If the
   project is only a landing page, answer "none: landing page only" and lean on question 3.
