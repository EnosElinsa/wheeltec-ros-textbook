from __future__ import annotations

import argparse
import csv
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

from generate_redirects import Redirect, load_redirects


PART_TITLES = {
    "01-foundations": "第一篇：从零认识 ROS 机器人",
    "02-bringup": "第二篇：实机接入与首次启动",
    "03-chassis-control": "第三篇：底盘控制与运动学",
    "04-ros2-development": "第四篇：ROS 2 开发",
    "05-sensors-navigation": "第五篇：传感器、建图与导航",
    "06-stm32-firmware": "第六篇：STM32 与底盘固件",
    "07-advanced-applications": "第七篇：高级应用",
    "08-r680-platform": "第八篇：R680 平台",
    "09-deployment-maintenance": "第九篇：部署、备份与维护",
}

PART_ROUTES = (
    "01-bringup/",
    "02-chassis-control/",
    "03-ros2-development/",
    "04-sensors-navigation/",
    "05-stm32-firmware/",
    "06-advanced-applications/",
    "07-r680-platform/",
    "08-deployment-maintenance/",
)

UNNUMBERED_ROUTES = (
    "08-deployment-maintenance/system-acceptance-checklist/",
    "08-deployment-maintenance/42-github-pages-deployment/",
)

FOUNDATIONS = (
    (1, "01-robot-components.md", "一台 ROS 机器人由什么组成"),
    (2, "02-ubuntu-terminal-programs.md", "Ubuntu、终端与程序"),
    (3, "03-what-ros2-solves.md", "ROS 2 解决什么问题"),
    (4, "04-first-ros2-observation.md", "第一次观察 ROS 2"),
    (5, "05-ros2-communication.md", "ROS 2 程序怎样协作"),
)


@dataclass(frozen=True)
class ChapterMove:
    old_path: str
    new_path: str
    old_number: int
    new_number: int


def _read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _redirect_lookup(redirects: list[Redirect]) -> dict[str, str]:
    return {row.source: row.target for row in redirects}


def _markdown_route(path: str) -> str:
    relative = path.removeprefix("docs/")
    if not relative.endswith(".md"):
        raise ValueError(f"not a Markdown path: {path}")
    return relative[:-3] + "/"


def _route_to_markdown(route: str) -> str:
    return "docs/" + route.rstrip("/") + ".md"


def load_moves(root: Path, redirects: list[Redirect]) -> list[ChapterMove]:
    rows = _read_manifest(root / "metadata" / "chapter-manifest.csv")
    if not any(row["kind"] == "theory" for row in rows):
        return []
    lookup = _redirect_lookup(redirects)
    moves: list[ChapterMove] = []
    for row in rows:
        if row["kind"] != "chapter":
            continue
        source = _markdown_route(row["path"])
        target = lookup.get(source)
        if not target:
            raise ValueError(f"missing chapter redirect: {source}")
        old_number = int(row["number"])
        moves.append(
            ChapterMove(
                row["path"],
                _route_to_markdown(target),
                old_number,
                old_number + 5,
            )
        )
    return moves


def rewrite_heading(text: str, old_number: int, new_number: int) -> str:
    pattern = re.compile(rf"^#\s+{old_number}\.\s+", flags=re.MULTILINE)
    rewritten, count = pattern.subn(f"# {new_number}. ", text, count=1)
    if count != 1:
        raise ValueError(f"expected one H1 for Chapter {old_number}")
    return rewritten


def _replace_h1(text: str, title: str) -> str:
    rewritten, count = re.subn(r"^#\s+.+$", f"# {title}", text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise ValueError(f"expected one H1 for {title}")
    return rewritten


def _write_manifest(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "kind",
        "number",
        "volume",
        "path",
        "title",
        "status",
        "size_limit_bytes",
    ]
    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _move_file(root: Path, old_path: str, new_path: str) -> None:
    source = root / old_path
    target = root / new_path
    target.parent.mkdir(parents=True, exist_ok=True)
    source.rename(target)


def apply_moves(root: Path, redirects: list[Redirect]) -> tuple[int, int, int]:
    manifest_path = root / "metadata" / "chapter-manifest.csv"
    rows = _read_manifest(manifest_path)
    moves = load_moves(root, redirects)
    if not moves:
        return (0, 0, 0)
    lookup = _redirect_lookup(redirects)

    file_moves: list[tuple[str, str]] = [
        (move.old_path, move.new_path) for move in moves
    ]
    for source_route in PART_ROUTES:
        file_moves.append(
            (
                f"docs/{source_route}index.md",
                f"docs/{lookup[source_route]}index.md",
            )
        )
    for source_route in UNNUMBERED_ROUTES:
        file_moves.append(
            (
                _route_to_markdown(source_route),
                _route_to_markdown(lookup[source_route]),
            )
        )

    missing = [source for source, _ in file_moves if not (root / source).is_file()]
    collisions = [target for _, target in file_moves if (root / target).exists()]
    if missing:
        raise FileNotFoundError(f"missing move sources: {missing}")
    if collisions:
        raise FileExistsError(f"move targets already exist: {collisions}")

    for move in moves:
        source = root / move.old_path
        text = source.read_text(encoding="utf-8")
        source.write_text(
            rewrite_heading(text, move.old_number, move.new_number),
            encoding="utf-8",
        )
    for source_route in PART_ROUTES:
        source = root / f"docs/{source_route}index.md"
        target_part = lookup[source_route].rstrip("/")
        source.write_text(
            _replace_h1(source.read_text(encoding="utf-8"), PART_TITLES[target_part]),
            encoding="utf-8",
        )

    for source, target in file_moves:
        _move_file(root, source, target)

    original_by_path = {row["path"]: row for row in rows}
    final_rows: list[dict[str, str]] = []
    for number, filename, title in FOUNDATIONS:
        final_rows.append(
            {
                "kind": "foundation",
                "number": str(number),
                "volume": "01-foundations",
                "path": f"docs/01-foundations/{filename}",
                "title": title,
                "status": "complete",
                "size_limit_bytes": "150000",
            }
        )
    for move in moves:
        original = original_by_path[move.old_path]
        final_rows.append(
            {
                **original,
                "number": str(move.new_number),
                "volume": Path(move.new_path).parent.name,
                "path": move.new_path,
            }
        )
    final_rows.extend(row for row in rows if row["kind"] == "appendix")
    _write_manifest(manifest_path, final_rows)

    for source_route in PART_ROUTES:
        directory = root / "docs" / source_route.rstrip("/")
        if directory.exists() and not any(directory.iterdir()):
            directory.rmdir()
    return (len(moves), len(PART_ROUTES), len(UNNUMBERED_ROUTES))


def main() -> int:
    parser = argparse.ArgumentParser(description="Renumber and move textbook chapters")
    parser.add_argument("--root", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    redirects = load_redirects(root / "metadata" / "legacy-redirects.csv")
    moves = load_moves(root, redirects)
    if args.dry_run:
        for move in moves:
            print(
                f"Chapter {move.old_number:02d} -> {move.new_number:02d}: "
                f"{move.old_path} -> {move.new_path}"
            )
        print(
            f"dry run: chapters={len(moves)} part_indexes={len(PART_ROUTES)} "
            f"unnumbered={len(UNNUMBERED_ROUTES)}"
        )
        return 0
    chapters, indexes, unnumbered = apply_moves(root, redirects)
    print(
        f"migrated chapters={chapters} part_indexes={indexes} "
        f"unnumbered={unnumbered}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
