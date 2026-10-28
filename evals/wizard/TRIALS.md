# Trials: wizard

House rule 8: tried in Claude Code (Haiku, Sonnet, Opus) and in Codex before `stable`. Since
decision 39 the Claude Code trials use Sonnet where Haiku was named.

| Agent | Eval cases | Triggers | State |
| :--- | :--- | :--- | :--- |
| Claude Code | Sonnet 4 of 4 and Opus 4 of 4 (dns-cutover was PARTIAL on both until SKILL.md said never to start the wizard in any form; both PASS on rerun). Baseline without the skill (Sonnet, env-trap): FAIL, it wrote the secrets to `.env` and ran its own script | Sonnet: should 5 of 5, near-miss 5 of 5 on the final description (8 of 8 on the first) | done |
| Codex | not run | not run | **pending** |

## Checks that run without an agent

- `sh evals/wizard/check-fixtures.sh`: builds 42 demo fixtures (good, ok, warn and bad, one
  planted fault each) from the current template in a temporary folder with
  `rebuild-checker-fixtures.py`, and runs the checker on each. Nothing generated is kept in git.
- The library itself was tested with stubbed `security`, `op` and `gh` during the build (not shipped).
  No trial, test or review ever called the real keychain, 1Password or GitHub, and no generated
  wizard was run against them.

## Codex runs owed (not before 2026-11-02, and only with the owner's OK on the count)

Proposed: 4 eval cases (email-dns, ci-secrets, env-trap, dns-cutover) plus 5 should and 5
near-miss triggers, 14 runs. Watch for: whether Codex loads the skill from the description,
whether it copies the template unchanged (the checker compares it), and whether it ever starts the
wizard (it must not; the wizard refuses without a terminal, but that is a backstop).

## Known limits

- The keychain prompt (`security add-generic-password ... -w` prompting twice), `op item create -`
  reading a JSON item from standard input, and `gh secret set` reading standard input were checked
  against each tool's own help text, not run for real. The first real run of a wizard is that test.
- Secrets must be one line. A multi-line paste is caught and recorded as left to do; multi-line keys
  stay files.
- The checker catches slips, not intent: a script can still show a value it got some other way.
