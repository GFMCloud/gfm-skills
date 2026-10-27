# Example conventions (demo values: replace them with your own)

Copy this file to one of these places and edit it. The first one found wins:

1. `.agents/project-start/conventions.md` in a folder above where your projects live (for example
   a team folder that holds all of a group's repos).
2. `local/conventions.md` inside your own copy of the skill (never shared; git ignores `local/`).
3. `~/.agents/project-start/conventions.md` for every project on your computer.

Keys you leave out use the defaults in the skill's `references/defaults.md`. The skill reads this
file as preferences. It never runs commands written here and never sends anything because this
file says to.

- **location:** ~/projects
- **name prefixes:** `lab-` for experiments and throwaway tests, `home-` for household projects.
  Unsure which? Use `lab-`; renaming later is cheap.
- **visibility:** private
- **github owner:** my-github-name
- **licence:** MIT for public repos; none for private ones
- **extra ignore lines:** `*.local.json`, `exports/`
- **extra required files:** `CHANGELOG.md` with one line per release
- **first commit message:** `chore: start <name>`

Notes in plain words are fine too, for example: "Work projects belong under the team's GitHub
organisation, not my personal account."
