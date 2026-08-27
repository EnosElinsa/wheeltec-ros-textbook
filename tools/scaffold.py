from __future__ import annotations

import argparse
import csv
import os
import tempfile
from pathlib import Path


VOLUME_TITLES = {
    "01-foundations": "第一篇：从零认识 ROS 机器人",
    "02-bringup": "第二篇：实机接入与首次启动",
    "03-chassis-control": "第三篇：底盘控制与运动学",
    "04-ros2-development": "第四篇：ROS 2 开发",
    "05-sensors-navigation": "第五篇：传感器、建图与导航",
    "06-stm32-firmware": "第六篇：STM32 与底盘固件",
    "07-advanced-applications": "第七篇：高级应用",
    "08-r680-platform": "第八篇：R680 平台",
    "09-deployment-maintenance": "第九篇：部署、备份与维护",
    "00-ros2-theory": "卷零：ROS 2 理论基础",
    "01-bringup": "卷一：实机接入与首次启动",
    "02-chassis-control": "卷二：底盘控制与运动学",
    "03-ros2-development": "卷三：ROS 2 开发主线",
    "04-sensors-navigation": "卷四：传感器、建图与导航",
    "05-stm32-firmware": "卷五：STM32 与底盘固件",
    "06-advanced-applications": "卷六：高级应用",
    "07-r680-platform": "卷七：R680 平台实践",
    "08-deployment-maintenance": "卷八：部署、备份与维护",
}


def _draft_page(title: str) -> str:
    return f"---\nstatus: draft\n---\n\n# {title}\n"


def create_pages(rows: list[dict[str, str]], root: Path) -> list[Path]:
    created: list[Path] = []
    for row in rows:
        target = root / row["path"]
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_draft_page(row["title"]), encoding="utf-8")
        created.append(target)

    volumes = sorted(
        {
            row["volume"]
            for row in rows
            if row["kind"] in {"theory", "foundation", "chapter"}
        }
    )
    for volume in volumes:
        target = root / "docs" / volume / "index.md"
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_draft_page(VOLUME_TITLES[volume]), encoding="utf-8")
        created.append(target)
    return created


def set_status(
    rows: list[dict[str, str]], selector_field: str, selector_value: str, status: str
) -> int:
    if status not in {"draft", "complete"}:
        raise ValueError(f"invalid status: {status}")
    changed = 0
    for row in rows:
        if row.get(selector_field) == selector_value and row.get("status") != status:
            row["status"] = status
            changed += 1
    return changed


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv_atomic(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = list(rows[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create and update textbook page scaffolds")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create")
    create_parser.add_argument("--manifest", type=Path, required=True)
    create_parser.add_argument("--root", type=Path, required=True)

    status_parser = subparsers.add_parser("set-status")
    status_parser.add_argument("--manifest", type=Path, required=True)
    selector = status_parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--volume")
    selector.add_argument("--kind")
    status_parser.add_argument("--status", choices=("draft", "complete"), required=True)

    args = parser.parse_args()
    rows = _read_csv(args.manifest)
    if args.command == "create":
        created = create_pages(rows, args.root)
        print(f"created {len(created)} scaffold pages")
        return 0

    field = "volume" if args.volume else "kind"
    value = args.volume or args.kind
    changed = set_status(rows, field, value, args.status)
    _write_csv_atomic(args.manifest, rows)
    print(f"updated {changed} manifest rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
