# Suggested agent rules

Some habits apply to every task, so they work better as a line in your own instructions than as a
skill, which loads only when a request matches it. Paste the ones you want into your `AGENTS.md`
(Codex) or `CLAUDE.md` (Claude Code). A `CLAUDE.md` that contains only `@AGENTS.md` makes Claude
Code read the same file. `install.sh` does not add these; they are yours to paste.

## Full output

```markdown
- Deliver everything that was asked for. Never stand in for code, rows, items or sections with `...`, `// rest unchanged`, "the others follow the same pattern", or a description of what the code would do. A placeholder the user asked for, a summary or excerpt they asked for, and a file edited on disk with an edit tool are fine. Long output goes in a file when you have a file tool. Only if a reply truly cannot hold it all, stop at a clean break, say what is still missing, and say where the next part starts.
```

**Why:** agents shorten long output to save space, and a placeholder looks finished. The gap shows
up later, when the pasted code fails or the list is short.
