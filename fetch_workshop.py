#!/usr/bin/env python3
"""Parse workshop.md and copy listed files from ../meta_practice."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

SECTION_HEADER = "## 가져올 파일 목록"
ITEM_PATTERN = re.compile(
    r"^(?P<prefix>\s*-\s*(?:\[(?P<state>[ xX])\]\s*)?)"
    r"`?(?P<src>[^`\s]+)`?"
    r"(?:\s*->\s*`?(?P<dst>[^`\s]+)`?)?"
    r"(?P<suffix>.*)$"
)
IGNORE_PATTERNS = shutil.ignore_patterns("__pycache__", "*.pyc", ".venv", ".DS_Store")


def resolve_source(source_root: Path, rel_path: str) -> Path | None:
    direct = source_root / rel_path
    if direct.exists():
        return direct
    fallback = source_root / "agent" / rel_path
    if fallback.exists():
        return fallback
    return None


def copy_entry(src: Path, dst: Path, dry_run: bool) -> None:
    if src.is_dir():
        if not dry_run:
            shutil.copytree(src, dst, dirs_exist_ok=True, ignore=IGNORE_PATTERNS)
    else:
        if not dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def process_markdown(
    md_path: Path,
    source_root: Path,
    dest_root: Path,
    dry_run: bool = False,
    mark_done: bool = False,
    include_checked: bool = False,
) -> int:
    lines = md_path.read_text(encoding="utf-8").splitlines(keepends=True)
    in_section = False
    updated_lines: list[str] = []
    copied_count = 0
    errors = 0

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            in_section = stripped == SECTION_HEADER
            updated_lines.append(line)
            continue

        if not in_section:
            updated_lines.append(line)
            continue

        match = ITEM_PATTERN.match(line.rstrip("\r\n"))
        if not match:
            updated_lines.append(line)
            continue

        state = match.group("state")
        if state and state.lower() == "x" and not include_checked:
            updated_lines.append(line)
            continue

        raw_src = match.group("src")
        raw_dst = match.group("dst") or raw_src

        src_path = resolve_source(source_root, raw_src)
        if src_path is None:
            print(f"[MISSING] {raw_src} (searched in {source_root})", file=sys.stderr)
            errors += 1
            updated_lines.append(line)
            continue

        dst_path = dest_root / raw_dst
        action = "DRY-RUN" if dry_run else "COPIED"
        kind = "DIR " if src_path.is_dir() else "FILE"
        print(f"[{action}] ({kind}) {src_path} -> {dst_path}")

        copy_entry(src_path, dst_path, dry_run=dry_run)
        copied_count += 1

        if mark_done and not dry_run and state is not None:
            newline = "\r\n" if line.endswith("\r\n") else ("\n" if line.endswith("\n") else "")
            new_line = re.sub(r"\[\s\]", "[x]", line.rstrip("\r\n"), count=1) + newline
            updated_lines.append(new_line)
        else:
            updated_lines.append(line)

    if mark_done and not dry_run and copied_count > 0:
        md_path.write_text("".join(updated_lines), encoding="utf-8")
        print(f"[UPDATED] Marked {copied_count} item(s) as [x] in {md_path}")

    print(f"Summary: {copied_count} processed, {errors} missing.")
    return 1 if errors > 0 else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch files listed in workshop.md")
    parser.add_argument("--md", type=Path, default=Path("workshop.md"), help="Markdown file path")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("../meta_practice"),
        help="Workshop source root directory",
    )
    parser.add_argument("--dest", type=Path, default=Path("."), help="Destination root directory")
    parser.add_argument("--dry-run", action="store_true", help="Preview without copying")
    parser.add_argument("--mark-done", action="store_true", help="Mark copied items as [x] in md")
    parser.add_argument("--all", action="store_true", help="Include already checked [x] items")
    args = parser.parse_args()

    if not args.md.exists():
        print(f"Error: Markdown file not found: {args.md}", file=sys.stderr)
        return 1
    if not args.source.exists():
        print(f"Error: Source directory not found: {args.source}", file=sys.stderr)
        return 1

    return process_markdown(
        md_path=args.md,
        source_root=args.source,
        dest_root=args.dest,
        dry_run=args.dry_run,
        mark_done=args.mark_done,
        include_checked=args.all,
    )


if __name__ == "__main__":
    raise SystemExit(main())
