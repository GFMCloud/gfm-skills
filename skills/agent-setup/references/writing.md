# Writing for agents

Read this when you write or edit a skill or an instructions file, and for the writing check in an
audit (`SKILL.md` step 6). A line an agent reads either changes what it does or spends its attention
for nothing. The six checks below find the second kind; the last section is the audit.

## Contents

- The user's words come first
- 1. A description is a pointer
- 2. Delete no-ops
- 3. Name the target, not the ban
- 4. End each step on a check
- 5. Disclose by branch
- 6. Leave lookups to the environment
- Writing audit

## The user's words come first

These checks serve the user's request, and the request wins where they meet.

- A description keeps the phrases the user types and the phrases in the skill's should-prompts:
  weaker models load a skill only when its description holds those words (`skills.md`).
- A rule the user dictated keeps the user's wording unless they asked for a rewrite. Apply the
  checks to it only where they don't change its meaning, and say what you changed.
- A request to tighten, trim or clean up a file covers all six checks, not only deletion: rewrite
  each ban as its target (section 3) and each vague line as a check (section 4) in the same edit
  when the file already implies the target or the check. When it needs a choice the file doesn't
  make, propose the exact rewrite instead.
- When neither the request nor the evals say what the user types, keep a description's existing
  phrases and propose the cuts.
- When the request is to add or change one thing, apply the checks to the new lines. Weak lines
  you notice elsewhere go to the user as a proposal; trimming is a change only when asked for.

## 1. A description is a pointer

A skill's description, and an instructions line that names another file, is all an agent sees
before it decides to read further. Its wording, not the material behind it, decides when that
material loads.

- One phrase per branch. A branch is a distinct job the skill handles (add a rule, allow a
  command, check for overlaps). A second phrase for a branch already covered is a synonym: cut it,
  unless it is the user's own wording (see above). "Digest, synopsis, abstract, TL;DR" beside
  "summarise this PDF" is one branch written five times.
- Start each phrase with the word the user would type: the verb or noun of the request.
- Leave out what only matters once the skill is loaded (how it works inside, its history).

Done when: every branch the body handles has a phrase, and every phrase is one a user would type.
Length and the "Not for" line: `skills.md`.

## 2. Delete no-ops

A no-op is a line the model would follow with no instruction at all. It costs every run and changes
nothing. Test each sentence: without it, would a capable agent behave any differently? If not,
delete the whole sentence; trimming words from it keeps the cost.

The blatant ones are easy to see ("Be thorough", "Write clean code", "You are an expert"). The subtle
ones read like real steps:

- "Use the shell to run the commands below." Every agent with a shell does.
- "Reply in English." in a skill whose every input, template and example is English.
- "Save the file after editing it." Every edit tool saves.

Keep a line that sounds obvious when it carries something the agent can't know: a local convention,
why a choice was made, a failure the config gives no hint of ("build the CSS before the docs: the
docs embed the built file"). A weak word is a no-op too: "carefully" changes nothing; a check the step
must pass does.

When you and the user disagree about a line, an eval settles it: run the case with and without the
line (`evals.md`).

## 3. Name the target, not the ban

A ban names the unwanted behaviour, which puts it in front of the agent, and the agent half-follows
it. Write the behaviour you want instead:

- "Don't write long commit messages" becomes "Commit subject: one line, at most 60 characters."
- "Don't call the payments API directly" becomes "Take payments through `lib/checkout.ts`, which
  adds the retry and the audit log."

Subtle bans hide inside good steps: "Report each failing test by file. Don't paste the whole log."
The second sentence names the thing to avoid; say what to show instead: "For each failing test,
quote the failed assertion and its `file:line`."

A prohibition stays only as a hard guardrail with no positive form (never print a secret, never
force-push `main`), and then with what to do instead beside it. If a tool call shows the event, a
rule or hook enforces it (`guards.md`) and the line only gives the reason.

Done when: every "never", "don't", "avoid" or "no" left is a guardrail with its target beside it.

## 4. End each step on a check

Each step ends with what done looks like, in a form the agent can test (a line like "check the
result is right" names no test: replace it with one, or delete it): a command passes, a file
exists, every item of a list is accounted for. "Understand the module" has no end; "List every
caller of `parse_date` with its file and line" does. A demanding check ("every changed file
accounted for") makes the agent dig; a vague one ("produce a summary") lets it stop early.

## 5. Disclose by branch

The main file holds what every run needs: the steps, the required output, the hard rules. A
reference file holds what only some runs need, behind a pointer that says when to read it ("for a
hook, read `references/guards.md`"). Keep each topic's rule, reason and exceptions under one
heading; a reason three sections away from its rule gets lost.

Sprawl is a file long enough that its steps get lost, even when no single line is wrong. Signs: the steps
start after a screen of background; one branch's detail sits inline though most runs skip it; the
same meaning appears in two places (keep one, point to it from the other). A `SKILL.md` near its
500-line limit, or an instructions file near the 32 KiB that Codex loads, is sprawling.

## 6. Leave lookups to the environment

What one command or one file shows stays there: the scripts in `package.json`, the folder layout, a
tool's `--help`, what a formatter's config enforces. A copy in the instructions goes stale and costs
every run. Write down what looking can't find: a habit nobody wrote into config, why it holds, what breaks.

## Writing audit

For each skill or instructions file the audit reads, count first:

```
wc -l -w <file>
grep -o -i -w -E "never|don't|do not|avoid|not|no" <file> | wc -l
```

The grep's hits include "Not for" lines, comments, quoted output and words like "no-op"; the bans
are what is left once those are dropped, counted by reading. Report both ("6 negation words, 3
bans"). Then read the file sentence by sentence against sections 1 to 6 and report one block per
file in the form `SKILL.md` step 6 gives. A weak description is kind "pointer", a step with no
check is "no check". A file with nothing to report gets its count line and "nothing found". Change
nothing until the user picks the fixes.
