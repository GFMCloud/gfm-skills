---
name: second-opinion
description: Gets independent second opinions on a decision, plan or draft from reviewers who never saw the conversation, and shows where they disagree. Use for go/no-go calls, tradeoffs, "am I anchored?", or checking work no test can check. Not for code review or facts.
metadata:
  status: draft
  codex-check: "pending: not yet tried in Codex; must pass before stable"
---

# Second opinion

A long conversation anchors everyone in it, including you. A second opinion is only worth having if
it comes from a context that did not see the first one. Independence comes from **what the reviewer
is given**, not from telling it to be neutral.

**First, pick the mode:**

| The user wants | Mode |
| :--- | :--- |
| A choice between credible options (ship or hold, A or B, "am I wrong?") | **Decide**: three voices |
| A finished draft checked before it goes out (copy, a document, a plan, a batch) | **Check**: two reviewers |
| A fact that can be looked up or computed | Neither. Answer it and say no panel was needed |

A draft that only needs checking against one source document is a plain fact check, not this skill
(`doc-vs-reality` in this library). Use **Check** when the user asks for independent reviewers, or
when the work must meet a rubric rather than match one source.

## How to get an independent reviewer

Use the first of these your agent offers, and say which you used:

1. **A fresh subagent** that gets only the brief, not the conversation (not a fork of this session).
2. **A fresh non-interactive run** of the agent's command-line tool, given only the brief file. This
   spends the user's usage; say how many runs before starting.
3. **Neither available:** say so plainly. Offer the brief as text the user can paste into a new
   session. If they want an answer now, do the review yourself, but label every part of it
   "not independent: same session".

Never fill in a missing reviewer yourself without that label. Each reviewer is a separate context;
reviewers never see each other's answers. Where you can choose the model, use one that differs from
the model that did the work; say which you used.

**The brief** holds the question or the draft, only the facts it needs (files, numbers, the spec),
and the reviewer's role. Leave out your reasoning, your preference and how the work was produced.

## Decide: three voices

1. **Write your own position first**, before any voice runs: the position, its three strongest
   reasons and its main risk. This stops the summary quietly becoming an echo of the voices.
2. **Run three voices**, each with the brief and one role:
   - **Skeptic:** questions the framing and the assumptions; proposes the simplest credible
     alternative, including "don't decide this now".
   - **Pragmatist:** cost, speed, who is affected and what actually happens on the day.
   - **Critic:** edge cases, downside, how the plan fails.

   Ask each to start with its role, then give: a position in one or two sentences, three short
   reasons, the biggest risk in its own recommendation, and one thing the others may miss. Under 300
   words.
3. **Combine under these rules.** Never dismiss a voice without a stated reason. Two voices against
   your position is a signal, not noise. Print the strongest dissent even when you reject it. Say
   whether your recommendation moved, and why.

```
## Second opinion: <short title>   (reviewers: <subagents | CLI runs | not independent>)
**You (written first):** <position>. <one line why>
**Skeptic:** <position>. <one line why>
**Pragmatist:** <position>. <one line why>
**Critic:** <position>. <one line why>
- Agree on: <where they align>
- Strongest dissent: <the disagreement that matters most>
- Recommendation: <the path, and whether it moved from your first position>
```

The decision stays with the user. One round is the default; for another, ask a narrower question.

## Check: two reviewers

1. **Write a rubric** from the spec: each line a criterion with an objective pass condition (every
   claim traces to the source, every requirement covered, names and numbers right, no rule broken).
   Drop or rewrite anything only taste can judge. Show it to the user if they did not give one.
2. **Run two reviewers in parallel**, each with the spec, the draft and the rubric. Tell them their job
   is to find problems, that they must judge every criterion, and to quote the exact text at fault.
   Each returns PASS or FAIL per criterion, with the quote.
3. **Gate:** it passes only when both reviewers pass every criterion. A problem only one reviewer
   found is still real; that miss is what the second reviewer is for.
4. **Fix only what was flagged.** No rewrites, no improvements nobody asked for.
5. **Review again with two new reviewers.** Stop after three rounds and hand the user the draft, the
   open issues and the round history.

```
Check: <title>   rounds: <n>   result: PASS | HANDED BACK
Round <n>: reviewer A <PASS|FAIL>, reviewer B <PASS|FAIL>; issues <n> (both found <n>, one found <n>)
Fixed: <list>     Open: <list or none>     Not covered by the rubric: <list>
```

This skill sends, publishes and merges nothing. If both reviewers pass everything on the first round,
say so and name what the rubric could not see.
