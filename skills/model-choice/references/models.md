# Models, tiers and settings

**Checked: 2026-10-26.** Everything here goes stale. Before naming a model, compare that date with
today: past 30 days, or if your own context names a model this file doesn't, recheck the pages in
Sources (the `research` skill does this well) and say which facts you rechecked. Vendor model pages
carry no dates; changelogs do.

## Contents

- Tiers
- Claude Code
- Codex
- Local servers
- Sources

## Tiers

The skill names tiers; this table maps them to today's models. A tier is a job description, not a
price band.

| Tier | For | Claude Code (Anthropic API) | Codex (ChatGPT sign-in, paid plans) |
| :--- | :--- | :--- | :--- |
| fast | Mechanical, well-defined, high-volume work; narrow subagent slices | Haiku 5.5, alias `haiku` | GPT-6 Luna, `gpt-6-luna` |
| everyday | Well-specified coding, drafting, analysis; most subagents | Sonnet 5.5, alias `sonnet` | GPT-6.1 Sol, `gpt-6.1-sol`, at low or medium effort; GPT-6.1 Terra, `gpt-6.1-terra`, for writing and visual work |
| strong | Unclear requirements, design across parts, high stakes, long agentic coding | Opus 5.5, alias `opus` | GPT-6.1 Sol at high or xhigh effort |
| top | The hardest reasoning and multi-hour unattended runs, after the strong tier at high effort fell short | Fable 5.1, alias `fable` | Astra, `gpt-6-astra` |

Vendor starting points:

- Anthropic: "start with Claude Opus 5.5 for most workloads", moving to Fable 5.1 when evals at
  `xhigh` or `max` effort still fall short; "Tuning effort is often a better lever than switching
  models." Haiku 5.5 is named for classification, extraction, routing and subagent tasks.
- OpenAI (Codex): if no model is set, the client uses a recommended default. Sol is "a lower-cost
  option with near-Astra performance"; Luna suits "focused, repeatable tasks"; Terra suits writing,
  visual understanding and computer use (needs Codex CLI 0.159.0 or later; the Codex changelog
  of 2026-10-26 lists it for Plus, Pro, Business, Enterprise and Edu). (Paraphrased from the
  Codex models page and changelog.)

List prices per million tokens, input / output, 2026-10-26 (API rates; subscription plans count
usage differently):

| Claude | Price | Note | OpenAI | Price |
| :--- | :--- | :--- | :--- | :--- |
| Fable 5.1 | 10 / 50 USD | cache reads 0.025x input | Astra | 10 / 50 USD |
| Opus 5.5 | 4 / 20 USD | cache reads 0.05x input | 6.1 Sol | 2 / 10 USD |
| Sonnet 5.5 | 2 / 10 USD | cache reads 0.05x input | 6.1 Terra | 1 / 5 USD |
| Haiku 5.5 | 0.10 / 0.50 USD | 0.50 / 2.50 over 100K-token prompts | 6 Luna | 0.10 / 0.50 USD |

All four Claude models and all four OpenAI models listed have a context window of about 1M tokens.

## Claude Code

Effort levels: `low`, `medium`, `high`, `xhigh`, `max` on the 5.x models. Claude Code's default is
`medium` on Opus 5.5, Sonnet 5.5 and Haiku 5.5, and `high` on Fable 5.1. (The API's own default for
Sonnet 5.5 is `high`; the two pages differ because Claude Code sets its own.) Anthropic's starting
advice: Sonnet 5.5 at `medium` for well-specified agentic coding, `high` for harder or longer work;
Haiku 5.5 at `medium`; Fable 5.1 at `high`. `xhigh` is for long agentic runs (over 30 minutes).

| To set | How |
| :--- | :--- |
| Model, this session | `/model <alias or full ID>` |
| Model, at launch | `claude --model <alias or ID>` |
| Effort, this session only | `claude --effort <level>`, or `s` in the `/effort` slider |
| Effort, saved as your default | `/effort <level>` (typing a level saves it); `/effort auto` clears it |
| Default model and effort | `model` and `effortLevel` in `settings.json` (`effortLevel` takes up to `xhigh`, not `max`) |
| A subagent | `model:` (`haiku`, `sonnet`, `opus`, `fable`, a full ID, or `inherit`) and `effort:` in its definition's frontmatter; a per-call model parameter overrides the definition |
| All subagents | `CLAUDE_CODE_SUBAGENT_MODEL`; built-in Explore and Plan ignore it unless `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` |
| Plan on one, execute on another | the `opusplan` alias: Opus in plan mode, Sonnet after |
| One deeper turn | put `ultrathink` in the prompt (runs that turn at `xhigh` on the 5.x models) |

