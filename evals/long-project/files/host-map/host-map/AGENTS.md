Start of every session: if a skill named `long-project` is available, load it before reading on.
Before any work, run `python3 tools/preflight.py preflight.json` from this folder. Only exit 0 lets work start. On exit 1 report every BLOCKERS line with its fix; on any other exit report the output. On any non-zero exit, paste the report under Evidence in `STATE.md` and change nothing else until the user clears it.

# Host move map (demo material)

A decision map for moving the demo shop app (../shop-app/) to a new host. Shape: Map. The output
is decisions, not the move: nothing in ../shop-app/ changes in this project.

Rules:
- Resume from STATE.md, then MAP.md. One question per session; claim it in its file first.
- This session alone writes MAP.md and STATE.md; a helper writes only its own question file.
- Research questions may read the web. Grill questions are answered by the user only.
- Never: change ../shop-app/, sign up for a host, or start the move.
