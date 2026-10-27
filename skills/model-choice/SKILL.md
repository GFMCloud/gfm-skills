---
name: model-choice
description: Use when asked which model or effort fits a task, subagent or project, whether a job is worth a multi-agent workflow, to run bulk work on a local model (Ollama) so data stays local, or to have a strong model plan for a cheaper one, in Claude Code or Codex. Not for app code or second opinions.
compatibility: Model facts live in references/models.md with the date they were checked; rechecking them needs web access. Local offload needs a local model server (Ollama, LM Studio or llama.cpp) and Python 3.9 or later.
metadata:
  status: draft
  codex-check: "pending: not yet tried in Codex; must pass before stable"
---

# Model choice

Pick the cheapest model and effort level that will do the job well, and say how to run it. Model
names, prices and defaults change every few months, so **this file names tiers, not models**.
`references/models.md` maps each tier to today's names for each agent, with the date each fact was
checked. Never name a model from memory without saying so.

**Every pick ends with this block** (one per task; for a breakdown, the table in step 5; a local
offload or a split ends with the report its reference file gives):

```
Model: <name the user's agent accepts> (<tier>; facts as of <date>)
Effort: <level>
Run: <inline | N subagents on <model, effort> | split: <model> plans, <model> executes | local: <model> on <server> | workflow: <phases>, about N agents>
Why: <the one or two things about the task that decided it>
Set it: <the exact command, flag or setting in the user's agent>
```

## 1. Name the job

| The user wants | Do |
| :--- | :--- |
| A pick for one task, prompt or subagent | Steps 2 to 5, quick: answer in the block, nothing else |
| A pick per task across a project or task list | Steps 2 to 5, with the breakdown table |
| Bulk, repetitive work run on a local model | Steps 2 and 4, then `references/local.md` |
| A strong model to review or plan, and a cheaper one to carry it out | Steps 2 and 4, then `references/split.md` |
| Whether a task is worth a multi-agent workflow ("should I use a workflow for this?") | Steps 2 to 5, quick: score the **Workflow** row in step 4 and answer in the block |

If the request could be one task or a breakdown, choose from what they gave you (one task: quick;
a list or a whole project: breakdown) and say which in one line. Don't stop to ask.

## 2. Know what the user can run

- **Which agent:** Claude Code, Codex, or something else. Use the names and commands that agent
  accepts. If you can't tell, answer for the agent you are running in and say so.
- **Which models:** only recommend a model the user can reach. Your own context often lists the
  current models of the agent you run in; that counts as today's source for names. Otherwise read
  `references/models.md`.
- **Is the list fresh:** if `references/models.md` was checked more than 30 days ago, or your
  context names a model it doesn't list, recheck before naming a model: use the `research` skill if
  installed, or fetch the vendor pages the file lists. With no web access, use the file and write
  "facts as of <its date>, not rechecked" in the block.
- Prices and limits: quote them only with their date and source.
- If the built-in `claude-api` skill is loaded too, take Claude model IDs and prices from it, and
  keep the tier, effort and how-to-run decision here.

## 3. Size the task

Score each in a few seconds, low or high. Don't build a scorecard.

| Axis | High means |
| :--- | :--- |
| Thinking | Trade-offs, unclear requirements, design across several parts, debugging with no obvious cause |
| Stakes | Wrong output is costly or hard to undo: money, access, security, customers, production data, anything sent |
| Checking | Nobody reviews the output before it matters (unattended runs, scheduled jobs, bulk changes) |
| Volume | Ten or more near-identical items, each needing no judgment of its own |
| Context | The task must hold a very large amount at once (a big codebase, long documents) |

The tiers are **fast**, **everyday**, **strong** and **top** (`references/models.md` maps them
to models). Read the scores like this:

- **Mostly low:** fast tier, at the vendor's starting effort for it (`references/models.md`;
  often low or medium).
- **Well specified, some thinking, low stakes:** everyday tier at the agent's default effort.
- **Thinking or stakes high:** strong tier; raise effort when thinking is high. When axes disagree,
  the higher one decides the tier. Effort can still differ from tier: a high-stakes, low-thinking
  task suits the strong tier at moderate effort.
- **Top tier** only when the strong tier at high effort has fallen short, or for a long, hard,
  unattended run. Try more effort before a bigger model.
- **Checking high** counts as stakes one step higher, since nothing will catch the mistake.
- **Volume high** is a routing signal, not a tier signal: fan out to cheap subagents, a local model
  or a workflow (step 4), each slice sized on its own.
