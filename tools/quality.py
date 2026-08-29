from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

from editorial_audit import scan_markdown
from terminology_audit import audit_rules, load_rules


REQUIRED_MANIFEST_COLUMNS = {
    "kind",
    "number",
    "volume",
    "path",
    "title",
    "status",
    "size_limit_bytes",
}
ALLOWED_STATUSES = {"draft", "complete"}
ALLOWED_KINDS = {"foundation", "chapter", "appendix"}
FOUNDATION_HEADINGS = ["章节导航"]
FOUNDATION_HEADINGS_BY_NUMBER = {
    1: [
        "1.1 从机器人软件的难题说起",
        "1.2 ROS 的名称与定位",
        "1.3 ROS 的发展历程",
        "1.4 从 ROS 1 到 ROS 2",
        "1.5 ROS 2 提供哪些基础能力",
        "1.6 ROS 2 在机器人系统中的位置",
        "1.7 本章小结",
        "1.8 思考与练习",
        "章节导航",
    ],
    2: [
        "2.1 从一次避障过程看机器人系统",
        "2.2 感知：传感器怎样描述环境",
        "2.3 计算：主控怎样运行机器人程序",
        "2.4 控制：控制板怎样执行速度目标",
        "2.5 执行：电机与机械结构怎样产生运动",
        "2.6 信息流与能量流",
        "2.7 本章小结",
        "2.8 观察练习",
        "章节导航",
    ],
    3: [
        "3.1 主控首先是一台计算机",
        "3.2 操作系统管理什么",
        "3.3 文件与目录",
        "3.4 程序与进程",
        "3.5 终端与命令",
        "3.6 本地终端与远程终端",
        "3.7 安全的观察命令",
        "3.8 本章小结与练习",
        "章节导航",
    ],
    4: [
        "4.1 观察目标与准备",
        "4.2 启动 talker",
        "4.3 启动 listener",
        "4.4 查看节点、话题与消息",
        "4.5 结束实验并解释现象",
        "4.6 本章小结与练习",
        "章节导航",
    ],
    5: [
        "5.1 节点：把任务拆成独立程序",
        "5.2 话题：持续发布的数据流",
        "5.3 服务：一次请求与一次响应",
        "5.4 动作：可以反馈和取消的耗时任务",
        "5.5 参数：节点自己的配置",
        "5.6 从雷达到电机的数据链",
        "5.7 本章小结与练习",
        "章节导航",
    ],
    6: [
        "6.1 主控与控制板",
        "6.2 CPU、MCU 与 STM32",
        "6.3 源码、固件与构建结果",
        "6.4 烧录与回滚",
        "6.5 电源域、信号域与功率级",
        "6.6 观察练习",
        "6.7 本章小结",
        "章节导航",
    ],
    7: [
        "7.1 接线前先分清电气条件",
        "7.2 USB 与串行端口",
        "7.3 UART、USART 与逻辑电平",
        "7.4 CAN 总线",
        "7.5 字节流、数据帧与校验",
        "7.6 GPIO、I²C、SPI 与 DMA",
        "7.7 本章小结与观察练习",
        "章节导航",
    ],
    8: [
        "8.1 环境信息与机器人自身状态",
        "8.2 编码器怎样记录转动",
        "8.3 GMR 与霍尔效应编码器",
        "8.4 IMU 怎样测量运动",
        "8.5 OLED 是状态窗口",
        "8.6 激光雷达、相机与 GNSS",
        "8.7 采样、时间与坐标方向",
        "8.8 本章小结与观察练习",
        "章节导航",
    ],
    9: [
        "9.1 机体坐标与底盘自由度",
        "9.2 正运动学与逆运动学",
        "9.3 从编码器到里程计",
        "9.4 电机驱动器与 PWM",
        "9.5 PI/PID 闭环控制",
        "9.6 限幅、超时与停止",
        "9.7 本章小结与观察练习",
        "章节导航",
    ],
}
def expected_engineering_headings(number: int) -> list[str]:
    if number == 47:
        return [
            "47.1 学习目标",
            "47.2 适用范围",
            "47.3 静态核对",
            "47.4 安全边界",
            "47.5 故障记录",
            "47.6 章节导航",
        ]
    task_titles = {
        (22, 5): "源码包确认",
        (25, 5): "启动链源码追踪",
        (27, 5): "源码修改练习",
        (37, 5): "固件实验记录",
        (38, 5): "外设最小实验",
        (39, 3): "闭环前置检查",
        (41, 5): "ROS—串口—固件链",
    }
    defaults = {
        1: "学习目标",
        2: "适用范围",
        3: "操作前检查",
        4: "工作原理",
        5: "操作步骤",
        6: "验收标准",
        7: "故障排查",
    }
    return [
        *[
            f"{number}.{section} {task_titles.get((number, section), defaults[section])}"
            for section in range(1, 8)
        ],
        "章节导航",
    ]
