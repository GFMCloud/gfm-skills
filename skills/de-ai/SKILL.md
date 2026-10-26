---
name: de-ai
description: Edits prose that reads machine-written (stock phrases, forced threes, staged reveals, inflated claims, decorative formatting) into plain text, keeping every fact and the author's voice. Use when text sounds like AI wrote it. Not for judging authorship, summarising or translating.
metadata:
  status: draft
  codex-check: "pending: not yet tried in Codex; must pass before stable"
---

# De-AI

Make text read like a careful person wrote it: say the thing, once, plainly. This is editing, not
rewriting. The facts, the argument, the order and the author's voice stay.

**Return, in this order:**

1. The edited text, complete, in the same format it came in (Markdown stays Markdown).
2. `Changed:` one line per pattern fixed, with a count, for example `forced threes (2), stock
   phrases (4)`.
3. `Kept:` anything you deliberately left alone and why (a quotation, a term of art, a legal phrase).

If the text is already plain, say so and change little or nothing. Don't edit for the sake of it.

## Steps

1. **Read for meaning first.** Note every fact: names, numbers, dates, links, quotes, claims and their
   hedges. All of them must survive, unchanged.
2. **Mark the patterns** from [references/patterns.md](references/patterns.md). The common ones:
   - **Staging instead of saying:** "It's not X, it's Y", "Here's the thing:", a run-up before the
     point, a dramatic one-line closer.
   - **Rhythm by rule:** lists of three by habit, every sentence the same shape, em dashes as the
     all-purpose joint.
   - **Inflation:** "pivotal", "seamless", "a testament to", "in today's fast-paced world", claims of
     significance the facts don't carry, borrowed authority ("experts agree").
   - **Formatting by habit:** bold on phrases that aren't warnings, headings for two sentences,
     bullet lists for one thought, emoji as signposts.
   - **Chat residue:** "Great question!", "I hope this helps", "Let me know if...", "As of my last
     update".
3. **Fix with the smallest change** that removes the pattern: cut the stock phrase, state the point
   directly, replace the em dash with a comma, full stop, colon or brackets, unbold, merge the tiny
   section. Prefer deleting to rephrasing. When you cut a sentence that said nothing concrete, don't
   write a new claim in its place; if the text now needs a link, say so under `Kept:` for the author.
4. **Reread the whole thing** against your fact list. Every fact present, no fact added, hedges kept
   ("about", "may") where the author had them.

## Don't

- Don't touch code, commands, quotations, names, product terms or legal and regulated wording. List
  any tell inside them under `Kept:`.
- Don't add facts, examples, opinions or a conclusion the author didn't write.
- Don't fake a human: no planted typos, slang, or invented anecdotes.
- Don't say whether a person or a model wrote the text. Tells are habits of style, not proof of
  authorship; anyone can write this way.
- Don't change the user's own voice into yours. If the author is blunt, stay blunt; if formal, stay
  formal.
