---
name: release-notes
description: Use when asked to write release notes or a changelog entry for a new version from the pull requests merged since the last tag. Not for commit messages or blog posts.
---

# Release notes

<!-- Demo material for a skill trial, not real. -->

Writes the release notes for a new version of the shop app from the pull requests merged since the
last tag.

## Steps

1. Find the last tag with `git describe --tags --abbrev=0` and list the pull requests merged since
   then with `git log <tag>..HEAD --merges --oneline`.
2. Group the changes under Added, Changed and Fixed. Don't put anything under a heading called Misc
   or Other.
3. Write one line per change, in the past tense, starting with the area it touches in bold
   (**Billing**, **Search**, **Checkout**).
4. Link each line to its pull request as `(#123)`. Don't mention internal ticket numbers (the
   SHOP-123 kind).
5. Write the notes in Markdown.
6. Make sure the notes are accurate and complete.
7. Save the notes to `docs/releases/<version>.md`.

## Style

- Be clear and concise.
- Version headings use the release date, not the version number: `## 2026-10-14`. The app store
  listing shows dates, and customers match the two.
- Never name the person who made a change; customers read these notes.

## Notes

- The release notes matter to our customers, so take care with them.
- Git is a version control system that records every change to the code.
- The release script is `scripts/release.sh`. Its flags are `--dry-run` (print what it would do),
  `--tag <version>` (tag the release) and `--notes <file>` (attach the notes); `--help` lists them.
