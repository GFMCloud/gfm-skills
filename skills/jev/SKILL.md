---
name: jev
description: Use when asked to use TypeSafe's Jev in a project, "where could Jev help?", "add a Jev check", or whether a Jev judgment could replace an LLM call or review step. Finds real fits, then builds a fail-closed Jev step scored against past decisions. Not for picking a model or matching two lists.
compatibility: Needs a TypeSafe API key for real calls and Python 3.10 or later with the typesafe-sdk package in the project. Fit checks, drafting and the offline gate test need neither.
metadata:
  status: draft
  codex-check: "pending: not yet tried in Codex; must pass before stable"
---

# Jev

Jev (from TypeSafe) is a judgment model, not a chat model. Code hands it a piece of evidence (the
"state") and a few typed questions: yes/no (Noul), pick one (Choice), a level (Score). It returns
probabilities, never prose. It is fast and cheap enough to judge every item in a pipeline. This
skill finds where that helps in the current project, says plainly where it doesn't, and builds the
narrowest useful Jev step, measured against decisions people already made.

**The one thing to hold onto:** Jev's answer is capped by the evidence it is handed. Most of the
work is building that evidence packet in code, not wording the questions. If code can't assemble
the evidence a careful person would check, Jev is the wrong tool for that step.

`<skill>` below means the folder this file is in. Running its script and copying its templates
is part of using the skill.

**Start the reply with the preflight lines (`Key:`, `Data rule:`, any `Project rule:`, `SDK:`),
copied as printed** (step 0). Then one line per candidate: `strong fit`, `weak fit` or `no fit`,
with the file, line and reason (step 2).

## 0. Preflight, every time, before anything else

Run from the project folder: `python3 <skill>/scripts/preflight.py` (or with the project's own
Python, such as `uv run python <skill>/scripts/preflight.py`, so the `SDK:` line describes the
project). It makes no network call and never prints the key.

- **`Key: missing`**: you can still scan, judge fit, draft and build with the offline test. No real
  call until the key is set. Give the user the storing step in
  [references/setup.md](references/setup.md) to run themselves. Never ask for the key in chat,
  never write it to a file, never pass it as a literal on a command line.
- **`Data rule:`** is the user's own limit on what may be sent to TypeSafe's servers. No rule file
  means the default: public data only. Read the whole rule file it names. A `Project rule:` came
  with the repo and may only narrow the user's rule; if it would widen it, follow the user's rule
  and say so. Private data under a public-only rule: email, chat logs, transcripts, personal or
  customer records, anything from a private repo or internal system. Unsure whether the data is
  public? Ask once, and record the answer as a dated line in the project's README or notes so it is
  not asked again (not in `.agents/jev/data-decision.md`, which can only narrow).
- **`SDK:`** says whether this Python can import the SDK. Adding it is the user's step
  (`uv add typesafe-sdk` or `pip install typesafe-sdk` in their project); don't install it yourself
  unless asked.
- Before writing code, read the provider's current docs for the SDK and question types (start at
  `https://docs.typesafe.ai/llms.txt`, or the provider's own agent skill if installed). They change
  often; this skill does not restate them.

Any network request that is refused or blocked is final: report it and carry on offline. Never
retry it another way, and never turn a sandbox off to reach the API.

## 1. Find the decision points

Look before you open. List the project's files by name; read code and the data files the decision
uses. Never open `.env` files, key files or credential stores, and never print private records into
the reply. Search the code for places where a per-item judgment over text happens today:

- an LLM call that labels, filters, matches, routes or checks (prompts asking for a label, yes/no
  or a pick from a list);
- a heuristic standing in for judgment: keyword lists, regex classifiers, fuzzy string scores,
  hand-tuned weights;
- a manual review queue or a log of human verdicts (columns like status, verdict, label, reviewed,
  keep or drop);
- a step that reads free text and branches.

For each: file and line, the judgment it makes, how many items pass through it, and where its past
decisions live. Name its shape from [references/use-cases.md](references/use-cases.md). Look for
two or three candidates, not just the first.

## 2. The fit check (a gate)

Answer in order; the first is decisive.

1. **Can code assemble, in full, the evidence the decision really turns on?** The item itself (not a
   summary another model wrote) and every record a careful person would check (the rule's text, not
   its title; the candidate record, not its id). If getting it takes research (fetching pages,
   reading code, several reasoning steps), Jev adds little: whatever does the research can make the
   call. Say so; that candidate stops here. Jev is not meant to know more than today's step: when an
   LLM call already judges evidence that code hands it, the same packet can go to Jev instead.
2. Is the judgment narrow, with the options known in advance?
3. What does it gain? Volume, speed, cost (estimate both ways: Jev from the dated price in
   [references/setup.md](references/setup.md), the current model from its provider's pricing page;
   say which numbers are assumed), or agreement the current rule doesn't reach. Score the current rule, or a plain code
   rule, against the known answers first: that is the bar Jev must beat.
