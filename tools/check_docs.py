#!/usr/bin/env python3
"""Check repository-local Markdown links. External URLs are not requested."""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlsplit

SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "build", "dist",
             "__pycache__", "Debug", "Release"}
INLINE_LINK = re.compile(r"!?\[[^\]\n]*\]\(\s*(<[^>]+>|[^\s)]+)"
                         r"(?:\s+[\"'][^\"']*[\"'])?\s*\)")
REFERENCE_DEF = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*(<[^>]+>|\S+)", re.M)
HTML_ANCHOR = re.compile(r"\b(?:id|name)\s*=\s*[\"']([^\"']+)[\"']", re.I)


def without_fences(text: str) -> str:
    result = []
    fence_char = None
    fence_length = 0
    for line in text.splitlines():
        marker = re.match(r"^\s{0,3}(\x60{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if fence_char is None:
                fence_char, fence_length = token[0], len(token)
            elif token[0] == fence_char and len(token) >= fence_length:
                fence_char = None
            result.append("")
        else:
            result.append("" if fence_char else line)
    return "\n".join(result)


def heading_slug(text: str) -> str:
    text = re.sub(r"<[^>]*>", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = text.replace(chr(96), "").replace("*", "").lower()
    text = "".join(c for c in text if c in "-_ " or
                   unicodedata.category(c)[0] in "LN")
    return text.replace(" ", "-")


def anchors(text: str) -> set[str]:
    clean = without_fences(text)
    found = set(HTML_ANCHOR.findall(clean))
    counts: dict[str, int] = {}
    for match in re.finditer(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", clean, re.M):
        slug = heading_slug(match.group(1))
        count = counts.get(slug, 0)
        candidate = slug if count == 0 else f"{slug}-{count}"
        while candidate in found:
            count += 1
            candidate = f"{slug}-{count}"
        counts[slug] = count + 1
        found.add(candidate)
    return found


def markdown_files(root: Path):
    for path in sorted(root.rglob("*.md")):
        if not any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            yield path


def check(root: Path) -> tuple[int, int, list[str]]:
    errors = []
    total_links = 0
    total_files = 0
    cache: dict[Path, set[str]] = {}
    for source in markdown_files(root):
        total_files += 1
        clean = without_fences(source.read_text(encoding="utf-8"))
        targets = [m.group(1) for m in INLINE_LINK.finditer(clean)]
        targets += [m.group(1) for m in REFERENCE_DEF.finditer(clean)]
        for raw in targets:
            url = raw.strip("<>")
            parsed = urlsplit(url)
            if parsed.scheme or parsed.netloc:
                continue
            total_links += 1
            target = source if not parsed.path else (
                root / unquote(parsed.path.lstrip("/")) if parsed.path.startswith("/")
                else source.parent / unquote(parsed.path)
            )
            target = target.resolve()
            location = source.relative_to(root).as_posix()
            try:
                target.relative_to(root)
            except ValueError:
                errors.append(f"{location}: link escapes repository: {url}")
                continue
            if not target.exists():
                errors.append(f"{location}: missing target: {url}")
                continue
            if parsed.fragment and target.is_file() and target.suffix.lower() == ".md":
                if target not in cache:
                    cache[target] = anchors(target.read_text(encoding="utf-8"))
                if unquote(parsed.fragment) not in cache[target]:
                    errors.append(f"{location}: missing heading/anchor: {url}")
    return total_files, total_links, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path,
                        default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        parser.error("root must be a directory")
    files, links, errors = check(root)
    for error in errors:
        print(f"[ERROR] {error}", file=sys.stderr)
    print(f"[{'FAIL' if errors else 'OK'}] {files} Markdown files; "
          f"{links} local links; {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
