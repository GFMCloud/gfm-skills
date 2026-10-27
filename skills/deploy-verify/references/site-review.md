# Reviewing a live site

"Is the site ready?" is a question about the site as visitors get it: the deployed address, not
the source folder. This review finds what is broken or missing. How the pages look and read is the
design skill's job; mention a design problem you notice, but don't grade it here.

## 1. Run the checks

```
python3 <skill>/scripts/check_site.py <url> --shots --out .deploy-check
```

`--shots` needs playwright (`uv run --with playwright python3 <skill>/scripts/check_site.py ...`
if `uv` is installed and has it cached). If playwright or its browser isn't there, the script says
`NOT RUN`; installing either downloads software, so ask first, or look at the site at 375px wide
in a browser you already have, or list phone width under `Not checked`.

Exit 2 means the site didn't answer: report that, with the command and its error, and stop. Never
fill in a review of a site you couldn't reach. If the start page redirects to another host (to
`https://www.` for example), the script follows it and says so; review that address. Links that
look like they change something (logout, delete, unsubscribe) are not opened; the script counts
them.

Open the screenshots and look at them: the script only catches sideways scrolling. Dark mode is
emulated through `prefers-color-scheme`; a site that switches theme by a button or class won't
change, so say so rather than report a dark-mode pass.

## 2. Check what no script can

| # | Check | How |
| ---: | :--- | :--- |
| 1 | Every page has a real title and description | Script output |
| 2 | No broken links, images, styles or scripts on the site | Script output (`--external` for other sites' links) |
| 3 | No placeholder text, leftover "TODO", test data, staging banners, or an error page ("Application Error", a stack trace) served with status 200 | Script output, then read the pages |
| 4 | Usable at phone width: nothing cut off, no sideways scroll, menu works | 375px screenshots |
| 5 | Readable in dark mode, if the site supports it | Dark screenshots |
| 6 | A missing page shows the site's own 404 page, with status 404 | Script output, then look at it |
| 7 | Contact details, prices, dates and opening hours agree everywhere they appear | Read every page; list each value and where |
| 8 | Copyright year and "last updated" dates are current | Script output, read the footer |
| 9 | `robots.txt` doesn't block the whole site on production; `sitemap.xml` exists if the site wants search traffic | Script output (it warns on `Disallow: /`) |
| 10 | Forms point somewhere real and say what happens next | Read the form's `action`; never submit it on a live site |

Where facts disagree (two phone numbers, two prices), don't pick one. List both with where each
appears, and ask the owner which is right.

## 3. Lab scores, only if asked or already available

Lighthouse gives lab scores for performance, accessibility, best practices and SEO. It runs with
`npx lighthouse <url>`, which downloads it the first time; ask before that. If you run it, print
these two lines with the scores, every time:

- The performance score is a lab test on one machine; it does not measure real visitors' speed.
- The accessibility score finds the problems a tool can find, a fraction of them; it is not a
  compliance result.

Never estimate or invent a score you didn't run. If you didn't run it, it goes under
`Not checked`.

## 4. Report

1. **Verdict first**: ready, ready after the listed fixes, or not ready, in one sentence.
2. **Findings table**, worst first: what, where (page and line or element), why it matters to a
   visitor, and the fix. Broken things before missing things before polish.
3. **What passed**, briefly, so the reader knows it was checked.
4. `Live check:` line (address, time, script summary line) and the `Not checked:` list.

Fixing is a separate step: change files only if the user asked for fixes. Then fix on a branch or
staging, deploy there (main skill steps 1 to 3), rerun the same checks, and show a before and
after table with the same rows.
