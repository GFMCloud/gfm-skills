# Bakery site: agent notes (demo material)

- Use British spelling in docs and page copy.
- Keep commit messages under 72 characters.
- Use rg instead of grep for searches here: rg was about 10x faster on the 2 GB orders export folder (timed once, spring).
- Use jq for the nightly orders report: it parsed the export in 3s against 11s for a Python json script.
- Never run the import script on a Friday: one Friday it charged 40 customers twice because the payment batch closes early.
- The staging database refuses more than 20 connections at once (found when the load test failed), so keep the worker pool at 16.
- Prefer short paragraphs in customer emails.