PROMOTIONAL_PATTERNS = ["推荐关注我们的公众号", "关注公众号", "获取更新资料"]
UNFINISHED_PATTERNS = [r"\bTODO\b", r"\bTBD\b", r"\[待写\]", r"\[内容待补\]"]
FORBIDDEN_FOUNDATION_PATTERNS = {
    "later chapter prerequisite": r"(?:已读|先读|完成|先完成)第\s*(?:1[0-9]|[2-4][0-9]|50)\s*章",
    "advanced middleware jargon": r"\b(?:DDS|QoS|TF|colcon|Launch|Docker)\b",
    "required SSH access": r"必须(?:使用|通过).*SSH",
    "required robot runtime": r"(?:机器人|WHEELTEC).*(?:节点|系统).*已启动",
}
LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)\r\n]+)\)")


@dataclass(frozen=True)
class Issue:
    severity: str
    path: str
    message: str


def load_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def check_manifest(rows: list[dict[str, str]]) -> list[str]:
    if not rows:
        return ["chapter manifest is empty"]

    errors: list[str] = []
    if set(rows[0]) != REQUIRED_MANIFEST_COLUMNS:
        errors.append("chapter manifest columns do not match the schema")

    paths = [row.get("path", "") for row in rows]
    if len(paths) != len(set(paths)):
        errors.append("chapter manifest paths are not unique")

    for row in rows:
        if row.get("kind") not in ALLOWED_KINDS:
            errors.append(f"invalid kind: {row.get('kind', '')}")
        if row.get("status") not in ALLOWED_STATUSES:
            errors.append(f"invalid status: {row.get('status', '')}")
        if not row.get("path", "").startswith("docs/"):
            errors.append(f"path is outside docs: {row.get('path', '')}")
        try:
            if int(row.get("size_limit_bytes", "0")) <= 0:
                raise ValueError
        except ValueError:
            errors.append(f"invalid size limit: {row.get('path', '')}")

    foundations = [row for row in rows if row.get("kind") == "foundation"]
    chapters = [row for row in rows if row.get("kind") == "chapter"]
    appendices = [row for row in rows if row.get("kind") == "appendix"]
    try:
        foundation_numbers = [int(row["number"]) for row in foundations]
        chapter_numbers = [int(row["number"]) for row in chapters]
        numbered_rows = [
            int(row["number"])
            for row in rows
            if row.get("kind") in {"foundation", "chapter"}
        ]
    except (KeyError, ValueError):
        foundation_numbers = []
        chapter_numbers = []
        numbered_rows = []
    if foundation_numbers != list(range(1, 10)):
        errors.append("foundation numbers must be consecutive from 1 through 9")
    if chapter_numbers != list(range(10, 51)):
        errors.append("engineering chapter numbers must be consecutive from 10 through 50")
    if numbered_rows != list(range(1, 51)):
        errors.append("all numbered pages must be ordered from 1 through 50")
    if [row.get("number") for row in appendices] != ["A", "B", "C", "D"]:
        errors.append("public chapter manifest must contain appendices A through D")
    return errors


def check_chapter(path: Path, size_limit: int, number: int = 6) -> list[Issue]:
    issues: list[Issue] = []
    relative = path.as_posix()
    if path.stat().st_size > size_limit:
        issues.append(Issue("error", relative, "file exceeds size limit"))
    text = path.read_text(encoding="utf-8")
    headings = [
        re.sub(r"\s+\{#[^}]+\}$", "", heading)
        for heading in re.findall(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE)
    ]
    for heading in expected_engineering_headings(number):
        if heading not in headings:
            issues.append(Issue("error", relative, f"missing section: {heading}"))
    if any(pattern in text for pattern in PROMOTIONAL_PATTERNS):
        issues.append(Issue("error", relative, "supplier promotional copy is not allowed"))
    for pattern in UNFINISHED_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            issues.append(Issue("error", relative, "unfinished-work marker is not allowed"))
            break
    return issues


def check_foundation(path: Path, size_limit: int, number: int | None = None) -> list[Issue]:
    issues: list[Issue] = []
    relative = path.as_posix()
    if path.stat().st_size > size_limit:
        issues.append(Issue("error", relative, "file exceeds size limit"))
    text = path.read_text(encoding="utf-8")
    headings = set(re.findall(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE))
    expected = FOUNDATION_HEADINGS_BY_NUMBER.get(number, FOUNDATION_HEADINGS)
    for heading in expected:
        if heading not in headings:
            issues.append(Issue("error", relative, f"missing section: {heading}"))
    for category, pattern in FORBIDDEN_FOUNDATION_PATTERNS.items():
        if re.search(pattern, text, flags=re.IGNORECASE):
            issues.append(Issue("error", relative, category))
    if any(pattern in text for pattern in PROMOTIONAL_PATTERNS):
        issues.append(Issue("error", relative, "supplier promotional copy is not allowed"))
    for pattern in UNFINISHED_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            issues.append(Issue("error", relative, "unfinished-work marker is not allowed"))
            break
    return issues


