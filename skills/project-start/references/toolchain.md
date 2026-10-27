# Pinning the toolchain

Do this when the user asks for the project to run the same on another machine, or the stack
needs one exact tool version. Otherwise leave it out and say it is available.

## 1. Look before writing

Find what the project uses (`pyproject.toml`, `requirements.txt`, `uv.lock`, `package.json`,
`go.mod`, `Cargo.toml`, `*.tf`) and what the user already has (`command -v uv mise nix direnv`).
Use the tool they already use. Never install a version manager, a package manager or Nix without
asking: that changes their computer, not just the project. If a pin file already exists, show it
and ask before changing it.

## 2. Pin with the stack's own tool

| Stack | Pin | Notes |
| :--- | :--- | :--- |
| Python with uv | `.python-version` and `requires-python` in `pyproject.toml`, `uv.lock` committed | Pin the minor version (`3.12`, not `3.12.13`) so every machine with any 3.12 works. Use one already on the machine (`uv python list --only-installed`) unless the user agrees to a download |
| Python without uv | `requires-python` plus a `requirements.txt` with exact `==` versions | |
| Node | `engines.node` and `packageManager` in `package.json`, lock file committed; `.nvmrc` if they use nvm | |
| Go, Rust | the `go` line in `go.mod`; `rust-toolchain.toml` | |
| Several tools at once | `mise.toml` if they use mise | |
| Nix users | `flake.nix` with a dev shell for every system they use (for example macOS and Linux), plus `.envrc` containing `use flake` if they use direnv | Python libraries still go through `uv`, not Nix packages; Nix gives the interpreter and tools |

Never put secrets in `.envrc`, `mise.toml` or a flake. They point at the password manager or an
environment variable instead.

Agent shells are not interactive, so a direnv or version-manager hook never switches the tool for
them. Write the full form into `AGENTS.md` (`direnv exec . <command>`, `nix develop -c <command>`,
`uv run <command>`, `mise exec -- <command>`) and use it yourself.

## 3. Prove it

Run the pinned tool from the project folder and show the output: for example
`uv run python --version`, `node --version` after the version manager has switched,
`direnv exec . command -v python` for a Nix shell (the path should be inside the Nix store).
If the path or version is the system one, the pin is not active: say so and find out why rather
than reporting it as working.
