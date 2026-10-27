---
name: deploy-verify
description: Deploys a change to staging or production and proves it works where users reach it, fixing and redeploying as needed. Also smoke tests, pre-launch site reviews, host moves. Use for "deploy this", "the deploy didn't take", "is the site ready?". Not for confirming a past deploy, planning or design.
metadata:
  status: draft
  codex-check: "pending: not yet tried in Codex; must pass before stable"
---

# Deploy and verify

A deploy is done when **the address users reach serves the new build, and it works there**. The
deploy tool saying "success", a green pipeline, or a 200 from a health check are not that.

**Three rules hold throughout:**

1. **Deploy only where the user said.** "Deploy" with no target means staging. Production, DNS
   records, deleting or switching off an old host, and data migrations each need the user's yes
   naming that target, in this conversation. A yes for staging is not a yes for production.
2. **Checks against a live site are read-only:** GET and HEAD requests and a browser. No form
   submissions, sign-ups, orders or load tests on anything real. `check_site.py` starts Chromium
   in a mode that works inside a sandbox; never turn the sandbox off to run a check.
3. **Every report opens with the bottom line and ends with a `Live check:` line and a
   `Not checked:` list** (format in step 5). `Not checked: none` needs a reason.

## Which job is this?

| The request | Do |
| :--- | :--- |
| Deploy, ship, release, push live, "get it on staging", "the deploy didn't take" | Steps 1 to 5 below |
| A smoke test or a post-deploy check to keep and rerun | `references/smoke-tests.md`, with `scripts/smoke.py` |
| "Is the site ready?", review a live site, broken links, how it looks on phones | `references/site-review.md`, with `scripts/check_site.py` |
| Move a site to a new host or domain, change its DNS | `references/host-move.md`, with `scripts/check_site.py --compare` |
| Only "did it work?" about a deploy already made, with nothing to ship or fix | The proof-of-work skill if it is installed; otherwise steps 2 and 5, read-only |
| "Plan it first, don't change anything" | The planning skill if it is installed; otherwise the matching steps or reference, stopping before any change |

Reading and running this skill's own files is part of using it. The scripts are standard-library
Python and only read from the site. Run them as `python3 <this skill's folder>/scripts/<name>.py`;
when the project should keep one (a smoke test), copy it into the project, so nothing the project
keeps points at this skill's folder.

## 1. Before the first deploy

Find these yourself (deploy docs, scripts, CI config, `AGENTS.md`, recent commits). Ask only for
what isn't written anywhere.

- **The exact deploy command for each environment**, as written in the project, not "run the
  deploy script".
- **The address users meet**: the page or endpoint a person or client actually uses, not the
  deploy tool's dashboard or the build server.
- **How to tell which build is live**: a version file, a commit hash in a meta tag or header, a
  `/version` endpoint. If there is none, add one to the build (a `version.txt` with the commit or
  build id is enough); without it you can't tell "new build, broken" from "old build still there".
- **The rollback**: the command, and whether it has ever been run. An untested rollback is a guess;
  say so.
- **Surprises in the way**: sign-in or tokens the deploy needs, caches and CDNs, DNS delay, manual
  steps, a second account. Read the notes for them before the first cycle, not after the third.

**Take a baseline** before deploying: what the address serves now (its version marker, and the
smoke test if there is one). Then a failure afterwards can be told apart from one that was already
there. If the rollback needs a copy of what is live now, keep it inside the project, in
`.deploy-check/`, not in a temporary folder elsewhere. In a git repository, keep that folder out of
commits by adding `.deploy-check/` to `.git/info/exclude` (local only, changes no tracked file).

