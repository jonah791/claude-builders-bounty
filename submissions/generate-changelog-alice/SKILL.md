---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a project's git history. Categorizes commits into Added / Fixed / Changed / Removed, using Conventional Commits with a keyword fallback for non-conventional histories. Use when the user asks to write or update a changelog, prepare a release, summarize what changed since the last tag, or turn a git log into release notes.
---

# Generate Changelog

Turn a project's git history into a structured `CHANGELOG.md` following the
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) convention.

## When to use this skill

- The user asks for a changelog, release notes, or "what changed since vX".
- The user is preparing a release and needs the changes summarized.
- The user wants a git log turned into something a human can read.

## How to run it

From the root of the repository you want a changelog for:

```bash
# Default: commits from the last git tag up to HEAD → ./CHANGELOG.md
bash changelog.sh

# Preview without writing a file
bash changelog.sh --stdout

# Explicit range and version heading
bash changelog.sh --from-tag v1.2.0 --version 1.3.0

# A repo with no tags yet (uses full history automatically)
bash changelog.sh --stdout
```

## What it produces

Four sections, in this order:

| Section | Fed by |
|---------|--------|
| **Added** | `feat`, `feature`, `add` — and subjects like "add/implement/introduce/create/init" |
| **Fixed** | `fix`, `bugfix`, `hotfix` — and "fix/bug/repair/patch/resolve/regression" |
| **Changed** | `refactor`, `perf`, `docs`, `chore`, `ci`, `build`, `test`, … and the default |
| **Removed** | `remove`, `delete`, `drop`, `revert` — and "remove/delete/drop/deprecate" |

Conventional Commits are parsed first, including scope and the breaking marker:

- `feat(auth): add refresh tokens` → **Added** → `- **auth:** add refresh tokens`
- `fix!: drop support for node 16` → **Fixed** → `- **BREAKING** drop support for node 16`

Anything that is not conventional-commit formatted falls back to intent
keywords, so real-world repositories still produce a useful changelog instead of
an empty one.

## Options

| Flag | Default | Meaning |
|------|---------|---------|
| `-o, --output` | `CHANGELOG.md` | output path |
| `--from-tag` | last git tag | start revision |
| `--to` | `HEAD` | end revision |
| `--version` | `Unreleased` | version heading |
| `--stdout` | off | print instead of writing |
| `--include-merges` | off | include merge commits |
| `--no-refs` | off | omit issue refs and commit links |

## Working notes for the agent

- **Always run it in the repository under discussion** — the tool reads `git log`
  from the current working directory, not from where the script lives.
- **Preview first** (`--stdout`) when the user has not asked you to write a file;
  only write `CHANGELOG.md` when they want it committed.
- **An empty range is not an error**: a repo with no commits since the last tag
  yields a valid document with a "no user-facing changes" note.
- **Review before committing**: conventional-commit *types* are only as accurate
  as the commits. If a commit is typed `feat:` but actually removes something,
  the tool follows the commit — fix the commit or edit the generated file.
- **Non-conventional histories** are the common case in older projects; the
  keyword fallback is what keeps those useful, and it is deliberately biased
  toward "Changed" rather than guessing.
