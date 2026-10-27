# Share a repo without your data

Use when someone else (a friend, a client, a colleague) should get a working copy of a repo that was
built around the user's own data. The original repo, its history and its remotes never change, and
nothing is created on GitHub or anywhere else without a yes to the exact name. Credentials never
travel: the recipient uses their own, or does without.

## Contents

1. Ask once, then list what must not travel
2. Cut a new tree, outside the repo
3. Make it general at the source
4. Prove it clean (gate)
5. Start the new history
6. Write the walkthrough, then run it (gate)
7. Stop before anything leaves the machine
8. Report

Steps 4 and 6 are gates: a finding in 4 or a failed command in 6 stops the hand-over until fixed.

## 1. Ask once, then list what must not travel

Settle in one message, proposing your own answers from what you can see:

- the recipient, and where their copy will live (their account, or a private repo under the user's
  account with them added). Propose; never create it (step 7);
- the **terms list**: the strings that identify the user or their world. Start it yourself from
  `git log --format='%an <%ae>' | sort -u`, `git config user.name`, the README, config files and
  data file names: full name, emails, phone, employer, team, league or client names, account ids,
  home-folder paths. Show it and let the user add to it.

Save the terms in a file **outside the repo** (for example `../<repo>-share-terms.txt`): it is
the very list that must not ship. Never paste the terms into the hand-over report.

Then place every file in one of three groups, and show the table:

| Group | Means | What happens |
| :--- | :--- | :--- |
| ships | code, docs, generators, config with nothing personal | copied as is |
| made general | does its job but hard-codes the user's specifics | the specifics move to a config the recipient fills in (step 3) |
| left out | personal data, exports, transcripts, recordings, copyrighted media, `.env`, keys | never ships; named in the report with one reason each |

Search the tree and the history for each term: `grep -rIil -e '<term>' --exclude-dir=.git .` and
`git log --all --oneline -S'<term>'`. Media and transcripts someone else owns go in "left out"
even when they hold nothing personal.

## 2. Cut a new tree, outside the repo

Two ways; pick the one with less to prove:

- **An older clean commit.** If every term first appears after some commit, the commit before the
  first hit is a candidate. Export it, never check it out in place:
  `mkdir -p ../<repo>-share && git archive <commit> | tar -x -C ../<repo>-share`. Use it when that
  commit is recent enough to be useful.
- **A copy of the "ships" files** plus the made-general versions, into `../<repo>-share`.

Either way, the new tree gets a new history. The user's history never travels.

## 3. Make it general at the source

Where a file hard-codes the user's specifics, change the code that reads them to read a config
instead (`config.example.json`, `.env.example` with names and no values, a `--league` flag). Edit
the generator, not its output. Mark each value the recipient must supply with a clear comment that
names it.

## 4. Prove it clean (gate)

From the user's repo folder:

```bash
python3 <skill folder>/scripts/clean_check.py ../<repo>-share --terms ../<repo>-share-terms.txt
```

It checks every file's name and contents for every term (as written, ignoring case: a name split
across two lines, or spelled another way, needs its own line in the terms file) (printing term numbers, never the terms),
flags secret-type files and data files to confirm, refuses a terms file inside the tree, and runs
gitleaks when installed. Any FAIL is a stop: fix the tree, run it again, keep the clean run's output
for the report. Never hide a secret with `.gitignore`: remove it, and if it was ever a real secret,
tell the user to rotate it, because it is in the original repo's history.

## 5. Start the new history

```bash
git -C ../<repo>-share init -b main
git -C ../<repo>-share add -A
git -C ../<repo>-share commit -m "First version for <recipient>"
```

Commits carry the author's name and email. If those are on the terms list, set a neutral author for
this repo only first (`git -C ../<repo>-share config user.name ...` and `user.email ...`, agreed
with the user), then run the step 4 check again: it reads the history too.

## 6. Write the walkthrough, then run it (gate)

Write `WALKTHROUGH.md` in the new tree: what it does, set-up, the commands to run, where the config
lives and what the recipient supplies. Then run every command in it, in order, in the new tree (or
a scratch copy of it), and keep each command's output. A command that fails, or prints something
other than what the walkthrough says, means the walkthrough is wrong: fix it and run it again.
Skip only commands that need the recipient's own credentials, and say so in the walkthrough.

End the walkthrough with three short prompts the recipient can give their own agent: get it
running, add their own data, and what to check when a step fails. Each names the files it relies on.

## 7. Stop before anything leaves the machine

Propose the exact destination, private: a concrete name (for example `<repo>-for-<recipient>`)
under the account `gh auth status` shows, or ask which account if it can't be read. Never leave
`<owner>/<name>` for the user to fill in. Give the exact commands, for example:

```bash
gh repo create <owner>/<name> --private --source=../<repo>-share --push
gh repo view <owner>/<name> --json visibility
```

and wait for the user's yes to that exact name. Never touch the original repo's `origin`. If the
original was a fork of a public project, suggest adding that project as `upstream` in the new
repo so the recipient can pull its updates.

## 8. Report

In this order: where the new tree is (and the repo, once the user created it); the "left out"
group with one reason each; the step 4 command and its output; the walkthrough run from step 6;
what the recipient must supply. Then the step 7 commands, waiting on the user.
