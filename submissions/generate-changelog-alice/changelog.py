#!/usr/bin/env python3
"""
generate-changelog — turn a project's git history into a structured CHANGELOG.md

Zero third-party dependencies (Python 3.8+ standard library only).
Output follows the Keep a Changelog convention, with the four categories the
bounty asks for: Added / Fixed / Changed / Removed.

Bounty: claude-builders-bounty#1  ·  $50 (Opire)
Usage:  python3 changelog.py [options]      (or:  bash changelog.sh [options])
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from collections import OrderedDict
from datetime import date

# ── Conventional-commit type → Keep a Changelog section ───────────────────────
# The four sections the bounty requires are explicit; everything else that is a
# legitimate commit type lands in "Changed" so nothing is silently dropped.
CATEGORY_MAP = {
    "feat": "Added",
    "feature": "Added",
    "add": "Added",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "hotfix": "Fixed",
    "perf": "Changed",
    "refactor": "Changed",
    "change": "Changed",
    "update": "Changed",
    "style": "Changed",
    "docs": "Changed",
    "doc": "Changed",
    "test": "Changed",
    "tests": "Changed",
    "chore": "Changed",
    "build": "Changed",
    "ci": "Changed",
    "remove": "Removed",
    "removal": "Removed",
    "delete": "Removed",
    "drop": "Removed",
    "revert": "Removed",
}

SECTION_ORDER = ["Added", "Fixed", "Changed", "Removed"]

# Keyword fallback for commits that are not conventional-commit formatted.
# Ordered: more specific intents win before the generic "Changed" default.
KEYWORD_FALLBACK = [
    ("Removed", re.compile(r"\b(remove[ds]?|delet(e|ed|ing)|drop(ped|ping)?|revert(ed|ing)?|deprecat(e|ed|ing))\b", re.I)),
    ("Fixed", re.compile(r"\b(fix(e[ds])?|fixing|bug|bugs|repair(ed|s)?|patch(ed)?|resolv(e|ed|es|ing)|correct(ed|s)?|regression|hotfix)\b", re.I)),
    ("Added", re.compile(r"\b(add(ed|s|ing)?|implement(ed|s|ing)?|introduc(e|ed|es|ing)|creat(e|ed|es|ing)|new|support(s|ed)?|initial|init|bootstrap|scaffold)\b", re.I)),
]

# "feat(scope)!: subject" / "fix: subject" / "FIX : subject"
CC_RE = re.compile(r"^(?P<type>[A-Za-z]+)(?:\((?P<scope>[^)]*)\))?(?P<breaking>!)?\s*:\s*(?P<subject>.+)$")

# "Merge pull request #12 from ..." / "Merge branch 'x'" — noise by default
MERGE_RE = re.compile(r"^Merge (pull request|branch|remote-tracking)", re.I)

ISSUE_RE = re.compile(r"(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)", re.I)
HASH_RE = re.compile(r"\(#(\d+)\)")


def run_git(args: list[str]) -> str | None:
    """Run a git command, returning stdout or None when git fails."""
    try:
        proc = subprocess.run(
            ["git", *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except (OSError, ValueError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.decode("utf-8", errors="replace")


def in_git_repo() -> bool:
    return run_git(["rev-parse", "--git-dir"]) is not None


def last_tag() -> str | None:
    """Most recent tag reachable from HEAD, or None for a repo with no tags."""
    tag = run_git(["describe", "--tags", "--abbrev=0"])
    if tag is None:
        return None
    tag = tag.strip()
    return tag or None


def resolve_range(since: str | None, to: str) -> str | None:
    """Return the git revision range, or None when the range cannot be built."""
    if since is None:
        return to
    # Guard against a tag that is not an ancestor of `to` (git log would fail).
    if run_git(["rev-parse", "--verify", f"{since}^{{commit}}"]) is None:
        return None
    return f"{since}..{to}"


def read_commits(rev_range: str, include_merges: bool) -> list[dict]:
    """
    Read commits in `rev_range` using ASCII unit/record separators so that
    multi-line commit bodies parse reliably (the common failure mode of
    line-based parsing).
    """
    fmt = "%H%x1f%s%x1f%b%x1e"
    out = run_git(["log", rev_range, f"--pretty=format:{fmt}", "--no-color"])
    if not out:
        return []

    commits: list[dict] = []
    for record in out.split("\x1e"):
        record = record.strip("\n")
        if not record:
            continue
        parts = record.split("\x1f")
        if len(parts) < 2:
            continue
        sha, subject = parts[0].strip(), parts[1].strip()
        body = parts[2] if len(parts) > 2 else ""
        if not subject:
            continue
        if not include_merges and MERGE_RE.match(subject):
            continue
        commits.append({"sha": sha, "subject": subject, "body": body})
    return commits


def classify(subject: str) -> tuple[str, str]:
    """
    Return (section, cleaned_subject).

    Conventional commits are honoured first (type + optional scope/breaking
    marker); subjects that are not conventional fall back to intent keywords so
    that real-world histories still produce a useful changelog.
    """
    match = CC_RE.match(subject)
    if match:
        ctype = match.group("type").lower()
        if ctype in CATEGORY_MAP:
            scope = match.group("scope")
            breaking = match.group("breaking")
            text = match.group("subject").strip()
            prefix = ""
            if scope:
                prefix = f"**{scope}:** "
            if breaking:
                prefix = "**BREAKING** " + prefix
            # Keep the original casing of the subject's first character.
            return CATEGORY_MAP[ctype], prefix + text

    for section, pattern in KEYWORD_FALLBACK:
        if pattern.search(subject):
            return section, subject
    return "Changed", subject


def referenced_issues(commit: dict) -> list[str]:
    refs = set(ISSUE_RE.findall(commit["body"])) | set(HASH_RE.findall(commit["subject"]))
    return sorted(refs, key=lambda n: int(n))


def build_changelog(commits: list[dict], version: str, title: str, repo_url: str | None, with_refs: bool) -> str:
    sections: "OrderedDict[str, list[str]]" = OrderedDict((name, []) for name in SECTION_ORDER)
    seen: set[str] = set()

    for commit in commits:
        section, text = classify(commit["subject"])
        # Normalise in-subject references once, so a subject that already ends
        # with "(#7)" does not produce "(#7) (#7)" after we append references.
        if with_refs:
            text = HASH_RE.sub("", text).strip()
        text = text.rstrip(". ")
        if not text:
            continue
        line = f"- {text}"
        if with_refs:
            refs = referenced_issues(commit)
            if refs:
                line += " (" + ", ".join(f"#{n}" for n in refs) + ")"
            if repo_url:
                line += f" — [`{commit['sha'][:7]}`]({repo_url}/commit/{commit['sha']})"
        key = line.lower()
        if key in seen:
            continue
        seen.add(key)
        sections[section].append(line)

    today = date.today().isoformat()
    out = [f"# Changelog", ""]
    out.append("All notable changes to this project are documented in this file.")
    out.append("")
    out.append("The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),")
    out.append("and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).")
    out.append("")
    out.append(f"## [{version}] - {today}")
    out.append("")

    empty = True
    for name in SECTION_ORDER:
        items = sections[name]
        if not items:
            continue
        empty = False
        out.append(f"### {name}")
        out.append("")
        out.extend(items)
        out.append("")

    if empty:
        out.append("_No user-facing changes in this range._")
        out.append("")

    return "\n".join(out).rstrip() + "\n"


def repo_url_of(remote: str = "origin") -> str | None:
    url = run_git(["config", "--get", f"remote.{remote}.url"])
    if not url:
        return None
    url = url.strip()
    # git@github.com:owner/repo.git → https://github.com/owner/repo
    m = re.match(r"git@([^:]+):(.+?)(?:\.git)?$", url)
    if m:
        return f"https://{m.group(1)}/{m.group(2)}"
    m = re.match(r"https?://(.+?)(?:\.git)?$", url)
    if m:
        return f"https://{m.group(1)}"
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="changelog",
        description="Generate a structured CHANGELOG.md from git history.",
    )
    parser.add_argument("-o", "--output", default="CHANGELOG.md", help="output file (default: CHANGELOG.md)")
    parser.add_argument("--from-tag", default=None, help="start revision (default: the last git tag)")
    parser.add_argument("--to", default="HEAD", help="end revision (default: HEAD)")
    parser.add_argument("--version", default="Unreleased", help="version heading (default: Unreleased)")
    parser.add_argument("--title", default="Changelog", help="document title")
    parser.add_argument("--stdout", action="store_true", help="print to stdout instead of writing a file")
    parser.add_argument("--include-merges", action="store_true", help="include merge commits (skipped by default)")
    parser.add_argument("--no-refs", action="store_true", help="omit issue references and commit links")
    args = parser.parse_args(argv)

    if not in_git_repo():
        print("changelog: not a git repository (run this inside a repo, or pass --from-tag/--to)", file=sys.stderr)
        return 2

    since = args.from_tag
    used_tag = None
    if since is None:
        used_tag = last_tag()
        since = used_tag

    rev_range = resolve_range(since, args.to)
    if rev_range is None:
        print(f"changelog: cannot resolve range {since}..{args.to}; falling back to full history", file=sys.stderr)
        rev_range = args.to
        since = None

    commits = read_commits(rev_range, args.include_merges)
    if not commits:
        print(f"changelog: no commits found in range ({since or 'beginning'}..{args.to})", file=sys.stderr)
        # Still emit a valid document — an empty range is a legitimate state.
        commits = []

    doc = build_changelog(
        commits,
        version=args.version,
        title=args.title,
        repo_url=None if args.no_refs else repo_url_of(),
        with_refs=not args.no_refs,
    )

    if args.stdout:
        sys.stdout.write(doc)
        return 0

    try:
        with open(args.output, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(doc)
    except OSError as exc:
        print(f"changelog: cannot write {args.output}: {exc}", file=sys.stderr)
        return 3

    span = f"{since or 'beginning'}..{args.to}"
    print(f"changelog: wrote {args.output} — {len(commits)} commit(s) from {span}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
