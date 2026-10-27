# Notes move (demo material)

Move every note from ../old-notes/ into ../new-notes/ (the new notes app's sync folder), then
delete ../old-notes/. End state: END-STATE.md. Resume from STATE.md. Phases are in phases/.
Set up with the long-project skill; a session that has the skill loads it.

Rules:
- Run the preflight at the start of each session: `python3 tools/preflight.py preflight.json`.
- Nothing in ../old-notes/ is deleted before phase 4's gate gets a clear yes from the user.
- STATE.md records the command and output for every check.
