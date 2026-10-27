# Kiln log: next sprint (demo material for a skill eval; not a real project)

We use Codex (CLI) for all of this. ChatGPT Plus plan.

1. Add docstrings to every public function in `kiln/` (about 60 files, one module at a time, the
   style is in CONTRIBUTING.md).
2. Design a cache for the firing-curve calculator. It is slow on long firings and nobody is sure
   where the time goes. Several ways to do it; memory is tight on the Raspberry Pi it runs on.
3. Write the release notes for 2.4 from the merged PR titles (about 25).
4. Migrate the SQLite schema to add a `cone` column to 3 years of firing records, then backfill it
   from the free-text notes field. Runs once against the only copy of the data on the Pi.
5. Rename `tempC` to `temp_c` across the codebase.
