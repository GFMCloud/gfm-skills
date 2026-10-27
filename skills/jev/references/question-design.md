# Designing Jev questions

Rules for shaping the state, the questions and the criteria. Each rule carries the evidence behind
it. "Measured" means live calls on `jev-1.13.0` in September 2026, on one project: a weekly triage
of public posts, each judged against an agent rulebook (is this idea new, an extension, already
covered, or a contradiction?). That project turned out to be a weak fit (use-cases shape 12), so
treat every number as a dated example from one case, not a benchmark. "Docs" means TypeSafe's
documentation at <https://docs.typesafe.ai/llms.txt>; check the syntax there, not here.

## The three inputs

| Input | Its job | Rule |
| :--- | :--- | :--- |
| state | the evidence, plus whatever it is compared against | named fields; only what the questions need; full text, not titles |
| instructions | the question | one narrow question; point at state fields with backticks (`` `item.claim` ``); may be an object (`question`, `focus`) |
| criteria | the yardstick | Choice options as what / not_for / examples; Noul `true` and `false` when the line is subtle; Score levels that describe situations |

Jev judges only against what these say. The question id is never sent to the model, so the meaning
must be in the instructions.

## Evidence

1. **Hand over the records the decision is really made against, in full.** Measured: with only the
   names of the related rules, 5 of 15 known "already covered" items routed correctly; with every
   rule's full text, 10 of 15.
2. **A title is not a record.** A rule given as its heading alone gave Jev nothing to compare with.
3. **More text helps only when it holds the deciding fact.** Measured: a whole reference document
   turned one item right; long sections gave other items more to "dispute" and pushed them wrong.
   On average, fuller state scored 11 of 23 against 15 for the short form.
4. **Check the plumbing.** Measured: a length filter silently dropped the one rule an item
   contradicted. Print the record count per item and read a sample state (`evaluate.py --dry-run`).
5. **Use each record as it stood when the past decision was made.** A record added later leaks the
   answer into the test. Git history at the decision's date is the usual source.
6. **Jev does not fetch or reason a step further.** Measured: a contradiction found by reading
   outside documents was not found by Jev given only the item and the rule. Put any lookup or
   multi-step reasoning before Jev, in code or a stronger model.

## Questions

1. **One question, one property the state can answer.** Measured: a question mixing "same problem?"
   with "fully solved?" sent a whole class to the wrong route; split, results held steady across
   six trials.
2. **A question whose answers barely vary measures nothing.** Measured: one yes/no came back 0.07 to
   0.33 for every item, including the ones that should be yes. Rewrite or drop it; don't tune a
   threshold on it.
3. **Don't ask about intent the state doesn't hold.** "Would this change what we build?" depends on
   plans Jev never saw; it answered yes to nearly everything.
4. **Define every option, including where it stops.** Measured: with undefined labels, every
   "already covered" item came back "extends", several at 0.96 confidence or more. With not_for
   lines added, those became low-confidence answers a gate can catch.
5. **A failure the reference exists to prevent is not a contradiction of it.** Say so in the
   criteria; measured, an item describing such a failure read as a contradiction until it did.
6. **Rules phrased as prohibitions draw false disputes.** Measured: a "this project never does X"
   rule drew three false contradiction flags. Keep scope and ownership rules out of a dispute check.
7. **Choose the type by what code does with the answer.** Choice picks a branch, Score is compared to
   a threshold, Noul feeds an `if`. A Noul of 0.5 is a coin flip, not "medium".
8. **Give a way out.** The docs advise a `none` or `other` option on every Choice. Not measured: in
   the first test the way out was offered and not chosen; the useful signal was a confidence of 0.24.
9. **Numbers, counts and dates belong in code.** The docs' own list of weak spots (the "jaggedness"
   page for each model version) says so; have Jev pick parts, compare them in code.

## Reading the answers

- **Confidently wrong on a whole class:** the criteria draw a different line than the person who
  made the past decisions. Fix the definitions.
- **Unsure:** the evidence is thin or the case is borderline. Fix the state, or let the band send it
  to review.
- **Several narrow questions are steadier than one broad Choice** and easier to debug. Measured: 0 or
  1 label changes across three trials, against 2 or 3 for the single Choice. They did not raise
  agreement on their own.

## Measuring

- Fix the tuning and held-out split before writing the first question; keep criteria examples out of
  both.
- Report agreement with past decisions, never accuracy.
- Measured noise: seven runs of identical inputs scored 12 to 15 of 23. Rerun before believing a
  difference of a few items.
- A revision is tested on items it never saw. A held-out set used to guide a revision is no longer a
  clean hold-out; say so.
- Prove the fail-closed gate by deliberate failure (`test_questions.py`) before any real call.
