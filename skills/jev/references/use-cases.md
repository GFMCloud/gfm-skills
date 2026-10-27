# Where Jev fits: twelve shapes

## Contents

- The gate every shape shares
- Shapes 1 to 11: fits
- Shape 12: a weak fit, measured
- Never a fit

Use this in step 1 to name a candidate's shape and in step 2 to check its fit signals. Doc paths are
pages under `https://docs.typesafe.ai/` as listed in its `llms.txt` in October 2026 (add `.md` for
Markdown); their numbers are the vendor's claims. "Measured" means one project's live calls in
September 2026 (see question-design.md).

## The gate every shape shares

Can code assemble, in full, the evidence the decision turns on? If yes, read on. If getting it
takes research, the shape doesn't matter: it is a weak fit or no fit.

## Fits

| # | Shape | Looks like in a project | Evidence code assembles | Question pattern | Fit notes |
| ---: | :--- | :--- | :--- | :--- | :--- |
| 1 | Routing and intent | tickets, messages or requests sent to one of several handlers | the message, plus account or order fields | one Choice over the handlers with a `none` option; confidence decides act or ask | strong when the handlers are a fixed list; weak when the right handler depends on history the message lacks |
| 2 | Record matching and dedupe | "same person, product or company as that one?"; fuzzy scores with a tie-break; a review file of hard pairs | the new record and each candidate, field by field | a Noul per pair with a threshold and a review band; or, when a cheap matcher already ranks candidates, its top three in one Choice with `none` | the strongest general fit: both records are already in code. Judging only the matcher's first pick can't recover when the matcher picked wrong |
| 3 | Checklist and compliance screening | one document checked against a list of conditions (policy, review checklist, spam signals) | the document, split into named fields where it can be | one Noul per condition, all in one call; combine in code | strong when each condition is visible in the text; a condition needing outside facts gets a lookup step first |
| 4 | Scoring and priority | "how urgent or severe is this?"; a ranked queue | the item | one Score per dimension, levels that describe situations; weights in code | good when dimensions are independent; if you can't describe each level distinctly, the dimension isn't ready |
| 5 | Which record applies | choosing which rule, document or passage bears on an item; re-ranking search results | the item and a shortlist of candidates in full | a Noul per item-candidate pair ("aimed at the same problem?"), sorted | a cheap front end for other shapes. Measured: it named the exact rule for both contradiction items (0.89, 0.79) |
| 6 | Checking an extraction against its source | an extracted field, citation or quoted figure that needs a check | the source text and the extracted value | a Noul per field; failures go to a stronger model | strong; the source is already in hand. Compare numbers and dates in code |
| 7 | Walking a taxonomy | a deep category tree (product codes, a catalogue) | the item and the tree | one Choice per level; keep the top two branches when the split is close | good when each level's options are distinct |
| 8 | Gating an agent's action | an agent or script about to act: confirm, act or abstain | the request and the available actions | Choices over actions and closed-set arguments; a Noul flags destructive actions with a stricter bar | sends request or screen content on every turn; check the data rule first |
| 9 | Finding a place in a document or repo | "where does this handle X?" | the document in numbered blocks, or a file tree | a Choice over block or file ids, plus a Noul "is the answer here at all?" | good for long, structured text |
| 10 | Features for another model | free text that should become numeric inputs | the item | many Nouls and Scores as features; the downstream model learns weights | needs a labelled set large enough to train on |
| 11 | Guarding an LLM's input or output | screening prompts or replies before they reach a user or tool | the prompt or reply | hazard Nouls plus a severity Score; pass, review or block in code | validate every response before trusting it |

Docs pages behind these shapes (October 2026): `patterns/intent-routing`, `patterns/composite-scoring`,
`patterns/confidence-routing`, `primitives/choice`, `primitives/noul`, `primitives/score`, and the
cookbooks for entity alignment, parallel questions, re-ranking, citation checks, hierarchical
classification, function calling, semantic find, feature discovery and LLM guardrails.

## 12. Novelty and contradiction against a rulebook (a weak fit, measured)

- **Looks like:** "is this idea already covered by what we have, does it extend it, or does it say
  we're wrong?"
- **What happened:** Jev separated "same problem or not" and caught contradictions an item stated
  outright. It could not reproduce the "covered versus extends" call, which turned on whether the
  extras mattered to the person deciding, and it missed contradictions whose deciding fact came from
  documents fetched during verification.
- **Verdict:** weak, because the evidence takes research to assemble. Use shape 5 to point a person
  at the right record, and leave the final call with whoever does the verification.

## Never a fit

- Writing, rewriting or summarising text: Jev returns probabilities, not prose.
- Arithmetic, counting and comparing dates: code.
- Anything whose deciding fact must be fetched or reasoned out in several steps.
- Data the user's data rule doesn't allow to leave the machine.
