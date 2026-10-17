#!/usr/bin/env python3
"""Quest soft integration gate resolver (run-process pre-flight, step 5).

Enumerates quest *frontmatter* in sidequests/*/ and sidequests/archive/*/ — not back-references —
and prints the done-but-unintegrated quests the given scope should surface.

Surfacing rule: a quest surfaces when its `parent:` is the scope (a quest owns the quests it
spawned) and it is `status: done` with `integrated: false`. Everything else is hidden — a
standalone quest (`parent: none`) has no owner to surface under, and there is no top-level scope.

Output: one line per surfaced quest, e.g.
    - probe-api (spike) [archived]: spike — acknowledge findings, then flip integrated:true
Nothing is printed when no quest qualifies. Exit 0 on success, 2 on usage error. No git or
prompt side effects; the caller decides what to do with the lines. Stdlib only.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import NamedTuple


class Quest(NamedTuple):
    slug: str
    status: str
    integrated: str
    parent: str
    qtype: str
    spec_refs: list[str]
    archived: bool


def _strip_inline_comment(value: str) -> str:
    """Drop a YAML inline comment. A '#' only starts a comment when preceded by
    whitespace, so a literal '#' inside a value survives, and `integrated: true  # note`
    still reads as true."""
    for sep in (" #", "\t#"):
        idx = value.find(sep)
        if idx != -1:
            value = value[:idx]
    return value.strip()


def _parse_frontmatter(text: str) -> tuple[dict[str, str], list[str]]:
    """Return (scalar fields, spec-refs list) from the first `---`…`---` block.

    A deliberately small YAML subset — `key: value` scalars plus a single
    block-sequence under `spec-refs:` (lines beginning `  - `). An inline `[]` reads
    as empty. Anything richer is not used by quest frontmatter.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, []
    fields: dict[str, str] = {}
    spec_refs: list[str] = []
    in_specrefs = False
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if in_specrefs:
            stripped = line.strip()
            if stripped.startswith("- "):
                spec_refs.append(_strip_inline_comment(stripped[2:]))
                continue
            # A non-indented, non-dash line ends the block sequence.
            if line[:1] not in (" ", "\t"):
                in_specrefs = False
            else:
                continue
        if line.startswith("spec-refs:"):
            in_specrefs = True
            continue
        if ":" in line and not line.startswith((" ", "\t")):
            key, _, value = line.partition(":")
            fields[key.strip()] = _strip_inline_comment(value)
    return fields, spec_refs


def _load_quest(rollout: Path, slug: str, *, archived: bool) -> Quest | None:
    try:
        fields, spec_refs = _parse_frontmatter(rollout.read_text(encoding="utf-8"))
    except OSError:
        return None
    if not fields:
        return None
    return Quest(
        slug=slug,
        status=fields.get("status", "").strip(),
        integrated=(fields.get("integrated", "false") or "false").strip().lower(),
        parent=(fields.get("parent", "none") or "none").strip(),
        qtype=fields.get("type", "").strip(),
        spec_refs=spec_refs,
        archived=archived,
    )


def enumerate_quests(root: Path) -> dict[str, Quest]:
    """Map slug -> Quest across sidequests/*/ and sidequests/archive/*/.

    Keyed strictly on `<dir>/<dir>-rollout.md`, so any other rollout-like file in a
    quest folder is ignored (it is not the quest's canonical rollout).
    """
    quests: dict[str, Quest] = {}
    sidequests = root / "sidequests"
    if not sidequests.is_dir():
        return quests

    def scan(base: Path, archived: bool) -> None:
        if not base.is_dir():
            return
        for qdir in sorted(base.iterdir()):
            if not qdir.is_dir() or qdir.name == "archive":
                continue
            rollout = qdir / f"{qdir.name}-rollout.md"
            if not rollout.is_file():
                continue
            quest = _load_quest(rollout, qdir.name, archived=archived)
            if quest is not None:
                quests[quest.slug] = quest

    scan(sidequests, archived=False)
    scan(sidequests / "archive", archived=True)
    return quests


def _reason(quest: Quest, root: Path) -> str:
    """Type-specific condition for flipping integrated:true."""
    if quest.qtype == "utility":
        if not quest.spec_refs:
            return "utility has empty spec-refs — cannot verify integration"
        missing = [ref for ref in quest.spec_refs if not (root / ref).is_file()]
        if missing:
            return "utility — missing spec files: " + "".join(f"{m} " for m in missing)
        return "utility — spec files at spec-refs paths exist; flip integrated:true to acknowledge"
    if quest.qtype == "feature":
        return "feature — confirm proposed changes have been applied to spec-refs paths, then flip integrated:true"
    if quest.qtype == "spike":
        return "spike — acknowledge findings, then flip integrated:true"
    return "review integration, then flip integrated:true"


def pending_for_scope(root: Path, scope: str) -> list[str]:
    """Formatted pending-quest lines for the given scope (a quest slug)."""
    quests = enumerate_quests(root)
    lines: list[str] = []
    for slug in sorted(quests):
        quest = quests[slug]
        # Candidate <=> a direct child of the scope that is closed (done) but not integrated.
        # Active, abandoned and integrated quests have nothing to gate on.
        if slug == scope or quest.parent != scope:
            continue
        if quest.status != "done" or quest.integrated == "true":
            continue
        loc_tag = " [archived]" if quest.archived else ""
        lines.append(f"  - {slug} ({quest.qtype}){loc_tag}: {_reason(quest, root)}")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve done-but-unintegrated quests for a pre-flight scope.")
    parser.add_argument("--scope", required=True, help="the slug of the quest being run")
    parser.add_argument("--root", default=".", help="repository root (default: cwd)")
    args = parser.parse_args(argv)
    scope = args.scope.strip()
    if not scope or scope == "none":
        parser.error("--scope must name a quest slug ('none' is the standalone parent marker, not a quest)")
    for line in pending_for_scope(Path(args.root), scope):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
