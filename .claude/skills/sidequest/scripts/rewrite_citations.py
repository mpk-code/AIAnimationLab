#!/usr/bin/env python3
"""Repair backticked repo-path citations that no longer resolve.

A markdown file cites a repository path in backticks — `sidequests/foo/foo-rollout.md:12` — and
the reader is meant to open it. When the file moves, the citation keeps the old coordinate. This
script finds each such citation that does not resolve and sorts it by cause, archived first:

  * archived — the path starts `sidequests/` and resolves once `archive/` is inserted after it:
    the quest was closed and moved. Rewritten.
  * moved — exactly one tracked file carries the cited basename. Rewritten to that file.
  * moved-ambiguous — several tracked files carry the basename. Listed with its candidates and
    never rewritten: choosing one would be a guess.
  * gone — no tracked file carries the basename. Listed, never rewritten.

A citation resolves when its path is tracked or exists on disk, relative to the repository root.

**Dry run is the default.** Without `--apply` the script prints what it would change and writes
nothing. With `--apply` it writes only the cited path substring of each rewritable citation; every
other byte of the file is kept as it was. `--only archived` (or `--only moved`) applies one cause
and reports the other as not applied: the archive step of `/sidequest close` rewrites what its own
move broke and nothing else.

Usage, from anywhere inside the repository:

    python3 .claude/skills/sidequest/scripts/rewrite_citations.py [--apply] [--only CAUSE] PATH [PATH ...]

Each PATH is a markdown file or a directory (read for `*.md` recursively). Output names files
relative to the repository root, as `<file>:<line>: <cause>: ...`, then one summary line.
Exit 0 on success, 2 when the arguments name no markdown file. Stdlib only.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

#: A backticked path under one of the repository's top-level trees, ending in an extension, with an
#: optional `:line` suffix. Group 1 is the path — the only bytes a rewrite replaces.
CITATION = re.compile(
    r"`((?:docs|scripts|sidequests|schemas|styles|skills|blender|validators|eval|decks|antidefaults"
    r"|tests|productions|\.claude)/[A-Za-z0-9_./-]+\.[a-z]{2,4})(?::\d+)?`"
)
ARCHIVE_FROM, ARCHIVE_TO = "sidequests/", "sidequests/archive/"


def repo_root() -> Path:
    out = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True
    ).stdout
    return Path(out.strip())


def tracked(root: Path) -> set[str]:
    out = subprocess.run(
        ["git", "-C", str(root), "ls-files"], capture_output=True, text=True, check=True
    ).stdout
    return {f for f in out.split("\n") if f}


def markdown_files(args: list[str]) -> list[Path]:
    files: set[Path] = set()
    for arg in args:
        p = Path(arg).resolve()
        if p.is_dir():
            files.update(p.rglob("*.md"))
        elif p.suffix == ".md" and p.is_file():
            files.add(p)
    return sorted(files)


def classify(
    path: str, root: Path, tr: set[str], bybase: dict[str, list[str]]
) -> tuple[str, str | None, list[str]] | None:
    """``None`` when ``path`` resolves; otherwise ``(cause, replacement or None, candidates)``."""
    if path in tr or (root / path).exists():
        return None
    if path.startswith(ARCHIVE_FROM):
        archived = ARCHIVE_TO + path[len(ARCHIVE_FROM) :]
        if archived in tr:
            return ("archived", archived, [])
    candidates = sorted(bybase.get(path.rsplit("/", 1)[-1], []))
    if len(candidates) == 1:
        return ("moved", candidates[0], candidates)
    if candidates:
        return ("moved-ambiguous", None, candidates)
    return ("gone", None, [])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("paths", nargs="+", help="markdown files or directories to read")
    parser.add_argument(
        "--apply", action="store_true", help="write the rewrites (default: dry run)"
    )
    parser.add_argument(
        "--only",
        choices=("archived", "moved"),
        help="rewrite this cause only; the other is listed as not applied",
    )
    args = parser.parse_args(argv)

    files = markdown_files(args.paths)
    if not files:
        print(
            "rewrite_citations: no markdown file in the given paths — nothing to read",
            file=sys.stderr,
        )
        return 2

    root = repo_root().resolve()
    tr = tracked(root)
    bybase: dict[str, list[str]] = defaultdict(list)
    for t in tr:
        bybase[t.rsplit("/", 1)[-1]].append(t)

    counts: dict[str, int] = defaultdict(int)
    changed_files = 0
    for f in files:
        raw = f.read_bytes()
        # surrogateescape round-trips any byte, so the bytes outside each span are written back
        # exactly as read; decoding does no newline translation.
        text = raw.decode("utf-8", errors="surrogateescape")
        rel = f.relative_to(root).as_posix()
        edits: list[tuple[int, int, str]] = []
        for m in CITATION.finditer(text):
            result = classify(m.group(1), root, tr, bybase)
            if result is None:
                continue
            cause, replacement, candidates = result
            counts[cause] += 1
            line = text.count("\n", 0, m.start()) + 1
            site = f"{rel}:{line}: {cause}: {m.group(1)}"
            if replacement is not None and args.only not in (None, cause):
                print(f"{site} -> {replacement} (not applied: --only {args.only})")
            elif replacement is not None:
                print(f"{site} -> {replacement}")
                edits.append((m.start(1), m.end(1), replacement))
            elif candidates:
                print(f"{site} (candidates: {', '.join(candidates)})")
            else:
                print(site)
        if edits and args.apply:
            for start, end, replacement in reversed(edits):
                text = text[:start] + replacement + text[end:]
            f.write_bytes(text.encode("utf-8", errors="surrogateescape"))
            changed_files += 1

    rewritable = counts["archived"] + counts["moved"]
    mode = (
        f"applied to {changed_files} file(s)"
        if args.apply
        else "dry run — nothing written (pass --apply to write)"
    )
    print(
        f"rewrite_citations: {rewritable} rewritable (archived {counts['archived']}, moved {counts['moved']}), "
        f"moved-ambiguous {counts['moved-ambiguous']}, gone {counts['gone']}, "
        f"across {len(files)} file(s); {mode}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