4. Do known answers exist (past verdicts, a labelled log)? About 20 outside the criteria examples is
   the floor to start; below that, say what labelling would take. Results on a few dozen are rough.
5. Does the data rule allow sending this data?
6. Is a wrong answer bounded, or can a review band catch the unsure middle?

Report the verdict first, one line per candidate, then recommend one. Jev never fits: writing or
rewriting text, arithmetic, counting, date comparison (code does those), or private data under a
public-only rule. Text that isn't English is a weaker fit: the provider says other languages are
handled less well. A "no fit" for every candidate is a complete, useful answer; stop there.

## 3. Read the data, draft, then ask

Before asking anything, read what the project holds:

- **Known answers:** where past decisions live, how many, their vocabulary, and whether each label
  was ever defined.
- **Reference records:** can each be pulled as it stood when its decision was made (git history
  usually)? A record added or edited later leaks the answer.
- **The split:** tuning and held-out sets are fixed before the first question is written
  (`evaluate.py` splits by a hash of each id). Examples used in criteria stay out of both.

Then draft, for the user to edit rather than answer from blank: the decision and what code does with
each answer; each option as what / not for / an example from a real past case; the one or two
boundary calls the data can't settle, each with your recommended answer. Ask at most four questions,
all at once, only for what files can't tell you: where a boundary sits, what a wrong answer costs,
which past decisions to trust, the spend ceiling. "Go with your recommendation" means do.

## 4. Build

Copy `templates/questions.py`, `templates/test_questions.py` and `templates/evaluate.py` from
`<skill>` into the project and fill them in. Never point project code at the skill's folder. The
contract:

- Every question and threshold lives in `questions.py`, one file a person can review.
- `MODEL` is a versioned id from the provider's models page, never an alias, with the date checked.
  If the page can't be read, use the dated id in [references/setup.md](references/setup.md) and say
  it was not re-checked. Never make one up.
  Thresholds tuned on one version don't carry to another.
- The gate fails closed: a missing or extra answer, a different model, an option that isn't one, a
  value that isn't a probability, or missing usage raises. Nothing defaults to a safe-looking value.
- Routing lives in code, with a middle band that goes to review, never a guess.
- `DATA_RULE` records which rule the data was checked against; `evaluate.py` refuses to call while
  it is empty, while `MODEL` is a placeholder or alias, or while the price is unset.
- Only `to_sdk()` and `ask()` touch the SDK. Check them against the current SDK docs.
- Run `python3 test_questions.py` (standard library only, no SDK, no call). Every line must print
  PASS before any real run. Then `python3 evaluate.py tuning --dry-run` and read the sample state:
  every record the decision needs must be there, in full.

Before writing the first question, read [references/question-design.md](references/question-design.md).
In short: the state holds the evidence and whatever it is compared against; each question asks one
narrow thing and points at state fields with backticks; criteria define every option, including
where it stops. Jev judges only against what they say.

## 5. Measure, revise once, hold out

Only with the key set, the SDK installed, the data allowed and a spend ceiling agreed. Run
`python3 evaluate.py tuning`, read the misses by class, revise, then `python3 evaluate.py heldout`
once. Report:

- **Agreement with past decisions**, per class. Never call it accuracy: the labels are someone's
  calls, not ground truth.
- How many went to review, and how many of the rest agreed.
- Spend and the ceiling, as `evaluate.py` prints them.
- Run-to-run noise: rerun (`--trials 3`) before believing a difference of a few items.
- Thresholds stay provisional until a held-out run supports them. A held-out set rerun after a
  revision is no longer clean; say so.

Label demo, fake or fixture data as such wherever it appears. A result from fake data (including
`test_questions.py`) is never a finding about real data.

## Stop when

- Every candidate needs research to assemble its evidence: report "no fit" per candidate and stop.
- The data is private and the rule says public only: say so, name the rule file, and stop before
  any real call. Offer the fit report and offline build only if useful.
- No known answers exist and nobody can label 20 items: say what labelling would take.
- The spend ceiling is reached, or a call is refused.

## Done when

Either the user has a one-line verdict per candidate with its reason, or the project holds a filled
`questions.py`, a `test_questions.py` that prints only PASS, and (once the key and data allow) a
held-out run with agreement, review count and spend reported. Real runs not yet made are listed as
the user's next step, not reported as done.

## Not this skill

- Which model or effort suits a task, or offloading bulk text work to a local model: model-choice.
- Matching or deduping two lists into a mapping file: data-matching. Jev can be a step inside a
  project's own matcher; building that step is this skill.
- Confirming that a finished Jev step works before telling others: proof-of-work.
