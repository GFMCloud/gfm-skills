# Research brief: minimum Python version (DEMO)

DEMO material written by hand for a skill trial. Not a real project or a real research result.

Decision this feeds: whether to raise our package's minimum Python version this sprint, and to which version.

Findings from last quarter's research:

1. The oldest Python release still receiving security fixes is 3.9.
2. Our package declares `requires-python = ">=3.9"` (see pyproject.toml).
3. Our README is 212 lines long.
4. The project's logo was last redrawn two years ago.

Recommendation from last quarter: keep 3.9 as the floor, since it is still supported.