**Staging first.** If there is no staging, say so; deploying straight to production needs the
user's yes for that. When the user names production and a staging exists, still go through staging
and promote the same build (step 4), unless they said to skip it ("straight to production", "skip
staging"); then say in the report that staging was skipped.

## 2. The loop: deploy, verify, diagnose, fix

1. **Deploy one change.** A cycle that changes three things can't tell you which one worked.
2. **Verify at the address users meet, at the level the failure would show.**

   | Not verification | Verification |
   | :--- | :--- |
   | The deploy tool printed success; the pipeline is green | The version marker at the real address shows the new build |
   | `curl -I` returns 200 | The page or endpoint returns the right content (the new price, the fixed field, the new route) |
   | One record looks right | Several representative pages or records look right, including an edge case |
   | It worked on staging | It works on production, checked the same way |

   Run the project's smoke test if it has one (`scripts/smoke.py` if it came from this skill).
   **Check the plain address first, the way users get it.** If it still shows the old build, fetch
   it again past the cache (`curl -s -H 'Cache-Control: no-cache' '<url>?v=<build>'`) to tell a
   stale cache from a failed deploy. A stale cache means "not live yet", not "done": purge it if the
   project has a purge step, or poll the plain address with a limit (every 15 to 30 seconds, for at
   most 5 minutes) instead of concluding at once or waiting with no end.
3. **Diagnose from real output**: the response body, the version marker, deploy and server logs,
   the file the server holds against the file the build made. Not from what probably went wrong.
   If the output you need doesn't exist, getting it (a log line, a version marker) is the next
   cycle, and it counts as progress.
4. **Fix and deploy again, without handing it back to the user**, as long as the fix stays inside
   what they asked for and the target they named. Fixing the build or the deploy script is in
   scope; a new credential, a different environment or a change to shared infrastructure is not.
5. **Log the cycle**: one line, what changed and what the check returned. The log is what makes
   cycle three smarter than cycle one, and it is the report if you stop.

**When the check can't reach the target at all** (no answer, DNS fails, sign-in refused before
any check ran), that is a setup failure, not a broken site. Say "the check never ran" and why.
Never report it as "the site is down" or as a failed deploy without more evidence, and never swap
in a different target (a local copy, production) and call the original verified.

## 3. Stop and hand back

Stop the loop and report when any of these is true:

- **Three cycles in a row failed and the last one taught you nothing new.** Ten cycles that each
  reveal something are fine; two identical failures are a loop.
- The next step needs a credential, a sign-in, a paid change, or a write outside the target and
  scope the user gave.
- The cause is outside the project: the host, an upstream service, a quota, an expired
  certificate on someone else's side.
- **Rolling back is now cheaper or safer than rolling forward.** Say so and give the command. Roll
  back yourself only on staging, or where the user agreed to it beforehand.

Hand back the diagnosis, the cycle log and a recommendation. Never hand back "please try it and
tell me".

## 4. Staging to production

Only with the user's yes for production.

- **Promote the build that passed on staging; don't rebuild it.** If the deploy tool can only
  rebuild, check that the version marker on production matches what staging showed.
- **Check production to the same standard** as staging: version marker, the changed pages or
  records, the smoke test. Staging passing is evidence about staging.
- After a production deploy, keep the rollback command at hand in the report.

## 5. Report

Open with the bottom line in one sentence (live and working, live but broken, not deployed, or
not checked), then:

```
Deployed: <build or commit> to <environment> with `<exact command>`   (or: Not deployed: <why>)
Live check: PASS | FAIL | NOT RUN at <address>, <date and time>: <what was seen, e.g. version.txt = 4f2a9c1, /opening-hours shows "Open Sundays">
Cycles:
  1. <what changed> -> <what the check returned>
  2. ...
Rollback: `<command>` (run before: yes/no)
Not checked: <each item, why, and who could check it>; or "none" with the reason
```

`Live check` names the address and time. `NOT RUN` covers every case where the check didn't
reach the target; say why on the same line. If you stopped (step 3), the last cycle line says why
and the next line is your recommendation.

## Borders with other skills

- Confirming that something already done worked, with no deploy to make: the proof-of-work skill.
  "I deployed it an hour ago; confirm it worked before I tell the team" is that skill's job.
- How a page looks and reads (layout, colour, copy): the design skill. This skill checks that a
  live site works and has nothing missing or broken.
- Planning a risky deploy, migration or DNS change before anyone touches it: the planning skill.
  This skill carries it out.
- Running checks on a schedule or after every push, or leaving an agent to fix and redeploy
  unattended: the automation skill. This skill runs the loop while someone is in the conversation,
  and writes the smoke test a schedule would run.
