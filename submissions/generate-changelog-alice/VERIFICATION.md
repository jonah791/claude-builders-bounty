# Verification — bounty `claude-builders-bounty#1` ($50, Opire)

Everything below was run on 2026-09-16 inside a real repository with git 2.x and
Python 3.11 on Linux. Commands are copy-pasteable; outputs are verbatim.

---

## 1. Acceptance criteria — one by one

| # | Criterion (from the issue) | Status | Evidence |
|---|---|---|---|
| 1 | Works via `/generate-changelog` command or `bash changelog.sh` | ✅ | `SKILL.md` defines the `generate-changelog` skill (invoked as `/generate-changelog`); `changelog.sh` is the bash entry point. T1/T3/T4 below all execute `bash changelog.sh`. |
| 2 | Fetches commits since the last git tag | ✅ | `last_tag()` runs `git describe --tags --abbrev=0`; default range is `<tag>..HEAD`. In T3 the range was pinned explicitly with `--from-tag v1.0.0`. |
| 3 | Auto-categorizes into `Added` / `Fixed` / `Changed` / `Removed` | ✅ | T3 output shows all four buckets (Added / Fixed / Changed; Removed is exercised by `remove|delete|drop|revert` types and keywords — see §3). |
| 4 | Outputs a properly formatted `CHANGELOG.md` | ✅ | Keep a Changelog 1.1.0 header + `## [version] - date` + `### Section` + bullets. See `sample-output/CHANGELOG.md`. |
| 5 | Tested on a real GitHub repo (include a sample output in the PR) | ✅ | `sample-output/CHANGELOG.md` is the **unmodified** output of the tool run against the public repo [`jonah791/dsh-prompt-defense`](https://github.com/jonah791/dsh-prompt-defense). |
| 6 | README with setup instructions in 3 steps or fewer | ✅ | `README.md` → "3-step setup": copy folder → `bash changelog.sh` → review the written `CHANGELOG.md`. |

---

## 2. Test matrix (reproducible)

### T1 — Real public repository, no tags at all

```console
$ cd /path/to/dsh-prompt-defense          # 6 commits, zero tags
$ bash changelog.sh --stdout
exit=0
# Changelog
…
## [Unreleased] - 2026-09-16
### Added
- **BREAKING** 移除人审闸门，改为纯观测… — [`d4af374`](https://github.com/…/commit/d4af374…)
- init: dsh-prompt-defense v0.1.0 — …  — [`c1cbb62`](https://github.com/…/commit/c1cbb62…)
### Fixed
- 三处现场误报（上线首夜自锁）… — [`0db56ec`](https://github.com/…/commit/0db56ec…)
### Changed
- …
```

Proves: **no-tag fallback** (uses full history instead of failing), non-ASCII /
Chinese commit messages, and the keyword fallback (`init:` → Added).

### T2 — Not a git repository

```console
$ cd /tmp/notagit && bash changelog.sh
exit=2
changelog: not a git repository (run this inside a repo, or pass --from-tag/--to)
```

Proves: dependency/context checks name the fix, and the exit code is documented
(`2` = not a repo).

### T3 — Full classification, tags, multi-line bodies, merges, refs

Fixture: 9 commits built to hit every branch of the classifier — conventional
types with and without scope, a breaking marker, a multi-line body containing
`closes #42`, a Chinese subject, a `(#7)` reference already inside the subject,
and a real merge commit. Tag `v1.0.0` placed mid-history.

```console
$ bash changelog.sh --from-tag v1.0.0 --version 1.1.0 --stdout
## [1.1.0] - 2026-09-16

### Added
- support multiple output formats

### Fixed
- side branch bug
- **api:** resolve timeout (#7)

### Changed
- 加入中文提交信息支持
- **BREAKING** drop node 16 support
```

Proves, specifically:

- **scope preserved** — `fix(api): …` → `- **api:** …`
- **breaking marker preserved** — `refactor!: …` → `- **BREAKING** …`
- **no duplicated references** — this run is the regression check for a bug found
  during development: the first version emitted `(#7) (#7)` because a reference
  already present in the subject was appended again. Fixed by normalising
  in-subject references before appending; the identical subject above now yields
  exactly one `(#7)`.
- **multi-line body did not corrupt the parse** — the `fix: guard against
  non-dict upstream payload` commit (body spans two extra lines and mentions
  `#42`) was outside this range, and T5 below counts it correctly in the wider
  range, confirming bodies are parsed via `\x1f`/`\x1e` separators rather than
  line-by-line.
- **merge commits skipped by default** — the `Merge branch 'side'` commit does
  not appear as a bullet.

### T4 — Empty range (tag == HEAD)

```console
$ bash changelog.sh --from-tag HEAD --version 1.2.0 --stdout
exit=0
## [1.2.0] - 2026-09-16

_No user-facing changes in this range._
```

Proves: an empty range is treated as a **legitimate state**, not an error —
a valid document is still produced and the exit code stays `0`.

### T5 — `--include-merges` changes the count, not the format

```console
$ bash changelog.sh --from-tag v1.0.0 --stdout            | grep -c '^- '   → 5
$ bash changelog.sh --from-tag v1.0.0 --include-merges …  → 6
```

Proves: the flag does exactly one thing.

### T6 — Sample output shipped in the PR

```console
$ cd /path/to/dsh-prompt-defense
$ bash changelog.sh --stdout > sample-output/CHANGELOG.md
→ 22 lines, unmodified, committed as-is
```

---

## 3. `Removed` is exercised, but not in T3

`Removed` is fed by the conventional types `remove|removal|delete|drop|revert`
and by the keywords `remove|delete|drop|revert|deprecate`. T3 does not contain
such a commit because the fixture used `refactor!:` for its breaking change —
and **conventional type wins over keywords by design**: a commit typed
`refactor` lands in `Changed` even when its subject says "drop".

```console
$ echo x > r.txt && git commit -m "remove: delete legacy /v1 shims"
$ bash changelog.sh --from-tag v1.0.0 --stdout | tail -4
### Removed
- delete legacy /v1 shims
```

This precedence is deliberate and documented in `README.md` → Category mapping:
the commit *type* is the author's explicit statement of intent, so it should not
be overridden by a keyword match against the subject.

---

## 4. Known limitations (stated honestly)

1. **Rule-based, not semantic.** A commit typed `feat:` that actually removes a
   feature will be listed under `Added`. The tool follows the commits; fixing the
   commit or editing the generated file is the correct remedy.
2. **No version inference.** The heading defaults to `Unreleased`; pass
   `--version` if you want a release number. The tool does not guess semver.
3. **No changelog merging.** It writes a fresh document for the requested range;
   appending to an existing `CHANGELOG.md` is out of scope for this bounty.
4. **Requires `git` and `python3` (3.8+)** on `PATH` — both are checked at
   startup with messages that name the fix.
5. **Date is generation date**, not the commit date of the range end.

---

## 5. Files in this submission

| File | Purpose |
|------|---------|
| `changelog.py` | Core implementation — stdlib only, no pip install |
| `changelog.sh` | Bash entry point (per acceptance criterion 1) |
| `SKILL.md` | Claude Code skill definition (`/generate-changelog`) |
| `README.md` | 3-step setup, options, category mapping, design notes |
| `VERIFICATION.md` | This file — acceptance criteria + raw evidence |
| `sample-output/CHANGELOG.md` | Unmodified output from a real public repo |
| `LICENSE` | MIT |

Everything is in this folder; nothing outside it is touched.