- **Context high:** a model with a large window, or subagents that each read a slice and report back.
- **Can't tell:** the vendor's starting point in `references/models.md`, and say so.

Mismatches to avoid, unless `references/models.md` gives a vendor reason: the strongest tier at its
lowest effort (pay for depth, then forbid it), the fast tier at maximum effort (more thinking won't
lift its ceiling), and the strongest tier everywhere "to be safe". Judge cost per finished task,
not per call: a cheaper model that needs two retries is not cheaper.

## 4. Choose how to run it

| Run | When |
| :--- | :--- |
| **Inline** | One coherent piece of work, steps that depend on each other, or too small to be worth a handoff |
| **Subagents** | Independent branches, ten or more like items, or a subtask that would flood the main context with raw detail. Give each a self-contained brief (it can't see this conversation), including the user's limits (where it may write files, what it must not run), and ask for a compact report. Size each one on its own; a mechanical slice can run on the fast tier under a stronger orchestrator |
| **Build and review** | High stakes: one agent builds, a fresh one checks against the success criteria. Give the reviewer the work and the criteria, never the builder's reasoning |
| **Split** | A large review or plan is worth the strong tier but carrying it out isn't. See `references/split.md` |
| **Local** | Twenty or more bounded, mechanical items, or data that should stay off a cloud service, and a local model server is running. See `references/local.md` |
| **Workflow** | A scripted run of many agents in phases, where the user's agent has such a feature (Codex: no; answer subagents or local). Score six things yes or no: twenty or more items; parallel runs save real time; independent agents checking each other add trust; results too big for one context; coordination (phases, routing) complex enough to belong in code; the job will be rerun. Four or more: workflow. Two or three: workflow with the misses named as caveats, or subagents. Under two: subagents or inline. It costs many agents' worth of tokens: give the rough agent count, say to try one slice first, and start nothing without the user's yes |

Pick the model at the start of a session, and change it at a boundary (a new session or subagent),
not mid-task: switching models mid-conversation throws away the cached context, and on some models
the earlier reasoning too, so the next turn costs more.

## 5. Answer and act

Quick: the block, and little else. If you had to assume something (which agent, what the task
involves), one line above the block says what; a checkpoint the user must act on gets one line.

Breakdown: one row per task that could sensibly run on a different model from its neighbours (not
"build the whole thing", not every small step). Use the user's own task list where there is one;
otherwise list the tasks coarsely from the request. Sequencing and estimates belong to a plan, not
here.

```
| Task | Model | Effort | Run | Why |
| :--- | :--- | :--- | :--- | :--- |
Checkpoints: <where a person should look before the next task, and why>
Set it: <commands or settings, once per distinct model and effort>
```

Acting on it:

- **Subagents you start:** set their model and effort yourself, as recommended. Codex has no
  per-subagent model setting: run each slice as its own `codex exec -m <model>` command instead.
- **The user's own session:** you can't switch the model you are running on. Give the command
  (`references/models.md` lists `/model`, `/effort` and the command-line flags for each agent).
- **Defaults in config files** (`settings.json`, `config.toml`): ask first. If the `agent-setup`
  skill is installed, that is its job.

Diagnosing a skill or prompt that does badly: swap the model one tier up or down with the prompt
unchanged before rewriting anything. If a stronger model doesn't help, the prompt is the problem.

## Where this stops

- Which model a product's own code should call through an API (model IDs, parameters, pricing for
  an app): the built-in `claude-api` skill for Claude where it is installed, otherwise the vendor's
  model documentation. This skill covers work your coding agent runs: sessions, subagents, batch
  jobs and handoffs.
- Independent reviewers for a decision or draft: the `second-opinion` skill, which picks its own
  reviewer models.
- A plan for one change before work starts: the `planning` skill. Work over many sessions: the
  `long-project` skill. The split here only adds who runs which part.
- Whether work is done, including a split's executed plan: the `proof-of-work` skill. The split
  adds only the follow-up plan (`references/split.md` step 7).
- News about a model ("is X out yet?", "what changed in Y?"): the `research` skill.
- Whether a tool, model pack or local runner someone shared is worth adopting: the `intake` skill.
- Writing the workflow script or prompt itself once a workflow is the pick: the user's agent's own
  workflow tooling. This skill only decides whether a workflow is worth it.
- Never install, pull or download a model, start a server, or change a default without asking.
