---
name: commit-helper
description: Drafts a commit message from the staged diff for the user to approve. Use when asked to write a commit message. Not for staging or pushing.
---

# Commit helper

1. Read `git diff --cached --stat`, then the diff. Stage nothing yourself.
2. Draft a subject line under 72 characters in the imperative mood, and a body that says why.
3. Show the draft. Commit only after the user approves, with hooks enabled.