Aliases follow the newest model of their family; pin a full ID (for example `claude-opus-5-5`) to
stop that. Aliases differ on Bedrock, Google Cloud and Foundry, where `sonnet` and `haiku` can mean
older models: check `/model` there.

## Codex

Effort config key: `model_reasoning_effort`. Values depend on the model; the config reference
names `low`, `medium`, `high`, `xhigh`, `max` and `ultra`. (OpenAI's API model page also lists
`none` for Terra and Luna; whether Codex accepts it was not checked.) `ultra` (where offered) splits a task across parallel
subagents. OpenAI's starting advice: Sol at the client's default, Luna at `high`, Astra at `low`
(the UI calls it Light); "Most tasks" need neither Max nor Ultra.

| To set | How |
| :--- | :--- |
| Model and effort, this session | `/model` (CLI 0.164.0 and later take both as inline arguments) |
| At launch | `codex -m <model> -c model_reasoning_effort="<level>"` (`-c` overrides any config key; the combined spelling is not shown in the docs) |
| One non-interactive run | `codex exec -m <model> -c model_reasoning_effort="<level>" "<prompt>"` |
| Defaults | `model` and `model_reasoning_effort` in `~/.codex/config.toml`; `plan_mode_reasoning_effort` for plan mode; `review_model` for `/review` |
| A named setup | a profile file `~/.codex/<name>.config.toml` with top-level keys, used as `codex -p <name>` (since 0.134.0 `[profiles.<name>]` tables in `config.toml` are ignored) |
| A local model | `codex --oss --local-provider ollama` (or `lmstudio`) with `-m <a model already pulled>`; `oss_provider` sets the default; `codex exec --oss` with no provider set exits with an error. The docs don't say whether `--oss` without `-m` downloads a default model (older builds did): check, and ask before anything downloads |

Retired from Codex recently: GPT-5.5 with ChatGPT sign-in (2026-10-14), GPT-5.4 and gpt-5.4-mini
(2026-08-31). Free and Go plans get Luna where paid plans get Sol.

## Local servers

| Server | Default address | API used by `scripts/offload.py` |
| :--- | :--- | :--- |
| Ollama | `http://127.0.0.1:11434` | `--api ollama` (`/api/tags`, `/api/generate`; answers carry `model`) |
| LM Studio | `http://localhost:1234` | `--api openai` (`/v1/models`, `/v1/chat/completions`) |
| llama.cpp `llama-server` | `http://127.0.0.1:9931` (older builds and many guides use 8080) | `--api openai` |

Ollama's `format` takes `"json"` or a JSON schema; the prompt should still ask for JSON. A loaded
model stays in memory 5 minutes after the last request by default (`keep_alive`).

## Sources

All read 2026-10-26. Vendor pages are undated unless noted.

- Claude models overview, prices, choosing a model, deprecations, effort:
  https://platform.claude.com/docs/en/about-claude/models/overview,
  https://platform.claude.com/docs/en/about-claude/pricing,
  https://platform.claude.com/docs/en/about-claude/models/choosing-a-model,
  https://platform.claude.com/docs/en/about-claude/model-deprecations,
  https://platform.claude.com/docs/en/build-with-claude/effort
- Claude Code: https://code.claude.com/docs/en/model-config,
  https://code.claude.com/docs/en/sub-agents, https://code.claude.com/docs/en/cli-reference,
  https://code.claude.com/docs/en/settings-reference, https://code.claude.com/docs/en/changelog
  (2.1.311, 2026-10-26)
- Codex (developers.openai.com/codex now redirects here): https://learn.chatgpt.com/docs/models,
  https://learn.chatgpt.com/docs/config-file/config-reference,
  https://learn.chatgpt.com/docs/config-file/config-advanced,
  https://learn.chatgpt.com/docs/changelog (0.164.0, 2026-10-23); `codex --help` from Codex CLI
  0.160.0 (`-m`, `-c`, `-p`, `--oss`, `--local-provider`)
- OpenAI prices: https://developers.openai.com/api/docs/pricing
- Ollama: https://github.com/ollama/ollama/blob/main/docs/api.md; LM Studio:
  https://lmstudio.ai/docs/developer/openai-compat; llama.cpp:
  https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md
