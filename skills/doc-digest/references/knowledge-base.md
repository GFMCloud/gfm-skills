# Knowledge-base files

For when the digest is a folder of files that a Claude or ChatGPT project, or an agent, will search
and answer from. Retrieval finds a file by its topic and headings, then answers from that file
alone, so each file must stand on its own. Steps 2 to 4 and 6 of `SKILL.md` still apply.

## Size it to the source

| Source | Files |
| :--- | :--- |
| Under about 15 pages, or fewer than four separate topics | 1 to 3 files: an index that also holds the cross-cutting rules, plus one or two topic files. Say why it is small |
| A typical handbook, policy set or manual | Index, one cross-cutting file, one file per topic, then reference files |
| More than about 15 topics | Topics take two bands (10-19, then 20-29), reference moves to 30+; or suggest splitting into two projects |
| Pure narrative (a story, a single argument) with no separable topics | No knowledge base: make a notes file and say why |

Don't ask the user to approve the file list first unless they asked to see it. Build it, then show
the list in the reply; renaming or regrouping later is cheap.

## Names and order

```
00-<topic>-index.md       what the document is, the file list, which file answers what
01-<topic>-rules.md       rules, dates and definitions that apply to every topic
10-<first-topic>.md       one topic per file, in the order a reader meets them
11-<second-topic>.md
...
20-<reference>.md         fee tables, registers, appendices, special cases
21-glossary.md
```

Numbered prefixes keep the general files first in any listing, so a search that matches several
files sees the index and the cross-cutting rules before narrow ones. Leave a gap in the numbers
where a topic may be added later. If the user wants other names, use them and keep them
consistent.

## Every file

```
# <Topic>
Source: <document>, pages 7-8 (and p. 19 for the fee table)
<For the index file only:> Coverage: read pages 1-31 of 31; not read: <which and why, or none>

## In short
<two to four sentences: what this covers and the headline rule, with locations>

## <Sections that fit the topic>
<for a rules-type topic: who it applies to, what is allowed, limits and amounts, how to do it,
dates and deadlines, exceptions, common problems>
```

- **Self-contained.** Repeat a key definition or number in each file that needs it rather than
  writing "see above" or "as defined earlier". Each repeat keeps its own location.
- **Same headings for same-kind files,** so every topic file answers the same questions in the
  same place.
- **Keep tightly linked content together.** If two sections keep referring to each other, they
  belong in one file.
- **Ended or replaced items** go in the index under "No longer running", with the location that
  says so, not in a file of their own.
- **Source issues** appear in every file they affect (step 4 rule 4 in `SKILL.md`), and all of them
  are listed together in the index.
- **Content only.** How the assistant should behave, its persona or tone belongs in the project's
  instructions, not in the knowledge files; the project-start skill writes those. Mention this in
  the reply when the user is building a project.
- No empty "notes" or "internal" placeholder sections. A section with nothing from the source is
  left out.
- Aim for roughly 300 to 1,500 words per file. Much shorter, merge with a neighbour; much longer,
  split by sub-topic.

## The index file

```
# <Document title>: index
Source: <document>, <n> pages, <its date or version>
Coverage: ...

## What this is
<one paragraph>

## Files
| File | Answers questions about | Source pages |

## No longer running
<ended items, with the location that says so, or leave the section out>

## Source issues
<every issue, with both locations>
```

## Reply

After the three status lines: the file list, the source issues, what was not read, and for a
project the two upload steps (add the files to the project's knowledge; put any behaviour
instructions in the project's instructions field, which the project-start skill can write).
