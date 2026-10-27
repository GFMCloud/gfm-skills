# Setting Jev up

What a project needs before a real call. Facts dated 27 October 2026 from
<https://docs.typesafe.ai/models.md> and <https://docs.typesafe.ai/sdk/python/changelog.md>;
check them again before relying on them.

## The key

The SDK reads `TYPESAFE_API_KEY` from the environment. Check it without printing it:
`python3 <skill>/scripts/preflight.py` (prints `Key: present` or `Key: missing`).

When it is missing, the user stores it themselves. Never ask for the key in chat, print it, write it
to a file in the project, or pass it as a literal on a command line (for example
`claude mcp add -e TYPESAFE_API_KEY=...` writes the value into a settings file).

- **macOS (Keychain).** The user runs this in their own terminal. `-w` with no value makes
  `security` prompt for the key without echoing it. The `grep -q` keeps the export line from being
  added twice.

  ```bash
  security add-generic-password -a "$USER" -s TYPESAFE_API_KEY -w && { grep -q 'TYPESAFE_API_KEY' ~/.zshenv 2>/dev/null || printf '%s\n' 'export TYPESAFE_API_KEY="$(security find-generic-password -a "$USER" -s TYPESAFE_API_KEY -w 2>/dev/null)"' >> ~/.zshenv; } && echo "stored TYPESAFE_API_KEY in the Keychain; open a new shell to load it"
  ```

- **A password manager with a CLI** (for example 1Password's `op run`): keep a reference in the
  project's `.env` that the CLI resolves at run time, and make sure `.env` is git-ignored.
- **Elsewhere:** the platform's secret store, exported into the shell that runs the project.

## Data

Requests go to TypeSafe's servers. In October 2026 the docs said requests are not used for training
and zero data retention is for enterprise accounts only, so a normal account keeps some data under
the Data Processing Agreement (<https://docs.typesafe.ai/legal.md>). The user decides what may be
sent and records it in a rule file the preflight finds:

1. `local/data-decision.md` in the skill folder (never committed), or
2. `~/.agents/jev/data-decision.md` (shared by every copy of the skill).

No file means "public data only". A project may carry `.agents/jev/data-decision.md`; it can only
narrow the user's rule. The format is a dated list, newest first; see `local.example/data-decision.md`.

## The SDK

Python: `typesafe-sdk` (`uv add typesafe-sdk` or `pip install typesafe-sdk`), version 0.7.5 on
14 October 2026. Client `TypeSafeClient`; the call is `client.system_one(...)` with `state` and
`questions`; answers are in `response.answers[<id>]`, each with a `type` (`noul`, `choice`,
`score`, `box`); `response.model` names the version that answered and `response.usage.input_tokens`
is the billable count. A JavaScript SDK exists too. The templates keep all of this inside `to_sdk()`
and `ask()` so a change in the SDK touches two functions. At debug log level the SDK writes request
and response bodies to the log (not the key), so keep logging at its default when the data is
private. Check them against these pages:
<https://docs.typesafe.ai/sdk/python/api/types/responses.md> (response and answer fields),
<https://docs.typesafe.ai/primitives/noul.md> and <https://docs.typesafe.ai/primitives/choice.md>
(criteria forms: a Noul takes `NoulCriteria(true=..., false=...)`; a Choice option may be a string or
an object such as what / not_for / examples), and <https://docs.typesafe.ai/sdk/python.md>.

## The model

On 27 October 2026 the current version was `jev-1.14.0`; `jev-latest` and `jev-preview` both pointed
to it, and `jev-1.13.0` was the previous release. Pin a versioned id once thresholds are set: an alias
moves when a release ships, and thresholds tuned on one version don't carry to another. Read the
version's "jaggedness" page (its list of known weak spots) before writing questions.

## Cost and speed

Billing is per input token; output is free. The models page listed $0.042 per million input tokens
for both versions in October 2026. Measured in September 2026 on one network: about 145 ms median at
780 input tokens and 295 ms at 28,000; checking one item against 47 full records cost about $0.0012.
Put the current price in `evaluate.py` (`PRICE_PER_M_INPUT`) with the date you read it.

## The provider's own agent skill

TypeSafe publishes an agent skill that points agents at the live docs
(<https://docs.typesafe.ai/agent-skill.md>). It is optional: read the docs directly if it isn't
installed. Installing it is the user's call.
