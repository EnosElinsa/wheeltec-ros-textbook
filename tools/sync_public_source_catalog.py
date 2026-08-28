from __future__ import annotations

import argparse
import csv
import html
from pathlib import Path


EXPORT_HEADERS = [
    "archive_id",
    "canonical_archive_id",
    "content_kind",
    "publication_status",
    "source_name",
    "source_sha256",
    "source_bytes",
    "snapshot_url",
    "release_download_url",
    "topic",
    "usage_level",
    "role",
    "chapter_paths",
]


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != EXPORT_HEADERS:
            raise ValueError("public source export columns do not match schema")
        rows = list(reader)
    if len(rows) != 240:
        raise ValueError(f"expected 240 public rows, got {len(rows)}")
    if sum(row["content_kind"] == "source_archive" for row in rows) != 220:
        raise ValueError("public source row count is not 220")
    if len({row["canonical_archive_id"] for row in rows if row["publication_status"] == "publishable"}) != 204:
        raise ValueError("unique publishable archive count is not 204")
    if any(":" in row["archive_id"] for row in rows):
        raise ValueError("internal archive IDs must not appear in textbook export")
    return rows


def write_metadata(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPORT_HEADERS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def render_appendix(rows: list[dict[str, str]]) -> str:
    lines = [
        "---",
        "status: complete",
        "---",
        "",
        "# D. 公开源码参考",
        "",
        "本附录把教材章节与独立公开源码参考仓库连接起来。公开不等于适配当前实机；STM32 与 R680 源码在实机照片补齐前只能用于阅读、比较和建立候选关系。",
        "",
        "## 使用方法",
        "",
        "1. 按公开 ID 找到源码快照，先阅读包结构、入口文件和依赖。",
        "2. 需要构建或完整资源时下载 Release 原始归档，并核对表中的 SHA-256。",
        "3. 按使用等级核对 ROS 发行版、主控平台、控制板、车型和编码器。",
        "4. 涉及运动、固件或烧录时，先完成教材中的安全检查和恢复准备。",
        "",
        "仓库主页：[wheeltec-ros-source-reference](https://github.com/EnosElinsa/wheeltec-ros-source-reference)，发布版本：`source-archive-2026-08-28`。",
        "",
        "## 使用等级",
        "",
        "- `learning`：硬件无关，可直接作为教学代码阅读或构建。",
        "- `reference_only`：用于比较结构和追踪实现，不据此操作实机。",
        "- `platform_match_required`：先匹配主控、操作系统和 ROS 发行版。",
        "- `hardware_match_required`：还必须匹配控制板、编码器、车型或电机结构。",
        "",
    ]
    topics: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        topics.setdefault(row["topic"], []).append(row)
    for topic in sorted(topics):
        lines.extend(
            [
                f"## {topic}",
                "",
                "| 公开 ID | 源码包 | 使用等级 | 浏览 | 下载 | 教材位置 |",
                "|---|---|---|---|---|---|",
            ]
        )
        for row in topics[topic]:
            browse = f"[查看]({row['snapshot_url']})" if row["snapshot_url"] else "目录记录"
            download = f"[下载]({row['release_download_url']})" if row["release_download_url"] else "非源码附件"
            lines.append(
                "| "
                f"`{cell(row['archive_id'])}` | {cell(row['source_name'])} | "
                f"`{cell(row['usage_level'])}` | {browse} | {download} | "
                f"{cell(row['chapter_paths'])} |"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync the public source catalog into the textbook")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--appendix", type=Path, required=True)
    args = parser.parse_args()
    rows = load_rows(args.source)
    write_metadata(args.metadata, rows)
    args.appendix.parent.mkdir(parents=True, exist_ok=True)
    args.appendix.write_text(render_appendix(rows), encoding="utf-8", newline="\n")
    print(f"synced {len(rows)} public source rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