def check_links(path: Path, docs_root: Path) -> list[Issue]:
    issues: list[Issue] = []
    text = path.read_text(encoding="utf-8")
    for match in LINK_PATTERN.finditer(text):
        raw = match.group(1).strip()
        if raw.startswith(("http://", "https://", "mailto:", "data:", "#")):
            continue
        path_part = unquote(raw.split("#", 1)[0].split("?", 1)[0])
        if not path_part:
            continue
        target = (path.parent / path_part).resolve()
        try:
            target.relative_to(docs_root.resolve())
        except ValueError:
            issues.append(Issue("error", path.as_posix(), f"link leaves docs root: {raw}"))
            continue
        if not target.exists():
            issues.append(Issue("error", path.as_posix(), f"missing internal link target: {raw}"))
    return issues


def _markdown_files(root: Path, selected_paths: list[Path] | None) -> list[Path]:
    if not selected_paths:
        return sorted((root / "docs").rglob("*.md"))
    files: set[Path] = set()
    for path in selected_paths:
        resolved = path if path.is_absolute() else root / path
        if resolved.is_file() and resolved.suffix.lower() == ".md":
            files.add(resolved)
        elif resolved.is_dir():
            files.update(resolved.rglob("*.md"))
    return sorted(files)


def check_duplicate_prose(paths: list[Path]) -> list[Issue]:
    seen: dict[str, Path] = {}
    issues: list[Issue] = []
    for path in paths:
        text = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.DOTALL)
        for paragraph in re.split(r"\n\s*\n", text):
            normalized = re.sub(r"\s+", " ", paragraph).strip()
            if len(normalized) <= 500 or normalized.startswith("|"):
                continue
            if normalized in seen:
                issues.append(
                    Issue(
                        "error",
                        path.as_posix(),
                        f"duplicate prose block also appears in {seen[normalized].as_posix()}",
                    )
                )
            else:
                seen[normalized] = path
    return issues


def check_all(root: Path, selected_paths: list[Path] | None = None) -> list[Issue]:
    root = root.resolve()
    issues: list[Issue] = []
    manifest = load_manifest(root / "metadata" / "chapter-manifest.csv")
    issues.extend(Issue("error", "metadata/chapter-manifest.csv", message) for message in check_manifest(manifest))
    manifest_by_path = {row["path"]: row for row in manifest}
    markdown_files = _markdown_files(root, selected_paths)

    for path in markdown_files:
        relative = path.relative_to(root).as_posix()
        row = manifest_by_path.get(relative)
        if row and row["status"] == "complete":
            size_limit = int(row["size_limit_bytes"])
            if row["kind"] == "foundation":
                issues.extend(check_foundation(path, size_limit, int(row["number"])))
            elif row["kind"] == "chapter":
                issues.extend(check_chapter(path, size_limit, int(row["number"])))
            elif path.stat().st_size > size_limit:
                issues.append(Issue("error", relative, "file exceeds size limit"))
        if relative == "docs/index.md" and path.stat().st_size > 20_000:
            issues.append(Issue("error", relative, "file exceeds size limit"))
        if relative.endswith("/index.md") and relative != "docs/index.md" and path.stat().st_size > 30_000:
            issues.append(Issue("error", relative, "file exceeds size limit"))
        issues.extend(check_links(path, root / "docs"))
        issues.extend(check_editorial_style(path))

    complete_paths = [
        root / row["path"]
        for row in manifest
        if row["status"] == "complete" and (root / row["path"]).is_file()
    ]
    issues.extend(check_duplicate_prose(complete_paths))
    return issues


def check_editorial_style(path: Path) -> list[Issue]:
    return [
        Issue("error", issue.path, f"{issue.category}: {issue.excerpt}")
        for issue in scan_markdown(path)
    ]


def check_terminology(root: Path, paths: list[Path] | None = None) -> list[Issue]:
    """Adapt terminology-audit findings to the repository quality issue type."""
    return [
        Issue("error", item.path, f"{item.category}: {item.term}: {item.message}")
        for item in audit_rules(
            root,
            load_rules(root / "metadata" / "terminology.csv"),
            paths=paths,
        )
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Check textbook structure and content quality")
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check")
    check.add_argument("--root", type=Path, required=True)
    check.add_argument("--paths", type=Path, nargs="*")
    check.add_argument("--editorial-strict", action="store_true")
    args = parser.parse_args()

    issues = check_all(args.root, args.paths)
    # Kept as a compatibility flag; editorial hard failures are now always enabled.
    for issue in issues:
        print(f"{issue.severity.upper()} {issue.path}: {issue.message}")
    errors = [issue for issue in issues if issue.severity == "error"]
    print(f"quality check: {len(errors)} errors, {len(issues) - len(errors)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
