# Local offload: bulk mechanical work on a local model

The agent designs the job and checks it; a small model on this machine does the repetitive part.
It saves cloud usage on high-volume work and keeps the data on the machine. Running
`scripts/offload.py` (in this skill's folder) is part of using this skill.

## Contents

1. Does the task qualify?
2. Is a server running?
3. Design the prompt
4. Sample, then stop
5. Run the batch
6. Check and escalate
7. Report

## 1. Does the task qualify?

All four must hold. If any fails, or it is borderline, do the work yourself (or with cloud
subagents): checking a bad batch costs more than the batch saved.

- Twenty or more similar items.
- Each item is bounded: clear input, a fixed output shape, and nothing needed beyond what fits in
  the per-item prompt.
- A wrong answer shows on inspection; it is not quietly plausible.
- No rules or judgment per item.

**Never offload,** whatever the volume: money figures or valuations, anything that applies rules
or contract terms, text that will go to a customer or the public, and anything where a
plausible-but-wrong answer would flow on unnoticed. The local model may extract or tag; the
judgment built on its output stays with you.

Sensitive data (customer records, finances, health, private notes) is a reason to offload locally
rather than send it to a cloud service, but the four checks above still apply.

## 2. Is a server running?

```
python3 <skill>/scripts/offload.py --check                    # Ollama on 127.0.0.1:11434
python3 <skill>/scripts/offload.py --check --api openai --host http://127.0.0.1:1234   # LM Studio
python3 <skill>/scripts/offload.py --check --api openai --host http://127.0.0.1:9931   # llama.cpp server
```

Ports are each server's default as of the date in `models.md`; use the one the user's server
actually listens on.

`<skill>` is this skill's folder. If the script says the connection was blocked, your agent's
sandbox is stopping local network: that says nothing about the server. Ask the user to run the
check outside the sandbox (or to allow it), and stop there; don't retry it outside the sandbox
or widen the sandbox yourself, even where your agent offers a way to.

If nothing answers, or no suitable model is loaded, say so and ask: start the server, pull a
model (name it and its download size), or do the work in the cloud.
Never install, pull or start anything without a yes, and don't quietly do the bulk work yourself
instead: that skips the point of asking. Prefer the largest instruction-tuned model already present.

## 3. Design the prompt

Write `PROMPT.txt` beside the task (not in this skill's folder), with `{input}` where each item
goes. It must:

- Lock the output: one JSON object with named keys (run with `--keys`), or one line.
- Say "Output only the answer, with no preamble or commentary."
- Keep names, numbers, dates and paths exactly as written.
- Give the escape: "If the item is ambiguous or you cannot tell, answer exactly UNSURE." With
  `--keys`, Ollama can only return JSON, so say instead: "If you cannot tell, set every key to the
  string UNSURE." The script escalates either form.

Turn the items into `ITEMS.jsonl`, one `{"id": ..., "input": "..."}` per line. The script refuses
the whole batch if any item is empty, blank, duplicated or not JSON, and sends nothing: a model
given nothing answers with confident nonsense.

## 4. Sample, then stop

Run 5 to 10 items, choosing some messy ones on purpose with `--only id,id,...` (or `--sample 8`):

```
python3 <skill>/scripts/offload.py --model <name> --prompt PROMPT.txt --input ITEMS.jsonl \
  --out RESULTS.jsonl --keys <a,b,c> --only <ids>
```

Show the user each input beside its output. **Stop and wait for a yes** before the full batch. If
the prompt changes after the sample, start a new `--out` file; the script refuses to mix answers
from two prompts or two models in one file.

## 5. Run the batch

The same command without `--only`. It skips items already answered, writes each answer as it
arrives, checks every answer's format, and marks any answer whose reported model differs from the
one asked for (a silent fallback is a failure, not a result). Temperature defaults to 0.1 so
reruns match. A rerun retries items that errored (server down, timeout); UNSURE and bad-format
answers are kept and escalated, not retried. A large model's first load can take minutes: raise
`--timeout` (seconds, default 120) rather than reading three timeouts as a dead server.

Exit codes: 0 done; 3 done but more than 10 percent escalated; 4 server stopped or model missing;
2 bad input.

## 6. Check and escalate

- Format is checked on every answer by the script.
- Content: check every ID the summary lists under "Spot-check" (5 percent, at least 10) against its
  source item yourself.
- Everything in `RESULTS.escalate.jsonl` (UNSURE, bad format, wrong model, errors) you handle one
  by one. The local model escalates; it never guesses.
- Over 10 percent escalated means the task wasn't suited to a local model, or the prompt needs
  work. Stop and say so rather than grinding on. Classes where UNSURE is the right answer (two
  people with the same initials) don't count against that limit; say which ones you excluded.

## 7. Report

```
Local offload: <model> on <server>; <n> items; <ok> ok, <n> escalated (<pct>%), all handled
Spot-check: <k> checked, <k> right
Output: <path>
```

Leave the results and escalation files with the task; they are the record of what ran.
