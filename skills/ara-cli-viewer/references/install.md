# Installing `ara`

Two paths. Try Homebrew first — it's one command and needs nothing else on the machine. Only
fall back to building from source if Homebrew isn't a fit.

## Recommended: Homebrew (macOS or Linux)

```bash
brew install ARA-Labs/tap/ara
ara --version
```

Prebuilt for macOS (Apple Silicon) and Linux (x86_64) per the `ara-cli` README. If `brew` itself
isn't installed, that's a bigger ask than this skill should make on its own — tell the user and
let them choose: install Homebrew (https://brew.sh), or use the Cargo path below instead.

## Fallback: build from source with Cargo

Works on any platform with a Rust toolchain. Check for one before doing anything else:

```bash
which cargo
```

- **`cargo` found** → `cargo install ara-cli`, then `ara --version` to confirm.
- **`cargo` not found** → do not install a Rust toolchain on the user's behalf uninvited —
  that's a much bigger footprint than installing one binary. Tell them `cargo` isn't present and
  give them the choice: install Rust via https://rustup.rs and re-run `cargo install ara-cli`,
  or use the Homebrew path above instead.

## Either way, confirm before moving on

`ara --version` should print something like `ara 0.1.11`. If the shell can't find `ara` right
after install (e.g. `~/.cargo/bin` not yet on `PATH`), that's a shell/PATH issue — say so plainly
rather than guessing at a fix or silently retrying.

## Check the installed version against this repo's pinned release

This repo pins the `ara-cli` release its own CI lints against, in
`.github/workflows/ara-check.yml` (the `ARA_VERSION` env var — `v0.1.11` as of this writing).
Whatever's installed should match that, or at least not be older:

```bash
grep 'ARA_VERSION' .github/workflows/ara-check.yml
```

- **Installed matches, or is newer** → carry on, nothing to flag.
- **Installed is older** → say so and suggest an upgrade (`brew upgrade ara`, or
  `cargo install ara-cli --force` on the Cargo path) before relying on results — an older binary
  can silently miss newer ARA schema fields (surfacing as spurious "unknown field" warnings, the
  same class of drift `the-ara-of-ara`'s CI job is deliberately warning-tolerant for) or lack
  `--fix` rules added since. Don't upgrade without asking first — same rule as install.
- **Can't find the pin** (e.g. this skill is running outside this repo, or the workflow moved) →
  don't block on it, and don't claim compatibility either; just proceed with whatever
  `ara --version` reports.

## The rule that applies regardless of path

Never run `brew install` or `cargo install` without the user's confirmation first — installing
software changes their machine, and that's their call, not a default to take silently just
because the skill needs the binary to proceed.
