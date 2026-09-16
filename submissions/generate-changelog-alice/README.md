# generate-changelog

Turn a project's git history into a structured `CHANGELOG.md` — commits from the
last tag to `HEAD`, categorized into **Added / Fixed / Changed / Removed**.

- **Zero dependencies** — Python 3.8+ standard library and `git`. No pip install, no node_modules.
- **Conventional Commits first, keywords as fallback** — works on tidy repos *and* on real-world messy ones.
- **Robust by design** — repos with no tags, empty ranges, multi-line commit bodies, non-ASCII/Chinese commit messages.
- **Bash entry point + Claude Code skill** — `bash changelog.sh`, or load `SKILL.md` as a skill.

## 3-step setup

1. Copy this folder into your project (or clone the repo anywhere).

2. From your project root, run:

   ```bash
   bash changelog.sh
   ```

3. `CHANGELOG.md` is written in the current directory. Review it, then commit.

That's it — no `pip install`, no config file, no daemon.

## Common usage

```bash
bash changelog.sh --stdout                      # preview, write nothing
bash changelog.sh --version 1.3.0               # heading becomes ## [1.3.0]
bash changelog.sh --from-tag v1.2.0 --to HEAD   # explicit range
bash changelog.sh --include-merges              # keep merge commits
bash changelog.sh --no-refs                     # plain bullets, no links
bash changelog.sh -o docs/CHANGELOG.md          # custom output path
```

## What the output looks like

```markdown
# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2026-09-16

### Added

- **auth:** add refresh tokens (#42) — [`a1b2c3d`](https://github.com/owner/repo/commit/a1b2c3d…)

### Fixed

- resolve timeout when the upstream returns a non-dict payload — [`e4f5g6h`](…)

### Changed

- **BREAKING** drop support for node 16 — [`i7j8k9l`](…)

### Removed

- delete the legacy `/v1` compatibility shims — [`m0n1o2p`](…)
```

A full sample generated from a real repository is in
[`sample-output/CHANGELOG.md`](sample-output/CHANGELOG.md), and the acceptance-criteria
walkthrough with raw command output is in [`VERIFICATION.md`](VERIFICATION.md).

## Category mapping

| Section | Conventional types | Keyword fallback |
|---------|--------------------|------------------|
| **Added** | `feat`, `feature`, `add` | add · implement · introduce · create · new · support · initial · init · bootstrap |
| **Fixed** | `fix`, `bugfix`, `hotfix` | fix · bug · repair · patch · resolve · correct · regression |
| **Changed** | `refactor`, `perf`, `docs`, `chore`, `ci`, `build`, `test`, `style`, `update` | *(default bucket)* |
| **Removed** | `remove`, `delete`, `drop`, `revert` | remove · delete · drop · revert · deprecate |

Scopes and breaking markers are preserved: `feat(auth)!: …` →
`- **BREAKING** **auth:** …`.

## Options

| Flag | Default | Meaning |
|------|---------|---------|
| `-o, --output <path>` | `CHANGELOG.md` | where to write |
| `--from-tag <rev>` | last git tag | start of the range |
| `--to <rev>` | `HEAD` | end of the range |
| `--version <v>` | `Unreleased` | version heading |
| `--stdout` | off | print instead of writing |
| `--include-merges` | off | include merge commits |
| `--no-refs` | off | omit `(#id)` and commit links |

## Requirements

- `git` on `PATH`
- `python3` (3.8+) on `PATH`

Both are checked at startup, and each failure names the fix rather than just the
problem. If either is missing you get a one-line message telling you what to
install.

## Design notes

- **Why the keyword fallback exists**: most repositories older than a couple of
  years have no Conventional Commits discipline. Without a fallback those
  histories produce an empty changelog, which is the failure mode that makes a
  generator useless in practice.
- **Why separators are `\x1f`/`\x1e`**: parsing `git log` line-by-line breaks the
  moment a commit body is multi-line. Using ASCII unit/record separators makes
  the parse unambiguous.
- **Why an empty range still writes a document**: "no changes since the last
  tag" is a legitimate state, not an error to dump on stderr and exit 1 over.
- **Exit codes**: `0` success · `2` not a git repository · `3` output not writable
  · `127` a required binary is missing.

## License

MIT — see [LICENSE](LICENSE).
