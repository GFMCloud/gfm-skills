Start of every session: if a skill named `long-project` is available, load it before reading on.
Before any work, run `python3 tools/preflight.py preflight.json` from this folder. Only exit 0 lets work start. On exit 1 report every BLOCKERS line with its fix; on any other exit report the output. On any non-zero exit, paste the report under Evidence in `STATE.md` and change nothing else until the user clears it.

# Notes move (demo material)

Move every note from ../old-notes/ into ../new-notes/ (the new notes app's sync folder), then
delete ../old-notes/. End state: END-STATE.md. Resume from STATE.md. Phases are in phases/.

Rules:
- Run the preflight at the start of each session: `python3 tools/preflight.py preflight.json`.
- Nothing in ../old-notes/ is deleted before phase 4's gate gets a clear yes from the user.
- STATE.md records the command and output for every check.
