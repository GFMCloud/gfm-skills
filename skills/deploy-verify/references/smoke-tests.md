# Smoke tests

A smoke test is a short, saved check the project runs after every deploy: is the right build live,
do the pages and endpoints that matter answer with the right content. It is worth keeping only if
**each check has been seen failing**: a check that has never failed may not be able to.

## 1. Put it in the project

Copy `scripts/smoke.py` from this skill into the project (next to its other scripts, or a
`smoke/` folder), and write `smoke.json` beside it. The project's copy is the one people run; it
must not point at this skill's folder. Add a line to the project's README or deploy notes saying
how to run it:

```
python3 smoke/smoke.py smoke/smoke.json --base https://staging.example.org
```

Don't add it to CI, a hook or a schedule unless the user asked; that is a separate change (the
automation skill's job).

## 2. Choose the checks

Read the site or service first. Five to ten checks is usually right. Cover each kind that applies:

| Kind | Example check | What it catches |
| :--- | :--- | :--- |
| Which build | `/version.txt` `equals` `${BUILD_ID}` (exact, so "142" doesn't pass for "42") | The old build still live; a deploy that copied the wrong folder |
| Key pages | `/`, `/pricing` answer 200 and contain a phrase only the real page has | Missing pages, an error page served with 200 |
| Content that matters | The current price, opening hours, the product name | Stale content, a half-finished template |
| Things that must not show | `not_contains`: "lorem ipsum", "Traceback", "Application Error", "undefined", "staging" on production | Placeholders, error pages served with 200, the wrong environment |
| Data and connections | An API endpoint that reads from the database returns a known record | A site that renders but can't reach its data |
| Assets | The main stylesheet and script answer 200 | A page that loads unstyled or without its code |
| Missing pages | A made-up path answers 404, not 200 | Soft 404s that hide broken links |

Write the text as a visitor reads it ("£4.20"); the script also matches it when the page writes
`&pound;4.20`. Pick text that **only the working page contains**. "Welcome" or the site name also appear on the
host's error page; "Open Sundays 9 to 1" does not. Use `${NAME}` for values that change per deploy (the
build id) and set them in the environment when running.

What a smoke test like this can't see, and you should say so: anything that needs a browser
(scripts that fail after load, layout at phone width), anything behind a sign-in, and anything
that needs a write (forms, orders, sign-ups). Never add checks that submit forms or create
records on a real site.

## 3. Prove each check can fail

Run it against a build where the checks should fail, and see each one go red:

```
python3 smoke/smoke.py smoke/smoke.json --base <good address> --prove <bad address>
```

The bad address can be the previous release, staging before the change, or a local copy with the
change reverted. If the script says "Can't prove the checks", a check already fails on the good
build: fix that check (or the site) first. Any check listed `NEVER SEEN FAILING` can't tell the two builds apart: change its
text so it can, or say in the report that it is unproven. Where no bad build exists, break one
check at a time on purpose (a wrong expected phrase, a made-up path), run it, and show the
`FAIL` line; record which way each check was proven.

Then run it against the real target and show the final `SMOKE PASS: n of n passed` line with its address and
time.

## 4. Read the exit code honestly

| Exit | Last line | Means |
| :--- | :--- | :--- |
| 0 | `SMOKE PASS: n of n passed` | Every check passed at that address, at that time |
| 1 | `SMOKE FAIL: k of n failed` | At least one check failed; the `FAIL` lines say what |
| 2 | `SMOKE SETUP` | Nothing ran (bad file, unset variable, no answer). Says nothing about the site |

Never report exit 2 as "the site is down". It is the check that didn't start.

## 5. Report

Give the file paths, the command to run it, the proof (which checks were seen failing, and how),
the green run's last line, and what the test doesn't cover. End with the `Live check:` line and
the `Not checked:` list from the main skill.
