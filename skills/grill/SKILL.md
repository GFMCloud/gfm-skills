---
name: grill
description: Interviews the user in rounds until every decision in a design or idea is settled, each question with a recommended answer. Use before planning, for "grill me on this", "interview me hard" or "stress-test my thinking". Not for writing plans or independent reviews.
metadata:
  status: draft
  codex-check: "pending: not yet tried in Codex; must pass before stable"
---

# Grill

The output is a **settled decision list**, not a plan and not the work. Ask in rounds until no
decision is left open, then show the list and wait for the user to confirm it. **Write nothing and
change nothing before that**: no plan file, no notes file, no code.

The user asked to be questioned, so the questions are the product. Two ways to fail: asking the
user something you could have found out, and deciding something that was theirs to decide.

## 1. Read, then map the decisions

1. **Read what is already there**: the request, any file or folder the user points at, the
   project's README, notes, config and recent commits. Anything you can read is not a question.
2. **List the decisions** the subject needs, and for each, which other decisions it depends on
   ("where uploads live" depends on "which host"). This is the decision tree. Keep it to yourself
   unless the user asks to see it; show only one line naming the main branches before round 1, so
   the user can say "you missed X".
3. **Sort facts from decisions.**
   - A **fact** is something the files, a read-only command, the docs or the running system can
     settle: a version, what a config sets, how many jobs exist, what a service supports. Look it
     up yourself (a subagent, if you have them, for anything slow). Never ask the user for a fact
     you can find, and never ask for a password, key or token. A fact you cannot reach (no
     files, or it lives in the user's head) becomes a question marked "fact, unverified".
   - A **decision** is the user's call: a preference, a trade-off, a risk they accept, a budget, a
     deadline. Never settle one yourself, however obvious. Your view goes in the recommendation.
4. **A fact that contradicts the user is a finding.** If the notes say one thing and the files
   another, say which says what, with the file, and turn it into a question.

## 2. Ask in rounds

The **frontier** means the open decisions that depend on nothing still open. A round puts that
entire set to the user, and nothing outside it.

- **Never pair two questions in the same round when one answer could change the other.** The
  dependent question waits for a later round, however tempting.
- **A lookup still running blocks only the questions that need its result.** Ask the rest now.
- **One question per real trade-off.** Bundle small related choices into one question with a
  recommended set, rather than asking each.
- **No cap on questions per round.** If a round would still run past about ten, the subject is
  probably too big: say so and offer to grill one branch first.
- **Ask in your reply text, not through a question tool**, so the user can answer by number and
  explain.

Format every round like this:

```
Round <n>. Settled <x>, open <y>, waiting on lookups <z>.
Found: <each fact you looked up this round, with the file or command it came from, or "none">

**Q1. <short title>.** <the question, with the options if there are several>
Recommended: <your answer and the reason, briefly>

**Q2. ...**

Answer by number: "1 yes, 2 no because ..., 3 b". "Yes" accepts my recommendation.
```

- "Open" counts every decision not yet settled, asked or not.
- **Phrase every question so that a plain "yes" takes your recommendation.** "Keep Postgres on
  the new host?" with "Recommended: yes", never "Switch to MySQL?" with "Recommended: no".
- Give a real recommendation every time, with the reason. "It depends" is not one; say what it
  depends on and pick for the likely case. For a number or date only the user knows (a budget, a
  deadline), propose one and ask whether it holds.
- **Before you send, read every Recommended line.** If one starts with anything but "yes", reword
  its question so it does. Short replies are where this slips.
- Then end the turn and wait. Do not answer your own questions and carry on.

If the user asks for one question at a time, do that: the next single frontier question, same
format.

## 3. After each answer

1. **Record** each answer as settled, with the tag the decision list will use: "yes" settles the
   recommendation, tagged "accepted recommendation"; any other answer settles what the user said,
   tagged "user". "You decide" or "your call" settles your recommendation, tagged "delegated".
   If the user hands over the whole interview ("just decide everything"), ask at most one last
   round, only the decisions where a wrong guess would throw work away, then go to Finish
   (section 4) with the rest tagged delegated.
2. **Push back once** when an answer conflicts with a fact you found or an earlier decision: say
   what conflicts, in the next round, as a question. Don't nod along, and don't argue twice. That
   question is how the branch reopens. When the user keeps the new answer, or changes an earlier
   one themselves, re-settle what depended on the old one and say which decisions changed.
3. **A vague answer settles nothing.** "Maybe", "sort of", "later" leave the question open; ask it
   again, narrower or as a choice between two options.
4. **Unanswered questions stay open** and go back into the next round.
5. **Recompute the frontier** from scratch and ask the next round. Later rounds should ask things
   round 1 could not have asked; never ask a settled question again.

## 4. Finish

The interview is over once no open decision remains, or when the user says to stop ("wrap up",
"that's enough"). Then reply with:

```
Decisions
1. <decision>: <what was settled>. (<tag>)
...

Still open
- <decision left open, and what it blocks>   (or "none")

Is this our shared understanding? Say yes, or correct any line.
```

- `<tag>` is one of: user, accepted recommendation, delegated, fact: <file or command>, or
  fact: user, unverified (a fact the user told you that nobody checked).
- Stop there. **Do not act on the decisions in the same turn**: no implementing, no plan, no file.
- After the user confirms, offer the next step in one line: the planning skill turns the list into
  a plan; the second-opinion skill gets an independent view of a decision that is still risky.
- Save the list to a file only when the user asks: at the path they name, or `DECISIONS.md` in the
  project root if they name none. If that file exists, show what you would add instead of
  overwriting it.

## Borders with other skills

- Turning settled decisions into steps, a done-check and risks: the planning skill. It asks at
  most three questions on purpose; this skill has no cap and writes no plan.
- Independent views from reviewers who never saw the conversation: the second-opinion skill. This
  skill questions the user; it does not review on their behalf.
- Facts from outside sources (prices, whether a product still does X): the research skill. Look up
  inside the project yourself.
- Work that spans many sessions: the long-project skill. A decision question there can be settled
  with this skill.
