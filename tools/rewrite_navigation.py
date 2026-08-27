from __future__ import annotations

import os
import re
from pathlib import Path, PurePosixPath
from urllib.parse import unquote

import quality
from generate_redirects import Redirect, load_redirects


PART_REPLACEMENTS = (
    ("卷零", "第一篇"),
    ("卷一", "第二篇"),
    ("卷二", "第三篇"),
    ("卷三", "第四篇"),
    ("卷四", "第五篇"),
    ("卷五", "第六篇"),
    ("卷六", "第七篇"),
    ("卷七", "第八篇"),
    ("卷八", "第九篇"),
    ("下一卷", "下一篇"),
    ("本卷", "本篇"),
)


def _route_to_doc_path(route: str) -> Path:
    trimmed = route.rstrip("/")
    parts = PurePosixPath(trimmed).parts
    if len(parts) == 1:
        return Path("docs", *parts, "index.md")
    return Path("docs", *parts[:-1], parts[-1] + ".md")


def build_path_map(redirects: list[Redirect]) -> dict[Path, Path]:
    return {
        _route_to_doc_path(row.source): _route_to_doc_path(row.target)
        for row in redirects
    }


def _split_suffix(raw: str) -> tuple[str, str]:
    positions = [index for index in (raw.find("?"), raw.find("#")) if index >= 0]
    if not positions:
        return raw, ""
    first = min(positions)
    return raw[:first], raw[first:]


def rewrite_links(
    text: str,
    current_path: Path,
    original_path: Path,
    docs_root: Path,
    absolute_map: dict[Path, Path],
) -> str:
    def replace(match: re.Match[str]) -> str:
        whole = match.group(0)
        raw = match.group(1).strip()
        if raw.startswith(("http://", "https://", "mailto:", "data:", "#")):
            return whole
        path_part, suffix = _split_suffix(raw)
        if not path_part:
            return whole
        current_target = (current_path.parent / unquote(path_part)).resolve()
        try:
            current_target.relative_to(docs_root.resolve())
        except ValueError:
            current_target = None
        if current_target is not None and current_target.exists():
            return whole
        old_target = (original_path.parent / unquote(path_part)).resolve()
        new_target = absolute_map.get(old_target, old_target)
        try:
            new_target.relative_to(docs_root.resolve())
        except ValueError:
            return whole
        relative = os.path.relpath(new_target, start=current_path.parent).replace("\\", "/")
        new_raw = relative + suffix
        return whole.replace(match.group(1), new_raw, 1)

    return quality.LINK_PATTERN.sub(replace, text)


def shift_chapter_references(text: str, current_number: int | None) -> str:
    range_pattern = re.compile(r"第\s*([1-9]|[1-3][0-9]|4[01])\s*[–-]\s*([1-9]|[1-3][0-9]|4[01])\s*章")
    single_pattern = re.compile(r"第\s*([1-9]|[1-3][0-9]|4[01])\s*章")
    output: list[str] = []
    fenced = False
    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            output.append(line)
            continue
        if fenced or line.startswith("# "):
            output.append(line)
            continue
        if current_number is not None and re.search(
            rf"第\s*{current_number}\s*章", line
        ):
            output.append(line)
            continue
        line = range_pattern.sub(
            lambda match: f"第 {int(match.group(1)) + 5}–{int(match.group(2)) + 5} 章",
            line,
        )
        line = single_pattern.sub(
            lambda match: f"第 {int(match.group(1)) + 5} 章", line
        )
        output.append(line)
    return "".join(output)


def _relative_link(source: Path, target: Path) -> str:
    return os.path.relpath(target, start=source.parent).replace("\\", "/")


def rewrite_chapter_navigation(root: Path, manifest: list[dict[str, str]]) -> None:
    numbered = [
        row for row in manifest if row["kind"] in {"foundation", "chapter"}
    ]
    for index, row in enumerate(numbered):
        path = root / row["path"]
        links: list[str] = []
        if index > 0:
            previous = numbered[index - 1]
            links.append(
                f"[上一章：{previous['title']}]"
                f"({_relative_link(path, root / previous['path'])})"
            )
        links.append("[返回本篇](index.md)")
        if index < len(numbered) - 1:
            following = numbered[index + 1]
            links.append(
                f"[下一章：{following['title']}]"
                f"({_relative_link(path, root / following['path'])})"
            )
        text = path.read_text(encoding="utf-8")
        pattern = re.compile(
            r"^##\s+章节导航\s*\r?\n.*?\Z", flags=re.MULTILINE | re.DOTALL
        )
        replacement = "## 章节导航\n\n" + " · ".join(links) + "\n"
        rewritten, count = pattern.subn(replacement, text)
        if count != 1:
            raise ValueError(f"expected one final navigation section: {row['path']}")
        path.write_text(rewritten, encoding="utf-8")


def rewrite_tree(root: Path) -> int:
    docs_root = (root / "docs").resolve()
    redirects = load_redirects(root / "metadata" / "legacy-redirects.csv")
    relative_map = build_path_map(redirects)
    absolute_map = {
        (root / old).resolve(): (root / new).resolve()
        for old, new in relative_map.items()
    }
    inverse = {new: old for old, new in absolute_map.items()}
    manifest = quality.load_manifest(root / "metadata" / "chapter-manifest.csv")
    number_by_path = {
        (root / row["path"]).resolve(): int(row["number"])
        for row in manifest
        if row["kind"] in {"foundation", "chapter"}
    }
    changed = 0
    for path in sorted(docs_root.rglob("*.md")):
        current = path.resolve()
        relative = path.relative_to(docs_root)
        original = current if relative.parts[0] == "01-foundations" else inverse.get(current, current)
        text = path.read_text(encoding="utf-8")
        rewritten = rewrite_links(text, current, original, docs_root, absolute_map)
        if relative.parts[0] != "01-foundations" and (
            relative.parts[0] in {
                "02-bringup",
                "03-chassis-control",
                "04-ros2-development",
                "05-sensors-navigation",
                "06-stm32-firmware",
                "07-advanced-applications",
                "08-r680-platform",
                "09-deployment-maintenance",
                "appendices",
            }
        ):
            rewritten = shift_chapter_references(
                rewritten, number_by_path.get(current)
            )
        for old, new in PART_REPLACEMENTS:
            rewritten = rewritten.replace(old, new)
        if rewritten != text:
            path.write_text(rewritten, encoding="utf-8")
            changed += 1
    rewrite_chapter_navigation(root, manifest)
    return changed


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    changed = rewrite_tree(root)
    print(f"rewrote navigation and references in {changed} Markdown files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
